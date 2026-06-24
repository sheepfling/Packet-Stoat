#!/usr/bin/env python3
"""Generate generic parser/visitor/serializer views for every cataloged DIS PDU."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from generate_fastdis_ir import build_ir
from generate_pdu_catalog import DEFAULT_DIS6, DEFAULT_DIS7, ROOT


def _field_names(ir: dict[str, object], class_name: str) -> tuple[str, ...]:
    classes = {entry["name"]: entry for entry in ir["classes"]}
    names: list[str] = []
    seen: set[str] = set()
    chain: list[str] = []
    current = class_name
    while current and current != "root" and current not in seen:
        seen.add(current)
        entry = classes.get(current)
        if entry is None:
            break
        chain.append(current)
        current = str(entry.get("inherits_from", "root"))
    for name in reversed(chain):
        entry = classes[name]
        for field in entry["fields"]:
            field_name = str(field["name"])
            if field_name not in names:
                names.append(field_name)
    return tuple(names)


def _descriptor_rows(ir6: dict[str, object], ir7: dict[str, object]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for ir in (ir6, ir7):
        for pdu in ir["pdus"]:
            class_name = str(pdu["class_name"])
            rows.append(
                {
                    "protocol_version": int(pdu["protocol_version"]),
                    "pdu_type": int(pdu["pdu_type"]),
                    "protocol_family": int(pdu["protocol_family"]),
                    "class_name": class_name,
                    "name": class_name.removesuffix("Pdu"),
                    "family_name": str(pdu["family_name"]),
                    "declared_fields": _field_names(ir, class_name),
                }
            )
    return sorted(rows, key=lambda row: (row["protocol_version"], row["pdu_type"], row["protocol_family"], row["class_name"]))


def generate_python(rows: list[dict[str, object]]) -> str:
    descriptor_rows = "\n".join(
        "    MessageDescriptor("
        f"{row['protocol_version']}, {row['pdu_type']}, {row['protocol_family']}, "
        f"{row['class_name']!r}, {row['name']!r}, {row['family_name']!r}, "
        f"{tuple(row['declared_fields'])!r}),"
        for row in rows
    )
    return (
        '"""Generated generic DIS PDU parser, visitor, and serializer views.\n\n'
        "These views cover every cataloged DIS 6/7 PDU at the packet boundary:\n"
        "header validation, byte-preserving parse, generic field visitation, and\n"
        "round-trip serialization. They are intentionally distinct from typed\n"
        "semantic body decoders such as the Entity State fast path.\n"
        '"""\n\n'
        "from __future__ import annotations\n\n"
        "from collections.abc import Callable, Iterable\n"
        "from typing import NamedTuple\n\n"
        "from . import _fallback\n\n\n"
        "class MessageDescriptor(NamedTuple):\n"
        "    protocol_version: int\n"
        "    pdu_type: int\n"
        "    protocol_family: int\n"
        "    class_name: str\n"
        "    name: str\n"
        "    family_name: str\n"
        "    declared_fields: tuple[str, ...]\n\n\n"
        "class GenericPduView(NamedTuple):\n"
        "    descriptor: MessageDescriptor\n"
        "    header: tuple[int, int, int, int, int, int, int, int]\n"
        "    packet: bytes\n\n"
        "    @property\n"
        "    def body(self) -> bytes:\n"
        "        return self.packet[12:self.header[5]]\n\n\n"
        "class FieldVisit(NamedTuple):\n"
        "    name: str\n"
        "    path: str\n"
        "    kind: str\n"
        "    offset: int\n"
        "    length: int\n"
        "    value: object\n\n\n"
        "MESSAGE_DESCRIPTORS: tuple[MessageDescriptor, ...] = (\n"
        + descriptor_rows
        + "\n)\n\n"
        "_DESCRIPTORS_BY_KEY = {(item.protocol_version, item.pdu_type): item for item in MESSAGE_DESCRIPTORS}\n\n\n"
        "def find_message_descriptor(protocol_version: int, pdu_type: int) -> MessageDescriptor | None:\n"
        "    return _DESCRIPTORS_BY_KEY.get((protocol_version, pdu_type))\n\n\n"
        "def parse_pdu(data: bytes | bytearray | memoryview, *, strict: bool = True) -> GenericPduView | None:\n"
        "    header = _fallback.parse_header(data, strict=strict)\n"
        "    if header is None:\n"
        "        return None\n"
        "    descriptor = find_message_descriptor(header[0], header[2])\n"
        "    if descriptor is None:\n"
        "        if strict:\n"
        "            raise ValueError(f'unknown DIS PDU type {header[2]} for protocol version {header[0]}')\n"
        "        return None\n"
        "    packet = bytes(memoryview(data).cast('B')[:header[5]])\n"
        "    return GenericPduView(descriptor, header, packet)\n\n\n"
        "def serialize_pdu(view: GenericPduView) -> bytes:\n"
        "    if not isinstance(view, GenericPduView):\n"
        "        raise TypeError('serialize_pdu expects a GenericPduView')\n"
        "    return bytes(view.packet)\n\n\n"
        "def visit_pdu_fields(data_or_view: bytes | bytearray | memoryview | GenericPduView) -> tuple[FieldVisit, ...]:\n"
        "    view = data_or_view if isinstance(data_or_view, GenericPduView) else parse_pdu(data_or_view)\n"
        "    if view is None:\n"
        "        return ()\n"
        "    header_names = ('version', 'exercise_id', 'pdu_type', 'protocol_family', 'timestamp', 'length', 'status', 'padding')\n"
        "    header_offsets = (0, 1, 2, 3, 4, 8, 10, 11)\n"
        "    header_lengths = (1, 1, 1, 1, 4, 2, 1 if view.header[0] >= 7 else 0, 1 if view.header[0] >= 7 else 2)\n"
        "    visits = [\n"
        "        FieldVisit(name, f'header.{name}', 'header', offset, length, value)\n"
        "        for name, offset, length, value in zip(header_names, header_offsets, header_lengths, view.header, strict=True)\n"
        "    ]\n"
        "    visits.append(FieldVisit('body', 'body', 'raw_body', 12, max(0, view.header[5] - 12), view.body))\n"
        "    visits.extend(\n"
        "        FieldVisit(name, f'schema.{name}', 'declared_schema_field', -1, -1, None)\n"
        "        for name in view.descriptor.declared_fields\n"
        "    )\n"
        "    return tuple(visits)\n\n\n"
        "def walk_pdu_fields(\n"
        "    data_or_view: bytes | bytearray | memoryview | GenericPduView,\n"
        "    visitor: Callable[[FieldVisit], object],\n"
        ") -> int:\n"
        "    count = 0\n"
        "    for field in visit_pdu_fields(data_or_view):\n"
        "        visitor(field)\n"
        "        count += 1\n"
        "    return count\n\n\n"
        "def roundtrip_packet(data: bytes | bytearray | memoryview) -> bytes:\n"
        "    view = parse_pdu(data)\n"
        "    if view is None:\n"
        "        raise ValueError('packet could not be parsed')\n"
        "    return serialize_pdu(view)\n\n\n"
        "def parse_many(packets: Iterable[bytes | bytearray | memoryview], *, strict: bool = False) -> list[GenericPduView]:\n"
        "    views: list[GenericPduView] = []\n"
        "    for packet in packets:\n"
        "        view = parse_pdu(packet, strict=strict)\n"
        "        if view is not None:\n"
        "            views.append(view)\n"
        "    return views\n\n\n"
        "PDU_PARSERS = {(item.protocol_version, item.pdu_type): parse_pdu for item in MESSAGE_DESCRIPTORS}\n"
        "PDU_SERIALIZERS = {(item.protocol_version, item.pdu_type): serialize_pdu for item in MESSAGE_DESCRIPTORS}\n"
    )


