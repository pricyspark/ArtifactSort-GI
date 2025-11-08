import numpy as np
import json
import math
from .constants import *

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
        
def visualize(mask, artifact_dicts):
    unactivated = []
    lvls = []
    slots = []
    sets = []
    for artifact in artifact_dicts:
        unactivated.append(bool(artifact['unactivatedSubstats']))
        lvls.append(artifact['level'])
        slots.append(SLOT_2_NUM[artifact['slotKey']])
        sets.append(SET_2_NUM[artifact['setKey']])
        
    sorted_idx = sorted(range(len(artifact_dicts)), key=lambda i: (-lvls[i], -sets[i], slots[i], unactivated[i]))
    mask = mask[sorted_idx]
    artifact_dicts = [artifact_dicts[i] for i in sorted_idx]
    lvls = [lvls[i] for i in sorted_idx]
    slots = [slots[i] for i in sorted_idx]
    sets = [sets[i] for i in sorted_idx]
    
    # Ignore properly locked artifacts
    for i, artifact in enumerate(artifact_dicts):
        mask[i] = artifact['lock'] == mask[i]
    
    for masked, artifact in zip(mask, artifact_dicts):
        if not masked:
            print_artifact_dict(artifact)
            print()

def ordered_visualize(mask, artifact_dicts):
    unactivated = []
    lvls = []
    slots = []
    sets = []
    for artifact in artifact_dicts:
        unactivated.append(bool(artifact['unactivatedSubstats']))
        lvls.append(artifact['level'])
        slots.append(SLOT_2_NUM[artifact['slotKey']])
        sets.append(SET_2_NUM[artifact['setKey']])
       
    # Ignore properly locked artifacts
    for i, artifact in enumerate(artifact_dicts):
        mask[i] = artifact['lock'] == mask[i]
            
    rows = [(mask[i:i+8], artifact_dicts[i:i+8], slots[i:i+8], sets[i:i+8], lvls[i:i+8]) for i in range(0, len(mask), 8)]
    
    print('+', end='')
    for _ in range(8):
        print('--------+', end='')
    print()
    
    for row in rows: 
        # Slot
        print('|', end='')
        for idx in range(len(row[0])):
            if row[0][idx]:
                print('        |', end='')
            else:
                print(f'{SLOTS[row[2][idx]]:<8}|', end='')
        print()
        
        # LVL
        print('|', end='')
        for idx in range(len(row[0])):
            if row[0][idx]:
                print('        |', end='')
            else:
                print(f'LVL: {str(row[4][idx]):<3}|', end='')
        print()
        
        # Set
        print('|', end='')
        for idx in range(len(row[0])):
            if row[0][idx]:
                print('        |', end='')
            else:
                print(f'{SETS[row[3][idx]][:8]:<8}|', end='')
        print()
        
        # Main stat
        print('|', end='')
        for idx in range(len(row[0])):
            if row[0][idx]:
                print('        |', end='')
            else:
                print(f'{row[1][idx]['mainStatKey'][:8]:<8}|', end='')
        print()
        
        # Space
        print('|', end='')
        for _ in range(len(row[0])):
            print('        |', end='')
        print()
        
        # Substats
        for sub_idx in range(4):
            print('|', end='')
            for idx in range(len(row[0])):
                if row[0][idx]:
                    print('        |', end='')
                else:
                    try:
                        sub = row[1][idx]['substats'][sub_idx]['key']
                        print(f'{sub[:8]:<8}|', end='')
                    except IndexError:
                        sub = row[1][idx]['unactivatedSubstats'][0]['key']
                        print(f'*{sub[:7]:<7}|', end='')
            print()    
            
        # Border
        print('+', end='')
        for _ in range(len(row[0])):
            print('--------+', end='')
        print()