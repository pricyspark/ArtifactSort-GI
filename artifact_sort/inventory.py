"""Lossless GOOD import and legal builds for the encoded-library pipeline.

Legacy ArtifactBatch uses rounded roll coefficients and percentage points.
This boundary preserves scanner values and normalizes percentages exactly once.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from hashlib import sha256
from importlib.resources import files
import json
import math
from pathlib import Path
from types import MappingProxyType
from typing import Iterable, Mapping, cast

from .formulas import Json, Stats
from .library_runtime import CompiledScenario, Evaluation, LEGAL_MAINS
from .model import SLOT_KEYS, STAT_KEYS, SUBSTAT_KEYS

_TABLE = json.loads(
    files("artifact_sort").joinpath("artifact-main-stats.json").read_text()
)
MAIN_STAT_REVISION: str = _TABLE["commit"]
MAIN_STAT_SOURCE: str = _TABLE["source"]
LEVEL_CAP_REVISION: str = _TABLE["level_cap_commit"]
MAIN_STATS: Mapping[int, Mapping[str, tuple[float, ...]]] = MappingProxyType(
    {
        int(rarity): MappingProxyType(
            {
                key: tuple(
                    float(value) for value in values[: _TABLE["level_caps"][rarity] + 1]
                )
                for key, values in stats.items()
            }
        )
        for rarity, stats in _TABLE["stats"].items()
    }
)
del _TABLE


def main_stat_value(rarity: int, key: str, level: int) -> float:
    if type(rarity) is not int or rarity not in MAIN_STATS:
        raise ValueError(f"unsupported rarity {rarity!r}")
    if key not in MAIN_STATS[rarity]:
        raise ValueError(f"unknown main stat {key!r}")
    values = MAIN_STATS[rarity][key]
    if type(level) is not int or not 0 <= level < len(values):
        raise ValueError(f"invalid level {level!r} for rarity {rarity}")
    return values[level]


@dataclass(frozen=True, slots=True)
class Artifact:
    id: str
    set_key: str
    slot: str
    main_stat: str
    rarity: int
    level: int
    substats: Stats
    hidden_substats: Stats
    locked: bool = False
    starred: bool = False
    location: str = ""

    def __post_init__(self) -> None:
        if not self.id or not self.set_key:
            raise ValueError("artifact needs a nonempty identity and set key")
        if self.slot not in LEGAL_MAINS or self.main_stat not in LEGAL_MAINS[self.slot]:
            raise ValueError(
                f"{self.id}: illegal main stat {self.slot}.{self.main_stat}"
            )
        main_stat_value(self.rarity, self.main_stat, self.level)
        for field in ("substats", "hidden_substats"):
            stats = dict(getattr(self, field))
            for key, value in stats.items():
                if key not in SUBSTAT_KEYS or key == self.main_stat:
                    raise ValueError(f"{self.id}: illegal substat {key!r}")
                if isinstance(value, bool) or not math.isfinite(value) or value < 0:
                    raise ValueError(f"{self.id}: invalid substat value {key!r}")
            object.__setattr__(self, field, MappingProxyType(stats))
        if self.substats.keys() & self.hidden_substats.keys():
            raise ValueError(f"{self.id}: duplicate active/hidden substat")
        if len(self.substats) + len(self.hidden_substats) > 4:
            raise ValueError(f"{self.id}: more than four substats")
        if self.hidden_substats and self.level >= 4:
            raise ValueError(f"{self.id}: hidden substats at level >= 4")

    @property
    def stats(self) -> Stats:
        """Actual current additions; hidden lines and future main growth excluded."""
        return MappingProxyType(
            {
                **self.substats,
                self.main_stat: main_stat_value(
                    self.rarity, self.main_stat, self.level
                ),
            }
        )


@dataclass(frozen=True, slots=True)
class Inventory:
    artifacts: tuple[Artifact, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "artifacts", tuple(self.artifacts))
        ids = [artifact.id for artifact in self.artifacts]
        if len(set(ids)) != len(ids):
            raise ValueError("artifact identities must be unique")

    def select(
        self, available_ids: Iterable[str] | None = None
    ) -> tuple[Artifact, ...]:
        if available_ids is None:
            return self.artifacts
        available = frozenset(available_ids)
        unknown = available - {artifact.id for artifact in self.artifacts}
        if unknown:
            raise ValueError(f"unknown available identities: {sorted(unknown)}")
        return tuple(
            artifact for artifact in self.artifacts if artifact.id in available
        )

    def fingerprint(self) -> str:
        content = {
            "units": "decimal-ratios",
            "main_stats": MAIN_STAT_REVISION,
            "level_caps": LEVEL_CAP_REVISION,
            "artifacts": [
                {
                    "id": a.id,
                    "set": a.set_key,
                    "slot": a.slot,
                    "main": a.main_stat,
                    "rarity": a.rarity,
                    "level": a.level,
                    "substats": dict(a.substats),
                    "hidden": dict(a.hidden_substats),
                    "locked": a.locked,
                    "starred": a.starred,
                    "location": a.location,
                }
                for a in sorted(self.artifacts, key=lambda a: a.id)
            ],
        }
        return sha256(json.dumps(content, sort_keys=True).encode()).hexdigest()

    def protected_ids(self, pinned_ids: Iterable[str] = ()) -> frozenset[str]:
        """Stars, equipped pieces, and explicit pins; ordinary locks confer no protection."""
        pinned = frozenset(pinned_ids)
        self.select(pinned)  # Reject stale or mistyped explicit pins.
        return pinned | frozenset(
            a.id for a in self.artifacts if a.starred or a.location
        )


@dataclass(frozen=True, slots=True)
class Build:
    artifact_ids: tuple[str, ...]
    stats: Stats
    set_counts: Mapping[str, int]
    main_stats: Mapping[str, str]


def assemble_build(artifacts: Iterable[Artifact]) -> Build:
    pieces = tuple(sorted(artifacts, key=lambda a: SLOT_KEYS.index(a.slot)))
    if len(pieces) != 5 or len({a.slot for a in pieces}) != 5:
        raise ValueError("a build requires exactly one artifact in each of five slots")
    if len({a.id for a in pieces}) != 5:
        raise ValueError("a build requires five distinct artifact identities")
    stats = {key: 0.0 for key in STAT_KEYS}
    for artifact in pieces:
        for key, value in artifact.stats.items():
            stats[key] += value
    return Build(
        tuple(a.id for a in pieces),
        MappingProxyType(stats),
        MappingProxyType(dict(Counter(a.set_key for a in pieces))),
        MappingProxyType({a.slot: a.main_stat for a in pieces}),
    )


def evaluate_build(
    scenario: CompiledScenario, artifacts: Iterable[Artifact]
) -> Evaluation:
    build = assemble_build(artifacts)
    return scenario.evaluate(build.stats, build.set_counts, main_stats=build.main_stats)


def _object(value: Json, name: str) -> dict[str, Json]:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be an object")
    return value


def _text(value: Json, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be a nonempty string")
    return value


def _integer(value: Json, name: str) -> int:
    if type(value) is not int:
        raise ValueError(f"{name} must be an integer")
    return value


def _flag(value: Json, name: str) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{name} must be a boolean")
    return value


def _good_substats(value: Json, name: str) -> dict[str, float]:
    if not isinstance(value, list):
        raise ValueError(f"{name} must be a list")
    result: dict[str, float] = {}
    for item in value:
        node = _object(item, name)
        key = _text(node.get("key"), f"{name}.key")
        number = node.get("value")
        if isinstance(number, bool) or not isinstance(number, (int, float)):
            raise ValueError(f"{name}.{key} must be numeric")
        if key in result:
            raise ValueError(f"{name}: duplicate substat {key!r}")
        result[key] = float(number) / 100 if key.endswith("_") else float(number)
    return result


def inventory_from_good(data: Mapping[str, Json]) -> Inventory:
    if data.get("format") != "GOOD" or _integer(data.get("version"), "version") != 3:
        raise ValueError("only GOOD v3 inventory input is supported")
    items = data.get("artifacts")
    if not isinstance(items, list):
        raise ValueError("GOOD input must contain an artifacts list")
    artifacts: list[Artifact] = []
    generated_counts: Counter[str] = Counter()
    for index, item in enumerate(items):
        node = _object(item, f"artifact {index}")
        supplied = node.get("id")
        if supplied is None:
            digest = sha256(json.dumps(node, sort_keys=True).encode()).hexdigest()[:16]
            generated_counts[digest] += 1
            identity = f"good-{digest}-{generated_counts[digest]}"
        elif isinstance(supplied, (str, int)) and not isinstance(supplied, bool):
            identity = str(supplied)
        else:
            raise ValueError(f"artifact {index}: invalid identity")
        location = node.get("location", "")
        if not isinstance(location, str):
            raise ValueError(f"{identity}: location must be a string")
        artifacts.append(
            Artifact(
                identity,
                _text(node.get("setKey"), f"{identity}.setKey"),
                _text(node.get("slotKey"), f"{identity}.slotKey"),
                _text(node.get("mainStatKey"), f"{identity}.mainStatKey"),
                _integer(node.get("rarity", 5), f"{identity}.rarity"),
                _integer(node.get("level", 0), f"{identity}.level"),
                _good_substats(node.get("substats", []), f"{identity}.substats"),
                _good_substats(
                    node.get("unactivatedSubstats", []),
                    f"{identity}.unactivatedSubstats",
                ),
                _flag(node.get("lock", False), f"{identity}.lock"),
                _flag(node.get("astralMark", False), f"{identity}.astralMark"),
                location,
            )
        )
    return Inventory(tuple(artifacts))


def load_inventory(path: str | Path) -> Inventory:
    with Path(path).open(encoding="utf-8") as stream:
        data = cast(Json, json.load(stream))
    return inventory_from_good(_object(data, "GOOD input"))
