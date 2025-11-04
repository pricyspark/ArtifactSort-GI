import numpy as np
from rank import *
import functools
import time
from numba import types
from numba.typed import Dict

CACHE_SIZE = 20000

class CachePercentile:
    def __init__(self, slot, target):
        self.slot = slot
        self.target = target
        self.target.setflags(write=False)
        self.trim_distro = [[None for _ in range(5)] for _ in range(6)]
        #self.trim_distro = [[trim_distro(i, j) for j in range(5)] for i in range(6)]
        
    @functools.lru_cache(maxsize=CACHE_SIZE)
    def helper(self, threshold):
        return artifact_percentile(self.slot, self.target, threshold, 20)
    
    def percent(self, artifact, slvl):
        if slvl < 0:
            num_upgrades = 4
        else:
            num_upgrades = 5 - slvl // 4
        
        main = find_main(artifact)
        useful_subs = find_sub(artifact * self.target, main)
        num_useful = len(useful_subs)
        if self.trim_distro[num_upgrades][num_useful] is None:
            self.trim_distro[num_upgrades][num_useful] = trim_distro(num_upgrades, num_useful)
        d, p = self.trim_distro[num_upgrades][num_useful]
        temp = np.repeat(artifact[None, :], len(d), axis=0)
        for i, sub in enumerate(useful_subs):
            temp[:, sub] += d[:, i]
        d = temp
        
        avg = 0
        scores = score(d, self.target) - 0.001
        for x, y in zip(scores, p):
            if y == 0:
                continue
            avg += 1 / self.helper(x) * y
        return avg

def distro_percentile(slot, artifact, slvl, target):
    @functools.lru_cache(maxsize=CACHE_SIZE)
    def _asdf(threshold):
        return artifact_percentile(slot, target, threshold, 20)
    
    if slvl < 0:
        num_upgrades = 4
    else:
        num_upgrades = 5 - slvl // 4
        
    d, p = adistro(artifact, num_upgrades=num_upgrades)
    avg = 0
    for x, y in zip(d, p):
        if y == 0:
            continue
        avg += 1 / _asdf(score(x, target)-0.001) * y
    return avg

def rank_percentile(artifacts, slvls, persist, targets, k=1):
    '''Estimate probability artifact is in top k for given targets, and
    sort based on p/(cost to max). If artifacts upgraded straight to
    max, this would be optimal. 
    '''
    # Format inputs
    num_artifacts = len(artifacts)
    num_targets = len(targets)
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

    # Initialize persist with artifacts
    if len(persist) == 0:
        persist['changed'] = []
        caches = [CachePercentile('flower', target) for target in targets]
        percentiles = np.zeros((num_artifacts, num_targets))
        #percentiles = np.zeros((num_targets, num_artifacts))
        for i, (artifact, slvl) in enumerate(zip(artifacts, slvls)):
            for j, target in enumerate(targets):
                percentiles[i, j] = caches[j].percent(artifact, slvl)
        persist['caches'] = caches
        persist['percentiles'] = percentiles
        persist['best'] = np.zeros(num_targets)
        persist['win'] = None
        
    # Update changed artifacts
    if len(persist['changed']) != 0:
        changed = persist['changed']
        try:
            _ = iter(changed)
        except:
            changed = [changed]
        for idx in changed:
            # (1,19) (19,num_targets)
            scores = score(artifacts[idx], targets.T).flatten()
            new_best = scores > persist['best']
            persist['best'] = np.where(new_best, scores, persist['best'])
            if persist['win'] is not None:
                for j, is_best in enumerate(new_best):
                    persist['win'][idx, j] = upgrade_percentile(artifacts[idx], slvls[idx], targets[j], persist['best'][j])
                    if not is_best:
                        continue
                    for i in range(num_artifacts):
                        persist['win'][i, j] = upgrade_percentile(artifacts[i], slvls[i], targets[j], persist['best'][j])
                
                '''
                for i, (artifact, slvl) in enumerate(zip(artifacts, slvls)):
                    for j, target in enumerate(targets):
                        win[i, j] = upgrade_percentile(artifact, slvl, target, best[j])
                '''
            
            #persist['best'] = np.maximum(persist['best'], scores)
            for j, target in enumerate(targets):
                persist['percentiles'][idx, j] = persist['caches'][j].percent(artifacts[idx], slvls[idx])
            
        persist['changed'] = []

    '''
    # If not enough artifacts, everything wins
    if num_artifacts <= k:
        #value = np.full((num_artifacts), num_trials, dtype=float)
        value = np.full((num_artifacts), 1, dtype=float)
        value /= np.where(slvls == 20, 1, MAX_REQ_EXP[slvls])
        
        return value
    '''
    percentiles, best, win = persist['percentiles'], persist['best'], persist['win']
    
    if np.all(slvls[np.argmax(percentiles, axis=0)] == 20):
        if win is None:
            persist['win'] = np.zeros((num_artifacts, num_targets))
            win = persist['win']
            for i, (artifact, slvl) in enumerate(zip(artifacts, slvls)):
                for j, target in enumerate(targets):
                    win[i, j] = upgrade_percentile(artifact, slvl, target, best[j])
        #return np.argmax(np.where(slvls[:, None] == 20, 0, percentiles)) // num_targets        
        qwer = np.argmax(np.where(slvls == 20, 0, np.sum(win, axis=1)))
        return qwer
        #return np.argmax(np.where(slvls == 20, 0, np.sum(win, axis=1)))
        #return np.argmax(np.where(slvls[:, None] == 20, 0, win)) // num_targets
    else:
        return np.argmax(np.where(slvls[:, None] == 20, 0, percentiles)) // num_targets

