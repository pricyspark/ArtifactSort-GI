import numpy as np
import copy
import zlib
import math
import json

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

def find_main(artifact):
    mask = artifact == 160
    if np.any(mask):
        return np.where(mask == True)[0][0]
    else:
        return np.where(artifact == 80)[0][0]
    
def find_sub(artifact, main=None): # TODO: i'm skeptical of performance
    if main is None:
        main = find_main(artifact)
    
    temp = artifact[main]
    artifact[main] = 0
    subs = np.nonzero(artifact)[0]
    artifact[main] = temp
    
    return subs

def generate(slot, main=None, lvls=None, source='domain', size=None, rng=None, seed=None):
    try:
        _ = iter(lvls)
        slvls = np.array(lvls)
        size = len(lvls)
    except:
        if size is None:
            size = 1
        if lvls is None:
            lvls = 0
        slvls = np.full(size, lvls)
        
    if rng is None:
        rng = np.random.default_rng(seed)

    # Figure out probability of starting with 4 substats
    match source:
        case 'domain':
            prob = 1/5
        case 'normal boss':
            prob = 1/3
        case 'weekly boss':
            prob = 1/3
        case 'strongbox':
            prob = 1/3
        case 'domain reliquary':
            prob = 1/3
        case _:
            raise ValueError('Invalid artifact source.')
        
    output = np.zeros((size, 19), dtype=np.uint8)
    
    for idx, slvl in enumerate(slvls):
        # Figure out num_upgrades and num_substats for each artifact
        num_upgrades = slvl // 4
        if rng.random() > prob:
            num_upgrades -= 1
            '''
            if num_upgrades == 0:
                num_substats -= 1
            else:
                num_upgrades -= 1
            '''
                
        # Figure out main stat
        main = rng.choice(19, p=MAIN_PROBS[slot])
        if main < 3:
            output[idx, main] = 160
        else:
            output[idx, main] = 80
            
        # Figure out unique substats
        sub_probs = SUB_PROBS.copy()
        sub_probs[main] = 0
        sub_probs /= np.sum(sub_probs)
        substats = rng.choice(19, size=4, replace=False, p=sub_probs)
        for substat in substats:
            output[idx, substat] += rng.choice(SUB_COEFS)
            
        if num_upgrades == -1:
            slvls[idx] -= 4
        else:
            # Upgrade substats
            upgrades = rng.choice(4, size=num_upgrades, replace=True)
            for upgrade in upgrades:
                output[idx, substats[upgrade]] += rng.choice(SUB_COEFS)
            
    return output, slvls

def artifact_to_dict(artifacts):
    pass

def dict_to_artifact(dicts):
    # TODO: add error checking for scans that don't store base
    if type(dicts) == dict:
        artifact = np.zeros(19, dtype=np.uint8)
        base_artifact = np.zeros(19, dtype=np.uint8)
        
        slot: int = SLOT_2_NUM[dicts['slotKey']]
        rarity: int = dicts['rarity']
        slvl: int = int(dicts['level'])
        setKey: int = SET_2_NUM[dicts['setKey']]
        main: int = STAT_2_NUM[dicts['mainStatKey']]
        if main < 3:
            artifact[main] = 160
            base_artifact[main] = 160
        else:
            artifact[main] = 80
            base_artifact[main] = 80
            
        for substat in dicts['substats']:
            stat = STAT_2_NUM[substat['key']]
            value = substat['value']
            coef = round(value / SUB_VALUES[stat] * 10)
            artifact[stat] = coef
            
            init_value = substat['initialValue']
            init_coef = round(init_value / SUB_VALUES[stat] * 10)
            base_artifact[stat] = init_coef
        
        for substat in dicts['unactivatedSubstats']:
            stat = STAT_2_NUM[substat['key']]
            value = substat['value']
            coef = round(value / SUB_VALUES[stat] * 10)
            artifact[stat] = coef
            
            init_value = substat['initialValue']
            init_coef = round(init_value / SUB_VALUES[stat] * 10)
            base_artifact[stat] = init_coef
            
            slvl -= 4
        
        unactivated = dicts['totalRolls'] == 8
        
        return artifact, base_artifact, slot, rarity, slvl, unactivated, setKey
        
    else:
        temp_artifacts = []
        temp_base_artifacts = []
        temp_slots = []
        temp_rarities = []
        temp_slvls = []
        temp_unactivated = []
        temp_sets = []
        
        #artifacts = np.zeros((len(dicts), 19), dtype=np.uint8)
        #slots = np.zeros(len(dicts), dtype=np.uint8)
        #lvls = np.zeros(len(dicts), dtype=np.uint8)
        #sets = np.zeros(len(dicts), dtype=int)
        for dictionary in dicts:
            artifact, base_artifact, slot, rarity, slvl, unactivated, setKey = dict_to_artifact(dictionary)
            temp_artifacts.append(artifact)
            temp_base_artifacts.append(base_artifact)
            temp_slots.append(slot)
            temp_rarities.append(rarity)
            temp_slvls.append(slvl)
            temp_unactivated.append(unactivated)
            temp_sets.append(setKey)
            
        artifacts = np.array(temp_artifacts, dtype=np.uint8)
        base_artifacts = np.array(temp_base_artifacts, dtype=np.uint8)
        slots = np.array(temp_slots, dtype=np.uint8)
        rarities = np.array(temp_rarities, dtype=np.uint8)
        slvls = np.array(temp_slvls, dtype=np.int8)
        unactivated = np.array(temp_unactivated, dtype=bool)
        sets = np.array(temp_sets, dtype=np.uint8)
        
        return artifacts, base_artifacts, slots, rarities, slvls, unactivated, sets
    
