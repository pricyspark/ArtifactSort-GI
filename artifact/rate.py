import numpy as np
from numpy.typing import NDArray
from typing import cast
import sys
import pickle
from functools import lru_cache
from typing import Callable
from .constants import CACHE_PATH, SLVL_DTYPE, SLOTS, SETS, ARTIFACT_DTYPE, CACHE_SIZE, TARGET_DTYPE, TOP_CACHE_PATH
from .targets import ALL_TARGETS, SET_TARGETS
from .core import find_main, find_sub, score, multi_vectorize
from .distributions import trim_distro
from .probs import base_artifact_probs, base_artifact_useful_probs
from .percentiles import iterative_artifact_percentile

try:
    with open(TOP_CACHE_PATH, 'rb') as f:
        top_cache: dict[tuple[str, int, bytes], float] = pickle.load(f)
    print('Top cache loaded')
except:
    top_cache: dict[tuple[str, int, bytes], float] = {}
    print('No top cache found')

try:
    with open(CACHE_PATH, 'rb') as f:
        helper_cache: dict[tuple[str, int, bytes], float] = pickle.load(f)
    print('Helper cache loaded')
except:
    helper_cache: dict[tuple[str, int, bytes], float] = {}
    print('No helper cache found')

def top_key(
    slot: str, 
    target: NDArray[TARGET_DTYPE], 
    artifact: NDArray[ARTIFACT_DTYPE], 
    slvl: int
) -> tuple:
    return (slot, target.tobytes(), artifact.tobytes(), slvl)

class CachePercentile:
    distros = [[trim_distro(j, i) for i in range(5)] for j in range(6)]
    def __init__(self, slot: str, target: NDArray[TARGET_DTYPE]) -> None:
        self.slot = slot
        self.target = target
        self.target.setflags(write=False)
        self.useful_target = np.append(target, 0)
        self.useful_target.setflags(write=False)
        mains, subs, probs = base_artifact_probs(slot)
        mains, subs, probs = base_artifact_useful_probs(mains, subs, probs, target)
        self.mains, self.subs, self.probs = mains, subs, probs
        hundred_sixty_mask = (-1 < mains) & (mains < 3)
        self.base_scores = self.useful_target[mains] * np.where(hundred_sixty_mask, 160, 80)
        self.num_useful = np.count_nonzero(subs != -1, axis=1)
        self.num_useless = 4 - self.num_useful
        self.weights_all = np.sort(self.useful_target[subs], axis=1)
        
    # Double caching is memory inefficient, but lru_cache uses native
    # C-caching, so it's way faster than dict caching
    # TODO: make this more elegant
    @lru_cache(maxsize=CACHE_SIZE)
    def helper(self, threshold: int) -> float:
        target_key = (self.slot, threshold, np.ascontiguousarray(self.target).tobytes())
        if target_key in helper_cache:
            return helper_cache[target_key]
        asdf = iterative_artifact_percentile(
            self.useful_target, 
            threshold, 
            20, 
            info=(
                self.mains, 
                self.subs, 
                self.probs, 
                self.base_scores, 
                self.num_useful, 
                self.num_useless, 
                self.weights_all))
        helper_cache[target_key] = asdf
        return asdf
    
    def percent(self, artifact: NDArray[ARTIFACT_DTYPE], slvl: int) -> float:
        key = top_key(self.slot, self.target, artifact, slvl)
        if key in top_cache:
            return top_cache[key]
        # TODO: maybe njit
        if slvl < 0:
            num_upgrades = 4
        else:
            num_upgrades = 5 - slvl // 4
        
        main = find_main(artifact)
        useful_subs = find_sub(artifact * self.target, main)
        num_useful = len(useful_subs)
        d, p = CachePercentile.distros[num_upgrades][num_useful]
        temp = np.repeat(artifact[None, :], len(d), axis=0)
        for i, sub in enumerate(useful_subs):
            temp[:, sub] += d[:, i]
        d = temp
        
        scores = cast(np.ndarray, score(d, self.target)).astype(int) - 1
        values, inverse = np.unique(scores, return_inverse=True) # Cannot njit this
        probs = np.bincount(inverse, weights=p)
        rarities = [self.helper(x) for x in values]
        output = np.sum(probs / rarities)
        top_cache[key] = output
        return output

def rate(
    artifacts: NDArray[ARTIFACT_DTYPE], 
    slots: NDArray[np.unsignedinteger], 
    mask: NDArray[np.bool], 
    slvls: NDArray[SLVL_DTYPE], 
    sets: NDArray[np.unsignedinteger], 
    ranker: Callable, k: int = 1
) -> tuple[NDArray, NDArray[np.unsignedinteger]]:
    # TODO: change persist to persist_artifact and persist_meta, for
    # more intuitive control over things like set masking
    relevance = np.zeros((len(artifacts), 2), dtype=float)
    counts = np.zeros((len(artifacts), 2), dtype=int)
    for slot in range(5):
        # TODO: this won't work if there's 0 artifacts
        #slot_mask = np.logical_and(mask, slots == slot)
        slot_mask = mask & (slots == slot)
        slot_original_idxs = np.flatnonzero(slot_mask)
        slot_artifacts = artifacts[slot_mask]
        slot_lvls = slvls[slot_mask]
        persist = {}
        relevance[slot_mask, 0] = ranker(slot_artifacts, slot_lvls, persist, ALL_TARGETS[SLOTS[slot]], k=2 * k)
        counts[slot_mask, 0] = len(slot_artifacts)
        
        for setKey in range(len(SETS)):
            set_mask = sets[slot_mask] == setKey
            if np.all(set_mask == 0):
                continue
            #new_mask = np.logical_and(mask, sets == setKey)
            set_original_idxs = slot_original_idxs[set_mask]
            set_artifacts = slot_artifacts[set_mask]
            set_lvls = slot_lvls[set_mask]
            set_persist = {}
            for a, b in persist.items():
                try:
                    #temp = asdf[set_mask]
                    if type(b) == np.ndarray:
                        temp = b[set_mask]
                    else:
                        temp = [val for val, m in zip(b, set_mask) if m]
                    set_persist[a] = temp
                    #set_persist.append(temp)
                except Exception as e:
                    set_persist[a] = b
                    #set_persist.append(None)
            #set_persist = [asdf[np.where(set_mask)[0]] for asdf in persist]
            relevance[set_original_idxs, 1] = ranker(set_artifacts, set_lvls, set_persist, SET_TARGETS[SETS[setKey]][SLOTS[slot]], k=k)
            counts[set_original_idxs, 1] = len(set_artifacts)
    
    return relevance, counts

