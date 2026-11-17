# Encoded-library deletion implementation

Implemented with Codex assistance. Updated: 2026-10-06.

## Implemented foundation

The new path uses the authored v4 library directly. It is separate from the
previous deletion command, with a joint selector and an end-to-end diagnostic
CLI/GUI path. Proven nonpositive baselines are excluded and reported; draft
sampling and game coverage remain unvalidated.

- `artifact_sort.inventory` imports GOOD v3 without rounding substats into roll
  coefficients, converts percentages once, and preserves hidden lines separately.
  Current main stats use actual level and rarity. Duplicate identities, illegal
  slot/main combinations, duplicate substats, and nonfinite values are rejected.
- `assemble_build` requires five distinct artifacts, one per slot, and computes
  aggregate additions, actual set counts, and main assignments. `evaluate_build`
  passes these through the compiled scenario evaluator.
- `search_builds` exactly enumerates small candidate products. Larger products
  use reproducible multi-start coordinate search with exact replacement scoring.
  Results distinguish exact, approximate, and timed-out searches. Only an exact
  search with no qualifying build establishes infeasibility within that selected
  scenario and inventory.
- `CompiledScenario.linearize` differentiates the complete active numerical
  calculation, including primary stat scaling, conversions, and additive or
  multiplicative channels. It returns an evaluation, weights in decimal units,
  and a flag for arithmetic branch boundaries. At tied min/max/clamp branches,
  it follows the first active branch; a unique derivative is not asserted.
  Set counts and conditions stay fixed. Constraint feasibility is evaluated
  separately, and a zero score derivative does not discard an ER requirement.
- `search_future_patterns` evaluates all 31 nonempty real-slot subsets against
  explicitly supplied completed real outcomes and frozen reference pools.
  Reference and real identities must be disjoint. Missing real slots cannot be
  filled by references. A global deadline marks unsearched patterns timed out.
  This is a search primitive, not a deletion selector.
- `artifact_sampling` generates whole-slot completed populations and ordinary
  five-star enhancement outcomes, preserving observed scanner values. Stable
  per-identity trial seeds couple outcomes across removal sets and input order.
  Known hidden lines are revealed; missing observed lines and unsupported
  rarities are explicit errors. Completed pieces receive no further rolls.
- `reference_profiles` scores every main using one shared weight vector and
  preserves its unconditional occurrence mass. `calibrate_slot` derives that
  vector from a legal surrounding build through the compiled evaluator. Tied
  score groups have percentile intervals and remain intact at the empirical
  inverse-CDF quantile. Explicit masses support correctly mixed stratified
  populations. Binomial/order-statistic confidence bounds apply only to IID
  unconditional draws; they report uncertainty and never widen the profile.
- `generate_reference_contexts` freezes contexts from both current-inventory
  builds and independently sampled hypothetical legal builds covering known
  sets. Their gradients come from the compiled evaluator. Each source has a
  separate search status; exact search of a hypothetical sample is still only
  approximate coverage of possible builds. Discovered main assignments,
  activated effects, and set-strategy regimes retain their best representatives,
  independently of the ordinary top-k score pool. This avoids a stat-distance
  threshold but does not guarantee coverage of numerical stat balances.
- `evaluate_future_outcomes` averages best qualifying scores across supplied
  upgrade trials separately for each of the 31 patterns. Proven failures count
  as zero. Unresolved trials withhold the point estimate and produce empirical
  qualification bounds. Approximate successful searches remain explicitly
  approximate. No qualifying baseline is an opportunity gap.
- `summarize_losses` implements worst relative loss and family-balanced average:
  contexts average within categories, current/ordinary/strong have equal shares
  within a family, and families have equal shares. Exceptional results cannot
  change primary objectives. Proven nonpositive baselines are excluded and
  reported by scenario and target. Remaining measurable categories receive equal
  shares within each family. Unknown evidence and apparent improvements after
  removal remain unresolved rather than supplying ratios.
