"""Rebuild the offline research batch from pinned inputs. Codex assisted.

Run from the repository root: python scripts/build_scenario_library.py
This authors draft definitions, never validated recommendations.
"""

from copy import deepcopy
from hashlib import sha256
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.scenario_library_coverage import build_coverage
from scripts.scenario_library_formulas import author_formulas, record

OUT = ROOT / "scenarios"
SNAPSHOT = OUT / "research/source-snapshot.json"
DATA = json.loads(SNAPSHOT.read_text())
REVISION = "roster-research-2026-10-05-1"
PIN = "research-subset-go-d517a2562e77-v1"
GO = f"{DATA['repository']}/blob/{DATA['commit']}/"
DATE = "2026-10-05"


SOURCES = {
    "go-data": {
        "url": GO + "libs/gi/stats/src/allStat_gen.json",
        "title": "Pinned GO generated stats and talent arrays",
        "locator": "char.data, char.expCurve, char.skillParam, weapon.data, weapon.expCurve, art.data",
        "retrieved_at": DATE,
        "commit": DATA["commit"],
        "game_version": "Not declared by this generated file; snapshot date is not a patch assertion.",
        "sha256": DATA["files"]["libs/gi/stats/src/allStat_gen.json"],
    },
    "go-reactions": {
        "url": GO + "libs/gi/formula/src/data/common/reaction.ts",
        "title": "Pinned GO reaction level table and EM curves",
        "locator": "transLvlMultis[90], eleMasMulti, additive and transformative formulas",
        "retrieved_at": DATE,
        "commit": DATA["commit"],
    },
    "kqm-damage": {
        "url": "https://library.keqingmains.com/combat-mechanics/damage/damage-formula",
        "title": "KQM TCL Damage Formula",
        "locator": "Critical Hits; Enemy Defense; Enemy Resistance; Transformative and Additive Reaction",
        "retrieved_at": DATE,
        "game_version": "Not stated on opened page",
    },
    "kqm-sets": {
        "url": "https://library.keqingmains.com/equipment/artifacts",
        "title": "KQM TCL artifact reference",
        "locator": "Named set sections; activation findings",
        "retrieved_at": DATE,
        "game_version": "Not stated on opened page; includes Lunar and Stellar set descriptions",
    },
    "kqm-index": {
        "url": "https://keqingmains.com/",
        "title": "KQM guide index",
        "locator": "Character/build guide cards, including newer 7.1 entries",
        "retrieved_at": DATE,
        "game_version": "Mixed guide versions; an index entry does not establish release availability",
    },
    "kqm-healing": {
        "url": "https://library.keqingmains.com/combat-mechanics/damage/healing",
        "title": "KQM TCL Healing",
        "locator": "General Formula and Base Healing: outgoing and incoming bonuses add; source and recipient differ",
        "retrieved_at": DATE,
        "game_version": "Not stated on opened page",
    },
    "kqm-shields": {
        "url": "https://library.keqingmains.com/combat-mechanics/damage/shields",
        "title": "KQM TCL Shields",
        "locator": "Shield Base Absorption; Shield Strength Bonuses; active recipient; Geo multiplier",
        "retrieved_at": DATE,
        "game_version": "Not stated on opened page; some examples are old",
    },
    "weapon-harbinger": {
        "url": GO + "libs/gi/sheets/src/Weapons/Sword/HarbingerOfDawn/index.tsx",
        "title": "Pinned GO Harbinger of Dawn",
        "locator": "critRateSrc_[5] and HP-above-90 activation",
        "retrieved_at": DATE,
        "commit": DATA["commit"],
    },
}
GUIDES = {
    "Fischl": ("fischl", "4.0"),
    "Xingqiu": ("xingqiu", "5.7"),
    "Barbara": ("barbara", "3.2"),
    "Zhongli": ("zhongli", "Luna II"),
    "KukiShinobu": ("shinobu", "5.4"),
    "RaidenShogun": ("raiden", "5.7"),
    "Thoma": ("thoma", "5.0"),
    "Albedo": ("albedo", "Luna V"),
    "Neuvillette": ("neuvillette", "Luna IV"),
    "Yelan": ("yelan", "5.4"),
    "KamisatoAyaka": ("ayaka", "5.8"),
    "Yaoyao": ("yaoyao", "4.0"),
    "Jean": ("jean", "4.0"),
    "Nahida": ("nahida", "not stated on opened page"),
}
for key, (slug, version) in GUIDES.items():
    SOURCES[f"guide-{key}"] = {
        "url": f"https://keqingmains.com/q/{slug}-quickguide/",
        "title": f"KQM {key} Quick Guide",
        "locator": "Playstyles; Artifacts: ER Requirements, Artifact Stats, Artifact Sets; Weapons",
        "retrieved_at": DATE,
        "game_version": version,
    }
    SOURCES[f"sheet-{key}"] = {
        "url": GO + f"libs/gi/sheets/src/Characters/{key}/index.tsx",
        "title": f"Pinned GO {key} field mapping",
        "locator": "dm talent-array indices and damage/healing/shield formulas",
        "retrieved_at": DATE,
        "commit": DATA["commit"],
    }

