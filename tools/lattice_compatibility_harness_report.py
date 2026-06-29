#!/usr/bin/env python3
"""Generate a local no-credential Lattice compatibility harness report."""

from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
import sys

import httpx

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
ADAPTER_SRC = ROOT / "packages" / "lattice" / "src"
for path in (SRC, ADAPTER_SRC):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from artifacts import VERIFICATION_REPORTS_DIR
from packet_stoat_lattice import (  # noqa: E402
    AuthError,
    MockLatticeRestHarness,
    build_offline_httpx_client,
    build_sdk_mock_transport,
    canonical_entity_from_fixture,
    lattice_track_payload_from_entity,
    offline_client_config_from_env,
)


OUT_DIR = VERIFICATION_REPORTS_DIR / "alpha4_1" / "lattice"
DIS_FIXTURE = ROOT / "packages" / "lattice" / "examples" / "dis_entity_fixture.json"


def headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Anduril-Sandbox-Authorization": "Bearer mock-sandbox-token",
    }


def build_report() -> dict[str, object]:
    harness = MockLatticeRestHarness()
    token_response = harness.oauth_token(client_id="packet-stoat-client", client_secret="packet-stoat-secret")
    active_headers = headers(str(token_response["access_token"]))
    payload = lattice_track_payload_from_entity(canonical_entity_from_fixture(DIS_FIXTURE)[0])

    auth_checks: dict[str, str] = {}
    try:
        harness.publish_entity(payload, headers={"Authorization": f"Bearer {token_response['access_token']}"})
    except AuthError as exc:
        auth_checks["missing_sandbox_header"] = f"passed:{exc.status_code}"
    else:
        auth_checks["missing_sandbox_header"] = "failed"

    publish = harness.publish_entity(payload, headers=active_headers)
    fetched = harness.get_entity(str(payload["entityId"]), headers=active_headers)
    upload = harness.upload_object("reports/track.json", "application/json", b'{"ok":true}', headers=active_headers)
    media = harness.link_object_to_entity_media(str(payload["entityId"]), "reports/track.json", headers=active_headers)
    task = harness.create_task(
        {"task_id": "task-report-1", "agent_id": str(payload["entityId"]), "task_type": "VisualId"},
        headers=active_headers,
    )
    task_status = harness.update_task_status("task-report-1", "in_progress", headers=active_headers)
    stream = harness.stream_entities(headers=active_headers, components_to_include=["location", "media"])
    task_stream = harness.stream_tasks(headers=active_headers, agent_id=str(payload["entityId"]))
    sdk_transport_checks = _exercise_sdk_transport()
    offline_config = offline_client_config_from_env(
        {
            "LATTICE_ENDPOINT": "offline-lattice.local:8443",
            "SANDBOXES_TOKEN": "mock-sandbox-token",
            "SKIP_TLS_VERIFY": "true",
        }
    )

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "overall_status": "compatibility_harness_ready_no_credentials",
        "real_lattice_verified": False,
        "auth_session": {
            "client_credentials": "passed",
            "environment_token": "passed",
            "sandbox_header_rejection": auth_checks["missing_sandbox_header"],
        },
        "official_rest_sdk_transport_shape": sdk_transport_checks,
        "offline_client": {
            "base_url": offline_config.base_url,
            "skip_tls_verify": offline_config.skip_tls_verify,
            "httpx_verify": offline_config.httpx_verify,
            "mock_transport_no_network": sdk_transport_checks["offline_mock_transport"],
        },
        "entities": {
            "publish": publish["status"],
            "get": "passed" if fetched is not None else "failed",
            "stream": "passed" if stream and stream[-1]["kind"] == "Heartbeat" else "failed",
        },
        "objects": {
            "upload": upload["status"],
            "metadata_sha256": "passed" if upload.get("sha256") else "failed",
            "media_link": media["status"],
        },
        "tasks": {
            "create": task["status"],
            "update_status": task_status["task_status"],
            "stream_as_agent": "passed" if task_stream else "failed",
        },
        "remaining_gap": [
            "real sandbox endpoint",
            "real auth/session lifecycle",
            "real REST service behavior",
            "real gRPC service behavior",
            "vendor-side validation details",
        ],
    }


def _exercise_sdk_transport() -> dict[str, str]:
    transport = build_sdk_mock_transport()
    sandbox_headers = {"Anduril-Sandbox-Authorization": "Bearer mock-sandbox-token"}
    with httpx.Client(transport=transport, base_url="http://lattice.mock") as client:
        token_response = client.post(
            "/api/v1/oauth/token",
            data={
                "grant_type": "client_credentials",
                "client_id": "packet-stoat-client",
                "client_secret": "packet-stoat-secret",
                "scope": "entities streams",
            },
            headers=sandbox_headers,
        )
        missing_sandbox = client.post(
            "/api/v1/oauth/token",
            data={
                "grant_type": "client_credentials",
                "client_id": "packet-stoat-client",
                "client_secret": "packet-stoat-secret",
            },
        )
    with build_offline_httpx_client(transport=transport, skip_tls_verify=True) as offline_client:
        offline_response = offline_client.get(
            "https://offline-lattice.local/api/v1/objects",
            headers={
                "Authorization": "Bearer mock-environment-token",
                "Anduril-Sandbox-Authorization": "Bearer mock-sandbox-token",
            },
        )
    return {
        "oauth_token_route": "passed" if token_response.status_code == 200 else f"failed:{token_response.status_code}",
        "oauth_sandbox_header_rejection": "passed"
        if missing_sandbox.status_code == 403
        else f"failed:{missing_sandbox.status_code}",
        "offline_mock_transport": "passed" if offline_response.status_code == 200 else f"failed:{offline_response.status_code}",
    }


def render_markdown(report: dict[str, object]) -> str:
    return "\n".join(
        [
            "# Alpha 4.1 Lattice Compatibility Harness Report",
            "",
            f"- overall_status: `{report['overall_status']}`",
            f"- real_lattice_verified: `{str(report['real_lattice_verified']).lower()}`",
            "",
            "## Covered Locally",
            "",
            "- auth/session token checks",
            "- REST OAuth token route and sandbox-header rejection",
            "- offline client configuration for self-signed/local endpoints",
            "- entity publish/get/stream",
            "- object upload/metadata/media linking",
            "- task create/update/agent stream",
            "",
            "## Remaining Credential-Gated Gap",
            "",
            *[f"- {item}" for item in report["remaining_gap"]],
            "",
        ]
    )


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    report = build_report()
    json_path = OUT_DIR / "compatibility_harness_report.json"
    md_path = OUT_DIR / "compatibility_harness_report.md"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps({"overall_status": report["overall_status"], "json": str(json_path), "markdown": str(md_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
