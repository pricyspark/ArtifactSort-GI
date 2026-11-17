# Encoded scenario library (draft v4)

The [roster research batch and coverage report](scenario-library-coverage.md)
adds `scenarios/library.json`, its matching research sidecar and executable draft
mechanics manifest. It inventories the pinned roster and sets, supplies researched
event definitions and sensitivity cases, and explicitly records incomplete
coverage. All definitions remain drafts; see the report before using the batch.

The authored library contains numerical scenario definitions. A separate research
file contains sources, assumptions, and review records. The loader expands definitions into immutable scenarios; the compiler builds
deterministic numerical programs before analysis. The encoded deletion path
has persistent result caching. Codex assisted with this format, its schema,
examples, and usage documentation.

This replaces the earlier fixed-formula and percentage-point proposals.
`library-builds`, `library-delete`, and the GUI authored-library cleanup mode
load this format. Legacy deletion and upgrade commands retain their previous
pipeline. The bundled examples are illustrative, not researched recommendations
or a usable mechanics database.

## Files and lists

- [library.example.json](../scenarios/library.example.json): compact numerical definitions.
- [library.example.research.json](../scenarios/library.example.research.json): supporting evidence and review notes, indexed by scenario ID.
- [scenario-library.schema.json](../scenarios/scenario-library.schema.json): machine-readable validation rules.
  The packaged copy in `artifact_sort/scenario-library.schema.json` must stay
  identical; an automated test checks this so installed distributions work too.

The library header contains `format`, `version`, `revision`, and `mechanics`.
`version` describes the file structure; `revision` identifies this content
release; `mechanics` pins an immutable mechanics release with game/evaluator
versions in its own manifest. None of these needs repeating in every scenario.

Three independent lists are retained:

| List | Contents |
| --- | --- |
| `established` | Complete definitions of documented character uses or established archetypes. |
| `parameter_variations` | Parent references plus numerical or condition changes for speculative sensitivity cases. |
| `structural_variations` | Complete definitions of speculative roles, scaling mechanisms, or set interactions. |

Documented alternatives belong in `established`, even when their parameters
vary. Collection membership is not a probability, ownership filter, or solver
priority. Analysis runs independently against established coverage and against
established plus both speculative lists, using the same inventory and deletion
count. Retention budgets and tradeoffs belong to analysis policy.

## A numerical scenario

```json
{
  "id": "atk-cryo-freeze",
  "characters": [],
  "scoring_formula": "atk-cryo-crit",
  "base": {"atk": 800, "critRate_": 0.05, "critDMG_": 0.5, "enerRech_": 1.0},
  "buffs": {"atk_": 0.2},
  "minimums": {"enerRech_": 1.4},
  "sets": [{"BlizzardStrayer": 4}],
  "conditions": {"enemy_state": "frozen"},
  "mains": {
    "sands": ["atk_", "enerRech_"],
    "goblet": ["cryo_dmg_"],
    "circlet": ["critRate_", "critDMG_"]
  }
}
```

These numbers demonstrate the format only. Required fields are `id`, `scoring_formula`,
`base`, and `sets`. Other fields can be omitted when empty.

| Field | Meaning |
| --- | --- |
| `characters` | Optional list of applicable GOOD character keys. An empty/omitted list denotes an archetype with no assigned characters. |
| `scoring_formula` | Reference to a shared scoring formula in the library's `scoring_formulas` table. |
| `base` | Character/weapon base HP, ATK, or DEF, plus intrinsic starting stats such as ER and crit. |
| `buffs` | All fixed non-artifact additions, including weapon secondary stats, ascension bonuses, and assumed team buffs. Flat HP/ATK/DEF additions go here, not in `base`. |
| `minimums`, `maximums` | Hard constraints on effective total stats after all effects, before utility-only caps such as crit-rate clipping. |
| `sets` | OR list of acceptable minimum set compositions; each map is an AND requirement. `[{}]` explicitly allows any composition. |
| `conditions` | Formula/mechanics inputs such as enemy state, activation flags, stack counts, or uptime. |
| `parameters` | Dimensionless numeric formula inputs such as counts and coefficient magnitudes; units are supplied by expressions. |
| `effects` | Optional IDs of character/weapon contribution components; registration changes are structural. |
| `mains` | Allowed main-stat keys per slot; omitted slots are unrestricted within valid game main stats. |

