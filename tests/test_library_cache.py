from dataclasses import replace

import pytest

from artifact_sort.artifact_sampling import (
    sample_completed_inventory,
    sample_slot,
    sampling_rules,
)
from artifact_sort.cache import ResultCache
from artifact_sort.inventory import Inventory, inventory_from_good
from artifact_sort.library_cache import AnalysisCache
from artifact_sort.library_search import search_builds
from test_inventory_search import artifact, good, inventory, scenario, deletion_fixture
from test_library import document, compile_doc


@pytest.mark.parametrize("budget", [1, 1000])
@pytest.mark.parametrize("contexts", [False, True])
def test_search_reuse_preserves_all_numerical_results(tmp_path, budget, contexts):
    batch, compiled = inventory(), scenario()
    options = dict(max_evaluations=budget, collect_contexts=contexts)
    expected = search_builds(batch, compiled, **options)
    store = ResultCache(tmp_path / "cache.sqlite")
    cache = AnalysisCache(store)
    assert search_builds(batch, compiled, cache=cache, **options) == expected
    assert search_builds(batch, compiled, cache=cache, **options) == expected
    assert cache.summary()["search"]["memoryHits"] == 1
    restarted = AnalysisCache(ResultCache(store.path))
    assert search_builds(batch, compiled, cache=restarted, **options) == expected
    assert restarted.summary()["search"]["persistentHits"] == 1


def test_search_keys_include_formula_stats_and_search_options():
    batch, compiled = inventory(), scenario()
    cache = AnalysisCache()
    search_builds(batch, compiled, cache=cache)
    changed = Inventory(
        tuple(
            replace(a, substats={"eleMas": 100}) if a.slot == "flower" else a
            for a in batch.artifacts
        )
    )
    cases = [
        (changed, compiled, {}),
        (batch, scenario(minimums={"enerRech_": 100}), {}),
        (batch, compiled, {"seed": 1}),
        (batch, compiled, {"top_k": 1}),
        (batch, compiled, {"max_evaluations": 1}),
        (batch, compiled, {"collect_contexts": True}),
    ]
    for candidates, target, options in cases:
        assert search_builds(
            candidates, target, cache=cache, **options
        ) == search_builds(candidates, target, **options)
    assert cache.summary()["search"]["misses"] == len(cases) + 1
    assert not cache.summary()["search"].get("memoryHits")


def test_changes_outside_eligible_candidates_reuse_search_across_runs(tmp_path):
    doc = document()
    doc["established"][0]["mains"] = {"sands": ["atk_"]}
    compiled = compile_doc(doc).scenarios["one"]
    batch = inventory_from_good(
        good(
            *[
                artifact(slot, slot)
                for slot in ("flower", "plume", "sands", "goblet", "circlet")
            ],
            artifact("ineligible", "sands", main="def_", substats={"eleMas": 10}),
        )
    )
    store = ResultCache(tmp_path / "cache.sqlite")
    original = search_builds(batch, compiled, cache=AnalysisCache(store))
    changed = Inventory(
        tuple(
            replace(a, substats={"eleMas": 20}) if a.id == "ineligible" else a
            for a in batch.artifacts
        )
    )
    restarted = AnalysisCache(ResultCache(store.path))
    assert search_builds(changed, compiled, cache=restarted) == original
    assert restarted.summary()["search"]["persistentHits"] == 1
    # Cache reuse must not conceal a now-invalid available-ID request.
    with pytest.raises(ValueError, match="unknown available"):
        search_builds(batch, compiled, available_ids=["missing"], cache=restarted)


def test_protection_metadata_is_not_part_of_numerical_search_keys():
    batch, compiled = inventory(), scenario()
    cache = AnalysisCache()
    expected = search_builds(batch, compiled, cache=cache)
    changed = Inventory(
        tuple(
            replace(a, starred=True, locked=True, location="KukiShinobu")
            for a in batch.artifacts
        )
    )
    assert search_builds(changed, compiled, cache=cache) == expected
    assert changed.protected_ids() == frozenset(a.id for a in changed.artifacts)
    assert cache.summary()["search"]["memoryHits"] == 1


def test_timed_out_searches_are_never_cached(tmp_path, monkeypatch):
    import artifact_sort.library_search as module

    clock = iter([0, 2])
    monkeypatch.setattr(module, "monotonic", lambda: next(clock))
    store = ResultCache(tmp_path / "cache.sqlite")
    cache = AnalysisCache(store)
    result = search_builds(inventory(), scenario(), time_limit=1, cache=cache)
    assert result.status == "timed_out"
    assert not cache.searches
    assert store.summary()["writes"] == 0
    assert cache.summary()["search"]["interrupted"] == 1


