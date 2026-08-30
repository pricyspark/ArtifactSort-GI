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

## GO

`artifact-sort import-go TEAM_EXPORT.json --output scenarios.json` preserves
the theorycraft build, optimization configuration, stat filters, custom
multi-targets, and target weights. Character formula paths are marked
`adapter_required`; the built-in evaluator will disable them instead of
silently approximating them.

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