Use GOOD stat/slot/set keys, but express all percentages as decimal ratios:
46.6% damage bonus is `0.466`, 5% crit rate is `0.05`, 150% crit damage is `1.5`,
and 140% ER is `1.4`. Baseline 100% ER is `1.0`. Percent stats and bonuses have
unit `scalar`. Uptime uses fractions from 0 to 1 where supported. Do not silently
average intervals; represent sampled values as explicit variants. Every numerical
parameter must be finite.

Normalize percentage-point source data once at the earliest input boundary:
GOOD/scanner imports, external stat tables, and research extraction must divide
percentage-point values by 100 before constructing internal stats or authored
scenarios. Leave already normalized ratios, flat stats, and counts unchanged.
Use the source's declared units; never infer units from magnitude, since ER and
crit damage legitimately exceed `1.0`. Apply this convention to base stats,
buffs, thresholds, artifact stats, roll increments, effect outputs, formula
inputs, and numerical research checks. Formula expressions need no percentage
conversion nodes. Human source descriptions can retain `%` notation; formatting
for display happens only at the output boundary.

Version 4 changes the unit contract. Reject or explicitly migrate older library
and cache data; do not silently load percentage-point values as ratios. The
legacy runtime still uses percentage points and is not integrated with this
library. Its import conversion and dependent calculations must be migrated
together before sharing stats with the new evaluator.

Multiple characters can reference one scenario when its effective numerical
assumptions represent them adequately. Matching scaling alone is insufficient:
base stats, buffs, ER, reactions, and attack contributions can change rankings.
Use variants or separate definitions for materially different cases. Character
labels do not change evaluation, multiply scenario priority, or create duplicate
solver targets. They are not a claim of exact character simulation.

## Encoded formulas and reusable components

`scoring_formulas` now contains an output unit and an expression, rather than a
fixed formula name. `components` contains reusable expressions, including effects.
An expression is data with defined mathematical semantics. The standalone
compiler evaluates it without interpreting research prose or calling an LLM.

```json
"components": {
  "hp-added-damage": {
    "stage": "bonus",
    "unit": "damage",
    "expression": {
      "op": "multiply",
      "args": [
        {"stat": "hp", "stage": "effective"},
        {"parameter": "hp_flat_coefficient"},
        {"value": 1, "unit": "damage/hp"}
      ]
    }
  }
}
```

A scoring expression can add `{"ref": "hp-added-damage"}` to talent-scaled
base damage before multiplying by applicable bonus and crit factors. The
coefficient is a scenario's `parameters` entry; it is not extracted from prose
at analysis time. The expanded example demonstrates this composition using
explicitly assumed numbers, without claiming a real character kit.

### Expression vocabulary

| Encoding | Meaning |
| --- | --- |
| `12` | Dimensionless numerical constant. |
| `{"value": 20000, "unit": "hp"}` | Constant with an explicit unit; percentage caps use scalar ratios such as `0.75`. |
| `{"stat": "enerRech_", "stage": "effective"}` | Named stat at a specified calculation stage. |
| `{"ref": "average-crit"}` | Named pure component; no inheritance or arbitrary code. |
| `{"parameter": "hit_count"}` | Numerical scenario input from `parameters`; absence is an error. |
| `{"condition": "husk_stacks"}` | Numeric value from `conditions`; strings/booleans are only for activation predicates. |
| `{"channel": "burst_dmg_bonus"}` | Aggregated contributions to a declared channel. |
| `{"op": "multiply", "args": [expression, expression]}` | Arithmetic operation over expressions. |

`add`, `multiply`, `min`, and `max` take at least two arguments. `subtract` and
`divide` take exactly two, ordered arguments. `clamp` takes value, lower, and
upper. Numeric inputs/results must be finite. A zero denominator, reversed
clamp bounds, or missing reference is an evaluation error; there is no guessed
fallback. A stat required by an expression is explicit in scenario inputs or
provided by the pinned mechanics implementation. Omitted additive buffs and
artifact entries are zero, not hidden character defaults.