def test_upgrade_delta_reuses_unchanged_artifacts_and_preserves_current_metadata(
    tmp_path,
):
    rules = sampling_rules()
    batch = sample_slot("flower", "TestSet", 20, rules, seed=4)
    # Exercise unfinished tapes, including a known hidden fourth line.
    batch = Inventory(tuple(replace(a, level=0) for a in batch.artifacts))
    store = ResultCache(tmp_path / "cache.sqlite")
    cache = AnalysisCache(store)
    expected = sample_completed_inventory(batch, rules, seed=3, trial=2)
    assert cache.completed_inventory(batch, rules, seed=3, trial=2) == expected
    first = batch.artifacts[0]
    key = next(iter(first.substats))
    modified = replace(first, substats={**first.substats, key: first.substats[key] + 1})
    changed = Inventory(
        (
            modified,
            *(
                replace(a, starred=True, locked=True, location="KukiShinobu")
                for a in batch.artifacts[1:]
            ),
        )
    )
    restarted = AnalysisCache(ResultCache(store.path))
    actual = restarted.completed_inventory(changed, rules, seed=3, trial=2)
    assert actual == sample_completed_inventory(changed, rules, seed=3, trial=2)
    assert restarted.summary()["upgrade"]["persistentHits"] == 19
    assert restarted.summary()["upgrade"]["misses"] == 1
    assert all(a.starred and a.location == "KukiShinobu" for a in actual.artifacts[1:])
    # Other tapes are independent cache entries.
    restarted.completed_inventory(changed, rules, seed=3, trial=3)
    assert restarted.summary()["upgrade"]["misses"] == 21


def test_population_reuse_and_invalidation(tmp_path):
    rules = sampling_rules()
    store = ResultCache(tmp_path / "cache.sqlite")
    cache = AnalysisCache(store)
    expected = sample_slot("flower", "TestSet", 32, rules, seed=2)
    assert cache.population("flower", "TestSet", 32, rules, seed=2) == expected
    restarted = AnalysisCache(ResultCache(store.path))
    assert restarted.population("flower", "TestSet", 32, rules, seed=2) == expected
    assert restarted.summary()["population"]["persistentHits"] == 1
    for size, seed in [(16, 2), (32, 3)]:
        assert restarted.population(
            "flower", "TestSet", size, rules, seed=seed
        ) == sample_slot("flower", "TestSet", size, rules, seed=seed)
    changed_rules = replace(rules, four_line_probability=0.5)
    assert restarted.population(
        "flower", "TestSet", 32, changed_rules, seed=2
    ) == sample_slot("flower", "TestSet", 32, changed_rules, seed=2)
    assert restarted.summary()["population"]["misses"] == 3


@pytest.mark.parametrize("method", ["exhaustive", "milp"])
def test_joint_selector_outputs_match_without_reuse(method):
    from artifact_sort.library_deletion import select_deletions

    batch, targets = deletion_fixture(exceptional=True)
    expected = select_deletions(batch, targets, 2, method=method)
    cache = AnalysisCache()
    actual = select_deletions(batch, targets, 2, method=method, cache=cache)
    assert actual == expected
    assert cache.summary()["search"]["memoryHits"] > 0


def test_bad_persistent_search_entry_is_a_miss(tmp_path):
    batch, compiled = inventory(), scenario()
    store = ResultCache(tmp_path / "cache.sqlite")
    cache = AnalysisCache(store)
    search_builds(batch, compiled, cache=cache)
    key = next(iter(cache.searches))
    store.put("encoded-search", key, {"status": "exact", "builds": "broken"})
    restarted = AnalysisCache(store)
    assert search_builds(batch, compiled, cache=restarted) == search_builds(
        batch, compiled
    )
    assert restarted.summary()["search"]["misses"] == 1


def test_search_cache_survives_a_new_process_and_hash_seed(tmp_path):
    import os
    from pathlib import Path
    import subprocess
    import sys

    path = tmp_path / "cache.sqlite"
    expected = search_builds(
        inventory(), scenario(), cache=AnalysisCache(ResultCache(path))
    )
    code = """
import sys
sys.path.insert(0, 'tests')
from test_inventory_search import inventory, scenario
from artifact_sort.cache import ResultCache
from artifact_sort.library_cache import AnalysisCache
from artifact_sort.library_search import search_builds
cache = AnalysisCache(ResultCache(sys.argv[1]))
result = search_builds(inventory(), scenario(), cache=cache)
assert cache.summary()['search']['persistentHits'] == 1
print(result.evaluated, result.combinations, result.status)
"""
    result = subprocess.run(
        [sys.executable, "-c", code, str(path)],
        cwd=Path(__file__).resolve().parents[1],
        env={**os.environ, "PYTHONHASHSEED": "123"},
        capture_output=True,
        text=True,
        check=True,
    )
    assert (
        result.stdout.strip()
        == f"{expected.evaluated} {expected.combinations} {expected.status}"
    )
