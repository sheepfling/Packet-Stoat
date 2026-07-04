#!/usr/bin/env python3
"""Build a tranche-scoped authoring packet for DIS oracle vector work."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

from report_envelope import write_json_report


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GOLDEN = ROOT / "artifacts" / "reports" / "dis_oracle_golden_vector_worklist" / "dis_oracle_golden_vector_worklist.json"
DEFAULT_MALFORMED = ROOT / "artifacts" / "reports" / "dis_oracle_malformed_vector_worklist" / "dis_oracle_malformed_vector_worklist.json"
DEFAULT_OUT_DIR = ROOT / "artifacts" / "reports" / "dis_oracle_vector_authoring_packet"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tranche", required=True, help="Tranche name from the layout-pin tranche plan, for example dis6_entity_information")
    parser.add_argument("--golden-worklist", type=Path, default=DEFAULT_GOLDEN)
    parser.add_argument("--malformed-worklist", type=Path, default=DEFAULT_MALFORMED)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--md-out", type=Path)
    return parser.parse_args(argv)


def display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _filter_slots(payload: dict[str, Any], tranche: str) -> list[dict[str, Any]]:
    tasks = payload.get("tasks") if isinstance(payload.get("tasks"), list) else []
    return [task for task in tasks if isinstance(task, dict) and task.get("tranche_name") == tranche]


def _placeholder_blocker_count(slots: list[dict[str, Any]], blocker: str) -> int:
    return sum(1 for slot in slots if blocker in (slot.get("blockers") or []))


def build_report(tranche: str, golden_worklist_path: Path, malformed_worklist_path: Path) -> dict[str, Any]:
    golden = load_json(golden_worklist_path)
    malformed = load_json(malformed_worklist_path)
    golden_slots = _filter_slots(golden, tranche)
    malformed_slots = _filter_slots(malformed, tranche)
    all_slots = golden_slots + malformed_slots
    version = all_slots[0].get("version") if all_slots else None
    family_name = all_slots[0].get("family_name") if all_slots else None

    return {
        "schema": "fastdis.dis_oracle_vector_authoring_packet.v1",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "status": "ready_for_authoring" if all_slots else "missing",
        "sources": {
            "golden_worklist": display_path(golden_worklist_path),
            "malformed_worklist": display_path(malformed_worklist_path),
        },
        "summary": {
            "tranche_name": tranche,
            "version": version,
            "family_name": family_name,
            "golden_slot_count": len(golden_slots),
            "malformed_slot_count": len(malformed_slots),
            "slot_count": len(all_slots),
            "spec_basis_pending_slots": _placeholder_blocker_count(all_slots, "spec_basis_pending"),
            "canonical_bytes_missing_slots": _placeholder_blocker_count(golden_slots, "canonical_bytes_missing"),
            "malformed_expectation_pending_slots": _placeholder_blocker_count(malformed_slots, "malformed_expectation_pending"),
            "first_golden_file": golden_slots[0].get("file") if golden_slots else None,
            "first_malformed_file": malformed_slots[0].get("file") if malformed_slots else None,
        },
        "golden_slots": golden_slots,
        "malformed_slots": malformed_slots,
        "commands": [
            f"python3 tools/build_dis_oracle_vector_authoring_packet.py --tranche {tranche}",
            "python3 tools/build_dis_oracle_golden_vector_worklist.py",
            "python3 tools/build_dis_oracle_malformed_vector_worklist.py",
        ],
        "claim_boundary": (
            "This packet organizes tranche-scoped vector authoring work only. It does not upgrade any vector to golden "
            "byte evidence until layout pins, exact references, bytes or malformed expectations, and final readiness checks are complete."
        ),
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# DIS Oracle Vector Authoring Packet",
        "",
        f"- schema: `{report['schema']}`",
        f"- status: `{report['status']}`",
        f"- tranche_name: `{report['summary']['tranche_name']}`",
        f"- version: `{report['summary']['version']}`",
        f"- family_name: `{report['summary']['family_name']}`",
        f"- golden_slot_count: `{report['summary']['golden_slot_count']}`",
        f"- malformed_slot_count: `{report['summary']['malformed_slot_count']}`",
        f"- spec_basis_pending_slots: `{report['summary']['spec_basis_pending_slots']}`",
        "",
        "## Golden Slots",
        "",
        "| pdu | vector | file | next action | blockers |",
        "| --- | --- | --- | --- | --- |",
    ]
    for slot in report["golden_slots"]:
        blockers = ", ".join(slot.get("blockers") or [])
        lines.append(f"| {slot['pdu_name']} | {slot['vector_type']} | `{slot['file']}` | `{slot['next_action']}` | {blockers} |")
    lines.extend(["", "## Malformed Slots", "", "| pdu | file | next action | blockers |", "| --- | --- | --- | --- |"])
    for slot in report["malformed_slots"]:
        blockers = ", ".join(slot.get("blockers") or [])
        lines.append(f"| {slot['pdu_name']} | `{slot['file']}` | `{slot['next_action']}` | {blockers} |")
    lines.extend(["", "## Claim Boundary", "", report["claim_boundary"], ""])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    json_out = args.json_out or (DEFAULT_OUT_DIR / f"dis_oracle_vector_authoring_packet_{args.tranche}.json")
    md_out = args.md_out or (DEFAULT_OUT_DIR / f"dis_oracle_vector_authoring_packet_{args.tranche}.md")
    report = build_report(args.tranche, args.golden_worklist, args.malformed_worklist)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.parent.mkdir(parents=True, exist_ok=True)
    write_json_report(
        json_out,
        report,
        schema="fastdis.dis_oracle_vector_authoring_packet.v1",
        producer="tools/build_dis_oracle_vector_authoring_packet.py",
    )
    md_out.write_text(render_markdown(report) + "\n", encoding="utf-8")
    print(f"json: {display_path(json_out)}")
    print(f"md: {display_path(md_out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
