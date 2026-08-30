from __future__ import annotations

from dataclasses import dataclass
import csv
from hashlib import sha256
import json
from pathlib import Path
import select
import subprocess
from threading import Lock
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
from numpy.typing import NDArray

from .model import SLOT_INDEX, STAT_INDEX, STAT_KEYS
from .scenarios import Evaluator, Scenario, _stat_vector, scenario_from_mapping


GO_IMPORT_VERSION = "go-export-v1"
AKASHA_SNAPSHOT_VERSION = 1


def _walk_mappings(value: object) -> Iterable[Mapping[str, Any]]:
    if isinstance(value, Mapping):
        yield value
        for child in value.values():
            yield from _walk_mappings(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_mappings(child)


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
        if isinstance(filter_value, Mapping):
            enabled = filter_value.get("enabled", True)
            if not enabled:
                continue
            for key in ("min", "minimum", "value"):
                value = filter_value.get(key)
                if isinstance(value, (int, float)):
                    values.append(float(value))
        elif isinstance(filter_value, (int, float)):
            values.append(float(filter_value))
        if values:
            result[STAT_INDEX[stat]] = max(values)
    return tuple(sorted(result.items()))


def import_go(path: str | Path) -> list[Scenario]:
    """Translate user-supplied GO team/theorycraft exports into scenarios.

    The original GO fragments are retained in metadata for the optional exact
    evaluator. Translation deliberately refuses to invent a formula: without
    that adapter, the built-in evaluator is only a documented approximation.
    """

    source_path = Path(path)
    with source_path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    builds = [node for node in _walk_mappings(data) if isinstance(node.get("artifact"), Mapping)]
    if not builds:
        raise ValueError("GO export contains no theorycraft builds")

    scenarios: list[Scenario] = []
    seen: set[str] = set()
    all_nodes = list(_walk_mappings(data))
    for ordinal, build in enumerate(builds):
        opt_config = build.get("optConfig")
        if not isinstance(opt_config, Mapping):
            opt_config = next(
                (node.get("optConfig") for node in all_nodes if isinstance(node.get("optConfig"), Mapping)),
                {},
            )
        targets = build.get("customMultiTargets")
        if not isinstance(targets, list) or not targets:
            targets = [
                {
                    "weight": 1.0,
                    "path": opt_config.get("optimizationTarget", []),
                    "name": "optimization-target",
                }
            ]
        character = str(
            build.get("characterKey")
            or build.get("key")
            or build.get("character")
            or "unknown-character"
        )
        name = str(build.get("name") or f"build-{ordinal + 1}")
        key_raw = f"{character}:{name}:{ordinal}"
        scenario_id = "go-" + sha256(key_raw.encode()).hexdigest()[:12]
        if scenario_id in seen:
            continue
        seen.add(scenario_id)

        target = targets[0] if isinstance(targets[0], Mapping) else {}
        objective = _target_objective(target, opt_config)
        metadata = {
            "adapter_required": True,
            "adapter_reason": "GO formula paths require the pinned GO calculation engine",
            "go_import_version": GO_IMPORT_VERSION,
            "character": character,
            "build_name": name,
            "targets": targets,
            "theorycraft_build": build,
            "opt_config": opt_config,
            "source_path": str(source_path),
        }
        scenarios.append(
            Scenario(
                id=scenario_id,
                tier="current",
                objective=objective,  # type: ignore[arg-type]
                scaling_stat=_scaling_stat(build),  # type: ignore[arg-type]
                damage_stat=_damage_stat(build),
                constraints=_constraints(opt_config),
                required_sets=_set_requirements(build),
                allowed_main_stats=_allowed_mains(opt_config),
                source="genshin-optimizer",
                metadata=metadata,
            )
        )
    return scenarios


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
