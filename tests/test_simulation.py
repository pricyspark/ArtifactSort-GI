from __future__ import annotations

import numpy as np

from artifact_sort.cache import ResultCache
from artifact_sort.model import SUBSTAT_MAX
from artifact_sort.scenarios import Scenario
from artifact_sort.simulation import (
    CritValuePolicy,
    CritValueUpgradePolicy,
    RandomDeletionPolicy,
    RandomUpgradePolicy,
    _hidden_stats,
    benchmark_deletion,
    benchmark_upgrades,
    summarize_deletion_benchmark,
    summarize_upgrade_benchmark,
)
from artifact_sort.upgrades import _outcome_stats


def test_deletion_benchmark_is_reproducible_and_has_oracle(small_batch):
    scenario = Scenario(id="test", tier="current")
    policies = [RandomDeletionPolicy(), CritValuePolicy()]
    first = benchmark_deletion(
        small_batch, [scenario], [], policies, free=1, trials=1, seed=42, curve_points=1
    )
    second = benchmark_deletion(
        small_batch, [scenario], [], policies, free=1, trials=1, seed=42, curve_points=1
    )
    assert first == second
    assert "clairvoyant-oracle" in first.confidence
    assert all(trial.slots_freed == 1 for trial in first.trials)
    summary = summarize_deletion_benchmark(first, [scenario])
    assert summary["benchmark"] == "deletion"
    assert summary["slots_freed"] == 1
    policies = summary["policies"]
    assert isinstance(policies, list)
    assert policies[0]["rank"] == 1
    assert policies[-1]["policy"] == "clairvoyant-oracle"
    assert policies[-1]["rank"] is None


def test_deletion_benchmark_computes_deterministic_policy_once(small_batch):
    class CountingPolicy:
        name = "counting"
        stochastic = False

        def __init__(self):
            self.calls = 0

        def delete(self, batch, scenarios, free, rng, *, cache=None):
            self.calls += 1
            return CritValuePolicy().delete(
                batch, scenarios, free, rng, cache=cache
            )

    policy = CountingPolicy()
    benchmark_deletion(
        small_batch,
        [Scenario(id="test", tier="current")],
        [],
        [policy],
        free=1,
        trials=3,
        seed=42,
        curve_points=1,
    )
    assert policy.calls == 1


def test_deletion_benchmark_resumes_cached_trials(tmp_path, small_batch):
    scenario = Scenario(id="test", tier="current")
    policies = [RandomDeletionPolicy(), CritValuePolicy()]
    path = tmp_path / "cache.sqlite"
    first_cache = ResultCache(path)
    first = benchmark_deletion(
        small_batch,
        [scenario],
        [],
        policies,
        free=1,
        trials=2,
        seed=42,
        curve_points=1,
        cache=first_cache,
    )
    assert first_cache.summary()["by_namespace"]["benchmark-deletion-trial"][
        "writes"
    ] == 2

    second_cache = ResultCache(path)
    second = benchmark_deletion(
        small_batch,
        [scenario],
        [],
        policies,
        free=1,
        trials=2,
        seed=42,
        curve_points=1,
        cache=second_cache,
    )
    assert second == first
    assert second_cache.summary()["by_namespace"]["benchmark-deletion-trial"][
        "hits"
    ] == 2


def test_simulated_rolls_preserve_main_stats(small_batch):
    current = small_batch.final_stats()
    tapes = [[] for _ in range(len(small_batch))]
    tapes[0] = [(8, 10)]
    hidden = _hidden_stats(small_batch, tapes)
    assert hidden[0, 0] == current[0, 0]
    assert hidden[0, 8] == current[0, 8] + SUBSTAT_MAX[8]

    outcome_rolls = np.repeat(small_batch.sub_rolls[0][None, :], 2, axis=0)
    outcome_rolls[1, 8] += 10
    outcomes = _outcome_stats(
        current[0], small_batch.sub_rolls[0], outcome_rolls
    )
    assert np.all(outcomes[:, 0] == current[0, 0])
    assert outcomes[1, 8] == current[0, 8] + SUBSTAT_MAX[8]


def test_upgrade_benchmark_reports_cost_and_calibration(small_batch):
    result = benchmark_upgrades(
        small_batch,
        [Scenario(id="test")],
        [RandomUpgradePolicy(), CritValueUpgradePolicy()],
        trials=1,
        seed=3,
        max_checkpoints=2,
        calibration_candidates=1,
    )
    assert len(result.trials) == 2
    assert len(result.calibration) == 5
    assert all(trial.reached_perfect for trial in result.trials)
    summary = summarize_upgrade_benchmark(result, [Scenario(id="test")])
    assert summary["benchmark"] == "upgrade"
    assert summary["progress_target_pct"] == 5.0
    policies = summary["policies"]
    assert isinstance(policies, list)
    assert len(policies) == 2
    assert policies[0]["rank"] == 1
