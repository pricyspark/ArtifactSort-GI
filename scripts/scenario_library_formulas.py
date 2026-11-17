"""Author typed formula and effect tables from pinned facts. Codex assisted."""


def op(name, *args):
    return {"op": name, "args": list(args)}


def stat(key, stage="effective"):
    return {"stat": key, "stage": stage}


def parameter(key):
    return {"parameter": key}


def typed(value, unit):
    return {"value": value, "unit": unit}


def ref(key):
    return {"ref": key}


def channel(key):
    return {"channel": key}


def condition(key, value):
    return {"condition": key, "equals": value}


def record(description, sources, notes=(), blockers=()):
    return {
        "status": "draft",
        "description": description,
        "sources": list(sources),
        "notes": list(notes),
        "blockers": list(blockers),
        "checks": [],
    }


def author_formulas(reaction_level90):
    COMPONENTS = {}
    COMPONENT_RECORDS = {}
    FORMULAS = {}
    FORMULA_RECORDS = {}
    CHANNELS = {
        key: {"unit": unit, "combine": combine}
        for key, unit, combine in [
            ("damage_bonus", "scalar", "add"),
            ("reaction_bonus", "scalar", "add"),
            ("resistance_shred", "scalar", "add"),
            ("received_healing", "scalar", "add"),
            ("shield_strength", "scalar", "add"),
            ("additive_damage", "damage", "add"),
            ("special_multiplier", "scalar", "multiply"),
            ("talent_crit_rate", "scalar", "add"),
        ]
    }
    SET_EFFECTS = []
    SET_SUPPORT = {}

    def component(
        key, stage, unit, expression, description, sources, target=None, when=None
    ):
        node = {"stage": stage, "unit": unit, "expression": expression}
        if target:
            node["contributes_to"] = target
        if when:
            node["when"] = when
        COMPONENTS[key] = node
        COMPONENT_RECORDS[key] = record(description, sources)

    def set_effect(
        key, set_key, pieces, stage, target, expression, description, extra=()
    ):
        when = {"set": set_key, "pieces": pieces}
        if extra:
            when = {"all": [when, *extra]}
        unit = "em" if target == "stats.eleMas" else "scalar"
        component(key, stage, unit, expression, description, ["kqm-sets"], target, when)
        SET_EFFECTS.append(key)
        SET_SUPPORT.setdefault(set_key, []).append(key)

    component(
        "expected-crit",
        "score",
        "scalar",
        op(
            "add",
            1,
            op(
                "multiply",
                op(
                    "clamp",
                    op("add", stat("critRate_"), channel("talent_crit_rate")),
                    0,
                    1,
                ),
                op("max", stat("critDMG_"), 0),
            ),
        ),
        "Expected crit factor, with crit rate clipped to [0, 1].",
        ["kqm-damage"],
    )
    r = op("subtract", parameter("enemy_resistance"), channel("resistance_shred"))
    component(
        "enemy-resistance",
        "score",
        "scalar",
        op(
            "add",
            op(
                "subtract",
                op("subtract", 1, op("divide", op("min", r, 0), 2)),
                op("clamp", r, 0, 0.75),
            ),
            op(
                "subtract",
                op("divide", 1, op("add", 1, op("multiply", 4, op("max", r, 0.75)))),
                0.25,
            ),
        ),
        "Continuous piecewise RES factor: 1-r/2 below zero, 1-r below 0.75, 1/(4r+1) otherwise.",
        ["kqm-damage"],
    )
    component(
        "enemy-defense",
        "bonus",
        "scalar",
        op(
            "divide",
            op("add", parameter("character_level"), 100),
            op(
                "add",
                op("add", parameter("character_level"), 100),
                op(
                    "multiply",
                    op("add", parameter("enemy_level"), 100),
                    op("subtract", 1, parameter("defense_reduction")),
                    op("subtract", 1, parameter("defense_ignore")),
                ),
            ),
        ),
        "Level-based enemy defense factor with separately supplied DEF reduction and ignore.",
        ["kqm-damage"],
    )
    for key, coefficient, denominator in [
        ("transformative-em", 16, 2000),
        ("additive-em", 5, 1200),
    ]:
        component(
            key,
            "score",
            "scalar",
            op(
                "add",
                1,
                op(
                    "divide",
                    op("multiply", coefficient, stat("eleMas")),
                    op("add", typed(denominator, "em"), stat("eleMas")),
                ),
                channel("reaction_bonus"),
            ),
            f"EM curve with numerator {coefficient} times EM and denominator EM + {denominator}, plus reaction bonus.",
            ["go-reactions", "kqm-damage"],
        )
    component(
        "level90-reaction",
        "bonus",
        "damage",
        typed(reaction_level90, "damage"),
        "Level 90 transformative/additive reaction base; no enemy DEF or crit included.",
        ["go-reactions"],
    )

    # Static two-piece effects apply to actual candidate counts, never fixed buffs.
    for set_key, stat_key, value in [
        ("EmblemOfSeveredFate", "enerRech_", 0.2),
        ("TenacityOfTheMillelith", "hp_", 0.2),
        ("VourukashasGlow", "hp_", 0.2),
        ("HuskOfOpulentDreams", "def_", 0.3),
        ("MaidenBeloved", "heal_", 0.15),
        ("OceanHuedClam", "heal_", 0.15),
        ("GladiatorsFinale", "atk_", 0.18),
        ("ShimenawasReminiscence", "atk_", 0.18),
        ("BlizzardStrayer", "cryo_dmg_", 0.15),
        ("HeartOfDepth", "hydro_dmg_", 0.15),
        ("NymphsDream", "hydro_dmg_", 0.15),
        ("ArchaicPetra", "geo_dmg_", 0.15),
        ("ThunderingFury", "electro_dmg_", 0.15),
        ("ViridescentVenerer", "anemo_dmg_", 0.15),
        ("DeepwoodMemories", "dendro_dmg_", 0.15),
        ("CrimsonWitchOfFlames", "pyro_dmg_", 0.15),
        ("WanderersTroupe", "eleMas", 80),
        ("GildedDreams", "eleMas", 80),
        ("FlowerOfParadiseLost", "eleMas", 80),
    ]:
        expression = typed(value, "em") if stat_key == "eleMas" else value
        set_effect(
            f"{set_key}-2",
            set_key,
            2,
            "static",
            f"stats.{stat_key}",
            expression,
            f"Two pieces add {value} to {stat_key}.",
        )

    set_effect(
        "emblem-burst",
        "EmblemOfSeveredFate",
        4,
        "bonus",
        "channels.damage_bonus",
        op("min", op("multiply", stat("enerRech_"), 0.25), 0.75),
        "Burst bonus is a quarter of effective ER, capped at 0.75.",
        [condition("damage_type", "burst")],
    )
    for pieces, value, extra, suffix in [
        (2, 0.2, [], "2"),
        (4, 0.25, [], "4"),
        (4, 0.25, [condition("golden_offfield_window", True)], "offfield"),
    ]:
        set_effect(
            f"golden-{suffix}",
            "GoldenTroupe",
            pieces,
            "bonus",
            "channels.damage_bonus",
            value,
            "Skill bonus; the additional off-field portion requires its explicit two-second grace-window state.",
            [condition("damage_type", "skill"), *extra],
        )
    for stat_key in ["def_", "geo_dmg_"]:
        set_effect(
            f"husk-{stat_key}",
            "HuskOfOpulentDreams",
            4,
            "static",
            f"stats.{stat_key}",
            op("multiply", op("clamp", {"condition": "husk_stacks"}, 0, 4), 0.06),
            "Curiosity adds 0.06 per stack, capped at four; evaluated at the declared snapshot.",
        )
    set_effect(
        "maiden-received",
        "MaidenBeloved",
        4,
        "bonus",
        "channels.received_healing",
        0.2,
        "Active ten-second Maiden buff adds received healing, separately from outgoing healing.",
        [condition("maiden_active", True)],
    )
    for key, state in [
        ("blizzard-cryo", ["cryo", "frozen"]),
        ("blizzard-frozen", ["frozen"]),
    ]:
        set_effect(
            key,
            "BlizzardStrayer",
            4,
            "static",
            "stats.critRate_",
            0.2,
            "Blizzard crit additions distinguish a Cryo aura from Frozen.",
            [{"any": [condition("enemy_state", value) for value in state]}],
        )
    set_effect(
        "marechaussee-crit",
        "MarechausseeHunter",
        4,
        "static",
        "stats.critRate_",
        op("multiply", op("clamp", {"condition": "marechaussee_stacks"}, 0, 3), 0.12),
        "Crit addition at an explicitly sampled HP-change stack count; stacking off-field is not assumed.",
    )
    set_effect(
        "marechaussee-attacks",
        "MarechausseeHunter",
        2,
        "bonus",
        "channels.damage_bonus",
        0.15,
        "Normal or charged attack damage bonus.",
        [{"any": [condition("damage_type", v) for v in ["normal", "charged"]]}],
    )
    set_effect(
        "noblesse-burst",
        "NoblesseOblige",
        2,
        "bonus",
        "channels.damage_bonus",
        0.2,
        "Two-piece Burst damage bonus; four-piece teammate buff is not modeled.",
        [condition("damage_type", "burst")],
    )
    set_effect(
        "gilded-em",
        "GildedDreams",
        4,
        "static",
        "stats.eleMas",
        op(
            "multiply",
            typed(50, "em"),
            op("clamp", {"condition": "gilded_different"}, 0, 3),
        ),
        "EM from different-element teammates after the triggering reaction, at a declared buff state.",
        [condition("gilded_active", True)],
    )
    set_effect(
        "gilded-atk",
        "GildedDreams",
        4,
        "static",
        "stats.atk_",
        op("multiply", 0.14, op("clamp", {"condition": "gilded_same"}, 0, 3)),
        "ATK from same-element teammates after activation; counts must sum to three.",
        [condition("gilded_active", True)],
    )
    set_effect(
        "paradise-reaction",
        "FlowerOfParadiseLost",
        4,
        "bonus",
        "channels.reaction_bonus",
        op(
            "multiply",
            0.4,
            op(
                "add",
                1,
                op(
                    "multiply",
                    0.25,
                    op("clamp", {"condition": "paradise_stacks"}, 0, 4),
                ),
            ),
        ),
        "Bloom-family reaction bonus; each stack adds one quarter of the base 0.4 bonus.",
        [
            {
                "any": [
                    condition("reaction", v) for v in ["bloom", "hyperbloom", "burgeon"]
                ]
            }
        ],
    )
    set_effect(
        "fury-hyperbloom",
        "ThunderingFury",
        4,
        "bonus",
        "channels.reaction_bonus",
        0.4,
        "Hyperbloom reaction damage bonus; no off-field cooldown reduction is scored.",
        [condition("reaction", "hyperbloom")],
    )
    set_effect(
        "witch-burgeon",
        "CrimsonWitchOfFlames",
        4,
        "bonus",
        "channels.reaction_bonus",
        0.4,
        "Burgeon damage bonus; Pyro talent damage is outside this objective.",
        [condition("reaction", "burgeon")],
    )
    set_effect(
        "deepwood-resistance",
        "DeepwoodMemories",
        4,
        "bonus",
        "channels.resistance_shred",
        0.3,
        "Dendro resistance reduction while the holder's Skill/Burst hit debuff remains active.",
        [condition("deepwood_active", True), condition("damage_element", "dendro")],
    )
    set_effect(
        "viridescent-swirl",
        "ViridescentVenerer",
        4,
        "bonus",
        "channels.reaction_bonus",
        0.6,
        "Swirl damage bonus; teammate resistance reduction remains outside this objective.",
        [condition("reaction", "swirl")],
    )
    set_effect(
        "viridescent-resistance",
        "ViridescentVenerer",
        4,
        "bonus",
        "channels.resistance_shred",
        0.4,
        "Resistance reduction of the declared Swirled element after on-field activation.",
        [condition("viridescent_active", True)],
    )
    for target, value in [("stats.atk_", 0.2), ("channels.shield_strength", 0.3)]:
        set_effect(
            f"tenacity-{target.split('.')[-1]}",
            "TenacityOfTheMillelith",
            4,
            "static" if target.startswith("stats") else "bonus",
            target,
            value,
            "Active Skill-hit team buff; shield strength belongs to the shield recipient.",
            [condition("tenacity_active", True)],
        )

    # Character and weapon effects are registered only by their own scenarios.
    component(
        "harbinger-crit",
        "static",
        "scalar",
        0.28,
        "R5 Harbinger crit buff while holder HP is above 90%.",
        ["weapon-harbinger"],
        "stats.critRate_",
        condition("harbinger_active", True),
    )
    component(
        "albedo-low-hp",
        "bonus",
        "scalar",
        0.25,
        "Albedo A1 bonus to Transient Blossoms below 50% enemy HP.",
        ["sheet-Albedo"],
        "channels.damage_bonus",
        condition("enemy_below_half", True),
    )
    component(
        "albedo-hex-addition",
        "bonus",
        "damage",
        op("multiply", stat("def"), typed(2.4, "damage/def")),
        "Silver Isotoma A1 additive damage is 2.4 times effective DEF; requires Hexerei activation.",
        ["sheet-Albedo", "guide-Albedo"],
        "channels.additive_damage",
        condition("silver_isotoma", True),
    )
    component(
        "neuvillette-hp-bonus",
        "static",
        "scalar",
        op(
            "clamp",
            op("multiply", op("subtract", {"condition": "hp_fraction"}, 0.3), 0.6),
            0,
            0.3,
        ),
        "A4 Hydro bonus from current HP fraction above 0.3, capped at 0.3; a single HP event state is sampled.",
        ["sheet-Neuvillette"],
        "stats.hydro_dmg_",
    )
    component(
        "neuvillette-a1",
        "bonus",
        "scalar",
        parameter("a1_multiplier"),
        "A1 separate enhanced charged-attack multiplier; authored sample chooses a documented discrete stack value.",
        ["sheet-Neuvillette"],
        "channels.special_multiplier",
    )
    component(
        "ayaka-dash",
        "static",
        "scalar",
        0.18,
        "Ayaka A4 Cryo bonus after the dash hits its target.",
        ["sheet-KamisatoAyaka"],
        "stats.cryo_dmg_",
        condition("ayaka_dash_active", True),
    )
    component(
        "shinobu-low-hp-healing",
        "static",
        "scalar",
        0.15,
        "Shinobu A1 outgoing healing addition at or below half HP.",
        ["sheet-KukiShinobu"],
        "stats.heal_",
        condition("holder_below_half", True),
    )
    for key, target, coefficient, cap in [
        ("nahida-a4-damage", "damage_bonus", 0.001, 0.8),
        ("nahida-a4-crit", "talent_crit_rate", 0.0003, 0.24),
    ]:
        component(
            key,
            "bonus",
            "scalar",
            op(
                "clamp",
                op(
                    "multiply",
                    op("subtract", stat("eleMas"), typed(200, "em")),
                    typed(coefficient, "scalar/em"),
                ),
                0,
                cap,
            ),
            "Nahida Tri-Karma A4 bonus from EM above 200, capped after 800 additional EM.",
            ["sheet-Nahida"],
            f"channels.{target}",
        )

    def formula(key, unit, expression, description, sources):
        FORMULAS[key] = {"unit": unit, "expression": expression}
        FORMULA_RECORDS[key] = record(description, sources)

    for primary, element in [
        ("atk", "electro"),
        ("atk", "hydro"),
        ("atk", "cryo"),
        ("hp", "hydro"),
        ("hp", "cryo"),
        ("def", "geo"),
    ]:
        damage = op(
            "add",
            op(
                "multiply",
                stat(primary),
                parameter("talent_coefficient"),
                typed(1, f"damage/{primary}"),
            ),
            channel("additive_damage"),
        )
        formula(
            f"{primary}-{element}-hit",
            "damage",
            op(
                "multiply",
                damage,
                op("add", 1, stat(f"{element}_dmg_"), channel("damage_bonus")),
                ref("expected-crit"),
                ref("enemy-defense"),
                ref("enemy-resistance"),
                channel("special_multiplier"),
            ),
            f"One {element} talent hit from {primary}, plus additive damage, applicable bonuses, expected crit, DEF and RES.",
            ["kqm-damage"],
        )
    formula(
        "em-reaction",
        "damage",
        op(
            "multiply",
            ref("level90-reaction"),
            parameter("reaction_multiplier"),
            ref("transformative-em"),
            ref("enemy-resistance"),
        ),
        "One level-90 owned transformative reaction; uses EM and resistance, ignores ordinary crit, DEF and talent bonuses.",
        ["go-reactions", "kqm-damage"],
    )
    formula(
        "atk-em-dendro-hit",
        "damage",
        op(
            "multiply",
            op(
                "add",
                op(
                    "multiply",
                    stat("atk"),
                    parameter("talent_coefficient"),
                    typed(1, "damage/atk"),
                ),
                op(
                    "multiply",
                    stat("eleMas"),
                    parameter("em_damage_coefficient"),
                    typed(1, "damage/em"),
                ),
                op(
                    "multiply",
                    ref("level90-reaction"),
                    parameter("reaction_multiplier"),
                    ref("additive-em"),
                ),
            ),
            op("add", 1, stat("dendro_dmg_"), channel("damage_bonus")),
            ref("expected-crit"),
            ref("enemy-defense"),
            ref("enemy-resistance"),
        ),
        "Mixed ATK/EM Dendro talent damage with optional owned Spread addition before bonuses and crit.",
        ["sheet-Nahida", "go-reactions", "kqm-damage"],
    )
    for primary in ["hp", "atk", "def"]:
        formula(
            f"{primary}-healing",
            "healing",
            op(
                "multiply",
                op(
                    "add",
                    op(
                        "multiply",
                        stat(primary),
                        parameter("healing_coefficient"),
                        typed(1, f"healing/{primary}"),
                    ),
                    op("multiply", parameter("flat_healing"), typed(1, "healing")),
                    op(
                        "multiply",
                        stat("eleMas"),
                        parameter("em_healing_coefficient"),
                        typed(1, "healing/em"),
                    ),
                ),
                op(
                    "add",
                    1,
                    stat("heal_"),
                    parameter("recipient_healing_bonus"),
                    channel("received_healing"),
                ),
            ),
            f"One received heal: {primary} talent term plus flat and optional EM terms; outgoing and incoming bonuses add, while remaining distinct source/recipient inputs.",
            ["kqm-healing"],
        )
    formula(
        "hp-shield-absorption",
        "shield",
        op(
            "multiply",
            op(
                "add",
                op(
                    "multiply",
                    stat("hp"),
                    parameter("shield_coefficient"),
                    typed(1, "shield/hp"),
                ),
                op("multiply", parameter("flat_shield"), typed(1, "shield")),
            ),
            parameter("absorption_multiplier"),
            op(
                "add",
                1,
                parameter("recipient_shield_strength"),
                channel("shield_strength"),
            ),
        ),
        "One shield's effective absorption, including talent flat term, elemental absorption and recipient shield strength.",
        ["sheet-Zhongli", "kqm-shields"],
    )
    formula(
        "atk-hp-cryo-hit",
        "damage",
        op(
            "multiply",
            op(
                "add",
                op(
                    "multiply",
                    stat("atk"),
                    parameter("talent_coefficient"),
                    typed(1, "damage/atk"),
                ),
                op(
                    "multiply",
                    stat("hp"),
                    parameter("hp_damage_coefficient"),
                    typed(1, "damage/hp"),
                ),
            ),
            op("add", 1, stat("cryo_dmg_"), channel("damage_bonus")),
            ref("expected-crit"),
            ref("enemy-defense"),
            ref("enemy-resistance"),
        ),
        "Assumed mixed ATK/HP Cryo hit with explicit independent scaling terms; no future kit is asserted.",
        ["kqm-damage"],
    )

    return (
        COMPONENTS,
        COMPONENT_RECORDS,
        FORMULAS,
        FORMULA_RECORDS,
        CHANNELS,
        SET_EFFECTS,
        SET_SUPPORT,
    )
