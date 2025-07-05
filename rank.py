import numpy as np
from analyze import *
import time

def rank(artifacts, lvls, targets, sets=None, k=1, num_trials=30, rng=None, seed=None):
    # TODO: implement sets
    
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
    
    distributions, probs = distro(artifacts, lvls=lvls)
    relevance = np.zeros(num_artifacts)
    for _ in range(num_trials):
        maxed = np.zeros((num_artifacts, 19), dtype=np.uint8)
        for i in range(num_artifacts):
            maxed[i] = rng.choice(distributions[i], p=probs[i])
        if type(targets) == dict or (type(targets) == np.ndarray and targets.ndim == 1):
            final_scores = score(maxed, targets)
            final_scores[lvls == 20] = 0
            best = np.argpartition(final_scores, -k)[-k:]
            relevance[best] += 1
        else:
            for target in targets:
                final_scores = score(maxed, target)
                final_scores[lvls == 20] = 0
                best = np.argpartition(final_scores, -k)[-k:]
                relevance[best] += 1
        
    #return relevance
    return np.argmax(relevance)

def rank_value(artifacts, lvls, persist, targets, change=True, k=1, num_trials=1000, rng=None, seed=None):
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
        while len(persist) < 2:
            persist.append(None)
        persist[0] = -1
        distributions, probs = distro_accurate(artifacts, lvls)
        maxed = np.zeros((num_artifacts, num_trials, 19), dtype=np.uint8)
        for i in range(num_artifacts):
            maxed[i] = rng.choice(distributions[i], p=probs[i], size=num_trials)
        persist[1] = maxed
    elif change:
        changed = persist[0]
        distributions, probs = distro_accurate(artifacts[changed], lvls[changed])
        persist[1][changed] = rng.choice(distributions, p=probs, size=num_trials)
        
    changed, maxed = persist
    relevance = np.zeros(num_artifacts, dtype=float)
    
    for i in range(num_trials):
        #maxed = np.zeros((num_artifacts, 19), dtype=np.uint8)
        #for i in range(num_artifacts):
        #    maxed[i] = rng.choice(distributions[i], p=probs[i])
        if type(targets) == dict or (type(targets) == np.ndarray and targets.ndim == 1):
            final_scores = score(maxed[:, i], targets)
            final_scores[lvls == 20] = 0
            maximum = np.max(final_scores)
            best = np.where(final_scores == maximum)[0]
            relevance[best] += 1 / len(best)
        else:
            for target in targets:
                final_scores = score(maxed[:, i], target)
                final_scores[lvls == 20] = 0
                maximum = np.max(final_scores)
                best = np.where(final_scores == maximum)[0]
                relevance[best] += 1 / len(best)
                # each target is weighted equally. Don't divide by the
                # number of targets, or else having more targets would
                # make each target less valuable, which isn't the case.
                
    for i in range(num_artifacts):
        if lvls[i] != 20:
            relevance[i] /= MAX_REQ_EXP[lvls[i]]
            #raise ValueError
        
    #return relevance
    #print_artifact(artifacts[np.argmax(relevance)])
    persist[0] = np.argmax(relevance)
    return relevance

def rank_estimate(artifacts, lvls, persist, targets, change=True, k=1, num_trials=10, rng=None, seed=None):
    # 
    print('start')
    print(time.time())
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
        distributions, probs = distro_accurate(artifacts, lvls)
        maxed = np.zeros((num_artifacts, num_trials, 19), dtype=np.uint8)
        for i in range(num_artifacts):
            maxed[i] = rng.choice(distributions[i], p=probs[i], size=num_trials)
        persist[1] = maxed
        
        single_maxed = []
        for i in range(num_artifacts):
            single_maxed.append([None, None])
            if lvls[i] == 20:
                continue
            
            current_distribution, current_probs = distro_accurate(artifacts[i], num_upgrades=1)
            single_maxed[-1][0] = []
            single_maxed[-1][1] = current_probs
            for j, upgrade in enumerate(current_distribution):
                potential_distribution, potential_probs = distro_accurate(upgrade, next_lvl(lvls[i]))
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
        distributions, probs = distro_accurate(artifacts[changed], lvls[changed])
        persist[1][changed] = rng.choice(distributions, p=probs, size=num_trials)
        if lvls[changed] != 20:
            current_distribution, current_probs = distro_accurate(artifacts[changed], num_upgrades=1)
            persist[2][changed][0] = []
            persist[2][changed][1] = current_probs
            for j, upgrade in enumerate(current_distribution):
                potential_distribution, potential_probs = distro_accurate(upgrade, next_lvl(lvls[changed]))
                persist[2][changed][0].append(rng.choice(potential_distribution, p=potential_probs, size=num_trials))
    # TODO: save scores instead of artifacts. Save a threshold score.
    # When computing potential new scores, count how many are above the
    # threshold. This is the relevance score. Don't recompute scores and
    # count. Compute scores once and get a threshold.
    
    print('setup')
    print(time.time())
    changed, maxed, single_maxed = persist
    relevance_std = np.zeros(num_artifacts, dtype=float)
    original_maxed = maxed.copy()
    for i in range(num_artifacts):
        if lvls[i] == 20:
            continue
        
        upgrades, current_probs = single_maxed[i]
        relevance = np.zeros(len(upgrades), dtype=float)
        for j, upgrade in enumerate(upgrades):
            maxed[i] = upgrade
            for k in range(num_trials):
                if type(targets) == dict or (type(targets) == np.ndarray and targets.ndim == 1):
                    final_scores = score(maxed[:, k], targets)
                    final_scores[lvls == 20] = 0
                    maximum = np.max(final_scores)
                    if final_scores[i] == maximum:
                        relevance[j] += 1 / np.count_nonzero(final_scores == maximum)
                else:
                    for target in targets:
                        final_scores = score(maxed[:, k], target)
                        final_scores[lvls == 20] = 0
                        maximum = np.max(final_scores)
                        if final_scores[i] == maximum:
                            relevance[j] += 1 / np.count_nonzero(final_scores == maximum)
                    
        mean = np.dot(relevance, current_probs)
        if mean >= 0.5 * num_trials:
            relevance_std[i] = 10000000000
            #break
        else:
            var = np.dot(current_probs, (relevance - mean)**2)
            relevance_std[i] = np.sqrt(var)
        
        maxed[i] = original_maxed[i]
        
    for i in range(num_artifacts):
        if lvls[i] != 20:
            relevance_std[i] /= MAX_REQ_EXP[lvls[i]]
            
    #print(relevance_std)
    persist[0] = np.argmax(relevance_std)
    
    #for i in relevance_std:
    #    print(i)
    print('done')
    print(time.time())
    
    return relevance_std

