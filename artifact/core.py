import numpy as np
from numpy.typing import NDArray
from collections.abc import Collection
from .constants import ARTIFACT_DTYPE, TARGET_DTYPE, STAT_2_NUM, STAT_DTYPE

def find_main(artifact: NDArray[ARTIFACT_DTYPE]) -> int:
    mask = artifact == 160
    if np.any(mask):
        return np.flatnonzero(mask)[0]
    else:
        return np.flatnonzero(artifact == 80)[0]
    
def find_sub(
    artifact: NDArray[ARTIFACT_DTYPE], 
    main: int | None = None
) -> NDArray[STAT_DTYPE]: # TODO: i'm skeptical of performance
    if main is None:
        main = find_main(artifact)
    
    temp = artifact[main]
    artifact[main] = 0
    subs = np.flatnonzero(artifact)
    artifact[main] = temp
    
    return subs

def vectorize(target: dict[str, int]) -> NDArray[TARGET_DTYPE]:
    output = np.zeros(19, dtype=TARGET_DTYPE)
    for key, value in target.items():
        if key == 'crit_':
            output[8] = value
            output[9] = value
            continue

        output[STAT_2_NUM[key]] = value

    return output

def multi_vectorize(
    targets: Collection[dict[str, int]]
) -> NDArray[TARGET_DTYPE]:
    output = np.zeros((len(targets), 19), dtype=TARGET_DTYPE)
    for i, target in enumerate(targets):
        output[i] = vectorize(target)
    return output

def score(
    artifacts: NDArray[ARTIFACT_DTYPE], 
    targets: NDArray[TARGET_DTYPE]
) -> int | NDArray[TARGET_DTYPE]:
    return artifacts @ targets