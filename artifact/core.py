import numpy as np
from .constants import *

def find_main(artifact):
    mask = artifact == 160
    if np.any(mask):
        return np.where(mask == True)[0][0]
    else:
        return np.where(artifact == 80)[0][0]
    
def find_sub(artifact, main=None): # TODO: i'm skeptical of performance
    if main is None:
        main = find_main(artifact)
    
    temp = artifact[main]
    artifact[main] = 0
    subs = np.nonzero(artifact)[0]
    artifact[main] = temp
    
    return subs

def vectorize(targets):
    """Convert a target dictionary to a target array.

    Args:
        targets (dict): Mapping from stat to weight. Weights must be
        ints, or they will be cast.

    Returns:
        NDArray: Array of stat weights.
    """
    if isinstance(targets, dict):
        output = np.zeros(19, dtype=np.uint32)
        for key, value in targets.items():
            if key == 'crit_':
                output[8] = value
                output[9] = value
                continue

            output[STAT_2_NUM[key]] = value
    else:
        output = np.zeros((len(targets), 19), dtype=np.uint32)
        for i, target in enumerate(targets):
            for key, value in target.items():
                if key == 'crit_':
                    output[i, 8] = value
                    output[i, 9] = value
                    continue

                output[i, STAT_2_NUM[key]] = value

    return output

def score(artifacts, targets):
    """Calculate scores. If given a single artifact, returns a scalar.
    If ggiven multiple artifacts, returns an array.

    Args:
        artifacts (_type_): _description_
        targets (_type_): _description_

    Returns:
        _type_: _description_
    """
    
    # TODO: additionally put vectorization to caller functions so this
    # doesn't repeat
    if type(targets) == dict:
        targets = vectorize(targets)
        
    return artifacts @ targets