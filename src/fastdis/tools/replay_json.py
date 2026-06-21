"""CLI helpers for `.fastdispkt` replay JSONL conversion."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterator, Sequence, cast

from fastdis.packet_json import DecodeLevel, RawPolicy, packet_from_json_record, packet_summary, packet_to_json_record
from fastdis.replay import ReplayFormatError, iter_v1_packets, write_v1_packets


def _to_int(value: object) -> int:
    return int(cast(Any, value))


def _jsonl_records(path: Path) -> Iterator[dict[str, object]]:
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            payload = json.loads(stripped)
            if not isinstance(payload, dict):
                raise ValueError(f"JSONL line {line_number} is not an object")
            yield cast(dict[str, object], payload)


def command_inspect(args: argparse.Namespace) -> int:
    count = 0
    total_bytes = 0
    by_type: dict[tuple[int, int], int] = {}
    first_summary: str | None = None
    for count, packet in enumerate(iter_v1_packets(args.replay), start=1):
        total_bytes += len(packet)
        record = packet_to_json_record(packet, record_index=count - 1, source_format="fastdispkt", decode_level="header", raw_policy="omit")
        header = cast(dict[str, object], record["header"])
        key = (_to_int(header.get("protocol_version", -1)), _to_int(header.get("pdu_type", -1)))
        by_type[key] = by_type.get(key, 0) + 1
        if first_summary is None:
            first_summary = packet_summary(record)
    print(f"FastDIS replay: packets={count} packet_bytes={total_bytes}")
    if first_summary is not None:
        print(f"first_packet: {first_summary}")
    for (version, pdu_type), seen in sorted(by_type.items()):
        print(f"  DIS v{version} PDU {pdu_type}: {seen}")
    return 0


def command_to_json(args: argparse.Namespace) -> int:
    args.out.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with args.out.open("w", encoding="utf-8") as handle:
        for index, packet in enumerate(iter_v1_packets(args.replay)):
            record = packet_to_json_record(
                packet,
                record_index=index,
                source_format="fastdispkt",
                decode_level=args.decode_level,
                raw_policy=args.raw_policy,
            )
            handle.write(json.dumps(record, sort_keys=False))
            handle.write("\n")
            count += 1
    print(f"wrote {count} JSONL packet records to {args.out}")
    return 0


def command_from_json(args: argparse.Namespace) -> int:
    count = write_v1_packets(args.out, (packet_from_json_record(record, prefer_raw=not args.no_prefer_raw) for record in _jsonl_records(args.replay_json)))
    print(f"wrote {count} packets to {args.out}")
    return 0


def command_roundtrip(args: argparse.Namespace) -> int:
    packets = []
    for index, packet in enumerate(iter_v1_packets(args.replay)):
        record = packet_to_json_record(
            packet,
            record_index=index,
            source_format="fastdispkt",
            decode_level=args.decode_level,
            raw_policy="include",
        )
        packets.append(packet_from_json_record(record, prefer_raw=True))
    count = write_v1_packets(args.out, packets)
    print(f"round-tripped {count} packets to {args.out}")
    return 0


def command_diff(args: argparse.Namespace) -> int:
    left = iter_v1_packets(args.left)
    right = iter_v1_packets(args.right)
    index = 0
    while True:
        try:
            left_packet = next(left)
        except StopIteration:
            try:
                next(right)
            except StopIteration:
                print(f"replays match: packets={index}")
                return 0
            print(f"replay differs: right has extra packet at index {index}")
            return 1
        try:
            right_packet = next(right)
        except StopIteration:
            print(f"replay differs: left has extra packet at index {index}")
            return 1
        if left_packet != right_packet:
            print(
                "replay differs: "
                f"index={index} left_size={len(left_packet)} right_size={len(right_packet)}"
            )
            return 1
        index += 1


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="fastdis replay", description="Convert FastDIS `.fastdispkt` replays to/from JSONL.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect = subparsers.add_parser("inspect", help="Print replay packet counts and type summary")
    inspect.add_argument("replay", type=Path)

    to_json = subparsers.add_parser("to-json", help="Convert a `.fastdispkt` replay to JSONL")
    to_json.add_argument("replay", type=Path)
    to_json.add_argument("--out", type=Path, required=True)
    to_json.add_argument("--decode-level", choices=("header", "typed", "semantic"), default="semantic")
    to_json.add_argument("--raw-policy", choices=("include", "omit"), default="include")

    from_json = subparsers.add_parser("from-json", help="Convert JSONL packet records to `.fastdispkt`")
    from_json.add_argument("replay_json", type=Path)
    from_json.add_argument("--out", type=Path, required=True)
    from_json.add_argument("--no-prefer-raw", action="store_true")

    roundtrip = subparsers.add_parser("roundtrip", help="Round-trip a replay through lossless JSON envelopes")
    roundtrip.add_argument("replay", type=Path)
    roundtrip.add_argument("--out", type=Path, required=True)
    roundtrip.add_argument("--decode-level", choices=("header", "typed", "semantic"), default="semantic")

    diff = subparsers.add_parser("diff", help="Compare two `.fastdispkt` replay files packet-by-packet")
    diff.add_argument("left", type=Path)
    diff.add_argument("right", type=Path)

    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.command == "inspect":
            return command_inspect(args)
        if args.command == "to-json":
            args.decode_level = cast(DecodeLevel, args.decode_level)
            args.raw_policy = cast(RawPolicy, args.raw_policy)
            return command_to_json(args)
        if args.command == "from-json":
            return command_from_json(args)
        if args.command == "roundtrip":
            args.decode_level = cast(DecodeLevel, args.decode_level)
            return command_roundtrip(args)
        if args.command == "diff":
            return command_diff(args)
    except ReplayFormatError as exc:
        print(f"replay format error: {exc}")
        return 2
    raise SystemExit(f"Unknown replay command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
