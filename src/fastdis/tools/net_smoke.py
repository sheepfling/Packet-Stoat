from __future__ import annotations

import argparse
import json
from pathlib import Path
import socket
import threading

import fastdis
from .. import native, replay
from .send_entity import build_packets
from ._shared import receive_udp_packets


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__ or "Run a localhost UDP/net smoke test through the fastdis pipeline.")
    parser.add_argument("--count", type=int, default=3)
    parser.add_argument("--entity-count", type=int, default=1)
    parser.add_argument("--timeout", type=float, default=2.0)
    parser.add_argument("--site", type=int, default=100)
    parser.add_argument("--application", type=int, default=1)
    parser.add_argument("--entity", type=int, default=42)
    parser.add_argument("--write-replay", type=Path)
    parser.add_argument("--print-json", action="store_true")
    return parser.parse_args()


def _ephemeral_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def main(argv: list[str] | None = None) -> int:
    _ = argv
    args = parse_args()
    port = _ephemeral_port()
    sender_args = argparse.Namespace(
        dst="127.0.0.1",
        port=port,
        count=args.count,
        entity_count=args.entity_count,
        rate_hz=0.0,
        site=args.site,
        application=args.application,
        entity=args.entity,
        force_id=1,
        exercise_id=3,
        marking="FASTDIS",
        lat=29.5597,
        lon=-95.0831,
        alt=100.0,
        heading=90.0,
        pitch=0.0,
        roll=0.0,
        print_orientation_debug=False,
    )
    packets_to_send, orientation_debug, _truth = build_packets(sender_args)
    captured: list[bytes] = []

    def _receiver() -> None:
        captured.extend(
            receive_udp_packets(
                bind_host="127.0.0.1",
                port=port,
                max_packets=args.count,
                timeout_s=args.timeout,
            )
        )

    thread = threading.Thread(target=_receiver, daemon=True)
    thread.start()
    from ._shared import send_udp_packets
    send_udp_packets(packets=packets_to_send, host="127.0.0.1", port=port, rate_hz=0.0)
    thread.join(timeout=args.timeout + 1.0)

    if args.write_replay is not None:
        replay.write_v1_packets(args.write_replay, captured)

    if len(captured) != args.count:
        raise SystemExit(f"expected {args.count} captured packet(s), got {len(captured)}")

    headers = [fastdis.parse_header(packet, strict=True) for packet in captured]
    if any(header is None for header in headers):
        raise SystemExit("header parse failed during net smoke")

    lib = native.load_native()
    scanner = lib.create_scanner().use_entity_transform_profile()
    table = lib.create_entity_table(max(args.count, 8))
    ingest_stats = table.ingest(scanner, captured)
    snapshots = lib.create_snapshot_buffer(max(args.count, 8), slots=3)
    view = snapshots.publish_changed(table, clear=True)
    last_entity = sender_args.entity + ((args.count - 1) % max(1, args.entity_count))
    latest = table.get((sender_args.site, sender_args.application, last_entity))
    if latest is None:
        raise SystemExit("latest entity snapshot missing after ingest")

    result = {
        "captured_packets": len(captured),
        "ingest_stats": ingest_stats,
        "snapshot_count": view.count,
        "entity": list(latest.transform.entity_id),
        "location_ecef_m": list(latest.transform.location),
        "orientation_dis_rad": list(latest.transform.orientation),
        "orientation_debug": orientation_debug,
    }
    if args.print_json:
        print(json.dumps(result, indent=2))
    else:
        print(
            f"fastdis net smoke passed packets={result['captured_packets']} "
            f"entity={result['entity']} snapshots={result['snapshot_count']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
