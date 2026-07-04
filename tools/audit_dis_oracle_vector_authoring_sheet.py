#!/usr/bin/env python3
"""Audit a vector authoring sheet for unresolved pending citation placeholders."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml
from report_envelope import write_json_report


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = ROOT / "artifacts" / "reports" / "dis_oracle_vector_authoring_sheet_audit"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sheet", type=Path, required=True)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--md-out", type=Path)
    return parser.parse_args(argv)


def display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def load_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _pending(value: Any) -> bool:
    text = json.dumps(value, sort_keys=True).lower()
    return "pending" in text or "tbd" in text or "<pin>" in text


def build_report(sheet_path: Path) -> dict[str, Any]:
    sheet = load_yaml(sheet_path)
    rows = sheet.get("rows") if isinstance(sheet.get("rows"), list) else []
    audit_rows: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        edit = row.get("edit") if isinstance(row.get("edit"), dict) else {}
        spec_basis = edit.get("spec_basis") if isinstance(edit.get("spec_basis"), list) else []
        audit_rows.append(
            {
                "file": row.get("file"),
                "pdu_name": row.get("pdu_name"),
                "vector_type": row.get("vector_type"),
                "spec_basis_pending": _pending(spec_basis),
                "malformed_expectation_pending": _pending(edit.get("malformed_expectation")),
                "expected_wire_pending": _pending(edit.get("expected_wire")),
            }
        )
    summary = {
        "row_count": len(audit_rows),
        "spec_basis_pending_rows": sum(1 for row in audit_rows if row["spec_basis_pending"]),
        "malformed_expectation_pending_rows": sum(1 for row in audit_rows if row["malformed_expectation_pending"]),
        "expected_wire_pending_rows": sum(1 for row in audit_rows if row["expected_wire_pending"]),
    }
    return {
        "schema": "fastdis.dis_oracle_vector_authoring_sheet_audit.v1",
        "status": "passed" if summary["spec_basis_pending_rows"] == 0 else "partial",
        "source_sheet": display_path(sheet_path),
        "summary": summary,
        "rows": audit_rows,
        "claim_boundary": "This audit only checks for unresolved placeholder content in the authoring sheet.",
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# DIS Oracle Vector Authoring Sheet Audit",
        "",
        f"- status: `{report['status']}`",
        f"- row_count: `{report['summary']['row_count']}`",
        f"- spec_basis_pending_rows: `{report['summary']['spec_basis_pending_rows']}`",
        "",
        "| pdu | vector | file | spec pending | malformed pending | wire pending |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in report["rows"]:
        lines.append(
            f"| {row['pdu_name']} | {row['vector_type']} | `{row['file']}` | `{row['spec_basis_pending']}` | `{row['malformed_expectation_pending']}` | `{row['expected_wire_pending']}` |"
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    stem = args.sheet.stem
    json_out = args.json_out or (DEFAULT_OUT_DIR / f"{stem}_audit.json")
    md_out = args.md_out or (DEFAULT_OUT_DIR / f"{stem}_audit.md")
    report = build_report(args.sheet)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.parent.mkdir(parents=True, exist_ok=True)
    write_json_report(
        json_out,
        report,
        schema="fastdis.dis_oracle_vector_authoring_sheet_audit.v1",
        producer="tools/audit_dis_oracle_vector_authoring_sheet.py",
    )
    md_out.write_text(render_markdown(report) + "\n", encoding="utf-8")
    print(f"json: {display_path(json_out)}")
    print(f"md: {display_path(md_out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
