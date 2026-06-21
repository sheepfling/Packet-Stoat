#!/usr/bin/env python3
"""Generate slotted semantic PDU parser entry points for every DIS 6/7 PDU row."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

from generate_pdu_catalog import DEFAULT_DIS6, DEFAULT_DIS7, ROOT
from generate_typed_pdu_parsers import typed_rows


def semantic_rows(dis6: Path, dis7: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in typed_rows(dis6, dis7):
        typed_semantic = bool(row["typed_semantic"])
        semantic_level = "semantic_prefix" if typed_semantic else "semantic_observation"
        semantic_class = str(row["parser_class"]).replace("Pdu", "SemanticPdu")
        if semantic_class == row["parser_class"]:
            semantic_class = f"{row['parser_class']}Semantic"
        rows.append(
            {
                **row,
                "semantic_class": semantic_class,
                "semantic_parser": True,
                "semantic_level": semantic_level,
                "fully_domain_decoded": typed_semantic,
                "diagnostic_policy": (
                    "domain_prefix_available"
                    if typed_semantic
                    else "typed observation preserves raw body and exposes schema/field metadata"
                ),
            }
        )
    return rows


def _descriptor_literal(row: dict[str, Any]) -> str:
    return (
        "    SemanticPduDescriptor("
        f"{row['protocol_version']}, {row['pdu_type']}, {row['protocol_family']}, "
        f"{row['standard_name']!r}, {row['standard_class_name']!r}, {row['semantic_class']!r}, "
        f"{row['parser_class']!r}, {row['family_name']!r}, {row['schema_status']!r}, "
        f"{row['catalog_status']!r}, {tuple(row['declared_fields'])!r}, {row['semantic_level']!r}, "
        f"{bool(row['fully_domain_decoded'])!r}),"
    )


def generate_python(rows: list[dict[str, Any]]) -> str:
    class_defs = "\n\n".join(
        f"@dataclass(frozen=True, slots=True)\nclass {row['semantic_class']}(SemanticPdu):\n    pass"
        for row in rows
    )
    descriptors = "\n".join(_descriptor_literal(row) for row in rows)
    class_map_entries = "\n".join(f"    {row['semantic_class']!r}: {row['semantic_class']}," for row in rows)
    return (
        '"""Generated slotted semantic DIS PDU parser entry points.\n\n'
        "Every standard DIS 6/7 PDU row gets a semantic parser class. Rows without\n"
        "full domain decoding are represented as explicit semantic observations\n"
        "with raw-body preservation and diagnostics.\n"
        '"""\n\n'
        "from __future__ import annotations\n\n"
        "from dataclasses import dataclass\n"
        "from types import MappingProxyType\n"
        "from typing import Mapping\n\n"
        "from .typed_pdus import TypedPdu, parse_typed_pdu, serialize_typed_pdu\n\n\n"
        "@dataclass(frozen=True, slots=True)\n"
        "class SemanticPduDescriptor:\n"
        "    protocol_version: int\n"
        "    pdu_type: int\n"
        "    protocol_family: int\n"
        "    standard_name: str\n"
        "    standard_class_name: str\n"
        "    semantic_class: str\n"
        "    typed_class: str\n"
        "    family_name: str\n"
        "    schema_status: str\n"
        "    catalog_status: str\n"
        "    declared_fields: tuple[str, ...]\n"
        "    semantic_level: str\n"
        "    fully_domain_decoded: bool\n\n\n"
        "@dataclass(frozen=True, slots=True)\n"
        "class SemanticPdu:\n"
        "    descriptor: SemanticPduDescriptor\n"
        "    typed: TypedPdu\n"
        "    semantic_fields: Mapping[str, object]\n"
        "    diagnostics: tuple[str, ...]\n\n"
        "    @property\n"
        "    def header(self):\n"
        "        return self.typed.header\n\n"
        "    @property\n"
        "    def packet(self) -> bytes:\n"
        "        return self.typed.packet\n\n"
        "    @property\n"
        "    def body(self) -> bytes:\n"
        "        return self.typed.body\n\n"
        "    @property\n"
        "    def semantic_level(self) -> str:\n"
        "        return self.descriptor.semantic_level\n\n\n"
        + class_defs
        + "\n\n\n"
        "SEMANTIC_PDU_DESCRIPTORS: tuple[SemanticPduDescriptor, ...] = (\n"
        + descriptors
        + "\n)\n\n"
        "_DESCRIPTORS_BY_KEY = {(item.protocol_version, item.pdu_type): item for item in SEMANTIC_PDU_DESCRIPTORS}\n"
        "_CLASS_BY_NAME: dict[str, type[SemanticPdu]] = {\n"
        + class_map_entries
        + "\n}\n\n\n"
        "def find_semantic_pdu_descriptor(protocol_version: int, pdu_type: int) -> SemanticPduDescriptor | None:\n"
        "    return _DESCRIPTORS_BY_KEY.get((protocol_version, pdu_type))\n\n\n"
        "def _semantic_fields(descriptor: SemanticPduDescriptor, typed: TypedPdu) -> Mapping[str, object]:\n"
        "    fields = {\n"
        "        'protocol_version': typed.header[0],\n"
        "        'exercise_id': typed.header[1],\n"
        "        'pdu_type': typed.header[2],\n"
        "        'protocol_family': typed.header[3],\n"
        "        'timestamp': typed.header[4],\n"
        "        'declared_length': typed.header[5],\n"
        "        'standard_name': descriptor.standard_name,\n"
        "        'standard_class_name': descriptor.standard_class_name,\n"
        "        'schema_status': descriptor.schema_status,\n"
        "        'catalog_status': descriptor.catalog_status,\n"
        "        'declared_fields': descriptor.declared_fields,\n"
        "        'raw_body_size': len(typed.body),\n"
        "        'raw_body': typed.body,\n"
        "        'typed_parse_level': typed.parse_level,\n"
        "        'fully_domain_decoded': descriptor.fully_domain_decoded,\n"
        "    }\n"
        "    if descriptor.fully_domain_decoded:\n"
        "        fields['semantic_prefix_available'] = True\n"
        "    return MappingProxyType(fields)\n\n\n"
        "def _diagnostics(descriptor: SemanticPduDescriptor) -> tuple[str, ...]:\n"
        "    if descriptor.fully_domain_decoded:\n"
        "        return ('semantic prefix parser available',)\n"
        "    return (\n"
        "        'semantic observation parser: full domain semantics not yet implemented',\n"
        "        f'schema_status={descriptor.schema_status}',\n"
        "    )\n\n\n"
        "def parse_semantic_pdu(data: bytes | bytearray | memoryview, *, strict: bool = True) -> SemanticPdu | None:\n"
        "    typed = parse_typed_pdu(data, strict=strict)\n"
        "    if typed is None:\n"
        "        return None\n"
        "    descriptor = find_semantic_pdu_descriptor(typed.header[0], typed.header[2])\n"
        "    if descriptor is None:\n"
        "        if strict:\n"
        "            raise ValueError(f'unknown DIS PDU type {typed.header[2]} for protocol version {typed.header[0]}')\n"
        "        return None\n"
        "    cls = _CLASS_BY_NAME[descriptor.semantic_class]\n"
        "    return cls(\n"
        "        descriptor=descriptor,\n"
        "        typed=typed,\n"
        "        semantic_fields=_semantic_fields(descriptor, typed),\n"
        "        diagnostics=_diagnostics(descriptor),\n"
        "    )\n\n\n"
        "def serialize_semantic_pdu(view: SemanticPdu) -> bytes:\n"
        "    if not isinstance(view, SemanticPdu):\n"
        "        raise TypeError('serialize_semantic_pdu expects a SemanticPdu')\n"
        "    return serialize_typed_pdu(view.typed)\n\n\n"
        "def parse_many_semantic(packets: list[bytes] | tuple[bytes, ...], *, strict: bool = False) -> list[SemanticPdu]:\n"
        "    out: list[SemanticPdu] = []\n"
        "    for packet in packets:\n"
        "        view = parse_semantic_pdu(packet, strict=strict)\n"
        "        if view is not None:\n"
        "            out.append(view)\n"
        "    return out\n\n\n"
        "SEMANTIC_PDU_PARSERS = {(item.protocol_version, item.pdu_type): parse_semantic_pdu for item in SEMANTIC_PDU_DESCRIPTORS}\n"
        "SEMANTIC_PDU_SERIALIZERS = {(item.protocol_version, item.pdu_type): serialize_semantic_pdu for item in SEMANTIC_PDU_DESCRIPTORS}\n"
    )


