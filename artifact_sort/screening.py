from __future__ import annotations

from typing import Iterable

import numpy as np
from numpy.typing import NDArray

from .model import STAT_INDEX, STAT_KEYS
from .scenarios import Evaluator, Scenario


def _representative_points(
    representative: NDArray[np.float64], scenario: Scenario
) -> Iterable[NDArray[np.float64]]:
    yield representative
    for stat, minimum in scenario.constraints:
        totals = scenario.base_stats + scenario.bonus_stats + representative
        boundary = representative.copy()
        boundary[stat] += minimum - totals[stat]
        for offset in (-5.0, 0.0, 5.0):
            point = boundary.copy()
            point[stat] += offset
            yield point
    crit_rate = STAT_INDEX["critRate_"]
    crit_cap = representative.copy()
    crit_cap[crit_rate] = max(
        0.0,
        100.0 - scenario.base_stats[crit_rate] - scenario.bonus_stats[crit_rate],
    )
    yield crit_cap
    metadata_points = scenario.metadata.get("representative_stats")
    if isinstance(metadata_points, list):
        for raw in metadata_points:
            if not isinstance(raw, dict):
                continue
            point = representative.copy()
            for key, value in raw.items():
                if key in STAT_INDEX and isinstance(value, (int, float)):
                    point[STAT_INDEX[key]] = float(value)
            yield point


def screening_directions(
    evaluator: Evaluator,
    scenario: Scenario,
    representative: NDArray[np.float64],
    *,
    cosine_threshold: float = 0.995,
) -> NDArray[np.float64]:
    """Finite-difference directions around nonlinear boundaries, clustered."""

    directions: list[NDArray[np.float64]] = []
    for point in _representative_points(representative, scenario):
        weights = evaluator.marginal_weights(point, scenario)
        norm = float(np.linalg.norm(weights))
        if norm == 0:
            continue
        direction = weights / norm
        if any(float(existing @ direction) >= cosine_threshold for existing in directions):
            continue
        directions.append(direction)
    for stat, _ in scenario.constraints:
        direction = np.zeros(len(STAT_KEYS), dtype=np.float64)
        direction[stat] = 1.0
        if not any(float(existing @ direction) >= cosine_threshold for existing in directions):
            directions.append(direction)
    if not directions:
        directions.append(np.ones(len(STAT_KEYS), dtype=np.float64))
    return np.vstack(directions)


def screen_scores(
    stats: NDArray[np.float64], directions: NDArray[np.float64]
) -> NDArray[np.float64]:
    projections = stats @ directions.T
    scales = np.maximum(np.max(np.abs(projections), axis=0), 1.0)
    return np.max(projections / scales, axis=1)