def load(filename):
    with open(filename) as f:
        data = json.load(f)
    
    if data['format'] != 'GOOD' or data['version'] != 3:
        raise ValueError('Only GOODv3 is supported.')
    
    artifact_dict = data['artifacts']
    return artifact_dict, *dict_to_artifact(artifact_dict)

def _artifact_eq(a1, a2):
    if (a1['setKey']        != a2['setKey'] or
        a1['slotKey']       != a2['slotKey'] or 
        a1['level']         != a2['level'] or
        a1['rarity']        != a2['rarity'] or
        a1['mainStatKey']   != a2['mainStatKey']):
        return False
    
    for s1, s2 in zip(a1['substats'], a2['substats']):
        if s1['key'] != s2['key'] or not math.isclose(s1['value'], s2['value'], abs_tol=0.11):
            return False
    for s1, s2 in zip(a1['unactivatedSubstats'], a2['unactivatedSubstats']):
        if s1['key'] != s2['key'] or not math.isclose(s1['value'], s2['value'], abs_tol=0.11):
            return False
        
    return True

def merge_scans(f1, f2, outfile=None):
    # TODO: maybe *args, **kwargs for arbitrary numbers of scans
    with open(f1) as f:
        d1 = json.load(f)    
    if d1['format'] != 'GOOD' or d1['version'] != 3:
        raise ValueError('Only GOODv3 is supported.')
    
    with open(f2) as f:
        d2 = json.load(f)
    if d2['format'] != 'GOOD' or d2['version'] != 3:
        raise ValueError('Only GOODv3 is supported.')
    
    if len(d1['artifacts']) != len(d2['artifacts']):
        raise ValueError('Scans do not have the same number of artifacts.')
    
    # TODO: merge character, weapon, and material data
    artifact_dict = {
        'format': 'GOOD',
        'version': 3,
        'souce': 'ArtifactSort',
        'characters': [],
        'artifacts': [],
        'weapons': [],
        'materials': {}
    }
    
    for a1 in d1['artifacts']:
        found = False
        for a2 in d2['artifacts']:
            if _artifact_eq(a1, a2):
                temp = a1 | a2
                temp['substats'] = []
                temp['unactivatedSubstats'] = []
                
                for s1, s2 in zip(a1['substats'], a2['substats']):
                    temp['substats'].append(s1 | s2)
                    
                for s1, s2 in zip(a1['unactivatedSubstats'], a2['unactivatedSubstats']):
                    temp['unactivatedSubstats'].append(s1 | s2)
                    
                artifact_dict['artifacts'].append(temp)
                found = True
                a2['setKey'] = None
                break
        if not found:
            raise ValueError
    if outfile is not None:     
        json.dump(artifact_dict, outfile)
    return artifact_dict['artifacts'], *dict_to_artifact(artifact_dict['artifacts'])

