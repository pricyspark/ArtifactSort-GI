from __future__ import annotations

from dataclasses import dataclass, fields
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np
from numpy.typing import NDArray


STAT_KEYS = (
    "hp",
    "atk",
    "def",
    "hp_",
    "atk_",
    "def_",
    "enerRech_",
    "eleMas",
    "critRate_",
    "critDMG_",
    "pyro_dmg_",
    "electro_dmg_",
    "cryo_dmg_",
    "hydro_dmg_",
    "dendro_dmg_",
    "anemo_dmg_",
    "geo_dmg_",
    "physical_dmg_",
    "heal_",
)
SUBSTAT_KEYS = STAT_KEYS[:10]
SLOT_KEYS = ("flower", "plume", "sands", "goblet", "circlet")

STAT_INDEX = {key: i for i, key in enumerate(STAT_KEYS)}
SLOT_INDEX = {key: i for i, key in enumerate(SLOT_KEYS)}

# Values of one maximum five-star substat roll. Percent stats are stored in
# percentage points, matching GOOD.
SUBSTAT_MAX = np.array(
    (298.75, 19.45, 23.13, 5.83, 5.83, 7.29, 6.48, 23.31, 3.89, 7.77),
    dtype=np.float64,
)
MAINSTAT_MAX = np.array(
    (
        4780.0,
        311.0,
        0.0,
        46.6,
        46.6,
        58.3,
        51.8,
        186.5,
        31.1,
        62.2,
        46.6,
        46.6,
        46.6,
        46.6,
        46.6,
        46.6,
        46.6,
        58.3,
        35.9,
    ),
    dtype=np.float64,
)


def _readonly(array: NDArray[Any], dtype: np.dtype[Any] | type[Any]) -> NDArray[Any]:
    result = np.ascontiguousarray(array, dtype=dtype)
    result.setflags(write=False)
    return result


def _infer_starting_lines(artifact: Mapping[str, Any]) -> tuple[int, bool, float]:
    unactivated = artifact.get("unactivatedSubstats") or []
    if unactivated:
        return 3, False, 0.0

    level = int(artifact.get("level", 0))
    total_rolls = artifact.get("totalRolls")
    if isinstance(total_rolls, int):
        starting = total_rolls - level // 4
        if starting in (3, 4):
            return starting, False, float(starting == 4)

    substats = artifact.get("substats") or []
    if level == 0 and len(substats) in (3, 4):
        lines = len(substats)
        return lines, False, float(lines == 4)

    initial_values = [sub.get("initialValue") for sub in substats]
    if initial_values and all(value is not None for value in initial_values):
        lines = len(initial_values)
        return lines, False, float(lines == 4)

    # Both three- and four-line histories can sometimes explain aggregate
    # scanner values. Keep the ambiguity explicit rather than guessing a roll
    # decomposition and presenting it as fact.
    return 3, True, 0.5


