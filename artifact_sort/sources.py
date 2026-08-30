from __future__ import annotations

from dataclasses import dataclass
import csv
from hashlib import sha256
import json
from pathlib import Path
import select
import subprocess
from threading import Lock
from typing import Any, Mapping, Sequence

import numpy as np
from numpy.typing import NDArray

from .model import SLOT_INDEX, STAT_INDEX, STAT_KEYS
from .scenarios import Evaluator, Scenario, _stat_vector, scenario_from_mapping


GO_IMPORT_VERSION = "go-database-v1"
AKASHA_SNAPSHOT_VERSION = 1


def _path_stat(value: object) -> str | None:
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            parsed = value
        return _path_stat(parsed)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for part in reversed(value):
            if isinstance(part, str) and part in STAT_INDEX:
                return part
    return None


def _target_objective(target: Mapping[str, Any], opt_config: Mapping[str, Any]) -> str:
    searchable = json.dumps(
        {"target": target, "optimizationTarget": opt_config.get("optimizationTarget")},
        sort_keys=True,
    ).lower()
    if "heal" in searchable:
        return "healing"
    if "shield" in searchable:
        return "shield"
    if "reaction" in searchable:
        return "reaction"
    return "damage"


def _tc_stat_totals(build: Mapping[str, Any]) -> dict[str, float]:
    totals: dict[str, float] = {}
    artifact = build.get("artifact")
    if not isinstance(artifact, Mapping):
        return totals
    substats = artifact.get("substats")
    if isinstance(substats, Mapping):
        stats = substats.get("stats", substats)
        if isinstance(stats, Mapping):
            for key, value in stats.items():
                if key in STAT_INDEX and isinstance(value, (int, float)):
                    totals[str(key)] = float(value)
    return totals


def _scaling_stat(build: Mapping[str, Any]) -> str:
    totals = _tc_stat_totals(build)
    candidates = ("atk_", "hp_", "def_")
    best = max(candidates, key=lambda key: totals.get(key, 0.0))
    return {"atk_": "atk", "hp_": "hp", "def_": "def"}[best]


def _damage_stat(build: Mapping[str, Any]) -> str | None:
    artifact = build.get("artifact")
    if not isinstance(artifact, Mapping):
        return None
    slots = artifact.get("slots")
    if isinstance(slots, Mapping):
        goblet = slots.get("goblet")
        if isinstance(goblet, Mapping):
            key = goblet.get("statKey")
            if isinstance(key, str) and (key.endswith("_dmg_") or key == "physical_dmg_"):
                return key
    return None


def _set_requirements(build: Mapping[str, Any]) -> tuple[tuple[str, int], ...]:
    artifact = build.get("artifact")
    if not isinstance(artifact, Mapping):
        return ()
    raw = artifact.get("sets")
    if not isinstance(raw, Mapping):
        return ()
    return tuple(
        sorted(
            (str(key), int(count))
            for key, count in raw.items()
            if isinstance(count, (int, float)) and int(count) >= 2
        )
    )


def _allowed_mains(opt_config: Mapping[str, Any]) -> tuple[tuple[int, tuple[int, ...]], ...]:
    raw = opt_config.get("mainStatKeys")
    if not isinstance(raw, Mapping):
        return ()
    allowed: list[tuple[int, tuple[int, ...]]] = []
    for slot, values in raw.items():
        if slot not in SLOT_INDEX or not isinstance(values, Sequence):
            continue
        stats = tuple(STAT_INDEX[value] for value in values if value in STAT_INDEX)
        if stats:
            allowed.append((SLOT_INDEX[str(slot)], stats))
    return tuple(sorted(allowed))


def _constraints(opt_config: Mapping[str, Any]) -> tuple[tuple[int, float], ...]:
    raw = opt_config.get("statFilters")
    if not isinstance(raw, Mapping):
        return ()
    result: dict[int, float] = {}
    for path, filter_value in raw.items():
        stat = _path_stat(path)
        if stat is None:
            continue
        values: list[float] = []
        settings = filter_value if isinstance(filter_value, list) else [filter_value]
        for setting in settings:
            if isinstance(setting, Mapping):
                if setting.get("disabled", False) or not setting.get("enabled", True):
                    continue
                for key in ("min", "minimum", "value"):
                    value = setting.get(key)
                    if isinstance(value, (int, float)):
                        values.append(float(value))
            elif isinstance(setting, (int, float)):
                values.append(float(setting))
        if values:
            result[STAT_INDEX[stat]] = max(values)
    return tuple(sorted(result.items()))


