"""Legal current-inventory search using compiled scenario formulas.

Exact enumeration is the small-case oracle. Bounded multi-start coordinate search
is explicitly approximate: no positive-weight dominance or optimality claims.
"""

from __future__ import annotations

from dataclasses import dataclass
import heapq
from itertools import islice, product
import math
import random
from time import monotonic
from typing import TYPE_CHECKING, Iterable, Literal

import numpy as np

from .batch_evaluation import evaluate_batch
from .inventory import MAIN_STATS, Artifact, Build, Inventory, assemble_build
from .library_runtime import CompiledScenario, Evaluation
from .model import SLOT_KEYS, STAT_KEYS

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
    candidate_limit: int | None = 12,
    cache: AnalysisCache | None = None,
) -> SearchResult:
    """Search actual current stats; unfinished pieces get no fictitious growth.

    Exhaustively enumerate when the full candidate product fits the budget.
    Otherwise use reproducible starts, local dot-product shortlists, and
    batched full-formula single-slot swaps. Shortlisting is approximate.
    candidate_limit retains at least that many pieces per set/main stratum
    (and at least top_k), plus constraint extremes and the current piece.
    None disables shortlisting for comparisons; it does not force enumeration.
    Approximate failure to find a qualifying build is never called infeasible.
    """
    if type(top_k) is not int or top_k <= 0:
        raise ValueError("top_k must be a positive integer")
    if type(max_evaluations) is not int or max_evaluations <= 0:
        raise ValueError("max_evaluations must be a positive integer")
    if candidate_limit is not None and (type(candidate_limit) is not int or candidate_limit <= 0):
        raise ValueError("candidate_limit must be a positive integer or None")
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
            scenario, candidates, top_k, max_evaluations, seed, collect_contexts,
            candidate_limit,
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
    # Artifact stats/main values and set encodings are prepared once, rather than
    # reconstructed and validated for every five-piece combination.
    flat = tuple(a for group in candidates for a in group)
    groups = []
    offset = 0
    for group in candidates:
        groups.append(tuple(range(offset, offset + len(group))))
        offset += len(group)
    stat_maps = [a.stats for a in flat]
    vectors = np.array([[stats.get(key, 0.0) for key in STAT_KEYS] for stats in stat_maps])
    set_names = tuple(sorted({a.set_key for a in flat}))
    set_codes = np.array([set_names.index(a.set_key) for a in flat])
    main_names = np.array([a.main_stat for a in flat])
    evaluated = 0
    heap: list[tuple[float, tuple[str, ...], ScoredBuild]] = []
    retained_ids: set[tuple[str, ...]] = set()
    contexts = {}
    status: Literal["exact", "approximate", "timed_out"] = (
        "exact" if exact else "approximate"
    )
    # A restart's memo stores compact ranks, not full evaluated build objects.
    seen = {}

    def exhausted() -> bool:
        nonlocal status
        if monotonic() >= deadline:
            status = "timed_out"
            return True
        return evaluated >= max_evaluations

    def identities(loadout):
        return tuple(flat[index].id for index in loadout)

    def evaluate_many(loadouts):
        nonlocal evaluated
        loadouts = list(dict.fromkeys(loadouts))
        fresh = [loadout for loadout in loadouts if loadout not in seen]
        fresh = fresh[:max_evaluations - evaluated]
        if not fresh:
            return
        indexes = np.asarray(fresh, dtype=np.int64)
        # Explicit left-to-right accumulation agrees with scalar build assembly.
        additions = np.zeros((len(fresh), len(STAT_KEYS)))
        for slot in range(5):
            additions += vectors[indexes[:, slot]]
        codes = set_codes[indexes]
        counts = {key: np.sum(codes == i, axis=1) for i, key in enumerate(set_names)}
        mains = {slot: main_names[indexes[:, i]] for i, slot in enumerate(SLOT_KEYS)}
        batch = evaluate_batch(scenario, additions, counts, main_stats=mains)
        evaluated += len(fresh)
        for i, loadout in enumerate(fresh):
            seen[loadout] = (
                not bool(batch.feasible[i]), int(batch.missing_set_pieces[i]),
                float(batch.deficit[i]), -float(batch.scores[i]), identities(loadout),
            )

        materialized = {}

        def materialize(i):
            if i not in materialized:
                build = assemble_build(flat[index] for index in fresh[i])
                materialized[i] = ScoredBuild(build, batch.row(i))
            return materialized[i]

        feasible = np.flatnonzero(batch.feasible)
        # Only reconstruct the best rows, including deterministic identity ties.
        contenders = feasible
        if len(contenders) > top_k:
            cutoff = np.partition(batch.scores[contenders], -top_k)[-top_k]
            contenders = contenders[batch.scores[contenders] >= cutoff]
        contenders = sorted(contenders, key=lambda i: (
            float(batch.scores[i]), identities(fresh[i])), reverse=True)[:top_k]
        for i in contenders:
            identity = identities(fresh[i])
            score = float(batch.scores[i])
            if identity in retained_ids:
                continue
            if len(heap) < top_k or (score, identity) > heap[0][:2]:
                item = score, identity, materialize(i)
                if len(heap) < top_k:
                    heapq.heappush(heap, item)
                else:
                    removed = heapq.heapreplace(heap, item)
                    retained_ids.remove(removed[1])
                retained_ids.add(identity)
        if collect_contexts:
            # Group structural regimes cheaply before reconstructing witnesses.
            # The activation predicates are constant within a set composition.
            regimes = {}
            for i in feasible:
                signature = (tuple(mains[slot][i] for slot in SLOT_KEYS), tuple(codes[i]))
                previous = regimes.get(signature)
                if previous is None or (batch.scores[i], identities(fresh[i])) > (
                    batch.scores[previous], identities(fresh[previous])):
                    regimes[signature] = i
            for i in regimes.values():
                sets = {key: int(value[i]) for key, value in counts.items()}
                signature = (
                    tuple(mains[slot][i] for slot in SLOT_KEYS),
                    tuple(effect.when is None or effect.when.evaluate(
                        scenario.definition.conditions, sets) for effect in scenario.effects),
                    tuple(j for j, strategy in enumerate(scenario.definition.sets)
                          if all(sets.get(key, 0) >= n for key, n in strategy.items())),
                )
                previous = contexts.get(signature)
                if previous is None or (batch.scores[i], identities(fresh[i])) > (
                    previous.evaluation.score, previous.build.artifact_ids):
                    contexts[signature] = materialize(i)

    if exact:
        iterator = product(*groups)
        while not exhausted():
            chunk = list(islice(iterator, min(512, max_evaluations - evaluated)))
            if not chunk:
                break
            evaluate_many(chunk)
            seen.clear()
    else:
        rng = random.Random(seed)
        seed_strategies = list(scenario.definition.sets)
        # A bonus can be optional rather than a hard set requirement. Seed its
        # activation explicitly, since single-slot moves can get stuck below it.
        def activation_thresholds(predicate):
            if predicate is None:
                return set()
            if predicate.op == "set":
                return {(predicate.key, predicate.pieces)}
            return set().union(*(activation_thresholds(child) for child in predicate.args))

        thresholds = set().union(*(activation_thresholds(effect.when) for effect in scenario.effects))
        for key, n in sorted(thresholds):
            if key not in set_names:
                continue
            for strategy in scenario.definition.sets:
                proposal = {**strategy, key: max(n, strategy.get(key, 0))}
                if sum(proposal.values()) <= 5 and proposal not in seed_strategies:
                    seed_strategies.append(proposal)
        # Greedy, set-aware seeds reduce the need for many blind restarts. Keep
        # enough starts to visit each authored strategy, capped at 64.
        start_cap = min(64, max(16, len(seed_strategies)))
        # Constrained stats and their conversion dependencies supply additional
        # screening directions. Keep both ends: upper bounds and excess stats
        # make positive-only screening unsafe even as a heuristic.
        constrained = set(scenario.definition.minimums) | set(scenario.definition.maximums)
        required = set(constrained)
        changed = True
        while changed:
            before = len(required)
            for key in tuple(required & {"hp", "atk", "def"}):
                required.add(f"{key}_")
            for effect in scenario.effects:
                kind, target = effect.target.split(".", 1)
                if kind == "stats" and target in required:
                    required.update(key for _, key in effect.program.stat_reads)
            changed = len(required) != before
        constraint_columns = [i for i, key in enumerate(STAT_KEYS) if key in required]
        strata = []
        constraint_keeps = []
        for group in groups:
            partitions = {}
            for index in group:
                a = flat[index]
                partitions.setdefault((a.set_key, a.main_stat), []).append(index)
            partitions = tuple(np.asarray(partition, dtype=np.int64) for partition in partitions.values())
            strata.append(partitions)
            keep = set()
            for partition in partitions:
                for column in constraint_columns:
                    ordered = partition[np.argsort(vectors[partition, column], kind="stable")]
                    keep.update(ordered[:2])
                    keep.update(ordered[-2:])
            constraint_keeps.append(keep)

        sweep_size = sum(map(len, groups)) if candidate_limit is None else sum(
            min(len(group), len(extra) + sum(min(len(partition), max(candidate_limit, top_k))
                                           for partition in partitions))
            for group, extra, partitions in zip(groups, constraint_keeps, strata)
        )
        starts = max(1, min(start_cap, max_evaluations // max(1, sweep_size)))

        shortlist_cache = {}

        def shortlists(loadout):
            if candidate_limit is None:
                return groups
            if loadout in shortlist_cache:
                return shortlist_cache[loadout]
            build = assemble_build(flat[index] for index in loadout)
            weights = scenario.linearize(build.stats, build.set_counts,
                                         main_stats=build.main_stats).weights
            with np.errstate(over="ignore", invalid="ignore"):
                scores = vectors @ np.array([weights.get(key, 0) for key in STAT_KEYS])
            if not np.all(np.isfinite(scores)):
                return groups
            selected = []
            for slot, partitions in enumerate(strata):
                keep = constraint_keeps[slot] | {loadout[slot]}
                for partition in partitions:
                    ordered = partition[np.argsort(scores[partition], kind="stable")][::-1]
                    keep.update(ordered[:max(candidate_limit, top_k)])
                selected.append(tuple(sorted(keep, key=lambda index: (scores[index], index), reverse=True)))
            if len(shortlist_cache) < 256:
                shortlist_cache[loadout] = selected
            return selected

        for start in range(starts):
            if exhausted():
                break
            seen.clear()
            loadout = tuple(group[0] if start == 0 else rng.choice(group) for group in groups)
            evaluate_many([loadout])
            # A greedy start for each allowed set strategy supplies coordinated
            # set assignments before individual-slot improvement begins.
            choices = shortlists(loadout)
            strategy = seed_strategies[start % len(seed_strategies)]
            reserved = {}
            for set_key, n in strategy.items():
                eligible = [slot for slot, group in enumerate(choices)
                            if slot not in reserved and any(flat[i].set_key == set_key for i in group)]
                rng.shuffle(eligible)
                for slot in eligible[:n]:
                    reserved[slot] = set_key
            seed_loadout = tuple(
                next((i for i in choices[slot] if flat[i].set_key == reserved[slot]), loadout[slot])
                if slot in reserved else choices[slot][0] for slot in range(5)
            )
            evaluate_many([seed_loadout])
            if seed_loadout in seen and seen[seed_loadout] < seen[loadout]:
                loadout = seed_loadout
            improved = True
            while improved and not exhausted():
                improved = False
                choices = shortlists(loadout)
                for slot, group in enumerate(choices):
                    if exhausted():
                        break
                    proposals = [loadout[:slot] + (index,) + loadout[slot + 1:] for index in group]
                    for offset in range(0, len(proposals), 512):
                        if exhausted():
                            break
                        evaluate_many(proposals[offset:offset + 512])
                    best = min((proposal for proposal in proposals if proposal in seen),
                               key=seen.__getitem__)
                    if seen[best] < seen[loadout]:
                        loadout = best
                        improved = True
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
