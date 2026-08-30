from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Callable, Mapping, Protocol, Sequence

import numpy as np
from numpy.typing import NDArray

from .cache import ResultCache, cache_key
from .model import ArtifactBatch, SUBSTAT_MAX, cumulative_artifact_exp, load_good
from .optimizer import BuildOptimizer, DeletionAnalyzer
from .outcomes import sample_upgrade_tapes
from .scenarios import BuiltinEvaluator, Scenario, scenario_to_mapping
from .upgrades import UpgradeAnalyzer


@dataclass(frozen=True, slots=True)
class DeletionDecision:
    indices: tuple[int, ...]


class Policy(Protocol):
    name: str


class DeletionPolicy(Policy, Protocol):
    stochastic: bool

    def delete(
        self,
        batch: ArtifactBatch,
        scenarios: Sequence[Scenario],
        free: int,
        rng: np.random.Generator,
        *,
        cache: ResultCache | None = None,
    ) -> DeletionDecision:
        ...


def _lowest_unprotected(
    batch: ArtifactBatch, scores: NDArray[np.float64], free: int
) -> tuple[int, ...]:
    scores = scores.copy()
    scores[batch.protected_mask()] = np.inf
    candidates = np.flatnonzero(np.isfinite(scores))
    if free > len(candidates):
        raise ValueError("not enough unprotected artifacts")
    if free == 0:
        return ()
    chosen = candidates[np.argpartition(scores[candidates], free - 1)[:free]]
    chosen = chosen[np.argsort(scores[chosen])]
    return tuple(int(value) for value in chosen)


class RandomDeletionPolicy:
    name = "random"
    stochastic = True

    def delete(
        self,
        batch: ArtifactBatch,
        scenarios: Sequence[Scenario],
        free: int,
        rng: np.random.Generator,
        *,
        cache: ResultCache | None = None,
    ) -> DeletionDecision:
        scores = rng.random(len(batch))
        return DeletionDecision(_lowest_unprotected(batch, scores, free))


class CritValuePolicy:
    name = "crit-value"
    stochastic = False

    def delete(
        self,
        batch: ArtifactBatch,
        scenarios: Sequence[Scenario],
        free: int,
        rng: np.random.Generator,
        *,
        cache: ResultCache | None = None,
    ) -> DeletionDecision:
        scores = batch.sub_rolls[:, 8].astype(float) * 2.0 + batch.sub_rolls[:, 9]
        scores += np.count_nonzero(batch.sub_rolls, axis=1) * 1e-3
        return DeletionDecision(_lowest_unprotected(batch, scores, free))


class StaticWeightPolicy:
    """The prior row-scoring family, using scenario-local linear weights."""

    name = "greedy-linearized-score"
    stochastic = False

    def delete(
        self,
        batch: ArtifactBatch,
        scenarios: Sequence[Scenario],
        free: int,
        rng: np.random.Generator,
        *,
        cache: ResultCache | None = None,
    ) -> DeletionDecision:
        evaluator = BuiltinEvaluator()
        stats = batch.final_stats()
        representative = np.median(stats, axis=0)
        scores = np.full(len(batch), -np.inf)
        for scenario in scenarios:
            weights = evaluator.marginal_weights(representative, scenario)
            scores = np.maximum(scores, stats @ weights)
        return DeletionDecision(_lowest_unprotected(batch, scores, free))


class ArchetypeWeightPolicy:
    """Conservative max over common build archetypes."""

    name = "archetype-weight"
    stochastic = False

    def delete(
        self,
        batch: ArtifactBatch,
        scenarios: Sequence[Scenario],
        free: int,
        rng: np.random.Generator,
        *,
        cache: ResultCache | None = None,
    ) -> DeletionDecision:
        # These are screening weights in roll-coefficient space, matching the
        # family of ATK/HP/DEF/EM, crit, and ER targets used by the old backend.
        archetypes = np.zeros((8, 10), dtype=np.float64)
        for row, primary in enumerate((4, 3, 5, 7)):
            archetypes[row, primary] = 1.0
            archetypes[row, 8:10] = (2.0, 1.0)
        archetypes[4, [4, 6, 8, 9]] = (1.0, 0.8, 2.0, 1.0)
        archetypes[5, [3, 6, 8, 9]] = (1.0, 0.8, 2.0, 1.0)
        archetypes[6, [5, 6, 8, 9]] = (1.0, 0.8, 2.0, 1.0)
        archetypes[7, [6, 7]] = (1.0, 1.0)
        scores = np.max(batch.sub_rolls.astype(np.float64) @ archetypes.T, axis=1)
        return DeletionDecision(_lowest_unprotected(batch, scores, free))


class RecordedDeletionPolicy:
    """Replay an externally recorded deletion ordering as a benchmark."""

    name = "recorded-policy"
    stochastic = False

    def __init__(self, artifact_ids: Sequence[str]) -> None:
        self.artifact_ids = tuple(artifact_ids)

    def delete(
        self,
        batch: ArtifactBatch,
        scenarios: Sequence[Scenario],
        free: int,
        rng: np.random.Generator,
        *,
        cache: ResultCache | None = None,
    ) -> DeletionDecision:
        index = {str(key): i for i, key in enumerate(batch.ids)}
        ordered = [index[key] for key in self.artifact_ids if key in index]
        ordered = [i for i in ordered if not batch.protected_mask()[i]]
        if len(ordered) < free:
            raise ValueError("recorded ordering does not contain enough eligible artifacts")
        return DeletionDecision(tuple(ordered[:free]))


