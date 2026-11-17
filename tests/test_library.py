from copy import deepcopy
import json
from pathlib import Path

import pytest

from artifact_sort.formulas import EvaluationError, LibraryError
from artifact_sort.library import (
    Mechanics,
    library_from_data,
    load_library,
    normalize_good_stats,
)

ROOT = Path(__file__).resolve().parents[1]


def document():
    return {
        "format": "artifact-sort-scenario-library",
        "version": 4,
        "revision": "test-1",
        "mechanics": "test-rules-1",
        "scoring_formulas": {
            "score": {
                "unit": "atk",
                "expression": {"stat": "atk", "stage": "effective"},
            }
        },
        "established": [
            {
                "id": "one",
                "scoring_formula": "score",
                "base": {"atk": 100},
                "sets": [{}],
            }
        ],
        "parameter_variations": [],
        "structural_variations": [],
        "components": {},
        "channels": {},
        "effects": [],
    }


def mechanics(doc, *, validated=False):
    # Test fixtures declare known game keys; they do not assert game accuracy.
    return Mechanics(
        doc["mechanics"],
        "test-game",
        frozenset(
            {
                "TestSet",
                "OtherSet",
                "BlizzardStrayer",
                "EmblemOfSeveredFate",
                "GoldenTroupe",
                "MaidenBeloved",
                "OceanHuedClam",
                "TenacityOfTheMillelith",
                "VourukashasGlow",
                "HuskOfOpulentDreams",
            }
        ),
        frozenset({"Fischl", "Xingqiu", "Barbara", "Zhongli"}),
        validated=validated,
    )


def compile_doc(doc):
    return library_from_data(doc).compile(mechanics(doc), allow_draft=True)


def stat(key, stage="effective"):
    return {"stat": key, "stage": stage}


def op(name, *args):
    return {"op": name, "args": list(args)}


def effect(
    doc,
    key,
    expression,
    *,
    stage="bonus",
    unit="scalar",
    target="channels.bonus",
    when=None,
):
    node = {
        "stage": stage,
        "unit": unit,
        "expression": expression,
        "contributes_to": target,
    }
    if when is not None:
        node["when"] = when
    doc["components"][key] = node
    doc["effects"].append(key)


def test_all_bundled_scenarios_compile_as_drafts():
    for name, counts in [("example", (1, 4)), ("pilot", (5, 10))]:
        library = load_library(ROOT / f"scenarios/library.{name}.json")
        compiled = library.compile(
            mechanics({"mechanics": library.mechanics}), allow_draft=True
        )
        assert len(compiled.select()) == counts[0]
        assert len(compiled.select(include_speculative=True)) == counts[1]
        assert compiled.draft and compiled.limitations
        with pytest.raises(LibraryError, match="not a validated release"):
            library.compile(mechanics({"mechanics": library.mechanics}))
        for scenario in compiled.scenarios.values():
            counts = dict(scenario.definition.sets[0])
            mains = {
                slot: values[0] for slot, values in scenario.definition.mains.items()
            }
            result = scenario.evaluate({}, counts, main_stats=mains)
            assert result.score > 0


def test_variants_merge_remove_and_replace_without_mutating_input():
    doc = document()
    doc["established"][0].update(
        buffs={"atk_": 0.2, "atk": 10}, mains={"sands": ["atk_", "enerRech_"]}
    )
    doc["parameter_variations"] = [
        {
            "id": "two",
            "extends": "one",
            "changes": {"buffs": {"atk": None}, "mains": {"sands": ["atk_"]}},
        },
        {"id": "three", "extends": "two", "changes": {"base": {"atk": 200}}},
    ]
    original = deepcopy(doc)
    library = library_from_data(doc)
    assert dict(library.scenarios["two"].buffs) == {"atk_": 0.2}
    assert library.scenarios["three"].mains["sands"] == ("atk_",)
    assert library.scenarios["three"].base["atk"] == 200
    assert library.scenarios["three"].collection == "parameter_variations"
    assert doc == original
    with pytest.raises(TypeError):
        library.scenarios["one"].base["atk"] = 5


