from __future__ import annotations

from dataclasses import dataclass, replace
from hashlib import sha256
import json
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Mapping, Protocol, cast

import numpy as np

from ..cache import ResultCache, cache_key
from ..model import ArtifactBatch, SLOT_KEYS, STAT_KEYS, SUBSTAT_MAX, from_good_data
from ..optimizer import BuildOptimizer, DeletionAnalyzer
from ..scenarios import (
    BuiltinEvaluator,
    Scenario,
    generic_scenarios,
    scenario_to_mapping,
)
from ..sources import GOImportResult, import_go_database
from ..upgrades import UpgradeAnalyzer
from ..formulas import Json

API_VERSION = 1


class ProgressReporter(Protocol):
    def __call__(self, progress: float, message: str) -> None: ...


class AnalysisBackend(Protocol):
    """Stable boundary between the web application and analysis implementation."""

    def import_files(
        self,
        inventory: Mapping[str, Any],
        inventory_name: str,
        go_database: Mapping[str, Any] | None = None,
        go_name: str | None = None,
    ) -> "ImportedAccount": ...

    def overview(self, account: "ImportedAccount") -> Mapping[str, Any]: ...

    def cleanup(
        self, account: "ImportedAccount", free: int, progress: ProgressReporter
    ) -> Mapping[str, Any]: ...

    def upgrades(
        self, account: "ImportedAccount", progress: ProgressReporter
    ) -> Mapping[str, Any]: ...

    def library_cleanup(
        self,
        account: "ImportedAccount",
        payload: Mapping[str, Any],
        progress: ProgressReporter,
    ) -> Mapping[str, Any]: ...


@dataclass(frozen=True, slots=True)
class ImportedAccount:
    batch: ArtifactBatch
    source_data: Mapping[str, Any]
    inventory_name: str
    scenarios: tuple[Scenario, ...]
    warnings: tuple[str, ...]
    profile: Mapping[str, Any] | None


_LABELS = {
    "hp": "HP",
    "atk": "ATK",
    "def": "DEF",
    "hp_": "HP%",
    "atk_": "ATK%",
    "def_": "DEF%",
    "enerRech_": "Energy Recharge",
    "eleMas": "Elemental Mastery",
    "critRate_": "CRIT Rate",
    "critDMG_": "CRIT DMG",
    "heal_": "Healing Bonus",
}


def _humanize(value: str) -> str:
    if value in _LABELS:
        return _LABELS[value]
    text = value.removesuffix("_").replace("_", " ")
    words: list[str] = []
    start = 0
    for index in range(1, len(text)):
        if text[index].isupper() and text[index - 1].islower():
            words.append(text[start:index])
            start = index
    words.append(text[start:])
    return " ".join(words).title()


def _artifact_view(batch: ArtifactBatch, index: int) -> dict[str, Any]:
    substats = []
    for stat_index, coefficient in enumerate(batch.sub_rolls[index]):
        if coefficient:
            raw_value = float(coefficient) * float(SUBSTAT_MAX[stat_index]) / 10.0
            substats.append(
                {
                    "key": STAT_KEYS[stat_index],
                    "label": _humanize(STAT_KEYS[stat_index]),
                    "rolls": round(float(coefficient) / 10.0, 1),
                    "value": round(raw_value, 1),
                    "percentage": stat_index in {3, 4, 5, 6, 8, 9},
                }
            )
    return {
        "id": str(batch.ids[index]),
        "index": index,
        "set": str(batch.set_keys[index]),
        "setLabel": _humanize(str(batch.set_keys[index])),
        "slot": SLOT_KEYS[int(batch.slots[index])],
        "slotLabel": _humanize(SLOT_KEYS[int(batch.slots[index])]),
        "mainStat": STAT_KEYS[int(batch.main_stats[index])],
        "mainStatLabel": _humanize(STAT_KEYS[int(batch.main_stats[index])]),
        "rarity": int(batch.rarities[index]),
        "level": int(batch.levels[index]),
        "location": str(batch.locations[index]),
        "locked": bool(batch.locked[index]),
        "marked": bool(batch.starred[index]),
        "substats": substats,
    }


