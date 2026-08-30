from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, Sequence

import numpy as np
from numpy.typing import NDArray

from .model import ArtifactBatch, SUBSTAT_MAX, cumulative_artifact_exp, load_good
from .optimizer import BuildOptimizer, DeletionAnalyzer
from .outcomes import sample_upgrade_tapes
from .scenarios import BuiltinEvaluator, Scenario
from .upgrades import UpgradeAnalyzer


@dataclass(frozen=True, slots=True)
class DeletionDecision:
    indices: tuple[int, ...]


class Policy(Protocol):
    name: str


class DeletionPolicy(Policy, Protocol):
    def delete(
        self,
        batch: ArtifactBatch,
        scenarios: Sequence[Scenario],
        free: int,
        rng: np.random.Generator,
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

    def delete(
        self,
        batch: ArtifactBatch,
        scenarios: Sequence[Scenario],
        free: int,
        rng: np.random.Generator,
    ) -> DeletionDecision:
        scores = rng.random(len(batch))
        return DeletionDecision(_lowest_unprotected(batch, scores, free))


class CritValuePolicy:
    name = "crit-value"

    def delete(
        self,
        batch: ArtifactBatch,
        scenarios: Sequence[Scenario],
        free: int,
        rng: np.random.Generator,
    ) -> DeletionDecision:
        scores = batch.sub_rolls[:, 8].astype(float) * 2.0 + batch.sub_rolls[:, 9]
        scores += np.count_nonzero(batch.sub_rolls, axis=1) * 1e-3
        return DeletionDecision(_lowest_unprotected(batch, scores, free))


class StaticWeightPolicy:
    """The prior row-scoring family, using scenario-local linear weights."""

    name = "greedy-linearized-score"

    def delete(
        self,
        batch: ArtifactBatch,
        scenarios: Sequence[Scenario],
        free: int,
        rng: np.random.Generator,
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

    def delete(
        self,
        batch: ArtifactBatch,
        scenarios: Sequence[Scenario],
        free: int,
        rng: np.random.Generator,
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

    def __init__(self, artifact_ids: Sequence[str]) -> None:
        self.artifact_ids = tuple(artifact_ids)

    def delete(
        self,
        batch: ArtifactBatch,
        scenarios: Sequence[Scenario],
        free: int,
        rng: np.random.Generator,
    ) -> DeletionDecision:
        index = {str(key): i for i, key in enumerate(batch.ids)}
        ordered = [index[key] for key in self.artifact_ids if key in index]
        ordered = [i for i in ordered if not batch.protected_mask()[i]]
        if len(ordered) < free:
            raise ValueError("recorded ordering does not contain enough eligible artifacts")
        return DeletionDecision(tuple(ordered[:free]))


class PortfolioDeletionPolicy:
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
    ) -> DeletionDecision:
        optimizer = BuildOptimizer(batch, candidate_limit=self.candidate_limit)
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


def _hidden_stats(batch: ArtifactBatch, tapes: Sequence[Sequence[tuple[int, int]]]) -> NDArray[np.float64]:
    rolls = _hidden_rolls(batch, tapes)
    stats = batch.final_stats()
    stats[:, :10] = rolls.astype(np.float64) * (SUBSTAT_MAX / 10.0)
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
) -> DeletionBenchmark:
    scenarios = tuple(calibration_scenarios) + tuple(heldout_scenarios)
    if not scenarios:
        raise ValueError("at least one calibration or held-out scenario is required")
    if trials <= 0:
        raise ValueError("trials must be positive")
    if free < 0:
        raise ValueError("free must be non-negative")
    seed_sequence = np.random.SeedSequence(seed)
    child_seeds = seed_sequence.spawn(trials)
    output: list[PolicyDeletionTrial] = []

    for child in child_seeds:
        trial_seed = int(child.generate_state(1)[0])
        tape_rng = np.random.default_rng(child)
        tapes = sample_upgrade_tapes(batch, tape_rng)
        hidden = _hidden_stats(batch, tapes)
        oracle_optimizer = BuildOptimizer(batch, candidate_limit=40)
        oracle_pools = [
            oracle_optimizer.optimize(
                scenario, stats=hidden, include_unfinished=True, top_k=20
            )
            for scenario in scenarios
        ]
        if any(not pool for pool in oracle_pools):
            missing = scenarios[next(i for i, pool in enumerate(oracle_pools) if not pool)].id
            raise ValueError(f"scenario {missing!r} has no legal build in simulation")
        baselines = np.asarray([pool[0].utility for pool in oracle_pools])
        oracle_members = {
            index
            for baseline, pool in zip(baselines, oracle_pools)
            for build in pool
            if build.utility >= (1.0 - 0.01) * baseline
            for index in build.indices
        }

        # The unattainable upper bound sees every hidden tape and the held-out
        # scenarios. It still obeys the same protection and exact-size rules.
        hidden_levels = np.where(batch.rarities == 5, 20, batch.levels).astype(np.uint8)
        hidden_batch = batch.with_states(
            sub_rolls=_hidden_rolls(batch, tapes), levels=hidden_levels
        )
        clairvoyant = DeletionAnalyzer(
            BuildOptimizer(hidden_batch, candidate_limit=40),
            scenarios,
            loadouts_per_scenario=80,
        ).analyze(free)
        trial_policies: list[tuple[str, DeletionDecision]] = []

        for policy_index, policy in enumerate(policies):
            policy_rng = np.random.default_rng(trial_seed + policy_index * 1_000_003)
            decision = policy.delete(batch, calibration_scenarios, free, policy_rng)
            trial_policies.append((policy.name, decision))
        trial_policies.append(
            ("clairvoyant-oracle", DeletionDecision(clairvoyant.deleted_indices))
        )

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
                for scenario in scenarios:
                    retained = oracle_optimizer.optimize(
                        scenario,
                        stats=hidden,
                        available=available,
                        include_unfinished=True,
                        top_k=1,
                    )
                    retained_values.append(retained[0].utility if retained else -np.inf)
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
            output.append(
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
