from copy import deepcopy
from itertools import product
import json
from pathlib import Path

import pytest

from artifact_sort.inventory import (
    Artifact,
    Inventory,
    assemble_build,
    evaluate_build,
    inventory_from_good,
    load_inventory,
    main_stat_value,
)
from artifact_sort.library import Mechanics, library_from_data
from artifact_sort.library_search import (
    REAL_SLOT_PATTERNS,
    search_builds,
    search_future_patterns,
)
from artifact_sort.model import SLOT_KEYS


def artifact(index, slot, *, level=20, main=None, substats=None, set_key="TestSet"):
    return {
        "id": str(index),
        "setKey": set_key,
        "slotKey": slot,
        "mainStatKey": main or {"flower": "hp", "plume": "atk"}.get(slot, "atk_"),
        "rarity": 5,
        "level": level,
        "substats": [
            {"key": key, "value": value} for key, value in (substats or {}).items()
        ],
    }


def good(*artifacts):
    return {"format": "GOOD", "version": 3, "artifacts": list(artifacts)}


def scenario(*, minimums=None, maximums=None, sets=None, effects=None):
    doc = {
        "format": "artifact-sort-scenario-library",
        "version": 4,
        "revision": "inventory-test",
        "mechanics": "test-rules",
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
                "base": {"atk": 100, "enerRech_": 1},
                "minimums": minimums or {},
                "maximums": maximums or {},
                "sets": sets or [{}],
            }
        ],
        "parameter_variations": [],
        "structural_variations": [],
        "components": effects or {},
        "channels": {},
        "effects": list(effects or {}),
    }
    return (
        library_from_data(doc)
        .compile(
            Mechanics("test-rules", "test", frozenset({"TestSet", "OtherSet"})),
            allow_draft=True,
        )
        .scenarios["one"]
    )


def inventory():
    return inventory_from_good(
        good(
            *[
                artifact(
                    f"{slot}-{i}",
                    slot,
                    substats=(
                        {"enerRech_": i * 10, "atk": i * 10}
                        if slot != "plume"
                        else {"enerRech_": i * 10}
                    ),
                )
                for slot in SLOT_KEYS
                for i in range(2)
            ]
        )
    )


def test_import_preserves_values_normalizes_once_and_freezes():
    data = good(
        artifact(
            "a", "goblet", main="pyro_dmg_", substats={"atk_": 17.49, "eleMas": 42.1}
        )
    )
    original = deepcopy(data)
    imported = inventory_from_good(data)
    a = imported.artifacts[0]
    assert dict(a.substats) == pytest.approx({"atk_": 0.1749, "eleMas": 42.1})
    assert a.stats["pyro_dmg_"] == 0.466
    assert data == original
    with pytest.raises(TypeError):
        a.substats["atk_"] = 1


def test_current_main_growth_and_hidden_lines_are_not_completed_stats():
    data = good(
        artifact("a", "sands", level=0, main="enerRech_", substats={"hp_": 5.8})
    )
    data["artifacts"][0]["unactivatedSubstats"] = [{"key": "atk_", "value": 5.8}]
    a = inventory_from_good(data).artifacts[0]
    assert dict(a.stats) == pytest.approx({"hp_": 0.058, "enerRech_": 0.078})
    assert dict(a.hidden_substats) == pytest.approx({"atk_": 0.058})
    assert main_stat_value(5, "enerRech_", 20) == 0.518


def test_main_table_uses_actual_rarity_and_level():
    data = good(artifact("a", "flower", level=8))
    data["artifacts"][0]["rarity"] = 4
    assert inventory_from_good(data).artifacts[0].stats["hp"] == 2108
    with pytest.raises(ValueError, match="invalid level"):
        main_stat_value(4, "hp", 20)
    # Generated tables include unreachable two-star levels; the game cap is +4.
    with pytest.raises(ValueError, match="invalid level"):
        main_stat_value(2, "hp", 8)


@pytest.mark.parametrize(
    "change, message",
    [
        ({"mainStatKey": "critRate_"}, "illegal main"),
        ({"level": -1}, "invalid level"),
        ({"level": 1.5}, "integer"),
        ({"lock": "false"}, "boolean"),
        ({"substats": [{"key": "hp", "value": 100}]}, "illegal substat"),
        (
            {"substats": [{"key": "critRate_", "value": float("nan")}]},
            "invalid substat",
        ),
        ({"substats": [{"key": "critRate_", "value": -1}]}, "invalid substat"),
        (
            {
                "substats": [
                    {"key": "critRate_", "value": 1},
                    {"key": "critRate_", "value": 2},
                ]
            },
            "duplicate substat",
        ),
    ],
)
def test_rejects_invalid_import(change, message):
    a = artifact("a", "flower")
    a.update(change)
    with pytest.raises(ValueError, match=message):
        inventory_from_good(good(a))


