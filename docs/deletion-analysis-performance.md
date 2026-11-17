# Deletion analysis performance diagnosis

Initial measurements and subsequent findings recorded with Codex assistance on
2026-10-05 and 2026-10-06. These measurements diagnose the current encoded backend;
validated cache speedups and remaining limitations are distinguished below.

## Evidence and method

The user's Kuki-only 1,800-second-budget run completed as `pool_relative`.
The Kuki + Zhongli run with the same budget timed out before producing a
verified list. Reports have budgets and outcomes, but no phase timings; they
cannot identify precise runtime shares retrospectively.

Two fresh experiments used the prepared 2,377-artifact five-star inventory and
actual Kuki/Zhongli definitions:

- Current searches: 5,000 evaluations per scenario, seed 0. Unprofiled time was
  0.463 seconds for Kuki and 0.394 seconds for Zhongli. Separate cProfile runs
  of the same problems show evaluator/build-assembly costs.
- Pipeline trace: both scenarios, one upgrade trial, 128 percentile samples,
  2,000 evaluations per search, seed 0, and a 45-second budget. Wrapped calls
  record phase/search timing and repeated numerical candidate problems. These
  diagnostic wrappers add overhead. Both scopes timed out. This is not a
  measurement of the user's full 100,000-evaluation run.

Artifacts are stored locally in `.artifact-sort/profiles/`: `search.pstats`,
`search-summary.json`, and `pipeline-summary.json`.

## Measured costs

The pipeline ran for 45.39 seconds, excluding initial import/library compilation:

| Operation | Seconds |
| --- | ---: |
| Sample one completed inventory | 0.22 |
| Reference contexts, both scenarios | 5.14 |
| Quantile profiles, both scenarios | 0.64 |
| Both deletion selectors | 39.29 |

Build-search calls consumed 38.14 seconds, about 84% of pipeline runtime.
There were 380 calls and 473,646 evaluated builds. Of these, 193 calls repeated
an already-seen numerical problem with the same scenario, effective candidates,
seed, evaluation budget, top-k, and context-collection setting. These repeated
calls consumed 19.39 seconds and performed 242,823 evaluations. Deadlines were
not part of repeat classification: this is a reuse opportunity, not an assertion
that timeout-truncated results are interchangeable. None of these individual
searches returned `timed_out`; pipeline deadlines expired between searches.

The search cProfile experiment included 10,000 evaluated builds and took 2.48
seconds under profiling. Cumulative costs overlap and must not be summed:

| Operation | Cumulative seconds | Approximate total share |
| --- | ---: | ---: |
| Scenario evaluation | 1.89 | 76% |
| Build assembly | 0.33 | 13% |
| Candidate-stat validation, inside evaluation | 0.38 | 15% |
| Effect predicate evaluation, inside evaluation | 0.37 | 15% |
| Formula programs, inside evaluation | 0.25 | 10% |
| Feasibility ranking | 0.17 | 7% |

cProfile changes absolute timings. Fractions identify hotspots; the native
search timings provide an independent check of the workload's scale.

## Causes and optimizations

Each scenario has 94 targets before exclusions: one current plus three future
categories times all 31 real-slot subsets. Each target can have multiple upgrade
trials and reference contexts. Initial baselines, retained-inventory verification,
refinements, and the two independent coverage scopes multiply search work.

The current scalar evaluator computes all stats, validates canonical internal
inputs repeatedly, and tests 41 registered effects for each candidate build.
`assemble_build` re-sorts and checks five artifacts, reconstructs stat dictionaries,
looks up main stats, and counts sets. Those operations are useful at boundaries
but unnecessarily repetitive in the inner search loop.

Suggested order:

1. Instrument normal reports with phase times, search-call/evaluation counts,
   cache hits, and the target being evaluated on timeout. Keep diagnostics separate
   from numerical fingerprints where appropriate.
2. Share deterministic numerical searches across targets and scopes. Normalize
   away removals of artifacts that cannot enter that candidate problem. Cache
   exact results or completed budget-limited approximate results with their
   fidelity/status metadata; do not certify interrupted searches. Persistent
   keys need scenario/evaluator fingerprints, actual candidate stats and IDs,
   seed, budgets, top-k, and search options. Frozen future outcomes/reference
   profiles must be represented. A cache hit must not silently claim new search
   coverage. Keep bounded memory and compact results rather than caching every
   full build snapshot.
3. Cache preparation: completed outcomes, reference contexts, and quantile profiles.
   The current persistent cache holds successful whole reports, so a timeout does
   not save partial progress. Preparation cache keys must include sampling rules,
   seeds, populations, formula/context content, and preparation algorithm versions.
