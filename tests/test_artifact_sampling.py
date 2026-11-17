from dataclasses import replace

import numpy as np
import pytest

from artifact_sort.artifact_sampling import (
    finish_artifact,
    sample_completed_inventory,
    sample_slot,
    sampling_rules,
)
from artifact_sort.inventory import Artifact, Inventory
from artifact_sort.reference_profiles import score_population


def starting(identity="one", **kwargs):
    return Artifact(
        identity,
        "TestSet",
        "flower",
        "hp",
        5,
        0,
        {"atk": 13.62, "critRate_": 0.0272, "enerRech_": 0.0453},
        {},
        **kwargs,
    )


def test_population_covers_whole_slot_with_legal_completed_artifacts():
    rules = sampling_rules()
    population = sample_slot("goblet", "TestSet", 2000, rules, seed=7)
    observed = {a.main_stat for a in population.artifacts}
    assert observed == set(rules.main_probabilities["goblet"])
    # A deterministic broad sanity check; not evidence that the model matches game data.
    pyro_frequency = (
        sum(a.main_stat == "pyro_dmg_" for a in population.artifacts) / 2000
    )
    assert 0.03 < pyro_frequency < 0.07
    assert not rules.validated
    for artifact in population.artifacts:
        assert artifact.level == 20 and len(artifact.substats) == 4
        assert artifact.main_stat not in artifact.substats
        assert not artifact.hidden_substats
    assert population == sample_slot("goblet", "TestSet", 2000, rules, seed=7)


def test_upgrade_tapes_survive_removal_order_and_substat_order():
    rules = sampling_rules()
    first, second = starting("one", locked=True, starred=True), starting("two")
    together = sample_completed_inventory(
        Inventory((first, second)), rules, seed=3, trial=9
    )
    alone = sample_completed_inventory(Inventory((first,)), rules, seed=3, trial=9)
    reordered = replace(first, substats=dict(reversed(tuple(first.substats.items()))))
    reordered_trial = sample_completed_inventory(
        Inventory((second, reordered)), rules, seed=3, trial=9
    )
    assert together.artifacts[0] == alone.artifacts[0] == reordered_trial.artifacts[1]
    assert together.artifacts[0].locked and together.artifacts[0].starred
    assert together.artifacts[0].id == "one"
    assert sample_completed_inventory(together, rules, seed=55, trial=22) == together


def test_hidden_line_reveal_and_remaining_checkpoint_count():
    rules = sampling_rules()
    initial = replace(starting(), hidden_substats={"def": 16.2})
    completed = finish_artifact(initial, rules, np.random.default_rng(2))
    assert set(completed.substats) == set(initial.substats) | {"def"}
    # +4 reveals; four later checkpoints improve existing lines. Summing in
    # per-stat roll units checks the event count independent of chosen hit keys.
    constant_rules = replace(rules, rolls={key: (1.0,) for key in rules.rolls})
    completed = finish_artifact(initial, constant_rules, np.random.default_rng(2))
    assert sum(completed.substats.values()) - sum(
        initial.substats.values()
    ) == pytest.approx(16.2 + 4)
    midway = replace(completed, level=19)
    last = finish_artifact(midway, constant_rules, np.random.default_rng(3))
    assert sum(last.substats.values()) - sum(midway.substats.values()) == pytest.approx(
        1
    )


def test_observed_values_are_preserved_without_roll_rounding():
    initial = replace(
        starting(),
        level=16,
        substats={
            "atk": 13.62123,
            "critRate_": 0.031234,
            "enerRech_": 0.0453123,
            "def": 16.2123,
        },
    )
    rules = sampling_rules()
    result = finish_artifact(initial, rules, np.random.default_rng(5))
    changed = [
        key for key in initial.substats if result.substats[key] != initial.substats[key]
    ]
    assert len(changed) == 1
    key = changed[0]
    assert any(
        result.substats[key] - initial.substats[key] == pytest.approx(value)
        for value in rules.rolls[key]
    )


@pytest.mark.parametrize(
    "piece, message",
    [
        (replace(starting(), rarity=4), "five-star"),
        (replace(starting(), level=4), "missing observed"),
        (replace(starting(), substats={"atk": 13.62}), "missing observed"),
    ],
)
def test_unsupported_or_missing_outcome_inputs_are_explicit(piece, message):
    with pytest.raises(ValueError, match=message):
        finish_artifact(piece, sampling_rules(), np.random.default_rng(0))


def goblet(identity, main):
    return Artifact(identity, "TestSet", "goblet", main, 5, 20, {}, {})


