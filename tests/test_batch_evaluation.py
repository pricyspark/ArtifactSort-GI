"""Scalar parity, search quality, and meaningful work-reduction checks."""

import numpy as np
import pytest

from artifact_sort.batch_evaluation import evaluate_batch
from artifact_sort.formulas import EvaluationError
from artifact_sort.inventory import inventory_from_good
from artifact_sort.library import load_library
from artifact_sort.library_cache import AnalysisCache
from artifact_sort.library_search import search_builds
from artifact_sort.model import SLOT_KEYS, STAT_KEYS
from test_inventory_search import artifact, good, inventory, scenario
from test_library import ROOT, compile_doc, document, effect, mechanics, op, stat


def assert_rows_match(target, additions, counts, mains=None):
    batch = evaluate_batch(target, additions, counts, main_stats=mains)
    for i in range(len(additions)):
        scalar = target.evaluate(
            dict(zip(STAT_KEYS, additions[i])),
            {key: int(values[i]) for key, values in counts.items()},
            main_stats=None if mains is None else {slot: values[i] for slot, values in mains.items()},
        )
        row = batch.row(i)
        assert row.score == pytest.approx(scalar.score, rel=1e-13)
        assert row.effective_stats == pytest.approx(scalar.effective_stats, rel=1e-13)
        assert row.channels == pytest.approx(scalar.channels, rel=1e-13)
        assert row.violations == scalar.violations
        assert batch.feasible[i] == scalar.feasible
    return batch


def test_example_scenarios_match_scalar_over_random_stats_sets_and_mains():
    library = load_library(ROOT / "scenarios/library.example.json")
    compiled = library.compile(mechanics({"mechanics": library.mechanics}), allow_draft=True)
    rng = np.random.default_rng(42)
    additions = rng.uniform(0, 2, size=(100, len(STAT_KEYS)))
    for i, key in enumerate(STAT_KEYS):
        if not key.endswith("_"):
            additions[:, i] *= 1000
    counts = {"TestSet": np.arange(100) % 6, "OtherSet": 5 - np.arange(100) % 6}
    mains = {"flower": np.full(100, "hp"), "plume": np.full(100, "atk"),
             "sands": np.resize(["atk_", "enerRech_"], 100),
             "goblet": np.full(100, "cryo_dmg_"), "circlet": np.full(100, "critRate_")}
    for target in compiled.scenarios.values():
        assert_rows_match(target, additions, counts, mains)


def test_staged_conversions_caps_multipliers_and_conditional_rows_match_scalar():
    doc = document()
    doc["established"][0].update(
        base={"atk": 100, "hp": 1000, "enerRech_": 1, "critRate_": 0.05},
        minimums={"enerRech_": 1.2}, maximums={"hp": 2000},
        sets=[{"TestSet": 4}, {"OtherSet": 2}], mains={"sands": ["atk_"]},
    )
    doc["channels"] = {"bonus": {"unit": "scalar", "combine": "multiply"}}
    doc["scoring_formulas"]["score"]["expression"] = op(
        "multiply", stat("atk"), {"channel": "bonus"},
        op("subtract", 2, op("clamp", stat("critRate_"), 0, 1)),
    )
    effect(doc, "er", 0.2, stage="static", target="stats.enerRech_",
           when={"set": "TestSet", "pieces": 2})
    effect(doc, "hp-growth", 0.2, stage="conversion", target="stats.hp_")
    effect(doc, "hp-atk", op("multiply", stat("hp", "raw"), {"value": 0.1, "unit": "atk/hp"}),
           stage="conversion", unit="atk", target="stats.atk")
    effect(doc, "bonus", op("max", 1, op("min", stat("enerRech_"), 3)),
           when={"set": "TestSet", "pieces": 4})
    effect(doc, "second", 1.5, when={"any": [{"set": "OtherSet", "pieces": 2},
                                             {"not": {"set": "TestSet", "pieces": 4}}]})
    target = compile_doc(doc).scenarios["one"]
    rng = np.random.default_rng(9)
    values = rng.uniform(0, 1, (60, len(STAT_KEYS)))
    counts = {"TestSet": np.arange(60) % 6, "OtherSet": 5 - np.arange(60) % 6}
    mains = {"sands": np.resize(["atk_", "enerRech_"], 60)}
    assert_rows_match(target, values, counts, mains)


def test_inactive_rows_do_not_evaluate_undefined_arithmetic():
    doc = document()
    doc["established"][0]["base"]["enerRech_"] = 0
    doc["channels"] = {"bonus": {"unit": "scalar", "combine": "add"}}
    effect(doc, "division", op("divide", 1, stat("enerRech_")),
           when={"set": "TestSet", "pieces": 4})
    values = np.zeros((2, len(STAT_KEYS)))
    values[1, STAT_KEYS.index("enerRech_")] = 1
    target = compile_doc(doc).scenarios["one"]
    assert_rows_match(target, values, {"TestSet": np.array([0, 4])})
    with pytest.raises(EvaluationError, match="division by zero"):
        evaluate_batch(target, values, {"TestSet": np.array([4, 4])})