class PortfolioDeletionPolicy:
    stochastic = False

    def __init__(
        self,
        *,
        candidate_limit: int = 28,
        loadouts: int = 60,
        probability_floor: float = 0.01,
        upgrade_candidates: int = 24,
    ) -> None:
        self.candidate_limit = candidate_limit
        self.loadouts = loadouts
        self.probability_floor = probability_floor
        self.upgrade_candidates = upgrade_candidates
        self.name = f"portfolio-p{probability_floor:g}"

    def delete(
        self,
        batch: ArtifactBatch,
        scenarios: Sequence[Scenario],
        free: int,
        rng: np.random.Generator,
        *,
        cache: ResultCache | None = None,
    ) -> DeletionDecision:
        optimizer = BuildOptimizer(
            batch, candidate_limit=self.candidate_limit, cache=cache
        )
        option_values = UpgradeAnalyzer(
            optimizer,
            scenarios,
            probability_floor=self.probability_floor,
            complement_pool_size=80,
        ).option_values(max_candidates=self.upgrade_candidates)
        result = DeletionAnalyzer(
            optimizer, scenarios, loadouts_per_scenario=self.loadouts
        ).analyze(free, option_values=option_values)
        return DeletionDecision(result.deleted_indices)


def _scenario_hash(scenarios: Sequence[Scenario]) -> str:
    payload = [scenario_to_mapping(scenario) for scenario in scenarios]
    return sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()


def _deletion_policy_spec(policy: DeletionPolicy) -> dict[str, object] | None:
    policy_type = type(policy)
    if policy_type is RandomDeletionPolicy:
        return {"type": "random"}
    if policy_type is CritValuePolicy:
        return {"type": "crit-value"}
    if policy_type is ArchetypeWeightPolicy:
        return {"type": "archetype-weight"}
    if policy_type is StaticWeightPolicy:
        return {"type": "greedy-linearized-score"}
    if policy_type is RecordedDeletionPolicy:
        return {
            "type": "recorded-policy",
            "artifact_ids": list(policy.artifact_ids),
        }
    if policy_type is PortfolioDeletionPolicy:
        return {
            "type": "portfolio",
            "candidate_limit": policy.candidate_limit,
            "loadouts": policy.loadouts,
            "probability_floor": policy.probability_floor,
            "upgrade_candidates": policy.upgrade_candidates,
        }
    return None


def _cached_deletion_decision(
    policy: DeletionPolicy,
    batch: ArtifactBatch,
    scenarios: Sequence[Scenario],
    free: int,
    rng: np.random.Generator,
    cache: ResultCache | None,
) -> tuple[DeletionDecision, bool]:
    spec = _deletion_policy_spec(policy)
    key = None
    if cache is not None and spec is not None:
        key = cache_key(
            artifact_fingerprint=batch.fingerprint(),
            scenario_hash=_scenario_hash(scenarios),
            evaluator_version=BuiltinEvaluator.version,
            parameters={
                "kind": "benchmark-deletion-decision",
                "benchmark_version": 2,
                "free": free,
                "policy": spec,
            },
        )
        found = cache.get("benchmark-deletion-decision", key)
        if isinstance(found, Mapping):
            indices = found.get("indices")
            if isinstance(indices, list) and len(indices) == free:
                try:
                    decision = DeletionDecision(tuple(int(index) for index in indices))
                except (TypeError, ValueError):
                    pass
                else:
                    return decision, True

    decision = policy.delete(batch, scenarios, free, rng, cache=cache)
    if cache is not None and key is not None:
        cache.put(
            "benchmark-deletion-decision",
            key,
            {"indices": list(decision.indices)},
        )
    return decision, False


@dataclass(frozen=True, slots=True)
class PolicyDeletionTrial:
    policy: str
    seed: int
    slots_freed: int
    first_punished_deletion: int | None
    oracle_build_deletion_fraction: float
    median_regret: float
    p95_regret: float
    worst_regret: float
    current_regret: float
    speculative_regret: float
    lost_set_options: int
    replacement_depth: float
    regret_curve: tuple[tuple[int, float], ...]


@dataclass(frozen=True, slots=True)
class ConfidenceInterval:
    estimate: float
    low: float
    high: float


@dataclass(frozen=True, slots=True)
class DeletionBenchmark:
    trials: tuple[PolicyDeletionTrial, ...]
    confidence: dict[str, dict[str, ConfidenceInterval]]
    seeds: tuple[int, ...]


def _rounded(value: float, digits: int = 6) -> float:
    return round(float(value), digits)


def _percent(value: float) -> float:
    return _rounded(100.0 * value)


def _percent_interval(interval: ConfidenceInterval) -> dict[str, float]:
    return {
        "estimate": _percent(interval.estimate),
        "low": _percent(interval.low),
        "high": _percent(interval.high),
    }


