import numpy as np
from artifact import *
import math
import time
from targets import *
import functools
from itertools import product, combinations, permutations

CACHE_SIZE = 1000 # TODO: tune for percentile, especially more complex targets

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

@functools.lru_cache(maxsize=CACHE_SIZE)
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
            
        w = SUB_PROBS[cand]
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

def base_artifact_useful_probs(mains, subs, probs, target):
    useless_idx = np.where(target == 0)[0]
    
    if len(useless_idx) == 0:
        return mains, subs, probs

    # Mark useless substats as -1
    combine = np.column_stack((mains, subs))
    np.putmask(combine, np.isin(combine, useless_idx), -1)
        
    v = combine[:, 1:]
    v.sort(axis=1)
        
    uniq, inv = np.unique(combine, axis=0, return_inverse=True)
    probs_out = np.bincount(inv, weights=probs)

    mains_out = uniq[:, 0].astype(int)
    subs_out  = uniq[:, 1:].astype(int)

    return mains_out, subs_out, probs_out

def artifact_percentile(slot, target, threshold, lvl):
    # Nest function so arrays are enclosing variables instead of
    # parameters, this allows easier caching
    @functools.lru_cache(maxsize=CACHE_SIZE)
    def _percentile_helper(diff, num_upgrades):
        if diff < 0:
            return 0.2 if num_upgrades == 0 else 1
        
        if num_upgrades == 0: # This isn't necessary, but might speed things up
            return 0

        upper_bound = max_weight * 10 * num_upgrades
        if diff >= upper_bound:
            return 0
            
        output = 0
        for sub in s:
            for coef in (10, 9, 8, 7):
                temp_diff = diff - coef * new_target[sub]
                temp_prob = _percentile_helper(temp_diff, num_upgrades - 1)
                if temp_prob == 0:
                    break
                output += temp_prob

        return output / 16
    
    if lvl < 0:
        raise ValueError('Invalid artifact level')
    
    mains, subs, probs = base_artifact_probs(slot)
    mains, subs, probs = base_artifact_useful_probs(mains, subs, probs, target)

    num_upgrades = lvl // 4
    new_target = np.append(target, 0)
    
    output = 0
    for m, s, p in zip(mains, subs, probs):
        diff = threshold - new_target[m] * (160 if m < 3 else 80)
        num_useful = np.count_nonzero(s != -1)
        num_useless = 4 - num_useful
        max_weight = np.max(new_target[s])
        for coefs in product((7, 8, 9, 10), repeat=num_useful):
            coefs = [0] * num_useless + list(coefs)
            temp_diff = diff
            for sub, coef in zip(s, coefs):
                temp_diff -= coef * new_target[sub]
                
            output += p * _percentile_helper(temp_diff, num_upgrades) / 4 ** num_useful

        _percentile_helper.cache_clear()

    return output

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

def reshape_percentile(base, target, threshold, unactivated, minimum=2):
    # TODO: This is copy-pasted from define. Find a more elegant solution
    @functools.lru_cache(maxsize=CACHE_SIZE)
    def _reshape_helper(diff, num_good, num_upgrades):
        if num_good + num_upgrades < minimum:
            return None
        
        if diff < 0 and num_good >= minimum:
            return 1
        
        if num_upgrades == 0:
            return 0
        
        upper_bound = max_weight * 10 * num_upgrades
        if diff >= upper_bound:
            return 0
        
        output = 0
        for sub in subs:
            temp_num_good = num_good + 1 if sub in best_subs else num_good
            for coef in (10, 9, 8, 7):
                temp_diff = diff - coef * target[sub]
                temp_prob = _reshape_helper(temp_diff, temp_num_good, num_upgrades - 1)
                if temp_prob is None:
                    break
                
                output += temp_prob
                
        return output / 16
    
    prob_valid = 0
    if unactivated:
        # Probability 3-stat has minimum good rolls
        temp = 0
        for i in range(5 - minimum):
            temp += math.comb(4, i)
        prob_valid += temp / 2 ** 4
    else:
        # Probability 4-stat has minimum good rolls
        temp = 0
        for i in range(6 - minimum):
            temp += math.comb(5, i)
        prob_valid += temp / 2 ** 5
    
    base_score = score(base, target)
    
    main = find_main(base)
    subs = find_sub(base, main)
    
    best_subs = np.argpartition(target[subs], -2)
    best_subs = subs[best_subs[-2:]]
    max_weight = np.max(target[subs])
    
    num_upgrades = 4 if unactivated else 5
    diff = (threshold - base_score).astype(int)
    
    output = _reshape_helper(diff, 0, num_upgrades)
    _reshape_helper.cache_clear()
    return output / prob_valid

