from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import heapq
from itertools import product
import json
from typing import Iterable, Sequence

import numpy as np
from numpy.typing import NDArray

from .cache import ResultCache, cache_key
from .model import ArtifactBatch, STAT_INDEX
from .scenarios import BuiltinEvaluator, Evaluator, Scenario, scenario_to_mapping
from .screening import screen_scores, screening_directions


@dataclass(frozen=True, slots=True)
class BuildResult:
    indices: tuple[int, int, int, int, int]
    utility: float
    stats: NDArray[np.float64]


@dataclass(frozen=True, slots=True)
class ScenarioRegret:
    scenario_id: str
    tier: str
    baseline_utility: float
    retained_utility: float
    regret: float
    baseline_build: tuple[int, ...]
    retained_build: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class DeletionResult:
    deleted_indices: tuple[int, ...]
    deleted_ids: tuple[str, ...]
    regrets: tuple[ScenarioRegret, ...]
    solver: str
    verified: bool


def _set_adjusted_stats(
    stats: NDArray[np.float64], sets: Sequence[str], scenario: Scenario
) -> NDArray[np.float64]:
    bonuses = scenario.metadata.get("set_stat_bonuses")
    if not isinstance(bonuses, dict):
        return stats
    result = stats.copy()
    counts: dict[str, int] = {}
    for key in sets:
        counts[key] = counts.get(key, 0) + 1
    for key, count in counts.items():
        set_bonuses = bonuses.get(key)
        if not isinstance(set_bonuses, dict):
            continue
        for threshold in (2, 4):
            values = set_bonuses.get(str(threshold), set_bonuses.get(threshold))
            if count < threshold or not isinstance(values, dict):
                continue
            for stat, value in values.items():
                if stat in STAT_INDEX:
                    result[STAT_INDEX[stat]] += float(value)
    return result


