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

''' 
artifact lookup: [num_artifacts x 6 x 19]
scores lookup [num_artifacts x 6 x num_scores]

'''

class SeededInventory:
    def __init__(self, num_inventories, num_iter, num_artifacts, seed, set, lvl, slot, source):
        self.artifacts= np.full((num_inventories, num_iter, num_artifacts, 6, 19), -1)
        for inventory in range(num_inventories):
            for iter in range(num_iter):
                for artifact in range(num_artifacts):
                    self.artifacts[inventory, iter, artifact, 0, :] = FastArtifact.generate(set, lvl, slot, source).stats