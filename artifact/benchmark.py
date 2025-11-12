import numpy as np
from typing import cast, Callable
from numpy.typing import NDArray
from .core import score
from .io import print_artifact
from .rate import CachePercentile
from .constants import UPGRADE_REQ_EXP, ARTIFACT_DTYPE, SLVL_DTYPE, TARGET_DTYPE
from .upgrades import smart_upgrade_until_max, smart_upgrade, next_lvl

def simulate_exp(
    artifacts: NDArray[ARTIFACT_DTYPE], 
    slvls: NDArray[SLVL_DTYPE], 
    targets: NDArray[TARGET_DTYPE], 
    fun: Callable, 
    num: int = 1, 
    mains: None = None
) -> int:
    # TODO: check if anything is maxed. They shouldn't be
    # TODO: add benchmark for how long it takes to acheive top 1%, not
    # just top 1
    original_artifacts = artifacts.copy()
    smart_upgrade_until_max(artifacts, slvls)
    
    # TODO: WTF is this
    if type(targets) == dict or (type(targets) == np.ndarray and targets.ndim == 1):
        scores = cast(np.ndarray, score(artifacts, targets))
        goal = np.argmax(scores)
        goal_scores = scores[goal]
    else:
        goal = np.zeros(len(targets), dtype=ARTIFACT_DTYPE)
        goal_scores = np.zeros(len(targets), dtype=float)
        for i, target in enumerate(targets):
            scores = cast(np.ndarray, score(artifacts, target))
            goal[i] = np.argmax(scores)
            goal_scores[i] = scores[goal[i]]
    
    print('goal:', goal)
    print('score:', goal_scores)
    print_artifact(artifacts[goal])
    print()
    '''
    '''
    artifacts[:] = original_artifacts.copy()
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
            exp += cast(int, UPGRADE_REQ_EXP[slvls[idx]])
            slvls[idx] = next_lvl(cast(int, slvls[idx]))
            #distros[0][idx], distros[1][idx] = distro(artifacts[idx], lvls[idx])
            
            print(exp)
            
        new_scores = score(artifacts[chosen], targets.T) # (n,U)
        new_maxes = np.max(new_scores, axis=0)  # (U,)
        target_maxes = np.maximum(target_maxes, new_maxes)
            
        persist['changed'] += list(chosen)
        print((target_maxes - start_maxes) / score_ranges)
        
        '''
        reshuffle = np.random.choice(np.arange(len(artifacts))[slvls != 20], size=num, replace=False)
        persist['changed'] += list(reshuffle)
        '''
            
    #print(np.histogram(slvls, bins=7)[0])
    return exp

def simulate_delete(
    slot: str, 
    artifacts: NDArray[ARTIFACT_DTYPE], 
    slvls: NDArray[SLVL_DTYPE], 
    targets: NDArray[TARGET_DTYPE]
) -> int:
    num_artifacts = len(artifacts)
    num_targets = len(targets)
    original_artifacts = artifacts.copy()
    smart_upgrade_until_max(artifacts, slvls)
    
    # TODO: WTF is this
    if type(targets) == dict or (type(targets) == np.ndarray and targets.ndim == 1):
        scores = cast(np.ndarray, score(artifacts, targets))
        goal = np.argmax(scores)
        goal_scores = scores[goal]
    else:
        maybe = {}
        qwer = [set() for _ in range(num_targets)]
        goal = []
        goal_scores = np.zeros(len(targets), dtype=float)
        scores = cast(np.ndarray, score(artifacts, targets.T)) # (N,D)
        goal_scores = np.max(scores, axis=0)  # (D,)
        for i, target in enumerate(targets):
            asdf = np.where(scores[:, i] >= goal_scores[i] * 1)[0]
            for _ in asdf:
                if _ in maybe:
                    maybe[_].add(i)
                else:
                    maybe[_] = set([i])
                qwer[i].add(_)
            goal.append(asdf)
        
    artifacts[:] = original_artifacts.copy()
    
    '''
    base_trials = 500
    rng = np.random.default_rng(42)
    
    maxed = np.zeros((num_artifacts, base_trials, 19), dtype=np.uint8)   # (N,T,19)
    for i in range(num_artifacts):
        maxed[i], _ = sample_upgrade(artifacts[i], base_trials, slvl=slvls[i], rng=rng)
    scores = score(maxed, targets.T)
    cutoff = scores.max(axis=0)
    winners = winner_prob(scores, cutoff, 1)
    p = np.mean(winners, axis=1)
    total_p = 1 - np.prod(1 - p, axis=1)
    for i, _ in enumerate(np.argsort(total_p)):
        if _ in maybe:
            for t in maybe[_]:
                if len(qwer[t]) == 1:
                    return i
                qwer[t].remove(_)
    return 500
    '''
    caches = [CachePercentile(slot, target) for target in targets]
    percentiles = np.zeros((num_artifacts, num_targets))
    #percentiles = np.zeros((num_targets, num_artifacts))
    for i, (artifact, slvl) in enumerate(zip(artifacts, slvls)):
        print('qwer')
        for j, target in enumerate(targets):
            percentiles[i, j] = caches[j].percent(artifact, slvl)
            
    levels = {0: 0, 4: 0, 8: 0, 12: 0, 16: 0, 20: 0}
    relevance = np.max(percentiles, axis=1) # (N,)
    for i, _ in enumerate(np.argsort(relevance)):
        if slvls[_] < 0:
            levels[0] += 1
        else:
            levels[int(slvls[_])] += 1
        if _ in maybe:
            for t in maybe[_]:
                if len(qwer[t]) == 1:
                    print(levels)
                    return i
                qwer[t].remove(_)
    return len(artifacts)