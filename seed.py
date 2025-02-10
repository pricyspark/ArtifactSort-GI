import random
import math
import numpy as np
import copy
import json
import functools
from memory_profiler import profile
from numba import jit
from numba.experimental import jitclass
from collections.abc import Iterable
from fast import FastArtifact
import os
from sortedcontainers import SortedKeyList
import time
from multiprocessing import shared_memory, Process, Queue

''' 
artifact lookup: [num_artifacts x 6 x 19]
scores lookup [num_artifacts x 6 x num_scores]

'''
def worker(q, x, shm_scores_name, scores_shape, scores_dtype, shm_finals_name, finals_shape, finals_dtype):
    t0 = time.time()
    existing_shm_scores = shared_memory.SharedMemory(name=shm_scores_name)
    existing_shm_finals = shared_memory.SharedMemory(name=shm_finals_name)

    shm_scores_array = np.ndarray(scores_shape, dtype=scores_dtype, buffer=existing_shm_scores.buf)
    shm_finals_array = np.ndarray(finals_shape, dtype=finals_dtype, buffer=existing_shm_finals.buf)

    y = simulate(x, shm_scores_array, shm_finals_array).reshape((-1, 1))
    row = np.hstack((x, y))

    q.put(row)
    t1 = time.time()
    print(t1 - t0)

def aggregator(q, final_array, num_workers):
    count = 0
    while count < num_workers:
        new_row = q.get()
        final_array = np.vstack((final_array, new_row))
        count += 1
    # final_array now has all rows appended
    return final_array