(
    COMPONENTS,
    COMPONENT_RECORDS,
    FORMULAS,
    FORMULA_RECORDS,
    CHANNELS,
    SET_EFFECTS,
    SET_SUPPORT,
) = author_formulas(DATA["reaction_level90"])

# Explicit inactive states for effects outside a scenario's modeled set strategy.
# They also make incomplete and unexpected candidate compositions diagnosable.
CONDITIONS = {
    "damage_type": "none",
    "damage_element": "none",
    "reaction": "none",
    "enemy_state": "none",
    "golden_offfield_window": False,
    "husk_stacks": 0,
    "maiden_active": False,
    "marechaussee_stacks": 0,
    "gilded_active": False,
    "gilded_same": 0,
    "gilded_different": 3,
    "paradise_stacks": 0,
    "deepwood_active": False,
    "viridescent_active": False,
    "tenacity_active": False,
    "constellation": 0,
    "burst_every_rotation": False,
}
PARAMETERS = {
    "character_level": 90,
    "enemy_level": 100,
    "enemy_resistance": 0.1,
    "defense_reduction": 0,
    "defense_ignore": 0,
}
ESTABLISHED = []
VARIANTS = []
STRUCTURAL = []
SCENARIO_RECORDS = {}


def talent(character, group, index, level=10):
    return DATA["talents"][character][group][index][level - 1]


def scenario(
    key,
    character,
    role,
    weapon,
    scoring,
    sets,
    mains,
    *,
    buffs=None,
    conditions=None,
    parameters=None,
    minimums=None,
    effects=(),
    notes=(),
    blockers=(),
):
    char = DATA["characters"][character]
    weapon_stats = DATA["weapons"][weapon]["stats"]
    base = {**char["base90"], "critRate_": 0.05, "critDMG_": 0.5, "enerRech_": 1.0}
    base["atk"] = round(base["atk"] + weapon_stats["atk"], 8)
    additions = dict(char["ascension6"])
    for stat_key, value in weapon_stats.items():
        if stat_key != "atk":
            additions[stat_key] = round(additions.get(stat_key, 0) + value, 8)
    for stat_key, value in (buffs or {}).items():
        additions[stat_key] = round(additions.get(stat_key, 0) + value, 8)
    node = {
        "id": key,
        "family": f"{character}/{role}",
        "characters": [character],
        "scoring_formula": scoring,
        "base": base,
        "buffs": additions,
        "sets": sets,
        "conditions": {**CONDITIONS, **(conditions or {})},
        "parameters": {**PARAMETERS, **(parameters or {})},
        "mains": mains,
    }
    if minimums:
        node["minimums"] = minimums
    if effects:
        node["effects"] = list(effects)
    ESTABLISHED.append(node)
    SCENARIO_RECORDS[key] = record(
        f"{character}: {role}; {scoring} event objective.",
        [f"guide-{character}", f"sheet-{character}", "go-data"],
        [
            f"Level 90/A6 character, level 90/A6 {weapon}; C{node['conditions']['constellation']}; talent 10 unless specified. Weapon refinement/passive state is documented below.",
            f"Base ATK = character {char['base90']['atk']} + weapon {weapon_stats['atk']} = {base['atk']}; HP/DEF use character base only. Weapon secondary and ascension stats are additions, not multiplied base stats.",
            "Enemy level 100, base resistance 0.10, zero DEF reduction/ignore are assumed reference target inputs. Unused set activations are explicitly inactive. No fixed teammate buff unless stated.",
            *notes,
        ],
        [
            "Draft event model, not a complete rotation or game-validated deletion recommendation.",
            "Independent in-game/GO complete-build comparison remains required.",
            *blockers,
        ],
    )
    SCENARIO_RECORDS[key]["input_evidence"] = {
        "base": "go-data: char.data + char.expCurve; derivation90 in source-snapshot.json",
        "buffs": "go-data: ascension6 and weapon level curves; extra additions stated in notes",
        "parameters": "sheet field indices for talent coefficients; other inputs explicitly assumed in notes",
        "sets_and_mains": f"guide-{character}: Artifact Stats and Artifact Sets",
        "conditions": "Explicit event snapshots; no inferred uptime multiplier",
        "minimums": "Guide endpoints or explicit assumed energy target, stated in notes",
    }
    return node


def parameter_variant(parent, suffix, changes, note):
    key = parent["id"] + "-" + suffix
    VARIANTS.append({"id": key, "extends": parent["id"], "changes": changes})
    SCENARIO_RECORDS[key] = record(
        "Sensitivity sample; same character/role family as parent.",
        SCENARIO_RECORDS[parent["id"]]["sources"],
        [note],
        ["Inherits all parent limitations; no account-specific energy guarantee."],
    )


def mains(sands, goblet, circlet):
    return {"sands": sands, "goblet": goblet, "circlet": circlet}


