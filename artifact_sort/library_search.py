"""Legal current-inventory search using compiled scenario formulas.

Exact enumeration is the small-case oracle. Bounded multi-start coordinate search
is explicitly approximate: no positive-weight dominance or optimality claims.
"""

from __future__ import annotations

from dataclasses import dataclass
import heapq
from itertools import product
import math
import random
from time import monotonic
from typing import TYPE_CHECKING, Iterable, Literal

from .inventory import MAIN_STATS, Artifact, Build, Inventory, assemble_build
from .library_runtime import CompiledScenario, Evaluation
from .model import SLOT_KEYS

if TYPE_CHECKING:
    from .library_cache import AnalysisCache

REAL_SLOT_PATTERNS = tuple(
    frozenset(slot for index, slot in enumerate(SLOT_KEYS) if mask & (1 << index))
    for mask in range(1, 1 << len(SLOT_KEYS))
)


@dataclass(frozen=True, slots=True)
class ScoredBuild:
    build: Build
    evaluation: Evaluation


@dataclass(frozen=True, slots=True)
class SearchResult:
    builds: tuple[ScoredBuild, ...]
    status: Literal["exact", "approximate", "timed_out"]
    evaluated: int
    combinations: int
    context_builds: tuple[ScoredBuild, ...] = ()

    @property
    def proven_infeasible(self) -> bool:
        return self.status == "exact" and not self.builds


def _feasibility_rank(
    result: ScoredBuild, scenario: CompiledScenario
) -> tuple[bool, int, float, float, tuple[str, ...]]:
    """Guide infeasible starts without replacing the scenario's score objective."""
    definition = scenario.definition
    evaluation = result.evaluation
    deficit = sum(
        max(0.0, value - evaluation.effective_stats[key]) / max(abs(value), 1.0)
        for key, value in definition.minimums.items()
    ) + sum(
        max(0.0, evaluation.effective_stats[key] - value) / max(abs(value), 1.0)
        for key, value in definition.maximums.items()
    )
    missing_set_pieces = min(
        sum(
            max(0, count - result.build.set_counts.get(key, 0))
            for key, count in strategy.items()
        )
        for strategy in definition.sets
    )
    return (
        not evaluation.feasible,
        missing_set_pieces,
        deficit,
        -evaluation.score,
        result.build.artifact_ids,
    )


