import numpy as np
import math
from numpy.typing import NDArray
from collections.abc import Collection
from typing import cast
from functools import lru_cache
from itertools import product
from .constants import CACHE_SIZE, ARTIFACT_DTYPE, TARGET_DTYPE
from .probs import base_artifact_probs, base_artifact_useful_probs, base_define_probs
from .core import score, find_sub
#from .core import *

COEFS = [np.array(list(product((7, 8, 9, 10), repeat=k)), dtype=ARTIFACT_DTYPE) for k in range(5)]

@lru_cache(maxsize=CACHE_SIZE)
def fixed_percentile_helper(
    diff: int, 
    num_upgrades: int, 
    weights: tuple[int]
) -> float:
    if diff < 0:
        return 1
    
    max_weight = weights[-1]
    
    upper_bound = max_weight * 10 * num_upgrades
    if diff >= upper_bound:
        return 0
        
    output = 0
    for weight in weights:
        for coef in (10, 9, 8, 7):
            temp_diff = diff - coef * weight
            temp_prob = fixed_percentile_helper(temp_diff, num_upgrades - 1, weights)
            if temp_prob == 0:
                break
            output += temp_prob

    return output / 16

@lru_cache(maxsize=CACHE_SIZE)
def random_percentile_helper(
    diff: int, 
    num_upgrades: int, 
    weights: tuple[int]
) -> float:
    if diff < 0:
        return 0.2 if num_upgrades == 0 else 1
    
    max_weight = weights[-1]
    
    upper_bound = max_weight * 10 * num_upgrades
    if diff >= upper_bound:
        return 0
        
    output = 0
    for weight in weights:
        for coef in (10, 9, 8, 7):
            temp_diff = diff - coef * weight
            temp_prob = random_percentile_helper(temp_diff, num_upgrades - 1, weights)
            if temp_prob == 0:
                break
            output += temp_prob

    return output / 16

def artifact_percentile(
    slot: str, 
    target: NDArray[TARGET_DTYPE], 
    threshold: int, 
    lvl: int
) -> float:
    if lvl < 0:
        raise ValueError('Invalid artifact level')
    
    mains, subs, probs = base_artifact_probs(slot)
    mains, subs, probs = base_artifact_useful_probs(mains, subs, probs, target)

    num_upgrades = lvl // 4
    new_target = np.append(target, 0)
    
    output = 0
    hundred_sixty_mask = (mains < 3) & (mains > -1)
    base_diffs = threshold - new_target[mains] * np.where(hundred_sixty_mask, 160, 80)
    num_useful = np.count_nonzero(subs != -1, axis=1)
    num_useless = 4 - num_useful
    
    for base_diff, s, p, useful, useless in zip(base_diffs, subs, probs, num_useful, num_useless):
        weights = np.sort(new_target[s])
        weights_tuple = tuple(weights)
        temp = 0
        base_substat_scores = weights[useless:] @ COEFS[useful].T
        for base_substat_score in base_substat_scores:
            temp += random_percentile_helper(base_diff - base_substat_score, num_upgrades, weights_tuple)
        output += p * temp / 4 ** useful
           
    return output

#@njit
def _iterative_helper(
    start: int, 
    w_memo: NDArray[TARGET_DTYPE], 
    max_weight: int, 
    weights: NDArray[TARGET_DTYPE]
) -> None:
    for i in range(w_memo.shape[0]):
        base = 0.2 if i == 1 else 1
        upper_bound = max_weight * 10 * i
        for j in range(start, upper_bound):
            # Vectorized version, which is slower ;;
            # temp_diff = j - (weights[:, None] * INCREMENTS).ravel()
            # neg = temp_diff < 0
            # temp = np.count_nonzero(neg) * base
            # temp += np.sum(w_memo[i - 1, temp_diff[~neg]])
            
            temp = 0
            for weight in weights:
                for coef in (10, 9, 8, 7):
                    temp_diff = j - coef * weight
                    if temp_diff < 0:
                        temp += base
                        continue
                    
                    prev = w_memo[i - 1, temp_diff]
                    if prev == 0:
                        break
                    temp += prev
            w_memo[i, j] = temp / 16
        w_memo[i, upper_bound:] = 0

