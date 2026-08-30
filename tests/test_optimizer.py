from __future__ import annotations

import numpy as np

from artifact_sort.optimizer import BuildOptimizer, DeletionAnalyzer
from artifact_sort.scenarios import Scenario, STAT_INDEX


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


def test_delete_frees_exact_count_and_ignores_ordinary_lock(small_batch):
    scenario = Scenario(id="test", tier="current")
    result = DeletionAnalyzer(
        BuildOptimizer(small_batch, candidate_limit=10), [scenario], loadouts_per_scenario=10
    ).analyze(2)
    assert len(result.deleted_indices) == 2
    assert result.solver == "scipy-milp"
    assert max(regret.regret for regret in result.regrets) == 0


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