def test_family_metadata_inherits_through_parameter_variants():
    doc = document()
    doc["established"][0]["family"] = "ExampleCharacter/on-field-damage"
    doc["parameter_variations"] = [
        {"id": "two", "extends": "one", "changes": {"base": {"atk": 200}}},
        {"id": "three", "extends": "two", "changes": {"base": {"atk": 300}}},
    ]
    doc["structural_variations"] = [
        {**doc["established"][0], "id": "support", "family": "ExampleCharacter/support"}
    ]
    compiled = compile_doc(doc)
    for identity in ("one", "two", "three"):
        assert (
            compiled.scenarios[identity].definition.family
            == "ExampleCharacter/on-field-damage"
        )
    assert compiled.scenarios["support"].definition.family == "ExampleCharacter/support"
    doc["structural_variations"][0]["family"] = "ExampleCharacter/on-field-damage"
    assert (
        compile_doc(doc).scenarios["support"].definition.family
        == compiled.scenarios["one"].definition.family
    )


@pytest.mark.parametrize("family", ["", "   ", None, 1])
def test_invalid_family_metadata_is_rejected(family):
    doc = document()
    doc["established"][0]["family"] = family
    with pytest.raises(LibraryError):
        library_from_data(doc)


def test_parameter_variants_cannot_override_or_remove_family():
    doc = document()
    doc["established"][0]["family"] = "ExampleCharacter/on-field-damage"
    for family in ("ExampleCharacter/support", None):
        doc["parameter_variations"] = [
            {"id": "two", "extends": "one", "changes": {"family": family}}
        ]
        with pytest.raises(LibraryError):
            library_from_data(doc)


def test_missing_family_remains_explicit_and_family_edits_change_fingerprint():
    doc = document()
    original = compile_doc(doc)
    assert original.scenarios["one"].definition.family is None
    doc["established"][0]["family"] = "archetype/attack-damage"
    grouped = compile_doc(doc)
    assert grouped.fingerprint != original.fingerprint
    assert (
        grouped.scenarios["one"].evaluate({}, {}).score
        == original.scenarios["one"].evaluate({}, {}).score
    )


def test_decimal_boundary_and_primary_stat_assembly():
    assert normalize_good_stats(
        {"atk": 100, "atk_": 46.6, "critDMG_": 150, "enerRech_": 200}
    ) == {
        "atk": 100,
        "atk_": 0.466,
        "critDMG_": 1.5,
        "enerRech_": 2,
    }
    doc = document()
    doc["established"][0]["buffs"] = {"atk_": 0.2, "atk": 10}
    scenario = compile_doc(doc).scenarios["one"]
    result = scenario.evaluate({"atk_": 0.466, "atk": 311}, {})
    assert result.score == pytest.approx(100 * 1.666 + 321)
    assert result.feasible
    assert scenario.relevant_stats == frozenset({"atk", "atk_"})


def test_conversion_uses_scaled_raw_snapshot_and_effects_apply_once():
    doc = document()
    doc["established"][0]["base"]["hp"] = 1000
    doc["established"][0]["buffs"] = {"hp_": 0.5, "hp": 100}
    # Convert 10% of pre-conversion HP into flat ATK, while doubling HP via a conversion.
    effect(
        doc,
        "hp-atk",
        op("multiply", stat("hp", "raw"), {"value": 0.1, "unit": "atk/hp"}),
        stage="conversion",
        unit="atk",
        target="stats.atk",
    )
    effect(doc, "more-hp", 1, stage="conversion", target="stats.hp_")
    doc["established"][0]["effects"] = [
        "hp-atk"
    ]  # global/local registration deduplicates
    result = compile_doc(doc).scenarios["one"].evaluate({}, {})
    assert result.score == 260  # 100 + 0.1 * (1000 * 1.5 + 100)
    assert result.effective_stats["hp"] == 2600
    reversed_doc = deepcopy(doc)
    reversed_doc["effects"].reverse()
    assert (
        compile_doc(reversed_doc).scenarios["one"].evaluate({}, {}).score
        == result.score
    )


