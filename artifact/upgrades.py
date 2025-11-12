import numpy as np
import math
from numpy.typing import NDArray
from numpy.random import Generator
from typing import Any
from collections.abc import Collection
from zlib import crc32
from typing import cast
from .core import find_sub
from .constants import ARTIFACT_DTYPE, INCREMENTS, SLVL_DTYPE, STAT_DTYPE, MAIN_PROBS, SUB_PROBS

def _upgrade_helper(
    artifact: NDArray[ARTIFACT_DTYPE], 
    rng: Generator, 
    main: int | None = None
) -> None:
    artifact[rng.choice(find_sub(artifact, main=main))] += rng.choice(INCREMENTS)

def upgrade(
    artifact: NDArray[ARTIFACT_DTYPE], 
    main: int | Collection | None = None, 
    rng: Generator | None = None, 
    seed: Any = None
) -> None:
    if rng is None:
        rng = np.random.default_rng(seed)
    
    if artifact.ndim == 1:
        assert not isinstance(main, Collection)
        _upgrade_helper(artifact, rng, main=main)
    else:
        if isinstance(main, int):
            main = [main] * len(artifact)
        elif main is None:
            main = [None] * len(artifact)
        for artifact, main in zip(artifact, main):
            _upgrade_helper(artifact, rng, main=main)

def _smart_seed(artifact: NDArray[ARTIFACT_DTYPE]) -> int | NDArray[np.uint32]:
    if artifact.ndim == 1:
        return crc32(artifact.tobytes())
    else:
        output = np.zeros(len(artifact), dtype=np.uint32)
        for idx, artifact in enumerate(artifact):
            output[idx] = crc32(artifact.flatten().tobytes())
        return output
    
def smart_upgrade(
    artifact: NDArray[ARTIFACT_DTYPE], 
    main: int | Collection | None = None
) -> None:
    if artifact.ndim == 1:
        RNG = np.random.default_rng(_smart_seed(artifact))
        assert isinstance(main, int)
        _upgrade_helper(artifact, RNG, main)
    else:
        if isinstance(main, int):
            main = [main] * len(artifact)
        elif main is None:
            main = [None] * len(artifact)
        seeds = cast(np.ndarray, _smart_seed(artifact))
        for a, s, m in zip(artifact, seeds, main):
            RNG = np.random.default_rng(s)
            _upgrade_helper(a, RNG, m)

