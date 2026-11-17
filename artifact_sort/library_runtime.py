"""Compiled scenario stat/effect evaluation, independent of deletion policy."""

from __future__ import annotations

from dataclasses import dataclass
import math
from numbers import Real
from types import MappingProxyType
from typing import Mapping

import numpy as np
from numpy.typing import NDArray

from .formulas import (
    Channel,
    Component,
    EvaluationError,
    LibraryError,
    Predicate,
    Program,
    Scalar,
    Stats,
)
from .model import STAT_KEYS

EVALUATOR_VERSION = "encoded-arithmetic-3"
PRIMARY_STATS = ("hp", "atk", "def")
INTRINSIC_STATS = frozenset((*PRIMARY_STATS, "enerRech_", "critRate_", "critDMG_"))
LEGAL_MAINS = {
    "flower": frozenset({"hp"}),
    "plume": frozenset({"atk"}),
    "sands": frozenset({"hp_", "atk_", "def_", "enerRech_", "eleMas"}),
    "goblet": frozenset({"hp_", "atk_", "def_", "eleMas", *STAT_KEYS[10:18]}),
    "circlet": frozenset(
        {"hp_", "atk_", "def_", "eleMas", "critRate_", "critDMG_", "heal_"}
    ),
}


def normalize_good_stats(stats: Stats) -> dict[str, float]:
    """Input boundary for GOOD percentage-point stats; never call on ratios."""
    result = _candidate_stats(stats)
    return {
        key: value / 100 if key.endswith("_") else value
        for key, value in result.items()
    }


def _candidate_stats(stats: Stats) -> dict[str, float]:
    result: dict[str, float] = {}
    for key, value in stats.items():
        if key not in STAT_KEYS:
            raise EvaluationError(f"unknown stat {key!r}")
        if (
            isinstance(value, bool)
            or not isinstance(value, Real)
            or not math.isfinite(value)
        ):
            raise EvaluationError(f"stat {key!r} must be finite and numeric")
        result[key] = float(value)
    return result


@dataclass(frozen=True, slots=True)
class ScenarioDefinition:
    id: str
    collection: str
    scoring_formula: str
    base: Stats
    buffs: Stats
    minimums: Stats
    maximums: Stats
    sets: tuple[Mapping[str, int], ...]
    conditions: Mapping[str, Scalar]
    parameters: Stats
    mains: Mapping[str, tuple[str, ...]]
    effects: tuple[str, ...]
    characters: tuple[str, ...]
    family: str | None = None


@dataclass(frozen=True, slots=True)
class Mechanics:
    """Explicit installed rules release; this class does not certify game accuracy.

    IDs must match the library pin. Validated is a release publisher's assertion.
    The caller supplies known game keys and any pinned components/channels.
    """

    id: str
    game_version: str
    sets: frozenset[str]
    characters: frozenset[str] = frozenset()
    components: Mapping[str, Component] | None = None
    channels: Mapping[str, Channel] | None = None
    validated: bool = False

    def __post_init__(self) -> None:
        if not self.id or not self.game_version:
            raise LibraryError("mechanics needs an ID and game version")
        object.__setattr__(self, "sets", frozenset(self.sets))
        object.__setattr__(self, "characters", frozenset(self.characters))
        object.__setattr__(
            self, "components", MappingProxyType(dict(self.components or {}))
        )
        object.__setattr__(
            self, "channels", MappingProxyType(dict(self.channels or {}))
        )


@dataclass(frozen=True, slots=True)
class Evaluation:
    score: float
    effective_stats: Stats
    channels: Stats
    violations: tuple[str, ...]

    @property
    def feasible(self) -> bool:
        """Meets scenario constraints; not a proof of a complete legal build."""
        return not self.violations


@dataclass(frozen=True, slots=True)
class CompiledEffect:
    id: str
    stage: int
    target: str
    when: Predicate | None
    program: Program


@dataclass(frozen=True, slots=True)
class Linearization:
    evaluation: Evaluation
    weights: Stats
    at_boundary: bool


