#!/usr/bin/env python3
"""Generate slotted typed PDU envelope parsers for every DIS 6/7 PDU row."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any

from generate_fastdis_ir import build_ir
from generate_message_views import _field_names
from generate_pdu_catalog import DEFAULT_DIS6, DEFAULT_DIS7, ROOT
from generate_pdu_coverage import build_manifests


def _class_identifier(version: int, class_name: str, pdu_type: int) -> str:
    base = re.sub(r"[^0-9A-Za-z_]+", "_", class_name).strip("_") or f"Pdu{pdu_type}"
    if base[0].isdigit():
        base = f"Pdu{base}"
    return f"Dis{version}{base}"


def _declared_fields_by_key(dis6: Path, dis7: Path) -> dict[tuple[int, int], tuple[str, ...]]:
    out: dict[tuple[int, int], tuple[str, ...]] = {}
    for version, path in ((6, dis6), (7, dis7)):
        ir = build_ir(path, version)
        for pdu in ir["pdus"]:
            key = (int(pdu["protocol_version"]), int(pdu["pdu_type"]))
            out[key] = _field_names(ir, str(pdu["class_name"]))
    return out


def typed_rows(dis6: Path, dis7: Path) -> list[dict[str, Any]]:
    _backbone, coverage = build_manifests(dis6, dis7)
    fields = _declared_fields_by_key(dis6, dis7)
    rows: list[dict[str, Any]] = []
    for row in coverage["rows"]:
        version = int(row["standard_version"])
        pdu_type = int(row["pdu_type"])
        class_name = str(row["standard_class_name"])
        declared_fields = fields.get((version, pdu_type), ())
        parser_class = _class_identifier(version, class_name, pdu_type)
        parse_level = "typed_structural" if declared_fields else "typed_envelope"
        if bool(row["typed_parser"]):
            parse_level = "typed_semantic_prefix"
        rows.append(
            {
                "protocol_version": version,
                "pdu_type": pdu_type,
                "protocol_family": int(row["protocol_family"]),
                "standard_name": str(row["standard_name"]),
                "standard_class_name": class_name,
                "parser_class": parser_class,
                "family_name": str(row["family_name"]),
                "schema_status": str(row["schema_status"]),
                "catalog_status": str(row["catalog_status"]),
                "declared_fields": declared_fields,
                "parse_level": parse_level,
                "typed_envelope": True,
                "typed_structural": bool(declared_fields),
                "typed_semantic": bool(row["typed_parser"]),
                "byte_preserving_serializer": True,
            }
        )
    return sorted(rows, key=lambda item: (item["protocol_version"], item["pdu_type"]))


def _descriptor_literal(row: dict[str, Any]) -> str:
    return (
        "    TypedPduDescriptor("
        f"{row['protocol_version']}, {row['pdu_type']}, {row['protocol_family']}, "
        f"{row['standard_name']!r}, {row['standard_class_name']!r}, {row['parser_class']!r}, "
        f"{row['family_name']!r}, {row['schema_status']!r}, {row['catalog_status']!r}, "
        f"{tuple(row['declared_fields'])!r}, {row['parse_level']!r}),"
    )


def generate_python(rows: list[dict[str, Any]]) -> str:
    class_defs = "\n\n".join(
        f"@dataclass(frozen=True, slots=True)\nclass {row['parser_class']}(TypedPdu):\n    pass"
        for row in rows
    )
    descriptors = "\n".join(_descriptor_literal(row) for row in rows)
    class_map_entries = "\n".join(f"    {row['parser_class']!r}: {row['parser_class']}," for row in rows)
    return (
        '"""Generated slotted typed DIS PDU envelope parsers.\n\n'
        "Every standard DIS 6/7 PDU row gets a concrete typed class. Schema-backed\n"
        "rows also expose declared field names as a lightweight structural field\n"
        "mapping, while all rows preserve raw packet bytes for byte-for-byte\n"
        "serialization.\n"
        '"""\n\n'
        "from __future__ import annotations\n\n"
        "from dataclasses import dataclass\n"
        "from types import MappingProxyType\n"
        "from typing import Mapping\n\n"
        "from . import _fallback\n\n\n"
        "HeaderTuple = tuple[int, int, int, int, int, int, int, int]\n\n\n"
        "@dataclass(frozen=True, slots=True)\n"
        "class TypedPduDescriptor:\n"
        "    protocol_version: int\n"
        "    pdu_type: int\n"
        "    protocol_family: int\n"
        "    standard_name: str\n"
        "    standard_class_name: str\n"
        "    parser_class: str\n"
        "    family_name: str\n"
        "    schema_status: str\n"
        "    catalog_status: str\n"
        "    declared_fields: tuple[str, ...]\n"
        "    parse_level: str\n\n\n"
        "@dataclass(frozen=True, slots=True)\n"
        "class TypedPdu:\n"
        "    descriptor: TypedPduDescriptor\n"
        "    header: HeaderTuple\n"
        "    packet: bytes\n"
        "    fields: Mapping[str, object]\n\n"
        "    @property\n"
        "    def body(self) -> bytes:\n"
        "        return self.packet[12:self.header[5]]\n\n"
        "    @property\n"
        "    def parse_level(self) -> str:\n"
        "        return self.descriptor.parse_level\n\n\n"
        + class_defs
        + "\n\n\n"
        "TYPED_PDU_DESCRIPTORS: tuple[TypedPduDescriptor, ...] = (\n"
        + descriptors
        + "\n)\n\n"
        "_DESCRIPTORS_BY_KEY = {(item.protocol_version, item.pdu_type): item for item in TYPED_PDU_DESCRIPTORS}\n"
        "_CLASS_BY_NAME: dict[str, type[TypedPdu]] = {\n"
        + class_map_entries
        + "\n}\n\n\n"
        "def find_typed_pdu_descriptor(protocol_version: int, pdu_type: int) -> TypedPduDescriptor | None:\n"
        "    return _DESCRIPTORS_BY_KEY.get((protocol_version, pdu_type))\n\n\n"
        "def _field_map(descriptor: TypedPduDescriptor, header: HeaderTuple, packet: bytes) -> Mapping[str, object]:\n"
        "    values: dict[str, object] = {\n"
        "        'protocolVersion': header[0],\n"
        "        'exerciseID': header[1],\n"
        "        'pduType': header[2],\n"
        "        'protocolFamily': header[3],\n"
        "        'timestamp': header[4],\n"
        "        'length': header[5],\n"
        "        'status': header[6],\n"
        "        'padding': header[7],\n"
        "        'rawBody': packet[12:header[5]],\n"
        "    }\n"
        "    for name in descriptor.declared_fields:\n"
        "        values.setdefault(name, None)\n"
        "    return MappingProxyType(values)\n\n\n"
        "def parse_typed_pdu(data: bytes | bytearray | memoryview, *, strict: bool = True) -> TypedPdu | None:\n"
        "    header = _fallback.parse_header(data, strict=strict)\n"
        "    if header is None:\n"
        "        return None\n"
        "    descriptor = find_typed_pdu_descriptor(header[0], header[2])\n"
        "    if descriptor is None:\n"
        "        if strict:\n"
        "            raise ValueError(f'unknown DIS PDU type {header[2]} for protocol version {header[0]}')\n"
        "        return None\n"
        "    packet = bytes(memoryview(data).cast('B')[:header[5]])\n"
        "    cls = _CLASS_BY_NAME[descriptor.parser_class]\n"
        "    return cls(descriptor=descriptor, header=header, packet=packet, fields=_field_map(descriptor, header, packet))\n\n\n"
        "def serialize_typed_pdu(view: TypedPdu) -> bytes:\n"
        "    if not isinstance(view, TypedPdu):\n"
        "        raise TypeError('serialize_typed_pdu expects a TypedPdu')\n"
        "    return bytes(view.packet)\n\n\n"
        "def parse_many_typed(packets: list[bytes] | tuple[bytes, ...], *, strict: bool = False) -> list[TypedPdu]:\n"
        "    out: list[TypedPdu] = []\n"
        "    for packet in packets:\n"
        "        view = parse_typed_pdu(packet, strict=strict)\n"
        "        if view is not None:\n"
        "            out.append(view)\n"
        "    return out\n\n\n"
        "TYPED_PDU_PARSERS = {(item.protocol_version, item.pdu_type): parse_typed_pdu for item in TYPED_PDU_DESCRIPTORS}\n"
        "TYPED_PDU_SERIALIZERS = {(item.protocol_version, item.pdu_type): serialize_typed_pdu for item in TYPED_PDU_DESCRIPTORS}\n"
    )


