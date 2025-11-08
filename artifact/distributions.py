import numpy as np
from .constants import *
from .core import *

def distro(N):
    increments = np.array([7, 8, 9, 10])
    n_vars = 4

    # initialize dictionary with starting state
    dist = {(0, 0, 0, 0): 1.0}

    # precompute all variable + increment combinations
    var_choices = np.arange(n_vars)
    inc_choices = increments
    choices = [(v, inc) for v in var_choices for inc in inc_choices]

    for _ in range(N):
        new_dist = {}
        for state, prob in dist.items():
            for v, inc in choices:
                new_state = list(state)
                new_state[v] += inc
                new_state = tuple(new_state)
                new_prob = prob / len(choices)
                new_dist[new_state] = new_dist.get(new_state, 0.0) + new_prob
        dist = new_dist

    # convert to structured numpy arrays for clarity
    states = np.array(list(dist.keys()), dtype=np.uint8)
    probs = np.array(list(dist.values()))

    return states, probs

def trim_distro(N, X):
    # possible increments
    increments = np.array([7, 8, 9, 10])
    N_VARS = min(X, 4)
    N_TOTAL = 4  # total possible slots

    # start with all zeros
    dist = {tuple([0] * N_VARS): 1.0}

    P_NONE = (N_TOTAL - N_VARS) / N_TOTAL
    P_VAR = 1 / N_TOTAL

    for _ in range(N):
        new_dist = {}
        for state, prob in dist.items():
            # case 1: nothing happens
            if P_NONE > 0:
                new_dist[state] = new_dist.get(state, 0.0) + prob * P_NONE
            # case 2: one of X vars gets incremented by 7–10
            for v in range(N_VARS):
                for inc in increments:
                    new_state = list(state)
                    new_state[v] += inc
                    new_state = tuple(new_state)
                    new_prob = prob * P_VAR / 4 # len(increments)
                    new_dist[new_state] = new_dist.get(new_state, 0.0) + new_prob
        dist = new_dist

    states = np.array(list(dist.keys()), dtype=np.uint8)
    probs = np.array(list(dist.values()))
    return states, probs

def single_distro(artifacts):
    if artifacts.ndim == 1:
        # Rename to "artifact" to make things less confusing
        artifact = artifacts
        # TODO: clean this shit up
        if np.count_nonzero(artifact) == 4:
            sub_probs = SUB_PROBS.copy()
            sub_probs[np.nonzero(artifact)[0]] = 0
            sub_probs /= np.sum(sub_probs)
            
            num_possibilities = np.count_nonzero(sub_probs) * 4
            dist = np.tile(artifact, (num_possibilities + 1, 1))
            probs = np.zeros((num_possibilities + 1), dtype=float)
            
            dist = np.tile(artifact, (num_possibilities + 1, 1))
            
            nz_mask = sub_probs != 0
            nz_idx  = np.nonzero(nz_mask)[0]           # shape (M,)
            M       = nz_idx.size

            i = np.arange(M)
            j = np.arange(4, dtype=np.uint8)
            rows = 1 + 4*i[:, None] + j               # shape (M,4)
            cols = nz_idx[:, None]                    # shape (M,1)

            dist[rows, cols] += (j + 7)               # broadcasts to (M,4)
            probs[1:] = np.repeat(sub_probs[sub_probs != 0], 4) / 4
            
        else:
            dist = np.tile(artifact, (17, 1))
            probs = np.full(17, 1/16, dtype=float)
            probs[0] = 0
            
            nz_idx  = find_sub(artifact)           # shape (M,)
            M       = nz_idx.size

            # 2. build row and column indices for dist update
            #    rows: for each i in [0..M-1], rows = 1 + 4*i + [0,1,2,3]
            i = np.arange(M)
            j = np.arange(4, dtype=np.uint8)
            rows = 1 + 4*i[:, None] + j               # shape (M,4)
            cols = nz_idx[:, None]                    # shape (M,1)

            # 3. add j+7 to dist at those positions in one shot
            dist[rows, cols] += (j + 7)               # broadcasts to (M,4)
    else:
        dist = []
        probs = []
        for artifact in artifacts:
            temp_dist, temp_probs = single_distro(artifact)
            dist.append(temp_dist)
            probs.append(temp_probs)
            
    return dist, probs