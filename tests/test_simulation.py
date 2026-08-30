from __future__ import annotations

from artifact_sort.scenarios import Scenario
from artifact_sort.simulation import (
    CritValuePolicy,
    CritValueUpgradePolicy,
    RandomDeletionPolicy,
    RandomUpgradePolicy,
    benchmark_deletion,
    benchmark_upgrades,
)


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
