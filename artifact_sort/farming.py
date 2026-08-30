from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np

from .model import (
    ArtifactBatch,
    SLOT_KEYS,
    SUBSTAT_KEYS,
    SUBSTAT_MAX,
    concatenate_batches,
    from_good_data,
)
from .optimizer import BuildOptimizer
from .outcomes import sample_final_rolls
from .scenarios import Scenario


MAIN_STAT_DISTRIBUTIONS: dict[str, tuple[tuple[str, float], ...]] = {
    "flower": (("hp", 1.0),),
    "plume": (("atk", 1.0),),
    "sands": (
        ("hp_", 0.2668),
        ("atk_", 0.2666),
        ("def_", 0.2666),
        ("enerRech_", 0.10),
        ("eleMas", 0.10),
    ),
    "goblet": (
        ("hp_", 0.1925),
        ("atk_", 0.1925),
        ("def_", 0.19),
        ("eleMas", 0.025),
        ("pyro_dmg_", 0.05),
        ("electro_dmg_", 0.05),
        ("cryo_dmg_", 0.05),
        ("hydro_dmg_", 0.05),
        ("dendro_dmg_", 0.05),
        ("anemo_dmg_", 0.05),
        ("geo_dmg_", 0.05),
        ("physical_dmg_", 0.05),
    ),
    "circlet": (
        ("hp_", 0.22),
        ("atk_", 0.22),
        ("def_", 0.22),
        ("eleMas", 0.04),
        ("critRate_", 0.10),
        ("critDMG_", 0.10),
        ("heal_", 0.10),
    ),
}

SUBSTAT_WEIGHTS = np.asarray((6, 6, 6, 4, 4, 4, 4, 4, 3, 3), dtype=np.float64)


@dataclass(frozen=True, slots=True)
class FarmConfig:
    domain_sets: tuple[str, str] = ("DomainSetA", "DomainSetB")
    four_line_probability: float = 0.20
    five_star_drops_per_20_resin: float = 1.065
    strongbox: bool = True
    strongbox_four_line_probability: float = 1.0 / 3.0
    max_resin: int = 100_000
    check_every_drops: int = 10


@dataclass(frozen=True, slots=True)
class DefinitionSpec:
    set_key: str
    slot: str
    main_stat: str
    substats: tuple[str, str]


@dataclass(frozen=True, slots=True)
class ReshapeSpec:
    artifact_id: str
    attempts: int = 1


@dataclass(frozen=True, slots=True)
class FarmTrial:
    seed: int
    resin: float
    drops: int
    strongbox_drops: int
    defined_artifacts: int
    reshape_attempts: int
    achieved_gain: float
    reached_target: bool


@dataclass(frozen=True, slots=True)
class FarmBenchmark:
    trials: tuple[FarmTrial, ...]
    target_gain: float
    median_resin: float
    p95_resin: float
    mean_resin: float
    confidence_95: tuple[float, float]


def generate_artifacts(
    count: int,
    rng: np.random.Generator,
    *,
    sets: Sequence[str],
    four_line_probability: float,
    id_prefix: str = "synthetic",
) -> ArtifactBatch:
    artifacts = []
    for index in range(count):
        slot = str(rng.choice(SLOT_KEYS))
        main_options, main_probabilities = zip(*MAIN_STAT_DISTRIBUTIONS[slot])
        main = str(rng.choice(main_options, p=np.asarray(main_probabilities) / sum(main_probabilities)))
        weights = SUBSTAT_WEIGHTS.copy()
        if main in SUBSTAT_KEYS:
            weights[SUBSTAT_KEYS.index(main)] = 0.0
        selected = rng.choice(10, size=4, replace=False, p=weights / weights.sum())
        coefficients = rng.choice((7, 8, 9, 10), size=4)
        substats = [
            {
                "key": SUBSTAT_KEYS[int(stat)],
                "value": float(coeff * SUBSTAT_MAX[int(stat)] / 10.0),
                "initialValue": float(coeff * SUBSTAT_MAX[int(stat)] / 10.0),
            }
            for stat, coeff in zip(selected, coefficients)
        ]
        four_line = bool(rng.random() < four_line_probability)
        artifacts.append(
            {
                "id": f"{id_prefix}-{index}",
                "setKey": str(rng.choice(sets)),
                "slotKey": slot,
                "mainStatKey": main,
                "rarity": 5,
                "level": 0,
                "totalRolls": 4 if four_line else 3,
                "substats": substats if four_line else substats[:3],
                "unactivatedSubstats": [] if four_line else substats[3:],
                "location": "",
                "lock": False,
            }
        )
    return from_good_data({"format": "GOOD", "version": 3, "artifacts": artifacts})


