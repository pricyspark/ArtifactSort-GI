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
