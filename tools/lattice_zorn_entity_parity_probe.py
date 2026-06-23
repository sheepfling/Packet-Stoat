#!/usr/bin/env python3
"""Probe entity REST↔gRPC parity against the pinned Zorn backend."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path
import sys
from typing import Any

import grpc
from google.protobuf.json_format import MessageToDict, ParseDict


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from artifacts import VERIFICATION_REPORTS_DIR
from fastdis.lattice_backend import load_lattice_backend_config


DEFAULT_OUT_DIR = VERIFICATION_REPORTS_DIR / "alpha5" / "lattice_zorn_entity_parity"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args()


def _check(name: str, status: str, detail: str = "") -> dict[str, str]:
    return {"name": name, "status": status, "detail": detail}


def _disposition(payload: dict[str, Any]) -> str | None:
    mil_view = payload.get("milView")
    if not isinstance(mil_view, dict):
        mil_view = payload.get("mil_view")
    if isinstance(mil_view, dict):
        value = mil_view.get("disposition")
        return value if isinstance(value, str) else None
    return None


def _run_probe(zorn_python: Path, checkout: Path, out_dir: Path) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    script_path = (out_dir / "zorn_entity_parity_probe_runtime.py").resolve()
    report_path = (out_dir / "zorn_entity_parity_probe_runtime.json").resolve()
    script_path.write_text(_PROBE_SCRIPT, encoding="utf-8")
    command = [
        str(zorn_python),
        str(script_path),
        "--repo-root",
        str(checkout),
        "--out",
        str(report_path),
    ]
    import subprocess

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
                "name": "entity_parity_probe",
                "status": "failed",
                "detail": "probe did not write a JSON report",
            }
        ],
    }


def build_report(out_dir: Path) -> dict[str, Any]:
    config = load_lattice_backend_config()
    checkout = config.checkout_path
    zorn_python = checkout / ".venv" / "bin" / "python"
    report: dict[str, Any] = {
        "schema": "fastdis.zorn.entity_parity.probe.v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "backend": config.backend,
        "transport": config.transport,
        "zorn_tag": config.tag,
        "zorn_checkout": str(checkout),
        "proof_source": "zorn-dual-transport-entity-parity",
        "real_lattice_verified": False,
        "zorn_python": str(zorn_python),
    }
    report.update(_run_probe(zorn_python, checkout, out_dir))
    return report


def write_report(report: dict[str, Any], out_dir: Path) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "zorn_entity_parity_probe_report.json"
    md_path = out_dir / "zorn_entity_parity_probe_report.md"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(_render_markdown(report), encoding="utf-8")
    return json_path, md_path


def _render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Zorn Entity REST to gRPC Parity Probe",
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
from pathlib import Path
from typing import Any
from urllib import error, request

import grpc
from google.protobuf.json_format import MessageToDict, ParseDict

from zorn.cert.runners.common import start_http_insecure_grpc_zorn_server, stop_dual_transport_zorn_server
from zorn.grpc_api.proto_modules import load_lattice_proto_modules


def _check(name: str, status: str, detail: str = "") -> dict[str, str]:
    return {"name": name, "status": status, "detail": detail}


def _http_json(method: str, url: str, *, token: str, payload: dict[str, object] | None = None) -> tuple[int, dict[str, Any]]:
    body = None
    headers = {"Authorization": f"Bearer {token}"}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = request.Request(url, data=body, method=method, headers=headers)
    try:
        with request.urlopen(req, timeout=10.0) as response:
            raw = response.read().decode("utf-8")
            return int(response.status), dict(json.loads(raw)) if raw else {}
    except error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        parsed = dict(json.loads(raw)) if raw else {}
        return int(exc.code), parsed


def _disposition(payload: dict[str, Any]) -> str | None:
    mil_view = payload.get("milView")
    if not isinstance(mil_view, dict):
        mil_view = payload.get("mil_view")
    if isinstance(mil_view, dict):
        disposition = mil_view.get("disposition")
        return disposition if isinstance(disposition, str) else None
    return None


async def _run(repo_root: Path) -> dict[str, Any]:
    token = "dev-token"
    server = start_http_insecure_grpc_zorn_server(repo_root=repo_root, token=token)
    checks: list[dict[str, str]] = []
    evidence: dict[str, Any] = {
        "rest_base_url": server.rest_base_url,
        "grpc_target": server.grpc_target,
    }
    proto_modules = load_lattice_proto_modules()
    metadata = (("authorization", f"Bearer {token}"),)
    try:
        async with grpc.aio.insecure_channel(server.grpc_target) as channel:
            stub = proto_modules.entity_api_grpc.EntityManagerAPIStub(channel)

            rest_publish_status, rest_publish_payload = _http_json(
                "PUT",
                f"{server.rest_base_url}/api/v1/entities",
                token=token,
                payload={
                    "entityId": "parity-rest-entity",
                    "description": "REST parity entity",
                    "isLive": True,
                    "noExpiry": True,
                },
            )
            if rest_publish_status != 200:
                return {"overall_status": "failed", "checks": [_check("rest_publish", "failed", json.dumps(rest_publish_payload, sort_keys=True))], "gaps": []}
            checks.append(_check("rest_publish", "passed", "entity published through REST"))

            fetched_rest = await stub.GetEntity(proto_modules.entity_api.GetEntityRequest(entity_id="parity-rest-entity"), metadata=metadata)
            checks.append(_check("rest_publish_visible_via_grpc_get", "passed" if fetched_rest.entity.entity_id == "parity-rest-entity" else "failed", "gRPC GetEntity saw REST entity"))

            grpc_entity = proto_modules.entity.Entity(entity_id="parity-grpc-entity", description="gRPC parity entity", is_live=True, no_expiry=True)
            await stub.PublishEntity(proto_modules.entity_api.PublishEntityRequest(entity=grpc_entity), metadata=metadata)
            checks.append(_check("grpc_publish", "passed", "entity published through gRPC"))

            grpc_rest_status, grpc_rest_payload = _http_json("GET", f"{server.rest_base_url}/api/v1/entities/parity-grpc-entity", token=token)
            checks.append(_check("grpc_publish_visible_via_rest_get", "passed" if grpc_rest_status == 200 and grpc_rest_payload.get("entityId") == "parity-grpc-entity" else "failed", json.dumps(grpc_rest_payload, sort_keys=True)))

            rest_override_entity_id = "parity-rest-override-entity"
            _http_json("PUT", f"{server.rest_base_url}/api/v1/entities", token=token, payload={"entityId": rest_override_entity_id, "description": "before override", "isLive": True, "noExpiry": True})
            rest_override_status, rest_override_payload = _http_json("PUT", f"{server.rest_base_url}/api/v1/entities/{rest_override_entity_id}/override/mil_view.disposition", token=token, payload={"entity": {"milView": {"disposition": "DISPOSITION_HOSTILE"}}})
            fetched_override_rest = await stub.GetEntity(
                proto_modules.entity_api.GetEntityRequest(entity_id=rest_override_entity_id),
                metadata=metadata,
            )
            fetched_override_rest_entity = MessageToDict(
                fetched_override_rest.entity,
                preserving_proto_field_name=True,
            )
            checks.append(
                _check(
                    "rest_override_visible_via_grpc_get",
                    "passed"
                    if rest_override_status == 200
                    and _disposition(fetched_override_rest_entity) == "DISPOSITION_HOSTILE"
                    else "failed",
                    json.dumps(fetched_override_rest_entity, sort_keys=True),
                )
            )

            grpc_override_entity_id = "parity-grpc-override-entity"
            _http_json("PUT", f"{server.rest_base_url}/api/v1/entities", token=token, payload={"entityId": grpc_override_entity_id, "description": "before override", "isLive": True, "noExpiry": True})
            override_entity = proto_modules.entity.Entity()
            ParseDict({"entityId": grpc_override_entity_id, "milView": {"disposition": "DISPOSITION_HOSTILE"}}, override_entity, ignore_unknown_fields=True)
            override_request = getattr(proto_modules.entity_api, "OverrideEntityRequest")(entity=override_entity)
            override_request.field_path.append("mil_view.disposition")
            await stub.OverrideEntity(override_request, metadata=metadata)
            grpc_override_status, grpc_override_payload = _http_json("GET", f"{server.rest_base_url}/api/v1/entities/{grpc_override_entity_id}", token=token)
            checks.append(_check("grpc_override_visible_via_rest_get", "passed" if grpc_override_status == 200 and _disposition(grpc_override_payload) == "DISPOSITION_HOSTILE" else "failed", json.dumps(grpc_override_payload, sort_keys=True)))

            remove_request = getattr(proto_modules.entity_api, "RemoveEntityOverrideRequest")(entity_id=grpc_override_entity_id)
            remove_request.field_path.append("mil_view.disposition")
            await stub.RemoveEntityOverride(remove_request, metadata=metadata)
            grpc_remove_status, grpc_remove_payload = _http_json("GET", f"{server.rest_base_url}/api/v1/entities/{grpc_override_entity_id}", token=token)
            checks.append(_check("grpc_remove_override_visible_via_rest_get", "passed" if grpc_remove_status == 200 and _disposition(grpc_remove_payload) in {None, "", "DISPOSITION_UNKNOWN"} else "failed", json.dumps(grpc_remove_payload, sort_keys=True)))

            rest_non_live_status, _rest_non_live_payload = _http_json("PUT", f"{server.rest_base_url}/api/v1/entities", token=token, payload={"entityId": "parity-rest-non-live-entity", "isLive": False, "noExpiry": True})
            fetched_non_live_rest = await stub.GetEntity(proto_modules.entity_api.GetEntityRequest(entity_id="parity-rest-non-live-entity"), metadata=metadata)
            checks.append(_check("rest_non_live_visible_via_grpc_get", "passed" if rest_non_live_status == 200 and fetched_non_live_rest.entity.is_live is False else "failed", "gRPC saw REST non-live state"))

            non_live_entity = proto_modules.entity.Entity(entity_id="parity-grpc-non-live-entity", description="gRPC non-live parity entity", is_live=False, no_expiry=True)
            await stub.PublishEntity(proto_modules.entity_api.PublishEntityRequest(entity=non_live_entity), metadata=metadata)
            grpc_non_live_status, grpc_non_live_payload = _http_json("GET", f"{server.rest_base_url}/api/v1/entities/parity-grpc-non-live-entity", token=token)
            checks.append(_check("grpc_non_live_visible_via_rest_get", "passed" if grpc_non_live_status == 200 and grpc_non_live_payload.get("isLive") is False else "failed", json.dumps(grpc_non_live_payload, sort_keys=True)))
    finally:
        logs = stop_dual_transport_zorn_server(server)
        evidence["rest_server_log_tail"] = logs.get("rest", "")[-4000:]
        evidence["grpc_server_log_tail"] = logs.get("grpc", "")[-4000:]

    failed = [check for check in checks if check["status"] == "failed"]
    gaps = [f"{check['name']}: {check['detail']}" for check in failed]
    return {"overall_status": "ready" if not failed else "ready-with-gaps", "checks": checks, "evidence": evidence, "gaps": gaps}


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
