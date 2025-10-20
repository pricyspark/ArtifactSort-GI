import numpy as np
from artifact import *
#from rank import *
import math
import time
from targets import *
#from scipy.stats import entropy
import functools
from itertools import combinations, permutations
#import artifact as Artifact
#from artifact import STATS, STAT_2_NUM, MAIN_PROBS, SUB_PROBS, MAIN_VALUES, SUB_VALUES, SUB_COEFS, ARTIFACT_REQ_EXP, UPGRADE_REQ_EXP

def _all_compositions(N, M):
    """Yield all length-N tuples of non-neg ints summing to M."""
    if N == 1:
        yield (M,)
    else:
        for k in range(M+1):
            for rest in _all_compositions(N-1, M-k):
                yield (k,) + rest

def _multinomial_prob(counts, N, M):
    """P(counts) = M! / (∏ counts_i!) * (1/N)^M"""
    num = math.factorial(M)
    denom = 1
    for c in counts:
        denom *= math.factorial(c)
    return num/denom * (1/N)**M

def _distribution(N, M):
    dist = []
    for counts in _all_compositions(N, M):
        dist.append((counts, _multinomial_prob(counts, N, M)))
    return tuple(dist)

def next_lvl(lvl):
    if lvl < 0:
        return 8
    else:
        return 4 * ((lvl // 4) + 1)
    
@functools.lru_cache(maxsize=10)
def _temp(N):
    # start with “zero” sum
    dist = {0: 1.0}
    
    if N == 0:
        return dist

    # convolve N times
    for _ in range(N):
        new_dist = {}
        for s, p_s in dist.items():
            for x in (7, 8, 9, 10):
                new_dist[s + x] = new_dist.get(s + x, 0) + p_s / 4
        dist = new_dist

    # dist now maps each sum → probability
    return dict(sorted(new_dist.items()))

def distro(artifacts, lvls=None, num_upgrades=None):
    """Create a distribution possible max artifacts. If given a single
    artifact, return twin arrays artifacts and probabilities. If given
    multiple artifacts, return twin lists of arrays instead.

    Args:
        artifacts (_type_): _description_
        lvls (_type_): _description_

    Raises:
        ValueError: _description_
        ValueError: _description_

    Returns:
        _type_: _description_
    """
    
    dist = []
    probs = []
    if artifacts.ndim == 1:
        if lvls == 20:
            return artifacts.reshape((1, -1)), np.array([1])
        
        if num_upgrades is None:
            num_upgrades = 5 - lvls // 4
        dist.append(artifacts.copy())
        probs.append(0)
        seed = []
        if np.count_nonzero(artifacts) == 4:
            num_upgrades -= 1
            sub_probs = SUB_PROBS.copy()
            sub_probs[np.nonzero(artifacts)[0]] = 0
            sub_probs /= np.sum(sub_probs)
            for idx in np.where(artifacts == 0)[0]:
                if sub_probs[idx] == 0:
                    continue
                for coef in (7, 8, 9, 10):
                    temp = artifacts.copy()
                    temp[idx] = coef
                    seed.append((temp, sub_probs[idx] / 4))
        else:
            seed.append((artifacts.copy(), 1))
            
        main = find_main(artifacts)
        upgrades = _distribution(4, num_upgrades)
        for artifact, prob in seed:
            for upgrade, upgrade_prob in upgrades:
                substats = find_sub(artifact, main)
                # TODO: make this not disgusting                
                for first, first_prob in _temp(upgrade[0]).items():
                    first_temp = artifact.copy()
                    first_temp[substats[0]] += first
                    for second, second_prob in _temp(upgrade[1]).items():
                        second_temp = first_temp.copy()
                        second_temp[substats[1]] += second
                        for third, third_prob in _temp(upgrade[2]).items():
                            third_temp = second_temp.copy()
                            third_temp[substats[2]] += third
                            for fourth, fourth_prob in _temp(upgrade[3]).items():
                                fourth_temp = third_temp.copy()
                                fourth_temp[substats[3]] += fourth
                                dist.append(fourth_temp)
                                probs.append(prob * upgrade_prob * first_prob * second_prob * third_prob * fourth_prob)
                                
        dist = np.array(dist, dtype=np.uint8)
        probs = np.array(probs)
    else:
        try:
            _ = iter(lvls)
        except:
            lvls = np.full(len(artifacts), lvls)
        
        for artifact, lvl in zip(artifacts, lvls):
            temp_dist, temp_probs = distro(artifact, lvls=lvl)
            dist.append(temp_dist)
            probs.append(temp_probs)

    return dist, probs

def single_distro(artifacts):
    if artifacts.ndim == 1:
        # Rename to "artifact" to make things less confusing
        artifact = artifacts
        # TODO: clean this shit up
        if np.count_nonzero(artifact) == 4:
            sub_probs = SUB_PROBS.copy()
            sub_probs[np.nonzero(artifact)[0]] = 0
            sub_probs /= np.sum(sub_probs)
            
            num_possibilities = np.count_nonzero(sub_probs) * 4
            dist = np.tile(artifact, (num_possibilities + 1, 1))
            probs = np.zeros((num_possibilities + 1), dtype=float)
            
            dist = np.tile(artifact, (num_possibilities + 1, 1))
            
            nz_mask = sub_probs != 0
            nz_idx  = np.nonzero(nz_mask)[0]           # shape (M,)
            M       = nz_idx.size

            # 2. build row and column indices for dist update
            #    rows: for each i in [0..M-1], rows = 1 + 4*i + [0,1,2,3]
            i = np.arange(M)
            j = np.arange(4, dtype=np.uint8)
            rows = 1 + 4*i[:, None] + j               # shape (M,4)
            cols = nz_idx[:, None]                    # shape (M,1)

            # 3. add j+7 to dist at those positions in one shot
            dist[rows, cols] += (j + 7)               # broadcasts to (M,4)
            probs[1:] = np.repeat(sub_probs[sub_probs != 0], 4) / 4
            
        else:
            dist = np.tile(artifact, (17, 1))
            probs = np.full(17, 1/16, dtype=float)
            probs[0] = 0
            
            nz_idx  = find_sub(artifact)           # shape (M,)
            M       = nz_idx.size

            # 2. build row and column indices for dist update
            #    rows: for each i in [0..M-1], rows = 1 + 4*i + [0,1,2,3]
            i = np.arange(M)
            j = np.arange(4, dtype=np.uint8)
            rows = 1 + 4*i[:, None] + j               # shape (M,4)
            cols = nz_idx[:, None]                    # shape (M,1)

            # 3. add j+7 to dist at those positions in one shot
            dist[rows, cols] += (j + 7)               # broadcasts to (M,4)
    else:
        dist = []
        probs = []
        for artifact in artifacts:
            temp_dist, temp_probs = single_distro(artifact)
            dist.append(temp_dist)
            probs.append(temp_probs)
            
    return dist, probs

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
    '''
    else:
        output = np.tile(artifact, (samples, 1))
        for _ in range(num_upgrades):
            upgrade(output, rng=rng)

        return output
    '''
    
def base_artifact_probs(slot):
    main_probs = MAIN_PROBS[slot]
    M = main_probs.size

    # Precompute the 24 permutations of positions [0,1,2,3]
    perms = np.array(list(permutations(range(4))), dtype=int)  # (24,4)

    all_mains = []
    all_subs  = []
    all_probs = []

    zero_subs = None
    zero_probs = None

    for main in range(M):
        main_p = main_probs[main]
        
        if main_p <= 0:
            continue

        # Substats are the same for all main stats >= 10
        if main >= 10:
            # Check cache
            if zero_subs is None:
                # Miss
                cand = np.arange(10)
            else:
                # Hit
                all_mains.append(np.full(C, main, dtype=int))
                all_subs.append(zero_subs)
                all_probs.append(zero_probs)
                continue
        else:
            cand = np.delete(np.arange(10), main)
            
        w = SUB_PROBS[cand].astype(float)
        total = w.sum()

        # All 4-combinations of candidate indices (indices into cand)
        comb_idx = np.array(list(combinations(np.arange(cand.size), 4)), dtype=int)  # (C,4)
        C = comb_idx.shape[0]

        # Weights for each combination, shape (C,4)
        w_sel = w[comb_idx]  # (C,4)

        # Reorder the 4 chosen weights along the 24 permutations: (C,24,4)
        w_perm = w_sel[:, perms]  # advanced indexing -> (C,24,4)

        # Denominators per step: total - exclusive cumsum of chosen weights
        # exclusive cumsum: cs_excl[..., k] = sum of previous weights (k terms)
        cs = np.cumsum(w_perm, axis=-1)                # (C,24,4)
        cs_excl = cs - w_perm                           # exclusive
        denoms = total - cs_excl                        # (C,24,4)

        # Order probability for each perm: prod_k w_perm[...,k] / denoms[...,k]
        with np.errstate(divide='ignore', invalid='ignore'):
            ratios = np.where(denoms > 0, w_perm / denoms, 0.0)
            p_order = np.prod(ratios, axis=-1)         # (C,24)

        # Unordered subset prob = sum over the 24 orders
        p_subset = p_order.sum(axis=1)                 # (C,)

        # Map back to original stat indices for the subset
        subs = cand[comb_idx]                          # (C,4)
        subs.sort(axis=1)                              # keep canonical order

        # Multiply by main probability
        probs = main_p * p_subset

        all_mains.append(np.full(C, main, dtype=int))
        all_subs.append(subs)
        all_probs.append(probs)
        if main >= 10:
            zero_subs = subs
            zero_probs = probs

    mains = np.concatenate(all_mains, axis=0)
    subs  = np.vstack(all_subs)
    probs = np.concatenate(all_probs, axis=0)
    
    return mains, subs, probs

def base_artifact_useful_probs(slot, targets):
    useless_idx = np.where(targets == 0)[0]
    mains, subs, probs = base_artifact_probs(slot)
    
    if not useless_idx:
        return mains, subs, probs
    
    combine = np.concatenate([mains[:, None], subs], axis=1)

    # Mark useless substats as -1
    if useless_idx.size:
        mask = np.isin(combine, useless_idx)
        combine[mask] = -1
        
    uniq, inv = np.unique(combine, axis=0, return_inverse=True)
    probs_out = np.bincount(inv, weights=probs)

    mains_out = uniq[:, 0].astype(int)
    subs_out  = uniq[:, 1:].astype(int)

    return mains_out, subs_out, probs_out

    
def avg(distribution, probs, targets, scores=None) -> float:
    """Find distribution's score average.

    Args:
        distribution (_type_): _description_
        probs (_type_): _description_
        targets (_type_): _description_
        scores (_type_, optional): _description_. Defaults to None.

    Returns:
        _type_: _description_
    """
    
    if scores is None:
        scores = score(distribution, targets)
    return scores @ probs

def second_moment(distribution, probs, targets, scores=None) -> float:
    """Find distribution's score second moment.

    Args:
        distribution (_type_): _description_
        probs (_type_): _description_
        targets (_type_): _description_
        scores (_type_, optional): _description_. Defaults to None.

    Returns:
        _type_: _description_
    """
    
    if scores is None:
        scores = score(distribution, targets)
    return scores**2 @ probs

def variance(distribution, probs, targets, scores=None, mean=None) -> float:
    """Find distribution's score variance.

    Args:
        distribution (_type_): _description_
        probs (_type_): _description_
        targets (_type_): _description_
        scores (_type_, optional): _description_. Defaults to None.
        mean (_type_, optional): _description_. Defaults to None.

    Returns:
        _type_: _description_
    """
    if scores is None:
        scores = score(distribution, targets)
    if mean is None:
        mean = avg(distribution, probs, targets, scores)
        
    return (scores - mean)**2 @ probs

def std(distribution, probs, targets, scores=None, mean=None) -> float:
    """Find distribution's score standard deviation.

    Args:
        distribution (_type_): _description_
        probs (_type_): _description_
        targets (_type_): _description_
        scores (_type_, optional): _description_. Defaults to None.
        mean (_type_, optional): _description_. Defaults to None.

    Returns:
        float: _description_
    """
    return np.sqrt(variance(distribution, probs, targets, scores, mean))

def vectorize(targets: dict):
    """Convert a target dictionary to a target array.

    Args:
        targets (dict): Mapping from stat to weight. Weights must be
        ints, or they will be cast.

    Returns:
        NDArray: Array of stat weights.
    """
    
    output = np.zeros(19, dtype=np.uint32)
    for target, value in targets.items():
        if target == 'crit_':
            output[8] = value
            output[9] = value
            continue

        output[STAT_2_NUM[target]] = value

    return output

def score(artifacts, targets):
    """Calculate scores. If given a single artifact, returns a scalar.
    If ggiven multiple artifacts, returns an array.

    Args:
        artifacts (_type_): _description_
        targets (_type_): _description_

    Returns:
        _type_: _description_
    """
    
    # TODO: additionally put vectorization to caller functions so this
    # doesn't repeat
    if type(targets) == dict:
        targets = vectorize(targets)
        
    return artifacts @ targets

def simulate_exp(artifacts, slvls, targets, fun, num=1, mains=None):
    # TODO: check if anything is maxed. They shouldn't be
    # TODO: add benchmark for how long it takes to acheive top 1%, not
    # just top 1
    match targets:
        case dict():
            targets = vectorize(targets).reshape((1, -1))
        case np.ndarray():
            if targets.ndim == 1:
                targets = targets.reshape((1, -1))    
        case _:
            temp = np.zeros((len(targets), 19), dtype=np.uint32)
            for i, target in enumerate(targets):
                temp[i] = vectorize(target)
            targets = temp
    
    original_artifacts = artifacts.copy()
    smart_upgrade_until_max(artifacts, slvls)
    
    if type(targets) == dict or (type(targets) == np.ndarray and targets.ndim == 1):
        scores = score(artifacts, targets)
        goal = np.argmax(scores)
        goal_scores = scores[goal]
    else:
        goal = np.zeros(len(targets), dtype=int)
        goal_scores = np.zeros(len(targets), dtype=float)
        for i, target in enumerate(targets):
            scores = score(artifacts, target)
            goal[i] = np.argmax(scores)
            goal_scores[i] = scores[goal[i]]
    
    print('goal:', goal)
    print('score:', goal_scores)
    print_artifact(artifacts[goal])
    print()
    '''
    '''
    artifacts = original_artifacts.copy()
    #distros = distro(artifacts, lvls)
    persist = {}
    
    exp = 0
    
    target_scores = score(artifacts, targets.T) # (N,U)
    start_maxes = np.max(target_scores, axis=0) # (U,)
    target_maxes = start_maxes.copy()           # (U,)
    score_ranges = goal_scores - start_maxes
    
    #while np.any(lvls[goal] != 20):
    while np.any(target_maxes < goal_scores):
        chosen = fun(artifacts, slvls, persist, targets)
        try:
            _ = iter(chosen)
            relevance = chosen
            relevance[slvls == 20] = -9999999999
            #chosen = np.argmax(relevance)
            chosen = np.argpartition(relevance, -num)[-num:]
        except:
            chosen = np.array([chosen])
            
        for idx in chosen:
            if slvls[idx] == 20:
                raise ValueError('Attempted to upgrade maxed artifact')
            #print_artifact(artifacts[idx])
            
            # Upgrade
            smart_upgrade(artifacts[idx])
            exp += UPGRADE_REQ_EXP[slvls[idx]]
            slvls[idx] = next_lvl(slvls[idx])
            #distros[0][idx], distros[1][idx] = distro(artifacts[idx], lvls[idx])
            
            print(exp)
            
        new_scores = score(artifacts[chosen], targets.T) # (n,U)
        new_maxes = np.max(new_scores, axis=0)  # (U,)
        target_maxes = np.maximum(target_maxes, new_maxes)
            
        persist['changed'] += list(chosen)
        print((target_maxes - start_maxes) / score_ranges)
        
        reshuffle = np.random.choice(np.arange(len(artifacts))[slvls != 20], size=num, replace=False)
        persist['changed'] += list(reshuffle)
            
    #print(np.histogram(slvls, bins=7)[0])
    return exp

def rate(artifacts, slots, rarities, lvls, sets, ranker, k=1, num=None, threshold=None):
    # TODO: change persist to persist_artifact and persist_meta, for
    # more intuitive control over things like set masking
    relevance = np.zeros((len(artifacts), 5 * (1 + len(SETS))), dtype=float)
    count = 0
    for slot in range(5):
        # TODO: this won't work if there's 0 artifacts
        slot_mask = np.logical_and(rarities == 5, slots == slot)
        original_idxs = np.where(slot_mask)[0]
        slot_artifacts = artifacts[slot_mask]
        slot_lvls = lvls[slot_mask]
        persist = {}
        relevance[original_idxs, count] = ranker(slot_artifacts, slot_lvls, persist, ALL_TARGETS[SLOTS[slot]], k=2 * k)
        count += 1
        
        for setKey in range(len(SETS)):
            set_mask = sets[slot_mask] == setKey
            if np.all(set_mask == 0):
                continue
            #new_mask = np.logical_and(mask, sets == setKey)
            original_idxs = np.where(slot_mask)[0][set_mask]
            set_artifacts = slot_artifacts[set_mask]
            set_lvls = slot_lvls[set_mask]
            set_persist = {}
            for a, b in persist.items():
                try:
                    #temp = asdf[set_mask]
                    if type(b) == np.ndarray:
                        temp = b[set_mask]
                    else:
                        temp = [val for val, m in zip(b, set_mask) if m]
                    set_persist[a] = temp
                    #set_persist.append(temp)
                except Exception as e:
                    set_persist[a] = b
                    #set_persist.append(None)
            #set_persist = [asdf[np.where(set_mask)[0]] for asdf in persist]
            relevance[original_idxs, count] = ranker(set_artifacts, set_lvls, set_persist, SET_TARGETS[SETS[setKey]][SLOTS[slot]], k=k)
            count += 1
    
    max_relevance = np.max(relevance, axis=1)
    #max_relevance[lvls == 20] = 999999
    max_relevance[rarities != 5] = 999999
    if threshold is None:
        relevances = np.sort(max_relevance)
        threshold = relevances[num - 1]
        print(threshold * 270275 * 100)
    #relevant = np.logical_or(lvls == 20, max_relevance > threshold)
    relevant = max_relevance > threshold
    return relevant

def visualize(mask, artifact_dicts, sort=False):
    unactivated = []
    lvls = []
    slots = []
    sets = []
    for artifact in artifact_dicts:
        unactivated.append(bool(artifact['unactivatedSubstats']))
        lvls.append(artifact['level'])
        slots.append(SLOT_2_NUM[artifact['slotKey']])
        sets.append(SET_2_NUM[artifact['setKey']])
        
    if sort:
        sorted_idx = sorted(range(len(artifact_dicts)), key=lambda i: (-lvls[i], -sets[i], slots[i], unactivated[i]))
        mask = mask[sorted_idx]
        artifact_dicts = [artifact_dicts[i] for i in sorted_idx]
        lvls = [lvls[i] for i in sorted_idx]
        slots = [slots[i] for i in sorted_idx]
        sets = [sets[i] for i in sorted_idx]
    
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