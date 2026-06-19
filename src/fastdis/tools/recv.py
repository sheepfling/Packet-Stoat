from __future__ import annotations

import argparse
import json

import fastdis
from .. import native
from ._shared import receive_udp_packets


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__ or "Receive UDP DIS packets and summarize them.")
    parser.add_argument("--bind", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=3001)
    parser.add_argument("--max-packets", type=int, default=128)
    parser.add_argument("--timeout", type=float, default=2.0)
    parser.add_argument("--stats", action="store_true")
    parser.add_argument("--jsonl", action="store_true")
    parser.add_argument("--entity-table", action="store_true")
    parser.add_argument("--snapshots", action="store_true")
    parser.add_argument("--slots", type=int, default=3)
    return parser.parse_args()


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

    if args.jsonl or args.entity_table or args.snapshots:
        lib = native.load_native()
        scanner = lib.new_scanner()
        scanner.use_entity_transform_profile()
        table = lib.create_entity_table(max(len(packets), 1))
        table_stats = table.ingest(scanner, packets)
        if args.entity_table:
            snapshots = table.snapshot_all(return_meta=False)
            for snapshot in snapshots:
                print(json.dumps({
                    "entity": list(snapshot.transform.entity_id),
                    "force_id": snapshot.transform.force_id,
                    "location_ecef_m": list(snapshot.transform.location),
                    "orientation_dis_rad": list(snapshot.transform.orientation),
                }))
        if args.snapshots:
            buffer = lib.create_snapshot_buffer(max(len(packets), 1), slots=args.slots)
            view = buffer.publish_changed(table, clear=True)
            print(json.dumps({
                "snapshot_count": view.count,
                "generation": view.generation,
                "slot": view.slot,
                "dropped": view.dropped,
                "table_updates": table_stats,
            }))

    if args.stats or not (args.jsonl or args.entity_table or args.snapshots):
        summary = {
            "packets": len(packets),
            "malformed": malformed,
            "counts_by_type": counts,
        }
        print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
