#!/usr/bin/env python3
"""Zorn-compatible bridge for FastDIS lattice workflow lanes.

This bridge is intentionally local and surrogate-based. It exercises the same
ingress/egress contract surfaces that the workflow expects, while keeping the
real Zorn probes separate in the dedicated parity/auth scripts.
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
ADAPTER_SRC = ROOT / "integrations" / "lattice" / "src"
for path in (SRC, ADAPTER_SRC):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from artifacts import VERIFICATION_REPORTS_DIR
from fastdis.lattice import canonical_entity_to_entity_state_packet
from fastdis.interop import canonical_entity_from_dict
from fastdis.lattice import canonical_entity_from_lattice_payload
from fastdis.replay import write_v1_packets
from packet_stoat_lattice import (
    MockLatticeRestHarness,
    canonical_entity_to_fixture,
    lattice_track_payload_from_entity,
)


DEFAULT_OUT_DIR = VERIFICATION_REPORTS_DIR / "alpha5" / "lattice_zorn_bridge"
DEFAULT_DIS_FIXTURE = ROOT / "integrations" / "lattice" / "examples" / "dis_entity_fixture.json"
DEFAULT_TRACK_FIXTURE = ROOT / "integrations" / "lattice" / "examples" / "lattice_track_fixture.json"
DEFAULT_OBJECT_FIXTURE = ROOT / "integrations" / "lattice" / "examples" / "object_fixture.json"
DEFAULT_TASK_FIXTURE = ROOT / "integrations" / "lattice" / "examples" / "task_fixture.json"


def _auth_headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Anduril-Sandbox-Authorization": "Bearer mock-sandbox-token",
    }


def _issue_token(harness: MockLatticeRestHarness) -> str:
    token = harness.oauth_token(
        client_id="packet-stoat-client",
        client_secret="packet-stoat-secret",
        scope="entities objects tasks streams",
    )
    return str(token["access_token"])


def _load_canonical_entities(path: Path):
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict) and "entities" in payload:
        rows = payload["entities"]
    elif isinstance(payload, list):
        rows = payload
    else:
        rows = [payload]
    entities = []
    for row in rows:
        candidate = dict(row)
        if "entity_id" in candidate:
            entities.append(canonical_entity_from_dict(candidate))
        elif "entity_key" in candidate and "pose" in candidate:
            entities.append(canonical_entity_from_lattice_payload(candidate))
        else:
            entities.append(canonical_entity_from_dict(candidate))
    return entities


def _canonical_to_zorn_dis_rows(entities) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for entity in entities:
        payload = lattice_track_payload_from_entity(entity)
        entity_id = str(payload["entityId"])
        rows.append({"eventType": "CREATE", "entity_id": entity_id, "is_live": True, "payload": payload})
        rows.append({"eventType": "UPDATE", "entity_id": entity_id, "is_live": True, "payload": payload})
        rows.append({"eventType": "DELETED", "entity_id": entity_id, "is_live": False, "payload": {**payload, "stale": True, "isLive": False}})
    return rows


def _evaluate_zorn_entity_events(payload: dict[str, Any]) -> dict[str, object]:
    events = payload.get("events")
    if not isinstance(events, list):
        events = []

    seen_create = False
    seen_update = False
    seen_delete_or_non_live = False
    observed_entity_id: str | None = None

    for event in events:
        if not isinstance(event, dict):
            continue
        kind = str(event.get("eventType") or event.get("kind") or "").upper()
        entity = event.get("entity")
        if isinstance(entity, dict):
            entity_id = entity.get("entityId") or entity.get("entity_id")
            if isinstance(entity_id, str) and entity_id:
                observed_entity_id = observed_entity_id or entity_id
            if entity.get("isLive") is False:
                seen_delete_or_non_live = True
        if kind in {"CREATE", "CREATED", "ENTITYPUBLISHED"}:
            seen_create = True
        if kind in {"UPDATE", "UPDATED", "ENTITYUPDATED"}:
            seen_update = True
        if kind in {"DELETED", "DELETE", "REMOVED", "ENTITYDELETED"}:
            seen_delete_or_non_live = True

    missing: list[str] = []
    if not seen_create:
        missing.append("entities.stream.create")
    if not seen_update:
        missing.append("entities.stream.create_update_order")
    if not seen_delete_or_non_live:
        missing.append("entities.stream.delete_or_non_live")

    if not events or not seen_create:
        status = "failed"
    elif missing:
        status = "ready-with-gaps"
    else:
        status = "ready"

    return {
        "status": status,
        "missing": missing,
        "observed_entity_id": observed_entity_id,
        "counts": {
            "events": len(events),
            "create": int(seen_create),
            "update": int(seen_update),
            "delete_or_non_live": int(seen_delete_or_non_live),
        },
    }


def _build_report(kind: str, payload: dict[str, Any]) -> dict[str, object]:
    return {
        "kind": kind,
        "overall_status": payload.get("status", "ready-with-gaps"),
        "generated_at": datetime.now(UTC).isoformat(),
        "bridge_mode": "local-zorn-compatible-surrogate",
        "backend": "external-zorn",
        "transport": "mock",
        "proof_source": "fastdis-local-zorn-compatible-bridge",
        "real_lattice_verified": False,
        "payload": payload,
    }


def _write_report(out_dir: Path, basename: str, payload: dict[str, object]) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"{basename}.json"
    md_path = out_dir / f"{basename}.md"
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    md_path.write_text(_render_markdown(payload), encoding="utf-8")
    return json_path, md_path


def _render_markdown(report: dict[str, object]) -> str:
    payload = report.get("payload", {})
    lines = [
        f"# {report.get('kind', 'Lattice Bridge')}",
        "",
        f"- overall_status: `{report.get('overall_status', 'unknown')}`",
        f"- bridge_mode: `{report.get('bridge_mode', 'unknown')}`",
        f"- proof_source: `{report.get('proof_source', 'unknown')}`",
        "",
    ]
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key == "events" and isinstance(value, list):
                lines.append(f"- events: `{len(value)}`")
            elif key == "checks" and isinstance(value, list):
                lines.append(f"- checks: `{len(value)}`")
            elif key == "missing" and isinstance(value, list):
                lines.append(f"- missing: `{', '.join(str(item) for item in value)}`")
            elif key == "entity_ids" and isinstance(value, list):
                lines.append(f"- entity_ids: `{', '.join(str(item) for item in value)}`")
            elif key == "paths" and isinstance(value, list):
                lines.append(f"- paths: `{', '.join(str(item) for item in value)}`")
            elif key == "tasks" and isinstance(value, list):
                lines.append(f"- tasks: `{len(value)}`")
            elif key != "event_log":
                lines.append(f"- {key}: `{value}`")
    lines.append("")
    return "\n".join(lines)


def command_doctor(_args: argparse.Namespace) -> int:
    harness = MockLatticeRestHarness()
    token = _issue_token(harness)
    headers = _auth_headers(token)
    entity = _load_canonical_entities(DEFAULT_TRACK_FIXTURE)[0]
    payload = lattice_track_payload_from_entity(entity)
    published = harness.publish_entity(payload, headers=headers)
    fetched = harness.get_entity(str(payload["entityId"]), headers=headers)
    stream = harness.stream_entities(headers=headers, components_to_include=["aliases", "location"], pre_existing_only=True)
    task = harness.create_task(
        {"task_id": "bridge-doctor-task", "agent_id": str(payload["entityId"]), "task_type": "doctor"},
        headers=headers,
    )
    harness.update_task_status("bridge-doctor-task", "in_progress", headers=headers)
    object_result = harness.upload_object("bridge/doctor.json", "application/json", b'{"bridge":true}', headers=headers)

    report = _build_report(
        "Zorn Bridge Doctor",
        {
            "status": "ready",
            "entity_publish": published["status"],
            "entity_get": "passed" if fetched is not None else "failed",
            "entity_stream_events": len(stream),
            "task_create": task["status"],
            "object_upload": object_result["status"],
            "fixture": str(DEFAULT_TRACK_FIXTURE),
        },
    )
    print(json.dumps(report, indent=2, sort_keys=True, default=str))
    return 0


def command_dis_to_shim(args: argparse.Namespace) -> int:
    out_dir = Path(args.out_dir).resolve()
    fixture = Path(args.fixture).resolve()
    harness = MockLatticeRestHarness()
    token = _issue_token(harness)
    headers = _auth_headers(token)
    entities = _load_canonical_entities(fixture)
    published: list[dict[str, object]] = []
    entity_ids: list[str] = []
    for entity in entities:
        payload = lattice_track_payload_from_entity(entity)
        entity_ids.append(str(payload["entityId"]))
        published.append(harness.publish_entity(payload, headers=headers))
    stream = harness.stream_entities(headers=headers, components_to_include=["aliases", "location", "milView"], pre_existing_only=True)
    report = _build_report(
        "DIS to Shim",
        {
            "status": "ready",
            "fixture": str(fixture),
            "published_count": len(published),
            "entity_ids": entity_ids,
            "stream_events": len(stream),
            "event_log": stream,
        },
    )
    json_path, md_path = _write_report(out_dir, "dis_to_shim_report", report)
    print(json.dumps({"overall_status": report["overall_status"], "json": str(json_path), "markdown": str(md_path)}, indent=2))
    return 0


def command_shim_to_dis(args: argparse.Namespace) -> int:
    out_dir = Path(args.out_dir).resolve()
    fixture = Path(args.fixture).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    harness = MockLatticeRestHarness()
    token = _issue_token(harness)
    headers = _auth_headers(token)
    entities = _load_canonical_entities(fixture)
    observed = []
    packets: list[bytes] = []
    for entity in entities:
        payload = lattice_track_payload_from_entity(entity)
        harness.publish_entity(payload, headers=headers)
        fetched = harness.get_entity(str(payload["entityId"]), headers=headers)
        if fetched is None:
            raise RuntimeError("published entity was not retrievable from the shim lane")
        observed.append(fetched)
        packets.append(canonical_entity_to_entity_state_packet(entity))
    canonical_path = out_dir / "canonical_entities.json"
    replay_path = out_dir / "shim_to_dis.fastdispkt"
    canonical_entity_to_fixture(entities, canonical_path)
    packet_count = write_v1_packets(replay_path, packets)
    report = _build_report(
        "Shim to DIS",
        {
            "status": "ready",
            "fixture": str(fixture),
            "canonical_entities_path": str(canonical_path),
            "replay_path": str(replay_path),
            "entities_emitted": len(observed),
            "packets_emitted": packet_count,
            "entity_ids": [str(item["entityId"]) for item in observed if isinstance(item, dict) and "entityId" in item],
            "roundtrip": "entity_state_packet",
        },
    )
    json_path, md_path = _write_report(out_dir, "shim_to_dis_report", report)
    print(json.dumps({"overall_status": report["overall_status"], "json": str(json_path), "markdown": str(md_path)}, indent=2))
    return 0


def command_lab_state(args: argparse.Namespace) -> int:
    out_dir = Path(args.out_dir).resolve()
    object_fixture = Path(args.object_fixture).resolve()
    task_fixture = Path(args.task_fixture).resolve()
    harness = MockLatticeRestHarness()
    token = _issue_token(harness)
    headers = _auth_headers(token)
    object_payload = json.loads(object_fixture.read_text(encoding="utf-8"))
    task_payload = json.loads(task_fixture.read_text(encoding="utf-8"))
    uploaded: list[dict[str, object]] = []
    tasks: list[dict[str, object]] = []

    for row in object_payload.get("objects", []):
        if not isinstance(row, dict):
            continue
        path = str(row.get("path", "objects/unknown.bin"))
        content_type = str(row.get("content_type", "application/octet-stream"))
        content = str(row.get("content", "")).encode("utf-8")
        uploaded.append(harness.upload_object(path, content_type, content, headers=headers))

    for row in task_payload.get("tasks", []):
        if not isinstance(row, dict):
            continue
        task = harness.create_task(row, headers=headers)
        tasks.append(task)
        harness.update_task_status(str(row.get("task_id", "task-unknown")), "in_progress", headers=headers)

    stream = harness.stream_tasks(headers=headers)
    object_list = harness.list_objects(headers=headers)
    report = _build_report(
        "Lab State",
        {
            "status": "ready",
            "object_fixture": str(object_fixture),
            "task_fixture": str(task_fixture),
            "uploaded_objects": len(uploaded),
            "task_count": len(tasks),
            "object_count": len(object_list),
            "task_stream_count": len(stream),
        },
    )
    json_path, md_path = _write_report(out_dir, "lab_state_report", report)
    print(json.dumps({"overall_status": report["overall_status"], "json": str(json_path), "markdown": str(md_path)}, indent=2))
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("doctor", help="Inspect the local Zorn-compatible bridge")

    dis = subparsers.add_parser("dis-to-shim", help="Publish canonical DIS fixture entities into the bridge lane")
    dis.add_argument("--fixture", type=Path, default=DEFAULT_DIS_FIXTURE)
    dis.add_argument("--out-dir", type=Path, required=True)

    shim = subparsers.add_parser("shim-to-dis", help="Fetch bridge entities and emit DIS replay bytes")
    shim.add_argument("--fixture", type=Path, default=DEFAULT_TRACK_FIXTURE)
    shim.add_argument("--out-dir", type=Path, required=True)

    lab = subparsers.add_parser("lab-state", help="Exercise bridge object/task seams")
    lab.add_argument("--object-fixture", type=Path, default=DEFAULT_OBJECT_FIXTURE)
    lab.add_argument("--task-fixture", type=Path, default=DEFAULT_TASK_FIXTURE)
    lab.add_argument("--out-dir", type=Path, required=True)

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.command == "doctor":
        return command_doctor(args)
    if args.command == "dis-to-shim":
        return command_dis_to_shim(args)
    if args.command == "shim-to-dis":
        return command_shim_to_dis(args)
    if args.command == "lab-state":
        return command_lab_state(args)
    raise RuntimeError(f"unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
