#!/usr/bin/env python3
"""Build a capability coverage summary from the shared benchmark matrix."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = ROOT / "build" / "reports" / "benchmark_coverage"
DEFAULT_MATRIX = ROOT / "build" / "reports" / "benchmark_matrix" / "benchmark_matrix.json"
ENGINE_SURFACES = ("unreal", "unity", "godot")
CAPABILITY_MARKERS = {
    "filtering": ("filter", "reject", "malformed", "noise"),
    "latest_state": ("latest", "snapshot", "publish"),
    "replay": ("replay",),
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matrix", type=Path, default=DEFAULT_MATRIX)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_OUT_DIR / "benchmark_coverage_report.json")
    parser.add_argument("--md-out", type=Path, default=DEFAULT_OUT_DIR / "benchmark_coverage_report.md")
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


def _surface_rows(matrix: dict[str, Any]) -> list[dict[str, Any]]:
    rows = matrix.get("surfaces") if isinstance(matrix.get("surfaces"), list) else []
    return [row for row in rows if isinstance(row, dict) and isinstance(row.get("surface"), str)]


def _matching_scenarios(row: dict[str, Any], markers: tuple[str, ...]) -> list[str]:
    scenarios = row.get("scenarios") if isinstance(row.get("scenarios"), list) else []
    matched: list[str] = []
    for scenario in scenarios:
        if not isinstance(scenario, str):
            continue
        lowered = scenario.lower()
        if any(marker in lowered for marker in markers):
            matched.append(scenario)
    return matched


def _surface_capability_row(row: dict[str, Any]) -> dict[str, Any]:
    latency_rows = int(row.get("latency_rows", 0) or 0)
    runtime_metric_rows = int(row.get("runtime_metric_rows", 0) or 0)
    capability_rows = {
        "ingest": {
            "covered": latency_rows > 0 or runtime_metric_rows > 0,
            "scenarios": row.get("scenarios") if isinstance(row.get("scenarios"), list) else [],
        }
    }
    for capability, markers in CAPABILITY_MARKERS.items():
        scenarios = _matching_scenarios(row, markers)
        capability_rows[capability] = {
            "covered": bool(scenarios),
            "scenarios": scenarios,
        }
    engine_runtime = row.get("surface") in ENGINE_SURFACES and (latency_rows > 0 or runtime_metric_rows > 0)
    capability_rows["engine_runtime"] = {
        "covered": engine_runtime,
        "scenarios": row.get("scenarios") if engine_runtime and isinstance(row.get("scenarios"), list) else [],
    }
    return {
        "surface": row.get("surface"),
        "surface_kind": row.get("surface_kind"),
        "path": row.get("path"),
        "capabilities": capability_rows,
    }


def build_report(matrix_path: Path, matrix: dict[str, Any]) -> dict[str, Any]:
    surface_rows = [_surface_capability_row(row) for row in _surface_rows(matrix)]
    capability_summary: dict[str, dict[str, Any]] = {}
    for capability in ("ingest", "filtering", "latest_state", "replay", "engine_runtime"):
        covered_surfaces = [row["surface"] for row in surface_rows if row["capabilities"][capability]["covered"]]
        capability_summary[capability] = {
            "surface_count": len(covered_surfaces),
            "surfaces": covered_surfaces,
        }

    engine_runtime_surfaces = capability_summary["engine_runtime"]["surfaces"]
    status = "complete" if (
        capability_summary["ingest"]["surface_count"] >= 4
        and capability_summary["filtering"]["surface_count"] >= 1
        and capability_summary["latest_state"]["surface_count"] >= 1
        and capability_summary["replay"]["surface_count"] >= 1
        and all(surface in engine_runtime_surfaces for surface in ENGINE_SURFACES)
    ) else "partial"

    gaps: list[str] = []
    if capability_summary["ingest"]["surface_count"] < 4:
        gaps.append("shared ingest coverage does not yet reach native, C, C++, and Python together")
    if capability_summary["filtering"]["surface_count"] == 0:
        gaps.append("no shared benchmark surface currently exposes explicit filtering or malformed-traffic scenarios")
    if capability_summary["latest_state"]["surface_count"] == 0:
        gaps.append("no shared benchmark surface currently exposes explicit latest-state or snapshot scenarios")
    if capability_summary["replay"]["surface_count"] == 0:
        gaps.append("no shared benchmark surface currently exposes explicit replay scenarios")
    missing_engine_runtime = [surface for surface in ENGINE_SURFACES if surface not in engine_runtime_surfaces]
    if missing_engine_runtime:
        gaps.append("engine-runtime coverage missing for: " + ", ".join(missing_engine_runtime))

    return {
        "schema": "fastdis.benchmark_coverage_report.v1",
        "generated_at_utc": utc_now(),
        "status": status,
        "sources": {
            "matrix": display_path(matrix_path),
        },
        "summary": capability_summary,
        "surfaces": surface_rows,
        "gaps": gaps,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Benchmark Coverage Report",
        "",
        f"- schema: `{report['schema']}`",
        f"- status: `{report['status']}`",
        "",
        "## Summary",
        "",
    ]
    for capability, summary in report["summary"].items():
        lines.append(
            f"- {capability}: surfaces=`{summary['surface_count']}` "
            f"({', '.join(summary['surfaces']) if summary['surfaces'] else 'none'})"
        )
    lines.extend(["", "## Surface Coverage", "", "| surface | ingest | filtering | latest_state | replay | engine_runtime |", "| --- | --- | --- | --- | --- | --- |"])
    for row in report["surfaces"]:
        caps = row["capabilities"]
        lines.append(
            f"| {row['surface']} | {caps['ingest']['covered']} | {caps['filtering']['covered']} | "
            f"{caps['latest_state']['covered']} | {caps['replay']['covered']} | {caps['engine_runtime']['covered']} |"
        )
    lines.extend(["", "## Gaps", ""])
    if report["gaps"]:
        for gap in report["gaps"]:
            lines.append(f"- {gap}")
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    matrix = load_json(args.matrix)
    report = build_report(args.matrix, matrix)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.md_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    args.md_out.write_text(render_markdown(report) + "\n", encoding="utf-8")
    print(f"json: {display_path(args.json_out)}")
    print(f"md: {display_path(args.md_out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
