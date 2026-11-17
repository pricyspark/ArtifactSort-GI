from __future__ import annotations

import numpy as np

from artifact_sort.cache import ResultCache
from artifact_sort.model import concatenate_batches, from_good_data
from artifact_sort.optimizer import BuildOptimizer
from artifact_sort.outcomes import cached_final_outcomes
from artifact_sort.scenarios import BuiltinEvaluator, Scenario
from artifact_sort.upgrades import UpgradeAnalyzer

from conftest import good_artifact


class CountingEvaluator(BuiltinEvaluator):
    version = "counting-v1"

    def __init__(self) -> None:
        self.evaluated_rows = 0

    def evaluate_batch(self, artifact_stats, scenario):
        self.evaluated_rows += len(artifact_stats)
        return super().evaluate_batch(artifact_stats, scenario)


def test_upgrade_analysis_reports_candidate_and_scenario_progress(small_batch):
    levels = small_batch.levels.copy()
    levels[:2] = 16
    unfinished = small_batch.with_states(levels=levels)
    updates = []

    UpgradeAnalyzer(
        BuildOptimizer(unfinished, candidate_limit=10),
        [Scenario(id="upgrade", tier="current")],
        complement_pool_size=4,
    ).analyze(
        max_candidates=2,
        progress=lambda value, message: updates.append((value, message)),
    )

    assert len(updates) == 3
    assert [value for value, _ in updates] == sorted(value for value, _ in updates)
    assert updates[-1][0] == 1.0
    assert "artifact 2 of 2" in updates[-1][1]


def test_artifact_outcomes_are_cached_by_state_not_inventory(tmp_path):
    first_artifact = good_artifact(0, "flower", level=16)
    first = from_good_data(
        {"format": "GOOD", "version": 3, "artifacts": [first_artifact]}
    )
    second_artifact = dict(first_artifact)
    second_artifact["id"] = "different-id"
    second = from_good_data(
        {"format": "GOOD", "version": 3, "artifacts": [second_artifact]}
    )
    cache = ResultCache(tmp_path / "cache.sqlite")

    expected = cached_final_outcomes(first, 0, cache)
    found = cached_final_outcomes(second, 0, cache)

    assert np.array_equal(found.sub_rolls, expected.sub_rolls)
    assert np.array_equal(found.probabilities, expected.probabilities)
    stats = cache.summary()["by_namespace"]["artifact-outcome"]
    assert stats == {"hits": 1, "misses": 1, "writes": 1}


def test_scenario_and_build_evaluations_survive_inventory_growth(
    tmp_path, small_batch
):
    cache = ResultCache(tmp_path / "cache.sqlite")
    scenario = Scenario(id="same-scenario", tier="current")

    first_evaluator = CountingEvaluator()
    first = BuildOptimizer(
        small_batch, first_evaluator, candidate_limit=10, cache=cache
    ).optimize(scenario, top_k=2)
    assert first_evaluator.evaluated_rows > 0

    repeated_evaluator = CountingEvaluator()
    repeated = BuildOptimizer(
        small_batch, repeated_evaluator, candidate_limit=10, cache=cache
    ).optimize(scenario, top_k=2)
    assert repeated_evaluator.evaluated_rows == 0
    assert repeated[0].indices == first[0].indices

    extra = from_good_data(
        {
            "format": "GOOD",
            "version": 3,
            "artifacts": [good_artifact(99, "flower", high=False)],
        }
    )
    expanded = concatenate_batches(small_batch, extra)
    expanded_evaluator = CountingEvaluator()
    expanded_result = BuildOptimizer(
        expanded, expanded_evaluator, candidate_limit=10, cache=cache
    ).optimize(scenario, top_k=2)

    assert expanded_evaluator.evaluated_rows == 0
    assert expanded_result[0].indices == first[0].indices
    stats = cache.summary()["by_namespace"]
    assert stats["loadout-pool"]["hits"] >= 1
    assert stats["build-evaluation"]["hits"] >= 1


def test_different_scenario_does_not_reuse_build_utility(tmp_path, small_batch):
    cache = ResultCache(tmp_path / "cache.sqlite")
    first = Scenario(id="first", damage_stat="pyro_dmg_")
    second = Scenario(id="second", damage_stat="hydro_dmg_")
    BuildOptimizer(
        small_batch, CountingEvaluator(), candidate_limit=10, cache=cache
    ).optimize(first)

    evaluator = CountingEvaluator()
    BuildOptimizer(
        small_batch, evaluator, candidate_limit=10, cache=cache
    ).optimize(second)
    assert evaluator.evaluated_rows > 0


