# Standalone prompt: build the artifact scenario library

Use the following prompt with an agent that has repository and web access.
Codex assisted with this prompt and the initial research pilot.

---

You are building an offline, versioned scenario library for Artifact Sort, a
Genshin Impact artifact inventory analyzer. Produce research-backed numerical
definitions, encoded formula components, and their research records. Do not implement the deletion algorithm,
change the GUI, or publish unvalidated definitions as trusted recommendations.

## Purpose and product requirements

Deletion analysis should preserve useful artifacts across documented uses and
plausible future uses. A sparse user's Genshin Optimizer (GO) database must not
determine which characters or sets receive coverage. GO can personalize upgrade
priorities later; do not use saved GO winners as exhaustive deletion coverage.

The library has three separate lists:

- `established`: documented roles of released characters and established archetypes,
  including meaningful alternatives rather than only each character's best set.
- `parameter_variations`: speculative sensitivity cases with the same formula,
  role, and set strategy but different numerical inputs or activation conditions.
- `structural_variations`: plausible alternative scaling, roles, formulas, or set
  interactions, grounded in existing mechanics and explicit assumed parameters.

The intended analyzer produces two independently selected deletion lists for
the same inventory and deletion count: established coverage, and established
plus speculative coverage. Your task supplies definitions, not account ownership
filters, speculative weights, retention budgets, or deletion recommendations.
Incomplete sets, unfinished artifacts, and scenarios with no completed build
must remain visible coverage needs; lack of a build is not evidence of redundancy.

Declare an explicit `family` on complete scenarios for deletion aggregation.
Each family represents one character and role; weapon, set, and parameter
variants share that family. Distinct roles have separate families, and generic
archetypes have separately declared families. Parameter variants inherit the
parent's family and cannot override it. Structural variants share a family only
when they preserve the same character and role. Do not use a shared numerical
template's multi-character labels to merge different characters' families;
provide explicit per-character entries or clearly identify generic archetypes.

## Read the local contract first

Read `docs/scenario-library.md`, `scenarios/scenario-library.schema.json`,
`scenarios/library.example.json`, and its research sidecar. Inspect the pilot
and its sidecar if present. Follow applicable AGENTS.md instructions and preserve
existing user edits. Inspect `artifact_sort.library`, `artifact_sort.formulas`,
and `artifact_sort.library_runtime` for the implemented loader/compiler contract.
If the schema changes, copy it to `artifact_sort/scenario-library.schema.json`;
the package-schema equality test must pass. Use explicit pinned mechanics and
`allow_draft=True` for development checks;
passing those checks does not make a definition researched or game-validated.
Do not silently reuse the legacy `Scenario` evaluator or
its default base stats: this library is a separate authored format.

Keep `mechanics` as the shared game-rules release reference. Shared numerical
definitions belong in `scoring_formulas`; entries reference `scoring_formula`.
The v4 format uses arithmetic expression trees and reusable `components`, not a
closed menu of universal formulas. Both the scenario libraries and effects are
still drafts; the runtime compiles and evaluates v4 expressions. Encoding a formula
correctly does not establish that its physics or numerical inputs are correct.

If scope is supplied, cover that scope. Otherwise inventory all released artifact
sets and documented character roles, report a coverage matrix, and populate
tractable cases in coherent batches. Explicitly record unresearched, obsolete,
niche, unsupported, and non-five-star cases; do not force a scenario for every
set or claim that a partially populated library is complete. No new formula,
mechanics release, or condition key becomes implemented just by naming it.

## Research procedure

1. Find accessible primary theorycrafting guides and structured mechanics data.
   KQM guides explain role, main stats, sets, and team assumptions; KQM TCL or a
   pinned GO data/formula checkout can establish stats and effects. Prydwen and
   public Akasha configurations can supplement or cross-check coverage.
2. Open source pages rather than relying on snippets or remembered values. Record
   URLs, section locators, retrieval dates, and stated game versions where available.
   Check whether old guides omit newer roles or mechanics. Retrieval today does
   not mean a guide was updated today. Private Discord configs are optional;
   never invent their contents or require them for the baseline library.
