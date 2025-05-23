import numpy as np
from artifact import *
import math
import time
import xgboost as xgb
from targets import *
from scipy.stats import entropy
import functools
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
                temp = artifacts.copy()
                temp[idx] = 8 # This assume a 0.8333 coef
                seed.append((temp, sub_probs[idx]))
        else:
            seed.append((artifacts.copy(), 1))
            
        main = find_main(artifacts)
        upgrades = _distribution(4, num_upgrades)
        for artifact, prob in seed:
            for upgrade, upgrade_prob in upgrades:
                substats = find_sub(artifact, main)
                temp_artifact = artifact.copy()
                for i in range(4):
                    temp_artifact[substats[i]] += round(8.5 * upgrade[i])
                dist.append(temp_artifact)
                probs.append(prob * upgrade_prob)
                
        dist = np.array(dist, dtype=np.uint8)
        probs = np.array(probs)
        # TODO: get rid of this bug check
        if not np.isclose(sum(probs), 1):
            raise ValueError
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

def distro_accurate(artifacts, lvls=None, num_upgrades=None):
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
                temp = artifacts.copy()
                temp[idx] = 8 # This assume a 0.8333 coef
                seed.append((temp, sub_probs[idx]))
        else:
            seed.append((artifacts.copy(), 1))
            
        main = find_main(artifacts)
        upgrades = _distribution(4, num_upgrades)
        for artifact, prob in seed:
            for upgrade, upgrade_prob in upgrades:
                substats = find_sub(artifact, main)
                # TODO: make this not disgusting
                '''
                for first, first_prob in _temp(upgrade[0]).items():
                    # Do something
                    for second, second_prob in _temp(upgrade[1]).items():
                        # Do something
                        for third, third_prob in _temp(upgrade[2]).items():
                            # Do something
                            for fourth, fourth_prob in _temp(upgrade[3]).items():
                                # Do something
                '''
                
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
        # TODO: get rid of this bug check
        if not np.isclose(sum(probs), 1):
            raise ValueError
    else:
        try:
            _ = iter(lvls)
        except:
            lvls = np.full(len(artifacts), lvls)
        
        for artifact, lvl in zip(artifacts, lvls):
            temp_dist, temp_probs = distro_accurate(artifact, lvls=lvl)
            dist.append(temp_dist)
            probs.append(temp_probs)

    return dist, probs
    
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

def simulate_exp(artifacts, lvls, targets, fun, mains=None):
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
    #distros = distro_accurate(artifacts, lvls)
    persist = []
    
    exp = 0
    
    while np.any(lvls[goal] != 20):
        idx = fun(artifacts, lvls, persist, targets)
        try:
            _ = iter(idx)
            idx = np.argmax(idx)
        except:
            pass
        if lvls[idx] == 20:
            raise ValueError
        #print_artifact(artifacts[idx])
        smart_upgrade(artifacts[idx])
        exp += UPGRADE_REQ_EXP[lvls[idx]]
        lvls[idx] = next_lvl(lvls[idx])
        #distros[0][idx], distros[1][idx] = distro_accurate(artifacts[idx], lvls[idx])
            
    return exp

def upper_bound(artifacts, lvls, targets):
    scores = score(artifacts, targets)
    scores[lvls == 20] = 0
    return np.argmax(scores)

def rank(artifacts, lvls, targets, sets=None, k=1, num_trials=30, rng=None, seed=None):
    # TODO: implement sets
    
    num_artifacts = len(artifacts)
    try:
        _ = iter(lvls)
        lvls = np.array(lvls)
    except:
        if lvls is None:
            lvls = 0
        lvls = np.full(num_artifacts, lvls)
    
    if rng is None:
        rng = np.random.default_rng(seed)
    
    distributions, probs = distro(artifacts, lvls=lvls)
    relevance = np.zeros(num_artifacts)
    for _ in range(num_trials):
        maxed = np.zeros((num_artifacts, 19), dtype=np.uint8)
        for i in range(num_artifacts):
            maxed[i] = rng.choice(distributions[i], p=probs[i])
        if type(targets) == dict or (type(targets) == np.ndarray and targets.ndim == 1):
            final_scores = score(maxed, targets)
            final_scores[lvls == 20] = 0
            best = np.argpartition(final_scores, -k)[-k:]
            relevance[best] += 1
        else:
            for target in targets:
                final_scores = score(maxed, target)
                final_scores[lvls == 20] = 0
                best = np.argpartition(final_scores, -k)[-k:]
                relevance[best] += 1
        
    #return relevance
    return np.argmax(relevance)

