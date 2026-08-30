from __future__ import annotations

import numpy as np

from artifact_sort.model import from_good_data
from artifact_sort.outcomes import final_outcomes

from conftest import good_artifact


def test_batch_is_immutable_and_does_not_use_main_stat_sentinels(small_batch):
    assert small_batch.sub_rolls.shape == (10, 10)
    assert small_batch.final_stats().shape == (10, 19)
    assert not small_batch.sub_rolls.flags.writeable
    assert np.max(small_batch.sub_rolls) < 80
    assert np.all(small_batch.locked)
    assert not np.any(small_batch.protected_mask())


def test_exact_one_roll_outcomes_sum_to_one():
    artifact = good_artifact(0, "flower", level=16)
    batch = from_good_data({"format": "GOOD", "version": 3, "artifacts": [artifact]})
    outcomes = final_outcomes(batch, 0)
    assert len(outcomes.sub_rolls) == 16
    assert np.isclose(outcomes.probabilities.sum(), 1.0)
    assert np.allclose(outcomes.probabilities, 1 / 16)


def test_missing_initial_history_has_explicit_posterior():
    artifact = good_artifact(0, "flower", level=8)
    artifact.pop("totalRolls")
    for substat in artifact["substats"]:
        substat.pop("initialValue")
    batch = from_good_data({"format": "GOOD", "version": 3, "artifacts": [artifact]})
    assert batch.uncertain_history[0]
    assert batch.four_line_probability[0] == 0.5
    assert batch.remaining_random_rolls()[0] == 3