def summarize_deletion_benchmark(
    benchmark: DeletionBenchmark,
    calibration_scenarios: Sequence[Scenario] = (),
    heldout_scenarios: Sequence[Scenario] = (),
) -> dict[str, object]:
    """Create a compact, human-oriented view of a deletion benchmark."""

    grouped = {
        policy: [trial for trial in benchmark.trials if trial.policy == policy]
        for policy in benchmark.confidence
    }
    summaries: list[dict[str, object]] = []
    ranking_values: dict[str, tuple[float, ...]] = {}
    for policy, trials in grouped.items():
        if not trials:
            continue
        punished = [
            trial.first_punished_deletion
            for trial in trials
            if trial.first_punished_deletion is not None
        ]
        confidence = benchmark.confidence[policy]
        punished_rate = len(punished) / len(trials)
        current_regret = float(np.mean([trial.current_regret for trial in trials]))
        speculative_regret = float(
            np.mean([trial.speculative_regret for trial in trials])
        )
        worst_regret = float(np.mean([trial.worst_regret for trial in trials]))
        near_best_fraction = float(
            np.mean([trial.oracle_build_deletion_fraction for trial in trials])
        )
        summaries.append(
            {
                "policy": policy,
                "rank": None,
                "trials": len(trials),
                "mean_current_regret_pct": _percent(current_regret),
                "mean_speculative_regret_pct": _percent(speculative_regret),
                "mean_worst_regret_pct": _percent(worst_regret),
                "max_observed_worst_regret_pct": _percent(
                    max(trial.worst_regret for trial in trials)
                ),
                "worst_regret_mean_95_ci_pct": _percent_interval(
                    confidence["worst_regret"]
                ),
                "punished_trials": len(punished),
                "punished_trial_rate_pct": _percent(punished_rate),
                "earliest_punished_deletion": min(punished) if punished else None,
                "median_first_punished_deletion": (
                    _rounded(float(np.median(punished)), 1) if punished else None
                ),
                "mean_near_best_artifacts_deleted_pct": _percent(
                    near_best_fraction
                ),
                "near_best_deletion_mean_95_ci_pct": _percent_interval(
                    confidence["oracle_build_deletion_fraction"]
                ),
                "trials_deleting_any_near_best_artifact": sum(
                    trial.oracle_build_deletion_fraction > 0 for trial in trials
                ),
                "mean_lost_set_options": _rounded(
                    float(np.mean([trial.lost_set_options for trial in trials]))
                ),
                "max_lost_set_options": max(
                    trial.lost_set_options for trial in trials
                ),
                "mean_replacement_depth": _rounded(
                    float(np.mean([trial.replacement_depth for trial in trials]))
                ),
            }
        )
        ranking_values[policy] = (
            current_regret,
            speculative_regret,
            confidence["worst_regret"].high,
            near_best_fraction,
            punished_rate,
        )

    ranked = sorted(
        (
            summary
            for summary in summaries
            if summary["policy"] != "clairvoyant-oracle"
        ),
        key=lambda summary: (
            ranking_values[str(summary["policy"])],
            str(summary["policy"]),
        ),
    )
    for rank, summary in enumerate(ranked, start=1):
        summary["rank"] = rank
    summaries.sort(
        key=lambda summary: (
            summary["rank"] is None,
            summary["rank"] if summary["rank"] is not None else 0,
        )
    )
    portfolio = next(
        (
            summary
            for summary in ranked
            if str(summary["policy"]).startswith("portfolio-")
        ),
        None,
    )
    slots_freed = benchmark.trials[0].slots_freed if benchmark.trials else 0
    return {
        "benchmark": "deletion",
        "status": "descriptive-only",
        "trials": len(benchmark.seeds),
        "slots_freed": slots_freed,
        "calibration_scenarios": [
            scenario.id for scenario in calibration_scenarios
        ],
        "heldout_scenarios": [scenario.id for scenario in heldout_scenarios],
        "lowest_observed_risk_policy": (
            str(ranked[0]["policy"]) if ranked else None
        ),
        "lowest_observed_risk_portfolio_policy": (
            str(portfolio["policy"]) if portfolio is not None else None
        ),
        "ranking_basis": [
            "mean current-scenario regret",
            "mean speculative-scenario regret",
            "upper 95% confidence bound for mean worst regret",
            "fraction of deleted artifacts belonging to near-best oracle builds",
            "fraction of trials with a punished deletion",
        ],
        "policies": summaries,
        "notes": [
            "All regret values are percentages; lower is better.",
            "A punished deletion removes an artifact from an oracle-best or 1%-near-best build.",
            "Ranks describe only these scenarios and sampled trials; they are not proof of universal policy superiority.",
            "The clairvoyant oracle is an unattainable reference and is not ranked.",
        ],
    }


def _deletion_trial_from_mapping(value: object) -> PolicyDeletionTrial | None:
    if not isinstance(value, Mapping):
        return None
    try:
        curve = tuple(
            (int(point[0]), float(point[1])) for point in value["regret_curve"]
        )
        first = value["first_punished_deletion"]
        return PolicyDeletionTrial(
            policy=str(value["policy"]),
            seed=int(value["seed"]),
            slots_freed=int(value["slots_freed"]),
            first_punished_deletion=None if first is None else int(first),
            oracle_build_deletion_fraction=float(
                value["oracle_build_deletion_fraction"]
            ),
            median_regret=float(value["median_regret"]),
            p95_regret=float(value["p95_regret"]),
            worst_regret=float(value["worst_regret"]),
            current_regret=float(value["current_regret"]),
            speculative_regret=float(value["speculative_regret"]),
            lost_set_options=int(value["lost_set_options"]),
            replacement_depth=float(value["replacement_depth"]),
            regret_curve=curve,
        )
    except (KeyError, TypeError, ValueError):
        return None


def _deletion_trial_key(
    batch: ArtifactBatch,
    calibration_scenarios: Sequence[Scenario],
    heldout_scenarios: Sequence[Scenario],
    policies: Sequence[DeletionPolicy],
    *,
    free: int,
    curve_points: int,
    seed_state: Mapping[str, object],
) -> str | None:
    specs = [_deletion_policy_spec(policy) for policy in policies]
    if any(spec is None for spec in specs):
        return None
    return cache_key(
        artifact_fingerprint=batch.fingerprint(),
        scenario_hash=_scenario_hash(
            tuple(calibration_scenarios) + tuple(heldout_scenarios)
        ),
        evaluator_version=BuiltinEvaluator.version,
        parameters={
            "kind": "benchmark-deletion-trial",
            "benchmark_version": 2,
            "calibration_scenarios": _scenario_hash(calibration_scenarios),
            "heldout_scenarios": _scenario_hash(heldout_scenarios),
            "policies": specs,
            "free": free,
            "curve_points": curve_points,
            "seed_state": dict(seed_state),
        },
    )