def rank_value(artifacts, lvls, persist, targets, k=1, num_trials=1000, rng=None, seed=None):
    num_artifacts = len(artifacts)
    try:
        _ = iter(lvls)
        lvls = np.array(lvls)
    except:
        if lvls is None:
            lvls = 0
        lvls = np.full(num_artifacts, lvls)
    
    if rng is None:
        rng = np.random.default_rng(seed)
    
    if len(persist) == 0:
        while len(persist) < 2:
            persist.append(None)
        persist[0] = -1
        distributions, probs = distro_accurate(artifacts, lvls)
        maxed = np.zeros((num_artifacts, num_trials, 19), dtype=np.uint8)
        for i in range(num_artifacts):
            maxed[i] = rng.choice(distributions[i], p=probs[i], size=num_trials)
        persist[1] = maxed
    else:
        changed = persist[0]
        distributions, probs = distro_accurate(artifacts[changed], lvls[changed])
        persist[1][changed] = rng.choice(distributions, p=probs, size=num_trials)
        
    changed, maxed = persist
    relevance = np.zeros(num_artifacts, dtype=float)
    
    for i in range(num_trials):
        #maxed = np.zeros((num_artifacts, 19), dtype=np.uint8)
        #for i in range(num_artifacts):
        #    maxed[i] = rng.choice(distributions[i], p=probs[i])
        if type(targets) == dict or (type(targets) == np.ndarray and targets.ndim == 1):
            final_scores = score(maxed[:, i], targets)
            final_scores[lvls == 20] = 0
            maximum = np.max(final_scores)
            best = np.where(final_scores == maximum)[0]
            relevance[best] += 1 / len(best)
        else:
            for target in targets:
                final_scores = score(maxed[:, i], target)
                final_scores[lvls == 20] = 0
                maximum = np.max(final_scores)
                best = np.where(final_scores == maximum)[0]
                relevance[best] += 1 / len(best)
                # each target is weighted equally. Don't divide by the
                # number of targets, or else having more targets would
                # make each target less valuable, which isn't the case.
                
    for i in range(num_artifacts):
        if lvls[i] != 20:
            relevance[i] /= MAX_REQ_EXP[lvls[i]]
            #raise ValueError
        
    #return relevance
    #print_artifact(artifacts[np.argmax(relevance)])
    persist[0] = np.argmax(relevance)
    return np.argmax(relevance)

