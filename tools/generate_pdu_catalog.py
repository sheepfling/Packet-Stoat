#!/usr/bin/env python3
"""Generate fastdis DIS PDU catalog metadata from Open-DIS XML descriptions."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
import textwrap
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DIS6 = ROOT / "references" / "open-dis" / "DIS6.xml"
DEFAULT_DIS7 = ROOT / "references" / "open-dis" / "DIS7.xml"

IMPLEMENTED_BODY_DECODERS = {
    "EntityStatePdu",
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


def load_classes(path: Path) -> dict[str, dict[str, object]]:
    root = ET.parse(path).getroot()
    classes: dict[str, dict[str, object]] = {}
    for cls in root.findall("class"):
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
    classes = load_classes(path)
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dis6", type=Path, default=DEFAULT_DIS6)
    parser.add_argument("--dis7", type=Path, default=DEFAULT_DIS7)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    records = catalog_from_xml(args.dis6, 6) + catalog_from_xml(args.dis7, 7)

    write(ROOT / "include" / "fastdis" / "fastdis_pdu_catalog.h", generate_c_header(records))
    write(ROOT / "include" / "fastdis" / "fastdis_pdu_catalog.hpp", generate_cpp_header())
    write(ROOT / "src" / "fastdis" / "pdu_catalog.py", generate_python(records))
    write(ROOT / "docs" / "DIS_PDU_CATALOG.md", generate_markdown(records))
    print(f"generated {len(records)} PDU catalog entries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