3. Extract distinct roles and meaningful alternatives, then record their concrete
   assumptions: level, weapon/refinement/passive, constellation, rotation,
   team buffs, damage types, reaction ownership, set activation, and energy supply.
   Preserve source disagreements as explicit cases rather than averaging them.
4. Collect numerical stats from game data separately from guide recommendations.
   Show the derivation of combined character/weapon base stats and fixed bonuses
   in the research notes. Identify each assumed value as assumed.
5. Decompose each calculation into reusable parts: stat conversions, talent
   scaling, additive base damage, applicable bonuses, crit, reactions, defense,
   resistance, and special multipliers. Reuse components by ID instead of
   copying whole formulas for every combination. Encode each numerical part
   using the specified expression language, and explain it in research records.
6. If arithmetic is insufficient, record a coverage gap and a proposed extension
   with argument/result units, dependencies, semantics, and reference cases.
   Do not invent working operation names. A proxy is allowed only with explicit
   approximation notes and blockers; never replace EM/mixed-scaling damage
   with pure ATK scoring.

Paraphrase recommendations and retain source links; do not copy large guide
passages. Evidence quality, account priority, and speculation are distinct.

## Numerical authoring rules

- Use GOOD character, set, slot, and stat keys, with every percentage expressed
  as a decimal ratio: 46.6% damage bonus is `0.466`, baseline ER is `1.0`,
  140% ER is `1.4`, and 150% crit damage is `1.5`. Normalize percentage-point
  source data once during extraction/import, before writing numerical entries.
  Already normalized ratios, flat stats, and counts are unchanged. Determine
  units from the source contract, never magnitude; ratios can exceed `1.0`.
  This also applies to thresholds, effect constants, and numerical reference
  checks. Source prose may use `%`; condition uptimes use fractions when supported.
- `base` contains character/weapon base HP, ATK, or DEF and intrinsic starting
  stats. `buffs` contains fixed non-artifact additions. Put flat bonuses in
  `buffs`, not in the base multiplied by percentage stats.
- Use concrete finite inputs, not unexplained universal defaults. State the
  level and equipment behind them. Bounds become explicit sensitivity samples;
  do not silently average ranges or create an unlimited Cartesian product.
- ER thresholds need their weapon, constellation, team/rotation assumptions.
  A guide range is not an account-specific guarantee. Document endpoint choices.
- `sets` lists acceptable minimum compositions as alternatives. Do not hard-code
  only GO winners. Separate established niche support roles where their utility
  differs, even if their set is not recommended to farm.
- Set effects come from the pinned mechanics release and actual candidate set
  counts, not fixed bonuses copied into `buffs`. Specify damage type, field time,
  stack counts, activation, or other necessary conditions. Distinguish outgoing
  healing from received healing, holder stats from teammate buffs, and raw HP
  from effective shield absorption. Do not ignore caps, conversions, or resistance.
- Multiple characters may label a shared scenario only when the numerical
  assumptions adequately represent them. Matching scaling alone is insufficient.
  Character labels neither alter the formula nor multiply its importance.
- Parameter variants use `id`, `extends`, and `changes`. Objects merge recursively,
  scalars and arrays replace, and null removes keys. Only the schema's permitted
  parameter fields can change. Structural scenarios are complete definitions.
- Documented alternate builds remain established. A hypothetical future
  archetype is structural and has no invented named future character. Sampling
  different ER or buff levels is parameter sensitivity, not evidence of a new kit.

## Formula encoding contract

Emit both machine-readable arithmetic and a plain-language explanation. The
expression drives deterministic calculation; the explanation and evidence stay
in the research sidecar. Analysis must not need another LLM to interpret them.

Read the schema's recursive `expression` definition. Initially supported shapes
are numerical constants, typed constants, named stats at `base`/`raw`/`effective`
stages, pure component references, numerical parameters and conditions, channels,
and `add`, `subtract`, `multiply`, `divide`, `min`, `max`, `clamp`. Follow exact
operation arities and argument order. Never put mathematical prose, Python, or
an unparsed formula string into an expression field.

Percentage ratios use unit `scalar`, including bonus channels and caps. For
example, Emblem's bonus is `min(effective_ER * 0.25, 0.75)`: ER `2.0` produces
bonus `0.5`. Inputs are already normalized; do not encode multiplication or
division by 100 to convert percentages inside formulas. Preserve actual talent
and conversion coefficients. HP-derived damage needs a coefficient with
damage/HP units; do not relabel HP as ATK or damage.