def test_duplicate_ids_are_not_silently_merged():
    with pytest.raises(ValueError, match="unique"):
        inventory_from_good(good(artifact("same", "flower"), artifact("same", "plume")))


def test_generated_ids_keep_identical_pieces_distinct_and_fingerprint_order_independent():
    a = artifact("a", "flower")
    del a["id"]
    batch = inventory_from_good(good(a, a))
    assert len({a.id for a in batch.artifacts}) == 2
    assert (
        batch.fingerprint() == Inventory(tuple(reversed(batch.artifacts))).fingerprint()
    )
    assert batch.fingerprint() == inventory_from_good(good(a, a)).fingerprint()


def test_build_enforces_slots_and_distinct_ids():
    pieces = inventory().artifacts[::2]
    assert assemble_build(reversed(pieces)).artifact_ids == tuple(a.id for a in pieces)
    with pytest.raises(ValueError, match="each of five slots"):
        assemble_build(pieces[:-1])
    duplicate = Artifact(pieces[0].id, "TestSet", "plume", "atk", 5, 20, {}, {})
    with pytest.raises(ValueError, match="distinct"):
        assemble_build((pieces[0], duplicate, *pieces[2:]))


def test_actual_sets_activate_effects_and_scores_match_manual_assembly():
    effect = {
        "bonus": {
            "stage": "static",
            "unit": "atk",
            "expression": {"value": 100, "unit": "atk"},
            "contributes_to": "stats.atk",
            "when": {"set": "TestSet", "pieces": 4},
        }
    }
    target = scenario(effects=effect)
    pieces = inventory().artifacts[::2]
    result = evaluate_build(target, pieces)
    assert result.score == pytest.approx(100 * (1 + 3 * 0.466) + 311 + 100)
    assert result.feasible


def test_exact_search_matches_exhaustive_manual_scores():
    batch = inventory()
    target = scenario(minimums={"enerRech_": 1.2}, maximums={"enerRech_": 1.4})
    groups = [tuple(a for a in batch.artifacts if a.slot == slot) for slot in SLOT_KEYS]
    expected = sorted(
        (evaluation.score, tuple(a.id for a in loadout))
        for loadout in product(*groups)
        if (evaluation := evaluate_build(target, loadout)).feasible
    )
    result = search_builds(batch, target, top_k=100)
    assert result.status == "exact"
    assert result.combinations == result.evaluated == 32
    assert [(b.evaluation.score, b.build.artifact_ids) for b in result.builds] == list(
        reversed(expected)
    )


def test_upper_bound_does_not_trigger_unsafe_positive_stat_pruning():
    result = search_builds(inventory(), scenario(maximums={"enerRech_": 1.0}))
    assert result.status == "exact"
    assert len(result.builds) == 1
    assert all(
        identity.endswith("-0") for identity in result.builds[0].build.artifact_ids
    )


def test_removed_id_search_and_missing_slot_are_exactly_infeasible():
    batch = inventory()
    available = {a.id for a in batch.artifacts if a.slot != "goblet"}
    result = search_builds(batch, scenario(), available_ids=available)
    assert result.proven_infeasible
    with pytest.raises(ValueError, match="unknown available"):
        search_builds(batch, scenario(), available_ids=["missing"])


def test_unfinished_main_cannot_falsely_meet_current_threshold():
    batch = inventory_from_good(
        good(
            *[
                artifact(
                    slot, slot, level=0, main="enerRech_" if slot == "sands" else None
                )
                for slot in SLOT_KEYS
            ]
        )
    )
    result = search_builds(batch, scenario(minimums={"enerRech_": 1.4}))
    assert result.proven_infeasible


def test_bounded_failure_is_not_proven_infeasible_and_budget_is_respected():
    target = scenario(minimums={"enerRech_": 10})
    result = search_builds(inventory(), target, max_evaluations=3)
    assert result.status == "approximate"
    assert result.evaluated <= 3
    assert not result.proven_infeasible


def test_bounded_search_is_deterministic_and_improves_start():
    batch = inventory()
    first = search_builds(batch, scenario(), max_evaluations=20, seed=8)
    second = search_builds(batch, scenario(), max_evaluations=20, seed=8)
    assert first == second
    assert (
        first.builds[0].evaluation.score
        > evaluate_build(scenario(), batch.artifacts[::2]).score
    )


def test_unknown_set_is_not_silently_ignored():
    batch = inventory_from_good(good(artifact("a", "flower", set_key="UnknownSet")))
    with pytest.raises(ValueError, match="unknown inventory sets"):
        search_builds(batch, scenario())