def test_crit_bonus_cap_and_hp_addition_reference():
    lib = load_library(ROOT / "scenarios/library.example.json")
    compiled = lib.compile(mechanics({"mechanics": lib.mechanics}), allow_draft=True)
    scenario = compiled.scenarios["speculative-atk-hp-cryo-flat"]
    # ATK=1000, HP=20000, crit rate=.5, crit damage=1, cryo bonus=.5.
    result = scenario.evaluate(
        {"atk": 40, "hp": 6000, "critRate_": 0.45, "critDMG_": 0.5, "cryo_dmg_": 0.5},
        {},
    )
    assert result.score == pytest.approx(2700)
    capped = scenario.evaluate(
        {"atk": 40, "hp": 6000, "critRate_": 1.15, "critDMG_": 1.5, "cryo_dmg_": 0.5},
        {},
    )
    assert capped.score == pytest.approx(5400)


def test_emblem_activates_from_actual_counts_and_caps_after_er_bonus():
    doc = document()
    doc["established"][0]["base"]["enerRech_"] = 1
    doc["established"][0]["conditions"] = {"damage_type": "burst"}
    doc["channels"]["bonus"] = {"unit": "scalar", "combine": "add"}
    doc["scoring_formulas"]["score"]["expression"] = op(
        "multiply", stat("atk"), op("add", 1, {"channel": "bonus"})
    )
    effect(
        doc,
        "er",
        0.2,
        stage="static",
        target="stats.enerRech_",
        when={"set": "TestSet", "pieces": 2},
    )
    effect(
        doc,
        "burst",
        op("min", op("multiply", stat("enerRech_"), 0.25), 0.75),
        when={
            "all": [
                {"set": "TestSet", "pieces": 4},
                {"condition": "damage_type", "equals": "burst"},
            ]
        },
    )
    scenario = compile_doc(doc).scenarios["one"]
    assert scenario.evaluate({"enerRech_": 0.8}, {"TestSet": 4}).score == 150
    assert scenario.evaluate({"enerRech_": 4}, {"TestSet": 4}).score == 175
    assert scenario.evaluate({"enerRech_": 0.8}, {"TestSet": 2}).score == 100
    assert (
        scenario.evaluate({"enerRech_": 0.8}, {"OtherSet": 4}).effective_stats[
            "enerRech_"
        ]
        == 1.8
    )


def test_short_circuit_and_false_multiplier_identity():
    doc = document()
    doc["channels"]["bonus"] = {"unit": "scalar", "combine": "multiply"}
    doc["scoring_formulas"]["score"]["expression"] = op(
        "multiply", stat("atk"), {"channel": "bonus"}
    )
    effect(
        doc,
        "mult",
        op("divide", 1, 0),
        when={
            "all": [
                {"set": "TestSet", "pieces": 4},
                {"condition": "missing", "equals": True},
            ]
        },
    )
    scenario = compile_doc(doc).scenarios["one"]
    assert scenario.evaluate({}, {}).score == 100
    with pytest.raises(EvaluationError, match="missing activation condition"):
        scenario.evaluate({}, {"TestSet": 4})
    doc["established"][0]["conditions"] = {"missing": False}
    assert compile_doc(doc).scenarios["one"].evaluate({}, {"TestSet": 4}).score == 100
    doc["established"][0]["conditions"]["missing"] = True
    with pytest.raises(EvaluationError, match="division by zero"):
        compile_doc(doc).scenarios["one"].evaluate({}, {"TestSet": 4})


def test_condition_equality_distinguishes_bool_from_number():
    doc = document()
    doc["established"][0]["conditions"] = {"flag": 1}
    effect(
        doc,
        "flag",
        {"value": 50, "unit": "atk"},
        stage="static",
        unit="atk",
        target="stats.atk",
        when={"condition": "flag", "equals": True},
    )
    assert compile_doc(doc).scenarios["one"].evaluate({}, {}).score == 100
    doc["components"]["flag"]["when"]["equals"] = 1.0
    assert compile_doc(doc).scenarios["one"].evaluate({}, {}).score == 150


