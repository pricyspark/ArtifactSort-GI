"""Prepare frozen quantile profiles and run both independent deletion selections."""

from __future__ import annotations

from dataclasses import dataclass
import math
from time import monotonic
from typing import Iterable, Mapping, cast

from .artifact_sampling import SamplingRules, sample_completed_inventory
from .cache import ResultCache, cache_key
from .formulas import Json
from .inventory import Inventory
from .library_deletion import (
    CoverageGap,
    DeletionSelection,
    build_targets,
    select_deletions,
)
from .library_runtime import CompiledLibrary
from .library_cache import AnalysisCache
from .reference_contexts import generate_reference_contexts
from .reference_profiles import ReferenceProfiles, generate_reference_profiles

ANALYSIS_VERSION = "encoded-deletion-4"


@dataclass(frozen=True, slots=True)
class LibraryDeletionAnalysis:
    selections: Mapping[str, DeletionSelection]
    profiles: Mapping[str, ReferenceProfiles]
    context_statuses: Mapping[str, tuple[str, str]]
    draft: bool
    sampling_fingerprint: str


def deletion_report(
    inventory: Inventory,
    library: CompiledLibrary,
    rules: SamplingRules,
    free: int,
    *,
    pinned_ids: Iterable[str] = (),
    trial_count: int = 16,
    population_size: int = 1000,
    max_evaluations: int = 100_000,
    time_limit: float = 180,
    seed: int = 0,
    cache: ResultCache | None = None,
    reuse: bool = True,
) -> dict[str, Json]:
    """Shared CLI/GUI report cache, including every numerical input and budget."""
    pinned = tuple(pinned_ids)
    key = cache_key(
        artifact_fingerprint=inventory.fingerprint(),
        scenario_hash=library.fingerprint,
        evaluator_version=ANALYSIS_VERSION,
        parameters={
            "free": free,
            "pins": sorted(pinned),
            "sampling": rules.fingerprint,
            "seed": seed,
            "trials": trial_count,
            "population": population_size,
            "max_evaluations": max_evaluations,
            "time_limit": time_limit,
        },
    )
    cached = None if cache is None or not reuse else cache.get("encoded-deletion", key)
    if (
        isinstance(cached, dict)
        and cached.get("kind") == "library-deletion-diagnostics"
    ):
        result = cast(dict[str, Json], cached)
        return {
            **result,
            "cacheStatus": "hit",
            "cacheStatistics": {"reportHit": True, "intermediate": {}},
        }
    intermediates = AnalysisCache(cache) if reuse else None
    analysis = analyze_deletions(
        inventory,
        library,
        rules,
        free,
        pinned_ids=pinned,
        trial_count=trial_count,
        population_size=population_size,
        max_evaluations=max_evaluations,
        time_limit=time_limit,
        seed=seed,
        cache=intermediates,
    )
    payload = analysis_payload(analysis)
    payload.update(
        inventoryFingerprint=inventory.fingerprint(),
        libraryFingerprint=library.fingerprint,
        formulaValidation={
            "draft": library.draft,
            "limitations": list(library.limitations),
        },
        cacheStatus="disabled" if cache is None or not reuse else "miss",
        cacheStatistics={
            "reportHit": False,
            "intermediate": {} if intermediates is None else intermediates.summary(),
        },
        computation={
            "trialCount": trial_count,
            "populationSize": population_size,
            "maxEvaluations": max_evaluations,
            "timeLimit": time_limit,
            "seed": seed,
        },
    )
    if (
        cache is not None
        and reuse
        and all(
            selection.status in ("exact", "pool_relative")
            for selection in analysis.selections.values()
        )
    ):
        cache.put("encoded-deletion", key, payload)
    return payload


