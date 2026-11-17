"""Unconditional qualifying performance for each real-slot opportunity.

Reference profiles are supplied explicitly. This layer averages upgrade trials,
not contexts: every real-slot pattern remains a separate preservation target.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from time import monotonic
from typing import Iterable, Literal, Sequence

from .inventory import MAIN_STATS, Inventory
from .library_runtime import CompiledScenario
from .library_search import REAL_SLOT_PATTERNS, SearchResult, search_future_patterns


@dataclass(frozen=True, slots=True)
class FutureTrial:
    score: float | None
    search_status: Literal["exact", "approximate", "timed_out"]
    artifact_ids: tuple[str, ...]

    @property
    def qualified(self) -> bool:
        return bool(self.artifact_ids)


@dataclass(frozen=True, slots=True)
class FuturePatternValue:
    real_slots: frozenset[str]
    trials: tuple[FutureTrial, ...]

    @property
    def unresolved(self) -> int:
        return sum(trial.score is None for trial in self.trials)

    @property
    def expected_score(self) -> float | None:
        """Unconditional trial mean, including proven failures as zero.

        With approximate successful searches this is a found-performance lower
        bound, not an exact optimum. Unknown qualification has no point estimate.
        """
        if self.unresolved:
            return None
        return math.fsum(
            trial.score for trial in self.trials if trial.score is not None
        ) / len(self.trials)

    @property
    def qualification_probability(self) -> tuple[float, float]:
        """Empirical bounds; unresolved trials may or may not qualify.

        These bounds describe search uncertainty, not Monte Carlo confidence.
        """
        qualified = sum(trial.qualified for trial in self.trials)
        count = len(self.trials)
        return qualified / count, (qualified + self.unresolved) / count

    @property
    def exact(self) -> bool:
        return all(trial.search_status == "exact" for trial in self.trials)

    @property
    def opportunity_gap(self) -> bool:
        """No qualifying baseline: do not interpret this as deletion evidence."""
        return not self.unresolved and not any(trial.qualified for trial in self.trials)


def _trial(result: SearchResult) -> FutureTrial:
    if result.builds:
        best = result.builds[0]
        return FutureTrial(
            best.evaluation.score, result.status, best.build.artifact_ids
        )
    return FutureTrial(0.0 if result.proven_infeasible else None, result.status, ())


def evaluate_future_outcomes(
    completed_trials: Sequence[Inventory],
    scenario: CompiledScenario,
    complements: Inventory,
    *,
    available_ids: Iterable[str] | None = None,
    max_evaluations: int = 100_000,
    time_limit: float | None = None,
    seed: int = 0,
) -> tuple[FuturePatternValue, ...]:
    """Search all 31 patterns in each supplied coupled upgrade trial.

    Reuse the same completed trials and complements when comparing removal
    sets. Selection must not regenerate outcomes or choose a different profile.
    The deadline spans all trials, including work not yet started.
    """
    if not completed_trials:
        raise ValueError("at least one completed trial is required")
    if type(max_evaluations) is not int or max_evaluations <= 0:
        raise ValueError("max_evaluations must be a positive integer")
    if time_limit is not None and (not math.isfinite(time_limit) or time_limit <= 0):
        raise ValueError("time_limit must be finite and positive")
    identities = {
        a.id: (a.set_key, a.slot, a.main_stat, a.rarity)
        for a in completed_trials[0].artifacts
    }
    for inventory in completed_trials:
        if {
            a.id: (a.set_key, a.slot, a.main_stat, a.rarity)
            for a in inventory.artifacts
        } != identities:
            raise ValueError(
                "coupled trials must contain the same artifact identities and properties"
            )
    if any(
        a.level != len(MAIN_STATS[a.rarity][a.main_stat]) - 1
        for inventory in (*completed_trials, complements)
        for a in inventory.artifacts
    ):
        raise ValueError(
            "future evaluation requires completed outcomes and complements"
        )
    if identities.keys() & {a.id for a in complements.artifacts}:
        raise ValueError("reference and real artifact identities must be disjoint")
    available = None if available_ids is None else tuple(available_ids)
    completed_trials[0].select(available)
    deadline = math.inf if time_limit is None else monotonic() + time_limit
    trials: list[list[FutureTrial]] = [[] for _ in REAL_SLOT_PATTERNS]
    for index, inventory in enumerate(completed_trials):
        remaining = deadline - monotonic()
        if remaining <= 0:
            for outcomes in trials:
                outcomes.append(FutureTrial(None, "timed_out", ()))
            continue
        results = search_future_patterns(
            inventory,
            scenario,
            complements,
            available_ids=available,
            top_k=1,
            max_evaluations=max_evaluations,
            time_limit=None if time_limit is None else remaining,
            seed=seed + index,
        )
        for outcomes, result in zip(trials, results):
            outcomes.append(_trial(result.search))
    return tuple(
        FuturePatternValue(pattern, tuple(outcomes))
        for pattern, outcomes in zip(REAL_SLOT_PATTERNS, trials)
    )