def test_deadline_is_not_proven_infeasibility(monkeypatch):
    import artifact_sort.library_search as module

    ticks = iter([0, 2])
    monkeypatch.setattr(module, "monotonic", lambda: next(ticks))
    result = search_builds(inventory(), scenario(), time_limit=1)
    assert result.status == "timed_out"
    assert result.evaluated == 0
    assert not result.proven_infeasible


def test_file_import(tmp_path):
    path = tmp_path / "good.json"
    path.write_text(json.dumps(good(artifact("a", "flower"))))
    assert load_inventory(path).artifacts[0].id == "a"


def test_all_31_patterns_use_real_pieces_only_in_designated_slots():
    batch = inventory()
    references = inventory_from_good(
        good(*[artifact(f"reference-{slot}", slot) for slot in SLOT_KEYS])
    )
    reports = search_future_patterns(batch, scenario(), references, top_k=1)
    assert len(reports) == len(set(REAL_SLOT_PATTERNS)) == 31
    assert {len(pattern) for pattern in REAL_SLOT_PATTERNS} == {1, 2, 3, 4, 5}
    for report in reports:
        assert report.search.status == "exact"
        for slot, identity in zip(
            SLOT_KEYS, report.search.builds[0].build.artifact_ids
        ):
            assert identity.startswith("reference-") == (slot not in report.real_slots)
    all_real = next(report for report in reports if len(report.real_slots) == 5)
    assert all_real.search == search_builds(batch, scenario(), top_k=1)


def test_reference_pieces_cannot_replace_a_missing_real_slot():
    batch = inventory()
    references = inventory_from_good(
        good(*[artifact(f"reference-{slot}", slot) for slot in SLOT_KEYS])
    )
    available = {a.id for a in batch.artifacts if a.slot != "goblet"}
    reports = search_future_patterns(
        batch, scenario(), references, available_ids=available
    )
    assert all(
        report.search.proven_infeasible
        for report in reports
        if "goblet" in report.real_slots
    )
    assert all(
        report.search.builds for report in reports if "goblet" not in report.real_slots
    )


def test_future_search_requires_completed_outcomes_and_disjoint_identities():
    batch = inventory()
    with pytest.raises(ValueError, match="disjoint"):
        search_future_patterns(batch, scenario(), batch)
    unfinished = inventory_from_good(good(artifact("unfinished", "flower", level=0)))
    with pytest.raises(ValueError, match="completed"):
        search_future_patterns(unfinished, scenario(), Inventory(()))


def test_global_future_deadline_keeps_all_patterns_visible(monkeypatch):
    import artifact_sort.library_search as module

    ticks = iter([0] + [2] * 31)
    monkeypatch.setattr(module, "monotonic", lambda: next(ticks))
    reports = search_future_patterns(
        inventory(), scenario(), Inventory(()), time_limit=1
    )
    assert len(reports) == 31
    assert all(report.search.status == "timed_out" for report in reports)
    assert all(not report.search.proven_infeasible for report in reports)


def test_rules_manifest_and_diagnostic_cli(tmp_path, capsys):
    from artifact_sort.cli import main
    from artifact_sort.library import load_mechanics

    # Use a draft bundled formula with explicitly declared test game keys.
    root = Path(__file__).resolve().parents[1]
    library_path = root / "scenarios/library.example.json"
    document = json.loads(library_path.read_text())
    rules = {
        "format": "artifact-sort-mechanics",
        "version": 1,
        "id": document["mechanics"],
        "game_version": "test",
        "sets": ["TestSet", "OtherSet", "BlizzardStrayer", "EmblemOfSeveredFate"],
    }
    rules_path, good_path = tmp_path / "rules.json", tmp_path / "inventory.json"
    rules_path.write_text(json.dumps(rules))
    good_path.write_text(
        json.dumps(
            good(
                *[
                    artifact(
                        slot,
                        slot,
                        main={"goblet": "cryo_dmg_", "circlet": "critRate_"}.get(slot),
                        set_key="BlizzardStrayer",
                        substats={"enerRech_": 20},
                    )
                    for slot in SLOT_KEYS
                ]
            )
        )
    )
    assert not load_mechanics(rules_path).validated
    assert (
        main(
            [
                "library-builds",
                str(good_path),
                str(library_path),
                "--mechanics",
                str(rules_path),
                "--allow-draft",
            ]
        )
        == 0
    )
    output = json.loads(capsys.readouterr().out)
    assert output["kind"] == "library-build-diagnostics"
    assert output["formulaValidation"]["draft"]
    assert output["results"][0]["status"] == "exact"
    assert output["results"][0]["builds"]
    assert "trust" not in output