def test_upgrade_potential_is_reused_across_deletion_counts_and_inventory_growth(
    tmp_path, small_batch
):
    levels = small_batch.levels.copy()
    levels[0] = 16
    unfinished = small_batch.with_states(levels=levels)
    cache = ResultCache(tmp_path / "cache.sqlite")
    scenario = Scenario(id="upgrade", tier="current")

    first_evaluator = CountingEvaluator()
    first = UpgradeAnalyzer(
        BuildOptimizer(
            unfinished, first_evaluator, candidate_limit=10, cache=cache
        ),
        [scenario],
        complement_pool_size=4,
    ).analyze(max_candidates=1)
    assert first_evaluator.evaluated_rows > 0

    repeated_evaluator = CountingEvaluator()
    repeated = UpgradeAnalyzer(
        BuildOptimizer(
            unfinished, repeated_evaluator, candidate_limit=10, cache=cache
        ),
        [scenario],
        complement_pool_size=4,
    ).analyze(max_candidates=1)
    assert repeated_evaluator.evaluated_rows == 0
    assert repeated == first

    extra = from_good_data(
        {
            "format": "GOOD",
            "version": 3,
            "artifacts": [good_artifact(99, "flower", high=False)],
        }
    )
    expanded = concatenate_batches(unfinished, extra)
    expanded_evaluator = CountingEvaluator()
    expanded_result = UpgradeAnalyzer(
        BuildOptimizer(
            expanded, expanded_evaluator, candidate_limit=10, cache=cache
        ),
        [scenario],
        complement_pool_size=4,
    ).analyze(max_candidates=1)

    assert expanded_evaluator.evaluated_rows == 0
    assert expanded_result[0].artifact_id == first[0].artifact_id
    potential_stats = cache.summary()["by_namespace"]["upgrade-potential"]
    assert potential_stats["hits"] == 2
    assert potential_stats["misses"] == 1
    assert potential_stats["writes"] == 1


def test_upgrade_potential_invalidates_when_epsilon_changes(tmp_path, small_batch):
    levels = small_batch.levels.copy()
    levels[0] = 16
    unfinished = small_batch.with_states(levels=levels)
    cache = ResultCache(tmp_path / "cache.sqlite")
    scenario = Scenario(id="upgrade", tier="current")
    UpgradeAnalyzer(
        BuildOptimizer(unfinished, CountingEvaluator(), candidate_limit=10, cache=cache),
        [scenario],
        epsilon=0.01,
        complement_pool_size=4,
    ).analyze(max_candidates=1)

    evaluator = CountingEvaluator()
    UpgradeAnalyzer(
        BuildOptimizer(unfinished, evaluator, candidate_limit=10, cache=cache),
        [scenario],
        epsilon=0.05,
        complement_pool_size=4,
    ).analyze(max_candidates=1)
    assert evaluator.evaluated_rows > 0


def test_upgrade_potential_invalidates_when_complement_pool_changes(
    tmp_path, small_batch
):
    levels = small_batch.levels.copy()
    levels[0] = 16
    unfinished = small_batch.with_states(levels=levels)
    cache = ResultCache(tmp_path / "cache.sqlite")
    scenario = Scenario(id="upgrade", tier="current")
    UpgradeAnalyzer(
        BuildOptimizer(unfinished, CountingEvaluator(), candidate_limit=10, cache=cache),
        [scenario],
        complement_pool_size=4,
    ).analyze(max_candidates=1)

    better_plume = good_artifact(100, "plume", high=True)
    for substat in better_plume["substats"]:
        substat["value"] *= 1.25
    expanded = concatenate_batches(
        unfinished,
        from_good_data(
            {"format": "GOOD", "version": 3, "artifacts": [better_plume]}
        ),
    )
    evaluator = CountingEvaluator()
    UpgradeAnalyzer(
        BuildOptimizer(expanded, evaluator, candidate_limit=10, cache=cache),
        [scenario],
        complement_pool_size=4,
    ).analyze(max_candidates=1)

    assert evaluator.evaluated_rows > 0
    potential_stats = cache.summary()["by_namespace"]["upgrade-potential"]
    assert potential_stats["hits"] == 0
    assert potential_stats["misses"] == 2