def test_constraints_use_uncapped_totals_and_missing_mains_are_visible():
    doc = document()
    doc["established"][0].update(
        base={"atk": 100, "critRate_": 0.05, "enerRech_": 1},
        minimums={"enerRech_": 1.4},
        maximums={"critRate_": 1},
        sets=[{"TestSet": 4}],
        mains={"sands": ["atk_"]},
    )
    scenario = compile_doc(doc).scenarios["one"]
    result = scenario.evaluate({"critRate_": 1.1}, {"TestSet": 2})
    assert len(result.violations) == 4 and result.score == 100
    assert not result.feasible
    assert scenario.evaluate(
        {"enerRech_": 0.4}, {"TestSet": 4}, main_stats={"sands": "atk_"}
    ).feasible


@pytest.mark.parametrize(
    "change, match",
    [
        (lambda d: d.update(version=3), "version"),
        (
            lambda d: d["established"].append(deepcopy(d["established"][0])),
            "duplicate scenario",
        ),
        (lambda d: d["established"][0].update(base={"atk": float("nan")}), "nonfinite"),
        (
            lambda d: d["established"][0].update(
                minimums={"atk": 200}, maximums={"atk": 100}
            ),
            "exceeds",
        ),
        (
            lambda d: d["established"][0].update(sets=[{"TestSet": 4, "OtherSet": 2}]),
            "five pieces",
        ),
        (
            lambda d: d["established"][0].update(mains={"flower": ["atk_"]}),
            "illegal main stat",
        ),
        (
            lambda d: d["established"][0].update(scoring_formula="missing"),
            "unresolved scoring formula",
        ),
        (
            lambda d: d["scoring_formulas"]["score"].update(
                expression=op("add", stat("atk"), 1)
            ),
            "incompatible units",
        ),
        (
            lambda d: d["scoring_formulas"]["score"].update(
                expression={"ref": "missing"}
            ),
            "unresolved component",
        ),
        (
            lambda d: d["scoring_formulas"]["score"].update(
                expression=op("multiply", stat("atk"), {"parameter": "missing"})
            ),
            "missing parameter",
        ),
        (lambda d: d["established"][0].update(base={}), "missing intrinsic"),
        (lambda d: d["established"][0].update(sets=[{"Typo": 4}]), "unknown set"),
        (
            lambda d: d["established"][0].update(characters=["Typo"]),
            "unknown character",
        ),
        (
            lambda d: d["scoring_formulas"]["score"].update(
                expression={"op": "extension", "name": "x", "version": "1", "args": []}
            ),
            "unsupported extension",
        ),
        (
            lambda d: d["scoring_formulas"]["score"].update(
                expression=op("divide", 1, 2, 3)
            ),
            "expression",
        ),
    ],
)
def test_invalid_libraries_fail_explicitly(change, match):
    doc = document()
    change(doc)
    with pytest.raises(LibraryError, match=match):
        compile_doc(doc)


def test_cycles_future_stages_and_effect_references_fail():
    doc = document()
    doc["components"] = {
        "a": {"stage": "score", "unit": "atk", "expression": {"ref": "b"}},
        "b": {"stage": "score", "unit": "atk", "expression": {"ref": "a"}},
    }
    with pytest.raises(LibraryError, match="cycle"):
        compile_doc(doc)
    doc = document()
    effect(
        doc, "future", stat("atk"), stage="conversion", unit="atk", target="stats.atk"
    )
    with pytest.raises(LibraryError, match="future"):
        compile_doc(doc)
    doc = document()
    effect(
        doc,
        "add",
        {"value": 1, "unit": "atk"},
        stage="static",
        unit="atk",
        target="stats.atk",
    )
    doc["scoring_formulas"]["score"]["expression"] = {"ref": "add"}
    with pytest.raises(LibraryError, match="pure reference"):
        compile_doc(doc)