CRIT = ["critRate_", "critDMG_"]
EM_MIXED = [
    {a: 2, b: 2}
    for a, b in [
        ("WanderersTroupe", "GildedDreams"),
        ("WanderersTroupe", "FlowerOfParadiseLost"),
        ("GildedDreams", "FlowerOfParadiseLost"),
    ]
]
for character, weapon, reaction, er, note in [
    (
        "KukiShinobu",
        "IronSting",
        "hyperbloom",
        None,
        "Iron Sting R1 passive has no effect on Hyperbloom; Burst is omitted. Team: Nahida/Xingqiu/Yelan; no Electro teammate.",
    ),
    (
        "RaidenShogun",
        "DragonsBane",
        "hyperbloom",
        None,
        "Dragon's Bane R1 ordinary damage passive does not affect Hyperbloom. Skill-only trigger; no Burst. Team: Nahida/Xingqiu/Yelan.",
    ),
    (
        "Thoma",
        "KitainCrossSpear",
        "burgeon",
        2.4,
        "R3 Kitain; C0, solo Pyro, one Skill, Burst each rotation, two Favonius teammates. Guide's 240% ER estimate is sampled. Team: Nahida/Xingqiu/Yaoyao with two Favonius weapons; procs assumed.",
    ),
]:
    strategies = [
        ("paradise", [{"FlowerOfParadiseLost": 4}]),
        ("gilded", [{"GildedDreams": 4}]),
        ("mixed", EM_MIXED),
    ]
    if character == "KukiShinobu":
        strategies += [
            ("fury", [{"ThunderingFury": 4}]),
            ("deepwood", [{"DeepwoodMemories": 4}]),
        ]
    if character == "Thoma":
        strategies += [
            ("em-er", [{"EmblemOfSeveredFate": 2, "WanderersTroupe": 2}]),
            ("witch", [{"CrimsonWitchOfFlames": 4}]),
        ]
    for suffix, sets in strategies:
        node = scenario(
            f"{character.lower()}-{reaction}-{suffix}",
            character,
            f"{reaction}-trigger",
            weapon,
            "em-reaction",
            sets,
            mains(
                ["eleMas", "enerRech_"] if er else ["eleMas"], ["eleMas"], ["eleMas"]
            ),
            conditions={
                "reaction": reaction,
                "damage_element": "dendro",
                "gilded_active": True,
                "paradise_stacks": 4,
                "deepwood_active": suffix == "deepwood",
                "burst_every_rotation": bool(er),
            },
            parameters={"reaction_multiplier": 3},
            minimums={"enerRech_": er} if er else None,
            notes=[
                note,
                "One owned core damage event at full buff stacks; initial procs and core-generation timing remain separate coverage needs. No C2 Nahida reaction crit. External Deepwood is absent unless holder wears it; sample it explicitly as sensitivity.",
            ],
        )
        if suffix == "paradise":
            parameter_variant(
                node,
                "first-core",
                {"conditions": {"paradise_stacks": 1}},
                "First stack sample: the triggering core receives Paradise's new stack per TCL findings; no guessed uptime.",
            )
            parameter_variant(
                node,
                "external-deepwood",
                {"parameters": {"enemy_resistance": -0.2}},
                "Assumed teammate Deepwood has reduced a 0.10 Dendro resistance target by 0.30. Holder has no Deepwood debuff; do not count it twice.",
            )
        if suffix == "gilded":
            parameter_variant(
                node,
                "before-activation",
                {"conditions": {"gilded_active": False}},
                "Inactive Gilded snapshot before its buff. This bounds the documented activation timing uncertainty, rather than multiplying nonlinear damage by uptime.",
            )
        if character == "Thoma" and suffix == "paradise":
            parameter_variant(
                node,
                "two-skills",
                {"minimums": {"enerRech_": 2.1}},
                "Guide's C0-C3/R3 Kitain two-Skill estimate, two Favonius teammates; 210% ER. Same owned-core formula and role.",
            )

for suffix, sets in [
    ("golden", [{"GoldenTroupe": 4}]),
    (
        "mixed",
        [
            {"GoldenTroupe": 2, "ThunderingFury": 2},
            {"GoldenTroupe": 2, "GladiatorsFinale": 2},
            {"ThunderingFury": 2, "GladiatorsFinale": 2},
        ],
    ),
]:
    node = scenario(
        f"fischl-offfield-{suffix}",
        "Fischl",
        "off-field-damage",
        "PrototypeCrescent",
        "atk-electro-hit",
        sets,
        mains(["atk_"], ["electro_dmg_"], CRIT),
        minimums={"enerRech_": 1.2},
        conditions={
            "damage_type": "skill",
            "damage_element": "electro",
            "golden_offfield_window": True,
            "burst_every_rotation": True,
        },
        parameters={"talent_coefficient": talent("Fischl", "skill", 0)},
        notes=[
            "C0/R1 Crescent; weak-point passive inactive, Hexerei bonus inactive (no second Hexerei unit). One Oz projectile, skillParam.skill[0][9]. Guide ER lower endpoint 1.20; team energy remains an assumption.",
            "Excludes A4/C6 and summon/Burst damage; Aggravate and new Hexerei rotations remain unsupported coverage.",
        ],
    )
    if suffix == "golden":
        parameter_variant(
            node,
            "er140",
            {"minimums": {"enerRech_": 1.4}},
            "Upper guide endpoint, uncertain team energy with Burst every rotation.",
        )
        parameter_variant(
            node,
            "onfield",
            {"conditions": {"golden_offfield_window": False}},
            "On-field Skill hit after Golden's two-second grace window; this is not an on-field Physical-role formula.",
        )
        parameter_variant(
            node,
            "atk500",
            {"buffs": {"atk": 500}},
            "Assumed external 500 flat ATK, not a sourced Bennett kit value; sensitivity only.",
        )

