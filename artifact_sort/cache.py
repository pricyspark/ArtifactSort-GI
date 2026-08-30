from __future__ import annotations

from contextlib import closing
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
from typing import Any, Mapping, Sequence


SCHEMA_VERSION = 2
MECHANICS_VERSION = "genshin-artifact-2026-08"
ALGORITHM_VERSION = "portfolio-v2-layered-cache"


def cache_key(
    *,
    artifact_fingerprint: str,
    scenario_hash: str,
    evaluator_version: str,
    parameters: Any,
) -> str:
    payload = {
        "mechanics": MECHANICS_VERSION,
        "algorithm": ALGORITHM_VERSION,
        "artifacts": artifact_fingerprint,
        "scenarios": scenario_hash,
        "evaluator": evaluator_version,
        "parameters": parameters,
    }
    return sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


class ResultCache:
    __slots__ = ("path", "_hits", "_misses", "_writes")

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._hits: dict[str, int] = {}
        self._misses: dict[str, int] = {}
        self._writes: dict[str, int] = {}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.path)) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS cache (
                    namespace TEXT NOT NULL,
                    key TEXT NOT NULL,
                    schema_version INTEGER NOT NULL,
                    value TEXT NOT NULL,
                    PRIMARY KEY (namespace, key)
                )
                """
            )
            connection.execute(
                "DELETE FROM cache WHERE schema_version <> ?", (SCHEMA_VERSION,)
            )
            connection.commit()

    @staticmethod
    def _count(counters: dict[str, int], namespace: str, amount: int = 1) -> None:
        counters[namespace] = counters.get(namespace, 0) + amount

    def get(self, namespace: str, key: str, *, track: bool = True) -> Any | None:
        try:
            with closing(sqlite3.connect(self.path)) as connection:
                row = connection.execute(
                    "SELECT schema_version, value FROM cache WHERE namespace=? AND key=?",
                    (namespace, key),
                ).fetchone()
        except sqlite3.DatabaseError:
            if track:
                self._count(self._misses, namespace)
            return None
        if row is None or row[0] != SCHEMA_VERSION:
            if track:
                self._count(self._misses, namespace)
            return None
        try:
            value = json.loads(row[1])
        except json.JSONDecodeError:
            if track:
                self._count(self._misses, namespace)
            return None
        if track:
            self._count(self._hits, namespace)
        return value

    def record_lookup(self, namespace: str, *, hit: bool) -> None:
        self._count(self._hits if hit else self._misses, namespace)

    def get_many(self, namespace: str, keys: Sequence[str]) -> dict[str, Any]:
        unique = tuple(dict.fromkeys(keys))
        if not unique:
            return {}
        found: dict[str, Any] = {}
        try:
            with closing(sqlite3.connect(self.path)) as connection:
                for start in range(0, len(unique), 900):
                    chunk = unique[start : start + 900]
                    placeholders = ",".join("?" for _ in chunk)
                    rows = connection.execute(
                        f"SELECT key, schema_version, value FROM cache "
                        f"WHERE namespace=? AND key IN ({placeholders})",
                        (namespace, *chunk),
                    )
                    for key, schema_version, payload in rows:
                        if schema_version != SCHEMA_VERSION:
                            continue
                        try:
                            found[str(key)] = json.loads(payload)
                        except json.JSONDecodeError:
                            continue
        except sqlite3.DatabaseError:
            found = {}
        self._count(self._hits, namespace, len(found))
        self._count(self._misses, namespace, len(unique) - len(found))
        return found

    def put(self, namespace: str, key: str, value: Any) -> None:
        self.put_many(namespace, {key: value})

    def put_many(self, namespace: str, values: Mapping[str, Any]) -> None:
        if not values:
            return
        rows = [
            (
                namespace,
                key,
                SCHEMA_VERSION,
                json.dumps(value, separators=(",", ":"), sort_keys=True),
            )
            for key, value in values.items()
        ]
        with closing(sqlite3.connect(self.path)) as connection:
            connection.executemany(
                """
                INSERT INTO cache(namespace, key, schema_version, value)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(namespace, key) DO UPDATE SET
                    schema_version=excluded.schema_version,
                    value=excluded.value
                """,
                rows,
            )
            connection.commit()
        self._count(self._writes, namespace, len(rows))

    def summary(self) -> dict[str, object]:
        namespaces = sorted(set(self._hits) | set(self._misses) | set(self._writes))
        by_namespace = {
            namespace: {
                "hits": self._hits.get(namespace, 0),
                "misses": self._misses.get(namespace, 0),
                "writes": self._writes.get(namespace, 0),
            }
            for namespace in namespaces
        }
        return {
            "path": str(self.path),
            "hits": sum(self._hits.values()),
            "misses": sum(self._misses.values()),
            "writes": sum(self._writes.values()),
            "by_namespace": by_namespace,
        }

    def clear(self) -> None:
        with closing(sqlite3.connect(self.path)) as connection:
            connection.execute("DELETE FROM cache")
            connection.commit()
