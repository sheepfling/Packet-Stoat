#!/usr/bin/env python3
"""Audit readiness to promote DIS oracle vectors to golden byte evidence."""

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


DEFAULT_CATALOG = ROOT / "artifacts" / "reports" / "dis_oracle_catalog" / "dis_oracle_catalog.json"
DEFAULT_OUT_DIR = ROOT / "artifacts" / "reports" / "dis_oracle_vector_readiness"
VECTOR_TYPES = ("minimal", "typical", "boundary", "stress_variable", "malformed")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_OUT_DIR / "dis_oracle_vector_readiness.json")
    parser.add_argument("--md-out", type=Path, default=DEFAULT_OUT_DIR / "dis_oracle_vector_readiness.md")
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


def _pending_text(value: Any) -> bool:
    text = json.dumps(value, sort_keys=True).lower()
    return "pending" in text or "todo" in text or "<pin>" in text


def _rooted(path_text: str | None) -> Path | None:
    if not path_text:
        return None
    path = Path(path_text)
    return path if path.is_absolute() else ROOT / path


def assess_vector(vector_type: str, file_text: str | None, catalog_quality: str, *, normative_layout_pinned: bool) -> dict[str, Any]:
    path = _rooted(file_text)
    payload = load_json_if_present(path)
    expected_wire = payload.get("expected_wire") if isinstance(payload.get("expected_wire"), dict) else {}
    spec_basis = payload.get("spec_basis") if isinstance(payload.get("spec_basis"), list) else []
    blockers: list[str] = []
    if not normative_layout_pinned:
        blockers.append("layout_not_pinned")
    present = path is not None and path.is_file()
    if not present:
        blockers.append("vector_file_missing")
    if payload.get("schema") != "fastdis.dis_oracle_vector.v1":
        blockers.append("schema_invalid")
    if payload.get("vector_status") != "golden":
        blockers.append("vector_status_not_golden")
    if not spec_basis or _pending_text(spec_basis):
        blockers.append("spec_basis_pending")
    if expected_wire.get("endianness") != "big":
        blockers.append("endianness_missing")
    if vector_type == "malformed":
        malformed_expectation = payload.get("malformed_expectation")
        if expected_wire.get("status") != "malformed_rejected":
            blockers.append("malformed_status_missing")
        if not isinstance(malformed_expectation, dict) or _pending_text(malformed_expectation):
            blockers.append("malformed_expectation_pending")
    else:
        if expected_wire.get("status") != "canonical_bytes_known":
            blockers.append("canonical_bytes_missing")
        if not isinstance(expected_wire.get("total_length"), int) or expected_wire.get("total_length") <= 0:
            blockers.append("total_length_missing")
        if not isinstance(expected_wire.get("sha256"), str) or len(expected_wire.get("sha256", "")) != 64:
            blockers.append("sha256_missing")
        if not isinstance(expected_wire.get("hex"), str) or not expected_wire.get("hex"):
            blockers.append("hex_missing")
        if not isinstance(expected_wire.get("field_offsets"), dict) or not expected_wire.get("field_offsets"):
            blockers.append("field_offsets_missing")
        if not isinstance(expected_wire.get("field_widths"), dict) or not expected_wire.get("field_widths"):
            blockers.append("field_widths_missing")
    return {
        "vector_type": vector_type,
        "file": display_path(path) if path is not None else None,
        "present": present,
        "catalog_quality": catalog_quality,
        "normative_layout_pinned": normative_layout_pinned,
        "vector_status": payload.get("vector_status"),
        "wire_status": expected_wire.get("status"),
        "has_sha256": isinstance(expected_wire.get("sha256"), str) and len(expected_wire.get("sha256", "")) == 64,
        "has_hex": isinstance(expected_wire.get("hex"), str) and bool(expected_wire.get("hex")),
        "has_field_offsets": isinstance(expected_wire.get("field_offsets"), dict) and bool(expected_wire.get("field_offsets")),
        "has_field_widths": isinstance(expected_wire.get("field_widths"), dict) and bool(expected_wire.get("field_widths")),
        "blockers": blockers,
        "readiness": "golden_ready" if not blockers else ("draft_byte_evidence" if expected_wire.get("status") == "canonical_bytes_known" else "skeleton_or_missing"),
    }