def reshape_resin(slot, base, target, threshold, unactivated, minimum=2):
    reshape_prob = reshape_percentile(base, target, threshold, unactivated, minimum)
    percentile = artifact_percentile(slot, target, threshold, 20)
    resin = estimate_resin(percentile)
    
    return reshape_prob * resin

def base_define_probs(slot, target):
    main = np.argmax(np.where(MAIN_PROBS[slot] == 0, 0, target))
    best_subs = np.argpartition(np.where(np.arange(19) == main, 0, target), -2)[-2:]
    
    # TODO: simplify this. This is adapted from base_artifact_probs and overkill
    perms = np.array(list(permutations(range(2))), dtype=int)
    
    if main < 10:
        cand = np.delete(np.arange(10), [main, *best_subs])
    else:
        cand = np.delete(np.arange(10), best_subs)
        
    w = SUB_PROBS[cand]
    total = w.sum()
    
    comb_idx = np.array(list(combinations(np.arange(cand.size), 2)), dtype=int)  # (C,4)
    C = comb_idx.shape[0]
    
    w_sel = w[comb_idx]
    w_perm = w_sel[:, perms]
    
    cs = np.cumsum(w_perm, axis=-1)
    cs_excl = cs - w_perm
    denoms = total - cs_excl
    
    with np.errstate(divide='ignore', invalid='ignore'):
        ratios = np.where(denoms > 0, w_perm / denoms, 0.0)
        p_order = np.prod(ratios, axis=-1)
        
    probs = p_order.sum(axis=1)
    
    subs = cand[comb_idx]
    subs = np.concatenate([subs, np.broadcast_to(best_subs, (len(subs), best_subs.shape[0]))], axis=1)
    subs.sort(axis=1)
    
    return np.full(C, main, dtype=int), subs, probs

def define_percentile(slot, target, threshold):
    @functools.lru_cache(maxsize=CACHE_SIZE)
    def _define_helper(diff, num_good, num_upgrades):
        if num_good + num_upgrades < MINIMUM:
            return None
        
        if diff < 0 and num_good >= MINIMUM:
            return 0.2 if num_upgrades == 0 else 1 # TODO: fine out if this should be 1/3
        
        if num_upgrades == 0:
            return 0
        
        upper_bound = max_weight * 10 * num_upgrades
        if diff >= upper_bound:
            return 0
        
        output = 0
        for sub in s:
            temp_num_good = num_good + 1 if sub in best_subs else num_good
            for coef in (10, 9, 8, 7):
                temp_diff = diff - coef * new_target[sub]
                temp_prob = _define_helper(temp_diff, temp_num_good, num_upgrades - 1)
                if temp_prob is None:
                    break
                
                output += temp_prob
                
        return output / 16
    
    MINIMUM = 2
    
    prob_valid = 0
    # Probability 3-stat has minimum good rolls
    temp = 0
    for i in range(5 - MINIMUM):
        temp += math.comb(4, i)
    prob_valid += 0.8 * temp / 2 ** 4
    # Probability 4-stat has minimum good rolls
    temp = 0
    for i in range(6 - MINIMUM):
        temp += math.comb(5, i)
    prob_valid += 0.2 * temp / 2 ** 5
    
    mains, subs, probs = base_define_probs(slot, target)
    mains, subs, probs = base_artifact_useful_probs(mains, subs, probs, target)
    
    new_target = np.append(target, 0)
    
    best_subs = subs[0, [np.argpartition(new_target[subs[0]], -2)[-2:]]]
    
    output = 0
    for m, s, p in zip(mains, subs, probs):
        diff = threshold - new_target[m] * (160 if m < 3 else 80)
        num_useful = np.count_nonzero(s != -1)
        num_useless = 4 - num_useful
        max_weight = np.max(new_target[s])
        for coefs in product((7, 8, 9, 10), repeat=num_useful):
            coefs = [0] * num_useless + list(coefs)
            temp_diff = diff
            for sub, coef in zip(s, coefs):
                temp_diff -= coef * new_target[sub]

            output += p * _define_helper(temp_diff, 0, 5) / 4 ** num_useful
            
        _define_helper.cache_clear()
        
    return output / prob_valid

def define_resin(slot, target, threshold):
    define_prob = define_percentile(slot, target, threshold)
    percentile = artifact_percentile(slot, target, threshold, 20)
    resin = estimate_resin(percentile)
    
    return define_prob * resin

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

