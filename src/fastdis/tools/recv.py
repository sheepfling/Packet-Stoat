from __future__ import annotations

import argparse
import json
from pathlib import Path

import fastdis
from .. import native
from ._shared import load_session_truth, receive_udp_packets


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__ or "Receive UDP DIS packets and summarize them.")
    parser.add_argument("--bind", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=3001)
    parser.add_argument("--max-packets", type=int, default=128)
    parser.add_argument("--timeout", type=float, default=2.0)
    parser.add_argument("--surface", default="python")
    parser.add_argument("--verify", type=Path)
    parser.add_argument("--stats", action="store_true")
    parser.add_argument("--jsonl", action="store_true")
    parser.add_argument("--entity-table", action="store_true")
    parser.add_argument("--snapshots", action="store_true")
    parser.add_argument("--slots", type=int, default=3)
    return parser.parse_args()


def canonical_report(
    *,
    packets: list[bytes],
    malformed: int,
    counts_by_type: dict[int, int],
    table_snapshots: list[object],
    snapshot_count: int,
    errors: list[str],
    surface: str,
) -> dict[str, object]:
    latest_entities = [
        {
            "site": snapshot.transform.entity_id[0],
            "application": snapshot.transform.entity_id[1],
            "entity": snapshot.transform.entity_id[2],
            "force_id": snapshot.transform.force_id,
            "location_ecef_m": list(snapshot.transform.location),
            "orientation_dis_rad": list(snapshot.transform.orientation),
        }
        for snapshot in sorted(
            table_snapshots,
            key=lambda item: (
                item.transform.entity_id[0],
                item.transform.entity_id[1],
                item.transform.entity_id[2],
            ),
        )
    ]
    entity_state = counts_by_type.get(1, 0)
    return {
        "schema": "fastdis.network_report.v1",
        "surface": surface,
        "packets_received": len(packets),
        "packets_parsed": len(packets) - malformed,
        "malformed": malformed,
        "entity_state": entity_state,
        "unique_entities": len(latest_entities),
        "snapshots_published": snapshot_count,
        "latest_entities": latest_entities,
        "errors": errors,
    }


def verify_against_truth(report: dict[str, object], truth: dict[str, object]) -> list[str]:
    errors: list[str] = []
    for key in ("packet_count", "packets_parsed", "malformed", "entity_state", "unique_entities"):
        truth_key = "packets_received" if key == "packet_count" else key
        expected = truth[key]
        actual = report[truth_key]
        if actual != expected:
            errors.append(f"{truth_key}: expected {expected}, got {actual}")
    expected_entities = [
        (
            entity["site"],
            entity["application"],
            entity["entity"],
            entity["force_id"],
            tuple(round(float(v), 3) for v in entity["location_ecef_m"]),
            tuple(round(float(v), 6) for v in entity["orientation_dis_rad"]),
        )
        for entity in truth["latest_entities"]
    ]
    actual_entities = [
        (
            entity["site"],
            entity["application"],
            entity["entity"],
            entity["force_id"],
            tuple(round(float(v), 3) for v in entity["location_ecef_m"]),
            tuple(round(float(v), 6) for v in entity["orientation_dis_rad"]),
        )
        for entity in report["latest_entities"]
    ]
    if actual_entities != expected_entities:
        errors.append("latest_entities mismatch")
    return errors


def main(argv: list[str] | None = None) -> int:
    _ = argv
    args = parse_args()
    packets = receive_udp_packets(
        bind_host=args.bind,
        port=args.port,
        max_packets=args.max_packets,
        timeout_s=args.timeout,
    )
    counts: dict[int, int] = {}
    malformed = 0
    for packet in packets:
        header = fastdis.parse_header(packet, strict=False)
        if header is None:
            malformed += 1
            continue
        counts[header.pdu_type] = counts.get(header.pdu_type, 0) + 1

    lib = native.load_native()
    scanner = lib.create_scanner()
    scanner.use_entity_transform_profile()
    table = lib.create_entity_table(max(len(packets), 1))
    table_stats = table.ingest(scanner, packets)
    table_snapshots = table.snapshot_all(return_meta=False)

    snapshot_view = None
    snapshot_count = 0
    if args.snapshots or args.verify is not None:
        buffer = lib.create_snapshot_buffer(max(len(packets), 1), slots=args.slots)
        snapshot_view = buffer.publish_changed(table, clear=True)
        snapshot_count = snapshot_view.count

    errors: list[str] = []
    report = canonical_report(
        packets=packets,
        malformed=malformed,
        counts_by_type=counts,
        table_snapshots=table_snapshots,
        snapshot_count=snapshot_count,
        errors=errors,
        surface=args.surface,
    )
    if args.verify is not None:
        truth = load_session_truth(args.verify)
        errors.extend(verify_against_truth(report, truth))
        report["errors"] = errors

    if args.jsonl or args.entity_table:
        for snapshot in table_snapshots:
            print(json.dumps({
                "entity": list(snapshot.transform.entity_id),
                "force_id": snapshot.transform.force_id,
                "location_ecef_m": list(snapshot.transform.location),
                "orientation_dis_rad": list(snapshot.transform.orientation),
            }))
    if args.snapshots and snapshot_view is not None:
        print(json.dumps({
            "snapshot_count": snapshot_view.count,
            "generation": snapshot_view.generation,
            "slot": snapshot_view.slot,
            "dropped": snapshot_view.dropped,
            "table_updates": table_stats,
        }))

    if args.verify is not None or args.stats or not (args.jsonl or args.entity_table or args.snapshots):
        print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