def test_parent_cycles_unresolved_and_required_input_removal():
    doc = document()
    doc["parameter_variations"] = [
        {"id": "a", "extends": "b", "changes": {"base": {"atk": 1}}},
        {"id": "b", "extends": "a", "changes": {"base": {"atk": 1}}},
    ]
    with pytest.raises(LibraryError, match="parent cycle"):
        compile_doc(doc)
    doc["parameter_variations"] = [
        {"id": "a", "extends": "absent", "changes": {"base": {"atk": 1}}}
    ]
    with pytest.raises(LibraryError, match="unresolved scenario parent"):
        compile_doc(doc)
    doc["parameter_variations"] = [
        {"id": "a", "extends": "one", "changes": {"base": {"atk": None}}}
    ]
    with pytest.raises(LibraryError, match="missing intrinsic"):
        compile_doc(doc)


@pytest.mark.parametrize(
    "expression, match",
    [
        (op("multiply", stat("atk"), op("divide", 1, 0)), "division by zero"),
        (op("multiply", stat("atk"), op("clamp", 1, 2, 0)), "reversed clamp"),
        (op("multiply", stat("atk"), 1e308), "nonfinite"),
    ],
)
def test_arithmetic_errors(expression, match):
    doc = document()
    doc["scoring_formulas"]["score"]["expression"] = expression
    with pytest.raises(EvaluationError, match=match):
        compile_doc(doc).scenarios["one"].evaluate({}, {})


def test_dependency_tracking_and_reused_component_program():
    doc = document()
    doc["established"][0]["base"]["eleMas"] = 200
    doc["components"]["em"] = {
        "stage": "bonus",
        "unit": "scalar",
        "expression": op(
            "multiply", stat("eleMas"), {"value": 0.01, "unit": "scalar/em"}
        ),
    }
    doc["scoring_formulas"]["score"]["expression"] = op(
        "multiply", stat("atk"), {"ref": "em"}, {"ref": "em"}
    )
    scenario = compile_doc(doc).scenarios["one"]
    assert scenario.relevant_stats == frozenset({"atk", "atk_", "eleMas"})
    assert (
        sum(
            instruction.op == "stat" and instruction.key == "eleMas"
            for instruction in scenario.score.instructions
        )
        == 1
    )
    assert scenario.evaluate({}, {}).score == 400


def test_content_fingerprints_and_mechanics_pin():
    doc = document()
    first = compile_doc(doc)
    assert first.fingerprint == compile_doc(deepcopy(doc)).fingerprint
    doc["established"][0]["base"]["atk"] = 101
    assert first.fingerprint != compile_doc(doc).fingerprint
    library = library_from_data(doc)
    with pytest.raises(LibraryError, match="pin"):
        library.compile(Mechanics("wrong", "test", frozenset()), allow_draft=True)
    with pytest.raises(LibraryError, match="selected scenario"):
        library.compile(mechanics(doc), allow_draft=True, scenario_ids=["missing"])


def test_release_gate_and_research_validation():
    doc = document()
    research = {
        "library_revision": "test-1",
        "sources": {},
        "components": {},
        "scenarios": {"one": {"status": "validated", "sources": []}},
        "scoring_formulas": {"score": {"status": "validated", "sources": []}},
    }
    lib = library_from_data(doc, research=research)
    assert not lib.compile(mechanics(doc, validated=True)).draft
    with pytest.raises(LibraryError, match="not validated"):
        lib.compile(mechanics(doc))
    research["library_revision"] = "wrong"
    with pytest.raises(LibraryError, match="revision"):
        library_from_data(doc, research=research)
    research["library_revision"] = "test-1"
    research["scenarios"]["one"]["sources"] = ["missing"]
    with pytest.raises(LibraryError, match="unresolved research sources"):
        library_from_data(doc, research=research)


def test_duplicate_json_keys_rejected(tmp_path):
    path = tmp_path / "library.json"
    path.write_text('{"version":4,"version":4}')
    with pytest.raises(LibraryError, match="duplicate JSON key"):
        load_library(path)


