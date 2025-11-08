import numpy as np
from zlib import crc32
from .core import *

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
        return crc32(artifacts.tobytes())
    else:
        output = np.zeros(len(artifacts), dtype=np.int64)
        for idx, artifact in enumerate(artifacts):
            output[idx] = crc32(artifact.flatten().tobytes())
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
    
def next_lvl(lvl):
    if lvl < 0:
        return 8
    else:
        return 4 * ((lvl // 4) + 1)
    
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
    
def sample_upgrade(artifact, samples, num_upgrades=None, slvl=None, rng=None, seed=None):
    if rng is None:
        rng = np.random.default_rng(seed)

    if num_upgrades is None:
        num_upgrades = np.where(slvl < 0, 4, 5 - slvl // 4)
    
    output = np.tile(artifact, (samples, 1))
    if num_upgrades == 0:
        return output, None
    
    tape = np.zeros((samples, num_upgrades), dtype=np.uint8)
    
    if np.count_nonzero(artifact) == 4:
        #print(artifact)
        # Calculate new substat probabilities
        sub_probs = SUB_PROBS.copy()
        sub_probs[np.nonzero(artifact)[0]] = 0
        sub_probs /= np.sum(sub_probs)

        current_subs = find_sub(artifact)
        new_subs = rng.choice(19, p=sub_probs, size=samples)
        #subs = np.hstack((np.tile(current_subs, (samples, 1)), new_subs.reshape((-1, 1))))
        # TODO: see if combining current and new subs together and
        # choosing from each row is faster. Pro: No weird overriding.
        # Con: Creates a 2D array of choices instead of 2 1D arrays.

        # Add the new substats
        rows = np.arange(samples)
        increments = rng.choice(SUB_COEFS, size=samples)
        output[rows, new_subs] += increments
        tape[:, 0] = 4 * new_subs + increments - 7
        
        # Upgrade
        for _ in range(num_upgrades - 1):
            # Assume one of the original 3 substats upgrades
            cols = rng.choice(current_subs, size=samples)
            # Replace the upgraded substat with the new one with 25% chance
            cols = np.where(rng.random(size=samples) < 0.75, cols, new_subs)
            increments = rng.choice(SUB_COEFS, size=samples)
            output[rows, cols] += increments
            tape[:, _ + 1] = 4 * cols + increments - 7
    else:
        subs = find_sub(artifact)
        rows = np.arange(samples)
        for _ in range(num_upgrades):
            cols = rng.choice(subs, size=samples)
            increments = rng.choice(SUB_COEFS, size=samples)
            output[rows, cols] += increments
            tape[:, _] = 4 * cols + increments - 7
    
    return output, tape