def rank_estimate(artifacts, lvls, persist, targets, k=1, num_trials=30, rng=None, seed=None):
    # 
    num_artifacts = len(artifacts)
    try:
        _ = iter(lvls)
        lvls = np.array(lvls)
    except:
        if lvls is None:
            lvls = 0
        lvls = np.full(num_artifacts, lvls)
    
    if rng is None:
        rng = np.random.default_rng(seed)
        
    if len(persist) == 0:
        while len(persist) < 3:
            persist.append(None)
        persist[0] = -1
        distributions, probs = distro_accurate(artifacts, lvls)
        maxed = np.zeros((num_artifacts, num_trials, 19), dtype=np.uint8)
        for i in range(num_artifacts):
            maxed[i] = rng.choice(distributions[i], p=probs[i], size=num_trials)
        persist[1] = maxed
        
        distros = []
        for i in range(num_artifacts):
            distros.append([None, None])
            if lvls[i] == 20:
                continue
            
            current_distribution, current_probs = distro_accurate(artifacts[i], num_upgrades=1)
            distros[-1][0] = []
            distros[-1][1] = current_probs
            for j, upgrade in enumerate(current_distribution):
                potential_distribution, potential_probs = distro_accurate(upgrade, next_lvl(lvls[i]))
                distros[-1][0].append(rng.choice(potential_distribution, p=potential_probs, size=num_trials))
            
        persist[2] = distros
    else:
        changed = persist[0]
        distributions, probs = distro_accurate(artifacts[changed], lvls[changed])
        persist[1][changed] = rng.choice(distributions, p=probs, size=num_trials)
        if lvls[changed] != 20:
            current_distribution, current_probs = distro_accurate(artifacts[changed], num_upgrades=1)
            persist[2][changed][0] = []
            persist[2][changed][1] = current_probs
            for j, upgrade in enumerate(current_distribution):
                potential_distribution, potential_probs = distro_accurate(upgrade, next_lvl(lvls[changed]))
                persist[2][changed][0].append(rng.choice(potential_distribution, p=potential_probs, size=num_trials))
    # TODO: save scores instead of artifacts. Save a threshold score.
    # When computing potential new scores, count how many are above the
    # threshold. This is the relevance score. Don't recompute scores and
    # count. Compute scores once and get a threshold.
    
    changed, maxed, distros = persist
    relevance_std = np.zeros(num_artifacts, dtype=float)
    original_maxed = maxed.copy()
    for i in range(num_artifacts):
        if lvls[i] == 20:
            continue
        
        maxes, current_probs = distros[i]
        relevance = np.zeros(len(maxes), dtype=float)
        for j, asdf in enumerate(maxes):
            maxed[i] = asdf
            for k in range(num_trials):
                if type(targets) == dict or (type(targets) == np.ndarray and targets.ndim == 1):
                    final_scores = score(maxed[:, k], targets)
                    final_scores[lvls == 20] = 0
                    maximum = np.max(final_scores)
                    best = np.where(final_scores == maximum)[0]
                    if final_scores[i] == maximum:
                        relevance[j] += 1 / len(best)
                else:
                    raise NotImplementedError
                
        #print(relevance)
        mean = np.dot(relevance, current_probs)
        if mean >= 0.5 * num_trials:
            print('ABOVE 50%')
            return i
        var = np.dot(current_probs, (relevance - mean)**2)
        relevance_std[i] = np.sqrt(var)
        
        maxed[i] = original_maxed[i]
        
    for i in range(num_artifacts):
        if lvls[i] != 20:
            relevance_std[i] /= MAX_REQ_EXP[lvls[i]]        
            
    #print(relevance_std)
    output = np.argmax(relevance_std)
    persist[0] = output
    return output

