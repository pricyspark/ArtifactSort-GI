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
    return -np.sum(array * np.log(array, where=array != 0), axis=axis)
    #return -np.sum(np.where(array > 0, array * np.log(array), 0.0), axis=axis)

def entropy_np(p, axis=0, eps=1e-12):
    # normalize across the axis
    s = p.sum(axis=axis, keepdims=True)
    p = np.divide(p, np.maximum(s, eps), out=np.zeros_like(p), where=s>0)
    # stable -sum p*log(p)
    plogp = np.where(p > 0, p * np.log(p), 0.0)
    return -plogp.sum(axis=axis)
    
def winner_prob(scores, cutoff, k):
    num_trials = scores.shape[1]
    above = scores > cutoff                     # (N,T,U)
    eq = scores == cutoff                       # (N,T,U)
    above_count = above.sum(axis=0)             # (T,U)
    leftover = k - above_count                  # (T,U)
    eq_count = eq.sum(axis=0)                   # (T,U)
    frac_per_tie = leftover / eq_count          # (T,U)
    points_eq = eq * frac_per_tie[None, ...]    # (N,T,U)
    return above + points_eq                    # (N,T,U)

def new_winner_prob(scores, cutoff, k):
    num_trials = scores.shape[1]
    above = scores > cutoff                     # (N,T,U)
    eq = scores == cutoff                       # (N,T,U)
    above_count = above.sum(axis=0)             # (T,U)
    leftover = k - above_count                  # (T,U)
    eq_count = eq.sum(axis=0)                   # (T,U)
    frac_per_tie = leftover / eq_count          # (T,U)
    points_eq = eq * frac_per_tie[None, ...]    # (N,T,U)
    return above, points_eq                    # (N,T,U)

def new_estimate_exp(above, eq, exp, rng, num_samples=30):
    num_artifacts, num_trials, num_targets = above.shape
    prob = above + eq   # (N,T,U)
    
    artifact_prob = np.mean(prob, axis=1)   # (N,U)
    scores = np.sum(artifact_prob, axis=1) / np.maximum(1, exp) # (N,)
    order = np.argsort(scores)[::-1]
    
    totals = np.cumsum(exp[order])
    rank_idx = np.argsort(order)
    
    samples = rng.choice(num_trials, size=num_samples)
    output = 0
    for sample in samples:
        trial = eq[:, sample, :]    # (N,U)
        
        J, I = np.where(trial.T)                     # J = column indices (0..U-1), I = row indices
        counts = np.bincount(J, minlength=trial.shape[1])
        splits  = np.cumsum(counts)[:-1]
        rows_per_col = np.split(I, splits)       # list of length U; each item is an array of row indices
        asdf = []
        for idxs in rows_per_col:
            if not np.any(exp[idxs] == 0):
                asdf.append(np.min(rank_idx[idxs]))
        
        done = round(statistics.median(asdf))
        
        output += totals[done]
    '''
    for sample in samples:
        trial_above = above[:, sample, :] # (N,U)
        temp = np.argmax(trial_above, axis=0) # (U,)
        mask = np.any(trial_above, axis=0)  # (U,)
        
        if np.any(mask):
            done_above = np.max(rank_idx[temp[mask]])
        else:
            done_above = -1
        
        trial_eq = eq[:, sample, :]    # (N,U)
        J, I = np.where(trial_eq.T)                     # J = column indices (0..U-1), I = row indices
        counts = np.bincount(J, minlength=trial_eq.shape[1])
        splits  = np.cumsum(counts)[:-1]
        rows_per_col = np.split(I, splits)       # list of length U; each item is an array of row indices
        asdf = []
        for idxs in rows_per_col:
            asdf.append(np.min(rank_idx[idxs]))
        
        done_eq = max(asdf)
        
        output += totals[max(done_above, done_eq)]
    '''
        
    return output / num_samples

def estimate_exp(probs, exp):
    '''
    print('probs')
    for _ in range(4):
        print(probs[50*_:50*(_+1)])
    print('maxes')
    print(np.max(probs, axis=0))
    '''
    
    '''
    num_artifacts, num_trials, num_targets = probs.shape
    artifact_probs = np.mean(probs, axis=1) # (N,U)
    scores = np.sum(probs, axis=1) / np.maximum(1, exp)
    order = np.argsort(scores)[::-1]
    
    totals = np.cumsum(exp[order])
    num_samples = 30
    
    samples = rng.choice(num_trials), size=num_samples)
    for sample in samples:
        trial = probs[:, sample, :] # (N,U)
        temp = np.sum(trial, axis=1) # (N,)
        
        
    '''
    #print(probs)
    # probs: (N, U), exp: (N,) or scalar
    #probs = np.asarray(probs, dtype=float)
    #exp   = np.asarray(exp,   dtype=float)

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