@pytest.mark.parametrize(
    "stats, counts",
    [
        ({"atk": float("inf")}, {}),
        ({"bad": 1}, {}),
        ({"atk": True}, {}),
        ({}, {"TestSet": True}),
        ({}, {"TestSet": -1}),
        ({}, {"TestSet": 6}),
        ({}, {"Typo": 1}),
    ],
)
def test_invalid_candidates(stats, counts):
    with pytest.raises(EvaluationError):
        compile_doc(document()).scenarios["one"].evaluate(stats, counts)


def test_pinned_components_resolve_and_contents_change_fingerprint():
    from artifact_sort.formulas import Component, Expression, dimension

    doc = document()
    doc["scoring_formulas"]["score"]["expression"] = op(
        "multiply", stat("atk"), {"ref": "pinned"}
    )
    library = library_from_data(doc)
    component = Component(2, (), Expression("constant", value=2))
    installed = Mechanics(
        "test-rules-1", "test-game", frozenset(), components={"pinned": component}
    )
    compiled = library.compile(installed, allow_draft=True)
    assert compiled.scenarios["one"].evaluate({}, {}).score == 200
    changed = Mechanics(
        "test-rules-1",
        "test-game",
        frozenset(),
        components={
            "pinned": Component(2, (), Expression("constant", value=3)),
        },
    )
    assert (
        compiled.fingerprint != library.compile(changed, allow_draft=True).fingerprint
    )
    doc["components"]["pinned"] = {"stage": "bonus", "unit": "scalar", "expression": 2}
    with pytest.raises(LibraryError, match="conflicting local/pinned"):
        library_from_data(doc).compile(installed, allow_draft=True)
    malformed = Mechanics(
        "test-rules-1",
        "test-game",
        frozenset(),
        components={
            "pinned": Component(
                2,
                dimension("scalar"),
                Expression("divide", (Expression("constant", value=1),)),
            ),
        },
    )
    with pytest.raises(LibraryError, match="argument count"):
        library.compile(malformed, allow_draft=True)


def test_numeric_conditions_bind_and_bool_conditions_cannot_be_numbers():
    doc = document()
    doc["scoring_formulas"]["score"]["expression"] = op(
        "multiply", stat("atk"), {"condition": "stacks"}
    )
    doc["established"][0]["conditions"] = {"stacks": 2}
    assert compile_doc(doc).scenarios["one"].evaluate({}, {}).score == 200
    doc["established"][0]["conditions"]["stacks"] = True
    with pytest.raises(LibraryError, match="must be numeric"):
        compile_doc(doc)
    doc["established"][0]["conditions"] = {}
    with pytest.raises(LibraryError, match="missing condition"):
        compile_doc(doc)


def test_any_not_predicates_and_dimension_cancellation():
    doc = document()
    doc["established"][0]["conditions"] = {"enabled": True}
    effect(
        doc,
        "flat",
        op(
            "divide",
            op("multiply", stat("atk", "base"), {"value": 1, "unit": "hp/atk"}),
            {"value": 2, "unit": "hp/atk"},
        ),
        stage="static",
        unit="atk",
        target="stats.atk",
        when={
            "any": [
                {"set": "TestSet", "pieces": 4},
                {"not": {"condition": "enabled", "equals": False}},
            ]
        },
    )
    assert compile_doc(doc).scenarios["one"].evaluate({}, {}).score == 150
    assert compile_doc(doc).scenarios["one"].relevant_stats == frozenset(
        {"atk", "atk_"}
    )


def test_conversion_flat_and_percent_are_applied_in_correct_order():
    doc = document()
    doc["established"][0]["buffs"] = {"atk_": 0.2, "atk": 10}
    effect(doc, "percent", 0.5, stage="conversion", target="stats.atk_")
    effect(
        doc,
        "flat",
        {"value": 30, "unit": "atk"},
        stage="conversion",
        unit="atk",
        target="stats.atk",
    )
    assert compile_doc(doc).scenarios["one"].evaluate(
        {"atk_": 0.466, "atk": 311}, {}
    ).score == pytest.approx(100 * (1 + 0.2 + 0.466 + 0.5) + 10 + 311 + 30)


