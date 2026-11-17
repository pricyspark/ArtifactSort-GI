# Encoded deletion caching

Implemented with Codex assistance, 2026-10-06. The search algorithm, trial tapes,
quality percentiles, all 31 slot subsets, and deletion objective are unchanged.

## What is reused

`artifact_sort.library_cache.AnalysisCache` shares numerical work between targets
and the two independently selected coverage lists. Its optional SQLite backing
uses the existing `ResultCache` file.

- **Completed build searches:** keys include the compiled scenario and evaluator,
  main-stat/level-cap data, the actual candidate artifacts in each slot after
  availability/main-stat filtering, seed, evaluation budget, top-k, and whether
  structural contexts were collected. Exact and fully completed budget-limited
  approximate searches retain their original status, evaluation count, discovered
  builds, and contexts. Timed-out searches are not reused or stored.
- **Individual upgrade outcomes:** keys include original identity and numerical
  state (including hidden lines), seed, trial, and sampling rules. Reads/writes
  are batched per inventory. Unchanged artifacts reuse their deterministic trial
  tapes across scans, even if other artifacts are added, removed, or upgraded.
  Current protection metadata is applied to restored outcomes.
- **Sampled whole-slot populations:** keys include slot, set, population size,
  seed, sampling rules, and main-stat data. This covers both hypothetical context
  populations and quantile-calibration populations. Populations are independent
  of ownership; their scores/quantiles are recomputed for the current context.
- **Whole reports:** successful reports still reuse the existing whole-report
  cache. The analysis version is now `encoded-deletion-3` so older reports are
  not mistaken for reports with the new diagnostics.

The memory search cache retains at most 512 results; population memory retains
128 entries, and memoized object fingerprints retain 8,192 objects. These are
memory-management limits, not numerical-quality parameters. SQLite retains
completed entries; deletion counts and protection policy remain selection inputs.

## Inventory changes

More than 90% unchanged artifacts does not imply 90% unchanged optimizations.
A new or improved artifact may change a joint optimum and inventory-derived
reference weights. Changed candidate domains require fresh search. A cached
winning build does not prove optimality over an expanded domain.

Nevertheless, unchanged per-artifact upgrade tapes are reused directly;
hypothetical populations/searches remain reusable when their inputs match;
and future slot-subset searches can be reused when their eligible real artifacts
and reference complements match. Changes to disallowed/unavailable pieces do
not invalidate a numerical search. Changes to locks, stars, or equipment do
not invalidate numerical scores, but protection is reevaluated during selection.

If inventory-derived reference contexts change, their gradients and quantiles
are recomputed. This implementation does not approximate the new joint search
or warm-start it with old rankings. Stable artifact IDs improve cross-scan reuse;
exports without IDs currently derive IDs from artifact content.

## Result preservation and deadlines

Cache keys retain complete numerical search inputs and budgets. Reuse does not
change signed weights, caps, feasibility, ties, or artifact identities. Equivalent
artifacts are not collapsed. The current algorithm still performs independent
joint selection for each coverage scope.

A wall-clock-limited uncached run may time out where cached computation finishes,
so statuses/recommendations can differ when the clock interrupts one run. This is
additional completed work, not a change to the numerical algorithm. Cache hits
never turn a truncated search into a certified completed search. Different
seeds/budgets/population sizes cannot use an incompatible search entry.

Partial reports are not cached as whole reports, but completed subwork survives
later timeouts. Individual search evaluation counts describe the stored search's
coverage, not new evaluations performed on a hit; use cache diagnostics to
identify reused work. Full per-build evaluation memoization is not implemented;
it may provide more reuse when a joint candidate domain changes, with additional
storage/prefetch and memory costs to measure.

## CLI and GUI comparison

Caching is enabled automatically in `library-delete` and GUI authored-library
cleanup. CLI defaults to `.artifact-sort/cache.sqlite`; GUI defaults to
`.artifact-sort/gui-cache.sqlite`. Use `--cache PATH` for an isolated test cache.
`--cache ''` disables persistent storage but retains within-run memory reuse.
`--no-reuse` disables both whole-report and intermediate reuse for a baseline.
In the GUI, uncheck **Reuse cached computations** under Computation settings.

Example: keep all analysis parameters identical for comparison runs. Do not
remove the normal search budget to make caching appear faster.

```bash
python -m artifact_sort library-delete \
  /tmp/artifact-sort-test-inventory.json scenarios/library.json \
  --mechanics scenarios/library.mechanics.json --allow-draft \
  --scenario kukishinobu-hyperbloom-paradise \
  --scenario zhongli-shield-double-hp --free 2 --trials 1 --population 128 \
  --time-limit 1800 --cache .artifact-sort/cache-comparison.sqlite \
  --no-reuse --output deletion-uncached.json
```

Run again without `--no-reuse`, using `deletion-cached.json` as output. Repeat for
whole-report reuse. Changing the deletion count forces a new report while letting
identical intermediate problems hit the cache. Increasing trials reuses old
artifact tapes and samples only additional trials.

The CLI/GUI JSON contains `cacheStatistics.reportHit` and
`cacheStatistics.intermediate`, with `memoryHits`, `persistentHits`, `misses`,
`writes`, and `interrupted` counters by kind. GUI results also display these
under **Cache reuse**. A whole-report hit reports no intermediate work for that
request, rather than displaying the original report's old hit counters.

## Measured verification

A real-inventory Kuki+Zhongli comparison used 2,377 artifacts, one upgrade trial,
128 percentile samples, seed 0, 1,000 evaluations per search, and a 300-second
budget. Whole-report caching was bypassed by invoking the pipeline directly:

| Run | Seconds | Outcome |
| --- | ---: | --- |
| Uncached | 78.57 | Both lists pool-relative |
| Cold cache, within-run reuse | 45.89 | Identical numerical report |
| New cache object, persistent reuse | 6.54 | Identical numerical report |

The cold run reused 681 searches in memory; the restarted run restored 223
searches, 2,377 upgrade outcomes, and 640 populations, plus within-run hits.
A separate test verifies persistence across a new Python process with a changed
hash seed. A 10,000-evaluation Kuki search took 0.89 seconds uncached, 0.96 seconds
cold, 0.003 seconds from memory, and 0.015 seconds from disk. Cold caching has
key/serialization overhead. These measurements are not a prediction for the
100,000-evaluation runs or evidence of game accuracy.

Local benchmark artifacts are in `.artifact-sort/profiles/cache-*-benchmark.json`.
Tests cover exact/approximate/context result equality, selector equality, formula
and candidate invalidation, protected metadata, corrupted entry misses, timeout
exclusion, changed deletion counts, sampling rule/tape invalidation, and a
19-of-20 unchanged-artifact reuse case. Full suite: 217 passed. Mypy passed for
six changed numerical modules. QuickJS checked script syntax, unique DOM IDs,
and cache-diagnostic rendering; no browser interaction test was run.

## Expanded-workload limitation, 2026-10-06

The five-scenario real-inventory follow-up at 10,000 evaluations per search timed
out despite 1,524 persistent search hits, 746 memory hits, and restoration of all
2,377 upgrade outcomes. It also performed 2,566 completed new search computations.
The established selector timed out during baseline evaluation; neither list
produced recommendations. Caching helps but does not remove the cost of distinct
future-context searches. See the [expanded validation findings](deletion-analysis-performance.md#expanded-real-inventory-validation-2026-10-06)
for parameters, stage diagnosis, three-seed search quality, and profiling priorities.
