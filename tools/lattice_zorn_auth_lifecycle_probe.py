#!/usr/bin/env python3
"""Probe Zorn auth lifecycle realism for REST and gRPC."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from artifacts import VERIFICATION_REPORTS_DIR
from fastdis.lattice_backend import load_lattice_backend_config


DEFAULT_OUT_DIR = VERIFICATION_REPORTS_DIR / "alpha5" / "lattice_zorn_auth_lifecycle"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args()


def _find_zorn_python(checkout: Path) -> Path | None:
    env_override = os.environ.get("FASTDIS_LATTICE_BACKEND_PYTHON")
    if env_override:
        candidate = Path(env_override).resolve()
        if candidate.is_file():
            return candidate
    for candidate in (
        checkout / ".venv" / "bin" / "python",
        checkout / ".venv" / "Scripts" / "python.exe",
    ):
        if candidate.is_file():
            return candidate
    return None


def _write_probe_script(out_dir: Path) -> Path:
    runtime_path = Path(__file__).with_name("lattice_zorn_auth_lifecycle_probe_runtime.py").resolve()
    if runtime_path.is_file():
        return runtime_path
    out_dir.mkdir(parents=True, exist_ok=True)
    script_path = (out_dir / "zorn_auth_lifecycle_probe_runtime.py").resolve()
    script_path.write_text(_PROBE_SCRIPT, encoding="utf-8")
    return script_path


def _run_probe(zorn_python: Path, checkout: Path, out_dir: Path) -> dict[str, Any]:
    script_path = _write_probe_script(out_dir)
    report_path = (out_dir / "zorn_auth_lifecycle_probe_runtime.json").resolve()
    command = [
        str(zorn_python),
        str(script_path),
        "--repo-root",
        str(checkout),
        "--out",
        str(report_path),
    ]
    completed = subprocess.run(command, cwd=checkout, check=False, text=True, capture_output=True)
    if report_path.is_file():
        payload = json.loads(report_path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            payload["probe_returncode"] = completed.returncode
            payload["probe_stdout"] = completed.stdout
            payload["probe_stderr"] = completed.stderr
            return payload
    return {
        "overall_status": "failed",
        "probe_returncode": completed.returncode,
        "probe_stdout": completed.stdout,
        "probe_stderr": completed.stderr,
        "checks": [
            {
                "name": "auth_lifecycle_probe",
                "status": "failed",
                "detail": "probe did not write a JSON report",
            }
        ],
    }


def build_report(out_dir: Path) -> dict[str, Any]:
    config = load_lattice_backend_config()
    checkout = config.checkout_path
    zorn_python = _find_zorn_python(checkout)
    report: dict[str, Any] = {
        "schema": "fastdis.zorn.auth_lifecycle.probe.v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "backend": config.backend,
        "transport": config.transport,
        "zorn_tag": config.tag,
        "zorn_checkout": str(checkout),
        "proof_source": "zorn-rest-grpc-auth-lifecycle",
        "real_lattice_verified": False,
    }
    if not checkout.is_dir():
        report.update(
            {
                "overall_status": "failed",
                "checks": [{"name": "zorn_checkout", "status": "failed", "detail": str(checkout)}],
            }
        )
        return report
    if zorn_python is None:
        report.update(
            {
                "overall_status": "failed",
                "checks": [{"name": "zorn_python", "status": "failed", "detail": f"python not found under {checkout}"}],
            }
        )
        return report
    report["zorn_python"] = str(zorn_python)
    report.update(_run_probe(zorn_python, checkout, out_dir))
    return report


def write_report(report: dict[str, Any], out_dir: Path) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "zorn_auth_lifecycle_probe_report.json"
    md_path = out_dir / "zorn_auth_lifecycle_probe_report.md"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(_render_markdown(report), encoding="utf-8")
    return json_path, md_path


def _render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Zorn Auth Lifecycle Probe",
        "",
        f"- overall_status: `{report.get('overall_status', 'unknown')}`",
        f"- proof_source: `{report.get('proof_source', 'unknown')}`",
        f"- zorn_tag: `{report.get('zorn_tag', 'unknown')}`",
        f"- real_lattice_verified: `{str(report.get('real_lattice_verified')).lower()}`",
        "",
        "## Checks",
        "",
    ]
    for check in report.get("checks", []):
        if isinstance(check, dict):
            lines.append(f"- `{check.get('name')}`: `{check.get('status')}` - {check.get('detail', '')}")
    gaps = report.get("gaps", [])
    if gaps:
        lines.extend(["", "## Gaps", ""])
        for gap in gaps:
            lines.append(f"- {gap}")
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    report = build_report(args.out_dir)
    json_path, md_path = write_report(report, args.out_dir)
    print(json.dumps({"overall_status": report["overall_status"], "json": str(json_path), "markdown": str(md_path)}, indent=2))
    return 0 if report["overall_status"] in {"ready", "ready-with-gaps"} else 1


_PROBE_SCRIPT = r'''
from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import tempfile
import time
from typing import Any
from urllib import error, request

import grpc

from zorn.grpc_api.proto_modules import load_lattice_proto_modules


def _check(name: str, status: str, detail: str = "") -> dict[str, str]:
    return {"name": name, "status": status, "detail": detail}


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as handle:
        handle.bind(("127.0.0.1", 0))
        return int(handle.getsockname()[1])


def _tcp_ready(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.5):
            return True
    except OSError:
        return False


def _http_json(
    method: str,
    url: str,
    *,
    headers: dict[str, str] | None = None,
    payload: dict[str, object] | None = None,
) -> tuple[int, dict[str, Any]]:
    body = None
    request_headers = dict(headers or {})
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        request_headers["Content-Type"] = "application/json"
    req = request.Request(url, data=body, method=method, headers=request_headers)
    try:
        with request.urlopen(req, timeout=10.0) as response:
            raw = response.read().decode("utf-8")
            return int(response.status), dict(json.loads(raw)) if raw else {}
    except error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        parsed = dict(json.loads(raw)) if raw else {}
        return int(exc.code), parsed


class DualServer:
    def __init__(
        self,
        *,
        repo_root: Path,
        auth_mode: str,
        token: str,
        require_sandbox_header: bool = False,
        oauth_dev_token_ttl_seconds: int | None = None,
        oauth_scope_mode: str | None = None,
        grpc_sandbox_auth_mode: str | None = None,
    ) -> None:
        self.repo_root = repo_root
        self.auth_mode = auth_mode
        self.token = token
        self.require_sandbox_header = require_sandbox_header
        self.oauth_dev_token_ttl_seconds = oauth_dev_token_ttl_seconds
        self.oauth_scope_mode = oauth_scope_mode
        self.grpc_sandbox_auth_mode = grpc_sandbox_auth_mode
        self.workspace = Path(tempfile.mkdtemp(prefix="fastdis-zorn-auth-"))
        self.db_path = self.workspace / "zorn.db"
        self.object_root = self.workspace / "objects"
        self.object_root.mkdir(parents=True, exist_ok=True)
        self.rest_port = _free_port()
        self.grpc_port = _free_port()
        self.rest_base_url = f"http://127.0.0.1:{self.rest_port}"
        self.grpc_target = f"127.0.0.1:{self.grpc_port}"
        self.rest_process: subprocess.Popen[str] | None = None
        self.grpc_process: subprocess.Popen[str] | None = None

    def start(self) -> None:
        env = os.environ.copy()
        env.update(
            {
                "PYTHONPATH": str(self.repo_root / "src") + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else ""),
                "C2_COMPAT_AUTH_MODE": self.auth_mode,
                "C2_COMPAT_STATIC_TOKENS": self.token,
                "C2_COMPAT_REQUIRE_SANDBOX_HEADER": "true" if self.require_sandbox_header else "false",
                "C2_COMPAT_DATABASE_URL": f"sqlite:///{self.db_path}",
                "C2_COMPAT_OBJECT_ROOT": str(self.object_root),
                "C2_COMPAT_GRPC_HOST": "127.0.0.1",
                "C2_COMPAT_GRPC_PORT": str(self.grpc_port),
                "C2_COMPAT_GRPC_TLS_MODE": "insecure",
            }
        )
        if self.oauth_dev_token_ttl_seconds is not None:
            env["C2_COMPAT_OAUTH_DEV_TOKEN_TTL_SECONDS"] = str(self.oauth_dev_token_ttl_seconds)
        if self.oauth_scope_mode is not None:
            env["C2_COMPAT_OAUTH_SCOPE_MODE"] = self.oauth_scope_mode
        if self.grpc_sandbox_auth_mode is not None:
            env["C2_COMPAT_GRPC_SANDBOX_AUTH_MODE"] = self.grpc_sandbox_auth_mode
        python = str(self.repo_root / ".venv" / "bin" / "python")
        self.rest_process = subprocess.Popen(
            [python, "-m", "uvicorn", "zorn.app:build_app", "--factory", "--host", "127.0.0.1", "--port", str(self.rest_port)],
            cwd=self.repo_root,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            start_new_session=True,
        )
        self.grpc_process = subprocess.Popen(
            [python, "-m", "zorn.main_grpc"],
            cwd=self.repo_root,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            start_new_session=True,
        )
        deadline = time.time() + 20.0
        last_error = ""
        while time.time() < deadline:
            if self.rest_process.poll() is not None:
                last_error = self.rest_process.stdout.read() if self.rest_process.stdout else ""
                break
            if self.grpc_process.poll() is not None:
                last_error = self.grpc_process.stdout.read() if self.grpc_process.stdout else ""
                break
            try:
                status, payload = _http_json(
                    "POST",
                    f"{self.rest_base_url}/api/v1/oauth/token",
                    payload={"client_id": "fastdis-auth-probe", "client_secret": "fastdis-auth-probe", "scope": "entities tasks objects"},
                )
                if status == 200 and payload.get("access_token") and _tcp_ready("127.0.0.1", self.grpc_port):
                    return
                last_error = json.dumps(payload, sort_keys=True)
            except Exception as exc:  # noqa: BLE001
                last_error = str(exc)
            time.sleep(0.2)
        self.stop()
        raise RuntimeError(f"dual auth server failed readiness check: {last_error}")

    def stop(self) -> dict[str, str]:
        outputs: dict[str, str] = {}
        for name, process in (("rest", self.rest_process), ("grpc", self.grpc_process)):
            if process is None:
                continue
            process.terminate()
            try:
                stdout, _stderr = process.communicate(timeout=10.0)
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, _stderr = process.communicate(timeout=5.0)
            outputs[name] = stdout
        shutil.rmtree(self.workspace, ignore_errors=True)
        return outputs


async def _run(repo_root: Path) -> dict[str, Any]:
    proto_modules = load_lattice_proto_modules()
    checks: list[dict[str, str]] = []
    evidence: dict[str, Any] = {}
    gaps = [
        "OAuth refresh semantics are not exposed on either REST or gRPC.",
        "Token scope is only validated at issuance when oauth_scope_mode is locked; request-time scope enforcement is not exposed on REST or gRPC.",
        "There is no vendor-like refresh/revocation lifecycle to exercise beyond expiring oauth-dev tokens.",
    ]

    static_server = DualServer(repo_root=repo_root, auth_mode="static", token="dev-token")
    sandbox_server = DualServer(repo_root=repo_root, auth_mode="static", token="dev-token", require_sandbox_header=True)
    oauth_server = DualServer(repo_root=repo_root, auth_mode="oauth-dev", token="dev-token")
    oauth_expiring_server = DualServer(
        repo_root=repo_root,
        auth_mode="oauth-dev",
        token="dev-token",
        oauth_dev_token_ttl_seconds=1,
    )
    oauth_locked_server = DualServer(
        repo_root=repo_root,
        auth_mode="oauth-dev",
        token="dev-token",
        oauth_scope_mode="locked",
    )
    grpc_strict_server = DualServer(
        repo_root=repo_root,
        auth_mode="static",
        token="dev-token",
        require_sandbox_header=True,
        grpc_sandbox_auth_mode="strict_separate",
    )
    none_server = DualServer(repo_root=repo_root, auth_mode="none", token="dev-token")
    try:
        static_server.start()
        sandbox_server.start()
        oauth_server.start()
        oauth_expiring_server.start()
        oauth_locked_server.start()
        grpc_strict_server.start()
        none_server.start()

        missing_status, missing_payload = _http_json("GET", f"{static_server.rest_base_url}/api/v1/entities/missing")
        checks.append(_check("rest_missing_bearer_rejected", "passed" if missing_status == 401 else "failed", json.dumps(missing_payload, sort_keys=True)))

        invalid_status, invalid_payload = _http_json(
            "GET",
            f"{static_server.rest_base_url}/api/v1/entities/missing",
            headers={"Authorization": "Bearer wrong-token"},
        )
        checks.append(_check("rest_invalid_bearer_rejected", "passed" if invalid_status == 403 else "failed", json.dumps(invalid_payload, sort_keys=True)))

        expired_status, expired_payload = _http_json(
            "GET",
            f"{static_server.rest_base_url}/api/v1/entities/missing",
            headers={"Authorization": "Bearer expired-token"},
        )
        checks.append(_check("rest_expired_bearer_rejected", "passed" if expired_status == 403 else "failed", json.dumps(expired_payload, sort_keys=True)))

        valid_status, valid_payload = _http_json(
            "PUT",
            f"{static_server.rest_base_url}/api/v1/entities",
            headers={"Authorization": "Bearer dev-token"},
            payload={"entityId": "static-auth-entity", "isLive": True},
        )
        checks.append(_check("rest_static_environment_token_accepted", "passed" if valid_status == 200 else "failed", json.dumps(valid_payload, sort_keys=True)))

        api_key_status, api_key_payload = _http_json(
            "PUT",
            f"{static_server.rest_base_url}/api/v1/entities",
            headers={"x-api-key": "dev-token"},
            payload={"entityId": "static-api-key-entity", "isLive": True},
        )
        checks.append(_check("rest_x_api_key_accepted", "passed" if api_key_status == 200 else "failed", json.dumps(api_key_payload, sort_keys=True)))

        sandbox_only_status, sandbox_only_payload = _http_json(
            "GET",
            f"{sandbox_server.rest_base_url}/api/v1/entities/missing",
            headers={"Anduril-Sandbox-Authorization": "Bearer dev-token"},
        )
        checks.append(
            _check(
                "rest_sandbox_header_without_bearer_rejected",
                "passed" if sandbox_only_status == 401 else "failed",
                json.dumps(sandbox_only_payload, sort_keys=True),
            )
        )

        no_sandbox_status, no_sandbox_payload = _http_json(
            "GET",
            f"{sandbox_server.rest_base_url}/api/v1/entities/missing",
            headers={"Authorization": "Bearer dev-token"},
        )
        checks.append(_check("rest_missing_sandbox_header_rejected", "passed" if no_sandbox_status == 403 else "failed", json.dumps(no_sandbox_payload, sort_keys=True)))

        with_sandbox_status, with_sandbox_payload = _http_json(
            "PUT",
            f"{sandbox_server.rest_base_url}/api/v1/entities",
            headers={
                "Authorization": "Bearer dev-token",
                "Anduril-Sandbox-Authorization": "Bearer dev-token",
            },
            payload={"entityId": "sandbox-auth-entity", "isLive": True},
        )
        checks.append(_check("rest_sandbox_header_accepted", "passed" if with_sandbox_status == 200 else "failed", json.dumps(with_sandbox_payload, sort_keys=True)))

        oauth_status, oauth_payload = _http_json(
            "POST",
            f"{oauth_server.rest_base_url}/api/v1/oauth/token",
            payload={"client_id": "fastdis", "client_secret": "fastdis", "scope": "entities streams"},
        )
        oauth_token = str(oauth_payload.get("access_token", ""))
        oauth_ok = oauth_status == 200 and bool(oauth_token)
        checks.append(_check("rest_oauth_client_credentials", "passed" if oauth_ok else "failed", json.dumps(oauth_payload, sort_keys=True)))

        oauth_entity_status, oauth_entity_payload = _http_json(
            "PUT",
            f"{oauth_server.rest_base_url}/api/v1/entities",
            headers={"Authorization": f"Bearer {oauth_token}"},
            payload={"entityId": "oauth-auth-entity", "isLive": True},
        )
        checks.append(_check("rest_oauth_issued_token_accepted", "passed" if oauth_entity_status == 200 else "failed", json.dumps(oauth_entity_payload, sort_keys=True)))

        expiring_issue_status, expiring_issue_payload = _http_json(
            "POST",
            f"{oauth_expiring_server.rest_base_url}/api/v1/oauth/token",
            payload={"client_id": "fastdis", "client_secret": "fastdis", "scope": "entities"},
        )
        expiring_token = str(expiring_issue_payload.get("access_token", ""))
        checks.append(
            _check(
                "rest_oauth_dev_expiring_token_issued",
                "passed" if expiring_issue_status == 200 and bool(expiring_token) and int(expiring_issue_payload.get("expires_in", 0)) == 1 else "failed",
                json.dumps(expiring_issue_payload, sort_keys=True),
            )
        )
        expiring_immediate_status, expiring_immediate_payload = _http_json(
            "PUT",
            f"{oauth_expiring_server.rest_base_url}/api/v1/entities",
            headers={"Authorization": f"Bearer {expiring_token}"},
            payload={"entityId": "oauth-expiring-entity", "isLive": True},
        )
        checks.append(
            _check(
                "rest_oauth_dev_token_before_expiry_accepted",
                "passed" if expiring_immediate_status == 200 else "failed",
                json.dumps(expiring_immediate_payload, sort_keys=True),
            )
        )
        time.sleep(2.0)
        expiring_after_status, expiring_after_payload = _http_json(
            "GET",
            f"{oauth_expiring_server.rest_base_url}/api/v1/entities/oauth-expiring-entity",
            headers={"Authorization": f"Bearer {expiring_token}"},
        )
        checks.append(
            _check(
                "rest_oauth_dev_token_after_expiry_rejected",
                "passed" if expiring_after_status == 403 else "failed",
                json.dumps(expiring_after_payload, sort_keys=True),
            )
        )

        locked_issue_status, locked_issue_payload = _http_json(
            "POST",
            f"{oauth_locked_server.rest_base_url}/api/v1/oauth/token",
            payload={"client_id": "fastdis", "client_secret": "fastdis", "scope": "entities tasks"},
        )
        checks.append(
            _check(
                "rest_oauth_scope_locked_rejects_requested_scope",
                "passed" if locked_issue_status == 400 else "failed",
                json.dumps(locked_issue_payload, sort_keys=True),
            )
        )
        locked_default_status, locked_default_payload = _http_json(
            "POST",
            f"{oauth_locked_server.rest_base_url}/api/v1/oauth/token",
            payload={"client_id": "fastdis", "client_secret": "fastdis"},
        )
        checks.append(
            _check(
                "rest_oauth_scope_locked_accepts_unspecified_scope",
                "passed" if locked_default_status == 200 else "failed",
                json.dumps(locked_default_payload, sort_keys=True),
            )
        )

        none_status, none_payload = _http_json(
            "PUT",
            f"{none_server.rest_base_url}/api/v1/entities",
            payload={"entityId": "none-auth-entity", "isLive": True},
        )
        checks.append(_check("rest_auth_mode_none_accepts_without_headers", "passed" if none_status == 200 else "failed", json.dumps(none_payload, sort_keys=True)))

        async with grpc.aio.insecure_channel(static_server.grpc_target) as channel:
            entity_stub = proto_modules.entity_api_grpc.EntityManagerAPIStub(channel)
            await entity_stub.PublishEntity(
                proto_modules.entity_api.PublishEntityRequest(
                    entity=proto_modules.entity.Entity(
                        entity_id="grpc-static-auth-entity",
                        description="grpc auth",
                        is_live=True,
                        no_expiry=True,
                    )
                ),
                metadata=(("authorization", "Bearer dev-token"),),
            )
            grpc_static = await entity_stub.GetEntity(
                proto_modules.entity_api.GetEntityRequest(entity_id="grpc-static-auth-entity"),
                metadata=(("x-api-key", "dev-token"),),
            )
            checks.append(_check("grpc_static_bearer_metadata_accepted", "passed" if grpc_static.entity.entity_id == "grpc-static-auth-entity" else "failed", grpc_static.entity.entity_id))
            try:
                await entity_stub.GetEntity(
                    proto_modules.entity_api.GetEntityRequest(entity_id="missing"),
                    metadata=(("authorization", "Bearer wrong-token"),),
                )
            except grpc.aio.AioRpcError as exc:
                checks.append(_check("grpc_invalid_bearer_rejected", "passed" if exc.code() == grpc.StatusCode.UNAUTHENTICATED else "failed", str(exc.code())))
            else:
                checks.append(_check("grpc_invalid_bearer_rejected", "failed", "invalid token unexpectedly accepted"))

            try:
                await entity_stub.GetEntity(
                    proto_modules.entity_api.GetEntityRequest(entity_id="missing"),
                    metadata=(("authorization", "Bearer expired-token"),),
                )
            except grpc.aio.AioRpcError as exc:
                checks.append(_check("grpc_expired_bearer_rejected", "passed" if exc.code() == grpc.StatusCode.UNAUTHENTICATED else "failed", str(exc.code())))
            else:
                checks.append(_check("grpc_expired_bearer_rejected", "failed", "expired token unexpectedly accepted"))

        async with grpc.aio.insecure_channel(static_server.grpc_target) as channel:
            entity_stub = proto_modules.entity_api_grpc.EntityManagerAPIStub(channel)
            await entity_stub.PublishEntity(
                proto_modules.entity_api.PublishEntityRequest(
                    entity=proto_modules.entity.Entity(
                        entity_id="grpc-api-key-auth-entity",
                        description="grpc api key auth",
                        is_live=True,
                        no_expiry=True,
                    )
                ),
                metadata=(("x-api-key", "dev-token"),),
            )
            grpc_api_key = await entity_stub.GetEntity(
                proto_modules.entity_api.GetEntityRequest(entity_id="grpc-api-key-auth-entity"),
                metadata=(("x-api-key", "dev-token"),),
            )
            checks.append(_check("grpc_x_api_key_accepted", "passed" if grpc_api_key.entity.entity_id == "grpc-api-key-auth-entity" else "failed", grpc_api_key.entity.entity_id))

        async with grpc.aio.insecure_channel(sandbox_server.grpc_target) as channel:
            entity_stub = proto_modules.entity_api_grpc.EntityManagerAPIStub(channel)
            await entity_stub.PublishEntity(
                proto_modules.entity_api.PublishEntityRequest(
                    entity=proto_modules.entity.Entity(
                        entity_id="grpc-sandbox-auth-entity",
                        description="grpc sandbox auth",
                        is_live=True,
                        no_expiry=True,
                    )
                ),
                metadata=(("anduril-sandbox-authorization", "Bearer dev-token"),),
            )
            grpc_sandbox = await entity_stub.GetEntity(
                proto_modules.entity_api.GetEntityRequest(entity_id="grpc-sandbox-auth-entity"),
                metadata=(("anduril-sandbox-authorization", "Bearer dev-token"),),
            )
            checks.append(_check("grpc_sandbox_header_as_bearer_accepted", "passed" if grpc_sandbox.entity.entity_id == "grpc-sandbox-auth-entity" else "failed", grpc_sandbox.entity.entity_id))

        async with grpc.aio.insecure_channel(grpc_strict_server.grpc_target) as channel:
            entity_stub = proto_modules.entity_api_grpc.EntityManagerAPIStub(channel)
            try:
                await entity_stub.GetEntity(
                    proto_modules.entity_api.GetEntityRequest(entity_id="missing"),
                    metadata=(("anduril-sandbox-authorization", "Bearer dev-token"),),
                )
            except grpc.aio.AioRpcError as exc:
                checks.append(
                    _check(
                        "grpc_strict_sandbox_bearer_only_rejected",
                        "passed" if exc.code() == grpc.StatusCode.UNAUTHENTICATED else "failed",
                        str(exc.code()),
                    )
                )
            else:
                checks.append(_check("grpc_strict_sandbox_bearer_only_rejected", "failed", "sandbox bearer unexpectedly accepted"))
            await entity_stub.PublishEntity(
                proto_modules.entity_api.PublishEntityRequest(
                    entity=proto_modules.entity.Entity(
                        entity_id="grpc-strict-sandbox-entity",
                        description="grpc strict sandbox auth",
                        is_live=True,
                        no_expiry=True,
                    )
                ),
                metadata=(("x-anduril-sandbox", "true"), ("authorization", "Bearer dev-token")),
            )
            grpc_strict = await entity_stub.GetEntity(
                proto_modules.entity_api.GetEntityRequest(entity_id="grpc-strict-sandbox-entity"),
                metadata=(("x-anduril-sandbox", "true"), ("authorization", "Bearer dev-token")),
            )
            checks.append(
                _check(
                    "grpc_strict_sandbox_header_plus_bearer_accepted",
                    "passed" if grpc_strict.entity.entity_id == "grpc-strict-sandbox-entity" else "failed",
                    grpc_strict.entity.entity_id,
                )
            )

        async with grpc.aio.insecure_channel(oauth_server.grpc_target) as channel:
            entity_stub = proto_modules.entity_api_grpc.EntityManagerAPIStub(channel)
            await entity_stub.PublishEntity(
                proto_modules.entity_api.PublishEntityRequest(
                    entity=proto_modules.entity.Entity(
                        entity_id="grpc-oauth-auth-entity",
                        description="grpc oauth auth",
                        is_live=True,
                        no_expiry=True,
                    )
                ),
                metadata=(("authorization", f"Bearer {oauth_token}"),),
            )
            grpc_oauth = await entity_stub.GetEntity(
                proto_modules.entity_api.GetEntityRequest(entity_id="grpc-oauth-auth-entity"),
                metadata=(("authorization", f"Bearer {oauth_token}"),),
            )
            checks.append(_check("grpc_oauth_issued_token_accepted", "passed" if grpc_oauth.entity.entity_id == "grpc-oauth-auth-entity" else "failed", grpc_oauth.entity.entity_id))

        async with grpc.aio.insecure_channel(none_server.grpc_target) as channel:
            entity_stub = proto_modules.entity_api_grpc.EntityManagerAPIStub(channel)
            await entity_stub.PublishEntity(
                proto_modules.entity_api.PublishEntityRequest(
                    entity=proto_modules.entity.Entity(
                        entity_id="grpc-none-auth-entity",
                        description="grpc none auth",
                        is_live=True,
                        no_expiry=True,
                    )
                )
            )
            grpc_none = await entity_stub.GetEntity(
                proto_modules.entity_api.GetEntityRequest(entity_id="grpc-none-auth-entity"),
            )
            checks.append(_check("grpc_auth_mode_none_accepts_without_headers", "passed" if grpc_none.entity.entity_id == "grpc-none-auth-entity" else "failed", grpc_none.entity.entity_id))

        evidence["oauth_expires_in"] = oauth_payload.get("expires_in")
        evidence["oauth_scope"] = oauth_payload.get("scope")
        evidence["oauth_expiring_expires_in"] = expiring_issue_payload.get("expires_in")
        evidence["oauth_locked_scope_mode"] = "locked"
        evidence["grpc_strict_sandbox_mode"] = "strict_separate"
    finally:
        evidence["static_logs"] = static_server.stop()
        evidence["sandbox_logs"] = sandbox_server.stop()
        evidence["oauth_logs"] = oauth_server.stop()
        evidence["oauth_expiring_logs"] = oauth_expiring_server.stop()
        evidence["oauth_locked_logs"] = oauth_locked_server.stop()
        evidence["grpc_strict_logs"] = grpc_strict_server.stop()
        evidence["none_logs"] = none_server.stop()

    failed = [check for check in checks if check["status"] == "failed"]
    return {
        "overall_status": "failed" if failed else "ready-with-gaps",
        "checks": checks,
        "gaps": gaps,
        "evidence": evidence,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = asyncio.run(_run(args.repo_root.resolve()))
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if payload["overall_status"] in {"ready", "ready-with-gaps"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
'''


if __name__ == "__main__":
    raise SystemExit(main())