def smart_upgrade_until_max(
    artifact: NDArray[ARTIFACT_DTYPE], 
    slvl: int | NDArray[SLVL_DTYPE], 
    main: int | Collection | None = None
) -> None: # TODO: this is code duplication
    num_upgrades = np.where(slvl < 0, 4, 5 - slvl // 4)    
    
    if artifact.ndim == 1 or len(artifact) == 1:
        for _ in range(num_upgrades):
            smart_upgrade(artifact, main)
    else:
        assert isinstance(slvl, np.ndarray)
        if isinstance(main, int):
            main = [main] * len(artifact)
        elif main is None:
            main = [None] * len(artifact)
        for artifact, num, main in zip(artifact, num_upgrades, main):
            for _ in range(num):
                smart_upgrade(artifact, main)
    
def upgrade_until_max(
    artifact: NDArray[ARTIFACT_DTYPE], 
    slvl: int | NDArray[SLVL_DTYPE], 
    main: int | Collection | None = None, 
    seed: Any = None
) -> None:
    num_upgrades = np.where(slvl < 0, 4, 5 - slvl // 4)    
    
    if artifact.ndim == 1 or len(artifact) == 1:
        for _ in range(num_upgrades):
            upgrade(artifact, main, seed)
    else:
        assert isinstance(slvl, np.ndarray)
        if isinstance(main, int):
            main = [main] * len(artifact)
        elif main is None:
            main = [None] * len(artifact)
        for artifact, num, main in zip(artifact, num_upgrades, main):
            for _ in range(num):
                upgrade(artifact, main) # TODO seed generator, otherwise they all get the same seed

def estimate_upgrades(x: int) -> int | float:
    lower = math.ceil(x / 10)
    upper = x // 7
    
    if upper == lower:
        return lower
    
    return (lower + upper) / 2 # TODO: use math to make this more accurate

def next_lvl(lvl: int) -> int:
    if lvl < 0:
        return 8
    else:
        return 4 * ((lvl // 4) + 1)
    
def generate(
    slot: str, 
    main: int | Collection[int] | None = None, 
    lvl: int | Collection[int] = 0, 
    source: str = 'domain', 
    size: int | None = None, 
    rng: Generator | None= None, 
    seed: Any = None
) -> tuple[NDArray[ARTIFACT_DTYPE], NDArray]:
    if rng is None:
        rng = np.random.default_rng(seed)
        
    # TODO: test if this handling works properly
    main_c = isinstance(main, Collection)
    lvl_c = isinstance(lvl, Collection)
    if size is None:
        if not main_c and not lvl_c:
            raise ValueError('Size cannot be inferred')
        
        if main_c and lvl_c and len(main) != len(lvl):
            raise ValueError('Sizes do not match')
        
        if main_c: # Stupid type checker makes me do ugly stuff
            size = len(main)
        if lvl_c:
            size = len(lvl)
        assert size is not None
    else:
        if main_c and size != len(main):
            raise ValueError('Sizes do not match')
        if lvl_c and size != len(lvl):
            raise ValueError('Sizes do not match')
        
    '''
    if size is None:
        if isinstance(main, Collection):
            size = len(main)
        else:
            assert isinstance(lvl, Collection), 'Size cannot be inferred'
            size = len(lvl)
    '''
            
    if isinstance(main, int):
        main = np.full(size, main, dtype=STAT_DTYPE)
    elif isinstance(main, Collection):
        main = np.array(main, dtype=STAT_DTYPE)
    else:
        main = rng.choice(19, p=MAIN_PROBS[slot], size=size)
        
    if isinstance(lvl, Collection):
        slvls = np.array(lvl, dtype=SLVL_DTYPE)
    else:
        slvls = np.full(size, lvl, dtype=SLVL_DTYPE)

    # Figure out probability of starting with 4 substats
    match source:
        case 'domain':
            prob = 1/5
        case 'normal boss':
            prob = 1/3
        case 'weekly boss':
            prob = 1/3
        case 'strongbox':
            prob = 1/3
        case 'domain reliquary':
            prob = 1/3
        case _:
            raise ValueError('Invalid artifact source.')
        
    output = np.zeros((size, 19), dtype=ARTIFACT_DTYPE)
    output[np.arange(size), main] = np.where(main < 3, 160, 80)
    
    sub_probs = np.repeat(SUB_PROBS[None, :10], repeats=size, axis=0) # Stats >9 can't be substats
    sub_probs[np.arange(size), main] = 0
    sub_probs /= np.sum(sub_probs, axis=1)[:, None]
    
    # Efraimidis-Spirakis weighted reservoir sampling
    r = rng.random((size, 10))
    with np.errstate(divide='ignore', invalid='ignore'):
        s = r ** (1 / sub_probs)
    substats = np.argpartition(s, 4, axis=1)[:, -4:]
    
    coefs = rng.choice(INCREMENTS, (size, 4))
    output[np.arange(size)[:, None], substats] += coefs
    
    num_upgrades = slvls // 4
    r = rng.random(size)
    mask = r >= prob
    num_upgrades[mask] -= 1
    
    for i, n in enumerate(num_upgrades):
        if n == -1:
            slvls[i] -= 4
            continue
        r = rng.integers(16, size=n)
        upgrades = r // 4
        coefs = upgrades % 4
        for upgrade, coef in zip(upgrades, coefs):
            output[i, substats[i, upgrade]] += INCREMENTS[coef]
            
    return output, slvls
    
# TODO: see if refactor is necessary
def sample_upgrade(
    artifact: NDArray[ARTIFACT_DTYPE], 
    samples: int, 
    num_upgrades: int | None = None, 
    slvl: int | None = None, 
    rng: Generator | None = None, 
    seed: Any = None
):
    if rng is None:
        rng = np.random.default_rng(seed)

    if num_upgrades is None:
        assert slvl is not None
        num_upgrades = 4 if slvl < 0 else 5 - slvl // 4
    
    output = np.tile(artifact, (samples, 1))
    if num_upgrades == 0:
        return output, None
    
    tape = np.zeros((samples, num_upgrades), dtype=np.uint8)
    
    subs = find_sub(artifact)
    rows = np.arange(samples)
    for _ in range(num_upgrades):
        cols = rng.choice(subs, size=samples)
        increments = rng.choice(INCREMENTS, size=samples)
        output[rows, cols] += increments
        tape[:, _] = 4 * cols + increments - 7
    
    return output, tape