- Complete v4 scenarios accept explicit `family` metadata. Parameter variants
  inherit it and cannot override it; structural scenarios declare their own
  grouping. Families represent character and role, with generic archetypes
  separately authored. Missing families remain visible as `null` in current-
  build CLI diagnostics; the loader does not guess grouping for older libraries.
- `Inventory.protected_ids` protects stars (`astralMark` in GOOD), equipped
  pieces, and explicit pins. Ordinary GOOD locks do not protect artifacts.
- `build_targets` assembles actual current targets and all 31 patterns for
  ordinary/strong/exceptional futures. Reference contexts remain separate
  alternatives; pieces from unrelated contexts cannot form a stronger mixed
  reference build. Baseline/removal comparisons never regenerate outcomes.
- `select_deletions` enumerates removal sets as the small-case oracle or uses
  a joint MILP with three lexicographic passes: worst primary loss, family
  average, then exceptional worst loss. Current qualification is a hard
  constraint. Retained-inventory searches feed missed alternatives back into
  the pool; an infeasible sparse pool triggers bounded alternative discovery
  rather than a false inventory-infeasibility claim. Search limits remain
  approximate and numerical worsening of an earlier objective is rejected.
- `library_analysis` prepares profiles and trials once, then independently runs
  established and combined selection. Shared CLI/GUI report caching includes
  inventory/library/sampling fingerprints, pins, seeds, and budgets. Transient
  blocked/timed-out results are not cached. Persistent intermediate-stage caches
  remain a possible performance improvement.

