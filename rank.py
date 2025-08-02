import numpy as np
from analyze import *
import time
#from scipy.stats import entropy

'''
def calc_relevance(scores, k):
    if k == 1:
        # maximum per (i, j)
        cutoff = scores.max(axis=0)                    # shape (num_trials, num_targets)
    else:
        # k‑th largest via partition
        cutoff = np.partition(scores, -k, axis=0)[-k]  # same shape

    # 2) Mask of strictly above cutoff
    above = scores > cutoff[None, ...]                 # shape (n_items, num_trials, num_targets)
    above_count = above.sum(axis=0)
    leftover = k - above_count

    # 3) Mask of exactly equal to cutoff
    eq    = scores == cutoff[None, ...]                # same shape

    # 4) Count ties so we can split fractional credit
    tie_counts = eq.sum(axis=0)                        # shape (num_trials, num_targets)
    frac_per_tie = np.where(tie_counts > 0, leftover / tie_counts, 0)
    eq_contrib = eq * frac_per_tie[None, ...]

    # 5) Sum up:
    #    - 1 point for every “above”
    #    - 1/tie_counts for every “tie”
    relevance = above.sum(axis=1).astype(float)
    relevance += eq_contrib.sum(axis=1)
    return relevance
'''
def my_entropy(array, axis=None):
    return -np.sum(array * np.log(array), axis=axis)

def rank_value(artifacts, lvls, persist, targets, CHANGE=True, k=2, num_trials=1000, rng=None, seed=None):
    num_artifacts = len(artifacts)
    try:
        _ = iter(lvls)
        lvls = np.array(lvls)
    except:
        if lvls is None:
            lvls = 0
        lvls = np.full(num_artifacts, lvls)
    
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

    if rng is None:
        rng = np.random.default_rng(seed)
    
    if len(persist) == 0:
        persist['changed'] = -1

        maxed = np.zeros((num_artifacts, num_trials, 19), dtype=np.uint8)
        for i in range(num_artifacts):
            maxed[i] = sample_upgrade(artifacts[i], num_trials, lvl=lvls[i], rng=rng)
        persist['maxed'] = maxed
        persist['targets'] = None
    
    # TODO: possible optimization. Instead of recomputing scores for all
    # targets, collect ALL targets beforehand, compute them ALL, and
    # then hash/cache the scores for each target. Then, whenever the
    # target changes, collect it. This avoid duplicate score calculation
    # for the same target
    if not np.array_equal(persist['targets'], targets):
        persist['targets'] = targets
        persist['scores'] = score(persist['maxed'], targets.T)    
        
    if persist['changed'] != -1:
        changed = persist['changed']
        persist['maxed'][changed] = sample_upgrade(artifacts[changed], num_trials, lvl=lvls[changed], rng=rng)
        persist['scores'][changed] = score(persist['maxed'][changed], targets.T)
        
    scores = persist['scores']
    
    if num_artifacts <= k:
        relevance = np.full((num_artifacts), num_trials, dtype=float)
        relevance /= np.where(lvls == 20, 1, MAX_REQ_EXP[lvls])
        
        if CHANGE:
            persist['changed'] = np.argmax(relevance)
        return relevance
    
    if k == 1:
        # maximum per (i, j)
        cutoff = scores.max(axis=0)                    # shape (num_trials, num_targets)
    else:
        # k‑th largest via partition
        cutoff = np.partition(scores, -k, axis=0)[-k]  # same shape

    # 2) Mask of strictly above cutoff
    above = scores > cutoff[None, ...]                 # shape (n_items, num_trials, num_targets)
    above_count = above.sum(axis=0)
    leftover = k - above_count

    # 3) Mask of exactly equal to cutoff
    eq    = scores == cutoff[None, ...]                # same shape

    # 4) Count ties so we can split fractional credit
    tie_counts = eq.sum(axis=0)                        # shape (num_trials, num_targets)
    frac_per_tie = np.where(tie_counts > 0, leftover / tie_counts, 0)
    eq_contrib = eq * frac_per_tie[None, ...]

    # 5) Sum up:
    #    - 1 point for every “above”
    #    - 1/tie_counts for every “tie”
    relevance = above.sum(axis=(1, 2)).astype(float)
    relevance += eq_contrib.sum(axis=(1, 2))
    # relevance = np.sum(calc_relevance(scores, k), axis=1) # This extra function call and sum adds non-negligible overhead
    relevance /= np.where(lvls == 20, 1, MAX_REQ_EXP[lvls])
    if CHANGE:
        relevance[lvls == 20] = 0
        
    if CHANGE:
        persist['changed'] = np.argmax(relevance)
    #return relevance
    #print_artifact(artifacts[np.argmax(relevance)])
    if relevance[persist['changed']] == 0 and CHANGE:
        print('max was 0')
        for i in range(num_artifacts):
            persist['maxed'][i] = sample_upgrade(artifacts[i], num_trials, lvl=lvls[i], rng=rng)
        persist['targets'] = None
        persist['changed'] = -1
        return rank_value(artifacts, lvls, persist, targets, CHANGE, k, num_trials, rng)
        
    return relevance