def test_activation_short_circuits_missing_conditions():
    doc = document()
    doc["channels"] = {"bonus": {"unit": "scalar", "combine": "add"}}
    effect(doc, "unreachable", op("divide", 1, 0), when={"all": [
        {"set": "TestSet", "pieces": 4}, {"condition": "missing", "equals": True}]})
    target = compile_doc(doc).scenarios["one"]
    values = np.zeros((2, len(STAT_KEYS)))
    assert_rows_match(target, values, {"TestSet": np.array([0, 2])})
    with pytest.raises(EvaluationError, match="missing activation condition"):
        evaluate_batch(target, values, {"TestSet": np.array([0, 4])})


@pytest.mark.parametrize("expression, message", [
    (op("multiply", stat("atk"), op("divide", 1, 0)), "division by zero"),
    (op("multiply", stat("atk"), op("clamp", 1, 2, 0)), "reversed clamp"),
    (op("multiply", stat("atk"), 1e308), "nonfinite"),
])
def test_batch_arithmetic_errors(expression, message):
    doc = document()
    doc["scoring_formulas"]["score"]["expression"] = expression
    with pytest.raises(EvaluationError, match=message):
        evaluate_batch(compile_doc(doc).scenarios["one"], np.zeros((2, len(STAT_KEYS))), {})


def test_batch_threshold_tolerance_matches_scalar():
    target = scenario(minimums={"enerRech_": 1.2}, maximums={"enerRech_": 1.4})
    values = np.zeros((6, len(STAT_KEYS)))
    values[:, STAT_KEYS.index("enerRech_")] = [0.2 - 1e-13, 0.2 - 1e-9, 0.2, 0.4, 0.4 + 1e-13, 0.4 + 1e-9]
    result = assert_rows_match(target, values, {})
    assert result.feasible.tolist() == [True, False, True, True, True, False]


def test_batch_addition_preserves_scalar_cancellation_behavior():
    doc = document()
    doc["scoring_formulas"]["score"]["expression"] = op(
        "add", {"value": 1e16, "unit": "atk"},
        stat("atk"), {"value": -1e16, "unit": "atk"})
    values = np.zeros((3, len(STAT_KEYS)))
    values[:, STAT_KEYS.index("atk")] = [0.125, 1, 3]
    assert_rows_match(compile_doc(doc).scenarios["one"], values, {})


def test_shortlisting_reduces_evaluations_without_losing_linear_winner():
    pieces = inventory_from_good(good(*[
        artifact(f"{slot}-{i:03}", slot, substats={"def": i} if slot == "plume" else {"atk": i})
        for slot in SLOT_KEYS for i in range(80)
    ]))
    target = scenario()
    options = dict(top_k=2, max_evaluations=20_000, seed=1)
    pruned = search_builds(pieces, target, **options)
    full = search_builds(pieces, target, candidate_limit=None, **options)
    assert pruned.status == full.status == "approximate"
    assert pruned.evaluated < full.evaluated
    assert pruned.builds[0].evaluation.score == full.builds[0].evaluation.score
    assert len(pruned.builds) == 2


def test_pruned_search_keeps_constraint_extremes_and_set_alternatives():
    pieces = inventory_from_good(good(*[
        artifact(f"{slot}-{set_key}-{i:02}", slot, set_key=set_key,
                 substats={"enerRech_": i * 2, "atk": i} if slot != "plume" else {"enerRech_": i * 2})
        for slot in SLOT_KEYS for set_key in ("TestSet", "OtherSet") for i in range(20)
    ]))
    target = scenario(minimums={"enerRech_": 1.1}, maximums={"enerRech_": 1.2},
                      sets=[{"TestSet": 4}])
    result = search_builds(pieces, target, top_k=1, candidate_limit=1, max_evaluations=2000)
    assert result.builds and result.status == "approximate"
    assert result.builds[0].evaluation.feasible
    assert result.builds[0].build.set_counts["TestSet"] >= 4


def test_small_exact_oracle_is_unchanged_even_with_aggressive_screening():
    batch, target = inventory(), scenario(maximums={"enerRech_": 1.0})
    result = search_builds(batch, target, candidate_limit=1)
    assert result.status == "exact" and result.evaluated == 32
    assert len(result.builds) == 1


@pytest.mark.parametrize("seed", [0, 1, 2])
def test_optional_set_bonus_is_seeded_even_when_individual_swaps_hurt(seed):
    pieces = inventory_from_good(good(*[
        artifact(f"{slot}-{key}-{i:02}", slot, set_key=key,
                 substats={} if key == "TestSet" or slot == "plume" else {"atk": 10})
        for slot in SLOT_KEYS for key in ("TestSet", "OtherSet") for i in range(10)
    ]))
    target = scenario(effects={"four-piece": {
        "stage": "static", "unit": "atk", "expression": {"value": 1000, "unit": "atk"},
        "contributes_to": "stats.atk", "when": {"set": "TestSet", "pieces": 4},
    }})
    result = search_builds(pieces, target, top_k=2, candidate_limit=1,
                           max_evaluations=2000, seed=seed)
    assert result.builds[0].build.set_counts["TestSet"] >= 4
    assert result.builds[0].evaluation.score > 1000


def test_candidate_limit_changes_cache_key_and_invalid_values_are_rejected():
    cache = AnalysisCache()
    for limit in (None, 1, 12):
        search_builds(inventory(), scenario(), candidate_limit=limit, cache=cache)
    assert cache.summary()["search"]["misses"] == 3
    for invalid in (0, -1, True, 1.5):
        with pytest.raises(ValueError, match="candidate_limit"):
            search_builds(inventory(), scenario(), candidate_limit=invalid)
