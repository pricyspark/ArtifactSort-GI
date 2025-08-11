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
    
def rank_value(artifacts, lvls, persist, targets, k=2, num_trials=1000, rng=None, seed=None):
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
        persist['changed'] = None

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
        
    if persist['changed'] is not None:
        changed = persist['changed']
        try:
            _ = iter(changed)
        except:
            changed = [changed]
        for idx in changed:
            persist['maxed'][idx] = sample_upgrade(artifacts[idx], num_trials, lvl=lvls[idx], rng=rng)
            persist['scores'][idx] = score(persist['maxed'][idx], targets.T)
        
    scores = persist['scores']
    
    if num_artifacts <= k:
        relevance = np.full((num_artifacts), num_trials, dtype=float)
        relevance /= np.where(lvls == 20, 1, MAX_REQ_EXP[lvls])
        
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
    if np.max(relevance) == 0:
        print('max was 0')
        for i in range(num_artifacts):
            persist['maxed'][i] = sample_upgrade(artifacts[i], num_trials, lvl=lvls[i], rng=rng)
        persist['targets'] = None
        persist['changed'] = -1
        return rank_value(artifacts, lvls, persist, targets, k, num_trials, rng)
        
    return relevance

def rank_entropy(artifacts, lvls, persist, targets, k=2, num_trials=200, rng=None, seed=None):
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
                
        persist['changed'] = None
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
                        
    if persist['changed'] is not None:
        changed = persist['changed']
        try:
            _ = iter(changed)
        except:
            changed = [changed]
        for idx in changed:
            persist['maxed'][idx] = sample_upgrade(artifacts[idx], num_trials, lvl=lvls[idx], rng=rng)
            persist['scores'][idx]= score(persist['maxed'][idx], targets.T)
            
            if lvls[idx] == 20:
                persist['distros'][idx] = None
                persist['distros_maxed'][idx] = None
                persist['distros_scores'][idx] = None
            else:
                next = next_lvl(lvls[idx])
                
                upgrades, probs = single_distro(artifacts[idx])
                persist['distros'][idx] = (upgrades, probs)
                
                distro_maxed = persist['distros_maxed'][idx]
                if len(distro_maxed) != len(upgrades):
                    persist['distros_maxed'][idx] = np.zeros((len(upgrades), num_trials, 19), dtype=np.uint8)

                for i, upgrade in enumerate(upgrades):
                    persist['distros_maxed'][idx][i] = sample_upgrade(upgrade, num_trials, lvl=next, rng=rng)
                    
                persist['distros_scores'][idx] = score(persist['distros_maxed'][idx], targets.T)
            
    scores, distros, distros_scores = persist['scores'], persist['distros'], persist['distros_scores']
    
    if num_artifacts <= k:
        relevance = np.full((num_artifacts), num_trials, dtype=float)
        relevance /= np.where(lvls == 20, 1, MAX_REQ_EXP[lvls])
        
        #if CHANGE:
        #    persist['changed'] = np.argmax(relevance)
        return relevance
    
    if k == 1:
        pass
    elif k == 2:
        k_plus_cutoff, k_cutoff, k_minus_cutoff = np.partition(scores, (-k - 1, -k, -k + 1), axis=0)[-k - 1:] # (T,U)
    else:
        k_plus_cutoff, k_cutoff, k_minus_cutoff = np.partition(scores, (-k - 1, -k, -k + 1), axis=0)[-k - 1:-k + 1]

    above = scores > k_cutoff           # (N,T,U)
    eq = scores == k_cutoff             # (N,T,U)
    above_count = above.sum(axis=0)     # (T,U)
    leftover = k - above_count          # (T,U)
    eq_count = eq.sum(axis=0)           # (T,U)
    frac_per_tie = leftover / eq_count  # (T,U)
    points_eq = eq * frac_per_tie[None, ...] # (N,T,U)
    points = above.astype(float) + points_eq # (N,T,U)

    base_relevance = points.sum(axis=1) # (N,U)
    if np.max(base_relevance) > k / 2:
        flat_idx = base_relevance.argmax()
        row_idx = flat_idx // base_relevance.shape[1]
        if lvls[row_idx] != 20:
            print()
            print('early stop', flat_idx % base_relevance.shape[1])
            print(row_idx)
            print_artifact(artifacts[row_idx])
            print()
            return row_idx
        
    base_entropy = entropy(base_relevance, axis=0) # (U,)
    information_gain = np.tile(base_entropy, (num_artifacts, 1)) # (N,U)
    
    if np.max(information_gain) == np.inf:
        raise ValueError

    for i in range(len(artifacts)):
        if lvls[i] == 20:
            information_gain[i] = 0
            continue
        
        probs = distros[i][1]           # (X,)
        upgrades = distros_scores[i]    # (X,T,U)
        
        upgrades = upgrades[probs != 0]
        probs = probs[probs != 0]
        
        num_upgrades = len(upgrades)
        
        original = scores[i]            # (T,U)

        if k == 1:
            pass
        else:
            new_k_cutoff        = np.where(original < k_cutoff, k_cutoff, k_plus_cutoff)        # (T,U)
            new_k_minus_cutoff  = np.where(original < k_minus_cutoff, k_minus_cutoff, k_cutoff) # (T,U)
            potential           = np.minimum(upgrades, new_k_minus_cutoff[None, ...])           # (X,T,U)
            cutoffs             = np.maximum(potential, new_k_cutoff[None, ...])                # (X,T,U)
            
        upgrades_above  = upgrades > cutoffs    # (X,T,U)
        upgrades_eq     = upgrades == cutoffs   # (X,T,U)
        
        original_above = above[i]   # (T,U)
        original_eq = eq[i]         # (T,U)
        
        same_mask = (
            (upgrades_above == original_above[None, ...]) & 
            (upgrades_eq == original_eq[None, ...]) &
            (cutoffs == k_cutoff[None, ...])
        )                       # (X,T,U)
        diff_mask = ~same_mask  # (X,T,U)
        
        x, t, u = np.where(same_mask)
        nx, nt, nu = np.where(diff_mask)
        
        cutoffs_all = cutoffs[:, None, ...]             # (X,1,T,U)
        above_all   = scores[None, ...] > cutoffs_all   # (X,N,T,U)
        eq_all      = scores[None, ...] == cutoffs_all  # (X,N,T,U)
        
        above_all[:, i, ...]    = upgrades_above
        eq_all[:, i, ...]       = upgrades_eq
        
        above_count_all = np.zeros((num_upgrades, num_trials, num_targets)) # (X,T,U)
        above_count_all[x, t, u] = above_count[t, u]
        above_count_all[nx, nt, nu] = above_all[nx, :, nt, nu].sum(axis=1)
        
        eq_count_all = np.zeros((num_upgrades, num_trials, num_targets))    # (X,T,U)
        eq_count_all[x, t, u] = eq_count[t, u]
        eq_count_all[nx, nt, nu] = eq_all[nx, :, nt, nu].sum(axis=1)
        
        leftover_all        = k - above_count_all           # (X,T,U)
        frac_per_tie_all    = leftover_all / eq_count_all   # (X,T,U)
        
        base = above.sum(axis=1)[None, ...]          # (1, N, U)
        relevance_above = np.broadcast_to(base, (above_all.shape[0],) + base.shape[1:]).copy()
        for x in range(above_all.shape[0]):
            t_idx, u_idx = np.where(diff_mask[x])    # ~Kx positions
            if t_idx.size == 0:
                continue
            contrib = above_all[x, :, t_idx, u_idx].astype(int).T - above[:, t_idx, u_idx].astype(int) # (N, Kx)
            np.add.at(relevance_above[x], (slice(None), u_idx), contrib)
            
        base = points_eq.sum(axis=1)[None, ...] # (1,N,U)
        relevance_ties = np.broadcast_to(base, (eq_all.shape[0],) + base.shape[1:]).copy()
        idk = eq_all * frac_per_tie_all[:, None, ...]
        for x in range(eq_all.shape[0]):
            t_idx, u_idx = np.where(diff_mask[x])
            if t_idx.size == 0:
                continue
            contrib = (idk[x, :, t_idx, u_idx]).T - points_eq[:, t_idx, u_idx]
            np.add.at(relevance_ties[x], (slice(None), u_idx), contrib)
        relevance_ties[np.isclose(relevance_ties, 0)] = 0
        
        relevance_all   = relevance_above + relevance_ties      # (X,N,U)
        entropy_all         = entropy(relevance_all, axis=1)    # (X,U)
        expected_entropy    = probs @ entropy_all               # (U,)
        information_gain[i] -= expected_entropy                 # (N,U)
            
    #information_gain[np.isclose(information_gain, 0)] = 0
    information_gain[information_gain < 0] = 0
    
    if np.isclose(np.max(information_gain), 0):
        print('damn')
        persist = {}
        asdf =  rank_entropy(artifacts, lvls, persist, targets, k, num_trials * 2, rng)
        persist = {}
        return asdf
    
    relevance = np.sum(information_gain, axis=1)
    
    #relevance /= np.where(lvls == 20, 1, UPGRADE_REQ_EXP[lvls])
    
    print()
    print(changed)
    print_artifact(artifacts[changed])
    print(information_gain[changed])
    print()
    
    return relevance
    
if __name__ == '__main__':
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
        totals[i] = (simulate_exp(artifacts, np.zeros(50, dtype=int), targets, rank_value))
        print(i, totals[i])
        print()

    cumsum = np.cumsum(totals)
    for i in range(len(cumsum)):
        time_avg[i] = cumsum[i] / (i + 1)
        
    print(time_avg[-1])
    end = time.time()
    print(end - start)
    '''

    '''
    '''
    start = time.time()
    filename = 'artifacts/genshinData_GOOD_2025_07_31_18_01.json'
    artifacts, slots, rarities, lvls, sets = load(filename)
    relevant = rate(artifacts, slots, rarities, lvls, sets, rank_value, num=100)
    
    count = 0
    
    visualize(relevant, artifacts, slots, sets, lvls)
    end = time.time()
    print(end - start)