@dataclass(frozen=True, slots=True)
class HistoricalScan:
    timestamp: str
    path: str
    batch: ArtifactBatch


@dataclass(frozen=True, slots=True)
class HistoricalReplayEvent:
    policy: str
    from_timestamp: str
    to_timestamp: str
    deleted: int
    deleted_ids_seen_again: int
    future_best_build_hits: int


def load_historical_scans(paths: Sequence[str | Path]) -> list[HistoricalScan]:
    scans = []
    for ordinal, path in enumerate(paths):
        batch, data = load_good(path)
        timestamp = str(
            data.get("timestamp")
            or data.get("exportDate")
            or data.get("lastUpdate")
            or f"undated-{ordinal:06d}"
        )
        scans.append(HistoricalScan(timestamp, str(path), batch))
    return sorted(scans, key=lambda scan: scan.timestamp)


def replay_historical_deletions(
    scans: Sequence[HistoricalScan],
    scenarios: Sequence[Scenario],
    policies: Sequence[DeletionPolicy],
    *,
    free: int,
    seed: int = 0,
) -> tuple[HistoricalReplayEvent, ...]:
    """Replay decisions against the next timestamped scan without hidden access."""

    if len(scans) < 2:
        raise ValueError("historical replay needs at least two scans")
    events: list[HistoricalReplayEvent] = []
    for scan_index, (current, future) in enumerate(zip(scans, scans[1:])):
        future_optimizer = BuildOptimizer(future.batch, candidate_limit=36)
        future_best_ids = {
            str(future.batch.ids[index])
            for scenario in scenarios
            for result in future_optimizer.optimize(
                scenario, include_unfinished=True, top_k=1
            )
            for index in result.indices
        }
        future_ids = set(str(value) for value in future.batch.ids)
        for policy_index, policy in enumerate(policies):
            rng = np.random.default_rng(seed + scan_index * 1009 + policy_index * 1_000_003)
            decision = policy.delete(current.batch, scenarios, free, rng)
            deleted_ids = {str(current.batch.ids[index]) for index in decision.indices}
            events.append(
                HistoricalReplayEvent(
                    policy.name,
                    current.timestamp,
                    future.timestamp,
                    len(deleted_ids),
                    len(deleted_ids & future_ids),
                    len(deleted_ids & future_best_ids),
                )
            )
    return tuple(events)


def _hidden_stats(
    batch: ArtifactBatch, tapes: Sequence[Sequence[tuple[int, int]]]
) -> NDArray[np.float64]:
    rolls = _hidden_rolls(batch, tapes)
    stats = batch.final_stats()
    roll_delta = rolls.astype(np.float64) - batch.sub_rolls.astype(np.float64)
    stats[:, :10] += roll_delta * (SUBSTAT_MAX / 10.0)
    return stats


def _hidden_rolls(
    batch: ArtifactBatch, tapes: Sequence[Sequence[tuple[int, int]]]
) -> NDArray[np.uint8]:
    rolls = batch.sub_rolls.copy()
    for index, tape in enumerate(tapes):
        for stat, increment in tape:
            rolls[index, stat] += increment
    return rolls


def _bootstrap_interval(
    values: Sequence[float], rng: np.random.Generator, samples: int = 1000
) -> ConfidenceInterval:
    array = np.asarray(values, dtype=np.float64)
    estimate = float(np.mean(array))
    if len(array) < 2:
        return ConfidenceInterval(estimate, estimate, estimate)
    means = np.mean(rng.choice(array, size=(samples, len(array)), replace=True), axis=1)
    low, high = np.quantile(means, (0.025, 0.975))
    return ConfidenceInterval(estimate, float(low), float(high))


