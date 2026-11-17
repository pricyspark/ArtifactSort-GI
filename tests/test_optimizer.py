from __future__ import annotations

import numpy as np

from artifact_sort.model import from_good_data
from artifact_sort.optimizer import BuildOptimizer, DeletionAnalyzer
from artifact_sort.scenarios import Scenario, SetStrategy, STAT_INDEX

from conftest import good_artifact


def test_complete_build_optimizer_selects_best_per_slot(small_batch):
    scenario = Scenario(id="test", tier="current", damage_stat="pyro_dmg_")
    result = BuildOptimizer(small_batch, candidate_limit=10).optimize(scenario)[0]
    assert set(result.indices) == {1, 3, 5, 7, 9}
    assert result.utility > 0


def test_threshold_is_hard_constraint(small_batch):
    impossible = Scenario(
        id="er",
        objective="support",
        constraints=((STAT_INDEX["enerRech_"], 10_000.0),),
    )
    assert BuildOptimizer(small_batch).optimize(impossible) == []


def test_set_strategies_are_alternative_legal_compositions(small_batch):
    scenario = Scenario(
        id="sets",
        set_strategies=(
            SetStrategy((("MissingSet", 4),), source="test"),
            SetStrategy((("TestSet", 4),), source="test"),
        ),
    )

    result = BuildOptimizer(small_batch, candidate_limit=10).optimize(scenario)

    assert result
    assert all(small_batch.set_keys[index] == "TestSet" for index in result[0].indices)


def test_set_strategy_preserves_weaker_in_set_screening_candidates():
    artifacts = []
    slots = ("flower", "plume", "sands", "goblet", "circlet")
    for index, slot in enumerate(slots):
        artifacts.append(good_artifact(index * 2, slot, set_key="NeededSet"))
        artifacts.append(
            good_artifact(index * 2 + 1, slot, high=True, set_key="StrongerOffSet")
        )
    batch = from_good_data({"format": "GOOD", "version": 3, "artifacts": artifacts})
    scenario = Scenario(
        id="niche-set",
        set_strategies=(SetStrategy((("NeededSet", 4),), source="test"),),
    )

    result = BuildOptimizer(batch, candidate_limit=1).optimize(scenario)

    assert result
    assert sum(batch.set_keys[index] == "NeededSet" for index in result[0].indices) >= 4


def test_missing_strategy_set_does_not_create_float_indices():
    artifacts = []
    slots = ("flower", "plume", "sands", "goblet", "circlet")
    for index, slot in enumerate(slots):
        artifacts.append(good_artifact(index * 2, slot, set_key="OtherSetA"))
        artifacts.append(
            good_artifact(index * 2 + 1, slot, high=True, set_key="OtherSetB")
        )
    batch = from_good_data({"format": "GOOD", "version": 3, "artifacts": artifacts})
    scenario = Scenario(
        id="unavailable-set",
        set_strategies=(SetStrategy((("MissingSet", 4),), source="test"),),
    )

    result = BuildOptimizer(batch, candidate_limit=1).optimize(scenario)

    assert result == []


def test_delete_frees_exact_count_and_ignores_ordinary_lock(small_batch):
    scenario = Scenario(id="test", tier="current")
    updates = []
    result = DeletionAnalyzer(
        BuildOptimizer(small_batch, candidate_limit=10), [scenario], loadouts_per_scenario=10
    ).analyze(2, progress=lambda value, message: updates.append((value, message)))
    assert len(result.deleted_indices) == 2
    assert result.solver == "scipy-milp"
    assert max(regret.regret for regret in result.regrets) == 0
    assert len(updates) >= 5
    assert [value for value, _ in updates] == sorted(value for value, _ in updates)
    assert updates[-1][0] == 1.0


def test_astral_and_equipped_are_protected(small_batch):
    starred = small_batch.starred.copy()
    starred[0] = True
    locations = small_batch.locations.copy()
    locations[2] = "Traveler"
    protected = small_batch.__class__(
        ids=small_batch.ids,
        set_keys=small_batch.set_keys,
        slots=small_batch.slots,
        main_stats=small_batch.main_stats,
        rarities=small_batch.rarities,
        levels=small_batch.levels,
        starting_lines=small_batch.starting_lines,
        sub_rolls=small_batch.sub_rolls,
        initial_sub_rolls=small_batch.initial_sub_rolls,
        uncertain_history=small_batch.uncertain_history,
        four_line_probability=small_batch.four_line_probability,
        locations=locations,
        locked=small_batch.locked,
        starred=starred,
        invested_exp=small_batch.invested_exp,
    )
    assert np.array_equal(np.flatnonzero(protected.protected_mask()), (0, 2))
