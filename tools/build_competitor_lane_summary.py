#!/usr/bin/env python3
"""Build a concise competitor lane summary from current benchmark artifacts."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = ROOT / "build" / "reports" / "competitor_lane_summary"
DEFAULT_MATRIX = ROOT / "build" / "reports" / "benchmark_matrix" / "benchmark_matrix.json"
DEFAULT_VALIDATION = ROOT / "build" / "reports" / "competitor_capture_validation.json"
DEFAULT_CLAIM_SUMMARY = ROOT / "build" / "reports" / "benchmark_claim_summary" / "benchmark_claim_summary.json"
DEFAULT_STATUS_REPORTS = {
    "unreal_vs_grill": ROOT / "build" / "reports" / "engine_head_to_head" / "unreal_vs_grill_status.json",
    "unity_vs_grill": ROOT / "build" / "reports" / "engine_head_to_head" / "unity_vs_grill_status.json",
}
LANE_COMPARISON_KEYS = {
    "unreal_vs_grill": ("unreal", "grill_unreal"),
    "unity_vs_grill": ("unity", "grill_unity"),
}

LANE_ROUTE_GUIDANCE = {
    "unreal_vs_grill": {
        "route_scope": "current public GRILL Unreal source route",
        "blocked_gap_summary": "The current public GRILL Unreal route is source-available but Windows-only on the checked-in plugin path.",
        "testing_workaround": "Capture GRILL Unreal on a Windows host, or keep a private Mac/Linux port clearly labeled as internal-only research.",
        "safe_advertising_point": "FastDIS publishes route-scoped failure evidence and broader host/build proof, while the current public GRILL Unreal route remains Windows-only.",
        "non_publishable_angle": "Do not claim direct Unreal head-to-head performance wins until a same-host GRILL capture exists.",
    },
    "unity_vs_grill": {
        "route_scope": "current public GRILL Unity source/package route",
        "blocked_gap_summary": "The current public GRILL Unity route is source-available but import-blocked on the current Mac host and Unity editor combination.",
        "testing_workaround": "Capture GRILL Unity on a Unity host/editor combination that successfully imports the public plugin or example project.",
        "safe_advertising_point": "FastDIS publishes install smoke and failure artifacts for competitor routes instead of hand-waving over importability gaps.",
        "non_publishable_angle": "Do not claim direct Unity head-to-head performance wins until a same-host or clearly comparable-host GRILL capture exists.",
    },
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matrix", type=Path, default=DEFAULT_MATRIX)
    parser.add_argument("--validation", type=Path, default=DEFAULT_VALIDATION)
    parser.add_argument("--claim-summary", type=Path, default=DEFAULT_CLAIM_SUMMARY)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_OUT_DIR / "competitor_lane_summary.json")
    parser.add_argument("--md-out", type=Path, default=DEFAULT_OUT_DIR / "competitor_lane_summary.md")
    return parser.parse_args(argv)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_optional_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    return load_json(path)


def display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _comparison_index(matrix: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = matrix.get("comparisons") if isinstance(matrix.get("comparisons"), list) else []
    index: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        for lane, key in LANE_COMPARISON_KEYS.items():
            if row.get("left_surface") == key[0] and row.get("right_surface") == key[1]:
                index[lane] = row
    return index


def _validation_index(validation: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = validation.get("lanes") if isinstance(validation.get("lanes"), list) else []
    return {
        row["lane"]: row
        for row in rows
        if isinstance(row, dict) and isinstance(row.get("lane"), str)
    }


def _status_payload(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    return load_json(path)


def _lane_state(comparison: dict[str, Any] | None, validation_lane: dict[str, Any] | None, status_payload: dict[str, Any] | None) -> str:
    if isinstance(status_payload, dict):
        if status_payload.get("status") == "ready":
            head_to_head = status_payload.get("head_to_head_readiness") if isinstance(status_payload.get("head_to_head_readiness"), dict) else {}
            if head_to_head.get("status") == "comparable":
                return "measured_claim_ready"
    if isinstance(comparison, dict) and comparison.get("supported_claim") is True:
        return "measured_claim_ready"
    if isinstance(validation_lane, dict) and validation_lane.get("artifact_mode") == "blocked_evidence_only":
        return "blocked_evidence_only"
    if isinstance(status_payload, dict) and status_payload.get("status") == "blocked_on_grill_baseline":
        return "blocked_on_competitor"
    return "missing_or_unverified"


def _claim_boundary(lane_name: str, current_state: str) -> dict[str, Any]:
    return _claim_boundary_from_status(lane_name, current_state, None)


def _claim_boundary_from_status(lane_name: str, current_state: str, status_payload: dict[str, Any] | None) -> dict[str, Any]:
    guidance = LANE_ROUTE_GUIDANCE.get(lane_name, {})
    publishable_today = current_state in {"blocked_evidence_only", "measured_claim_ready"}
    gap_summary = guidance.get("blocked_gap_summary")
    testing_workaround = guidance.get("testing_workaround")
    safe_advertising_point = guidance.get("safe_advertising_point")
    if lane_name == "unity_vs_grill" and isinstance(status_payload, dict):
        head_to_head = status_payload.get("head_to_head_readiness") if isinstance(status_payload.get("head_to_head_readiness"), dict) else {}
        import_smoke = status_payload.get("import_smoke") if isinstance(status_payload.get("import_smoke"), dict) else {}
        baseline_status = status_payload.get("status")
        comparison_status = head_to_head.get("status")
        import_status = import_smoke.get("status")
        import_failure_stage = import_smoke.get("failure_stage")
        if baseline_status == "ready":
            gap_summary = (
                "The current public GRILL Unity route now imports and benchmark-captures on the checked Mac/Unity host, "
                "but the direct FastDIS-vs-GRILL Unity comparator still lacks a matched canonical scenario with publishable comparable metrics."
            )
            testing_workaround = (
                "Add at least one canonical shared Unity scenario row to the FastDIS engine report with same-host comparable metrics, "
                "then rerun the Unity head-to-head comparator."
            )
            safe_advertising_point = (
                "FastDIS can now capture the public GRILL Unity route on the checked Mac host and state the remaining comparison gap precisely "
                "instead of treating GRILL as untestable."
            )
            if comparison_status == "comparable":
                gap_summary = "The current public GRILL Unity route imports and compares directly on the checked Mac/Unity host."
                testing_workaround = "Review the matched Unity comparison rows and publish only the claims supported by the same-host report."
                safe_advertising_point = "FastDIS now has same-host public-route Unity comparison evidence and can publish proof-backed competitor claims."
        elif import_status == "pass":
            gap_summary = (
                "The current public GRILL Unity route imports on the checked Mac/Unity host, "
                "but a current shared GRILL benchmark payload is still missing."
            )
            testing_workaround = "Capture a current GRILL Unity shared benchmark report on this host now that the public-route import smoke passes."
            safe_advertising_point = "FastDIS publishes route-scoped install evidence and can now pursue a direct Unity comparison from the public GRILL source route."
        elif import_failure_stage == "host-startup" or import_status == "blocked-host-startup":
            gap_summary = (
                "The current public GRILL Unity route has not yet been meaningfully tested on the checked Mac route "
                "because the host/editor startup baseline failed before plugin import could be judged."
            )
            testing_workaround = "Fix the current Mac Unity startup route or move the GRILL capture to a host/editor combination that can import a blank project first."
            safe_advertising_point = "FastDIS publishes route-scoped startup and install evidence instead of overstating what the current host proved about GRILL."
    if lane_name == "unreal_vs_grill" and isinstance(status_payload, dict):
        mapping_export = status_payload.get("mapping_export") if isinstance(status_payload.get("mapping_export"), dict) else {}
        mapping_materialize = status_payload.get("mapping_materialize") if isinstance(status_payload.get("mapping_materialize"), dict) else {}
        export_failure_kind = mapping_export.get("failure_kind")
        materialize_failure_kind = mapping_materialize.get("failure_kind")
        if export_failure_kind == materialize_failure_kind == "missing-game-module":
            gap_summary = (
                "The current public GRILL Unreal route does not reach a runnable same-host comparison on the checked Mac/UE5.8 lane: "
                "both GRILL mapping export and FastDIS swap materialization stop at `missing-game-module` after Unreal skips incompatible "
                "public GRILL plugins and reports unloadable GRILL example assets."
            )
            testing_workaround = (
                "Capture GRILL Unreal on a Windows/GRILL-compatible host for publishable numbers, or keep any local Mac/Linux port clearly "
                "labeled as internal-only research."
            )
            safe_advertising_point = (
                "FastDIS publishes exact same-host failure boundaries for the public GRILL Unreal route instead of implying a direct performance "
                "comparison where the competitor lane never became runnable."
            )
    return {
        "route_scope": guidance.get("route_scope"),
        "gap_summary": gap_summary,
        "testing_workaround": testing_workaround,
        "safe_advertising_point": safe_advertising_point,
        "publishable_today": publishable_today,
        "non_publishable_angle": None if current_state == "measured_claim_ready" else guidance.get("non_publishable_angle"),
    }


def build_report(
    matrix_path: Path,
    matrix: dict[str, Any],
    validation_path: Path,
    validation: dict[str, Any],
    claim_summary_path: Path,
    claim_summary: dict[str, Any] | None,
) -> dict[str, Any]:
    comparison_index = _comparison_index(matrix)
    validation_index = _validation_index(validation)
    lanes: list[dict[str, Any]] = []

    for lane_name, status_path in DEFAULT_STATUS_REPORTS.items():
        comparison = comparison_index.get(lane_name)
        validation_lane = validation_index.get(lane_name)
        status_payload = _status_payload(status_path)
        current_state = _lane_state(comparison, validation_lane, status_payload)
        blockers = status_payload.get("blockers") if isinstance(status_payload, dict) and isinstance(status_payload.get("blockers"), list) else []
        lanes.append(
            {
                "lane": lane_name,
                "current_state": current_state,
                "blocked_evidence_available": bool(isinstance(validation_lane, dict) and validation_lane.get("artifact_mode") == "blocked_evidence_only"),
                "direct_claim_publishable": bool(
                    current_state == "measured_claim_ready"
                    or (isinstance(comparison, dict) and comparison.get("supported_claim") is True)
                ),
                "claim_boundary": _claim_boundary_from_status(lane_name, current_state, status_payload),
                "comparison": {
                    "path": comparison.get("path") if isinstance(comparison, dict) else None,
                    "status": comparison.get("status") if isinstance(comparison, dict) else None,
                    "evidence_kind": comparison.get("evidence_kind") if isinstance(comparison, dict) else None,
                    "matched_scenarios": comparison.get("matched_scenarios") if isinstance(comparison, dict) else None,
                    "validation_passed": comparison.get("validation_passed") if isinstance(comparison, dict) else None,
                },
                "validation": {
                    "path": display_path(validation_path),
                    "report_status": validation.get("status"),
                    "artifact_mode": validation_lane.get("artifact_mode") if isinstance(validation_lane, dict) else None,
                    "present": validation_lane.get("present") if isinstance(validation_lane, dict) else None,
                    "errors": validation_lane.get("errors") if isinstance(validation_lane, dict) and isinstance(validation_lane.get("errors"), list) else [],
                },
                "baseline_status": {
                    "path": display_path(status_path),
                    "status": status_payload.get("status") if isinstance(status_payload, dict) else None,
                    "blockers": blockers,
                },
            }
        )

    measured_count = sum(1 for lane in lanes if lane["current_state"] == "measured_claim_ready")
    blocked_evidence_count = sum(1 for lane in lanes if lane["current_state"] == "blocked_evidence_only")
    blocked_count = sum(1 for lane in lanes if lane["current_state"] in {"blocked_evidence_only", "blocked_on_competitor"})
    missing_count = sum(1 for lane in lanes if lane["current_state"] == "missing_or_unverified")

    return {
        "schema": "fastdis.competitor_lane_summary.v1",
        "generated_at_utc": utc_now(),
        "status": "complete" if missing_count == 0 else "partial",
        "sources": {
            "matrix": display_path(matrix_path),
            "validation": display_path(validation_path),
            "claim_summary": display_path(claim_summary_path),
        },
        "summary": {
            "lane_count": len(lanes),
            "measured_claim_ready_count": measured_count,
            "blocked_lane_count": blocked_count,
            "blocked_evidence_lane_count": blocked_evidence_count,
            "missing_or_unverified_count": missing_count,
            "publishable_claim_count": int(claim_summary.get("summary", {}).get("publishable_claim_count", 0)) if isinstance((claim_summary or {}).get("summary"), dict) else 0,
            "blocked_claim_count": int(claim_summary.get("summary", {}).get("blocked_claim_count", 0)) if isinstance((claim_summary or {}).get("summary"), dict) else 0,
        },
        "lanes": lanes,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Competitor Lane Summary",
        "",
        f"- schema: `{report['schema']}`",
        f"- status: `{report['status']}`",
        f"- lane_count: `{report['summary']['lane_count']}`",
        f"- measured_claim_ready_count: `{report['summary']['measured_claim_ready_count']}`",
        f"- blocked_lane_count: `{report['summary']['blocked_lane_count']}`",
        f"- blocked_evidence_lane_count: `{report['summary']['blocked_evidence_lane_count']}`",
        f"- missing_or_unverified_count: `{report['summary']['missing_or_unverified_count']}`",
        f"- publishable_claim_count: `{report['summary']['publishable_claim_count']}`",
        f"- blocked_claim_count: `{report['summary']['blocked_claim_count']}`",
        "",
        "| lane | state | publishable | blocked_evidence | comparison_status | evidence_kind | baseline_status | blockers |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for lane in report["lanes"]:
        blockers = "; ".join(str(item) for item in lane["baseline_status"]["blockers"]) or "none"
        lines.append(
            f"| {lane['lane']} | {lane['current_state']} | {lane['direct_claim_publishable']} | "
            f"{lane['blocked_evidence_available']} | {lane['comparison']['status']} | "
            f"{lane['comparison']['evidence_kind']} | {lane['baseline_status']['status']} | {blockers} |"
        )
        claim_boundary = lane.get("claim_boundary") if isinstance(lane.get("claim_boundary"), dict) else {}
        route_scope = claim_boundary.get("route_scope")
        gap_summary = claim_boundary.get("gap_summary")
        testing_workaround = claim_boundary.get("testing_workaround")
        safe_advertising_point = claim_boundary.get("safe_advertising_point")
        non_publishable_angle = claim_boundary.get("non_publishable_angle")
        if route_scope:
            lines.append(f"  route_scope: {route_scope}")
        if gap_summary:
            lines.append(f"  gap_summary: {gap_summary}")
        if testing_workaround:
            lines.append(f"  testing_workaround: {testing_workaround}")
        if safe_advertising_point:
            lines.append(f"  safe_advertising_point: {safe_advertising_point}")
        if non_publishable_angle:
            lines.append(f"  non_publishable_angle: {non_publishable_angle}")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    matrix = load_json(args.matrix)
    validation = load_json(args.validation)
    claim_summary = load_optional_json(args.claim_summary)
    report = build_report(args.matrix, matrix, args.validation, validation, args.claim_summary, claim_summary)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.md_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    args.md_out.write_text(render_markdown(report) + "\n", encoding="utf-8")
    print(f"json: {display_path(args.json_out)}")
    print(f"md: {display_path(args.md_out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
