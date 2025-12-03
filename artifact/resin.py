import numpy as np
from numpy.typing import NDArray
from typing import cast
import math
from .constants import ARTIFACT_DTYPE, LVL_DTYPE, TARGET_DTYPE, SLOTS, SLOT_2_NUM
from .core import score
from .probs import base_artifact_probs, base_artifact_useful_probs
from .percentiles import artifact_percentile, reshape_percentile, define_percentile, iterative_artifact_percentile

def estimate_resin(percentile: float) -> float:
    if percentile == 0:
        return math.inf
    return 1.065 / percentile * 40

def range_resin(
    artifacts: NDArray[ARTIFACT_DTYPE], 
    base_artifacts: NDArray[ARTIFACT_DTYPE],
    slots: NDArray[np.uint8], 
    rarities: NDArray[np.uint8], 
    lvls: NDArray[LVL_DTYPE], 
    unactivated: NDArray[np.bool],
    sets: NDArray[np.uint8], 
    set_key: int,
    target: NDArray[TARGET_DTYPE],
    slot: str,
    minimum: int = 2
) -> tuple[int, list[float], list[float], list[tuple[float, int]]]:
    d_costs = (1, 1, 2, 4, 3)
    r_costs = (1, 1, 2, 2, 2)
    slot_mask = np.logical_and(rarities == 5, slots == SLOT_2_NUM[slot])
    slot_mask = np.logical_and(slot_mask, lvls == 20)
    slot_mask = np.logical_and(slot_mask, sets == set_key)
    if np.count_nonzero(slot_mask) == 0:
        return (-1, [], [], [])
    
    useful_target = np.append(target, 0)
    mains, subs, probs = base_artifact_probs(slot)
    mains, subs, probs = base_artifact_useful_probs(mains, subs, probs, target)
    hundred_sixty_mask = (-1 < mains) & (mains < 3)
    base_scores = useful_target[mains] * np.where(hundred_sixty_mask, 160, 80)
    num_useful = np.count_nonzero(subs != -1, axis=1)
    num_useless = 4 - num_useful
    weights_all = np.sort(useful_target[subs], axis=1)
    
    scores = cast(NDArray, score(artifacts[slot_mask], target))
    slot_idx = np.argmax(scores)
    idx = np.flatnonzero(slot_mask)[slot_idx]
    best_score = scores[slot_idx]
    if best_score == 0:
        return (-2, [], [], [])
    
    resins: tuple[int, list[float], list[float], list[tuple[float, int]]] = (idx, [], [], [])
        
    candidates = np.zeros(len(artifacts), dtype=np.bool)
    candidates[slot_mask] = True
    
    improvement = 1.0
    possible_reshape = True
    while True:
        threshold = math.floor(best_score * improvement)
        improvement += 0.01
        percentile = iterative_artifact_percentile(
            useful_target, 
            threshold, 
            20, 
            slot, 
            info = (
                mains, 
                subs, 
                probs, 
                base_scores, 
                num_useful, 
                num_useless, 
                weights_all
            )
        )
        d_percentile = define_percentile(slot, target, threshold)
        
        if percentile == 0:
            break
        
        resin = estimate_resin(percentile)
        resins[1].append(resin)
        resins[2].append(d_percentile * resin / d_costs[SLOT_2_NUM[slot]])
        
        if not possible_reshape:
            continue
        
        best = 0
        best_idx = -1
        temp = []
        for i in range(len(artifacts)):
            if not candidates[i]:
                continue
            reshape_prob = reshape_percentile(base_artifacts[i], target, threshold, unactivated[i], minimum)
            temp.append(reshape_prob)
            if reshape_prob == 0:
                candidates[i] = False
            if reshape_prob > best:
                best = reshape_prob
                best_idx = i
               
        if best == 0:
            possible_reshape = False
            continue
        
        resins[3].append((best * resin / r_costs[SLOT_2_NUM[slot]], best_idx))
        
    return resins

