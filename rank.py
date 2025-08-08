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
        # maximum per (i, j)
        cutoff = scores.max(axis=0)                    # shape (num_trials, num_targets)
    elif k == 2:
        k_plus_cutoff, k_cutoff, k_minus_cutoff = np.partition(scores, (-k - 1, -k, -k + 1), axis=0)[-k - 1:]
        #cutoff = np.partition(scores, -k, axis=0)[-k]  # same shape
    else:
        k_plus_cutoff, k_cutoff, k_minus_cutoff = np.partition(scores, (-k - 1, -k, -k + 1), axis=0)[-k - 1:-k + 1]
        #cutoff = np.partition(scores, -k, axis=0)[-k]  # same shape

    k_above = scores > k_cutoff                 # shape (n_items, num_trials, num_targets)
    k_above_count = np.count_nonzero(k_above, axis=0)
    k_leftover = k - k_above_count

    k_eq    = scores == k_cutoff
    k_tie_count = np.count_nonzero(k_eq, axis=0)
    k_frac_per_tie = k_leftover / k_tie_count
    k_eq_contrib = k_eq * k_frac_per_tie

    k_plus_above = scores > k_plus_cutoff
    k_plus_above_count = np.count_nonzero(k_plus_above, axis=0)

    k_plus_eq    = scores == k_plus_cutoff
    k_plus_tie_count = np.count_nonzero(k_plus_eq, axis=0)

    k_minus_above = scores > k_minus_cutoff
    k_minus_above_count = np.count_nonzero(k_minus_above, axis=0)

    k_minus_eq    = scores == k_minus_cutoff
    k_minus_tie_count = np.count_nonzero(k_minus_eq, axis=0)

    
    relevance = np.count_nonzero(k_above, axis=1).astype(float)
    relevance += k_eq_contrib.sum(axis=1)
    
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
    
    current_entropies = my_entropy(relevance, axis=0)
    
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
        
        new_k_above = scores > new_k_cutoff
        new_k_above_count = np.count_nonzero(new_k_above, axis=0)
        
        adjusted_k_plus_above_count = k_plus_above_count - k_plus_above[i]
        adjusted_k_minus_above_count = k_minus_above_count - k_minus_above[i]
        adjusted_k_above_count = k_above_count - k_above[i]
        
        adjusted_k_plus_tie_count = k_plus_tie_count - k_plus_eq[i]
        adjusted_k_minus_tie_count = k_minus_tie_count - k_minus_eq[i]
        adjusted_k_tie_count = k_tie_count - k_eq[i]
        
        for upgrade, prob in zip(distros_scores[i], probs):
            if prob == 0:
                continue
            
            scores[i] = upgrade # (num_trials, num_targets)
            
            if k == 1:
                cutoff = scores.max(axis=0)
            else:
                potential_cutoff = np.minimum(upgrade, new_k_minus_cutoff)
                cutoff = np.maximum(potential_cutoff, new_k_cutoff)
            
            # TARGET
            above = scores > cutoff
            eq = scores == cutoff
            above_count = np.count_nonzero(above, axis=0)
            leftover = k - above_count
            tie_count = np.count_nonzero(eq, axis=0)
            frac_per_tie = leftover / tie_count
            eq_contrib = eq * frac_per_tie
            target_relevance = np.count_nonzero(above, axis=1).astype(float)
            target_relevance += eq_contrib.sum(axis=1)
                
            #ent = my_entropy(target_relevance, axis=0)
            #information_gain[i] -= prob * ent
            '''
            '''
            
            '''
            # TEST
            upgrade_above = upgrade > cutoff
            upgrade_eq = upgrade == cutoff
            
            above = np.zeros((num_artifacts, num_trials, num_targets), dtype=bool)
            above[:, cutoff == upgrade] = new_k_above[:, cutoff == upgrade]
            above[:, cutoff == k_plus_cutoff] = k_plus_above[:, cutoff == k_plus_cutoff]
            above[:, cutoff == k_minus_cutoff] = k_minus_above[:, cutoff == k_minus_cutoff]
            above[:, cutoff == k_cutoff] = k_above[:, cutoff == k_cutoff]
            above[i] = upgrade_above
            
            eq = np.zeros((num_artifacts, num_trials, num_targets), dtype=bool)
            eq[:, cutoff == k_plus_cutoff] = k_plus_eq[:, cutoff == k_plus_cutoff]
            eq[:, cutoff == k_minus_cutoff] = k_minus_eq[:, cutoff == k_minus_cutoff]
            eq[:, cutoff == k_cutoff] = k_eq[:, cutoff == k_cutoff]
            eq[i] = upgrade_eq
            
            above_count = np.zeros((num_trials, num_targets), dtype=int)
            above_count[cutoff == upgrade] = new_k_above_count[cutoff == upgrade]
            above_count[cutoff == k_plus_cutoff] = adjusted_k_plus_above_count[cutoff == k_plus_cutoff]
            above_count[cutoff == k_minus_cutoff] = adjusted_k_minus_above_count[cutoff == k_minus_cutoff]
            above_count[cutoff == k_cutoff] = adjusted_k_above_count[cutoff == k_cutoff]
            above_count += upgrade_above
            
            leftover = k - above_count
            
            tie_count = np.zeros((num_trials, num_targets), dtype=int)
            tie_count[cutoff == k_plus_cutoff] = adjusted_k_plus_tie_count[cutoff == k_plus_cutoff]
            tie_count[cutoff == k_minus_cutoff] = adjusted_k_minus_tie_count[cutoff == k_minus_cutoff]
            tie_count[cutoff == k_cutoff] = adjusted_k_tie_count[cutoff == k_cutoff]
            tie_count += upgrade_eq
            
            frac_per_tie = leftover / tie_count
            eq_contrib = eq * frac_per_tie
            test_relevance = np.count_nonzero(above, axis=1).astype(float)
            test_relevance += eq_contrib.sum(axis=1)
            
            if not np.allclose(target_relevance, test_relevance):
                raise ValueError
            
            ent = entropy(test_relevance, axis=0)
            information_gain[i] -= prob * ent
            '''
            
            # CHAT
            upgrade_above = upgrade > cutoff
            upgrade_eq = upgrade == cutoff
            mode_upgrade = (cutoff == upgrade)
            mode_kplus   = (cutoff == k_plus_cutoff)
            mode_kminus  = (cutoff == k_minus_cutoff)
            mode_k       = (cutoff == k_cutoff)

            # 1) above_count and tie_count without temp arrays or repeated indexing
            above_count = np.where(
                mode_k, adjusted_k_above_count,
                np.where(mode_kplus,  adjusted_k_plus_above_count,
                np.where(mode_kminus, adjusted_k_minus_above_count,
                np.where(mode_upgrade, new_k_above_count, 0)))
            )
            above_count += upgrade_above  # bool -> int, adds 1 where upgrade_above is True
            
            leftover   = k - above_count
            
            tie_count  = np.where(
                mode_kplus,  adjusted_k_plus_tie_count,
                np.where(mode_kminus, adjusted_k_minus_tie_count, np.where(mode_k, adjusted_k_tie_count, 0))
            )
            tie_count += upgrade_eq  # include upgraded artifact's ties

            # Avoid division warnings; when tie_count==0, frac is never used because eq is False there.
            with np.errstate(divide='ignore', invalid='ignore'):
                frac = (leftover / tie_count).astype(np.float32)
                frac[tie_count == 0] = 0.0

            # 2) above term WITHOUT building a 3D boolean "above" tensor
            #    Sum along trials immediately, masked by the mode for each (trial, target).
            eff_k       = mode_k
            eff_kminus  = mode_kminus & ~eff_k
            eff_kplus   = mode_kplus  & ~(eff_k | eff_kminus)
            eff_upgrade = mode_upgrade & ~(eff_k | eff_kminus | eff_kplus)

            # --- ABOVE term without building a 3D scratch array ---
            above_sum = (
                (new_k_above  & eff_upgrade[None, ...]).sum(axis=1, dtype=np.int32) +
                (k_plus_above & eff_kplus[None,   ...]).sum(axis=1, dtype=np.int32) +
                (k_minus_above& eff_kminus[None,  ...]).sum(axis=1, dtype=np.int32) +
                (k_above      & eff_k[None,       ...]).sum(axis=1, dtype=np.int32)
            )

            # Row i is fully overridden by the upgrade in your original code
            above_sum[i] = upgrade_above.sum(axis=0, dtype=np.int32).astype(np.float32)
            
            # 3) tie contribution via einsum (no big temp like eq * frac_per_tie)
            #    For each bank, only positions in its mode contribute.
            def eq_contrib(eq_bank, eff_mask):
                # sum over trials with fractional tie credit
                return np.einsum('ijk,jk->ik', eq_bank & eff_mask[None, ...], frac, optimize=True)

            eq_term = (
                eq_contrib(k_plus_eq,  eff_kplus) +
                eq_contrib(k_minus_eq, eff_kminus) +
                eq_contrib(k_eq,       eff_k)
            )

            # Row i override
            eq_term[i] = np.einsum('jk,jk->k', upgrade_eq, frac, optimize=True).astype(np.float32)

            # --- final relevance and entropy ---
            test_relevance = above_sum + eq_term                                   # shape: (num_artifacts, num_targets)
            ent = my_entropy(test_relevance, axis=0)                     # per-target entropy
            information_gain[i] -= prob * ent
            if not np.allclose(test_relevance, target_relevance):
                raise ValueError
                        
            '''

            
            above = scores > cutoff
            eq    = scores == cutoff
            
            above_count = np.count_nonzero(above, axis=0)
            leftover = k - above_count
            
            tie_count = np.count_nonzero(eq, axis=0)
            frac_per_tie = leftover / tie_count
            eq_contrib = eq * frac_per_tie
            #relevance = above.sum(axis=1).astype(float)
            relevance = np.count_nonzero(above, axis=1).astype(float)
            relevance += eq_contrib.sum(axis=1)
            
            
            upgrade_above = upgrade > cutoff
            upgrade_eq = upgrade == cutoff
            
            new_above = np.zeros_like(k_above)
            new_above[:, cutoff == upgrade] = new_k_above[:, cutoff == upgrade]
            new_above[:, cutoff == k_plus_cutoff] = k_plus_above[:, cutoff == k_plus_cutoff]
            new_above[:, cutoff == k_minus_cutoff] = k_minus_above[:, cutoff == k_minus_cutoff]
            new_above[:, cutoff == k_cutoff] = k_above[:, cutoff == k_cutoff]
            
            # This isn't exactly the same when the new upgrade is the k cutoff.
            # With this, the cutoff is "above" since upgrade > new_k_cutoff, when
            # it should be equal. However, this doesn't matter, since my definition,
            # it must be unique, and thus the eq part of relevance will give it a value
            # of 1 anyways. So leave this, and if cutoff == upgrade for eq, don't do anything.
            
            actual_above_count = np.zeros_like(k_above_count)
            actual_above_count[cutoff == upgrade] = (new_k_above_count - new_k_above[i])[cutoff == upgrade]
            actual_above_count[cutoff == k_plus_cutoff] = (k_plus_above_count - k_plus_above[i])[cutoff == k_plus_cutoff]
            actual_above_count[cutoff == k_minus_cutoff] = (k_minus_above_count - k_minus_above[i])[cutoff == k_minus_cutoff]
            actual_above_count[cutoff == k_cutoff] = (k_above_count - k_above[i])[cutoff == k_cutoff]
            actual_above_count += upgrade_above
            new_above[i] = upgrade_above
            target_above_count = np.count_nonzero(new_above, axis=0)
            
            a = np.allclose(target_above_count[cutoff == upgrade], actual_above_count[cutoff == upgrade])
            b = np.allclose(target_above_count[cutoff == k_plus_cutoff], actual_above_count[cutoff == k_plus_cutoff])
            c = np.allclose(target_above_count[cutoff == k_minus_cutoff], actual_above_count[cutoff == k_minus_cutoff])
            d = np.allclose(target_above_count[cutoff == k_cutoff], actual_above_count[cutoff == k_cutoff])
            if not a:
                raise ValueError
            if not b:
                raise ValueError
            if not c:
                raise ValueError
            if not d:
                raise ValueError
            
            something_leftover = k - actual_above_count
            
            new_eq = np.zeros_like(k_above)
            #eq_attempt[:, cutoff == upgrade] = 0
            new_eq[:, cutoff == k_plus_cutoff] = k_plus_eq[:, cutoff == k_plus_cutoff]
            new_eq[:, cutoff == k_minus_cutoff] = k_minus_eq[:, cutoff == k_minus_cutoff]
            #eq_attempt[:, cutoff == upgrade] = (scores == cutoff)[:, cutoff == upgrade]
            new_eq[:, cutoff == k_cutoff] = k_eq[:, cutoff == k_cutoff]
            
            
            actual_tie_count = np.zeros_like(k_tie_count)
            actual_tie_count[cutoff == upgrade] = (0 - new_k_eq[i])[cutoff == upgrade]
            actual_tie_count[cutoff == k_plus_cutoff] = (k_plus_tie_count - k_plus_eq[i])[cutoff == k_plus_cutoff]
            actual_tie_count[cutoff == k_minus_cutoff] = (k_minus_tie_count - k_minus_eq[i])[cutoff == k_minus_cutoff]
            actual_tie_count[cutoff == k_cutoff] = (k_tie_count - k_eq[i])[cutoff == k_cutoff]
            actual_tie_count += upgrade_eq
            new_eq[i] = upgrade_eq
            target_tie_count = np.count_nonzero(new_eq, axis=0)
            
            a = np.allclose(target_tie_count[cutoff == upgrade], actual_tie_count[cutoff == upgrade])
            b = np.allclose(target_tie_count[cutoff == k_plus_cutoff], actual_tie_count[cutoff == k_plus_cutoff])
            c = np.allclose(target_tie_count[cutoff == k_minus_cutoff], actual_tie_count[cutoff == k_minus_cutoff])
            d = np.allclose(target_tie_count[cutoff == k_cutoff], actual_tie_count[cutoff == k_cutoff])
            if not a:
                where = np.where(target_tie_count != actual_tie_count)
                target = target_tie_count[target_tie_count != actual_tie_count]
                actual = actual_tie_count[target_tie_count != actual_tie_count]
                current_cutoffs = cutoff[target_tie_count != actual_tie_count]
                current_upgrade = upgrade[target_tie_count != actual_tie_count]
                raise ValueError
            if not b:
                raise ValueError
            if not c:
                raise ValueError
            if not d:
                raise ValueError


            #if not np.allclose(eq_attempt, eq):
            #    raise ValueError

            above_count_attempt = np.count_nonzero(new_above, axis=0)
            leftover_attempt = k - above_count_attempt

            tie_count_attempt = np.count_nonzero(new_eq, axis=0)
            frac_per_tie_attempt = leftover_attempt / tie_count_attempt
            eq_contrib_attempt = new_eq * frac_per_tie_attempt
            relevance_attempt = np.count_nonzero(new_above, axis=1).astype(float)
            relevance_attempt += eq_contrib_attempt.sum(axis=1)
            
            
            
            above_count = np.count_nonzero(above, axis=0)
            leftover = k - above_count
            
            if not np.array_equal(leftover, something_leftover):
                raise ValueError

            tie_count = np.count_nonzero(eq, axis=0)
            frac_per_tie = leftover / tie_count
            eq_contrib = eq * frac_per_tie[None, ...]
            #relevance = above.sum(axis=1).astype(float)
            relevance = np.count_nonzero(above, axis=1).astype(float)
            relevance += eq_contrib.sum(axis=1)

            if not np.allclose(relevance, relevance_attempt):
                upgrade_mask = np.where(cutoff == upgrade)
                mask = relevance != relevance_attempt
                where = np.where(mask)
                target = relevance[mask]
                actual = relevance_attempt[mask]
                target_ties = tie_count[cutoff == upgrade]
                actual_ties = tie_count_attempt[cutoff == upgrade]
                equal = np.array_equal(target_ties, actual_ties)
                sums = np.sum(relevance_attempt, axis=0)
                raise ValueError
            


            #tie_count = eq.sum(axis=0)
            
            #ent = my_entropy(relevance, axis=0)
            ent = my_entropy(relevance_attempt, axis=0)
            information_gain[i] -= prob * ent
            '''
            #print('iteration')
            
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