def _record_index(
    data: Mapping[str, Any], collection: str, *, id_key: str = "id"
) -> dict[str, Mapping[str, Any]]:
    raw = data.get(collection)
    if not isinstance(raw, list):
        raise ValueError(f"GO database export has no {collection!r} array")
    result: dict[str, Mapping[str, Any]] = {}
    for ordinal, record in enumerate(raw):
        if not isinstance(record, Mapping):
            raise ValueError(f"GO {collection}[{ordinal}] is not an object")
        record_id = record.get(id_key)
        if not isinstance(record_id, str) or not record_id:
            raise ValueError(f"GO {collection}[{ordinal}] has no {id_key!r}")
        if record_id in result:
            raise ValueError(f"GO {collection} contains duplicate ID {record_id!r}")
        result[record_id] = record
    return result


def _location_key(character: str) -> str:
    return "Traveler" if character.startswith("Traveler") else character


def _resolved_artifacts(
    artifact_ids: object, artifacts: Mapping[str, Mapping[str, Any]]
) -> list[Mapping[str, Any]]:
    if not isinstance(artifact_ids, Mapping):
        return []
    result: list[Mapping[str, Any]] = []
    for artifact_id in artifact_ids.values():
        if not artifact_id:
            continue
        if not isinstance(artifact_id, str) or artifact_id not in artifacts:
            raise ValueError(f"GO build references missing artifact {artifact_id!r}")
        result.append(artifacts[artifact_id])
    return result


