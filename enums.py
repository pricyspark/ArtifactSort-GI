from enum import Enum

Type = Enum('Type', ['FLOWER', 'FEATHER', 'SANDS', 'GOBLET', 'CIRCLET'], start = 0)

Set = Enum('Set', [
    'INITIATE', 'ADVENTURER', 'LUCKY_DOG', 'TRAVELING_DOCTOR', 'BERSERKER',
    'BRAVE_HEART', 'DEFENDERS_WILL', 'GAMBLER', 'INSTRUCTOR', 'MARTIAL_ARTIST',
    'PRAYERS_FOR_DESTINY', 'PRAYERS_FOR_ILLUMINATION', 'PRAYERS_FOR_WISDOM',
    'PRAYERS_FOR_SPRINGTIME', 'RESOLUTION_OF_SOJOURNER', 'SCHOLAR', 'THE_EXILE',
    'TINY_MIRACLE', 'ARCHAIC_PETRA', 'BLIZZARD_STRAYER',
    'BLOODSTAINED_CHIVALRY', 'CRIMSON_WITCH_OF_FLAMES', 'DEEPWOOD_MEMORIES',
    'DESERT_PAVILLION_CHRONICLE', 'ECHOES_OF_AN_OFFERING',
    'EMBLEM_OF_SEVERED_FATE', 'FLOWER_OF_PARADISE_LOST',
    'FRAGMENT_OF_HARMONIC_WHIMSY', 'GILDED_DREAMS', 'GLADIATORS_FINALE',
    'GOLDEN_TROUPE', 'HEART_OF_DEPTH', 'HUSK_OF_OPULENT_DREAMS', 'LAVAWALKER',
    'MAIDEN_BELOVED', 'MARECHAUSSEE_HUNTER',
    'NIGHTTIME_WHISPERS_IN_THE_ECHOING_WOODS', 'NOBLESSE_OBLIGE',
    'NYMPHS_DREAM', 'OBSIDIAN_CODEX', 'OCEAN_HUED_CLAM', 'PALE_FLAME',
    'RETRACING_BOLIDE', 'SCROLL_OF_THE_HERO_OF_CINDER_CITY',
    'SHIMENAWAS_REMINISCENCE', 'SONG_OF_DAYS_PAST', 'TENACITY_OF_THE_MILLELITH',
    'THUNDERING_FURY', 'THUNDERSOOTHER', 'UNFINISHED_REVERIE',
    'VERMILLION_HEREAFTER', 'VIRIDESCENT_VENERER', 'VOURUKASHAS_GLOW',
    'WANDERERS_TROUPE'
], start = 0)

Stat = Enum('Stat', [
    'HP', 'ATK', 'DEF', 'HP_p', 'ATK_p', 'DEF_p', 'ER', 'EM', 'CR', 'CD',
    'PYRO', 'ELECTRO', 'CRYO', 'HYDRO', 'DENDRO', 'ANEMO', 'GEO', 'PHYSICAL',
    'HEAL'
], start = 0)

STR2TYPE = {
	'flower': Type.FLOWER,
	'plume': Type.FEATHER,
	'sands': Type.SANDS,
	'goblet': Type.GOBLET,
	'circlet': Type.CIRCLET
}

STR2SET = {
	'': Set.INITIATE,
	'': Set.ADVENTURER,
	'': Set.LUCKY_DOG,
	'': Set.TRAVELING_DOCTOR,
	'': Set.BERSERKER,
	'': Set.BRAVE_HEART,
	'': Set.DEFENDERS_WILL,
	'Gambler':                  Set.GAMBLER,
	'Instructor':               Set.INSTRUCTOR,
	'MartialArtist':            Set.MARTIAL_ARTIST,
	'': Set.PRAYERS_FOR_DESTINY,
	'': Set.PRAYERS_FOR_ILLUMINATION,
	'': Set.PRAYERS_FOR_WISDOM,
	'': Set.PRAYERS_FOR_SPRINGTIME,
	'': Set.RESOLUTION_OF_SOJOURNER,
	'': Set.SCHOLAR,
	'': Set.THE_EXILE,
	'': Set.TINY_MIRACLE,
	'ArchaicPetra':             Set.ARCHAIC_PETRA,
	'BlizzardStrayer':          Set.BLIZZARD_STRAYER,
	'BloodstainedChivalry':     Set.BLOODSTAINED_CHIVALRY,
	'CrimsonWitchOfFlames':     Set.CRIMSON_WITCH_OF_FLAMES,
	'DeepwoodMemories':         Set.DEEPWOOD_MEMORIES,
	'DesertPavilionChronicle':  Set.DESERT_PAVILLION_CHRONICLE,
	'EchoesOfAnOffering':       Set.ECHOES_OF_AN_OFFERING,
	'EmblemOfSeveredFate':      Set.EMBLEM_OF_SEVERED_FATE,
	'FlowerOfParadiseLost':     Set.FLOWER_OF_PARADISE_LOST,
	'FragmentOfHarmonicWhimsy': Set.FRAGMENT_OF_HARMONIC_WHIMSY,
	'GildedDreams':             Set.GILDED_DREAMS,
	'GladiatorsFinale':         Set.GLADIATORS_FINALE,
	'GoldenTroupe':             Set.GOLDEN_TROUPE,
	'HeartOfDepth':             Set.HEART_OF_DEPTH,
	'HuskOfOpulentDreams':      Set.HUSK_OF_OPULENT_DREAMS,
	'Lavawalker':               Set.LAVAWALKER,
	'MaidenBeloved':            Set.MAIDEN_BELOVED,
	'MarechausseeHunter':       Set.MARECHAUSSEE_HUNTER,
	'': Set.NIGHTTIME_WHISPERS_IN_THE_ECHOING_WOODS,
	'NoblesseOblige':           Set.NOBLESSE_OBLIGE,
	'NymphsDream':              Set.NYMPHS_DREAM,
	'': Set.OBSIDIAN_CODEX,
	'OceanHuedClam':            Set.OCEAN_HUED_CLAM,
	'PaleFlame':                Set.PALE_FLAME,
	'RetracingBolide':          Set.RETRACING_BOLIDE,
	'': Set.SCROLL_OF_THE_HERO_OF_CINDER_CITY,
	'ShimenawasReminiscence':   Set.SHIMENAWAS_REMINISCENCE,
	'': Set.SONG_OF_DAYS_PAST,
	'TenacityOfTheMillelith':   Set.TENACITY_OF_THE_MILLELITH,
	'ThunderingFury':           Set.THUNDERING_FURY,
	'Thundersoother':           Set.THUNDERSOOTHER,
	'UnfinishedReverie':        Set.UNFINISHED_REVERIE,
	'VermillionHereafter':      Set.VERMILLION_HEREAFTER,
	'ViridescentVenerer':       Set.VIRIDESCENT_VENERER,
	'VourukashasGlow':          Set.VOURUKASHAS_GLOW,
	'WanderersTroupe':          Set.WANDERERS_TROUPE
}

