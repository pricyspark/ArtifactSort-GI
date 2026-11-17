"""Content-addressed numerical work for encoded deletion analysis.

Cache completed searches, sampled populations, and individual upgrade tapes.
Protection metadata remains current. Interrupted searches are never certified
or persisted, and a changed candidate domain is never a cached optimum.
"""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import fields, is_dataclass, replace
from hashlib import sha256
import json
import math
from types import MappingProxyType
from typing import Mapping, Sequence, cast

import numpy as np

from .artifact_sampling import SamplingRules, finish_artifact, sample_slot
from .cache import ResultCache
from .formulas import Json
from .inventory import (
    Artifact,
    Build,
    Inventory,
    MAIN_STAT_REVISION,
    LEVEL_CAP_REVISION,
)
from .library_runtime import CompiledScenario, EVALUATOR_VERSION, Evaluation
from .library_search import ScoredBuild, SearchResult

CACHE_VERSION = "encoded-intermediates-1"


def _canonical(value: object) -> Json:
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    if isinstance(value, Mapping):
        return {str(key): _canonical(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_canonical(item) for item in value]
    if isinstance(value, (set, frozenset)):
        return [_canonical(item) for item in sorted(value)]
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _canonical(getattr(value, field.name))
            for field in fields(value)
        }
    raise TypeError(f"unsupported cache key value: {type(value).__name__}")


