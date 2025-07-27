import numpy as np
from analyze import *
import time

def rank_value(artifacts, lvls, persist, targets, change=True, k=2, num_trials=1000, rng=None, seed=None):
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
        persist['changed'] = -1
        distributions, probs = distro(artifacts, lvls)
        maxed = np.zeros((num_artifacts, num_trials, 19), dtype=np.uint8)
        for i in range(num_artifacts):
            maxed[i] = rng.choice(distributions[i], p=probs[i], size=num_trials)
        persist['maxed'] = maxed
    elif change:
        changed = persist['changed']
        distributions, probs = distro(artifacts[changed], lvls[changed])
        persist['maxed'][changed] = rng.choice(distributions, p=probs, size=num_trials)
        
    changed = persist['changed']
    maxed = persist['maxed']
    #changed, maxed = persist['changed'], persist['maxed']
    relevance = np.zeros(num_artifacts, dtype=float)
    
    if num_artifacts <= k:
        relevance[:] = num_trials
        for i in range(num_artifacts):
            if lvls[i] == 20:
                if change:
                    relevance[i] = 0
            else:
                relevance[i] /= MAX_REQ_EXP[lvls[i]]
                #relevance[i] /= UPGRADE_REQ_EXP[lvls[i]]
        persist['changed'] = np.argmax(relevance)
        return relevance
    
    for i in range(num_trials):
        #maxed = np.zeros((num_artifacts, 19), dtype=np.uint8)
        #for i in range(num_artifacts):
        #    maxed[i] = rng.choice(distributions[i], p=probs[i])
        if type(targets) == dict or (type(targets) == np.ndarray and targets.ndim == 1):
            final_scores = score(maxed[:, i], targets)
            #final_scores[lvls == 20] = 0
            if k == 1:
                maximum = np.max(final_scores)
                best = np.where(final_scores == maximum)[0]
                relevance[best] += 1 / len(best)
            else:
                # TODO: this seems really slow
                threshold = np.sort(final_scores)[-k]
                relevance[final_scores > threshold] += 1
                asdf = np.where(final_scores == threshold)[0]
                relevance[asdf] += 1 / len(asdf)
                #best = np.argpartition(final_scores, -k)[-k:]
        else:
            for target in targets:
                final_scores = score(maxed[:, i], target)
                if k == 1:
                    maximum = np.max(final_scores)
                    best = np.where(final_scores == maximum)[0]
                    relevance[best] += 1 / len(best)
                else:
                    # TODO: this seems really slow
                    threshold = np.sort(final_scores)[-k]
                    relevance[final_scores > threshold] += 1
                    asdf = np.where(final_scores == threshold)[0]
                    relevance[asdf] += 1 / len(asdf)
                # each target is weighted equally. Don't divide by the
                # number of targets, or else having more targets would
                # make each target less valuable, which isn't the case.
                
    for i in range(num_artifacts):
        if lvls[i] == 20:
            if change:
                relevance[i] = 0
        else:
            relevance[i] /= MAX_REQ_EXP[lvls[i]]
            #relevance[i] /= UPGRADE_REQ_EXP[lvls[i]]
            #raise ValueError
        
    persist['changed'] = np.argmax(relevance)
    #return relevance
    #print_artifact(artifacts[np.argmax(relevance)])
    if relevance[persist['changed']] == 0 and change:
        print('max was 0')
        distributions, probs = distro(artifacts, lvls)
        maxed = np.zeros((num_artifacts, num_trials, 19), dtype=np.uint8)
        for i in range(num_artifacts):
            maxed[i] = rng.choice(distributions[i], p=probs[i], size=num_trials)
        persist['maxed'] = maxed
        return rank_value(artifacts, lvls, persist, targets, change, k, num_trials, rng)
    
    return relevance