def generate_defined_artifact(
    spec: DefinitionSpec,
    rng: np.random.Generator,
    *,
    four_line_probability: float = 0.20,
    artifact_id: str = "defined-0",
) -> ArtifactBatch:
    if spec.slot not in MAIN_STAT_DISTRIBUTIONS:
        raise ValueError(f"unknown definition slot {spec.slot!r}")
    legal_mains = {key for key, _ in MAIN_STAT_DISTRIBUTIONS[spec.slot]}
    if spec.main_stat not in legal_mains:
        raise ValueError(f"main stat {spec.main_stat!r} is not legal on {spec.slot}")
    if len(set(spec.substats)) != 2 or any(key not in SUBSTAT_KEYS for key in spec.substats):
        raise ValueError("a definition needs two distinct legal substats")
    if spec.main_stat in spec.substats:
        raise ValueError("a defined substat cannot equal the main stat")
    selected = [SUBSTAT_KEYS.index(key) for key in spec.substats]
    weights = SUBSTAT_WEIGHTS.copy()
    weights[selected] = 0
    if spec.main_stat in SUBSTAT_KEYS:
        weights[SUBSTAT_KEYS.index(spec.main_stat)] = 0
    selected.extend(int(value) for value in rng.choice(10, 2, replace=False, p=weights / weights.sum()))
    coefficients = rng.choice((7, 8, 9, 10), size=4)
    substats = [
        {
            "key": SUBSTAT_KEYS[stat],
            "value": float(coefficient * SUBSTAT_MAX[stat] / 10.0),
            "initialValue": float(coefficient * SUBSTAT_MAX[stat] / 10.0),
        }
        for stat, coefficient in zip(selected, coefficients)
    ]
    four_line = bool(rng.random() < four_line_probability)
    return from_good_data(
        {
            "format": "GOOD",
            "version": 3,
            "artifacts": [
                {
                    "id": artifact_id,
                    "setKey": spec.set_key,
                    "slotKey": spec.slot,
                    "mainStatKey": spec.main_stat,
                    "rarity": 5,
                    "level": 0,
                    "totalRolls": 4 if four_line else 3,
                    "substats": substats if four_line else substats[:3],
                    "unactivatedSubstats": [] if four_line else substats[3:],
                    "location": "",
                    "lock": False,
                }
            ],
        }
    )


def reshape_artifact(
    batch: ArtifactBatch, index: int, rng: np.random.Generator
) -> ArtifactBatch:
    initial = batch.initial_sub_rolls[index]
    if np.count_nonzero(initial) != 4:
        raise ValueError(
            f"artifact {batch.ids[index]} lacks exact initial rolls and cannot be reshaped exactly"
        )
    base = batch.take((index,)).with_states(
        sub_rolls=initial[None, :], levels=np.zeros(1, dtype=np.uint8)
    )
    reshaped = sample_final_rolls(base, rng)[0]
    rolls = batch.sub_rolls.copy()
    rolls[index] = reshaped
    return batch.with_states(sub_rolls=rolls)


def _finalized_batch(batch: ArtifactBatch, rng: np.random.Generator) -> ArtifactBatch:
    rolls = sample_final_rolls(batch, rng)
    levels = np.where(batch.rarities == 5, 20, batch.levels).astype(np.uint8)
    return batch.with_states(sub_rolls=rolls, levels=levels)


def _mean_utility(batch: ArtifactBatch, scenarios: Sequence[Scenario]) -> float:
    optimizer = BuildOptimizer(batch, candidate_limit=30, beam_width=4000)
    values = []
    for scenario in scenarios:
        result = optimizer.optimize(scenario)
        if result:
            values.append(result[0].utility)
    return float(np.mean(values)) if values else 0.0


def _retain_build_options(
    current: ArtifactBatch,
    acquired: ArtifactBatch,
    scenarios: Sequence[Scenario],
    *,
    loadouts: int = 12,
) -> tuple[ArtifactBatch, int]:
    combined = concatenate_batches(current, acquired)
    optimizer = BuildOptimizer(combined, candidate_limit=24, beam_width=2500)
    keep_new = np.zeros(len(acquired), dtype=np.bool_)
    offset = len(current)
    for scenario in scenarios:
        for build in optimizer.optimize(scenario, top_k=loadouts):
            for index in build.indices:
                if index >= offset:
                    keep_new[index - offset] = True
    rejected = int(np.count_nonzero(~keep_new))
    return concatenate_batches(current, acquired.mask(keep_new)), rejected