def test_reusing_expression_cannot_bypass_stage_validation():
    doc = document()
    # The same stat expression occurs in an allowed bonus component and then
    # an illegal static dependency inside the scoring formula.
    doc["components"]["late"] = {
        "stage": "bonus",
        "unit": "atk",
        "expression": stat("atk"),
    }
    doc["components"]["early"] = {
        "stage": "static",
        "unit": "atk",
        "expression": stat("atk"),
    }
    doc["scoring_formulas"]["score"]["expression"] = op(
        "add", {"ref": "late"}, {"ref": "early"}
    )
    with pytest.raises(LibraryError, match="future"):
        compile_doc(doc)


def test_mismatched_effect_target_units_and_illegal_contribution_stages():
    doc = document()
    effect(doc, "bad", 0.5, stage="conversion", target="stats.atk")
    with pytest.raises(LibraryError, match="incompatible units"):
        compile_doc(doc)
    doc["components"]["bad"]["expression"] = {"value": 1, "unit": "atk"}
    doc["components"]["bad"]["unit"] = "atk"
    doc["components"]["bad"]["stage"] = "bonus"
    with pytest.raises(LibraryError, match="static/conversion"):
        compile_doc(doc)


def test_packaged_schema_matches_the_authoring_schema():
    from importlib.resources import files

    assert json.loads(
        files("artifact_sort").joinpath("scenario-library.schema.json").read_text()
    ) == json.loads((ROOT / "scenarios/scenario-library.schema.json").read_text())


def test_base_only_conversion_does_not_create_false_artifact_dependencies():
    doc = document()
    doc["established"][0]["base"]["hp"] = 1000
    effect(
        doc,
        "hp-flat",
        op("multiply", stat("hp", "base"), {"value": 0.1, "unit": "atk/hp"}),
        stage="conversion",
        unit="atk",
        target="stats.atk",
    )
    scenario = compile_doc(doc).scenarios["one"]
    assert scenario.relevant_stats == frozenset({"atk", "atk_"})
    assert scenario.evaluate({"hp": 10000, "hp_": 1}, {}).score == 200


def test_threshold_comparisons_tolerate_roundoff_without_relaxing_real_limits():
    doc = document()
    doc["established"][0].update(
        base={"atk": 100, "enerRech_": 1},
        buffs={"enerRech_": 0.1},
        minimums={"enerRech_": 1.3},
        maximums={"enerRech_": 1.3},
    )
    scenario = compile_doc(doc).scenarios["one"]
    assert scenario.evaluate({"enerRech_": 0.2}, {}).feasible
    assert not scenario.evaluate({"enerRech_": 0.20001}, {}).feasible


def test_pinned_channels_and_contribution_targets_are_validated():
    from artifact_sort.formulas import Channel, Component, Expression

    doc = document()
    library = library_from_data(doc)
    bad_channel = Mechanics(
        doc["mechanics"],
        "test",
        frozenset(),
        channels={"bonus": Channel((), "unknown")},
    )
    with pytest.raises(LibraryError, match="invalid aggregation"):
        library.compile(bad_channel, allow_draft=True)
    bad_target = Mechanics(
        doc["mechanics"],
        "test",
        frozenset(),
        channels={"bonus": Channel((), "add")},
        components={
            "bad": Component(2, (), Expression("constant", value=1), "other.bonus")
        },
    )
    with pytest.raises(LibraryError, match="invalid contribution target"):
        library.compile(bad_target, allow_draft=True)


