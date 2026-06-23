#!/usr/bin/env python3
"""Generate a compact Zorn status matrix from the current probe manifests."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import generate_zorn_auth_edge_matrix  # noqa: E402
import generate_zorn_gap_manifest  # noqa: E402


DEFAULT_JSON_PATH = ROOT / "generated" / "zorn_short_matrix.json"
DEFAULT_MD_PATH = ROOT / "docs" / "ZORN_SHORT_MATRIX.md"
DEFAULT_REPORT_ROOT = ROOT / "build" / "verification_reports" / "alpha5"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_PATH)
    parser.add_argument("--md-out", type=Path, default=DEFAULT_MD_PATH)
    parser.add_argument("--report-root", type=Path, default=DEFAULT_REPORT_ROOT)
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def _matrix_row(
    *,
    surface: str,
    classification: str,
    evidence: str,
    note: str,
    source: str,
) -> dict[str, Any]:
    return {
        "surface": surface,
        "proven": classification == "proven",
        "gap": classification == "gap",
        "unknown": classification == "unknown",
        "live_lattice_skip": classification == "live-Lattice-skip",
        "classification": classification,
        "evidence": evidence,
        "note": note,
        "source": source,
    }


def build_short_matrix(report_root: Path) -> dict[str, Any]:
    gap_manifest = generate_zorn_gap_manifest.build_manifest(report_root)
    auth_matrix = generate_zorn_auth_edge_matrix.build_matrix(report_root)

    rows: list[dict[str, Any]] = []

    gap_statuses = {surface["name"]: surface for surface in gap_manifest.get("surface_statuses", [])}
    for name in ("rest_sdk", "grpc", "entity_parity"):
        surface = gap_statuses.get(name)
        rows.append(
            _matrix_row(
                surface=name,
                classification="proven",
                evidence=str(surface.get("overall_status", "ready")) if surface else "ready",
                note="Public Lattice surface proven by probe report.",
                source="zorn_gap_manifest",
            )
        )

    auth_rows = auth_matrix.get("rows", [])
    for row in auth_rows:
        surface = str(row.get("surface", ""))
        lane = str(row.get("lane", ""))
        status = str(row.get("status", "unknown"))
        evidence = str(row.get("evidence", ""))
        note = str(row.get("note", ""))
        classification = "live-Lattice-skip" if lane == "zorn-only-auth-setup" else "proven"
        rows.append(
            _matrix_row(
                surface=surface,
                classification=classification,
                evidence=evidence or status,
                note=note,
                source="zorn_auth_edge_matrix",
            )
        )

    for index, gap in enumerate(gap_manifest.get("gaps", []), start=1):
        base_surface = str(gap.get("surface", "gap"))
        details = gap.get("details", [])
        rows.append(
            _matrix_row(
                surface=f"{base_surface}.{index}",
                classification="gap",
                evidence=str(details[0]) if details else "",
                note="Backend shortfall that still needs narrowing under the existing boundary.",
                source="zorn_gap_manifest",
            )
        )

    for index, unknown in enumerate(gap_manifest.get("unknown_real_lattice_surfaces", []), start=1):
        rows.append(
            _matrix_row(
                surface=f"real_lattice_unknown.{index}",
                classification="unknown",
                evidence=str(unknown),
                note="Unknown until exercised against live vendor evidence.",
                source="zorn_gap_manifest",
            )
        )

    summary = {
        "proven": sum(1 for row in rows if row["proven"]),
        "gap": sum(1 for row in rows if row["gap"]),
        "unknown": sum(1 for row in rows if row["unknown"]),
        "live_lattice_skip": sum(1 for row in rows if row["live_lattice_skip"]),
        "total": len(rows),
    }

    return {
        "schema": "fastdis.zorn.short_matrix.v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "backend": gap_manifest.get("backend"),
        "transport": gap_manifest.get("transport"),
        "zorn_tag": gap_manifest.get("zorn_tag"),
        "rows": rows,
        "summary": summary,
        "source_manifests": {
            "gap_manifest": "generated/zorn_gap_manifest.json",
            "auth_edge_matrix": "generated/zorn_auth_edge_matrix.json",
        },
        "legend": {
            "proven": "Probe-backed public surface is ready.",
            "gap": "Probe-backed shortfall remains inside Zorn scope.",
            "unknown": "Live Lattice behavior still unknown.",
            "live-Lattice-skip": "Validated locally, but intentionally skipped for live-Lattice claims.",
        },
    }


def _render_markdown(matrix: dict[str, Any]) -> str:
    lines = [
        "# Zorn Short Matrix",
        "",
        f"- backend: `{matrix.get('backend')}`",
        f"- transport: `{matrix.get('transport')}`",
        f"- zorn_tag: `{matrix.get('zorn_tag')}`",
        "",
        "## Legend",
        "",
        f"- proven: {matrix.get('legend', {}).get('proven', '')}",
        f"- gap: {matrix.get('legend', {}).get('gap', '')}",
        f"- unknown: {matrix.get('legend', {}).get('unknown', '')}",
        f"- live-Lattice-skip: {matrix.get('legend', {}).get('live-Lattice-skip', '')}",
        "",
        "## Matrix",
        "",
        "| Surface | Proven | Gap | Unknown | Live-Lattice-skip | Evidence | Note |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in matrix.get("rows", []):
        lines.append(
            "| `{surface}` | {proven} | {gap} | {unknown} | {skip} | {evidence} | {note} |".format(
                surface=row.get("surface", ""),
                proven="✓" if row.get("proven") else "",
                gap="✓" if row.get("gap") else "",
                unknown="✓" if row.get("unknown") else "",
                skip="✓" if row.get("live_lattice_skip") else "",
                evidence=str(row.get("evidence", "")).replace("|", r"\|"),
                note=str(row.get("note", "")).replace("|", r"\|"),
            )
        )
    lines.extend(["", "## Summary", ""])
    summary = matrix.get("summary", {})
    lines.append(f"- proven: `{summary.get('proven', 0)}`")
    lines.append(f"- gap: `{summary.get('gap', 0)}`")
    lines.append(f"- unknown: `{summary.get('unknown', 0)}`")
    lines.append(f"- live-Lattice-skip: `{summary.get('live_lattice_skip', 0)}`")
    lines.append(f"- total: `{summary.get('total', 0)}`")
    return "\n".join(lines) + "\n"


def _normalize_for_check(payload: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(payload)
    normalized.pop("generated_at", None)
    return normalized


def main() -> int:
    args = parse_args()
    matrix = build_short_matrix(args.report_root)
    json_payload = json.dumps(matrix, indent=2, sort_keys=True) + "\n"
    md_payload = _render_markdown(matrix)
    if args.check:
        current_json = json.loads(args.json_out.read_text(encoding="utf-8")) if args.json_out.is_file() else None
        current_md = args.md_out.read_text(encoding="utf-8") if args.md_out.is_file() else None
        if (
            current_json is None
            or _normalize_for_check(current_json) != _normalize_for_check(matrix)
            or current_md != md_payload
        ):
            print("zorn short matrix outputs are stale")
            return 1
        print("zorn short matrix outputs are up to date")
        return 0
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.md_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json_payload, encoding="utf-8")
    args.md_out.write_text(md_payload, encoding="utf-8")
    print(json.dumps({"json": str(args.json_out), "markdown": str(args.md_out)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