def generate_manifest(rows: list[dict[str, object]]) -> str:
    payload = {
        "version": "0.17.0-alpha7",
        "policy": {
            "parser": "Every cataloged DIS 6/7 PDU has a generated byte-preserving generic parser.",
            "visitor": "Every cataloged DIS 6/7 PDU has generated header/body visitor coverage and schema-declared field names.",
            "serializer": "Every cataloged DIS 6/7 PDU can serialize a parsed generic view back to the original packet bytes.",
            "semantic_boundary": "Generated generic views are not a claim of full typed semantic body decoding.",
        },
        "summary": {
            "records": len(rows),
            "generic_parsers": len(rows),
            "generic_visitors": len(rows),
            "byte_preserving_serializers": len(rows),
        },
        "records": rows,
    }
    return json.dumps(payload, indent=2) + "\n"


def generate_markdown(rows: list[dict[str, object]]) -> str:
    lines = [
        "# Generated Message Views",
        "",
        "FastDIS generates parser, visitor, and serializer views for every cataloged DIS 6/7 PDU.",
        "",
        "Current guarantee:",
        "",
        "- every known PDU has a generated generic parser",
        "- every known PDU has generated header/body visitor coverage",
        "- every known PDU has a byte-preserving serializer for parsed packet views",
        "- typed semantic body decoders remain tracked separately",
        "",
        "This is the broad product coverage layer. The Entity State fast path remains the production typed transform decoder.",
        "",
        "| DIS | PDU | Family | Class | Declared fields | Parser | Visitor | Serializer |",
        "|---:|---:|---|---|---:|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['protocol_version']} | {row['pdu_type']} | {row['family_name']} | `{row['class_name']}` | "
            f"{len(row['declared_fields'])} | generated | generated | byte-preserving |"
        )
    lines.append("")
    return "\n".join(lines)


def outputs(dis6: Path, dis7: Path) -> dict[Path, str]:
    ir6 = build_ir(dis6, 6)
    ir7 = build_ir(dis7, 7)
    rows = _descriptor_rows(ir6, ir7)
    return {
        ROOT / "src" / "fastdis" / "message_views.py": generate_python(rows),
        ROOT / "generated" / "message_views_manifest.json": generate_manifest(rows),
        ROOT / "docs" / "GENERATED_MESSAGE_VIEWS.md": generate_markdown(rows),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dis6", type=Path, default=DEFAULT_DIS6)
    parser.add_argument("--dis7", type=Path, default=DEFAULT_DIS7)
    parser.add_argument("--check", action="store_true", help="Verify generated message view outputs are fresh.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    expected = outputs(args.dis6, args.dis7)
    if args.check:
        failures: list[str] = []
        for path, content in expected.items():
            if not path.exists():
                failures.append(f"missing generated file: {path.relative_to(ROOT)}")
            elif path.read_text(encoding="utf-8") != content:
                failures.append(f"stale generated file: {path.relative_to(ROOT)}")
        if failures:
            for failure in failures:
                print(failure, file=sys.stderr)
            return 1
        print("generated message views are up to date")
        return 0

    for path, content in expected.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    print("generated generic message parsers, visitors, and serializers")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