def simulate_delete(artifacts, slvls, targets, fun):
    num_artifacts = len(artifacts)
    num_targets = len(targets)
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
    
    original_artifacts = artifacts.copy()
    smart_upgrade_until_max(artifacts, slvls)
    
    if type(targets) == dict or (type(targets) == np.ndarray and targets.ndim == 1):
        scores = score(artifacts, targets)
        goal = np.argmax(scores)
        goal_scores = scores[goal]
    else:
        maybe = {}
        qwer = [set() for _ in range(num_targets)]
        goal = []
        goal_scores = np.zeros(len(targets), dtype=float)
        scores = score(artifacts, targets.T) # (N,D)
        goal_scores = np.max(scores, axis=0)  # (D,)
        for i, target in enumerate(targets):
            asdf = np.where(scores[:, i] >= goal_scores[i] * 1)[0]
            for _ in asdf:
                if _ in maybe:
                    maybe[_].add(i)
                else:
                    maybe[_] = set([i])
                qwer[i].add(_)
            goal.append(asdf)
        
    artifacts[:] = original_artifacts.copy()
    
    '''
    base_trials = 500
    rng = np.random.default_rng(42)
    
    maxed = np.zeros((num_artifacts, base_trials, 19), dtype=np.uint8)   # (N,T,19)
    for i in range(num_artifacts):
        maxed[i], _ = sample_upgrade(artifacts[i], base_trials, slvl=slvls[i], rng=rng)
    scores = score(maxed, targets.T)
    cutoff = scores.max(axis=0)
    winners = winner_prob(scores, cutoff, 1)
    p = np.mean(winners, axis=1)
    total_p = 1 - np.prod(1 - p, axis=1)
    for i, _ in enumerate(np.argsort(total_p)):
        if _ in maybe:
            for t in maybe[_]:
                if len(qwer[t]) == 1:
                    return i
                qwer[t].remove(_)
    return 500
    '''
    caches = [CachePercentile('flower', target) for target in targets]
    percentiles = np.zeros((num_artifacts, num_targets))
    #percentiles = np.zeros((num_targets, num_artifacts))
    for i, (artifact, slvl) in enumerate(zip(artifacts, slvls)):
        for j, target in enumerate(targets):
            percentiles[i, j] = caches[j].percent(artifact, slvl)
            
    levels = {0: 0, 4: 0, 8: 0, 12: 0, 16: 0, 20: 0}
    relevance = np.max(percentiles, axis=1) # (N,)
    for i, _ in enumerate(np.argsort(relevance)):
        if slvls[_] < 0:
            levels[0] += 1
        else:
            levels[slvls[_]] += 1
        if _ in maybe:
            for t in maybe[_]:
                if len(qwer[t]) == 1:
                    print(levels)
                    return i
                qwer[t].remove(_)
    return 500