def rank_entropy(artifacts, lvls, persist, targets, CHANGE=True, k=2, num_trials=100, rng=None, seed=None):
    num_artifacts = len(artifacts)
    try:
        _ = iter(lvls)
        lvls = np.array(lvls)
    except:
        if lvls is None:
            lvls = 0
        lvls = np.full(num_artifacts, lvls)
    
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
    
    num_targets = len(targets)
    
    if rng is None:
        rng = np.random.default_rng(seed)
        
    if len(persist) == 0:
        
        maxed = np.zeros((num_artifacts, num_trials, 19), dtype=np.uint8)
        for i in range(num_artifacts):
            maxed[i] = sample_upgrade(artifacts[i], num_trials, lvl=lvls[i], rng=rng)
        
        distros = []
        distros_maxed = []
        for i, artifact in enumerate(artifacts):
            if lvls[i] == 20:
                distros.append(None)
                distros_maxed.append(None)
                continue
            
            next = next_lvl(lvls[i])
            
            upgrades, probs = single_distro(artifact)
            
            distros.append((upgrades, probs))
            distros_maxed.append(np.zeros((len(upgrades), num_trials, 19), dtype=np.uint8))
            
            for j, upgrade in enumerate(upgrades):
                distros_maxed[-1][j] = sample_upgrade(upgrade, num_trials, lvl=next, rng=rng)
                
        persist['changed'] = -1
        persist['maxed'] = maxed
        persist['distros'] = distros
        persist['distros_maxed'] = distros_maxed
        persist['targets'] = None
        
    if not np.array_equal(persist['targets'], targets):
        persist['targets'] = targets
        persist['scores'] = score(persist['maxed'], targets.T)
        
        distros_maxed = persist['distros_maxed']
        distros_scores = []
        for distro_maxed in distros_maxed:
            if distro_maxed is None:
                distros_scores.append(None)
                continue
            
            distros_scores.append(score(distro_maxed, targets.T))
        
        persist['distros_scores'] = distros_scores
                        
    if persist['changed'] != -1:
        changed = persist['changed']
        persist['maxed'][changed] = sample_upgrade(artifacts[changed], num_trials, lvl=lvls[changed], rng=rng)
        persist['scores'][changed]= score(persist['maxed'][changed], targets.T)
        
        if lvls[changed] == 20:
            persist['distros'][changed] = None
            persist['distros_maxed'][changed] = None
            persist['distros_scores'][changed] = None
        else:
            next = next_lvl(lvls[changed])
            
            upgrades, probs = single_distro(artifacts[changed])
            persist['distros'][changed] = (upgrades, probs)
            
            distro_maxed = persist['distros_maxed'][changed]
            if len(distro_maxed) != len(upgrades):
                persist['distros_maxed'][changed] = np.zeros((len(upgrades), num_trials, 19), dtype=np.uint8)

            for i, upgrade in enumerate(upgrades):
                persist['distros_maxed'][changed][i] = sample_upgrade(upgrade, num_trials, lvl=next, rng=rng)
                
            persist['distros_scores'][changed] = score(persist['distros_maxed'][changed], targets.T)
            
    scores, distros, distros_scores = persist['scores'], persist['distros'], persist['distros_scores']
    
    if k == 1:
        # maximum per (i, j)
        cutoff = scores.max(axis=0)                    # shape (num_trials, num_targets)
    elif k == 2:
        k_plus_cutoff, k_cutoff, k_minus_cutoff = np.partition(scores, (-k - 1, -k, -k + 1), axis=0)[-k - 1:]
        #cutoff = np.partition(scores, -k, axis=0)[-k]  # same shape
    else:
        k_plus_cutoff, k_cutoff, k_minus_cutoff = np.partition(scores, (-k - 1, -k, -k + 1), axis=0)[-k - 1:-k + 1]
        #cutoff = np.partition(scores, -k, axis=0)[-k]  # same shape

    # 2) Mask of strictly above cutoff
    above = scores > k_cutoff[None, ...]                 # shape (n_items, num_trials, num_targets)
    above_count = np.count_nonzero(above, axis=0)
    #above_count = above.sum(axis=0)
    leftover = k - above_count

    # 3) Mask of exactly equal to cutoff
    eq    = scores == k_cutoff[None, ...]                # same shape

    # 4) Count ties so we can split fractional credit
    tie_counts = np.count_nonzero(eq, axis=0)
    #tie_counts = eq.sum(axis=0)                        # shape (num_trials, num_targets)
    frac_per_tie = leftover / tie_counts
    eq_contrib = eq * frac_per_tie[None, ...]
    
    relevance = np.count_nonzero(above, axis=1).astype(float)
    relevance += eq_contrib.sum(axis=1)
    
    if np.max(relevance) > k / 2:
        flat_idx = relevance.argmax()
        row_idx = flat_idx // relevance.shape[1]
        if lvls[row_idx] != 20:
            if CHANGE:
                persist['changed'] = row_idx
            print()
            print('asdf', flat_idx % relevance.shape[1])
            print(row_idx)
            print_artifact(artifacts[row_idx])
            print()
            return row_idx
    
    current_entropies = entropy(relevance, axis=0)
    
    information_gain = np.tile(current_entropies, (num_artifacts, 1))
    for i, artifact in enumerate(artifacts):
        if lvls[i] == 20:
            information_gain[i] = -10
            continue
        
        probs = distros[i][1]
        temp = scores[i].copy()
        
        new_k_cutoff = np.where(scores[i] < k_cutoff, k_cutoff, k_plus_cutoff)
        new_k_minus_cutoff = np.where(scores[i] < k_minus_cutoff, k_minus_cutoff, k_cutoff)
        scores[i] = 0
        
        #k_plus_cutoff, k_cutoff, k_minus_cutoff = np.partition(scores, (-k - 1, -k, -k + 1), axis=0)[-k - 1:]
        
        for upgrade, prob in zip(distros_scores[i], probs):
            if prob == 0:
                continue
            
            scores[i] = upgrade # (num_trials, num_targets)
            
            if k == 1:
                cutoff = scores.max(axis=0)
            else:
                potential_cutoff = np.minimum(upgrade, new_k_minus_cutoff)
                cutoff = np.maximum(potential_cutoff, new_k_cutoff)

            above = scores > cutoff[None, ...]
            above_count = np.count_nonzero(above, axis=0)
            #above_count = above.sum(axis=0)
            leftover = k - above_count

            eq    = scores == cutoff[None, ...]

            #tie_counts = eq.sum(axis=0)
            tie_counts = np.count_nonzero(eq, axis=0)
            frac_per_tie = leftover / tie_counts
            eq_contrib = eq * frac_per_tie[None, ...]
            #relevance = above.sum(axis=1).astype(float)
            relevance = np.count_nonzero(above, axis=1).astype(float)
            relevance += eq_contrib.sum(axis=1)
            
            ent = entropy(relevance, axis=0)
            information_gain[i] -= prob * ent
            
        #print(info_gain[i])
        scores[i] = temp
    
    #information_gain[np.isclose(information_gain, 0)] = 0
    information_gain[information_gain < 0] = 0
    
    if np.isclose(np.max(information_gain), 0):
        print('qpweoifhjap')
        persist = {}
        asdf =  rank_entropy(artifacts, lvls, persist, targets, CHANGE, k, num_trials * 2, rng)
        persist = {}
        return asdf
    
    relevance = np.sum(information_gain, axis=1)
    
    #relevance /= np.where(lvls == 20, 1, UPGRADE_REQ_EXP[lvls])
    
    if np.sum(information_gain) == 0:
        print('qpweoifhjap')
    
    if CHANGE:
        relevance[lvls == 20] = 0
        changed = np.argmax(relevance)
        persist['changed'] = changed
        print()
        print(changed)
        print_artifact(artifacts[changed])
        print(information_gain[changed])
        print()
    
    return changed
    
