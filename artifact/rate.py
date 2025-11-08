import numpy as np
import sys
import pickle
from functools import lru_cache
from .constants import *
from .targets import *
from .core import *
from .distributions import *
from .probs import *
from .percentiles import *
from .rank import *

try:
    with open(CACHE_PATH, 'rb') as f:
        helper_cache = pickle.load(f)
except:
    helper_cache = {}

class CachePercentile:
    distros = [[trim_distro(j, i) for i in range(5)] for j in range(6)]
    def __init__(self, slot, target):
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
        self.max_threshold = 999999
        
    # Double caching is memoory inefficient, but lru_cache is still
    # significantly faster.
    # TODO: make this more elegant
    @lru_cache(maxsize=CACHE_SIZE)
    def helper(self, threshold):
        target_key = (self.slot, threshold, np.ascontiguousarray(self.target).view(np.uint16).tobytes())
        if target_key in helper_cache:
            return helper_cache[target_key]
        asdf = iterative_artifact_percentile(
            self.useful_target, 
            threshold, 
            20, 
            base=(
                self.mains, 
                self.subs, 
                self.probs, 
                self.base_scores, 
                self.num_useful, 
                self.num_useless, 
                self.weights_all))
        helper_cache[target_key] = asdf
        return asdf
    
    def percent(self, artifact, slvl):
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
        
        scores = score(d, self.target).astype(int) - 1
        rarities = np.zeros(len(scores))
        for i, x in enumerate(scores):
            rarities[i] = self.helper(x)
        return np.sum(p / rarities)

def rate(artifacts, slots, mask, slvls, sets, ranker, k=1):
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

def upgrade_analyze(relevance, counts, mask, slvls, num=None, threshold=None):
    scaled_relevance = np.sum(relevance * counts, axis=1)
    scaled_relevance[~mask] = -999999999
    scaled_relevance[slvls == 20] = -999999999
    
    if threshold is None:
        threshold = np.partition(scaled_relevance, -num)[-num]
        
    return scaled_relevance >= threshold

def _temp_bar(i, n):
    BAR_LENGTH = 50
    progress = i / n
    filled_length = int(progress * BAR_LENGTH)
    bar = '█' * filled_length + '░' * (BAR_LENGTH - filled_length)
    sys.stdout.write(f'\r|{bar}| {round(progress * 100, 1)}%')
    sys.stdout.flush()

def delete_rate(artifacts, slots, mask, slvls, sets):
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
        
        targets = vectorize(ALL_TARGETS[SLOTS[slot]])
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
            
            targets = vectorize(SET_TARGETS[SETS[setKey]][SLOTS[slot]])
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
    return relevance, counts

def delete_analyze(relevance, counts, mask, num=None, threshold=None):
    counts[~mask] = -1
    scaled_relevance = np.max(relevance / counts, axis=1)
    #relevance = np.max(relevance, axis=1)
    
    if threshold is None:
        threshold = np.partition(scaled_relevance[mask], num)[num]
        
    return scaled_relevance <= threshold