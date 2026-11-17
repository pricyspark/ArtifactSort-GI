"""Research-library encoding regressions, not game certification. Codex assisted."""

from pathlib import Path

import pytest

from artifact_sort.library import load_library, load_mechanics
from scripts.validate_scenario_library import validate

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def compiled():
    library = load_library(ROOT / "scenarios/library.json")
    mechanics = load_mechanics(ROOT / "scenarios/library.mechanics.json")
    return library.compile(mechanics, allow_draft=True)


def evaluate(compiled, key, additions=None, counts=None):
    scenario = compiled.scenarios[key]
    return scenario.evaluate(
        additions or {},
        counts if counts is not None else scenario.definition.sets[0],
        main_stats={
            slot: values[0] for slot, values in scenario.definition.mains.items()
        },
    )


def test_offline_reference_cases_and_coverage():
    report = validate()
    assert report["result"] == "passed-encoding-checks"
    assert report["counts"]["compiled_scenarios"] == 78
    assert report["counts"]["component_cases"] >= 91
    assert not report["game_validated"]


def test_golden_troupe_activation_and_incomplete_counts(compiled):
    full = evaluate(compiled, "fischl-offfield-golden")
    onfield = evaluate(compiled, "fischl-offfield-golden-onfield")
    two_piece = evaluate(compiled, "fischl-offfield-golden", counts={"GoldenTroupe": 2})
    no_set = evaluate(compiled, "fischl-offfield-golden", counts={})
    assert full.channels["damage_bonus"] == pytest.approx(0.7)
    assert onfield.channels["damage_bonus"] == pytest.approx(0.45)
    assert two_piece.channels["damage_bonus"] == pytest.approx(0.2)
    assert no_set.channels["damage_bonus"] == 0
    assert not two_piece.feasible and not no_set.feasible


def test_emblem_uses_effective_er_and_caps_at_75_percent(compiled):
    result = evaluate(compiled, "xingqiu-burst-emblem", {"enerRech_": 2})
    two = evaluate(compiled, "xingqiu-burst-emblem", counts={"EmblemOfSeveredFate": 2})
    assert result.channels["damage_bonus"] == 0.75
    assert result.effective_stats["enerRech_"] == pytest.approx(1 + 0.6125318 + 0.2 + 2)
    assert two.channels["damage_bonus"] == 0
    assert any("enerRech_" in violation for violation in two.violations)


def test_received_healing_adds_to_outgoing_bonus(compiled):
    active = evaluate(compiled, "barbara-healer-maiden", {"heal_": 0.359})
    expired = evaluate(compiled, "barbara-healer-maiden-buff-expired", {"heal_": 0.359})
    base = active.effective_stats["hp"] * 0.0135 + 158.902
    assert active.score == pytest.approx(base * (1 + 0.15 + 0.359 + 0.2))
    assert expired.score == pytest.approx(base * (1 + 0.15 + 0.359))
    assert active.effective_stats["heal_"] == expired.effective_stats["heal_"]


def test_shield_absorption_uses_recipient_and_flat_term(compiled):
    result = evaluate(compiled, "zhongli-shield-double-hp")
    expected_hp = 14695.093176 * (1 + 0.469199 + 0.2 + 0.2)
    assert result.effective_stats["hp"] == pytest.approx(expected_hp)
    assert result.score == pytest.approx(
        (expected_hp * 0.2304 + 2711.5093) * 1.5 * 1.25
    )
    fresh = evaluate(compiled, "zhongli-shield-double-hp-no-fortify")
    assert fresh.score == pytest.approx(result.score / 1.25)


def test_hyperbloom_ignores_atk_crit_and_preserves_em(compiled):
    key = "kukishinobu-hyperbloom-paradise"
    ordinary = evaluate(compiled, key, {"eleMas": 500})
    offensive = evaluate(
        compiled,
        key,
        {"eleMas": 500, "atk": 1000, "atk_": 1, "critRate_": 1, "critDMG_": 2},
    )
    assert offensive.score == ordinary.score
    mastery = 165.384 + 80 + 500
    assert ordinary.score == pytest.approx(
        1446.8535 * 3 * (1 + 16 * mastery / (2000 + mastery) + 0.8) * 0.9
    )
    assert evaluate(compiled, key, {"eleMas": 600}).score > ordinary.score
    assert (
        compiled.scenarios[key].definition.family
        != compiled.scenarios["raidenshogun-hyperbloom-paradise"].definition.family
    )
    assert (
        compiled.scenarios[key].definition.family
        != compiled.scenarios["kukishinobu-healer-mixed"].definition.family
    )


def test_nahida_mixed_scaling_caps_and_deepwood(compiled):
    key = "nahida-spread-deepwood"
    capped = evaluate(compiled, key, {"eleMas": 1500})
    assert capped.channels["damage_bonus"] == 0.8
    assert capped.channels["talent_crit_rate"] == 0.24
    assert capped.channels["resistance_shred"] == 0.3
    assert evaluate(compiled, key, {"atk": 500}).score > evaluate(compiled, key).score
    assert (
        evaluate(compiled, key, {"eleMas": 500}).score > evaluate(compiled, key).score
    )
    expired = evaluate(
        compiled, "nahida-spread-deepwood-debuff-expired", {"eleMas": 1500}
    )
    assert capped.score / expired.score == pytest.approx(1.1 / 0.9)


def test_parameter_inheritance_and_structural_families(compiled):
    parent = compiled.scenarios["neuvillette-charged-hunter"].definition
    variant = compiled.scenarios["neuvillette-charged-hunter-hp80"].definition
    assert variant.family == parent.family
    assert variant.conditions["hp_fraction"] == 0.8
    assert variant.scoring_formula == parent.scoring_formula
    for scenario in compiled.select(include_speculative=True):
        definition = scenario.definition
        if definition.collection == "structural_variations":
            assert not definition.characters
            assert definition.family.startswith("archetype/")
