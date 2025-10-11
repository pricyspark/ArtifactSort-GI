import numpy as np
from analyze import *
import time
from scipy.stats import entropy
import statistics
np.seterr(all='raise')
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
    # TODO: this has an issue with nan, check if this is a problem and
    # solve if needed
    #mask = array > 0
    #return -np.sum(array[mask] * np.log(array[mask]), axis=axis)
    #return -np.sum(array * np.log(array, where=array != 0, out=np.zeros_like(array)), axis=axis)
    return -np.sum(array * np.log(array, out=np.zeros_like(array), where=array != 0), axis=axis)
    #return -np.sum(np.where(array > 0, array * np.log(array), 0.0), axis=axis)

def winner_prob(scores, cutoff, k):
    # TODO: instead of dividing ties, tiebreak using highest lvl
    eq = scores == cutoff                       # (N,T,U)
    eq_count = eq.sum(axis=0)                   # (T,U)
    
    if k == 1:
        frac_per_tie = 1 / eq_count                 # (T,U)
        points_eq = eq * frac_per_tie[None, ...]    # (N,T,U)
        return points_eq                            # (N,T,U)
    
    above = scores > cutoff                     # (N,T,U)
    above_count = above.sum(axis=0)             # (T,U)
    leftover = k - above_count                  # (T,U)
    frac_per_tie = leftover / eq_count          # (T,U)
    points_eq = eq * frac_per_tie[None, ...]    # (N,T,U)
    return above + points_eq                    # (N,T,U)

def new_estimate_exp(probs, slvls):
    exp_max = MAX_REQ_EXP[slvls]
    exp_learn = LEARN_REQ_EXP[slvls]
    
    scores = probs.sum(axis=1) / np.maximum(1.0, exp_max)
    order  = np.argsort(scores)[::-1]

    total = 0.0
    taken = np.zeros(probs.shape[1], dtype=float)  # == (1 - remaining_prob)
    coef = 1.0
    #print('start')
    for idx in order:
        prob_here = 1.0 - np.prod(taken)
        #print(taken)
        #print(prob_here)
        if prob_here < 0.001:
            break
        
        prob_learn = np.prod(1 - probs[idx])
        prob_max = 1 - prob_learn
        total += prob_here * (prob_max * exp_max[idx] + prob_learn * exp_learn[idx])
        taken += coef * probs[idx]  # in-place
        coef *= 1.1
        taken = np.minimum(taken, 1)
    #print('end')
    return total

def estimate_exp(probs, exp):
    # rank once; scores don't change in the loop
    scores = probs.sum(axis=1) / np.maximum(1.0, exp)
    order  = np.argsort(scores)[::-1]

    total = 0.0
    taken = np.zeros(probs.shape[1], dtype=float)  # == (1 - remaining_prob)
    for idx in order:
        prob_here = 1.0 - np.prod(taken)
        if prob_here < 0.001:
            break
        
        total += prob_here * exp[idx]
        taken += probs[idx]  # in-place
        
    #if total == 0:
    #    return estimate_exp(probs, exp)

    '''
    Honestly, I don't understand how this current ChatGPT speedup works.
    This is my original code for reference.
    
    # probs (N,U)
    total_exp = 0
    num_artifacts, num_targets = probs.shape
    
    scores = np.sum(probs, axis=1) / np.maximum(1, exp)
    args = np.argsort(scores)[::-1]
    
    overall_prob = np.ones(num_targets, dtype=float)
    remaining_prob = np.ones(num_targets, dtype=float)
    for idx in args:
        prob_not_here = 1 - overall_prob
        prob_here = 1 - np.prod(prob_not_here)
        if prob_here < 0.001:
            break
        
        total_exp += prob_here * exp[idx]
        temp = np.divide(probs[idx], remaining_prob, out=np.zeros_like(remaining_prob), where=remaining_prob != 0)
        
        prob_continue = 1 - temp
        overall_prob *= prob_continue
        remaining_prob -= probs[idx]
        
    return total_exp
    '''
    return total

def rank_value(artifacts, slvls, persist, targets, k=1, base_trials=500, rng=None, seed=None):
    '''Estimate probability artifact is in top k for given targets, and
    sort based on p/(cost to max). If artifacts upgraded straight to
    max, this would be optimal. 
    '''
    # Format inputs
    num_artifacts = len(artifacts)
    try:
        _ = iter(slvls)
        slvls = np.array(slvls)
    except:
        if slvls is None:
            slvls = 0
        slvls = np.full(num_artifacts, slvls)
    
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

    # Prepare RNG
    if rng is None:
        rng = np.random.default_rng(seed)
    
    # Initialize persist with artifacts
    if len(persist) == 0:
        persist['changed'] = []

        maxed = np.zeros((num_artifacts, base_trials, 19), dtype=np.uint8)   # (N,T,19)
        for i in range(num_artifacts):
            maxed[i], _ = sample_upgrade(artifacts[i], base_trials, slvl=slvls[i], rng=rng)
        persist['maxed'] = maxed
        persist['targets'] = None
        
        # Hoeffding bound for 99% confidence
        persist['epsilon'] = np.sqrt(2 * np.log((num_artifacts - 1) / 0.01) / base_trials)
        
    num_trials = persist['maxed'].shape[1]
    
    # Score artifacts if needed
    if not np.array_equal(persist['targets'], targets):
        persist['targets'] = targets
        persist['scores'] = score(persist['maxed'], targets.T)

    # Update changed artifacts
    if len(persist['changed']) != 0:
        changed = persist['changed']
        try:
            _ = iter(changed)
        except:
            changed = [changed]
        for idx in changed:
            persist['maxed'][idx], _ = sample_upgrade(artifacts[idx], num_trials, slvl=slvls[idx], rng=rng)
            persist['scores'][idx] = score(persist['maxed'][idx], targets.T)
            
        persist['changed'] = []

    # If not enough artifacts, everything wins
    if num_artifacts <= k:
        value = np.full((num_artifacts), num_trials, dtype=float)
        value /= np.where(slvls == 20, 1, MAX_REQ_EXP[slvls])
        
        return value
    
    # ------------------------------------------------------------------
    # START COMPUTATION
    # ------------------------------------------------------------------

    scores, epsilon = persist['scores'], persist['epsilon']
    
    # Calculate winning score cutoffs
    if k == 1:
        cutoff = scores.max(axis=0)                             # (T,U)
    else:
        cutoff = np.partition(scores, -k, axis=0)[-k]           # (T,U)

    # Calculate winning probabilities
    winners = winner_prob(scores, cutoff, k)                # (N,T,U)
    p = np.mean(winners, axis=1)   # (N,U)

    # Check if we need more trials using Hoeffding bound
    chosen = rival = None
    if k == 1:
        #temp = np.argpartition(p, (-3, -2, -1), axis=0)    # (N,U)
        asdf, rival, chosen = np.argpartition(p, (-3, -2, -1), axis=0)[-3:]           # (2,U)
        if np.all(slvls[chosen] == 20):
            print('max')
            chosen = p[rival]
            rival = p[asdf]       
        else:
            chosen = p[chosen]
            rival = p[rival]         
    else:
        temp = np.partition(p, (-k-1, -k), axis=0)           # (2,U)
        rival = temp[-k-1]
        chosen = temp[-k]
    if np.all(chosen - rival < epsilon):
        # TODO: add memory limit in case of infinite recursion
        persist.clear() # Inefficiently deletes current artifacts instead of appending new trials
        print('doubling trials to', num_trials * 2)
        return rank_value(artifacts, slvls, persist, targets, k, num_trials * 2, rng)
    '''
    '''
    '''
    
    if np.all(slvls[chosen] == 20):
        print('All chosen are maxed')
        print('chosen:', p[chosen[0]])
        print('rival:', p[rival])
    
    if np.all(p[chosen[0]] - p[rival] < epsilon):
        # TODO: add memory limit in case of infinite recursion
        persist.clear() # Inefficiently deletes current artifacts instead of appending new trials
        print('doubling trials to', num_trials * 2)
        return rank_value(artifacts, slvls, persist, targets, k, num_trials * 2, rng)
    '''
    
    # Enough trials, continue
    #total_p = p.sum(axis=1)   # (N,)
    total_p = 1 - np.prod(1 - p, axis=1) # (N,)
    
    # Dollarize probabilities
    value = total_p / np.maximum(1, MAX_REQ_EXP[slvls])
    
    '''
    value[slvls == 20] = -99999999
    choose = np.argmax(value)
    print('choose', choose)
    print(p[choose])
    '''
    
    return value

