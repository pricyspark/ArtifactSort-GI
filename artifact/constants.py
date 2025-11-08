import numpy as np
from itertools import product

# TODO: This isn't the order they appear in-game for some reason
SETS = (
    'Initiate',
    'Adventurer',
    'LuckyDog',
    'TravelingDoctor',
    'ResolutionOfSojourner',
    'TinyMiracle',
    'Berserker',
    'Instructor',
    'TheExile',
    'DefendersWill',
    'BraveHeart',
    'MartialArtist',
    'Gambler',
    'Scholar',
    'PrayersForWisdom',
    'PrayersForDestiny',
    'PrayersForIllumination',
    'PrayersToSpringtime',
    'GladiatorsFinale',
    'WanderersTroupe',
    'NoblesseOblige',
    'BloodstainedChivalry',
    'MaidenBeloved',
    'ViridescentVenerer',
    'ArchaicPetra',
    'RetracingBolide',
    'Thundersoother',
    'ThunderingFury',
    'Lavawalker',
    'CrimsonWitchOfFlames',
    'BlizzardStrayer',
    'HeartOfDepth',
    'TenacityOfTheMillelith',
    'PaleFlame',
    'ShimenawasReminiscence',
    'EmblemOfSeveredFate',
    'HuskOfOpulentDreams',
    'OceanHuedClam',
    'VermillionHereafter',
    'EchoesOfAnOffering',
    'DeepwoodMemories',
    'GildedDreams',
    'DesertPavilionChronicle',
    'FlowerOfParadiseLost',
    'NymphsDream',
    'VourukashasGlow',
    'MarechausseeHunter',
    'GoldenTroupe',
    'SongOfDaysPast',
    'NighttimeWhispersInTheEchoingWoods',
    'FragmentOfHarmonicWhimsy',
    'UnfinishedReverie',
    'ScrollOfTheHeroOfCinderCity',
    'ObsidianCodex',
    'FinaleOfTheDeepGalleries',
    'LongNightsOath',
    'NightOfTheSkysUnveiling',
    'SilkenMoonsSerenade'
)

SET_2_NUM = {artifact_set: index for index, artifact_set in enumerate(SETS)}

SLOTS = ('flower', 'plume', 'sands', 'goblet', 'circlet')

SLOT_2_NUM = {slot: index for index, slot in enumerate(SLOTS)}

STATS = (
    'hp',           # 0
    'atk',          # 1
    'def',          # 2
    'hp_',          # 3
    'atk_',         # 4
    'def_',         # 5
    'enerRech_',    # 6
    'eleMas',       # 7
    'critRate_',    # 8
    'critDMG_',     # 9
    'pyro_dmg_',    # 10
    'electro_dmg_', # 11
    'cryo_dmg_',    # 12
    'hydro_dmg_',   # 13
    'dendro_dmg_',  # 14
    'anemo_dmg_',   # 15
    'geo_dmg_',     # 16
    'physical_dmg_',# 17
    'heal_'         # 18
)

STAT_2_NUM = {stat: index for index, stat in enumerate(STATS)}

MAIN_PROBS = {
    'flower':   np.array((1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)),
    'plume':    np.array((0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)),
    'sands':    np.array((0, 0, 0, 8/30, 8/30, 8/30, 3/30, 3/30, 0, 0, 0, 0, 0, 0, 0, 0, 
                0, 0, 0)),
    'goblet':   np.array((0, 0, 0, 77/400, 77/400, 76/400, 0, 10/400, 0, 0, 20/400, 
                20/400, 20/400, 20/400, 20/400, 20/400, 20/400, 20/400, 0)),
    'circlet':  np.array((0, 0, 0, 11/50, 11/50, 11/50, 0, 2/50, 5/50, 5/50, 0, 0, 0, 0, 
                0, 0, 0, 0, 5/50))
}

SUB_PROBS = np.array(
    (6, 6, 6, 4, 4, 4, 4, 4, 3, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0), 
    dtype=float
)

MAIN_VALUES = np.array(
    (
        4780, 311, -1, 46.6, 46.6, 58.3, 51.8, 186.5, 31.1, 62.2, 46.6, 46.6, 
        46.6, 46.6, 46.6, 46.6, 46.6, 58.3, 34.9
    )
)

SUB_VALUES = np.array(
    (
        298.75, 19.45, 23.13, 5.83, 5.83, 7.29, 6.48, 23.31, 3.89, 7.77, 5.83, 
        5.83, 5.83, 5.83, 5.83, 5.83, 5.83, 5.83, 4.4875
    )
)

SUB_COEFS = np.array((7, 8, 9, 10), dtype=np.uint8)

ARTIFACT_REQ_EXP = np.array(
    (
        0,      3000,   6725,   11150, 
        16300,  22200,  28875,  36375, 
        44725,  53950,  64075,  75125, 
        87150,  100175, 115325, 132925, 
        153300, 176800, 203850, 234900, 
        270475, 
        0,      3000,   6725,   11150
    ), 
    dtype=int
)

UPGRADE_REQ_EXP = np.array(
    (
        16300,  13300,  9575,   5150, 
        28425,  22525,  15850,  8350, 
        42425,  33200,  23075,  12025, 
        66150,  53125,  37975,  20375, 
        117175, 93675,  66625,  35575, 
        0,
        44725,  41725,  38000,  33575
    ), 
    dtype=int
) # TODO: check this

MAX_REQ_EXP = np.array(
    (
        270475, 267475, 263750, 259325,
        254175, 248275, 241600, 234100,
        225750, 216525, 206400, 195350,
        183325, 170300, 155150, 137550,
        117175, 93675,  66625,  35575,
        0,
        270475, 267475, 263750, 259325
    ), 
    dtype=int
)

LEARN_REQ_EXP = np.array(
    (
        140404, 137404, 133679, 129254, # 0 1/6 1/6 1/6 1/6 2/6
        148925, 143025, 136350, 128850, # 4 1/5 1/5 1/5 2/5
        150625, 141400, 131275, 120225, # 8 1/4 1/4 2/4
        144267, 131242, 116092, 98492, # 12 1/3 2/3
        117175, 93675,  66625,  35575, 
        0,
        165225, 159325, 152650, 145150
    )
)

CACHE_SIZE = 200000

CACHE_PATH = 'cache.pkl'

INCREMENTS = np.array((7, 8, 9, 10), dtype=int)

COEFS = [np.array(list(product((7, 8, 9, 10), repeat=k)), dtype=int) for k in range(5)]