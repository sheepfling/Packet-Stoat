"""CLI helpers for raw DIS PDU JSON conversion."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence, cast

from fastdis.packet_json import (
    DecodeLevel,
    RawPolicy,
    entity_state_packet_to_json,
    packet_from_json_record,
    packet_summary,
    packet_to_json_record,
)


def _read_packet(path: Path) -> bytes:
    return path.read_bytes()


def _write_json(path: Path, payload: object, *, pretty: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2 if pretty else None, sort_keys=pretty)
    path.write_text(f"{text}\n", encoding="utf-8")


def command_inspect(args: argparse.Namespace) -> int:
    record = packet_to_json_record(
        _read_packet(args.packet),
        source_format="binary",
        decode_level=args.decode_level,
        raw_policy="omit",
    )
    print(packet_summary(record))
    return 0


def command_to_json(args: argparse.Namespace) -> int:
    packet = _read_packet(args.packet)
    if args.editable_entity_state:
        payload = entity_state_packet_to_json(packet)
    else:
        payload = packet_to_json_record(
            packet,
            source_format="binary",
            decode_level=args.decode_level,
            raw_policy=args.raw_policy,
        )
    _write_json(args.out, payload, pretty=args.pretty)
    return 0


def command_from_json(args: argparse.Namespace) -> int:
    payload = json.loads(args.packet_json.read_text(encoding="utf-8"))
    packet = packet_from_json_record(payload, prefer_raw=not args.no_prefer_raw)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(packet)
    return 0


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="fastdis pdu", description="Convert single DIS PDU packets to/from JSON.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect = subparsers.add_parser("inspect", help="Print a compact human-readable packet summary")
    inspect.add_argument("packet", type=Path)
    inspect.add_argument("--decode-level", choices=("header", "typed", "semantic"), default="semantic")

    to_json = subparsers.add_parser("to-json", help="Convert one binary PDU packet to JSON")
    to_json.add_argument("packet", type=Path)
    to_json.add_argument("--out", type=Path, required=True)
    to_json.add_argument("--decode-level", choices=("header", "typed", "semantic"), default="semantic")
    to_json.add_argument("--raw-policy", choices=("include", "omit"), default="include")
    to_json.add_argument("--editable-entity-state", action="store_true", help="Emit editable Entity State JSON")
    to_json.add_argument("--pretty", action="store_true")

    from_json = subparsers.add_parser("from-json", help="Convert one FastDIS JSON packet record to binary")
    from_json.add_argument("packet_json", type=Path)
    from_json.add_argument("--out", type=Path, required=True)
    from_json.add_argument("--no-prefer-raw", action="store_true", help="Ignore raw_base64 and use editable fields")

    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    args.decode_level = getattr(args, "decode_level", "semantic")
    args.raw_policy = getattr(args, "raw_policy", "include")
    if args.command == "inspect":
        args.decode_level = cast(DecodeLevel, args.decode_level)
        return command_inspect(args)
    if args.command == "to-json":
        args.decode_level = cast(DecodeLevel, args.decode_level)
        args.raw_policy = cast(RawPolicy, args.raw_policy)
        return command_to_json(args)
    if args.command == "from-json":
        return command_from_json(args)
    raise SystemExit(f"Unknown pdu command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
