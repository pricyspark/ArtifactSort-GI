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

def rank_entropy(artifacts, lvls, persist, targets, CHANGE=True, k=1, num_trials=200, rng=None, seed=None):
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
    temp = above.sum(axis=1) + eq_contrib.sum(axis=1)
    
    if np.max(temp) > k / 2:
        flat_idx = temp.argmax()
        row_idx = flat_idx // temp.shape[1]
        if lvls[row_idx] != 20:
            if CHANGE:
                persist['changed'] = row_idx
            print()
            print('asdf', flat_idx % temp.shape[1])
            print(row_idx)
            print_artifact(artifacts[row_idx])
            print()
            return row_idx
    
    relevance = above.sum(axis=1).astype(float)
    relevance += eq_contrib.sum(axis=1)
    
    current_entropies = np.zeros(num_targets, dtype=float)
    for i in range(num_targets):
        current_entropies[i] = entropy(relevance[:, i])
    
    temp_check = True
    information_gain = np.tile(current_entropies, (num_artifacts, 1))
    for i, artifact in enumerate(artifacts):
        if lvls[i] == 20:
            information_gain[i] = -10
            continue
        
        probs = distros[i][1]
        temp = scores[i].copy()
        
        scores[i] = 0
        
        '''
        if k == 1:
            k_cutoff = scores.max(axis=0)
        else:
            k_cutoff, k_1_cutoff = np.partition(scores, [-k, -k+1], axis=0)[-k]
            
        k_above = scores > k_cutoff[None, ...]
        k_above_count = np.count_nonzero(k_above, axis=0)
        
        k_eq    = scores == k_cutoff[None, ...]
        k_tie_counts = np.count_nonzero(k_eq, axis=0)
        
        k_1_above = scores > k_1_cutoff[None, ...]
        k_1_above_count = np.count_nonzero(k_1_above, axis=0)
        
        k_1_eq = scores == k_1_cutoff[None, ...]
        k_1_tie_counts = np.count_nonzero(k_1_eq, axis=0)    
        '''
        
            

        '''
        k_above = scores > k_cutoff[None, ...]
        k_above_count = np.count_nonzero(k_above, axis=0)
        k_leftover = k - k_above_count

        k_eq    = scores == k_cutoff[None, ...]
        k_tie_counts = np.count_nonzero(k_eq, axis=0)
        k_frac_per_tie = np.where(k_tie_counts > 0, k_leftover / k_tie_counts, 0)
        eq_contrib = k_eq * k_frac_per_tie[None, ...]
        base_relevance = np.count_nonzero(k_above, axis=1).astype(float)
        base_relevance += eq_contrib.sum(axis=1)
        
        base_ent = entropy(base_relevance, axis=0)
        '''
        
        
        for upgrade, prob in zip(distros_scores[i], probs):
            if prob == 0:
                continue
            
            '''
            precompute:
            mask for where current is = (k - 1) threshold
            mask for where current is = k treshold
            
            mask for where new is > (k - 1) threshold
            mask for where new is = (k - 1) threshold
            mask for where new is = k threshold
            
            
            precompute entropy from other artifacts for each possible case
            '''
            
            
            
            '''
            
            INSERTING
            
            if in top k:
                if in top k - 1:
                    top k, change
                if in edge k - 1:
                    if new is in k - 1:
                        edge of k, cutoff is old (k - 1)
                    if new is in edge k - 1:
                        edge of k, cutoff is old (k - 1), edge size increments
                    if new is not in k - 1:
                        top k, no change
            if in edge k
                if top k - 1 == top k:
                    if new is in top k:
                        edge of k, cutoff is old (k - 1), no change
                    if new is in edge:
                        edge of k, cutoff is old (k - 1), edge size increments
                if top k - 1 != top k:
                    if new is in top k:
                        not in k
                    if new is in edge k:
                        edge of k, edge size increments
            if not in k:
                not in k
                    
                
            if in top k:
                if in top k - 1:
                    A
                if in edge k - 1:
                    if new is in k - 1:
                        B
                    if new is in edge k - 1:
                        C
                    if new is not in k - 1:
                        A
            if in edge k
                if top k - 1 == top k:
                    if new is in top k:
                        B
                    if new is in edge:
                        C
                if top k - 1 != top k:
                    if new is in top k:
                        D
                    if new is in edge k:
                        E
            if not in k:
                D
                    
                    
            A: 
                if in top k - 1
                if in edge k - 1 AND new is not in k - 1
            B:
                if in edge k - 1 AND new is in k - 1
            C:
                if in edge k - 1 AND new is in edge k - 1
            D: 
                if in edge k AND not in edge k - 1 AND new is in top k
                if not in k
            E:
                if in edge k AND not in edge k - 1 AND new is in edge k
            
            
            
                
            in top k - 1:
                top k
            in edge k - 1:
                new is in k - 1
                    edge of k, cutoff is old (k - 1) 
                new is in edge k - 1
                    edge of k, cutoff is old (k - 1), edge size increments
                new is not in k - 1
                    top k
            in edge k:
                new is in k
                    not in k
                new is in edge k
                    edge of k, edge size increments
            not in k:
                not in k
                
                
            new is in k - 1:
                in edge k - 1:
                    edge of k, cutoff is old (k - 1)
                in edge k:
                    not in k
            new is in edge k - 1:
                in edge k - 1:
                    edge of k, cutoff is old (k - 1), edge size increments
                in edge k:
                    not in k
            new is in edge k:
                in edge k:
                    edge of k, edge size increments
                
            
            
            
            
                
            top k: 
                if in top k - 1
                if in edge k - 1 AND new is not in k - 1
            edge of k, cutoff is old (k - 1):
                if in edge k - 1 AND new is in k - 1
            edge of k, cutoff is old (k - 1), edge size increments:
                if in edge k - 1 AND new is in edge k - 1
            not in k:
                if in edge k AND not in edge k - 1 AND new is in top k
                if not in k
            edge of k, edge size increments:
                if in edge k AND not in edge k - 1 AND new is in edge k
            '''
            
            '''
            
            DELETING
            
            old is in k:
                if k cutoff == k + 1 cutoff:
                    nothing
                else:    
                    in edge k:
                        in k
                    in edge k + 1:
                        in edge k, cutoff is old (k + 1)
            old is in edge k:
                if k cutoff == k + 1 cutoff:
                    decrement edge
                else:
                    in edge k:
                        in k
                    in edge k + 1:
                        in edge k, cutoff is old (k + 1)
            
            in top k:
                top k
            in edge k:
                if in edge of k + 1:
                    nothing happens
                is not in k + 1:
                    in k
            in edge k + 1:
                edge of k, cutoff is old (k + 1)
            not in k + 1:
                not in k
            
            
            
            if in top k:
                top k
            if in edge k:
                if top k == top k + 1:
                    
                if top k != top k + 1:
            if not in k:
                if not in top k + 1:
                    not in k
                if in edge k + 1:
                    if old was in k:
                        edge of k, cutoff is old (k + 1)
                    if old was in edge k:
                        edge of k, cutoff is old (k + 1)
            '''
            
            temp_check = False
            
            '''
            greater = upgrade > k_cutoff
            eq = upgrade == k_cutoff
            less = upgrade < k_cutoff
            
            useless = np.count_nonzero(less, axis=0) == num_trials
            '''
            
            scores[i] = upgrade # (num_trials, num_targets)
            
            if k == 1:
                cutoff = scores.max(axis=0)
            else:
                cutoff = np.partition(scores, -k, axis=0)[-k]

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
    
    information_gain[np.isclose(information_gain, 0)] = 0
    information_gain[information_gain < 0] = 0
    
    if temp_check == (np.max(information_gain) == 0):
        print('match')
    else:
        print('dont match')
        print(temp_check)
        print(np.max(information_gain) == 0)
        print(information_gain)
    
    if np.max(information_gain) == 0:
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
    num = 10
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
        artifacts = generate('flower', size=200, seed=i)
        totals[i] = (simulate_exp(artifacts, np.zeros(200, dtype=int), targets, rank_entropy))
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