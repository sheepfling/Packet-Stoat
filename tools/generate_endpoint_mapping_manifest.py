#!/usr/bin/env python3
"""Generate endpoint behavior coverage for every known DIS PDU."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from generate_pdu_catalog import DEFAULT_DIS6, DEFAULT_DIS7, ROOT, PduRecord, catalog_from_xml


STATE_UPDATE_TYPES = {1, 11, 12, 67}
EVENT_TYPES = {2, 3, 4, 49, 50, 66, 68, 69}
COMMUNICATION_TYPES = {23, 24, 25, 26, 27, 28, 29, 30, 31, 32}
SIM_CONTROL_TYPES = set(range(13, 23)) | set(range(51, 66))


def support_level(record: PduRecord) -> str:
    if record.class_name == "EntityStatePdu":
        return "production_supported"
    if record.pdu_type in STATE_UPDATE_TYPES:
        return "endpoint_mapped"
    if record.pdu_type in EVENT_TYPES or record.pdu_type in COMMUNICATION_TYPES or record.pdu_type in SIM_CONTROL_TYPES:
        return "cataloged_generic_endpoint"
    return "cataloged_safe_ingest"


def python_behavior(record: PduRecord) -> dict[str, str]:
    if record.class_name == "EntityStatePdu":
        return {"behavior": "state_update", "api": "fastdis.native entity transform snapshot"}
    if record.pdu_type in STATE_UPDATE_TYPES:
        return {"behavior": "typed_event_planned", "api": f"fastdis.events.{record.class_name[:-3]}Event"}
    return {"behavior": "generic_field_event", "api": "fastdis.visit_fields / fastdis generic PDU observation"}


def unreal_behavior(record: PduRecord) -> dict[str, str]:
    if record.class_name == "EntityStatePdu":
        return {"behavior": "engine_actor_mapping", "api": "FastDIS snapshot actor update"}
    if record.pdu_type in STATE_UPDATE_TYPES:
        return {"behavior": "state_update_planned", "api": "OnFastDisEntityLifecycle"}
    if record.pdu_type in EVENT_TYPES:
        return {"behavior": "blueprint_event_planned", "api": f"OnFastDis{record.class_name[:-3]}"}
    return {"behavior": "generic_raw_event", "api": "OnFastDisPduReceived"}


def godot_behavior(record: PduRecord) -> dict[str, str]:
    if record.class_name == "EntityStatePdu":
        return {"behavior": "engine_node_mapping", "api": "FastDisWorld snapshot Node3D update"}
    if record.pdu_type in STATE_UPDATE_TYPES:
        return {"behavior": "state_update_planned", "api": "entity_lifecycle_received"}
    if record.pdu_type in EVENT_TYPES:
        return {"behavior": "signal_planned", "api": f"{record.class_name[:-3].lower()}_received"}
    return {"behavior": "generic_raw_event", "api": "pdu_received"}


def lattice_behavior(record: PduRecord) -> dict[str, str]:
    if record.class_name == "EntityStatePdu":
        return {"behavior": "lattice_entity_mapping", "api": "Lattice-shaped Entity"}
    if record.pdu_type in STATE_UPDATE_TYPES:
        return {"behavior": "lattice_entity_lifecycle_planned", "api": "Entity update/tombstone/expiry"}
    if record.pdu_type in EVENT_TYPES:
        return {"behavior": "simulation_event", "api": "SimulationEvent"}
    if record.pdu_type in COMMUNICATION_TYPES:
        return {"behavior": "communication_event", "api": "CommunicationEvent"}
    if record.pdu_type in SIM_CONTROL_TYPES:
        return {"behavior": "simulation_control_event", "api": "SimulationControlEvent"}
    return {"behavior": "simulation_pdu_observation", "api": "SimulationPduObservation"}


def record_mapping(record: PduRecord) -> dict[str, object]:
    return {
        "protocol_version": record.protocol_version,
        "pdu_type": record.pdu_type,
        "name": record.name,
        "class_name": record.class_name,
        "family": record.family_name,
        "support_level": support_level(record),
        "python": python_behavior(record),
        "unreal": unreal_behavior(record),
        "godot": godot_behavior(record),
        "lattice_lab": lattice_behavior(record),
        "fuzz_shallow": True,
        "generic_event_required": True,
    }


def build_payload(records: list[PduRecord]) -> dict[str, object]:
    rows = [record_mapping(record) for record in records]
    missing = [
        row for row in rows
        if any(row[endpoint]["behavior"] == "none" for endpoint in ("python", "unreal", "godot", "lattice_lab"))
    ]
    return {
        "version": "0.17.0-alpha7",
        "policy": {
            "minimum_endpoint_behavior": "generic_raw_event",
            "known_pdu_rule": "No known DIS6/DIS7 PDU may be invisible to Python, Unreal, Godot, or Lattice Lab.",
            "semantic_note": "Generic endpoint behavior is not full semantic parsing.",
        },
        "summary": {
            "records": len(rows),
            "missing_endpoint_behavior": len(missing),
            "production_supported": sum(1 for row in rows if row["support_level"] == "production_supported"),
            "endpoint_mapped_or_better": sum(1 for row in rows if row["support_level"] in {"production_supported", "endpoint_mapped"}),
        },
        "records": rows,
    }


def render_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Endpoint Coverage",
        "",
        "This generated report defines product endpoint behavior for every known DIS 6/7 PDU.",
        "",
        "Policy:",
        "",
        "- no known PDU may be invisible",
        "- generic behavior is acceptable for early coverage",
        "- Entity State remains the production transform path",
        "- specialized events are added by support level over time",
        "",
        f"- records: `{payload['summary']['records']}`",
        f"- missing endpoint behavior: `{payload['summary']['missing_endpoint_behavior']}`",
        "",
        "| DIS | PDU | Class | Support | Python | Unreal | Godot | Lattice Lab |",
        "|---:|---:|---|---|---|---|---|---|",
    ]
    for row in payload["records"]:
        lines.append(
            f"| {row['protocol_version']} | {row['pdu_type']} | `{row['class_name']}` | "
            f"{row['support_level']} | {row['python']['behavior']} | {row['unreal']['behavior']} | "
            f"{row['godot']['behavior']} | {row['lattice_lab']['behavior']} |"
        )
    lines.append("")
    return "\n".join(lines)


def outputs(dis6: Path, dis7: Path) -> dict[Path, str]:
    records = catalog_from_xml(dis6, 6) + catalog_from_xml(dis7, 7)
    payload = build_payload(records)
    return {
        ROOT / "generated" / "endpoint_mapping_manifest.json": json.dumps(payload, indent=2) + "\n",
        ROOT / "docs" / "ENDPOINT_COVERAGE.md": render_markdown(payload),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dis6", type=Path, default=DEFAULT_DIS6)
    parser.add_argument("--dis7", type=Path, default=DEFAULT_DIS7)
    parser.add_argument("--check", action="store_true", help="Verify generated outputs are fresh.")
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
        print("endpoint mapping manifest is up to date")
        return 0

    for path, content in expected.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    print("generated endpoint mapping manifest")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
