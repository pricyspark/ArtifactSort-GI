from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
import tomllib
from typing import Any, Literal, Mapping, Protocol, Sequence

import numpy as np
from numpy.typing import NDArray

from .model import SLOT_INDEX, STAT_INDEX, STAT_KEYS


Tier = Literal["current", "speculative"]
Objective = Literal["damage", "reaction", "healing", "shield", "support"]


def _stat_vector(values: Mapping[str, float] | None) -> NDArray[np.float64]:
    result = np.zeros(len(STAT_KEYS), dtype=np.float64)
    for key, value in (values or {}).items():
        try:
            result[STAT_INDEX[key]] = float(value)
        except KeyError as exc:
            raise ValueError(f"unknown scenario stat {key!r}") from exc
    result.setflags(write=False)
    return result


@dataclass(frozen=True, slots=True)
class SetStrategy:
    """One acceptable set composition for a scenario."""

    required_sets: tuple[tuple[str, int], ...]
    source: str = "configured"
    evidence_count: int = 1

    def __post_init__(self) -> None:
        if any(not key or count not in (1, 2, 4) for key, count in self.required_sets):
            raise ValueError("set strategy requirements must use valid 1/2/4-piece counts")
        if len({key for key, _ in self.required_sets}) != len(self.required_sets):
            raise ValueError("set strategy cannot contain duplicate sets")
        if sum(count for _, count in self.required_sets) > 5:
            raise ValueError("set strategy cannot require more than five artifacts")
        if self.evidence_count < 1:
            raise ValueError("set strategy evidence_count must be positive")

    @property
    def requirements(self) -> dict[str, int]:
        return dict(self.required_sets)


@dataclass(frozen=True, slots=True)
class Scenario:
    id: str
    tier: Tier = "speculative"
    objective: Objective = "damage"
    scaling_stat: Literal["hp", "atk", "def", "eleMas"] = "atk"
    damage_stat: str | None = None
    base_stats: NDArray[np.float64] = field(
        default_factory=lambda: _stat_vector(
            {
                "hp": 12000,
                "atk": 800,
                "def": 700,
                "enerRech_": 100,
                "critRate_": 5,
                "critDMG_": 50,
            }
        )
    )
    bonus_stats: NDArray[np.float64] = field(default_factory=lambda: _stat_vector(None))
    constraints: tuple[tuple[int, float], ...] = ()
    required_sets: tuple[tuple[str, int], ...] = ()
    set_strategies: tuple[SetStrategy, ...] = ()
    allowed_main_stats: tuple[tuple[int, tuple[int, ...]], ...] = ()
    multiplier: float = 1.0
    reaction_multiplier: float = 1.0
    source: str = "builtin"
    metadata: Mapping[str, Any] = field(default_factory=dict, compare=False, hash=False)

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("scenario id cannot be empty")
        if self.tier not in ("current", "speculative"):
            raise ValueError(f"invalid scenario tier {self.tier!r}")
        if self.base_stats.shape != (len(STAT_KEYS),):
            raise ValueError("base_stats has invalid shape")
        if self.bonus_stats.shape != (len(STAT_KEYS),):
            raise ValueError("bonus_stats has invalid shape")
        if self.required_sets and self.set_strategies:
            raise ValueError("use required_sets or set_strategies, not both")

    @property
    def allowed_mains(self) -> dict[int, tuple[int, ...]]:
        return dict(self.allowed_main_stats)

    @property
    def set_requirements(self) -> dict[str, int]:
        return dict(self.required_sets)

    @property
    def set_requirement_options(self) -> tuple[dict[str, int], ...]:
        if self.set_strategies:
            return tuple(strategy.requirements for strategy in self.set_strategies)
        if self.required_sets:
            return (dict(self.required_sets),)
        return ({},)


