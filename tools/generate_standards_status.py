#!/usr/bin/env python3
"""Generate FastDIS standards/update-readiness manifests and docs."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "standards" / "registry.yaml"
PDU_COVERAGE_PATH = ROOT / "generated" / "pdu_coverage_manifest.json"


ENUM_FAMILIES: tuple[dict[str, object], ...] = (
    {
        "id": "pdu_type",
        "display_name": "PDU Type",
        "source": "OpenDIS PduType/PduTypeDIS7 enum backbone plus FastDIS patches",
        "coverage_status": "generated_backbone_complete",
        "known_update_source": "IEEE 1278.1 family and OpenDIS references",
    },
    {
        "id": "protocol_family",
        "display_name": "Protocol Family",
        "source": "OpenDIS XML schema/catalog references",
        "coverage_status": "tracked",
        "known_update_source": "IEEE 1278.1 family",
    },
    {
        "id": "force_id",
        "display_name": "Force ID",
        "source": "DIS Entity State field semantics",
        "coverage_status": "tracked_core_values",
        "known_update_source": "SISO-REF-010",
    },
    {
        "id": "dead_reckoning_algorithm",
        "display_name": "Dead Reckoning Algorithm",
        "source": "DIS Entity State field semantics",
        "coverage_status": "tracked_0_to_9",
        "known_update_source": "SISO-REF-010",
    },
    {
        "id": "entity_type",
        "display_name": "Entity Type kind/domain/country/category/subcategory/specific/extra",
        "source": "DIS Entity Type records",
        "coverage_status": "numeric_preserve_only",
        "known_update_source": "SISO-REF-010 living data files",
    },
    {
        "id": "emitter_system",
        "display_name": "Emitter / sensor / EW systems",
        "source": "DIS emissions and radio families",
        "coverage_status": "numeric_preserve_only",
        "known_update_source": "SISO-REF-010 living data files",
    },
    {
        "id": "munition_descriptor",
        "display_name": "Munition descriptor enumerations",
        "source": "Warfare PDU records",
        "coverage_status": "numeric_preserve_only",
        "known_update_source": "SISO-REF-010 living data files",
    },
    {
        "id": "simulation_management_reason_action",
        "display_name": "Simulation management reason/action/status values",
        "source": "Simulation Management PDUs",
        "coverage_status": "numeric_preserve_only",
        "known_update_source": "SISO-REF-010 living data files",
    },
    {
        "id": "attribute_record_type",
        "display_name": "Attribute record type",
        "source": "DIS 7 Attribute PDU",
        "coverage_status": "schema_gap_tracked",
        "known_update_source": "SISO-REF-010 and DIS 7 references",
    },
)


def load_registry(path: Path = REGISTRY_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_pdu_coverage(path: Path = PDU_COVERAGE_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def enum_manifest(registry: dict[str, Any]) -> dict[str, Any]:
    pinned = next((row for row in registry["standards"] if row["id"] == "siso-ref-010-v32"), None)
    rows = [
        {
            **family,
            "pinned_reference": None if pinned is None else pinned["id"],
            "future_update_behavior": "preserve_unknown_numeric_values_and_report_unknown_label",
        }
        for family in ENUM_FAMILIES
    ]
    counts = Counter(str(row["coverage_status"]) for row in rows)
    return {
        "schema": "fastdis.enum_coverage_manifest.v1",
        "generated_from": [str(REGISTRY_PATH.relative_to(ROOT))],
        "summary": {
            "enum_family_rows": len(rows),
            "pinned_siso_ref_010": None if pinned is None else pinned["id"],
            "coverage_status_counts": dict(sorted(counts.items())),
            "full_siso_ref_010_imported": False,
        },
        "rows": rows,
    }


def standards_manifest(registry: dict[str, Any], pdu_coverage: dict[str, Any], enum_coverage: dict[str, Any]) -> dict[str, Any]:
    standards = registry["standards"]
    by_type = Counter(str(row["source_type"]) for row in standards)
    pdu_summary = pdu_coverage["summary"]
    return {
        "schema": "fastdis.standards_status.v1",
        "generated_from": [
            str(REGISTRY_PATH.relative_to(ROOT)),
            str(PDU_COVERAGE_PATH.relative_to(ROOT)),
            "tools/generate_standards_status.py",
        ],
        "overall_status": "update_ready",
        "registry_updated": registry.get("updated"),
        "source_type_counts": dict(sorted(by_type.items())),
        "protocol_layouts": {
            "dis6": {
                "standard_id": "ieee-1278.1a-1998",
                "pdu_rows": pdu_summary["standard_dis6_rows"],
                "expected_rows": 68,
                "safe_ingest_rows": sum(1 for row in pdu_coverage["rows"] if row["standard_version"] == 6 and row["safe_ingest"]),
            },
            "dis7": {
                "standard_id": "ieee-1278.1-2012",
                "pdu_rows": pdu_summary["standard_dis7_rows"],
                "expected_rows": 73,
                "safe_ingest_rows": sum(1 for row in pdu_coverage["rows"] if row["standard_version"] == 7 and row["safe_ingest"]),
            },
            "p1278_1_next": {
                "standard_id": "ieee-p1278.1-next",
                "status": "watch_only",
            },
        },
        "enumerations": enum_coverage["summary"],
        "companion_standards": [
            row for row in standards if row["source_type"] == "companion_standard"
        ],
        "watch_items": [
            {
                "id": row["id"],
                "display_name": row["display_name"],
                "source_type": row["source_type"],
                "status": row["status"],
            }
            for row in standards
            if "watch" in str(row["source_type"]) or "watch" in str(row["status"])
        ],
        "forward_compatibility_policy": registry["update_policy"],
        "known_gaps": pdu_coverage["catalog_gap_rows"],
    }


def render_markdown(manifest: dict[str, Any], registry: dict[str, Any]) -> str:
    lines = [
        "# Standards Status",
        "",
        "This document is generated by `tools/generate_standards_status.py`.",
        "",
        f"- overall_status: `{manifest['overall_status']}`",
        f"- registry_updated: `{manifest['registry_updated']}`",
        "",
        "## Protocol Layouts",
        "",
    ]
    for key, row in manifest["protocol_layouts"].items():
        lines.append(f"- `{key}`: `{row['standard_id']}`")
        if "pdu_rows" in row:
            lines.append(f"  - PDU rows: `{row['pdu_rows']} / {row['expected_rows']}`")
            lines.append(f"  - Safe ingest rows: `{row['safe_ingest_rows']} / {row['expected_rows']}`")
        else:
            lines.append(f"  - status: `{row['status']}`")
    lines.extend(["", "## Enumerations", ""])
    enum_summary = manifest["enumerations"]
    lines.append(f"- Pinned SISO-REF-010 reference: `{enum_summary['pinned_siso_ref_010']}`")
    lines.append(f"- Enum family rows tracked: `{enum_summary['enum_family_rows']}`")
    lines.append(f"- Full SISO-REF-010 import: `{enum_summary['full_siso_ref_010_imported']}`")
    lines.extend(["", "## Watch Items", ""])
    for row in manifest["watch_items"]:
        lines.append(f"- `{row['id']}` ({row['source_type']}): {row['display_name']} - `{row['status']}`")
    lines.extend(["", "## Forward Compatibility Policy", ""])
    for key, value in manifest["forward_compatibility_policy"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Known PDU Schema/Catalog Gaps", ""])
    if not manifest["known_gaps"]:
        lines.append("none")
    else:
        lines.extend(["| Version | PDU | Name | Status |", "| --- | ---: | --- | --- |"])
        for row in manifest["known_gaps"]:
            lines.append(f"| DIS {row['version']} | {row['pdu_type']} | {row['standard_name']} | `{row['schema_status']}` |")
    lines.extend(["", "## Registry Entries", ""])
    for row in registry["standards"]:
        lines.append(f"- `{row['id']}`: {row['display_name']} (`{row['source_type']}`, `{row['status']}`)")
    return "\n".join(lines) + "\n"


def outputs() -> dict[Path, str]:
    registry = load_registry()
    pdu_coverage = load_pdu_coverage()
    enum_coverage = enum_manifest(registry)
    manifest = standards_manifest(registry, pdu_coverage, enum_coverage)
    return {
        ROOT / "generated" / "enum_coverage_manifest.json": json.dumps(enum_coverage, indent=2) + "\n",
        ROOT / "generated" / "standards_status_manifest.json": json.dumps(manifest, indent=2) + "\n",
        ROOT / "docs" / "STANDARDS_STATUS.md": render_markdown(manifest, registry),
    }


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    rendered = outputs()
    if args.check:
        stale = [path for path, content in rendered.items() if not path.exists() or path.read_text(encoding="utf-8") != content]
        if stale:
            print("stale generated standards artifacts:", file=sys.stderr)
            for path in stale:
                print(f"  {path.relative_to(ROOT)}", file=sys.stderr)
            return 1
        return 0
    for path, content in rendered.items():
        write(path, content)
    manifest = json.loads(rendered[ROOT / "generated" / "standards_status_manifest.json"])
    print(f"generated standards status={manifest['overall_status']} enum_families={manifest['enumerations']['enum_family_rows']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
