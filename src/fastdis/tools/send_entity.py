from __future__ import annotations

import argparse
import json
from pathlib import Path

from ._shared import (
    EntityStateSpec,
    entity_state_spec_from_geodetic,
    make_entity_state_packet,
    send_udp_packets,
    session_truth_from_specs,
    write_session_truth,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__ or "Send synthetic DIS Entity State PDUs over UDP.")
    parser.add_argument("--dst", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=3001)
    parser.add_argument("--count", type=int, default=1)
    parser.add_argument("--entity-count", type=int, default=1)
    parser.add_argument("--rate-hz", type=float, default=0.0)
    parser.add_argument("--site", type=int, default=100)
    parser.add_argument("--application", type=int, default=1)
    parser.add_argument("--entity", type=int, default=1)
    parser.add_argument("--force-id", type=int, default=1)
    parser.add_argument("--exercise-id", type=int, default=3)
    parser.add_argument("--marking", default="FASTDIS")
    parser.add_argument("--lat", type=float, default=29.5597)
    parser.add_argument("--lon", type=float, default=-95.0831)
    parser.add_argument("--alt", type=float, default=100.0)
    parser.add_argument("--heading", type=float, default=90.0)
    parser.add_argument("--pitch", type=float, default=0.0)
    parser.add_argument("--roll", type=float, default=0.0)
    parser.add_argument("--print-orientation-debug", action="store_true")
    parser.add_argument("--truth-out", type=Path)
    return parser.parse_args()


def build_specs(args: argparse.Namespace) -> tuple[list[EntityStateSpec], dict[str, object]]:
    specs: list[EntityStateSpec] = []
    orientation_debug: dict[str, object] | None = None
    entity_count = max(1, int(args.entity_count))
    for index in range(args.count):
        entity_slot = index % entity_count
        spec = entity_state_spec_from_geodetic(
            lat_deg=args.lat,
            lon_deg=args.lon,
            alt_m=args.alt,
            heading_deg=args.heading,
            pitch_deg=args.pitch,
            roll_deg=args.roll,
            site=args.site,
            application=args.application,
            entity=args.entity + entity_slot,
            force_id=args.force_id,
            exercise_id=args.exercise_id,
            marking=args.marking,
            timestamp=0x10000000 + index,
        )
        step = float(index // entity_count)
        location = (
            spec.location_ecef_m[0] + step * 10.0,
            spec.location_ecef_m[1] + entity_slot * 3.0,
            spec.location_ecef_m[2],
        )
        spec = EntityStateSpec(
            **{
                **spec.__dict__,
                "location_ecef_m": location,
            }
        )
        specs.append(spec)
        if orientation_debug is None:
            orientation_debug = {
                "location_ecef_m": spec.location_ecef_m,
                "dis_orientation_deg": {
                    "psi": spec.orientation_dis_deg[0],
                    "theta": spec.orientation_dis_deg[1],
                    "phi": spec.orientation_dis_deg[2],
                },
            }
    return specs, orientation_debug or {}


def build_packets(args: argparse.Namespace) -> tuple[list[bytes], dict[str, object], dict[str, object]]:
    specs, orientation_debug = build_specs(args)
    packets = [make_entity_state_packet(spec) for spec in specs]
    truth = session_truth_from_specs(specs)
    return packets, orientation_debug, truth


def main(argv: list[str] | None = None) -> int:
    _ = argv
    args = parse_args()
    packets, orientation_debug, truth = build_packets(args)
    if args.truth_out is not None:
        write_session_truth(args.truth_out, truth)
    sent = send_udp_packets(packets=packets, host=args.dst, port=args.port, rate_hz=args.rate_hz)
    if args.print_orientation_debug:
        print(json.dumps(orientation_debug, indent=2))
    print(f"sent {sent} Entity State packet(s) to {args.dst}:{args.port}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
