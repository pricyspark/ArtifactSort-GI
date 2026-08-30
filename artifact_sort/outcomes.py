from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from functools import lru_cache
import numpy as np
from numpy.typing import NDArray

from .model import ArtifactBatch


ROLL_INCREMENTS = (7, 8, 9, 10)


@dataclass(frozen=True, slots=True)
class OutcomeDistribution:
    sub_rolls: NDArray[np.uint8]
    probabilities: NDArray[np.float64]

    def __post_init__(self) -> None:
        if self.sub_rolls.ndim != 2 or self.sub_rolls.shape[1] != 10:
            raise ValueError("outcome sub-rolls must have shape (N, 10)")
        if self.probabilities.shape != (len(self.sub_rolls),):
            raise ValueError("outcome probabilities have invalid shape")
        if not np.isclose(self.probabilities.sum(), 1.0):
            raise ValueError("outcome probabilities must sum to one")


@lru_cache(maxsize=4096)
def _increments(remaining: int, substats: tuple[int, ...]) -> tuple[tuple[tuple[int, ...], float], ...]:
    if remaining == 0:
        return (((0,) * 10, 1.0),)
    states: dict[tuple[int, ...], float] = {(0,) * 10: 1.0}
    chance = 1.0 / (len(substats) * len(ROLL_INCREMENTS))
    for _ in range(remaining):
        next_states: dict[tuple[int, ...], float] = defaultdict(float)
        for state, probability in states.items():
            for stat in substats:
                for increment in ROLL_INCREMENTS:
                    updated = list(state)
                    updated[stat] += increment
                    next_states[tuple(updated)] += probability * chance
        states = next_states
    return tuple(states.items())


def final_outcomes(batch: ArtifactBatch, index: int) -> OutcomeDistribution:
    base = batch.sub_rolls[index]
    substats = tuple(int(i) for i in np.flatnonzero(base))
    if len(substats) != 4:
        raise ValueError(f"artifact {batch.ids[index]} does not have four known substats")
    nominal_remaining = int(batch.remaining_random_rolls()[index])
    # Once an artifact has reached +4, both starting-line histories have the
    # same number of future checkpoints. The posterior still matters when
    # reconstructing invested history, but it must not create a fictitious
    # extra future roll.
    remaining_weights = {nominal_remaining: 1.0}
    combined: dict[tuple[int, ...], float] = defaultdict(float)
    for remaining, branch_probability in remaining_weights.items():
        for delta, probability in _increments(remaining, substats):
            state = tuple((base + np.asarray(delta, dtype=np.uint8)).tolist())
            combined[state] += branch_probability * probability
    states = np.asarray(tuple(combined), dtype=np.uint8)
    probabilities = np.asarray(tuple(combined.values()), dtype=np.float64)
    probabilities /= probabilities.sum()
    states.setflags(write=False)
    probabilities.setflags(write=False)
    return OutcomeDistribution(states, probabilities)


def sample_final_rolls(
    batch: ArtifactBatch, rng: np.random.Generator
) -> NDArray[np.uint8]:
    result = batch.sub_rolls.copy()
    for i, remaining in enumerate(batch.remaining_random_rolls()):
        substats = np.flatnonzero(result[i])
        if len(substats) != 4:
            continue
        for _ in range(int(remaining)):
            stat = int(rng.choice(substats))
            result[i, stat] += int(rng.choice(ROLL_INCREMENTS))
    return result


def sample_upgrade_tapes(
    batch: ArtifactBatch, rng: np.random.Generator
) -> tuple[tuple[tuple[int, int], ...], ...]:
    """Sample hidden (stat, roll coefficient) tapes once for a trial."""

    tapes: list[tuple[tuple[int, int], ...]] = []
    for i, nominal in enumerate(batch.remaining_random_rolls()):
        substats = np.flatnonzero(batch.sub_rolls[i])
        remaining = int(nominal)
        if len(substats) != 4:
            tapes.append(())
            continue
        tapes.append(
            tuple(
                (int(rng.choice(substats)), int(rng.choice(ROLL_INCREMENTS)))
                for _ in range(remaining)
            )
        )
    return tuple(tapes)
