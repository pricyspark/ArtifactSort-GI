import numpy as np
from artifact import *
#from rank import *
import math
import time
from targets import *
#from scipy.stats import entropy
import functools
from itertools import product
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

def sample_upgrade(artifact, samples, num_upgrades=None, lvl=None, rng=None, seed=None):
    if rng is None:
        rng = np.random.default_rng(seed)

    if num_upgrades is None:
        num_upgrades = 5 - (lvl // 4)
    
    output = np.tile(artifact, (samples, 1))
    if num_upgrades == 0:
        return output
    
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
        
        # Upgrade
        for _ in range(num_upgrades - 1):
            # Assume one of the original 3 substats upgrades
            cols = rng.choice(current_subs, size=samples)
            # Replace the upgraded substat with the new one with 25% chance
            cols = np.where(rng.random(size=samples) < 0.75, cols, new_subs)
            increments = rng.choice(SUB_COEFS, size=samples)
            output[rows, cols] += increments
        return output
    else:
        subs = find_sub(artifact)
        rows = np.arange(samples)
        for _ in range(num_upgrades):
            cols = rng.choice(subs, size=samples)
            increments = rng.choice(SUB_COEFS, size=samples)
            output[rows, cols] += increments
        return output
    '''
    else:
        output = np.tile(artifact, (samples, 1))
        for _ in range(num_upgrades):
            upgrade(output, rng=rng)

        return output
    '''

    
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

def simulate_exp(artifacts, lvls, targets, fun, num=1, mains=None):
    # TODO: check if anything is maxed. They shouldn't be
    # TODO: add benchmark for how long it takes to acheive top 1%, not
    # just top 1
    original_artifacts = artifacts.copy()
    smart_upgrade_until_max(artifacts, lvls)
    
    if type(targets) == dict or (type(targets) == np.ndarray and targets.ndim == 1):
        scores = score(artifacts, targets)
        goal = np.argmax(scores)
    else:
        goal = np.zeros(len(targets), dtype=int)
        for i, target in enumerate(targets):
            scores = score(artifacts, target)
            goal[i] = np.argmax(scores)
    
    print('goal:', goal)
    print_artifact(artifacts[goal])
    print()
    artifacts = original_artifacts.copy()
    #distros = distro(artifacts, lvls)
    persist = {}
    
    exp = 0
    
    while np.any(lvls[goal] != 20):
        chosen = fun(artifacts, lvls, persist, targets)
        try:
            _ = iter(chosen)
            relevance = chosen
            relevance[lvls == 20] = 0
            #chosen = np.argmax(relevance)
            chosen = np.argpartition(relevance, -num)[-num:]
        except:
            chosen = [chosen]
            
        for idx in chosen:
            if lvls[idx] == 20:
                raise ValueError
            #print_artifact(artifacts[idx])
            smart_upgrade(artifacts[idx])
            exp += UPGRADE_REQ_EXP[lvls[idx]]
            lvls[idx] = next_lvl(lvls[idx])
            #distros[0][idx], distros[1][idx] = distro(artifacts[idx], lvls[idx])
            print(exp)
            
        persist['changed'] = chosen
            
    return exp

def upper_bound(artifacts, lvls, targets):
    scores = score(artifacts, targets)
    scores[lvls == 20] = 0
    return np.argmax(scores)
        
def create_dataset(num_queries, slot, lvls, targets, source='domain', size=None, num_trials=1000, seed=None):
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
    
    num_artifacts = len(lvls)
    avgs = np.zeros(num_queries * num_artifacts, dtype=float)
    second_moments = np.zeros(num_queries * num_artifacts, dtype=float)
    variances = np.zeros(num_queries * num_artifacts, dtype=float)
    relevance = np.zeros(num_queries * num_artifacts, dtype=float)
    # TODO: this is temp. other_relevance is a counter. Increment if
    # it's the max for a trial.
    other_relevance = np.zeros(num_queries * num_artifacts, dtype=float)
    artifacts = np.zeros((num_queries * num_artifacts, 19), dtype=np.uint8)
    RNG = np.random.default_rng(seed)
    for query in range(num_queries):
        this_slice = slice(query * num_artifacts, (query + 1) * num_artifacts)
        artifacts[this_slice] = generate(slot, lvls=lvls, source=source, rng=RNG)
        distributions, probs = distro(artifacts[this_slice], lvls=lvls)
        
        for i, (distribution, prob) in enumerate(zip(distributions, probs)):
            scores = score(distribution, targets)
            #avgs[this_slice][i] = scores @ prob
            mean = avg(None, prob, None, scores)
            second_m = second_moment(None, prob, None, scores)
            var = variance(None, prob, None, scores, mean)
            
            avgs[this_slice][i] = mean
            second_moments[this_slice][i] = second_m
            variances[this_slice][i] = var
        
        for _ in range(num_trials):
            maxed = np.zeros((num_artifacts, 19), dtype=np.uint8)
            for i in range(num_artifacts):
                maxed[i] = RNG.choice(distributions[i], p=probs[i])
            final_scores = score(maxed, targets)
            order = np.argsort(np.argsort(final_scores))
            relevance[this_slice] += order / num_trials
            best = np.argmax(final_scores)
            other_relevance[this_slice][best] += 1
        #scores = relevance[this_slice]
        #order = np.argsort(np.argsort(scores))
        #relevance[this_slice] = order - len(order) + 32
    
    lvls = np.tile(lvls, num_queries).reshape((-1, 1))
    avgs = avgs.reshape((-1, 1))
    second_moments = second_moments.reshape((-1, 1))
    variances = variances.reshape((-1, 1))
    
    metadata = np.column_stack((lvls, avgs, second_moments, variances))
    x = np.append(artifacts, metadata, axis=1)
    #x = np.append(x, avgs, axis=1)
    #x = np.append(x, second_moments, axis=1)
    #x = np.append(x, variances, axis=1)
    
    relevance = np.append(relevance.reshape((-1, 1)), other_relevance.reshape((-1, 1)), axis=1)
    
    #relevance[relevance < 0] = 0
    qid = np.repeat(np.arange(num_queries), size)
    
    return x, relevance, qid

def choose_samples(x, y, qid):
    current = -1
    idxs = []
    for idx, (artifact, relevance, query) in enumerate(zip(x, y, qid)):
        if current != query and relevance == 0:
            current = query
            idxs.append(idx)
        if relevance != 0:
            idxs.append(idx)
            
    return x[idxs], y[idxs], qid[idxs]

def rate(artifacts, slots, rarities, lvls, sets, ranker, num=None, threshold=None):
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
        relevance[original_idxs, count] = ranker(slot_artifacts, slot_lvls, persist, ALL_TARGETS[SLOTS[slot]], num_trials=1000)
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
            relevance[original_idxs, count] = ranker(set_artifacts, set_lvls, set_persist, SET_TARGETS[SETS[setKey]][SLOTS[slot]], num_trials=1000)
            count += 1
    
    max_relevance = np.max(relevance, axis=1)
    #max_relevance[lvls == 20] = 999999
    max_relevance[rarities != 5] = 999999
    if threshold is None:
        relevances = np.sort(max_relevance)
        threshold = relevances[num - 1]
        print(threshold)
    #relevant = np.logical_or(lvls == 20, max_relevance > threshold)
    relevant = max_relevance > threshold
    return relevant

def visualize(mask, artifacts, slots, sets, lvls):
    rows = [(mask[i:i+8], artifacts[i:i+8], slots[i:i+8], sets[i:i+8], lvls[i:i+8]) for i in range(0, len(mask), 8)]
    
    # TODO: this only works if there are more than 8 artifacts, so the
    # first row is filled
    # Border
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
                print(f'{STATS[find_main(row[1][idx])][:8]:<8}|', end='')
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
                    subs = find_sub(row[1][idx])
                    try:
                        print(f'{STATS[subs[sub_idx]][:8]:<8}|', end='')
                    except:
                        print('        |', end='')    
            print()    
            
        # Border
        print('+', end='')
        for _ in range(len(row[0])):
            print('--------+', end='')
        print()