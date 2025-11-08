import numpy as np
from itertools import combinations, permutations
from .constants import *

#@njit
def base_artifact_probs(slot):
    main_probs = MAIN_PROBS[slot]
    M = main_probs.size

    # Precompute the 24 permutations of positions [0,1,2,3]
    PERMS = np.array(list(permutations(range(4))), dtype=int)  # (24,4)

    all_mains = []
    all_subs  = []
    all_probs = []

    zero_subs = None
    zero_probs = None

    for main in range(M):
        main_p = main_probs[main]
        
        if main_p <= 0:
            continue

        # Substats are the same for all main stats >= 10
        if main >= 10:
            # Check cache
            if zero_subs is None:
                # Miss
                cand = np.arange(10)
            else:
                # Hit
                all_mains.append(np.full(C, main, dtype=int))
                all_subs.append(zero_subs)
                all_probs.append(zero_probs)
                continue
        else:
            cand = np.delete(np.arange(10), main)
            
        w = SUB_PROBS[cand]
        total = w.sum()

        # All 4-combinations of candidate indices (indices into cand)
        comb_idx = np.array(list(combinations(np.arange(cand.size), 4)), dtype=int)  # (C,4)
        C = comb_idx.shape[0]

        # Weights for each combination, shape (C,4)
        w_sel = w[comb_idx]  # (C,4)

        # Reorder the 4 chosen weights along the 24 permutations: (C,24,4)
        w_perm = w_sel[:, PERMS]  # advanced indexing -> (C,24,4)

        # Denominators per step: total - exclusive cumsum of chosen weights
        # exclusive cumsum: cs_excl[..., k] = sum of previous weights (k terms)
        cs = np.cumsum(w_perm, axis=-1)                # (C,24,4)
        cs_excl = cs - w_perm                           # exclusive
        denoms = total - cs_excl                        # (C,24,4)

        # Order probability for each perm: prod_k w_perm[...,k] / denoms[...,k]
        with np.errstate(divide='ignore', invalid='ignore'):
            ratios = np.where(denoms > 0, w_perm / denoms, 0.0)
            p_order = np.prod(ratios, axis=-1)         # (C,24)

        # Unordered subset prob = sum over the 24 orders
        p_subset = p_order.sum(axis=1)                 # (C,)

        # Map back to original stat indices for the subset
        subs = cand[comb_idx]                          # (C,4)
        subs.sort(axis=1)                              # keep canonical order

        # Multiply by main probability
        probs = main_p * p_subset

        all_mains.append(np.full(C, main, dtype=int))
        all_subs.append(subs)
        all_probs.append(probs)
        if main >= 10:
            zero_subs = subs
            zero_probs = probs

    mains = np.concatenate(all_mains, axis=0)
    subs  = np.vstack(all_subs)
    probs = np.concatenate(all_probs, axis=0)
    
    return mains, subs, probs

#@njit
def base_artifact_useful_probs(mains, subs, probs, target):
    useless_idx = np.where(target == 0)[0]
    
    if len(useless_idx) == 0:
        return mains, subs, probs

    # Mark useless substats as -1
    combine = np.column_stack((mains, subs))
    np.putmask(combine, np.isin(combine, useless_idx), -1)
        
    v = combine[:, 1:]
    v.sort(axis=1)
        
    uniq, inv = np.unique(combine, axis=0, return_inverse=True)
    probs_out = np.bincount(inv, weights=probs)

    mains_out = uniq[:, 0].astype(int)
    subs_out  = uniq[:, 1:].astype(int)

    return mains_out, subs_out, probs_out

def base_define_probs(slot, target):
    main = np.argmax(np.where(MAIN_PROBS[slot] == 0, 0, target))
    best_subs = np.argpartition(np.where(np.arange(19) == main, 0, target), -2)[-2:]
    
    # TODO: simplify this. This is adapted from base_artifact_probs and overkill
    perms = np.array(list(permutations(range(2))), dtype=int)
    
    if main < 10:
        cand = np.delete(np.arange(10), [main, *best_subs])
    else:
        cand = np.delete(np.arange(10), best_subs)
        
    w = SUB_PROBS[cand]
    total = w.sum()
    
    comb_idx = np.array(list(combinations(np.arange(cand.size), 2)), dtype=int)  # (C,4)
    C = comb_idx.shape[0]
    
    w_sel = w[comb_idx]
    w_perm = w_sel[:, perms]
    
    cs = np.cumsum(w_perm, axis=-1)
    cs_excl = cs - w_perm
    denoms = total - cs_excl
    
    with np.errstate(divide='ignore', invalid='ignore'):
        ratios = np.where(denoms > 0, w_perm / denoms, 0.0)
        p_order = np.prod(ratios, axis=-1)
        
    probs = p_order.sum(axis=1)
    
    subs = cand[comb_idx]
    subs = np.concatenate([subs, np.broadcast_to(best_subs, (len(subs), best_subs.shape[0]))], axis=1)
    subs.sort(axis=1)
    
    return np.full(C, main, dtype=int), subs, probs