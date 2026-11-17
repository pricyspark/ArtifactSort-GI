# Portfolio backend

The `artifact_sort` package uses an immutable NumPy structure of arrays. Main
stats are separate fields and substats are exact integer roll coefficients
rather than overloaded sentinel values.

## Scenario files

JSON files contain a `scenarios` array. A minimal built-in scenario is:

```json
{
  "scenarios": [
    {
      "id": "example",
      "tier": "current",
      "objective": "damage",
      "scaling_stat": "atk",
      "damage_stat": "pyro_dmg_",
      "constraints": {"enerRech_": 180},
      "required_sets": {"EmblemOfSeveredFate": 4},
      "allowed_main_stats": {"sands": ["atk_", "enerRech_"]}
    }
  ]
}
```

`tier` is `current` or `speculative`. Current regret is minimized before
speculative regret. Artifact-stat finite differences are used only for Pareto
pruning and search order; every accepted build is evaluated with the nonlinear
utility.

Use `set_strategies` when more than one composition is acceptable. For example,
this allows either a four-piece set or a particular two-plus-two combination:

```json
"set_strategies": [
  {"required_sets": {"GoldenTroupe": 4}},
  {"required_sets": {"GoldenTroupe": 2, "GladiatorsFinale": 2}}
]
```

`required_sets` remains the concise form for one mandatory composition; it
cannot be combined with `set_strategies` in the same scenario.

## GO

Download the complete current database from GO's **Settings > Database >
Download**, then run:

```sh
artifact-sort import-go GO_DATABASE.json --output scenarios.json
```

The importer requires a complete GO database backup; individual team exports
and scanner-only GOOD files are rejected. It resolves each team through its
loadout, character configuration, optimization configuration, and active
equipped, real, or theorycraft build. Each configured team member's selected
optimization target becomes one current-account scenario. Members without an
optimization target are listed in the output's `skipped` array.

The resolved team context, representative build, stat filters, selected custom
multi-target, individual target weights, enemy settings, reactions, and bonus
stats are preserved. Real and equipped builds are converted into aggregate
theorycraft baselines for build screening while their exact weapon and artifact
records remain in the scenario metadata for the GO evaluator.

When an optimization configuration links to a saved `generatedBuildList`, the
importer resolves its GO-ranked artifact builds and records their distinct set
compositions as alternative `set_strategies`. These strategies already reflect
the set choices made by GO's exact calculation at the time that optimizer result
was generated. The first ranked build's artifact IDs are retained as reference
artifacts. If no generated result exists, an explicit theorycraft set definition
is used as the fallback. A merely equipped or saved real set is not treated as a
hard constraint.

Candidate search reserves full screening depth for every set named by a strategy
and accepts a build when it satisfies any strategy. This allows four-piece and
two-plus-two options to compete within one character target while still allowing
a global off-piece. Re-run optimization in GO before exporting if its saved
generated build lists are stale.

Character formula paths are marked `adapter_required`; the built-in evaluator
disables them rather than silently approximating them. The GUI explicitly uses
the imported set strategies as a local screening approximation. It does not
claim to recalculate the set effects themselves.

The optional `--go-adapter "node path/to/adapter.js"` command starts one pinned
local process. Communication is newline-delimited JSON:

- request `{"protocol":1,"type":"version"}` returns a `version` or
  `goVersion` string;
- request `{"protocol":1,"type":"evaluateBatch","goVersion":"...",
  "scenario":{...},"artifactStats":[{...}]}` returns
  `{"goVersion":"...","utilities":[...]}`.

The returned version is checked on every batch and included in persistent cache
keys. The adapter is optional because this repository does not vendor or pin a
GO checkout.

## Caching

Delete and upgrade analysis use a versioned SQLite cache at
`.artifact-sort/cache.sqlite` by default. It has five independent layers:

- `artifact-outcome` stores exact final-roll distributions by artifact roll
  state, independent of inventory membership and artifact ID.
- `build-evaluation` stores nonlinear utility by scenario, evaluator version,
  and aggregate five-artifact stat vector. Adding, removing, or upgrading an
  artifact therefore preserves evaluations for unchanged build combinations.
