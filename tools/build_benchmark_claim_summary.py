#!/usr/bin/env python3
"""Build a publication-oriented claim summary from current benchmark artifacts."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = ROOT / "build" / "reports" / "benchmark_claim_summary"
DEFAULT_MATRIX = ROOT / "build" / "reports" / "benchmark_matrix" / "benchmark_matrix.json"
DEFAULT_COVERAGE = ROOT / "build" / "reports" / "benchmark_coverage" / "benchmark_coverage_report.json"
DEFAULT_AUDIT = ROOT / "build" / "reports" / "benchmark_completion_audit" / "benchmark_completion_audit.json"
DEFAULT_COMPETITOR_SUMMARY = ROOT / "build" / "reports" / "competitor_lane_summary" / "competitor_lane_summary.json"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matrix", type=Path, default=DEFAULT_MATRIX)
    parser.add_argument("--coverage", type=Path, default=DEFAULT_COVERAGE)
    parser.add_argument("--audit", type=Path, default=DEFAULT_AUDIT)
    parser.add_argument("--competitor-summary", type=Path, default=DEFAULT_COMPETITOR_SUMMARY)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_OUT_DIR / "benchmark_claim_summary.json")
    parser.add_argument("--md-out", type=Path, default=DEFAULT_OUT_DIR / "benchmark_claim_summary.md")
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


def _comparison_label(row: dict[str, Any]) -> str:
    return f"{row.get('left_surface')} vs {row.get('right_surface')}"


def _requirement_index(audit: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = audit.get("requirements") if isinstance(audit.get("requirements"), list) else []
    return {
        row["id"]: row
        for row in rows
        if isinstance(row, dict) and isinstance(row.get("id"), str)
    }


def _blocked_validation_lane_index(matrix: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = matrix.get("competitor_validations") if isinstance(matrix.get("competitor_validations"), list) else []
    index: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        for lane in row.get("lanes") if isinstance(row.get("lanes"), list) else []:
            if isinstance(lane, dict) and isinstance(lane.get("lane"), str):
                index[lane["lane"]] = lane
    return index


def _competitor_lane_index(summary: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = summary.get("lanes") if isinstance(summary.get("lanes"), list) else []
    return {
        row["lane"]: row
        for row in rows
        if isinstance(row, dict) and isinstance(row.get("lane"), str)
    }


def _lane_claim(lane_name: str) -> str:
    if lane_name == "unreal_vs_grill":
        return "Honest same-host Unreal FastDIS-vs-GRILL head-to-head report"
    if lane_name == "unity_vs_grill":
        return "Honest same-host Unity FastDIS-vs-GRILL head-to-head report"
    return lane_name


def build_report(
    matrix_path: Path,
    matrix: dict[str, Any],
    coverage_path: Path,
    coverage: dict[str, Any],
    audit_path: Path,
    audit: dict[str, Any],
    competitor_summary_path: Path,
    competitor_summary: dict[str, Any],
) -> dict[str, Any]:
    requirement_index = _requirement_index(audit)
    blocked_validation_lanes = _blocked_validation_lane_index(matrix)
    competitor_lane_index = _competitor_lane_index(competitor_summary)
    surfaces = matrix.get("surfaces") if isinstance(matrix.get("surfaces"), list) else []
    comparisons = matrix.get("comparisons") if isinstance(matrix.get("comparisons"), list) else []
    supported_claims = [row for row in comparisons if isinstance(row, dict) and row.get("supported_claim") is True]
    measured_competitor_lanes = {
        lane_name: lane
        for lane_name, lane in competitor_lane_index.items()
        if isinstance(lane, dict) and lane.get("current_state") == "measured_claim_ready"
    }

    measured_surfaces: list[dict[str, Any]] = []
    for row in surfaces:
        if not isinstance(row, dict) or not isinstance(row.get("surface"), str):
            continue
        measured_surfaces.append(
            {
                "surface": row["surface"],
                "surface_kind": row.get("surface_kind"),
                "evidence_kind": row.get("evidence_kind"),
                "row_count": row.get("row_count"),
                "runtime_capable": bool(int(row.get("latency_rows", 0)) > 0 or int(row.get("runtime_metric_rows", 0)) > 0),
                "truth_capable": bool(int(row.get("truth_rows", 0)) > 0),
                "path": row.get("path"),
            }
        )

    publishable_today: list[dict[str, Any]] = []
    if requirement_index.get("shared_contract", {}).get("status") == "complete":
        publishable_today.append(
            {
                "claim": "FastDIS publishes shared benchmark reports across native, C, C++, Python, Unreal, Unity, and Godot under one contract.",
                "evidence": [display_path(matrix_path), display_path(coverage_path), display_path(audit_path)],
            }
        )
    if requirement_index.get("ingest_filter_latest_state", {}).get("status") == "complete":
        publishable_today.append(
            {
                "claim": "FastDIS publishes reproducible ingest, filtering, and latest-state benchmark evidence across the shared benchmark surfaces.",
                "evidence": [display_path(coverage_path), display_path(audit_path)],
            }
        )
    if requirement_index.get("replay_reports", {}).get("status") == "complete":
        publishable_today.append(
            {
                "claim": "FastDIS publishes explicit replay benchmark coverage in its shared benchmark reports.",
                "evidence": [display_path(coverage_path), display_path(audit_path)],
            }
        )
    if requirement_index.get("cross_engine_equivalence", {}).get("status") == "complete":
        publishable_today.append(
            {
                "claim": "FastDIS publishes cross-engine equivalence evidence for consistency claims across its supported surfaces.",
                "evidence": [display_path(audit_path)],
            }
        )
    if requirement_index.get("engine_runtime_reports", {}).get("status") == "complete":
        publishable_today.append(
            {
                "claim": "FastDIS publishes measured engine-runtime benchmark reports for Unreal, Unity, and Godot.",
                "evidence": [display_path(audit_path)],
            }
        )
    for row in supported_claims:
        publishable_today.append(
            {
                "claim": f"FastDIS publishes a supported same-host direct competitor claim for {_comparison_label(row)}.",
                "evidence": [str(row.get("path"))] if isinstance(row.get("path"), str) else [display_path(matrix_path)],
            }
        )
    existing_publishable_claims = {row["claim"] for row in publishable_today if isinstance(row, dict) and isinstance(row.get("claim"), str)}
    for lane_name, lane in measured_competitor_lanes.items():
        claim = _lane_claim(lane_name)
        if claim in existing_publishable_claims:
            continue
        baseline = lane.get("baseline_status") if isinstance(lane.get("baseline_status"), dict) else {}
        comparison = lane.get("comparison") if isinstance(lane.get("comparison"), dict) else {}
        evidence = []
        if isinstance(comparison.get("path"), str):
            evidence.append(str(comparison["path"]))
        if isinstance(baseline.get("path"), str):
            evidence.append(str(baseline["path"]))
        publishable_today.append(
            {
                "claim": claim,
                "evidence": evidence or [display_path(competitor_summary_path)],
            }
        )

    not_publishable_yet: list[dict[str, Any]] = []
    shared_contract = requirement_index.get("shared_contract")
    if isinstance(shared_contract, dict) and shared_contract.get("status") != "complete":
        shared_contract_gaps = shared_contract.get("gaps") if isinstance(shared_contract.get("gaps"), list) else []
        family_overlap_present = any("canonical scenario families" in str(gap) for gap in shared_contract_gaps)
        not_publishable_yet.append(
            {
                "claim": "FastDIS publishes one canonical shared benchmark scenario contract across native, C, C++, Python, Unreal, Unity, and Godot.",
                "status": shared_contract.get("status"),
                "gaps": shared_contract_gaps,
                "evidence": shared_contract.get("evidence") if isinstance(shared_contract.get("evidence"), list) else [],
                "blocked_evidence_available": False,
                "route_scope": None,
                "gap_summary": (
                    "The shared report family exists, and some surfaces now overlap canonical scenario families, "
                    "but the canonical scenario suite is not yet carried under stable shared scenario names across every required surface."
                    if family_overlap_present
                    else "The shared report family exists, but the canonical scenario suite is not yet carried under stable shared scenario names across every required surface."
                ),
                "testing_workaround": "Normalize or rerun each surface against the canonical scenario suite so the shared scenario names appear directly in the benchmark matrix.",
                "safe_advertising_point": (
                    "FastDIS already publishes shared report, truth, claim-boundary infrastructure, and some documented scenario-family overlap even though canonical scenario-name alignment is still incomplete."
                    if family_overlap_present
                    else "FastDIS already publishes shared report, truth, and claim-boundary infrastructure even though canonical scenario-name alignment is still incomplete."
                ),
                "non_publishable_angle": "Do not claim full canonical shared-scenario contract completion across every required surface yet.",
            }
        )
    for requirement_id in ("unreal_competitor", "unity_competitor"):
        requirement = requirement_index.get(requirement_id)
        if not isinstance(requirement, dict) or requirement.get("status") == "complete":
            continue
        lane_name = "unreal_vs_grill" if requirement_id == "unreal_competitor" else "unity_vs_grill"
        competitor_lane = competitor_lane_index.get(lane_name, {})
        if isinstance(competitor_lane, dict) and competitor_lane.get("current_state") == "measured_claim_ready":
            continue
        lane = blocked_validation_lanes.get(lane_name, {})
        claim_boundary = competitor_lane.get("claim_boundary") if isinstance(competitor_lane.get("claim_boundary"), dict) else {}
        not_publishable_yet.append(
            {
                "claim": requirement.get("title"),
                "status": requirement.get("status"),
                "gaps": requirement.get("gaps") if isinstance(requirement.get("gaps"), list) else [],
                "evidence": requirement.get("evidence") if isinstance(requirement.get("evidence"), list) else [],
                "blocked_evidence_available": lane.get("artifact_mode") == "blocked_evidence_only",
                "route_scope": claim_boundary.get("route_scope"),
                "gap_summary": claim_boundary.get("gap_summary"),
                "testing_workaround": claim_boundary.get("testing_workaround"),
                "safe_advertising_point": claim_boundary.get("safe_advertising_point"),
                "non_publishable_angle": claim_boundary.get("non_publishable_angle"),
            }
        )

    claim_boundaries = matrix.get("claim_boundaries") if isinstance(matrix.get("claim_boundaries"), list) else []
    next_steps = audit.get("next_steps") if isinstance(audit.get("next_steps"), list) else []

    return {
        "schema": "fastdis.benchmark_claim_summary.v1",
        "generated_at_utc": utc_now(),
        "status": "publishable_partial" if not_publishable_yet else "publishable_complete",
        "sources": {
            "matrix": display_path(matrix_path),
            "coverage": display_path(coverage_path),
            "audit": display_path(audit_path),
            "competitor_summary": display_path(competitor_summary_path),
        },
        "summary": {
            "publishable_claim_count": len(publishable_today),
            "blocked_claim_count": len(not_publishable_yet),
            "blocked_evidence_lane_count": int(matrix.get("summary", {}).get("blocked_evidence_lane_count", 0)) if isinstance(matrix.get("summary"), dict) else 0,
            "measured_surface_count": len(measured_surfaces),
            "supported_competitor_claim_count": len({*(row.get("right_surface") for row in supported_claims if isinstance(row, dict)), *measured_competitor_lanes.keys()}),
        },
        "publishable_today": publishable_today,
        "not_publishable_yet": not_publishable_yet,
        "measured_surfaces": measured_surfaces,
        "claim_boundaries": claim_boundaries,
        "next_steps": next_steps,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Benchmark Claim Summary",
        "",
        f"- schema: `{report['schema']}`",
        f"- status: `{report['status']}`",
        f"- publishable_claim_count: `{report['summary']['publishable_claim_count']}`",
        f"- blocked_claim_count: `{report['summary']['blocked_claim_count']}`",
        f"- blocked_evidence_lane_count: `{report['summary']['blocked_evidence_lane_count']}`",
        f"- supported_competitor_claim_count: `{report['summary']['supported_competitor_claim_count']}`",
        "",
        "## Publishable Today",
        "",
    ]
    if report["publishable_today"]:
        for row in report["publishable_today"]:
            lines.append(f"- {row['claim']}")
            evidence = row.get("evidence") if isinstance(row.get("evidence"), list) else []
            if evidence:
                lines.append(f"  evidence: {', '.join(f'`{item}`' for item in evidence)}")
    else:
        lines.append("- none")
    lines.extend(["", "## Not Publishable Yet", ""])
    if report["not_publishable_yet"]:
        for row in report["not_publishable_yet"]:
            lines.append(f"- {row['claim']} status=`{row['status']}`")
            gaps = row.get("gaps") if isinstance(row.get("gaps"), list) else []
            if gaps:
                lines.append(f"  gaps: {'; '.join(str(item) for item in gaps)}")
            if row.get("blocked_evidence_available") is True:
                lines.append("  blocked_evidence_available: true")
            if row.get("route_scope"):
                lines.append(f"  route_scope: {row['route_scope']}")
            if row.get("gap_summary"):
                lines.append(f"  gap_summary: {row['gap_summary']}")
            if row.get("testing_workaround"):
                lines.append(f"  testing_workaround: {row['testing_workaround']}")
            if row.get("safe_advertising_point"):
                lines.append(f"  safe_advertising_point: {row['safe_advertising_point']}")
            if row.get("non_publishable_angle"):
                lines.append(f"  non_publishable_angle: {row['non_publishable_angle']}")
    else:
        lines.append("- none")
    lines.extend(["", "## Claim Boundaries", ""])
    for row in report["claim_boundaries"]:
        lines.append(f"- {row}")
    lines.extend(["", "## Next Steps", ""])
    if report["next_steps"]:
        for row in report["next_steps"]:
            lines.append(f"- {row}")
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    matrix = load_json(args.matrix)
    coverage = load_json(args.coverage)
    audit = load_json(args.audit)
    competitor_summary = load_json(args.competitor_summary)
    report = build_report(
        args.matrix,
        matrix,
        args.coverage,
        coverage,
        args.audit,
        audit,
        args.competitor_summary,
        competitor_summary,
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