def simulate(X, scores, finals):
    y = np.full(X.shape[0], -1, dtype=float)
    num_inventories, num_artifacts = finals.shape
    
    for coef_idx, coefs in enumerate(X):
        total = 0
        for inventory in range(num_inventories):
            max_score = 0
            exp = 10080 * num_artifacts / 3
            lvls = np.zeros(num_artifacts, dtype=int)
            sorted_artifacts = SortedKeyList(range(num_artifacts), key=lambda idx: -coefs @ scores[inventory, idx, lvls[idx] // 4, :])
            while sorted_artifacts:
                best = sorted_artifacts.pop(0)
                req_exp = FastArtifact.static_upgrade_req_exp(lvls[best])
                for artifact in reversed(sorted_artifacts[1:]):
                    if exp >= req_exp:
                        break

                    exp += FastArtifact.static_salvage_exp(lvls[artifact]) / 3
                    sorted_artifacts.pop(-1)
                
                if exp < req_exp:
                    break

                exp -= req_exp
                lvls[best] += 4

                if lvls[best] == 20:
                    max_score = max(max_score, finals[inventory, best])
                else:
                    sorted_artifacts.add(best)

            total += max_score
        y[coef_idx] = total / num_inventories
        
    return y

class SeededInventory:
    def __init__(self, targets, metrics, num_inventories, num_artifacts, seed, set, lvl, slot, source='domain', populate=True):
        self.num_inventories = num_inventories
        self.num_artifacts = num_artifacts
        self.seed = seed
        self.rng = np.random.default_rng(seed)
        if not populate:
            return
        
        num_metrics = metrics(None, None)

        self.artifacts= np.full((num_inventories, num_artifacts, 5, 19), -1, dtype=float)
        self.scores = np.full((num_inventories, num_artifacts, 5, num_metrics), -1, dtype=float)
        self.finals = np.full((num_inventories, num_artifacts), -1, dtype=float)
        for inventory_idx in range(num_inventories):
            for artifact_idx in range(num_artifacts):
                artifact = FastArtifact.generate(set, lvl, slot, None, source, rng=self.rng)
                self.artifacts[inventory_idx, artifact_idx, 0, :] = artifact.stats

                scores = metrics(artifact, targets)
                for i in range(num_metrics):
                    self.scores[inventory_idx, artifact_idx, 0, i] = scores[i]

                for i in range(1, 5):
                    artifact.random_upgrade(rng=self.rng)
                    self.artifacts[inventory_idx, artifact_idx, i, :] = artifact.stats

                    scores = metrics(artifact, targets)
                    for j in range(num_metrics):
                        self.scores[inventory_idx, artifact_idx, i, j] = scores[j]

                artifact.random_upgrade(rng=self.rng)
                self.finals[inventory_idx, artifact_idx] = artifact.score(targets)

    def __eq__(self, other):
        return (np.array_equal(self.artifacts, other.artifacts) and
                np.array_equal(self.scores, other.scores) and
                np.array_equal(self.finals, other.finals))
    
    def __ne__(self, other):
        return self != other

    @staticmethod
    def load(targets, metrics, num_inventories, num_artifacts, seed, set, lvl, slot):
        output = SeededInventory(targets, metrics, num_inventories, num_artifacts, seed, set, lvl, slot, populate=False)
        output.artifacts = np.load(f'seeded/{num_inventories}_{num_artifacts}_{seed}_artifacts.npy')
        output.scores = np.load(f'seeded/{num_inventories}_{num_artifacts}_{seed}_scores.npy')
        output.finals = np.load(f'seeded/{num_inventories}_{num_artifacts}_{seed}_finals.npy')
        return output
    
    def save(self):
        np.save(f'seeded/{self.num_inventories}_{self.num_artifacts}_{self.seed}_artifacts', self.artifacts)
        np.save(f'seeded/{self.num_inventories}_{self.num_artifacts}_{self.seed}_scores', self.scores)
        np.save(f'seeded/{self.num_inventories}_{self.num_artifacts}_{self.seed}_finals', self.finals)

    def upper_bound(self):
        sum = 0
        for inventory in self.finals:
            sum += np.max(inventory)
        
        return sum / self.num_inventories

    def simulate(self, X):
        return simulate(X, self.scores, self.finals)

    def simulate_multi(self, X, num_workers):
        shm_scores = shared_memory.SharedMemory(create=True, size=self.scores.nbytes)
        shm_finals = shared_memory.SharedMemory(create=True, size=self.finals.nbytes)

        shm_scores_array = np.ndarray(self.scores.shape, dtype=self.scores.dtype, buffer=shm_scores.buf)
        shm_finals_array = np.ndarray(self.finals.shape, dtype=self.finals.dtype, buffer=shm_finals.buf)

        shm_scores_array[:] = self.scores[:]
        shm_finals_array[:] = self.finals[:]

        xs = np.array_split(X, num_workers)

        q = Queue()
        processes = []
        for i in range(num_workers):
            p = Process(target=worker, args=(q, xs[i], shm_scores.name, self.scores.shape, self.scores.dtype, shm_finals.name, self.finals.shape, self.finals.dtype))
            p.start()
            processes.append(p)

        for p in processes:
            p.join()

        results = np.zeros((0, 3), dtype=float)
        results = aggregator(q, results, 4)
        print(results)

        shm_scores.close()
        shm_finals.close()

        shm_scores.unlink()
        shm_finals.unlink()

if __name__ == '__main__':

    def metrics(artifact, targets):
        if artifact is None or targets is None:
            return 2

        num_upgrades = 5 - (artifact.lvl // 4)
        distro = FastArtifact.upgrade_distro(num_upgrades, artifact.stats)
        return (FastArtifact.score_second_moment(distro, targets), 
                FastArtifact.score_std_dev(distro, targets))

    targets = FastArtifact.vectorize_targets({'atk_': 1, 'atk': 1/3, 'crit_': 4/3})

    print('initializing')
    t0 = time.time()
    seeded = SeededInventory.load(targets, metrics, 1000, 200, 0, None, 0, 'flower')
    t1 = time.time()
    print(t1 - t0)
    #seeded = SeededInventory(targets, metrics, 1000, 200, 1, None, 0, 'flower', 'domain', True)
    print('initialized')

    stuff = np.load('seed.npy')
    print(seeded.upper_bound())
    coefs = np.random.rand(100, 1)
    x = np.hstack((coefs, 1 - coefs))
    seeded.simulate_multi(x, 4)
    ''' 
    while True:
        np.save('backup.npy', stuff)
        t0 = time.time()
        coef = np.random.rand(10, 1)
        x = np.hstack((coef, 1 - coef))
        y = seeded.simulate(x).reshape((-1, 1))
        combined = np.hstack((x, y))
        stuff = np.vstack((stuff, combined))
        t1 = time.time()
        print(t1 - t0)
        np.save('seed.npy', stuff)

    load = SeededInventory.load(targets, metrics, 10, 200, 0, None, 0, 'flower')
    print(load == seeded)

    print(t1 - t0)
    '''