@dataclass(frozen=True, slots=True)
class ArtifactBatch:
    """Immutable structure-of-arrays representation of an artifact inventory."""

    ids: NDArray[np.str_]
    set_keys: NDArray[np.str_]
    slots: NDArray[np.uint8]
    main_stats: NDArray[np.uint8]
    rarities: NDArray[np.uint8]
    levels: NDArray[np.uint8]
    starting_lines: NDArray[np.uint8]
    sub_rolls: NDArray[np.uint8]
    initial_sub_rolls: NDArray[np.uint8]
    uncertain_history: NDArray[np.bool_]
    four_line_probability: NDArray[np.float64]
    locations: NDArray[np.str_]
    locked: NDArray[np.bool_]
    starred: NDArray[np.bool_]
    invested_exp: NDArray[np.int64]

    def __post_init__(self) -> None:
        count = len(self.ids)
        one_dimensional = (
            "set_keys",
            "slots",
            "main_stats",
            "rarities",
            "levels",
            "starting_lines",
            "uncertain_history",
            "four_line_probability",
            "locations",
            "locked",
            "starred",
            "invested_exp",
        )
        for name in one_dimensional:
            value = getattr(self, name)
            if value.shape != (count,):
                raise ValueError(f"{name} must have shape ({count},), got {value.shape}")
        for name in ("sub_rolls", "initial_sub_rolls"):
            value = getattr(self, name)
            if value.shape != (count, len(SUBSTAT_KEYS)):
                raise ValueError(
                    f"{name} must have shape ({count}, {len(SUBSTAT_KEYS)}), got {value.shape}"
                )
        if np.any(self.slots >= len(SLOT_KEYS)):
            raise ValueError("invalid artifact slot index")
        if np.any(self.main_stats >= len(STAT_KEYS)):
            raise ValueError("invalid artifact main-stat index")
        five_star = self.rarities == 5
        if np.any(five_star & (self.starting_lines != 3) & (self.starting_lines != 4)):
            raise ValueError("five-star starting_lines must contain only 3 or 4")
        if np.any(self.starting_lines > 4):
            raise ValueError("starting_lines cannot exceed 4")
        if np.any((self.four_line_probability < 0) | (self.four_line_probability > 1)):
            raise ValueError("four_line_probability must be between zero and one")

        # A frozen dataclass prevents rebinding; read-only arrays prevent
        # mutation through a retained NumPy reference.
        for field in fields(self):
            value = getattr(self, field.name)
            value.setflags(write=False)

    def __len__(self) -> int:
        return len(self.ids)

    def take(self, indices: NDArray[np.integer[Any]] | Iterable[int]) -> ArtifactBatch:
        idx = np.asarray(list(indices) if not isinstance(indices, np.ndarray) else indices)
        return ArtifactBatch(**{field.name: getattr(self, field.name)[idx] for field in fields(self)})

    def mask(self, mask: NDArray[np.bool_]) -> ArtifactBatch:
        if mask.shape != (len(self),):
            raise ValueError("mask shape does not match inventory")
        return ArtifactBatch(**{field.name: getattr(self, field.name)[mask] for field in fields(self)})

    def final_stats(self) -> NDArray[np.float64]:
        """Return current substats plus level-20 main stats for build search."""

        result = np.zeros((len(self), len(STAT_KEYS)), dtype=np.float64)
        result[:, : len(SUBSTAT_KEYS)] = self.sub_rolls * (SUBSTAT_MAX / 10.0)
        result[np.arange(len(self)), self.main_stats] += MAINSTAT_MAX[self.main_stats]
        return result

    def remaining_random_rolls(self) -> NDArray[np.uint8]:
        milestones = self.levels // 4
        three_line_done = np.maximum(milestones.astype(np.int16) - 1, 0)
        remaining_three = 4 - three_line_done
        remaining_four = 5 - milestones
        remaining = np.where(self.starting_lines == 3, remaining_three, remaining_four)
        remaining = np.where(self.rarities == 5, remaining, 0)
        return np.clip(remaining, 0, 5).astype(np.uint8)

    def protected_mask(self, pinned_ids: Iterable[str] = ()) -> NDArray[np.bool_]:
        pins = set(pinned_ids)
        return self.starred | (self.locations != "") | np.isin(self.ids, tuple(pins))

    def fingerprint(self) -> str:
        digest = sha256()
        for field in fields(self):
            value = np.ascontiguousarray(getattr(self, field.name))
            digest.update(field.name.encode())
            digest.update(value.dtype.str.encode())
            digest.update(str(value.shape).encode())
            digest.update(value.tobytes())
        return digest.hexdigest()

    def with_states(
        self,
        *,
        sub_rolls: NDArray[np.uint8] | None = None,
        levels: NDArray[np.uint8] | None = None,
    ) -> ArtifactBatch:
        """Return a new batch with simulator-visible enhancement state."""

        values = {field.name: getattr(self, field.name) for field in fields(self)}
        if sub_rolls is not None:
            if sub_rolls.shape != self.sub_rolls.shape:
                raise ValueError("sub_rolls replacement has invalid shape")
            values["sub_rolls"] = _readonly(sub_rolls, np.uint8)
        if levels is not None:
            if levels.shape != self.levels.shape:
                raise ValueError("levels replacement has invalid shape")
            values["levels"] = _readonly(levels, np.uint8)
            values["invested_exp"] = _readonly(
                np.asarray(
                    [
                        _CUMULATIVE_EXP[int(level)] if rarity == 5 else 0
                        for level, rarity in zip(levels, self.rarities)
                    ]
                ),
                np.int64,
            )
        return ArtifactBatch(**values)


def _artifact_id(artifact: Mapping[str, Any], index: int) -> str:
    supplied = artifact.get("id")
    if supplied is not None:
        return str(supplied)
    stable = {
        "setKey": artifact.get("setKey"),
        "slotKey": artifact.get("slotKey"),
        "mainStatKey": artifact.get("mainStatKey"),
        "level": artifact.get("level"),
        "rarity": artifact.get("rarity"),
        "substats": artifact.get("substats"),
        "unactivatedSubstats": artifact.get("unactivatedSubstats"),
        "location": artifact.get("location", ""),
    }
    raw = json.dumps(stable, sort_keys=True, separators=(",", ":")).encode()
    return f"a-{index}-{sha256(raw).hexdigest()[:16]}"


def _roll_coefficient(stat: int, value: float) -> int:
    return int(np.clip(round(float(value) / SUBSTAT_MAX[stat] * 10), 0, 255))


# Cumulative five-star artifact EXP at each level.
_CUMULATIVE_EXP = np.array(
    (
        0,
        3000,
        6725,
        11150,
        16300,
        22200,
        28875,
        36375,
        44725,
        53950,
        64075,
        75125,
        87150,
        100175,
        115325,
        132925,
        153300,
        176800,
        203850,
        234900,
        270475,
    ),
    dtype=np.int64,
)