for character, weapon, coefficient, er, buffs, notes in [
    (
        "Xingqiu",
        "FavoniusSword",
        talent("Xingqiu", "burst", 0),
        1.9,
        {"hydro_dmg_": 0.2},
        "C0/R5 Favonius; one reliable proc, Skill -> Burst, 21s reference rotation. Guide's 190% lower endpoint assumes average energy, not this account's exact particles. One Rain Sword; A4 Hydro addition is fixed. No reverse Vaporize on this event.",
    ),
    (
        "Yelan",
        "FavoniusWarbow",
        talent("Yelan", "burst", 1),
        1.85,
        {"hp_": 0.43},
        "C0/R5 Favonius; one Skill/proc, double Hydro. Team Yelan/Xingqiu/Hu Tao/Sucrose: Hydro resonance 0.25 HP plus three-element A1 0.18 HP. Guide's 185% ER lower endpoint. One Exquisite Throw projectile; off-field holder does not receive her A4 active-character buff.",
    ),
]:
    primary = "atk" if character == "Xingqiu" else "hp"
    for suffix, sets in [
        ("emblem", [{"EmblemOfSeveredFate": 4}]),
        (
            "mixed",
            [
                {"NoblesseOblige": 2, "HeartOfDepth": 2},
                {"HeartOfDepth": 2, "EmblemOfSeveredFate": 2},
            ],
        ),
    ]:
        node = scenario(
            f"{character.lower()}-burst-{suffix}",
            character,
            "off-field-damage",
            weapon,
            f"{primary}-hydro-hit",
            sets,
            mains([primary + "_", "enerRech_"], ["hydro_dmg_"], CRIT),
            buffs=buffs,
            minimums={"enerRech_": er},
            conditions={
                "damage_type": "burst",
                "damage_element": "hydro",
                "burst_every_rotation": True,
            },
            parameters={"talent_coefficient": coefficient},
            notes=[
                notes,
                "Single Burst-hit objective excludes Skill damage, defensive utility, and teammate set value.",
            ],
        )
        if suffix == "emblem":
            parameter_variant(
                node,
                "higher-er",
                {"minimums": {"enerRech_": 2.2 if character == "Xingqiu" else 1.95}},
                "Upper endpoint of the same guide energy case: Xingqiu 220%; double-Hydro one-Skill Favonius Yelan 195%.",
            )

for suffix, sets in [
    ("husk", [{"HuskOfOpulentDreams": 4}]),
    ("golden", [{"GoldenTroupe": 4}]),
    (
        "mixed",
        [
            {"HuskOfOpulentDreams": 2, "ArchaicPetra": 2},
            {"HuskOfOpulentDreams": 2, "GoldenTroupe": 2},
            {"ArchaicPetra": 2, "GoldenTroupe": 2},
        ],
    ),
]:
    node = scenario(
        f"albedo-blossom-{suffix}",
        "Albedo",
        "off-field-damage",
        "HarbingerOfDawn",
        "def-geo-hit",
        sets,
        mains(["def_"], ["geo_dmg_", "def_"], CRIT),
        conditions={
            "damage_type": "skill",
            "damage_element": "geo",
            "husk_stacks": 4,
            "golden_offfield_window": True,
            "harbinger_active": True,
            "enemy_below_half": False,
            "silver_isotoma": False,
        },
        parameters={"talent_coefficient": talent("Albedo", "skill", 1)},
        effects=["harbinger-crit", "albedo-low-hp", "albedo-hex-addition"],
        notes=[
            "C0, R5 Harbinger passive active above 90% HP. One Transient Blossom, skillParam.skill[1][9]. Burst omitted; no ER constraint. Four Husk stacks are preloaded before snapshot. Hexerei inactive in this baseline.",
            "Damage from casts, Burst, other party members, and Lunar-Crystallize is omitted.",
        ],
    )
    if suffix == "husk":
        parameter_variant(
            node,
            "zero-stacks",
            {"conditions": {"husk_stacks": 0}},
            "Unstacked Husk snapshot before combat; not an uptime average.",
        )
        parameter_variant(
            node,
            "weapon-inactive",
            {"conditions": {"harbinger_active": False}},
            "Harbinger HP condition fails; R5 crit buff excluded.",
        )
    hex_node = deepcopy(node)
    hex_node["id"] += "-hexerei"
    hex_node["conditions"]["silver_isotoma"] = True
    ESTABLISHED.append(hex_node)
    SCENARIO_RECORDS[hex_node["id"]] = deepcopy(SCENARIO_RECORDS[node["id"]])
    SCENARIO_RECORDS[hex_node["id"]]["notes"].append(
        "Documented established Hexerei alternative: second Hexerei teammate, homework complete, Silver Isotoma active; A1 adds 2.4 DEF. Personal blossom objective still omits Albedo's DEF-dependent teammate buff, timing and new C2 effects."
    )

