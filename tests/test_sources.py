from __future__ import annotations

import json
import sys

import numpy as np

from artifact_sort.model import STAT_INDEX
from artifact_sort.scenarios import (
    Scenario,
    SetStrategy,
    scenario_from_mapping,
    scenario_to_mapping,
)
from artifact_sort.sources import (
    GOEvaluator,
    akasha_scenarios,
    import_akasha,
    import_go,
    import_go_database,
)


def _go_database() -> dict[str, object]:
    return {
        "format": "GOOD",
        "source": "Genshin Optimizer",
        "version": 3,
        "dbVersion": 42,
        "dbMeta": {"name": "Account", "gender": "F"},
        "characters": [
            {
                "key": "RaidenShogun",
                "level": 90,
                "ascension": 6,
                "constellation": 2,
                "talent": {"auto": 6, "skill": 9, "burst": 10},
            }
        ],
        "artifacts": [],
        "weapons": [],
        "builds": [],
        "buildTcs": [
            {
                "id": "buildTc_0",
                "name": "Burst",
                "characterKey": "RaidenShogun",
                "artifact": {
                    "sets": {"EmblemOfSeveredFate": 4},
                    "slots": {"goblet": {"statKey": "electro_dmg_"}},
                    "substats": {"stats": {"atk_": 46.6, "enerRech_": 50}},
                },
            }
        ],
        "optConfigs": [
            {
                "id": "optConfig_0",
                "optimizationTarget": ["custom", "0"],
                "statFilters": {
                    '["basic","enerRech_"]': [
                        {"value": 220, "disabled": False}
                    ]
                },
                "mainStatKeys": {"sands": ["enerRech_", "atk_"]},
            }
        ],
        "teamchars": [
            {
                "id": "teamchar_0",
                "key": "RaidenShogun",
                "name": "Raiden carry",
                "optConfigId": "optConfig_0",
                "customMultiTargets": [
                    {
                        "name": "Rotation",
                        "targets": [
                            {
                                "weight": 2,
                                "path": ["burst", "dmg"],
                                "hitMode": "avgHit",
                            }
                        ],
                    }
                ],
                "bonusStats": {},
                "hitMode": "avgHit",
            }
        ],
        "teams": [
            {
                "id": "team_0",
                "name": "Raiden National",
                "loadoutData": [
                    {
                        "teamCharId": "teamchar_0",
                        "buildType": "tc",
                        "buildTcId": "buildTc_0",
                        "buildId": "",
                    }
                ],
            }
        ],
    }


def test_go_database_import_resolves_team_target_and_build(tmp_path):
    export = _go_database()
    path = tmp_path / "go-database.json"
    path.write_text(json.dumps(export))
    result = import_go_database(path)
    scenarios = list(result.scenarios)
    assert result.database["counts"]["teams"] == 1
    assert result.skipped == ()
    assert len(scenarios) == 1
    scenario = scenarios[0]
    assert scenario.tier == "current"
    assert scenario.set_requirements == {"EmblemOfSeveredFate": 4}
    assert dict(scenario.constraints)[STAT_INDEX["enerRech_"]] == 220
    assert scenario.metadata["adapter_required"] is True
    assert scenario.metadata["targets"][0]["weight"] == 2
    assert scenario.metadata["team_id"] == "team_0"
    assert scenario.metadata["build_origin"] == "tc"
    assert scenario.metadata["team_context"]["loadouts"][0][
        "opt_config_id"
    ] == "optConfig_0"


def test_go_database_import_derives_selected_real_build(tmp_path):
    export = _go_database()
    export["artifacts"] = [
        {
            "id": f"artifact_{index}",
            "setKey": "EmblemOfSeveredFate",
            "slotKey": slot,
            "level": 20,
            "rarity": 5,
            "mainStatKey": main,
            "substats": [{"key": "critRate_", "value": 7.8}],
        }
        for index, (slot, main) in enumerate(
            (
                ("flower", "hp"),
                ("plume", "atk"),
                ("sands", "enerRech_"),
                ("goblet", "electro_dmg_"),
                ("circlet", "critRate_"),
            )
        )
    ]
    export["weapons"] = [
        {
            "id": "weapon_0",
            "key": "EngulfingLightning",
            "level": 90,
            "ascension": 6,
            "refinement": 1,
        }
    ]
    export["builds"] = [
        {
            "id": "build_0",
            "name": "Saved build",
            "characterKey": "RaidenShogun",
            "weaponId": "weapon_0",
            "artifactIds": {
                slot: f"artifact_{index}"
                for index, slot in enumerate(
                    ("flower", "plume", "sands", "goblet", "circlet")
                )
            },
        }
    ]
    export["teams"][0]["loadoutData"][0].update(
        {"buildType": "real", "buildId": "build_0", "buildTcId": ""}
    )
    path = tmp_path / "go-database.json"
    path.write_text(json.dumps(export))
    scenario = import_go(path)[0]
    assert scenario.metadata["build_origin"] == "real"
    assert scenario.damage_stat == "electro_dmg_"
    assert scenario.set_requirements == {}
    assert len(scenario.metadata["focus_loadout"]["selected_build"]["artifacts"]) == 5