class Evaluator(Protocol):
    version: str

    def evaluate(self, artifact_stats: NDArray[np.float64], scenario: Scenario) -> float:
        ...

    def marginal_weights(
        self, baseline: NDArray[np.float64], scenario: Scenario
    ) -> NDArray[np.float64]:
        ...

    def evaluate_batch(
        self, artifact_stats: NDArray[np.float64], scenario: Scenario
    ) -> NDArray[np.float64]:
        ...


class ScenarioProvider(Protocol):
    name: str

    def scenarios(self) -> Sequence[Scenario]:
        ...


@dataclass(frozen=True, slots=True)
class BuiltinScenarioProvider:
    name: str = "builtin"

    def scenarios(self) -> Sequence[Scenario]:
        return generic_scenarios()


@dataclass(frozen=True, slots=True)
class FileScenarioProvider:
    path: str | Path
    name: str = "file"

    def scenarios(self) -> Sequence[Scenario]:
        return load_scenarios(self.path)


class BuiltinEvaluator:
    """Compact nonlinear evaluator for generic and translated scenarios."""

    version = "builtin-v1"

    @staticmethod
    def _totals(artifact_stats: NDArray[np.float64], scenario: Scenario) -> NDArray[np.float64]:
        return scenario.base_stats + scenario.bonus_stats + artifact_stats

    @staticmethod
    def _primary(totals: NDArray[np.float64], key: str, base: NDArray[np.float64]) -> float:
        if key == "eleMas":
            return max(0.0, float(totals[STAT_INDEX["eleMas"]]))
        flat = float(totals[STAT_INDEX[key]])
        percent = float(totals[STAT_INDEX[f"{key}_"]]) / 100.0
        # base[key] is the character/weapon base portion. Flat bonuses are
        # represented by totals[key] - base[key].
        return float(base[STAT_INDEX[key]]) * (1.0 + percent) + (
            flat - float(base[STAT_INDEX[key]])
        )

    def evaluate(self, artifact_stats: NDArray[np.float64], scenario: Scenario) -> float:
        totals = self._totals(artifact_stats, scenario)
        for stat, minimum in scenario.constraints:
            if totals[stat] + 1e-12 < minimum:
                return -np.inf

        primary = self._primary(totals, scenario.scaling_stat, scenario.base_stats)
        if scenario.objective == "support":
            margins = [totals[stat] / minimum for stat, minimum in scenario.constraints if minimum > 0]
            return float(min(margins, default=primary))

        if scenario.objective == "reaction":
            em = max(0.0, totals[STAT_INDEX["eleMas"]])
            mode = str(scenario.metadata.get("reaction_mode", "transformative"))
            if mode == "amplifying":
                em_factor = 1.0 + 2.78 * em / (em + 1400.0)
                crit_rate = np.clip(totals[STAT_INDEX["critRate_"]] / 100.0, 0.0, 1.0)
                crit_damage = max(0.0, totals[STAT_INDEX["critDMG_"]] / 100.0)
                crit_factor = 1.0 + crit_rate * crit_damage
                primary = self._primary(totals, scenario.scaling_stat, scenario.base_stats)
                return float(
                    scenario.multiplier
                    * scenario.reaction_multiplier
                    * primary
                    * em_factor
                    * crit_factor
                )
            if mode == "additive":
                em_factor = 1.0 + 5.0 * em / (em + 1200.0)
                primary = self._primary(totals, scenario.scaling_stat, scenario.base_stats)
                return float(
                    scenario.multiplier
                    * (primary + scenario.reaction_multiplier * em_factor)
                )
            em_factor = 1.0 + 16.0 * em / (em + 2000.0)
            return float(scenario.multiplier * scenario.reaction_multiplier * em_factor)

        if scenario.objective == "healing":
            healing = 1.0 + totals[STAT_INDEX["heal_"]] / 100.0
            return float(scenario.multiplier * primary * healing)

        if scenario.objective == "shield":
            return float(scenario.multiplier * primary)

        crit_rate = np.clip(totals[STAT_INDEX["critRate_"]] / 100.0, 0.0, 1.0)
        crit_damage = max(0.0, totals[STAT_INDEX["critDMG_"]] / 100.0)
        crit_factor = (
            1.0 + crit_rate * crit_damage
            if bool(scenario.metadata.get("can_crit", True))
            else 1.0
        )
        damage_bonus = 0.0
        if scenario.damage_stat is not None:
            damage_bonus = totals[STAT_INDEX[scenario.damage_stat]] / 100.0
        return float(scenario.multiplier * primary * (1.0 + damage_bonus) * crit_factor)

    def evaluate_batch(
        self, artifact_stats: NDArray[np.float64], scenario: Scenario
    ) -> NDArray[np.float64]:
        if artifact_stats.ndim != 2 or artifact_stats.shape[1] != len(STAT_KEYS):
            raise ValueError("artifact_stats must have shape (N, 19)")
        return np.fromiter(
            (self.evaluate(row, scenario) for row in artifact_stats),
            dtype=np.float64,
            count=len(artifact_stats),
        )

    def marginal_weights(
        self, baseline: NDArray[np.float64], scenario: Scenario
    ) -> NDArray[np.float64]:
        feasible = baseline.copy()
        totals = scenario.base_stats + scenario.bonus_stats + feasible
        for stat, minimum in scenario.constraints:
            feasible[stat] += max(0.0, minimum - totals[stat])
        base_value = self.evaluate(feasible, scenario)
        weights = np.zeros(len(STAT_KEYS), dtype=np.float64)
        # A uniform numerical step is adequate for screening because weights
        # are normalized afterwards. Final ranking never uses this linearization.
        for i in range(len(STAT_KEYS)):
            step = 1.0
            perturbed = feasible.copy()
            perturbed[i] += step
            value = self.evaluate(perturbed, scenario)
            if np.isfinite(base_value) and np.isfinite(value):
                weights[i] = max(0.0, value - base_value)
        maximum = weights.max(initial=0.0)
        if maximum > 0:
            weights /= maximum
        return weights