def upgrade_analyze(
    relevance: NDArray, 
    counts: NDArray[np.unsignedinteger], 
    mask: NDArray[np.bool], 
    slvls: NDArray[SLVL_DTYPE], 
    num: int | None = None, 
    threshold: int | float | None = None
) -> NDArray[np.bool]:
    scaled_relevance = np.sum(relevance * counts, axis=1)
    scaled_relevance[~mask] = -999999999
    scaled_relevance[slvls == 20] = -999999999
    
    if threshold is None:
        assert num is not None
        threshold = np.partition(scaled_relevance, -num)[-num]
        
    return scaled_relevance >= threshold

def _temp_bar(i, n):
    BAR_LENGTH = 50
    progress = i / n
    filled_length = int(progress * BAR_LENGTH)
    bar = '█' * filled_length + '░' * (BAR_LENGTH - filled_length)
    sys.stdout.write(f'\r|{bar}| {round(progress * 100, 1)}%')
    sys.stdout.flush()

def delete_rate(
    artifacts: NDArray[ARTIFACT_DTYPE], 
    slots: NDArray[np.unsignedinteger], 
    mask: NDArray[np.bool], 
    slvls: NDArray[SLVL_DTYPE], 
    sets: NDArray[np.unsignedinteger]
) -> tuple[NDArray, NDArray[np.unsignedinteger]]:
    caches = {}
    relevance = np.zeros((len(artifacts), 2), dtype=float)
    counts = np.zeros((len(artifacts), 2), dtype=int)
    # TODO: get rid of these these are temp for the progress bar
    total_num = 5 * (1 + len(SETS))
    count = 0
    
    for slot in range(5):
        count += 1
        _temp_bar(count, total_num)
        
        slot_mask = mask & (slots == slot)
        slot_original_idxs = np.flatnonzero(slot_mask)
        slot_artifacts = artifacts[slot_mask]
        slot_lvls = slvls[slot_mask]
        
        targets = multi_vectorize(ALL_TARGETS[SLOTS[slot]])
        temp = np.zeros((len(slot_artifacts), len(targets)))
        for j, target in enumerate(targets):
            cache_key = (slot, tuple(target))
            if cache_key not in caches:
                caches[cache_key] = CachePercentile(SLOTS[slot], target)
            for i, (artifact, slvl) in enumerate(zip(slot_artifacts, slot_lvls)):
                temp[i, j] = caches[cache_key].percent(artifact, slvl)
        relevance[slot_mask, 0] = np.max(temp, axis=1)
        counts[slot_mask, 0] = len(slot_artifacts)
        
        for setKey in range(len(SETS)):
            count += 1
            _temp_bar(count, total_num)
            
            set_mask = sets[slot_mask] == setKey
            if np.all(set_mask == 0):
                continue
            
            set_original_idxs = slot_original_idxs[set_mask]
            set_artifacts = slot_artifacts[set_mask]
            set_lvls = slot_lvls[set_mask]
            
            targets = multi_vectorize(SET_TARGETS[SETS[setKey]][SLOTS[slot]])
            temp = np.zeros((len(set_artifacts), len(targets)))
            for j, target in enumerate(targets):
                cache_key = (slot, tuple(target))
                if cache_key not in caches:
                    caches[cache_key] = CachePercentile(SLOTS[slot], target)
                for i, (artifact, slvl) in enumerate(zip(set_artifacts, set_lvls)):
                    temp[i, j] = caches[cache_key].percent(artifact, slvl)
            relevance[set_original_idxs, 1] = np.max(temp, axis=1)
            counts[set_original_idxs, 1] = len(set_artifacts)
            
    print() # TODO: get rid of this
            
    with open(CACHE_PATH, 'wb') as f:
        pickle.dump(helper_cache, f)
    with open('top_cache.pkl', 'wb') as f:
        pickle.dump(top_cache, f)
    return relevance, counts


def delete_analyze(
    relevance: NDArray, 
    counts: NDArray[np.unsignedinteger], 
    mask: NDArray[np.bool], 
    num: int | None = None, 
    threshold: int | float | None = None
) -> NDArray[np.bool]:
    counts[~mask] = -1
    scaled_relevance = np.max(relevance / counts, axis=1)
    #relevance = np.max(relevance, axis=1)
    
    if threshold is None:
        assert num is not None
        threshold = np.partition(scaled_relevance[mask], num)[num]
        
    return scaled_relevance <= threshold