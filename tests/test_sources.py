from __future__ import annotations

import json
import sys

import numpy as np

from artifact_sort.scenarios import Scenario
from artifact_sort.sources import GOEvaluator, akasha_scenarios, import_akasha, import_go


def test_go_import_preserves_exact_target_metadata(tmp_path):
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
    scenarios = import_go(path)
    assert len(scenarios) == 1
    scenario = scenarios[0]
    assert scenario.tier == "current"
    assert scenario.set_requirements == {"EmblemOfSeveredFate": 4}
    assert scenario.metadata["adapter_required"] is True
    assert scenario.metadata["targets"][0]["weight"] == 2


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
