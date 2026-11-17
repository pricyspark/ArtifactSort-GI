# Artifact Sort

Artifact Sort evaluates a Genshin Impact artifact inventory as a portfolio of
complete five-artifact builds. Deletion and upgrade decisions use nonlinear
scenario utility, build constraints, future-roll probabilities, and measured
policy regret instead of assigning every artifact a standalone weighted score.

## Installation

Python 3.11 or newer is required.

```sh
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .
```

Alternatively, create the pinned Conda environment:

```sh
conda env create -f environment.yml
conda activate artifact_sort
pip install -e . --no-deps
```

## Desktop-friendly app

Launch the local app after installation:

```sh
artifact-sort-gui
```

From a source checkout, `python -m artifact_sort.gui` works as well.

It opens in your browser, but runs entirely on your computer. Choose a GOOD v3
inventory export from Inventory Kamera, Irminsul, or Genshin Optimizer. You can
also select an inventory scan and a full GO database backup together; the app
recognizes their roles automatically and uses configured team targets to focus
the analysis. A GO database can be used by itself because it already includes
the inventory. If you use GO's copy-to-clipboard option, choose **Paste GO
database** in the app instead of saving it as a file.

The app provides an inventory overview, ranks promising upgrade candidates, and
creates searchable cleanup review lists that can be exported as CSV or JSON.
It never changes your source files or deletes artifacts. From a GO backup, the
app uses required sets, allowed main stats, stat minimums, and other build
preferences. It does not reproduce GO's exact character damage calculations,
so results are useful estimates and may rank close artifacts differently from
GO. Saved GO optimizer results are used to preserve their winning four-piece or
two-plus-two set strategies; rerun GO optimization before exporting when those
results are stale. No additional setup is required. Cleanup output remains
explicitly marked for review.

## Quick start

Start with a GOOD v3 artifact export and one or more scenario files:

```sh
artifact-sort delete scan.json \
  --scenarios scenarios/example.json \
  --free 100

artifact-sort upgrades scan.json \
  --scenarios scenarios/example.json

artifact-sort benchmark-policy scan.json \
  --scenarios scenarios/example.json \
  --free 100 \
  --trials 20 \
  --summary-only
```

Other commands:

```sh
artifact-sort import-go GO_DATABASE.json --output go-scenarios.json
artifact-sort import-akasha SNAPSHOT.json --output akasha-scenarios.json
artifact-sort farm scan.json --scenarios scenarios/example.json --increase 0.05
artifact-sort materials scan.json
```

Deletion output is deliberately marked `unvalidated` until the selected policy
has been benchmarked against relevant calibration and held-out scenarios.

## How it works

- Artifacts use an immutable NumPy structure-of-arrays representation with
  separate main-stat fields and exact integer substat roll coefficients.
- Scenarios describe utility formulas, set requirements, allowed main stats,
  stat thresholds, and current-versus-speculative priority.
- Build search Pareto-prunes compatible artifacts, preserves nonlinear
  threshold directions, and reevaluates complete candidate builds with the
  scenario evaluator.
- Exact-size deletion uses a binary MILP and then reruns build optimization to
  verify the retained inventory.
- Upgrade analysis enumerates exact roll outcomes and reports expected
  portfolio gain plus 0.1%, 1%, and 5% usefulness sensitivity.
- Layered SQLite caching reuses unchanged artifact outcomes and per-scenario
  build evaluations across inventory scans; command output reports cache hits.
- Policy benchmarks use shared hidden upgrade tapes, reproducible seeds,
  bootstrap confidence intervals, resumable per-trial cache checkpoints, and a
  clairvoyant upper bound.

See [the backend guide](docs/backend.md) for scenario formats, GO adapter
protocol, Akasha snapshot schema, simulation assumptions, and caching details.

## Development

```sh
conda env create -f environment_dev.yml
conda activate dev
pip install -e . --no-deps
pytest -q
```


The new offline scenario engine is available through `artifact_sort.library`.
It loads version-4 libraries and compiles encoded formulas with decimal-ratio
stats independently of the current analyzer. See the [library contract and
Python usage example](docs/scenario-library.md#using-the-standalone-loader-and-evaluator).
The new deletion prototype is connected through `library-delete` and the GUI's
authored-library cleanup mode. The previous analyzer remains available separately.
Draft library and sampling inputs produce diagnostics, not validated game coverage.

The `artifact-sort library-builds` diagnostic command imports GOOD inventory
without roll rounding and searches legal current builds using compiled library
formulas. The Python API also provides automatic local stat weights and all 31
real-slot context searches. See the [implementation notes](docs/deletion-analysis-implementation.md)
for usage, explicit mechanics manifests, limitations, and remaining work.

```sh
artifact-sort library-delete inventory.json scenarios.json \
  --mechanics mechanics.json --allow-draft --free 100
```

It prepares shared 80th/95th/99th whole-slot quantile references and coupled
upgrade trials, then selects independent established and combined lists. The
GUI accepts the library, mechanics, and optional research sidecar files and
exports the same diagnostic evidence. Targets with proven nonpositive baselines are excluded and reported by scenario.
Missing families, unsupported coverage, and unresolved searches still block affected analyses.


Encoded deletion now shares and persists completed build searches, individual
upgrade tapes, and sampled populations. Use `--no-reuse` to compare against an
uncached run, or the GUI's **Reuse cached computations** checkbox. Exported JSON
includes cache counters. See [caching details](docs/deletion-analysis-caching.md)
for inventory-change behavior, result-preservation limits, and measured timings.
