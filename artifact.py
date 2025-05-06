import numpy as np
import copy
import zlib

STATS = (
    'hp', 'atk', 'def', 'hp_', 'atk_', 'def_', 'enerRech_', 'eleMas', 
    'critRate_', 'critDMG_', 'pyro_dmg_', 'electro_dmg_', 'cryo_dmg_', 
    'hydro_dmg_', 'dendro_dmg_', 'anemo_dmg_', 'geo_dmg_', 'physical_dmg_', 
    'heal_'
)

STAT_2_NUM = {stat: index for index, stat in enumerate(STATS)}

MAIN_PROBS = {
    'flower':  (1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'plume':   (0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'sands':   (0, 0, 0, 8/30, 8/30, 8/30, 3/30, 3/30, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'goblet':  (0, 0, 0, 77/400, 77/400, 76/400, 0, 10/400, 0, 0, 20/400, 20/400, 20/400, 20/400, 20/400, 20/400, 20/400, 20/400, 0),
    'circlet': (0, 0, 0, 11/50, 11/50, 11/50, 0, 2/50, 5/50, 5/50, 0, 0, 0, 0, 0, 0, 0, 0, 5/50)
}

SUB_PROBS = np.array((6, 6, 6, 4, 4, 4, 4, 4, 3, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0), dtype=float)

MAIN_VALUES = ( 4780, 311, -1, 46.6, 46.6, 58.3, 51.8, 186.5, 31.1, 62.2, 
                46.6, 46.6, 46.6, 46.6, 46.6, 46.6, 46.6, 58.3, 34.9)
SUB_VALUES = (  298.75, 19.45, 23.13, 5.83, 5.83, 7.29, 6.48, 23.31, 3.89, 7.77, 
                0, 0, 0, 0, 0, 0, 0, 0, 0)

SUB_COEFS = np.array((21, 24, 27, 30), dtype=np.uint8)

ARTIFACT_REQ_EXP = (
    0, 3000, 6725, 11150, 16300, 22200, 28875, 36375, 44725, 53950, 
    64075, 75125, 87150, 100175, 115325, 132925, 153300, 176800, 203850, 234900, 
    270475
)

UPGRADE_REQ_EXP = (
    16300, 13300, 9575, 5150, 28425, 22525, 15850, 8350, 42425, 33200, 
    23075, 12025, 66150, 53125, 37975, 20375, 117175, 93675, 66625, 35575, 0
) # TODO: check this

def _find_main(artifact):
    mask = artifact == 160
    if np.any(mask):
        return np.where(mask == True)[0][0]
    else:
        return np.where(artifact == 240)[0][0]

def generate(slot, main=None, lvls=None, source='domain', size=None, seed=None):
    try:
        _ = iter(lvls)
        lvls = np.array(lvls)
        size = len(lvls)
    except:
        if size is None:
            size = 1
        if lvls is None:
            lvls = 0
        lvls = np.full(size, lvls)
        
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
    
    for idx, lvl in enumerate(lvls):
        # Figure out num_upgrades and num_substats for each artifact
        num_upgrades = lvl // 4
        num_substats = 4
        if rng.random() > prob:
            if num_upgrades == 0:
                num_substats -= 1
            else:
                num_upgrades -= 1
                
        # Figure out main stat
        main = rng.choice(19, p=MAIN_PROBS[slot])
        if main < 3:
            output[idx, main] = 160
        else:
            output[idx, main] = 240
            
        # Figure out unique substats
        sub_probs = SUB_PROBS.copy()
        sub_probs[main] = 0
        sub_probs /= np.sum(sub_probs)
        substats = rng.choice(19, size=num_substats, replace=False, p=sub_probs)
        for substat in substats:
            output[idx, substat] += rng.choice(SUB_COEFS)
            
        # Upgrade substats
        upgrades = rng.choice(4, size=num_upgrades, replace=True)
        for upgrade in upgrades:
            output[idx, substats[upgrade]] += rng.choice(SUB_COEFS)
            
    return output

def print_artifact(artifacts) -> None:
    if artifacts.ndim == 1:
        stats = np.nonzero(artifacts)[0]
        for stat in stats:
            print(STATS[stat], artifacts[stat])
    else:
        for artifact in artifacts:
            print_artifact(artifact)
            print()

def _upgrade_helper(artifact, rng):
    main = _find_main(artifact)
    
    sub_probs = SUB_PROBS.copy()
    sub_probs[main] = 0
    if np.count_nonzero(artifact) == 4:
        for idx in np.nonzero(artifact):
            sub_probs[idx] = 0
        sub_probs /= np.sum(sub_probs)
        artifact[rng.choice(19, p=sub_probs)] = rng.choice(SUB_COEFS)
    else:
        temp = artifact[main]
        artifact[main] = 0
        artifact[rng.choice(np.nonzero(artifact)[0])] += rng.choice(SUB_COEFS)
        artifact[main] = temp

def upgrade(artifacts, mains=None, seed=None):
    # TODO: add mains optional param
    
    rng = np.random.default_rng(seed)
    if artifacts.ndim == 1:
        _upgrade_helper(artifacts, rng)
    else:
        for artifact in artifacts:
            _upgrade_helper(artifact, rng)

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
        rng = np.random.default_rng(_smart_seed(artifacts))
        _upgrade_helper(artifacts, rng)
    else:
        seeds = _smart_seed(artifacts)
        for artifact, seed in zip(artifacts, seeds):
            rng = np.random.default_rng(seed)
            _upgrade_helper(artifact, rng)
            
def smart_upgrade_until_max(artifacts, lvls, mains=None): # TODO: this is code duplication
    num_upgrades = 5 - lvls // 4
    
    if artifacts.ndim == 1 or len(artifacts) == 1:
        for _ in range(num_upgrades):
            smart_upgrade(artifacts, mains)
    else:
        if mains is None:
            mains = [None] * len(lvls)
        for artifact, lvl, main in zip(artifacts, num_upgrades, mains):
            for _ in range(lvl):
                smart_upgrade(artifact, main)
    
def upgrade_until_max(artifacts, lvls, mains=None, seed=None):
    num_upgrades = 5 - lvls // 4
    
    if artifacts.ndim == 1 or len(artifacts) == 1:
        for _ in range(num_upgrades):
            upgrade(artifacts, mains, seed)
    else:
        if mains is None:
            mains = [None] * len(lvls)
        for artifact, lvl, main in zip(artifacts, num_upgrades, mains):
            for _ in range(lvl):
                upgrade(artifact, main, seed) # TODO seed generator, otherwise they all get the same seed

if __name__ == '__main__':
    artifacts = generate('sands', size=2)
    print(artifacts)
    upgrade_until_max(artifacts, np.array([0, 0]))
    print(artifacts)