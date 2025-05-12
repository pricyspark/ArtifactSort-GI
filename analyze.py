import numpy as np
from artifact import *
import math
import time
import xgboost as xgb
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

def distro(artifacts, lvls):    
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
                temp[idx] = 25 # This assume a 0.8333 coef
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
                    temp_artifact[substats[i]] += math.floor(25.5 * upgrade[i])
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
            temp_dist, temp_probs = distro(artifact, lvl)
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
    # TODO: add benchmark for how long it takes to acheive top n%, not
    # just top 1
    original_artifacts = artifacts.copy()
    smart_upgrade_until_max(artifacts, lvls)
    scores = score(artifacts, targets)
    goal = np.argmax(scores)
    print_artifact(artifacts[goal])
    artifacts = original_artifacts.copy()
    
    exp = 0
    
    while lvls[goal] != 20:
        idx = fun(artifacts, lvls, targets)
        if lvls[idx] == 20:
            raise ValueError
        smart_upgrade(artifacts[idx])
        exp += UPGRADE_REQ_EXP[lvls[idx]]
        lvls[idx] = 4 * ((lvls[idx] // 4) + 1)
            
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
    
    distributions, probs = distro(artifacts, lvls)
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

def asdf_rank(artifacts, lvls, targets, sets=None, k=1, num_trials=30, rng=None, seed=None):
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
    
    distributions, probs = distro(artifacts, lvls)
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
                
    for i in range(num_artifacts):
        if lvls[i] != 20:
            relevance[i] /= MAX_REQ_EXP[lvls[i]]
            #raise ValueError
        
    return relevance
    #return np.argmax(relevance)
        
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
        distributions, probs = distro(artifacts[this_slice], lvls)
        
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

if __name__ == '__main__':
    filename = 'artifacts/genshinData_GOOD_2025_05_12_02_34.json'
    artifacts, slots, lvls, sets = load(filename)
    
    targets = [
        {'hp_': 3, 'hp': 1, 'crit_': 4},
        {'hp_': 3, 'hp': 1, 'crit_': 4, 'enerRech_': 5},
        {'hp_': 3, 'hp': 1, 'crit_': 4, 'eleMas': 3},
        {'hp_': 3, 'hp': 1, 'crit_': 4, 'enerRech_': 5, 'eleMas': 3},
        
        {'atk_': 3, 'atk': 1, 'crit_': 4},
        {'atk_': 3, 'atk': 1, 'crit_': 4, 'enerRech_': 5},
        {'atk_': 3, 'atk': 1, 'crit_': 4, 'eleMas': 3},
        {'atk_': 3, 'atk': 1, 'crit_': 4, 'enerRech_': 5, 'eleMas': 3},
        
        {'def_': 3, 'def': 1, 'crit_': 4},
        {'def_': 3, 'def': 1, 'crit_': 4, 'enerRech_': 5},
        {'def_': 3, 'def': 1, 'crit_': 4, 'eleMas': 3},
        {'def_': 3, 'def': 1, 'crit_': 4, 'enerRech_': 5, 'eleMas': 3}
    ]
    
    sands_targets = [
        {'hp_': 3, 'hp': 1, 'crit_': 4},
        {'hp_': 3, 'hp': 1, 'crit_': 4, 'enerRech_': 5},
        {'hp_': 3, 'hp': 1, 'crit_': 4, 'eleMas': 3},
        {'hp_': 3, 'hp': 1, 'crit_': 4, 'enerRech_': 5, 'eleMas': 3},
        {'hp_': 3, 'hp': 1, 'enerRech_': 5, 'eleMas': 8},
        
        {'atk_': 3, 'atk': 1, 'crit_': 4},
        {'atk_': 3, 'atk': 1, 'crit_': 4, 'enerRech_': 5},
        {'atk_': 3, 'atk': 1, 'crit_': 4, 'eleMas': 3},
        {'atk_': 3, 'atk': 1, 'crit_': 4, 'enerRech_': 5, 'eleMas': 3},
        {'atk_': 3, 'atk': 1, 'enerRech_': 5, 'eleMas': 8},
        
        {'def_': 3, 'def': 1, 'crit_': 4},
        {'def_': 3, 'def': 1, 'crit_': 4, 'enerRech_': 5},
        {'def_': 3, 'def': 1, 'crit_': 4, 'eleMas': 3},
        {'def_': 3, 'def': 1, 'crit_': 4, 'enerRech_': 5, 'eleMas': 3},
        {'def_': 3, 'def': 1, 'enerRech_': 5, 'eleMas': 8}
    ]
    
    goblet_targets = [
        {'hp_': 3, 'hp': 1, 'crit_': 4},
        {'hp_': 3, 'hp': 1, 'crit_': 4, 'enerRech_': 5},
        {'hp_': 3, 'hp': 1, 'crit_': 4, 'eleMas': 3},
        {'hp_': 3, 'hp': 1, 'crit_': 4, 'enerRech_': 5, 'eleMas': 3},
        {'hp_': 3, 'hp': 1, 'enerRech_': 5, 'eleMas': 8},
        {'hp_': 3, 'hp': 1, 'pyro_dmg_': 4, 'crit_': 4},
        {'hp_': 3, 'hp': 1, 'pyro_dmg_': 4, 'crit_': 4, 'enerRech_': 5},
        {'hp_': 3, 'hp': 1, 'pyro_dmg_': 4, 'crit_': 4, 'eleMas': 3},
        {'hp_': 3, 'hp': 1, 'pyro_dmg_': 4, 'crit_': 4, 'enerRech_': 5, 'eleMas': 3},
        {'hp_': 3, 'hp': 1, 'pyro_dmg_': 4, 'enerRech_': 5, 'eleMas': 8},
        {'hp_': 3, 'hp': 1, 'electro_dmg_': 4, 'crit_': 4},
        {'hp_': 3, 'hp': 1, 'electro_dmg_': 4, 'crit_': 4, 'enerRech_': 5},
        {'hp_': 3, 'hp': 1, 'electro_dmg_': 4, 'crit_': 4, 'eleMas': 3},
        {'hp_': 3, 'hp': 1, 'electro_dmg_': 4, 'crit_': 4, 'enerRech_': 5, 'eleMas': 3},
        {'hp_': 3, 'hp': 1, 'electro_dmg_': 4, 'enerRech_': 5, 'eleMas': 8},
        {'hp_': 3, 'hp': 1, 'cryo_dmg_': 4, 'crit_': 4},
        {'hp_': 3, 'hp': 1, 'cryo_dmg_': 4, 'crit_': 4, 'enerRech_': 5},
        {'hp_': 3, 'hp': 1, 'cryo_dmg_': 4, 'crit_': 4, 'eleMas': 3},
        {'hp_': 3, 'hp': 1, 'cryo_dmg_': 4, 'crit_': 4, 'enerRech_': 5, 'eleMas': 3},
        {'hp_': 3, 'hp': 1, 'cryo_dmg_': 4, 'enerRech_': 5, 'eleMas': 8},
        {'hp_': 3, 'hp': 1, 'hydro_dmg_': 4, 'crit_': 4},
        {'hp_': 3, 'hp': 1, 'hydro_dmg_': 4, 'crit_': 4, 'enerRech_': 5},
        {'hp_': 3, 'hp': 1, 'hydro_dmg_': 4, 'crit_': 4, 'eleMas': 3},
        {'hp_': 3, 'hp': 1, 'hydro_dmg_': 4, 'crit_': 4, 'enerRech_': 5, 'eleMas': 3},
        {'hp_': 3, 'hp': 1, 'hydro_dmg_': 4, 'enerRech_': 5, 'eleMas': 8},
        {'hp_': 3, 'hp': 1, 'dendro_dmg_': 4, 'crit_': 4},
        {'hp_': 3, 'hp': 1, 'dendro_dmg_': 4, 'crit_': 4, 'enerRech_': 5},
        {'hp_': 3, 'hp': 1, 'dendro_dmg_': 4, 'crit_': 4, 'eleMas': 3},
        {'hp_': 3, 'hp': 1, 'dendro_dmg_': 4, 'crit_': 4, 'enerRech_': 5, 'eleMas': 3},
        {'hp_': 3, 'hp': 1, 'dendro_dmg_': 4, 'enerRech_': 5, 'eleMas': 8},
        {'hp_': 3, 'hp': 1, 'anemo_dmg_': 4, 'crit_': 4},
        {'hp_': 3, 'hp': 1, 'anemo_dmg_': 4, 'crit_': 4, 'enerRech_': 5},
        {'hp_': 3, 'hp': 1, 'anemo_dmg_': 4, 'crit_': 4, 'eleMas': 3},
        {'hp_': 3, 'hp': 1, 'anemo_dmg_': 4, 'crit_': 4, 'enerRech_': 5, 'eleMas': 3},
        {'hp_': 3, 'hp': 1, 'anemo_dmg_': 4, 'enerRech_': 5, 'eleMas': 8},
        {'hp_': 3, 'hp': 1, 'geo_dmg_': 4, 'crit_': 4},
        {'hp_': 3, 'hp': 1, 'geo_dmg_': 4, 'crit_': 4, 'enerRech_': 5},
        {'hp_': 3, 'hp': 1, 'geo_dmg_': 4, 'crit_': 4, 'eleMas': 3},
        {'hp_': 3, 'hp': 1, 'geo_dmg_': 4, 'crit_': 4, 'enerRech_': 5, 'eleMas': 3},
        {'hp_': 3, 'hp': 1, 'geo_dmg_': 4, 'enerRech_': 5, 'eleMas': 8},
        {'hp_': 3, 'hp': 1, 'physical_dmg_': 4, 'crit_': 4},
        {'hp_': 3, 'hp': 1, 'physical_dmg_': 4, 'crit_': 4, 'enerRech_': 5},
        {'hp_': 3, 'hp': 1, 'physical_dmg_': 4, 'crit_': 4, 'eleMas': 3},
        {'hp_': 3, 'hp': 1, 'physical_dmg_': 4, 'crit_': 4, 'enerRech_': 5, 'eleMas': 3},
        {'hp_': 3, 'hp': 1, 'physical_dmg_': 4, 'enerRech_': 5, 'eleMas': 8},
        
        {'atk_': 3, 'atk': 1, 'crit_': 4},
        {'atk_': 3, 'atk': 1, 'crit_': 4, 'enerRech_': 5},
        {'atk_': 3, 'atk': 1, 'crit_': 4, 'eleMas': 3},
        {'atk_': 3, 'atk': 1, 'crit_': 4, 'enerRech_': 5, 'eleMas': 3},
        {'atk_': 3, 'atk': 1, 'enerRech_': 5, 'eleMas': 8},
        {'atk_': 3, 'atk': 1, 'pyro_dmg_': 4, 'crit_': 4},
        {'atk_': 3, 'atk': 1, 'pyro_dmg_': 4, 'crit_': 4, 'enerRech_': 5},
        {'atk_': 3, 'atk': 1, 'pyro_dmg_': 4, 'crit_': 4, 'eleMas': 3},
        {'atk_': 3, 'atk': 1, 'pyro_dmg_': 4, 'crit_': 4, 'enerRech_': 5, 'eleMas': 3},
        {'atk_': 3, 'atk': 1, 'pyro_dmg_': 4, 'enerRech_': 5, 'eleMas': 8},
        {'atk_': 3, 'atk': 1, 'electro_dmg_': 4, 'crit_': 4},
        {'atk_': 3, 'atk': 1, 'electro_dmg_': 4, 'crit_': 4, 'enerRech_': 5},
        {'atk_': 3, 'atk': 1, 'electro_dmg_': 4, 'crit_': 4, 'eleMas': 3},
        {'atk_': 3, 'atk': 1, 'electro_dmg_': 4, 'crit_': 4, 'enerRech_': 5, 'eleMas': 3},
        {'atk_': 3, 'atk': 1, 'electro_dmg_': 4, 'enerRech_': 5, 'eleMas': 8},
        {'atk_': 3, 'atk': 1, 'cryo_dmg_': 4, 'crit_': 4},
        {'atk_': 3, 'atk': 1, 'cryo_dmg_': 4, 'crit_': 4, 'enerRech_': 5},
        {'atk_': 3, 'atk': 1, 'cryo_dmg_': 4, 'crit_': 4, 'eleMas': 3},
        {'atk_': 3, 'atk': 1, 'cryo_dmg_': 4, 'crit_': 4, 'enerRech_': 5, 'eleMas': 3},
        {'atk_': 3, 'atk': 1, 'cryo_dmg_': 4, 'enerRech_': 5, 'eleMas': 8},
        {'atk_': 3, 'atk': 1, 'hydro_dmg_': 4, 'crit_': 4},
        {'atk_': 3, 'atk': 1, 'hydro_dmg_': 4, 'crit_': 4, 'enerRech_': 5},
        {'atk_': 3, 'atk': 1, 'hydro_dmg_': 4, 'crit_': 4, 'eleMas': 3},
        {'atk_': 3, 'atk': 1, 'hydro_dmg_': 4, 'crit_': 4, 'enerRech_': 5, 'eleMas': 3},
        {'atk_': 3, 'atk': 1, 'hydro_dmg_': 4, 'enerRech_': 5, 'eleMas': 8},
        {'atk_': 3, 'atk': 1, 'dendro_dmg_': 4, 'crit_': 4},
        {'atk_': 3, 'atk': 1, 'dendro_dmg_': 4, 'crit_': 4, 'enerRech_': 5},
        {'atk_': 3, 'atk': 1, 'dendro_dmg_': 4, 'crit_': 4, 'eleMas': 3},
        {'atk_': 3, 'atk': 1, 'dendro_dmg_': 4, 'crit_': 4, 'enerRech_': 5, 'eleMas': 3},
        {'atk_': 3, 'atk': 1, 'dendro_dmg_': 4, 'enerRech_': 5, 'eleMas': 8},
        {'atk_': 3, 'atk': 1, 'anemo_dmg_': 4, 'crit_': 4},
        {'atk_': 3, 'atk': 1, 'anemo_dmg_': 4, 'crit_': 4, 'enerRech_': 5},
        {'atk_': 3, 'atk': 1, 'anemo_dmg_': 4, 'crit_': 4, 'eleMas': 3},
        {'atk_': 3, 'atk': 1, 'anemo_dmg_': 4, 'crit_': 4, 'enerRech_': 5, 'eleMas': 3},
        {'atk_': 3, 'atk': 1, 'anemo_dmg_': 4, 'enerRech_': 5, 'eleMas': 8},
        {'atk_': 3, 'atk': 1, 'geo_dmg_': 4, 'crit_': 4},
        {'atk_': 3, 'atk': 1, 'geo_dmg_': 4, 'crit_': 4, 'enerRech_': 5},
        {'atk_': 3, 'atk': 1, 'geo_dmg_': 4, 'crit_': 4, 'eleMas': 3},
        {'atk_': 3, 'atk': 1, 'geo_dmg_': 4, 'crit_': 4, 'enerRech_': 5, 'eleMas': 3},
        {'atk_': 3, 'atk': 1, 'geo_dmg_': 4, 'enerRech_': 5, 'eleMas': 8},
        {'atk_': 3, 'atk': 1, 'physical_dmg_': 4, 'crit_': 4},
        {'atk_': 3, 'atk': 1, 'physical_dmg_': 4, 'crit_': 4, 'enerRech_': 5},
        {'atk_': 3, 'atk': 1, 'physical_dmg_': 4, 'crit_': 4, 'eleMas': 3},
        {'atk_': 3, 'atk': 1, 'physical_dmg_': 4, 'crit_': 4, 'enerRech_': 5, 'eleMas': 3},
        {'atk_': 3, 'atk': 1, 'physical_dmg_': 4, 'enerRech_': 5, 'eleMas': 8},
        
        {'def_': 3, 'def': 1, 'crit_': 4},
        {'def_': 3, 'def': 1, 'crit_': 4, 'enerRech_': 5},
        {'def_': 3, 'def': 1, 'crit_': 4, 'eleMas': 3},
        {'def_': 3, 'def': 1, 'crit_': 4, 'enerRech_': 5, 'eleMas': 3},
        {'def_': 3, 'def': 1, 'enerRech_': 5, 'eleMas': 8},
        {'def_': 3, 'def': 1, 'pyro_dmg_': 4, 'crit_': 4},
        {'def_': 3, 'def': 1, 'pyro_dmg_': 4, 'crit_': 4, 'enerRech_': 5},
        {'def_': 3, 'def': 1, 'pyro_dmg_': 4, 'crit_': 4, 'eleMas': 3},
        {'def_': 3, 'def': 1, 'pyro_dmg_': 4, 'crit_': 4, 'enerRech_': 5, 'eleMas': 3},
        {'def_': 3, 'def': 1, 'pyro_dmg_': 4, 'enerRech_': 5, 'eleMas': 8},
        {'def_': 3, 'def': 1, 'electro_dmg_': 4, 'crit_': 4},
        {'def_': 3, 'def': 1, 'electro_dmg_': 4, 'crit_': 4, 'enerRech_': 5},
        {'def_': 3, 'def': 1, 'electro_dmg_': 4, 'crit_': 4, 'eleMas': 3},
        {'def_': 3, 'def': 1, 'electro_dmg_': 4, 'crit_': 4, 'enerRech_': 5, 'eleMas': 3},
        {'def_': 3, 'def': 1, 'electro_dmg_': 4, 'enerRech_': 5, 'eleMas': 8},
        {'def_': 3, 'def': 1, 'cryo_dmg_': 4, 'crit_': 4},
        {'def_': 3, 'def': 1, 'cryo_dmg_': 4, 'crit_': 4, 'enerRech_': 5},
        {'def_': 3, 'def': 1, 'cryo_dmg_': 4, 'crit_': 4, 'eleMas': 3},
        {'def_': 3, 'def': 1, 'cryo_dmg_': 4, 'crit_': 4, 'enerRech_': 5, 'eleMas': 3},
        {'def_': 3, 'def': 1, 'cryo_dmg_': 4, 'enerRech_': 5, 'eleMas': 8},
        {'def_': 3, 'def': 1, 'hydro_dmg_': 4, 'crit_': 4},
        {'def_': 3, 'def': 1, 'hydro_dmg_': 4, 'crit_': 4, 'enerRech_': 5},
        {'def_': 3, 'def': 1, 'hydro_dmg_': 4, 'crit_': 4, 'eleMas': 3},
        {'def_': 3, 'def': 1, 'hydro_dmg_': 4, 'crit_': 4, 'enerRech_': 5, 'eleMas': 3},
        {'def_': 3, 'def': 1, 'hydro_dmg_': 4, 'enerRech_': 5, 'eleMas': 8},
        {'def_': 3, 'def': 1, 'dendro_dmg_': 4, 'crit_': 4},
        {'def_': 3, 'def': 1, 'dendro_dmg_': 4, 'crit_': 4, 'enerRech_': 5},
        {'def_': 3, 'def': 1, 'dendro_dmg_': 4, 'crit_': 4, 'eleMas': 3},
        {'def_': 3, 'def': 1, 'dendro_dmg_': 4, 'crit_': 4, 'enerRech_': 5, 'eleMas': 3},
        {'def_': 3, 'def': 1, 'dendro_dmg_': 4, 'enerRech_': 5, 'eleMas': 8},
        {'def_': 3, 'def': 1, 'anemo_dmg_': 4, 'crit_': 4},
        {'def_': 3, 'def': 1, 'anemo_dmg_': 4, 'crit_': 4, 'enerRech_': 5},
        {'def_': 3, 'def': 1, 'anemo_dmg_': 4, 'crit_': 4, 'eleMas': 3},
        {'def_': 3, 'def': 1, 'anemo_dmg_': 4, 'crit_': 4, 'enerRech_': 5, 'eleMas': 3},
        {'def_': 3, 'def': 1, 'anemo_dmg_': 4, 'enerRech_': 5, 'eleMas': 8},
        {'def_': 3, 'def': 1, 'geo_dmg_': 4, 'crit_': 4},
        {'def_': 3, 'def': 1, 'geo_dmg_': 4, 'crit_': 4, 'enerRech_': 5},
        {'def_': 3, 'def': 1, 'geo_dmg_': 4, 'crit_': 4, 'eleMas': 3},
        {'def_': 3, 'def': 1, 'geo_dmg_': 4, 'crit_': 4, 'enerRech_': 5, 'eleMas': 3},
        {'def_': 3, 'def': 1, 'geo_dmg_': 4, 'enerRech_': 5, 'eleMas': 8},
        {'def_': 3, 'def': 1, 'physical_dmg_': 4, 'crit_': 4},
        {'def_': 3, 'def': 1, 'physical_dmg_': 4, 'crit_': 4, 'enerRech_': 5},
        {'def_': 3, 'def': 1, 'physical_dmg_': 4, 'crit_': 4, 'eleMas': 3},
        {'def_': 3, 'def': 1, 'physical_dmg_': 4, 'crit_': 4, 'enerRech_': 5, 'eleMas': 3},
        {'def_': 3, 'def': 1, 'physical_dmg_': 4, 'enerRech_': 5, 'eleMas': 8}
    ]
    
    circlet_targets = [
        {'hp_': 3, 'hp': 1, 'crit_': 4},
        {'hp_': 3, 'hp': 1, 'crit_': 4, 'enerRech_': 5},
        {'hp_': 3, 'hp': 1, 'crit_': 4, 'eleMas': 3},
        {'hp_': 3, 'hp': 1, 'crit_': 4, 'enerRech_': 5, 'eleMas': 3},
        {'hp_': 3, 'hp': 1, 'enerRech_': 5, 'eleMas': 8},
        {'hp_': 3, 'hp': 1, 'enerRech_': 5, 'heal_': 8},
        
        {'atk_': 3, 'atk': 1, 'crit_': 4},
        {'atk_': 3, 'atk': 1, 'crit_': 4, 'enerRech_': 5},
        {'atk_': 3, 'atk': 1, 'crit_': 4, 'eleMas': 3},
        {'atk_': 3, 'atk': 1, 'crit_': 4, 'enerRech_': 5, 'eleMas': 3},
        {'atk_': 3, 'atk': 1, 'enerRech_': 5, 'eleMas': 8},
        {'atk_': 3, 'atk': 1, 'enerRech_': 5, 'heal_': 8},
        
        {'def_': 3, 'def': 1, 'crit_': 4},
        {'def_': 3, 'def': 1, 'crit_': 4, 'enerRech_': 5},
        {'def_': 3, 'def': 1, 'crit_': 4, 'eleMas': 3},
        {'def_': 3, 'def': 1, 'crit_': 4, 'enerRech_': 5, 'eleMas': 3},
        {'def_': 3, 'def': 1, 'enerRech_': 5, 'eleMas': 8},
        {'def_': 3, 'def': 1, 'enerRech_': 5, 'heal_': 8}
    ]
    
    asdf = np.zeros(len(artifacts))
    for slot in (0, 1):
        if slot == 0:
            print('flowers')
        else:
            print('feathers')
        for setKey in range(len(SETS)):
            printed = False
            current_artifacts = artifacts[np.logical_and(slots == slot, sets == setKey)]
            current_lvls = lvls[np.logical_and(slots == slot, sets == setKey)]
            relevance = asdf_rank(current_artifacts, current_lvls, targets, num_trials=1000)
            for i in range(len(current_artifacts)):
                if relevance[i] <= 0.00018486 and current_lvls[i] != 20:
                    if not printed:
                        print(SETS[setKey])
                        printed = True
                    print('relevance:', relevance[i])
                    print('level:', current_lvls[i])
                    print_artifact(current_artifacts[i])
                    print()
    
    print('sands')
    for slot in [2]:
        for setKey in range(len(SETS)):
            printed = False
            current_artifacts = artifacts[np.logical_and(slots == slot, sets == setKey)]
            current_lvls = lvls[np.logical_and(slots == slot, sets == setKey)]
            relevance = asdf_rank(current_artifacts, current_lvls, sands_targets, num_trials=1000)
            for i in range(len(current_artifacts)):
                if relevance[i] <= 0.00018486 and current_lvls[i] != 20:
                    if not printed:
                        print(SETS[setKey])
                        printed = True
                    print('relevance:', relevance[i])
                    print('level:', current_lvls[i])
                    print_artifact(current_artifacts[i])
                    print()
                    
    print('goblets')
    for slot in [3]:
        for setKey in range(len(SETS)):
            printed = False
            current_artifacts = artifacts[np.logical_and(slots == slot, sets == setKey)]
            current_lvls = lvls[np.logical_and(slots == slot, sets == setKey)]
            relevance = asdf_rank(current_artifacts, current_lvls, goblet_targets, num_trials=1000)
            for i in range(len(current_artifacts)):
                if relevance[i] <= 0.00018486 and current_lvls[i] != 20:
                    if not printed:
                        print(SETS[setKey])
                        printed = True
                    print('relevance:', relevance[i])
                    print('level:', current_lvls[i])
                    print_artifact(current_artifacts[i])
                    print()
                    
    print('circlets')
    for slot in [4]:
        for setKey in range(len(SETS)):
            printed = False
            current_artifacts = artifacts[np.logical_and(slots == slot, sets == setKey)]
            current_lvls = lvls[np.logical_and(slots == slot, sets == setKey)]
            relevance = asdf_rank(current_artifacts, current_lvls, circlet_targets, num_trials=1000)
            for i in range(len(current_artifacts)):
                if relevance[i] <= 0.00018486 and current_lvls[i] != 20:
                    if not printed:
                        print(SETS[setKey])
                        printed = True
                    print('relevance:', relevance[i])
                    print('level:', current_lvls[i])
                    print_artifact(current_artifacts[i])
                    print()
    '''
    print('relevant')
    for slot in range(5):
        for setKey in range(len(SETS)):
            print(SETS[setKey])
            current_artifacts = artifacts[np.logical_and(slots == slot, sets == setKey)]
            current_lvls = lvls[np.logical_and(slots == slot, sets == setKey)]
            relevance = asdf_rank(current_artifacts, current_lvls, targets, num_trials=1000)
            for i in range(len(current_artifacts)):
                if relevance[i] != 0:
                    print_artifact(current_artifacts[i])
                    print()
                    
        if slot == 1:
            break
    '''