def rank_value(artifacts, slvls, persist, targets, k=1, num_trials=2000, rng=None, seed=None, save_entropy=False):
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

    if rng is None:
        rng = np.random.default_rng(seed)
    
    if len(persist) == 0:
        persist['changed'] = []

        maxed = np.zeros((num_artifacts, num_trials, 19), dtype=np.uint8)
        for i in range(num_artifacts):
            maxed[i], tape = sample_upgrade(artifacts[i], num_trials, slvl=slvls[i], rng=rng)
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
            persist['maxed'][idx], tape = sample_upgrade(artifacts[idx], num_trials, slvl=slvls[idx], rng=rng)
            persist['scores'][idx] = score(persist['maxed'][idx], targets.T)
            
        persist['changed'] = []
        
    scores = persist['scores']
    
    if num_artifacts <= k:
        relevance = np.full((num_artifacts), num_trials, dtype=float)
        relevance /= np.where(slvls == 20, 1, MAX_REQ_EXP[slvls])
        
        return relevance
    
    if k == 1:
        # maximum per (i, j)
        cutoff = scores.max(axis=0)                    # shape (num_trials, num_targets)
    else:
        # k‑th largest via partition
        cutoff = np.partition(scores, -k, axis=0)[-k]  # same shape

    #above, eq = new_winner_prob(scores, cutoff, k)
    #print('estimate', new_estimate_exp(above, eq, MAX_REQ_EXP[lvls], rng))
    #relevance = np.mean(above + eq, axis=1)
    
    relevance = np.mean(winner_prob(scores, cutoff, k), axis=1)
    
    #print('estimate')
    #print(estimate_exp(relevance, MAX_REQ_EXP[lvls]))
    if save_entropy:
        persist['entropy'] = np.linalg.norm(entropy(relevance, axis=0))
    relevance = relevance.sum(axis=1)   # (N,)
        
    #relevance = np.linalg.norm(relevance, axis=1)
    # relevance = np.sum(calc_relevance(scores, k), axis=1) # This extra function call and sum adds non-negligible overhead
    relevance /= np.where(slvls == 20, 1, MAX_REQ_EXP[slvls])
    '''
    if np.max(relevance[lvls != 20]) == 0:
        print('max was 0')
        for i in range(num_artifacts):
            persist['maxed'][i], tape = sample_upgrade(artifacts[i], num_trials, lvl=lvls[i], rng=rng)
        persist['targets'] = None
        persist['changed'] = []
        return rank_value(artifacts, lvls, persist, targets, k, num_trials, rng)
    '''
        
    return relevance