def rank_myopic(artifacts, lvls, distros, targets, k=1, num_trials=100, rng=None, seed=None):
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
        
    '''
    Psuedo:
    Store num_trials x num_artifacts x 19 array of the maxed artifacts
    Compute current relevance from that
    Compute current entropy from current relevance
    
    For each artifact
        Store current maxed artifacts for selected artifact
        For each possible upgrade
            Compute num_trials new maxed artifacts
            Replace maxed artifacts with new ones for selected artifact
            Compute new relevance
            Compute new entropy
            
        Compute expected new entropy
        Put back original maxed artifacts for selected artifact
        
    Return artifact with maximum entropy reduction per cost
    '''
    current_relevance = np.zeros(num_artifacts, dtype=float)
    
    distributions, probs = distros
    maxed = np.zeros((num_artifacts, num_trials, 19), dtype=np.uint8)
    for i in range(num_artifacts):
        maxed[i] = rng.choice(distributions[i], p=probs[i], size=num_trials)
    original_maxed = maxed.copy()
    for i in range(num_trials):
        #maxed = np.zeros((num_artifacts, 19), dtype=np.uint8)
        #for i in range(num_artifacts):
        #    maxed[i] = rng.choice(distributions[i], p=probs[i])
        if type(targets) == dict or (type(targets) == np.ndarray and targets.ndim == 1):
            final_scores = score(maxed[:, i], targets)
            final_scores[lvls == 20] = 0
            maximum = np.max(final_scores)
            best = np.where(final_scores == maximum)[0]
            current_relevance[best] += 1 / len(best)
            #current_relevance[best] += 1
        else:
            for target in targets:
                final_scores = score(maxed[:, i], target)
                final_scores[lvls == 20] = 0
                maximum = np.max(final_scores)
                best = np.where(final_scores == maximum)[0]
                current_relevance[best] += 1 / len(best)
                #best = np.argpartition(final_scores, -k)[-k:]
                #current_relevance[best] += 1
    current_entropy = entropy(current_relevance)
    if current_entropy == 0:
        return np.argmax(current_relevance)
    entropy_reduction_value = np.zeros(num_artifacts, dtype=float) - 999999
    
    # TODO: upgrade everyone one at the same time, instead of interating
    # through each artifact and upgrading it one by one
    for i in range(num_artifacts):
        if lvls[i] == 20:
            continue
        new_lvl = next_lvl(lvls[i])
        old_maxed = maxed[i].copy()
        expected_entropy = 0
        #new_relevance = np.zeros(num_artifacts, dtype=int)
        counter = -1
        for upgrade, prob in zip(*distro(artifacts[i], num_upgrades=1)):
            new_relevance = np.zeros(num_artifacts, dtype=float)
            counter += 1
            if prob == 0:
                continue
            new_maxed, new_probs = distro(upgrade, lvls=new_lvl)
            maxed[i] = rng.choice(new_maxed, size=num_trials, p=new_probs)
            for j in range(num_trials):
                if type(targets) == dict or (type(targets) == np.ndarray and targets.ndim == 1):
                    final_scores = score(maxed[:, j], targets)
                    final_scores[lvls == 20] = 0
                    #best = np.argpartition(final_scores, -k)[-k:]
                    maximum = np.max(final_scores)
                    best = np.where(final_scores == maximum)[0]
                    new_relevance[best] += 1 / len(best)
                    #new_relevance[best] += 1
                else:
                    for target in targets:
                        final_scores = score(maxed[:, j], target)
                        final_scores[lvls == 20] = 0
                        maximum = np.max(final_scores)
                        best = np.where(final_scores == maximum)[0]
                        new_relevance[best] += 1 / len(best)
                        #best = np.argpartition(final_scores, -k)[-k:]
                        #new_relevance[best] += 1
                        
            #print(counter)
            #print(prob)
            #print(new_relevance)
            new_entropy = entropy(new_relevance)
            expected_entropy += prob * new_entropy
        maxed[i] = old_maxed
        entropy_reduction_value[i] = (current_entropy - expected_entropy) / UPGRADE_REQ_EXP[lvls[i]]
    super_new_maxed = maxed.copy()
    asdf = np.array_equal(original_maxed, super_new_maxed)
    output = np.argmax(entropy_reduction_value)
    if entropy_reduction_value[output] == 0:
        print(current_relevance)
        for i in range(num_artifacts):
            if lvls[i] != 20:
                current_relevance[i] /= MAX_REQ_EXP[lvls[i]]
        output = np.argmax(current_relevance)
    print('best:', output)
    print(entropy_reduction_value[output])
    print(lvls[output])
    print_artifact(artifacts[output])
    print()
    return output
        
        
