"""Joint deletion over frozen encoded-formula build trials.

Exhaustive removal search is the small-case oracle. The MILP optimizes a build
pool, then re-searches retained gear and adds omitted alternatives. Neither
sampled futures nor a pool-relative optimum certify game coverage.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
import math
from time import monotonic
from typing import TYPE_CHECKING, Iterable, Literal, Mapping, Sequence

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import lil_matrix

from .deletion_objective import (
    Category,
    DeletionObjective,
    TargetPerformance,
    summarize_losses,
)
from .inventory import MAIN_STATS, Inventory
from .library_runtime import CompiledScenario
from .library_search import REAL_SLOT_PATTERNS, search_builds

if TYPE_CHECKING:
    from .library_cache import AnalysisCache

SelectionStatus = Literal[
    "exact", "pool_relative", "timed_out", "infeasible", "blocked"
]


@dataclass(frozen=True, slots=True)
class BuildTrial:
    scenario: CompiledScenario
    candidates: tuple[Inventory, ...]


@dataclass(frozen=True, slots=True)
class BuildTarget:
    id: str
    family: str
    category: Category
    trials: tuple[BuildTrial, ...]


@dataclass(frozen=True, slots=True)
class CoverageGap:
    reason: str
    affected_ids: frozenset[str] | None = None


@dataclass(frozen=True, slots=True)
class BuildAlternative:
    real_ids: frozenset[str]
    score: float


@dataclass(frozen=True, slots=True)
class TargetQualification:
    target: str
    baseline: float
    retained: float


@dataclass(frozen=True, slots=True)
class ExcludedTarget:
    target: str
    scenarios: tuple[str, ...]
    family: str
    category: Category
    baseline: float
    reason: str = "nonpositive_baseline"


@dataclass(frozen=True, slots=True)
class DeletionSelection:
    deleted_ids: tuple[str, ...]
    status: SelectionStatus
    objective: DeletionObjective | None
    gaps: tuple[CoverageGap, ...]
    checked: int
    refinements: int
    search_exact: bool
    qualification: tuple[TargetQualification, ...] = ()
    excluded: tuple[ExcludedTarget, ...] = ()


def build_targets(
    inventory: Inventory,
    scenarios: Sequence[CompiledScenario],
    completed_trials: Sequence[Inventory],
    profiles: Mapping[str, Mapping[Category, Sequence[Inventory]]],
) -> tuple[BuildTarget, ...]:
    """Assemble current and 31-pattern future targets without resampling.

    Each trial searches alternative reference contexts separately and chooses
    the best result afterward. Pieces from unrelated contexts cannot be mixed
    into one stronger reference build. Call twice with independently selected
    established/combined scenario lists, sharing the same frozen inputs.
    """
    if not completed_trials:
        raise ValueError("at least one coupled completed trial is required")
    identities = {
        a.id: (a.set_key, a.slot, a.main_stat, a.rarity) for a in inventory.artifacts
    }
    for trial in completed_trials:
        if {
            a.id: (a.set_key, a.slot, a.main_stat, a.rarity) for a in trial.artifacts
        } != identities:
            raise ValueError(
                "completed trials must preserve original identities and properties"
            )
    targets = []
    for scenario in scenarios:
        definition = scenario.definition
        if not definition.family:
            raise ValueError(f"{definition.id}: missing character-and-role family")
        targets.append(
            BuildTarget(
                f"{definition.id}/current",
                definition.family,
                "current",
                (BuildTrial(scenario, (inventory,)),),
            )
        )
        for category in ("ordinary", "strong", "exceptional"):
            contexts = profiles[definition.id][category]
            if not contexts:
                raise ValueError(f"{definition.id}/{category}: no reference contexts")
            for context in contexts:
                if any(a.id in identities for a in context.artifacts):
                    raise ValueError("real and reference identities must be disjoint")
            for pattern in REAL_SLOT_PATTERNS:
                trials = tuple(
                    BuildTrial(
                        scenario,
                        tuple(
                            Inventory(
                                tuple(a for a in outcome.artifacts if a.slot in pattern)
                                + tuple(
                                    a
                                    for a in context.artifacts
                                    if a.slot not in pattern
                                )
                            )
                            for context in contexts
                        ),
                    )
                    for outcome in completed_trials
                )
                suffix = ",".join(sorted(pattern))
                targets.append(
                    BuildTarget(
                        f"{definition.id}/{category}/{suffix}",
                        definition.family,
                        category,
                        trials,
                    )
                )
    return tuple(targets)


def select_deletions(
    inventory: Inventory,
    targets: Sequence[BuildTarget],
    free: int,
    *,
    pinned_ids: Iterable[str] = (),
    coverage_gaps: Sequence[CoverageGap] = (),
    method: Literal["auto", "exhaustive", "milp"] = "auto",
    max_removal_combinations: int = 10_000,
    max_evaluations: int = 100_000,
    builds_per_trial: int = 20,
    max_refinements: int = 5,
    time_limit: float = 180,
    seed: int = 0,
    cache: AnalysisCache | None = None,
) -> DeletionSelection:
    """Compare exact-count removal sets with identical contexts and trial tapes.

    Bounded unsupported gaps protect their affected pieces; unbounded gaps block
    selection. Proven nonpositive baselines are excluded and reported. Unknown
    baselines block rather than invent ratios.
    Approximate positive searches remain explicitly approximate. No-build search
    is a failure only when exhaustive over every candidate context in that trial.
    """
    if type(free) is not int or not 0 <= free <= len(inventory.artifacts):
        raise ValueError("free must be an integer within the inventory size")
    for budget in (max_removal_combinations, max_evaluations, builds_per_trial):
        if type(budget) is not int or budget <= 0:
            raise ValueError("search and pool sizes must be positive integers")
    if type(max_refinements) is not int or max_refinements < 0:
        raise ValueError("max_refinements must be a nonnegative integer")
    if not math.isfinite(time_limit) or time_limit <= 0:
        raise ValueError("time_limit must be finite and positive")
    if method not in ("auto", "exhaustive", "milp"):
        raise ValueError("unknown deletion selection method")
    if not targets or len({target.id for target in targets}) != len(targets):
        raise ValueError("targets must be nonempty and have unique identities")
    for target in targets:
        if (
            not target.family
            or not target.trials
            or (target.category == "current" and len(target.trials) != 1)
        ):
            raise ValueError(
                "targets need a family and trials; current targets need one trial"
            )
        if any(not trial.candidates for trial in target.trials):
            raise ValueError("each trial needs at least one frozen candidate context")
    identities = frozenset(a.id for a in inventory.artifacts)
    by_id = {a.id: a for a in inventory.artifacts}
    for target in targets:
        for trial in target.trials:
            for candidates in trial.candidates:
                if target.category == "current":
                    if any(
                        a.id not in by_id or a != by_id[a.id]
                        for a in candidates.artifacts
                    ):
                        raise ValueError(
                            "current targets require actual inventory pieces and stats"
                        )
                elif any(
                    a.level != len(MAIN_STATS[a.rarity][a.main_stat]) - 1
                    for a in candidates.artifacts
                ):
                    raise ValueError(
                        "future targets require completed outcomes and complements"
                    )
                if target.category != "current":
                    for artifact in candidates.artifacts:
                        original = by_id.get(artifact.id)
                        if original is None:
                            continue
                        if (
                            artifact.slot,
                            artifact.set_key,
                            artifact.main_stat,
                            artifact.rarity,
                        ) != (
                            original.slot,
                            original.set_key,
                            original.main_stat,
                            original.rarity,
                        ):
                            raise ValueError(
                                "future outcomes must preserve artifact identity and properties"
                            )
                        observed = {**original.substats, **original.hidden_substats}
                        if any(
                            key not in artifact.substats
                            or artifact.substats[key] < value
                            for key, value in observed.items()
                        ):
                            raise ValueError(
                                "future outcomes must preserve observed substats"
                            )
    excluded: tuple[ExcludedTarget, ...] = ()
    baseline_search = True
    target_exact: list[bool] = []
    protected = inventory.protected_ids(pinned_ids)
    gaps = list(coverage_gaps)
    for gap in gaps:
        if gap.affected_ids is not None:
            inventory.select(gap.affected_ids)
            protected |= gap.affected_ids
    if any(gap.affected_ids is None for gap in gaps):
        return DeletionSelection(
            (), "blocked", None, tuple(gaps), 0, 0, False, excluded=excluded
        )
    eligible = tuple(sorted(identities - protected))
    if free > len(eligible):
        return DeletionSelection(
            (), "infeasible", None, tuple(gaps), 0, 0, False, excluded=excluded
        )
    deadline = monotonic() + time_limit
    pools: list[list[dict[frozenset[str], BuildAlternative]]] = [
        [{} for _ in target.trials] for target in targets
    ]
    search_exact = True
    checked = 0

    def evaluate(available: frozenset[str]) -> tuple[list[float] | None, bool, bool]:
        nonlocal search_exact
        values = []
        current_feasible = True
        all_exact = True
        for target_index, target in enumerate(targets):
            scores = []
            target_is_exact = True
            for trial_index, trial in enumerate(target.trials):
                pool = pools[target_index][trial_index]
                exact = True
                found = False
                for candidates in trial.candidates:
                    remaining = deadline - monotonic()
                    if remaining <= 0:
                        return None, False, False
                    allowed = tuple(
                        a.id
                        for a in candidates.artifacts
                        if a.id not in identities or a.id in available
                    )
                    result = search_builds(
                        candidates,
                        trial.scenario,
                        available_ids=allowed,
                        top_k=builds_per_trial,
                        max_evaluations=max_evaluations,
                        time_limit=remaining,
                        seed=seed,
                        cache=cache,
                    )
                    exact &= result.status == "exact"
                    for build in result.builds:
                        found = True
                        if not baseline_search and build.evaluation.score < 0:
                            gaps.append(
                                CoverageGap(
                                    f"{target.id}: negative qualifying performance"
                                )
                            )
                            return None, False, False
                        real = frozenset(build.build.artifact_ids) & identities
                        alternative = BuildAlternative(real, build.evaluation.score)
                        previous = pool.get(real)
                        if previous is None or previous.score < alternative.score:
                            pool[real] = alternative
                search_exact &= exact
                all_exact &= exact
                target_is_exact &= exact
                surviving = [
                    build.score
                    for build in pool.values()
                    if build.real_ids <= available
                ]
                if not found and not exact and not surviving:
                    gaps.append(
                        CoverageGap(f"{target.id}: unresolved qualifying build search")
                    )
                    return None, False, False
                if target.category == "current" and not surviving:
                    current_feasible = False
                scores.append(max(surviving, default=0.0))
            values.append(math.fsum(scores) / len(scores))
            if baseline_search:
                target_exact.append(target_is_exact)
        return values, current_feasible, all_exact

    def objective(
        baselines: Sequence[float], values: Sequence[float]
    ) -> DeletionObjective:
        return summarize_losses(
            tuple(
                TargetPerformance(
                    target.id, target.family, target.category, baseline, retained
                )
                for target, baseline, retained in zip(targets, baselines, values)
            )
        )

    def rank(value: DeletionObjective) -> tuple[float, float, float]:
        assert value.worst_loss is not None and value.family_average is not None
        return (
            value.worst_loss,
            value.family_average,
            value.exceptional_worst_loss or 0.0,
        )

    def qualification(deleted: tuple[str, ...]) -> tuple[TargetQualification, ...]:
        available = identities - frozenset(deleted)
        return tuple(
            TargetQualification(
                target.id,
                sum(bool(pool) for pool in trials) / len(trials),
                sum(
                    any(build.real_ids <= available for build in pool.values())
                    for pool in trials
                )
                / len(trials),
            )
            for target, trials in zip(targets, pools)
        )

    baselines, feasible, exact = evaluate(identities)
    status: SelectionStatus
    if baselines is None:
        status = "timed_out" if monotonic() >= deadline else "blocked"
        return DeletionSelection(
            (), status, None, tuple(gaps), 0, 0, False, excluded=excluded
        )
    # An approximate empty/nonpositive search cannot establish absence.
    if any(
        baseline <= 0 and not proven
        for baseline, proven in zip(baselines, target_exact)
    ):
        gaps.append(
            CoverageGap("nonpositive baseline remains unresolved by approximate search")
        )
        return DeletionSelection(
            (), "blocked", None, tuple(gaps), 0, 0, search_exact, excluded=excluded
        )
    excluded = tuple(
        ExcludedTarget(
            target.id,
            tuple(sorted({trial.scenario.definition.id for trial in target.trials})),
            target.family,
            target.category,
            baseline,
        )
        for target, baseline in zip(targets, baselines)
        if baseline <= 0
    )
    active = [index for index, baseline in enumerate(baselines) if baseline > 0]
    targets = tuple(targets[index] for index in active)
    pools = [pools[index] for index in active]
    baselines = [baselines[index] for index in active]
    baseline_search = False
    if not any(target.category != "exceptional" for target in targets):
        gaps.append(CoverageGap("no measurable primary targets remain"))
        return DeletionSelection(
            (), "blocked", None, tuple(gaps), 0, 0, search_exact, excluded=excluded
        )
    # Signed future outcomes require a different MILP fallback formulation.
    if any(
        build.score < 0
        for trials in pools
        for pool in trials
        for build in pool.values()
    ):
        gaps.append(
            CoverageGap(
                "positive baseline includes unsupported negative qualifying performance"
            )
        )
        return DeletionSelection(
            (), "blocked", None, tuple(gaps), 0, 0, search_exact, excluded=excluded
        )
    if method == "auto":
        method = (
            "exhaustive"
            if math.comb(len(eligible), free) <= max_removal_combinations
            else "milp"
        )
    best: tuple[tuple[str, ...], DeletionObjective] | None = None
    if method == "exhaustive":
        complete = True
        for deleted in combinations(eligible, free):
            if checked >= max_removal_combinations or monotonic() >= deadline:
                complete = False
                break
            values, feasible, exact = evaluate(identities - frozenset(deleted))
            checked += 1
            if values is None:
                complete = False
                break
            if not feasible:
                continue
            value = objective(baselines, values)
            if value.gaps:
                gaps.extend(CoverageGap(message) for message in value.gaps)
                complete = False
                break
            if best is None or (rank(value), deleted) < (rank(best[1]), best[0]):
                best = deleted, value
        if best is None:
            status = (
                "infeasible"
                if complete and search_exact
                else "timed_out" if monotonic() >= deadline else "blocked"
            )
            return DeletionSelection(
                (),
                status,
                None,
                tuple(gaps),
                checked,
                0,
                search_exact,
                excluded=excluded,
            )
        status = (
            "exact"
            if complete and search_exact
            else "timed_out" if monotonic() >= deadline else "pool_relative"
        )
        return DeletionSelection(
            best[0],
            status,
            best[1],
            tuple(gaps),
            checked,
            0,
            search_exact,
            qualification(best[0]),
            excluded=excluded,
        )

    for refinement in range(max_refinements + 1):
        pooled = tuple(
            tuple(tuple(pool.values()) for pool in trials) for trials in pools
        )
        solved = _solve_pool(
            eligible, protected, free, targets, pooled, baselines, deadline
        )
        if solved is None and refinement == 0 and monotonic() < deadline:
            # A sparse pool can be infeasible even when retained gear has legal
            # alternatives. Bounded removal exploration discovers such builds;
            # only complete exact exploration can establish true infeasibility.
            discovery_complete = (
                math.comb(len(eligible), free) <= max_removal_combinations
            )
            discovery_feasible = False
            for deleted in combinations(eligible, free):
                if checked >= max_removal_combinations or monotonic() >= deadline:
                    discovery_complete = False
                    break
                values, feasible, exact = evaluate(identities - frozenset(deleted))
                checked += 1
                if values is None:
                    discovery_complete = False
                    break
                discovery_feasible |= feasible
            if discovery_complete and search_exact and not discovery_feasible:
                return DeletionSelection(
                    (),
                    "infeasible",
                    None,
                    tuple(gaps),
                    checked,
                    refinement,
                    True,
                    excluded=excluded,
                )
            baselines = [
                math.fsum(
                    max((build.score for build in pool.values()), default=0.0)
                    for pool in trials
                )
                / len(trials)
                for trials in pools
            ]
            pooled = tuple(
                tuple(tuple(pool.values()) for pool in trials) for trials in pools
            )
            solved = _solve_pool(
                eligible, protected, free, targets, pooled, baselines, deadline
            )
        if solved is None:
            status = "timed_out" if monotonic() >= deadline else "blocked"
            return DeletionSelection(
                () if best is None else best[0],
                status,
                None if best is None else best[1],
                tuple(gaps),
                checked,
                refinement,
                search_exact,
                excluded=excluded,
            )
        deleted, solver_complete = solved
        before = pooled
        values, feasible, exact = evaluate(identities - frozenset(deleted))
        checked += 1
        # Newly found builds are also valid original-inventory alternatives.
        baselines = [
            math.fsum(
                max((build.score for build in pool.values()), default=0.0)
                for pool in trials
            )
            / len(trials)
            for trials in pools
        ]
        if values is None or not feasible:
            status = "timed_out" if monotonic() >= deadline else "blocked"
            return DeletionSelection(
                (),
                status,
                None,
                tuple(gaps),
                checked,
                refinement,
                search_exact,
                excluded=excluded,
            )
        value = objective(baselines, values)
        if value.gaps:
            gaps.extend(CoverageGap(message) for message in value.gaps)
            return DeletionSelection(
                (),
                "blocked",
                value,
                tuple(gaps),
                checked,
                refinement,
                search_exact,
                excluded=excluded,
            )
        best = deleted, value
        after = tuple(
            tuple(tuple(pool.values()) for pool in trials) for trials in pools
        )
        if after == before or not solver_complete:
            if not solver_complete:
                gaps.append(
                    CoverageGap("MILP lexicographic optimization remains unresolved")
                )
            status = (
                "pool_relative"
                if solver_complete
                else "timed_out" if monotonic() >= deadline else "blocked"
            )
            return DeletionSelection(
                deleted,
                status,
                value,
                tuple(gaps),
                checked,
                refinement,
                search_exact,
                qualification(deleted),
                excluded=excluded,
            )
    assert best is not None
    return DeletionSelection(
        best[0],
        "pool_relative",
        best[1],
        tuple(gaps),
        checked,
        max_refinements,
        search_exact,
        qualification(best[0]),
        excluded=excluded,
    )


def _solve_pool(
    eligible: tuple[str, ...],
    protected: frozenset[str],
    free: int,
    targets: Sequence[BuildTarget],
    pools: tuple[tuple[tuple[BuildAlternative, ...], ...], ...],
    baselines: Sequence[float],
    deadline: float,
) -> tuple[tuple[str, ...], bool] | None:
    """Lexicographic MILP; no weighted blend of primary and exceptional losses."""
    deletions = {identity: index for index, identity in enumerate(eligible)}
    count = len(eligible)
    groups = []
    for trials in pools:
        trial_groups = []
        for builds in trials:
            trial_groups.append(tuple(range(count, count + len(builds))))
            count += len(builds)
        groups.append(trial_groups)
    worst, exceptional = count, count + 1
    size = count + 2
    rows: list[tuple[dict[int, float], float, float]] = [
        ({index: 1.0 for index in deletions.values()}, float(free), float(free))
    ]
    categories: dict[tuple[str, Category], int] = {}
    families = {target.family for target in targets if target.category != "exceptional"}
    for target in targets:
        if target.category != "exceptional":
            key = target.family, target.category
            categories[key] = categories.get(key, 0) + 1
    average = np.zeros(size)
    for target, trials, trial_groups, baseline in zip(
        targets, pools, groups, baselines
    ):
        scores = {}
        for builds, variables in zip(trials, trial_groups):
            rows.append(
                (
                    {index: 1.0 for index in variables},
                    1.0 if target.category == "current" else 0.0,
                    1.0,
                )
            )
            for build, variable in zip(builds, variables):
                for identity in build.real_ids - protected:
                    rows.append(
                        ({variable: 1.0, deletions[identity]: 1.0}, -np.inf, 1.0)
                    )
                coefficient = build.score / baseline / len(trials)
                scores[variable] = coefficient
                if target.category != "exceptional":
                    average[variable] = (
                        -coefficient
                        / len(families)
                        / sum(family == target.family for family, _ in categories)
                        / categories[target.family, target.category]
                    )
        scores[exceptional if target.category == "exceptional" else worst] = 1.0
        rows.append((scores, 1.0, np.inf))
    matrix = lil_matrix((len(rows), size), dtype=np.float64)
    lower = np.empty(len(rows))
    upper = np.empty(len(rows))
    for row, (coefficients, lo, hi) in enumerate(rows):
        for column, coefficient in coefficients.items():
            matrix[row, column] = coefficient
        lower[row], upper[row] = lo, hi
    constraints = [LinearConstraint(matrix.tocsr(), lower, upper)]
    integrality = np.zeros(size, dtype=np.uint8)
    integrality[:count] = 1
    bounds = Bounds(np.zeros(size), np.ones(size))
    objectives = [np.eye(1, size, worst).ravel(), average]
    if any(target.category == "exceptional" for target in targets):
        objectives.append(np.eye(1, size, exceptional).ravel())
    deleted = None
    achieved: list[tuple[np.ndarray, float]] = []
    for objective in objectives:
        remaining = deadline - monotonic()
        if remaining <= 0:
            return None if deleted is None else (deleted, False)
        result = milp(
            objective,
            integrality=integrality,
            bounds=bounds,
            constraints=constraints,
            options={"time_limit": remaining, "mip_rel_gap": 0.0},
        )
        if result.x is None:
            return None if deleted is None else (deleted, False)
        # Do not accept a later pass that worsens an earlier objective through
        # the solver's floating-point feasibility tolerance.
        if any(float(previous @ result.x) > optimum for previous, optimum in achieved):
            return None if deleted is None else (deleted, False)
        deleted = tuple(
            identity for identity, index in deletions.items() if result.x[index] > 0.5
        )
        if len(deleted) != free:
            return None
        if not result.success:
            return deleted, False
        optimum = float(objective @ result.x)
        achieved.append((objective, optimum))
        constraints.append(LinearConstraint(objective.reshape(1, -1), -np.inf, optimum))
    return None if deleted is None else (deleted, True)
