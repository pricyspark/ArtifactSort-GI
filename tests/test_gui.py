from __future__ import annotations

from dataclasses import replace
import time
import pytest

from artifact_sort.gui.app import AppState
from artifact_sort.gui.backend import PortfolioBackend, _screening_proxy
from artifact_sort.scenarios import Scenario

from conftest import good_artifact


def _inventory() -> dict[str, object]:
    slots = ("flower", "plume", "sands", "goblet", "circlet")
    return {
        "format": "GOOD",
        "version": 3,
        "source": "Inventory_Kamera",
        "artifacts": [good_artifact(index, slots[index % 5]) for index in range(10)],
    }


def test_gui_backend_exposes_stable_inventory_overview(tmp_path):
    backend = PortfolioBackend(tmp_path / "gui-cache.sqlite")
    account = backend.import_files(_inventory(), "scan.json")

    overview = backend.overview(account)

    assert overview["apiVersion"] == 1
    assert overview["inventory"]["total"] == 10
    assert overview["inventory"]["source"] == "Inventory_Kamera"
    assert overview["coverage"]["mode"] == "broad"
    assert sum(slot["count"] for slot in overview["inventory"]["slots"]) == 10


def test_gui_import_removes_go_empty_substat_placeholders(tmp_path):
    inventory = _inventory()
    inventory["artifacts"][0]["substats"].append({"key": "", "value": 0})
    backend = PortfolioBackend(tmp_path / "gui-cache.sqlite")

    account = backend.import_files(inventory, "go-database.json")

    assert len(account.batch) == 10


def test_go_screening_cache_identity_drops_temporary_source_path():
    scenario = Scenario(
        id="go-test",
        metadata={"source_path": "/tmp/random-import-name.json", "team_id": "team-1"},
    )

    proxy = _screening_proxy(scenario)

    assert "source_path" not in proxy.metadata
    assert proxy.metadata["team_id"] == "team-1"


def test_go_reference_artifact_matches_inventory_with_a_different_id(tmp_path):
    backend = PortfolioBackend(tmp_path / "gui-cache.sqlite")
    account = backend.import_files(_inventory(), "scan.json")
    reference = dict(account.source_data["artifacts"][0])
    reference["id"] = "go-artifact-with-a-different-id"
    scenario = replace(
        account.scenarios[0],
        metadata={"reference_artifacts": (reference,)},
    )
    account = replace(account, scenarios=(scenario,))

    protected = backend._reference_artifact_ids(account)

    assert str(account.batch.ids[0]) in protected


def test_cleanup_explains_review_order(tmp_path):
    backend = PortfolioBackend(tmp_path / "gui-cache.sqlite")
    account = backend.import_files(_inventory(), "scan.json")

    result = backend.cleanup(account, 2, lambda progress, message: None)

    assert [item["reviewOrder"] for item in result["artifacts"]] == [1, 2]
    for item in result["artifacts"]:
        assert item["setLabel"]
        assert item["mainStatLabel"]
        evidence = item["evidence"]
        assert evidence["targetCount"] > 0
        assert evidence["alternatives"] > 0
        assert evidence["reasons"]
    assert "one complete set" in result["summary"]["orderExplanation"]

    repeated = backend.cleanup(account, 2, lambda progress, message: None)
    assert repeated["summary"]["cacheStatus"] == "hit"


class ImmediateBackend(PortfolioBackend):
    def upgrades(self, account, progress):
        progress(0.5, "Halfway")
        return {"apiVersion": 1, "kind": "upgrades", "artifacts": []}


def test_gui_jobs_hide_backend_objects_and_report_progress(tmp_path):
    app = AppState(ImmediateBackend(tmp_path / "gui-cache.sqlite"))
    imported = app.import_account(
        {"inventory": {"name": "scan.json", "data": _inventory()}}
    )
    job = app.create_job({"sessionId": imported["sessionId"], "kind": "upgrades"})

    deadline = time.monotonic() + 2
    while job.status not in {"complete", "failed"} and time.monotonic() < deadline:
        time.sleep(0.01)

    assert job.status == "complete"
    assert job.progress == 1.0
    assert job.view()["result"]["kind"] == "upgrades"


def test_gui_encoded_cleanup_reports_both_lists_and_missing_family_gap(tmp_path):
    from test_library import document

    backend = PortfolioBackend(tmp_path / "cache.sqlite")
    account = backend.import_files(_inventory(), "scan.json")
    library = document()
    payload = {
        "library": library,
        "mechanics": {
            "format": "artifact-sort-mechanics",
            "version": 1,
            "id": library["mechanics"],
            "game_version": "test",
            "sets": ["TestSet"],
        },
        "allowDraft": True,
        "free": 1,
        "trials": 1,
        "population": 16,
        "timeLimit": 10,
    }
    result = backend.library_cleanup(account, payload, lambda fraction, message: None)
    assert result["kind"] == "library-deletion-diagnostics" and result["draft"]
    assert set(result["selections"]) == {"established", "combined"}
    assert all(
        selection["status"] == "blocked" for selection in result["selections"].values()
    )
    assert "family" in result["selections"]["established"]["gaps"][0]["reason"]
    assert len(result["artifactViews"]) == 10
    with pytest.raises(ValueError):
        backend.library_cleanup(
            account, {**payload, "allowDraft": False}, lambda fraction, message: None
        )


def test_gui_dispatches_encoded_cleanup_job(tmp_path):
    class EncodedBackend(PortfolioBackend):
        def library_cleanup(self, account, payload, progress):
            assert payload["free"] == 2
            progress(0.5, "Comparing both coverage lists")
            return {"kind": "library-deletion-diagnostics", "selections": {}}

    app = AppState(EncodedBackend(tmp_path / "cache.sqlite"))
    imported = app.import_account(
        {"inventory": {"name": "scan.json", "data": _inventory()}}
    )
    job = app.create_job(
        {"sessionId": imported["sessionId"], "kind": "library-cleanup", "free": 2}
    )
    deadline = time.monotonic() + 2
    while job.status not in {"complete", "failed"} and time.monotonic() < deadline:
        time.sleep(0.01)
    assert job.status == "complete"
    assert job.view()["result"]["kind"] == "library-deletion-diagnostics"