def _screening_proxy(scenario: Scenario) -> Scenario:
    """Retain GO constraints while explicitly dropping its unavailable formula."""

    metadata = {
        key: value
        for key, value in scenario.metadata.items()
        if key not in {"adapter_required", "adapter_reason", "source_path"}
    }
    metadata["screening_proxy"] = True
    return replace(scenario, source="gui-go-screening-proxy", metadata=metadata)


def _scenario_hash(scenarios: tuple[Scenario, ...]) -> str:
    payload = [scenario_to_mapping(scenario) for scenario in scenarios]
    encoded = json.dumps(payload, sort_keys=True, default=str).encode()
    return sha256(encoded).hexdigest()


def _profile_from_go(result: GOImportResult, name: str) -> dict[str, Any]:
    counts = result.database.get("counts", {})
    set_informed = sum(
        bool(scenario.set_strategies or scenario.required_sets)
        for scenario in result.scenarios
    )
    return {
        "name": name,
        "accountName": (
            result.database.get("dbMeta", {}).get("name", "Account")
            if isinstance(result.database.get("dbMeta"), Mapping)
            else "Account"
        ),
        "teams": int(counts.get("teams", 0)) if isinstance(counts, Mapping) else 0,
        "targets": len(result.scenarios),
        "setInformedTargets": set_informed,
        "skipped": len(result.skipped),
    }


def _normalize_inventory(raw: Mapping[str, Any]) -> Mapping[str, Any]:
    """Remove exporter placeholders without relaxing the engine's GOOD parser."""

    artifacts = raw.get("artifacts")
    if not isinstance(artifacts, list):
        return raw
    normalized = dict(raw)
    normalized_artifacts = []
    for item in artifacts:
        if not isinstance(item, Mapping):
            normalized_artifacts.append(item)
            continue
        artifact = dict(item)
        for field in ("substats", "unactivatedSubstats"):
            values = artifact.get(field)
            if isinstance(values, list):
                artifact[field] = [
                    value
                    for value in values
                    if not isinstance(value, Mapping) or value.get("key")
                ]
        normalized_artifacts.append(artifact)
    normalized["artifacts"] = normalized_artifacts
    return normalized


def _artifact_signature(artifact: Mapping[str, Any]) -> tuple[object, ...] | None:
    identity = tuple(
        artifact.get(key)
        for key in ("setKey", "slotKey", "mainStatKey", "rarity", "level")
    )
    if any(value is None for value in identity[:3]):
        return None

    def stats(field: str) -> tuple[tuple[str, float], ...]:
        values = artifact.get(field)
        if not isinstance(values, list):
            return ()
        return tuple(
            sorted(
                (str(value["key"]), round(float(value.get("value", 0.0)), 2))
                for value in values
                if isinstance(value, Mapping) and value.get("key")
            )
        )

    return (*identity, stats("substats"), stats("unactivatedSubstats"))