def test_rules_manifest_rejects_unknown_fields_and_invalid_channels(tmp_path):
    from artifact_sort.library import load_mechanics

    path = tmp_path / "rules.json"
    data = {
        "format": "artifact-sort-mechanics",
        "version": 1,
        "id": "rules",
        "game_version": "test",
        "sets": [],
        "surprise": True,
    }
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        load_mechanics(path)
    del data["surprise"]
    data["channels"] = {"bad": {"unit": "scalar", "combine": "mystery"}}
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        load_mechanics(path)


def test_future_mean_counts_failed_trials_as_zero_and_reports_qualification():
    from artifact_sort.future_value import evaluate_future_outcomes

    # Same artifact identities, two completed outcomes: one qualifies for ER,
    # the other provably fails. References cannot hide failure of an all-real build.
    passed = inventory_from_good(
        good(*[artifact(slot, slot, substats={"enerRech_": 30}) for slot in SLOT_KEYS])
    )
    failed = inventory_from_good(good(*[artifact(slot, slot) for slot in SLOT_KEYS]))
    reports = evaluate_future_outcomes(
        (passed, failed), scenario(minimums={"enerRech_": 2}), Inventory(())
    )
    all_real = next(report for report in reports if len(report.real_slots) == 5)
    qualified_score = (
        search_builds(passed, scenario(minimums={"enerRech_": 2}))
        .builds[0]
        .evaluation.score
    )
    assert all_real.expected_score == pytest.approx(qualified_score / 2)
    assert all_real.qualification_probability == (0.5, 0.5)
    assert all_real.exact and not all_real.opportunity_gap
    assert all_real.trials[1].score == 0
    assert len(reports) == 31
    assert all(
        report.opportunity_gap for report in reports if len(report.real_slots) != 5
    )


def test_approximate_future_failure_stays_unresolved():
    from artifact_sort.future_value import evaluate_future_outcomes

    reports = evaluate_future_outcomes(
        (inventory(),),
        scenario(minimums={"enerRech_": 100}),
        Inventory(()),
        max_evaluations=1,
    )
    all_real = next(report for report in reports if len(report.real_slots) == 5)
    assert all_real.expected_score is None
    assert all_real.qualification_probability == (0, 1)
    assert all_real.unresolved == 1
    assert not all_real.exact and not all_real.opportunity_gap


def test_future_deadline_marks_unstarted_trials_unresolved(monkeypatch):
    import artifact_sort.future_value as module

    monkeypatch.setattr(module, "monotonic", iter([0, 2, 2]).__next__)
    reports = module.evaluate_future_outcomes(
        (inventory(), inventory()), scenario(), Inventory(()), time_limit=1
    )
    assert all(
        report.unresolved == 2 and report.expected_score is None for report in reports
    )
    assert all(report.qualification_probability == (0, 1) for report in reports)


def test_future_trials_require_stable_identities():
    from artifact_sort.future_value import evaluate_future_outcomes

    with pytest.raises(ValueError, match="same artifact identities"):
        evaluate_future_outcomes(
            (inventory(), Inventory(())), scenario(), Inventory(())
        )


def test_slot_calibration_derives_weights_from_the_compiled_scenario():
    from artifact_sort.reference_profiles import calibrate_slot

    batch = inventory()
    context = Inventory(tuple(a for a in batch.artifacts if a.id.endswith("-0")))
    population = Inventory(tuple(a for a in batch.artifacts if a.slot == "flower"))
    calibrated, local = calibrate_slot(population, scenario(), context)
    assert local.weights["atk"] == 1
    assert local.weights["atk_"] == 100
    assert local.weights["enerRech_"] == 0
    assert calibrated.scores[1] - calibrated.scores[0] == pytest.approx(10)


def test_future_removal_reuses_outcomes_and_cannot_increase_exact_value():
    from artifact_sort.future_value import evaluate_future_outcomes

    batch = inventory()
    references = inventory_from_good(
        good(*[artifact(f"ref-{slot}", slot) for slot in SLOT_KEYS])
    )
    baseline = evaluate_future_outcomes((batch,), scenario(), references)
    retained = evaluate_future_outcomes(
        (batch,),
        scenario(),
        references,
        available_ids=(a.id for a in batch.artifacts if a.id != "flower-1"),
    )
    for original, reduced in zip(baseline, retained):
        assert reduced.exact and original.exact
        assert reduced.expected_score <= original.expected_score
        if "flower" not in original.real_slots:
            assert reduced == original