def _set_counts(artifacts: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    raw: dict[str, int] = {}
    for artifact in artifacts:
        set_key = artifact.get("setKey")
        if isinstance(set_key, str) and set_key:
            raw[set_key] = raw.get(set_key, 0) + 1
    result: dict[str, int] = {}
    for set_key, count in raw.items():
        effective = 2 if count == 3 else 4 if count >= 5 else count
        if effective >= 2 or (effective == 1 and set_key.startswith("PrayersFor")):
            result[set_key] = effective
    return result


def _derived_theorycraft_build(
    *,
    name: str,
    description: str,
    character_key: str,
    character: Mapping[str, Any] | None,
    weapon: Mapping[str, Any] | None,
    artifacts: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    slots: dict[str, dict[str, Any]] = {}
    substats: dict[str, float] = {}
    for artifact in artifacts:
        slot = artifact.get("slotKey")
        main_stat = artifact.get("mainStatKey")
        if isinstance(slot, str) and isinstance(main_stat, str):
            slots[slot] = {
                "level": int(artifact.get("level", 0)),
                "rarity": int(artifact.get("rarity", 5)),
                "statKey": main_stat,
            }
        raw_substats = artifact.get("substats")
        if not isinstance(raw_substats, list):
            continue
        for substat in raw_substats:
            if not isinstance(substat, Mapping):
                continue
            key = substat.get("key")
            value = substat.get("value")
            if key in STAT_INDEX and isinstance(value, (int, float)):
                substats[str(key)] = substats.get(str(key), 0.0) + float(value)

    character_state = None
    if character is not None:
        character_state = {
            key: value
            for key, value in character.items()
            if key in {"level", "ascension", "constellation", "talent"}
        }
    weapon_state = None
    if weapon is not None:
        weapon_state = {
            key: value
            for key, value in weapon.items()
            if key in {"key", "level", "ascension", "refinement"}
        }
    return {
        "name": name,
        "description": description,
        "characterKey": character_key,
        "character": character_state,
        "weapon": weapon_state,
        "artifact": {
            "slots": slots,
            "substats": {"type": "max", "stats": substats, "rarity": 5},
            "sets": _set_counts(artifacts),
        },
    }


def _selected_build(
    loadout: Mapping[str, Any],
    team_character: Mapping[str, Any],
    *,
    characters: Mapping[str, Mapping[str, Any]],
    weapons: Mapping[str, Mapping[str, Any]],
    artifacts: Mapping[str, Mapping[str, Any]],
    builds: Mapping[str, Mapping[str, Any]],
    theorycraft_builds: Mapping[str, Mapping[str, Any]],
) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
    character_key = str(team_character["key"])
    character = characters.get(character_key)
    build_type = str(loadout.get("buildType") or "equipped")
    if build_type == "tc":
        build_id = loadout.get("buildTcId")
        if not isinstance(build_id, str) or build_id not in theorycraft_builds:
            raise ValueError(
                f"GO loadout {team_character.get('id')!r} references missing TC build {build_id!r}"
            )
        build = theorycraft_builds[build_id]
        return build, {"type": "tc", "id": build_id, "definition": build}

    if build_type == "real":
        build_id = loadout.get("buildId")
        if not isinstance(build_id, str) or build_id not in builds:
            raise ValueError(
                f"GO loadout {team_character.get('id')!r} references missing build {build_id!r}"
            )
        definition = builds[build_id]
        selected_artifacts = _resolved_artifacts(definition.get("artifactIds"), artifacts)
        weapon_id = definition.get("weaponId")
        if weapon_id and (not isinstance(weapon_id, str) or weapon_id not in weapons):
            raise ValueError(f"GO build {build_id!r} references missing weapon {weapon_id!r}")
        weapon = weapons.get(str(weapon_id)) if weapon_id else None
        build = _derived_theorycraft_build(
            name=str(definition.get("name") or "Selected real build"),
            description=str(definition.get("description") or ""),
            character_key=character_key,
            character=character,
            weapon=weapon,
            artifacts=selected_artifacts,
        )
        return build, {
            "type": "real",
            "id": build_id,
            "definition": definition,
            "weapon": weapon,
            "artifacts": selected_artifacts,
        }

    if build_type != "equipped":
        raise ValueError(f"GO loadout has unsupported build type {build_type!r}")
    location = _location_key(character_key)
    selected_artifacts = [
        artifact for artifact in artifacts.values() if artifact.get("location") == location
    ]
    weapon = next(
        (candidate for candidate in weapons.values() if candidate.get("location") == location),
        None,
    )
    build = _derived_theorycraft_build(
        name="Equipped",
        description="Resolved from the equipped inventory in the GO database export",
        character_key=character_key,
        character=character,
        weapon=weapon,
        artifacts=selected_artifacts,
    )
    return build, {
        "type": "equipped",
        "id": None,
        "character": character,
        "weapon": weapon,
        "artifacts": selected_artifacts,
    }


def _selected_targets(
    team_character: Mapping[str, Any], opt_config: Mapping[str, Any]
) -> tuple[list[Mapping[str, Any]], Mapping[str, Any] | None]:
    path = opt_config.get("optimizationTarget")
    if not isinstance(path, list) or not path or not all(
        isinstance(part, str) for part in path
    ):
        return [], None
    if path[0] != "custom":
        target: dict[str, Any] = {
            "weight": 1.0,
            "path": path,
            "hitMode": team_character.get("hitMode", "avgHit"),
            "bonusStats": team_character.get("bonusStats", {}),
        }
        for key in ("reaction", "infusionAura"):
            if team_character.get(key):
                target[key] = team_character[key]
        return [target], None

    if len(path) < 2:
        return [], None
    try:
        index = int(path[1])
    except ValueError:
        return [], None
    custom_targets = team_character.get("customMultiTargets")
    if not isinstance(custom_targets, list) or not 0 <= index < len(custom_targets):
        return [], None
    selected = custom_targets[index]
    if not isinstance(selected, Mapping):
        return [], None
    raw_targets = selected.get("targets")
    if not isinstance(raw_targets, list):
        return [], selected
    targets = [target for target in raw_targets if isinstance(target, Mapping)]
    return targets, selected


@dataclass(frozen=True, slots=True)
class GOImportResult:
    scenarios: tuple[Scenario, ...]
    skipped: tuple[Mapping[str, Any], ...]
    database: Mapping[str, Any]


def import_go_database(path: str | Path) -> GOImportResult:
    """Resolve a complete Genshin Optimizer database backup into scenarios."""

    source_path = Path(path)
    with source_path.open(encoding="utf-8") as handle:
        raw = json.load(handle)
    if not isinstance(raw, Mapping):
        raise ValueError("GO database export must be a JSON object")
    if raw.get("format") != "GOOD" or raw.get("source") != "Genshin Optimizer":
        raise ValueError(
            "import-go requires a full Genshin Optimizer database download, "
            "not an individual team export or scanner-only GOOD file"
        )

    teams = _record_index(raw, "teams")
    team_characters = _record_index(raw, "teamchars")
    opt_configs = _record_index(raw, "optConfigs")
    builds = _record_index(raw, "builds")
    theorycraft_builds = _record_index(raw, "buildTcs")
    artifacts = _record_index(raw, "artifacts")
    weapons = _record_index(raw, "weapons")
    characters = _record_index(raw, "characters", id_key="key")
    if not teams:
        raise ValueError("GO database export contains no teams")

    database_meta = {
        "format": raw.get("format"),
        "source": raw.get("source"),
        "version": raw.get("version"),
        "dbVersion": raw.get("dbVersion"),
        "dbMeta": raw.get("dbMeta", {}),
        "counts": {
            "teams": len(teams),
            "teamchars": len(team_characters),
            "builds": len(builds),
            "buildTcs": len(theorycraft_builds),
            "artifacts": len(artifacts),
            "weapons": len(weapons),
            "characters": len(characters),
        },
    }
    scenarios: list[Scenario] = []
    skipped: list[Mapping[str, Any]] = []

    for team_id, team in teams.items():
        loadout_data = team.get("loadoutData")
        if not isinstance(loadout_data, list):
            raise ValueError(f"GO team {team_id!r} has invalid loadoutData")
        resolved_loadouts: list[Mapping[str, Any] | None] = []
        for slot, loadout in enumerate(loadout_data):
            if loadout is None:
                resolved_loadouts.append(None)
                continue
            if not isinstance(loadout, Mapping):
                raise ValueError(f"GO team {team_id!r} loadout {slot} is not an object")
            team_character_id = loadout.get("teamCharId")
            if (
                not isinstance(team_character_id, str)
                or team_character_id not in team_characters
            ):
                raise ValueError(
                    f"GO team {team_id!r} loadout {slot} references missing "
                    f"team character {team_character_id!r}"
                )
            team_character = team_characters[team_character_id]
            opt_config_id = team_character.get("optConfigId")
            if not isinstance(opt_config_id, str) or opt_config_id not in opt_configs:
                raise ValueError(
                    f"GO team character {team_character_id!r} references missing "
                    f"optimization config {opt_config_id!r}"
                )
            build, selected_build = _selected_build(
                loadout,
                team_character,
                characters=characters,
                weapons=weapons,
                artifacts=artifacts,
                builds=builds,
                theorycraft_builds=theorycraft_builds,
            )
            resolved_loadouts.append(
                {
                    "slot": slot,
                    "loadout": loadout,
                    "team_character_id": team_character_id,
                    "team_character": team_character,
                    "opt_config_id": opt_config_id,
                    "opt_config": opt_configs[opt_config_id],
                    "selected_build": selected_build,
                    "theorycraft_build": build,
                }
            )

        team_context = {
            "team_id": team_id,
            "team": team,
            "loadouts": resolved_loadouts,
        }
        for resolved in resolved_loadouts:
            if resolved is None:
                continue
            team_character = resolved["team_character"]
            opt_config = resolved["opt_config"]
            build = resolved["theorycraft_build"]
            assert isinstance(team_character, Mapping)
            assert isinstance(opt_config, Mapping)
            assert isinstance(build, Mapping)
            targets, custom_target = _selected_targets(team_character, opt_config)
            if not targets:
                skipped.append(
                    {
                        "team_id": team_id,
                        "team_name": team.get("name", team_id),
                        "slot": resolved["slot"],
                        "team_character_id": resolved["team_character_id"],
                        "character": team_character.get("key", ""),
                        "reason": "no configured optimization target",
                    }
                )
                continue

            character = str(team_character.get("key") or "unknown-character")
            target_name = (
                str(custom_target.get("name"))
                if custom_target and custom_target.get("name")
                else "/".join(str(part) for part in opt_config["optimizationTarget"])
            )
            scenario_name = (
                f"{team.get('name', team_id)} / "
                f"{team_character.get('name', character)} / {target_name}"
            )
            identity = {
                "database": raw.get("dbMeta", {}).get("name")
                if isinstance(raw.get("dbMeta"), Mapping)
                else None,
                "team_id": team_id,
                "team_character_id": resolved["team_character_id"],
                "character": character,
                "target": opt_config.get("optimizationTarget"),
            }
            scenario_id = "go-" + sha256(
                json.dumps(identity, sort_keys=True).encode()
            ).hexdigest()[:12]
            objective_probe: Mapping[str, Any] = {"targets": targets}
            metadata = {
                "adapter_required": True,
                "adapter_reason": "GO formula paths require the pinned GO calculation engine",
                "go_import_version": GO_IMPORT_VERSION,
                "database": database_meta,
                "scenario_name": scenario_name,
                "team_id": team_id,
                "team_character_id": resolved["team_character_id"],
                "character": character,
                "build_name": build.get("name", "Selected build"),
                "build_origin": resolved["selected_build"].get("type"),
                "targets": targets,
                "custom_multi_target": custom_target,
                "theorycraft_build": build,
                "opt_config": opt_config,
                "focus_loadout": resolved,
                "team_context": team_context,
                "source_path": str(source_path),
            }
            scenarios.append(
                Scenario(
                    id=scenario_id,
                    tier="current",
                    objective=_target_objective(  # type: ignore[arg-type]
                        objective_probe, opt_config
                    ),
                    scaling_stat=_scaling_stat(build),  # type: ignore[arg-type]
                    damage_stat=_damage_stat(build),
                    constraints=_constraints(opt_config),
                    required_sets=_set_requirements(build),
                    allowed_main_stats=_allowed_mains(opt_config),
                    source="genshin-optimizer",
                    metadata=metadata,
                )
            )

    if not scenarios:
        raise ValueError(
            "GO database contains no team loadouts with configured optimization targets"
        )
    return GOImportResult(tuple(scenarios), tuple(skipped), database_meta)


def import_go(path: str | Path) -> list[Scenario]:
    return list(import_go_database(path).scenarios)


@dataclass(frozen=True, slots=True)
class AkashaBuild:
    leaderboard_id: str
    category: str
    score: float
    artifacts: tuple[Mapping[str, Any], ...]
    conditions: Mapping[str, Any]
    timestamp: str
    source_url: str
    character: str = ""
    stats: Mapping[str, float] | None = None


@dataclass(frozen=True, slots=True)
class AkashaSnapshot:
    version: int
    builds: tuple[AkashaBuild, ...]

    def baselines(self, leaderboard_id: str) -> NDArray[np.float64]:
        rows = []
        for build in self.builds:
            if build.leaderboard_id == leaderboard_id and build.stats:
                rows.append(_stat_vector(build.stats))
        return np.vstack(rows) if rows else np.empty((0, len(STAT_KEYS)))


def _akasha_build(raw: Mapping[str, Any]) -> AkashaBuild:
    artifacts = raw.get("artifacts", ())
    if isinstance(artifacts, Mapping):
        artifacts = tuple(value for value in artifacts.values() if isinstance(value, Mapping))
    elif isinstance(artifacts, list):
        artifacts = tuple(value for value in artifacts if isinstance(value, Mapping))
    else:
        artifacts = ()
    stats = raw.get("stats")
    return AkashaBuild(
        leaderboard_id=str(raw.get("leaderboard_id") or raw.get("leaderboardId") or ""),
        category=str(raw.get("category") or raw.get("name") or ""),
        score=float(raw.get("score") or raw.get("calculated_score") or 0.0),
        artifacts=artifacts,
        conditions=dict(raw.get("conditions") or {}),
        timestamp=str(raw.get("timestamp") or raw.get("updatedAt") or ""),
        source_url=str(raw.get("source_url") or raw.get("sourceUrl") or ""),
        character=str(raw.get("character") or raw.get("characterId") or ""),
        stats=dict(stats) if isinstance(stats, Mapping) else None,
    )


def import_akasha(path: str | Path) -> AkashaSnapshot:
    source_path = Path(path)
    if source_path.suffix.lower() == ".csv":
        with source_path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        builds = tuple(_akasha_build(row) for row in rows)
        return AkashaSnapshot(AKASHA_SNAPSHOT_VERSION, builds)

    with source_path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if isinstance(data, list):
        version = AKASHA_SNAPSHOT_VERSION
        rows = data
    elif isinstance(data, Mapping):
        version = int(data.get("version", AKASHA_SNAPSHOT_VERSION))
        rows = data.get("builds", data.get("entries", []))
    else:
        raise ValueError("Akasha snapshot must be a JSON object or array")
    if version != AKASHA_SNAPSHOT_VERSION:
        raise ValueError(f"unsupported Akasha snapshot version {version}")
    if not isinstance(rows, list):
        raise ValueError("Akasha snapshot has no builds array")
    return AkashaSnapshot(version, tuple(_akasha_build(row) for row in rows))


def akasha_scenarios(snapshot: AkashaSnapshot) -> list[Scenario]:
    grouped: dict[str, AkashaBuild] = {}
    for build in snapshot.builds:
        grouped.setdefault(build.leaderboard_id, build)
    result: list[Scenario] = []
    for leaderboard_id, representative in grouped.items():
        raw = representative.conditions.get("scenario")
        if not isinstance(raw, Mapping):
            continue
        mapping = dict(raw)
        mapping.setdefault("id", f"akasha-{leaderboard_id}")
        mapping.setdefault("tier", "speculative")
        metadata = dict(mapping.get("metadata") or {})
        metadata.update(
            {
                "leaderboard_id": leaderboard_id,
                "category": representative.category,
                "source_url": representative.source_url,
                "snapshot_timestamp": representative.timestamp,
                "representative_stats": [
                    dict(build.stats)
                    for build in snapshot.builds
                    if build.leaderboard_id == leaderboard_id and build.stats
                ],
            }
        )
        mapping["metadata"] = metadata
        scenario = scenario_from_mapping(mapping, source="akasha-snapshot")
        result.append(scenario)
    return result


@dataclass(frozen=True, slots=True)
class AkashaCalibration:
    leaderboard_id: str
    samples: int
    rank_correlation: float | None
    note: str


def calibrate_akasha(
    snapshot: AkashaSnapshot, scenarios: Sequence[Scenario], evaluator: Evaluator
) -> list[AkashaCalibration]:
    scenario_map = {
        str(scenario.metadata.get("leaderboard_id")): scenario for scenario in scenarios
    }
    result: list[AkashaCalibration] = []
    for leaderboard_id in sorted({build.leaderboard_id for build in snapshot.builds}):
        scenario = scenario_map.get(leaderboard_id)
        rows = [
            build
            for build in snapshot.builds
            if build.leaderboard_id == leaderboard_id and build.stats
        ]
        if scenario is None or len(rows) < 2:
            result.append(
                AkashaCalibration(
                    leaderboard_id,
                    len(rows),
                    None,
                    "requires a labeled scenario and at least two stat baselines",
                )
            )
            continue
        predicted = np.asarray(
            [evaluator.evaluate(_stat_vector(build.stats), scenario) for build in rows]
        )
        observed = np.asarray([build.score for build in rows])
        predicted_rank = np.argsort(np.argsort(predicted))
        observed_rank = np.argsort(np.argsort(observed))
        correlation = float(np.corrcoef(predicted_rank, observed_rank)[0, 1])
        result.append(
            AkashaCalibration(
                leaderboard_id,
                len(rows),
                correlation,
                "rank correlation is validation only; it is not fitted as a universal weight",
            )
        )
    return result


class GOAdapterError(RuntimeError):
    pass


class GOEvaluator:
    """Evaluator backed by a pinned local GO JSON-lines adapter process."""

    def __init__(self, command: Sequence[str], *, timeout: float = 60.0) -> None:
        if not command:
            raise ValueError("GO adapter command cannot be empty")
        self.command = tuple(command)
        self.timeout = timeout
        try:
            self._process = subprocess.Popen(
                self.command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                bufsize=1,
            )
        except OSError as exc:
            raise GOAdapterError(f"could not start GO adapter: {exc}") from exc
        self._lock = Lock()
        response = self._request({"protocol": 1, "type": "version"})
        version = response.get("goVersion") or response.get("version")
        if not isinstance(version, str) or not version:
            raise GOAdapterError("GO adapter did not report a version")
        self.version = f"go:{version}"

    def _request(self, request: Mapping[str, Any]) -> Mapping[str, Any]:
        stdin = self._process.stdin
        stdout = self._process.stdout
        if stdin is None or stdout is None or self._process.poll() is not None:
            raise GOAdapterError("GO adapter is not running")
        try:
            with self._lock:
                stdin.write(json.dumps(request, separators=(",", ":")) + "\n")
                stdin.flush()
                readable, _, _ = select.select([stdout], [], [], self.timeout)
                if not readable:
                    raise GOAdapterError("GO adapter timed out")
                line = stdout.readline()
        except (OSError, BrokenPipeError) as exc:
            raise GOAdapterError(f"GO adapter communication failed: {exc}") from exc
        try:
            response = json.loads(line)
        except json.JSONDecodeError as exc:
            raise GOAdapterError("GO adapter returned invalid JSON") from exc
        if not isinstance(response, Mapping):
            raise GOAdapterError("GO adapter response must be an object")
        if response.get("error"):
            raise GOAdapterError(str(response["error"]))
        return response

    def close(self) -> None:
        if self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=2.0)
            except subprocess.TimeoutExpired:
                self._process.kill()

    def __del__(self) -> None:
        process = getattr(self, "_process", None)
        if process is not None and process.poll() is None:
            process.terminate()

    def evaluate(self, artifact_stats: NDArray[np.float64], scenario: Scenario) -> float:
        return float(self.evaluate_batch(artifact_stats[None, :], scenario)[0])

    def evaluate_batch(
        self, artifact_stats: NDArray[np.float64], scenario: Scenario
    ) -> NDArray[np.float64]:
        response = self._request(
            {
                "protocol": 1,
                "type": "evaluateBatch",
                "goVersion": self.version.removeprefix("go:"),
                "scenario": scenario.metadata,
                "artifactStats": [
                    {key: float(row[i]) for i, key in enumerate(STAT_KEYS)}
                    for row in artifact_stats
                ],
            }
        )
        reported_version = response.get("goVersion") or response.get("version")
        if reported_version != self.version.removeprefix("go:"):
            raise GOAdapterError("GO adapter result version does not match its handshake")
        utilities = response.get("utilities")
        if not isinstance(utilities, list) or len(utilities) != len(artifact_stats):
            raise GOAdapterError("GO adapter result has invalid utilities")
        result = np.asarray(utilities, dtype=np.float64)
        if not np.all(np.isfinite(result) | np.isneginf(result)):
            raise GOAdapterError("GO adapter returned a non-numeric utility")
        return result

    def marginal_weights(
        self, baseline: NDArray[np.float64], scenario: Scenario
    ) -> NDArray[np.float64]:
        points = np.repeat(baseline[None, :], len(STAT_KEYS) + 1, axis=0)
        points[np.arange(1, len(STAT_KEYS) + 1), np.arange(len(STAT_KEYS))] += 1.0
        values = self.evaluate_batch(points, scenario)
        result = np.maximum(0.0, values[1:] - values[0])
        maximum = result.max(initial=0.0)
        return result / maximum if maximum else result


@dataclass(frozen=True, slots=True)
class GOScenarioProvider:
    path: str | Path
    name: str = "genshin-optimizer"

    def scenarios(self) -> Sequence[Scenario]:
        return import_go(self.path)


@dataclass(frozen=True, slots=True)
class AkashaScenarioProvider:
    path: str | Path
    name: str = "akasha-snapshot"

    def scenarios(self) -> Sequence[Scenario]:
        return akasha_scenarios(import_akasha(self.path))