def _digest(value: object) -> str:
    return sha256(
        json.dumps(_canonical(value), sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _artifact_data(artifact: Artifact) -> dict[str, Json]:
    # Scores and upgrade tapes do not depend on stars, locks, or equipment.
    return {
        "id": artifact.id,
        "set_key": artifact.set_key,
        "slot": artifact.slot,
        "main_stat": artifact.main_stat,
        "rarity": artifact.rarity,
        "level": artifact.level,
        "substats": dict(artifact.substats),
        "hidden_substats": dict(artifact.hidden_substats),
    }


def _stats(value: Json) -> Mapping[str, float]:
    if not isinstance(value, dict) or any(
        isinstance(number, bool)
        or not isinstance(number, (int, float))
        or not math.isfinite(number)
        for number in value.values()
    ):
        raise ValueError("invalid cached stats")
    return MappingProxyType(
        {key: float(cast(float, number)) for key, number in value.items()}
    )


def _artifact(value: Json) -> Artifact:
    data = cast(dict[str, Json], value)
    return Artifact(
        cast(str, data["id"]),
        cast(str, data["set_key"]),
        cast(str, data["slot"]),
        cast(str, data["main_stat"]),
        cast(int, data["rarity"]),
        cast(int, data["level"]),
        _stats(data["substats"]),
        _stats(data["hidden_substats"]),
    )


def _scored_data(value: ScoredBuild) -> dict[str, Json]:
    return {
        "ids": list(value.build.artifact_ids),
        "stats": dict(value.build.stats),
        "sets": dict(value.build.set_counts),
        "mains": dict(value.build.main_stats),
        "score": value.evaluation.score,
        "effective": dict(value.evaluation.effective_stats),
        "channels": dict(value.evaluation.channels),
        "violations": list(value.evaluation.violations),
    }


def _scored(value: Json) -> ScoredBuild:
    data = cast(dict[str, Json], value)
    score = data["score"]
    if (
        isinstance(score, bool)
        or not isinstance(score, (int, float))
        or not math.isfinite(score)
    ):
        raise ValueError("invalid cached score")
    return ScoredBuild(
        Build(
            tuple(cast(list[str], data["ids"])),
            _stats(data["stats"]),
            MappingProxyType(cast(dict[str, int], data["sets"])),
            MappingProxyType(cast(dict[str, str], data["mains"])),
        ),
        Evaluation(
            float(score),
            _stats(data["effective"]),
            _stats(data["channels"]),
            tuple(cast(list[str], data["violations"])),
        ),
    )


class AnalysisCache:
    """One run's shared numerical cache, optionally backed by SQLite.

    Fingerprints of immutable objects are memoized while retaining their objects,
    avoiding identity reuse. Upgrade reads/writes are batched per inventory.
    """

    def __init__(self, persistent: ResultCache | None = None) -> None:
        self.persistent = persistent
        self.searches: OrderedDict[str, SearchResult] = OrderedDict()
        self.populations: OrderedDict[str, Inventory] = OrderedDict()
        self.upgrades: dict[str, Artifact] = {}
        self.fingerprints: OrderedDict[int, tuple[object, str]] = OrderedDict()
        self.counts: dict[str, dict[str, int]] = {}

    def _count(self, kind: str, event: str, amount: int = 1) -> None:
        counts = self.counts.setdefault(kind, {})
        counts[event] = counts.get(event, 0) + amount

    def _fingerprint(self, value: object, content: object) -> str:
        identity = id(value)
        if identity not in self.fingerprints:
            self.fingerprints[identity] = (value, _digest(content))
            if len(self.fingerprints) > 8192:
                self.fingerprints.popitem(last=False)
        self.fingerprints.move_to_end(identity)
        return self.fingerprints[identity][1]

    def search_key(
        self,
        scenario: CompiledScenario,
        candidates: Sequence[Sequence[Artifact]],
        top_k: int,
        max_evaluations: int,
        seed: int,
        collect_contexts: bool,
    ) -> str:
        scenario_hash = self._fingerprint(scenario, scenario)
        pieces = [
            [self._fingerprint(a, _artifact_data(a)) for a in group]
            for group in candidates
        ]
        return _digest(
            [
                CACHE_VERSION,
                EVALUATOR_VERSION,
                MAIN_STAT_REVISION,
                LEVEL_CAP_REVISION,
                scenario_hash,
                pieces,
                top_k,
                max_evaluations,
                seed,
                collect_contexts,
            ]
        )

    def get_search(self, key: str) -> SearchResult | None:
        if key in self.searches:
            self.searches.move_to_end(key)
            self._count("search", "memoryHits")
            return self.searches[key]
        data = (
            None
            if self.persistent is None
            else self.persistent.get("encoded-search", key)
        )
        if isinstance(data, dict):
            try:
                if data["status"] not in ("exact", "approximate"):
                    raise ValueError("incomplete cached search")
                result = SearchResult(
                    tuple(_scored(value) for value in data["builds"]),
                    data["status"],
                    data["evaluated"],
                    data["combinations"],
                    tuple(_scored(value) for value in data["contexts"]),
                )
                self._remember_search(key, result)
                self._count("search", "persistentHits")
                return result
            except (KeyError, TypeError, ValueError, AttributeError):
                pass
        self._count("search", "misses")
        return None

    def _remember_search(self, key: str, result: SearchResult) -> None:
        self.searches[key] = result
        self.searches.move_to_end(key)
        if len(self.searches) > 512:
            self.searches.popitem(last=False)

    def put_search(self, key: str, result: SearchResult) -> None:
        if result.status == "timed_out":
            self._count("search", "interrupted")
            return
        self._remember_search(key, result)
        self._count("search", "writes")
        if self.persistent is not None:
            self.persistent.put(
                "encoded-search",
                key,
                {
                    "status": result.status,
                    "evaluated": result.evaluated,
                    "combinations": result.combinations,
                    "builds": [_scored_data(value) for value in result.builds],
                    "contexts": [
                        _scored_data(value) for value in result.context_builds
                    ],
                },
            )

    def completed_inventory(
        self, inventory: Inventory, rules: SamplingRules, *, seed: int, trial: int
    ) -> Inventory:
        if type(seed) is not int or type(trial) is not int or trial < 0:
            raise ValueError("seed must be an integer and trial a nonnegative integer")
        keys = [
            _digest(
                [
                    CACHE_VERSION,
                    "coupled-upgrades-1",
                    MAIN_STAT_REVISION,
                    rules.fingerprint,
                    seed,
                    trial,
                    _artifact_data(a),
                ]
            )
            for a in inventory.artifacts
        ]
        missing = [key for key in keys if key not in self.upgrades]
        stored = (
            {}
            if self.persistent is None
            else self.persistent.get_many("encoded-upgrade", missing)
        )
        writes: dict[str, Json] = {}
        completed = []
        for key, artifact in zip(keys, inventory.artifacts):
            finished = self.upgrades.get(key)
            if finished is not None:
                self._count("upgrade", "memoryHits")
            elif key in stored:
                try:
                    finished = _artifact(stored[key])
                    self._count("upgrade", "persistentHits")
                except (KeyError, TypeError, ValueError, AttributeError):
                    finished = None
            if finished is None:
                self._count("upgrade", "misses")
                payload = json.dumps(
                    ["coupled-upgrades-1", seed, trial, artifact.id, rules.fingerprint]
                )
                entropy = int.from_bytes(sha256(payload.encode()).digest(), "big")
                finished = finish_artifact(
                    artifact, rules, np.random.default_rng(entropy)
                )
                writes[key] = _artifact_data(finished)
                self._count("upgrade", "writes")
            self.upgrades[key] = finished
            completed.append(
                replace(
                    artifact,
                    level=finished.level,
                    substats=finished.substats,
                    hidden_substats=finished.hidden_substats,
                )
            )
        if self.persistent is not None:
            self.persistent.put_many("encoded-upgrade", writes)
        return Inventory(tuple(completed))

    def population(
        self, slot: str, set_key: str, count: int, rules: SamplingRules, *, seed: int
    ) -> Inventory:
        key = _digest(
            [
                CACHE_VERSION,
                "sample-slot-1",
                MAIN_STAT_REVISION,
                rules.fingerprint,
                slot,
                set_key,
                count,
                seed,
            ]
        )
        if key in self.populations:
            self.populations.move_to_end(key)
            self._count("population", "memoryHits")
            return self.populations[key]
        data = (
            None
            if self.persistent is None
            else self.persistent.get("encoded-population", key)
        )
        result = None
        if isinstance(data, list):
            try:
                result = Inventory(tuple(_artifact(value) for value in data))
                self._count("population", "persistentHits")
            except (KeyError, TypeError, ValueError, AttributeError):
                pass
        if result is None:
            self._count("population", "misses")
            result = sample_slot(slot, set_key, count, rules, seed=seed)
            self._count("population", "writes")
            if self.persistent is not None:
                self.persistent.put(
                    "encoded-population",
                    key,
                    [_artifact_data(a) for a in result.artifacts],
                )
        self.populations[key] = result
        if len(self.populations) > 128:
            self.populations.popitem(last=False)
        return result

    def summary(self) -> dict[str, Json]:
        return {kind: dict(counts) for kind, counts in self.counts.items()}