def rank_smart(artifacts, slvls, persist, targets, k=1, base_trials=500, rng=None, seed=None):
    '''Estimate probability artifact is in top k for given targets, and
    sort based on p/(cost to max). If artifacts upgraded straight to
    max, this would be optimal. 
    '''
    # Format inputs
    num_artifacts = len(artifacts)
    num_targets = len(targets)
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

    # Prepare RNG
    if rng is None:
        rng = np.random.default_rng(seed)
    
    # Initialize persist with artifacts
    if len(persist) == 0:
        persist['changed'] = []

        maxed = np.zeros((num_artifacts, base_trials, 19), dtype=np.uint8)   # (N,T,19)
        for i in range(num_artifacts):
            maxed[i], _ = sample_upgrade(artifacts[i], base_trials, slvl=slvls[i], rng=rng)
        persist['maxed'] = maxed
        persist['targets'] = None
        persist['best'] = np.zeros(num_targets)
        persist['win'] = None
        
        persist['epsilon'] = np.sqrt(2 * np.log((num_artifacts - 1) / 0.01) / base_trials)
        
    num_trials = persist['maxed'].shape[1]
    
    # Score artifacts if needed
    if not np.array_equal(persist['targets'], targets):
        persist['targets'] = targets
        persist['scores'] = score(persist['maxed'], targets.T)

    # Update changed artifacts
    if len(persist['changed']) != 0:
        changed = persist['changed']
        try:
            _ = iter(changed)
        except:
            changed = [changed]
        for idx in changed:
            persist['maxed'][idx], _ = sample_upgrade(artifacts[idx], num_trials, slvl=slvls[idx], rng=rng)
            persist['scores'][idx] = score(persist['maxed'][idx], targets.T)
            
            asdf = score(artifacts[idx], targets.T).flatten()
            new_best = asdf > persist['best']
            persist['best'] = np.where(new_best, asdf, persist['best'])
            if persist['win'] is not None:
                for j, is_best in enumerate(new_best):
                    persist['win'][idx, j] = upgrade_percentile(artifacts[idx], slvls[idx], targets[j], persist['best'][j])
                    if not is_best:
                        continue
                    for i in range(num_artifacts):
                        persist['win'][i, j] = upgrade_percentile(artifacts[i], slvls[i], targets[j], persist['best'][j])
            
        persist['changed'] = []

    # If not enough artifacts, everything wins
    if num_artifacts <= k:
        #value = np.full((num_artifacts), num_trials, dtype=float)
        value = np.full((num_artifacts), 1, dtype=float)
        value /= np.where(slvls == 20, 1, MAX_REQ_EXP[slvls])
        
        return value
    
    # ------------------------------------------------------------------
    # START COMPUTATION
    # ------------------------------------------------------------------

    scores, best, win, epsilon = persist['scores'], persist['best'], persist['win'], persist['epsilon']
    
    
    # Calculate winning score cutoffs
    if k == 1:
        cutoff = scores.max(axis=0)                             # (T,U)
    else:
        cutoff = np.partition(scores, -k, axis=0)[-k]           # (T,U)

    # Calculate winning probabilities
    winners = winner_prob(scores, cutoff, k)                # (N,T,U)
    p = np.mean(winners, axis=1)   # (N,U)

    if np.all(slvls[np.argmax(p, axis=0)] == 20):
        if win is None:
            persist['win'] = np.zeros((num_artifacts, num_targets))
            win = persist['win']
            for i, (artifact, slvl) in enumerate(zip(artifacts, slvls)):
                for j, target in enumerate(targets):
                    win[i, j] = upgrade_percentile(artifact, slvl, target, best[j])
                    
        qwer = np.argmax(np.where(slvls == 20, 0, np.sum(win, axis=1)))
        return qwer
    
    rival, top = np.partition(p, -2, axis=0)[-2:]
    r = top / (top + rival)
    t = 0.95
    asdf = 2 * np.log(1 - t) / (-r * (1 - (1 / 2 * r)))
    chosen = rival = None
    if k == 1:
        #temp = np.argpartition(p, (-3, -2, -1), axis=0)    # (N,U)
        asdf, rival, chosen = np.argpartition(p, (-3, -2, -1), axis=0)[-3:]           # (2,U)
        if np.all(slvls[chosen] == 20):
            print('max')
            chosen = p[rival]
            rival = p[asdf]       
        else:
            chosen = p[chosen]
            rival = p[rival]         
    else:
        temp = np.partition(p, (-k-1, -k), axis=0)           # (2,U)
        rival = temp[-k-1]
        chosen = temp[-k]
        
        
    if np.all(chosen - rival < epsilon) and num_trials < 10000:
        # TODO: add memory limit in case of infinite recursion
        persist.clear() # Inefficiently deletes current artifacts instead of appending new trials
        print('doubling trials to', num_trials * 2)
        return rank_smart(artifacts, slvls, persist, targets, k, num_trials * 2, rng)
    
    # Enough trials, continue
    #total_p = p.sum(axis=1)   # (N,)
    total_p = 1 - np.prod(1 - p, axis=1) # (N,)
    
    # Dollarize probabilities
    value = total_p / np.maximum(1, MAX_REQ_EXP[slvls])
    
    '''
    value[slvls == 20] = -99999999
    choose = np.argmax(value)
    print('choose', choose)
    print(p[choose])
    '''
    
    return value