The pinned main-stat dataset is from
[gcsim's generated artifact tables](https://github.com/genshinsim/gcsim/blob/a3b24946babe26eb5b9e9101d0e0a55c20a2ea59/ui/packages/ui/src/data/artifact_main_gen.json).
Its commit and source URL are packaged with the data and the commit participates
in inventory fingerprints. Legal level caps are pinned separately from
[Genshin Optimizer's artifact constants](https://github.com/frzyc/genshin-optimizer/blob/7348b03b8314613823dc5fb475b995f962e4f469/libs/gi/consts/src/artifact.ts);
generated stat tables alone can include unreachable levels. Both pins participate
in inventory fingerprints. Percentages in that source are already ratios; only
GOOD substat values undergo percentage-point conversion. This table does not
constitute a validated character/mechanics release or a roll-probability model.

The packaged sampling manifest pins five-star roll increments from
[Genshin Optimizer's substat tables](https://github.com/frzyc/genshin-optimizer/blob/7348b03b8314613823dc5fb475b995f962e4f469/libs/gi/stats/Data/Artifacts/artifact_sub.json).
Main occurrence probabilities, substat weights, and ordinary enhancement
probabilities currently carry the previous farming module's assumptions;
**the manifest is explicitly draft**, with assumptions and a content fingerprint.
Ordinary drops and other acquisition sources may have different starting-line
probabilities. Special crafting or altered enhancement mechanics are outside
this model. This sampler is a development primitive, not validated coverage.

## Python usage

```python
from artifact_sort.inventory import load_inventory, assemble_build
from artifact_sort.library import load_library, load_mechanics
from artifact_sort.library_search import search_builds

inventory = load_inventory("inventory.json")
compiled = load_library("scenarios.json").compile(
    load_mechanics("mechanics.json"),
    allow_draft=True,  # Explicit development permission, not game validation.
)
scenario = compiled.select()[0]
result = search_builds(inventory, scenario, time_limit=180)
print(result.status, result.evaluated, result.proven_infeasible)
if result.builds:
    best = result.builds[0]
    local = scenario.linearize(
        best.build.stats,
        best.build.set_counts,
        main_stats=best.build.main_stats,
    )
    print(local.weights, local.at_boundary)
```

Future primitives can be exercised independently while the joint selector is
being implemented:

```python
from artifact_sort.artifact_sampling import sampling_rules, sample_slot, sample_completed_inventory
from artifact_sort.reference_contexts import generate_reference_contexts
from artifact_sort.reference_profiles import calibrate_slot
from artifact_sort.future_value import evaluate_future_outcomes

rules = sampling_rules()  # Currently draft; metadata is not a validation claim.
contexts = generate_reference_contexts(inventory, scenario, rules, time_limit=30)
population = sample_slot("goblet", "EmblemOfSeveredFate", 2000, rules, seed=7)
if contexts.contexts:
    ranked, local = calibrate_slot(population, scenario, contexts.contexts[0].inventory)
    band = ranked.band(.79, .81)  # Diagnostic band, not a calibrated release setting.

trials = tuple(sample_completed_inventory(inventory, rules, seed=7, trial=i) for i in range(8))
# Supply one frozen, completed complement pool shared by baseline/removal runs.
values = evaluate_future_outcomes(trials, scenario, complements, time_limit=30)
```

`complements` above must be supplied explicitly; this example does not generate
a calibrated full profile or claim production recommendations. Probabilities in
future results are empirical trial frequencies, not confidence intervals.

Synthetic identities generated for GOOD pieces lacking IDs are deterministic
within identical content groups; they cannot establish identity continuity across
scanner exports whose artifact state changes. Export-provided stable IDs are
preferred. Inventory fingerprints are independent of artifact ordering.

## Diagnostic CLI

```bash
artifact-sort library-builds inventory.json scenarios.json \
  --mechanics mechanics.json --allow-draft \
  --top-k 20 --max-evaluations 100000 --time-limit 180
```

The command reports actual current builds and selected-scenario coverage only.
It does not evaluate future opportunities or output a deletion list. Draft
definitions are rejected unless `--allow-draft` is provided. Add
`--include-speculative` to include both speculative collections, or repeat
`--scenario ID` to compile specific definitions. The deadline covers search
across selected scenarios; library/import setup is outside that search deadline.

Mechanics manifests have this shape:

```json
{
  "format": "artifact-sort-mechanics",
  "version": 1,
  "id": "explicit-library-mechanics-pin",
  "game_version": "explicit-release-version",
  "sets": ["BlizzardStrayer", "EmblemOfSeveredFate"],
  "characters": [],
  "validated": false,
  "components": {},
  "channels": {}
}
```

Set/character keys must include those used by the selected definitions and
candidate inventory. Components and channels follow the existing v4 encoding;
compilation checks the merged graph. `validated` is a publisher assertion, not
an automatic reference check. Do not construct an installed rules release by
guessing keys or setting this assertion true.

## Remaining work and decision questions

Remaining work includes authoring
family assignments for bundled coverage, independent game-reference/probability
checks, broader approximation and held-out-scenario measurements, performance
profiling, and refinement of context diversity and GUI explanations.

**Confirmed absence policy:** exclude targets with a proven nonpositive baseline
from both selectors and report their scenario IDs, category, baseline, and reason
in `excludedTargets`. Average remaining measurable categories equally within a
family, and remaining measurable families equally. Do not assign zero loss or
protect artifacts solely because an excluded target cannot qualify. Positive
current targets still require qualifying retained builds. If no primary target
remains, report this and produce no deletion list. Approximate failed searches
and unsupported mechanics remain unresolved coverage gaps. Cache version 2
invalidates results computed under the previous global-block policy.

## End-to-end diagnostic CLI and GUI

```bash
artifact-sort library-delete inventory.json scenarios.json \
  --mechanics mechanics.json --allow-draft --free 100 \
  --trials 16 --population 1000 --time-limit 180
```

The report contains both independently selected lists, per-target baselines and
losses, empirical qualification frequencies, quantile evidence with explicit
95% confidence levels, search statuses, and coverage gaps. `--pin` protects an
explicit artifact identity. The cache key includes all exposed computational
settings; changing them invalidates the report. These settings control numerical
effort, not the definition of ordinary/strong/exceptional quality.

In the GUI, choose authored scenario library in Cleanup, upload the numerical
library and mechanics manifest, and optionally its research sidecar. Draft
scenario inputs require the diagnostic checkbox. Both lists and gaps appear
separately, with JSON export. The previous analyzer remains selectable. No
artifacts are deleted automatically. Browser visual verification is still pending;
backend dispatch and JavaScript DOM wiring/rendering have been checked.

The first production-profile design uses the 80th/95th whole-slot quantiles for
ordinary/strong primary targets and the 99th percentile for exceptional
references. Exceptional losses serve only as a tie-breaker after both primary
objectives. All profiles use the same quantile definition and complete tie
groups, not an arbitrary narrow band. The current band API is a diagnostic primitive.
Quality bands, adaptive sampling, and extra configuration are potential later
extensions; see the tuning audit in the architecture record. No numerical
prototype default is a claim of adequate diversity or recommendation accuracy.

Lock policy is settled: ordinary GOOD locks alone do not protect artifacts.
The user locks all artifacts and uses stars for explicit protection. Preserve
the lock metadata, but do not introduce a weaker lock preference without a
separate decision. Starred protection is independent of ordinary locks.

The future-score policy is settled: modeled outcomes with no qualifying build
contribute zero usable performance to the expected score. Report qualification
probability separately as well. A failed outcome means no qualifying build
within the defined outcome/context, established by exact search or valid bounds.
Approximate search failure, unsupported mechanics, and missing coverage are
unknown results, not zero-performance outcomes. An entirely absent qualifying
baseline remains a coverage/opportunity gap rather than evidence for deletion.

This policy does not change the current-build diagnostic API.

**Performance follow-up:** all 31 slot patterns may multiply scenario, profile,
and outcome costs substantially. Measure per-pattern costs and reuse search work
before considering fewer patterns. A reduced-pattern mode is not implemented;
it would omit opportunities and cannot be advertised as equivalent analysis.

## Verification for this foundation

- Full repository suite: 195 tests passed, including 108 additional inventory,
  search, derivative, sampling, percentile, future-value, objective, context,
  deadline, CLI/cache, family-metadata, joint-selection, and GUI checks.
- Mypy passed for inventory, library search, formulas, library runtime,
  library loading, sampling, reference profiles, future value, deletion
  objectives, reference contexts, library deletion, and library analysis (12 modules)
  with `--follow-imports=silent`; this is not a whole-repository
  type-check claim. The three modules changed for the absence policy were
  rechecked successfully.
- Changed Python files were formatted with Black targeting Python 3.11.
- QuickJS parsed the GUI script and checked referenced DOM IDs, blocked-result
  rendering, and excluded-scenario reporting and HTML escaping. Node and a browser automation runtime were unavailable; this is not
  a browser layout/interaction test.
- Wheel construction and installed-package smoke checks passed, including
  packaged main-stat/sampling data, level caps, exact search, automatic weights,
  the end-to-end `library-delete` command, both lists, and packaged GUI controls.

These checks establish software behavior, not broad game-accuracy validation or
completed deletion analysis.


## Numerical cache implementation

Search, per-artifact upgrade, and population caching is implemented and connected
to CLI/GUI. The analysis version is `encoded-deletion-3`. See the
[caching record](deletion-analysis-caching.md) for cache keys, unchanged-inventory
reuse, timeout fidelity, comparison flags, bounded memory, and benchmark evidence.
The full suite now passes 217 tests; the six changed numerical cache/search/
analysis modules passed Mypy. The real-inventory reduced-budget benchmark verified
identical numerical reports with and without intermediate reuse.

## Expanded validation status, 2026-10-06

Real-inventory tests with five included roles resolved Xingqiu reference discovery
at 10,000 evaluations per search, but both deletion lists timed out within the
1,800-second overall budget. The established pass did not finish baseline
evaluation. Three-seed current-build searches also exposed substantial variation
for Nahida and smaller variation for Xingqiu and Albedo. Existing before/after
checks preserved discovered builds, but expanded joint deletion quality and
independent future-value validation remain unestablished. See the
[performance findings](deletion-analysis-performance.md#expanded-real-inventory-validation-2026-10-06)
for evidence and the next profiling work. These findings do not change the
settled deletion policies or reduce the 31 slot patterns.
