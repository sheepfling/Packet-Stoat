#!/usr/bin/env python3
"""Build per-surface claim-boundary guidance from current benchmark artifacts."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = ROOT / "artifacts" / "reports" / "surface_claim_report"
DEFAULT_MATRIX = ROOT / "artifacts" / "reports" / "benchmark_matrix" / "benchmark_matrix.json"
DEFAULT_COVERAGE = ROOT / "artifacts" / "reports" / "benchmark_coverage" / "benchmark_coverage_report.json"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matrix", type=Path, default=DEFAULT_MATRIX)
    parser.add_argument("--coverage", type=Path, default=DEFAULT_COVERAGE)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_OUT_DIR / "surface_claim_report.json")
    parser.add_argument("--md-out", type=Path, default=DEFAULT_OUT_DIR / "surface_claim_report.md")
    return parser.parse_args(argv)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _coverage_index(coverage: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = coverage.get("surfaces") if isinstance(coverage.get("surfaces"), list) else []
    return {
        row["surface"]: row
        for row in rows
        if isinstance(row, dict) and isinstance(row.get("surface"), str)
    }


def _surface_claim_row(surface: dict[str, Any], coverage_row: dict[str, Any] | None) -> dict[str, Any]:
    surface_name = str(surface.get("surface"))
    safe_claims: list[str] = []
    boundaries: list[str] = []
    capability_index = coverage_row.get("capabilities") if isinstance(coverage_row, dict) and isinstance(coverage_row.get("capabilities"), dict) else {}

    if surface.get("evidence_kind") in {"measured", "measured_or_verified"}:
        safe_claims.append(f"{surface_name} has a current shared benchmark report in the published matrix.")
    if bool((capability_index.get("ingest") or {}).get("covered")):
        safe_claims.append(f"{surface_name} has published ingest coverage.")
    if bool((capability_index.get("filtering") or {}).get("covered")):
        safe_claims.append(f"{surface_name} has published filtering or malformed-traffic benchmark coverage.")
    if bool((capability_index.get("latest_state") or {}).get("covered")):
        safe_claims.append(f"{surface_name} has published latest-state or snapshot benchmark coverage.")
    if bool((capability_index.get("replay") or {}).get("covered")):
        safe_claims.append(f"{surface_name} has published replay benchmark coverage.")
    if int(surface.get("truth_rows", 0) or 0) > 0:
        safe_claims.append(f"{surface_name} has truth-backed verification rows in the shared report contract.")
    if int(surface.get("latency_rows", 0) or 0) > 0 or int(surface.get("runtime_metric_rows", 0) or 0) > 0:
        safe_claims.append(f"{surface_name} has measured timing or runtime rows in the shared report contract.")

    if surface.get("evidence_kind") == "sample":
        boundaries.append("Do not use this surface for performance or product claims until a current measured report replaces the sample.")
    if surface.get("surface_kind") == "engine" and int(surface.get("latency_rows", 0) or 0) == 0 and int(surface.get("runtime_metric_rows", 0) or 0) == 0:
        boundaries.append("Do not describe this engine lane as a measured runtime benchmark; it is still a proof bridge.")
    if int(surface.get("truth_rows", 0) or 0) == 0:
        boundaries.append("Do not claim final truth verification for this surface from the shared benchmark report alone.")
    if not bool((capability_index.get("filtering") or {}).get("covered")):
        boundaries.append("Do not claim explicit filtering or malformed-traffic coverage for this surface.")
    if not bool((capability_index.get("latest_state") or {}).get("covered")):
        boundaries.append("Do not claim explicit latest-state or snapshot coverage for this surface.")
    if not bool((capability_index.get("replay") or {}).get("covered")):
        boundaries.append("Do not claim explicit replay benchmark coverage for this surface.")
    if surface_name not in {"unreal", "unity", "godot"} and int(surface.get("runtime_metric_rows", 0) or 0) == 0:
        boundaries.append("Do not frame this surface as an engine-runtime benchmark lane.")

    return {
        "surface": surface_name,
        "surface_kind": surface.get("surface_kind"),
        "evidence_kind": surface.get("evidence_kind"),
        "path": surface.get("path"),
        "safe_claims": safe_claims,
        "boundaries": boundaries,
    }


def build_report(matrix_path: Path, matrix: dict[str, Any], coverage_path: Path, coverage: dict[str, Any]) -> dict[str, Any]:
    surfaces = matrix.get("surfaces") if isinstance(matrix.get("surfaces"), list) else []
    coverage_index = _coverage_index(coverage)
    rows = [
        _surface_claim_row(surface, coverage_index.get(str(surface.get("surface"))))
        for surface in surfaces
        if isinstance(surface, dict) and isinstance(surface.get("surface"), str)
    ]
    return {
        "schema": "fastdis.surface_claim_report.v1",
        "generated_at_utc": utc_now(),
        "status": "complete",
        "sources": {
            "matrix": display_path(matrix_path),
            "coverage": display_path(coverage_path),
        },
        "surface_count": len(rows),
        "surfaces": rows,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Surface Claim Report",
        "",
        f"- schema: `{report['schema']}`",
        f"- status: `{report['status']}`",
        f"- surface_count: `{report['surface_count']}`",
        "",
    ]
    for row in report["surfaces"]:
        lines.append(f"## {row['surface']}")
        lines.append("")
        lines.append(f"- surface_kind: `{row['surface_kind']}`")
        lines.append(f"- evidence_kind: `{row['evidence_kind']}`")
        lines.append("Safe claims:")
        if row["safe_claims"]:
            for claim in row["safe_claims"]:
                lines.append(f"- {claim}")
        else:
            lines.append("- none")
        lines.append("Boundaries:")
        if row["boundaries"]:
            for boundary in row["boundaries"]:
                lines.append(f"- {boundary}")
        else:
            lines.append("- none")
        lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    matrix = load_json(args.matrix)
    coverage = load_json(args.coverage)
    report = build_report(args.matrix, matrix, args.coverage, coverage)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.md_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    args.md_out.write_text(render_markdown(report) + "\n", encoding="utf-8")
    print(f"json: {display_path(args.json_out)}")
    print(f"md: {display_path(args.md_out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
