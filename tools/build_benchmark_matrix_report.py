#!/usr/bin/env python3
"""Aggregate shared engine benchmark and head-to-head reports into one matrix summary."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any

TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import path_compat


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = ROOT / "artifacts" / "reports" / "benchmark_matrix"
DEFAULT_HEAD_TO_HEAD_CANDIDATES = [
    [
        ROOT / "artifacts" / "reports" / "engine_head_to_head" / "unreal_vs_grill.json",
        ROOT / "artifacts" / "reports" / "engine_head_to_head" / "unreal_vs_grill.sample.json",
    ],
    [
        ROOT / "artifacts" / "reports" / "engine_head_to_head" / "unity_vs_grill.json",
    ],
]
DEFAULT_COMPETITOR_STATUS = [
    ROOT / "artifacts" / "reports" / "engine_head_to_head" / "unreal_vs_grill_status.json",
    ROOT / "artifacts" / "reports" / "engine_head_to_head" / "unity_vs_grill_status.json",
]
DEFAULT_COMPETITOR_VALIDATION = [
    ROOT / "artifacts" / "reports" / "competitor_capture_validation.json",
]
DEFAULT_COMPETITOR_SUMMARY = ROOT / "artifacts" / "reports" / "competitor_lane_summary" / "competitor_lane_summary.json"
DEFAULT_CROSS_ENGINE_EQUIVALENCE = [
    ROOT / "artifacts" / "reports" / "cross_engine_equivalence.json",
]
DEFAULT_ENGINE_REPORT_CANDIDATES = [
    [ROOT / "artifacts" / "reports" / "engine_benchmarks" / "native_engine_benchmark_report.json"],
    [ROOT / "artifacts" / "reports" / "engine_benchmarks" / "c_engine_benchmark_report.json"],
    [ROOT / "artifacts" / "reports" / "engine_benchmarks" / "cpp_engine_benchmark_report.json"],
    [ROOT / "artifacts" / "reports" / "engine_benchmarks" / "python_ctypes_engine_benchmark_report.json"],
    [
        ROOT / "artifacts" / "reports" / "engine_benchmarks" / "unreal_engine_benchmark_report.json",
        ROOT / "artifacts" / "reports" / "engine_benchmarks" / "samples" / "unreal_engine_benchmark_report.json",
    ],
    [
        ROOT / "artifacts" / "reports" / "engine_benchmarks" / "godot_engine_benchmark_report.json",
        ROOT / "artifacts" / "reports" / "engine_benchmarks" / "samples" / "godot_engine_benchmark_report.json",
    ],
    [
        ROOT / "artifacts" / "reports" / "engine_benchmarks" / "unity_engine_benchmark_report.json",
        ROOT / "artifacts" / "reports" / "engine_benchmarks" / "samples" / "unity_engine_benchmark_report.json",
    ],
]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine-report", dest="engine_reports", type=Path, action="append", help="Shared engine benchmark report path")
    parser.add_argument("--head-to-head", dest="head_to_head_reports", type=Path, action="append", help="Shared head-to-head report path")
    parser.add_argument("--competitor-status", dest="competitor_status_reports", type=Path, action="append", help="Competitor baseline status report path")
    parser.add_argument("--competitor-validation", dest="competitor_validation_reports", type=Path, action="append", help="Competitor capture validation report path")
    parser.add_argument("--competitor-summary", dest="competitor_summary_report", type=Path, help="Competitor lane summary report path")
    parser.add_argument("--cross-engine-equivalence", dest="cross_engine_equivalence_reports", type=Path, action="append", help="Shared cross-engine equivalence report path")
    parser.add_argument("--json-out", type=Path, default=DEFAULT_OUT_DIR / "benchmark_matrix.json")
    parser.add_argument("--md-out", type=Path, default=DEFAULT_OUT_DIR / "benchmark_matrix.md")
    return parser.parse_args(argv)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_json_compat(path: Path) -> tuple[Path, dict[str, Any]]:
    resolved = path_compat.resolve_existing(path)
    if resolved is None:
        raise FileNotFoundError(path)
    return resolved, load_json(resolved)


def display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def existing_paths(paths: list[Path]) -> list[Path]:
    resolved: list[Path] = []
    seen: set[Path] = set()
    for path in paths:
        candidate = path_compat.resolve_existing(path)
        if candidate is None or candidate in seen:
            continue
        seen.add(candidate)
        resolved.append(candidate)
    return resolved


def preferred_default_engine_reports() -> list[Path]:
    selected: list[Path] = []
    for candidates in DEFAULT_ENGINE_REPORT_CANDIDATES:
        for path in candidates:
            if path.exists():
                selected.append(path)
                break
    return selected


def preferred_default_head_to_head_reports() -> list[Path]:
    selected: list[Path] = []
    for candidates in DEFAULT_HEAD_TO_HEAD_CANDIDATES:
        for path in candidates:
            if path.exists():
                selected.append(path)
                break
    return selected


def classify_evidence(path: Path, payload: dict[str, Any]) -> str:
    if "/samples/" in path.as_posix() or ".sample." in path.name:
        return "sample"
    rows = payload.get("rows")
    if isinstance(rows, list) and any(isinstance(row, dict) and (row.get("truth") or {}).get("final_truth_match") is True for row in rows):
        return "measured_or_verified"
    return "measured"


def classify_head_to_head_evidence(path: Path, payload: dict[str, Any]) -> str:
    if payload.get("status") == "blocked_on_competitor":
        return "blocked"
    if "/samples/" in path.as_posix() or ".sample." in path.name:
        return "sample"
    inputs = payload.get("inputs") if isinstance(payload.get("inputs"), dict) else {}
    for key in ("left", "right"):
        value = inputs.get(key)
        if isinstance(value, str) and ("/samples/" in value or ".sample." in value):
            return "sample"
    return "measured"


def summarize_engine_report(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    rows = payload.get("rows") if isinstance(payload.get("rows"), list) else []
    truth_rows = sum(1 for row in rows if isinstance(row, dict) and isinstance(row.get("truth"), dict) and row["truth"].get("final_truth_match") is not None)
    latency_rows = sum(
        1
        for row in rows
        if isinstance(row, dict)
        and isinstance(row.get("metrics"), dict)
        and any(row["metrics"].get(key) is not None for key in ("p50_ingest_ms", "p95_ingest_ms", "p99_ingest_ms"))
    )
    runtime_metric_rows = sum(
        1
        for row in rows
        if isinstance(row, dict)
        and isinstance(row.get("metrics"), dict)
        and row["metrics"].get("runtime_elapsed_seconds") is not None
    )
    scenarios = [row["scenario"] for row in rows if isinstance(row, dict) and isinstance(row.get("scenario"), str)]
    truth_supported_scenarios = [
        row["scenario"]
        for row in rows
        if isinstance(row, dict)
        and isinstance(row.get("scenario"), str)
        and isinstance(row.get("truth"), dict)
        and row["truth"].get("final_truth_match") is True
    ]
    notes: list[str] = []
    if payload.get("surface_kind") == "engine" and latency_rows == 0 and runtime_metric_rows == 0:
        notes.append("engine lane currently has no measured latency or runtime elapsed fields")
    if truth_rows == 0:
        notes.append("no truth-match rows in this report")
    return {
        "surface": payload.get("surface"),
        "surface_kind": payload.get("surface_kind"),
        "path": display_path(path),
        "evidence_kind": classify_evidence(path, payload),
        "row_count": len(rows),
        "latency_rows": latency_rows,
        "runtime_metric_rows": runtime_metric_rows,
        "truth_rows": truth_rows,
        "scenario_count": len(scenarios),
        "scenarios": scenarios,
        "truth_supported_scenarios": truth_supported_scenarios,
        "host": payload.get("host") if isinstance(payload.get("host"), dict) else {},
        "proof_context": payload.get("proof_context") if isinstance(payload.get("proof_context"), dict) else None,
        "notes": notes,
    }


def summarize_head_to_head_report(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    comparison = payload.get("comparison") if isinstance(payload.get("comparison"), dict) else {}
    inputs = payload.get("inputs") if isinstance(payload.get("inputs"), dict) else {}
    left_surface = inputs.get("left_surface")
    right_surface = inputs.get("right_surface")
    evidence_kind = classify_head_to_head_evidence(path, payload)
    supported_claim = bool(
        evidence_kind != "sample"
        and payload.get("status") == "comparable"
        and comparison.get("same_host") is True
        and int(comparison.get("matched_scenarios", 0)) > 0
    )
    return {
        "path": display_path(path),
        "evidence_kind": evidence_kind,
        "status": payload.get("status"),
        "left_surface": left_surface,
        "right_surface": right_surface,
        "same_host": comparison.get("same_host"),
        "matched_scenarios": comparison.get("matched_scenarios"),
        "comparable_metric_rows": comparison.get("comparable_metric_rows"),
        "supported_claim": supported_claim,
        "claim_boundaries": comparison.get("claim_boundaries") if isinstance(comparison.get("claim_boundaries"), list) else [],
        "left_proof_context": inputs.get("left_proof_context") if isinstance(inputs.get("left_proof_context"), dict) else None,
        "right_proof_context": inputs.get("right_proof_context") if isinstance(inputs.get("right_proof_context"), dict) else None,
    }


def _competitor_validation_lane_index(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        report_status = row.get("status")
        for lane in row.get("lanes") if isinstance(row.get("lanes"), list) else []:
            if not isinstance(lane, dict) or not isinstance(lane.get("lane"), str):
                continue
            lane_copy = dict(lane)
            lane_copy["_report_status"] = report_status
            lane_copy["_handoff_workbench_status"] = row.get("handoff_workbench_status")
            lane_copy["_handoff_bundle_kind"] = row.get("handoff_bundle_kind")
            lane_copy["_handoff_self_describing_bundle"] = row.get("handoff_self_describing_bundle")
            index[lane["lane"]] = lane_copy
    return index


def _validation_lane_for_comparison(left_surface: Any, right_surface: Any) -> str | None:
    mapping = {
        ("unreal", "grill_unreal"): "unreal_vs_grill",
        ("unity", "grill_unity"): "unity_vs_grill",
    }
    key = (str(left_surface) if isinstance(left_surface, str) else left_surface, str(right_surface) if isinstance(right_surface, str) else right_surface)
    return mapping.get(key)


def _competitor_summary_lane_index(payload: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not isinstance(payload, dict):
        return {}
    rows = payload.get("lanes") if isinstance(payload.get("lanes"), list) else []
    return {
        row["lane"]: row
        for row in rows
        if isinstance(row, dict) and isinstance(row.get("lane"), str)
    }


def apply_competitor_validation(
    comparison_rows: list[dict[str, Any]],
    competitor_validation_rows: list[dict[str, Any]],
    competitor_summary_payload: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    lane_index = _competitor_validation_lane_index(competitor_validation_rows)
    competitor_summary_index = _competitor_summary_lane_index(competitor_summary_payload)
    adjusted: list[dict[str, Any]] = []
    for row in comparison_rows:
        lane_name = _validation_lane_for_comparison(row.get("left_surface"), row.get("right_surface"))
        if lane_name is None:
            adjusted.append(row)
            continue
        lane = lane_index.get(lane_name)
        summary_lane = competitor_summary_index.get(lane_name, {})
        claim_boundary_detail = summary_lane.get("claim_boundary") if isinstance(summary_lane.get("claim_boundary"), dict) else None
        validation_passed = bool(
            isinstance(lane, dict)
            and lane.get("present") is True
            and lane.get("error_count") == 0
            and lane.get("_report_status") == "pass"
            and lane.get("_handoff_workbench_status") == "pass"
            and lane.get("artifact_mode") in {"benchmark_capture", "blocked_evidence_only"}
        )
        updated = dict(row)
        updated["validation_lane"] = lane_name
        updated["validation_passed"] = validation_passed
        updated["supported_claim"] = bool(row.get("supported_claim") is True and validation_passed)
        updated["claim_boundary_detail"] = claim_boundary_detail
        adjusted.append(updated)
    return adjusted


def summarize_competitor_status_report(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "path": display_path(path),
        "schema": payload.get("schema"),
        "status": payload.get("status"),
        "blockers": payload.get("blockers") if isinstance(payload.get("blockers"), list) else [],
        "note": payload.get("note"),
    }


def summarize_competitor_validation_report(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    lanes = payload.get("lanes") if isinstance(payload.get("lanes"), list) else []
    handoff = payload.get("handoff_workbench") if isinstance(payload.get("handoff_workbench"), dict) else {}
    handoff_summary = handoff.get("summary") if isinstance(handoff.get("summary"), dict) else {}
    lane_rows: list[dict[str, Any]] = []
    for lane in lanes:
        if not isinstance(lane, dict) or not isinstance(lane.get("lane"), str):
            continue
        lane_rows.append(
            {
                "lane": lane["lane"],
                "present": lane.get("present"),
                "artifact_mode": lane.get("artifact_mode"),
                "shared_scenarios": lane.get("shared_scenarios") if isinstance(lane.get("shared_scenarios"), list) else [],
                "error_count": len(lane.get("errors")) if isinstance(lane.get("errors"), list) else 0,
            }
        )
    blocked_evidence_lane_count = sum(1 for lane in lane_rows if lane.get("artifact_mode") == "blocked_evidence_only")
    return {
        "path": display_path(path),
        "schema": payload.get("schema"),
        "status": payload.get("status"),
        "active_lane_count": payload.get("active_lane_count"),
        "blocked_evidence_lane_count": blocked_evidence_lane_count,
        "error_count": len(payload.get("errors")) if isinstance(payload.get("errors"), list) else 0,
        "handoff_workbench_status": handoff.get("status"),
        "handoff_bundle_kind": handoff_summary.get("bundle_kind"),
        "handoff_self_describing_bundle": handoff_summary.get("self_describing_bundle"),
        "handoff_manifest_present": handoff_summary.get("manifest_present"),
        "lanes": lane_rows,
    }


def summarize_cross_engine_equivalence_report(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    return {
        "path": display_path(path),
        "schema": payload.get("schema"),
        "status": payload.get("status"),
        "deep_complete": summary.get("deep_complete"),
        "runtime_truth_complete": summary.get("runtime_truth_complete"),
        "benchmark_contract_present": summary.get("benchmark_contract_present"),
        "gaps": payload.get("gaps") if isinstance(payload.get("gaps"), list) else [],
        "note": payload.get("note"),
    }


def build_report(
    engine_reports: list[Path],
    head_to_head_reports: list[Path],
    competitor_status_reports: list[Path] | None = None,
    competitor_validation_reports: list[Path] | None = None,
    competitor_summary_report: Path | None = None,
    cross_engine_equivalence_reports: list[Path] | None = None,
) -> dict[str, Any]:
    engine_payloads = [(path, load_json_compat(path)[1]) for path in engine_reports if path_compat.resolve_existing(path) is not None]
    head_payloads = [(path, load_json_compat(path)[1]) for path in head_to_head_reports if path_compat.resolve_existing(path) is not None]
    status_payloads = [(path, load_json_compat(path)[1]) for path in (competitor_status_reports or []) if path_compat.resolve_existing(path) is not None]
    validation_payloads = [(path, load_json_compat(path)[1]) for path in (competitor_validation_reports or []) if path_compat.resolve_existing(path) is not None]
    competitor_summary_payload = None
    if isinstance(competitor_summary_report, Path):
        resolved_competitor_summary = path_compat.resolve_existing(competitor_summary_report)
        if resolved_competitor_summary is not None:
            competitor_summary_payload = load_json(resolved_competitor_summary)
    cross_engine_payloads = [(path, load_json_compat(path)[1]) for path in (cross_engine_equivalence_reports or []) if path_compat.resolve_existing(path) is not None]

    surface_rows = [summarize_engine_report(path, payload) for path, payload in engine_payloads]
    comparison_rows = [summarize_head_to_head_report(path, payload) for path, payload in head_payloads]
    competitor_status_rows = [summarize_competitor_status_report(path, payload) for path, payload in status_payloads]
    competitor_validation_rows = [summarize_competitor_validation_report(path, payload) for path, payload in validation_payloads]
    comparison_rows = apply_competitor_validation(comparison_rows, competitor_validation_rows, competitor_summary_payload)
    cross_engine_rows = [summarize_cross_engine_equivalence_report(path, payload) for path, payload in cross_engine_payloads]

    claim_boundaries = [
        "Only head-to-head reports marked comparable with same-host evidence support direct competitor claims.",
        "Returned competitor evidence should carry a passing competitor-capture validation artifact before it is treated as publishable same-host proof.",
        "Sample artifacts demonstrate contract shape but do not support product-performance claims.",
        "Engine reports with null latency or apply-time fields are ingest/truth bridges, not full runtime benchmarks.",
        "Wall-clock runtime rows are tracked separately from ingest latency percentiles and should not be compared as parser-speed claims.",
        "Cross-engine equivalence supports consistency claims, not competitor-performance claims.",
    ]

    supported_claims = [
        row for row in comparison_rows if row["supported_claim"]
    ]
    gaps: list[str] = []
    if not any(row["surface"] == "unity" for row in surface_rows):
        gaps.append("unity shared engine benchmark report not present")
    if not any(row["surface"] == "unreal" for row in surface_rows):
        gaps.append("unreal shared engine benchmark report not present")
    if not any(row["surface"] == "godot" for row in surface_rows):
        gaps.append("godot shared engine benchmark report not present")
    if not any(row["surface"] == "native" for row in surface_rows):
        gaps.append("native benchmark report not present")
    if not any(row["surface"] == "c" for row in surface_rows):
        gaps.append("c benchmark report not present")
    if not any(row["surface"] == "cpp" for row in surface_rows):
        gaps.append("cpp benchmark report not present")
    if not any(row["surface"] == "python_ctypes" for row in surface_rows):
        gaps.append("python ctypes benchmark report not present")
    if not any(row["status"] == "complete" for row in cross_engine_rows):
        gaps.append("shared cross-engine equivalence report not complete")
    if not any(row["left_surface"] == "unreal" and row["right_surface"] == "grill_unreal" and row["supported_claim"] for row in comparison_rows):
        gaps.append("no supported unreal vs grill same-host claim yet")
    if not any(row["left_surface"] == "unity" and row["right_surface"] == "grill_unity" and row["supported_claim"] for row in comparison_rows):
        gaps.append("no supported unity vs grill same-host claim yet")
    if not competitor_validation_rows:
        gaps.append("competitor capture validation report not present")
    elif not any(row["status"] == "pass" for row in competitor_validation_rows):
        gaps.append("competitor capture validation report has not passed for any returned lane")
    elif not any(
        row["status"] == "pass"
        and row.get("handoff_workbench_status") == "pass"
        and row.get("handoff_bundle_kind") == "archive_bundle"
        and row.get("handoff_self_describing_bundle") is True
        for row in competitor_validation_rows
    ):
        gaps.append("competitor capture validation has not recorded a self-describing returned bundle")

    return {
        "schema": "fastdis.engine_benchmark_matrix.v1",
        "generated_at_utc": utc_now(),
        "summary": {
            "surface_report_count": len(surface_rows),
            "comparison_report_count": len(comparison_rows),
            "competitor_status_count": len(competitor_status_rows),
            "competitor_validation_count": len(competitor_validation_rows),
            "passing_competitor_validation_count": sum(1 for row in competitor_validation_rows if row["status"] == "pass"),
            "blocked_evidence_lane_count": sum(int(row.get("blocked_evidence_lane_count", 0)) for row in competitor_validation_rows),
            "cross_engine_equivalence_count": len(cross_engine_rows),
            "supported_competitor_claim_count": len(supported_claims),
            "sample_surface_count": sum(1 for row in surface_rows if row["evidence_kind"] == "sample"),
            "sample_comparison_count": sum(1 for row in comparison_rows if row["evidence_kind"] == "sample"),
            "complete_cross_engine_equivalence_count": sum(1 for row in cross_engine_rows if row["status"] == "complete"),
        },
        "claim_boundaries": claim_boundaries,
        "surfaces": surface_rows,
        "comparisons": comparison_rows,
        "competitor_statuses": competitor_status_rows,
        "competitor_validations": competitor_validation_rows,
        "cross_engine_equivalence": cross_engine_rows,
        "gaps": gaps,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Benchmark Matrix",
        "",
        f"- schema: `{report['schema']}`",
        f"- surface_report_count: `{report['summary']['surface_report_count']}`",
        f"- comparison_report_count: `{report['summary']['comparison_report_count']}`",
        f"- supported_competitor_claim_count: `{report['summary']['supported_competitor_claim_count']}`",
        f"- competitor_validation_count: `{report['summary']['competitor_validation_count']}`",
        f"- blocked_evidence_lane_count: `{report['summary']['blocked_evidence_lane_count']}`",
        f"- complete_cross_engine_equivalence_count: `{report['summary']['complete_cross_engine_equivalence_count']}`",
        "",
        "## Claim Boundaries",
        "",
    ]
    for note in report["claim_boundaries"]:
        lines.append(f"- {note}")
    lines.extend(["", "## Surfaces", "", "| surface | kind | evidence | rows | latency_rows | runtime_metric_rows | truth_rows | notes |", "| --- | --- | --- | --- | --- | --- | --- | --- |"])
    for row in report["surfaces"]:
        lines.append(
            f"| {row['surface']} | {row['surface_kind']} | {row['evidence_kind']} | {row['row_count']} | {row['latency_rows']} | {row['runtime_metric_rows']} | {row['truth_rows']} | {'; '.join(row['notes']) if row['notes'] else 'none'} |"
        )
    lines.extend(["", "## Comparisons", "", "| left | right | status | same_host | matched | comparable_rows | validation_lane | validation_passed | supported_claim |", "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"])
    for row in report["comparisons"]:
        lines.append(
            f"| {row['left_surface']} | {row['right_surface']} | {row['status']} | {row['same_host']} | {row['matched_scenarios']} | {row['comparable_metric_rows']} | {row.get('validation_lane', 'n/a')} | {row.get('validation_passed', 'n/a')} | {row['supported_claim']} |"
        )
        boundary = row.get("claim_boundary_detail") if isinstance(row.get("claim_boundary_detail"), dict) else {}
        if boundary.get("route_scope"):
            lines.append(f"  route_scope: {boundary['route_scope']}")
        if boundary.get("gap_summary"):
            lines.append(f"  gap_summary: {boundary['gap_summary']}")
        if boundary.get("testing_workaround"):
            lines.append(f"  testing_workaround: {boundary['testing_workaround']}")
        if boundary.get("safe_advertising_point"):
            lines.append(f"  safe_advertising_point: {boundary['safe_advertising_point']}")
        if boundary.get("non_publishable_angle"):
            lines.append(f"  non_publishable_angle: {boundary['non_publishable_angle']}")
    lines.extend(["", "## Competitor Status", ""])
    if report["competitor_statuses"]:
        for row in report["competitor_statuses"]:
            blocker_text = "; ".join(row["blockers"]) if row["blockers"] else "none"
            lines.append(f"- `{row['path']}` status=`{row['status']}` blockers=`{blocker_text}`")
    else:
        lines.append("- none")
    lines.extend(["", "## Competitor Validation", ""])
    if report["competitor_validations"]:
        for row in report["competitor_validations"]:
            lines.append(
                f"- `{row['path']}` status=`{row['status']}` active_lane_count=`{row['active_lane_count']}` blocked_evidence_lane_count=`{row.get('blocked_evidence_lane_count')}` error_count=`{row['error_count']}` handoff_workbench_status=`{row.get('handoff_workbench_status')}` bundle_kind=`{row.get('handoff_bundle_kind')}` self_describing_bundle=`{row.get('handoff_self_describing_bundle')}`"
            )
            lanes = row.get("lanes") if isinstance(row.get("lanes"), list) else []
            for lane in lanes:
                if not isinstance(lane, dict):
                    continue
                lines.append(
                    f"  lane `{lane.get('lane')}` present=`{lane.get('present')}` artifact_mode=`{lane.get('artifact_mode')}` shared_scenarios=`{', '.join(lane.get('shared_scenarios', [])) if isinstance(lane.get('shared_scenarios'), list) and lane.get('shared_scenarios') else 'none'}` error_count=`{lane.get('error_count')}`"
                )
    else:
        lines.append("- none")
    lines.extend(["", "## Cross-Engine Equivalence", ""])
    if report["cross_engine_equivalence"]:
        for row in report["cross_engine_equivalence"]:
            gap_text = "; ".join(row["gaps"]) if row["gaps"] else "none"
            lines.append(
                f"- `{row['path']}` status=`{row['status']}` deep_complete=`{row['deep_complete']}` runtime_truth_complete=`{row['runtime_truth_complete']}` gaps=`{gap_text}`"
            )
    else:
        lines.append("- none")
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
    engine_reports = existing_paths(args.engine_reports) if args.engine_reports else preferred_default_engine_reports()
    head_to_head_reports = existing_paths(args.head_to_head_reports) if args.head_to_head_reports else preferred_default_head_to_head_reports()
    competitor_status_reports = existing_paths(args.competitor_status_reports or DEFAULT_COMPETITOR_STATUS)
    competitor_validation_reports = existing_paths(args.competitor_validation_reports or DEFAULT_COMPETITOR_VALIDATION)
    competitor_summary_report = args.competitor_summary_report or DEFAULT_COMPETITOR_SUMMARY
    cross_engine_equivalence_reports = existing_paths(args.cross_engine_equivalence_reports or DEFAULT_CROSS_ENGINE_EQUIVALENCE)
    report = build_report(
        engine_reports,
        head_to_head_reports,
        competitor_status_reports,
        competitor_validation_reports,
        competitor_summary_report,
        cross_engine_equivalence_reports,
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