def rank_entropy(artifacts, slvls, persist, targets, k=1, num_trials=1000, rng=None, seed=None, value_threshold=0):
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
        #k_plus_cutoff, k_cutoff = np.partition(scores, -2, axis=0)[-2:]
    else:
        k_cutoff = np.partition(scores, -k, axis=0)[-k] # (T,U)
    
    above, eq = new_winner_prob(scores, k_cutoff, k)    # (N,T,U)
    winners = above + eq
    base_relevance = np.mean(winners, axis=1)   # (N,U)
    value_relevance = np.sum(base_relevance, axis=1)
    value_relevance /= np.maximum(1, MAX_REQ_EXP[slvls])
    value_relevance[slvls == 20] = -99999999
    value_choice = np.argmax(value_relevance)
    base_entropy = my_entropy(base_relevance, axis=0)  # (U,)
    #base_entropy = entropy(base_relevance, axis=0)  # (U,)
    
    information_gain = np.tile(base_entropy[None, :], (num_artifacts, 1))
    #prob_diff = np.zeros((num_artifacts, num_targets), dtype=float)
    estimate_exps = UPGRADE_REQ_EXP[slvls]
    
    #original_estimate_exp = estimate_exp(base_relevance,
    #MAX_REQ_EXP[lvls]
    for i in range(len(artifacts)):
        if slvls[i] == 20:
            continue
        
        tape = tapes[i]                                 # (T,X)
        masks = tape_values[i][:, None] == tape[:, 0]   # (T,)
        '''
        s_star = np.where(b == i, second, first)
        m = np.subtract(s_star, scores[i], dtype=int)
        #m = np.maximum(m, 0)
        
        delta = np.zeros((num_trials, num_targets), dtype=float)
        for upgrade, mask in zip(tape_values[i], masks):
            sub = upgrade // 4
            increment = upgrade % 4 + 7
            if np.count_nonzero(artifacts[i]) == 4:
                increment += 40
            delta[mask] = increment * targets[:, sub]
            
        greater = delta > m # (T,U)
        p_flip = np.mean(greater, axis=0)   # (U,)
        p_flip_comp = 1 - p_flip
        
        ig_ub = -(p_flip * np.log(p_flip, where=p_flip != 0) + p_flip_comp * np.log(p_flip_comp, where=p_flip_comp != 0))
        '''
        temp_slvls = slvls.copy()
        temp_slvls[i] = next_lvl(temp_slvls[i])
        
        for mask in masks:
            prob = np.mean(mask)
            if prob == 0:
                continue
            
            potential_points = np.mean(winners[:, mask, :], axis=1)   # (N,U)
            #print(np.sum(potential_points, axis=0))
            potential_entropy = my_entropy(potential_points, axis=0)
            #potential_entropy = entropy(potential_points, axis=0)
            #asdf = my_entropy(potential_points, axis=0)
            #if not np.allclose(potential_entropy, asdf):
            #    raise ValueError
            #if np.isnan(np.sum(asdf)):
            #    raise ValueError
            potential_exp = estimate_exp(potential_points, MAX_REQ_EXP[temp_slvls])
            #potential_exp = new_estimate_exp(a, b, MAX_REQ_EXP[temp_lvls], rng)
            information_gain[i] -= prob * potential_entropy
            estimate_exps[i] += prob * potential_exp
        #maskmask = base_relevance[i] > 0.005
        #if not np.all(ig_ub >= information_gain[i]):
        #    raise ValueError
    
    '''
    if np.max(evsi[lvls != 20]) < 0.03:
        return rank_value(artifacts, lvls, persist, targets, k, num_trials, rng)
    '''
    #print('median', np.median(information_gain))
    information_gain = np.linalg.norm(information_gain, axis=1) # (N,)
    information_gain /= np.maximum(1, MAX_REQ_EXP[slvls])
    information_gain[slvls == 20] = -999999
    IG_choice = np.argmax(information_gain)
    print('IG choice', IG_choice)
    if estimate_exps[IG_choice] < estimate_exps[value_choice]:
        print('entropy', estimate_exps[IG_choice], estimate_exps[value_choice])
        return information_gain
    print('value', estimate_exps[IG_choice], estimate_exps[value_choice])
    return value_relevance

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
    
def rank_estimate(artifacts, lvls, persist, targets, k=1, num_trials=1000, rng=None, seed=None):
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
    else:
        k_cutoff = np.partition(scores, -k, axis=0)[-k] # (T,U)
    
    potential_estimate_exps = UPGRADE_REQ_EXP[lvls]
    
    for i in range(len(artifacts)):
        if lvls[i] == 20:
            continue
        
        potential_lvls = lvls.copy()
        potential_lvls[i] += 4
        
        tape = tapes[i]
        masks = tape_values[i][:, None] == tape[:, 0]
        
        for mask in masks:
            prob = np.mean(mask)
            if prob == 0:
                continue
            
            masked_scores = scores[:, mask, :]
            masked_cutoff = k_cutoff[mask, :]
            
            a, b = new_winner_prob(masked_scores, masked_cutoff, k)
            #potential_relevance = winner_prob(masked_scores, masked_cutoff, k)  # (N,T,U)
            
            #potential_points = np.mean(potential_relevance, axis=1)   # (N,U)
            #potential_estimate_exp = estimate_exp(potential_points, MAX_REQ_EXP[potential_lvls])
            potential_estimate_exp = new_estimate_exp(a, b, MAX_REQ_EXP[potential_lvls], rng)
            potential_estimate_exps[i] += prob * potential_estimate_exp
    #print()
    #print('min estimate exp:', np.min(potential_estimate_exps[lvls != 20]))
    return -potential_estimate_exps
    
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
    
    above, eq = new_winner_prob(scores, k_cutoff, k)
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
    '''
    '''

    num_seeds = 10
    num_iterations = 10
    totals = np.zeros((num_seeds, num_iterations))
    
    start = time.time()
    for i in range(num_seeds):
        for j in range(num_iterations):
            artifacts, slvls = generate('flower', size=200, seed=i)
            totals[i, j] = (simulate_exp(artifacts, slvls, targets, rank_entropy))
    end = time.time()
            
    np.save('data/entropy_0.125_2000_200.npy', totals)
            
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
    filename = 'artifacts/genshinData_GOOD_2025_09_01_01_03.json'
    artifacts, slots, rarities, lvls, sets = load(filename)
    relevant = rate(artifacts, slots, rarities, lvls, sets, rank_value, num=100)
    
    count = 0
    
    visualize(relevant, artifacts, slots, sets, lvls)
    end = time.time()
    print(end - start)
    '''