Units use the atoms `scalar`, `atk`, `hp`, `def`, `em`,
`damage`, `healing`, and `shield`, with optional products/ratios such as
`damage/hp`. The compiler must normalize dimensions: HP times damage/HP is
damage. Percentage ratios are dimensionless scalars.
Addition, subtraction, min/max, and clamp require compatible units. Plain
numbers are scalar; use a typed constant when a cap or offset has units.

There is no implicit HP-to-damage or outgoing-to-incoming-healing conversion. Explicit coefficients supply the units for talent
scaling and cross-stat additions. Proxy scoring formulas can output ATK or HP
units, but must remain labeled as proxies in research; those units are not
absolute damage. Never compare unnormalized scores across scenarios.

### Calculation stages and contributions

Components declare `stage`, `unit`, and `expression`. Pure components are named
intermediate values referenced by formulas. Effects additionally declare
`contributes_to`; only registered effects are applied, never every component
in the table. Optional `when` defines activation. A conditional component must
be an effect; formulas reference pure components and channels, not effect IDs.

| Stage | Inputs and timing |
| --- | --- |
| `static` | Reads fixed `base` stats, parameters, and conditions. Adds fixed contributions before raw stats are formed. |
| `conversion` | Reads `base` or `raw` stats; contributes stat conversions without reading their own final results. |
| `bonus` | Reads `base`, `raw`, or `effective` stats; produces attack bonuses, additions, and multipliers. |
| `score` | Reads earlier results and the effective stats to assemble final utility. |

`base` is the supplied intrinsic vector. After static contributions, `raw`
contains pre-conversion totals in normalized units. HP/ATK/DEF already include
percentage and flat additions: `raw.atk = base.atk * (1 + raw.atk_) + flat_atk`.
Other stats sum base, buffs, artifact additions, and static contributions.
Every conversion reads this same raw snapshot. Then `effective` recomputes
HP/ATK/DEF with conversion additions included: percentage conversions multiply
explicit base stats, while flat conversions add after scaling. For example,
`effective.atk = base.atk * (1 + raw.atk_ + converted_atk_percent) + flat_atk + converted_atk`.
Other stats add their conversion contributions to raw totals. No conversion
silently reads another conversion's output. More complicated ordered chains
or snapshot rules need a declared extension or a future stage contract.

`contributes_to` uses `stats.KEY` for a stat addition or `channels.NAME` for a
formula contribution. Static/conversion effects may target stats only; bonus
effects may target channels only. Pure score components cannot contribute.
Target units must match. `channels` declares each channel's unit and aggregation:
`add` has identity zero, `multiply` has identity one. False effects are excluded
rather than assigned zero, preserving multiplier semantics. Stat contributions
add. Flat damage, outgoing healing, received healing, and separate multipliers
must use distinct channels; do not collapse unlike bonuses.

The library-wide `effects` list registers candidate set effects; scenario-local
`effects` can register character/weapon effects. Components from the pinned
mechanics release may also be referenced. IDs must resolve, and each effect is
applied once to actual candidate set counts. Conflicting local/pinned definitions
are errors. Set constraints do not substitute for effect activation, and effect
values must not also be copied into `buffs`.

### Activation example

Both example libraries encode Emblem's ER contribution and capped Burst bonus:

```json
{
  "stage": "bonus",
  "unit": "scalar",
  "contributes_to": "channels.burst_dmg_bonus",
  "when": {
    "all": [
      {"set": "EmblemOfSeveredFate", "pieces": 4},
      {"condition": "damage_type", "equals": "burst"}
    ]
  },
  "expression": {
    "op": "min",
    "args": [
      {"op": "multiply", "args": [{"stat": "enerRech_", "stage": "effective"}, 0.25]},
      0.75
    ]
  }
}
```

