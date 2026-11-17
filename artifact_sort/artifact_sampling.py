"""Whole-slot populations and identity-coupled ordinary five-star upgrades.

Probability assumptions are explicit, fingerprinted, and currently draft.
Observed scanner values are preserved; only future increments are generated.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from hashlib import sha256
from importlib.resources import files
import json
import math
from types import MappingProxyType
from typing import Mapping

import numpy as np

from .formulas import Stats
from .inventory import Artifact, Inventory
from .library_runtime import LEGAL_MAINS
from .model import SUBSTAT_KEYS


@dataclass(frozen=True, slots=True)
class SamplingRules:
    id: str
    source_fingerprint: str
    main_probabilities: Mapping[str, Stats]
    substat_weights: Stats
    rolls: Mapping[str, tuple[float, ...]]
    four_line_probability: float
    validated: bool
    assumptions: tuple[str, ...]
    fingerprint: str = field(init=False)

    def __post_init__(self) -> None:
        if set(self.main_probabilities) != set(LEGAL_MAINS):
            raise ValueError("main probabilities must cover every slot")
        for slot, values in self.main_probabilities.items():
            if (
                set(values) != LEGAL_MAINS[slot]
                or any(not math.isfinite(p) or p <= 0 for p in values.values())
                or not math.isclose(sum(values.values()), 1, rel_tol=1e-10)
            ):
                raise ValueError(f"invalid main probability distribution for {slot}")
        if set(self.substat_weights) != set(SUBSTAT_KEYS) or any(
            not math.isfinite(w) or w <= 0 for w in self.substat_weights.values()
        ):
            raise ValueError(
                "substat weights must cover every substat with positive finite weight"
            )
        if set(self.rolls) != set(SUBSTAT_KEYS) or any(
            not tiers or any(not math.isfinite(value) or value <= 0 for value in tiers)
            for tiers in self.rolls.values()
        ):
            raise ValueError(
                "roll tiers must cover every substat with positive finite values"
            )
        if not 0 <= self.four_line_probability <= 1:
            raise ValueError("four-line probability must lie between zero and one")
        object.__setattr__(
            self,
            "main_probabilities",
            MappingProxyType(
                {
                    slot: MappingProxyType(dict(values))
                    for slot, values in self.main_probabilities.items()
                }
            ),
        )
        object.__setattr__(
            self, "substat_weights", MappingProxyType(dict(self.substat_weights))
        )
        object.__setattr__(
            self,
            "rolls",
            MappingProxyType(
                {key: tuple(values) for key, values in self.rolls.items()}
            ),
        )
        content = {
            "source": self.source_fingerprint,
            "id": self.id,
            "mains": {
                slot: dict(values) for slot, values in self.main_probabilities.items()
            },
            "weights": dict(self.substat_weights),
            "rolls": dict(self.rolls),
            "four_line_probability": self.four_line_probability,
            "validated": self.validated,
            "assumptions": self.assumptions,
        }
        object.__setattr__(
            self,
            "fingerprint",
            sha256(json.dumps(content, sort_keys=True).encode()).hexdigest(),
        )


def sampling_rules() -> SamplingRules:
    data = json.loads(
        files("artifact_sort").joinpath("artifact-sampling-rules.json").read_text()
    )
    return SamplingRules(
        data["id"],
        sha256(json.dumps(data, sort_keys=True).encode()).hexdigest(),
        MappingProxyType(
            {
                slot: MappingProxyType(dict(values))
                for slot, values in data["main_probabilities"].items()
            }
        ),
        MappingProxyType(dict(data["substat_weights"])),
        MappingProxyType({key: tuple(values) for key, values in data["rolls"].items()}),
        data["four_line_probability"],
        data["validated"],
        tuple(data["assumptions"]),
    )


def _draw_substat(
    main: str, existing: Stats, rules: SamplingRules, rng: np.random.Generator
) -> str:
    keys = tuple(key for key in SUBSTAT_KEYS if key != main and key not in existing)
    weights = np.array([rules.substat_weights[key] for key in keys], dtype=np.float64)
    return str(rng.choice(keys, p=weights / weights.sum()))


def finish_artifact(
    artifact: Artifact, rules: SamplingRules, rng: np.random.Generator
) -> Artifact:
    """Ordinary enhancement only; missing scanner lines are explicit errors."""
    if artifact.rarity != 5:
        raise ValueError(
            f"{artifact.id}: ordinary outcome model currently supports only five-star artifacts"
        )
    if artifact.level >= 4 and len(artifact.substats) != 4:
        raise ValueError(f"{artifact.id}: missing observed substat lines after +4")
    if artifact.level < 4 and len(artifact.substats) not in (3, 4):
        raise ValueError(f"{artifact.id}: missing observed starting substat lines")
    if artifact.hidden_substats and (
        len(artifact.substats) != 3 or len(artifact.hidden_substats) != 1
    ):
        raise ValueError(f"{artifact.id}: unsupported hidden-line state")
    stats = dict(artifact.substats)
    for _ in range(artifact.level // 4, 5):
        if len(stats) == 3:
            if artifact.hidden_substats:
                stats.update(artifact.hidden_substats)
            else:
                key = _draw_substat(artifact.main_stat, stats, rules, rng)
                stats[key] = float(rng.choice(rules.rolls[key]))
        else:
            key = str(rng.choice(tuple(sorted(stats))))
            stats[key] += float(rng.choice(rules.rolls[key]))
    return replace(artifact, level=20, substats=stats, hidden_substats={})


def sample_completed_inventory(
    inventory: Inventory, rules: SamplingRules, *, seed: int = 0, trial: int = 0
) -> Inventory:
    """Same identity receives the same trial tape regardless of other pieces."""
    if type(seed) is not int or type(trial) is not int or trial < 0:
        raise ValueError("seed must be an integer and trial a nonnegative integer")
    completed = []
    for artifact in inventory.artifacts:
        payload = json.dumps(
            ["coupled-upgrades-1", seed, trial, artifact.id, rules.fingerprint]
        )
        entropy = int.from_bytes(sha256(payload.encode()).digest(), "big")
        completed.append(
            finish_artifact(artifact, rules, np.random.default_rng(entropy))
        )
    return Inventory(tuple(completed))


def sample_slot(
    slot: str, set_key: str, count: int, rules: SamplingRules, *, seed: int = 0
) -> Inventory:
    """Unconditional slot population: every main stat keeps its occurrence mass."""
    if slot not in LEGAL_MAINS:
        raise ValueError(f"unknown slot {slot!r}")
    if type(count) is not int or count <= 0:
        raise ValueError("count must be a positive integer")
    rng = np.random.default_rng(seed)
    main_distribution = rules.main_probabilities[slot]
    mains = tuple(sorted(main_distribution))
    probabilities = np.array(
        [main_distribution[main] for main in mains], dtype=np.float64
    )
    if set(mains) != LEGAL_MAINS[slot] or np.any(probabilities <= 0):
        raise ValueError(
            "main distribution must cover every legal main with positive mass"
        )
    probabilities /= probabilities.sum()
    pieces = []
    prefix = sha256(
        json.dumps([slot, set_key, seed, rules.fingerprint]).encode()
    ).hexdigest()[:16]
    for index in range(count):
        main = str(rng.choice(mains, p=probabilities))
        four = rng.random() < rules.four_line_probability
        stats: dict[str, float] = {}
        for _ in range(4 if four else 3):
            key = _draw_substat(main, stats, rules, rng)
            stats[key] = float(rng.choice(rules.rolls[key]))
        initial = Artifact(
            f"reference-{prefix}-{index}", set_key, slot, main, 5, 0, stats, {}
        )
        pieces.append(finish_artifact(initial, rules, rng))
    return Inventory(tuple(pieces))