@dataclass(frozen=True, slots=True)
class CompiledScenario:
    definition: ScenarioDefinition
    score: Program
    effects: tuple[CompiledEffect, ...]
    channels: Mapping[str, Channel]
    known_sets: frozenset[str]
    relevant_stats: frozenset[str]

    def evaluate(
        self,
        artifact_stats: Stats,
        set_counts: Mapping[str, int],
        *,
        main_stats: Mapping[str, str] | None = None,
    ) -> Evaluation:
        """Evaluate aggregate artifact additions in decimal units, even if infeasible.

        Main-stat assignments are needed for restricted slots. Missing assignments
        are reported as violations, not silently treated as permitted builds.
        """
        result, _, _ = self._evaluate(artifact_stats, set_counts, main_stats, False)
        return result

    def linearize(
        self,
        artifact_stats: Stats,
        set_counts: Mapping[str, int],
        *,
        main_stats: Mapping[str, str] | None = None,
    ) -> Linearization:
        """Derive local weights through every active effect, conversion, and channel.

        Set counts and conditions stay fixed. These weights are a local surrogate,
        not a feasibility penalty or a context-independent artifact rating.
        """
        result, derivative, boundary = self._evaluate(
            artifact_stats, set_counts, main_stats, True
        )
        assert derivative is not None
        return Linearization(
            result,
            MappingProxyType(dict(zip(STAT_KEYS, map(float, derivative)))),
            boundary,
        )

    def _evaluate(
        self,
        artifact_stats: Stats,
        set_counts: Mapping[str, int],
        main_stats: Mapping[str, str] | None,
        differentiate: bool,
    ) -> tuple[Evaluation, NDArray[np.float64] | None, bool]:
        artifact = _candidate_stats(artifact_stats)
        sets = dict(set_counts)
        if set(sets) - self.known_sets:
            raise EvaluationError(
                f"unknown candidate sets: {sorted(set(sets) - self.known_sets)}"
            )
        if (
            any(type(count) is not int or count < 0 for count in sets.values())
            or sum(sets.values()) > 5
        ):
            raise EvaluationError(
                "set counts must be nonnegative integers totaling at most five"
            )
        mains = dict(main_stats or {})
        for slot, key in mains.items():
            if slot not in LEGAL_MAINS or key not in LEGAL_MAINS[slot]:
                raise EvaluationError(f"illegal candidate main stat {slot}.{key}")
        definition = self.definition
        base = dict(definition.base)
        additions = {
            key: definition.buffs.get(key, 0) + artifact.get(key, 0)
            for key in STAT_KEYS
        }
        raw: dict[str, float] = {}
        effective: dict[str, float] = {}
        channels = {
            key: 0.0 if channel.combine == "add" else 1.0
            for key, channel in self.channels.items()
        }
        stats = base, raw, effective
        zero = np.zeros(len(STAT_KEYS), dtype=np.float64)
        addition_derivatives = (
            dict(zip(STAT_KEYS, np.eye(len(STAT_KEYS)))) if differentiate else {}
        )
        raw_derivatives: dict[str, NDArray[np.float64]] = {}
        effective_derivatives: dict[str, NDArray[np.float64]] = {}
        stat_derivatives: tuple[
            Mapping[str, NDArray[np.float64]],
            Mapping[str, NDArray[np.float64]],
            Mapping[str, NDArray[np.float64]],
        ] = (
            {},
            raw_derivatives,
            effective_derivatives,
        )
        channel_derivatives: dict[str, NDArray[np.float64]] = {}
        boundary = False
        for stage in (0, 1, 2):
            # Contributions accumulate separately: each conversion reads the same raw snapshot.
            contributions: dict[str, float] = {}
            contribution_derivatives: dict[str, NDArray[np.float64]] = {}
            for effect in self.effects:
                if effect.stage != stage:
                    continue
                if effect.when and not effect.when.evaluate(
                    definition.conditions, sets
                ):
                    continue
                if differentiate:
                    value, derivative, at_boundary = effect.program.differentiate(
                        stats, channels, stat_derivatives, channel_derivatives
                    )
                    boundary |= at_boundary
                else:
                    value = effect.program.evaluate(stats, channels)
                    derivative = zero
                kind, target = effect.target.split(".", 1)
                if kind == "stats":
                    contributions[target] = contributions.get(target, 0) + value
                    if differentiate:
                        contribution_derivatives[target] = (
                            contribution_derivatives.get(target, zero) + derivative
                        )
                elif self.channels[target].combine == "add":
                    channels[target] += value
                    if differentiate:
                        channel_derivatives[target] = (
                            channel_derivatives.get(target, zero) + derivative
                        )
                else:
                    if differentiate:
                        channel_derivatives[target] = (
                            channel_derivatives.get(target, zero) * value
                            + channels[target] * derivative
                        )
                    channels[target] *= value
            if stage == 0:
                for key in STAT_KEYS:
                    additions[key] += contributions.get(key, 0)
                    raw[key] = base.get(key, 0) + additions[key]
                    if differentiate:
                        addition_derivatives[key] = addition_derivatives[
                            key
                        ] + contribution_derivatives.get(key, zero)
                        raw_derivatives[key] = addition_derivatives[key]
                for key in PRIMARY_STATS:
                    if key in base:
                        raw[key] = base[key] * (1 + raw[f"{key}_"]) + additions[key]
                        if differentiate:
                            raw_derivatives[key] = (
                                base[key] * raw_derivatives[f"{key}_"]
                                + addition_derivatives[key]
                            )
            elif stage == 1:
                effective.update(
                    {
                        key: raw[key] + contributions.get(key, 0)
                        for key in STAT_KEYS
                        if key not in PRIMARY_STATS
                    }
                )
                if differentiate:
                    effective_derivatives.update(
                        {
                            key: raw_derivatives[key]
                            + contribution_derivatives.get(key, zero)
                            for key in STAT_KEYS
                            if key not in PRIMARY_STATS
                        }
                    )
                for key in PRIMARY_STATS:
                    if key in base:
                        effective[key] = (
                            base[key] * (1 + effective[f"{key}_"])
                            + additions[key]
                            + contributions.get(key, 0)
                        )
                        if differentiate:
                            effective_derivatives[key] = (
                                base[key] * effective_derivatives[f"{key}_"]
                                + addition_derivatives[key]
                                + contribution_derivatives.get(key, zero)
                            )
        if not all(
            math.isfinite(value)
            for values in (raw, effective, channels)
            for value in values.values()
        ):
            raise EvaluationError("nonfinite aggregated stat or channel")
        try:
            score_derivative = None
            if differentiate:
                score, score_derivative, at_boundary = self.score.differentiate(
                    stats, channels, stat_derivatives, channel_derivatives
                )
                boundary |= at_boundary
            else:
                score = self.score.evaluate(stats, channels)
        except EvaluationError as error:
            raise EvaluationError(f"{definition.id}: {error}") from error
        violations: list[str] = []
        for key, minimum in definition.minimums.items():
            if effective[key] < minimum and not math.isclose(
                effective[key], minimum, rel_tol=1e-12, abs_tol=1e-12
            ):
                violations.append(f"{key} below minimum {minimum}")
        for key, maximum in definition.maximums.items():
            if effective[key] > maximum and not math.isclose(
                effective[key], maximum, rel_tol=1e-12, abs_tol=1e-12
            ):
                violations.append(f"{key} above maximum {maximum}")
        if not any(
            all(sets.get(key, 0) >= count for key, count in strategy.items())
            for strategy in definition.sets
        ):
            violations.append("set composition does not match any allowed strategy")
        for slot, allowed in definition.mains.items():
            if slot not in mains:
                violations.append(f"missing main stat for {slot}")
            elif mains[slot] not in allowed:
                violations.append(f"main stat for {slot} is not allowed")
        result = Evaluation(
            score,
            MappingProxyType(effective),
            MappingProxyType(channels),
            tuple(violations),
        )
        return result, score_derivative, boundary


@dataclass(frozen=True, slots=True)
class CompiledLibrary:
    scenarios: Mapping[str, CompiledScenario]
    fingerprint: str
    mechanics: Mechanics
    draft: bool
    limitations: tuple[str, ...]

    def select(
        self, *, include_speculative: bool = False
    ) -> tuple[CompiledScenario, ...]:
        return tuple(
            scenario
            for scenario in self.scenarios.values()
            if include_speculative or scenario.definition.collection == "established"
        )