def rank_myopic(artifacts, lvls, distros, targets, k=1, num_trials=100, rng=None, seed=None):
    num_artifacts = len(artifacts)
    try:
        _ = iter(lvls)
        lvls = np.array(lvls)
    except:
        if lvls is None:
            lvls = 0
        lvls = np.full(num_artifacts, lvls)
    
    if rng is None:
        rng = np.random.default_rng(seed)
        
    '''
    Psuedo:
    Store num_trials x num_artifacts x 19 array of the maxed artifacts
    Compute current relevance from that
    Compute current entropy from current relevance
    
    For each artifact
        Store current maxed artifacts for selected artifact
        For each possible upgrade
            Compute num_trials new maxed artifacts
            Replace maxed artifacts with new ones for selected artifact
            Compute new relevance
            Compute new entropy
            
        Compute expected new entropy
        Put back original maxed artifacts for selected artifact
        
    Return artifact with maximum entropy reduction per cost
    '''
    current_relevance = np.zeros(num_artifacts, dtype=float)
    
    distributions, probs = distros
    maxed = np.zeros((num_artifacts, num_trials, 19), dtype=np.uint8)
    for i in range(num_artifacts):
        maxed[i] = rng.choice(distributions[i], p=probs[i], size=num_trials)
    original_maxed = maxed.copy()
    for i in range(num_trials):
        #maxed = np.zeros((num_artifacts, 19), dtype=np.uint8)
        #for i in range(num_artifacts):
        #    maxed[i] = rng.choice(distributions[i], p=probs[i])
        if type(targets) == dict or (type(targets) == np.ndarray and targets.ndim == 1):
            final_scores = score(maxed[:, i], targets)
            final_scores[lvls == 20] = 0
            maximum = np.max(final_scores)
            best = np.where(final_scores == maximum)[0]
            current_relevance[best] += 1 / len(best)
            #current_relevance[best] += 1
        else:
            for target in targets:
                final_scores = score(maxed[:, i], target)
                final_scores[lvls == 20] = 0
                maximum = np.max(final_scores)
                best = np.where(final_scores == maximum)[0]
                current_relevance[best] += 1 / len(best)
                #best = np.argpartition(final_scores, -k)[-k:]
                #current_relevance[best] += 1
    current_entropy = entropy(current_relevance)
    if current_entropy == 0:
        return np.argmax(current_relevance)
    entropy_reduction_value = np.zeros(num_artifacts, dtype=float) - 999999
    
    # TODO: upgrade everyone one at the same time, instead of interating
    # through each artifact and upgrading it one by one
    for i in range(num_artifacts):
        if lvls[i] == 20:
            continue
        new_lvl = next_lvl(lvls[i])
        old_maxed = maxed[i].copy()
        expected_entropy = 0
        #new_relevance = np.zeros(num_artifacts, dtype=int)
        counter = -1
        for upgrade, prob in zip(*distro(artifacts[i], num_upgrades=1)):
            new_relevance = np.zeros(num_artifacts, dtype=float)
            counter += 1
            if prob == 0:
                continue
            new_maxed, new_probs = distro(upgrade, lvls=new_lvl)
            maxed[i] = rng.choice(new_maxed, size=num_trials, p=new_probs)
            for j in range(num_trials):
                if type(targets) == dict or (type(targets) == np.ndarray and targets.ndim == 1):
                    final_scores = score(maxed[:, j], targets)
                    final_scores[lvls == 20] = 0
                    #best = np.argpartition(final_scores, -k)[-k:]
                    maximum = np.max(final_scores)
                    best = np.where(final_scores == maximum)[0]
                    new_relevance[best] += 1 / len(best)
                    #new_relevance[best] += 1
                else:
                    for target in targets:
                        final_scores = score(maxed[:, j], target)
                        final_scores[lvls == 20] = 0
                        maximum = np.max(final_scores)
                        best = np.where(final_scores == maximum)[0]
                        new_relevance[best] += 1 / len(best)
                        #best = np.argpartition(final_scores, -k)[-k:]
                        #new_relevance[best] += 1
                        
            #print(counter)
            #print(prob)
            #print(new_relevance)
            new_entropy = entropy(new_relevance)
            expected_entropy += prob * new_entropy
        maxed[i] = old_maxed
        entropy_reduction_value[i] = (current_entropy - expected_entropy) / UPGRADE_REQ_EXP[lvls[i]]
    super_new_maxed = maxed.copy()
    asdf = np.array_equal(original_maxed, super_new_maxed)
    output = np.argmax(entropy_reduction_value)
    if entropy_reduction_value[output] == 0:
        print(current_relevance)
        for i in range(num_artifacts):
            if lvls[i] != 20:
                current_relevance[i] /= MAX_REQ_EXP[lvls[i]]
        output = np.argmax(current_relevance)
    print('best:', output)
    print(entropy_reduction_value[output])
    print(lvls[output])
    print_artifact(artifacts[output])
    print()
    return output
        
        