def generate_manifest(rows: list[dict[str, Any]]) -> str:
    payload = {
        "schema": "fastdis.typed_pdu_parser_manifest.v1",
        "policy": {
            "typed_envelope": "Every standard DIS 6/7 PDU row has a concrete slotted Python class.",
            "typed_structural": "Rows with XML/IR schema expose declared fields as a structural mapping.",
            "typed_semantic": "Rows with hand-supported semantic parsers are tracked separately.",
            "serializer": "All typed views preserve and serialize the original packet bytes.",
        },
        "summary": {
            "records": len(rows),
            "typed_envelope": sum(1 for row in rows if row["typed_envelope"]),
            "typed_structural": sum(1 for row in rows if row["typed_structural"]),
            "typed_semantic": sum(1 for row in rows if row["typed_semantic"]),
            "byte_preserving_serializer": sum(1 for row in rows if row["byte_preserving_serializer"]),
        },
        "records": rows,
    }
    return json.dumps(payload, indent=2) + "\n"


def generate_markdown(rows: list[dict[str, Any]]) -> str:
    typed_envelope = sum(1 for row in rows if row["typed_envelope"])
    typed_structural = sum(1 for row in rows if row["typed_structural"])
    typed_semantic = sum(1 for row in rows if row["typed_semantic"])
    lines = [
        "# Typed PDU Parsers",
        "",
        "FastDIS generates slotted Python typed PDU envelope classes for every standard DIS 6/7 PDU row.",
        "",
        "## Summary",
        "",
        f"- Typed envelope classes: `{typed_envelope} / 141`",
        f"- Typed structural parsers: `{typed_structural} / 141`",
        f"- Typed semantic parsers: `{typed_semantic} / 141`",
        f"- Byte-preserving serializers: `{len(rows)} / 141`",
        "",
        "Typed envelope coverage means every standard PDU dispatches to a named class with header fields, raw body bytes, and byte-preserving serialization. Typed structural coverage means XML/IR-backed declared fields are exposed as a generated field mapping. Typed semantic coverage remains wave-based.",
        "",
        "| DIS | PDU | Name | Parser class | Level | Declared fields |",
        "| ---: | ---: | --- | --- | --- | ---: |",
    ]
    for row in rows:
        lines.append(
            f"| {row['protocol_version']} | {row['pdu_type']} | {row['standard_name']} | "
            f"`{row['parser_class']}` | `{row['parse_level']}` | {len(row['declared_fields'])} |"
        )
    return "\n".join(lines) + "\n"


def outputs(dis6: Path, dis7: Path) -> dict[Path, str]:
    rows = typed_rows(dis6, dis7)
    return {
        ROOT / "src" / "fastdis" / "typed_pdus.py": generate_python(rows),
        ROOT / "generated" / "typed_pdu_parser_manifest.json": generate_manifest(rows),
        ROOT / "docs" / "TYPED_PDU_COVERAGE.md": generate_markdown(rows),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dis6", type=Path, default=DEFAULT_DIS6)
    parser.add_argument("--dis7", type=Path, default=DEFAULT_DIS7)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    rendered = outputs(args.dis6, args.dis7)
    if args.check:
        stale: list[Path] = []
        for path, content in rendered.items():
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                stale.append(path)
        if stale:
            print("stale generated typed PDU parser artifacts:", file=sys.stderr)
            for path in stale:
                print(f"  {path.relative_to(ROOT)}", file=sys.stderr)
            return 1
        return 0

    for path, content in rendered.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    rows = typed_rows(args.dis6, args.dis7)
    print(
        "generated typed PDU parsers "
        f"typed_envelope={len(rows)} typed_structural={sum(1 for row in rows if row['typed_structural'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