def test_percentiles_mix_main_occurrence_mass_and_overlapping_scores():
    population = Inventory(
        (goblet("pyro", "pyro_dmg_"), goblet("atk", "atk_"), goblet("hp", "hp_"))
    )
    scored = score_population(
        population, {"pyro_dmg_": 2, "atk_": 1}, probabilities=[0.1, 0.3, 0.6]
    )
    pyro, attack, hp = scored.scores
    assert scored.percentile_interval(float(pyro)) == pytest.approx((0.9, 1))
    assert scored.percentile_interval(float(attack)) == pytest.approx((0.6, 0.9))
    assert scored.percentile_interval(float(hp)) == pytest.approx((0, 0.6))
    # The top 20% crosses main types: it cannot be obtained solely by taking
    # a conditional percentile within the 10%-occurrence Pyro stratum.
    assert {a.id for a in scored.band(0.8, 1).artifacts} == {"pyro", "atk"}
    equal = score_population(
        population, {"pyro_dmg_": 1, "atk_": 1}, probabilities=[0.1, 0.3, 0.6]
    )
    assert equal.scores[0] == equal.scores[1]
    assert equal.percentile_interval(float(equal.scores[0])) == pytest.approx((0.6, 1))
    assert {a.id for a in equal.band(0.94, 0.96).artifacts} == {"pyro", "atk"}


def test_ties_preserve_all_candidates_and_signed_weights_are_allowed():
    pieces = Inventory((goblet("one", "hp_"), goblet("two", "atk_")))
    tied = score_population(pieces, {})
    assert tied.percentile_interval(0) == (0, 1)
    assert tied.band(0.79, 0.81) == pieces
    assert tied.band(0.94, 0.96) == pieces
    signed = score_population(pieces, {"hp_": -1})
    assert signed.scores[0] < signed.scores[1]
    assert not signed.scores.flags.writeable


@pytest.mark.parametrize("mass", [[0.1, 0.1], [0.5, float("nan")], [1, 0]])
def test_invalid_stratified_probability_masses_are_rejected(mass):
    with pytest.raises(ValueError, match="probabilities"):
        score_population(
            Inventory((goblet("one", "hp_"), goblet("two", "atk_"))),
            {},
            probabilities=mass,
        )


def test_sampling_rules_reject_invalid_probabilities():
    with pytest.raises(ValueError, match="four-line"):
        replace(sampling_rules(), four_line_probability=float("nan"))
    with pytest.raises(ValueError, match="main probability"):
        rules = sampling_rules()
        replace(
            rules,
            main_probabilities={**rules.main_probabilities, "flower": {"hp": 0.9}},
        )


def test_sampling_fingerprint_changes_with_assumptions_and_roll_model():
    rules = sampling_rules()
    assert replace(rules).fingerprint == rules.fingerprint
    assert replace(rules, four_line_probability=0.3).fingerprint != rules.fingerprint
    assert replace(rules, validated=True).fingerprint != rules.fingerprint
    changed_rolls = {**rules.rolls, "atk": (14.0,)}
    changed = replace(rules, rolls=changed_rolls)
    changed_rolls["atk"] = (15.0,)
    assert changed.rolls["atk"] == (14.0,)
    assert changed.fingerprint != rules.fingerprint


def test_quantile_uses_whole_slot_mass_and_preserves_boundary_ties():
    population = Inventory(
        (goblet("pyro", "pyro_dmg_"), goblet("atk", "atk_"), goblet("hp", "hp_"))
    )
    scored = score_population(
        population, {"pyro_dmg_": 2, "atk_": 1}, probabilities=[0.1, 0.3, 0.6]
    )
    assert tuple(a.id for a in scored.quantile(0.8).artifacts) == ("atk",)
    assert tuple(a.id for a in scored.quantile(0.95).artifacts) == ("pyro",)
    assert scored.quantile(0.99) == scored.quantile(1)
    tied = score_population(population, {})
    assert tied.quantile(0.8) == tied.quantile(0.99) == population
    with pytest.raises(ValueError, match="percentile"):
        tied.quantile(0)


def test_order_statistic_bounds_expose_insufficient_tail_samples():
    scored = score_population(
        Inventory((goblet("one", "hp_"), goblet("two", "atk_"))), {"atk_": 1}
    )
    lower, upper = scored.quantile_interval(0.99)
    assert upper == float("inf")
    assert lower <= scored.scores.max()
    stratified = score_population(
        Inventory((goblet("one", "hp_"), goblet("two", "atk_"))),
        {},
        probabilities=[0.1, 0.9],
    )
    with pytest.raises(ValueError, match="IID"):
        stratified.quantile_interval(0.8)