def rank_entropy(artifacts, slvls, persist, targets, k=1, num_trials=2000, rng=None, seed=None, value_threshold=0):
    num_artifacts = len(artifacts)
    try:
        _ = iter(slvls)
        slvls = np.array(slvls)
    except:
        if slvls is None:
            slvls = 0
        slvls = np.full(num_artifacts, slvls)
    
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
        tape_values = []
        tapes = []
        #tapes = np.zeros((num_artifacts, num_trials, 5), dtype=np.uint8)
        for i in range(num_artifacts):
            maxed[i], tape = sample_upgrade(artifacts[i], num_trials, slvl=slvls[i], rng=rng)
            tapes.append(tape)
            tape_values.append((find_sub(artifacts[i])[:, None] * 4 + np.arange(4)).flatten())
                
        persist['changed'] = []
        persist['maxed'] = maxed
        persist['tape_values'] = tape_values
        persist['tapes'] = tapes
        persist['targets'] = None
        
    if not np.array_equal(persist['targets'], targets):
        persist['targets'] = targets
        persist['scores'] = score(persist['maxed'], targets.T)
        
    if len(persist['changed']) != 0:
        changed = persist['changed']
        try:
            _ = iter(changed)
        except:
            changed = [changed]
        for idx in changed:
            persist['maxed'][idx], persist['tapes'][idx] = sample_upgrade(artifacts[idx], num_trials, slvl=slvls[idx], rng=rng)
            persist['scores'][idx]= score(persist['maxed'][idx], targets.T)
            
            if slvls[idx] == 20:
                persist['tape_values'][idx] = None
                
        persist['changed'] = []
            
    scores, tape_values, tapes = persist['scores'], persist['tape_values'], persist['tapes']
    
    if num_artifacts <= k:
        relevance = np.full((num_artifacts), num_trials, dtype=float)
        relevance /= np.where(slvls == 20, 1, MAX_REQ_EXP[slvls])
        
        return relevance
    
    if k == 1:
        cutoff = np.max(scores, axis=0)
    else:
        cutoff = np.partition(scores, -k, axis=0)[-k] # (T,U)

    winners = winner_prob(scores, cutoff, k)                # (N,T,U)
    p = np.mean(winners, axis=1)   # (N,U)
    
    total_p = np.sum(p, axis=1)
    
    if np.max(p) >= 0.5: # After 1 solved target, this is always true. Thhis is bad
        print('value')
        value = total_p / np.maximum(1, MAX_REQ_EXP[slvls])
        return value
    print('entropy')
    #print('prob', np.max(total_p[slvls != 20]))
    #value = total_p / np.maximum(1, MAX_REQ_EXP[slvls])
    #value[slvls == 20] = -99999999
    #value_choice = np.argmax(value)
    #print('value', np.max(value[slvls != 20]))
    base_entropy = my_entropy(p, axis=0)  # (U,)
    #base_entropy = entropy(p, axis=0)  # (U,)
    
    information_gain = np.tile(base_entropy[None, :], (num_artifacts, 1))
    #prob_diff = np.zeros((num_artifacts, num_targets), dtype=float)
    #estimate_exps = UPGRADE_REQ_EXP[slvls]
    
    #original_estimate_exp = estimate_exp(base_relevance,
    #MAX_REQ_EXP[lvls]
    
    '''
    a, b = np.argpartition(scores, -2, axis=0)[-2:] # (T,U)
    second = scores[a, *np.indices(a.shape)] # (T,U)
    first = scores[b, *np.indices(b.shape)] # (T,U)
    '''
    
    #asdf_mask = win_prob > 0
    
    '''
    splits = np.array_split(winners, 16, axis=1)
    temp_entropy = np.zeros(num_targets, dtype=float)
    for split in splits:
        split_p = np.mean(split, axis=1)  # (N,U)
        split_entropy = entropy(split_p, axis=0)
        temp_entropy += split.shape[1] / num_trials * split_entropy
    '''
        
    for i in range(len(artifacts)):
        #print(i)
        if slvls[i] == 20:
            continue
        
        '''
        ub = -np.log(p[i], out=np.zeros(num_targets, dtype=float), where=p[i] != 0) * p[i]   # (U,)
        
        if not np.any(ub >= temp_entropy):
            continue
        print('possible')
        '''
        tape = tapes[i]                                 # (T,X)
        masks = tape_values[i][:, None] == tape[:, 0]   # (T,)
        
        temp_slvls = slvls.copy()
        temp_slvls[i] = next_lvl(temp_slvls[i])
        
        for mask in masks:
            prob = np.mean(mask)
            if prob == 0:
                continue
            
            potential_points = np.mean(winners[:, mask, :], axis=1)   # (N,U)
            potential_entropy = my_entropy(potential_points, axis=0)
            #potential_entropy = entropy(potential_points, axis=0)
            information_gain[i] -= prob * potential_entropy
        '''
        print(base_entropy - temp_entropy)
        print(ub)
        print(information_gain[i])
        '''
            
    information_gain = np.linalg.norm(information_gain, axis=1) # (N,)
    information_gain[slvls == 20] = -999999
    information_gain /= np.maximum(1, UPGRADE_REQ_EXP[slvls])
    return information_gain
    #print('IG choice', IG_choice)
    '''
    if estimate_exps[IG_choice] * 1.05 < estimate_exps[value_choice]:
        print('entropy', estimate_exps[IG_choice], estimate_exps[value_choice])
        return information_gain
    print('value', estimate_exps[IG_choice], estimate_exps[value_choice])
    '''
    return value

