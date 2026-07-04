#!/usr/bin/env python3
"""Build an authoring worklist for DIS oracle golden vector slots."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from report_envelope import write_json_report


DEFAULT_VECTOR_READINESS = ROOT / "artifacts" / "reports" / "dis_oracle_vector_readiness" / "dis_oracle_vector_readiness.json"
DEFAULT_TRANCHE_PLAN = ROOT / "artifacts" / "reports" / "dis_oracle_layout_pin_tranche_plan" / "dis_oracle_layout_pin_tranche_plan.json"
DEFAULT_OUT_DIR = ROOT / "artifacts" / "reports" / "dis_oracle_vector_worklist"
VECTOR_TYPES = ("minimal", "typical", "boundary", "stress_variable", "malformed")

ACTION_PRIORITY = {
    "pin_normative_layout": 5,
    "create_vector_file": 10,
    "pin_spec_basis": 20,
    "fill_canonical_bytes": 30,
    "fill_field_map": 40,
    "write_malformed_expectation": 45,
    "mark_vector_golden": 60,
    "ready": 90,
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vector-readiness", type=Path, default=DEFAULT_VECTOR_READINESS)
    parser.add_argument("--tranche-plan", type=Path, default=DEFAULT_TRANCHE_PLAN)
    parser.add_argument("--ignore-layout-gate", action="store_true", help="Prioritize actionable authoring beyond the layout-pin gate.")
    parser.add_argument("--only-vector-type", choices=VECTOR_TYPES, action="append")
    parser.add_argument("--json-out", type=Path, default=DEFAULT_OUT_DIR / "dis_oracle_vector_worklist.json")
    parser.add_argument("--md-out", type=Path, default=DEFAULT_OUT_DIR / "dis_oracle_vector_worklist.md")
    return parser.parse_args(argv)


def display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_json_if_present(path: Path | None) -> dict[str, Any]:
    if path is None or not path.is_file():
        return {}
    return load_json(path)


def tranche_index(tranche_plan: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    rows = tranche_plan.get("tranches") if isinstance(tranche_plan.get("tranches"), list) else []
    return {
        (str(row.get("version") or ""), str(row.get("family_name") or "")): row
        for row in rows
        if isinstance(row, dict)
    }


def next_action(vector: dict[str, Any], *, ignore_layout_gate: bool) -> tuple[str, str]:
    blockers = set(vector.get("blockers") if isinstance(vector.get("blockers"), list) else [])
    vector_type = str(vector.get("vector_type") or "")
    if "layout_not_pinned" in blockers and not ignore_layout_gate:
        return ("pin_normative_layout", "Pin the row's normative field layout before promoting any vectors to golden byte evidence.")
    if "vector_file_missing" in blockers or "schema_invalid" in blockers:
        return ("create_vector_file", "Create a valid vector JSON file for this required slot.")
    if "spec_basis_pending" in blockers:
        return ("pin_spec_basis", "Replace pending spec_basis with exact IEEE/SISO references for this vector claim.")
    if vector_type == "malformed":
        if "malformed_status_missing" in blockers or "malformed_expectation_pending" in blockers:
            return ("write_malformed_expectation", "Define malformed bytes/case and expected reject-or-flag behavior.")
    if blockers.intersection({"canonical_bytes_missing", "total_length_missing", "sha256_missing", "hex_missing"}):
        return ("fill_canonical_bytes", "Author canonical wire bytes, total length, hex, and sha256.")
    if blockers.intersection({"field_offsets_missing", "field_widths_missing"}):
        return ("fill_field_map", "Record expected field offsets and widths for this vector.")
    if "vector_status_not_golden" in blockers:
        return ("mark_vector_golden", "After review, set vector_status to golden.")
    return ("ready", "Vector slot satisfies golden-readiness checks.")


def build_report(
    vector_readiness_path: Path,
    *,
    tranche_plan_path: Path | None = None,
    ignore_layout_gate: bool = False,
    only_vector_types: set[str] | None = None,
) -> dict[str, Any]:
    readiness = load_json(vector_readiness_path)
    tranches = tranche_index(load_json_if_present(tranche_plan_path))
    tasks: list[dict[str, Any]] = []
    action_counts: dict[str, int] = {}
    for row in readiness.get("rows", []) if isinstance(readiness.get("rows"), list) else []:
        if not isinstance(row, dict):
            continue
        family_name = str(row.get("family_name") or "")
        tranche = tranches.get((str(row.get("version") or ""), family_name), {})
        for vector in row.get("vectors", []) if isinstance(row.get("vectors"), list) else []:
            if not isinstance(vector, dict):
                continue
            vector_type = str(vector.get("vector_type") or "")
            if only_vector_types is not None and vector_type not in only_vector_types:
                continue
            action, detail = next_action(vector, ignore_layout_gate=ignore_layout_gate)
            action_counts[action] = action_counts.get(action, 0) + 1
            tasks.append(
                {
                    "tranche_name": tranche.get("name"),
                    "review_order": int(tranche.get("review_order") or 999),
                    "version": row.get("version"),
                    "family_name": row.get("family_name"),
                    "pdu_type": row.get("pdu_type"),
                    "pdu_name": row.get("pdu_name"),
                    "vector_type": vector_type,
                    "file": vector.get("file"),
                    "readiness": vector.get("readiness"),
                    "priority": ACTION_PRIORITY.get(action, 99),
                    "next_action": action,
                    "next_action_detail": detail,
                    "blockers": vector.get("blockers") if isinstance(vector.get("blockers"), list) else [],
                }
            )
    tasks.sort(
        key=lambda task: (
            int(task["priority"]),
            int(task.get("review_order") or 999),
            str(task["version"]),
            int(task.get("pdu_type") or 0),
            str(task["pdu_name"]),
            str(task["vector_type"]),
        )
    )
    pending = [task for task in tasks if task["next_action"] != "ready"]
    return {
        "schema": "fastdis.dis_oracle_vector_worklist.v1",
        "status": "passed" if tasks and not pending else "partial",
        "sources": {
            "vector_readiness": display_path(vector_readiness_path),
            "tranche_plan": display_path(tranche_plan_path) if tranche_plan_path is not None else None,
        },
        "summary": {
            "slot_count": len(tasks),
            "pending_slot_count": len(pending),
            "ready_slot_count": action_counts.get("ready", 0),
            "action_counts": action_counts,
            "top_action": pending[0]["next_action"] if pending else "none",
            "top_action_count": action_counts.get(pending[0]["next_action"], 0) if pending else 0,
            "ignore_layout_gate": ignore_layout_gate,
            "vector_type_filter": sorted(only_vector_types) if only_vector_types is not None else list(VECTOR_TYPES),
            "first_tranche": pending[0].get("tranche_name") if pending else None,
        },
        "tasks": tasks,
        "claim_boundary": (
            "This is a vector authoring worklist. A vector slot is not golden byte evidence until exact references, "
            "a pinned normative layout, canonical bytes or malformed expectations, field maps, and vector_status=golden all pass readiness checks."
        ),
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# DIS Oracle Vector Worklist",
        "",
        f"- schema: `{report['schema']}`",
        f"- status: `{report['status']}`",
        f"- slot_count: `{report['summary']['slot_count']}`",
        f"- pending_slot_count: `{report['summary']['pending_slot_count']}`",
        f"- top_action: `{report['summary']['top_action']}`",
        "",
        "## Action Counts",
        "",
    ]
    for action, count in sorted(report["summary"]["action_counts"].items()):
        lines.append(f"- {action}: `{count}`")
    lines.extend(
        [
            "",
            "## Queue",
            "",
            "| priority | order | tranche | version | pdu | name | vector | next action | blockers |",
            "| ---: | ---: | --- | --- | ---: | --- | --- | --- | --- |",
        ]
    )
    for task in report["tasks"][:100]:
        blockers = ", ".join(task["blockers"][:6]) if task["blockers"] else "none"
        lines.append(
            f"| {task['priority']} | {task['review_order']} | {task['tranche_name']} | {task['version']} | {task['pdu_type']} | {task['pdu_name']} | "
            f"{task['vector_type']} | `{task['next_action']}` | {blockers} |"
        )
    lines.extend(["", "## Claim Boundary", "", report["claim_boundary"], ""])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report = build_report(
        args.vector_readiness,
        tranche_plan_path=args.tranche_plan,
        ignore_layout_gate=bool(args.ignore_layout_gate),
        only_vector_types=set(args.only_vector_type) if args.only_vector_type else None,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.md_out.parent.mkdir(parents=True, exist_ok=True)
    write_json_report(
        args.json_out,
        report,
        schema="fastdis.dis_oracle_vector_worklist.v1",
        producer="tools/build_dis_oracle_vector_worklist.py",
    )
    args.md_out.write_text(render_markdown(report) + "\n", encoding="utf-8")
    print(f"json: {display_path(args.json_out)}")
    print(f"md: {display_path(args.md_out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