for suffix, sets in [
    ("hunter", [{"MarechausseeHunter": 4}]),
    (
        "mixed",
        [
            {"HeartOfDepth": 2, "TenacityOfTheMillelith": 2},
            {"TenacityOfTheMillelith": 2, "VourukashasGlow": 2},
            {"HeartOfDepth": 2, "NymphsDream": 2},
        ],
    ),
]:
    node = scenario(
        f"neuvillette-charged-{suffix}",
        "Neuvillette",
        "on-field-damage",
        "PrototypeAmber",
        "hp-hydro-hit",
        sets,
        mains(["hp_"], ["hydro_dmg_", "hp_"], [*CRIT, "hp_"]),
        minimums={"enerRech_": 1.0},
        conditions={
            "damage_type": "charged",
            "damage_element": "hydro",
            "marechaussee_stacks": 3,
            "hp_fraction": 0.5,
            "burst_every_rotation": True,
        },
        parameters={
            "talent_coefficient": talent("Neuvillette", "auto", 4),
            "a1_multiplier": 1.6,
        },
        effects=["neuvillette-hp-bonus", "neuvillette-a1"],
        notes=[
            "C0/R5 Prototype Amber, two Skills per Burst; two assumed team Favonius procs. One enhanced charged tick, auto[4][9]. Three distinct Hydro reaction types have activated A1 (1.6 multiplier). HP fraction 0.50 is an explicit event sample, not an averaged HP trace. Hunter has three preexisting HP-change stacks.",
            "Amber energy refund is represented by the guide ER constraint; Amber healing and Skill/Burst damage are outside the tick objective. Guides can omit later team alternatives.",
        ],
    )
    if suffix == "hunter":
        parameter_variant(
            node,
            "hp80",
            {"conditions": {"hp_fraction": 0.8}},
            "Explicit 80% current HP event, at the A4 cap.",
        )
        parameter_variant(
            node,
            "hp30",
            {"conditions": {"hp_fraction": 0.3}},
            "Explicit 30% current HP event; A4 bonus is zero.",
        )
        parameter_variant(
            node,
            "er120",
            {"minimums": {"enerRech_": 1.2}},
            "Assumed missing Favonius energy case: +0.20 ER over baseline; needs exact team energy calculation.",
        )

for suffix, sets, state, stacks in [
    ("freeze", [{"BlizzardStrayer": 4}], "frozen", 0),
    ("mono-cryo", [{"BlizzardStrayer": 4}], "cryo", 0),
    ("furina-hunter", [{"MarechausseeHunter": 4}], "none", 3),
    (
        "mixed",
        [
            {"BlizzardStrayer": 2, "GladiatorsFinale": 2},
            {"BlizzardStrayer": 2, "EmblemOfSeveredFate": 2},
        ],
        "none",
        0,
    ),
]:
    node = scenario(
        f"ayaka-quickswap-{suffix}",
        "KamisatoAyaka",
        "quickswap-damage",
        "AmenomaKageuchi",
        "atk-cryo-hit",
        sets,
        mains(["atk_", "enerRech_"], ["cryo_dmg_", "atk_"], CRIT),
        minimums={"enerRech_": 1.4},
        conditions={
            "damage_type": "burst",
            "damage_element": "cryo",
            "enemy_state": state,
            "marechaussee_stacks": stacks,
            "ayaka_dash_active": True,
            "burst_every_rotation": True,
        },
        parameters={"talent_coefficient": talent("KamisatoAyaka", "burst", 0)},
        effects=["ayaka-dash"],
        notes=[
            "C0/R1 Amenoma; two Skill uses, Burst each rotation, assumed Cryo battery. ER 1.40 is an assumed conservative sample, not a claimed universal guide endpoint; seed refund not calculated. One cutting Burst tick, burst[0][9]; final bloom and normals excluded. A4 dash active.",
            "Furina/Hunter case has three HP-change stacks at Burst snapshot, healer present; Fanfare magnitude is assumed zero to isolate the set case. Cryo resonance omitted explicitly. No claim of full-rotation set ordering.",
        ],
    )
    if suffix == "freeze":
        parameter_variant(
            node,
            "unfreezable",
            {"conditions": {"enemy_state": "cryo"}},
            "Only Cryo aura remains on an unfreezable target; same quickswap role and set strategy.",
        )
        parameter_variant(
            node,
            "er180",
            {"minimums": {"enerRech_": 1.8}},
            "Explicit assumed higher-energy sample; exact battery/refund calculation is still required.",
        )

