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
DEFAULT_TRUTH = ROOT / "tests" / "data" / "engine_benchmark_truth" / "core_matrix.v1.json"
DEFAULT_ALIASES = ROOT / "tests" / "data" / "engine_benchmark_scenarios" / "core_matrix_aliases.v1.json"
ENGINE_SURFACES = ("unreal", "unity", "godot")
CAPABILITY_MARKERS = {
    "filtering": ("filter", "reject", "malformed", "noise"),
    "latest_state": ("latest", "snapshot", "publish"),
    "replay": ("replay",),
}
CANONICAL_FILTERING_SCENARIOS = ("filter_reject_90pct", "malformed_10pct")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matrix", type=Path, default=DEFAULT_MATRIX)
    parser.add_argument("--truth", type=Path, default=DEFAULT_TRUTH)
    parser.add_argument("--aliases", type=Path, default=DEFAULT_ALIASES)
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


def _truth_index(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = payload.get("truths") if isinstance(payload.get("truths"), list) else []
    return {
        row["scenario"]: row.get("expectations") or {}
        for row in rows
        if isinstance(row, dict) and isinstance(row.get("scenario"), str)
    }


def _alias_index(payload: dict[str, Any]) -> dict[tuple[str, str], list[dict[str, Any]]]:
    rows = payload.get("aliases") if isinstance(payload.get("aliases"), list) else []
    index: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        surface = row.get("surface")
        observed = row.get("observed")
        if not isinstance(surface, str) or not isinstance(observed, str):
            continue
        index.setdefault((surface, observed), []).append(row)
    return index


def _canonical_capability_sets(truth_payload: dict[str, Any]) -> dict[str, set[str]]:
    truth_index = _truth_index(truth_payload)
    latest_state = {
        scenario
        for scenario, expectations in truth_index.items()
        if isinstance(expectations, dict) and expectations.get("latest_state_required") is True
    }
    replay = {
        scenario
        for scenario, expectations in truth_index.items()
        if isinstance(expectations, dict) and expectations.get("replay_final_transform_required") is True
    }
    return {
        "filtering": set(CANONICAL_FILTERING_SCENARIOS),
        "latest_state": latest_state,
        "replay": replay,
    }


def _capability_detail(
    *,
    surface: str,
    observed_names: list[str],
    truth_supported_names: list[str],
    alias_index: dict[tuple[str, str], list[dict[str, Any]]],
    canonical_targets: set[str],
    markers: tuple[str, ...],
) -> dict[str, Any]:
    exact = sorted(name for name in truth_supported_names if name in canonical_targets)
    alias_equivalent: set[str] = set()
    family_alignments: set[str] = set()
    aliased_observed: set[str] = set()
    for name in observed_names:
        for row in alias_index.get((surface, name), []):
            canonical = row.get("canonical")
            alignment = row.get("alignment")
            if not isinstance(canonical, str) or canonical not in canonical_targets:
                continue
            aliased_observed.add(name)
            if alignment == "equivalent":
                alias_equivalent.add(canonical)
            elif alignment == "family":
                family_alignments.add(canonical)
    heuristic = []
    for name in observed_names:
        if name in exact or name in aliased_observed:
            continue
        lowered = name.lower()
        if any(marker in lowered for marker in markers):
            heuristic.append(name)
    return {
        "covered": bool(exact or alias_equivalent or family_alignments or heuristic),
        "shared_contract_defined": bool(canonical_targets),
        "shared_contract_covered": bool(exact or alias_equivalent),
        "exact_scenarios": exact,
        "alias_equivalent_scenarios": sorted(alias_equivalent),
        "family_scenarios": sorted(family_alignments),
        "heuristic_scenarios": heuristic,
        "scenarios": sorted(dict.fromkeys(exact + sorted(alias_equivalent) + sorted(family_alignments) + heuristic)),
    }


def _surface_capability_row(
    row: dict[str, Any],
    truth_payload: dict[str, Any],
    alias_index: dict[tuple[str, str], list[dict[str, Any]]],
) -> dict[str, Any]:
    latency_rows = int(row.get("latency_rows", 0) or 0)
    runtime_metric_rows = int(row.get("runtime_metric_rows", 0) or 0)
    observed = row.get("scenarios") if isinstance(row.get("scenarios"), list) else []
    observed_names = [name for name in observed if isinstance(name, str)]
    truth_supported = (
        row.get("truth_supported_scenarios")
        if isinstance(row.get("truth_supported_scenarios"), list)
        else observed_names
    )
    truth_supported_names = [name for name in truth_supported if isinstance(name, str)]
    canonical_targets = _canonical_capability_sets(truth_payload)
    capability_rows = {
        "ingest": {
            "covered": latency_rows > 0 or runtime_metric_rows > 0,
            "shared_contract_defined": True,
            "shared_contract_covered": bool(truth_supported_names),
            "exact_scenarios": truth_supported_names,
            "alias_equivalent_scenarios": [],
            "family_scenarios": [],
            "heuristic_scenarios": [],
            "scenarios": observed_names,
        }
    }
    for capability, markers in CAPABILITY_MARKERS.items():
        capability_rows[capability] = _capability_detail(
            surface=str(row.get("surface")),
            observed_names=observed_names,
            truth_supported_names=truth_supported_names,
            alias_index=alias_index,
            canonical_targets=canonical_targets[capability],
            markers=markers,
        )
    engine_runtime = row.get("surface") in ENGINE_SURFACES and (latency_rows > 0 or runtime_metric_rows > 0)
    capability_rows["engine_runtime"] = {
        "covered": engine_runtime,
        "shared_contract_defined": False,
        "shared_contract_covered": False,
        "exact_scenarios": [],
        "alias_equivalent_scenarios": [],
        "family_scenarios": [],
        "heuristic_scenarios": [],
        "scenarios": observed_names if engine_runtime else [],
    }
    return {
        "surface": row.get("surface"),
        "surface_kind": row.get("surface_kind"),
        "path": row.get("path"),
        "capabilities": capability_rows,
    }


def build_report(
    matrix_path: Path,
    matrix: dict[str, Any],
    truth_path: Path,
    truth_payload: dict[str, Any],
    alias_path: Path,
    alias_payload: dict[str, Any],
) -> dict[str, Any]:
    alias_index = _alias_index(alias_payload)
    surface_rows = [_surface_capability_row(row, truth_payload, alias_index) for row in _surface_rows(matrix)]
    capability_summary: dict[str, dict[str, Any]] = {}
    for capability in ("ingest", "filtering", "latest_state", "replay", "engine_runtime"):
        covered_surfaces = [row["surface"] for row in surface_rows if row["capabilities"][capability]["covered"]]
        shared_contract_surfaces = [row["surface"] for row in surface_rows if row["capabilities"][capability]["shared_contract_covered"]]
        shared_contract_defined = any(row["capabilities"][capability]["shared_contract_defined"] for row in surface_rows)
        capability_summary[capability] = {
            "surface_count": len(covered_surfaces),
            "surfaces": covered_surfaces,
            "shared_contract_defined": shared_contract_defined,
            "shared_contract_surface_count": len(shared_contract_surfaces),
            "shared_contract_surfaces": shared_contract_surfaces,
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
    elif not capability_summary["replay"]["shared_contract_defined"]:
        gaps.append("no canonical truth scenario currently defines shared replay coverage")
    missing_engine_runtime = [surface for surface in ENGINE_SURFACES if surface not in engine_runtime_surfaces]
    if missing_engine_runtime:
        gaps.append("engine-runtime coverage missing for: " + ", ".join(missing_engine_runtime))

    return {
        "schema": "fastdis.benchmark_coverage_report.v1",
        "generated_at_utc": utc_now(),
        "status": status,
        "sources": {
            "matrix": display_path(matrix_path),
            "truth": display_path(truth_path),
            "aliases": display_path(alias_path),
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
            f"({', '.join(summary['surfaces']) if summary['surfaces'] else 'none'}) "
            f"shared_contract=`{summary['shared_contract_surface_count']}` "
            f"({', '.join(summary['shared_contract_surfaces']) if summary['shared_contract_surfaces'] else 'none'})"
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
    truth_payload = load_json(args.truth)
    alias_payload = load_json(args.aliases)
    report = build_report(args.matrix, matrix, args.truth, truth_payload, args.aliases, alias_payload)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.md_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    args.md_out.write_text(render_markdown(report) + "\n", encoding="utf-8")
    print(f"json: {display_path(args.json_out)}")
    print(f"md: {display_path(args.md_out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