memo = {} # Manual memoization instead of caching _iterative_helper for numba compatability
def iterative_artifact_percentile(
    useful_target: NDArray[TARGET_DTYPE], 
    threshold: int, 
    lvl: int, 
    slot: str | None = None, 
    info: Collection | None = None
) -> float:
    if lvl < 0:
        raise ValueError('Invalid artifact level')
        
    if info is None:
        assert isinstance(slot, str)
        mains, subs, probs = base_artifact_probs(slot)
        mains, subs, probs = base_artifact_useful_probs(mains, subs, probs, useful_target)
        hundred_sixty_mask = (-1 < mains) & (mains < 3)
        base_scores = useful_target[mains] * np.where(hundred_sixty_mask, 160, 80)
        num_useful = np.count_nonzero(subs != -1, axis=1)
        num_useless = 4 - num_useful
        weights_all = np.sort(useful_target[subs], axis=1)
    else:
        mains, subs, probs, base_scores, num_useful, num_useless, weights_all = info

    num_upgrades = lvl // 4
    #new_target = np.append(target, 0)
    base = 0.2 if num_upgrades == 0 else 1

    base_diffs = threshold - base_scores
    
    temp = np.empty(len(base_diffs))
    for i, (base_diff, weights, useful, useless) in enumerate(zip(base_diffs, weights_all, num_useful, num_useless)):
        #weights_tuple = tuple(weights)
        weights_key = np.ascontiguousarray(weights).view(np.uint16).tobytes()
        max_weight = weights[-1]
        
        start = None
        if weights_key not in memo:
            # TODO: the first row of this is all zeros. Maybe fix since
            # that's wasted memory
            super_loose_upper_bound = max(threshold + 1, 250 * max_weight) # TODO: this is so overkill but I'm too tired to think
            memo[weights_key] = np.zeros((6, super_loose_upper_bound + 1)) # TODO: check if this is correct or should be expanded
            start = 0
        elif memo[weights_key].shape[1] < threshold + 1:
            w_memo = memo[weights_key]
            start = w_memo.shape[1]
            new_memo = np.zeros((6, threshold + 1))
            new_memo[:, :start] = w_memo
            memo[weights_key] = new_memo
        
        w_memo: np.ndarray = memo[weights_key]
        
        if start is not None:
            _iterative_helper(start, w_memo, max_weight, weights)
            
        base_substat_scores = weights[useless:] @ COEFS[useful].T
        diffs = base_diff - base_substat_scores
        row = w_memo[num_upgrades]
        base_count = np.count_nonzero(diffs < 0)
        recurse = np.take(row, diffs, mode='clip') # negatives become row[0]
        temp[i] = recurse.sum() + base_count * (base - row[0])
        # More readable equivalent
        # neg = diffs < 0
        # row = w_memo[num_upgrades]
        # temp[i] = np.count_nonzero(neg) * base + np.sum(row[diffs[~neg]])
    return np.sum(probs * temp / 4 ** num_useful)

def upgrade_percentile(
    artifact: NDArray[ARTIFACT_DTYPE], 
    slvl: int, 
    target: NDArray[TARGET_DTYPE], 
    threshold: int, 
    base_score: int | None = None
) -> float:
    num_upgrades = 4 if slvl < 0 else 5 - slvl // 4
    
    if base_score is None:
        base_score = cast(int, score(artifact, target))
    base_diff = threshold - base_score
    
    subs = find_sub(artifact)
    weights = np.sort(target[subs])
    weights_tuple = tuple(weights)
    
    return fixed_percentile_helper(base_diff, num_upgrades, weights_tuple)