for character, weapon, group, hp_index, flat_index, extra, note in [
    (
        "Barbara",
        "ThrillingTalesOfDragonSlayers",
        "skill",
        2,
        3,
        0,
        "C0/R5 TTDS; one periodic off-field Skill heal, skill[2:4] at talent 10. Burst not required. TTDS buffs the next teammate and is not added to Barbara.",
    ),
    (
        "KukiShinobu",
        "IronSting",
        "skill",
        1,
        2,
        0.75,
        "C0/R1 Iron Sting; one ring heal, skill[1:3] at talent 10, including A4's 0.75 healing per EM. A1 low-HP outgoing bonus is active. Burst not required.",
    ),
    (
        "Yaoyao",
        "BlackTassel",
        "skill",
        1,
        2,
        0,
        "C0/R1 Black Tassel; one radish direct heal, skill[1:3] at talent 10. Burst omitted in this event model; A4 regeneration not included. No particle requirement is inferred from a completed build.",
    ),
]:
    for suffix, sets in [
        ("maiden", [{"MaidenBeloved": 4}]),
        (
            "mixed",
            [
                {"MaidenBeloved": 2, "OceanHuedClam": 2},
                {"MaidenBeloved": 2, "TenacityOfTheMillelith": 2},
                {"OceanHuedClam": 2, "TenacityOfTheMillelith": 2},
            ],
        ),
    ]:
        # Yaoyao's guide documents Maiden; mixed sets are plausible sensitivity,
        # not an invented documented recommendation for her.
        if character == "Yaoyao" and suffix == "mixed":
            continue
        if character == "KukiShinobu" and suffix == "maiden":
            suffix, sets = "tenacity", [{"TenacityOfTheMillelith": 4}]
        node = scenario(
            f"{character.lower()}-healer-{suffix}",
            character,
            "healing",
            weapon,
            "hp-healing",
            sets,
            mains(
                ["hp_", "eleMas"] if character == "KukiShinobu" else ["hp_"],
                ["hp_", "eleMas"] if character == "KukiShinobu" else ["hp_"],
                (
                    ["heal_", "hp_", "eleMas"]
                    if character == "KukiShinobu"
                    else (["heal_", "hp_"] if character == "Yaoyao" else ["heal_"])
                ),
            ),
            conditions={
                "maiden_active": True,
                "holder_below_half": True,
                "tenacity_active": suffix == "tenacity",
            },
            parameters={
                "healing_coefficient": talent(character, group, hp_index),
                "flat_healing": talent(character, group, flat_index),
                "em_healing_coefficient": extra,
                "recipient_healing_bonus": 0,
            },
            effects=["shinobu-low-hp-healing"] if character == "KukiShinobu" else [],
            notes=[
                note,
                "Recipient has no other incoming-healing bonus. Objective is received healing for one event; no overheal usefulness or damage is inferred. Four-piece Clam accumulation is not represented.",
            ],
        )
        if suffix == "maiden":
            parameter_variant(
                node,
                "buff-expired",
                {"conditions": {"maiden_active": False}},
                "Maiden's received-healing window has expired; two-piece outgoing bonus remains.",
            )

for suffix, sets in [
    ("double-hp", [{"TenacityOfTheMillelith": 2, "VourukashasGlow": 2}]),
    ("tenacity", [{"TenacityOfTheMillelith": 4}]),
]:
    node = scenario(
        f"zhongli-shield-{suffix}",
        "Zhongli",
        "shielding",
        "BlackTassel",
        "hp-shield-absorption",
        sets,
        mains(["hp_"], ["hp_"], ["hp_"]),
        conditions={"tenacity_active": suffix == "tenacity"},
        parameters={
            "shield_coefficient": talent("Zhongli", "skill", 5),
            "flat_shield": talent("Zhongli", "skill", 4),
            "absorption_multiplier": 1.5,
            "recipient_shield_strength": 0.25,
        },
        notes=[
            "C0/R1 Black Tassel, talent 10 shield, skill[5][9] HP term + skill[4][9] flat absorption. Geo shield absorbs all damage at 1.5; five Fortify stacks give recipient 0.25 shield strength. Burst omitted. No recipient Bolide or Geo resonance. Tenacity case assumes a Skill hit in the last three seconds.",
            "Shield objective alone does not encode Tenacity's team ATK utility; full support role remains a coverage gap.",
        ],
    )
    if suffix == "double-hp":
        parameter_variant(
            node,
            "no-fortify",
            {"parameters": {"recipient_shield_strength": 0}},
            "Zero Fortify stacks on a fresh shield; same shielding family.",
        )
    else:
        parameter_variant(
            node,
            "buff-expired",
            {"conditions": {"tenacity_active": False}},
            "Stele did not maintain Tenacity's three-second buff window.",
        )

node = scenario(
    "jean-sunfire-swirl",
    "Jean",
    "sunfire-trigger",
    "IronSting",
    "em-reaction",
    [{"ViridescentVenerer": 4}],
    mains(["eleMas", "enerRech_"], ["eleMas"], ["eleMas"]),
    minimums={"enerRech_": 1.6},
    conditions={
        "reaction": "swirl",
        "damage_element": "pyro",
        "viridescent_active": True,
        "burst_every_rotation": True,
    },
    parameters={"reaction_multiplier": 0.6},
    notes=[
        "C0/R1 Iron Sting, paired with Bennett; Burst once and Skill twice per rotation. 1.60 ER lower endpoint of solo-Anemo guide range is an assumed low-energy-cost sample. One Pyro Swirl owned by Jean, after on-field VV activation; self-Swirl is not claimed to activate VV without a prior enemy Swirl.",
        "Single-target event excludes simultaneous Swirl target limits, healing, chain Vaporize, aura timings and team damage. Independent reference still required.",
    ],
)
parameter_variant(
    node,
    "er200",
    {"minimums": {"enerRech_": 2.0}},
    "Solo-Anemo guide upper endpoint; no extra energy source inferred.",
)