- `loadout-pool` stores optimizer results separately for each scenario and
  eligible inventory state. Adding or removing another scenario does not
  invalidate existing scenario pools.
- `upgrade-potential` stores the exact expected gain and usefulness probability
  for one artifact and scenario. Its key includes the baseline, outcome
  distribution, epsilon, and complete complement-build stat pool, so changing
  `--free` reuses it while any result-affecting input invalidates it.
- `delete` retains the whole-command result for exact reruns, avoiding another
  MILP solve. Upgrade analysis relies only on its reusable intermediate layers.

Candidate evaluation sets larger than 100,000 are not persisted, preventing an
exact-search edge case from creating millions of SQLite rows. Default bounded
beam searches remain cacheable. Command output includes hit, miss, and write
counts for each layer. Pass `--cache ''` to disable caching.

Cache keys include mechanics, algorithm, schema, evaluator/GO version, scenario
contents, artifact state, and all result-affecting CLI search parameters.

Deletion policy benchmarks add two resumable layers to the same database:

- `benchmark-deletion-decision` stores deterministic visible-policy decisions.
  A policy is evaluated once for an inventory/scenario/deletion configuration,
  rather than once for every hidden-roll trial.
- `benchmark-deletion-trial` checkpoints the complete result for each spawned
  seed. Repeating an interrupted command reuses completed trials while running
  only the missing seeds.

Randomized hidden inventory states remain in memory and are not persisted as
one-off optimizer entries. This keeps the cache useful without filling it with
states that are unlikely to occur again.

## Akasha

Akasha access is offline by default. Version-1 JSON snapshots contain `builds`
with `leaderboard_id`, `category`, `conditions`, `score`, `artifacts`,
`timestamp`, `source_url`, and optional aggregate `stats`. CSV accepts the same
column names. Leaderboards remain separately labeled. Aggregate stats become
representative nonlinear screening points and recorded scores are available for
rank-correlation validation; they are never averaged into universal weights.

## Policy benchmarks

Deletion and upgrade simulations draw a hidden upgrade tape once per trial and
give every policy the same tape and scenario sequence. Policy code only sees
the visible batch. Reports include seeds and bootstrap confidence intervals.
The deletion harness includes random, crit value, conservative hand-written
target-family, local-linear greedy, portfolio policies at 0.1%, 1%, and 5%
unfinished-piece floors, an optional recorded external-policy ordering, and a
clairvoyant upper bound. Pass a JSON array of artifact IDs through
`--recorded-order` to replay any previously recorded policy.
Benchmark progress is written to stderr after policy preparation and each
trial; `--no-progress` disables it. The default cache is
`.artifact-sort/cache.sqlite`, `--cache ''` disables it, and `--curve-points`
controls the number of deletion counts sampled for each regret curve. Changing
the trial count preserves checkpoints for the seeds shared with the earlier
run.

Benchmark JSON starts with a compact `summary` containing an observed-risk
ranking, percentage regrets and confidence intervals, punished-trial counts,
near-best deletion rates, and resource outcomes. The complete seeds and
per-trial records follow under `result` for auditing. Pass `--summary-only` to
omit those details and produce a short report; this changes only presentation
and still uses the same cached benchmark trials.
The Python API also exposes `load_historical_scans` and
`replay_historical_deletions`; meaningful cross-scan punishment counts require
scanner-supplied stable artifact IDs.

The farming command reoptimizes after acquisition batches and reports resin
tails. Domain rejects, rather than duplicate retained pieces, feed the
strongbox balance. `--define SET SLOT MAIN SUB1 SUB2` adds a chosen-main/two-
substat definition to each trial. `--reshape ARTIFACT_ID ATTEMPTS` resamples a
piece only when its exact initial rolls are present; uncertain scanner history
is rejected instead of filled with guessed averages. Farming currently
finalizes every retained synthetic candidate, so its result is an optimistic
artifact-outcome bound; use the separate upgrade benchmark for adaptive
EXP/Mora costs. Resin equivalents are omitted unless a conversion is explicitly
supplied. Missing material balances produce break-even curves instead of a
categorical recommendation.

Deletion output is an analysis result, not a validated recommendation, until a
benchmark using the relevant calibration and held-out scenarios establishes
the acceptance criteria for that account.
