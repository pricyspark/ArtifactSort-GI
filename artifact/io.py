import numpy as np
import json
import math
from numpy.typing import NDArray
from typing import Any, cast
from typing import IO
from collections.abc import Collection, Sequence
from .constants import ARTIFACT_DTYPE, SLOT_2_NUM, SET_2_NUM, STAT_2_NUM, SUB_VALUES, STATS, SLOTS, SETS, SLVL_DTYPE
from .upgrades import estimate_upgrades

# TODO: maybe create a special GOOD_artifact TypedDict, but this isn't
# necessary. It's just to make the code more clear

# TODO: make a dataclass or something because the outputs are so long

def artifact_to_dict(artifacts: NDArray[ARTIFACT_DTYPE]) -> dict[str, Any]:
    raise NotImplementedError
    return {}

def dict_to_artifact(
    d: dict[str, Any]
) -> tuple[NDArray[ARTIFACT_DTYPE], NDArray[ARTIFACT_DTYPE], int, int, int, bool, int]:
    artifact = np.zeros(19, dtype=ARTIFACT_DTYPE)
    base_artifact = np.zeros(19, dtype=np.uint8)
    slot = SLOT_2_NUM[d['slotKey']]
    rarity = d['rarity']
    slvl = d['level']
    setKey = SET_2_NUM[d['setKey']]
    main = STAT_2_NUM[d['mainStatKey']]
    if main < 3:
        artifact[main] = 160
        base_artifact[main] = 160
    else:
        artifact[main] = 80
        base_artifact[main] = 80
        
    estimate_num_upgrades: list[int | float] = []
    for substat in d['substats']:
        stat = STAT_2_NUM[substat['key']]
        value = substat['value']
        coef = round(value / SUB_VALUES[stat] * 10)
        artifact[stat] = coef
        
        if 'initialValue' in substat:
            init_value = substat['initialValue']
            init_coef = round(init_value / SUB_VALUES[stat] * 10)
            base_artifact[stat] = init_coef
        else:
            estimate_num_upgrades.append(estimate_upgrades(coef))
    
    for substat in d['unactivatedSubstats']:
        stat = STAT_2_NUM[substat['key']]
        value = substat['value']
        coef = round(value / SUB_VALUES[stat] * 10)
        artifact[stat] = coef
        base_artifact[stat] = coef
        
        slvl -= 4
    
    if estimate_num_upgrades:
        # Assign base_artifact afterwards because there's a chance it
        # estimates < 8 total substats, which is impossible.
        guess = sum(estimate_num_upgrades) + len(d['unactivatedSubstats'])
        for substat, n in zip(d['substats'], estimate_num_upgrades):
            stat = STAT_2_NUM[substat['key']]
            value = substat['value']
            coef = round(value / SUB_VALUES[stat] * 10)
            base_artifact[stat] = round(coef / (math.ceil(n) if guess < 8 else n))
            
        unactivated = max(8, round(guess)) == 8
    else:
        unactivated = d['totalRolls'] == 8 # This is only used for max artifacts, so for now this is enough
    
    return artifact, base_artifact, slot, rarity, slvl, unactivated, setKey

def dicts_to_artifacts(
    dicts: Collection[dict[str, Any]]
) -> tuple[NDArray[ARTIFACT_DTYPE], NDArray[ARTIFACT_DTYPE], NDArray[np.uint8], NDArray[np.uint8], NDArray[SLVL_DTYPE], NDArray[np.bool], NDArray[np.unsignedinteger]]:
    num_dicts = len(dicts)
    artifacts = np.zeros((num_dicts, 19), dtype=ARTIFACT_DTYPE)
    base_artifacts = np.zeros((num_dicts, 19), dtype=ARTIFACT_DTYPE)
    slots = np.zeros(num_dicts, dtype=np.uint8)
    rarities = np.zeros(num_dicts, dtype=np.uint8)
    slvls = np.zeros(num_dicts, dtype=SLVL_DTYPE)
    unactivated = np.zeros(num_dicts, dtype=np.bool)
    sets = np.zeros(num_dicts, dtype=np.uint16)
    
    for i, d in enumerate(dicts):
        artifacts[i], base_artifacts[i], slots[i], rarities[i], slvls[i], unactivated[i], sets[i] = dict_to_artifact(d)
    return artifacts, base_artifacts, slots, rarities, slvls, unactivated, sets

def load(
    filename: str
) -> tuple[dict, NDArray[ARTIFACT_DTYPE], NDArray[ARTIFACT_DTYPE], NDArray[np.uint8], NDArray[np.uint8], NDArray[SLVL_DTYPE], NDArray[np.bool], NDArray[np.unsignedinteger]]:
    with open(filename) as f:
        data = json.load(f)
    
    if data['format'] != 'GOOD' or data['version'] != 3:
        raise ValueError('Only GOODv3 is supported.')
    
    artifact_dict = data['artifacts']
    return artifact_dict, *dicts_to_artifacts(artifact_dict)

def _artifact_eq(a1: dict[str, Any], a2: dict[str, Any]) -> bool:
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

def merge_scans(
    f1: str, 
    f2: str, 
    outfile: IO | None = None
) -> tuple[dict, NDArray[ARTIFACT_DTYPE], NDArray[ARTIFACT_DTYPE], NDArray[np.uint8], NDArray[np.uint8], NDArray[SLVL_DTYPE], NDArray[np.bool], NDArray[np.unsignedinteger]]:
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
    return artifact_dict['artifacts'], *dicts_to_artifacts(artifact_dict['artifacts'])

def print_artifact(
    artifact: NDArray[ARTIFACT_DTYPE], 
    human_readable=True
) -> None:
    if artifact.ndim == 1:
        stats = np.flatnonzero(artifact)
        for stat in stats:
            value = round(cast(float, artifact[stat] * SUB_VALUES[stat] / 10), 2) if human_readable else artifact[stat]
            print(f'{STATS[stat]} {value}')
    else:
        for a in artifact:
            print_artifact(a)
            print()
            
def print_artifact_dict(artifacts: dict[str, Any] | Collection[dict]) -> None:
    if isinstance(artifacts, dict):
        artifacts = [artifacts]
        artifacts = cast(list[dict], artifacts)
        
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
        
def visualize(mask: NDArray[np.bool], artifact_dicts: Sequence[dict]) -> None:
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

def ordered_visualize(
    mask: NDArray[np.bool], 
    artifact_dicts: Sequence[dict]
) -> None:
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