def rate(artifacts, slots, mask, slvls, sets, ranker, k=1):
    # TODO: change persist to persist_artifact and persist_meta, for
    # more intuitive control over things like set masking
    relevance = np.zeros((len(artifacts), 2), dtype=float)
    counts = np.zeros((len(artifacts), 2), dtype=int)
    for slot in range(5):
        # TODO: this won't work if there's 0 artifacts
        slot_mask = np.logical_and(mask, slots == slot)
        original_idxs = np.where(slot_mask)[0]
        slot_artifacts = artifacts[slot_mask]
        slot_lvls = slvls[slot_mask]
        persist = {}
        relevance[slot_mask, 0] = ranker(slot_artifacts, slot_lvls, persist, ALL_TARGETS[SLOTS[slot]], k=2 * k)
        counts[slot_mask, 0] = len(slot_artifacts)
        
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
            relevance[original_idxs, 1] = ranker(set_artifacts, set_lvls, set_persist, SET_TARGETS[SETS[setKey]][SLOTS[slot]], k=k)
            counts[original_idxs, 1] = len(set_artifacts)
    
    return relevance, counts

def upgrade_analyze(relevance, counts, mask, slvls, num=None, threshold=None):
    scaled_relevance = np.sum(relevance * counts, axis=1)
    scaled_relevance[~mask] = -999999999
    scaled_relevance[slvls == 20] = -999999999
    
    if threshold is None:
        threshold = np.partition(scaled_relevance, -num)[-num]
        
    return scaled_relevance >= threshold

def delete_analyze(relevance, mask, num=None, threshold=None):
    relevance = np.max(relevance, axis=1)
    relevance[~mask] = 999999999
    
    if threshold is None:
        threshold = np.partition(relevance, num)[num]
        
    return relevance <= threshold

def estimate_resin(percentile):
    if percentile == 0:
        return math.inf
    return math.ceil(1.065 / percentile) * 40

def set_resin(artifacts, slots, rarities, lvls, sets, set_key, target, improvement=0.0):
    slot_estimates = []
    
    for slot in range(5):
        slot_mask = np.logical_and(rarities == 5, slots == slot)
        slot_mask = np.logical_and(slot_mask, lvls == 20)
        slot_mask = np.logical_and(slot_mask, sets == set_key)
        scores = score(artifacts[slot_mask], target)
        threshold = np.max(scores) * (1 + improvement)
        percentile = artifact_percentile(SLOTS[slot], target, threshold, 20)
        slot_estimates.append(estimate_resin(percentile))
        
    return slot_estimates

def set_reshape_resin(artifacts, base_artifacts, slots, rarities, lvls, unactivated, sets, set_key, target, minimum=2, improvement=0.0):
    slot_estimates = []
    costs = [1, 1, 2, 2, 2]
    
    for slot in range(5):
        slot_mask = np.logical_and(rarities == 5, slots == slot)
        slot_mask = np.logical_and(slot_mask, lvls == 20)
        slot_mask = np.logical_and(slot_mask, sets == set_key)
        scores = score(artifacts[slot_mask], target)
        threshold = np.max(scores) * (1 + improvement)
        best = 0
        best_idx = -1
        for i in range(len(artifacts)):
            if not slot_mask[i]:
                continue
            reshape_prob = reshape_percentile(base_artifacts[i], target, threshold, unactivated[i], minimum)
            if reshape_prob > best:
                best = reshape_prob
                best_idx = i
        percentile = artifact_percentile(SLOTS[slot], target, threshold, 20)
        resin = estimate_resin(percentile)
        saving = math.inf if resin == math.inf else round(best * resin / costs[slot])
        slot_estimates.append((saving, best_idx))
        
    return slot_estimates

def set_define_resin(artifacts, slots, rarities, lvls, sets, set_key, target, improvement=0.0):
    slot_estimates = []
    costs = [1, 1, 2, 4, 3]
    
    for slot in range(5):
        slot_mask = np.logical_and(rarities == 5, slots == slot)
        slot_mask = np.logical_and(slot_mask, lvls == 20)
        slot_mask = np.logical_and(slot_mask, sets == set_key)
        scores = score(artifacts[slot_mask], target)
        threshold = np.max(scores) * (1 + improvement)
        define_prob = define_percentile(SLOTS[slot], target, threshold)
        percentile = artifact_percentile(SLOTS[slot], target, threshold, 20)
        resin = estimate_resin(percentile)
        saving = math.inf if resin == math.inf else round(define_prob * resin / costs[slot])
        slot_estimates.append(saving)
        
    return slot_estimates

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