def simulate_farming(
    inventory: ArtifactBatch,
    scenarios: Sequence[Scenario],
    *,
    increase: float,
    config: FarmConfig = FarmConfig(),
    trials: int = 100,
    seed: int = 0,
    definitions: Sequence[DefinitionSpec] = (),
    reshapes: Sequence[ReshapeSpec] = (),
) -> FarmBenchmark:
    """Monte Carlo farming with inventory reoptimization after each drop batch.

    Drops receive fixed hidden upgrade outcomes at acquisition. This benchmark
    finalizes each retained candidate, so its EXP figure is an optimistic
    upper-bound policy; the independent upgrade benchmark measures adaptive
    enhancement costs without that assumption.
    """

    if not scenarios:
        raise ValueError("at least one scenario is required")
    if trials <= 0:
        raise ValueError("trials must be positive")
    if increase < 0:
        raise ValueError("increase must be non-negative")
    baseline = _mean_utility(inventory, scenarios)
    target = baseline * (1.0 + increase)
    sequences = np.random.SeedSequence(seed).spawn(trials)
    output: list[FarmTrial] = []
    max_drops = int(config.max_resin / 20 * config.five_star_drops_per_20_resin)
    for sequence in sequences:
        rng = np.random.default_rng(sequence)
        current = inventory
        for definition_index, definition in enumerate(definitions):
            defined = generate_defined_artifact(
                definition,
                rng,
                artifact_id=f"defined-{int(sequence.entropy)}-{definition_index}",
            )
            current = concatenate_batches(current, _finalized_batch(defined, rng))
        reshape_attempts = 0
        id_index = {str(artifact_id): i for i, artifact_id in enumerate(current.ids)}
        for reshape in reshapes:
            if reshape.artifact_id not in id_index:
                raise ValueError(f"reshape artifact {reshape.artifact_id!r} is not in inventory")
            for _ in range(reshape.attempts):
                current = reshape_artifact(current, id_index[reshape.artifact_id], rng)
                reshape_attempts += 1
        achieved = _mean_utility(current, scenarios)
        strongbox_inputs = 0
        strongbox_drops = 0
        drops = 0
        while drops < max_drops and achieved < target:
            take = min(config.check_every_drops, max_drops - drops)
            acquired = generate_artifacts(
                take,
                rng,
                sets=config.domain_sets,
                four_line_probability=config.four_line_probability,
                id_prefix=f"farm-{int(sequence.entropy)}-{drops}",
            )
            finalized = _finalized_batch(acquired, rng)
            current, rejected = _retain_build_options(current, finalized, scenarios)
            drops += take
            if config.strongbox:
                strongbox_inputs += rejected
                box_count = strongbox_inputs // 3
                strongbox_inputs %= 3
                if box_count:
                    boxed = generate_artifacts(
                        box_count,
                        rng,
                        sets=(config.domain_sets[0],),
                        four_line_probability=config.strongbox_four_line_probability,
                        id_prefix=f"strongbox-{int(sequence.entropy)}-{strongbox_drops}",
                    )
                    current, rejected_boxed = _retain_build_options(
                        current, _finalized_batch(boxed, rng), scenarios
                    )
                    strongbox_inputs += rejected_boxed
                    strongbox_drops += box_count
            achieved = _mean_utility(current, scenarios)
        resin = drops / config.five_star_drops_per_20_resin * 20.0
        output.append(
            FarmTrial(
                int(sequence.generate_state(1)[0]),
                resin,
                drops,
                strongbox_drops,
                len(definitions),
                reshape_attempts,
                achieved / baseline - 1.0 if baseline > 0 else 0.0,
                achieved >= target,
            )
        )
    resin_values = np.asarray([trial.resin for trial in output])
    trial_rng = np.random.default_rng(seed ^ 0xC0FFEE)
    means = np.mean(
        trial_rng.choice(resin_values, size=(1000, len(resin_values)), replace=True), axis=1
    )
    interval = np.quantile(means, (0.025, 0.975))
    return FarmBenchmark(
        tuple(output),
        increase,
        float(np.median(resin_values)),
        float(np.quantile(resin_values, 0.95)),
        float(np.mean(resin_values)),
        (float(interval[0]), float(interval[1])),
    )


@dataclass(frozen=True, slots=True)
class MaterialAnalysis:
    artifact_exp: float | None
    mora: float | None
    five_star_count: int
    five_star_feed_exp: float
    strongbox_outputs: int
    break_even: tuple[tuple[float, float], ...]
    warnings: tuple[str, ...]


def analyze_materials(batch: ArtifactBatch, good_data: dict[str, object]) -> MaterialAnalysis:
    materials = good_data.get("materials")
    material_map = materials if isinstance(materials, dict) else {}
    artifact_exp = material_map.get("artificatEXP", material_map.get("artifactEXP"))
    mora = material_map.get("mora")
    exp_value = float(artifact_exp) if isinstance(artifact_exp, (int, float)) else None
    mora_value = float(mora) if isinstance(mora, (int, float)) else None
    five_star = int(np.count_nonzero(batch.rarities == 5))
    # A level-zero five-star provides 3,780 enhancement EXP. Leveled fodder
    # additionally returns 80% of invested EXP.
    feed_exp = float(five_star * 3780 + np.sum(batch.invested_exp[batch.rarities == 5]) * 0.8)
    warnings = []
    if exp_value is None or mora_value is None:
        warnings.append("material balances are incomplete; reporting break-even curves")
    break_even = tuple(
        (mora_per_exp, feed_exp * mora_per_exp)
        for mora_per_exp in (0.25, 0.5, 1.0, 2.0, 4.0)
    )
    return MaterialAnalysis(
        exp_value,
        mora_value,
        five_star,
        feed_exp,
        five_star // 3,
        break_even,
        tuple(warnings),
    )