for suffix, sets in [
    ("deepwood", [{"DeepwoodMemories": 4}]),
    ("gilded", [{"GildedDreams": 4}]),
    (
        "mixed",
        [
            {"DeepwoodMemories": 2, "WanderersTroupe": 2},
            {"WanderersTroupe": 2, "GildedDreams": 2},
        ],
    ),
]:
    node = scenario(
        f"nahida-spread-{suffix}",
        "Nahida",
        "off-field-damage",
        "SacrificialFragments",
        "atk-em-dendro-hit",
        sets,
        mains(["eleMas"], ["eleMas", "dendro_dmg_"], ["eleMas", *CRIT]),
        minimums={"enerRech_": 1.2},
        conditions={
            "damage_type": "skill",
            "damage_element": "dendro",
            "reaction": "spread",
            "deepwood_active": suffix == "deepwood",
            "gilded_active": True,
            "gilded_same": 0,
            "gilded_different": 3,
            "burst_every_rotation": True,
        },
        parameters={
            "talent_coefficient": talent("Nahida", "skill", 2),
            "em_damage_coefficient": talent("Nahida", "skill", 3),
            "reaction_multiplier": 1.25,
        },
        effects=["nahida-a4-damage", "nahida-a4-crit"],
        notes=[
            "C0/R1 Sacrificial Fragments, reset passive excluded. Team Nahida/Keqing/Fischl/Jean (double Electro); 1.20 ER guide upper endpoint. One off-field Tri-Karma hit with owned Spread; skill[2][9] ATK plus skill[3][9] EM. No Pyro Burst damage bonus, no A1 EM share to off-field Nahida, no C2 DEF reduction. External Deepwood absent unless explicitly sampled.",
            "A4 talent-specific crit and bonus depend on effective EM and their caps. Team EM sharing, cast hits, on-field normals, cores and hit frequency remain coverage gaps.",
        ],
    )
    if suffix == "deepwood":
        parameter_variant(
            node,
            "debuff-expired",
            {"conditions": {"deepwood_active": False}},
            "Dendro debuff expired before the evaluated hit.",
        )
        parameter_variant(
            node,
            "no-spread",
            {
                "parameters": {"reaction_multiplier": 0},
                "conditions": {"reaction": "none"},
            },
            "No Quicken aura: mixed ATK/EM talent scaling and A4 remain; additive Spread is zero.",
        )
    else:
        parameter_variant(
            node,
            "external-deepwood",
            {"parameters": {"enemy_resistance": -0.2}},
            "Explicit teammate Deepwood sample. No holder Deepwood debuff is added twice.",
        )

# Prospects are generic archetypes, not invented named future characters.
for key, scoring, base, sets, main_map, params, conds, note in [
    (
        "hp-cryo-freeze",
        "hp-cryo-hit",
        {"hp": 14000},
        [{"BlizzardStrayer": 4}],
        mains(["hp_"], ["cryo_dmg_"], CRIT),
        {"talent_coefficient": 0.12},
        {"damage_type": "skill", "damage_element": "cryo", "enemy_state": "frozen"},
        "Assumed HP 14000 and 0.12 damage/HP; existing freeze crit mechanics applied to an unnamed HP-scaling kit.",
    ),
    (
        "atk-hp-cryo",
        "atk-hp-cryo-hit",
        {"atk": 800, "hp": 14000},
        [{"BlizzardStrayer": 4}],
        mains(["atk_", "hp_"], ["cryo_dmg_"], CRIT),
        {"talent_coefficient": 2, "hp_damage_coefficient": 0.02},
        {"damage_type": "skill", "damage_element": "cryo", "enemy_state": "cryo"},
        "Assumed mixed scaling: ATK 800, HP 14000, coefficients 2 damage/ATK and 0.02 damage/HP; independent terms.",
    ),
    (
        "def-geo-skill",
        "def-geo-hit",
        {"def": 800},
        [{"HuskOfOpulentDreams": 4}, {"GoldenTroupe": 4}],
        mains(["def_"], ["geo_dmg_", "def_"], CRIT),
        {"talent_coefficient": 2},
        {
            "damage_type": "skill",
            "damage_element": "geo",
            "husk_stacks": 4,
            "golden_offfield_window": True,
        },
        "Assumed DEF 800, coefficient 2 damage/DEF; bounded comparison of existing DEF and off-field skill set interactions.",
    ),
    (
        "atk-healer",
        "atk-healing",
        {"atk": 800},
        [{"MaidenBeloved": 4}],
        mains(["atk_"], ["atk_"], ["heal_"]),
        {
            "healing_coefficient": 1.5,
            "flat_healing": 500,
            "em_healing_coefficient": 0,
            "recipient_healing_bonus": 0,
        },
        {"maiden_active": True},
        "Assumed ATK 800, heal 1.5 ATK + 500. Existing ATK healing establishes plausibility, not a future kit.",
    ),
    (
        "def-healer",
        "def-healing",
        {"def": 800},
        [{"HuskOfOpulentDreams": 2, "MaidenBeloved": 2}],
        mains(["def_"], ["def_"], ["heal_"]),
        {
            "healing_coefficient": 0.6,
            "flat_healing": 300,
            "em_healing_coefficient": 0,
            "recipient_healing_bonus": 0,
        },
        {},
        "Assumed DEF 800, heal 0.6 DEF + 300. Noelle provides existing DEF-healing precedent; coefficients are assumed.",
    ),
]:
    key = "prospect-" + key
    node = {
        "id": key,
        "family": "archetype/" + key.removeprefix("prospect-"),
        "characters": [],
        "scoring_formula": scoring,
        "base": {**base, "critRate_": 0.05, "critDMG_": 0.5, "enerRech_": 1.0},
        "sets": sets,
        "conditions": {**CONDITIONS, **conds},
        "parameters": {**PARAMETERS, **params},
        "mains": main_map,
    }
    STRUCTURAL.append(node)
    SCENARIO_RECORDS[key] = record(
        "Structural sensitivity archetype with explicitly assumed inputs.",
        ["kqm-sets", "kqm-damage"],
        [
            note,
            "No weapon, constellation or released character is assigned. Intrinsic crit/ER and target inputs are assumed. This samples existing mechanics only.",
        ],
        [
            "No actual kit or independent game reference validates these assumed numbers.",
            "Archetype sampling is partial; Lunar/Stellar and ordered conversion prospects remain gaps.",
        ],
    )