def test_new_inventory_protection_uses_stars_equipment_and_pins_not_locks():
    batch = inventory_from_good(
        good(
            {**artifact("locked", "flower"), "lock": True},
            {**artifact("starred", "flower"), "astralMark": True},
            {**artifact("equipped", "plume"), "location": "Amber"},
            artifact("pinned", "goblet"),
        )
    )
    assert batch.protected_ids(("pinned",)) == {"starred", "equipped", "pinned"}
    with pytest.raises(ValueError, match="unknown available"):
        batch.protected_ids(("missing",))


def test_hypothetical_contexts_cover_sets_missing_from_owned_inventory():
    from artifact_sort.artifact_sampling import sampling_rules
    from artifact_sort.reference_contexts import generate_reference_contexts

    definition = scenario(sets=[{"TestSet": 4}])
    portfolio = generate_reference_contexts(
        Inventory(()),
        definition,
        sampling_rules(),
        population_per_set_slot=1,
        top_k=1,
        max_evaluations=100,
        seed=7,
    )
    assert portfolio.inventory_search.proven_infeasible
    assert portfolio.contexts
    assert all(context.source == "hypothetical" for context in portfolio.contexts)
    assert portfolio.hypothetical_search.status == "approximate"
    assert not portfolio.hypothetical_search.proven_infeasible
    assert not portfolio.sampling_validated
    for context in portfolio.contexts:
        assert context.linearization.evaluation.feasible
        assert sum(a.set_key == "TestSet" for a in context.inventory.artifacts) >= 4


def test_shared_context_portfolio_contains_both_sources_and_is_reproducible():
    from artifact_sort.artifact_sampling import sampling_rules
    from artifact_sort.reference_contexts import generate_reference_contexts

    options = dict(population_per_set_slot=1, top_k=1, max_evaluations=100, seed=3)
    first = generate_reference_contexts(
        inventory(), scenario(), sampling_rules(), **options
    )
    second = generate_reference_contexts(
        inventory(), scenario(), sampling_rules(), **options
    )
    assert {context.source for context in first.contexts} == {
        "inventory",
        "hypothetical",
    }
    assert first == second


def test_future_timeout_does_not_hide_invalid_identity_or_completion_inputs():
    from artifact_sort.future_value import evaluate_future_outcomes

    with pytest.raises(ValueError, match="unknown available"):
        evaluate_future_outcomes(
            (inventory(),),
            scenario(),
            Inventory(()),
            available_ids=("missing",),
            time_limit=1e-12,
        )
    unfinished = inventory_from_good(good(artifact("unfinished", "flower", level=0)))
    with pytest.raises(ValueError, match="completed"):
        evaluate_future_outcomes(
            (unfinished,), scenario(), Inventory(()), time_limit=1e-12
        )


def deletion_fixture(*, exceptional=False):
    from artifact_sort.library_deletion import BuildTarget, BuildTrial

    batch = inventory_from_good(
        good(
            artifact("attack", "flower", substats={"atk": 1000}),
            artifact("defense", "flower", substats={"def": 1000}),
            artifact("balanced", "flower", substats={"atk": 500, "def": 500}),
            *[
                {**artifact(slot, slot), "astralMark": True}
                for slot in SLOT_KEYS
                if slot != "flower"
            ],
        )
    )
    targets = []
    for key in ("atk", "def"):
        doc = {
            "format": "artifact-sort-scenario-library",
            "version": 4,
            "revision": "deletion-test",
            "mechanics": "rules",
            "scoring_formulas": {
                "score": {
                    "unit": key,
                    "expression": {"stat": key, "stage": "effective"},
                }
            },
            "established": [
                {
                    "id": key,
                    "family": f"character/{key}",
                    "scoring_formula": "score",
                    "base": {"atk": 100, "def": 100},
                    "sets": [{}],
                }
            ],
            "parameter_variations": [],
            "structural_variations": [],
            "components": {},
            "channels": {},
            "effects": [],
        }
        compiled = (
            library_from_data(doc)
            .compile(
                Mechanics("rules", "test", frozenset({"TestSet"})), allow_draft=True
            )
            .scenarios[key]
        )
        for category in ("current", "ordinary", "strong"):
            targets.append(
                BuildTarget(
                    f"{key}-{category}",
                    f"character/{key}",
                    category,
                    (BuildTrial(compiled, (batch,)),),
                )
            )
        if exceptional:
            targets.append(
                BuildTarget(
                    f"{key}-exceptional",
                    f"character/{key}",
                    "exceptional",
                    (BuildTrial(compiled, (batch,)),),
                )
            )
    return batch, tuple(targets)


def test_joint_deletion_oracle_keeps_the_balanced_piece_not_two_specialists():
    from artifact_sort.library_deletion import select_deletions

    batch, targets = deletion_fixture()
    result = select_deletions(batch, targets, 2, method="exhaustive")
    assert result.status == "exact"
    assert result.deleted_ids == ("attack", "defense")
    assert result.checked == 3 and result.search_exact
    assert not result.gaps


