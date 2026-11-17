"""Offline encoding checks for the authored research batch. Codex assisted.

These scalar references verify implementation, not game accuracy. Run with
--write-results to attach observations and save the validation report.
"""

import argparse
from copy import deepcopy
from hashlib import sha256
import json
import math
from pathlib import Path
import sys

# Permit direct execution from an uninstalled checkout.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from artifact_sort.formulas import LibraryError, compile_expression, dimension
from artifact_sort.library import load_library, load_mechanics


def reference_score(definition, evaluation):
    """Independent scalar math, using reported totals; no expression interpreter."""
    stats, channels, params = (
        evaluation.effective_stats,
        evaluation.channels,
        definition.parameters,
    )
    name = definition.scoring_formula
    resistance = params["enemy_resistance"] - channels["resistance_shred"]
    if resistance < 0:
        resist = 1 - resistance / 2
    elif resistance < 0.75:
        resist = 1 - resistance
    else:
        resist = 1 / (4 * resistance + 1)
    if name == "em-reaction":
        return (
            1446.8535
            * params["reaction_multiplier"]
            * (
                1
                + 16 * stats.get("eleMas", 0) / (2000 + stats.get("eleMas", 0))
                + channels["reaction_bonus"]
            )
            * resist
        )
    if name.endswith("-healing"):
        primary = name.split("-")[0]
        heal = (
            stats[primary] * params["healing_coefficient"]
            + params["flat_healing"]
            + stats.get("eleMas", 0) * params["em_healing_coefficient"]
        )
        return heal * (
            1
            + stats["heal_"]
            + params["recipient_healing_bonus"]
            + channels["received_healing"]
        )
    if name == "hp-shield-absorption":
        return (
            (stats["hp"] * params["shield_coefficient"] + params["flat_shield"])
            * params["absorption_multiplier"]
            * (1 + params["recipient_shield_strength"] + channels["shield_strength"])
        )
    parts = name.split("-")
    primary, element = parts[0], parts[-2]
    base_damage = stats[primary] * params["talent_coefficient"]
    if name == "atk-em-dendro-hit":
        mastery = stats.get("eleMas", 0)
        base_damage += mastery * params["em_damage_coefficient"]
        base_damage += (
            1446.8535
            * params["reaction_multiplier"]
            * (1 + 5 * mastery / (1200 + mastery) + channels["reaction_bonus"])
        )
    elif name == "atk-hp-cryo-hit":
        base_damage += stats["hp"] * params["hp_damage_coefficient"]
    else:
        base_damage += channels["additive_damage"]
    crit = 1 + max(0, min(1, stats["critRate_"] + channels["talent_crit_rate"])) * max(
        0, stats["critDMG_"]
    )
    defense = (params["character_level"] + 100) / (
        params["character_level"]
        + 100
        + (params["enemy_level"] + 100)
        * (1 - params["defense_reduction"])
        * (1 - params["defense_ignore"])
    )
    return (
        base_damage
        * (1 + stats.get(f"{element}_dmg_", 0) + channels["damage_bonus"])
        * crit
        * defense
        * resist
        * (
            channels["special_multiplier"]
            if name != "atk-em-dendro-hit" and name != "atk-hp-cryo-hit"
            else 1
        )
    )