STR2STAT = {
	'hp':            Stat.HP,
	'atk':           Stat.ATK,
	'def':           Stat.DEF,
	'hp_':           Stat.HP_p,
	'atk_':          Stat.ATK_p,
	'def_':          Stat.DEF_p,
	'enerRech_':     Stat.ER,
	'eleMas':        Stat.EM,
	'critRate_':     Stat.CR,
	'critDMG_':      Stat.CD,
	'pyro_dmg_':     Stat.PYRO,
	'electro_dmg_':  Stat.ELECTRO,
	'cryo_dmg_':     Stat.CRYO,
	'hydro_dmg_':    Stat.HYDRO,
	'dendro_dmg_':   Stat.DENDRO,
	'anemo_dmg_':    Stat.ANEMO,
	'geo_dmg_':      Stat.GEO,
	'physical_dmg_': Stat.PHYSICAL,
	'heal_':         Stat.HEAL
}

'''
class Type(Enum):
    FLOWER = 0
    FEATHER = 1
    SANDS = 2
    GOBLET = 3
    CIRCLET = 4

class Set(Enum):
    INITIATE = 0
    ADVENTURER = 1
    LUCKY_DOG = 2
    TRAVELING_DOCTOR = 3
    BERSERKER = 4
    BRAVE_HEART = 5
    DEFENDERS_WILL = 6
    GAMBLER = 7
    INSTRUCTOR = 8
    MARTIAL_ARTIST = 9
    PRAYERS_FOR_DESTINY = 10
    PRAYERS_FOR_ILLUMINATION = 11
    PRAYERS_FOR_WISDOM = 12
    PRAYERS_FOR_SPRINGTIME = 13
    RESOLUTION_OF_SOJOURNER = 14
    SCHOLAR = 15
    THE_EXILE = 16
    TINY_MIRACLE = 17
    ARCHAIC_PETRA = 18
    BLIZZARD_STRAYER = 19
    BLOODSTAINED_CHIVALRY = 20
    CRIMSON_WITCH_OF_FLAMES = 21
    DEEPWOOD_MEMORIES = 22
    DESERT_PAVILLION_CHRONICLE = 23
    ECHOES_OF_AN_OFFERING = 24
    EMBLEM_OF_SEVERED_FATE = 25
    FLOWER_OF_PARADISE_LOST = 26
    FRAGMENT_OF_HARMONIC_WHIMSY = 27
    GILDED_DREAMS = 28
    GLADIATORS_FINALE = 29
    GOLDEN_TROUPE = 30
    HEART_OF_DEPTH = 31
    HUSK_OF_OPULENT_DREAMS = 32
    LAVAWALKER = 33
    MAIDEN_BELOVED = 34
    MARECHAUSSEE_HUNTER = 35
    NIGHTTIME_WHISPERS_IN_THE_ECHOING_WOODS = 36
    NOBLESSE_OBLIGE = 37
    NYMPHS_DREAM = 38
    OBSIDIAN_CODEX = 39
    OCEAN_HUED_CLAM = 40
    PALE_FLAME = 41
    RETRACING_BOLIDE = 42
    SCROLL_OF_THE_HERO_OF_CINDER_CITY = 43
    SHIMENAWAS_REMINISCENCE = 44
    SONG_OF_DAYS_PAST = 45
    TENACITY_OF_THE_MILLELITH = 46
    THUNDERING_FURY = 47
    THUNDERSOOTHER = 48
    UNFINISHED_REVERIE = 49
    VERMILLION_HEREAFTER = 50
    VIRIDESCENT_VENERER = 51
    VOURUKASHAS_GLOW = 52
    WANDERERS_TROUPE = 53

class Stat(Enum):
    HP = 0
    ATK = 1
    DEF = 2
    HP_p = 3
    ATK_p = 4
    DEF_p = 5
    ER = 6
    EM = 7
    CR = 8
    CD = 9
    PYRO = 10
    ELECTRO = 11
    CRYO = 12
    HYDRO = 13
    DENDRO = 14
    ANEMO = 15
    GEO = 16
    PHYSICAL = 17
    HEAL = 18
'''