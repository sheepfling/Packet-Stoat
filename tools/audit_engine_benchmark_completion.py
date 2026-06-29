#!/usr/bin/env python3
"""Audit how much of the benchmark-program objective is currently proven."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = ROOT / "build" / "reports" / "benchmark_completion_audit"
DEFAULT_MATRIX = ROOT / "build" / "reports" / "benchmark_matrix" / "benchmark_matrix.json"
DEFAULT_COVERAGE = ROOT / "build" / "reports" / "benchmark_coverage" / "benchmark_coverage_report.json"
DEFAULT_SCENARIO_CONTRACT = ROOT / "build" / "reports" / "scenario_contract" / "scenario_contract_report.json"
DEFAULT_SURFACE_CLAIMS = ROOT / "build" / "reports" / "surface_claim_report" / "surface_claim_report.json"
DEFAULT_CROSS_ENGINE = ROOT / "build" / "reports" / "cross_engine_equivalence.json"
DEFAULT_COMPETITOR_SUMMARY = ROOT / "build" / "reports" / "competitor_lane_summary" / "competitor_lane_summary.json"
DEFAULT_UNREAL_STATUS = ROOT / "build" / "reports" / "engine_head_to_head" / "unreal_vs_grill_status.json"
DEFAULT_UNITY_STATUS = ROOT / "build" / "reports" / "engine_head_to_head" / "unity_vs_grill_status.json"
REQUIRED_DEEP_SURFACES = ("c", "cpp", "python", "unreal", "godot", "unity")
REQUIRED_ENGINE_SURFACES = ("native", "c", "cpp", "python_ctypes", "unreal", "unity", "godot")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matrix", type=Path, default=DEFAULT_MATRIX)
    parser.add_argument("--coverage", type=Path, default=DEFAULT_COVERAGE)
    parser.add_argument("--scenario-contract", type=Path, default=DEFAULT_SCENARIO_CONTRACT)
    parser.add_argument("--surface-claims", type=Path, default=DEFAULT_SURFACE_CLAIMS)
    parser.add_argument("--cross-engine-equivalence", type=Path, default=DEFAULT_CROSS_ENGINE)
    parser.add_argument("--competitor-summary", type=Path, default=DEFAULT_COMPETITOR_SUMMARY)
    parser.add_argument("--unreal-status", type=Path, default=DEFAULT_UNREAL_STATUS)
    parser.add_argument("--unity-status", type=Path, default=DEFAULT_UNITY_STATUS)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_OUT_DIR / "benchmark_completion_audit.json")
    parser.add_argument("--md-out", type=Path, default=DEFAULT_OUT_DIR / "benchmark_completion_audit.md")
    parser.add_argument(
        "--fail-incomplete",
        action="store_true",
        help="Return a nonzero exit code when the benchmark objective is not yet complete.",
    )
    return parser.parse_args(argv)


def load_json(path: Path | None) -> dict[str, Any] | None:
    if path is None or not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _engine_surface_index(matrix: dict[str, Any]) -> dict[str, dict[str, Any]]:
    surfaces = matrix.get("surfaces") if isinstance(matrix.get("surfaces"), list) else []
    rows = [row for row in surfaces if isinstance(row, dict) and isinstance(row.get("surface"), str)]
    return {row["surface"]: row for row in rows}


def _comparison_index(matrix: dict[str, Any]) -> dict[tuple[str | None, str | None], dict[str, Any]]:
    comparisons = matrix.get("comparisons") if isinstance(matrix.get("comparisons"), list) else []
    rows = [row for row in comparisons if isinstance(row, dict)]
    return {(row.get("left_surface"), row.get("right_surface")): row for row in rows}


def _competitor_validation_index(matrix: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = matrix.get("competitor_validations") if isinstance(matrix.get("competitor_validations"), list) else []
    index: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        for lane in row.get("lanes") if isinstance(row.get("lanes"), list) else []:
            if isinstance(lane, dict) and isinstance(lane.get("lane"), str):
                lane_copy = dict(lane)
                lane_copy["_report_status"] = row.get("status")
                lane_copy["_report_path"] = row.get("path")
                lane_copy["_handoff_workbench_status"] = row.get("handoff_workbench_status")
                lane_copy["_handoff_bundle_kind"] = row.get("handoff_bundle_kind")
                lane_copy["_handoff_self_describing_bundle"] = row.get("handoff_self_describing_bundle")
                index[lane["lane"]] = lane_copy
    return index


def _competitor_lane_index(summary: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not isinstance(summary, dict):
        return {}
    rows = summary.get("lanes") if isinstance(summary.get("lanes"), list) else []
    return {
        row["lane"]: row
        for row in rows
        if isinstance(row, dict) and isinstance(row.get("lane"), str)
    }


def _find_keywords(row: dict[str, Any], keywords: tuple[str, ...]) -> bool:
    scenarios = row.get("scenarios") if isinstance(row.get("scenarios"), list) else []
    notes = row.get("notes") if isinstance(row.get("notes"), list) else []
    haystack = [str(value).lower() for value in scenarios + notes]
    return any(keyword in text for text in haystack for keyword in keywords)


def _requirement(
    *,
    requirement_id: str,
    title: str,
    status: str,
    summary: str,
    evidence: list[str],
    gaps: list[str],
    route_scope: str | None = None,
    gap_summary: str | None = None,
    testing_workaround: str | None = None,
    safe_advertising_point: str | None = None,
    non_publishable_angle: str | None = None,
) -> dict[str, Any]:
    return {
        "id": requirement_id,
        "title": title,
        "status": status,
        "summary": summary,
        "evidence": evidence,
        "gaps": gaps,
        "route_scope": route_scope,
        "gap_summary": gap_summary,
        "testing_workaround": testing_workaround,
        "safe_advertising_point": safe_advertising_point,
        "non_publishable_angle": non_publishable_angle,
    }


def build_report(
    matrix_path: Path,
    matrix: dict[str, Any] | None,
    coverage_path: Path,
    coverage: dict[str, Any] | None,
    scenario_contract_path: Path,
    scenario_contract: dict[str, Any] | None,
    surface_claims_path: Path,
    surface_claims: dict[str, Any] | None,
    cross_engine_path: Path,
    cross_engine: dict[str, Any] | None,
    competitor_summary_path: Path,
    competitor_summary: dict[str, Any] | None,
    unreal_status_path: Path,
    unreal_status: dict[str, Any] | None,
    unity_status_path: Path,
    unity_status: dict[str, Any] | None,
) -> dict[str, Any]:
    engine_rows = _engine_surface_index(matrix or {})
    comparison_rows = _comparison_index(matrix or {})
    competitor_validation_rows = _competitor_validation_index(matrix or {})
    competitor_lane_rows = _competitor_lane_index(competitor_summary)
    matrix_summary = matrix.get("summary") if isinstance(matrix, dict) and isinstance(matrix.get("summary"), dict) else {}
    coverage_summary = coverage.get("summary") if isinstance(coverage, dict) and isinstance(coverage.get("summary"), dict) else {}
    surface_claim_rows = surface_claims.get("surfaces") if isinstance(surface_claims, dict) and isinstance(surface_claims.get("surfaces"), list) else []
    cross_summary = cross_engine.get("summary") if isinstance(cross_engine, dict) and isinstance(cross_engine.get("summary"), dict) else {}
    deep_surfaces = cross_engine.get("deep_surfaces") if isinstance(cross_engine, dict) and isinstance(cross_engine.get("deep_surfaces"), dict) else {}

    required_surface_count = sum(1 for name in REQUIRED_ENGINE_SURFACES if name in engine_rows)
    deep_surface_count = sum(
        1
        for surface in REQUIRED_DEEP_SURFACES
        if isinstance(deep_surfaces.get(surface), dict) and deep_surfaces[surface].get("deep_rows") == 141
    )
    contract_complete = (
        required_surface_count == len(REQUIRED_ENGINE_SURFACES)
        and deep_surface_count == len(REQUIRED_DEEP_SURFACES)
        and cross_summary.get("benchmark_contract_present") is True
        and isinstance(scenario_contract, dict)
        and scenario_contract.get("status") == "complete"
    )
    contract_status = "complete" if contract_complete else "partial"
    contract_gaps: list[str] = []
    if required_surface_count != len(REQUIRED_ENGINE_SURFACES):
        missing = [name for name in REQUIRED_ENGINE_SURFACES if name not in engine_rows]
        contract_gaps.append(f"shared engine reports missing for: {', '.join(missing)}")
    if deep_surface_count != len(REQUIRED_DEEP_SURFACES):
        missing = [
            name
            for name in REQUIRED_DEEP_SURFACES
            if not (isinstance(deep_surfaces.get(name), dict) and deep_surfaces[name].get("deep_rows") == 141)
        ]
        contract_gaps.append(f"deep-surface coverage incomplete for: {', '.join(missing)}")
    if cross_summary.get("benchmark_contract_present") is not True:
        contract_gaps.append("cross-engine equivalence report does not confirm benchmark-contract presence")
    if not isinstance(scenario_contract, dict):
        contract_gaps.append("scenario contract report missing")
    elif scenario_contract.get("status") != "complete":
        contract_gaps.extend(
            scenario_contract.get("gaps") if isinstance(scenario_contract.get("gaps"), list) else ["scenario contract report is not complete"]
        )

    ingest_surface_count = int((coverage_summary.get("ingest") or {}).get("surface_count", 0)) if isinstance(coverage_summary.get("ingest"), dict) else 0
    filtering_surface_count = int((coverage_summary.get("filtering") or {}).get("surface_count", 0)) if isinstance(coverage_summary.get("filtering"), dict) else 0
    latest_state_surface_count = int((coverage_summary.get("latest_state") or {}).get("surface_count", 0)) if isinstance(coverage_summary.get("latest_state"), dict) else 0
    replay_surface_count = int((coverage_summary.get("replay") or {}).get("surface_count", 0)) if isinstance(coverage_summary.get("replay"), dict) else 0
    ingest_filter_proven = ingest_surface_count >= 4 and filtering_surface_count >= 1
    latest_state_proven = ingest_surface_count >= 4 and latest_state_surface_count >= 1
    reproducible_core_status = "complete" if ingest_filter_proven and latest_state_proven else "partial"
    reproducible_core_gaps: list[str] = []
    if ingest_surface_count < 4:
        reproducible_core_gaps.append("shared ingest coverage does not yet reach native, C, C++, and Python together")
    if not ingest_filter_proven:
        reproducible_core_gaps.append("filtering or malformed-traffic benchmark coverage is not explicitly published in the coverage report")
    if not latest_state_proven:
        reproducible_core_gaps.append("latest-state or snapshot benchmark coverage is not explicitly published in the coverage report")

    replay_status = "complete" if replay_surface_count >= 1 else "partial"
    replay_gaps = [] if replay_surface_count >= 1 else ["no shared benchmark surface currently exposes explicit replay scenarios in the coverage report"]

    engine_runtime_surfaces = [engine_rows.get(name) for name in ("unreal", "unity", "godot")]
    measured_runtime_surfaces = [
        row
        for row in engine_runtime_surfaces
        if isinstance(row, dict) and (int(row.get("latency_rows", 0)) > 0 or int(row.get("runtime_metric_rows", 0)) > 0)
    ]
    engine_runtime_status = "complete" if len(measured_runtime_surfaces) == 3 else "partial"
    engine_runtime_gaps = []
    for name in ("unreal", "unity", "godot"):
        row = engine_rows.get(name)
        if not isinstance(row, dict):
            engine_runtime_gaps.append(f"{name} shared engine benchmark report missing")
        elif int(row.get("latency_rows", 0)) == 0 and int(row.get("runtime_metric_rows", 0)) == 0:
            engine_runtime_gaps.append(f"{name} has verification rows but no measured runtime latency or wall-clock runtime rows")

    unreal_compare = comparison_rows.get(("unreal", "grill_unreal"), {})
    unreal_lane = competitor_lane_rows.get("unreal_vs_grill", {})
    unreal_boundary = unreal_lane.get("claim_boundary") if isinstance(unreal_lane.get("claim_boundary"), dict) else {}
    unreal_lane_measured = unreal_lane.get("current_state") == "measured_claim_ready"
    unreal_supported = unreal_compare.get("supported_claim") is True
    unreal_validation = competitor_validation_rows.get("unreal_vs_grill", {})
    unreal_blocked_evidence_available = unreal_validation.get("artifact_mode") == "blocked_evidence_only"
    unreal_validation_passed = bool(
        unreal_validation.get("present") is True
        and unreal_validation.get("error_count") == 0
        and unreal_validation.get("_report_status") == "pass"
        and unreal_validation.get("_handoff_workbench_status") == "pass"
        and unreal_validation.get("_handoff_bundle_kind") == "archive_bundle"
        and unreal_validation.get("_handoff_self_describing_bundle") is True
    )
    unreal_blockers = unreal_status.get("blockers") if isinstance(unreal_status, dict) and isinstance(unreal_status.get("blockers"), list) else []
    if unreal_lane_measured or (unreal_supported and unreal_validation_passed):
        unreal_head_to_head_status = "complete"
        unreal_head_to_head_gaps: list[str] = []
    elif not unreal_supported:
        unreal_head_to_head_status = "blocked"
        unreal_head_to_head_gaps = list(unreal_blockers or ["no supported Unreal same-host GRILL comparison report"])
        if unreal_blocked_evidence_available:
            unreal_head_to_head_gaps.append("local blocked-evidence lane is present and recorded in competitor capture validation")
    else:
        unreal_head_to_head_status = "partial"
        unreal_head_to_head_gaps = ["supported Unreal GRILL comparison exists, but competitor-capture validation for the Unreal lane has not passed through a self-describing returned bundle"]

    unity_compare = comparison_rows.get(("unity", "grill_unity"), {})
    unity_lane = competitor_lane_rows.get("unity_vs_grill", {})
    unity_boundary = unity_lane.get("claim_boundary") if isinstance(unity_lane.get("claim_boundary"), dict) else {}
    unity_lane_measured = unity_lane.get("current_state") == "measured_claim_ready"
    unity_supported = unity_compare.get("supported_claim") is True
    unity_validation = competitor_validation_rows.get("unity_vs_grill", {})
    unity_blocked_evidence_available = unity_validation.get("artifact_mode") == "blocked_evidence_only"
    unity_validation_passed = bool(
        unity_validation.get("present") is True
        and unity_validation.get("error_count") == 0
        and unity_validation.get("_report_status") == "pass"
        and unity_validation.get("_handoff_workbench_status") == "pass"
        and unity_validation.get("_handoff_bundle_kind") == "archive_bundle"
        and unity_validation.get("_handoff_self_describing_bundle") is True
    )
    unity_blockers = unity_status.get("blockers") if isinstance(unity_status, dict) and isinstance(unity_status.get("blockers"), list) else []
    if unity_lane_measured or (unity_supported and unity_validation_passed):
        unity_head_to_head_status = "complete"
        unity_head_to_head_gaps: list[str] = []
    elif not unity_supported:
        unity_head_to_head_status = "blocked"
        unity_head_to_head_gaps = list(unity_blockers or ["no supported Unity same-host GRILL comparison report"])
        if unity_blocked_evidence_available:
            unity_head_to_head_gaps.append("local blocked-evidence lane is present and recorded in competitor capture validation")
    else:
        unity_head_to_head_status = "partial"
        unity_head_to_head_gaps = ["supported Unity GRILL comparison exists, but competitor-capture validation for the Unity lane has not passed through a self-describing returned bundle"]

    equivalence_complete = isinstance(cross_engine, dict) and cross_engine.get("status") == "complete"
    equivalence_status = "complete" if equivalence_complete else "partial"
    equivalence_gaps = [] if equivalence_complete else list(cross_engine.get("gaps") if isinstance(cross_engine, dict) and isinstance(cross_engine.get("gaps"), list) else ["cross-engine equivalence report missing or incomplete"])

    matrix_claim_boundaries = matrix.get("claim_boundaries") if isinstance(matrix, dict) and isinstance(matrix.get("claim_boundaries"), list) else []
    cross_claim_boundaries = cross_engine.get("claim_boundaries") if isinstance(cross_engine, dict) and isinstance(cross_engine.get("claim_boundaries"), list) else []
    measured_surface_names = {
        row["surface"]
        for row in engine_rows.values()
        if isinstance(row, dict) and isinstance(row.get("surface"), str) and row.get("evidence_kind") != "sample"
    }
    surfaced_boundary_names = {
        row.get("surface")
        for row in surface_claim_rows
        if isinstance(row, dict)
        and isinstance(row.get("surface"), str)
        and isinstance(row.get("boundaries"), list)
        and len(row.get("boundaries") or []) > 0
    }
    missing_surface_boundaries = sorted(name for name in measured_surface_names if name not in surfaced_boundary_names)
    claim_boundary_complete = bool(matrix_claim_boundaries) and bool(cross_claim_boundaries) and not missing_surface_boundaries
    claim_boundary_status = "complete" if claim_boundary_complete else "partial"
    claim_boundary_gaps = []
    if not matrix_claim_boundaries:
        claim_boundary_gaps.append("benchmark matrix claim boundaries missing")
    if not cross_claim_boundaries:
        claim_boundary_gaps.append("cross-engine equivalence claim boundaries missing")
    if not surface_claim_rows:
        claim_boundary_gaps.append("surface claim report missing or empty")
    elif missing_surface_boundaries:
        claim_boundary_gaps.append("surface claim boundaries missing for: " + ", ".join(missing_surface_boundaries))

    requirements = [
        _requirement(
            requirement_id="shared_contract",
            title="Shared scenarios, truth payloads, and metrics/report contract across the benchmark surfaces",
            status=contract_status,
            summary=(
                "Current evidence shows shared deep-surface equivalence across C/C++/Python/Unreal/Godot/Unity and shared benchmark-report coverage for native, Python, Unreal, Unity, and Godot."
                if contract_status == "complete"
                else "Shared contract evidence exists, but at least one required surface or deep-surface contract proof is still incomplete."
            ),
            evidence=[display_path(matrix_path), display_path(cross_engine_path), display_path(scenario_contract_path)],
            gaps=contract_gaps,
        ),
        _requirement(
            requirement_id="ingest_filter_latest_state",
            title="Reproducible ingest, filtering, and latest-state benchmark reports",
            status=reproducible_core_status,
            summary=(
                "Native/C/C++/Python benchmark reports contain measured ingest rows and explicit filtering/latest-state scenario evidence."
                if reproducible_core_status == "complete"
                else "Core benchmark evidence exists, but the current reports do not yet prove the full ingest/filter/latest-state benchmark claim cleanly."
            ),
            evidence=[display_path(matrix_path), display_path(coverage_path)],
            gaps=reproducible_core_gaps,
        ),
        _requirement(
            requirement_id="replay_reports",
            title="Reproducible replay benchmark reports",
            status=replay_status,
            summary=(
                "At least one shared benchmark report exposes explicit replay scenario evidence."
                if replay_status == "complete"
                else "Replay appears in surrounding proof work, but the current shared benchmark reports do not yet expose explicit replay benchmark rows."
            ),
            evidence=[display_path(matrix_path), display_path(coverage_path)],
            gaps=replay_gaps,
        ),
        _requirement(
            requirement_id="engine_runtime_reports",
            title="Measured engine-runtime benchmark reports for Unreal, Unity, and Godot",
            status=engine_runtime_status,
            summary=(
                "All three engine lanes carry measured runtime latency/apply metrics in the shared report contract."
                if engine_runtime_status == "complete"
                else "Current engine reports are proof-backed bridges, but one or more engine lanes still lack measured runtime latency or wall-clock runtime metrics."
            ),
            evidence=[display_path(matrix_path)],
            gaps=engine_runtime_gaps,
        ),
        _requirement(
            requirement_id="unreal_competitor",
            title="Honest same-host Unreal FastDIS-vs-GRILL head-to-head report",
            status=unreal_head_to_head_status,
            summary=(
                "A supported same-host Unreal head-to-head claim is present."
                if unreal_head_to_head_status == "complete"
                else "The Unreal competitor lane is still blocked on missing same-host current GRILL evidence."
            ),
            evidence=[display_path(matrix_path), display_path(unreal_status_path)],
            gaps=unreal_head_to_head_gaps,
            route_scope=unreal_boundary.get("route_scope"),
            gap_summary=unreal_boundary.get("gap_summary"),
            testing_workaround=unreal_boundary.get("testing_workaround"),
            safe_advertising_point=unreal_boundary.get("safe_advertising_point"),
            non_publishable_angle=unreal_boundary.get("non_publishable_angle"),
        ),
        _requirement(
            requirement_id="unity_competitor",
            title="Honest same-host Unity FastDIS-vs-GRILL head-to-head report",
            status=unity_head_to_head_status,
            summary=(
                "A supported same-host Unity head-to-head claim is present."
                if unity_head_to_head_status == "complete"
                else "The Unity competitor lane is still blocked on missing current GRILL baseline evidence and a GRILL-compatible host."
            ),
            evidence=[display_path(matrix_path), display_path(unity_status_path)],
            gaps=unity_head_to_head_gaps,
            route_scope=unity_boundary.get("route_scope"),
            gap_summary=unity_boundary.get("gap_summary"),
            testing_workaround=unity_boundary.get("testing_workaround"),
            safe_advertising_point=unity_boundary.get("safe_advertising_point"),
            non_publishable_angle=unity_boundary.get("non_publishable_angle"),
        ),
        _requirement(
            requirement_id="cross_engine_equivalence",
            title="Cross-engine equivalence evidence",
            status=equivalence_status,
            summary=(
                "The shared cross-engine equivalence report is complete and supports consistency claims."
                if equivalence_status == "complete"
                else "Cross-engine equivalence evidence exists, but the current report is not yet complete."
            ),
            evidence=[display_path(cross_engine_path)],
            gaps=equivalence_gaps,
        ),
        _requirement(
            requirement_id="claim_boundaries",
            title="Clear claim boundaries for every measured surface",
            status=claim_boundary_status,
            summary=(
                "Current matrix, per-surface surface-claim, and equivalence outputs publish explicit claim-boundary guidance."
                if claim_boundary_status == "complete"
                else "One or more measured surfaces or top-level reports are still missing explicit claim-boundary guidance."
            ),
            evidence=[display_path(matrix_path), display_path(surface_claims_path), display_path(cross_engine_path)],
            gaps=claim_boundary_gaps,
        ),
    ]

    status_counts = {
        "complete": sum(1 for row in requirements if row["status"] == "complete"),
        "partial": sum(1 for row in requirements if row["status"] == "partial"),
        "blocked": sum(1 for row in requirements if row["status"] == "blocked"),
    }
    complete = status_counts["complete"] == len(requirements)
    overall_status = "complete" if complete else "incomplete"
    missing_labels: list[str] = []
    if engine_runtime_status != "complete":
        missing_labels.append("engine-runtime measurement")
    if "c" not in engine_rows:
        missing_labels.append("c shared benchmark coverage")
    if "cpp" not in engine_rows:
        missing_labels.append("cpp shared benchmark coverage")
    if unreal_head_to_head_status != "complete" or unity_head_to_head_status != "complete":
        missing_labels.append("competitor baseline capture")
    if replay_status != "complete":
        missing_labels.append("replay benchmark coverage")
    note = "The benchmark-program objective is fully proven by current artifacts."
    if not complete:
        missing_text = ", ".join(missing_labels) if missing_labels else "one or more evidence areas"
        note = (
            "The benchmark-program objective is not yet fully proven. "
            f"Current artifacts still need {missing_text} to close the remaining gaps."
        )

    next_steps: list[str] = []
    if engine_runtime_status != "complete":
        engine_runtime_missing = [
            name
            for name in ("unreal", "unity", "godot")
            if not isinstance(engine_rows.get(name), dict)
            or (int(engine_rows[name].get("latency_rows", 0)) == 0 and int(engine_rows[name].get("runtime_metric_rows", 0)) == 0)
        ]
        next_steps.append(
            "Promote "
            + ", ".join(engine_runtime_missing)
            + " from proof-backed bridges to measured runtime rows with latency/apply or wall-clock runtime metrics."
        )
    if "c" not in engine_rows:
        next_steps.append("Add a shared `c` benchmark report lane to the current benchmark source payload and refresh path so the cross-language contract covers C explicitly.")
    if "cpp" not in engine_rows:
        next_steps.append("Add a shared `cpp` benchmark report lane to the current benchmark source payload and refresh path so the cross-language contract covers C++ explicitly.")
    if replay_status != "complete":
        next_steps.append("Add explicit replay scenarios to the shared benchmark reports so replay claims are directly evidenced in the matrix.")
    if unreal_head_to_head_status != "complete":
        if unreal_supported and not unreal_validation_passed:
            next_steps.append("Regenerate a passing competitor-capture validation artifact for the Unreal GRILL lane before treating the comparison as publishable proof.")
        else:
            next_steps.append(
                unreal_boundary.get("testing_workaround")
                or "Capture a current same-host GRILL Unreal shared benchmark report and rerun the shared comparator."
            )
    if unity_head_to_head_status != "complete":
        if unity_supported and not unity_validation_passed:
            next_steps.append("Regenerate a passing competitor-capture validation artifact for the Unity GRILL lane before treating the comparison as publishable proof.")
        else:
            next_steps.append(
                unity_boundary.get("testing_workaround")
                or "Capture a current GRILL Unity shared benchmark report on a GRILL-compatible host and rerun the shared comparator."
            )

    return {
        "schema": "fastdis.engine_benchmark_completion_audit.v1",
        "generated_at_utc": utc_now(),
        "status": overall_status,
        "note": note,
        "summary": {
            "requirement_count": len(requirements),
            "complete_count": status_counts["complete"],
            "partial_count": status_counts["partial"],
            "blocked_count": status_counts["blocked"],
            "supported_competitor_claim_count": matrix_summary.get("supported_competitor_claim_count", 0),
            "passing_competitor_validation_count": matrix_summary.get("passing_competitor_validation_count", 0),
            "blocked_evidence_lane_count": matrix_summary.get("blocked_evidence_lane_count", 0),
            "engine_runtime_measured_surface_count": len(measured_runtime_surfaces),
        },
        "requirements": requirements,
        "claim_boundaries": [
            "This audit is requirement-driven: missing or indirect evidence does not count as completion.",
            "Cross-engine equivalence and benchmark coverage are separate requirements from same-host competitor proof.",
            "Proof-backed engine bridges do not count as measured engine-runtime benchmark completion until runtime metrics are present.",
            "Blocked competitor rows must stay scoped to the GRILL route actually tested; private ports do not count as public-route proof.",
        ],
        "next_steps": next_steps,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Benchmark Completion Audit",
        "",
        f"- schema: `{report['schema']}`",
        f"- status: `{report['status']}`",
        "",
        report["note"],
        "",
        "## Summary",
        "",
        f"- requirement_count: `{report['summary']['requirement_count']}`",
        f"- complete_count: `{report['summary']['complete_count']}`",
        f"- partial_count: `{report['summary']['partial_count']}`",
        f"- blocked_count: `{report['summary']['blocked_count']}`",
        f"- supported_competitor_claim_count: `{report['summary']['supported_competitor_claim_count']}`",
        f"- passing_competitor_validation_count: `{report['summary']['passing_competitor_validation_count']}`",
        f"- blocked_evidence_lane_count: `{report['summary']['blocked_evidence_lane_count']}`",
        f"- engine_runtime_measured_surface_count: `{report['summary']['engine_runtime_measured_surface_count']}`",
        "",
        "## Requirements",
        "",
        "| id | status | title |",
        "| --- | --- | --- |",
    ]
    for row in report["requirements"]:
        lines.append(f"| {row['id']} | {row['status']} | {row['title']} |")
    lines.extend(["", "## Details", ""])
    for row in report["requirements"]:
        lines.extend(
            [
                f"### {row['id']}",
                "",
                f"- status: `{row['status']}`",
                f"- title: {row['title']}",
                f"- summary: {row['summary']}",
                "",
                "Evidence:",
            ]
        )
        for item in row["evidence"]:
            lines.append(f"- `{item}`")
        lines.append("")
        lines.append("Gaps:")
        if row["gaps"]:
            for gap in row["gaps"]:
                lines.append(f"- {gap}")
        else:
            lines.append("- none")
        if row.get("route_scope"):
            lines.append(f"- route_scope: {row['route_scope']}")
        if row.get("gap_summary"):
            lines.append(f"- gap_summary: {row['gap_summary']}")
        if row.get("testing_workaround"):
            lines.append(f"- testing_workaround: {row['testing_workaround']}")
        if row.get("safe_advertising_point"):
            lines.append(f"- safe_advertising_point: {row['safe_advertising_point']}")
        if row.get("non_publishable_angle"):
            lines.append(f"- non_publishable_angle: {row['non_publishable_angle']}")
        lines.append("")
    lines.extend(["## Next Steps", ""])
    if report["next_steps"]:
        for step in report["next_steps"]:
            lines.append(f"- {step}")
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    matrix = load_json(args.matrix)
    coverage = load_json(args.coverage)
    cross_engine = load_json(args.cross_engine_equivalence)
    competitor_summary = load_json(args.competitor_summary)
    scenario_contract = load_json(args.scenario_contract)
    surface_claims = load_json(args.surface_claims)
    unreal_status = load_json(args.unreal_status)
    unity_status = load_json(args.unity_status)
    report = build_report(
        args.matrix,
        matrix,
        args.coverage,
        coverage,
        args.scenario_contract,
        scenario_contract,
        args.surface_claims,
        surface_claims,
        args.cross_engine_equivalence,
        cross_engine,
        args.competitor_summary,
        competitor_summary,
        args.unreal_status,
        unreal_status,
        args.unity_status,
        unity_status,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.md_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    args.md_out.write_text(render_markdown(report) + "\n", encoding="utf-8")
    print(f"json: {display_path(args.json_out)}")
    print(f"md: {display_path(args.md_out)}")
    return 1 if args.fail_incomplete and report["status"] != "complete" else 0


if __name__ == "__main__":
    raise SystemExit(main())
