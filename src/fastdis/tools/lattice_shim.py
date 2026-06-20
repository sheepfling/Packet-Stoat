from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from fastdis import native
from fastdis.lattice import (
    canonical_entity_from_entity_state_packet,
    canonical_entity_from_lattice_payload,
    canonical_entity_from_snapshot,
)
from fastdis.replay import read_v1_packets
from fastdis.replay import write_v1_packets


ROOT = Path(__file__).resolve().parents[3]
INTEGRATION_SRC = ROOT / "integrations" / "lattice" / "src"
if str(INTEGRATION_SRC) not in sys.path:
    sys.path.insert(0, str(INTEGRATION_SRC))

from packet_stoat_lattice import (  # noqa: E402
    MockLatticeShim,
    canonical_entity_from_fixture,
    canonical_entity_to_fixture,
    entity_is_exportable_to_dis,
    entity_state_packet_from_track_payload,
    lattice_track_payload_from_entity,
    loop_suppression_reason,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__ or "Run the local Lattice shim operator lanes.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    dis_to_shim = subparsers.add_parser("dis-to-shim", help="Convert canonical/DIS fixture entities into shim events.")
    dis_to_shim.add_argument("fixture", type=Path)
    dis_to_shim.add_argument("--out-dir", type=Path, required=True)
    dis_to_shim.add_argument("--components", default="aliases,location,ontology,milView,provenance,packetStoat")
    dis_to_shim.add_argument("--heartbeat-interval-ms", type=int, default=1000)

    shim_to_dis = subparsers.add_parser("shim-to-dis", help="Convert shim-stored entities back into DIS Entity State packets.")
    shim_to_dis.add_argument("fixture", type=Path)
    shim_to_dis.add_argument("--out-dir", type=Path, required=True)
    shim_to_dis.add_argument("--heartbeat-interval-ms", type=int, default=1000)

    lab_state = subparsers.add_parser("lab-state", help="Exercise bounded object/task seams and emit local shim state reports.")
    lab_state.add_argument("--object-fixture", type=Path, default=ROOT / "integrations" / "lattice" / "examples" / "object_fixture.json")
    lab_state.add_argument("--task-fixture", type=Path, default=ROOT / "integrations" / "lattice" / "examples" / "task_fixture.json")
    lab_state.add_argument("--out-dir", type=Path, required=True)

    return parser.parse_args()


def _load_track_payloads(fixture: Path) -> list[dict[str, Any]]:
    if fixture.suffix == ".fastdispkt":
        packets = read_v1_packets(fixture)
        metadata = {
            "replay_fixture": str(fixture.resolve()),
            "ingest_surface": "replay",
        }
        try:
            lib = native.load_native()
        except Exception:
            return [
                lattice_track_payload_from_entity(
                    canonical_entity_from_entity_state_packet(packet, source="dis-ingress", metadata=metadata)
                )
                for packet in packets
            ]

        scanner = lib.create_scanner()
        scanner.use_entity_transform_profile()
        table = lib.create_entity_table(max(len(packets), 1))
        table.ingest(scanner, packets)
        snapshots = table.snapshot_all(return_meta=False)
        return [
            lattice_track_payload_from_entity(
                canonical_entity_from_snapshot(snapshot, source="dis-ingress", metadata=metadata)
            )
            for snapshot in snapshots
        ]
    payload = json.loads(fixture.read_text(encoding="utf-8"))
    if isinstance(payload, dict) and payload.get("schema") == "fastdis.mock-lattice.track.v1":
        return [dict(payload)]
    entities = canonical_entity_from_fixture(fixture)
    return [lattice_track_payload_from_entity(entity) for entity in entities]


def _ensure_out_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _load_rows(path: Path, *, key: str) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return [dict(row) for row in payload]
    rows = payload.get(key, [])
    return [dict(row) for row in rows]


def command_dis_to_shim(args: argparse.Namespace) -> int:
    out_dir = args.out_dir.resolve()
    _ensure_out_dir(out_dir)
    shim = MockLatticeShim()
    payloads = _load_track_payloads(args.fixture)
    publish = shim.publish_batch(payloads)
    components = [value.strip() for value in str(args.components).split(",") if value.strip()]
    events = shim.stream_entities(
        components_to_include=components,
        heartbeat_interval_ms=int(args.heartbeat_interval_ms),
    )

    (out_dir / "shim_entities.json").write_text(json.dumps(shim.list_entities(), indent=2), encoding="utf-8")
    (out_dir / "stream_events.json").write_text(json.dumps(events, indent=2), encoding="utf-8")
    shim.write_event_log_jsonl(out_dir / "shim_event_log.jsonl")
    report = {
        "mode": "dis-to-shim",
        "fixture": str(args.fixture.resolve()),
        "attempted": len(payloads),
        "accepted": int(publish["accepted"]),
        "entity_count": shim.metrics()["entity_count"],
        "event_count": shim.metrics()["event_count"],
        "stream_event_count": len(events),
        "components": components,
        "heartbeat_interval_ms": int(args.heartbeat_interval_ms),
        "metrics": shim.metrics(),
    }
    (out_dir / "dis_to_shim_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


def command_shim_to_dis(args: argparse.Namespace) -> int:
    out_dir = args.out_dir.resolve()
    _ensure_out_dir(out_dir)
    shim = MockLatticeShim()
    payloads = _load_track_payloads(args.fixture)
    shim.publish_batch(payloads)
    stream_events = shim.stream_entities(
        heartbeat_interval_ms=int(args.heartbeat_interval_ms),
        include_heartbeat=True,
    )
    streamed_payloads = [
        dict(event["payload"])
        for event in stream_events
        if event.get("kind") == "EntityEvent" and isinstance(event.get("payload"), dict)
    ]
    export_report = shim.export_report_for_dis()
    exportable = [payload for payload in streamed_payloads if entity_is_exportable_to_dis(payload)]
    suppressed = [
        {
            "entity_id": payload.get("entityId") or payload.get("entity_key"),
            "reason": loop_suppression_reason(payload),
        }
        for payload in streamed_payloads
        if not entity_is_exportable_to_dis(payload)
    ]
    packets = [entity_state_packet_from_track_payload(payload) for payload in exportable]
    replay_path = out_dir / "shim_to_dis.fastdispkt"
    count = write_v1_packets(replay_path, packets)
    canonical_entities = [canonical_entity_from_lattice_payload(payload) for payload in exportable]
    canonical_entity_to_fixture(canonical_entities, out_dir / "canonical_entities.json")
    (out_dir / "stream_events.json").write_text(json.dumps(stream_events, indent=2), encoding="utf-8")
    shim.write_event_log_jsonl(out_dir / "shim_event_log.jsonl")
    report = {
        "mode": "shim-to-dis",
        "fixture": str(args.fixture.resolve()),
        "shim_entity_count": shim.metrics()["entity_count"],
        "stream_event_count": len(stream_events),
        "exportable_entity_count": len(exportable),
        "suppressed_entity_count": len(suppressed),
        "packet_count": count,
        "replay_path": str(replay_path),
        "entity_ids": [payload.get("entityId") or payload.get("entity_key") for payload in exportable],
        "packet_lengths": [len(packet) for packet in packets],
        "suppressed": suppressed,
        "export_report": export_report,
        "metrics": shim.metrics(),
    }
    (out_dir / "shim_to_dis_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


def command_lab_state(args: argparse.Namespace) -> int:
    out_dir = args.out_dir.resolve()
    _ensure_out_dir(out_dir)
    shim = MockLatticeShim()
    object_rows = _load_rows(args.object_fixture, key="objects")
    task_rows = _load_rows(args.task_fixture, key="tasks")
    object_results = [
        shim.put_object(
            str(row["path"]),
            str(row.get("content_type", "application/octet-stream")),
            str(row.get("content", "")).encode("utf-8"),
        )
        for row in object_rows
    ]
    task_results = [shim.create_task(row) for row in task_rows]
    status_results = [shim.update_task_status(str(row["task_id"]), str(row.get("status", "queued"))) for row in task_rows]
    objects = shim.list_objects()
    tasks = shim.list_tasks()
    task_events = shim.stream_tasks()
    shim.write_event_log_jsonl(out_dir / "shim_event_log.jsonl")
    (out_dir / "objects.json").write_text(json.dumps(objects, indent=2), encoding="utf-8")
    (out_dir / "tasks.json").write_text(json.dumps(tasks, indent=2), encoding="utf-8")
    (out_dir / "task_events.json").write_text(json.dumps(task_events, indent=2), encoding="utf-8")
    report = {
        "mode": "lab-state",
        "object_fixture": str(Path(args.object_fixture).resolve()),
        "task_fixture": str(Path(args.task_fixture).resolve()),
        "object_results": object_results,
        "task_results": task_results,
        "status_results": status_results,
        "object_count": len(objects),
        "task_count": len(tasks),
        "task_event_count": len(task_events),
        "metrics": shim.metrics(),
    }
    (out_dir / "lab_state_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    _ = argv
    args = parse_args()
    if args.command == "dis-to-shim":
        return command_dis_to_shim(args)
    if args.command == "shim-to-dis":
        return command_shim_to_dis(args)
    if args.command == "lab-state":
        return command_lab_state(args)
    raise SystemExit(f"Unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
