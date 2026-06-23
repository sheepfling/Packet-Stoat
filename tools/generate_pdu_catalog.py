#!/usr/bin/env python3
"""Generate fastdis DIS PDU catalog metadata from Open-DIS XML descriptions."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import re
import sys
import textwrap
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DIS6 = ROOT / "references" / "open-dis" / "DIS6.xml"
DEFAULT_DIS7 = ROOT / "references" / "open-dis" / "DIS7.xml"
DEFAULT_PATCH_DIS6 = ROOT / "schemas" / "patches" / "dis6"
DEFAULT_PATCH_DIS7 = ROOT / "schemas" / "patches" / "dis7"

IMPLEMENTED_BODY_DECODERS = {
    "EntityStatePdu",
    "EntityStateUpdatePdu",
}

FAMILY_NAMES = {
    1: "Entity Information",
    2: "Warfare",
    3: "Logistics",
    4: "Radio Communications",
    5: "Simulation Management",
    6: "Distributed Emission Regeneration",
    7: "Entity Management",
    8: "Minefield",
    9: "Synthetic Environment",
    10: "Simulation Management with Reliability",
    11: "Live Entity",
    12: "Non-Real-Time",
    13: "Information Operations",
}


@dataclass(frozen=True)
class PduRecord:
    protocol_version: int
    pdu_type: int
    protocol_family: int
    class_name: str
    name: str
    family_name: str
    body_decoder: bool


@dataclass(frozen=True)
class CoverageRecord:
    protocol_version: int
    pdu_type: int
    protocol_family: int
    class_name: str
    name: str
    family_name: str
    c_catalog: bool
    cpp_catalog: bool
    python_catalog: bool
    unreal_catalog: bool
    godot_catalog: bool
    unity_catalog: bool
    c_body_decoder: bool
    cpp_body_decoder: bool
    python_body_decoder: bool
    unreal_adapter: bool
    godot_adapter: bool
    unity_adapter: bool
    cataloged: bool
    header_validated: bool
    min_length_known: bool
    typed_prefix_parser: bool
    full_parser: bool
    serializer: bool
    roundtrip_tested: bool
    fuzzed_shallow: bool
    fuzzed_deep: bool
    differential_oracle: str | None


def coverage_records(records: list[PduRecord]) -> list[CoverageRecord]:
    out: list[CoverageRecord] = []
    for record in records:
        body = record.body_decoder
        out.append(
            CoverageRecord(
                protocol_version=record.protocol_version,
                pdu_type=record.pdu_type,
                protocol_family=record.protocol_family,
                class_name=record.class_name,
                name=record.name,
                family_name=record.family_name,
                c_catalog=True,
                cpp_catalog=True,
                python_catalog=True,
                unreal_catalog=True,
                godot_catalog=True,
                unity_catalog=False,
                c_body_decoder=body,
                cpp_body_decoder=body,
                python_body_decoder=body,
                unreal_adapter=body,
                godot_adapter=body,
                unity_adapter=False,
                cataloged=True,
                header_validated=True,
                min_length_known=body,
                typed_prefix_parser=body,
                full_parser=True,
                serializer=True,
                roundtrip_tested=True,
                fuzzed_shallow=True,
                fuzzed_deep=body,
                differential_oracle="open-dis-python fixture report" if record.class_name == "EntityStatePdu" else None,
            )
        )
    return out


def display_name(class_name: str) -> str:
    base = class_name[:-3] if class_name.endswith("Pdu") else class_name
    return re.sub(r"(?<!^)(?=[A-Z])", " ", base)


def macro_name(class_name: str) -> str:
    base = class_name[:-3] if class_name.endswith("Pdu") else class_name
    chars: list[str] = []
    for index, ch in enumerate(base):
        if ch.isupper() and index > 0 and (not base[index - 1].isupper()):
            chars.append("_")
        chars.append(ch.upper())
    return re.sub(r"[^A-Z0-9]+", "_", "".join(chars)).strip("_")


def _class_elements(path: Path, patch_dir: Path | None = None) -> list[ET.Element]:
    elements = list(ET.parse(path).getroot().findall("class"))
    if patch_dir is not None and patch_dir.exists():
        for patch_path in sorted(patch_dir.glob("*.xml")):
            patch_root = ET.parse(patch_path).getroot()
            elements.extend(patch_root.findall("class"))
    return elements


def load_classes(path: Path, patch_dir: Path | None = None) -> dict[str, dict[str, object]]:
    classes: dict[str, dict[str, object]] = {}
    for cls in _class_elements(path, patch_dir):
        name = cls.attrib["name"]
        initial: dict[str, int] = {}
        for item in cls.findall("initialValue"):
            field_name = item.attrib.get("name")
            value = item.attrib.get("value")
            if field_name and value is not None:
                try:
                    initial[field_name] = int(value, 0)
                except ValueError:
                    continue
        classes[name] = {
            "inherits": cls.attrib.get("inheritsFrom", "root"),
            "initial": initial,
        }
    return classes


def inherited_value(classes: dict[str, dict[str, object]], class_name: str, field_name: str) -> int | None:
    seen: set[str] = set()
    current = class_name
    while current and current != "root" and current not in seen:
        seen.add(current)
        cls = classes.get(current)
        if cls is None:
            return None
        initial = cls["initial"]
        assert isinstance(initial, dict)
        if field_name in initial:
            return int(initial[field_name])
        current = str(cls.get("inherits", "root"))
    return None


def catalog_from_xml(path: Path, protocol_version: int) -> list[PduRecord]:
    patch_dir = DEFAULT_PATCH_DIS6 if protocol_version == 6 else DEFAULT_PATCH_DIS7
    classes = load_classes(path, patch_dir)
    records: list[PduRecord] = []
    seen: set[tuple[int, int]] = set()
    for class_name, cls in classes.items():
        if class_name == "FastEntityStatePdu":
            continue
        initial = cls["initial"]
        assert isinstance(initial, dict)
        if "pduType" not in initial:
            continue
        pdu_type = int(initial["pduType"])
        protocol_family = inherited_value(classes, class_name, "protocolFamily")
        if protocol_family is None:
            continue
        key = (pdu_type, protocol_family)
        if key in seen:
            continue
        seen.add(key)
        records.append(
            PduRecord(
                protocol_version=protocol_version,
                pdu_type=pdu_type,
                protocol_family=protocol_family,
                class_name=class_name,
                name=display_name(class_name),
                family_name=FAMILY_NAMES.get(protocol_family, f"Protocol Family {protocol_family}"),
                body_decoder=class_name in IMPLEMENTED_BODY_DECODERS,
            )
        )
    return sorted(records, key=lambda item: (item.protocol_version, item.pdu_type, item.protocol_family, item.class_name))


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def generate_c_header(records: list[PduRecord]) -> str:
    macros: list[str] = []
    seen_macros: set[str] = set()
    for record in sorted(records, key=lambda item: (item.pdu_type, item.class_name, item.protocol_version)):
        name = f"FASTDIS_PDU_TYPE_{macro_name(record.class_name)}"
        if name in seen_macros:
            continue
        seen_macros.add(name)
        macros.append(f"#define {name:<52} {record.pdu_type}u")

    entries = "\n".join(
        f'    {{{record.protocol_version}u, {record.pdu_type}u, {record.protocol_family}u, '
        f'"{record.class_name}", "{record.name}", "{record.family_name}", {1 if record.body_decoder else 0}u}},'
        for record in records
    )

    return (
        "/* Generated by tools/generate_pdu_catalog.py. Do not edit manually. */\n"
        "#ifndef FASTDIS_PDU_CATALOG_H\n"
        "#define FASTDIS_PDU_CATALOG_H\n\n"
        '#include "fastdis/fastdis.h"\n\n'
        "#ifdef __cplusplus\nextern \"C\" {\n#endif\n\n"
        "typedef struct fastdis_pdu_catalog_entry_s {\n"
        "    uint8_t protocol_version;\n"
        "    uint8_t pdu_type;\n"
        "    uint8_t protocol_family;\n"
        "    const char* class_name;\n"
        "    const char* name;\n"
        "    const char* family_name;\n"
        "    uint8_t has_body_decoder;\n"
        "} fastdis_pdu_catalog_entry_t;\n\n"
        + "\n".join(macros)
        + "\n\n"
        f"#define FASTDIS_PDU_CATALOG_COUNT {len(records)}u\n\n"
        "static const fastdis_pdu_catalog_entry_t FASTDIS_PDU_CATALOG[] = {\n"
        + entries
        + "\n};\n\n"
        "static inline const fastdis_pdu_catalog_entry_t* fastdis_pdu_catalog_find(uint8_t protocol_version, uint8_t pdu_type) {\n"
        "    for (uint32_t i = 0; i < FASTDIS_PDU_CATALOG_COUNT; ++i) {\n"
        "        const fastdis_pdu_catalog_entry_t* entry = &FASTDIS_PDU_CATALOG[i];\n"
        "        if (entry->protocol_version == protocol_version && entry->pdu_type == pdu_type) {\n"
        "            return entry;\n"
        "        }\n"
        "    }\n"
        "    return 0;\n"
        "}\n\n"
        "#ifdef __cplusplus\n}\n#endif\n\n"
        "#endif /* FASTDIS_PDU_CATALOG_H */\n"
    )


def generate_cpp_header() -> str:
    return textwrap.dedent(
        """\
        /* Generated wrapper for the source-level PDU catalog. */
        #ifndef FASTDIS_PDU_CATALOG_HPP
        #define FASTDIS_PDU_CATALOG_HPP

        #include <fastdis/fastdis_pdu_catalog.h>

        #include <cstddef>
        #include <cstdint>

        namespace fastdis {

        using PduCatalogEntry = fastdis_pdu_catalog_entry_t;

        inline constexpr std::size_t pdu_catalog_count = FASTDIS_PDU_CATALOG_COUNT;

        inline const PduCatalogEntry* pdu_catalog() noexcept {
            return FASTDIS_PDU_CATALOG;
        }

        inline const PduCatalogEntry* find_pdu(std::uint8_t protocol_version, std::uint8_t pdu_type) noexcept {
            return fastdis_pdu_catalog_find(protocol_version, pdu_type);
        }

        inline bool has_body_decoder(std::uint8_t protocol_version, std::uint8_t pdu_type) noexcept {
            const PduCatalogEntry* entry = find_pdu(protocol_version, pdu_type);
            return entry != nullptr && entry->has_body_decoder != 0u;
        }

        } // namespace fastdis

        #endif /* FASTDIS_PDU_CATALOG_HPP */
        """
    )


def generate_python(records: list[PduRecord]) -> str:
    rows = "\n".join(
        f'    PduCatalogEntry({record.protocol_version}, {record.pdu_type}, {record.protocol_family}, '
        f'"{record.class_name}", "{record.name}", "{record.family_name}", {record.body_decoder}),'
        for record in records
    )
    return (
        '"""Generated DIS 6/7 PDU catalog metadata from Open-DIS XML descriptions."""\n\n'
        "from __future__ import annotations\n\n"
        "from typing import NamedTuple\n\n\n"
        "class PduCatalogEntry(NamedTuple):\n"
        "    protocol_version: int\n"
        "    pdu_type: int\n"
        "    protocol_family: int\n"
        "    class_name: str\n"
        "    name: str\n"
        "    family_name: str\n"
        "    has_body_decoder: bool\n\n\n"
        "PDU_CATALOG: tuple[PduCatalogEntry, ...] = (\n"
        + rows
        + "\n)\n\n"
        "def find_pdu(protocol_version: int, pdu_type: int) -> PduCatalogEntry | None:\n"
        "    for entry in PDU_CATALOG:\n"
        "        if entry.protocol_version == protocol_version and entry.pdu_type == pdu_type:\n"
        "            return entry\n"
        "    return None\n\n"
        "def known_pdu_types(protocol_version: int) -> list[int]:\n"
        "    return sorted({entry.pdu_type for entry in PDU_CATALOG if entry.protocol_version == protocol_version})\n\n"
        "def body_decoder_available(protocol_version: int, pdu_type: int) -> bool:\n"
        "    entry = find_pdu(protocol_version, pdu_type)\n"
        "    return bool(entry and entry.has_body_decoder)\n"
    )


def generate_markdown(records: list[PduRecord]) -> str:
    lines = [
        "# DIS PDU Catalog",
        "",
        "Generated from Open-DIS `dis-description` XML files. This catalog lists known DIS 6 and DIS 7 PDU classes and marks whether fastdis currently implements a body decoder.",
        "",
        "A known catalog entry does not imply full body parsing. Alpha 2 intentionally keeps Entity State as the implemented fast path while exposing metadata for the broader DIS message surface.",
        "",
        "| DIS | PDU type | Family | Class | Body decoder |",
        "|---:|---:|---|---|---|",
    ]
    for record in records:
        lines.append(
            f"| {record.protocol_version} | {record.pdu_type} | {record.family_name} | "
            f"`{record.class_name}` | {'yes' if record.body_decoder else 'no'} |"
        )
    lines.append("")
    return "\n".join(lines)


def generate_coverage_json(records: list[PduRecord]) -> str:
    coverage = coverage_records(records)
    payload = {
        "source": "Open-DIS dis-description DIS6.xml and DIS7.xml",
        "policy": "Catalog support is metadata. Generic parser/serializer support is byte-preserving packet-view support. Body decoder support means fastdis exposes a typed semantic parser/adapter path.",
        "records": [record.__dict__ for record in coverage],
    }
    return json.dumps(payload, indent=2) + "\n"


def generate_message_coverage_manifest_json(records: list[PduRecord]) -> str:
    coverage = coverage_records(records)
    payload = {
        "version": "0.13.0-alpha3-dev",
        "generated_from": [
            "references/open-dis/DIS6.xml",
            "references/open-dis/DIS7.xml",
        ],
        "policy": {
            "cataloged": "Known DIS 6/7 message metadata is present in generated fastdis catalogs.",
            "header_validated": "The shared header parser validates the fixed 12-byte DIS header and declared packet length handling.",
            "min_length_known": "A PDU-specific minimum body length is known and enforced by typed parser logic.",
            "typed_prefix_parser": "fastdis exposes a typed body-prefix parser path for this PDU.",
            "full_parser": "fastdis exposes a generated full packet-view parser for this PDU. This is generic and byte-preserving unless typed_prefix_parser is also true.",
            "serializer": "fastdis can serialize the generated packet view back to bytes.",
            "roundtrip_tested": "fastdis has generated packet-view parse/serialize roundtrip tests for this PDU.",
            "fuzzed_shallow": "This PDU has broad shallow fuzz coverage for header, dispatch, and length handling.",
            "fuzzed_deep": "Typed parsing for this PDU is exercised by deep fuzz targets.",
            "differential_oracle": "Independent implementation oracle used for semantic comparisons, if any.",
        },
        "summary": {
            "records": len(coverage),
            "cataloged": sum(1 for item in coverage if item.cataloged),
            "header_validated": sum(1 for item in coverage if item.header_validated),
            "min_length_known": sum(1 for item in coverage if item.min_length_known),
            "typed_prefix_parser": sum(1 for item in coverage if item.typed_prefix_parser),
            "full_parser": sum(1 for item in coverage if item.full_parser),
            "serializer": sum(1 for item in coverage if item.serializer),
            "roundtrip_tested": sum(1 for item in coverage if item.roundtrip_tested),
            "fuzzed_shallow": sum(1 for item in coverage if item.fuzzed_shallow),
            "fuzzed_deep": sum(1 for item in coverage if item.fuzzed_deep),
        },
        "records": [record.__dict__ for record in coverage],
    }
    return json.dumps(payload, indent=2) + "\n"


def yes_no(value: bool) -> str:
    return "yes" if value else "no"


def generate_cross_language_markdown(records: list[PduRecord]) -> str:
    coverage = coverage_records(records)
    lines = [
        "# Cross-Language DIS Message Set",
        "",
        "This is the complete, explicit Alpha 2 message coverage table generated from Open-DIS `DIS6.xml` and `DIS7.xml`.",
        "",
        "Definitions:",
        "",
        "- `catalog`: the language/surface can identify the PDU type/name/family from generated metadata.",
        "- `body`: the language/surface has a typed fastdis body decoder or adapter path.",
        "- `adapter`: Unreal/Godot engine path can consume and apply that message type without custom user glue.",
        "",
        "Honest current state: C, C++, Python, Unreal, and Godot have catalog visibility for every listed DIS6/DIS7 PDU. Typed body/adapter support is Entity State only. Unity has no adapter yet.",
        "",
        "| DIS | PDU | Family | Class | C catalog | C body | C++ catalog | C++ body | Python catalog | Python body | Unreal catalog | Unreal adapter | Godot catalog | Godot adapter | Unity catalog | Unity adapter |",
        "|---:|---:|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for item in coverage:
        lines.append(
            f"| {item.protocol_version} | {item.pdu_type} | {item.family_name} | `{item.class_name}` | "
            f"{yes_no(item.c_catalog)} | {yes_no(item.c_body_decoder)} | "
            f"{yes_no(item.cpp_catalog)} | {yes_no(item.cpp_body_decoder)} | "
            f"{yes_no(item.python_catalog)} | {yes_no(item.python_body_decoder)} | "
            f"{yes_no(item.unreal_catalog)} | {yes_no(item.unreal_adapter)} | "
            f"{yes_no(item.godot_catalog)} | {yes_no(item.godot_adapter)} | "
            f"{yes_no(item.unity_catalog)} | {yes_no(item.unity_adapter)} |"
        )
    lines.append("")
    return "\n".join(lines)


def generate_message_set_python(records: list[PduRecord]) -> str:
    rows = "\n".join(
        "    MessageCoverage("
        f"{item.protocol_version}, {item.pdu_type}, {item.protocol_family}, "
        f'"{item.class_name}", "{item.name}", "{item.family_name}", '
        f"{item.c_catalog}, {item.cpp_catalog}, {item.python_catalog}, "
        f"{item.unreal_catalog}, {item.godot_catalog}, {item.unity_catalog}, "
        f"{item.c_body_decoder}, {item.cpp_body_decoder}, {item.python_body_decoder}, "
        f"{item.unreal_adapter}, {item.godot_adapter}, {item.unity_adapter}, "
        f"{item.cataloged}, {item.header_validated}, {item.min_length_known}, "
        f"{item.typed_prefix_parser}, {item.full_parser}, {item.serializer}, "
        f"{item.roundtrip_tested}, {item.fuzzed_shallow}, {item.fuzzed_deep}, "
        f"{item.differential_oracle!r}),"
        for item in coverage_records(records)
    )
    return (
        '"""Generated fastdis DIS message coverage metadata."""\n\n'
        "from __future__ import annotations\n\n"
        "from typing import NamedTuple\n\n\n"
        "class MessageCoverage(NamedTuple):\n"
        "    protocol_version: int\n"
        "    pdu_type: int\n"
        "    protocol_family: int\n"
        "    class_name: str\n"
        "    name: str\n"
        "    family_name: str\n"
        "    c_catalog: bool\n"
        "    cpp_catalog: bool\n"
        "    python_catalog: bool\n"
        "    unreal_catalog: bool\n"
        "    godot_catalog: bool\n"
        "    unity_catalog: bool\n"
        "    c_body_decoder: bool\n"
        "    cpp_body_decoder: bool\n"
        "    python_body_decoder: bool\n"
        "    unreal_adapter: bool\n"
        "    godot_adapter: bool\n"
        "    unity_adapter: bool\n"
        "    cataloged: bool\n"
        "    header_validated: bool\n"
        "    min_length_known: bool\n"
        "    typed_prefix_parser: bool\n"
        "    full_parser: bool\n"
        "    serializer: bool\n"
        "    roundtrip_tested: bool\n"
        "    fuzzed_shallow: bool\n"
        "    fuzzed_deep: bool\n"
        "    differential_oracle: str | None\n\n\n"
        "MESSAGE_COVERAGE: tuple[MessageCoverage, ...] = (\n"
        + rows
        + "\n)\n\n"
        "def find_message_coverage(protocol_version: int, pdu_type: int) -> MessageCoverage | None:\n"
        "    for entry in MESSAGE_COVERAGE:\n"
        "        if entry.protocol_version == protocol_version and entry.pdu_type == pdu_type:\n"
        "            return entry\n"
        "    return None\n\n"
        "def unsupported_body_decoders(protocol_version: int | None = None) -> list[MessageCoverage]:\n"
        "    return [\n"
        "        entry\n"
        "        for entry in MESSAGE_COVERAGE\n"
        "        if (protocol_version is None or entry.protocol_version == protocol_version)\n"
        "        and not entry.c_body_decoder\n"
        "    ]\n"
    )


def generate_message_coverage_markdown(records: list[PduRecord]) -> str:
    coverage = coverage_records(records)
    lines = [
        "# Message Coverage",
        "",
        "This is the generated Alpha 3 message-coverage manifest for fastdis.",
        "",
        "Honest current state:",
        "",
        "- Every listed DIS 6/7 PDU is cataloged in generated metadata.",
        "- Fixed-header validation is in place for all packets at the shared header layer.",
        "- PDU-specific minimum-length knowledge, typed parsing, and deep fuzzing remain Entity State only.",
        "- Every listed DIS 6/7 PDU has a generated generic packet-view parser, visitor, byte-preserving serializer, and roundtrip guarantee.",
        "- Typed semantic body parsing and deep fuzzing remain Entity State only.",
        "",
        "Column definitions:",
        "",
        "- `cataloged`: appears in generated DIS 6/7 metadata.",
        "- `header`: shared header parser validates the packet header/declared length path.",
        "- `min`: PDU-specific minimum length is known by typed parser logic.",
        "- `prefix`: a typed body-prefix parser exists.",
        "- `full`: a generated full packet-view parser exists.",
        "- `ser`: a byte-preserving packet-view serializer exists.",
        "- `rt`: generated packet-view parse/serialize roundtrip tests exist.",
        "- `fuzz shallow`: broad header/dispatch/length fuzz coverage exists.",
        "- `fuzz deep`: deep typed-parser fuzz coverage exists.",
        "- `oracle`: independent semantic differential oracle, if any.",
        "",
        "| DIS | PDU | Family | Class | cataloged | header | min | prefix | full | ser | rt | fuzz shallow | fuzz deep | oracle |",
        "|---:|---:|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for item in coverage:
        lines.append(
            f"| {item.protocol_version} | {item.pdu_type} | {item.family_name} | `{item.class_name}` | "
            f"{yes_no(item.cataloged)} | {yes_no(item.header_validated)} | {yes_no(item.min_length_known)} | "
            f"{yes_no(item.typed_prefix_parser)} | {yes_no(item.full_parser)} | {yes_no(item.serializer)} | "
            f"{yes_no(item.roundtrip_tested)} | {yes_no(item.fuzzed_shallow)} | {yes_no(item.fuzzed_deep)} | "
            f"{item.differential_oracle or ''} |"
        )
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dis6", type=Path, default=DEFAULT_DIS6)
    parser.add_argument("--dis7", type=Path, default=DEFAULT_DIS7)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify generated outputs are up to date instead of writing them.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    records = catalog_from_xml(args.dis6, 6) + catalog_from_xml(args.dis7, 7)

    outputs = {
        ROOT / "include" / "fastdis" / "fastdis_pdu_catalog.h": generate_c_header(records),
        ROOT / "include" / "fastdis" / "fastdis_pdu_catalog.hpp": generate_cpp_header(),
        ROOT / "src" / "fastdis" / "pdu_catalog.py": generate_python(records),
        ROOT / "src" / "fastdis" / "message_set.py": generate_message_set_python(records),
        ROOT / "docs" / "DIS_PDU_CATALOG.md": generate_markdown(records),
        ROOT / "docs" / "MESSAGE_CROSS_LANGUAGE_SET.md": generate_cross_language_markdown(records),
        ROOT / "docs" / "message_cross_language_set.json": generate_coverage_json(records),
        ROOT / "docs" / "MESSAGE_COVERAGE.md": generate_message_coverage_markdown(records),
        ROOT / "generated" / "message_coverage_manifest.json": generate_message_coverage_manifest_json(records),
    }
    if args.check:
        stale: list[Path] = []
        missing: list[Path] = []
        for path, content in outputs.items():
            if not path.exists():
                missing.append(path)
                continue
            if path.read_text(encoding="utf-8") != content:
                stale.append(path)
        if missing or stale:
            for path in missing:
                print(f"missing generated file: {path.relative_to(ROOT)}", file=sys.stderr)
            for path in stale:
                print(f"stale generated file: {path.relative_to(ROOT)}", file=sys.stderr)
            return 1
        print(f"generated outputs are up to date for {len(records)} PDU catalog entries")
        return 0

    for path, content in outputs.items():
        write(path, content)
    print(f"generated {len(records)} PDU catalog entries across {len(outputs)} artifacts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