def test_joint_milp_matches_exhaustive_oracle_with_exceptional_targets():
    from artifact_sort.library_deletion import select_deletions

    batch, targets = deletion_fixture(exceptional=True)
    exact = select_deletions(batch, targets, 2, method="exhaustive")
    pooled = select_deletions(batch, targets, 2, method="milp")
    assert pooled.status == "pool_relative"
    assert pooled.deleted_ids == exact.deleted_ids
    assert pooled.objective == exact.objective


def test_retained_research_recovers_builds_missing_from_initial_top_one_pool():
    from artifact_sort.library_deletion import select_deletions

    # One alternative per term initially forces both specialist winners to
    # survive. Explore retained gear instead of declaring pool failure infeasible.
    batch, targets = deletion_fixture()
    incomplete = select_deletions(batch, targets, 2, method="milp", builds_per_trial=1)
    assert incomplete.status == "pool_relative"
    assert incomplete.deleted_ids == ("attack", "defense")
    assert incomplete.checked >= 3


def test_bounded_coverage_gaps_protect_and_unbounded_gaps_block():
    from artifact_sort.library_deletion import CoverageGap, select_deletions

    batch, targets = deletion_fixture()
    blocked = select_deletions(
        batch, targets, 2, coverage_gaps=(CoverageGap("unknown coverage"),)
    )
    assert blocked.status == "blocked"
    protected = select_deletions(
        batch,
        targets,
        2,
        coverage_gaps=(CoverageGap("unsupported crafting", frozenset({"attack"})),),
    )
    assert protected.status == "exact"
    assert "attack" not in protected.deleted_ids
    assert protected.gaps[0].affected_ids == {"attack"}


def test_requested_count_exceeding_protection_is_infeasible():
    from artifact_sort.library_deletion import select_deletions

    batch, targets = deletion_fixture()
    result = select_deletions(batch, targets, 4)
    assert result.status == "infeasible" and not result.deleted_ids


def test_current_targets_cannot_use_hypothetical_or_invented_stats():
    from artifact_sort.library_deletion import BuildTarget, BuildTrial, select_deletions

    batch, targets = deletion_fixture()
    fictional = inventory_from_good(good(artifact("reference", "flower")))
    forged = BuildTarget(
        "forged",
        "character/atk",
        "current",
        (BuildTrial(targets[0].trials[0].scenario, (fictional,)),),
    )
    with pytest.raises(ValueError, match="actual inventory"):
        select_deletions(batch, (forged,), 1)


def test_oracle_budget_does_not_claim_exact_or_infeasible():
    from artifact_sort.library_deletion import select_deletions

    batch, targets = deletion_fixture()
    result = select_deletions(
        batch, targets, 2, method="exhaustive", max_removal_combinations=1
    )
    assert result.status == "pool_relative" and result.checked == 1


def test_available_primary_category_can_rank_deletions():
    from artifact_sort.library_deletion import select_deletions

    batch, targets = deletion_fixture()
    result = select_deletions(batch, targets[:1], 1)
    assert result.status == "exact"
    assert result.objective.family_average == result.objective.worst_loss


def test_structural_contexts_survive_a_top_one_score_pool():
    batch = inventory_from_good(
        good(
            artifact("flower", "flower"),
            artifact("plume", "plume"),
            artifact("attack-sands", "sands", main="atk_"),
            artifact("energy-sands", "sands", main="enerRech_"),
            artifact("goblet", "goblet"),
            artifact("circlet", "circlet"),
        )
    )
    result = search_builds(batch, scenario(), top_k=1, collect_contexts=True)
    assert len(result.builds) == 1
    assert {build.build.main_stats["sands"] for build in result.context_builds} == {
        "atk_",
        "enerRech_",
    }


def test_target_assembly_keeps_all_31_patterns_and_separate_reference_contexts():
    from dataclasses import replace
    from artifact_sort.library_deletion import build_targets

    batch = inventory()
    definition = scenario()
    definition = replace(
        definition, definition=replace(definition.definition, family="character/role")
    )
    first = inventory_from_good(
        good(*[artifact(f"reference-a-{slot}", slot) for slot in SLOT_KEYS])
    )
    second = inventory_from_good(
        good(*[artifact(f"reference-b-{slot}", slot) for slot in SLOT_KEYS])
    )
    profiles = {
        "one": {
            category: (first, second)
            for category in ("ordinary", "strong", "exceptional")
        }
    }
    targets = build_targets(batch, (definition,), (batch,), profiles)
    assert len(targets) == 1 + 3 * 31
    assert targets[0].category == "current"
    for target in targets[1:]:
        assert len(target.trials[0].candidates) == 2
        for candidates in target.trials[0].candidates:
            references = {
                a.id.split("-")[1]
                for a in candidates.artifacts
                if a.id.startswith("reference-")
            }
            assert len(references) <= 1