def test_go_import_uses_generated_optimizer_sets_instead_of_selected_build(tmp_path):
    export = _go_database()
    slots = ("flower", "plume", "sands", "goblet", "circlet")
    export["artifacts"] = [
        {
            "id": f"artifact_{index}",
            "setKey": "GoldenTroupe",
            "slotKey": slot,
            "level": 20,
            "rarity": 5,
            "mainStatKey": {"flower": "hp", "plume": "atk"}.get(slot, "atk_"),
            "substats": [{"key": "critRate_", "value": 7.8}],
        }
        for index, slot in enumerate(slots)
    ]
    export["generatedBuildList"] = [
        {
            "id": "generated_0",
            "builds": [
                {
                    "artifactIds": {
                        slot: f"artifact_{index}" for index, slot in enumerate(slots)
                    }
                }
            ],
        }
    ]
    export["optConfigs"][0]["generatedBuildListId"] = "generated_0"
    path = tmp_path / "go-database.json"
    path.write_text(json.dumps(export))

    scenario = import_go(path)[0]

    assert scenario.set_requirements == {}
    assert [strategy.requirements for strategy in scenario.set_strategies] == [
        {"GoldenTroupe": 4}
    ]
    assert scenario.metadata["set_strategy_source"] == "go-generated-builds"
    assert scenario.metadata["reference_artifact_ids"] == tuple(
        f"artifact_{index}" for index in range(5)
    )
    assert len(scenario.metadata["reference_artifacts"]) == 5


def test_set_strategies_round_trip_through_scenario_mapping():
    scenario = Scenario(
        id="alternative-sets",
        set_strategies=(
            SetStrategy((("GoldenTroupe", 4),), source="go", evidence_count=4),
            SetStrategy(
                (("GladiatorsFinale", 2), ("GoldenTroupe", 2)),
                source="go",
            ),
        ),
    )

    restored = scenario_from_mapping(scenario_to_mapping(scenario))

    assert restored.set_strategies == scenario.set_strategies


def test_go_import_rejects_individual_team_export(tmp_path):
    export = {
        "loadoutData": {
            "key": "RaidenShogun",
            "buildTcs": [
                {
                    "name": "Burst",
                    "characterKey": "RaidenShogun",
                    "artifact": {
                        "sets": {"EmblemOfSeveredFate": 4},
                        "slots": {"goblet": {"statKey": "electro_dmg_"}},
                        "substats": {"stats": {"atk_": 46.6, "enerRech_": 50}},
                    },
                    "optConfig": {
                        "optimizationTarget": ["burst", "dmg"],
                        "statFilters": {
                            '["basic","enerRech_"]': {"enabled": True, "min": 220}
                        },
                        "mainStatKeys": {"sands": ["enerRech_", "atk_"]},
                    },
                    "customMultiTargets": [
                        {"weight": 2, "path": ["burst", "dmg"], "hitMode": "avgHit"}
                    ],
                }
            ],
        }
    }
    path = tmp_path / "go.json"
    path.write_text(json.dumps(export))
    with np.testing.assert_raises_regex(ValueError, "full Genshin Optimizer database"):
        import_go(path)


def test_akasha_snapshot_keeps_leaderboards_separate(tmp_path):
    path = tmp_path / "akasha.json"
    path.write_text(
        json.dumps(
            {
                "version": 1,
                "builds": [
                    {
                        "leaderboard_id": "a",
                        "category": "A",
                        "score": 100,
                        "artifacts": [],
                        "conditions": {"scenario": {"objective": "damage"}},
                    },
                    {
                        "leaderboard_id": "b",
                        "category": "B",
                        "score": 90,
                        "artifacts": [],
                        "conditions": {"scenario": {"objective": "reaction"}},
                    },
                ],
            }
        )
    )
    snapshot = import_akasha(path)
    assert len(snapshot.builds) == 2
    assert {scenario.id for scenario in akasha_scenarios(snapshot)} == {
        "akasha-a",
        "akasha-b",
    }


def test_go_evaluator_uses_persistent_versioned_batch_protocol():
    adapter = """
import json, sys
for line in sys.stdin:
    request = json.loads(line)
    if request['type'] == 'version':
        response = {'goVersion': 'test-commit'}
    else:
        response = {
            'goVersion': 'test-commit',
            'utilities': [sum(row.values()) for row in request['artifactStats']],
        }
    print(json.dumps(response), flush=True)
"""
    evaluator = GOEvaluator((sys.executable, "-u", "-c", adapter))
    try:
        values = evaluator.evaluate_batch(np.ones((2, 19)), Scenario(id="go"))
        assert evaluator.version == "go:test-commit"
        assert np.array_equal(values, (19.0, 19.0))
    finally:
        evaluator.close()