def rank_temp(artifacts, lvls, persist, targets, change=True, k=2, num_trials=1000, rng=None, seed=None):
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
    
    if not np.array_equal(persist['targets'], targets):
        persist['targets'] = targets
        scores = np.zeros((num_artifacts, num_trials, len(targets)), dtype=np.uint32)
        for i in range(num_trials):
            for j in range(len(targets)):
                scores[:, i, j] = score(persist['maxed'][:, i], targets[j])
        persist['scores'] = scores    
        
    if persist['changed'] != -1:
        changed = persist['changed']
        persist['maxed'][changed] = sample_upgrade(artifacts[changed], num_trials, lvl=lvls[changed], rng=rng)
        for i in range(num_trials):
            for j in range(len(targets)):
                persist['scores'][changed, i, j] = score(persist['maxed'][changed, i], targets[j])        
        
    changed, maxed, scores = persist['changed'], persist['maxed'], persist['scores']
    relevance = np.zeros(num_artifacts, dtype=float)
    
    if num_artifacts <= k:
        relevance[:] = num_trials
        for i in range(num_artifacts):
            if lvls[i] == 20:
                if change:
                    relevance[i] = 0
            else:
                relevance[i] /= MAX_REQ_EXP[lvls[i]]
                #relevance[i] /= UPGRADE_REQ_EXP[lvls[i]]
        if change:
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

    # 3) Mask of exactly equal to cutoff
    eq    = scores == cutoff[None, ...]                # same shape

    # 4) Count ties so we can split fractional credit
    tie_counts = eq.sum(axis=0)                        # shape (num_trials, num_targets)

    # 5) Sum up:
    #    - 1 point for every “above”
    #    - 1/tie_counts for every “tie”
    relevance = above.sum(axis=(1, 2)).astype(float)
    relevance += (eq / tie_counts[None, ...]).sum(axis=(1, 2))
                
    relevance /= np.where(lvls == 20, 1, MAX_REQ_EXP[lvls])
    if change:
        relevance[lvls == 20] = 0
    '''
    for i in range(num_artifacts):
        if lvls[i] == 20:
            if change:
                relevance[i] = 0
        else:
            relevance[i] /= MAX_REQ_EXP[lvls[i]]
            #relevance[i] /= UPGRADE_REQ_EXP[lvls[i]]
            #raise ValueError
    '''
        
    if change:
        persist['changed'] = np.argmax(relevance)
    #return relevance
    #print_artifact(artifacts[np.argmax(relevance)])
    if relevance[persist['changed']] == 0 and change:
        print('max was 0')
        for i in range(num_artifacts):
            persist['maxed'][i] = sample_upgrade(artifacts[i], num_trials, lvl=lvls[i], rng=rng)
        persist['targets'] = None
        persist['changed'] = -1
        return rank_temp(artifacts, lvls, persist, targets, change, k, num_trials, rng)
        
    return relevance