def scenario_from_mapping(raw: Mapping[str, Any], *, source: str = "file") -> Scenario:
    constraints = tuple(
        (STAT_INDEX[key], float(value)) for key, value in raw.get("constraints", {}).items()
    )
    required_sets = tuple(
        sorted((str(key), int(value)) for key, value in raw.get("required_sets", {}).items())
    )
    set_strategies = tuple(
        SetStrategy(
            tuple(
                sorted(
                    (str(key), int(value))
                    for key, value in strategy.get("required_sets", {}).items()
                )
            ),
            source=str(strategy.get("source", "file")),
            evidence_count=int(strategy.get("evidence_count", 1)),
        )
        for strategy in raw.get("set_strategies", ())
        if isinstance(strategy, Mapping)
    )
    allowed: list[tuple[int, tuple[int, ...]]] = []
    for slot, stats in raw.get("allowed_main_stats", {}).items():
        allowed.append((SLOT_INDEX[slot], tuple(STAT_INDEX[stat] for stat in stats)))

    default_base = {
        "hp": 12000.0,
        "atk": 800.0,
        "def": 700.0,
        "enerRech_": 100.0,
        "critRate_": 5.0,
        "critDMG_": 50.0,
    }
    return Scenario(
        id=str(raw["id"]),
        tier=str(raw.get("tier", "speculative")),  # type: ignore[arg-type]
        objective=str(raw.get("objective", "damage")),  # type: ignore[arg-type]
        scaling_stat=str(raw.get("scaling_stat", "atk")),  # type: ignore[arg-type]
        damage_stat=raw.get("damage_stat"),
        base_stats=_stat_vector(raw.get("base_stats", default_base)),
        bonus_stats=_stat_vector(raw.get("bonus_stats")),
        constraints=constraints,
        required_sets=required_sets,
        set_strategies=set_strategies,
        allowed_main_stats=tuple(sorted(allowed)),
        multiplier=float(raw.get("multiplier", 1.0)),
        reaction_multiplier=float(raw.get("reaction_multiplier", 1.0)),
        source=source,
        metadata=dict(raw.get("metadata", {})),
    )