def cumulative_artifact_exp(level: int) -> int:
    if not 0 <= level <= 20:
        raise ValueError("artifact level must be between 0 and 20")
    return int(_CUMULATIVE_EXP[level])


def from_good_data(data: Mapping[str, Any]) -> ArtifactBatch:
    if data.get("format") != "GOOD" or int(data.get("version", -1)) != 3:
        raise ValueError("only GOOD v3 input is supported")
    artifacts = data.get("artifacts")
    if not isinstance(artifacts, list):
        raise ValueError("GOOD input has no artifact list")

    count = len(artifacts)
    ids: list[str] = []
    set_keys: list[str] = []
    slots = np.empty(count, dtype=np.uint8)
    mains = np.empty(count, dtype=np.uint8)
    rarities = np.empty(count, dtype=np.uint8)
    levels = np.empty(count, dtype=np.uint8)
    starting_lines = np.empty(count, dtype=np.uint8)
    sub_rolls = np.zeros((count, len(SUBSTAT_KEYS)), dtype=np.uint8)
    initial_rolls = np.zeros_like(sub_rolls)
    uncertain = np.empty(count, dtype=np.bool_)
    four_line_probability = np.empty(count, dtype=np.float64)
    locations: list[str] = []
    locked = np.empty(count, dtype=np.bool_)
    starred = np.empty(count, dtype=np.bool_)
    invested_exp = np.empty(count, dtype=np.int64)

    for i, artifact in enumerate(artifacts):
        try:
            slot = SLOT_INDEX[str(artifact["slotKey"])]
            main = STAT_INDEX[str(artifact["mainStatKey"])]
        except KeyError as exc:
            raise ValueError(f"artifact {i} has an unknown slot or stat: {exc}") from exc

        ids.append(_artifact_id(artifact, i))
        set_keys.append(str(artifact["setKey"]))
        slots[i] = slot
        mains[i] = main
        rarities[i] = int(artifact.get("rarity", 5))
        level = int(artifact.get("level", 0))
        if not 0 <= level <= 20:
            raise ValueError(f"artifact {i} has invalid level {level}")
        levels[i] = level
        starting_lines[i], uncertain[i], four_line_probability[i] = _infer_starting_lines(
            artifact
        )
        locations.append(str(artifact.get("location", "")))
        locked[i] = bool(artifact.get("lock", False))
        starred[i] = bool(artifact.get("astralMark", False))
        invested_exp[i] = _CUMULATIVE_EXP[level] if rarities[i] == 5 else 0

        all_substats = list(artifact.get("substats") or []) + list(
            artifact.get("unactivatedSubstats") or []
        )
        if rarities[i] != 5:
            starting_lines[i] = min(4, len(all_substats))
            uncertain[i] = False
            four_line_probability[i] = float(starting_lines[i] == 4)
        for substat in all_substats:
            key = str(substat.get("key"))
            if key not in STAT_INDEX or STAT_INDEX[key] >= len(SUBSTAT_KEYS):
                raise ValueError(f"artifact {i} has invalid substat {key!r}")
            stat = STAT_INDEX[key]
            sub_rolls[i, stat] = _roll_coefficient(stat, float(substat["value"]))
            initial = substat.get("initialValue")
            if initial is not None:
                initial_rolls[i, stat] = _roll_coefficient(stat, float(initial))

    return ArtifactBatch(
        ids=_readonly(np.asarray(ids), np.str_),
        set_keys=_readonly(np.asarray(set_keys), np.str_),
        slots=_readonly(slots, np.uint8),
        main_stats=_readonly(mains, np.uint8),
        rarities=_readonly(rarities, np.uint8),
        levels=_readonly(levels, np.uint8),
        starting_lines=_readonly(starting_lines, np.uint8),
        sub_rolls=_readonly(sub_rolls, np.uint8),
        initial_sub_rolls=_readonly(initial_rolls, np.uint8),
        uncertain_history=_readonly(uncertain, np.bool_),
        four_line_probability=_readonly(four_line_probability, np.float64),
        locations=_readonly(np.asarray(locations), np.str_),
        locked=_readonly(locked, np.bool_),
        starred=_readonly(starred, np.bool_),
        invested_exp=_readonly(invested_exp, np.int64),
    )


def load_good(path: str | Path) -> tuple[ArtifactBatch, dict[str, Any]]:
    with Path(path).open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("GOOD input must be a JSON object")
    return from_good_data(data), data


def concatenate_batches(*batches: ArtifactBatch) -> ArtifactBatch:
    if not batches:
        raise ValueError("at least one batch is required")
    return ArtifactBatch(
        **{
            field.name: _readonly(
                np.concatenate([getattr(batch, field.name) for batch in batches], axis=0),
                getattr(batches[0], field.name).dtype,
            )
            for field in fields(batches[0])
        }
    )