def test_end_to_end_encoded_deletion_cli_and_persistent_cache(tmp_path, capsys):
    from artifact_sort.cli import main
    from test_library import document

    library = document()
    library["established"][0]["family"] = "character/role"
    library_path, mechanics_path, inventory_path = (
        tmp_path / name for name in ("library.json", "rules.json", "inventory.json")
    )
    library_path.write_text(json.dumps(library))
    mechanics_path.write_text(
        json.dumps(
            {
                "format": "artifact-sort-mechanics",
                "version": 1,
                "id": library["mechanics"],
                "game_version": "test",
                "sets": ["TestSet"],
            }
        )
    )
    pieces = []
    for slot in SLOT_KEYS:
        subs = {"critRate_": 7, "critDMG_": 14, "enerRech_": 10}
        subs["hp" if slot == "plume" else "atk"] = 200 if slot == "plume" else 20
        pieces.append(
            {**artifact(slot, slot, substats=subs), "astralMark": slot != "flower"}
        )
    pieces.append(
        artifact(
            "weak-flower",
            "flower",
            substats={"atk": 10, "critRate_": 7, "critDMG_": 14, "enerRech_": 10},
        )
    )
    inventory_path.write_text(json.dumps(good(*pieces)))
    args = [
        "library-delete",
        str(inventory_path),
        str(library_path),
        "--mechanics",
        str(mechanics_path),
        "--allow-draft",
        "--free",
        "1",
        "--population",
        "32",
        "--trials",
        "1",
        "--max-evaluations",
        "64",
        "--time-limit",
        "30",
        "--cache",
        str(tmp_path / "cache.sqlite"),
    ]
    assert main(args) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["kind"] == "library-deletion-diagnostics" and output["draft"]
    assert output["cacheStatus"] == "miss"
    for selection in output["selections"].values():
        assert selection["deletedArtifactIds"] == ["weak-flower"]
        assert selection["status"] in ("exact", "pool_relative")
        assert len(selection["qualification"]) == 94
    assert main(args) == 0
    cached = json.loads(capsys.readouterr().out)
    assert cached["cacheStatus"] == "hit"
    assert cached["selections"] == output["selections"]

    assert main([*args, "--no-reuse"]) == 0
    uncached = json.loads(capsys.readouterr().out)
    assert uncached["cacheStatus"] == "disabled"
    assert uncached["cacheStatistics"]["intermediate"] == {}
    assert uncached["selections"] == output["selections"]

    # A different deletion count bypasses the report cache but shares numerical work.
    changed = list(args)
    changed[changed.index("--free") + 1] = "0"
    assert main(changed) == 0
    partial = json.loads(capsys.readouterr().out)
    assert partial["cacheStatus"] == "miss"
    assert partial["cacheStatistics"]["intermediate"]["search"]["persistentHits"] > 0
    assert partial["cacheStatistics"]["intermediate"]["upgrade"][
        "persistentHits"
    ] == len(pieces)


def test_exceptional_tie_break_cannot_buy_a_worse_primary_result():
    from dataclasses import replace
    from artifact_sort.library_deletion import BuildTarget, BuildTrial, select_deletions

    batch, targets = deletion_fixture()
    exception = BuildTarget(
        "attack-exceptional", "character/atk", "exceptional", targets[0].trials
    )
    result = select_deletions(batch, (*targets, exception), 2, method="milp")
    assert result.deleted_ids == ("attack", "defense")
    assert result.objective.exceptional_worst_loss > 0


def test_joint_future_qualification_counts_failed_trials_in_unconditional_mean():
    from artifact_sort.library_deletion import BuildTarget, BuildTrial, select_deletions

    batch, targets = deletion_fixture()
    passing = BuildTrial(targets[0].trials[0].scenario, (batch,))
    failing = BuildTrial(scenario(minimums={"enerRech_": 100}), (batch,))
    configured = tuple(
        BuildTarget(
            target.id,
            target.family,
            target.category,
            target.trials if target.category == "current" else (passing, failing),
        )
        for target in targets[:3]
    )
    result = select_deletions(batch, configured, 1, method="exhaustive")
    assert result.status == "exact"
    for item in result.qualification:
        expected = 1 if item.target.endswith("current") else 0.5
        assert item.baseline == item.retained == expected
    measured = {
        item.target.category: item.target.baseline for item in result.objective.targets
    }
    assert measured["ordinary"] == measured["current"] / 2


