#!/usr/bin/env python3
"""Build a spec-basis-only fill packet from a vector authoring sheet."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml
from report_envelope import write_json_report


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = ROOT / "artifacts" / "reports" / "dis_oracle_vector_spec_basis_packet"


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


def _is_pending(spec_basis: list[dict[str, Any]]) -> bool:
    text = yaml.safe_dump(spec_basis, sort_keys=True).lower()
    return "pending" in text or "tbd" in text or "<pin>" in text


def build_report(sheet_path: Path) -> dict[str, Any]:
    sheet = load_yaml(sheet_path)
    rows = sheet.get("rows") if isinstance(sheet.get("rows"), list) else []
    packet_rows: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        edit = row.get("edit") if isinstance(row.get("edit"), dict) else {}
        spec_basis = edit.get("spec_basis") if isinstance(edit.get("spec_basis"), list) else []
        if not spec_basis:
            continue
        packet_rows.append(
            {
                "file": row.get("file"),
                "version": row.get("version"),
                "family_name": row.get("family_name"),
                "pdu_name": row.get("pdu_name"),
                "vector_type": row.get("vector_type"),
                "spec_basis": spec_basis,
                "pending": _is_pending(spec_basis),
            }
        )
    pending_rows = [row for row in packet_rows if row["pending"]]
    return {
        "schema": "fastdis.dis_oracle_vector_spec_basis_packet.v1",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "status": "ready_for_review" if packet_rows else "missing",
        "source_sheet": display_path(sheet_path),
        "summary": {
            "row_count": len(packet_rows),
            "pending_row_count": len(pending_rows),
            "first_pending_file": pending_rows[0]["file"] if pending_rows else None,
        },
        "rows": packet_rows,
        "claim_boundary": (
            "This packet isolates vector spec-basis citation work only. It does not validate, apply, or promote vector byte evidence."
        ),
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# DIS Oracle Vector Spec Basis Packet",
        "",
        f"- schema: `{report['schema']}`",
        f"- status: `{report['status']}`",
        f"- row_count: `{report['summary']['row_count']}`",
        f"- pending_row_count: `{report['summary']['pending_row_count']}`",
        "",
        "| pdu | vector | file | pending |",
        "| --- | --- | --- | --- |",
    ]
    for row in report["rows"]:
        lines.append(f"| {row['pdu_name']} | {row['vector_type']} | `{row['file']}` | `{row['pending']}` |")
    lines.extend(["", "## Claim Boundary", "", report["claim_boundary"], ""])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    stem = args.sheet.stem.replace("dis_oracle_vector_authoring_sheet_", "")
    json_out = args.json_out or (DEFAULT_OUT_DIR / f"dis_oracle_vector_spec_basis_packet_{stem}.json")
    md_out = args.md_out or (DEFAULT_OUT_DIR / f"dis_oracle_vector_spec_basis_packet_{stem}.md")
    report = build_report(args.sheet)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.parent.mkdir(parents=True, exist_ok=True)
    write_json_report(
        json_out,
        report,
        schema="fastdis.dis_oracle_vector_spec_basis_packet.v1",
        producer="tools/build_dis_oracle_vector_spec_basis_packet.py",
    )
    md_out.write_text(render_markdown(report) + "\n", encoding="utf-8")
    print(f"json: {display_path(json_out)}")
    print(f"md: {display_path(md_out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