class BuildOptimizer:
    """Complete five-slot optimizer with exact small search and bounded large search."""

    def __init__(
        self,
        batch: ArtifactBatch,
        evaluator: Evaluator | None = None,
        *,
        candidate_limit: int = 36,
        per_set_limit: int = 3,
        beam_width: int = 6000,
        exact_product_limit: int = 1_500_000,
        cache: ResultCache | None = None,
        evaluation_cache_limit: int = 100_000,
    ) -> None:
        self.batch = batch
        self.evaluator = evaluator or BuiltinEvaluator()
        self.candidate_limit = candidate_limit
        self.per_set_limit = per_set_limit
        self.beam_width = beam_width
        self.exact_product_limit = exact_product_limit
        self.cache = cache
        self.evaluation_cache_limit = evaluation_cache_limit
        self._loadout_memory: dict[str, tuple[int, list[BuildResult]]] = {}
        self._scenario_fingerprints: dict[int, str] = {}

    def scenario_fingerprint(self, scenario: Scenario) -> str:
        identity = id(scenario)
        found = self._scenario_fingerprints.get(identity)
        if found is not None:
            return found
        payload = scenario_to_mapping(scenario)
        fingerprint = sha256(
            json.dumps(payload, sort_keys=True, default=str).encode()
        ).hexdigest()
        self._scenario_fingerprints[identity] = fingerprint
        return fingerprint

    def _search_key(
        self,
        scenario: Scenario,
        stats: NDArray[np.float64],
        available: NDArray[np.bool_],
        include_unfinished: bool,
        forced_index: int | None,
    ) -> str | None:
        if len(set(self.batch.ids.tolist())) != len(self.batch):
            return None
        digest = sha256()
        indices = np.flatnonzero(available)
        order = indices[np.argsort(self.batch.ids[indices])]
        for index in order:
            digest.update(str(self.batch.ids[index]).encode())
            digest.update(b"\0")
            digest.update(str(self.batch.set_keys[index]).encode())
            digest.update(bytes((int(self.batch.slots[index]),)))
            digest.update(bytes((int(self.batch.main_stats[index]),)))
            digest.update(bytes((int(self.batch.rarities[index]),)))
            digest.update(np.ascontiguousarray(stats[index], dtype=np.float64).tobytes())
        forced_id = str(self.batch.ids[forced_index]) if forced_index is not None else None
        return cache_key(
            artifact_fingerprint=digest.hexdigest(),
            scenario_hash=self.scenario_fingerprint(scenario),
            evaluator_version=self.evaluator.version,
            parameters={
                "kind": "loadout-pool",
                "candidate_limit": self.candidate_limit,
                "per_set_limit": self.per_set_limit,
                "beam_width": self.beam_width,
                "exact_product_limit": self.exact_product_limit,
                "include_unfinished": include_unfinished,
                "forced_id": forced_id,
            },
        )

    def _restore_loadouts(
        self, value: object, requested: int
    ) -> list[BuildResult] | None:
        if not isinstance(value, dict):
            return None
        cached_depth = value.get("requested_top_k")
        if not isinstance(cached_depth, int) or cached_depth < requested:
            return None
        raw_builds = value.get("builds")
        if not isinstance(raw_builds, list):
            return None
        id_to_index = {str(artifact_id): index for index, artifact_id in enumerate(self.batch.ids)}
        results: list[BuildResult] = []
        try:
            for raw in raw_builds[:requested]:
                if not isinstance(raw, dict):
                    return None
                artifact_ids = raw["artifact_ids"]
                if not isinstance(artifact_ids, list) or len(artifact_ids) != 5:
                    return None
                indices = tuple(id_to_index[str(artifact_id)] for artifact_id in artifact_ids)
                stats = np.asarray(raw["stats"], dtype=np.float64)
                if stats.shape != (19,):
                    return None
                stats.setflags(write=False)
                results.append(BuildResult(indices, float(raw["utility"]), stats))
        except (KeyError, TypeError, ValueError):
            return None
        return results

    def _cached_loadouts(self, key: str, requested: int) -> list[BuildResult] | None:
        memory = self._loadout_memory.get(key)
        if memory is not None and memory[0] >= requested:
            return memory[1][:requested]
        if self.cache is None:
            return None
        value = self.cache.get("loadout-pool", key, track=False)
        restored = self._restore_loadouts(value, requested)
        self.cache.record_lookup("loadout-pool", hit=restored is not None)
        if restored is not None:
            self._loadout_memory[key] = (requested, restored)
        return restored

    def _store_loadouts(
        self, key: str | None, requested: int, results: list[BuildResult]
    ) -> None:
        if key is None:
            return
        self._loadout_memory[key] = (requested, results)
        if self.cache is None:
            return
        self.cache.put(
            "loadout-pool",
            key,
            {
                "requested_top_k": requested,
                "builds": [
                    {
                        "artifact_ids": [str(self.batch.ids[index]) for index in result.indices],
                        "utility": result.utility,
                        "stats": result.stats.tolist(),
                    }
                    for result in results
                ],
            },
        )

    def _candidate_lists(
        self,
        scenario: Scenario,
        stats: NDArray[np.float64],
        available: NDArray[np.bool_],
        *,
        forced_index: int | None = None,
    ) -> list[NDArray[np.int64]]:
        baseline = np.median(stats[available], axis=0)
        directions = screening_directions(self.evaluator, scenario, baseline)
        weights = np.max(directions, axis=0)
        scores = screen_scores(stats, directions)
        allowed_mains = scenario.allowed_mains
        output: list[NDArray[np.int64]] = []

        for slot in range(5):
            mask = available & (self.batch.slots == slot) & (self.batch.rarities == 5)
            allowed = allowed_mains.get(slot)
            if allowed:
                mask &= np.isin(self.batch.main_stats, allowed)
            indices = np.flatnonzero(mask)
            if forced_index is not None and int(self.batch.slots[forced_index]) == slot:
                indices = np.array([forced_index], dtype=np.int64)
            else:
                indices = self._pareto_prune(indices, stats, weights)
            if forced_index is None and len(indices) > self.candidate_limit:
                global_best = indices[
                    np.argpartition(scores[indices], -self.candidate_limit)[-self.candidate_limit :]
                ]
                preserved: list[int] = []
                for set_key in np.unique(self.batch.set_keys[indices]):
                    group = indices[self.batch.set_keys[indices] == set_key]
                    take = min(self.per_set_limit, len(group))
                    preserved.extend(
                        group[np.argpartition(scores[group], -take)[-take:]].tolist()
                    )
                indices = np.unique(np.concatenate((global_best, np.asarray(preserved))))
            if len(indices) == 0:
                return []
            indices = indices[np.argsort(scores[indices])[::-1]]
            output.append(indices.astype(np.int64, copy=False))
        return output

    def _pareto_prune(
        self,
        indices: NDArray[np.int64],
        stats: NDArray[np.float64],
        weights: NDArray[np.float64],
    ) -> NDArray[np.int64]:
        relevant = np.flatnonzero(weights > 1e-12)
        if len(indices) < 2 or len(relevant) == 0:
            return indices
        retained: list[int] = []
        # Dominance is only safe inside an identical set/main/slot group.
        groups = np.char.add(
            np.char.add(self.batch.set_keys[indices], "\x00"),
            self.batch.main_stats[indices].astype(str),
        )
        for group in np.unique(groups):
            group_indices = indices[groups == group]
            values = stats[np.ix_(group_indices, relevant)]
            keep = np.ones(len(group_indices), dtype=np.bool_)
            for row in range(len(group_indices)):
                dominated = np.all(values >= values[row], axis=1) & np.any(
                    values > values[row], axis=1
                )
                dominated[row] = False
                if np.any(dominated):
                    keep[row] = False
            retained.extend(int(index) for index in group_indices[keep])
        return np.asarray(retained, dtype=np.int64)

    def _legal_sets(self, indices: Sequence[int], scenario: Scenario) -> bool:
        requirements = scenario.set_requirements
        if not requirements:
            return True
        sets = self.batch.set_keys[np.asarray(indices)]
        return all(np.count_nonzero(sets == key) >= count for key, count in requirements.items())

    def _candidate_builds(
        self,
        lists: list[NDArray[np.int64]],
        stats: NDArray[np.float64],
        scenario: Scenario,
        top_k: int,
    ) -> list[BuildResult]:
        sizes = [len(values) for values in lists]
        combinations = int(np.prod(sizes, dtype=np.int64))
        bounded_candidates = (
            combinations
            if combinations <= self.exact_product_limit
            else self.beam_width
        )
        cache_evaluations = (
            self.cache is not None
            and bounded_candidates <= self.evaluation_cache_limit
        )
        evaluation_scope = cache_key(
            artifact_fingerprint="",
            scenario_hash=self.scenario_fingerprint(scenario),
            evaluator_version=self.evaluator.version,
            parameters={"kind": "build-evaluation"},
        )
        representative = np.median(stats[np.concatenate(lists)], axis=0)
        directions = screening_directions(self.evaluator, scenario, representative)
        screen = screen_scores(stats, directions)

        if combinations <= self.exact_product_limit:
            candidates: Iterable[tuple[int, ...]] = product(*lists)
        else:
            partials: list[tuple[float, tuple[int, ...]]] = [(0.0, ())]
            for values in lists:
                global_heap: list[tuple[float, tuple[int, ...]]] = []
                constraint_heaps: list[list[tuple[float, tuple[int, ...]]]] = [
                    [] for _ in scenario.constraints
                ]
                constraint_width = max(
                    1, self.beam_width // max(2, 2 * len(scenario.constraints))
                )
                for partial_score, partial in partials:
                    for index in values:
                        indices = partial + (int(index),)
                        score = partial_score + float(screen[index])
                        item = (score, indices)
                        if len(global_heap) < self.beam_width:
                            heapq.heappush(global_heap, item)
                        elif score > global_heap[0][0]:
                            heapq.heapreplace(global_heap, item)
                        for constraint_heap, (stat, _) in zip(
                            constraint_heaps, scenario.constraints
                        ):
                            constraint_score = float(stats[np.asarray(indices), stat].sum())
                            constraint_item = (constraint_score, indices)
                            if len(constraint_heap) < constraint_width:
                                heapq.heappush(constraint_heap, constraint_item)
                            elif constraint_score > constraint_heap[0][0]:
                                heapq.heapreplace(constraint_heap, constraint_item)
                preserved: dict[tuple[int, ...], float] = {}
                for constraint_heap in constraint_heaps:
                    for _, indices in constraint_heap:
                        preserved[indices] = float(screen[np.asarray(indices)].sum())
                for score, indices in sorted(global_heap, reverse=True):
                    if len(preserved) >= self.beam_width:
                        break
                    preserved.setdefault(indices, score)
                partials = [(score, indices) for indices, score in preserved.items()]
            candidates = (indices for _, indices in partials)

        best: list[tuple[float, tuple[int, ...], NDArray[np.float64]]] = []
        pending_indices: list[tuple[int, ...]] = []
        pending_totals: list[NDArray[np.float64]] = []

        def evaluate_pending() -> None:
            if not pending_indices:
                return
            totals_array = np.vstack(pending_totals)
            if cache_evaluations and self.cache is not None:
                keys = [
                    sha256(evaluation_scope.encode() + total.tobytes()).hexdigest()
                    for total in totals_array
                ]
                cached = self.cache.get_many("build-evaluation", keys)
                values: dict[str, float] = {}
                for key, value in cached.items():
                    if isinstance(value, (int, float)):
                        values[key] = float(value)
                missing: dict[str, NDArray[np.float64]] = {}
                for key, total in zip(keys, totals_array):
                    if key not in values:
                        missing.setdefault(key, total)
                if missing:
                    missing_keys = list(missing)
                    evaluated = self.evaluator.evaluate_batch(
                        np.vstack([missing[key] for key in missing_keys]), scenario
                    )
                    writes = {
                        key: float(utility)
                        for key, utility in zip(missing_keys, evaluated)
                    }
                    self.cache.put_many("build-evaluation", writes)
                    values.update(writes)
                utilities = np.asarray([values[key] for key in keys], dtype=np.float64)
            else:
                utilities = self.evaluator.evaluate_batch(totals_array, scenario)
            for utility, indices, total in zip(
                utilities, pending_indices, pending_totals
            ):
                if not np.isfinite(utility):
                    continue
                item = (float(utility), indices, total)
                if len(best) < top_k:
                    heapq.heappush(best, item)
                elif utility > best[0][0]:
                    heapq.heapreplace(best, item)
            pending_indices.clear()
            pending_totals.clear()

        for raw_indices in candidates:
            indices = tuple(int(i) for i in raw_indices)
            if not self._legal_sets(indices, scenario):
                continue
            total = stats[np.asarray(indices)].sum(axis=0)
            total = _set_adjusted_stats(total, self.batch.set_keys[np.asarray(indices)], scenario)
            pending_indices.append(indices)
            pending_totals.append(total)
            if len(pending_indices) >= 2048:
                evaluate_pending()
        evaluate_pending()

        return [
            BuildResult(indices, utility, total)
            for utility, indices, total in sorted(best, key=lambda item: item[0], reverse=True)
        ]

    def optimize(
        self,
        scenario: Scenario,
        *,
        available: NDArray[np.bool_] | None = None,
        stats: NDArray[np.float64] | None = None,
        include_unfinished: bool = False,
        forced_index: int | None = None,
        top_k: int = 1,
    ) -> list[BuildResult]:
        if stats is None:
            stats = self.batch.final_stats()
        if stats.shape != (len(self.batch), 19):
            raise ValueError("artifact stats have invalid shape")
        if available is None:
            available = np.ones(len(self.batch), dtype=np.bool_)
        else:
            available = available.copy()
        if not include_unfinished:
            available &= self.batch.levels == 20
        if forced_index is not None:
            available[forced_index] = True

        requested = max(1, top_k)
        search_key = self._search_key(
            scenario, stats, available, include_unfinished, forced_index
        )
        if search_key is not None:
            cached = self._cached_loadouts(search_key, requested)
            if cached is not None:
                return cached

        lists = self._candidate_lists(
            scenario, stats, available, forced_index=forced_index
        )
        if len(lists) != 5:
            self._store_loadouts(search_key, requested, [])
            return []
        results = self._candidate_builds(lists, stats, scenario, requested)
        self._store_loadouts(search_key, requested, results)
        return results


