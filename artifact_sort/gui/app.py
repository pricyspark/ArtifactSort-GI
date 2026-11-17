from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
from pathlib import Path
from threading import Lock, Thread
import time
from typing import Any, Mapping, Sequence
from urllib.parse import urlparse
from uuid import uuid4
import webbrowser

from .backend import AnalysisBackend, ImportedAccount, PortfolioBackend

STATIC_ROOT = Path(__file__).with_name("static")
MAX_REQUEST_BYTES = 40 * 1024 * 1024


@dataclass(slots=True)
class Job:
    id: str
    kind: str
    status: str = "queued"
    progress: float = 0.0
    message: str = "Waiting to start"
    result: Mapping[str, Any] | None = None
    error: str | None = None
    created_at: float = field(default_factory=time.time)

    def view(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "status": self.status,
            "progress": self.progress,
            "message": self.message,
            "result": self.result,
            "error": self.error,
        }


class AppState:
    def __init__(self, backend: AnalysisBackend):
        self.backend = backend
        self.accounts: dict[str, ImportedAccount] = {}
        self.jobs: dict[str, Job] = {}
        self.lock = Lock()

    def import_account(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        inventory = payload.get("inventory")
        if not isinstance(inventory, Mapping):
            raise ValueError("Choose a GOOD v3 inventory JSON file")
        raw_inventory = inventory.get("data")
        if not isinstance(raw_inventory, Mapping):
            raise ValueError("The inventory file is not a JSON object")
        profile = payload.get("goDatabase")
        raw_profile = profile.get("data") if isinstance(profile, Mapping) else None
        if raw_profile is not None and not isinstance(raw_profile, Mapping):
            raise ValueError("The GO database file is not a JSON object")
        account = self.backend.import_files(
            raw_inventory,
            str(inventory.get("name") or "inventory.json"),
            raw_profile,
            (
                str(profile.get("name") or "go-database.json")
                if isinstance(profile, Mapping)
                else None
            ),
        )
        session_id = uuid4().hex
        with self.lock:
            self.accounts[session_id] = account
        overview = self.backend.overview(account)
        return {"sessionId": session_id, **overview}

    def create_job(self, payload: Mapping[str, Any]) -> Job:
        session_id = str(payload.get("sessionId") or "")
        kind = str(payload.get("kind") or "")
        with self.lock:
            account = self.accounts.get(session_id)
        if account is None:
            raise ValueError("Your inventory session expired. Please import it again.")
        if kind not in {"cleanup", "library-cleanup", "upgrades"}:
            raise ValueError("Unknown analysis type")
        job = Job(uuid4().hex, kind)
        with self.lock:
            self.jobs[job.id] = job
        Thread(
            target=self._run_job,
            args=(job, account, payload),
            daemon=True,
            name=f"artifact-sort-{kind}",
        ).start()
        return job

    def _run_job(
        self, job: Job, account: ImportedAccount, payload: Mapping[str, Any]
    ) -> None:
        def report(progress: float, message: str) -> None:
            with self.lock:
                job.progress = max(job.progress, min(0.99, progress))
                job.message = message

        try:
            with self.lock:
                job.status = "running"
                job.message = "Starting analysis"
            if job.kind == "cleanup":
                free = int(payload.get("free", 100))
                result = self.backend.cleanup(account, free, report)
            elif job.kind == "library-cleanup":
                result = self.backend.library_cleanup(account, payload, report)
            else:
                result = self.backend.upgrades(account, report)
            with self.lock:
                job.result = result
                job.status = "complete"
                job.progress = 1.0
                job.message = "Ready to review"
        except Exception as exc:  # Keep analysis failures inside the job contract.
            with self.lock:
                job.status = "failed"
                job.error = str(exc) or exc.__class__.__name__
                job.message = "Analysis could not be completed"


class GuiRequestHandler(BaseHTTPRequestHandler):
    server_version = "ArtifactSortGUI/1"

    @property
    def state(self) -> AppState:
        return self.server.app_state  # type: ignore[attr-defined]

    def log_message(self, format: str, *args: object) -> None:
        return

    def _security_headers(self) -> None:
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cache-Control", "no-store")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self'; "
            "img-src 'self' data:; connect-src 'self'",
        )

    def _json(self, value: object, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(value, separators=(",", ":")).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._security_headers()
        self.end_headers()
        self.wfile.write(body)

    def _payload(self) -> Mapping[str, Any]:
        content_type = self.headers.get_content_type()
        if content_type != "application/json":
            raise ValueError("Requests must use JSON")
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > MAX_REQUEST_BYTES:
            raise ValueError("The selected files are too large")
        value = json.loads(self.rfile.read(length))
        if not isinstance(value, Mapping):
            raise ValueError("Request must be a JSON object")
        return value

    def do_POST(self) -> None:
        try:
            path = urlparse(self.path).path
            if path == "/api/import":
                self._json(self.state.import_account(self._payload()))
                return
            if path == "/api/jobs":
                job = self.state.create_job(self._payload())
                self._json(job.view(), HTTPStatus.ACCEPTED)
                return
            self._json({"error": "Not found"}, HTTPStatus.NOT_FOUND)
        except (ValueError, json.JSONDecodeError) as exc:
            self._json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
        except Exception as exc:
            self._json(
                {"error": str(exc) or "The request could not be completed"},
                HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/health":
            self._json({"status": "ok", "apiVersion": 1})
            return
        if path.startswith("/api/jobs/"):
            job_id = path.rsplit("/", 1)[-1]
            with self.state.lock:
                job = self.state.jobs.get(job_id)
                view = job.view() if job else None
            if view is None:
                self._json({"error": "Job not found"}, HTTPStatus.NOT_FOUND)
            else:
                self._json(view)
            return
        relative = "index.html" if path in {"", "/"} else path.lstrip("/")
        candidate = (STATIC_ROOT / relative).resolve()
        if (
            STATIC_ROOT.resolve() not in candidate.parents
            and candidate != STATIC_ROOT.resolve()
        ):
            self._json({"error": "Not found"}, HTTPStatus.NOT_FOUND)
            return
        if not candidate.is_file():
            self._json({"error": "Not found"}, HTTPStatus.NOT_FOUND)
            return
        body = candidate.read_bytes()
        self.send_response(HTTPStatus.OK)
        content_type = (
            mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"
        )
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self._security_headers()
        self.end_headers()
        self.wfile.write(body)


def create_server(
    host: str = "127.0.0.1",
    port: int = 0,
    backend: AnalysisBackend | None = None,
) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer((host, port), GuiRequestHandler)
    server.app_state = AppState(  # type: ignore[attr-defined]
        backend or PortfolioBackend()
    )
    return server


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Start the Artifact Sort app")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-open", action="store_true", help="do not open a browser")
    args = parser.parse_args(argv)
    server = create_server(args.host, args.port)
    url = f"http://{args.host}:{server.server_address[1]}"
    print(f"Artifact Sort is running at {url}")
    print("Press Ctrl+C to stop. Your files stay on this computer.")
    if not args.no_open:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Artifact Sort.")
    finally:
        server.server_close()
    return 0