def rank_combine(artifacts, lvls, persist, targets, k=2, num_trials=100, rng=None, seed=None):
    num_artifacts = len(artifacts)
    
    match targets: # This is only here in case num_targets is needed
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
        value_persist = {}
        entropy_persist = {}
        
        persist['value'] = value_persist
        persist['entropy'] = entropy_persist
        persist['changed'] = []
        persist['value_changed'] = []
        persist['entropy_changed'] = []
        
    if len(persist['changed']) != 0:
        changed = persist['changed']
        try:
            persist['value']['changed'] += changed
        except:
            pass
        try:
            persist['entropy']['changed'] += changed
        except:
            pass
        
        
    value_persist, entropy_persist = persist['value'], persist['entropy']
        
    beta = 0.05
    value_relevance = rank_value(artifacts, lvls, value_persist, targets, k, 1000, rng, save_entropy=True)
    if k == 1:
        a, b = np.partition(value_relevance[lvls != 20], (-2, -1))[-2:]
    else:
        a, b = np.partition(value_relevance[lvls != 20], (-k-1, -k))[-k-1:-k+1]
    max_entropy = value_persist['entropy']
    #what = 
    max_entropy_relevance = beta * max_entropy / UPGRADE_REQ_EXP[0] * 0.5
    #if b - a > -beta * np.log(1/num_artifacts):
    diff = b - a
    if diff > max_entropy_relevance:
        #print('       skipped')
        return value_relevance
    
    '''
    print('       not skipped')
    print(diff)
    print(max_entropy_relevance)
    '''
    #print(-np.log(1/num_artifacts) * beta * np.sqrt(num_targets) / UPGRADE_REQ_EXP[0])
    value_threshold = b - max_entropy_relevance
    entropy_relevance = rank_entropy(artifacts, lvls, entropy_persist, targets, k, num_trials, rng, value_threshold=value_threshold)
    
    '''
    (x + y)^2 = xy
    x^2 + 2xy + y^2 = xy
    
    print()
    value_relevance[lvls == 20] = 0
    try:
        entropy_relevance[lvls == 20] = 0
    except:
        pass
    print(value_relevance)
    print(entropy_relevance)
    print('value', np.max(value_relevance))
    print('entropy', np.max(entropy_relevance))
    print()
    '''
    
    
    return value_relevance + beta * entropy_relevance

def rank_evsi_prob(artifacts, lvls, persist, targets, k=2, num_trials=500, rng=None, seed=None):
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
            maxed[i], tape = sample_upgrade(artifacts[i], num_trials, lvl=lvls[i], rng=rng)
        
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
                distros_maxed[-1][j], tape = sample_upgrade(upgrade, num_trials, lvl=next, rng=rng)
                
        persist['changed'] = []
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
        
    if len(persist['changed']) != 0:
        changed = persist['changed']
        try:
            _ = iter(changed)
        except:
            changed = [changed]
        for idx in changed:
            persist['maxed'][idx], tape = sample_upgrade(artifacts[idx], num_trials, lvl=lvls[idx], rng=rng)
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
                    persist['distros_maxed'][idx][i], tape = sample_upgrade(upgrade, num_trials, lvl=next, rng=rng)
                    
                persist['distros_scores'][idx] = score(persist['distros_maxed'][idx], targets.T)
                
        persist['changed'] = []
            
    scores, distros, distros_scores = persist['scores'], persist['distros'], persist['distros_scores']
    
    if num_artifacts <= k:
        relevance = np.full((num_artifacts), num_trials, dtype=float)
        
        return relevance
    
    if k == 1:
        k_plus_cutoff, k_cutoff = np.partition(scores, -2, axis=0)[-2:]
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
    base_relevance  = above + points_eq     # (N,T,U)
    
    asdf = np.mean(base_relevance, axis=1)   # (N,U)
    asdf = np.max(asdf, axis=0)            # (U,)
    start_prob = asdf
    #start_prob = np.sum(asdf)
    #print(value_threshold)
    #value_threshold = 1e-08

    prob_diff = np.zeros((num_artifacts, num_targets), dtype=float)

    for i in range(len(artifacts)):
        if lvls[i] == 20:
            continue
        
        probs = distros[i][1]           # (X,)
        upgrades = distros_scores[i]    # (X,T,U)
        
        upgrades = upgrades[probs != 0]
        probs = probs[probs != 0]
        
        num_upgrades = len(upgrades)
        
        original = scores[i]            # (T,U)

        if k == 1:
            new_k_cutoff        = np.where(original < k_cutoff, k_cutoff, k_plus_cutoff)        # (T,U)
            cutoffs             = np.maximum(upgrades, new_k_cutoff[None, ...])                # (X,T,U)
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
        '''
        above_count_all = np.sum(above_all, axis=1) # (X,T,U)
        leftover = k - above_count_all
        
        tie_count_all = np.sum(eq_all, axis=1)  # (X,T,U)
        frac_per_tie_all = leftover / tie_count_all # (X,T,U)
        
        eq_contrib = eq_all * frac_per_tie_all[:, None, ...] # (X,N,T,U)
        
        target = np.sum(above_all + eq_contrib, axis=2) # (X,N,U)
        '''
        
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
        
        relevance_all   = (relevance_above + relevance_ties) / num_trials   # (X,N,U)
        
        #print('total', np.sum(relevance_all))
        max_prob = np.max(relevance_all, axis=1)    # (X,U)
        #temp = np.sum(max_prob, axis=1) # (X,)
        
        current_prob = probs @ max_prob # (U,)
        
        prob_diff[i] = current_prob - start_prob
    
    '''
    if np.max(prob_diff[lvls != 20]) < 3e-06:
        value_relevance = np.sum(base_relevance, axis=(1, 2))
        #value_relevance /= num_trials
        value_relevance /= np.where(lvls == 20, 1, MAX_REQ_EXP[lvls])
        
        if np.max(value_relevance[lvls != 20]) == 0:
            print('max was 0')
            for i in range(num_artifacts):
                persist['maxed'][i] = sample_upgrade(artifacts[i], num_trials, lvl=lvls[i], rng=rng)
            persist['targets'] = None
            persist['changed'] = []
            return rank_value(artifacts, lvls, persist, targets, k, num_trials, rng)
        
        return value_relevance
    '''    
    if np.max(prob_diff[lvls != 20]) < 0.02:
        return rank_value(artifacts, lvls, persist, targets, k, num_trials, rng)
    #prob_diff /= np.where(lvls == 20, 1, UPGRADE_REQ_EXP[lvls])
    print('prob diff')
    print(prob_diff)
    print(np.max(prob_diff[lvls != 20]))
    print(np.min(prob_diff[lvls != 20]))
    
    a = np.sum(prob_diff, axis=1)
    return np.sum(prob_diff, axis=1)
    #return prob_diff
    
