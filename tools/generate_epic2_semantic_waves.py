#!/usr/bin/env python3
"""Generate the Epic 2 typed-semantic wave worklist from current 141-row manifests."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

from generate_pdu_catalog import DEFAULT_DIS6, DEFAULT_DIS7, ROOT
from generate_pdu_coverage import build_manifests
from generate_semantic_pdu_parsers import semantic_rows


WAVES: tuple[dict[str, str], ...] = (
    {
        "id": "wave1",
        "name": "Wave 1: State And Lifecycle",
        "slug": "state_lifecycle",
        "goal": "Drive entity state, identity, and immediate lifecycle rows first so the hot-path product semantics become deeper before broader protocol families.",
    },
    {
        "id": "wave2",
        "name": "Wave 2: Warfare And Effects",
        "slug": "warfare_effects",
        "goal": "Add semantically useful combat, collision, and visible-effect rows that unblock gameplay events and verification scenes.",
    },
    {
        "id": "wave3",
        "name": "Wave 3: Radio, Sensor, EW, IFF, And Designator",
        "slug": "radio_sensor_ew",
        "goal": "Deepen sensor, comms, emission, designator, and identification semantics with consistent engine and bridge events.",
    },
    {
        "id": "wave4",
        "name": "Wave 4: Simulation Management",
        "slug": "simulation_management",
        "goal": "Complete typed task/control semantics for simulation-management families, including reliable variants that currently stay generic.",
    },
    {
        "id": "wave5",
        "name": "Wave 5: Logistics, Environment, Aggregate, And Remaining Rows",
        "slug": "remaining_families",
        "goal": "Finish the remaining logistics, environment, aggregate, minefield, attribute, and information-operations families without leaving uncategorized rows behind.",
    },
)


WAVE1_NAMES = {
    "Entity State",
    "Entity State Update",
    "Create Entity",
    "Create Entity-R",
    "Remove Entity",
    "Remove Entity-R",
    "TSPI",
    "Appearance",
    "Articulated Parts",
    "Attribute",
}

WAVE2_NAMES = {
    "Fire",
    "Detonation",
    "Collision",
    "Collision-Elastic",
    "LE Fire",
    "LE Detonation",
    "Directed Energy Fire",
    "Entity Damage Status",
}

WAVE3_FAMILIES = {
    "Distributed Emission Regeneration",
    "Radio Communications",
}

WAVE4_FAMILIES = {
    "Simulation Management",
    "Simulation Management with Reliability",
}


def _wave_for_row(row: dict[str, Any]) -> tuple[str, str]:
    name = str(row["standard_name"])
    family = str(row["family_name"])
    if name in WAVE1_NAMES:
        return "wave1", "direct state/lifecycle row"
    if name in WAVE2_NAMES:
        return "wave2", "direct warfare/effects row"
    if family in WAVE3_FAMILIES:
        return "wave3", f"family={family}"
    if family in WAVE4_FAMILIES:
        return "wave4", f"family={family}"
    return "wave5", f"family={family}"


def build_wave_manifest(dis6: Path, dis7: Path) -> dict[str, Any]:
    _backbone, coverage_manifest = build_manifests(dis6, dis7)
    coverage_by_key = {
        (int(row["standard_version"]), int(row["pdu_type"])): row for row in coverage_manifest["rows"]
    }
    records: list[dict[str, Any]] = []
    wave_summaries = {
        wave["id"]: {
            "wave_id": wave["id"],
            "wave_name": wave["name"],
            "wave_slug": wave["slug"],
            "goal": wave["goal"],
            "rows": 0,
            "field_visitor_rows": 0,
            "typed_structural_rows": 0,
            "semantic_observation_rows": 0,
            "semantic_prefix_rows": 0,
            "fully_domain_decoded_rows": 0,
        }
        for wave in WAVES
    }

    for row in semantic_rows(dis6, dis7):
        key = (int(row["protocol_version"]), int(row["pdu_type"]))
        coverage = coverage_by_key[key]
        wave_id, reason = _wave_for_row(row)
        record = {
            "protocol_version": int(row["protocol_version"]),
            "pdu_type": int(row["pdu_type"]),
            "standard_name": str(row["standard_name"]),
            "standard_class_name": str(row["standard_class_name"]),
            "family_name": str(row["family_name"]),
            "wave_id": wave_id,
            "wave_name": next(w["name"] for w in WAVES if w["id"] == wave_id),
            "selection_reason": reason,
            "field_visitor": bool(coverage["field_visitor"]),
            "typed_structural": bool(row["typed_structural"]),
            "semantic_level": str(row["semantic_level"]),
            "fully_domain_decoded": bool(row["fully_domain_decoded"]),
            "endpoint_behavior": str(coverage["endpoint_behavior"]),
            "support_level": str(coverage["support_level"]),
        }
        summary = wave_summaries[wave_id]
        summary["rows"] += 1
        summary["field_visitor_rows"] += int(record["field_visitor"])
        summary["typed_structural_rows"] += int(record["typed_structural"])
        summary["semantic_observation_rows"] += int(record["semantic_level"] == "semantic_observation")
        summary["semantic_prefix_rows"] += int(record["semantic_level"] == "semantic_prefix")
        summary["fully_domain_decoded_rows"] += int(record["fully_domain_decoded"])
        records.append(record)

    records.sort(key=lambda item: (item["wave_id"], item["protocol_version"], item["pdu_type"]))
    ordered_summaries = [wave_summaries[wave["id"]] for wave in WAVES]
    return {
        "schema": "fastdis.epic2.semantic_waves.v1",
        "policy": {
            "goal": "Classify every standard DIS 6/7 row into a typed-semantic implementation wave without claiming rows are already fully domain-decoded.",
            "wave1": "State/lifecycle rows and immediate entity-state adjacencies.",
            "wave2": "Warfare and visible-effect rows.",
            "wave3": "Radio, sensor, EW, IFF, and designator families.",
            "wave4": "Simulation-management families, including reliable variants.",
            "wave5": "Remaining logistics, environment, aggregate, minefield, attribute, and information-operations rows.",
        },
        "summary": {
            "records": len(records),
            "waves": len(WAVES),
            "field_visitor_rows": sum(item["field_visitor_rows"] for item in ordered_summaries),
            "typed_structural_rows": sum(item["typed_structural_rows"] for item in ordered_summaries),
            "semantic_prefix_rows": sum(item["semantic_prefix_rows"] for item in ordered_summaries),
            "fully_domain_decoded_rows": sum(item["fully_domain_decoded_rows"] for item in ordered_summaries),
        },
        "waves": ordered_summaries,
        "records": records,
    }


def generate_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Epic 2 Semantic Waves",
        "",
        "This generated worklist assigns every standard DIS 6/7 versioned row to one typed-semantic buildout wave.",
        "",
        "## Summary",
        "",
        f"- Versioned rows classified: `{payload['summary']['records']} / 141`",
        f"- Waves: `{payload['summary']['waves']}`",
        f"- Field visitor rows already present: `{payload['summary']['field_visitor_rows']} / 141`",
        f"- Typed structural rows already present: `{payload['summary']['typed_structural_rows']} / 141`",
        f"- Semantic prefix rows already present: `{payload['summary']['semantic_prefix_rows']} / 141`",
        f"- Fully domain-decoded rows already present: `{payload['summary']['fully_domain_decoded_rows']} / 141`",
        "",
        "The waves are planning buckets, not claims that every row in a wave is already semantically complete.",
        "",
        "## Wave Summary",
        "",
        "| Wave | Rows | Structural | Prefix | Fully decoded | Goal |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for wave in payload["waves"]:
        lines.append(
            f"| {wave['wave_name']} | {wave['rows']} | {wave['typed_structural_rows']} | "
            f"{wave['semantic_prefix_rows']} | {wave['fully_domain_decoded_rows']} | {wave['goal']} |"
        )

    for wave in payload["waves"]:
        lines.extend(
            [
                "",
                f"## {wave['wave_name']}",
                "",
                wave["goal"],
                "",
                "| DIS | PDU | Name | Family | Semantic level | Structural | Decoded | Reason |",
                "| ---: | ---: | --- | --- | --- | --- | --- | --- |",
            ]
        )
        for record in payload["records"]:
            if record["wave_id"] != wave["wave_id"]:
                continue
            lines.append(
                f"| {record['protocol_version']} | {record['pdu_type']} | {record['standard_name']} | "
                f"{record['family_name']} | `{record['semantic_level']}` | "
                f"{'yes' if record['typed_structural'] else 'no'} | "
                f"{'yes' if record['fully_domain_decoded'] else 'no'} | {record['selection_reason']} |"
            )
    return "\n".join(lines) + "\n"


def outputs(dis6: Path, dis7: Path) -> dict[Path, str]:
    payload = build_wave_manifest(dis6, dis7)
    return {
        ROOT / "generated" / "epic2_semantic_waves.json": json.dumps(payload, indent=2) + "\n",
        ROOT / "docs" / "EPIC2_SEMANTIC_WAVES.md": generate_markdown(payload),
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
            print("stale generated Epic 2 semantic wave artifacts:", file=sys.stderr)
            for path in stale:
                print(f"  {path.relative_to(ROOT)}", file=sys.stderr)
            return 1
        return 0

    for path, content in rendered.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    payload = build_wave_manifest(args.dis6, args.dis7)
    print(
        "generated Epic 2 semantic wave worklist "
        f"records={payload['summary']['records']} waves={payload['summary']['waves']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
