import numpy as np
from artifact import *
import math
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

def distro(artifacts, num_upgrades):    
    #raise NotImplementedError
    if num_upgrades == 0:
        return
    
    dist = []
    if artifacts.ndim == 1:
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
                
                dist.append((temp_artifact, prob * upgrade_prob))
                
    else:
        dist = []
        for artifact in artifacts:
            dist.append(distro(artifact, num_upgrades))
        
    return tuple(dist)

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
    #print_artifact(artifacts[goal])
    artifacts = original_artifacts.copy()
    #print_artifact(artifacts[goal])
    
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

def create_dataset(num_queries, slot, lvls, targets, source='domain', num_trials=1000):
    artifacts = generate(slot, lvls, source)
    for i in range(num_trials):
        original_artifacts = artifacts.copy()
        artifacts = original_artifacts
    num = 10000
    totals = np.zeros(num)
    avg = np.zeros(num)
    targets = vectorize({'atk_': 3, 'atk': 1, 'crit_': 4})
    for i in range(num):
        artifacts = generate('flower', size=200, seed=i)
        totals[i] = (simulate_exp(artifacts, np.zeros(200, dtype=int), targets, upper_bound))

    cumsum = np.cumsum(totals)
    for i in range(len(cumsum)):
        avg[i] = cumsum[i] / (i + 1)