if __name__ == '__main__':
    '''
    NUM_SEEDS = 10
    NUM_ITERATIONS = 1
    targets = (
        {'hp_': 6, 'hp': 2, 'crit_': 8},
        {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10},
        {'hp_': 6, 'hp': 2, 'crit_': 8, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'enerRech_': 10},
        {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 16},

        {'atk_': 6, 'atk': 2, 'crit_': 8},
        {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
        {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'enerRech_': 10},
        {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 16},

        {'def_': 6, 'def': 2, 'crit_': 8},
        {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10},
        {'def_': 6, 'def': 2, 'crit_': 8, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'enerRech_': 10},
        {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 16}
    )
    
    totals = np.zeros((NUM_SEEDS, NUM_ITERATIONS))
    
    start = time.perf_counter()
    for i in range(NUM_SEEDS):
        for j in range(NUM_ITERATIONS):
            artifacts, slvls = generate('flower', size=200, seed=i)
            totals[i, j] = (simulate_exp(artifacts, slvls, targets, rank_value))
    end = time.perf_counter()
            
    print('done')
    print(totals)
    row_mean = np.mean(totals, axis=1)
    row_std = np.std(totals, axis=1)
    print(row_mean)
    print(row_std)
    print(row_std / row_mean / np.sqrt(NUM_ITERATIONS))
    print('mean', np.mean(totals))
    print('std', np.linalg.norm(row_std) / NUM_SEEDS)
    print('ratio', np.linalg.norm(row_std) / NUM_SEEDS / np.mean(totals))
    print(end - start)
    '''
    '''
    target = vectorize({'hp_': 6, 'hp': 2, 'crit_': 8})
    start = time.perf_counter()
    for _ in range(10):
        artifact, slvl = generate('flower', seed=_+10)
        artifact = artifact[0]
        slvl = slvl[0]
        threshold = score(artifact, target)
        print(slvl, distro_percentile('flower', artifact, slvl, target))
    end = time.perf_counter()
    print(end - start)
    print()
    target = vectorize({'hp_': 6, 'hp': 2, 'crit_': 8})
    start = time.perf_counter()
    qwer = CachePercentile('flower', target)
    for _ in range(10):
        artifact, slvl = generate('flower', seed=_+10)
        artifact = artifact[0]
        slvl = slvl[0]
        threshold = score(artifact, target)
        print(slvl, qwer.percent(artifact, slvl))
    end = time.perf_counter()
    print(end - start)
    '''
    targets = (
        {'hp_': 6, 'hp': 2, 'crit_': 8},
        {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10},
        {'hp_': 6, 'hp': 2, 'crit_': 8, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'enerRech_': 10},
        {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 16},

        {'atk_': 6, 'atk': 2, 'crit_': 8},
        {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
        {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'enerRech_': 10},
        {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 16},

        {'def_': 6, 'def': 2, 'crit_': 8},
        {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10},
        {'def_': 6, 'def': 2, 'crit_': 8, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'enerRech_': 10},
        {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 16}
    )
    asdf = []
    for _ in range(10):
        artifacts = []
        slvls = []
        base = 10
        a, s = generate('flower', size=base * 32, seed=_)
        artifacts.append(a)
        slvls.append(s)
        
        a, s = generate('flower', size=base * 16, seed=_, lvls=4)
        artifacts.append(a)
        slvls.append(s)
        
        a, s = generate('flower', size=base * 8, seed=_, lvls=8)
        artifacts.append(a)
        slvls.append(s)
        
        a, s = generate('flower', size=base * 4, seed=_, lvls=12)
        artifacts.append(a)
        slvls.append(s)
        
        a, s = generate('flower', size=base * 2, seed=_, lvls=16)
        artifacts.append(a)
        slvls.append(s)
        
        a, s = generate('flower', size=base, seed=_, lvls=20)
        artifacts.append(a)
        slvls.append(s)
        
        artifacts = np.concatenate(artifacts, axis=0)
        slvls = np.concatenate(slvls)
        
        start = time.perf_counter()
        asdf.append(simulate_delete(artifacts, slvls, targets, None))
        #asdf.append(simulate_exp(artifacts, slvls, targets, rank_smart))
        end = time.perf_counter()
        print(end - start)
        break
    print(np.mean(asdf))
    print(asdf)
    print(random_percentile_helper.cache_info())
    '''
    artifacts, slvls = generate('flower', size=1, seed=3)
    target = vectorize({'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7})
    print(artifact_percentile('flower', target, score(artifacts[0], target), 0))
    print_artifact(artifacts[0])
    
    artifacts, slvls = generate('flower', size=1, seed=4)
    target = vectorize({'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7})
    print(artifact_percentile('flower', target, score(artifacts[0], target), 0))
    print_artifact(artifacts[0])
    '''
    '''
    0.8426271369971801
    3.0315445739979623
    3.090717732993653
    12.071330200997181
    0.48605442499683704
    3.034152496009483
    3.4467439479922177
    '''