def load_scenarios(path: str | Path) -> list[Scenario]:
    path = Path(path)
    if path.suffix.lower() == ".toml":
        with path.open("rb") as handle:
            data = tomllib.load(handle)
    else:
        with path.open(encoding="utf-8") as handle:
            data = json.load(handle)
    raw_scenarios = data.get("scenarios", data if isinstance(data, list) else None)
    if not isinstance(raw_scenarios, list):
        raise ValueError("scenario file must contain a 'scenarios' array")
    return [scenario_from_mapping(raw, source=str(path)) for raw in raw_scenarios]


def scenario_to_mapping(scenario: Scenario) -> dict[str, Any]:
    return {
        "id": scenario.id,
        "tier": scenario.tier,
        "objective": scenario.objective,
        "scaling_stat": scenario.scaling_stat,
        "damage_stat": scenario.damage_stat,
        "base_stats": {
            key: float(scenario.base_stats[i])
            for i, key in enumerate(STAT_KEYS)
            if scenario.base_stats[i] != 0
        },
        "bonus_stats": {
            key: float(scenario.bonus_stats[i])
            for i, key in enumerate(STAT_KEYS)
            if scenario.bonus_stats[i] != 0
        },
        "constraints": {
            STAT_KEYS[index]: value for index, value in scenario.constraints
        },
        "required_sets": dict(scenario.required_sets),
        "set_strategies": [
            {
                "required_sets": strategy.requirements,
                "source": strategy.source,
                "evidence_count": strategy.evidence_count,
            }
            for strategy in scenario.set_strategies
        ],
        "allowed_main_stats": {
            next(key for key, index in SLOT_INDEX.items() if index == slot): [
                STAT_KEYS[stat] for stat in stats
            ]
            for slot, stats in scenario.allowed_main_stats
        },
        "multiplier": scenario.multiplier,
        "reaction_multiplier": scenario.reaction_multiplier,
        "source": scenario.source,
        "metadata": dict(scenario.metadata),
    }


def generic_scenarios() -> list[Scenario]:
    scenarios: list[Scenario] = []
    for scaling in ("atk", "hp", "def"):
        for damage_stat in (
            "pyro_dmg_",
            "electro_dmg_",
            "cryo_dmg_",
            "hydro_dmg_",
            "dendro_dmg_",
            "anemo_dmg_",
            "geo_dmg_",
            "physical_dmg_",
        ):
            scenarios.append(
                Scenario(
                    id=f"generic-{scaling}-{damage_stat}",
                    scaling_stat=scaling,  # type: ignore[arg-type]
                    damage_stat=damage_stat,
                )
            )
    scenarios.extend(
        (
            Scenario(
                id="generic-em-transformative",
                objective="reaction",
                scaling_stat="eleMas",
                metadata={"reaction_mode": "transformative"},
            ),
            Scenario(
                id="generic-atk-amplifying",
                objective="reaction",
                scaling_stat="atk",
                metadata={"reaction_mode": "amplifying"},
            ),
            Scenario(
                id="generic-atk-additive",
                objective="reaction",
                scaling_stat="atk",
                metadata={"reaction_mode": "additive"},
            ),
            Scenario(
                id="generic-atk-noncrit",
                objective="damage",
                scaling_stat="atk",
                metadata={"can_crit": False},
            ),
            Scenario(id="generic-hp-healing", objective="healing", scaling_stat="hp"),
            Scenario(id="generic-hp-shield", objective="shield", scaling_stat="hp"),
            Scenario(id="generic-def-shield", objective="shield", scaling_stat="def"),
            Scenario(
                id="generic-er-support",
                objective="support",
                constraints=((STAT_INDEX["enerRech_"], 180.0),),
            ),
        )
    )
    return scenarios