def rank_estimate(artifacts, slvls, persist, targets, k=1, num_trials=1000, rng=None, seed=None):
    num_artifacts = len(artifacts)
    try:
        _ = iter(slvls)
        slvls = np.array(slvls)
    except:
        if slvls is None:
            slvls = 0
        slvls = np.full(num_artifacts, slvls)
    
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
        tape_values = []
        tapes = []
        #tapes = np.zeros((num_artifacts, num_trials, 5), dtype=np.uint8)
        for i in range(num_artifacts):
            maxed[i], tape = sample_upgrade(artifacts[i], num_trials, slvl=slvls[i], rng=rng)
            tapes.append(tape)
            tape_values.append((find_sub(artifacts[i])[:, None] * 4 + np.arange(4)).flatten())
                
        persist['changed'] = []
        persist['maxed'] = maxed
        persist['tape_values'] = tape_values
        persist['tapes'] = tapes
        persist['targets'] = None
        
    if not np.array_equal(persist['targets'], targets):
        persist['targets'] = targets
        persist['scores'] = score(persist['maxed'], targets.T)
        
    if len(persist['changed']) != 0:
        changed = persist['changed']
        try:
            _ = iter(changed)
        except:
            changed = [changed]
        for idx in changed:
            persist['maxed'][idx], persist['tapes'][idx] = sample_upgrade(artifacts[idx], num_trials, slvl=slvls[idx], rng=rng)
            persist['scores'][idx]= score(persist['maxed'][idx], targets.T)
            
            if slvls[idx] == 20:
                persist['tape_values'][idx] = None
                
        persist['changed'] = []
            
    scores, tape_values, tapes = persist['scores'], persist['tape_values'], persist['tapes']
    
    if num_artifacts <= k:
        relevance = np.full((num_artifacts), num_trials, dtype=float)
        
        return relevance
    
    if k == 1:
        k_cutoff = np.max(scores, axis=0)
    else:
        k_cutoff = np.partition(scores, -k, axis=0)[-k] # (T,U)
    
    above, eq = winner_prob(scores, k_cutoff, k)    # (N,T,U)
    winners = above + eq
    estimate_exps = UPGRADE_REQ_EXP[slvls]
    
    for i in range(len(artifacts)):
        if slvls[i] == 20:
            continue
        
        tape = tapes[i]
        masks = tape_values[i][:, None] == tape[:, 0]
        
        temp_slvls = slvls.copy()
        temp_slvls[i] = next_lvl(temp_slvls[i])
        
        for mask in masks:
            prob = np.mean(mask)
            if prob == 0:
                continue
            
            potential_points = np.mean(winners[:, mask, :], axis=1)   # (N,U)
            potential_exp = estimate_exp(potential_points, MAX_REQ_EXP[temp_slvls])
            estimate_exps[i] += prob * potential_exp
    #print()
    #print('min estimate exp:', np.min(potential_estimate_exps[lvls != 20]))
    return -estimate_exps

