#!/usr/bin/env python3
"""Generate standard-backed DIS PDU coverage manifests.

This generator deliberately separates the standard PDU enum backbone from the
checked-in XML schema inputs. The XML catalogs are useful generation inputs, but
they are not complete enough to be the source of truth for standard presence.
"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import sys
from typing import Any

from generate_pdu_catalog import (
    DEFAULT_DIS6,
    DEFAULT_DIS7,
    FAMILY_NAMES,
    PduRecord,
    catalog_from_xml,
    load_classes,
)


ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class StandardPdu:
    pdu_type: int
    dis6_name: str
    dis7_name: str
    protocol_family: int
    dis6_class_name: str
    dis7_class_name: str


STANDARD_PDUS: tuple[StandardPdu, ...] = (
    StandardPdu(0, "Other", "Other", 0, "OtherPdu", "OtherPdu"),
    StandardPdu(1, "Entity State", "Entity State", 1, "EntityStatePdu", "EntityStatePdu"),
    StandardPdu(2, "Fire", "Fire", 2, "FirePdu", "FirePdu"),
    StandardPdu(3, "Detonation", "Detonation", 2, "DetonationPdu", "DetonationPdu"),
    StandardPdu(4, "Collision", "Collision", 1, "CollisionPdu", "CollisionPdu"),
    StandardPdu(5, "Service Request", "Service Request", 3, "ServiceRequestPdu", "ServiceRequestPdu"),
    StandardPdu(6, "Resupply Offer", "Resupply Offer", 3, "ResupplyOfferPdu", "ResupplyOfferPdu"),
    StandardPdu(7, "Resupply Received", "Resupply Received", 3, "ResupplyReceivedPdu", "ResupplyReceivedPdu"),
    StandardPdu(8, "Resupply Cancel", "Resupply Cancel", 3, "ResupplyCancelPdu", "ResupplyCancelPdu"),
    StandardPdu(9, "Repair Complete", "Repair Complete", 3, "RepairCompletePdu", "RepairCompletePdu"),
    StandardPdu(10, "Repair Response", "Repair Response", 3, "RepairResponsePdu", "RepairResponsePdu"),
    StandardPdu(11, "Create Entity", "Create Entity", 5, "CreateEntityPdu", "CreateEntityPdu"),
    StandardPdu(12, "Remove Entity", "Remove Entity", 5, "RemoveEntityPdu", "RemoveEntityPdu"),
    StandardPdu(13, "Start/Resume", "Start/Resume", 5, "StartResumePdu", "StartResumePdu"),
    StandardPdu(14, "Stop/Freeze", "Stop/Freeze", 5, "StopFreezePdu", "StopFreezePdu"),
    StandardPdu(15, "Acknowledge", "Acknowledge", 5, "AcknowledgePdu", "AcknowledgePdu"),
    StandardPdu(16, "Action Request", "Action Request", 5, "ActionRequestPdu", "ActionRequestPdu"),
    StandardPdu(17, "Action Response", "Action Response", 5, "ActionResponsePdu", "ActionResponsePdu"),
    StandardPdu(18, "Data Query", "Data Query", 5, "DataQueryPdu", "DataQueryPdu"),
    StandardPdu(19, "Set Data", "Set Data", 5, "SetDataPdu", "SetDataPdu"),
    StandardPdu(20, "Data", "Data", 5, "DataPdu", "DataPdu"),
    StandardPdu(21, "Event Report", "Event Report", 5, "EventReportPdu", "EventReportPdu"),
    StandardPdu(22, "Comment", "Comment", 5, "CommentPdu", "CommentPdu"),
    StandardPdu(23, "Electromagnetic Emission", "Electromagnetic Emission", 6, "ElectronicEmissionsPdu", "ElectronicEmissionsPdu"),
    StandardPdu(24, "Designator", "Designator", 6, "DesignatorPdu", "DesignatorPdu"),
    StandardPdu(25, "Transmitter", "Transmitter", 4, "TransmitterPdu", "TransmitterPdu"),
    StandardPdu(26, "Signal", "Signal", 4, "SignalPdu", "SignalPdu"),
    StandardPdu(27, "Receiver", "Receiver", 4, "ReceiverPdu", "ReceiverPdu"),
    StandardPdu(28, "IFF/ATC/NAVAIDS", "IFF", 6, "IffAtcNavAidsLayer1Pdu", "IffPdu"),
    StandardPdu(29, "Underwater Acoustic", "Underwater Acoustic", 6, "UaPdu", "UaPdu"),
    StandardPdu(30, "Supplemental Emission / Entity State", "Supplemental Emission / Entity State", 6, "SEESPdu", "SEESPdu"),
    StandardPdu(31, "Intercom Signal", "Intercom Signal", 4, "IntercomSignalPdu", "IntercomSignalPdu"),
    StandardPdu(32, "Intercom Control", "Intercom Control", 4, "IntercomControlPdu", "IntercomControlPdu"),
    StandardPdu(33, "Aggregate State", "Aggregate State", 7, "AggregateStatePdu", "AggregateStatePdu"),
    StandardPdu(34, "IsGroupOf", "IsGroupOf", 7, "IsGroupOfPdu", "IsGroupOfPdu"),
    StandardPdu(35, "Transfer Control", "Transfer Ownership", 7, "TransferControlRequestPdu", "TransferOwnershipPdu"),
    StandardPdu(36, "IsPartOf", "IsPartOf", 7, "IsPartOfPdu", "IsPartOfPdu"),
    StandardPdu(37, "Minefield State", "Minefield State", 8, "MinefieldStatePdu", "MinefieldStatePdu"),
    StandardPdu(38, "Minefield Query", "Minefield Query", 8, "MinefieldQueryPdu", "MinefieldQueryPdu"),
    StandardPdu(39, "Minefield Data", "Minefield Data", 8, "MinefieldDataPdu", "MinefieldDataPdu"),
    StandardPdu(40, "Minefield Response NACK", "Minefield Response NACK", 8, "MinefieldResponseNackPdu", "MinefieldResponseNackPdu"),
    StandardPdu(41, "Environmental Process", "Environmental Process", 9, "EnvironmentalProcessPdu", "EnvironmentalProcessPdu"),
    StandardPdu(42, "Gridded Data", "Gridded Data", 9, "GriddedDataPdu", "GriddedDataPdu"),
    StandardPdu(43, "Point Object State", "Point Object State", 9, "PointObjectStatePdu", "PointObjectStatePdu"),
    StandardPdu(44, "Linear Object State", "Linear Object State", 9, "LinearObjectStatePdu", "LinearObjectStatePdu"),
    StandardPdu(45, "Areal Object State", "Areal Object State", 9, "ArealObjectStatePdu", "ArealObjectStatePdu"),
    StandardPdu(46, "TSPI", "TSPI", 11, "TSPIPdu", "TSPIPdu"),
    StandardPdu(47, "Appearance", "Appearance", 11, "AppearancePdu", "AppearancePdu"),
    StandardPdu(48, "Articulated Parts", "Articulated Parts", 11, "ArticulatedPartsPdu", "ArticulatedPartsPdu"),
    StandardPdu(49, "LE Fire", "LE Fire", 11, "LEFirePdu", "LEFirePdu"),
    StandardPdu(50, "LE Detonation", "LE Detonation", 11, "LEDetonationPdu", "LEDetonationPdu"),
    StandardPdu(51, "Create Entity-R", "Create Entity-R", 10, "CreateEntityReliablePdu", "CreateEntityReliablePdu"),
    StandardPdu(52, "Remove Entity-R", "Remove Entity-R", 10, "RemoveEntityReliablePdu", "RemoveEntityReliablePdu"),
    StandardPdu(53, "Start/Resume-R", "Start/Resume-R", 10, "StartResumeReliablePdu", "StartResumeReliablePdu"),
    StandardPdu(54, "Stop/Freeze-R", "Stop/Freeze-R", 10, "StopFreezeReliablePdu", "StopFreezeReliablePdu"),
    StandardPdu(55, "Acknowledge-R", "Acknowledge-R", 10, "AcknowledgeReliablePdu", "AcknowledgeReliablePdu"),
    StandardPdu(56, "Action Request-R", "Action Request-R", 10, "ActionRequestReliablePdu", "ActionRequestReliablePdu"),
    StandardPdu(57, "Action Response-R", "Action Response-R", 10, "ActionResponseReliablePdu", "ActionResponseReliablePdu"),
    StandardPdu(58, "Data Query-R", "Data Query-R", 10, "DataQueryReliablePdu", "DataQueryReliablePdu"),
    StandardPdu(59, "Set Data-R", "Set Data-R", 10, "SetDataReliablePdu", "SetDataReliablePdu"),
    StandardPdu(60, "Data-R", "Data-R", 10, "DataReliablePdu", "DataReliablePdu"),
    StandardPdu(61, "Event Report-R", "Event Report-R", 10, "EventReportReliablePdu", "EventReportReliablePdu"),
    StandardPdu(62, "Comment-R", "Comment-R", 10, "CommentReliablePdu", "CommentReliablePdu"),
    StandardPdu(63, "Record-R", "Record-R", 10, "RecordReliablePdu", "RecordReliablePdu"),
    StandardPdu(64, "Set Record-R", "Set Record-R", 10, "SetRecordReliablePdu", "SetRecordReliablePdu"),
    StandardPdu(65, "Record Query-R", "Record Query-R", 10, "RecordQueryReliablePdu", "RecordQueryReliablePdu"),
    StandardPdu(66, "Collision-Elastic", "Collision-Elastic", 1, "CollisionElasticPdu", "CollisionElasticPdu"),
    StandardPdu(67, "Entity State Update", "Entity State Update", 1, "EntityStateUpdatePdu", "EntityStateUpdatePdu"),
    StandardPdu(68, "", "Directed Energy Fire", 2, "", "DirectedEnergyFirePdu"),
    StandardPdu(69, "", "Entity Damage Status", 2, "", "EntityDamageStatusPdu"),
    StandardPdu(70, "", "Information Operations Action", 13, "", "InformationOperationsActionPdu"),
    StandardPdu(71, "", "Information Operations Report", 13, "", "InformationOperationsReportPdu"),
    StandardPdu(72, "", "Attribute", 1, "", "AttributePdu"),
)

ALIAS_PDUS = {
    28: ("IFF/ATC/NAVAIDS", "IFF"),
    35: ("Transfer Control", "Transfer Ownership"),
}


def standard_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in STANDARD_PDUS:
        versions = []
        if item.pdu_type <= 67:
            versions.append((6, item.dis6_name, item.dis6_class_name))
        versions.append((7, item.dis7_name, item.dis7_class_name))
        for version, name, class_name in versions:
            rows.append(
                {
                    "standard_version": version,
                    "pdu_type": item.pdu_type,
                    "standard_name": name,
                    "standard_class_name": class_name,
                    "protocol_family": item.protocol_family,
                    "family_name": FAMILY_NAMES.get(item.protocol_family, f"Protocol Family {item.protocol_family}"),
                    "expected": True,
                    "alias": item.pdu_type in ALIAS_PDUS,
                    "source": "OpenDIS PduType/PduTypeDIS7 enum backbone",
                }
            )
    return sorted(rows, key=lambda row: (row["standard_version"], row["pdu_type"]))


def _record_payload(record: PduRecord | None) -> dict[str, Any] | None:
    if record is None:
        return None
    return asdict(record)


def _xml_class_index(path: Path) -> set[str]:
    return set(load_classes(path))


def _schema_status(
    *,
    version: int,
    class_name: str,
    catalog_record: PduRecord | None,
    xml_classes: set[str],
) -> str:
    if catalog_record is not None:
        return "PRESENT"
    if class_name in xml_classes:
        return "PRESENT_BUT_MISSING_PDU_TYPE_INITIAL_VALUE"
    return "SCHEMA_GAP"


def _support_level(catalog_record: PduRecord | None, schema_status: str) -> str:
    if catalog_record and catalog_record.body_decoder:
        return "TYPED_PREFIX"
    if catalog_record is not None:
        return "FIELD_VISITOR"
    if schema_status == "PRESENT_BUT_MISSING_PDU_TYPE_INITIAL_VALUE":
        return "SCHEMA_PATCH_REQUIRED"
    return "GENERIC_EVENT"


def _translation_status(version: int, pdu_type: int) -> str:
    if pdu_type in ALIAS_PDUS:
        return "RENAMED"
    if version == 7 and pdu_type >= 68:
        return "DROPPED_PDU_TO_DIS6"
    return "EXACT_OR_DEFAULTED"


def coverage_rows(dis6: Path, dis7: Path) -> list[dict[str, Any]]:
    catalog6 = {(row.protocol_version, row.pdu_type): row for row in catalog_from_xml(dis6, 6)}
    catalog7 = {(row.protocol_version, row.pdu_type): row for row in catalog_from_xml(dis7, 7)}
    catalogs = {**catalog6, **catalog7}
    xml_classes = {
        6: _xml_class_index(dis6),
        7: _xml_class_index(dis7),
    }

    rows: list[dict[str, Any]] = []
    for row in standard_rows():
        version = int(row["standard_version"])
        pdu_type = int(row["pdu_type"])
        class_name = str(row["standard_class_name"])
        catalog_record = catalogs.get((version, pdu_type))
        schema_status = _schema_status(
            version=version,
            class_name=class_name,
            catalog_record=catalog_record,
            xml_classes=xml_classes[version],
        )
        schema_present = schema_status in {"PRESENT", "PRESENT_BUT_MISSING_PDU_TYPE_INITIAL_VALUE"}
        generated_catalog_present = catalog_record is not None
        typed_parser = bool(catalog_record and catalog_record.body_decoder)
        field_visitor = generated_catalog_present
        support_level = _support_level(catalog_record, schema_status)
        endpoint_behavior = "SPECIALIZED_ENTITY_STATE" if typed_parser else "GENERIC_PDU_EVENT"
        rows.append(
            {
                **row,
                "schema_present": schema_present,
                "schema_status": schema_status,
                "schema_class": class_name if schema_present else None,
                "generated_catalog_present": generated_catalog_present,
                "generated_catalog_record": _record_payload(catalog_record),
                "catalog_status": "CATALOGED" if generated_catalog_present else "ENUM_ONLY",
                "safe_ingest": True,
                "header_validated": True,
                "length_checked": True,
                "shallow_fuzz_target": True,
                "generic_endpoint": True,
                "field_visitor": field_visitor,
                "typed_parser": typed_parser,
                "full_parser": typed_parser,
                "serializer": field_visitor,
                "production_supported": typed_parser,
                "support_level": support_level,
                "endpoint_behavior": {
                    "python": endpoint_behavior,
                    "c": endpoint_behavior,
                    "cpp": endpoint_behavior,
                    "unreal": "ENTITY_STATE_ADAPTER" if typed_parser else "OnFastDisPduReceived",
                    "godot": "entity_state_signal" if typed_parser else "pdu_received",
                    "unity": "EntityStateEvent" if typed_parser else "PduReceived",
                    "lattice_lab": "Entity" if typed_parser else "SimulationPduObservation",
                },
                "translation_status": _translation_status(version, pdu_type),
            }
        )
    return rows


def build_manifests(dis6: Path, dis7: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    backbone_rows = standard_rows()
    rows = coverage_rows(dis6, dis7)
    standard_counts = Counter(row["standard_version"] for row in backbone_rows)
    schema_counts = Counter(row["schema_status"] for row in rows)
    support_counts = Counter(row["support_level"] for row in rows)
    missing = [row for row in rows if not row["generated_catalog_present"]]
    backbone = {
        "schema": "fastdis.pdu_standard_backbone.v1",
        "source": "OpenDIS PduType/PduTypeDIS7 enum backbone encoded as FastDIS owned generation data",
        "source_metadata": {
            "standards_registry": "standards/registry.yaml",
            "protocol_layouts": ["ieee-1278.1a-1998", "ieee-1278.1-2012"],
            "implementation_reference": "opendis-reference-sources",
            "patch_policy": "FastDIS patch overlays keep standard enum rows even when XML schema inputs are incomplete.",
        },
        "summary": {
            "dis6_rows": standard_counts[6],
            "dis7_rows": standard_counts[7],
            "total_rows": len(backbone_rows),
            "expected_dis6_rows": 68,
            "expected_dis7_rows": 73,
            "expected_total_rows": 141,
            "aliases": [
                {"pdu_type": pdu_type, "dis6_name": names[0], "dis7_name": names[1]}
                for pdu_type, names in sorted(ALIAS_PDUS.items())
            ],
        },
        "rows": backbone_rows,
    }
    coverage = {
        "schema": "fastdis.pdu_coverage_manifest.v1",
        "generated_from": [
            str(dis6.relative_to(ROOT)),
            str(dis7.relative_to(ROOT)),
            "tools/generate_pdu_coverage.py standard backbone",
        ],
        "source_metadata": {
            "standards_registry": "standards/registry.yaml",
            "protocol_layouts": ["ieee-1278.1a-1998", "ieee-1278.1-2012"],
            "enumerations_watch": "siso-ref-010-latest",
            "companion_standard_watch": "siso-std-023-2024-cdis",
        },
        "coverage_model": {
            "level_0_standard_backbone": "Every expected DIS 6 and DIS 7 PDU enum value exists in the manifest.",
            "level_1_schema_ir": "Every row is connected to XML/IR schema or explicitly marked schema gap.",
            "level_2_safe_ingest": "Every standard PDU can be header parsed, length checked, counted, and safely skipped.",
            "level_3_generic_endpoint": "Every standard PDU has a generic endpoint behavior.",
            "level_4_field_visitor": "Schema-backed generated catalog rows have generated field visitors.",
            "level_5_typed_parser": "High-value rows have typed parsers; currently Entity State only.",
            "level_6_full_semantic": "Full semantic support remains opt-in by typed parser waves.",
        },
        "summary": {
            "standard_dis6_rows": backbone["summary"]["dis6_rows"],
            "standard_dis7_rows": backbone["summary"]["dis7_rows"],
            "standard_total_rows": len(rows),
            "xml_catalog_dis6_rows": sum(1 for row in rows if row["standard_version"] == 6 and row["generated_catalog_present"]),
            "xml_catalog_dis7_rows": sum(1 for row in rows if row["standard_version"] == 7 and row["generated_catalog_present"]),
            "xml_catalog_total_rows": sum(1 for row in rows if row["generated_catalog_present"]),
            "catalog_gap_rows": len(missing),
            "schema_status_counts": dict(sorted(schema_counts.items())),
            "support_level_counts": dict(sorted(support_counts.items())),
            "safe_ingest_rows": sum(1 for row in rows if row["safe_ingest"]),
            "generic_endpoint_rows": sum(1 for row in rows if row["generic_endpoint"]),
            "field_visitor_rows": sum(1 for row in rows if row["field_visitor"]),
            "typed_parser_rows": sum(1 for row in rows if row["typed_parser"]),
        },
        "catalog_gap_rows": [
            {
                "version": row["standard_version"],
                "pdu_type": row["pdu_type"],
                "standard_name": row["standard_name"],
                "schema_status": row["schema_status"],
                "standard_class_name": row["standard_class_name"],
                "translation_status": row["translation_status"],
            }
            for row in missing
        ],
        "rows": rows,
    }
    return backbone, coverage


def markdown_table(rows: list[dict[str, Any]]) -> str:
    lines = [
        "| Version | PDU | Standard name | Family | Schema status | Catalog | Support | Endpoint |",
        "| --- | ---: | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| DIS {row['standard_version']} | {row['pdu_type']} | {row['standard_name']} | "
            f"{row['family_name']} | `{row['schema_status']}` | "
            f"{'yes' if row['generated_catalog_present'] else 'no'} | `{row['support_level']}` | "
            f"`{row['endpoint_behavior']['python']}` |"
        )
    return "\n".join(lines)


def generate_backbone_markdown(backbone: dict[str, Any]) -> str:
    summary = backbone["summary"]
    lines = [
        "# PDU Standard Backbone",
        "",
        "This document is generated by `tools/generate_pdu_coverage.py`.",
        "",
        "The standard backbone is separate from the checked-in XML catalog. XML gaps do not remove standard PDU rows.",
        "",
        "## Summary",
        "",
        f"- DIS 6 rows: `{summary['dis6_rows']} / {summary['expected_dis6_rows']}`",
        f"- DIS 7 rows: `{summary['dis7_rows']} / {summary['expected_dis7_rows']}`",
        f"- Total versioned rows: `{summary['total_rows']} / {summary['expected_total_rows']}`",
        "",
        "## Aliases",
        "",
        "| PDU | DIS 6 name | DIS 7 name |",
        "| ---: | --- | --- |",
    ]
    for alias in summary["aliases"]:
        lines.append(f"| {alias['pdu_type']} | {alias['dis6_name']} | {alias['dis7_name']} |")
    lines.extend(
        [
            "",
            "## Rows",
            "",
            "| Version | PDU | Name | Family | Class |",
            "| --- | ---: | --- | --- | --- |",
        ]
    )
    for row in backbone["rows"]:
        lines.append(
            f"| DIS {row['standard_version']} | {row['pdu_type']} | {row['standard_name']} | "
            f"{row['family_name']} | `{row['standard_class_name']}` |"
        )
    return "\n".join(lines) + "\n"


def generate_coverage_markdown(coverage: dict[str, Any]) -> str:
    summary = coverage["summary"]
    lines = [
        "# PDU Coverage",
        "",
        "This document is generated by `tools/generate_pdu_coverage.py`.",
        "",
        "FastDIS tracks PDU coverage in layers. Standard presence, XML schema presence, safe ingest, generic endpoint behavior, field visitors, and typed semantic parsing are separate claims.",
        "",
        "## Summary",
        "",
        f"- Standard backbone: `DIS6 {summary['standard_dis6_rows']} / 68`, `DIS7 {summary['standard_dis7_rows']} / 73`, total `{summary['standard_total_rows']} / 141`",
        f"- XML-derived catalog rows: `DIS6 {summary['xml_catalog_dis6_rows']}`, `DIS7 {summary['xml_catalog_dis7_rows']}`, total `{summary['xml_catalog_total_rows']}`",
        f"- Catalog/schema gap rows: `{summary['catalog_gap_rows']}`",
        f"- Safe ingest rows: `{summary['safe_ingest_rows']} / 141`",
        f"- Generic endpoint rows: `{summary['generic_endpoint_rows']} / 141`",
        f"- Field visitor rows: `{summary['field_visitor_rows']} / 141`",
        f"- Typed parser rows: `{summary['typed_parser_rows']} / 141`",
        "",
        "## Schema Status Counts",
        "",
    ]
    for key, value in summary["schema_status_counts"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Support Level Counts", ""])
    for key, value in summary["support_level_counts"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "## Catalog Gaps",
            "",
            "| Version | PDU | Name | Schema status | Class | Translation |",
            "| --- | ---: | --- | --- | --- | --- |",
        ]
    )
    for row in coverage["catalog_gap_rows"]:
        lines.append(
            f"| DIS {row['version']} | {row['pdu_type']} | {row['standard_name']} | "
            f"`{row['schema_status']}` | `{row['standard_class_name']}` | `{row['translation_status']}` |"
        )
    lines.extend(["", "## Coverage Matrix", "", markdown_table(coverage["rows"])])
    return "\n".join(lines) + "\n"


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def outputs(dis6: Path, dis7: Path) -> dict[Path, str]:
    backbone, coverage = build_manifests(dis6, dis7)
    return {
        ROOT / "generated" / "pdu_standard_backbone.json": json.dumps(backbone, indent=2) + "\n",
        ROOT / "generated" / "pdu_coverage_manifest.json": json.dumps(coverage, indent=2) + "\n",
        ROOT / "docs" / "PDU_STANDARD_BACKBONE.md": generate_backbone_markdown(backbone),
        ROOT / "docs" / "PDU_COVERAGE.md": generate_coverage_markdown(coverage),
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
            print("stale generated PDU coverage artifacts:", file=sys.stderr)
            for path in stale:
                print(f"  {path.relative_to(ROOT)}", file=sys.stderr)
            return 1
        return 0

    for path, content in rendered.items():
        write(path, content)
    backbone, coverage = build_manifests(args.dis6, args.dis7)
    print(
        "generated PDU standard backbone "
        f"DIS6={backbone['summary']['dis6_rows']} DIS7={backbone['summary']['dis7_rows']} "
        f"coverage_rows={coverage['summary']['standard_total_rows']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
