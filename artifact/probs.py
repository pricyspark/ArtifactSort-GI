import numpy as np
from numpy.typing import NDArray
from itertools import combinations, permutations
from .constants import MAIN_PROBS, SUB_PROBS, TARGET_DTYPE, STAT_DTYPE

# Precompute the 24 permutations of positions [0,1,2,3]
PERMS = np.array(list(permutations(range(4))), dtype=int)  # (24,4)

COMBS = [np.array(list(combinations(np.arange(i), 4)), dtype=STAT_DTYPE) for i in range(11)]
#@njit
def base_artifact_probs(
    slot: str
) -> tuple[NDArray[STAT_DTYPE], NDArray[STAT_DTYPE], NDArray]:
    main_probs = MAIN_PROBS[slot]
    M = main_probs.size

    all_mains: list[NDArray[STAT_DTYPE]] = []
    all_subs: list[NDArray[STAT_DTYPE]]  = []
    all_probs: list[NDArray] = []

    zero_subs = None
    zero_probs = None

    for main in range(M):
        main_p = main_probs[main]
        
        if main_p <= 0:
            continue

        # Substats are the same for all main stats >= 10
        if main >= 10:
            # Check cache
            if zero_subs is None or zero_probs is None:
                # Miss
                cand = np.arange(10, dtype=STAT_DTYPE)
            else:
                # Hit
                all_mains.append(np.full(C, main, dtype=STAT_DTYPE))
                all_subs.append(zero_subs)
                all_probs.append(zero_probs)
                continue
        else:
            cand = np.delete(np.arange(10, dtype=STAT_DTYPE), main)
            
        w = SUB_PROBS[cand]
        total = w.sum()

        # All 4-combinations of candidate indices (indices into cand)
        comb_idx = COMBS[cand.size] # (C,4)
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

        all_mains.append(np.full(C, main, dtype=STAT_DTYPE))
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
def base_artifact_useful_probs(
    mains: NDArray[STAT_DTYPE], 
    subs: NDArray[STAT_DTYPE], 
    probs: NDArray, 
    target: NDArray[TARGET_DTYPE]
) -> tuple[NDArray[STAT_DTYPE], NDArray[STAT_DTYPE], NDArray]:
    useless_idx = np.flatnonzero(target == 0)
    
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

# TODO: simplify this. This is adapted from base_artifact_probs and overkill
DEFINE_PERMS = np.array(list(permutations(range(2))), dtype=int)

def base_define_probs(
    slot: str, 
    target: NDArray[TARGET_DTYPE]
) -> tuple[NDArray[STAT_DTYPE], NDArray[STAT_DTYPE], NDArray]:
    main = np.argmax(np.where(MAIN_PROBS[slot] == 0, 0, target))
    best_subs = np.argpartition(np.where(np.arange(19) == main, 0, target), -2)[-2:]
    
    if main < 10:
        cand = np.delete(np.arange(10, dtype=STAT_DTYPE), [main, *best_subs])
    else:
        cand = np.delete(np.arange(10, dtype=STAT_DTYPE), best_subs)
        
    w = SUB_PROBS[cand]
    total = w.sum()
    
    comb_idx = np.array(list(combinations(np.arange(cand.size), 2)), dtype=int)  # (C,4)
    C = comb_idx.shape[0]
    
    w_sel = w[comb_idx]
    w_perm = w_sel[:, DEFINE_PERMS]
    
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