def define_percentile(
    slot: str, 
    target: NDArray[TARGET_DTYPE], 
    threshold: int
) -> float:
    @lru_cache(maxsize=CACHE_SIZE)
    def _define_helper(diff: int, num_good: int, num_upgrades: int) -> float:
        if num_good + num_upgrades < MINIMUM:
            return -1
        
        if diff < 0 and num_good >= MINIMUM:
            return 0.2 if num_upgrades == 0 else 1 # TODO: fine out if this should be 1/3
        
        if num_upgrades == 0:
            return 0
        
        upper_bound = max_weight * 10 * num_upgrades
        if diff >= upper_bound:
            return 0
        
        output = 0
        for sub in s:
            temp_num_good = num_good + 1 if sub in best_subs else num_good
            for coef in (10, 9, 8, 7):
                temp_diff = diff - cast(int, coef * new_target[sub])
                temp_prob = _define_helper(temp_diff, temp_num_good, num_upgrades - 1)
                if temp_prob == -1:
                    break
                
                output += temp_prob
                
        return output / 16
    
    MINIMUM = 2
    
    prob_valid = 0
    # Probability 3-stat has minimum good rolls
    temp = 0
    for i in range(5 - MINIMUM):
        temp += math.comb(4, i)
    prob_valid += 0.8 * temp / 2 ** 4
    # Probability 4-stat has minimum good rolls
    temp = 0
    for i in range(6 - MINIMUM):
        temp += math.comb(5, i)
    prob_valid += 0.2 * temp / 2 ** 5
    
    mains, subs, probs = base_define_probs(slot, target)
    mains, subs, probs = base_artifact_useful_probs(mains, subs, probs, target)
    
    new_target = np.append(target, 0).astype(TARGET_DTYPE)
    
    best_subs = subs[0, [np.argpartition(new_target[subs[0]], -2)[-2:]]]
    
    output = 0
    for m, s, p in zip(mains, subs, probs):
        diff = threshold - cast(int, new_target[m]) * (160 if m < 3 else 80)
        num_useful = int(np.count_nonzero(s != -1)) # TODO: is this kind of casting the best option
        num_useless = 4 - num_useful
        max_weight = np.max(new_target[s])
        for coefs in COEFS[num_useful]:
            coefs = [0] * num_useless + list(coefs)
            temp_diff = diff - cast(int, coefs @ new_target[s])
            output += p * _define_helper(temp_diff, 0, 5) / 4 ** num_useful
            
        _define_helper.cache_clear()
        
    return output / prob_valid

def reshape_percentile(
    base: NDArray[ARTIFACT_DTYPE],
    target: NDArray[TARGET_DTYPE], 
    threshold: int, 
    unactivated: bool, 
    minimum: int = 2
) -> float:
    # TODO: This is copy-pasted from define. Find a more elegant solution
    @lru_cache(maxsize=CACHE_SIZE)
    def _reshape_helper(diff: int, num_good: int, num_upgrades: int) -> float:
        if num_good + num_upgrades < minimum:
            return -1
        
        if diff < 0 and num_good >= minimum:
            return 1
        
        if num_upgrades == 0:
            return 0
        
        upper_bound = max_weight * 10 * num_upgrades
        if diff >= upper_bound:
            return 0
        
        output = 0
        for sub in subs:
            temp_num_good = num_good + 1 if sub in best_subs else num_good
            for coef in (10, 9, 8, 7):
                temp_diff = cast(int, diff - coef * target[sub])
                temp_prob = _reshape_helper(temp_diff, temp_num_good, num_upgrades - 1)
                if temp_prob == -1:
                    break
                
                output += temp_prob
                
        return output / 16
    
    prob_valid = 0
    if unactivated:
        # Probability 3-stat has minimum good rolls
        temp = 0
        for i in range(5 - minimum):
            temp += math.comb(4, i)
        prob_valid += temp / 2 ** 4
    else:
        # Probability 4-stat has minimum good rolls
        temp = 0
        for i in range(6 - minimum):
            temp += math.comb(5, i)
        prob_valid += temp / 2 ** 5
    
    base_score = cast(int, score(base, target))
    
    subs = find_sub(base)
    
    best_subs = np.argpartition(target[subs], -2)
    best_subs = subs[best_subs[-2:]]
    max_weight = np.max(target[subs])
    
    num_upgrades = 4 if unactivated else 5
    diff = threshold - base_score
    
    output = _reshape_helper(diff, 0, num_upgrades)
    _reshape_helper.cache_clear()
    return output / prob_valid