"""Array execution of compiled scenarios; scalar evaluation remains the oracle.

Rows contain aggregate artifact additions in STAT_KEYS order. Search validates
artifact identities and legal slots before constructing these numerical inputs.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

import numpy as np
from numpy.typing import NDArray

from .formulas import EvaluationError, Predicate
from .library_runtime import CompiledScenario, Evaluation, LEGAL_MAINS, PRIMARY_STATS
from .model import STAT_KEYS


@dataclass(frozen=True)
class BatchEvaluation:
    scores: NDArray[np.float64]
    feasible: NDArray[np.bool_]
    effective_stats: Mapping[str, NDArray[np.float64]]
    channels: Mapping[str, NDArray[np.float64]]
    violations: Mapping[str, NDArray[np.bool_]]
    missing_set_pieces: NDArray[np.int64]
    deficit: NDArray[np.float64]

    def row(self, index: int) -> Evaluation:
        return Evaluation(
            float(self.scores[index]),
            MappingProxyType(
                {key: float(value[index]) for key, value in self.effective_stats.items()}
            ),
            MappingProxyType({key: float(value[index]) for key, value in self.channels.items()}),
            tuple(key for key, mask in self.violations.items() if mask[index]),
        )


def evaluate_batch(
    scenario: CompiledScenario,
    artifact_stats: NDArray[np.float64],
    set_counts: Mapping[str, NDArray[np.int64]],
    *,
    main_stats: Mapping[str, NDArray[np.str_]] | None = None,
) -> BatchEvaluation:
    """Evaluate full formulas, staged effects and constraints for a build batch.

    Inactive effects are evaluated only on their active rows, preserving scalar
    behavior even when an inactive formula would divide by zero.
    """
    additions_array = np.asarray(artifact_stats, dtype=np.float64)
    if additions_array.ndim != 2 or additions_array.shape[1] != len(STAT_KEYS):
        raise EvaluationError("batch stats must have shape (N, len(STAT_KEYS))")
    if not np.all(np.isfinite(additions_array)):
        raise EvaluationError("batch stats must be finite")
    count = len(additions_array)
    unknown = set(set_counts) - scenario.known_sets
    if unknown:
        raise EvaluationError(f"unknown candidate sets: {sorted(unknown)}")
    sets = {key: np.asarray(values) for key, values in set_counts.items()}
    if any(
        values.shape != (count,)
        or values.dtype.kind not in "iu"
        or np.any(values < 0)
        for values in sets.values()
    ):
        raise EvaluationError("batch set counts must be nonnegative integer vectors")
    if np.any(sum(sets.values(), np.zeros(count, dtype=np.int64)) > 5):
        raise EvaluationError("set counts must total at most five")
    mains = {key: np.asarray(values) for key, values in (main_stats or {}).items()}
    if any(
        slot not in LEGAL_MAINS
        or values.shape != (count,)
        or not np.all(np.isin(values, tuple(LEGAL_MAINS[slot])))
        for slot, values in mains.items()
    ):
        raise EvaluationError("illegal batch main stat")
    definition = scenario.definition
    base = definition.base
    additions = {
        key: additions_array[:, i] + definition.buffs.get(key, 0)
        for i, key in enumerate(STAT_KEYS)
    }
    raw = {}
    effective = {}
    channels = {
        key: np.full(count, 0.0 if channel.combine == "add" else 1.0)
        for key, channel in scenario.channels.items()
    }
    stats = base, raw, effective

    def activation(predicate: Predicate, active=None):
        if active is None:
            active = np.ones(count, dtype=bool)
        if not np.any(active):
            return active
        if predicate.op == "set":
            values = sets.get(predicate.key, np.zeros(count, dtype=np.int64))
            return active & (values >= predicate.pieces)
        if predicate.op == "all":
            result = active
            for child in predicate.args:
                result = activation(child, result)
            return result
        if predicate.op == "any":
            result = np.zeros(count, dtype=bool)
            for child in predicate.args:
                result |= activation(child, active & ~result)
            return result
        if predicate.op == "not":
            return active & ~activation(predicate.args[0], active)
        return active & predicate.evaluate(definition.conditions, {})

    for stage in (0, 1, 2):
        contributions = {}
        for effect in scenario.effects:
            if effect.stage != stage:
                continue
            mask = np.ones(count, dtype=bool) if effect.when is None else activation(effect.when)
            if not np.any(mask):
                continue
            active_count = int(mask.sum())
            if active_count == count:
                value = effect.program.evaluate_batch(stats, channels, count)
            else:
                selected_stats = (
                    base,
                    {k: v[mask] for k, v in raw.items()},
                    {k: v[mask] for k, v in effective.items()},
                )
                selected_channels = {k: v[mask] for k, v in channels.items()}
                value = effect.program.evaluate_batch(
                    selected_stats, selected_channels, active_count
                )
            kind, target = effect.target.split(".", 1)
            if kind == "stats":
                if target not in contributions:
                    contributions[target] = np.zeros(count)
                contributions[target][mask] += value
            elif scenario.channels[target].combine == "add":
                channels[target][mask] += value
            else:
                channels[target][mask] *= value
        if stage == 0:
            for key in STAT_KEYS:
                additions[key] = additions[key] + contributions.get(key, 0)
                raw[key] = base.get(key, 0) + additions[key]
            for key in PRIMARY_STATS:
                if key in base:
                    raw[key] = base[key] * (1 + raw[f"{key}_"]) + additions[key]
        elif stage == 1:
            effective.update({
                key: raw[key] + contributions.get(key, 0)
                for key in STAT_KEYS if key not in PRIMARY_STATS
            })
            for key in PRIMARY_STATS:
                if key in base:
                    effective[key] = (
                        base[key] * (1 + effective[f"{key}_"])
                        + additions[key] + contributions.get(key, 0)
                    )
    if any(
        not np.all(np.isfinite(value))
        for mapping in (raw, effective, channels) for value in mapping.values()
    ):
        raise EvaluationError("nonfinite aggregated stat or channel")
    try:
        scores = scenario.score.evaluate_batch(stats, channels, count)
    except EvaluationError as error:
        raise EvaluationError(f"{definition.id}: {error}") from error
    violations = {}
    deficit = np.zeros(count)
    for key, minimum in definition.minimums.items():
        values = effective[key]
        close = np.abs(values - minimum) <= np.maximum(
            1e-12, 1e-12 * np.maximum(np.abs(values), abs(minimum))
        )
        violations[f"{key} below minimum {minimum}"] = (values < minimum) & ~close
        deficit += np.maximum(0, minimum - values) / max(abs(minimum), 1.0)
    for key, maximum in definition.maximums.items():
        values = effective[key]
        close = np.abs(values - maximum) <= np.maximum(
            1e-12, 1e-12 * np.maximum(np.abs(values), abs(maximum))
        )
        violations[f"{key} above maximum {maximum}"] = (values > maximum) & ~close
        deficit += np.maximum(0, values - maximum) / max(abs(maximum), 1.0)
    missing = np.full(count, 6, dtype=np.int64)
    for strategy in definition.sets:
        strategy_missing = np.zeros(count, dtype=np.int64)
        for key, required in strategy.items():
            strategy_missing += np.maximum(
                0, required - sets.get(key, np.zeros(count, dtype=np.int64))
            )
        missing = np.minimum(missing, strategy_missing)
    violations["set composition does not match any allowed strategy"] = missing != 0
    for slot, allowed in definition.mains.items():
        if slot not in mains:
            violations[f"missing main stat for {slot}"] = np.ones(count, dtype=bool)
        else:
            violations[f"main stat for {slot} is not allowed"] = ~np.isin(mains[slot], allowed)
    feasible = np.ones(count, dtype=bool)
    for mask in violations.values():
        feasible &= ~mask
    return BatchEvaluation(scores, feasible, effective, channels, violations, missing, deficit)
