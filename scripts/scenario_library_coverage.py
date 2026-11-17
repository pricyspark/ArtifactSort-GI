"""Build explicit character, role and set coverage gaps. Codex assisted."""


def build_coverage(
    data,
    plan,
    established,
    structural,
    set_support,
    revision,
    date,
    guide_keys,
    variant_count,
):
    characters = {}
    for key, char in data["characters"].items():
        roles = plan["characters"].get(key, plan["new_mechanics_research"].get(key, []))
        if key == "Traveler":
            roles = [
                f"{element}/{role}"
                for element, entries in plan["traveler_elements"].items()
                for role in entries
            ]
        assert roles, f"Missing research plan for {key}"
        entries = [node for node in established if node["characters"] == [key]]
        families = {node["family"] for node in entries}
        characters[key] = {
            "element": char["element"],
            "rarity": char["rarity"],
            "status": "partial-draft" if entries else "unresearched",
            "release_status": "present-in-pinned-GO; individually unaudited, not a release certification",
            "source": "go-data",
            "guide_source": f"guide-{key}" if key in guide_keys else None,
            "roles": [
                {
                    "role": role,
                    "family": f"{key}/{role}",
                    "status": (
                        "draft-event-subset"
                        if f"{key}/{role}" in families
                        else "remaining-research"
                    ),
                    "evidence": (
                        "opened-guide-and-numerical-sidecar"
                        if f"{key}/{role}" in families
                        else "research-candidate; not yet established by guide review"
                    ),
                    "scenario_ids": [
                        node["id"]
                        for node in entries
                        if node["family"] == f"{key}/{role}"
                    ],
                    "blockers": (
                        [
                            "Complete rotation and independent game comparison remain outstanding."
                        ]
                        if f"{key}/{role}" in families
                        else [
                            "Research kit, roles, weapons, sets, energy, activation and numerical formulas; do not infer redundancy."
                        ]
                    ),
                }
                for role in roles
            ],
        }
    sets = {}
    full_event_sets = {
        "EmblemOfSeveredFate",
        "GoldenTroupe",
        "HuskOfOpulentDreams",
        "MaidenBeloved",
        "BlizzardStrayer",
        "MarechausseeHunter",
        "GildedDreams",
    }
    specific_gaps = {
        "OceanHuedClam": "Four-piece accumulation, overflow healing, shared bubble limits, physical resistance and event timing are not modeled.",
        "NoblesseOblige": "Four-piece team ATK utility and Burst snapshot timing are not modeled.",
        "TenacityOfTheMillelith": "Holder ATK and recipient shield strength are encoded; teammate ATK utility and uptime are not scored.",
        "ViridescentVenerer": "Single Swirl event and a preexisting resistance debuff are modeled; multi-target limits and teammate utility remain gaps.",
        "DeepwoodMemories": "Dendro bonus and active resistance debuff are modeled; teammate utility and multi-wave timing remain gaps.",
        "FlowerOfParadiseLost": "Bloom/Hyperbloom/Burgeon samples are encoded; Lunar-Bloom, initial stack timing and ICD event traces require reference checks.",
        "ThunderingFury": "Electro bonus and Hyperbloom bonus only; other reactions and cooldown resets remain gaps.",
        "CrimsonWitchOfFlames": "Pyro two-piece and Burgeon bonus only; amplifying reactions and Skill stacks remain gaps.",
        "Instructor": "Niche on-field reaction support; four-star stats and team EM buff require dedicated support coverage.",
        "TheExile": "Niche team energy support; four-star enhancement and teammate energy utility remain unsupported.",
    }
    for key, metadata in data["sets"].items():
        effects = set_support.get(key, [])
        used = [
            node["id"]
            for group in [established, structural]
            for node in group
            if any(key in composition for composition in node["sets"])
        ]
        sets[key] = {
            "rarities": metadata["rarities"],
            "source": "go-data",
            "category": (
                "five-star-capable" if 5 in metadata["rarities"] else "non-five-star"
            ),
            "status": (
                "draft-event-subset"
                if key in full_event_sets
                else "partial-effects" if effects else "unresearched"
            ),
            "effect_ids": effects,
            "scenario_ids": used,
            "obsolete": "not assessed; lack of a best-in-slot recommendation is not obsolescence",
            "blockers": [
                specific_gaps.get(
                    key,
                    (
                        "Activation snapshots and complete rotations need independent game checks."
                        if key in full_event_sets
                        else (
                            "Two-piece only; four-piece role/effects require research."
                            if effects
                            else "No executable effect coverage. Naming this key in mechanics does not implement its effects."
                        )
                    ),
                )
            ],
        }
    return {
        "format": "artifact-sort-library-coverage",
        "version": 1,
        "library_revision": revision,
        "created_with": "Codex assistance",
        "as_of": date,
        "complete": False,
        "scope": "All pinned GO character records, every Traveler element, all pinned sets, and mismatches found in the KQM guide index. This is a full inventory of that snapshot, not a certified current released roster or exhaustive role census.",
        "counts": {
            "snapshot_characters": len(characters),
            "traveler_elements": len(plan["traveler_elements"]),
            "guide_index_only": len(plan["guide_index_only"]),
            "sets": len(sets),
            "characters_with_numerical_drafts": sum(
                bool(node["status"] == "partial-draft") for node in characters.values()
            ),
            "established": len(established),
            "parameter_variations": variant_count,
            "structural_variations": len(structural),
            "validated_scenarios": 0,
        },
        "characters": characters,
        "guide_index_only": plan["guide_index_only"],
        "sets": sets,
        "prospects": [
            {
                "id": node["id"],
                "family": node["family"],
                "status": "assumed-structural-draft",
            }
            for node in structural
        ],
        "proposed_extensions": [
            {
                "capability": "ordered-event-model",
                "implemented": False,
                "argument_units": [
                    "time seconds",
                    "GOOD actors and target keys",
                    "stat snapshots",
                    "typed hit/healing/shield events",
                ],
                "result_units": ["damage", "healing", "shield", "energy"],
                "dependencies": [
                    "talent coefficients",
                    "ICD and ownership",
                    "set timing",
                    "buff/snapshot rules",
                    "complete team inputs",
                ],
                "semantics": "Deterministic ordered event trace applies timed effects, ownership and hit/target limits before aggregating damage and utility. No unsupported expression operation is emitted.",
                "reference_cases": [
                    "Clam capped/uncapped three-second window",
                    "Gilded activation first and subsequent cores",
                    "two Hyperblooms on one target in 0.5s",
                    "Nahida C2 reaction crit",
                    "Lunar multi-character contribution and Stellar reactions",
                ],
            },
            {
                "capability": "team-objective-contract",
                "implemented": False,
                "argument_units": [
                    "per-actor damage/healing/shield/energy outcomes",
                    "explicit team rotations",
                ],
                "result_units": ["damage or separately declared support utility"],
                "dependencies": [
                    "teammate base stats",
                    "shared artifact/actor feasibility",
                    "buff recipients and timing",
                ],
                "semantics": "Keep outgoing/received healing, holder/recipient stats and teammate buffs separate; choose a documented objective without implicit retention weights.",
                "reference_cases": [
                    "Noblesse ATK buff with snapshot and dynamic recipients",
                    "Instructor versus five-star sets",
                    "Bolide wearer versus shield caster",
                    "Scroll independent buff durations",
                ],
            },
        ],
    }