def test_automatic_weights_follow_conversions_channels_and_primary_scaling():
    doc = document()
    doc["established"][0]["base"].update(hp=1000, enerRech_=1)
    doc["channels"] = {"bonus": {"unit": "scalar", "combine": "add"}}
    effect(
        doc,
        "hp-atk",
        op("multiply", stat("hp", "raw"), {"value": 0.1, "unit": "atk/hp"}),
        stage="conversion",
        unit="atk",
        target="stats.atk",
    )
    effect(doc, "hp-growth", 0.2, stage="conversion", target="stats.hp_")
    effect(doc, "er-bonus", op("min", op("multiply", stat("enerRech_"), 0.25), 0.75))
    doc["scoring_formulas"]["score"]["expression"] = op(
        "multiply", stat("atk"), op("add", 1, {"channel": "bonus"})
    )
    scenario = compile_doc(doc).scenarios["one"]
    additions = {"hp_": 0.5, "hp": 100, "atk_": 0.2, "atk": 30, "enerRech_": 0.5}
    local = scenario.linearize(additions, {})
    assert local.evaluation == scenario.evaluate(additions, {})
    assert not local.at_boundary
    assert local.weights["hp_"] == pytest.approx(100 * 1.375)
    assert local.weights["hp"] == pytest.approx(0.1 * 1.375)
    assert local.weights["atk_"] == pytest.approx(100 * 1.375)
    # HP conversion reads pre-conversion raw HP, not the HP-growth effect.
    assert local.weights["enerRech_"] == pytest.approx((150 + 160) * 0.25)
    for key in additions:
        step = 1e-5
        upper, lower = dict(additions), dict(additions)
        upper[key] += step
        lower[key] -= step
        numerical = (
            scenario.evaluate(upper, {}).score - scenario.evaluate(lower, {}).score
        ) / (2 * step)
        assert local.weights[key] == pytest.approx(numerical, rel=1e-7)


@pytest.mark.parametrize(
    "expression, expected",
    [
        (
            op("divide", stat("atk"), op("add", 1, stat("enerRech_"))),
            {"atk": 0.5, "enerRech_": -25},
        ),
        (
            op("multiply", stat("atk"), op("subtract", stat("enerRech_"), 1)),
            {"atk": 0, "enerRech_": 100},
        ),
        (op("max", stat("atk"), {"value": 50, "unit": "atk"}), {"atk": 1}),
        (
            op(
                "clamp",
                stat("atk"),
                {"value": 50, "unit": "atk"},
                {"value": 200, "unit": "atk"},
            ),
            {"atk": 1},
        ),
    ],
)
def test_automatic_weights_cover_arithmetic_and_zero_factors(expression, expected):
    doc = document()
    doc["established"][0]["base"]["enerRech_"] = 1
    doc["scoring_formulas"]["score"]["expression"] = expression
    local = compile_doc(doc).scenarios["one"].linearize({}, {})
    for key, value in expected.items():
        assert local.weights[key] == pytest.approx(value)


def test_automatic_weights_for_multiplicative_channels():
    doc = document()
    doc["established"][0]["base"]["enerRech_"] = 1
    doc["channels"] = {"bonus": {"unit": "scalar", "combine": "multiply"}}
    effect(doc, "first", stat("enerRech_"))
    effect(doc, "second", op("add", 1, stat("enerRech_")))
    doc["scoring_formulas"]["score"]["expression"] = op(
        "multiply", stat("atk"), {"channel": "bonus"}
    )
    local = compile_doc(doc).scenarios["one"].linearize({}, {})
    assert local.evaluation.score == 200
    assert local.weights["atk"] == 2
    assert local.weights["enerRech_"] == 300


def test_automatic_weights_report_cap_boundary_and_plateau():
    doc = document()
    doc["scoring_formulas"]["score"]["expression"] = op(
        "min", stat("atk"), {"value": 100, "unit": "atk"}
    )
    scenario = compile_doc(doc).scenarios["one"]
    assert scenario.linearize({}, {}).at_boundary
    plateau = scenario.linearize({"atk": 10}, {})
    assert plateau.weights["atk"] == 0
    assert not plateau.at_boundary


def test_zero_damage_gradient_does_not_remove_energy_constraint():
    doc = document()
    doc["established"][0]["base"]["enerRech_"] = 1
    doc["established"][0]["minimums"] = {"enerRech_": 1.5}
    local = compile_doc(doc).scenarios["one"].linearize({}, {})
    assert local.weights["enerRech_"] == 0
    assert not local.evaluation.feasible