def test_future_identity_properties_cannot_change_between_trials():
    from dataclasses import replace
    from artifact_sort.library_deletion import BuildTarget, BuildTrial, select_deletions

    batch, targets = deletion_fixture()
    forged = Inventory(
        tuple(
            replace(a, set_key="OtherSet") if a.id == "attack" else a
            for a in batch.artifacts
        )
    )
    target = BuildTarget(
        "forged-future",
        "character/atk",
        "ordinary",
        (BuildTrial(targets[0].trials[0].scenario, (forged,)),),
    )
    with pytest.raises(ValueError, match="identity"):
        select_deletions(batch, (target,), 1)


@pytest.mark.parametrize("method", ["exhaustive", "milp"])
@pytest.mark.parametrize("category", ["current", "ordinary", "exceptional"])
def test_nonpositive_targets_do_not_block_other_scenarios(method, category):
    from artifact_sort.library_deletion import BuildTarget, BuildTrial, select_deletions

    batch, targets = deletion_fixture()
    absent = BuildTarget(
        "absent/" + category,
        "missing/role",
        category,
        (BuildTrial(scenario(minimums={"enerRech_": 100}), (batch,)),),
    )
    original = select_deletions(batch, targets, 2, method=method)
    result = select_deletions(batch, (*targets, absent), 2, method=method)
    assert result.status == original.status
    assert result.deleted_ids == original.deleted_ids
    assert result.objective == original.objective
    assert not result.gaps
    assert len(result.excluded) == 1
    assert result.excluded[0].target == absent.id
    assert result.excluded[0].scenarios == (absent.trials[0].scenario.definition.id,)
    assert result.excluded[0].baseline == 0
    assert all(value.target != absent.id for value in result.qualification)


def test_excluding_all_targets_reports_absence_without_blind_deletions():
    from artifact_sort.library_deletion import BuildTarget, BuildTrial, select_deletions

    batch, _ = deletion_fixture()
    absent = BuildTarget(
        "absent",
        "missing/role",
        "current",
        (BuildTrial(scenario(minimums={"enerRech_": 100}), (batch,)),),
    )
    result = select_deletions(batch, (absent,), 1)
    assert result.status == "blocked"
    assert not result.deleted_ids
    assert result.excluded[0].target == "absent"
    assert result.gaps[0].reason == "no measurable primary targets remain"


def test_approximate_empty_baseline_stays_unresolved():
    from artifact_sort.library_deletion import BuildTarget, BuildTrial, select_deletions

    batch, targets = deletion_fixture()
    absent = BuildTarget(
        "unresolved",
        "missing/role",
        "ordinary",
        (BuildTrial(scenario(minimums={"enerRech_": 100}), (batch,)),),
    )
    result = select_deletions(batch, (*targets, absent), 1, max_evaluations=1)
    assert result.status == "blocked"
    assert not result.excluded
    assert any("unresolved" in gap.reason for gap in result.gaps)


@pytest.mark.parametrize("method", ["exhaustive", "milp"])
@pytest.mark.parametrize("baseline", [0, -10])
def test_qualifying_nonpositive_baseline_is_excluded_and_serialized(method, baseline):
    from artifact_sort.library_analysis import LibraryDeletionAnalysis, analysis_payload
    from artifact_sort.library_deletion import BuildTarget, BuildTrial, select_deletions
    from test_library import document, compile_doc

    batch, targets = deletion_fixture()
    doc = document()
    doc["scoring_formulas"]["score"]["expression"] = {"value": baseline, "unit": "atk"}
    nonpositive = compile_doc(doc).scenarios["one"]
    # Replace one category in a measurable family: the remaining two categories
    # must receive equal shares in both the oracle and MILP objectives.
    configured = (
        BuildTarget(
            "nonpositive",
            targets[0].family,
            "current",
            (BuildTrial(nonpositive, (batch,)),),
        ),
        *targets[1:],
    )
    result = select_deletions(batch, configured, 2, method=method)
    expected = select_deletions(batch, targets[1:], 2, method=method)
    assert result.status == expected.status
    assert result.deleted_ids == expected.deleted_ids
    assert result.objective == expected.objective
    assert result.excluded[0].baseline == baseline
    payload = analysis_payload(
        LibraryDeletionAnalysis(
            {"established": result, "combined": result},
            {},
            {},
            True,
            "test",
        )
    )
    decoded = json.loads(json.dumps(payload))
    for selection in decoded["selections"].values():
        assert selection["excludedTargets"] == [
            {
                "target": "nonpositive",
                "scenarioIds": ["one"],
                "family": targets[0].family,
                "category": "current",
                "baseline": baseline,
                "reason": "nonpositive_baseline",
            }
        ]