4. Precompute artifact stat vectors and fixed slot order. Use a trusted numerical
   evaluator inside validated search; retain the checked public evaluator and
   reconstruct full explanations for returned builds. Remove irrelevant effect
   and channel work using a verified dependency closure including constraints,
   conversions, caps, and activation predicates. Existing `relevant_stats` includes
   reads from unrelated registered effects and is not a minimal scoring kernel.
5. Compile exact simpler search cases. With the current fixed legal set
   compositions and no additional stat thresholds, Kuki's objective is monotone
   in EM and Zhongli's is monotone in HP. Zhongli's artifact contribution ranks as
   `base_hp * hp_percent + flat_hp`; Kuki's ranks as EM. Enumerate legal set/slot
   assignments and preserve identities/alternatives. This is a mathematical
   specialization of encoded formulas, not manually chosen character weights.
   General nonlinear/conditional cases retain the full evaluator.
6. Use formula-derived gradients for seed selection and proposal ordering in
   remaining general cases. Preserve exact evaluation of selected proposals and
   hard constraints. Pruning or shortening search is approximate unless supported
   by valid bounds; reevaluation alone does not recover missed candidates. Measure
   against exhaustive small cases and held-out scenarios. Do not reduce the 31
   subsets by default; reuse computations among them first.

Surviving baseline witnesses allow work to be skipped only with an explicit
contract: an exact baseline plus a surviving optimal build establishes the
retained optimum. An approximate baseline supplies a known attainable score,
not proof of the global optimum. Warm starts/pool reuse are useful but must not
mislabel that distinction. Equality of established/combined scenario sets permits
sharing one numerical result; distinct coverage still requires independent joint
selection, even when most search inputs overlap.

## Parallel execution and GPUs