Declare each component's stage and result unit. Pure components are referenced
by `ref`; effects register `contributes_to` and activation predicates. Register
set effects in the library `effects` list and character/weapon effects in the
scenario's list. Declare channel units and whether contributions add or multiply.
Effects must not also be copied into buffs, and the same ID applies only once.

Activation uses actual set-piece counts and explicit condition equality, with
`all`/`any`/`not` where necessary. A false multiplier effect is excluded, preserving
the channel's identity of one. Do not multiply a nonlinear formula by guessed
uptime unless that faithfully represents the stated event model. Separate attack
sources or explicit condition samples can be more accurate.

Honor stage ordering. Static effects precede raw stats; raw HP/ATK/DEF already
include percentage and flat bonuses. Conversions read the same pre-conversion
raw totals, never one another's output. Bonus components read effective stats;
scores assemble earlier values.
Do not create circular stat conversions or read future results. Snapshot rules,
reaction ownership, teammate contributions, and timing must remain explicit
assumptions or blockers, not hidden in prose that is needed to execute the score.

The reserved `extension` expression requires a name, version, and encoded
arguments. No extension is supported until a pinned deterministic implementation
exists and specifies its units, dependencies, and reference tests. Do not define
an implementation merely by writing an extension expression.

Use the full composed expression to determine relevant stats through dependency
tracking. Do not manually discard stats that appear unimportant: effects can
introduce ER-to-bonus, HP-to-ATK, EM-to-damage, and other indirect dependencies.
Keep nonlinear caps and formulas; fixed stat weights may only aid screening.

## Research records and validation

Keep sources, assumptions, blockers, and checks in a separate research sidecar
keyed by stable scenario, component, and scoring-formula IDs. Use `draft`, `reviewed`, and `validated` accurately.
No entry is validated because it parses or an agent feels confident.

Validate the JSON against the schema. Also check unique IDs, resolvable formula,
parent and source references, parent cycles, expanded variants, legal main stats,
finite inputs, set totals no greater than five, threshold ordering, and required
scaling base stats, operation arity, dimensional units, stage ordering, effect
activation, and reachable component dependencies. Check evidence for every consequential numerical input.

Before calling a scenario validated, resolve a real immutable mechanics release
and compare representative complete builds with an independent reference
calculation. Exercise the effects that could change deletion decisions: crit
caps, ER thresholds and conversion caps, on/off-field bonuses, incomplete set
compositions, set activation, and relevant reactions. Record method, reference,
result, and tolerances justified for the formula's fidelity. Do not claim tests
or calculations passed unless they were actually run.

Unsupported calculations remain blockers and coverage gaps. They must not be
silently dropped or converted into numerical evidence for safe deletion. Do not
mark an unresolved placeholder mechanics reference as an executable release.

## Deliverables

- Compact v4 scenario JSON with reusable components, explicit character/role families,
  and a research sidecar with matching revision IDs.
- A matching executable mechanics manifest, or the exact path to an existing one.
  Use the JSON contract in `artifact_sort.library.mechanics_from_data`: format
  `artifact-sort-mechanics`, version 1, `id` matching the library's `mechanics`,
  `game_version`, declared `sets` and `characters`, and any shared `components`
  and `channels`. Do not mark `validated` true without independent verification.
  A list of recognized sets does not implement their effects; encode those effects
  in the library or mechanics components. Report unresolved support explicitly.
- Each new component paired with a description, source/assumption record, and numerical reference cases; unresolved capabilities reported as blockers.
- A coverage report separating researched definitions, validated calculations,
  unsupported roles, and remaining research. Include sets beyond Blizzard Strayer
  and several scaling/role families when working on a general batch.
- Validation results, formula limitations, and a short account of assumptions
  that most affect artifact rankings. Include source links for findings.
- Preserve stable IDs and increment the content revision when definitions change.
  Cached analysis should use expanded numerical content and pinned mechanics,
  not source prose or revision labels alone.

Report partial coverage honestly. Prefer a small batch with clear numerical
derivations and unresolved limits over a large collection of unsupported claims.
