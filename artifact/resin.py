import numpy as np
from numpy.typing import NDArray
import math
from .constants import ARTIFACT_DTYPE, LVL_DTYPE, TARGET_DTYPE, SLOTS
from .core import score
from .percentiles import artifact_percentile, reshape_percentile, define_percentile

def estimate_resin(percentile: float) -> float:
    if percentile == 0:
        return math.inf
    return math.ceil(1.065 / percentile) * 40

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

def reshape_resin(slot, base, target, threshold, unactivated, minimum=2):
    reshape_prob = reshape_percentile(base, target, threshold, unactivated, minimum)
    percentile = artifact_percentile(slot, target, threshold, 20)
    resin = estimate_resin(percentile)
    
    return reshape_prob * resin

def set_reshape_resin(artifacts, base_artifacts, slots, rarities, lvls, unactivated, sets, set_key, target, minimum=2, improvement=0.0):
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