def benchmark_deletion(
    batch: ArtifactBatch,
    calibration_scenarios: Sequence[Scenario],
    heldout_scenarios: Sequence[Scenario],
    policies: Sequence[DeletionPolicy],
    *,
    free: int,
    trials: int = 20,
    seed: int = 0,
    curve_points: int = 12,
    cache: ResultCache | None = None,
    progress: Callable[[str], None] | None = None,
) -> DeletionBenchmark:
    scenarios = tuple(calibration_scenarios) + tuple(heldout_scenarios)
    if not scenarios:
        raise ValueError("at least one calibration or held-out scenario is required")
    if trials <= 0:
        raise ValueError("trials must be positive")
    if free < 0:
        raise ValueError("free must be non-negative")
    if curve_points <= 0:
        raise ValueError("curve_points must be positive")
    seed_sequence = np.random.SeedSequence(seed)
    child_seeds = seed_sequence.spawn(trials)
    output: list[PolicyDeletionTrial] = []

    expected_policies = [policy.name for policy in policies] + ["clairvoyant-oracle"]
    trial_keys = [
        _deletion_trial_key(
            batch,
            calibration_scenarios,
            heldout_scenarios,
            policies,
            free=free,
            curve_points=curve_points,
            seed_state=child.state,
        )
        if cache is not None
        else None
        for child in child_seeds
    ]
    cached_trials: dict[int, tuple[PolicyDeletionTrial, ...]] = {}
    if cache is not None:
        for trial_index, (child, key) in enumerate(zip(child_seeds, trial_keys)):
            if key is None:
                continue
            found = cache.get("benchmark-deletion-trial", key)
            if not isinstance(found, Mapping) or not isinstance(found.get("rows"), list):
                continue
            restored = tuple(
                row
                for value in found["rows"]
                if (row := _deletion_trial_from_mapping(value)) is not None
            )
            trial_seed = int(child.generate_state(1)[0])
            if (
                len(restored) == len(expected_policies)
                and [row.policy for row in restored] == expected_policies
                and all(row.seed == trial_seed for row in restored)
            ):
                cached_trials[trial_index] = restored

    fixed_decisions: dict[int, DeletionDecision] = {}
    if len(cached_trials) < trials:
        first_seed = int(child_seeds[0].generate_state(1)[0])
        for policy_index, policy in enumerate(policies):
            if getattr(policy, "stochastic", True):
                continue
            if progress is not None:
                progress(f"preparing deterministic policy {policy.name}")
            policy_rng = np.random.default_rng(
                first_seed + policy_index * 1_000_003
            )
            decision, found = _cached_deletion_decision(
                policy,
                batch,
                calibration_scenarios,
                free,
                policy_rng,
                cache,
            )
            fixed_decisions[policy_index] = decision
            if progress is not None and found:
                progress(f"reused cached decision for {policy.name}")

    for trial_index, child in enumerate(child_seeds):
        trial_seed = int(child.generate_state(1)[0])
        cached_trial = cached_trials.get(trial_index)
        if cached_trial is not None:
            output.extend(cached_trial)
            if progress is not None:
                progress(f"trial {trial_index + 1}/{trials}: reused cached result")
            continue
        if progress is not None:
            progress(f"trial {trial_index + 1}/{trials}: simulating")
        tape_rng = np.random.default_rng(child)
        tapes = sample_upgrade_tapes(batch, tape_rng)
        hidden_rolls = _hidden_rolls(batch, tapes)
        hidden_levels = np.where(batch.rarities == 5, 20, batch.levels).astype(
            np.uint8
        )
        hidden_batch = batch.with_states(
            sub_rolls=hidden_rolls, levels=hidden_levels
        )
        oracle_optimizer = BuildOptimizer(hidden_batch, candidate_limit=40)
        oracle_pools = [
            oracle_optimizer.optimize(scenario, top_k=80)
            for scenario in scenarios
        ]
        if any(not pool for pool in oracle_pools):
            missing = scenarios[next(i for i, pool in enumerate(oracle_pools) if not pool)].id
            raise ValueError(f"scenario {missing!r} has no legal build in simulation")
        baselines = np.asarray([pool[0].utility for pool in oracle_pools])
        oracle_members = {
            index
            for baseline, pool in zip(baselines, oracle_pools)
            for build in pool[:20]
            if build.utility >= (1.0 - 0.01) * baseline
            for index in build.indices
        }

        # The unattainable upper bound sees every hidden tape and the held-out
        # scenarios. It still obeys the same protection and exact-size rules.
        clairvoyant = DeletionAnalyzer(
            oracle_optimizer,
            scenarios,
            loadouts_per_scenario=80,
        ).analyze(free)
        trial_policies: list[tuple[str, DeletionDecision]] = []

        for policy_index, policy in enumerate(policies):
            decision = fixed_decisions.get(policy_index)
            if decision is None:
                policy_rng = np.random.default_rng(
                    trial_seed + policy_index * 1_000_003
                )
                decision = policy.delete(
                    batch,
                    calibration_scenarios,
                    free,
                    policy_rng,
                    cache=cache,
                )
            trial_policies.append((policy.name, decision))
        trial_policies.append(
            ("clairvoyant-oracle", DeletionDecision(clairvoyant.deleted_indices))
        )

        trial_rows: list[PolicyDeletionTrial] = []
        for policy_name, decision in trial_policies:
            deleted = np.asarray(decision.indices, dtype=np.int64)
            if len(deleted) != free or len(np.unique(deleted)) != free:
                raise ValueError(f"policy {policy_name} did not delete exactly {free} artifacts")
            if np.any(batch.protected_mask()[deleted]):
                raise ValueError(f"policy {policy_name} deleted a protected artifact")
            first_punished = next(
                (rank for rank, index in enumerate(deleted, start=1) if int(index) in oracle_members),
                None,
            )
            member_fraction = (
                float(np.count_nonzero(np.isin(deleted, tuple(oracle_members))) / free)
                if free
                else 0.0
            )
            checkpoints = np.unique(
                np.linspace(1, free, min(curve_points, free), dtype=np.int64)
                if free
                else np.asarray((0,), dtype=np.int64)
            )
            curve: list[tuple[int, float]] = []
            final_regrets = np.zeros(len(scenarios), dtype=np.float64)
            for checkpoint in checkpoints:
                available = np.ones(len(batch), dtype=np.bool_)
                available[deleted[:checkpoint]] = False
                retained_values = []
                for scenario_index, scenario in enumerate(scenarios):
                    best = oracle_pools[scenario_index][0]
                    if np.all(available[np.asarray(best.indices, dtype=np.int64)]):
                        retained_values.append(baselines[scenario_index])
                        continue
                    retained = oracle_optimizer.optimize(
                        scenario, available=available, top_k=1
                    )
                    retained_values.append(
                        retained[0].utility if retained else -np.inf
                    )
                retained_array = np.asarray(retained_values)
                regrets = np.where(
                    baselines > 0,
                    np.clip(1.0 - retained_array / baselines, 0.0, 1.0),
                    0.0,
                )
                curve.append((int(checkpoint), float(np.max(regrets))))
                if checkpoint == checkpoints[-1]:
                    final_regrets = regrets

            lost_sets = sum(
                len({str(batch.set_keys[index]) for index in build.indices if index in deleted})
                for pool in oracle_pools
                for build in pool[:1]
            )
            depth = []
            for index in oracle_members:
                same = (
                    (batch.slots == batch.slots[index])
                    & (batch.set_keys == batch.set_keys[index])
                    & (batch.main_stats == batch.main_stats[index])
                )
                same[deleted] = False
                depth.append(int(np.count_nonzero(same)))
            current_mask = np.asarray([s.tier == "current" for s in scenarios])
            speculative_mask = ~current_mask
            trial_rows.append(
                PolicyDeletionTrial(
                    policy_name,
                    trial_seed,
                    free,
                    first_punished,
                    member_fraction,
                    float(np.median(final_regrets)),
                    float(np.quantile(final_regrets, 0.95)),
                    float(np.max(final_regrets)),
                    float(np.max(final_regrets[current_mask], initial=0.0)),
                    float(np.max(final_regrets[speculative_mask], initial=0.0)),
                    lost_sets,
                    float(np.mean(depth)) if depth else 0.0,
                    tuple(curve),
                )
            )

        output.extend(trial_rows)
        key = trial_keys[trial_index]
        if cache is not None and key is not None:
            cache.put(
                "benchmark-deletion-trial",
                key,
                {"rows": [asdict(row) for row in trial_rows]},
            )
        if progress is not None:
            progress(f"trial {trial_index + 1}/{trials}: complete")

    interval_rng = np.random.default_rng(seed ^ 0xA5A5A5A5)
    confidence: dict[str, dict[str, ConfidenceInterval]] = {}
    policy_names = [policy.name for policy in policies] + ["clairvoyant-oracle"]
    for policy_name in policy_names:
        rows = [trial for trial in output if trial.policy == policy_name]
        confidence[policy_name] = {
            "median_regret": _bootstrap_interval(
                [row.median_regret for row in rows], interval_rng
            ),
            "worst_regret": _bootstrap_interval(
                [row.worst_regret for row in rows], interval_rng
            ),
            "oracle_build_deletion_fraction": _bootstrap_interval(
                [row.oracle_build_deletion_fraction for row in rows], interval_rng
            ),
        }
    return DeletionBenchmark(
        tuple(output), confidence, tuple(int(seed.generate_state(1)[0]) for seed in child_seeds)
    )