if __name__ == '__main__':
    '''
    '''
    start = time.time()
    num = 1
    totals = np.zeros(num)
    time_avg = np.zeros(num)
    #targets = {'atk_': 6, 'atk': 2, 'crit_': 8}
    targets = (
        {'hp_': 6, 'hp': 2, 'crit_': 8},
        {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10},
        {'hp_': 6, 'hp': 2, 'crit_': 8, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},

        {'atk_': 6, 'atk': 2, 'crit_': 8},
        {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
        {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},

        {'def_': 6, 'def': 2, 'crit_': 8},
        {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10},
        {'def_': 6, 'def': 2, 'crit_': 8, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7}
    )

    for i in range(num):
        artifacts = generate('flower', size=50, seed=i)
        totals[i] = (simulate_exp(artifacts, np.zeros(50, dtype=int), targets, rank_entropy))
        print(i, totals[i])
        print()

    cumsum = np.cumsum(totals)
    for i in range(len(cumsum)):
        time_avg[i] = cumsum[i] / (i + 1)
        
    print(time_avg[-1])
    end = time.time()
    print(end - start)
    
    '''
    start = time.time()
    filename = 'artifacts/genshinData_GOOD_2025_07_31_18_01.json'
    artifacts, slots, rarities, lvls, sets = load(filename)
    relevant = rate(artifacts, slots, rarities, lvls, sets, rank_value, num=100)
    
    count = 0
    
    visualize(relevant, artifacts, slots, sets, lvls)
    end = time.time()
    print(end - start)
    '''