def rank_marginal_relevance(artifacts, lvls, targets, k=1, num_trials=100, rng=None, seed=None):
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
        
    current_relevance = np.zeros(num_artifacts, dtype=int)
    
    distributions, probs = distro(artifacts, lvls=lvls)
    maxed = np.zeros((num_artifacts, num_trials, 19), dtype=np.uint8)
    for i in range(num_artifacts):
        maxed[i] = rng.choice(distributions[i], p=probs[i], size=num_trials)
    
    for i in range(num_trials):
        #maxed = np.zeros((num_artifacts, 19), dtype=np.uint8)
        #for i in range(num_artifacts):
        #    maxed[i] = rng.choice(distributions[i], p=probs[i])
        if type(targets) == dict or (type(targets) == np.ndarray and targets.ndim == 1):
            final_scores = score(maxed[:, i], targets)
            final_scores[lvls == 20] = 0
            best = np.argpartition(final_scores, -k)[-k:]
            current_relevance[best] += 1
        else:
            for target in targets:
                final_scores = score(maxed[:, i], target)
                final_scores[lvls == 20] = 0
                best = np.argpartition(final_scores, -k)[-k:]
                current_relevance[best] += 1
    current_entropy = entropy(current_relevance)
    entropy_reduction_value = np.zeros(num_artifacts, dtype=float) - 999999
    
    # TODO: upgrade everyone one at the same time, instead of interating
    # through each artifact and upgrading it one by one
    for i in range(num_artifacts):
        if lvls[i] == 20:
            continue
        new_lvl = next_lvl(lvls[i])
        old_maxed = maxed[i].copy()
        expected_entropy = 0
        new_relevance = np.zeros(num_artifacts, dtype=int)
        for upgrade, prob in zip(*distro(artifacts[i], num_upgrades=1)):
            if prob == 0:
                continue
            new_maxed, new_probs = distro(upgrade, lvls=new_lvl)
            maxed[i] = rng.choice(new_maxed, size=num_trials, p=new_probs)
            for j in range(num_trials):
                if type(targets) == dict or (type(targets) == np.ndarray and targets.ndim == 1):
                    final_scores = score(maxed[:, j], targets)
                    final_scores[lvls == 20] = 0
                    best = np.argpartition(final_scores, -k)[-k:]
                    new_relevance[best] += 1
                else:
                    for target in targets:
                        final_scores = score(maxed[:, j], target)
                        final_scores[lvls == 20] = 0
                        best = np.argpartition(final_scores, -k)[-k:]
                        new_relevance[best] += 1
                        
            new_entropy = entropy(new_relevance)
            expected_entropy += prob * new_entropy
        maxed[i] = old_maxed
        entropy_reduction_value[i] = (current_entropy - expected_entropy) / UPGRADE_REQ_EXP[lvls[i]]
    
    output = np.argmax(entropy_reduction_value)
    print(entropy_reduction_value[output])
    print(lvls[output])
    print_artifact(artifacts[output])
    print()
    return np.argmax(entropy_reduction_value)

if __name__ == '__main__':
    start = time.time()
    filename = 'artifacts/genshinData_GOOD_2025_07_03_02_41.json'
    artifacts, slots, rarities, lvls, sets = load(filename)
    relevant = rate(artifacts, slots, rarities, lvls, sets, rank_estimate, num=100)
    
    count = 0
    '''
    for idx, (relevance, artifact, slot, lvl, artifact_set) in enumerate(zip(relevant, artifacts, slots, lvls, sets)):
        if not relevance:
            count += 1
            print(idx)
            print(SLOTS[slot])
            print(SETS[artifact_set])
            print('lvl:', lvl)
            print_artifact(artifact)
            print()
    print(count)
    '''
    
    visualize(relevant, artifacts, slots, sets)
    end = time.time()
    print(end - start)