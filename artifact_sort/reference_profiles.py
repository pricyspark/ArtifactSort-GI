"""Whole-slot dot-product calibration with explicit probability mass and ties."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import math
from types import MappingProxyType
from time import monotonic
from typing import TYPE_CHECKING, Sequence

import numpy as np
from numpy.typing import NDArray

from .formulas import Stats
from .artifact_sampling import SamplingRules, sample_slot
from .deletion_objective import Category
from .inventory import Artifact, Inventory, assemble_build
from .library_runtime import CompiledScenario, Linearization
from .model import STAT_KEYS
from .reference_contexts import ContextPortfolio

if TYPE_CHECKING:
    from .library_cache import AnalysisCache

PROFILE_PERCENTILES: MappingProxyType[Category, float] = MappingProxyType(
    {"ordinary": 0.8, "strong": 0.95, "exceptional": 0.99}
)


@dataclass(frozen=True, slots=True)
class ScorePopulation:
    artifacts: tuple[Artifact, ...]
    weights: Stats
    scores: NDArray[np.float64]
    probabilities: NDArray[np.float64]
    sorted_scores: NDArray[np.float64]
    cumulative: NDArray[np.float64]

    def quantile(self, percentile: float) -> Inventory:
        """Generalized inverse CDF, preserving the complete quantile tie group."""
        if not 0 < percentile <= 1:
            raise ValueError("percentile must satisfy 0 < percentile <= 1")
        index = int(np.searchsorted(self.cumulative[1:], percentile, side="left"))
        score = self.sorted_scores[index]
        return Inventory(
            tuple(a for a, value in zip(self.artifacts, self.scores) if value == score)
        )

    def quantile_interval(
        self, percentile: float, *, confidence: float = 0.95
    ) -> tuple[float, float]:
        """Order-statistic confidence bounds for independent whole-slot draws.

        Call only for IID unconditional populations, not stratified or selected
        samples. Equal masses are checked, but cannot establish independence.
        Infinite endpoints explicitly indicate insufficient tail observations.
        These bounds describe sampling uncertainty, not an allowed quality band.
        """
        from scipy.stats import binom

        if not 0 < percentile < 1 or not 0 < confidence < 1:
            raise ValueError(
                "percentile and confidence must be strictly between zero and one"
            )
        count = len(self.artifacts)
        if not np.all(self.probabilities == 1 / count):
            raise ValueError(
                "order-statistic bounds require IID equally weighted draws"
            )
        tail = (1 - confidence) / 2
        lower = int(binom.ppf(tail, count, percentile))
        upper = int(binom.ppf(1 - tail, count, percentile)) + 1
        return (
            float(self.sorted_scores[lower - 1]) if lower else -math.inf,
            float(self.sorted_scores[upper - 1]) if upper <= count else math.inf,
        )

    def percentile_interval(self, score: float) -> tuple[float, float]:
        """P(S < score), P(S <= score); no invented ranking inside tied mass."""
        if not math.isfinite(score):
            raise ValueError("score must be finite")
        left = int(np.searchsorted(self.sorted_scores, score, side="left"))
        right = int(np.searchsorted(self.sorted_scores, score, side="right"))
        return float(self.cumulative[left]), float(self.cumulative[right])

    def band(self, lower: float, upper: float) -> Inventory:
        """Select support overlapping a percentile band; tied groups stay intact.

        The entire group is returned, not one average vector or a fabricated
        percentile. Callers can subsequently choose diverse representatives.
        """
        if not 0 <= lower < upper <= 1:
            raise ValueError("percentile band must satisfy 0 <= lower < upper <= 1")
        selected = []
        for artifact, score in zip(self.artifacts, self.scores):
            left, right = self.percentile_interval(float(score))
            if left < upper and right > lower:
                selected.append(artifact)
        return Inventory(tuple(selected))


def score_population(
    population: Inventory,
    weights: Stats,
    *,
    probabilities: Sequence[float] | None = None,
) -> ScorePopulation:
    """One shared weight vector scores all mains, including their main values.

    Default mass is empirical 1/N for unconditional slot samples. Explicit masses
    support stratified sampling: each main's occurrence mass must be apportioned
    across its conditional samples by the caller, never normalized within mains.
    """
    artifacts = population.artifacts
    if not artifacts or len({a.slot for a in artifacts}) != 1:
        raise ValueError("population must be nonempty and contain one slot")
    if any(a.rarity != 5 or a.level != 20 for a in artifacts):
        raise ValueError("reference populations require completed five-star artifacts")
    if set(weights) - set(STAT_KEYS):
        raise ValueError("unknown scoring stat")
    vector = np.array([weights.get(key, 0) for key in STAT_KEYS], dtype=np.float64)
    if not np.all(np.isfinite(vector)):
        raise ValueError("weights must be finite")
    stat_maps = [a.stats for a in artifacts]
    stats = np.array(
        [[values.get(key, 0) for key in STAT_KEYS] for values in stat_maps],
        dtype=np.float64,
    )
    scores = stats @ vector
    mass = (
        np.full(len(artifacts), 1 / len(artifacts), dtype=np.float64)
        if probabilities is None
        else np.array(probabilities, dtype=np.float64, copy=True)
    )
    if (
        mass.shape != (len(artifacts),)
        or not np.all(np.isfinite(mass))
        or np.any(mass <= 0)
        or not math.isclose(float(mass.sum()), 1, rel_tol=1e-10)
    ):
        raise ValueError("probabilities must be positive finite masses totaling one")
    if not np.all(np.isfinite(scores)):
        raise ValueError("nonfinite population scores")
    order = np.argsort(scores, kind="stable")
    sorted_scores = scores[order]
    cumulative = np.concatenate(([0.0], np.cumsum(mass[order])))
    cumulative[-1] = 1
    for array in (scores, mass, sorted_scores, cumulative):
        array.setflags(write=False)
    return ScorePopulation(
        artifacts,
        MappingProxyType(dict(weights)),
        scores,
        mass,
        sorted_scores,
        cumulative,
    )


def calibrate_slot(
    population: Inventory,
    scenario: CompiledScenario,
    context: Inventory,
    *,
    probabilities: Sequence[float] | None = None,
) -> tuple[ScorePopulation, Linearization]:
    """Derive weights from a concrete legal surrounding build, then rank a slot.

    The returned linearization preserves constraint and branch-boundary evidence.
    Context selection remains explicit; this does not choose a context portfolio
    or certify that the surrogate preserves nonlinear rankings or set effects.
    """
    build = assemble_build(context.artifacts)
    local = scenario.linearize(
        build.stats, build.set_counts, main_stats=build.main_stats
    )
    return (
        score_population(population, local.weights, probabilities=probabilities),
        local,
    )


@dataclass(frozen=True, slots=True)
class QuantileEvidence:
    source: str
    context: int
    slot: str
    category: Category
    percentile: float
    score: float
    percentile_interval: tuple[float, float]
    confidence_interval: tuple[float, float]
    ties: int


@dataclass(frozen=True, slots=True)
class ReferenceProfiles:
    profiles: MappingProxyType[Category, tuple[Inventory, ...]]
    evidence: tuple[QuantileEvidence, ...]


def generate_reference_profiles(
    portfolio: ContextPortfolio,
    rules: SamplingRules,
    *,
    population_size: int = 1000,
    seed: int = 0,
    time_limit: float | None = None,
    cache: AnalysisCache | None = None,
) -> ReferenceProfiles:
    """Point quantiles of shared whole-slot populations; no band-width tuning.

    Set assignments come from each legal surrounding context. Profiles remain
    separate alternatives, including all ties in each slot. The 95% confidence
    intervals are diagnostics conditional on IID ordinary-drop assumptions;
    they never widen the quality profile. Population count is a precision setting.
    """
    if portfolio.sampling_fingerprint != rules.fingerprint:
        raise ValueError("contexts and profiles must use the same sampling rules")
    if type(population_size) is not int or population_size <= 0:
        raise ValueError("population_size must be a positive integer")
    if type(seed) is not int:
        raise ValueError("seed must be an integer")
    if time_limit is not None and (not math.isfinite(time_limit) or time_limit <= 0):
        raise ValueError("time_limit must be finite and positive")
    deadline = math.inf if time_limit is None else monotonic() + time_limit
    populations: dict[tuple[str, str], Inventory] = {}
    profiles: dict[Category, list[Inventory]] = {
        category: [] for category in PROFILE_PERCENTILES
    }
    seen: dict[Category, set[str]] = {
        category: set() for category in PROFILE_PERCENTILES
    }
    evidence = []
    for index, context in enumerate(portfolio.contexts):
        pieces: dict[Category, list[Artifact]] = {
            category: [] for category in PROFILE_PERCENTILES
        }
        for artifact in context.inventory.artifacts:
            if monotonic() >= deadline:
                raise TimeoutError("reference-profile generation did not finish")
            key = artifact.slot, artifact.set_key
            if key not in populations:
                payload = json.dumps(["whole-slot-profiles-1", seed, *key])
                entropy = int.from_bytes(sha256(payload.encode()).digest(), "big")
                populations[key] = (sample_slot if cache is None else cache.population)(
                    artifact.slot,
                    artifact.set_key,
                    population_size,
                    rules,
                    seed=entropy,
                )
            ranked = score_population(populations[key], context.linearization.weights)
            for category, percentile in PROFILE_PERCENTILES.items():
                selected = ranked.quantile(percentile)
                pieces[category].extend(selected.artifacts)
                # Use the actual vectorized ranking value, avoiding a different
                # floating-point reduction at a tied percentile boundary.
                selected_id = selected.artifacts[0].id
                score = float(
                    next(
                        value
                        for piece, value in zip(ranked.artifacts, ranked.scores)
                        if piece.id == selected_id
                    )
                )
                evidence.append(
                    QuantileEvidence(
                        context.source,
                        index,
                        artifact.slot,
                        category,
                        percentile,
                        score,
                        ranked.percentile_interval(score),
                        ranked.quantile_interval(percentile),
                        len(selected.artifacts),
                    )
                )
        for category in PROFILE_PERCENTILES:
            profile = Inventory(tuple(pieces[category]))
            fingerprint = profile.fingerprint()
            if fingerprint not in seen[category]:
                profiles[category].append(profile)
                seen[category].add(fingerprint)
    return ReferenceProfiles(
        MappingProxyType(
            {category: tuple(values) for category, values in profiles.items()}
        ),
        tuple(evidence),
    )