def set_resin(
    artifacts: NDArray[ARTIFACT_DTYPE], 
    slots: NDArray[np.uint8], 
    rarities: NDArray[np.uint8], 
    lvls: NDArray[LVL_DTYPE], 
    sets: NDArray[np.uint8], 
    set_key: int, 
    target: NDArray[TARGET_DTYPE], 
    improvement: float = 0.0
) -> list[float]:
    slot_estimates = []
    
    for slot in range(5):
        slot_mask = np.logical_and(rarities == 5, slots == slot)
        slot_mask = np.logical_and(slot_mask, lvls == 20)
        slot_mask = np.logical_and(slot_mask, sets == set_key)
        scores = score(artifacts[slot_mask], target)
        threshold = np.max(scores) * (1 + improvement)
        percentile = artifact_percentile(SLOTS[slot], target, threshold, 20)
        slot_estimates.append(estimate_resin(percentile))
        
    return slot_estimates

def reshape_resin(
    slot: str, 
    base: NDArray[ARTIFACT_DTYPE], 
    target: NDArray[TARGET_DTYPE], 
    threshold: int, 
    unactivated: bool, 
    minimum: int = 2
) -> float:
    reshape_prob = reshape_percentile(base, target, threshold, unactivated, minimum)
    percentile = artifact_percentile(slot, target, threshold, 20)
    resin = estimate_resin(percentile)
    
    return reshape_prob * resin

def set_reshape_resin(
    artifacts: NDArray[ARTIFACT_DTYPE], 
    base_artifacts: NDArray[ARTIFACT_DTYPE], 
    slots: NDArray[np.uint8], 
    rarities: NDArray[np.uint8], 
    lvls: NDArray[LVL_DTYPE], 
    unactivated: NDArray[np.bool], 
    sets: NDArray[np.uint8], 
    set_key: int, 
    target: NDArray[TARGET_DTYPE], 
    minimum: int = 2, 
    improvement: float = 0.0
) -> list[tuple[float, int]]:
    slot_estimates = []
    costs = [1, 1, 2, 2, 2]
    
    for slot in range(5):
        slot_mask = np.logical_and(rarities == 5, slots == slot)
        slot_mask = np.logical_and(slot_mask, lvls == 20)
        slot_mask = np.logical_and(slot_mask, sets == set_key)
        scores = score(artifacts[slot_mask], target)
        threshold = np.max(scores) * (1 + improvement)
        best = 0
        best_idx = -1
        for i in range(len(artifacts)):
            if not slot_mask[i]:
                continue
            reshape_prob = reshape_percentile(base_artifacts[i], target, threshold, unactivated[i], minimum)
            if reshape_prob > best:
                best = reshape_prob
                best_idx = i
        print(slot, best_idx)
        percentile = artifact_percentile(SLOTS[slot], target, threshold, 20)
        resin = estimate_resin(percentile)
        saving = math.inf if resin == math.inf else round(best * resin / costs[slot])
        slot_estimates.append((saving, best_idx))
        
    return slot_estimates

def define_resin(slot, target, threshold):
    define_prob = define_percentile(slot, target, threshold)
    percentile = artifact_percentile(slot, target, threshold, 20)
    resin = estimate_resin(percentile)
    
    return define_prob * resin

def set_define_resin(artifacts, slots, rarities, lvls, sets, set_key, target, improvement=0.0):
    slot_estimates = []
    costs = [1, 1, 2, 4, 3]
    
    for slot in range(5):
        slot_mask = np.logical_and(rarities == 5, slots == slot)
        slot_mask = np.logical_and(slot_mask, lvls == 20)
        slot_mask = np.logical_and(slot_mask, sets == set_key)
        scores = score(artifacts[slot_mask], target)
        threshold = np.max(scores) * (1 + improvement)
        define_prob = define_percentile(SLOTS[slot], target, threshold)
        percentile = artifact_percentile(SLOTS[slot], target, threshold, 20)
        resin = estimate_resin(percentile)
        saving = math.inf if resin == math.inf else round(define_prob * resin / costs[slot])
        slot_estimates.append(saving)
        
    return slot_estimates