def rank_new(artifacts, slvls, persist, targets, k=1, num_trials=2000, rng=None, seed=None):
    num_artifacts = len(artifacts)
    try:
        _ = iter(slvls)
        slvls = np.array(slvls)
    except:
        if slvls is None:
            slvls = 0
        slvls = np.full(num_artifacts, slvls)
    
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
        tape_values = []
        tapes = []
        #tapes = np.zeros((num_artifacts, num_trials, 5), dtype=np.uint8)
        for i in range(num_artifacts):
            maxed[i], tape = sample_upgrade(artifacts[i], num_trials, slvl=slvls[i], rng=rng)
            tapes.append(tape)
            tape_values.append((find_sub(artifacts[i])[:, None] * 4 + np.arange(4)).flatten())
                
        persist['changed'] = []
        persist['maxed'] = maxed
        persist['tape_values'] = tape_values
        persist['tapes'] = tapes
        persist['targets'] = None
        
    if not np.array_equal(persist['targets'], targets):
        persist['targets'] = targets
        persist['scores'] = score(persist['maxed'], targets.T)
        
    if len(persist['changed']) != 0:
        changed = persist['changed']
        try:
            _ = iter(changed)
        except:
            changed = [changed]
        for idx in changed:
            persist['maxed'][idx], persist['tapes'][idx] = sample_upgrade(artifacts[idx], num_trials, slvl=slvls[idx], rng=rng)
            persist['scores'][idx]= score(persist['maxed'][idx], targets.T)
            
            if slvls[idx] == 20:
                persist['tape_values'][idx] = None
                
        persist['changed'] = []
            
    scores, tape_values, tapes = persist['scores'], persist['tape_values'], persist['tapes']
    
    if num_artifacts <= k:
        relevance = np.full((num_artifacts), num_trials, dtype=float)
        
        return relevance
    
    if k == 1:
        k_cutoff = np.max(scores, axis=0)
    else:
        k_cutoff = np.partition(scores, -k, axis=0)[-k] # (T,U)
    
    winners = winner_prob(scores, k_cutoff, k)    # (N,T,U)
    p = np.mean(winners, axis=1)    # (N,U)
    
    if np.max(p) >= 0.5:
        total_p = p.sum(axis=1)
        value = total_p / np.where(slvls == 20, 1, MAX_REQ_EXP[slvls])
        print('CONFIDENT')
        return value
    
    print('NOT CONFIDENT')
    mu = np.mean(scores, axis=1)    # (N,U)
    
    idx2, idx1 = np.argpartition(mu, -2, axis=0)[-2:]  # (U)
    m2 = mu[idx2, np.arange(num_targets)]
    m1 = mu[idx1, np.arange(num_targets)]
    mask = np.arange(num_artifacts)[:, None] == idx1[None, :]   # (N,U)
    #second = scores[a, *np.indices(a.shape)] # (T,U)
    #first = scores[b, *np.indices(b.shape)] # (T,U)
    m_except = np.where(mask, m2, m1)   # (N,U)
    asdf = p * (mu - m_except)
    fin = np.maximum(asdf, 0) / np.maximum(1, MAX_REQ_EXP[slvls][:, None]) # (N,U)
    
    total_p = p.sum(axis=1)
    value = total_p / np.where(slvls == 20, 1, MAX_REQ_EXP[slvls])
    value_choice = np.argmax(value)
    
    asdf = np.linalg.norm(fin, axis=1)  # (N,)
    fin_choice = np.argmax(asdf)
    
    if value_choice == fin_choice:
        print('match')
    else:
        print('diff')
        
    return np.linalg.norm(fin, axis=1)  # (N,)
    
    h = entropy(p, axis=0)  # (U,)
    
    #base_entropy = entropy(base_relevance, axis=0)  # (U,)
    
    ig = np.tile(h[None, :], (num_artifacts, 1))    # (N,U)
    for i in range(len(artifacts)):
        if slvls[i] == 20:
            continue
        
        tape = tapes[i]                                 # (T,X)
        masks = tape_values[i][:, None] == tape[:, 0]   # (T,)
        temp_slvls = slvls.copy()
        temp_slvls[i] = next_lvl(temp_slvls[i])
        
        for mask in masks:
            prob = np.mean(mask)
            if prob == 0:
                continue
            
            potential_points = np.mean(winners[:, mask, :], axis=1)   # (N,U)
            potential_entropy = entropy(potential_points, axis=0)
            ig[i] -= prob * potential_entropy
    
    evsi = ig / UPGRADE_REQ_EXP[slvls][:, None]
    print()
    
    
def rank_temp(artifacts, lvls, persist, targets, k=1, num_trials=1000, rng=None, seed=None):
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
        tape_values = []
        tapes = []
        #tapes = np.zeros((num_artifacts, num_trials, 5), dtype=np.uint8)
        for i in range(num_artifacts):
            maxed[i], tape = sample_upgrade(artifacts[i], num_trials, lvl=lvls[i], rng=rng)
            tapes.append(tape)
        
            if np.count_nonzero(artifacts[i]) == 4:
                possible_substats = np.where(artifacts[i, :10] == 0)[0]
                tape_values.append((possible_substats[:, None] * 4 + np.arange(4)).flatten())
            else:
                tape_values.append((find_sub(artifacts[i])[:, None] * 4 + np.arange(4)).flatten())
                
        persist['changed'] = []
        persist['maxed'] = maxed
        persist['tape_values'] = tape_values
        persist['tapes'] = tapes
        persist['targets'] = None
        
    if not np.array_equal(persist['targets'], targets):
        persist['targets'] = targets
        persist['scores'] = score(persist['maxed'], targets.T)
        
    if len(persist['changed']) != 0:
        changed = persist['changed']
        try:
            _ = iter(changed)
        except:
            changed = [changed]
        for idx in changed:
            persist['maxed'][idx], persist['tapes'][idx] = sample_upgrade(artifacts[idx], num_trials, lvl=lvls[idx], rng=rng)
            persist['scores'][idx]= score(persist['maxed'][idx], targets.T)
            
            if lvls[idx] == 20:
                persist['tape_values'][idx] = None
            elif lvls[idx] == 4:
                persist['tape_values'][idx] = (find_sub(artifacts[idx])[:, None] * 4 + np.arange(4)).flatten()
                
        persist['changed'] = []
            
    scores, tape_values, tapes = persist['scores'], persist['tape_values'], persist['tapes']
    
    if num_artifacts <= k:
        relevance = np.full((num_artifacts), num_trials, dtype=float)
        
        return relevance
    
    if k == 1:
        k_cutoff = np.max(scores, axis=0)
        #k_plus_cutoff, k_cutoff = np.partition(scores, -2, axis=0)[-2:]
    else:
        k_cutoff = np.partition(scores, -k, axis=0)[-k] # (T,U)
    
    above, eq = winner_prob(scores, k_cutoff, k)
    winners = above + eq
    base_relevance = np.mean(winners, axis=1)   # (N,U)
    start_prob = np.max(base_relevance, axis=0)        # (U,)
    value_relevance = np.sum(base_relevance, axis=1)
    value_relevance /= np.maximum(1, MAX_REQ_EXP[lvls])
    value_relevance[lvls == 20] = -99999999
    value_choice = np.argmax(value_relevance)
    #start_prob = np.sum(asdf)
    #print(value_threshold)
    #value_threshold = 1e-08

    #prob_diff = np.zeros((num_artifacts, num_targets), dtype=float)
    evsi = np.tile(-start_prob[None, ...], (num_artifacts, 1))
    estimate_exps = UPGRADE_REQ_EXP[lvls]

    #original_estimate_exp = estimate_exp(base_relevance,
    #MAX_REQ_EXP[lvls])
    
    for i in range(len(artifacts)):
        if lvls[i] == 20:
            continue
        
        tape = tapes[i]                                 # (T,X)
        masks = tape_values[i][:, None] == tape[:, 0]   # (T,)
        temp_lvls = lvls.copy()
        temp_lvls[i] += 4
        
        for mask in masks:
            prob = np.mean(mask)
            if prob == 0:
                continue
            
            potential_points = np.mean(winners[:, mask, :], axis=1)   # (N,U)
            potential_prob = np.max(potential_points, axis=0)            # (U,)
            potential_exp = estimate_exp(potential_points, MAX_REQ_EXP[temp_lvls])
            #potential_exp = new_estimate_exp(a, b, MAX_REQ_EXP[temp_lvls], rng)
            
            evsi[i] += prob * potential_prob
            estimate_exps[i] += prob * potential_exp
    
    '''
    if np.max(evsi[lvls != 20]) < 0.03:
        return rank_value(artifacts, lvls, persist, targets, k, num_trials, rng)
    '''
    evsi = np.sum(evsi, axis=1)
    evsi /= np.where(lvls == 20, 1, MAX_REQ_EXP[lvls])
    evsi[lvls == 20] = -999999
    evsi_choice = np.argmax(evsi)
    if estimate_exps[evsi_choice] < estimate_exps[value_choice]:
        print('evsi', estimate_exps[evsi_choice], estimate_exps[value_choice])
        return evsi
    print('value', estimate_exps[evsi_choice], estimate_exps[value_choice])
    return value_relevance
    #return rank_value(artifacts, lvls, persist, targets, k, num_trials, rng)
    #prob_diff *= MAX_REQ_EXP[lvls]
    #prob_diff /= np.where(lvls == 20, 1, UPGRADE_REQ_EXP[lvls])
    #print('prob diff')
    #print(prob_diff)
    #print(np.max(prob_diff[lvls != 20]))
    #print(np.min(prob_diff[lvls != 20]))
    
    return evsi

