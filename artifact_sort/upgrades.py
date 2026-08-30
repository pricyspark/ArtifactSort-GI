from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np
from numpy.typing import NDArray

from .model import ArtifactBatch, SUBSTAT_MAX, cumulative_artifact_exp
from .optimizer import BuildOptimizer, BuildResult
from .outcomes import final_outcomes
from .scenarios import Scenario


@dataclass(frozen=True, slots=True)
class ScenarioPotential:
    scenario_id: str
    tier: str
    baseline_utility: float
    expected_utility: float
    expected_relative_gain: float
    useful_probability: float


@dataclass(frozen=True, slots=True)
class UpgradeRecommendation:
    index: int
    artifact_id: str
    level: int
    next_checkpoint: int
    incremental_exp: int
    incremental_mora: int
    expected_relative_gain: float
    gain_per_1000_exp: float
    useful_probability: float
    protected_at_probability_floor: bool
    sensitivity: tuple[tuple[float, bool], ...]
    scenarios: tuple[ScenarioPotential, ...]


def _next_checkpoint(level: int) -> int:
    return min(20, ((level // 4) + 1) * 4)


def _outcome_stats(
    current: NDArray[np.float64], sub_rolls: NDArray[np.uint8]
) -> NDArray[np.float64]:
    result = np.repeat(current[None, :], len(sub_rolls), axis=0)
    result[:, :10] = sub_rolls.astype(np.float64) * (SUBSTAT_MAX / 10.0)
    return result


def _forced_utility(
    optimizer: BuildOptimizer,
    scenario: Scenario,
    pools: Sequence[BuildResult],
    index: int,
    old_stats: NDArray[np.float64],
    outcomes: NDArray[np.float64],
) -> NDArray[np.float64]:
    if not pools:
        return np.full(len(outcomes), -np.inf)
    values = np.full(len(outcomes), -np.inf, dtype=np.float64)
    for build in pools:
        # Set membership does not change across outcomes, so the set-adjusted
        # build total can be updated by replacing only this artifact's row.
        totals = build.stats[None, :] - old_stats[None, :] + outcomes
        evaluated = optimizer.evaluator.evaluate_batch(totals, scenario)
        values = np.maximum(values, evaluated)
    return values


class UpgradeAnalyzer:
    """Exact roll probabilities evaluated against complete-build complements."""

    def __init__(
        self,
        optimizer: BuildOptimizer,
        scenarios: Sequence[Scenario],
        *,
        epsilon: float = 0.01,
        probability_floor: float = 0.01,
        complement_pool_size: int = 160,
    ) -> None:
        if not scenarios:
            raise ValueError("at least one scenario is required")
        if not 0 <= epsilon < 1:
            raise ValueError("epsilon must be between zero and one")
        if not 0 <= probability_floor <= 1:
            raise ValueError("probability_floor must be between zero and one")
        self.optimizer = optimizer
        self.scenarios = tuple(scenarios)
        self.epsilon = epsilon
        self.probability_floor = probability_floor
        self.complement_pool_size = complement_pool_size

    def _screen(self, max_candidates: int | None) -> NDArray[np.int64]:
        batch = self.optimizer.batch
        candidates = np.flatnonzero(
            (batch.rarities == 5)
            & (batch.levels < 20)
            & (np.count_nonzero(batch.sub_rolls, axis=1) == 4)
        )
        if max_candidates is None or len(candidates) <= max_candidates:
            return candidates.astype(np.int64, copy=False)
        stats = batch.final_stats()
        scores = np.zeros(len(batch), dtype=np.float64)
        representative = np.median(stats[candidates], axis=0)
        for scenario in self.scenarios:
            weights = self.optimizer.evaluator.marginal_weights(representative, scenario)
            scores = np.maximum(scores, stats @ weights)
        selected = candidates[
            np.argpartition(scores[candidates], -max_candidates)[-max_candidates:]
        ]
        return selected[np.argsort(scores[selected])[::-1]].astype(np.int64)

    def analyze(self, *, max_candidates: int | None = 24) -> list[UpgradeRecommendation]:
        batch = self.optimizer.batch
        current_stats = batch.final_stats()
        baselines: dict[str, float] = {}
        for scenario in self.scenarios:
            result = self.optimizer.optimize(scenario, top_k=1)
            baselines[scenario.id] = result[0].utility if result else -np.inf

        recommendations: list[UpgradeRecommendation] = []
        for index in self._screen(max_candidates):
            distribution = final_outcomes(batch, int(index))
            outcome_stats = _outcome_stats(current_stats[index], distribution.sub_rolls)
            scenario_results: list[ScenarioPotential] = []
            gains: list[float] = []
            usefulness: list[float] = []
            for scenario in self.scenarios:
                pools = self.optimizer.optimize(
                    scenario,
                    stats=current_stats,
                    include_unfinished=True,
                    forced_index=int(index),
                    top_k=self.complement_pool_size,
                )
                utilities = _forced_utility(
                    self.optimizer,
                    scenario,
                    pools,
                    int(index),
                    current_stats[index],
                    outcome_stats,
                )
                baseline = baselines[scenario.id]
                portfolio = np.maximum(utilities, baseline)
                if baseline > 0 and np.isfinite(baseline):
                    relative = np.maximum(0.0, portfolio / baseline - 1.0)
                    expected_gain = float(distribution.probabilities @ relative)
                    useful = float(
                        distribution.probabilities[
                            utilities >= (1.0 - self.epsilon) * baseline
                        ].sum()
                    )
                else:
                    expected_gain = 0.0
                    useful = 0.0
                scenario_results.append(
                    ScenarioPotential(
                        scenario.id,
                        scenario.tier,
                        baseline,
                        float(distribution.probabilities @ portfolio),
                        expected_gain,
                        useful,
                    )
                )
                gains.append(expected_gain)
                usefulness.append(useful)

            level = int(batch.levels[index])
            checkpoint = _next_checkpoint(level)
            exp_cost = cumulative_artifact_exp(checkpoint) - cumulative_artifact_exp(level)
            expected_gain = float(np.mean(gains)) if gains else 0.0
            useful_probability = max(usefulness, default=0.0)
            sensitivity = tuple(
                (floor, useful_probability >= floor) for floor in (0.001, 0.01, 0.05)
            )
            recommendations.append(
                UpgradeRecommendation(
                    int(index),
                    str(batch.ids[index]),
                    level,
                    checkpoint,
                    exp_cost,
                    exp_cost,
                    expected_gain,
                    expected_gain / max(exp_cost, 1) * 1000.0,
                    useful_probability,
                    useful_probability >= self.probability_floor,
                    sensitivity,
                    tuple(scenario_results),
                )
            )
        recommendations.sort(
            key=lambda item: (item.gain_per_1000_exp, item.useful_probability), reverse=True
        )
        return recommendations

    def option_values(self, *, max_candidates: int | None = 64) -> NDArray[np.float64]:
        values = np.zeros(len(self.optimizer.batch), dtype=np.float64)
        for item in self.analyze(max_candidates=max_candidates):
            # A probability-protected unfinished artifact is expensive for the
            # tertiary deletion objective; the primary regret objectives still
            # remain lexicographically dominant.
            protection = 1.0 if item.protected_at_probability_floor else 0.0
            values[item.index] = (
                protection + item.useful_probability + item.expected_relative_gain
            )
        return values