class UpgradePolicy(Protocol):
    name: str

    def choose(
        self,
        batch: ArtifactBatch,
        scenarios: Sequence[Scenario],
        rng: np.random.Generator,
    ) -> int | None:
        ...


class RandomUpgradePolicy:
    name = "random"

    def choose(
        self,
        batch: ArtifactBatch,
        scenarios: Sequence[Scenario],
        rng: np.random.Generator,
    ) -> int | None:
        candidates = np.flatnonzero((batch.rarities == 5) & (batch.levels < 20))
        return int(rng.choice(candidates)) if len(candidates) else None


class CritValueUpgradePolicy:
    name = "crit-value"

    def choose(
        self,
        batch: ArtifactBatch,
        scenarios: Sequence[Scenario],
        rng: np.random.Generator,
    ) -> int | None:
        candidates = np.flatnonzero((batch.rarities == 5) & (batch.levels < 20))
        if not len(candidates):
            return None
        score = batch.sub_rolls[:, 8].astype(float) * 2 + batch.sub_rolls[:, 9]
        return int(candidates[np.argmax(score[candidates])])


class PortfolioUpgradePolicy:
    name = "portfolio"

    def choose(
        self,
        batch: ArtifactBatch,
        scenarios: Sequence[Scenario],
        rng: np.random.Generator,
    ) -> int | None:
        optimizer = BuildOptimizer(batch, candidate_limit=20, beam_width=2500)
        recommendations = UpgradeAnalyzer(
            optimizer, scenarios, complement_pool_size=60
        ).analyze(max_candidates=12)
        return recommendations[0].index if recommendations else None


@dataclass(frozen=True, slots=True)
class UpgradeTrial:
    policy: str
    seed: int
    exp_cost: float
    mora_cost: float
    resin_cost: float | None
    exp_to_progress: float | None
    exp_to_perfect: float | None
    checkpoints: int
    reached_perfect: bool
    reached_progress: bool
    oracle_fraction: float
    abandoned_exp_by_level: tuple[tuple[int, int], ...]


@dataclass(frozen=True, slots=True)
class UpgradeBenchmark:
    trials: tuple[UpgradeTrial, ...]
    confidence: dict[str, dict[str, ConfidenceInterval]]
    calibration: tuple[UpgradeCalibrationBin, ...]
    progress_target: float
    resin_per_exp: float | None


@dataclass(frozen=True, slots=True)
class UpgradeCalibrationBin:
    lower: float
    upper: float
    count: int
    mean_predicted: float | None
    observed_frequency: float | None