def validate(root=ROOT):
    folder = root / "scenarios"
    library = load_library(folder / "library.json")
    mechanics = load_mechanics(folder / "library.mechanics.json")
    compiled = library.compile(mechanics, allow_draft=True)
    references = json.loads((folder / "research/reference-cases.json").read_text())
    snapshot = json.loads((folder / "research/source-snapshot.json").read_text())
    coverage = json.loads((folder / "library.coverage.json").read_text())
    research = json.loads((folder / "library.research.json").read_text())
    assert (folder / "scenario-library.schema.json").read_bytes() == (
        root / "artifact_sort/scenario-library.schema.json"
    ).read_bytes()
    assert (
        research["snapshot"]["sha256"]
        == sha256((folder / "research/source-snapshot.json").read_bytes()).hexdigest()
    )
    assert coverage["library_revision"] == library.revision
    assert not coverage["complete"] and not mechanics.validated
    assert set(coverage["characters"]) == set(snapshot["characters"])
    assert set(coverage["sets"]) == set(snapshot["sets"]) == set(mechanics.sets)
    assert coverage["counts"]["validated_scenarios"] == 0
    for table in ["characters", "weapons"]:
        for node in snapshot[table].values():
            totals = node["base90"] if table == "characters" else node["stats"]
            for key, derivation in node["derivation90"].items():
                expected = (
                    derivation["level1"] * derivation["factor90"]
                    + derivation["ascension6"]
                )
                assert math.isclose(totals[key], expected, rel_tol=1e-10, abs_tol=1e-8)
    for scenario in library.scenarios.values():
        assert scenario.family
        assert len(scenario.characters) <= 1
        if scenario.characters:
            assert scenario.family.startswith(scenario.characters[0] + "/")
        if scenario.conditions.get("gilded_active"):
            assert (
                scenario.conditions["gilded_same"]
                + scenario.conditions["gilded_different"]
                == 3
            )
    try:
        library.compile(mechanics)
    except LibraryError:
        pass
    else:
        raise AssertionError("Draft library unexpectedly passed publication gating")

    observations = {"components": {}, "scoring_formulas": {}, "scenarios": {}}
    for table, definitions in [
        ("components", library.components),
        ("scoring_formulas", library.scoring_formulas),
    ]:
        assert set(references[table]) == set(
            definitions
        ), f"Missing reference cases for {table}"
        for key, definition in definitions.items():
            cases = []
            for case in references[table][key]:
                env = {
                    name: {**values, **case["inputs"].get(name, {})}
                    for name, values in references["environment"].items()
                }
                if table == "components":
                    expression, unit, stage = (
                        definition.expression,
                        definition.unit,
                        definition.stage,
                    )
                else:
                    expression, unit_name = definition
                    unit, stage = dimension(unit_name), 3
                program = compile_expression(
                    expression,
                    unit,
                    components=library.components,
                    channels=library.channels,
                    stage=stage,
                    parameters=env["parameters"],
                    conditions=env["conditions"],
                )
                actual = program.evaluate(
                    (env["stats"], env["stats"], env["stats"]), env["channels"]
                )
                tolerance = case["tolerance"]
                assert math.isclose(
                    actual,
                    case["expected"],
                    rel_tol=tolerance["relative"],
                    abs_tol=tolerance["absolute"],
                ), (key, case["label"], actual, case["expected"])
                cases.append({**case, "observed": actual, "result": "passed"})
            observations[table][key] = cases

    # Legal main assignments, with synthetic aggregate additions for diagnostics.
    # This is not an independently verified five-artifact build or energy model.
    for key, scenario in compiled.scenarios.items():
        definition = scenario.definition
        main_map = {slot: values[0] for slot, values in definition.mains.items()}
        additions = {
            "hp": 4780,
            "atk": 311,
            "eleMas": 80,
            "critRate_": 0.12,
            "critDMG_": 0.6,
            "enerRech_": 0.9,
        }
        main_values = {
            "hp_": 0.466,
            "atk_": 0.466,
            "def_": 0.583,
            "eleMas": 186.5,
            "enerRech_": 0.518,
            "critRate_": 0.311,
            "critDMG_": 0.622,
            "heal_": 0.359,
        }
        for stat_key in main_map.values():
            additions[stat_key] = additions.get(stat_key, 0) + main_values.get(
                stat_key, 0.466
            )
        cases = []
        for composition in definition.sets:
            for incomplete in [False, True]:
                counts = dict(composition)
                if incomplete and counts:
                    counts[next(iter(counts))] -= 1
                result = scenario.evaluate(additions, counts, main_stats=main_map)
                expected = reference_score(definition, result)
                assert math.isclose(
                    result.score, expected, rel_tol=1e-12, abs_tol=1e-9
                ), key
                if incomplete:
                    assert not result.feasible, (
                        key,
                        "incomplete set should remain a gap",
                    )
                cases.append(
                    {
                        "kind": "aggregate-encoding-reference",
                        "inputs": {
                            "artifact_stats": additions,
                            "set_counts": counts,
                            "main_stats": main_map,
                        },
                        "expected": expected,
                        "observed": result.score,
                        "feasible": result.feasible,
                        "violations": list(result.violations),
                        "result": "passed",
                        "tolerance": {"relative": 1e-12, "absolute": 1e-9},
                        "method": "Independent scalar score math using engine-reported totals; not independent stat/game/build validation.",
                    }
                )
        observations["scenarios"][key] = cases
    return {
        "library_revision": library.revision,
        "created_with": "Codex assistance",
        "checked_at": "2026-10-05",
        "result": "passed-encoding-checks",
        "game_validated": False,
        "counts": {
            "compiled_scenarios": len(compiled.scenarios),
            "component_cases": sum(map(len, observations["components"].values())),
            "formula_cases": sum(map(len, observations["scoring_formulas"].values())),
            "aggregate_cases": sum(map(len, observations["scenarios"].values())),
        },
        "checks": [
            "JSON schema and package schema equality",
            "matching revisions and snapshot SHA256",
            "pinned source level-90 derivations",
            "references, units, stages and variant expansion",
            "explicit character/role families",
            "reference arithmetic",
            "incomplete set gaps",
            "draft publication gating",
        ],
        "limitations": [
            "No independent in-game or GO complete-build comparison was performed.",
            "Aggregate fixtures do not establish equipment legality, particle supply, snapshot timing, or complete-role coverage.",
            "Source release availability and new mechanics remain unaudited; see coverage report.",
        ],
        "observations": observations,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-results", action="store_true")
    args = parser.parse_args()
    report = validate()
    if args.write_results:
        folder = ROOT / "scenarios"
        sidecar = folder / "library.research.json"
        research = json.loads(sidecar.read_text())
        for table, records in report["observations"].items():
            for key, cases in records.items():
                research[table][key]["checks"] = deepcopy(cases)
        sidecar.write_text(json.dumps(research, indent=2) + "\n")
        report["sha256"] = {
            name: sha256((folder / name).read_bytes()).hexdigest()
            for name in [
                "library.json",
                "library.research.json",
                "library.mechanics.json",
                "library.coverage.json",
            ]
        }
        (folder / "library.validation.json").write_text(
            json.dumps(report, indent=2) + "\n"
        )
    print(
        json.dumps(
            {key: value for key, value in report.items() if key != "observations"},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