def DELETE(artifacts, lvls, persist, targets, k=1, num_trials=1000, rng=None, seed=None):
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
        tape_values = []
        tapes = []
        #tapes = np.zeros((num_artifacts, num_trials, 5), dtype=np.uint8)
        for i in range(num_artifacts):
            maxed[i], tape = sample_upgrade(artifacts[i], num_trials, lvl=lvls[i], rng=rng)
            tapes.append(tape)
        
            if np.count_nonzero(artifacts[i]) == 4:
                possible_substats = np.where(artifacts[i, :10] == 0)[0]
                tape_values.append((possible_substats[:, None] * 4 + np.arange(4)).flatten())
            else:
                tape_values.append((find_sub(artifacts[i])[:, None] * 4 + np.arange(4)).flatten())
                
        persist['changed'] = []
        persist['maxed'] = maxed
        persist['tape_values'] = tape_values
        persist['tapes'] = tapes
        persist['targets'] = None
        
    if not np.array_equal(persist['targets'], targets):
        persist['targets'] = targets
        persist['scores'] = score(persist['maxed'], targets.T)
        
    if len(persist['changed']) != 0:
        changed = persist['changed']
        try:
            _ = iter(changed)
        except:
            changed = [changed]
        for idx in changed:
            persist['maxed'][idx], persist['tapes'][idx] = sample_upgrade(artifacts[idx], num_trials, lvl=lvls[idx], rng=rng)
            persist['scores'][idx]= score(persist['maxed'][idx], targets.T)
            
            if lvls[idx] == 20:
                persist['tape_values'][idx] = None
            elif lvls[idx] == 4:
                persist['tape_values'][idx] = (find_sub(artifacts[idx])[:, None] * 4 + np.arange(4)).flatten()
                
        persist['changed'] = []
            
    scores, tape_values, tapes = persist['scores'], persist['tape_values'], persist['tapes']
    
    if num_artifacts <= k:
        relevance = np.full((num_artifacts), num_trials, dtype=float)
        
        return relevance
    
    if k == 1:
        k_cutoff = np.max(scores, axis=0)
        #k_plus_cutoff, k_cutoff = np.partition(scores, -2, axis=0)[-2:]
    else:
        k_cutoff = np.partition(scores, -k, axis=0)[-k] # (T,U)
    
    base_relevance = winner_prob(scores, k_cutoff, k)   # (N,T,U)
    
    base_points = np.mean(base_relevance, axis=1)   # (N,U)
    start_prob = np.max(base_points, axis=0)        # (U,)
    #start_prob = np.sum(asdf)
    #print(value_threshold)
    #value_threshold = 1e-08

    #prob_diff = np.zeros((num_artifacts, num_targets), dtype=float)
    evsi = np.tile(-start_prob[None, ...], (num_artifacts, 1))
    
    for i in range(len(artifacts)):
        if lvls[i] == 20:
            continue
        
        tape = tapes[i]
        masks = tape_values[i][:, None] == tape[:, 0]
        temp_lvls = lvls.copy()
        temp_lvls[i] += 4
        
        for mask in masks:
            prob = np.mean(mask)
            if prob == 0:
                continue
            
            masked_scores = scores[:, mask, :]
            masked_cutoff = k_cutoff[mask, :]
            
            potential_relevance = winner_prob(masked_scores, masked_cutoff, k)  # (N,T,U)
            
            potential_points = np.mean(potential_relevance, axis=1)   # (N,U)
            potential_prob = np.max(potential_points, axis=0)            # (U,)
            
            evsi[i] += prob * potential_prob
    
    if np.max(evsi[lvls != 20]) < 0.03:
        return rank_value(artifacts, lvls, persist, targets, k, num_trials, rng)
    
    evsi = np.sum(evsi, axis=1)
    evsi /= np.where(lvls == 20, 1, MAX_REQ_EXP[lvls])
    #prob_diff *= MAX_REQ_EXP[lvls]
    #prob_diff /= np.where(lvls == 20, 1, UPGRADE_REQ_EXP[lvls])
    #print('prob diff')
    #print(prob_diff)
    #print(np.max(prob_diff[lvls != 20]))
    #print(np.min(prob_diff[lvls != 20]))
    
    return evsi
    
