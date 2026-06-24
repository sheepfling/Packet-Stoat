#!/usr/bin/env python3
"""Generate DIS 6 <-> DIS 7 translation rule metadata."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys
from typing import Any

from generate_pdu_catalog import DEFAULT_DIS6, DEFAULT_DIS7, PduRecord, catalog_from_xml


ROOT = Path(__file__).resolve().parents[1]

TRANSLATION_STATUSES = (
    "EXACT",
    "RENAMED",
    "DEFAULTED",
    "DROPPED_FIELD",
    "DROPPED_PDU",
    "PASSTHROUGH_RAW",
    "SYNTHETIC",
    "FAILED_STRICT",
)

POLICY_DESCRIPTIONS = {
    "strict": "Allow exact, renamed, and documented safe defaults. Refuse target-incompatible loss.",
    "tolerant": "Allow documented defaults and drops with structured diagnostics.",
    "preserve_raw": "Tolerant behavior plus retain original packet bytes in sidecar metadata.",
    "bridge": "Emit target DIS when possible and report every drop/failure for network bridge use.",
    "engine": "Normalize to canonical engine events; untranslatable PDUs become monitor events.",
    "lattice_lab": "Normalize to Lattice Lab entities/events/observations while preserving raw context.",
}

CATALOG_GAP_HINTS = {
    28: {
        "dis6_name": "IFF/ATC/NAVAIDS",
        "dis7_name": "IFF",
        "expected_status": "RENAMED",
        "note": "OpenDIS DIS7 enum commentary treats this as a DIS6/DIS7 name alias, but the checked-in DIS7 XML description does not catalog this PDU row.",
    },
}


def record_key(record: PduRecord) -> tuple[int, int]:
    return (record.pdu_type, record.protocol_family)


def record_payload(record: PduRecord) -> dict[str, Any]:
    return {
        "protocol_version": record.protocol_version,
        "pdu_type": record.pdu_type,
        "protocol_family": record.protocol_family,
        "class_name": record.class_name,
        "name": record.name,
        "family_name": record.family_name,
        "has_body_decoder": record.body_decoder,
    }


def field_rules(source_version: int, target_version: int, target: PduRecord | None) -> list[dict[str, Any]]:
    if target is None:
        return []
    if source_version == 6 and target_version == 7:
        return [
            {
                "field": "pduStatus",
                "source": "absent",
                "target": "present",
                "status": "DEFAULTED",
                "rule": "default_zero",
                "strict_behavior": "allowed_default_safe",
            }
        ]
    if source_version == 7 and target_version == 6:
        return [
            {
                "field": "pduStatus",
                "source": "present",
                "target": "absent",
                "status": "DROPPED_FIELD",
                "rule": "drop_for_dis6_header",
                "strict_behavior": "conditional_fail_if_nonzero_or_policy_requires_lossless",
            }
        ]
    return []


def common_policy_behaviors(source_version: int, target_version: int) -> dict[str, str]:
    if source_version == 7 and target_version == 6:
        return {
            "strict": "conditional: fail if pduStatus or later field rules require lossy target emission",
            "tolerant": "emit target DIS 6 packet and report dropped/defaulted fields",
            "preserve_raw": "emit target DIS 6 packet, report diagnostics, and preserve original DIS 7 bytes",
            "bridge": "emit target DIS 6 packet when field rules allow; otherwise route to explicit failure/drop report",
            "engine": "emit canonical engine event plus translation diagnostics",
            "lattice_lab": "emit canonical Lattice Lab event/entity plus raw sidecar when requested",
        }
    return {
        "strict": "emit target packet with exact, renamed, or default-safe fields only",
        "tolerant": "emit target packet and report any defaulted fields",
        "preserve_raw": "emit target packet and preserve original source bytes in sidecar metadata",
        "bridge": "emit target packet and include translation counters in bridge report",
        "engine": "emit canonical engine event plus translation diagnostics",
        "lattice_lab": "emit canonical Lattice Lab event/entity plus raw sidecar when requested",
    }


def dropped_policy_behaviors(target_version: int) -> dict[str, str]:
    return {
        "strict": "FAILED_STRICT",
        "tolerant": "GENERIC_EVENT",
        "preserve_raw": "GENERIC_EVENT_WITH_RAW_SIDECAR",
        "bridge": "DROP_WITH_STRUCTURED_REPORT",
        "engine": "PDU_MONITOR_EVENT",
        "lattice_lab": "SimulationPduObservation",
    }


def translation_row(source: PduRecord, target: PduRecord | None, target_version: int) -> dict[str, Any]:
    source_version = source.protocol_version
    rules = field_rules(source_version, target_version, target)
    if target is None:
        status = "DROPPED_PDU"
        statuses = ["DROPPED_PDU", "PASSTHROUGH_RAW", "FAILED_STRICT"]
        policy_behaviors = dropped_policy_behaviors(target_version)
        notes = [
            f"No DIS {target_version} catalog equivalent was generated for this source PDU key.",
            "No synthetic substitute is emitted unless a future explicit per-PDU policy opts in.",
        ]
        if source.pdu_type in CATALOG_GAP_HINTS:
            notes.append(CATALOG_GAP_HINTS[source.pdu_type]["note"])
    else:
        renamed = source.class_name != target.class_name or source.name != target.name
        status = "RENAMED" if renamed else "EXACT"
        statuses = [status, *(rule["status"] for rule in rules)]
        policy_behaviors = common_policy_behaviors(source_version, target_version)
        notes = []
        if renamed:
            notes.append("Source and target catalog names differ; numeric PDU identity is treated as equivalent.")

    row = {
        "id": f"dis{source_version}_to_dis{target_version}_type_{source.pdu_type}_family_{source.protocol_family}",
        "source_version": source_version,
        "target_version": target_version,
        "pdu_type": source.pdu_type,
        "protocol_family": source.protocol_family,
        "source": record_payload(source),
        "target_equivalent": record_payload(target) if target is not None else None,
        "translation_status": status,
        "translation_statuses": statuses,
        "field_rules": rules,
        "strict_behavior": policy_behaviors["strict"],
        "tolerant_behavior": policy_behaviors["tolerant"],
        "preserve_raw_behavior": policy_behaviors["preserve_raw"],
        "policy_behaviors": policy_behaviors,
        "engine_behavior": policy_behaviors["engine"],
        "lattice_lab_behavior": policy_behaviors["lattice_lab"],
        "bridge_behavior": policy_behaviors["bridge"],
        "source_support": {
            "cataloged": True,
            "header_validated": True,
            "generic_packet_view_parser": True,
            "generic_visitor": True,
            "byte_preserving_serializer": True,
            "typed_body_decoder": source.body_decoder,
        },
        "target_support": {
            "cataloged": target is not None,
            "typed_body_decoder": bool(target and target.body_decoder),
        },
        "loss_metadata": [
            {
                "status": rule["status"],
                "field": rule["field"],
                "rule": rule["rule"],
            }
            for rule in rules
        ],
        "notes": notes,
    }
    return row


def build_manifest(dis6: Path, dis7: Path) -> dict[str, Any]:
    records6 = catalog_from_xml(dis6, 6)
    records7 = catalog_from_xml(dis7, 7)
    by6 = {record_key(record): record for record in records6}
    by7 = {record_key(record): record for record in records7}
    rows = [translation_row(record, by7.get(record_key(record)), 7) for record in records6]
    rows.extend(translation_row(record, by6.get(record_key(record)), 6) for record in records7)

    status_counts = Counter()
    for row in rows:
        for status in row["translation_statuses"]:
            status_counts[status] += 1

    dis6_only = sorted(record.pdu_type for key, record in by6.items() if key not in by7)
    dis7_only = sorted(record.pdu_type for key, record in by7.items() if key not in by6)
    catalog_gap_alias_hints = [
        {"pdu_type": pdu_type, **hint}
        for pdu_type, hint in sorted(CATALOG_GAP_HINTS.items())
        if (pdu_type, 1) not in by7 or (pdu_type, 1) not in by6
    ]

    return {
        "schema": "fastdis.version_translation_manifest.v1",
        "generated_from": [
            str(dis6.relative_to(ROOT)),
            str(dis7.relative_to(ROOT)),
        ],
        "catalog_policy": "Rows are generated from the checked-in DIS XML PDU catalogs. Enum-only or upstream-missing PDU values are reported as catalog gaps instead of silently invented.",
        "translation_model": "DIS packet -> versioned parser -> canonical FastDIS IR -> target-version emitter",
        "status_enum": list(TRANSLATION_STATUSES),
        "policy_descriptions": POLICY_DESCRIPTIONS,
        "summary": {
            "dis6_catalog_records": len(records6),
            "dis7_catalog_records": len(records7),
            "translation_rows": len(rows),
            "status_counts": dict(sorted(status_counts.items())),
            "dis6_only_pdu_types": dis6_only,
            "dis7_only_pdu_types": dis7_only,
            "catalog_gap_alias_hints": len(catalog_gap_alias_hints),
        },
        "catalog_gap_alias_hints": catalog_gap_alias_hints,
        "rows": rows,
    }


def generate_version_translation_markdown(manifest: dict[str, Any]) -> str:
    summary = manifest["summary"]
    lines = [
        "# DIS Version Translation",
        "",
        "FastDIS cross-version translation is built around a canonical internal model:",
        "",
        "```text",
        "DIS 6 packet -> versioned parser -> canonical FastDIS IR -> DIS 7 emitter",
        "DIS 7 packet -> versioned parser -> canonical FastDIS IR -> DIS 6 emitter",
        "```",
        "",
        "The rule is explicit: every cataloged PDU gets a translation rule, not every rule is lossless, and no unsupported PDU is silently guessed.",
        "",
        "This document is generated from the checked-in DIS XML catalogs. The current XML inputs produce "
        f"{summary['dis6_catalog_records']} DIS 6 rows and {summary['dis7_catalog_records']} DIS 7 rows. "
        "If an OpenDIS enum value is not present in those XML catalogs, it is tracked as an upstream catalog gap rather than invented by hand.",
        "",
        "## Status Enum",
        "",
    ]
    for status in TRANSLATION_STATUSES:
        lines.append(f"- `{status}`")
    lines.extend(
        [
            "",
            "## Policies",
            "",
        ]
    )
    for name, description in POLICY_DESCRIPTIONS.items():
        lines.append(f"- `{name}`: {description}")
    lines.extend(
        [
            "",
            "## Summary",
            "",
            f"- DIS 6 catalog rows: `{summary['dis6_catalog_records']}`",
            f"- DIS 7 catalog rows: `{summary['dis7_catalog_records']}`",
            f"- Translation rows: `{summary['translation_rows']}`",
            f"- DIS 6-only catalog PDU types: `{summary['dis6_only_pdu_types']}`",
            f"- DIS 7-only catalog PDU types: `{summary['dis7_only_pdu_types']}`",
            "",
            "## Behavior",
            "",
            "- `strict` mode refuses target-incompatible loss and reports `FAILED_STRICT` for PDU-level drops.",
            "- `tolerant` mode emits target packets/events when a documented default/drop is allowed.",
            "- `preserve_raw` mode keeps the original bytes in sidecar metadata when target DIS cannot represent the source exactly.",
            "- Engine endpoints receive canonical events or explicit monitor events; known PDUs do not disappear.",
            "- Lattice Lab maps Entity State to entities and unsupported traffic to `SimulationPduObservation` style events.",
            "",
            "## Catalog Gaps",
            "",
        ]
    )
    hints = manifest["catalog_gap_alias_hints"]
    if not hints:
        lines.append("No alias catalog gaps were detected.")
    else:
        lines.append("| PDU | DIS 6 name | DIS 7 name | Expected status | Note |")
        lines.append("|---:|---|---|---|---|")
        for hint in hints:
            lines.append(
                f"| {hint['pdu_type']} | {hint['dis6_name']} | {hint['dis7_name']} | "
                f"`{hint['expected_status']}` | {hint['note']} |"
            )
    lines.append("")
    return "\n".join(lines)


def generate_matrix_markdown(manifest: dict[str, Any]) -> str:
    lines = [
        "# DIS 6 / DIS 7 Translation Matrix",
        "",
        "Generated from `generated/version_translation_manifest.json`.",
        "",
        "| Direction | PDU | Family | Source class | Target class | Status | Strict | Tolerant | Preserve raw |",
        "|---|---:|---:|---|---|---|---|---|---|",
    ]
    for row in manifest["rows"]:
        target = row["target_equivalent"]
        target_class = f"`{target['class_name']}`" if target else ""
        lines.append(
            f"| DIS {row['source_version']} -> DIS {row['target_version']} | "
            f"{row['pdu_type']} | {row['protocol_family']} | `{row['source']['class_name']}` | "
            f"{target_class} | `{row['translation_status']}` | {row['strict_behavior']} | "
            f"{row['tolerant_behavior']} | {row['preserve_raw_behavior']} |"
        )
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dis6", type=Path, default=DEFAULT_DIS6)
    parser.add_argument("--dis7", type=Path, default=DEFAULT_DIS7)
    parser.add_argument("--check", action="store_true", help="Verify outputs are current instead of writing them.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest = build_manifest(args.dis6, args.dis7)
    outputs = {
        ROOT / "generated" / "version_translation_manifest.json": json.dumps(manifest, indent=2) + "\n",
        ROOT / "docs" / "DIS_VERSION_TRANSLATION.md": generate_version_translation_markdown(manifest),
        ROOT / "docs" / "DIS6_DIS7_TRANSLATION_MATRIX.md": generate_matrix_markdown(manifest),
    }

    if args.check:
        missing: list[Path] = []
        stale: list[Path] = []
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
        print(f"generated version translation manifest is up to date for {manifest['summary']['translation_rows']} rows")
        return 0

    for path, content in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    print(f"generated {manifest['summary']['translation_rows']} DIS version translation rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