def rank_marginal_relevance(artifacts, lvls, targets, k=1, num_trials=100, rng=None, seed=None):
    num_artifacts = len(artifacts)
    try:
        _ = iter(lvls)
        lvls = np.array(lvls)
    except:
        if lvls is None:
            lvls = 0
        lvls = np.full(num_artifacts, lvls)
    
    if rng is None:
        rng = np.random.default_rng(seed)
        
    current_relevance = np.zeros(num_artifacts, dtype=int)
    
    distributions, probs = distro(artifacts, lvls=lvls)
    maxed = np.zeros((num_artifacts, num_trials, 19), dtype=np.uint8)
    for i in range(num_artifacts):
        maxed[i] = rng.choice(distributions[i], p=probs[i], size=num_trials)
    
    for i in range(num_trials):
        #maxed = np.zeros((num_artifacts, 19), dtype=np.uint8)
        #for i in range(num_artifacts):
        #    maxed[i] = rng.choice(distributions[i], p=probs[i])
        if type(targets) == dict or (type(targets) == np.ndarray and targets.ndim == 1):
            final_scores = score(maxed[:, i], targets)
            final_scores[lvls == 20] = 0
            best = np.argpartition(final_scores, -k)[-k:]
            current_relevance[best] += 1
        else:
            for target in targets:
                final_scores = score(maxed[:, i], target)
                final_scores[lvls == 20] = 0
                best = np.argpartition(final_scores, -k)[-k:]
                current_relevance[best] += 1
    current_entropy = entropy(current_relevance)
    entropy_reduction_value = np.zeros(num_artifacts, dtype=float) - 999999
    
    # TODO: upgrade everyone one at the same time, instead of interating
    # through each artifact and upgrading it one by one
    for i in range(num_artifacts):
        if lvls[i] == 20:
            continue
        new_lvl = next_lvl(lvls[i])
        old_maxed = maxed[i].copy()
        expected_entropy = 0
        new_relevance = np.zeros(num_artifacts, dtype=int)
        for upgrade, prob in zip(*distro(artifacts[i], num_upgrades=1)):
            if prob == 0:
                continue
            new_maxed, new_probs = distro(upgrade, lvls=new_lvl)
            maxed[i] = rng.choice(new_maxed, size=num_trials, p=new_probs)
            for j in range(num_trials):
                if type(targets) == dict or (type(targets) == np.ndarray and targets.ndim == 1):
                    final_scores = score(maxed[:, j], targets)
                    final_scores[lvls == 20] = 0
                    best = np.argpartition(final_scores, -k)[-k:]
                    new_relevance[best] += 1
                else:
                    for target in targets:
                        final_scores = score(maxed[:, j], target)
                        final_scores[lvls == 20] = 0
                        best = np.argpartition(final_scores, -k)[-k:]
                        new_relevance[best] += 1
                        
            new_entropy = entropy(new_relevance)
            expected_entropy += prob * new_entropy
        maxed[i] = old_maxed
        entropy_reduction_value[i] = (current_entropy - expected_entropy) / UPGRADE_REQ_EXP[lvls[i]]
    
    output = np.argmax(entropy_reduction_value)
    print(entropy_reduction_value[output])
    print(lvls[output])
    print_artifact(artifacts[output])
    print()
    return np.argmax(entropy_reduction_value)
        
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

def rate(artifacts, slots, lvls, sets, ranker, threshold):
    relevant = np.zeros(len(artifacts), dtype=bool)
    for slot in range(5):
        mask = slots == slot
        original_idxs = np.where(slots == slot)[0]
        current_artifacts = artifacts[slots == slot]
        current_lvls = lvls[slots == slot]
        relevance = ranker(current_artifacts, current_lvls, ALL_TARGETS[SLOTS[slot]], num_trials=1000)
        for i in range(len(current_artifacts)):
            if relevance[i] >= threshold or current_lvls[i] == 20:
                relevant[original_idxs[i]] = True
        
        for setKey in range(len(SETS)):
            mask = np.logical_and(slots == slot, sets == setKey)
            original_idxs = np.where(mask)[0]
            current_artifacts = artifacts[mask]
            current_lvls = lvls[mask]
            relevance = ranker(current_artifacts, current_lvls, SET_TARGETS[SETS[setKey]][SLOTS[slot]], num_trials=1000)
            for i in range(len(current_artifacts)):
                if relevance[i] >= threshold or current_lvls[i] == 20:
                    relevant[original_idxs[i]] = True
                    
    return relevant

if __name__ == '__main__':
    num = 10
    totals = np.zeros(num)
    time_avg = np.zeros(num)
    targets = {'atk_': 3, 'atk': 1, 'crit_': 4}

    for i in range(num):
        artifacts = generate('flower', size=20, seed=i)
        totals[i] = (simulate_exp(artifacts, np.zeros(20, dtype=int), targets, rank_estimate))
        print(i, totals[i])
        print()

    cumsum = np.cumsum(totals)
    for i in range(len(cumsum)):
        time_avg[i] = cumsum[i] / (i + 1)
        
    print(time_avg[-1])