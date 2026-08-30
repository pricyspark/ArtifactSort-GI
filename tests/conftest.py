from __future__ import annotations

from typing import Iterable

import pytest

from artifact_sort.model import SUBSTAT_MAX, from_good_data


def good_artifact(
    index: int,
    slot: str,
    *,
    level: int = 20,
    high: bool = False,
    set_key: str = "TestSet",
    starred: bool = False,
) -> dict[str, object]:
    main = {"flower": "hp", "plume": "atk"}.get(slot, "atk_")
    stats = ("critRate_", "critDMG_", "enerRech_", "atk_")
    coefficient = 18 if high else 8
    substats = [
        {
            "key": key,
            "value": float(coefficient * SUBSTAT_MAX[i] / 10),
            "initialValue": float(8 * SUBSTAT_MAX[i] / 10),
        }
        for key, i in zip(stats, (8, 9, 6, 4))
        if key != main
    ]
    if main in stats:
        substats.append(
            {
                "key": "hp_",
                "value": float(coefficient * SUBSTAT_MAX[3] / 10),
                "initialValue": float(8 * SUBSTAT_MAX[3] / 10),
            }
        )
    return {
        "id": f"artifact-{index}",
        "setKey": set_key,
        "slotKey": slot,
        "mainStatKey": main,
        "rarity": 5,
        "level": level,
        "totalRolls": 4 + level // 4,
        "substats": substats,
        "unactivatedSubstats": [],
        "location": "",
        "lock": True,
        "astralMark": starred,
    }


@pytest.fixture
def small_batch():
    artifacts = []
    index = 0
    for slot in ("flower", "plume", "sands", "goblet", "circlet"):
        artifacts.append(good_artifact(index, slot, high=False))
        index += 1
        artifacts.append(good_artifact(index, slot, high=True))
        index += 1
    return from_good_data({"format": "GOOD", "version": 3, "artifacts": artifacts})
