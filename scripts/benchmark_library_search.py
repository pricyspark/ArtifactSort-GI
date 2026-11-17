"""Reproducible scalar/batch and screened/unscreened search comparisons.

Run from the repository root:
    python -m scripts.benchmark_library_search --seeds 3
Use --library and --mechanics to exercise a particular installed rules release.
Results describe the supplied sample, not global search error or game accuracy.
"""

import argparse
import json
from time import perf_counter

import numpy as np

from artifact_sort.artifact_sampling import sample_slot, sampling_rules
from artifact_sort.batch_evaluation import evaluate_batch
from artifact_sort.inventory import Inventory, assemble_build
from artifact_sort.library import Mechanics, load_library, load_mechanics
from artifact_sort.library_search import search_builds
from artifact_sort.model import SLOT_KEYS, STAT_KEYS


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library", default="scenarios/library.example.json")
    parser.add_argument("--mechanics")
    parser.add_argument("--scenario")
    parser.add_argument("--rows", type=int, default=20_000)
    parser.add_argument("--pieces", type=int, default=100, help="samples per set and slot")
    parser.add_argument("--evaluations", type=int, default=20_000)
    parser.add_argument("--seeds", type=int, default=3)
    args = parser.parse_args()
    if min(args.rows, args.pieces, args.evaluations, args.seeds) <= 0:
        parser.error("counts must be positive")
    library = load_library(args.library)
    if args.mechanics:
        mechanics = load_mechanics(args.mechanics)
    else:
        # The bundled example needs no external numerical components. Other
        # libraries can provide their pinned release explicitly via --mechanics.
        keys = {key for scenario in library.scenarios.values()
                for strategy in scenario.sets for key in strategy}
        keys.update(key for component in library.components.values()
                    if component.when for key in component.when.set_keys)
        mechanics = Mechanics(
            library.mechanics, "benchmark-only", frozenset(keys | {"TestSet", "OtherSet"}),
            frozenset(key for scenario in library.scenarios.values() for key in scenario.characters),
        )
    compiled = library.compile(mechanics, allow_draft=True)
    target = compiled.scenarios[args.scenario] if args.scenario else next(iter(compiled.scenarios.values()))
    sets = sorted({key for strategy in target.definition.sets for key in strategy}
                  | {key for effect in target.effects if effect.when for key in effect.when.set_keys})
    if not sets:
        sets = sorted(mechanics.sets)[:2]
    rules = sampling_rules()
    artifacts = tuple(a for i, key in enumerate(sets) for j, slot in enumerate(SLOT_KEYS)
                      for a in sample_slot(slot, key, args.pieces, rules, seed=i * 5 + j).artifacts)
    inventory = Inventory(artifacts)
    groups = [tuple(a for a in artifacts if a.slot == slot
                    and a.main_stat in target.definition.mains.get(slot, (a.main_stat,)))
              for slot in SLOT_KEYS]
    if not all(groups):
        parser.error("sample omitted a required main stat; increase --pieces")
    rng = np.random.default_rng(42)
    loadouts = [tuple(group[int(rng.integers(len(group)))] for group in groups)
                for _ in range(args.rows)]
    builds = [assemble_build(loadout) for loadout in loadouts]
    additions = np.array([[build.stats.get(key, 0) for key in STAT_KEYS] for build in builds])
    counts = {key: np.array([build.set_counts.get(key, 0) for build in builds]) for key in sets}
    mains = {slot: np.array([build.main_stats[slot] for build in builds]) for slot in SLOT_KEYS}
    start = perf_counter()
    scalar = [target.evaluate(build.stats, build.set_counts, main_stats=build.main_stats) for build in builds]
    scalar_seconds = perf_counter() - start
    start = perf_counter()
    batch = evaluate_batch(target, additions, counts, main_stats=mains)
    batch_seconds = perf_counter() - start
    np.testing.assert_allclose(batch.scores, [value.score for value in scalar], rtol=1e-12)
    assert batch.feasible.tolist() == [value.feasible for value in scalar]
    results = {
        "scenario": target.definition.id, "artifacts": len(artifacts),
        "formula": {"rows": args.rows, "scalarSeconds": scalar_seconds,
                    "batchSeconds": batch_seconds, "includesBuildAssembly": False},
        "searches": [],
    }
    for seed in range(args.seeds):
        for name, limit in (("unscreened", None), ("screened", 12)):
            start = perf_counter()
            result = search_builds(inventory, target, max_evaluations=args.evaluations,
                                   top_k=5, seed=seed, candidate_limit=limit)
            results["searches"].append({
                "mode": name, "seed": seed, "seconds": perf_counter() - start,
                "evaluated": result.evaluated, "status": result.status,
                "bestScore": result.builds[0].evaluation.score if result.builds else None,
            })
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