def print_artifact(artifacts, human_readable=True) -> None:
    if artifacts.ndim == 1:
        stats = np.nonzero(artifacts)[0]
        for stat in stats:
            if human_readable:
                print(STATS[stat], round(artifacts[stat] * SUB_VALUES[stat] / 10, 2))
            else:
                print(STATS[stat], artifacts[stat])
    else:
        for artifact in artifacts:
            print_artifact(artifact)
            print()
            
def print_artifact_dict(artifacts):
    if isinstance(artifacts, dict):
        artifacts = [artifacts]
        
    for artifact in artifacts:
        print(f'+--------------------+')
        print(f'|{artifact['slotKey']:<20}|')
        print(f'|LVL: {artifact['level']:<15}|')
        print(f'|Set: {artifact['setKey'][:15]:<15}|')
        print(f'|{artifact['mainStatKey']:<20}|')
        print(f'|                    |')
        for sub in artifact['substats']:
            s = f'{sub['key']}: {sub['value']}'
            print(f'|{s[:20]:<20}|')
        for sub in artifact['unactivatedSubstats']:
            s = f'{sub['key']}: {sub['value']}'
            print(f'|*{s[:19]:<19}|')
        print(f'+--------------------+')

def _upgrade_helper(artifact, rng, main=None):
    artifact[rng.choice(find_sub(artifact, main=main))] += rng.choice(SUB_COEFS)

def upgrade(artifacts, mains=None, rng=None, seed=None):
    if rng is None:
        rng = np.random.default_rng(seed)
    
    if artifacts.ndim == 1:
        _upgrade_helper(artifacts, rng, main=mains)
    else:
        if mains is None:
            mains = [None] * len(artifacts)
        for artifact, main in zip(artifacts, mains):
            _upgrade_helper(artifact, rng, main=main)

def _smart_seed(artifacts):
    if artifacts.ndim == 1:
        return zlib.crc32(artifacts.tobytes())
    else:
        output = np.zeros(len(artifacts), dtype=np.int64)
        for idx, artifact in enumerate(artifacts):
            output[idx] = zlib.crc32(artifact.flatten().tobytes())
        return output
    
def smart_upgrade(artifacts, mains=None):
    if artifacts.ndim == 1:
        RNG = np.random.default_rng(_smart_seed(artifacts))
        _upgrade_helper(artifacts, RNG)
    else:
        seeds = _smart_seed(artifacts)
        for artifact, seed in zip(artifacts, seeds):
            RNG = np.random.default_rng(seed)
            _upgrade_helper(artifact, RNG)

def smart_upgrade_until_max(artifacts, slvls, mains=None): # TODO: this is code duplication
    num_upgrades = np.where(slvls < 0, 4, 5 - slvls // 4)    
    
    if artifacts.ndim == 1 or len(artifacts) == 1:
        for _ in range(num_upgrades):
            smart_upgrade(artifacts, mains)
    else:
        if mains is None:
            mains = [None] * len(slvls)
        for artifact, num, main in zip(artifacts, num_upgrades, mains):
            for _ in range(num):
                smart_upgrade(artifact, main)
    
def upgrade_until_max(artifacts, slvls, mains=None, seed=None):
    num_upgrades = np.where(slvls < 0, 4, 5 - slvls // 4)    
    
    if artifacts.ndim == 1 or len(artifacts) == 1:
        for _ in range(num_upgrades):
            upgrade(artifacts, mains, seed)
    else:
        if mains is None:
            mains = [None] * len(slvls)
        for artifact, num, main in zip(artifacts, num_upgrades, mains):
            for _ in range(num):
                upgrade(artifact, main) # TODO seed generator, otherwise they all get the same seed

def estimate_lvl(artifacts):
    # TODO: maybe make this more advanced, considering the number of
    # rolls from each substat individually
    if artifacts.ndim == 1:
        substats = find_sub(artifacts)
        rolls = round(np.sum(artifacts[substats]) / 8.5)
        if rolls == 3:
            return 0
        if rolls == 9:
            return 20
        return 4 * (rolls - 4) + 2
    else:
        lvls = np.zeros(len(artifacts), dtype=int)
        for idx, artifact in enumerate(artifacts):
            lvls[idx] = estimate_lvl(artifact)
            
        return lvls

if __name__ == '__main__':
    artifacts = generate('sands', size=2)
    print(artifacts)
    upgrade_until_max(artifacts, np.array([0, 0]))
    print(artifacts)