def analyze_deletions(
    inventory: Inventory,
    library: CompiledLibrary,
    rules: SamplingRules,
    free: int,
    *,
    pinned_ids: Iterable[str] = (),
    trial_count: int = 16,
    population_size: int = 1000,
    max_evaluations: int = 100_000,
    time_limit: float = 180,
    seed: int = 0,
    cache: AnalysisCache | None = None,
) -> LibraryDeletionAnalysis:
    """Prepare once; established/combined runs share gear, trials, and profiles.

    Draft inputs permit diagnostic candidate lists, not validated preservation
    claims. Unknown model coverage blocks the affected selection. Unsupported
    upgrade states currently block both runs: protecting just that identity
    would not bound its interactions with other candidates.
    """
    if type(trial_count) is not int or trial_count <= 0:
        raise ValueError("trial_count must be a positive integer")
    if type(population_size) is not int or population_size <= 0:
        raise ValueError("population_size must be a positive integer")
    if not math.isfinite(time_limit) or time_limit <= 0:
        raise ValueError("time_limit must be finite and positive")
    if type(free) is not int or not 0 <= free <= len(inventory.artifacts):
        raise ValueError("free must be within the inventory size")
    pinned = tuple(pinned_ids)
    inventory.protected_ids(pinned)
    deadline = monotonic() + time_limit
    scenarios = library.select(include_speculative=True)
    profiles = {}
    context_statuses = {}
    scenario_gaps: dict[str, list[CoverageGap]] = {}
    global_gaps = []
    trials = []
    try:
        for index in range(trial_count):
            if monotonic() >= deadline:
                raise TimeoutError("upgrade sampling did not finish")
            trials.append(
                (
                    sample_completed_inventory
                    if cache is None
                    else cache.completed_inventory
                )(inventory, rules, seed=seed, trial=index)
            )
    except (ValueError, TimeoutError) as error:
        global_gaps.append(CoverageGap(f"future model: {error}"))
    if not global_gaps:
        for index, scenario in enumerate(scenarios):
            identity = scenario.definition.id
            if not scenario.definition.family:
                scenario_gaps[identity] = [
                    CoverageGap(f"{identity}: missing character-and-role family")
                ]
                continue
            remaining = deadline - monotonic()
            if remaining <= 0:
                scenario_gaps[identity] = [
                    CoverageGap(f"{identity}: profile preparation timed out")
                ]
                continue
            # Budget shares reserve time for both independent selection runs.
            share = remaining / (len(scenarios) - index + 2)
            try:
                contexts = generate_reference_contexts(
                    inventory,
                    scenario,
                    rules,
                    time_limit=share / 2,
                    max_evaluations=max_evaluations,
                    seed=seed,
                    cache=cache,
                )
                context_statuses[identity] = (
                    contexts.inventory_search.status,
                    contexts.hypothetical_search.status,
                )
                if not contexts.contexts:
                    raise ValueError("no qualifying reference context was found")
                profiles[identity] = generate_reference_profiles(
                    contexts,
                    rules,
                    population_size=population_size,
                    time_limit=share / 2,
                    seed=seed,
                    cache=cache,
                )
            except (ValueError, TimeoutError) as error:
                scenario_gaps[identity] = [CoverageGap(f"{identity}: {error}")]
    selections = {}
    scopes = {"established": library.select(), "combined": scenarios}
    for index, (scope, selected) in enumerate(scopes.items()):
        gaps = global_gaps + [
            gap
            for scenario in selected
            for gap in scenario_gaps.get(scenario.definition.id, ())
        ]
        remaining = deadline - monotonic()
        if gaps or not selected:
            if not selected:
                gaps.append(CoverageGap("no selected scenarios"))
            selections[scope] = DeletionSelection(
                (), "blocked", None, tuple(gaps), 0, 0, False
            )
        elif remaining <= 0:
            selections[scope] = DeletionSelection(
                (), "timed_out", None, (), 0, 0, False
            )
        else:
            targets = build_targets(
                inventory,
                selected,
                tuple(trials),
                {key: value.profiles for key, value in profiles.items()},
            )
            selections[scope] = select_deletions(
                inventory,
                targets,
                free,
                pinned_ids=pinned,
                max_evaluations=max_evaluations,
                time_limit=remaining / (len(scopes) - index),
                seed=seed,
                cache=cache,
            )
    return LibraryDeletionAnalysis(
        selections,
        profiles,
        context_statuses,
        library.draft or not rules.validated,
        rules.fingerprint,
    )


def analysis_payload(analysis: LibraryDeletionAnalysis) -> dict[str, Json]:
    """JSON-safe diagnostic evidence; infinities are explicit interval endpoints."""
    selections: dict[str, Json] = {}
    for scope, selection in analysis.selections.items():
        objective = selection.objective
        selections[scope] = {
            "status": selection.status,
            "deletedArtifactIds": list(selection.deleted_ids),
            "worstLoss": None if objective is None else objective.worst_loss,
            "familyAverage": None if objective is None else objective.family_average,
            "exceptionalWorstLoss": (
                None if objective is None else objective.exceptional_worst_loss
            ),
            "searchExact": selection.search_exact,
            "removalSetsChecked": selection.checked,
            "refinements": selection.refinements,
            "gaps": [
                {
                    "reason": gap.reason,
                    "affectedArtifactIds": (
                        None
                        if gap.affected_ids is None
                        else cast(Json, sorted(gap.affected_ids))
                    ),
                }
                for gap in selection.gaps
            ],
            "targets": (
                []
                if objective is None
                else [
                    {
                        "id": value.target.id,
                        "family": value.target.family,
                        "category": value.target.category,
                        "baseline": value.target.baseline,
                        "retained": value.target.retained,
                        "relativeLoss": value.loss,
                        "gap": value.gap,
                    }
                    for value in objective.targets
                ]
            ),
            "excludedTargets": [
                {
                    "target": value.target,
                    "scenarioIds": list(value.scenarios),
                    "family": value.family,
                    "category": value.category,
                    "baseline": value.baseline,
                    "reason": value.reason,
                }
                for value in selection.excluded
            ],
            "qualification": [
                {
                    "target": value.target,
                    "baseline": value.baseline,
                    "retained": value.retained,
                }
                for value in selection.qualification
            ],
        }
    profiles: dict[str, Json] = {}
    for identity, profile in analysis.profiles.items():
        profiles[identity] = {
            "contextSearchStatus": list(analysis.context_statuses[identity]),
            "quantiles": [
                {
                    "source": value.source,
                    "context": value.context,
                    "slot": value.slot,
                    "category": value.category,
                    "percentile": value.percentile,
                    "score": value.score,
                    "percentileInterval": list(value.percentile_interval),
                    "confidenceInterval": [
                        (
                            number
                            if math.isfinite(number)
                            else "-infinity" if number < 0 else "+infinity"
                        )
                        for number in value.confidence_interval
                    ],
                    "confidenceLevel": 0.95,
                    "ties": value.ties,
                }
                for value in profile.evidence
            ],
        }
    return {
        "kind": "library-deletion-diagnostics",
        "analysisVersion": ANALYSIS_VERSION,
        "draft": analysis.draft,
        "samplingFingerprint": analysis.sampling_fingerprint,
        "coverage": "selected scenarios only; not a declaration of complete role coverage",
        "selections": selections,
        "profiles": profiles,
    }
