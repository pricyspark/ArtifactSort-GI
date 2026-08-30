from __future__ import annotations

import numpy as np

from artifact_sort.farming import FarmConfig, generate_artifacts, simulate_farming
from artifact_sort.scenarios import Scenario


def test_synthetic_stream_is_reproducible_and_legal():
    first = generate_artifacts(
        20,
        np.random.default_rng(7),
        sets=("A", "B"),
        four_line_probability=0.2,
    )
    second = generate_artifacts(
        20,
        np.random.default_rng(7),
        sets=("A", "B"),
        four_line_probability=0.2,
    )
    assert first.fingerprint() == second.fingerprint()
    assert np.all(np.count_nonzero(first.sub_rolls, axis=1) == 4)
    assert set(first.set_keys) <= {"A", "B"}


def test_zero_progress_farm_target_costs_no_resin(small_batch):
    result = simulate_farming(
        small_batch,
        [Scenario(id="test")],
        increase=0.0,
        config=FarmConfig(max_resin=100, check_every_drops=1),
        trials=2,
        seed=9,
    )
    assert result.median_resin == 0
    assert all(trial.reached_target for trial in result.trials)