def generate_manifest(rows: list[dict[str, Any]]) -> str:
    payload = {
        "schema": "fastdis.semantic_pdu_parser_manifest.v1",
        "policy": {
            "semantic_parser": "Every standard DIS 6/7 PDU row has a generated semantic parser entry point.",
            "semantic_observation": "Rows without full domain decoding produce explicit semantic observations with diagnostics.",
            "semantic_prefix": "Rows with current typed semantic support expose semantic-prefix availability.",
        },
        "summary": {
            "records": len(rows),
            "semantic_parsers": sum(1 for row in rows if row["semantic_parser"]),
            "semantic_observation": sum(1 for row in rows if row["semantic_level"] == "semantic_observation"),
            "semantic_prefix": sum(1 for row in rows if row["semantic_level"] == "semantic_prefix"),
            "fully_domain_decoded": sum(1 for row in rows if row["fully_domain_decoded"]),
        },
        "records": rows,
    }
    return json.dumps(payload, indent=2) + "\n"


def generate_markdown(rows: list[dict[str, Any]]) -> str:
    semantic_parsers = sum(1 for row in rows if row["semantic_parser"])
    semantic_observation = sum(1 for row in rows if row["semantic_level"] == "semantic_observation")
    semantic_prefix = sum(1 for row in rows if row["semantic_level"] == "semantic_prefix")
    fully_domain_decoded = sum(1 for row in rows if row["fully_domain_decoded"])
    lines = [
        "# Semantic PDU Coverage",
        "",
        "FastDIS generates semantic parser entry points for every standard DIS 6/7 PDU row.",
        "",
        "## Summary",
        "",
        f"- Semantic parser entry points: `{semantic_parsers} / 141`",
        f"- Semantic observation parsers: `{semantic_observation} / 141`",
        f"- Semantic prefix parsers: `{semantic_prefix} / 141`",
        f"- Fully domain-decoded semantic parsers: `{fully_domain_decoded} / 141`",
        "",
        "A semantic observation is a real parser entry point with a named slotted class, header identity, raw body preservation, declared-field metadata where available, and diagnostics that say full domain decoding is not implemented yet. This avoids silent overclaiming while still giving every PDU a typed semantic surface.",
        "",
        "| DIS | PDU | Name | Semantic class | Level | Fully decoded |",
        "| ---: | ---: | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {row['protocol_version']} | {row['pdu_type']} | {row['standard_name']} | "
            f"`{row['semantic_class']}` | `{row['semantic_level']}` | "
            f"{'yes' if row['fully_domain_decoded'] else 'no'} |"
        )
    return "\n".join(lines) + "\n"


def outputs(dis6: Path, dis7: Path) -> dict[Path, str]:
    rows = semantic_rows(dis6, dis7)
    return {
        ROOT / "src" / "fastdis" / "semantic_pdus.py": generate_python(rows),
        ROOT / "generated" / "semantic_pdu_parser_manifest.json": generate_manifest(rows),
        ROOT / "docs" / "SEMANTIC_PDU_COVERAGE.md": generate_markdown(rows),
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
            print("stale generated semantic PDU parser artifacts:", file=sys.stderr)
            for path in stale:
                print(f"  {path.relative_to(ROOT)}", file=sys.stderr)
            return 1
        return 0

    for path, content in rendered.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    rows = semantic_rows(args.dis6, args.dis7)
    print(
        "generated semantic PDU parsers "
        f"semantic_parsers={len(rows)} fully_domain_decoded={sum(1 for row in rows if row['fully_domain_decoded'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