def write_json(path, data):
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    )


def main():
    library = {
        "$schema": "./scenario-library.schema.json",
        "format": "artifact-sort-scenario-library",
        "version": 4,
        "revision": REVISION,
        "mechanics": PIN,
        "scoring_formulas": FORMULAS,
        "components": COMPONENTS,
        "channels": CHANNELS,
        "effects": SET_EFFECTS,
        "established": ESTABLISHED,
        "parameter_variations": VARIANTS,
        "structural_variations": STRUCTURAL,
    }
    research = {
        "library_revision": REVISION,
        "created_with": "Codex assistance",
        "retrieved_at": DATE,
        "unit_convention": "Percentage stats and bonuses are decimal ratios; flat EM/stats unchanged. Source field contracts govern conversion, never magnitude.",
        "snapshot": {
            "path": "research/source-snapshot.json",
            "sha256": sha256(SNAPSHOT.read_bytes()).hexdigest(),
            "commit": DATA["commit"],
        },
        "sources": SOURCES,
        "scenarios": SCENARIO_RECORDS,
        "components": COMPONENT_RECORDS,
        "scoring_formulas": FORMULA_RECORDS,
        "coverage_gaps": [
            {
                "use": "All remaining characters and roles",
                "reason": "See library.coverage.json; absence of a numerical scenario is unresolved coverage, not artifact redundancy.",
            },
            {
                "use": "Complete rotations, team support and reactions",
                "reason": "Event objectives omit some talent sources, teammate damage, timings, ownership and snapshots. No universal weights or team utility proxies are supplied.",
            },
            {
                "use": "Newer kits and sets",
                "reason": "Lunar, Stellar, Hexerei team buffs, and new 7.1 roles require research and deterministic reference calculations. Known keys alone do not implement effects.",
            },
            {
                "use": "Clam, incoming healing and shields",
                "reason": "Received healing and Geo absorption are encoded; Clam accumulation, overheal utility, shield uptime and competing bubbles are not.",
            },
            {
                "use": "Non-five-star support",
                "reason": "Instructor, Exile and prayer sets remain visible; ordinary five-star enhancement sampling cannot certify their upgrade states.",
            },
        ],
    }
    reference_path = OUT / "research/reference-cases.json"
    if reference_path.exists():
        references = json.loads(reference_path.read_text())
        for table in ["components", "scoring_formulas"]:
            assert set(references[table]) == set(research[table])
            for key, cases in references[table].items():
                research[table][key]["checks"] = cases
    mechanics = {
        "format": "artifact-sort-mechanics",
        "version": 1,
        "id": PIN,
        "game_version": "7.1 research context; GO snapshot 2026-10-05; explicitly limited legacy/Lunar subset",
        "validated": False,
        "sets": sorted(DATA["sets"]),
        "characters": sorted(
            [
                *DATA["characters"],
                *[
                    "Traveler" + element.title()
                    for element in [
                        "anemo",
                        "geo",
                        "electro",
                        "dendro",
                        "hydro",
                        "pyro",
                        "cryo",
                    ]
                ],
            ]
        ),
        "components": {},
        "channels": {},
    }
    write_json(OUT / "library.json", library)
    write_json(OUT / "library.research.json", research)
    write_json(OUT / "library.mechanics.json", mechanics)
    write_json(
        OUT / "library.coverage.json",
        build_coverage(
            DATA,
            json.loads((OUT / "research/coverage-plan.json").read_text()),
            ESTABLISHED,
            STRUCTURAL,
            SET_SUPPORT,
            REVISION,
            DATE,
            set(GUIDES),
            len(VARIANTS),
        ),
    )
    print(
        f"Built {len(ESTABLISHED)} established, {len(VARIANTS)} parameter, {len(STRUCTURAL)} structural drafts."
    )


if __name__ == "__main__":
    main()