def _regret(baseline: float, retained: float) -> float:
    if baseline <= 0 or not np.isfinite(baseline):
        return 0.0 if retained == baseline else 1.0
    if not np.isfinite(retained):
        return 1.0
    return float(np.clip(1.0 - retained / baseline, 0.0, 1.0))


class DeletionAnalyzer:
    def __init__(
        self,
        optimizer: BuildOptimizer,
        scenarios: Sequence[Scenario],
        *,
        loadouts_per_scenario: int = 80,
    ) -> None:
        if not scenarios:
            raise ValueError("at least one scenario is required")
        self.optimizer = optimizer
        self.scenarios = tuple(scenarios)
        self.loadouts_per_scenario = loadouts_per_scenario

    def _loadout_pool(self) -> tuple[list[BuildResult], list[list[int]], list[float]]:
        builds: list[BuildResult] = []
        groups: list[list[int]] = []
        baselines: list[float] = []
        for scenario in self.scenarios:
            results = self.optimizer.optimize(
                scenario, top_k=self.loadouts_per_scenario
            )
            if not results:
                raise ValueError(f"scenario {scenario.id!r} has no legal completed build")
            group: list[int] = []
            for result in results:
                group.append(len(builds))
                builds.append(result)
            groups.append(group)
            baselines.append(results[0].utility)
        return builds, groups, baselines

    def _solve_milp(
        self,
        free: int,
        builds: Sequence[BuildResult],
        groups: Sequence[Sequence[int]],
        baselines: Sequence[float],
        protected: NDArray[np.bool_],
        option_values: NDArray[np.float64],
    ) -> NDArray[np.bool_]:
        from scipy.optimize import Bounds, LinearConstraint, milp
        from scipy.sparse import lil_matrix

        n_artifacts = len(self.optimizer.batch)
        n_builds = len(builds)
        r_current = n_artifacts + n_builds
        r_speculative = r_current + 1
        variables = r_speculative + 1
        rows: list[tuple[dict[int, float], float, float]] = []

        rows.append(({i: 1.0 for i in range(n_artifacts)}, float(free), float(free)))
        for build_index, build in enumerate(builds):
            y = n_artifacts + build_index
            for artifact in build.indices:
                rows.append(({y: 1.0, artifact: 1.0}, -np.inf, 1.0))
        for scenario_index, group in enumerate(groups):
            rows.append(
                ({n_artifacts + build_index: 1.0 for build_index in group}, 1.0, np.inf)
            )
            baseline = baselines[scenario_index]
            tier_var = (
                r_current
                if self.scenarios[scenario_index].tier == "current"
                else r_speculative
            )
            for build_index in group:
                regret = _regret(baseline, builds[build_index].utility)
                rows.append(
                    ({n_artifacts + build_index: regret, tier_var: -1.0}, -np.inf, 0.0)
                )

        matrix = lil_matrix((len(rows), variables), dtype=np.float64)
        lower = np.empty(len(rows), dtype=np.float64)
        upper = np.empty(len(rows), dtype=np.float64)
        for row, (coefficients, lo, hi) in enumerate(rows):
            for column, value in coefficients.items():
                matrix[row, column] = value
            lower[row] = lo
            upper[row] = hi

        integrality = np.zeros(variables, dtype=np.uint8)
        integrality[: n_artifacts + n_builds] = 1
        bounds_lower = np.zeros(variables, dtype=np.float64)
        bounds_upper = np.ones(variables, dtype=np.float64)
        bounds_upper[:n_artifacts][protected] = 0.0
        constraints: list[LinearConstraint] = [
            LinearConstraint(matrix.tocsr(), lower, upper)
        ]

        def solve(objective: NDArray[np.float64]):
            result = milp(
                objective,
                integrality=integrality,
                bounds=Bounds(bounds_lower, bounds_upper),
                constraints=constraints,
                options={"time_limit": 180.0, "mip_rel_gap": 1e-8},
            )
            if not result.success or result.x is None:
                raise RuntimeError(f"deletion MILP failed: {result.message}")
            return result

        has_current = any(scenario.tier == "current" for scenario in self.scenarios)
        objective = np.zeros(variables)
        objective[r_current if has_current else r_speculative] = 1.0
        first = solve(objective)
        first_var = r_current if has_current else r_speculative
        lock = lil_matrix((1, variables), dtype=np.float64)
        lock[0, first_var] = 1.0
        constraints.append(LinearConstraint(lock.tocsr(), -np.inf, first.x[first_var] + 1e-9))

        if has_current and any(s.tier == "speculative" for s in self.scenarios):
            objective = np.zeros(variables)
            objective[r_speculative] = 1.0
            second = solve(objective)
            lock = lil_matrix((1, variables), dtype=np.float64)
            lock[0, r_speculative] = 1.0
            constraints.append(
                LinearConstraint(lock.tocsr(), -np.inf, second.x[r_speculative] + 1e-9)
            )

        objective = np.zeros(variables)
        invested = self.optimizer.batch.invested_exp.astype(np.float64)
        invested /= max(1.0, invested.max(initial=0.0))
        objective[:n_artifacts] = option_values + invested * 1e-6
        final = solve(objective)
        return final.x[:n_artifacts] > 0.5

    def analyze(
        self,
        free: int,
        *,
        pinned_ids: Iterable[str] = (),
        option_values: NDArray[np.float64] | None = None,
    ) -> DeletionResult:
        if free < 0:
            raise ValueError("free must be non-negative")
        protected = self.optimizer.batch.protected_mask(pinned_ids)
        if free > np.count_nonzero(~protected):
            raise ValueError("requested deletion count exceeds unprotected inventory")
        if option_values is None:
            option_values = np.zeros(len(self.optimizer.batch), dtype=np.float64)
        if option_values.shape != (len(self.optimizer.batch),):
            raise ValueError("option_values has invalid shape")

        builds, groups, baselines = self._loadout_pool()
        deleted = self._solve_milp(
            free, builds, groups, baselines, protected, option_values
        )

        available = ~deleted
        regrets: list[ScenarioRegret] = []
        verified = True
        for scenario, baseline in zip(self.scenarios, baselines):
            base_build = self.optimizer.optimize(scenario, top_k=1)[0]
            retained = self.optimizer.optimize(scenario, available=available, top_k=1)
            if retained:
                retained_build = retained[0]
                retained_utility = retained_build.utility
                retained_indices: tuple[int, ...] = retained_build.indices
            else:
                retained_utility = -np.inf
                retained_indices = ()
            regret = _regret(baseline, retained_utility)
            if regret > 1e-8:
                # Non-zero regret is valid, but this flag tells callers that
                # the candidate pool was verified through a full re-search.
                verified &= np.isfinite(retained_utility)
            regrets.append(
                ScenarioRegret(
                    scenario.id,
                    scenario.tier,
                    baseline,
                    retained_utility,
                    regret,
                    base_build.indices,
                    retained_indices,
                )
            )

        indices = tuple(int(i) for i in np.flatnonzero(deleted))
        return DeletionResult(
            indices,
            tuple(str(self.optimizer.batch.ids[i]) for i in indices),
            tuple(regrets),
            "scipy-milp",
            verified,
        )