Most current search work is Python code, so Python threads will not scale it
across cores under the usual GIL-enabled interpreter. The measured environment
is Python 3.14.7 with the GIL enabled. Python documents this limitation in its
[threading reference](https://docs.python.org/3/library/threading.html);
[NumPy documents](https://numpy.org/doc/stable/reference/thread_safety.html) that
many native operations release the GIL. Multiprocessing can run
independent scenarios, trial/context searches, or restarts. Initialize the library
and inventory in each worker: MappingProxyType-backed compiled objects are not
ordinary pickle-ready task payloads. Share compact arrays when useful, aggregate
results in a stable order, preserve per-artifact random tapes, and centralize or
coordinate persistent-cache writes. Process count and BLAS/solver threads must
avoid oversubscription. Parallelism increases throughput but does not remove
repeated work or certify approximate search.

Batching numeric candidate evaluations on CPU is the prerequisite for GPU work.
The arithmetic expression programs could eventually support array/tensor execution;
set activation can become masks. The present dictionary/dataclass/interpreter
pipeline cannot simply be moved to a GPU. Coordinate search has sequential steps,
small formulas have low arithmetic intensity, and MILP stays on CPU in the current
solver. GPU value must be measured after batching and reuse, including transfers,
compilation, launch costs, memory use, and numerical agreement at caps/constraints.

## Reproducing CPU profiles

From the repository root, an existing CLI command can be profiled without
changing numerical policy. This example limits search evaluations for diagnosis:

```bash
python -m cProfile -o deletion-profile.pstats -m artifact_sort library-delete \
  /tmp/artifact-sort-test-inventory.json scenarios/library.json \
  --mechanics scenarios/library.mechanics.json --allow-draft \
  --scenario kukishinobu-hyperbloom-paradise \
  --scenario zhongli-shield-double-hp \
  --free 2 --trials 1 --population 128 --max-evaluations 2000 \
  --time-limit 120 --cache '' --output deletion-profile-result.json

python -c "import pstats; pstats.Stats('deletion-profile.pstats').strip_dirs().sort_stats('cumulative').print_stats(30)"
```

Profiling consumes deadline budget and this run can time out. Do not compare its
recommendation quality to the larger-budget runs as though the work were equal.
No evidence yet supports a guaranteed speedup factor from any proposed change.


## Implemented caching follow-up, 2026-10-06

Within-run and persistent numerical caching is now implemented. See
[deletion-analysis-caching.md](deletion-analysis-caching.md) for the reuse contract,
comparison controls, tests, and benchmark results. The reduced-budget real
Kuki+Zhongli pipeline produced identical numerical reports in 78.57 seconds
uncached, 45.89 seconds cold with within-run reuse, and 6.54 seconds with
persistent intermediate reuse. Formula/search algorithms were unchanged.

## User runtime tests and startup profile, 2026-10-06

The user's timings at 1,000 search evaluations, one trial, 128 population samples,
Kuki+Zhongli, and a 300-second deadline were:

| Request | Wall seconds | Peak RSS MiB |
| --- | ---: | ---: |
| Cold cache, two deletions | 60.23 | 144.98 |
| Identical request | 9.55 | 88.62 |
| Existing cache, ten deletions | 26.09 | 150.42 |
| Identical ten-deletion request | 9.55 | 88.51 |

Cached originals and the latest exported report confirm both coverage lists
completed as pool-relative. The ten-deletion report measured zero loss, checked
two removal sets, and used one refinement. Its original intermediate counters
show 2,377 upgrade hits, 640 population hits, 192 persistent search hits, 627
memory search hits, and 85 recomputed searches. Thus reuse works across a changed
deletion request as well as whole-report repetition. The cold cache has higher
filesystem output and 65% CPU utilization; this is consistent with waiting on
cache writes but does not isolate storage waiting from scheduler contention.
No swapping or major page faults were recorded. GNU time CPU percentages are
aggregate CPU time divided by wall time, not utilization of every machine core.

A fresh whole-report-hit startup measurement in the workspace found:

| Stage | Seconds |
| --- | ---: |
| Imports | 0.450 |
| Inventory import | 0.032 |
| Library loading/validation | 7.473 |
| Mechanics loading | 0.001 |
| Library compilation | 0.006 |
| Report-cache lookup | 0.021 |

The profile is in `.artifact-sort/profiles/runtime-startup-profile.json`. Absolute
timings differ across executions. The observed warm-request floor is primarily
validation, not residual build search or compilation.

`library_from_data` initially validates the complete document, then wraps each
expanded scenario in another complete document and validates shared components,
channels, and formulas again. For 78 scenarios this repeats expensive shared
schema checks. Validate shared data once and validate only expanded scenario
nodes on subsequent passes, with equivalence/regression tests covering inheritance,
null removals, illegal fields, and invalid numerical inputs. This optimization
has been identified but is not implemented here. Batched SQLite transactions are
another candidate to measure for cold-cache write latency.

All four user commands used the same output filename, so the exported JSON
contains only the latest result. Distinct filenames preserve comparison evidence.
A subsequent ten-deletion `--no-reuse` run took 80.71 seconds and selected the
same ten artifacts as the cached request. An inventory-delta run remains useful.
These measurements establish cache/integration behavior, not broad recommendation
accuracy.

## Expanded real-inventory validation, 2026-10-06

Evidence is in the user's `deletion-tests/` and `deletion-tests-v2/` directories,
particularly `deletion-expanded.json`, `before-seed{0,1,2}.json`, and their
GNU time logs. These are local experiment outputs, not committed test fixtures.
Both rounds use the prepared 2,377-artifact inventory and draft encoded mechanics.
No game-accuracy claim follows from evaluating those same encodings.

### First expanded round: feasible-context discovery

Deletion selection included Kuki Hyperbloom (Paradise), Zhongli double-HP
shielding, Neuvillette Hunter charged damage, Xingqiu Emblem burst damage, and
Nahida Deepwood Spread damage. Parameters were ten deletions, one upgrade trial,
128 percentile samples, seed 0, 1,000 evaluations per search, and an overall
1,800-second budget.

The run stopped after 66.06 seconds with both lists blocked because
`xingqiu-burst-emblem: no qualifying reference context was found`. No removal
sets were checked. Stronger 100,000-evaluation current-build searches found
qualifying Xingqiu builds; the blocker therefore represented unresolved search,
not established inventory infeasibility. Increasing only the deadline would not
resolve an evaluation-budget limit. The four scenarios with profiles used only
inventory contexts; no hypothetical contexts were found at this budget.

Before/after searches on the original and old Kuki/Zhongli retained inventories
returned identical top-five builds for Neuvillette, Xingqiu, and Nahida, including
artifact IDs, scores, and effective stats. The earlier Kuki/Zhongli comparisons
also returned identical top-five builds. This establishes preservation of the
discovered current builds, not global optima or unfinished-artifact future value.
Of the ten old deletion candidates, nine were level-zero Long Night's Oath pieces;
the remaining candidate was `artifact_99`, a level-20 Hunter HP% goblet. Its
potential Neuvillette use motivated that held-out comparison.

The first held-out command omitted `--include-speculative`, so its output contained
only Albedo and Ayaka. Parameter variations such as higher-ER Xingqiu and no-Spread
Nahida require that flag in `library-builds`, even when explicitly requested by ID.
The second round corrected this command issue.

### Second expanded round: baseline evaluation exceeds its time share

`deletion-tests-v2/run.sh` increased the deletion search budget to 10,000
evaluations while retaining the same five included scenarios, seed, samples,
trial count, deletion count, and 1,800-second overall budget. The existing
`.artifact-sort/runtime-expanded.sqlite` cache was reused; this was not a cold run.

| Observation | Result |
| --- | --- |
| Wall time | 1,773.41 seconds (29 minutes 33 seconds) |
| User CPU time / CPU percentage | 1,709.35 seconds / 96% |
| Peak RSS | 227,052 KiB (about 222 MiB) |
| Reference preparation | Profiles generated for all five scenarios |
| Hypothetical contexts | Found for Zhongli, Neuvillette, Xingqiu, and Nahida; none for Kuki |
| Established list | `timed_out`, zero removal sets checked, no recommendations |
| Combined list | `timed_out`, one removal set attempted, no recommendations |

Reading the selector control flow alongside the report establishes that the
established pass timed out during original-inventory baseline evaluation. It
had not reached deletion-set evaluation. The combined pass completed baseline
evaluation, reported 119 proven nonpositive-baseline exclusions, and attempted
one removal set before timing out. The checked-set counter does not establish
that this attempted set finished evaluation. Both reports have no coverage gaps.
The exclusions implement the settled policy and did not block selection.

Time is allocated separately to the two selection passes from the remaining
overall budget. Thus the established timeout is a pass-deadline timeout, not
evidence that the entire 1,800 seconds was spent on that pass. Both scopes contain
the same five established scenarios in this experiment, but execute separate
selectors with shared numerical search caching.

Five scenarios create 470 targets before exclusions: five current targets plus
five times three future categories times 31 nonempty real-slot subsets. Each
future target may search several alternative reference contexts. The report
records 2,568 search misses, 2,566 completed search writes, two interrupted
searches, 1,524 persistent search hits, and 746 in-memory hits. Upgrade outcomes
were restored for all 2,377 artifacts. Populations recorded 1,596 persistent hits
and 21 new writes. These counters show useful reuse alongside thousands of
distinct search computations; they are not timings or per-phase cost shares.

The immediate bottleneck is baseline/future-context evaluation. These outputs
do not isolate formula evaluation, candidate assembly, search bookkeeping, or
SQLite costs, and do not establish the joint MILP solver as the dominant cost.
Timed-out whole reports are not stored as completed report-cache entries;
completed intermediate searches remain reusable.

### Search quality across three seeds

The second round searched nine scenarios on the original inventory with seeds
0, 1, and 2, 100,000 evaluations per scenario, and a 1,800-second command budget.
All scenario searches returned `approximate` after 100,000 evaluations. Whole
commands took 80.64, 79.30, and 82.78 seconds, respectively. The four held-out
scenarios were Albedo Husk, Ayaka freeze, higher-ER Xingqiu, and no-Spread Nahida.

Spread below is `(highest - lowest) / highest` across the three seeds. It measures
observed search instability, not approximation error relative to the unknown
global optimum.

| Scenario | Highest discovered score | Seed spread |
| --- | ---: | ---: |
| Kuki Hyperbloom Paradise | 26,293.593636 | 0% |
| Zhongli double-HP shielding | 30,269.150216 | 0% |
| Neuvillette Hunter | 17,738.422714 | 0% |
| Xingqiu Emblem | 3,073.235419 | 3.58% |
| Nahida Deepwood Spread | 20,453.434937 | 14.19% |
| Albedo Husk | 10,934.443453 | 6.97% |
| Ayaka freeze | 6,921.249899 | 0% |
| Xingqiu Emblem higher ER | 2,963.303580 | 0% |
| Nahida Deepwood without Spread | 9,887.772239 | 11.96% |

The earlier 16.54% Nahida figure was seed 1's improvement relative to seed 0,
using the lower score as denominator; it is consistent with the 14.19% spread
relative to the highest score here. Equal scores across seeds are encouraging
but do not prove optimality. The larger variations establish a concrete search
quality limitation for complex scenarios.

The script correctly stopped after failed deletion. No new retained inventories
or post-deletion validation reports were produced. These experiments therefore
do not validate expanded joint deletion quality or future-value preservation.

### Next work justified by these measurements

1. Record timings and evaluation counts by phase, scenario, category, and slot
   subset, preserving progress and the active target on timeout. Include
   baseline, proposal evaluation, solver, and refinement time separately.
2. Profile baseline evaluation to distinguish evaluator, assembly, search, and
   cache overhead before choosing an optimization.
3. Reduce repeated work without changing all 31 subsets, frozen contexts,
   coupled outcomes, or objective semantics. Cache counters alone do not prove
   which additional reuse will give a useful speedup.
4. Use these multi-seed build scores as search-quality regression evidence;
   validate proposals against stronger independent searches and small exhaustive
   cases. Do not use matching artifact IDs as the sole quality criterion.

No additional algorithmic optimization or independent future-upgrade simulation
was implemented as part of this findings update. Increasing sampling or budgets
further is not the recommended next diagnostic step.