def rank_evsi_mean(artifacts, lvls, persist, targets, k=2, num_trials=2000, rng=None, seed=None):    
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
            maxed[i], tape = sample_upgrade(artifacts[i], num_trials, lvl=lvls[i], rng=rng)
        
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
                distros_maxed[-1][j], tape = sample_upgrade(upgrade, num_trials, lvl=next, rng=rng)
                
        persist['changed'] = []
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
        
    if len(persist['changed']) != 0:
        changed = persist['changed']
        try:
            _ = iter(changed)
        except:
            changed = [changed]
        for idx in changed:
            persist['maxed'][idx], tape = sample_upgrade(artifacts[idx], num_trials, lvl=lvls[idx], rng=rng)
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
                    persist['distros_maxed'][idx][i], tape = sample_upgrade(upgrade, num_trials, lvl=next, rng=rng)
                    
                persist['distros_scores'][idx] = score(persist['distros_maxed'][idx], targets.T)
                
        persist['changed'] = []
            
    scores, distros, distros_scores = persist['scores'], persist['distros'], persist['distros_scores']
    
    if num_artifacts <= k:
        relevance = np.full((num_artifacts), num_trials, dtype=float)
        
        return relevance
    
    # scores (N,T,U)
    mean_scores = np.mean(scores, axis=1) # (N,U)
    current_best_scores = np.max(mean_scores, axis=0) # (U,)
    
    delta_regret = np.full((num_artifacts, num_targets), 0, dtype=float) # (N,U)
    
    for i in range(len(artifacts)):
        if lvls[i] == 20:
            continue
        
        probs = distros[i][1]           # (X,)
        upgrades = distros_scores[i]    # (X,T,U)
        
        upgrades = upgrades[probs != 0]
        probs = probs[probs != 0]
        
        num_upgrades = len(upgrades)
        
        mean_upgrades_scores = np.mean(upgrades, axis=1) # (X,U)
        
        temp_mean_scores = mean_scores[np.arange(num_artifacts) != i] # (N-1,U)
        temp_best_scores = np.max(temp_mean_scores, axis=0) # (U,)
                
        new_best_scores = np.maximum(mean_upgrades_scores, temp_best_scores[None, :])  # (X,U)
        
        idk = (new_best_scores.T @ probs).copy()
        temp = probs @ new_best_scores # (U,)
        something = temp - current_best_scores
        #if not np.isclose(np.min(something), 0):
        #    print('a')
        delta_regret[i] = something
        #print(temp)
        
    #print(np.sum(delta_regret, axis=1))
    delta_regret /= np.mean(mean_scores, axis=0)
    #delta_regret = np.linalg.norm(delta_regret, axis=1)
    delta_regret = np.sum(delta_regret, axis=1) # (N,)
    #delta_regret /= np.where(lvls == 20, 100, UPGRADE_REQ_EXP[lvls])
    #print(np.max(delta_regret[lvls != 20]))
    '''
    if np.max(delta_regret[lvls != 20]) < 0.35:
        persist['changed'] = []
        return rank_value(artifacts, lvls, persist, targets, k, num_trials, rng)
    '''
    
    #print(np.max(delta_regret[lvls != 20]))
    delta_regret /= np.where(lvls == 20, 1, UPGRADE_REQ_EXP[lvls])
    value_relevance = rank_value(artifacts, lvls, persist, targets, k, num_trials, rng)    
    
    return value_relevance + 0.30 * delta_regret

def rank_evsi_regret(artifacts, lvls, persist, targets, k=2, num_trials=1000, rng=None, seed=None):
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
            maxed[i], tape = sample_upgrade(artifacts[i], num_trials, lvl=lvls[i], rng=rng)
        
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
                distros_maxed[-1][j], tape = sample_upgrade(upgrade, num_trials, lvl=next, rng=rng)
                
        persist['changed'] = []
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
        
    if len(persist['changed']) != 0:
        changed = persist['changed']
        try:
            _ = iter(changed)
        except:
            changed = [changed]
        for idx in changed:
            persist['maxed'][idx], tape = sample_upgrade(artifacts[idx], num_trials, lvl=lvls[idx], rng=rng)
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
                    persist['distros_maxed'][idx][i], tape = sample_upgrade(upgrade, num_trials, lvl=next, rng=rng)
                    
                persist['distros_scores'][idx] = score(persist['distros_maxed'][idx], targets.T)
                
        persist['changed'] = []
            
    scores, distros, distros_scores = persist['scores'], persist['distros'], persist['distros_scores']
    
    if num_artifacts <= k:
        relevance = np.full((num_artifacts), num_trials, dtype=float)
        
        return relevance
    
    # scores (N,T,U)
    
    winning_scores = np.max(scores, axis=0) # (T,U)
    avg_max = np.mean(scores, axis=1)       # (N,U)
    current_best = np.max(avg_max, axis=0)  # (U,)
    avg_perfect = np.mean(winning_scores, axis=0) # (U,)
    regret = avg_perfect - current_best
    
    asdf = np.where(regret <= 0)[0]
    for i in asdf:
        ges = np.mean(scores[:, :, i], axis=1)       # (N,)
        qwer = np.argmax(ges)
        if lvls[qwer] != 20:
            print('skip', qwer)
            #return rank_value(artifacts, lvls, persist, targets, k, num_trials, rng)
            return qwer
    
    
    evsi = np.tile(regret[None, :], (num_artifacts, 1)) # (N,U)
    evsi[lvls == 20] = 0
        
    base_mean = np.mean(scores, axis=1) # (N,U)
    for i in range(len(artifacts)):
        if lvls[i] == 20:
            continue
        
        probs = distros[i][1]           # (X,)
        upgrades = distros_scores[i]    # (X,T,U)
        
        upgrades = upgrades[probs != 0]
        probs = probs[probs != 0]
        
        num_upgrades = len(upgrades)
        
        except_i_mask = np.arange(num_artifacts) != i
        base_winning_scores = np.max(scores[except_i_mask], axis=0)
        potential_regret = np.zeros((num_upgrades, num_targets), dtype=float)
        except_i_mean = base_mean[except_i_mask]
        for j, upgrade in enumerate(upgrades):      # (T,U)
            
            winning_scores = np.maximum(base_winning_scores, upgrade)   # (T,U)
            current_best = np.maximum(np.mean(upgrade, axis=0), np.max(except_i_mean, axis=0))
            avg_perfect = np.mean(winning_scores, axis=0) # (U,)
            potential_regret[j] = avg_perfect - current_best
            #potential_regret[j] = (np.mean(winning_scores, axis=0) - qwer) / normalization
            #potential_regret[j] = 1 - qwer / np.mean(winning_scores, axis=0)

        evsi[i] -= probs @ potential_regret
    
    #print(evsi)    
    if np.isclose(np.max(evsi), 0):
        persist = {}
        print('asdf')
        return rank_evsi_regret(artifacts, lvls, persist, targets, k, num_trials, rng)
        
    evsi = np.maximum(evsi, 0)
    evsi /= np.maximum(regret, 1e-12)
    #evsi[evsi < 0] /= 1000
    #avg_max = np.mean(scores, axis=1)      # (N,U)
    # np.max(avg_max, axis=0)               # (U,)
    winners = (avg_max == current_best[None, :]).astype(float)      # (N,U)
    num_winners = np.count_nonzero(winners, axis=0) # (U,)
    winners /= num_winners[None, :]
    times_won = np.sum(winners, axis=1)   # (N,)
    
    progress = times_won * UPGRADE_REQ_EXP[lvls]
    #relevance = np.linalg.norm(evsi, axis=1)
    relevance = np.sum(evsi, axis=1)
    relevance *= MAX_REQ_EXP[lvls]
    relevance += progress * 3.2
    relevance /= np.maximum(UPGRADE_REQ_EXP[lvls], 1)
    #relevance = np.sum(evsi, axis=1)
    #relevance /= np.where(lvls == 20, 1, UPGRADE_REQ_EXP[lvls])
    return relevance

