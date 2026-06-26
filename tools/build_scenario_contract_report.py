#!/usr/bin/env python3
"""Summarize coverage of the canonical shared benchmark scenario contract."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = ROOT / "build" / "reports" / "scenario_contract"
DEFAULT_MATRIX = ROOT / "build" / "reports" / "benchmark_matrix" / "benchmark_matrix.json"
DEFAULT_SCENARIOS = ROOT / "tests" / "data" / "engine_benchmark_scenarios" / "core_matrix.v1.json"
DEFAULT_ALIASES = ROOT / "tests" / "data" / "engine_benchmark_scenarios" / "core_matrix_aliases.v1.json"
REQUIRED_SURFACES = ("native", "c", "cpp", "python_ctypes", "unreal", "unity", "godot")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matrix", type=Path, default=DEFAULT_MATRIX)
    parser.add_argument("--scenarios", type=Path, default=DEFAULT_SCENARIOS)
    parser.add_argument("--aliases", type=Path, default=DEFAULT_ALIASES)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_OUT_DIR / "scenario_contract_report.json")
    parser.add_argument("--md-out", type=Path, default=DEFAULT_OUT_DIR / "scenario_contract_report.md")
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


def _surface_index(matrix: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = matrix.get("surfaces") if isinstance(matrix.get("surfaces"), list) else []
    return {
        row["surface"]: row
        for row in rows
        if isinstance(row, dict) and isinstance(row.get("surface"), str)
    }


def _alias_index(alias_payload: dict[str, Any]) -> dict[tuple[str, str], list[dict[str, Any]]]:
    aliases = alias_payload.get("aliases") if isinstance(alias_payload.get("aliases"), list) else []
    index: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in aliases:
        if not isinstance(row, dict):
            continue
        surface = row.get("surface")
        observed = row.get("observed")
        canonical = row.get("canonical")
        if not isinstance(surface, str) or not isinstance(observed, str) or not isinstance(canonical, str):
            continue
        index.setdefault((surface, observed), []).append(row)
    return index


def _canonical_alias_names(entries: list[dict[str, Any]], *, alignment: str) -> list[str]:
    names = {
        row["canonical"]
        for row in entries
        if isinstance(row.get("canonical"), str) and row.get("alignment") == alignment
    }
    return sorted(names)


def build_report(
    matrix_path: Path,
    matrix: dict[str, Any],
    scenario_path: Path,
    scenario_payload: dict[str, Any],
    alias_path: Path,
    alias_payload: dict[str, Any],
) -> dict[str, Any]:
    surface_index = _surface_index(matrix)
    alias_index = _alias_index(alias_payload)
    canonical_rows = scenario_payload.get("scenarios") if isinstance(scenario_payload.get("scenarios"), list) else []
    canonical_names = [row["name"] for row in canonical_rows if isinstance(row, dict) and isinstance(row.get("name"), str)]
    canonical_set = set(canonical_names)
    surfaces: list[dict[str, Any]] = []
    direct_surface_count = 0
    equivalent_surface_count = 0
    family_surface_count = 0

    for surface_name in REQUIRED_SURFACES:
        matrix_row = surface_index.get(surface_name, {})
        observed = matrix_row.get("scenarios") if isinstance(matrix_row.get("scenarios"), list) else []
        observed_names = [name for name in observed if isinstance(name, str)]
        truth_supported = (
            matrix_row.get("truth_supported_scenarios")
            if isinstance(matrix_row.get("truth_supported_scenarios"), list)
            else None
        )
        observed_exact_matches = [name for name in canonical_names if name in observed_names]
        exact_source = [
            name for name in truth_supported if isinstance(name, str)
        ] if truth_supported is not None else observed_names
        exact_matches = sorted(name for name in exact_source if name in canonical_set)
        alias_entries = [row for name in observed_names for row in alias_index.get((surface_name, name), [])]
        equivalent_matches = _canonical_alias_names(alias_entries, alignment="equivalent")
        family_matches = _canonical_alias_names(alias_entries, alignment="family")
        status = "missing"
        if observed_names:
            if exact_matches:
                status = "full" if len(exact_matches) == len(canonical_names) else "partial"
            elif observed_exact_matches:
                status = "canonical_present_unverified"
            elif equivalent_matches:
                status = "alias_equivalent"
            elif family_matches:
                status = "family_aligned"
            else:
                status = "bridge_only"
        if exact_matches:
            direct_surface_count += 1
        if equivalent_matches:
            equivalent_surface_count += 1
        if family_matches:
            family_surface_count += 1
        surfaces.append(
            {
                "surface": surface_name,
                "status": status,
                "observed_scenario_count": len(observed_names),
                "canonical_observed_match_count": len(observed_exact_matches),
                "canonical_observed_matches": observed_exact_matches,
                "canonical_match_count": len(exact_matches),
                "canonical_matches": exact_matches,
                "alias_equivalent_match_count": len(equivalent_matches),
                "alias_equivalent_matches": equivalent_matches,
                "family_alignment_count": len(family_matches),
                "family_alignments": family_matches,
                "observed_only": sorted(
                    name
                    for name in observed_names
                    if name not in canonical_set and (surface_name, name) not in alias_index
                ),
                "alias_details": [
                    {
                        "observed": name,
                        "canonical": row["canonical"],
                        "alignment": row.get("alignment"),
                        "reason": row.get("reason"),
                    }
                    for name in observed_names
                    for row in alias_index.get((surface_name, name), [])
                    if isinstance(row.get("canonical"), str)
                ],
            }
        )

    all_surface_shared = sorted(
        set.intersection(
            *[
                set(row["canonical_matches"])
                for row in surfaces
                if row["status"] not in {"missing"}
            ]
        )
    ) if surfaces and all(row["status"] != "missing" for row in surfaces) else []

    status = "complete" if len(all_surface_shared) == len(canonical_names) and direct_surface_count == len(REQUIRED_SURFACES) else "partial"
    gaps: list[str] = []
    for row in surfaces:
        if row["status"] == "missing":
            gaps.append(f"{row['surface']} has no current benchmark scenarios in the matrix")
        elif row["status"] == "bridge_only":
            gaps.append(f"{row['surface']} exposes benchmark rows, but none of them use canonical shared scenario names yet")
        elif row["status"] == "family_aligned":
            gaps.append(
                f"{row['surface']} overlaps {row['family_alignment_count']} canonical scenario families, but does not yet publish exact shared scenario names"
            )
        elif row["status"] == "canonical_present_unverified":
            gaps.append(
                f"{row['surface']} publishes {row['canonical_observed_match_count']} exact canonical scenario names, but none of them are currently truth-supported in the shared report"
            )
        elif row["status"] == "alias_equivalent":
            gaps.append(
                f"{row['surface']} has alias-equivalent scenario coverage, but still needs canonical shared scenario names for full contract completion"
            )
        elif row["status"] == "partial":
            gaps.append(f"{row['surface']} only covers {row['canonical_match_count']} of {len(canonical_names)} canonical scenarios")
    if not all_surface_shared:
        gaps.append("no canonical scenario name is currently shared across every required surface")

    return {
        "schema": "fastdis.scenario_contract_report.v1",
        "generated_at_utc": utc_now(),
        "status": status,
        "sources": {
            "matrix": display_path(matrix_path),
            "scenario_contract": display_path(scenario_path),
            "scenario_aliases": display_path(alias_path),
        },
        "summary": {
            "required_surface_count": len(REQUIRED_SURFACES),
            "canonical_scenario_count": len(canonical_names),
            "canonical_covered_surface_count": direct_surface_count,
            "alias_equivalent_surface_count": equivalent_surface_count,
            "family_aligned_surface_count": family_surface_count,
            "all_surface_shared_scenario_count": len(all_surface_shared),
        },
        "canonical_scenarios": canonical_names,
        "all_surface_shared_scenarios": all_surface_shared,
        "surfaces": surfaces,
        "gaps": gaps,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Scenario Contract Report",
        "",
        f"- schema: `{report['schema']}`",
        f"- status: `{report['status']}`",
        f"- canonical_scenario_count: `{report['summary']['canonical_scenario_count']}`",
        f"- canonical_covered_surface_count: `{report['summary']['canonical_covered_surface_count']}`",
        f"- alias_equivalent_surface_count: `{report['summary']['alias_equivalent_surface_count']}`",
        f"- family_aligned_surface_count: `{report['summary']['family_aligned_surface_count']}`",
        f"- all_surface_shared_scenario_count: `{report['summary']['all_surface_shared_scenario_count']}`",
        "",
        "| surface | status | observed | canonical_matches | alias_equivalent | family_aligned |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in report["surfaces"]:
        lines.append(
            f"| {row['surface']} | {row['status']} | {row['observed_scenario_count']} | {row['canonical_match_count']} | {row['alias_equivalent_match_count']} | {row['family_alignment_count']} |"
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
    report = build_report(
        args.matrix,
        load_json(args.matrix),
        args.scenarios,
        load_json(args.scenarios),
        args.aliases,
        load_json(args.aliases),
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.md_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    args.md_out.write_text(render_markdown(report) + "\n", encoding="utf-8")
    print(f"json: {display_path(args.json_out)}")
    print(f"md: {display_path(args.md_out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