class PortfolioBackend:
    """Adapter for the current portfolio engine; web code never imports engine types."""

    def __init__(self, cache_path: str | Path = ".artifact-sort/gui-cache.sqlite"):
        self.cache_path = Path(cache_path)

    def library_cleanup(
        self,
        account: ImportedAccount,
        payload: Mapping[str, Any],
        progress: ProgressReporter,
    ) -> Mapping[str, Any]:
        from ..artifact_sampling import sampling_rules
        from ..inventory import inventory_from_good
        from ..library import library_from_data, mechanics_from_data
        from ..library_analysis import deletion_report

        numerical, mechanics, research = (
            payload.get("library"),
            payload.get("mechanics"),
            payload.get("research"),
        )
        if not isinstance(numerical, Mapping) or not isinstance(mechanics, Mapping):
            raise ValueError("Choose a scenario library and its mechanics manifest")
        if research is not None and not isinstance(research, Mapping):
            raise ValueError("The research sidecar must be a JSON object")
        allow_draft = payload.get("allowDraft", False)
        if type(allow_draft) is not bool:
            raise ValueError("allowDraft must be a boolean")
        reuse = payload.get("reuse", True)
        if type(reuse) is not bool:
            raise ValueError("reuse must be a boolean")
        progress(0.02, "Loading the authored scenario library")
        library = library_from_data(
            cast(Mapping[str, Json], numerical),
            research=cast(Mapping[str, Json] | None, research),
        ).compile(
            mechanics_from_data(cast(Mapping[str, Json], mechanics)),
            allow_draft=allow_draft,
        )
        inventory = inventory_from_good(cast(Mapping[str, Json], account.source_data))
        progress(0.05, "Evaluating shared reference profiles and joint deletion sets")
        settings = {}
        for name, default in (
            ("free", 100),
            ("trials", 16),
            ("population", 1000),
            ("maxEvaluations", 100_000),
        ):
            value = payload.get(name, default)
            if type(value) is not int:
                raise ValueError(f"{name} must be an integer")
            settings[name] = value
        result = deletion_report(
            inventory,
            library,
            sampling_rules(),
            settings["free"],
            trial_count=settings["trials"],
            population_size=settings["population"],
            max_evaluations=settings["maxEvaluations"],
            time_limit=float(payload.get("timeLimit", 180)),
            cache=ResultCache(self.cache_path),
            reuse=reuse,
        )
        views = []
        for index, artifact in enumerate(inventory.artifacts):
            view = _artifact_view(account.batch, index)
            view["id"] = artifact.id
            view["substats"] = [
                {
                    "key": key,
                    "label": _humanize(key),
                    "value": value * 100 if key.endswith("_") else value,
                    "percentage": key.endswith("_"),
                }
                for key, value in artifact.substats.items()
            ]
            views.append(view)
        progress(0.99, "Preparing both independent review lists")
        return {**result, "artifactViews": views}

    def _load_go(self, raw: Mapping[str, Any]) -> GOImportResult:
        # The existing importer accepts paths. Keeping that detail here prevents it
        # from becoming part of the GUI contract and makes replacing it trivial.
        with NamedTemporaryFile(mode="w", suffix=".json", encoding="utf-8") as handle:
            json.dump(raw, handle)
            handle.flush()
            return import_go_database(handle.name)

    def import_files(
        self,
        inventory: Mapping[str, Any],
        inventory_name: str,
        go_database: Mapping[str, Any] | None = None,
        go_name: str | None = None,
    ) -> ImportedAccount:
        normalized_inventory = _normalize_inventory(inventory)
        batch = from_good_data(normalized_inventory)
        warnings: list[str] = []
        profile = None
        if go_database is not None:
            imported = self._load_go(go_database)
            scenarios = tuple(_screening_proxy(item) for item in imported.scenarios)
            profile = _profile_from_go(imported, go_name or "GO database")
            warnings.append(
                "Your GO teams and build preferences were imported successfully. "
                "Artifact Sort can use their saved set choices, main-stat filters, "
                "and stat minimums, but it cannot reproduce GO's exact character "
                "damage calculations by itself. Results are therefore useful "
                "estimates and may rank close artifacts differently from GO. You do "
                "not need to configure anything to continue."
            )
            set_informed = int(profile["setInformedTargets"])
            if set_informed:
                warnings.append(
                    f"Set strategies for {set_informed} of {len(scenarios)} targets "
                    "were taken from GO's saved optimizer results or explicit "
                    "theorycraft settings. Re-run GO optimization before exporting "
                    "when those results are outdated."
                )
            else:
                warnings.append(
                    "This GO database has no saved optimizer results or explicit "
                    "theorycraft set strategies. Set bonuses cannot be inferred for "
                    "these targets."
                )
        else:
            scenarios = tuple(generic_scenarios())
            warnings.append(
                "Using broad account coverage. Add a GO database to focus analysis on "
                "your configured teams."
            )
        return ImportedAccount(
            batch=batch,
            source_data=normalized_inventory,
            inventory_name=inventory_name,
            scenarios=scenarios,
            warnings=tuple(warnings),
            profile=profile,
        )

    def overview(self, account: ImportedAccount) -> Mapping[str, Any]:
        batch = account.batch
        set_counts: dict[str, int] = {}
        slot_counts = {slot: 0 for slot in SLOT_KEYS}
        for set_key, slot_index in zip(batch.set_keys, batch.slots):
            label = _humanize(str(set_key))
            set_counts[label] = set_counts.get(label, 0) + 1
            slot_counts[SLOT_KEYS[int(slot_index)]] += 1
        protected = batch.protected_mask(self._reference_artifact_ids(account))
        source = str(account.source_data.get("source") or "GOOD v3")
        payload = {
            "apiVersion": API_VERSION,
            "inventory": {
                "name": account.inventory_name,
                "source": source,
                "total": len(batch),
                "fiveStar": int(np.count_nonzero(batch.rarities == 5)),
                "maxed": int(np.count_nonzero(batch.levels == 20)),
                "unfinished": int(np.count_nonzero(batch.levels < 20)),
                "equipped": int(np.count_nonzero(batch.locations != "")),
                "marked": int(np.count_nonzero(batch.starred)),
                "protected": int(np.count_nonzero(protected)),
                "availableToClean": int(np.count_nonzero(~protected)),
                "sets": len(set_counts),
                "topSets": [
                    {"name": name, "count": count}
                    for name, count in sorted(
                        set_counts.items(), key=lambda item: item[1], reverse=True
                    )[:6]
                ],
                "slots": [
                    {"key": key, "label": _humanize(key), "count": count}
                    for key, count in slot_counts.items()
                ],
            },
            "profile": account.profile,
            "coverage": {
                "scenarioCount": len(account.scenarios),
                "mode": "go-proxy" if account.profile else "broad",
            },
            "warnings": list(account.warnings),
        }
        return payload

    @staticmethod
    def _reference_artifact_ids(account: ImportedAccount) -> set[str]:
        direct = {
            str(artifact_id)
            for scenario in account.scenarios
            for artifact_id in scenario.metadata.get("reference_artifact_ids", ())
        }
        inventory_ids = {str(artifact_id) for artifact_id in account.batch.ids}
        result = direct & inventory_ids
        reference_signatures = {
            signature
            for scenario in account.scenarios
            for artifact in scenario.metadata.get("reference_artifacts", ())
            if isinstance(artifact, Mapping)
            if (signature := _artifact_signature(artifact)) is not None
        }
        raw_artifacts = account.source_data.get("artifacts")
        if isinstance(raw_artifacts, list) and reference_signatures:
            for index, artifact in enumerate(raw_artifacts):
                if (
                    isinstance(artifact, Mapping)
                    and _artifact_signature(artifact) in reference_signatures
                ):
                    result.add(str(account.batch.ids[index]))
        return result

    @staticmethod
    def _viable_scenarios(
        optimizer: BuildOptimizer,
        scenarios: tuple[Scenario, ...],
        progress: ProgressReporter | None = None,
    ) -> tuple[tuple[Scenario, ...], int]:
        viable: list[Scenario] = []
        scenario_count = len(scenarios)
        for scenario_number, scenario in enumerate(scenarios, start=1):
            if optimizer.optimize(scenario, top_k=1):
                viable.append(scenario)
            if progress is not None:
                progress(
                    scenario_number / scenario_count,
                    f"Checked target {scenario_number} of {scenario_count}",
                )
        if not viable:
            raise ValueError(
                "No complete five-artifact build matches the current account targets"
            )
        return tuple(viable), len(scenarios) - len(viable)

    def cleanup(
        self, account: ImportedAccount, free: int, progress: ProgressReporter
    ) -> Mapping[str, Any]:
        reference_ids = self._reference_artifact_ids(account)
        available = int(np.count_nonzero(~account.batch.protected_mask(reference_ids)))
        if not 1 <= free <= available:
            raise ValueError(f"Choose between 1 and {available} artifacts to clear")
        progress(0.04, "Checking for a previous result")
        cache = ResultCache(self.cache_path)
        evaluator = BuiltinEvaluator()
        result_key = cache_key(
            artifact_fingerprint=account.batch.fingerprint(),
            scenario_hash=_scenario_hash(account.scenarios),
            evaluator_version=evaluator.version,
            parameters={
                "kind": "gui-cleanup",
                "result_version": 3,
                "free": free,
                "candidate_limit": 36,
                "beam_width": 6000,
                "upgrade_candidates": 32,
                "upgrade_pool": 100,
                "loadouts": 80,
            },
        )
        cached = cache.get("gui-cleanup", result_key)
        if isinstance(cached, Mapping) and cached.get("apiVersion") == API_VERSION:
            payload = dict(cached)
            payload["summary"] = {**dict(payload["summary"]), "cacheStatus": "hit"}
            progress(0.99, "Loaded your previous cleanup analysis")
            return payload

        progress(0.08, "Preparing your account targets")
        optimizer = BuildOptimizer(
            account.batch,
            evaluator,
            candidate_limit=36,
            beam_width=6000,
            cache=cache,
        )
        progress(0.16, "Checking which account targets are ready")
        scenarios, skipped = self._viable_scenarios(
            optimizer,
            account.scenarios,
            lambda value, message: progress(0.16 + 0.09 * value, message),
        )
        progress(0.25, "Protecting promising unfinished artifacts")
        upgrade_results = UpgradeAnalyzer(
            optimizer, scenarios, complement_pool_size=100
        ).analyze(
            max_candidates=32,
            progress=lambda value, message: progress(0.25 + 0.33 * value, message),
        )
        option_values = np.zeros(len(account.batch), dtype=np.float64)
        upgrade_by_index = {item.index: item for item in upgrade_results}
        for item in upgrade_results:
            protection = 1.0 if item.protected_at_probability_floor else 0.0
            option_values[item.index] = (
                protection + item.useful_probability + item.expected_relative_gain
            )
        progress(0.58, "Comparing complete builds")
        result = DeletionAnalyzer(
            optimizer, scenarios, loadouts_per_scenario=80
        ).analyze(
            free,
            pinned_ids=reference_ids,
            option_values=option_values,
            progress=lambda value, message: progress(0.58 + 0.36 * value, message),
        )
        progress(0.94, "Preparing your review list")
        retained = np.ones(len(account.batch), dtype=np.bool_)
        retained[np.asarray(result.deleted_indices, dtype=np.int64)] = False
        top_build_use = {
            index: sum(index in regret.baseline_build for regret in result.regrets)
            for index in result.deleted_indices
        }
        artifacts = []
        for index in result.deleted_indices:
            view = _artifact_view(account.batch, index)
            same_role = (
                retained
                & (account.batch.slots == account.batch.slots[index])
                & (account.batch.main_stats == account.batch.main_stats[index])
                & (account.batch.set_keys == account.batch.set_keys[index])
            )
            upgrade = upgrade_by_index.get(index)
            used_by = top_build_use[index]
            alternatives = int(np.count_nonzero(same_role))
            reasons = []
            if used_by == 0:
                reasons.append("Not used in any top account build")
            else:
                reasons.append("Its role is covered by a retained build")
            if int(account.batch.levels[index]) < 20:
                if upgrade is None:
                    reasons.append(
                        "Not shortlisted among the 32 strongest upgrade candidates"
                    )
                else:
                    reasons.append(
                        f"{upgrade.useful_probability:.1%} estimated useful-roll chance"
                    )
            if alternatives:
                reasons.append(
                    f"{alternatives} same-set, same-slot alternatives remain"
                )
            view["evidence"] = {
                "topBuildUse": used_by,
                "targetCount": len(result.regrets),
                "usefulChance": (
                    upgrade.useful_probability if upgrade is not None else None
                ),
                "expectedGain": (
                    upgrade.expected_relative_gain if upgrade is not None else None
                ),
                "upgradeShortlisted": upgrade is not None,
                "alternatives": alternatives,
                "investedExp": int(account.batch.invested_exp[index]),
                "reasons": reasons,
            }
            artifacts.append(view)
        artifacts.sort(
            key=lambda item: (
                int(item["evidence"]["topBuildUse"]),
                float(item["evidence"]["usefulChance"] or 0.0),
                float(item["evidence"]["expectedGain"] or 0.0),
                int(item["evidence"]["investedExp"]),
                -int(item["evidence"]["alternatives"]),
                int(item["index"]),
            )
        )
        for rank, artifact in enumerate(artifacts, start=1):
            artifact["reviewOrder"] = rank
        worst_regret = max((item.regret for item in result.regrets), default=0.0)
        payload = {
            "apiVersion": API_VERSION,
            "kind": "cleanup",
            "summary": {
                "count": len(artifacts),
                "protected": int(
                    np.count_nonzero(account.batch.protected_mask(reference_ids))
                ),
                "worstEstimatedLoss": worst_regret,
                "verified": result.verified,
                "status": "review-required",
                "cacheStatus": "computed",
                "orderExplanation": (
                    "Safest-looking artifacts appear first, using top-build use, "
                    "upgrade potential, invested EXP, and retained alternatives. The "
                    "analysis still selects the cleanup list as one complete set."
                ),
            },
            "artifacts": artifacts,
            "warnings": [
                *account.warnings,
                *(
                    [
                        f"Skipped {skipped} account targets that have no legal completed build."
                    ]
                    if skipped
                    else []
                ),
                (
                    "This is an unvalidated analysis list. Review artifacts in-game "
                    "before destroying them."
                ),
            ],
        }
        cache.put("gui-cleanup", result_key, payload)
        return payload

    def upgrades(
        self, account: ImportedAccount, progress: ProgressReporter
    ) -> Mapping[str, Any]:
        progress(0.04, "Checking for a previous result")
        cache = ResultCache(self.cache_path)
        evaluator = BuiltinEvaluator()
        result_key = cache_key(
            artifact_fingerprint=account.batch.fingerprint(),
            scenario_hash=_scenario_hash(account.scenarios),
            evaluator_version=evaluator.version,
            parameters={
                "kind": "gui-upgrades",
                "result_version": 2,
                "candidate_limit": 32,
                "beam_width": 4000,
                "max_candidates": 24,
                "complement_pool": 160,
            },
        )
        cached = cache.get("gui-upgrades", result_key)
        if isinstance(cached, Mapping) and cached.get("apiVersion") == API_VERSION:
            payload = dict(cached)
            payload["summary"] = {**dict(payload["summary"]), "cacheStatus": "hit"}
            progress(0.99, "Loaded your previous upgrade analysis")
            return payload

        progress(0.1, "Preparing your account targets")
        optimizer = BuildOptimizer(
            account.batch,
            evaluator,
            candidate_limit=32,
            beam_width=4000,
            cache=cache,
        )
        scenarios, skipped = self._viable_scenarios(
            optimizer,
            account.scenarios,
            lambda value, message: progress(0.1 + 0.15 * value, message),
        )
        progress(0.25, "Testing possible upgrade rolls")
        recommendations = UpgradeAnalyzer(
            optimizer, scenarios, complement_pool_size=160
        ).analyze(
            max_candidates=24,
            progress=lambda value, message: progress(0.25 + 0.67 * value, message),
        )
        progress(0.92, "Ranking the best opportunities")
        items = []
        for recommendation in recommendations:
            view = _artifact_view(account.batch, recommendation.index)
            view.update(
                {
                    "currentLevel": recommendation.level,
                    "nextLevel": recommendation.next_checkpoint,
                    "expCost": recommendation.incremental_exp,
                    "expectedGain": recommendation.expected_relative_gain,
                    "usefulChance": recommendation.useful_probability,
                    "worthTrying": recommendation.protected_at_probability_floor,
                }
            )
            items.append(view)
        payload = {
            "apiVersion": API_VERSION,
            "kind": "upgrades",
            "summary": {
                "count": len(items),
                "worthTrying": sum(bool(item["worthTrying"]) for item in items),
                "cacheStatus": "computed",
            },
            "artifacts": items,
            "warnings": [
                *account.warnings,
                *(
                    [
                        f"Skipped {skipped} account targets that have no legal completed build."
                    ]
                    if skipped
                    else []
                ),
            ],
        }
        cache.put("gui-upgrades", result_key, payload)
        return payload