def assess_row(row: dict[str, Any]) -> dict[str, Any]:
    vectors = row.get("vectors") if isinstance(row.get("vectors"), dict) else {}
    quality = vectors.get("quality") if isinstance(vectors.get("quality"), dict) else {}
    files = vectors.get("files") if isinstance(vectors.get("files"), dict) else {}
    coverage = row.get("coverage") if isinstance(row.get("coverage"), dict) else {}
    normative_layout_pinned = bool(coverage.get("normative_layout_pinned"))
    vector_rows = [
        assess_vector(
            vector_type,
            files.get(vector_type),
            str(quality.get(vector_type) or "missing"),
            normative_layout_pinned=normative_layout_pinned,
        )
        for vector_type in VECTOR_TYPES
    ]
    blockers = sorted({blocker for vector in vector_rows for blocker in vector["blockers"]})
    golden_count = sum(1 for vector in vector_rows if vector["readiness"] == "golden_ready")
    draft_byte_count = sum(1 for vector in vector_rows if vector["readiness"] == "draft_byte_evidence")
    return {
        "version": row.get("version"),
        "pdu_type": row.get("pdu_type"),
        "pdu_name": row.get("pdu_name"),
        "family_name": row.get("family_name"),
        "normative_layout_pinned": normative_layout_pinned,
        "golden_count": golden_count,
        "draft_byte_evidence_count": draft_byte_count,
        "required_count": len(VECTOR_TYPES),
        "golden_required_vectors": golden_count == len(VECTOR_TYPES),
        "blockers": blockers,
        "vectors": vector_rows,
        "review_state": "golden_ready" if golden_count == len(VECTOR_TYPES) else ("draft_byte_evidence" if draft_byte_count else "skeleton_or_missing"),
    }


def build_report(catalog_path: Path) -> dict[str, Any]:
    catalog = load_json(catalog_path)
    rows = catalog.get("rows") if isinstance(catalog.get("rows"), list) else []
    readiness_rows = [assess_row(row) for row in rows if isinstance(row, dict)]
    vector_rows = [vector for row in readiness_rows for vector in row["vectors"]]
    summary = {
        "row_count": len(readiness_rows),
        "required_vector_slots": len(vector_rows),
        "present_vector_files": sum(1 for vector in vector_rows if vector["present"]),
        "layout_pinned_rows": sum(1 for row in readiness_rows if row["normative_layout_pinned"]),
        "rows_blocked_by_unpinned_layout": sum(1 for row in readiness_rows if not row["normative_layout_pinned"]),
        "slots_blocked_by_unpinned_layout": sum(1 for vector in vector_rows if "layout_not_pinned" in vector["blockers"]),
        "golden_vector_slots": sum(1 for vector in vector_rows if vector["readiness"] == "golden_ready"),
        "draft_byte_evidence_slots": sum(1 for vector in vector_rows if vector["readiness"] == "draft_byte_evidence"),
        "skeleton_or_missing_slots": sum(1 for vector in vector_rows if vector["readiness"] == "skeleton_or_missing"),
        "rows_with_all_golden_vectors": sum(1 for row in readiness_rows if row["golden_required_vectors"]),
        "rows_with_any_draft_byte_evidence": sum(1 for row in readiness_rows if row["draft_byte_evidence_count"] > 0),
    }
    return {
        "schema": "fastdis.dis_oracle_vector_readiness.v1",
        "status": "passed" if summary["rows_with_all_golden_vectors"] == summary["row_count"] and summary["row_count"] else "partial",
        "sources": {"catalog": display_path(catalog_path)},
        "summary": summary,
        "rows": readiness_rows,
        "claim_boundary": (
            "Vector readiness tracks whether required vectors are golden byte evidence. "
            "A vector cannot become golden until its row has a pinned normative layout. "
            "Skeleton files, pending spec references, and FastDIS-only draft bytes are not golden vectors."
        ),
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# DIS Oracle Vector Readiness",
        "",
        f"- schema: `{report['schema']}`",
        f"- status: `{report['status']}`",
        f"- row_count: `{report['summary']['row_count']}`",
        f"- required_vector_slots: `{report['summary']['required_vector_slots']}`",
        f"- layout_pinned_rows: `{report['summary']['layout_pinned_rows']}`",
        f"- rows_blocked_by_unpinned_layout: `{report['summary']['rows_blocked_by_unpinned_layout']}`",
        f"- golden_vector_slots: `{report['summary']['golden_vector_slots']}`",
        f"- draft_byte_evidence_slots: `{report['summary']['draft_byte_evidence_slots']}`",
        "",
        "## Claim Boundary",
        "",
        report["claim_boundary"],
        "",
        "## Rows",
        "",
        "| version | pdu | name | layout pinned | state | golden | draft bytes | blockers |",
        "| --- | ---: | --- | --- | --- | ---: | ---: | --- |",
    ]
    for row in report["rows"]:
        blockers = ", ".join(row["blockers"][:8]) if row["blockers"] else "none"
        lines.append(
            f"| {row['version']} | {row['pdu_type']} | {row['pdu_name']} | `{row['normative_layout_pinned']}` | `{row['review_state']}` | "
            f"{row['golden_count']} | {row['draft_byte_evidence_count']} | {blockers} |"
        )
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report = build_report(args.catalog)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.md_out.parent.mkdir(parents=True, exist_ok=True)
    write_json_report(
        args.json_out,
        report,
        schema="fastdis.dis_oracle_vector_readiness.v1",
        producer="tools/audit_dis_oracle_vector_readiness.py",
    )
    args.md_out.write_text(render_markdown(report) + "\n", encoding="utf-8")
    print(f"json: {display_path(args.json_out)}")
    print(f"md: {display_path(args.md_out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