def summarize_upgrade_benchmark(
    benchmark: UpgradeBenchmark,
    scenarios: Sequence[Scenario] = (),
) -> dict[str, object]:
    """Create a compact, human-oriented view of an upgrade benchmark."""

    policy_names = list(benchmark.confidence)
    summaries: list[dict[str, object]] = []
    for policy in policy_names:
        trials = [trial for trial in benchmark.trials if trial.policy == policy]
        if not trials:
            continue
        confidence = benchmark.confidence[policy]
        progress_costs = [
            trial.exp_to_progress
            for trial in trials
            if trial.exp_to_progress is not None
        ]
        perfect_costs = [
            trial.exp_to_perfect
            for trial in trials
            if trial.exp_to_perfect is not None
        ]
        summaries.append(
            {
                "policy": policy,
                "rank": None,
                "trials": len(trials),
                "mean_exp_cost": _rounded(
                    float(np.mean([trial.exp_cost for trial in trials])), 1
                ),
                "mean_mora_cost": _rounded(
                    float(np.mean([trial.mora_cost for trial in trials])), 1
                ),
                "mean_resin_cost": (
                    _rounded(
                        float(
                            np.mean(
                                [
                                    trial.resin_cost
                                    for trial in trials
                                    if trial.resin_cost is not None
                                ]
                            )
                        ),
                        2,
                    )
                    if any(trial.resin_cost is not None for trial in trials)
                    else None
                ),
                "progress_success_rate_pct": _percent(
                    float(np.mean([trial.reached_progress for trial in trials]))
                ),
                "perfect_success_rate_pct": _percent(
                    float(np.mean([trial.reached_perfect for trial in trials]))
                ),
                "mean_exp_to_progress_when_reached": (
                    _rounded(float(np.mean(progress_costs)), 1)
                    if progress_costs
                    else None
                ),
                "mean_exp_to_perfect_when_reached": (
                    _rounded(float(np.mean(perfect_costs)), 1)
                    if perfect_costs
                    else None
                ),
                "mean_oracle_utility_pct": _percent(
                    float(np.mean([trial.oracle_fraction for trial in trials]))
                ),
                "exp_cost_mean_95_ci": {
                    "estimate": _rounded(confidence["exp_cost"].estimate, 1),
                    "low": _rounded(confidence["exp_cost"].low, 1),
                    "high": _rounded(confidence["exp_cost"].high, 1),
                },
                "oracle_utility_mean_95_ci_pct": _percent_interval(
                    confidence["oracle_fraction"]
                ),
            }
        )

    summaries.sort(
        key=lambda summary: (
            -float(summary["progress_success_rate_pct"]),
            -float(summary["perfect_success_rate_pct"]),
            -float(summary["mean_oracle_utility_pct"]),
            float(summary["mean_exp_cost"]),
            str(summary["policy"]),
        )
    )
    for rank, summary in enumerate(summaries, start=1):
        summary["rank"] = rank
    calibration = [
        {
            "range": [calibration_bin.lower, calibration_bin.upper],
            "count": calibration_bin.count,
            "mean_predicted_pct": (
                _percent(calibration_bin.mean_predicted)
                if calibration_bin.mean_predicted is not None
                else None
            ),
            "observed_frequency_pct": (
                _percent(calibration_bin.observed_frequency)
                if calibration_bin.observed_frequency is not None
                else None
            ),
        }
        for calibration_bin in benchmark.calibration
        if calibration_bin.count
    ]
    return {
        "benchmark": "upgrade",
        "status": "descriptive-only",
        "trials": len({trial.seed for trial in benchmark.trials}),
        "progress_target_pct": _percent(benchmark.progress_target),
        "scenarios": [scenario.id for scenario in scenarios],
        "highest_observed_progress_policy": (
            str(summaries[0]["policy"]) if summaries else None
        ),
        "policies": summaries,
        "calibration": calibration,
        "notes": [
            "Higher success and oracle-utility percentages are better; lower resource costs are better.",
            "Resource-cost averages include the full simulated stopping path.",
            "Ranks describe only these scenarios and sampled trials.",
        ],
    }


def _portfolio_utility(
    batch: ArtifactBatch,
    scenarios: Sequence[Scenario],
    *,
    stats: NDArray[np.float64] | None = None,
    include_unfinished: bool = False,
) -> float:
    optimizer = BuildOptimizer(batch, candidate_limit=32, beam_width=4000)
    values = []
    for scenario in scenarios:
        result = optimizer.optimize(
            scenario,
            stats=stats,
            include_unfinished=include_unfinished,
            top_k=1,
        )
        if result:
            values.append(result[0].utility)
    return float(np.mean(values)) if values else 0.0


