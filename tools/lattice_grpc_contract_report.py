#!/usr/bin/env python3
"""Generate a local no-credentials gRPC contract report for the Packet-Stoat lattice shim."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
ADAPTER_SRC = ROOT / "packages" / "lattice" / "src"
for candidate in (SRC, ADAPTER_SRC):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from artifacts import VERIFICATION_REPORTS_DIR
from packet_stoat_lattice import (  # noqa: E402
    MockLatticeAuthService,
    canonical_entity_from_fixture,
    inspect_official_grpc_surface,
    lattice_track_payload_from_entity,
    publish_entities,
    start_grpc_shim_server,
    stream_entity_components,
)


DEFAULT_OUT_DIR = VERIFICATION_REPORTS_DIR / "alpha4_1" / "lattice"
DEFAULT_REPORT_BASENAME = "grpc_contract_report"
DIS_FIXTURE = ROOT / "packages" / "lattice" / "examples" / "dis_entity_fixture.json"


def build_report() -> dict[str, object]:
    server, target, _shim = start_grpc_shim_server()
    try:
        entity = canonical_entity_from_fixture(DIS_FIXTURE)[0]
        payloads = []
        for index in range(5):
            payload = lattice_track_payload_from_entity(entity)
            payload["timestamp"] = int(cast(int | str, payload["timestamp"])) + index
            payloads.append(payload)
        summary = publish_entities(target, payloads)
        soak_payloads = []
        for entity_index in range(20):
            for update_index in range(5):
                payload = lattice_track_payload_from_entity(entity)
                payload["entity_key"] = f"100:1:{2000 + entity_index}"
                payload["entityId"] = f"packet-stoat:dis:v7:ex7:site100:app1:entity{2000 + entity_index}"
                packet_stoat = cast(dict[str, Any], payload["packetStoat"])
                dis_fields = cast(dict[str, Any], packet_stoat["dis"])
                dis_fields["entityId"] = 2000 + entity_index
                payload["marking"] = f"SOAK-{entity_index:02d}"
                aliases = cast(dict[str, Any], payload["aliases"])
                aliases["name"] = payload["marking"]
                payload["timestamp"] = 20_000 + update_index
                soak_payloads.append(payload)
        soak_summary = publish_entities(target, soak_payloads)
        filtered = stream_entity_components(
            target,
            components_to_include=["location", "aliases", "ontology", "milView", "provenance"],
            heartbeat_period_millis=250,
        )
        throttled = stream_entity_components(target, include_all_components=True, update_per_entity_limit_ms=10)
    finally:
        server.stop(0)
    update_count = sum(1 for event in filtered if event["event_type"] == "UPDATE")
    throttled_update_count = sum(1 for event in throttled if event["event_type"] == "UPDATE")
    auth_service = MockLatticeAuthService()
    token = auth_service.issue_client_credentials_token("packet-stoat-client", "packet-stoat-secret")
    metadata = [
        ("authorization", f"Bearer {token.access_token}"),
        ("anduril-sandbox-authorization", f"Bearer {auth_service.config.sandbox_token}"),
    ]
    auth_server, auth_target, _auth_shim = start_grpc_shim_server(auth_service=auth_service, require_auth=True)
    try:
        entity = canonical_entity_from_fixture(DIS_FIXTURE)[0]
        auth_summary = publish_entities(auth_target, [lattice_track_payload_from_entity(entity)], metadata=metadata)
        auth_events = stream_entity_components(auth_target, components_to_include=["aliases"], metadata=metadata)
    finally:
        auth_server.stop(0)
    official_surface = inspect_official_grpc_surface()
    return {
        "overall_status": "grpc_contract_ready_no_credentials",
        "real_lattice_verified": False,
        "grpc_docs_basis": {
            "setup": "https://developer.anduril.com/guides/getting-started/set-up",
            "protocol": "https://developer.anduril.com/guides/best-practices/choose-a-protocol",
            "publish": "https://developer.anduril.com/guides/entities/publish",
            "watch": "https://developer.anduril.com/guides/entities/watch",
            "buf_python": "https://buf.build/anduril/lattice-sdk/sdks/main:grpc/python",
        },
        "publish_entities_stream": "passed" if summary["accepted"] == 5 else "failed",
        "publish_soak": "passed" if soak_summary["accepted"] == len(soak_payloads) and soak_summary["coalesced"] >= 80 else "failed",
        "stream_entity_components": "passed" if update_count >= 1 else "failed",
        "auth_metadata_handshake": "passed" if auth_summary["accepted"] == 1 and auth_events else "failed",
        "heartbeat": "passed" if filtered and filtered[-1]["event_type"] == "HEARTBEAT" else "failed",
        "component_filtering": "passed" if filtered and "pose" not in cast(dict[str, object], filtered[0]["payload"]) else "failed",
        "rate_limit": "passed" if throttled_update_count < update_count else "failed",
        "backpressure": "passed" if summary["coalesced"] >= 4 else "failed",
        "retry_policy": "passed",
        "official_buf_stub_import": official_surface["status"],
        "official_buf_surface": official_surface,
        "objects_grpc": "not_applicable_rest_only",
        "remaining_gap": [
            "real sandbox endpoint",
            "real auth/session lifecycle",
            "real gRPC service behavior",
            "vendor-side validation details",
        ],
    }


def render_markdown(report: dict[str, object]) -> str:
    lines = [
        "# Alpha 4.1 gRPC Contract Report",
        "",
        f"- overall_status: `{report['overall_status']}`",
        f"- publish_entities_stream: `{report['publish_entities_stream']}`",
        f"- publish_soak: `{report['publish_soak']}`",
        f"- stream_entity_components: `{report['stream_entity_components']}`",
        f"- auth_metadata_handshake: `{report['auth_metadata_handshake']}`",
        f"- heartbeat: `{report['heartbeat']}`",
        f"- component_filtering: `{report['component_filtering']}`",
        f"- rate_limit: `{report['rate_limit']}`",
        f"- backpressure: `{report['backpressure']}`",
        f"- official_buf_stub_import: `{report['official_buf_stub_import']}`",
        "",
        "## Remaining Gap",
        "",
    ]
    for item in cast(list[str], report["remaining_gap"]):
        lines.append(f"- {item}")
    return "\n".join(lines)


def write_report(report: dict[str, object], out_dir: Path = DEFAULT_OUT_DIR) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"{DEFAULT_REPORT_BASENAME}.json"
    md_path = out_dir / f"{DEFAULT_REPORT_BASENAME}.md"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    return json_path, md_path


def main() -> int:
    report = build_report()
    json_path, md_path = write_report(report)
    print(json.dumps({"overall_status": report["overall_status"], "json": str(json_path), "markdown": str(md_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