def rank_estimate(artifacts, lvls, persist, targets, change=True, k=1, num_trials=30, rng=None, seed=None):
    # 
    num_artifacts = len(artifacts)
    if num_artifacts == 0:
        raise ValueError
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
        distributions, probs = distro(artifacts, lvls)
        maxed = np.zeros((num_artifacts, num_trials, 19), dtype=np.uint8)
        for i in range(num_artifacts):
            maxed[i] = rng.choice(distributions[i], p=probs[i], size=num_trials)
        persist[1] = maxed
        
        single_maxed = []
        for i in range(num_artifacts):
            single_maxed.append([None, None])
            if lvls[i] == 20:
                continue
            
            current_distribution, current_probs = distro(artifacts[i], num_upgrades=1)
            single_maxed[-1][0] = []
            single_maxed[-1][1] = current_probs
            for j, upgrade in enumerate(current_distribution):
                potential_distribution, potential_probs = distro(upgrade, next_lvl(lvls[i]))
                single_maxed[-1][0].append(rng.choice(potential_distribution, p=potential_probs, size=num_trials))
            
        # Single maxed is a list with num_artifacts elements. Each
        # element is a list with elements corresponding to each of the
        # possible single upgrades for that artifact. This list has two
        # elements. The first is a list numpy arrays. Each numpy array
        # is a sample maxed artifacts. There is an array for each
        # possible artifact after a single upgrade. The second is a
        # numpy array corresponding to the probability of each single
        # upgrade.
        persist[2] = single_maxed
    elif change:
        changed = persist[0]
        distributions, probs = distro(artifacts[changed], lvls[changed])
        persist[1][changed] = rng.choice(distributions, p=probs, size=num_trials)
        if lvls[changed] != 20:
            current_distribution, current_probs = distro(artifacts[changed], num_upgrades=1)
            persist[2][changed][0] = []
            persist[2][changed][1] = current_probs
            for j, upgrade in enumerate(current_distribution):
                potential_distribution, potential_probs = distro(upgrade, next_lvl(lvls[changed]))
                persist[2][changed][0].append(rng.choice(potential_distribution, p=potential_probs, size=num_trials))
    # TODO: save scores instead of artifacts. Save a threshold score.
    # When computing potential new scores, count how many are above the
    # threshold. This is the relevance score. Don't recompute scores and
    # count. Compute scores once and get a threshold.
    
    changed, maxed, single_maxed = persist
    relevance_std = np.zeros(num_artifacts, dtype=float)
    #original_maxed = maxed.copy()
    
    if type(targets) == dict or (type(targets) == np.ndarray and targets.ndim == 1):
        scores = np.zeros((num_trials, num_artifacts), dtype=float)
        for k in range(num_trials):
            scores[k] = score(maxed[:, k], targets)
        scores[:, lvls == 20] = 0
    else:
        scores = np.zeros((num_trials, len(targets), num_artifacts), dtype=float)
        for k in range(num_trials):
            for j, target in enumerate(targets):
                scores[k, j] = score(maxed[:, k], target)
        scores[:, :, lvls == 20] = 0
    
    for i in range(num_artifacts):
        if lvls[i] == 20:
            continue
        
        upgrades, current_probs = single_maxed[i]
        relevance = np.zeros(len(upgrades), dtype=float)
        
        if type(targets) == dict or (type(targets) == np.ndarray and targets.ndim == 1):
            for upgrade_id, upgrade in enumerate(upgrades):
                for trial_id in range(num_trials):
                    old_max = np.max(scores[trial_id, np.arange(num_artifacts) != i])
                    upgrade_score = score(upgrade[trial_id], targets)
                    if upgrade_score > old_max:
                        relevance[upgrade_id] += 1
                    elif upgrade_score == old_max:
                        relevance[upgrade_id] += 1 / (np.count_nonzero(scores[trial_id, np.arange(num_artifacts) != i] == old_max) + 1)
            mean = np.dot(relevance, current_probs)
            if mean >= 0.5 * num_trials:
                relevance_std[i] = 10000000000
                print('threshold')
            else:
                variance = np.dot(current_probs, (relevance - mean)**2)
                relevance_std[i] = np.sqrt(variance)
        else:
            variance = 0
            for target_id, target in enumerate(targets):
                relevance = np.zeros(len(upgrades), dtype=float)
                for upgrade_id, upgrade in enumerate(upgrades):
                    for trial_id in range(num_trials):
                        old_max = np.max(scores[trial_id, target_id, np.arange(num_artifacts) != i])
                        upgrade_score = score(upgrade[trial_id], target)
                        if upgrade_score > old_max:
                            relevance[upgrade_id] += 1
                        elif upgrade_score == old_max:
                            relevance[upgrade_id] += 1 / (np.count_nonzero(scores[trial_id, target_id, np.arange(num_artifacts) != i] == old_max) + 1)
        
                mean = np.dot(relevance, current_probs)
                if mean >= 0.5 * num_trials:
                    relevance_std[i] = 10000000000
                    print('threshold', target_id)
                    variance = -1
                    break
                variance += np.dot(current_probs, (relevance - mean)**2)
            if variance != -1:
                relevance_std[i] = np.sqrt(variance)


        '''
            for k in range(num_trials):
                if type(targets) == dict or (type(targets) == np.ndarray and targets.ndim == 1):
                    old_max = np.max(scores[k, np.arange(num_artifacts) != i])
                    upgrade_score = score(upgrade[k], targets)
                    if upgrade_score > old_max:
                        relevance[j] += 1
                    elif upgrade_score == old_max:
                        relevance[j] += 1 / (np.count_nonzero(scores[k, np.arange(num_artifacts) != i] == old_max) + 1)
                    #threshold = 0.5 * num_trials
                else:
                    for l, target in enumerate(targets):
                        old_max = np.max(scores[k, l, np.arange(num_artifacts) != i])
                        upgrade_score = score(upgrade[k], target)
                        if upgrade_score > old_max:
                            relevance[j] += 1
                        elif upgrade_score == old_max:
                            relevance[j] += 1 / (np.count_nonzero(scores[k, l, np.arange(num_artifacts) != i] == old_max) + 1)
                    #threshold = 0.5 * num_trials * len(targets)
                    
        mean = np.dot(relevance, current_probs)
        if mean >= 0.5 * num_trials:
            relevance_std[i] = 10000000000
            print('threshold')
            #break
        else:
            var = np.dot(current_probs, (relevance - mean)**2)
            relevance_std[i] = np.sqrt(var)
        '''
        
        #maxed[i] = original_maxed[i]
        
    for i in range(num_artifacts):
        if lvls[i] == 20:
            relevance_std[i] = 0
        else:
            relevance_std[i] /= MAX_REQ_EXP[lvls[i]]
            
    #print(relevance_std)
    persist[0] = np.argmax(relevance_std)
    print(np.max(relevance_std))
    print_artifact(artifacts[persist[0]])
    
    #for i in relevance_std:
    #    print(i)
    
    return relevance_std

if __name__ == '__main__':
    '''
    start = time.time()
    num = 30
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
        totals[i] = (simulate_exp(artifacts, np.zeros(200, dtype=int), targets, rank_temp))
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
    filename = 'artifacts/genshinData_GOOD_2025_07_26_19_37.json'
    artifacts, slots, rarities, lvls, sets = load(filename)
    relevant = rate(artifacts, slots, rarities, lvls, sets, rank_temp, num=100)
    
    count = 0
    
    visualize(relevant, artifacts, slots, sets, lvls)
    end = time.time()
    print(end - start)
    '''
    '''