The effect follows [KQM's set reference](https://library.keqingmains.com/equipment/artifacts#emblem-of-severed-fate).
Other set effects in the pilot remain coverage gaps; this example is not a
complete set database. The arithmetic evaluator executes the encoded effects,
but does not supply the missing set rules automatically.

Predicates support exact condition equality (numbers normalize to floats;
booleans and strings remain distinct), minimum set-piece
counts, `all`, `any`, and `not`. Lists are evaluated left to right with short
circuiting. Missing conditions in a reached predicate are errors. A set-count
predicate for a known set with no equipped pieces is false. Numerical changes
based on conditions can use numeric condition references; branching requiring
new mathematics must be explicit components or supported extensions.

### Extensions and compilation

An extension expression uses `{"op": "extension", "name": "...",
"version": "...", "args": [...]}`. This is a reserved wire shape, not automatic
support. A compiler must resolve a pinned installed implementation specifying
argument units/arity, result unit, dependencies, and deterministic semantics.
Absent or mismatched implementations are errors. Arbitrary Python, executable
strings, and prose are never formula encodings.

The compiler derives dependencies from expression references, checks units and
stage ordering, rejects cycles and invalid effect references, and binds fixed
scenario inputs. It validates the merged local/pinned definition graph and
compiles each selected scenario and registered effect. Shared references are
computed once within each program. Compiled programs currently live in memory;
persisted cache integration remains future work. Condition
and set-count dependencies also affect candidate search and cache identity.
Algebraic constant folding is optional; it must preserve caps and conditional
behavior. Timing, reactions, and teammate aggregation that are not adequately
specified remain unsupported even if their arithmetic can be expressed.

JSON Schema checks expression shape and operation arity. It cannot establish
unit consistency, dependency correctness, source accuracy, or executable
support; those are explicit compiler and release-validation requirements.

## Compact parameter variations

```json
{
  "id": "atk-cryo-freeze-higher-er",
  "extends": "atk-cryo-freeze",
  "changes": {"minimums": {"enerRech_": 1.8}}
}
```

`extends` resolves by ID across established scenarios and parameter variants.
The compiler recursively copies the parent, replaces its ID with the variant's
ID, and applies `changes`: objects merge by key; arrays and scalar values replace;
null removes a key. For example, `{"buffs": {"atk_": null}}` removes that fixed
buff. Missing fields inherit. Cycles and unresolved parents are errors.

Only `base`, `buffs`, `minimums`, `maximums`, `conditions`, `parameters`, and `mains` can change
in parameter variants. A different formula, scaling mechanism, or set strategy
requires a complete structural entry. Parameter variants inherit character
labels; characters with different parameter needs can share an established
entry only when that entry's assumptions are representative.

For deletion aggregation, each complete scenario can declare an explicit
`family` string, for example `"ExampleCharacter/on-field-damage"`. Families
represent **one character and role**: weapon, set, and parameter variants share
that family's influence; different roles receive separate families. Generic
archetypes use their own identifiers, such as `"archetype/pure-hp-support"`.
Parameter variants inherit `family` and cannot change it. Structural scenarios
declare the same family only when they preserve the same character and role.
Family identifiers are author-provided metadata, not parsed name conventions;
the runtime cannot verify the semantic role label. Existing library entries
without a family remain valid for build diagnostics, but this does not supply
the metadata required for family-balanced deletion. A shared numerical template
covering several character labels does not imply those characters form one
character-and-role family; deletion coverage will need explicit per-character
entries or explicit generic-archetype coverage.

Compilation validates the expanded definition and stores complete entries
without parent links. Missing inputs must never turn into defaults because a
patch removed a required field. This gives authors concise files and analysis
an unambiguous cached representation.

## Research and publication

The sidecar contains `library_revision`, a shared `sources` table, and a
`scenarios` table indexed by ID. Each record has `status` (`draft`, `reviewed`,
or `validated`), source IDs, notes explaining assumptions, and validation
checks. Detailed claim citations can be added there when useful; numerical
entries do not require a wrapper or citation for every field. The sidecar also has `components` and `scoring_formulas` records indexed by ID.
Each pairs a plain-language description with the numerical encoding, source IDs,
assumptions, and validation checks. Descriptions explain the calculation; they
never execute it. Mechanics evidence belongs alongside its definitions.

Review is a publication gate, not a score multiplier. Missing research records
are unreviewed. An executable release must validate all selected definitions,
resolve mechanics support, and retain its research records. Draft examples
cannot supply numerical evidence for deletion safety. Validation of JSON shape
alone does not establish the accuracy of the formula or numerical inputs.

Source disagreements should become explicit alternative scenarios where
appropriate. Future archetypes must state their assumptions without inventing
named unreleased characters. Unsupported uses remain visible coverage gaps,
not silently discarded scenarios.

The loader/compiler checks unique IDs, formula and parent references, game keys,
set totals (at most five), threshold ordering, required intrinsic/base stats,
units, stage order, and dependencies. Numerical parameters and conditions must
be present at compilation. Activation predicates preserve runtime short
circuiting; a missing condition is an error if evaluation reaches it.
The compiler produces a fingerprint of expanded numerical content, selected
IDs, installed mechanics definitions, and evaluator version. Analysis cache keys
must additionally include inventory and analysis settings; a revision string alone is insufficient. Live research
is never required during inventory analysis.

## Research pilot and builder prompt

[library.pilot.json](../scenarios/library.pilot.json) adds five established-role
drafts, three parameter variations, and two structural variations across
Golden Troupe, Emblem, Maiden, Ocean-Hued Clam, Tenacity, Vourukasha, and Husk.
Its [research records](../scenarios/library.pilot.research.json) distinguish
sourced stats and recommendations from assumptions and formula limitations and draft encoded components.
All entries are drafts and the mechanics reference is explicitly unimplemented.
The pilot tests authoring, not the accuracy of artifact deletion decisions.

The standalone [builder prompt](scenario-library-agent-prompt.md) describes the
goal, research procedure, numerical conventions, classification rules,
validation gates, and expected outputs for agents without conversation context.
One lesson from the pilot is that numerical inputs do not guarantee adequate
coverage: incoming healing, shield strength, reaction scaling, and teammate
buffs can require components beyond the previous generic proxies.
Record these gaps rather than making a scenario appear executable.


## Running deletion analysis

Install the checkout with `python -m pip install -e .` in your project environment.
You need a GOOD v3 inventory, an authored v4 library with explicit character/role
families, and a numerical mechanics manifest matching the library's `mechanics`
ID. Place a research sidecar beside `library.json` as `library.research.json` for
automatic CLI loading. The bundled example and pilot have placeholder mechanics
IDs and lack deletion families; they are not ready to run unchanged.

First inspect current builds, then request a small deletion list:

```sh
python -m artifact_sort library-builds inventory.json library.json \
  --mechanics mechanics.json --allow-draft --top-k 5 --output builds.json

python -m artifact_sort library-delete inventory.json library.json \
  --mechanics mechanics.json --allow-draft --free 1 \
  --trials 4 --population 256 --time-limit 120 --seed 0 \
  --output deletion.json
```

Small trial/population counts are for a first diagnostic run; they do not certify
quantile precision or search quality. Defaults are 16 trials, 1,000 population
samples, 100,000 evaluations per build search, and 180 seconds overall. Use
repeated `--scenario ID` arguments to limit coverage and `--pin ARTIFACT_ID` for
explicit protection. Stars and equipped artifacts are protected; locks alone
are not. Run the identical command again to exercise persistent result caching.
Only successful exact/pool-relative reports are cached.

The JSON contains independent `selections.established` and `selections.combined`
lists. Inspect `status`, `deletedArtifactIds`, losses, `gaps`, and `excludedTargets`.
`exact` refers to the modeled search, not game accuracy; `pool_relative` describes
the discovered build pool. Unresolved/blocked reports need their gaps addressed.
No artifacts or source exports are modified. Proven nonpositive baselines are
excluded and reported. Unsupported upgrade states can still block analysis;
the sampler currently supports ordinary five-star enhancement.

For the GUI, run `python -m artifact_sort.gui`, import the inventory, open Cleanup,
choose the authored-library mode, and upload the library, mechanics, and optional
sidecar. Enable draft diagnostics when using draft definitions, choose a deletion
count, and run analysis. The GUI presents both lists and exports the same JSON.

To test the implementation without preparing researched coverage:

```sh
python -m pytest -q tests/test_deletion_objective.py tests/test_inventory_search.py
python -m pytest -q tests/test_inventory_search.py::test_end_to_end_encoded_deletion_cli_and_persistent_cache
```

The end-to-end test creates synthetic inventory, library, and mechanics files,
runs both deletion scopes, and verifies cache reuse. These are software tests.

## Running the offline builder

There is no dedicated builder executable yet. Give an agent with repository and
web access [the standalone builder prompt](scenario-library-agent-prompt.md),
plus your requested character/role coverage and output paths. Request the library,
matching research sidecar, executable mechanics manifest, coverage report, and
validation results. Begin with a small researched batch. Require explicit families,
pinned mechanics, and honest draft status; parser tests do not establish game
accuracy. Research can use the internet; loading and deletion evaluation run
locally from the authored files.

## Using the standalone loader and evaluator

The Python API lives in `artifact_sort.library`. Loading performs schema checks,
variant expansion, numerical validation, and research-sidecar checks. Compilation
resolves the explicitly supplied mechanics release and validates units, references,
and stage dependencies. It does not reuse the legacy evaluator or deletion solver.

```python
from artifact_sort.library import Mechanics, load_library

library = load_library("scenarios/library.example.json")
# Development fixture only: this is not a validated game-rules release.
mechanics = Mechanics(
    id="example-unimplemented",
    game_version="development-example",
    sets=frozenset({"BlizzardStrayer", "EmblemOfSeveredFate"}),
)
compiled = library.compile(
    mechanics, allow_draft=True, scenario_ids=["atk-cryo-freeze"]
)
scenario = compiled.scenarios["atk-cryo-freeze"]
result = scenario.evaluate(
    {"atk_": 0.466, "atk": 311, "cryo_dmg_": 0.466,
     "critRate_": 0.311, "critDMG_": 0.622, "enerRech_": 0.4},
    {"BlizzardStrayer": 4},
    main_stats={"sands": "atk_", "goblet": "cryo_dmg_", "circlet": "critRate_"},
)
print(result.score, result.feasible, result.violations)
```

`artifact_stats` contains aggregate artifact additions, not character totals.
All percentages are already decimal ratios. `normalize_good_stats(mapping)` is
an explicit boundary adapter for GOOD percentage-point stat mappings. Never
pass legacy `ArtifactBatch.final_stats()` values directly to the new evaluator,
and never normalize a ratio mapping a second time. A separate lossless inventory
boundary and legal-build search are now available; see
[the implementation notes](deletion-analysis-implementation.md). The legacy
deletion/upgrade commands still use their previous pipeline.

`Evaluation` exposes score, effective stats, channels, and constraint violations.
Evaluation still returns a score when ER, set composition, or main-stat restrictions
are unmet. Stat threshold comparisons tolerate floating-point roundoff with
relative and absolute tolerances of `1e-12`. Missing main assignments for restricted slots are violations. An
arithmetic error raises `EvaluationError` rather than returning a fallback score.
`feasible` means the supplied aggregates meet this scenario's constraints; it does
not verify five distinct artifact identities, equipment legality, or simultaneous
team assignments. This permits testing incomplete compositions without defining
the future deletion policy for them.

Intrinsic HP/ATK/DEF and ER/crit baselines must be explicit when referenced;
there are no hidden character defaults. Omitted additive stats are zero. A primary
stat absent from `base` is not included in effective totals and cannot be referenced
or constrained. Every registered effect must have the numerical inputs it needs,
even when a particular candidate will not activate it.

`Mechanics` pins an installed release ID and game version, declares known set and
character keys, and can supply typed `Component` and `Channel` definitions from
`artifact_sort.formulas`. The library ID must match exactly; local/pinned ID
collisions are errors. Declaring a known set does not implement its effect. No
complete built-in game-rules database or extension runtime is supplied yet.

Compilation requires validated research records for selected scenarios, scoring
formulas, and reachable local components, plus the mechanics publisher's
`validated=True` assertion. These assertions are publication prerequisites, not
an engine-generated certification of game accuracy. `allow_draft=True` permits
development calculations and returns `draft` and `limitations`; it does not
hide unsupported encodings or missing numerical inputs. Research records are
retained separately and source prose never controls evaluation.

`compiled.select()` returns established scenarios. With
`include_speculative=True`, it returns all compiled collections. No loss weights,
retention policy, or upgrade policy are implied by selection. Persistent compiled
cache storage, inventory integration, and the two deletion analyses remain to be
implemented. The first evaluator is scalar; batch/vectorized execution can be
added when build search establishes its performance needs.

`tests/test_library.py` exercises both bundled libraries, variant inheritance,
conversion snapshots, decimal normalization, capped bonuses and crit, activation,
constraint reporting, cache identities, invalid definitions, and release gating.
These test the numerical engine contract, not full game formulas or deletion safety.
