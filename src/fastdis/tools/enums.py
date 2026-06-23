"""Inspect SISO-style FastDIS enum labels and coverage."""

from __future__ import annotations

import argparse
import json
from typing import Any

from fastdis import enums


def _print(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def command_check(_args: argparse.Namespace) -> int:
    manifest = enums.coverage_manifest()
    _print(manifest)
    pdu_family = next(row for row in manifest["families"] if row["enum_name"] == "PduType")
    return 0 if pdu_family["values_imported"] == 141 else 1


def command_lookup(args: argparse.Namespace) -> int:
    _print(enums.lookup(args.family, args.value, version=args.version).to_dict())
    return 0


def command_entity_type(args: argparse.Namespace) -> int:
    _print(
        enums.lookup_entity_type(
            args.kind,
            args.domain,
            args.country,
            args.category,
            args.subcategory,
            args.specific,
            args.extra,
        )
    )
    return 0


def command_describe_header(args: argparse.Namespace) -> int:
    _print(enums.describe_packet_header(args.version, args.pdu_type, args.protocol_family, args.force_id))
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("check", help="Print enum coverage and return nonzero if the PDU backbone is incomplete")

    lookup = subparsers.add_parser("lookup", help="Lookup a single enum value")
    lookup.add_argument("family")
    lookup.add_argument("value", type=int)
    lookup.add_argument("--version", type=int, help="DIS version, required for pdu_type")

    entity_type = subparsers.add_parser("entity-type", help="Describe an Entity Type seven-tuple")
    entity_type.add_argument("kind", type=int)
    entity_type.add_argument("domain", type=int)
    entity_type.add_argument("country", type=int)
    entity_type.add_argument("category", type=int)
    entity_type.add_argument("subcategory", type=int)
    entity_type.add_argument("specific", type=int)
    entity_type.add_argument("extra", type=int)

    describe = subparsers.add_parser("describe-header", help="Describe header enum fields")
    describe.add_argument("--version", type=int, required=True)
    describe.add_argument("--pdu-type", type=int, required=True)
    describe.add_argument("--protocol-family", type=int, required=True)
    describe.add_argument("--force-id", type=int)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.command == "check":
        return command_check(args)
    if args.command == "lookup":
        return command_lookup(args)
    if args.command == "entity-type":
        return command_entity_type(args)
    if args.command == "describe-header":
        return command_describe_header(args)
    raise SystemExit(f"Unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