def search_builds(
    inventory: Inventory,
    scenario: CompiledScenario,
    *,
    available_ids: Iterable[str] | None = None,
    top_k: int = 20,
    max_evaluations: int = 100_000,
    time_limit: float | None = None,
    seed: int = 0,
    collect_contexts: bool = False,
    cache: AnalysisCache | None = None,
) -> SearchResult:
    """Search actual current stats; unfinished pieces get no fictitious growth.

    Exhaustively enumerate when the full candidate product fits the budget.
    Otherwise use reproducible random starts and exact single-slot swaps.
    Approximate failure to find a qualifying build is never called infeasible.
    """
    if type(top_k) is not int or top_k <= 0:
        raise ValueError("top_k must be a positive integer")
    if type(max_evaluations) is not int or max_evaluations <= 0:
        raise ValueError("max_evaluations must be a positive integer")
    if time_limit is not None and (not math.isfinite(time_limit) or time_limit <= 0):
        raise ValueError("time_limit must be finite and positive")
    pieces = inventory.select(available_ids)
    unknown_sets = {a.set_key for a in pieces} - scenario.known_sets
    if unknown_sets:
        raise ValueError(f"unknown inventory sets: {sorted(unknown_sets)}")
    candidates = [
        tuple(
            sorted(
                (
                    a
                    for a in pieces
                    if a.slot == slot
                    and a.main_stat
                    in scenario.definition.mains.get(slot, (a.main_stat,))
                ),
                key=lambda a: a.id,
            )
        )
        for slot in SLOT_KEYS
    ]
    key = None
    if cache is not None:
        key = cache.search_key(
            scenario, candidates, top_k, max_evaluations, seed, collect_contexts
        )
        cached = cache.get_search(key)
        if cached is not None:
            return cached
    combinations = math.prod(len(group) for group in candidates)
    if combinations == 0:
        empty = SearchResult((), "exact", 0, 0)
        if cache is not None and key is not None:
            cache.put_search(key, empty)
        return empty
    deadline = math.inf if time_limit is None else monotonic() + time_limit
    exact = combinations <= max_evaluations
    seen: dict[tuple[str, ...], ScoredBuild] = {}
    evaluated = 0
    heap: list[tuple[float, tuple[str, ...], ScoredBuild]] = []
    retained_ids: set[tuple[str, ...]] = set()
    contexts: dict[
        tuple[tuple[str, ...], tuple[bool, ...], tuple[int, ...]], ScoredBuild
    ] = {}
    status: Literal["exact", "approximate", "timed_out"] = (
        "exact" if exact else "approximate"
    )

    def exhausted() -> bool:
        nonlocal status
        if monotonic() >= deadline:
            status = "timed_out"
            return True
        return evaluated >= max_evaluations

    def evaluate(loadout: tuple[Artifact, ...]) -> ScoredBuild:
        nonlocal evaluated
        identity = tuple(a.id for a in loadout)
        if identity in seen:
            return seen[identity]
        build = assemble_build(loadout)
        evaluation = scenario.evaluate(
            build.stats, build.set_counts, main_stats=build.main_stats
        )
        result = ScoredBuild(build, evaluation)
        evaluated += 1
        if not exact:
            seen[identity] = result
        if collect_contexts and evaluation.feasible:
            key = (
                tuple(build.main_stats[slot] for slot in SLOT_KEYS),
                tuple(
                    effect.when is None
                    or effect.when.evaluate(
                        scenario.definition.conditions, build.set_counts
                    )
                    for effect in scenario.effects
                ),
                tuple(
                    index
                    for index, strategy in enumerate(scenario.definition.sets)
                    if all(
                        build.set_counts.get(name, 0) >= count
                        for name, count in strategy.items()
                    )
                ),
            )
            previous = contexts.get(key)
            if previous is None or (result.evaluation.score, identity) > (
                previous.evaluation.score,
                previous.build.artifact_ids,
            ):
                contexts[key] = result
        if evaluation.feasible and identity not in retained_ids:
            item = evaluation.score, identity, result
            if len(heap) < top_k:
                heapq.heappush(heap, item)
                retained_ids.add(identity)
            elif item[:2] > heap[0][:2]:
                removed = heapq.heapreplace(heap, item)
                retained_ids.remove(removed[1])
                retained_ids.add(identity)
        return result

    if exact:
        for loadout in product(*candidates):
            if exhausted():
                break
            evaluate(loadout)
    else:
        rng = random.Random(seed)
        # More starts can recover different set/constraint regimes. Coordinate
        # swaps can miss coordinated improvements; this mode stays approximate.
        starts = max(1, min(64, max_evaluations // max(1, sum(map(len, candidates)))))
        for start in range(starts):
            if exhausted():
                break
            # Keep only one start's swap cache. Exact enumeration needs no cache;
            # retaining every full stat snapshot would make large scans costly.
            seen.clear()
            loadout = tuple(
                group[0] if start == 0 else rng.choice(group) for group in candidates
            )
            current = evaluate(loadout)
            changed = True
            while changed and not exhausted():
                changed = False
                for slot, group in enumerate(candidates):
                    best = current
                    best_loadout = loadout
                    for artifact in group:
                        if exhausted():
                            break
                        swapped = loadout[:slot] + (artifact,) + loadout[slot + 1 :]
                        result = evaluate(swapped)
                        if _feasibility_rank(result, scenario) < _feasibility_rank(
                            best, scenario
                        ):
                            best = result
                            best_loadout = swapped
                    if best_loadout != loadout:
                        loadout, current = best_loadout, best
                        changed = True
                    if exhausted():
                        break
    builds = tuple(
        item[2] for item in sorted(heap, key=lambda item: item[:2], reverse=True)
    )
    search_result = SearchResult(
        builds,
        status,
        evaluated,
        combinations,
        tuple(contexts[key] for key in sorted(contexts)),
    )
    if cache is not None and key is not None:
        cache.put_search(key, search_result)
    return search_result


@dataclass(frozen=True, slots=True)
class PatternSearchResult:
    real_slots: frozenset[str]
    search: SearchResult


def search_future_patterns(
    inventory: Inventory,
    scenario: CompiledScenario,
    complements: Inventory,
    *,
    available_ids: Iterable[str] | None = None,
    top_k: int = 20,
    max_evaluations: int = 100_000,
    time_limit: float | None = None,
    seed: int = 0,
) -> tuple[PatternSearchResult, ...]:
    """Evaluate all 31 real-slot patterns with an explicit frozen complement pool.

    The caller supplies modeled completed real outcomes; this function never
    invents rolls. A global deadline marks unsearched patterns timed_out, so
    omitted work cannot be mistaken for missing opportunities.
    """
    if time_limit is not None and (not math.isfinite(time_limit) or time_limit <= 0):
        raise ValueError("time_limit must be finite and positive")
    real = inventory.select(available_ids)
    if any(
        a.level != len(MAIN_STATS[a.rarity][a.main_stat]) - 1
        for a in (*real, *complements.artifacts)
    ):
        raise ValueError(
            "future-pattern search requires completed real outcomes and complements"
        )
    if {a.id for a in real} & {a.id for a in complements.artifacts}:
        raise ValueError("reference and real artifact identities must be disjoint")
    deadline = math.inf if time_limit is None else monotonic() + time_limit
    results: list[PatternSearchResult] = []
    # PERFORMANCE: 31 patterns multiply scenario/profile/outcome work. Profile
    # per-pattern costs before considering a reduced-pattern mode: that would
    # omit multi-piece opportunities, not merely accelerate the same model.
    for pattern in REAL_SLOT_PATTERNS:
        pieces = tuple(a for a in real if a.slot in pattern) + tuple(
            a for a in complements.artifacts if a.slot not in pattern
        )
        remaining = deadline - monotonic()
        if remaining <= 0:
            result = SearchResult((), "timed_out", 0, 0)
        else:
            result = search_builds(
                Inventory(pieces),
                scenario,
                top_k=top_k,
                max_evaluations=max_evaluations,
                time_limit=None if time_limit is None else remaining,
                seed=seed,
            )
        results.append(PatternSearchResult(pattern, result))
    return tuple(results)
