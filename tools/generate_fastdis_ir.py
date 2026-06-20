#!/usr/bin/env python3
"""Generate a normalized fastdis IR from the staged Open-DIS DIS6/DIS7 XML files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

from generate_pdu_catalog import (
    DEFAULT_DIS6,
    DEFAULT_DIS7,
    FAMILY_NAMES,
    ROOT,
    catalog_from_xml,
    inherited_value,
    load_classes,
)


def field_from_attribute(attribute: ET.Element) -> dict[str, object]:
    name = attribute.attrib["name"]
    comment = attribute.attrib.get("comment", "")
    child = next(iter(attribute), None)
    if child is None:
        return {
            "name": name,
            "comment": comment,
            "kind": "unknown",
        }

    if child.tag == "primitive":
        return {
            "name": name,
            "comment": comment,
            "kind": "primitive",
            "primitive_type": child.attrib["type"],
            "default_value": child.attrib.get("defaultValue"),
        }
    if child.tag == "classRef":
        return {
            "name": name,
            "comment": comment,
            "kind": "record",
            "record_type": child.attrib["name"],
        }
    if child.tag == "list":
        element = next(iter(child), None)
        element_kind = "unknown"
        element_type: str | None = None
        if element is not None and element.tag == "primitive":
            element_kind = "primitive"
            element_type = element.attrib["type"]
        elif element is not None and element.tag == "classRef":
            element_kind = "record"
            element_type = element.attrib["name"]
        field: dict[str, object] = {
            "name": name,
            "comment": comment,
            "kind": "list",
            "list_type": child.attrib.get("type"),
            "length": child.attrib.get("length"),
            "count_field": child.attrib.get("countFieldName"),
            "could_be_string": child.attrib.get("couldBeString") == "true",
            "element_kind": element_kind,
            "element_type": element_type,
        }
        if "lengthFieldName" in child.attrib:
            field["length_field"] = child.attrib["lengthFieldName"]
        if "padding" in child.attrib:
            field["padding"] = child.attrib["padding"]
        return field

    return {
        "name": name,
        "comment": comment,
        "kind": child.tag,
    }


def class_entry(xml_class: ET.Element, classes: dict[str, dict[str, object]]) -> dict[str, object]:
    name = xml_class.attrib["name"]
    inherits_from = xml_class.attrib.get("inheritsFrom", "root")
    initial_values = classes[name]["initial"]
    fields = [field_from_attribute(attribute) for attribute in xml_class.findall("attribute")]
    return {
        "name": name,
        "inherits_from": inherits_from,
        "comment": xml_class.attrib.get("comment", ""),
        "initial_values": dict(sorted(initial_values.items())),
        "field_count": len(fields),
        "fields": fields,
    }


def pdu_entry(version: int, class_name: str, entry: dict[str, object], classes: dict[str, dict[str, object]]) -> dict[str, object]:
    protocol_family = inherited_value(classes, class_name, "protocolFamily")
    assert protocol_family is not None
    initial_values = entry["initial"]
    assert isinstance(initial_values, dict)
    pdu_type = int(initial_values["pduType"])
    return {
        "protocol_version": version,
        "pdu_type": pdu_type,
        "protocol_family": protocol_family,
        "family_name": FAMILY_NAMES.get(protocol_family, f"Protocol Family {protocol_family}"),
        "class_name": class_name,
        "inherits_from": entry.get("inherits", "root"),
        "has_body_decoder": class_name == "EntityStatePdu",
        "initial_values": dict(sorted(initial_values.items())),
    }


def build_ir(xml_path: Path, version: int) -> dict[str, object]:
    xml_root = ET.parse(xml_path).getroot()
    classes = load_classes(xml_path)
    class_entries = [class_entry(xml_class, classes) for xml_class in xml_root.findall("class")]
    pdu_entries: list[dict[str, object]] = []
    seen: set[tuple[int, int]] = set()
    for class_name, entry in classes.items():
        initial_values = entry["initial"]
        assert isinstance(initial_values, dict)
        if "pduType" not in initial_values:
            continue
        protocol_family = inherited_value(classes, class_name, "protocolFamily")
        if protocol_family is None:
            continue
        key = (int(initial_values["pduType"]), protocol_family)
        if key in seen:
            continue
        seen.add(key)
        pdu_entries.append(pdu_entry(version, class_name, entry, classes))
    pdu_entries.sort(key=lambda item: (item["pdu_type"], item["protocol_family"], item["class_name"]))
    return {
        "schema_version": version,
        "source": str(xml_path.relative_to(ROOT)),
        "class_count": len(class_entries),
        "pdu_count": len(pdu_entries),
        "classes": class_entries,
        "pdus": pdu_entries,
    }


def outputs(dis6: Path, dis7: Path) -> dict[Path, str]:
    ir6 = build_ir(dis6, 6)
    ir7 = build_ir(dis7, 7)
    return {
        ROOT / "generated" / "fastdis_ir_dis6.json": json.dumps(ir6, indent=2) + "\n",
        ROOT / "generated" / "fastdis_ir_dis7.json": json.dumps(ir7, indent=2) + "\n",
    }


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dis6", type=Path, default=DEFAULT_DIS6)
    parser.add_argument("--dis7", type=Path, default=DEFAULT_DIS7)
    parser.add_argument("--check", action="store_true", help="Verify generated IR outputs are up to date instead of writing them.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    expected_outputs = outputs(args.dis6, args.dis7)
    if args.check:
        stale: list[Path] = []
        missing: list[Path] = []
        for path, content in expected_outputs.items():
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
        total_pdus = sum(payload["pdu_count"] for payload in (build_ir(args.dis6, 6), build_ir(args.dis7, 7)))
        print(f"generated IR outputs are up to date for {total_pdus} PDU entries")
        return 0

    for path, content in expected_outputs.items():
        write(path, content)
    total_pdus = len(catalog_from_xml(args.dis6, 6)) + len(catalog_from_xml(args.dis7, 7))
    print(f"generated normalized DIS IR for {total_pdus} PDU entries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
