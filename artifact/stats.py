import numpy as np
from numpy.typing import NDArray
from typing import cast
from .constants import ARTIFACT_DTYPE, TARGET_DTYPE
from .core import score

def avg(
    states: NDArray[ARTIFACT_DTYPE], 
    probs: NDArray, 
    targets: NDArray[TARGET_DTYPE]
) -> float | NDArray:
    scores = cast(np.ndarray, score(states, targets))
    return scores @ probs

def second_moment(
    states: NDArray[ARTIFACT_DTYPE], 
    probs: NDArray, 
    targets: NDArray[TARGET_DTYPE]
) -> float | NDArray:
    scores = cast(np.ndarray, score(states, targets))
    return scores**2 @ probs

def variance(
    states: NDArray[ARTIFACT_DTYPE], 
    probs: NDArray, 
    targets: NDArray[TARGET_DTYPE], 
    mean: float | NDArray | None = None
) -> float | NDArray:
    if mean is None:
        mean = avg(states, probs, targets)
        
    scores = cast(np.ndarray, score(states, targets))
    return (scores - mean)**2 @ probs

def std(
    states: NDArray[ARTIFACT_DTYPE], 
    probs: NDArray, 
    targets: NDArray[TARGET_DTYPE], 
    mean: float | NDArray | None = None
) -> float | NDArray:
    return np.sqrt(variance(states, probs, targets, mean))