def rank_pairwise(artifacts, lvls, persist, targets, k=2, num_trials=1000, rng=None, seed=None):
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
        persist['changed'] = []

        maxed = np.zeros((num_artifacts, num_trials, 19), dtype=np.uint8)
        for i in range(num_artifacts):
            maxed[i], tape = sample_upgrade(artifacts[i], num_trials, lvl=lvls[i], rng=rng)
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
        
    if len(persist['changed']) != 0:
        changed = persist['changed']
        try:
            _ = iter(changed)
        except:
            changed = [changed]
        for idx in changed:
            persist['maxed'][idx], tape = sample_upgrade(artifacts[idx], num_trials, lvl=lvls[idx], rng=rng)
            persist['scores'][idx] = score(persist['maxed'][idx], targets.T)
            
        persist['changed'] = []
        
    scores = persist['scores']
    
    if num_artifacts <= k:
        relevance = np.full((num_artifacts), num_trials, dtype=float)
        relevance /= np.where(lvls == 20, 1, MAX_REQ_EXP[lvls])
        
        return relevance
    
    N, T, U = scores.shape
    out = np.empty((N, U), dtype=float)
    rng1N = np.arange(1, N + 1)[:, None]  # ranks 1..N as a column

    for u in range(U):
        X = scores[:, :, u]                                   # (N, T)
        order = np.argsort(X, axis=0, kind='mergesort')       # stable for ties
        Xs = np.take_along_axis(X, order, axis=0)             # sorted values

        # Identify tie-group starts along artifact axis
        starts = np.ones_like(Xs, dtype=bool)
        starts[1:] = Xs[1:] != Xs[:-1]

        # First rank in the tie group (per row)
        first_rank = np.maximum.accumulate(
            np.where(starts, rng1N, 0), axis=0
        )

        # Last rank in the tie group (per row), via reverse scan
        rev_starts = starts[::-1]
        last_rev = np.maximum.accumulate(
            np.where(rev_starts, rng1N, 0), axis=0
        )
        last_rank = (N - last_rev[::-1] + 1)

        rank_used = (first_rank + last_rank) * 0.5
        
        # Map ranks back to original artifact order
        rank_back = np.empty_like(rank_used, dtype=float)
        rank_back[order, np.arange(T)] = rank_used

        # Per-trial pairwise mass, then mean over trials
        pm = (rank_back - 1.0) / (N - 1.0)                    # (N, T)
        out[:, u] = pm.mean(axis=1)                           # (N,)
        
    relevance = np.sum(out, axis=1)
    relevance /= np.where(lvls == 20, 1, MAX_REQ_EXP[lvls])
    return relevance
    
if __name__ == '__main__':
    target = vectorize({'atk_': 6, 'atk': 2, 'crit_': 8})
    percentile('circlet', target, 0)
    '''
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

    #seeds = [13, 19, 23, 26, 57, 64, 66]
    num_seeds = 30
    num_iterations = 1
    totals = np.zeros((num_seeds, num_iterations))
    
    start = time.time()
    for i in range(num_seeds):
    #for i in seeds:
        for j in range(num_iterations):
            print('seed:', i, 'iteration:', j)
            artifacts, slvls = generate('flower', size=500, seed=i)
            totals[i, j] = (simulate_exp(artifacts, slvls, targets, rank_value))
    end = time.time()
            
    #np.save('data/temp1.npy', totals)
            
    print('done')
    print(totals)
    row_mean = np.mean(totals, axis=1)
    row_std = np.std(totals, axis=1)
    print(row_mean)
    print(row_std / np.sqrt(num_iterations))
    print(row_std / row_mean / np.sqrt(num_iterations))
    print('mean', np.mean(totals))
    print('std', np.linalg.norm(row_std / np.sqrt(num_iterations)) / num_seeds)
    print('ratio', np.linalg.norm(row_std / np.sqrt(num_iterations)) / num_seeds / np.mean(totals))
    print(end - start)
    '''
    '''
    
    totals = np.zeros((num_seeds, num_iterations))
    
    start = time.time()
    for i in range(num_seeds):
        for j in range(num_iterations):
            artifacts = generate('flower', size=50, seed=i)
            totals[i, j] = (simulate_exp(artifacts, np.zeros(50, dtype=int), targets, rank_temp))
    end = time.time()
            
    print('done')
    print(totals)
    row_mean = np.mean(totals, axis=1)
    row_std = np.std(totals, axis=1)
    print(row_mean)
    print(row_std)
    print(row_std / row_mean / np.sqrt(num_iterations))
    print('mean', np.mean(totals))
    print('std', np.linalg.norm(row_std) / num_seeds)
    print('ratio', np.linalg.norm(row_std) / num_seeds / np.mean(totals))
    print(end - start)
    
    totals = np.zeros((num_seeds, num_iterations))
    
    start = time.time()
    for i in range(num_seeds):
        for j in range(num_iterations):
            artifacts = generate('flower', size=50, seed=i)
            totals[i, j] = (simulate_exp(artifacts, np.zeros(50, dtype=int), targets, rank_value))
    end = time.time()
            
    print('done')
    print(totals)
    row_mean = np.mean(totals, axis=1)
    row_std = np.std(totals, axis=1)
    print(row_mean)
    print(row_std)
    print(row_std / row_mean / np.sqrt(num_iterations))
    print('mean', np.mean(totals))
    print('std', np.linalg.norm(row_std) / num_seeds)
    print('ratio', np.linalg.norm(row_std) / num_seeds / np.mean(totals))
    print(end - start)
    '''

    '''
    start = time.time()
    filename = 'artifacts/9-15-2025.json'
    artifacts, slots, rarities, lvls, sets = load(filename)
    relevant = rate(artifacts, slots, rarities, lvls, sets, rank_value, k=2, num=100)
    
    count = 0
    
    visualize(relevant, artifacts, slots, sets, lvls)
    end = time.time()
    print(end - start)
    '''
    
    # TODO: check seed 22 and see just how unlucky it is, because
    # sometimes it does so terrible