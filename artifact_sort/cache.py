from __future__ import annotations

from contextlib import closing
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
from typing import Any


SCHEMA_VERSION = 1
MECHANICS_VERSION = "genshin-artifact-2026-08"
ALGORITHM_VERSION = "portfolio-v1"


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


@dataclass(slots=True)
class ResultCache:
    path: Path

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
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

    def get(self, namespace: str, key: str) -> Any | None:
        try:
            with closing(sqlite3.connect(self.path)) as connection:
                row = connection.execute(
                    "SELECT schema_version, value FROM cache WHERE namespace=? AND key=?",
                    (namespace, key),
                ).fetchone()
        except sqlite3.DatabaseError:
            return None
        if row is None or row[0] != SCHEMA_VERSION:
            return None
        try:
            return json.loads(row[1])
        except json.JSONDecodeError:
            return None

    def put(self, namespace: str, key: str, value: Any) -> None:
        payload = json.dumps(value, separators=(",", ":"), sort_keys=True)
        with closing(sqlite3.connect(self.path)) as connection:
            connection.execute(
                """
                INSERT INTO cache(namespace, key, schema_version, value)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(namespace, key) DO UPDATE SET
                    schema_version=excluded.schema_version,
                    value=excluded.value
                """,
                (namespace, key, SCHEMA_VERSION, payload),
            )
            connection.commit()

    def clear(self) -> None:
        with closing(sqlite3.connect(self.path)) as connection:
            connection.execute("DELETE FROM cache")
            connection.commit()