def benchmark_upgrades(
    batch: ArtifactBatch,
    scenarios: Sequence[Scenario],
    policies: Sequence[UpgradePolicy],
    *,
    trials: int = 20,
    seed: int = 0,
    progress_target: float = 0.05,
    max_checkpoints: int = 300,
    resin_per_exp: float | None = None,
    exp_multiplier_values: Sequence[float] = (1.0, 2.0, 5.0),
    exp_multiplier_probabilities: Sequence[float] = (0.9, 0.09, 0.01),
    calibration_candidates: int = 4,
) -> UpgradeBenchmark:
    if not scenarios:
        raise ValueError("at least one scenario is required")
    if trials <= 0:
        raise ValueError("trials must be positive")
    seed_sequence = np.random.SeedSequence(seed)
    child_seeds = seed_sequence.spawn(trials)
    rows: list[UpgradeTrial] = []
    calibration_predictions: list[float] = []
    calibration_observations: list[float] = []
    calibration_items = UpgradeAnalyzer(
        BuildOptimizer(batch, candidate_limit=20, beam_width=2500),
        scenarios,
        complement_pool_size=60,
    ).analyze(max_candidates=calibration_candidates)
    visible_baselines = {
        scenario.id: BuildOptimizer(batch, candidate_limit=24)
        .optimize(scenario, top_k=1)[0]
        .utility
        for scenario in scenarios
    }
    for child in child_seeds:
        trial_seed = int(child.generate_state(1)[0])
        tape_rng = np.random.default_rng(child)
        tapes = sample_upgrade_tapes(batch, tape_rng)
        hidden = _hidden_stats(batch, tapes)
        oracle = _portfolio_utility(
            batch, scenarios, stats=hidden, include_unfinished=True
        )
        baseline = _portfolio_utility(batch, scenarios)
        multipliers = tape_rng.choice(
            np.asarray(exp_multiplier_values, dtype=float),
            size=max_checkpoints,
            p=np.asarray(exp_multiplier_probabilities, dtype=float),
        )

        hidden_optimizer = BuildOptimizer(batch, candidate_limit=24, beam_width=3000)
        for item in calibration_items:
            observed = False
            for scenario in scenarios:
                forced = hidden_optimizer.optimize(
                    scenario,
                    stats=hidden,
                    include_unfinished=True,
                    forced_index=item.index,
                    top_k=1,
                )
                if forced and forced[0].utility >= 0.99 * visible_baselines[scenario.id]:
                    observed = True
                    break
            calibration_predictions.append(item.useful_probability)
            calibration_observations.append(float(observed))

        for policy_index, policy in enumerate(policies):
            levels = batch.levels.copy()
            rolls = batch.sub_rolls.copy()
            tape_positions = np.zeros(len(batch), dtype=np.int16)
            visible = batch.with_states(levels=levels, sub_rolls=rolls)
            rng = np.random.default_rng(trial_seed + policy_index * 1_000_003)
            exp_cost = 0.0
            reached_perfect = baseline >= oracle * (1.0 - 1e-9)
            reached_progress = baseline >= baseline * (1.0 + progress_target)
            exp_to_progress = 0.0 if reached_progress else None
            exp_to_perfect = 0.0 if reached_perfect else None
            achieved = baseline
            checkpoints = 0
            while checkpoints < max_checkpoints and not reached_perfect:
                index = policy.choose(visible, scenarios, rng)
                if index is None or levels[index] >= 20:
                    break
                old_level = int(levels[index])
                new_level = min(20, ((old_level // 4) + 1) * 4)
                raw_cost = cumulative_artifact_exp(new_level) - cumulative_artifact_exp(old_level)
                exp_cost += raw_cost / float(multipliers[checkpoints])
                levels[index] = new_level
                tape_position = int(tape_positions[index])
                # A three-line +0 piece reveals its known fourth line at +4;
                # only subsequent checkpoints consume random tape entries.
                consumes_roll = not (
                    old_level == 0
                    and batch.starting_lines[index] == 3
                    and not (
                        batch.uncertain_history[index]
                        and batch.four_line_probability[index] >= 0.5
                    )
                )
                if consumes_roll and tape_position < len(tapes[index]):
                    stat, increment = tapes[index][tape_position]
                    rolls[index, stat] += increment
                    tape_positions[index] += 1
                visible = batch.with_states(levels=levels, sub_rolls=rolls)
                achieved = _portfolio_utility(visible, scenarios)
                if not reached_progress and achieved >= baseline * (1.0 + progress_target):
                    reached_progress = True
                    exp_to_progress = exp_cost
                if not reached_perfect and achieved >= oracle * (1.0 - 1e-6):
                    reached_perfect = True
                    exp_to_perfect = exp_cost
                checkpoints += 1

            abandoned: dict[int, int] = {}
            for level in (4, 8, 12, 16):
                abandoned[level] = int(
                    np.sum(
                        [
                            cumulative_artifact_exp(level)
                            for artifact_level in levels
                            if int(artifact_level) == level
                        ]
                    )
                )
            rows.append(
                UpgradeTrial(
                    policy.name,
                    trial_seed,
                    exp_cost,
                    exp_cost,
                    exp_cost * resin_per_exp if resin_per_exp is not None else None,
                    exp_to_progress,
                    exp_to_perfect,
                    checkpoints,
                    reached_perfect,
                    reached_progress,
                    achieved / oracle if oracle > 0 else 1.0,
                    tuple(abandoned.items()),
                )
            )

    interval_rng = np.random.default_rng(seed ^ 0x5A5A5A5A)
    confidence: dict[str, dict[str, ConfidenceInterval]] = {}
    for policy in policies:
        selected = [row for row in rows if row.policy == policy.name]
        confidence[policy.name] = {
            "exp_cost": _bootstrap_interval([row.exp_cost for row in selected], interval_rng),
            "exp_to_progress": _bootstrap_interval(
                [
                    row.exp_to_progress
                    for row in selected
                    if row.exp_to_progress is not None
                ]
                or [float("nan")],
                interval_rng,
            ),
            "exp_to_perfect": _bootstrap_interval(
                [
                    row.exp_to_perfect
                    for row in selected
                    if row.exp_to_perfect is not None
                ]
                or [float("nan")],
                interval_rng,
            ),
            "oracle_fraction": _bootstrap_interval(
                [row.oracle_fraction for row in selected], interval_rng
            ),
            "perfect_probability": _bootstrap_interval(
                [float(row.reached_perfect) for row in selected], interval_rng
            ),
            "progress_probability": _bootstrap_interval(
                [float(row.reached_progress) for row in selected], interval_rng
            ),
        }
    predicted = np.asarray(calibration_predictions)
    observed = np.asarray(calibration_observations)
    calibration = []
    boundaries = (0.0, 0.001, 0.01, 0.05, 0.20, 1.0000001)
    for lower, upper in zip(boundaries, boundaries[1:]):
        mask = (predicted >= lower) & (predicted < upper)
        calibration.append(
            UpgradeCalibrationBin(
                lower,
                min(upper, 1.0),
                int(np.count_nonzero(mask)),
                float(np.mean(predicted[mask])) if np.any(mask) else None,
                float(np.mean(observed[mask])) if np.any(mask) else None,
            )
        )
    return UpgradeBenchmark(
        tuple(rows), confidence, tuple(calibration), progress_target, resin_per_exp
    )
