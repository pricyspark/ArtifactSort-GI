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
    tie_count = eq.sum(axis=0)                        # shape (num_trials, num_targets)
    frac_per_tie = np.where(tie_count > 0, leftover / tie_count, 0)
    eq_contrib = eq * frac_per_tie[None, ...]

    # 5) Sum up:
    #    - 1 point for every “above”
    #    - 1/tie_count for every “tie”
    relevance = above.sum(axis=1).astype(float)
    relevance += eq_contrib.sum(axis=1)
    return relevance
'''
def my_entropy(array, axis=None):
    return -np.sum(array * np.log(array, where=array != 0), axis=axis)
    
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
    above = scores > cutoff                 # shape (n_items, num_trials, num_targets)
    above_count = above.sum(axis=0)
    leftover = k - above_count

    # 3) Mask of exactly equal to cutoff
    eq    = scores == cutoff                # same shape

    # 4) Count ties so we can split fractional credit
    tie_count = eq.sum(axis=0)                        # shape (num_trials, num_targets)
    frac_per_tie = np.where(tie_count > 0, leftover / tie_count, 0)
    eq_contrib = eq * frac_per_tie

    # 5) Sum up:
    #    - 1 point for every “above”
    #    - 1/tie_count for every “tie”
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
        pass
    elif k == 2:
        k_plus_cutoff, k_cutoff, k_minus_cutoff = np.partition(scores, (-k - 1, -k, -k + 1), axis=0)[-k - 1:]
        #cutoff = np.partition(scores, -k, axis=0)[-k]  # same shape
    else:
        k_plus_cutoff, k_cutoff, k_minus_cutoff = np.partition(scores, (-k - 1, -k, -k + 1), axis=0)[-k - 1:-k + 1]
        #cutoff = np.partition(scores, -k, axis=0)[-k]  # same shape

    above = scores > k_cutoff           # (N,T,U)
    eq = scores == k_cutoff             # (N,T,U)
    above_count = above.sum(axis=0)     # (T,U)
    leftover = k - above_count          # (T,U)
    eq_count = eq.sum(axis=0)           # (T,U)
    frac_per_tie = leftover / eq_count  # (T,U)
    points = above.astype(float) + eq * frac_per_tie[None, ...] # (N,T,U)
    
    base_relevance = points.sum(axis=1) # (N,U)
    if np.max(base_relevance) > k / 2:
        flat_idx = base_relevance.argmax()
        row_idx = flat_idx // base_relevance.shape[1]
        if lvls[row_idx] != 20:
            if CHANGE:
                persist['changed'] = row_idx
            print()
            print('asdf', flat_idx % base_relevance.shape[1])
            print(row_idx)
            print_artifact(artifacts[row_idx])
            print()
            return row_idx
        
    base_entropy = entropy(base_relevance, axis=0) # (U,)
    information_gain = np.tile(base_entropy, (num_artifacts, 1)) # (N,U)

    for i, artifact in enumerate(artifacts):
        if lvls[i] == 20:
            information_gain[i] = -1
            continue
        
        probs = distros[i][1]           # (X,)
        upgrades = distros_scores[i]    # (X,T,U)
        
        upgrades = upgrades[probs != 0]
        probs = probs[probs != 0]
        
        original = scores[i]            # (T,U)

        if k == 1:
            pass
        else:
            new_k_cutoff = np.where(original < k_cutoff, k_cutoff, k_plus_cutoff)               # (T,U)
            new_k_minus_cutoff = np.where(original < k_minus_cutoff, k_minus_cutoff, k_cutoff)  # (T,U)
            potential = np.minimum(upgrades, new_k_minus_cutoff[None, ...])                     # (X,T,U)
            cutoffs = np.maximum(potential, new_k_cutoff[None, ...])                            # (X,T,U)
            
        upgrades_above = upgrades > cutoffs # (X,T,U)
        upgrades_eq = upgrades == cutoffs # (X,T,U)
        
        cutoffs_all = cutoffs[:, None, ...]         # (X,1,T,U)
        above_all = scores[None, ...] > cutoffs_all # (X,N,T,U)
        eq_all = scores[None, ...] == cutoffs_all   # (X,N,T,U)
        
        above_all[:, i, ...] = upgrades_above
        eq_all[:, i, ...] = upgrades_eq
        
        above_count_all = above_all.sum(axis=1)                                 # (X,T,U)
        leftover_all = k - above_count_all                                      # (X,T,U)
        eq_count_all = eq_all.sum(axis=1)                                       # (X,T,U)
        frac_per_tie_all = leftover_all / eq_count_all                          # (X,T,U)
        points_all = above_all.astype(float) + eq_all * frac_per_tie_all[:, None, ...]   # (X,N,T,U)
        
        relevance_all = points_all.sum(axis=2) # (X,N,U)
        entropy_all = entropy(relevance_all, axis=1) # (X,U)
        
        expected_entropy = probs @ entropy_all # (U,)
        information_gain[i] -= expected_entropy # (N,U)
        
        
        
        

    '''
    scores (N,T,U)
    
    for each cutoff, (X of them)
        above = scores > cutoff[None, ...] (N,T,U)
        
    

    k_above = scores > k_cutoff
    k_eq    = scores == k_cutoff
    k_above_count = k_above.sum(axis=0)                          # (T,U)
    k_leftover    = k - k_above_count
    k_tie_count   = k_eq.sum(axis=0)                             # (T,U)
    k_frac_per_tie = np.divide(k_leftover, k_tie_count,
                            out=np.zeros_like(k_leftover, dtype=float),
                            where=(k_tie_count > 0))
    credits0 = k_above.astype(float) + k_eq * k_frac_per_tie[None, ...]  # (N,T,U)

    # Early exit based on total relevance over all targets
    relevance_total = credits0.sum(axis=(1, 2))                  # (N,)
    if np.max(relevance_total) > k / 2:
        row_idx = int(np.argmax(relevance_total))
        if lvls[row_idx] != 20:
            if CHANGE:
                persist['changed'] = row_idx
            print()
            print('asdf', 0)  # placeholder to mirror your original print; no column in global relevance
            print(row_idx)
            print_artifact(artifacts[row_idx])
            print()
            return row_idx

    # Baseline per-target entropy H0(T,U)
    H0 = my_entropy(credits0, axis=0)                             # (T,U)
    information_gain = np.tile(H0[None, ...], (num_artifacts, 1, 1))  # (N,T,U)

    # Per-artifact evaluation (vectorized over upgrades)
    for i, artifact in enumerate(artifacts):
        if lvls[i] == 20:
            information_gain[i] = -10.0
            continue

        probs    = distros[i][1]          # (X,)
        upgrades = distros_scores[i]      # (X,T,U)
        base_i   = scores[i]              # (T,U)

        # Cutoffs per-upgrade (X,T,U)
        if k == 1:
            pass
        else:
            new_k_cutoff       = np.where(base_i < k_cutoff,       k_cutoff,       k_plus_cutoff)
            new_k_minus_cutoff = np.where(base_i < k_minus_cutoff, k_minus_cutoff, k_cutoff)
            potential = np.minimum(upgrades, new_k_minus_cutoff[None, ...])        # (X,T,U)
            cutoffs   = np.maximum(potential, new_k_cutoff[None, ...])             # (X,T,U)

        # Compare all items vs cutoffs, but swap in upgrades for item i
        cf = cutoffs[:, None, ...]                      # (X,1,T,U)
        above_all = (scores[None, ...] > cf)            # (X,N,T,U)
        eq_all    = (scores[None, ...] == cf)

        i_above = (upgrades > cutoffs)                  # (X,T,U)
        i_eq    = (upgrades == cutoffs)
        above_all[:, i, :, :] = i_above
        eq_all[:, i, :, :]    = i_eq

        # Per-upgrade per-target credits
        above_count = above_all.sum(axis=1)             # (X,T,U)
        leftover    = k - above_count
        tie_count   = eq_all.sum(axis=1)                # (X,T,U)
        frac_per_tie = np.divide(leftover, tie_count,
                                out=np.zeros_like(leftover, dtype=float),
                                where=(tie_count > 0))
        credits = above_all.astype(float) + eq_all * frac_per_tie[:, None, ...]  # (X,N,T,U)

        # Per-target entropy across artifacts for each upgrade → (X,T,U)
        ent = my_entropy(credits, axis=1)

        exp_ent = np.zeros((num_trials, num_targets))
        # Expected future entropy per-target
        for _, prob in enumerate(probs):
            exp_ent += prob * ent[_]
        #exp_ent = probs @ ent                           # (T,U)

        # IG per-target for artifact i
        information_gain[i] -= exp_ent                  # (T,U)                                 
    '''
        
    
    #information_gain[np.isclose(information_gain, 0)] = 0
    information_gain[information_gain < 0] = 0
    
    if np.isclose(np.max(information_gain), 0):
        print('damn')
        persist = {}
        asdf =  rank_entropy(artifacts, lvls, persist, targets, CHANGE, k, num_trials * 2, rng)
        persist = {}
        return asdf
    
    relevance = np.sum(information_gain, axis=1)
    
    #relevance /= np.where(lvls == 20, 1, UPGRADE_REQ_EXP[lvls])
    
    if np.sum(information_gain) == 0:
        print('fuck')
    
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
