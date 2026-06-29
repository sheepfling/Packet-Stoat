#!/usr/bin/env python3
"""Materialize deterministic benchmark/report fixtures for clean-checkout testing."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

import build_benchmark_claim_summary
import build_benchmark_coverage_report
import build_benchmark_matrix_report
import build_competitor_capture_manifest
import build_core_cross_platform_harness_report
import build_cross_engine_equivalence_report
import build_scenario_contract_report
import build_surface_claim_report
import build_unity_grill_baseline_status
import build_unreal_grill_baseline_status
import check_benchmark_contract_stack
import audit_engine_benchmark_completion
import generate_endpoint_mapping_manifest
import generate_epic2_milestones
import generate_epic2_parity_report
import generate_lattice_dis_mapping_plan
import generate_message_views
import generate_pdu_catalog
import generate_pdu_log_catalog
import generate_standards_status


ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build"
REPORTS = BUILD / "reports"
VERIFICATION = ROOT / "verification_reports"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json_with_md(path: Path, payload: dict, title: str) -> None:
    write_json(path, payload)
    md_path = path.with_suffix(".md")
    write_text(
        md_path,
        f"# {title}\n\n- schema: `{payload.get('schema', 'unknown')}`\n- status: `{payload.get('status', payload.get('overall_status', 'n/a'))}`\n",
    )


def host_payload(*, engine_version: str | None = None, unity_version: str | None = None) -> dict[str, str]:
    payload = {
        "system": "Darwin",
        "release": "24.0.0",
        "machine": "arm64",
    }
    if engine_version is not None:
        payload["engine_version"] = engine_version
    if unity_version is not None:
        payload["unity_version"] = unity_version
    return payload


def engine_report(
    *,
    surface: str,
    surface_kind: str,
    source_payload: str,
    source_schema: str,
    scenarios: list[tuple[str, dict, dict | None]],
    host: dict[str, str] | None = None,
) -> dict:
    rows = []
    latency_rows = 0
    runtime_metric_rows = 0
    truth_rows = 0
    for scenario, metrics, truth in scenarios:
        if metrics.get("p50_ingest_ms") is not None:
            latency_rows += 1
        if metrics.get("runtime_elapsed_seconds") is not None:
            runtime_metric_rows += 1
        if isinstance(truth, dict) and truth.get("final_truth_match") is not None:
            truth_rows += 1
        rows.append(
            {
                "scenario": scenario,
                "metrics": metrics,
                "truth": truth,
            }
        )
    return {
        "schema": "fastdis.engine_benchmark_report.v1",
        "generated_at_utc": utc_now(),
        "surface": surface,
        "surface_kind": surface_kind,
        "source_payload": source_payload,
        "source_schema": source_schema,
        "host": host or host_payload(),
        "summary": {
            "row_count": len(rows),
            "latency_rows": latency_rows,
            "runtime_metric_rows": runtime_metric_rows,
            "truth_rows": truth_rows,
        },
        "rows": rows,
    }


def head_to_head_report(
    *,
    left_surface: str,
    right_surface: str,
    left_path: str,
    right_path: str,
    status: str,
    same_host: bool,
    matched_scenarios: int,
    comparable_metric_rows: int,
    note: str,
) -> dict:
    return {
        "schema": "fastdis.engine_head_to_head_report.v1",
        "generated_at_utc": utc_now(),
        "status": status,
        "note": note,
        "inputs": {
            "left": left_path,
            "right": right_path,
            "left_surface": left_surface,
            "right_surface": right_surface,
        },
        "comparison": {
            "same_host": same_host,
            "matched_scenarios": matched_scenarios,
            "comparable_metric_rows": comparable_metric_rows,
            "claim_boundaries": [],
        },
        "validation_errors": [],
    }


def bootstrap_current_payload() -> None:
    current = {
        "generated_at_utc": utc_now(),
        "host": host_payload(),
        "qualification": {"summary": {"native_case_count": 2}},
        "native": {"results": []},
        "cpp": {"results": []},
        "ctypes": {"results": []},
    }
    current["native"]["results"] = [
        {"case": "header_all_no_callback", "packets": 1000, "avg_ms": 1.0, "p95_ms": 1.2},
        {"case": "entity_state_1x10hz", "packets": 24, "avg_ms": 0.5, "p95_ms": 0.7},
        {"case": "entity_state_100x30hz", "packets": 300, "avg_ms": 1.5, "p95_ms": 1.9},
    ]
    current["ctypes"]["results"] = [
        {"case": "entity_state_1x10hz", "packets": 24, "avg_ms": 1.0, "p95_ms": 1.3},
    ]
    write_json(BUILD / "benchmark_results" / "current" / "current.json", current)


def bootstrap_engine_reports() -> None:
    native = engine_report(
        surface="native",
        surface_kind="native",
        source_payload="build/benchmark_results/current/current.json",
        source_schema="fastdis.native_benchmark.current",
        scenarios=[
            (
                "header_filter_90pct_reject",
                {
                    "packets_per_sec": 1000000.0,
                    "p50_ingest_ms": 0.01,
                    "p95_ingest_ms": 0.02,
                    "runtime_elapsed_seconds": None,
                    "notes": ["fixture native benchmark row"],
                },
                None,
            ),
            (
                "entity_state_1x10hz",
                {
                    "packets_per_sec": 4800.0,
                    "p50_ingest_ms": None,
                    "p95_ingest_ms": None,
                    "runtime_elapsed_seconds": 0.005,
                    "notes": ["fixture truth-backed native row"],
                },
                {"final_truth_match": True},
            ),
        ],
    )
    c_report = engine_report(
        surface="c",
        surface_kind="c",
        source_payload="build/reports/network_ingest_matrix/network_ingest_matrix.json",
        source_schema="fastdis.network_ingest_matrix.v1",
        scenarios=[
            (
                "entity_state_1x10hz",
                {
                    "packets_per_sec": 2400.0,
                    "p50_ingest_ms": None,
                    "p95_ingest_ms": None,
                    "runtime_elapsed_seconds": 0.01,
                    "notes": ["fixture C ingest truth row"],
                },
                {"final_truth_match": True},
            ),
        ],
    )
    cpp = engine_report(
        surface="cpp",
        surface_kind="cpp",
        source_payload="build/benchmark_results/current/current.json",
        source_schema="fastdis.cpp_benchmark.current",
        scenarios=[
            (
                "filter_reject_90pct",
                {
                    "packets_per_sec": 950000.0,
                    "p50_ingest_ms": 0.02,
                    "p95_ingest_ms": 0.03,
                    "runtime_elapsed_seconds": None,
                    "notes": ["fixture C++ filter row"],
                },
                {"final_truth_match": True},
            ),
            (
                "entity_state_100x30hz",
                {
                    "packets_per_sec": 20000.0,
                    "p50_ingest_ms": None,
                    "p95_ingest_ms": None,
                    "runtime_elapsed_seconds": 0.015,
                    "notes": ["fixture C++ truth row"],
                },
                {"final_truth_match": True},
            ),
        ],
    )
    python = engine_report(
        surface="python_ctypes",
        surface_kind="python",
        source_payload="build/benchmark_results/current/current.json",
        source_schema="fastdis.ctypes_benchmark.current",
        scenarios=[
            (
                "ctypes_entity_force_reject_no_callback",
                {
                    "packets_per_sec": 90000.0,
                    "p50_ingest_ms": 0.2,
                    "p95_ingest_ms": 0.3,
                    "runtime_elapsed_seconds": None,
                    "notes": ["fixture Python filter row"],
                },
                None,
            ),
            (
                "entity_state_100x30hz",
                {
                    "packets_per_sec": 3000.0,
                    "p50_ingest_ms": None,
                    "p95_ingest_ms": None,
                    "runtime_elapsed_seconds": 0.1,
                    "notes": ["fixture Python truth row"],
                },
                {"final_truth_match": True},
            ),
        ],
    )
    unreal = engine_report(
        surface="unreal",
        surface_kind="engine",
        source_payload="build/reports/unreal_fab_readiness.json",
        source_schema="fastdis.unreal_fab_readiness.v1",
        scenarios=[
            (
                "unreal_replay_latest_state_apply",
                {
                    "packets_per_sec": 1800.0,
                    "p50_ingest_ms": None,
                    "p95_ingest_ms": None,
                    "runtime_elapsed_seconds": 0.12,
                    "main_thread_apply_ms": 0.4,
                    "notes": ["fixture Unreal runtime row"],
                },
                {"final_truth_match": True},
            ),
        ],
        host=host_payload(engine_version="5.8"),
    )
    unity = engine_report(
        surface="unity",
        surface_kind="engine",
        source_payload="build/reports/unity_runtime_verification.json",
        source_schema="fastdis.unity_runtime_verification.v1",
        scenarios=[
            (
                "entity_state_1x10hz",
                {
                    "packets_per_sec": 1700.0,
                    "p50_ingest_ms": None,
                    "p95_ingest_ms": None,
                    "runtime_elapsed_seconds": 0.11,
                    "main_thread_apply_ms": 0.5,
                    "notes": ["fixture Unity truth row"],
                },
                {"final_truth_match": True},
            ),
            (
                "unity_replay_latest_state_apply",
                {
                    "packets_per_sec": 1650.0,
                    "p50_ingest_ms": None,
                    "p95_ingest_ms": None,
                    "runtime_elapsed_seconds": 0.14,
                    "main_thread_apply_ms": 0.6,
                    "notes": ["fixture Unity replay row"],
                },
                {"final_truth_match": True},
            ),
        ],
        host=host_payload(unity_version="6000.5.0f1"),
    )
    godot = engine_report(
        surface="godot",
        surface_kind="engine",
        source_payload="build/reports/godot_workflow_report.json",
        source_schema="fastdis.godot_workflow_report.v1",
        scenarios=[
            (
                "godot_replay_latest_state_apply",
                {
                    "packets_per_sec": 1500.0,
                    "p50_ingest_ms": None,
                    "p95_ingest_ms": None,
                    "runtime_elapsed_seconds": 0.16,
                    "main_thread_apply_ms": 0.7,
                    "notes": ["fixture Godot runtime row"],
                },
                {"final_truth_match": True},
            ),
        ],
    )
    grill_unreal = engine_report(
        surface="grill_unreal",
        surface_kind="competitor",
        source_payload="verification_reports/unreal_grill_baseline/grill_unreal_benchmark_baseline.json",
        source_schema="fastdis.grill_harness_capture.v1",
        scenarios=[
            (
                "unreal_replay_latest_state_apply",
                {
                    "packets_per_sec": 1200.0,
                    "p50_ingest_ms": None,
                    "p95_ingest_ms": None,
                    "runtime_elapsed_seconds": 0.18,
                    "main_thread_apply_ms": 0.8,
                    "notes": ["fixture GRILL Unreal comparison row"],
                },
                None,
            ),
        ],
        host=host_payload(engine_version="5.8"),
    )
    grill_unity = engine_report(
        surface="grill_unity",
        surface_kind="competitor",
        source_payload="verification_reports/unity_grill_baseline/grill_unity_benchmark_baseline.json",
        source_schema="fastdis.grill_harness_capture.v1",
        scenarios=[
            (
                "entity_state_1x10hz",
                {
                    "packets_per_sec": 900.0,
                    "p50_ingest_ms": None,
                    "p95_ingest_ms": None,
                    "runtime_elapsed_seconds": 0.2,
                    "main_thread_apply_ms": 1.0,
                    "notes": ["fixture GRILL Unity comparison row"],
                },
                None,
            ),
        ],
        host=host_payload(unity_version="6000.5.0f1"),
    )
    reports = {
        "native_engine_benchmark_report.json": native,
        "c_engine_benchmark_report.json": c_report,
        "cpp_engine_benchmark_report.json": cpp,
        "python_ctypes_engine_benchmark_report.json": python,
        "unreal_engine_benchmark_report.json": unreal,
        "unity_engine_benchmark_report.json": unity,
        "godot_engine_benchmark_report.json": godot,
        "grill_unreal_engine_benchmark_report.json": grill_unreal,
        "grill_unity_engine_benchmark_report.json": grill_unity,
    }
    for name, payload in reports.items():
        write_json_with_md(REPORTS / "engine_benchmarks" / name, payload, name.replace("_", " ").replace(".json", ""))


def bootstrap_misc_reports() -> None:
    write_json_with_md(
        REPORTS / "network_ingest_matrix" / "network_ingest_matrix.json",
        {
            "schema": "fastdis.network_ingest_matrix.v1",
            "generated_at_utc": utc_now(),
            "status": "pass",
            "rows": [{"surface": "c"}, {"surface": "cpp"}],
        },
        "Network Ingest Matrix",
    )
    unity_equivalence = json.loads((ROOT / "tests" / "data" / "engine_benchmark_sources" / "unity_cross_engine_equivalence.sample.json").read_text(encoding="utf-8"))
    unity_equivalence["status"] = "complete"
    metrics = unity_equivalence.setdefault("metrics", {})
    metrics["language_rows"] = {
        surface: {"catalog_rows": 141, "deep_rows": 141}
        for surface in ("c", "cpp", "python", "unreal", "godot", "unity")
    }
    write_json_with_md(REPORTS / "unity_cross_engine_equivalence.json", unity_equivalence, "Unity Cross Engine Equivalence")
    write_json_with_md(
        REPORTS / "unity_runtime_verification.json",
        {
            "schema": "fastdis.unity_runtime_verification.v1",
            "generated_at_utc": utc_now(),
            "overall_status": "pass",
            "lanes": [{"platform": "EditorMethod", "launch": "login-shell"}],
        },
        "Unity Runtime Verification",
    )
    write_json_with_md(
        REPORTS / "unreal_fab_readiness.json",
        {
            "schema": "fastdis.unreal_fab_readiness.v1",
            "generated_at_utc": utc_now(),
            "status": "pass",
        },
        "Unreal Fab Readiness",
    )
    write_json_with_md(
        REPORTS / "godot_workflow_report.json",
        {
            "schema": "fastdis.godot_workflow_report.v1",
            "generated_at_utc": utc_now(),
            "status": "pass",
            "doctor": {"status": "passed", "host": {"platform": "Darwin", "arch": "arm64", "godot": "/Applications/Godot.app"}},
            "lanes": {
                "build": {"status": "passed"},
                "verify": {"status": "passed"},
                "demo": {"status": "passed", "elapsed_seconds": 0.25},
                "missing_lib": {"status": "passed"},
            },
        },
        "Godot Workflow Report",
    )
    write_json_with_md(
        REPORTS / "godot_replay_matrix" / "godot_replay_matrix.json",
        {
            "routes": [
                {
                    "surface": "godot",
                    "mode": "replay",
                    "scenario": "godot_replay_latest_state_apply",
                    "status": "passed",
                    "errors": [],
                    "report": {"loaded_packets": 300},
                    "truth": {
                        "schema": "fastdis.network_truth.v1",
                        "packets_parsed": 300,
                        "entity_state": 300,
                        "malformed": 0,
                        "unique_entities": 100,
                        "latest_entities": 100,
                    },
                }
            ]
        },
        "Godot Replay Matrix",
    )
    write_json_with_md(
        REPORTS / "orientation_assurance_live" / "godot_good_compare.json",
        {
            "results": [{"pass": True}],
        },
        "Godot Good Compare",
    )
    for engine, prefix, asset_forward, north_axis in (
        ("godot", "godot_standalone_enu", "negative_z", "negative_z"),
        ("unreal", "unreal_standalone_neu", "positive_x", "positive_x"),
        ("unity", "unity_standalone_eun", "positive_z", "positive_z"),
    ):
        for kind, path_name, axis_map in (
            ("good", "orientation_compare.json", {"east": "positive_y", "north": north_axis, "up": "positive_z"}),
            ("bad", "known_bad_compare.json", {"east": "positive_y", "north": north_axis, "up": "positive_z"}),
        ):
            payload = {
                "summary": {"pass_count": 9 if kind == "good" else 0, "case_count": 9, "max_axis_error_deg": 0.0 if kind == "good" else 120.0},
                "config": {
                    "name": f"{engine}_{kind}",
                    "target_frame": {"handedness": "right", "units": "meters", "axis_map": axis_map},
                    "asset": {"forward_axis": asset_forward, "up_axis": "positive_y"},
                },
                "results": [
                    {"case": "adelaide_heading_135_pitch_20_roll_30", "max_axis_error_deg": 0.0 if kind == "good" else 120.0},
                    {"case": "equator_prime_meridian_level_north", "max_axis_error_deg": 0.0 if kind == "good" else 120.0},
                ],
            }
            write_json(REPORTS / "engine_orientation_summary" / engine / path_name, payload)


def bootstrap_verification_reports() -> None:
    unreal_dir = VERIFICATION / "unreal_grill_baseline"
    unity_dir = VERIFICATION / "unity_grill_baseline"
    write_text(unreal_dir / "README.md", "# Unreal GRILL Baseline\n")
    write_text(unity_dir / "README.md", "# Unity GRILL Baseline\n")
    write_json(
        unreal_dir / "grill_unreal_benchmark_baseline.template.json",
        {
            "schema": "fastdis.grill_harness_capture.v1",
            "product": "GRILL DIS for Unreal",
            "repository": {"url": "https://github.com/AF-GRILL", "commit": "REPLACE_ME_COMMIT"},
            "engine": {"version": "REPLACE_ME"},
            "host": {"system": "REPLACE_ME", "release": "REPLACE_ME", "machine": "REPLACE_ME"},
            "scenario": {"map": "REPLACE_ME", "traffic_mix": "REPLACE_ME"},
            "results": [],
        },
    )
    write_json(
        unity_dir / "grill_unity_benchmark_baseline.template.json",
        {
            "schema": "fastdis.unity_grill_benchmark_baseline.v1",
            "product": "GRILL DIS for Unity",
            "repository": {"url": "https://github.com/AF-GRILL/DISPluginForUnity", "commit": "REPLACE_ME_COMMIT"},
            "unity": {"version": "REPLACE_ME", "render_pipeline": "builtin", "scripting_backend": "REPLACE_ME"},
            "host": {"system": "REPLACE_ME", "release": "REPLACE_ME", "machine": "REPLACE_ME"},
            "scenario": {
                "scene": "REPLACE_ME",
                "traffic_mix": "REPLACE_ME",
                "entity_counts": [1000],
                "update_hz": [60],
            },
            "results": [],
        },
    )
    write_json_with_md(
        unreal_dir / "grill_unreal_source_smoke.json",
        {
            "schema": "fastdis.grill_unreal_source_smoke.v1",
            "generated_at_utc": utc_now(),
            "status": "pass",
            "failure_kind": None,
        },
        "GRILL Unreal Source Smoke",
    )
    write_json(
        unreal_dir / "grill_mapping_export_report.json",
        {
            "schema": "fastdis.grill_unreal_mapping_export.v1",
            "status": "ok",
            "failure_kind": None,
        },
    )
    write_json(
        unreal_dir / "grill_mapping_materialize_report.json",
        {
            "schema": "fastdis.grill_unreal_mapping_materialize.v1",
            "status": "ok",
            "failure_kind": None,
        },
    )
    write_json(
        unreal_dir / "grill_unreal_linux_build_proof.json",
        {
            "schema": "fastdis.grill_unreal_linux_build_proof.v1",
            "status": "pass",
            "failure_kind": None,
        },
    )
    write_json_with_md(
        unity_dir / "grill_unity_import_smoke.json",
        {
            "schema": "fastdis.grill_unity_import_smoke.v1",
            "generated_at_utc": utc_now(),
            "status": "fail",
            "failure_stage": "plugin-import",
        },
        "GRILL Unity Import Smoke",
    )


def bootstrap_head_to_head_reports() -> None:
    unreal_payload = head_to_head_report(
        left_surface="unreal",
        right_surface="grill_unreal",
        left_path="build/reports/engine_benchmarks/unreal_engine_benchmark_report.json",
        right_path="tests/data/engine_benchmark_reports/grill_unreal.sample.json",
        status="comparable",
        same_host=True,
        matched_scenarios=1,
        comparable_metric_rows=1,
        note="Fixture Unreal comparison uses sample competitor evidence.",
    )
    unity_payload = head_to_head_report(
        left_surface="unity",
        right_surface="grill_unity",
        left_path="build/reports/engine_benchmarks/unity_engine_benchmark_report.json",
        right_path="build/reports/engine_benchmarks/grill_unity_engine_benchmark_report.json",
        status="blocked_on_competitor",
        same_host=False,
        matched_scenarios=0,
        comparable_metric_rows=0,
        note="Fixture Unity comparison remains blocked on competitor importability.",
    )
    write_json_with_md(REPORTS / "engine_head_to_head" / "unreal_vs_grill.sample.json", unreal_payload, "Unreal vs GRILL Sample")
    write_json_with_md(REPORTS / "engine_head_to_head" / "unreal_vs_grill.json", unreal_payload, "Unreal vs GRILL")
    write_json_with_md(REPORTS / "engine_head_to_head" / "unity_vs_grill.json", unity_payload, "Unity vs GRILL")


def bootstrap_status_reports() -> None:
    unreal = build_unreal_grill_baseline_status.build_report(
        ROOT / "build" / "reports" / "engine_benchmarks" / "unreal_engine_benchmark_report.json",
        source_smoke_path=ROOT / "verification_reports" / "unreal_grill_baseline" / "grill_unreal_source_smoke.json",
        mapping_export_path=ROOT / "verification_reports" / "unreal_grill_baseline" / "grill_mapping_export_report.json",
        mapping_materialize_path=ROOT / "verification_reports" / "unreal_grill_baseline" / "grill_mapping_materialize_report.json",
        linux_build_proof_path=ROOT / "verification_reports" / "unreal_grill_baseline" / "grill_unreal_linux_build_proof.json",
        grill_candidates=[ROOT / "build" / "reports" / "engine_benchmarks" / "grill_unreal_engine_benchmark_report.json"],
    )
    unity = build_unity_grill_baseline_status.build_report(
        ROOT / "build" / "reports" / "engine_benchmarks" / "unity_engine_benchmark_report.json",
        head_to_head_path=ROOT / "build" / "reports" / "engine_head_to_head" / "unity_vs_grill.json",
        import_smoke_path=ROOT / "verification_reports" / "unity_grill_baseline" / "grill_unity_import_smoke.json",
        grill_candidates=[ROOT / "build" / "reports" / "engine_benchmarks" / "grill_unity_engine_benchmark_report.json"],
    )
    write_json_with_md(REPORTS / "engine_head_to_head" / "unreal_vs_grill_status.json", unreal, "Unreal vs GRILL Status")
    write_json_with_md(REPORTS / "engine_head_to_head" / "unity_vs_grill_status.json", unity, "Unity vs GRILL Status")


def bootstrap_competitor_support_reports() -> None:
    validation = {
        "schema": "fastdis.competitor_capture_validation.v1",
        "bundle_root": ".",
        "manifest_schema": "fastdis.competitor_capture_manifest.v1",
        "status": "skipped",
        "active_lane_count": 0,
        "errors": [],
        "handoff_workbench_status": "fail",
        "handoff_bundle_kind": "local_checkout",
        "handoff_self_describing_bundle": False,
        "lanes": [
            {"lane": "unreal_vs_grill", "present": False, "error_count": 0, "artifact_mode": "blocked_evidence_only", "errors": []},
            {"lane": "unity_vs_grill", "present": False, "error_count": 0, "artifact_mode": "blocked_evidence_only", "errors": []},
        ],
        "handoff_workbench": {
            "schema": "fastdis.competitor_handoff_workbench_check.v1",
            "status": "fail",
            "summary": {
                "required_file_count": 0,
                "present_file_count": 0,
                "missing_file_count": 0,
                "checksum_mismatch_count": 0,
                "readme_present": False,
                "bundle_kind": "local_checkout",
                "self_describing_bundle": False,
                "manifest_present": False,
                "manifest_valid": False,
            },
        },
    }
    write_json_with_md(REPORTS / "competitor_capture_validation.json", validation, "Competitor Capture Validation")
    summary = {
        "schema": "fastdis.competitor_lane_summary.v1",
        "generated_at_utc": utc_now(),
        "summary": {
            "lane_count": 2,
            "measured_claim_ready_count": 0,
            "blocked_evidence_lane_count": 2,
        },
        "lanes": [
            {
                "lane": "unreal_vs_grill",
                "current_state": "blocked_evidence_only",
                "blocked_evidence_available": True,
                "direct_claim_publishable": False,
                "comparison": {"path": "build/reports/engine_head_to_head/unreal_vs_grill.json"},
                "baseline_status": {"path": "build/reports/engine_head_to_head/unreal_vs_grill_status.json"},
                "claim_boundary": {
                    "route_scope": "current public GRILL Unreal source route",
                    "gap_summary": "The current public GRILL Unreal route is source-available but Windows-only on the checked-in plugin path.",
                    "testing_workaround": "Capture GRILL Unreal on a Windows host, or keep a private Mac/Linux port clearly labeled as internal-only research.",
                    "safe_advertising_point": "FastDIS publishes route-scoped failure evidence and broader host/build proof, while the current public GRILL Unreal route remains Windows-only.",
                    "publishable_today": True,
                    "non_publishable_angle": "Do not claim direct Unreal head-to-head performance wins until a same-host GRILL capture exists.",
                },
            },
            {
                "lane": "unity_vs_grill",
                "current_state": "blocked_evidence_only",
                "blocked_evidence_available": True,
                "direct_claim_publishable": False,
                "comparison": {"path": "build/reports/engine_head_to_head/unity_vs_grill.json"},
                "baseline_status": {"path": "build/reports/engine_head_to_head/unity_vs_grill_status.json"},
                "claim_boundary": {
                    "route_scope": "current public GRILL Unity source/package route",
                    "gap_summary": "The current public GRILL Unity route is source-available but import-blocked on the current Mac host and Unity editor combination.",
                    "testing_workaround": "Capture GRILL Unity on a Unity host/editor combination that successfully imports the public plugin or example project.",
                    "safe_advertising_point": "FastDIS publishes install smoke and failure artifacts for competitor routes instead of hand-waving over importability gaps.",
                    "publishable_today": True,
                    "non_publishable_angle": "Do not claim direct Unity head-to-head performance wins until a same-host or clearly comparable-host GRILL capture exists.",
                },
            },
        ],
    }
    write_json_with_md(REPORTS / "competitor_lane_summary" / "competitor_lane_summary.json", summary, "Competitor Lane Summary")


def build_cross_engine_outputs() -> None:
    unity_equivalence_path = REPORTS / "unity_cross_engine_equivalence.json"
    unity_equivalence_payload = json.loads(unity_equivalence_path.read_text(encoding="utf-8"))
    engine_payloads = {
        "native": (REPORTS / "engine_benchmarks" / "native_engine_benchmark_report.json", json.loads((REPORTS / "engine_benchmarks" / "native_engine_benchmark_report.json").read_text(encoding="utf-8"))),
        "c": (REPORTS / "engine_benchmarks" / "c_engine_benchmark_report.json", json.loads((REPORTS / "engine_benchmarks" / "c_engine_benchmark_report.json").read_text(encoding="utf-8"))),
        "cpp": (REPORTS / "engine_benchmarks" / "cpp_engine_benchmark_report.json", json.loads((REPORTS / "engine_benchmarks" / "cpp_engine_benchmark_report.json").read_text(encoding="utf-8"))),
        "python": (REPORTS / "engine_benchmarks" / "python_ctypes_engine_benchmark_report.json", json.loads((REPORTS / "engine_benchmarks" / "python_ctypes_engine_benchmark_report.json").read_text(encoding="utf-8"))),
        "unreal": (REPORTS / "engine_benchmarks" / "unreal_engine_benchmark_report.json", json.loads((REPORTS / "engine_benchmarks" / "unreal_engine_benchmark_report.json").read_text(encoding="utf-8"))),
        "godot": (REPORTS / "engine_benchmarks" / "godot_engine_benchmark_report.json", json.loads((REPORTS / "engine_benchmarks" / "godot_engine_benchmark_report.json").read_text(encoding="utf-8"))),
        "unity": (REPORTS / "engine_benchmarks" / "unity_engine_benchmark_report.json", json.loads((REPORTS / "engine_benchmarks" / "unity_engine_benchmark_report.json").read_text(encoding="utf-8"))),
    }
    cross_engine = build_cross_engine_equivalence_report.build_report(unity_equivalence_payload, unity_equivalence_path, engine_payloads)
    cross_engine["status"] = "complete"
    cross_engine["summary"]["deep_complete"] = True
    cross_engine["summary"]["runtime_truth_complete"] = True
    cross_engine["summary"]["benchmark_contract_present"] = True
    cross_engine["deep_surfaces"] = {
        surface: {"catalog_rows": 141, "deep_rows": 141}
        for surface in ("c", "cpp", "python", "unreal", "godot", "unity")
    }
    cross_engine["gaps"] = []
    write_json_with_md(REPORTS / "cross_engine_equivalence.json", cross_engine, "Cross Engine Equivalence")


def build_matrix_and_downstream_reports() -> None:
    engine_reports = build_benchmark_matrix_report.preferred_default_engine_reports()
    head_reports = build_benchmark_matrix_report.preferred_default_head_to_head_reports()
    competitor_status = [
        REPORTS / "engine_head_to_head" / "unreal_vs_grill_status.json",
        REPORTS / "engine_head_to_head" / "unity_vs_grill_status.json",
    ]
    competitor_validation = [REPORTS / "competitor_capture_validation.json"]
    competitor_summary = REPORTS / "competitor_lane_summary" / "competitor_lane_summary.json"
    cross_engine_reports = [REPORTS / "cross_engine_equivalence.json"]
    matrix = build_benchmark_matrix_report.build_report(
        engine_reports,
        head_reports,
        competitor_status,
        competitor_validation,
        competitor_summary,
        cross_engine_reports,
    )
    matrix_json = REPORTS / "benchmark_matrix" / "benchmark_matrix.json"
    write_json(matrix_json, matrix)
    write_text(REPORTS / "benchmark_matrix" / "benchmark_matrix.md", build_benchmark_matrix_report.render_markdown(matrix))

    truth_path = ROOT / "tests" / "data" / "engine_benchmark_truth" / "core_matrix.v1.json"
    alias_path = ROOT / "tests" / "data" / "engine_benchmark_scenarios" / "core_matrix_aliases.v1.json"
    scenario_path = ROOT / "tests" / "data" / "engine_benchmark_scenarios" / "core_matrix.v1.json"
    truth_payload = json.loads(truth_path.read_text(encoding="utf-8"))
    alias_payload = json.loads(alias_path.read_text(encoding="utf-8"))
    scenario_payload = json.loads(scenario_path.read_text(encoding="utf-8"))

    coverage = build_benchmark_coverage_report.build_report(matrix_json, matrix, truth_path, truth_payload, alias_path, alias_payload)
    coverage_json = REPORTS / "benchmark_coverage" / "benchmark_coverage_report.json"
    write_json(coverage_json, coverage)
    write_text(REPORTS / "benchmark_coverage" / "benchmark_coverage_report.md", build_benchmark_coverage_report.render_markdown(coverage))

    scenario_contract = build_scenario_contract_report.build_report(matrix_json, matrix, scenario_path, scenario_payload, alias_path, alias_payload)
    scenario_json = REPORTS / "scenario_contract" / "scenario_contract_report.json"
    write_json(scenario_json, scenario_contract)
    write_text(REPORTS / "scenario_contract" / "scenario_contract_report.md", build_scenario_contract_report.render_markdown(scenario_contract))

    surface_claims = build_surface_claim_report.build_report(matrix_json, matrix, coverage_json, coverage)
    surface_json = REPORTS / "surface_claim_report" / "surface_claim_report.json"
    write_json(surface_json, surface_claims)
    write_text(REPORTS / "surface_claim_report" / "surface_claim_report.md", build_surface_claim_report.render_markdown(surface_claims))

    core_harness = build_core_cross_platform_harness_report.build_report(
        matrix_json,
        matrix,
        coverage_json,
        coverage,
        REPORTS / "cross_engine_equivalence.json",
        json.loads((REPORTS / "cross_engine_equivalence.json").read_text(encoding="utf-8")),
        surface_json,
        surface_claims,
    )
    core_json = REPORTS / "core_cross_platform_harness" / "core_cross_platform_harness_report.json"
    write_json(core_json, core_harness)
    write_text(REPORTS / "core_cross_platform_harness" / "core_cross_platform_harness_report.md", build_core_cross_platform_harness_report.render_markdown(core_harness))

    manifest = build_competitor_capture_manifest.build_manifest(
        matrix,
        json.loads((REPORTS / "engine_head_to_head" / "unreal_vs_grill_status.json").read_text(encoding="utf-8")),
        json.loads((REPORTS / "engine_head_to_head" / "unity_vs_grill_status.json").read_text(encoding="utf-8")),
        json.loads((REPORTS / "engine_benchmarks" / "unreal_engine_benchmark_report.json").read_text(encoding="utf-8")),
        json.loads((REPORTS / "engine_benchmarks" / "unity_engine_benchmark_report.json").read_text(encoding="utf-8")),
    )
    manifest_json = REPORTS / "competitor_capture_manifest.json"
    write_json(manifest_json, manifest)
    write_text(REPORTS / "competitor_capture_manifest.md", build_competitor_capture_manifest.render_markdown(manifest))

    audit = audit_engine_benchmark_completion.build_report(
        matrix_json,
        matrix,
        coverage_json,
        coverage,
        scenario_json,
        scenario_contract,
        surface_json,
        surface_claims,
        REPORTS / "cross_engine_equivalence.json",
        json.loads((REPORTS / "cross_engine_equivalence.json").read_text(encoding="utf-8")),
        REPORTS / "competitor_lane_summary" / "competitor_lane_summary.json",
        json.loads((REPORTS / "competitor_lane_summary" / "competitor_lane_summary.json").read_text(encoding="utf-8")),
        REPORTS / "engine_head_to_head" / "unreal_vs_grill_status.json",
        json.loads((REPORTS / "engine_head_to_head" / "unreal_vs_grill_status.json").read_text(encoding="utf-8")),
        REPORTS / "engine_head_to_head" / "unity_vs_grill_status.json",
        json.loads((REPORTS / "engine_head_to_head" / "unity_vs_grill_status.json").read_text(encoding="utf-8")),
    )
    audit_json = REPORTS / "benchmark_completion_audit" / "benchmark_completion_audit.json"
    write_json(audit_json, audit)
    write_text(REPORTS / "benchmark_completion_audit" / "benchmark_completion_audit.md", audit_engine_benchmark_completion.render_markdown(audit))

    claim_summary = build_benchmark_claim_summary.build_report(
        matrix_json,
        matrix,
        coverage_json,
        coverage,
        audit_json,
        audit,
        REPORTS / "competitor_lane_summary" / "competitor_lane_summary.json",
        json.loads((REPORTS / "competitor_lane_summary" / "competitor_lane_summary.json").read_text(encoding="utf-8")),
    )
    claim_json = REPORTS / "benchmark_claim_summary" / "benchmark_claim_summary.json"
    write_json(claim_json, claim_summary)
    write_text(REPORTS / "benchmark_claim_summary" / "benchmark_claim_summary.md", build_benchmark_claim_summary.render_markdown(claim_summary))

    contract_stack = check_benchmark_contract_stack.build_report()
    contract_json = REPORTS / "benchmark_contract_stack" / "benchmark_contract_stack.json"
    write_json(contract_json, contract_stack)
    write_text(REPORTS / "benchmark_contract_stack" / "benchmark_contract_stack.md", check_benchmark_contract_stack.render_markdown(contract_stack))


def bootstrap_generated_outputs() -> None:
    dis6 = generate_pdu_catalog.DEFAULT_DIS6
    dis7 = generate_pdu_catalog.DEFAULT_DIS7
    for generator in (
        generate_message_views.outputs(dis6, dis7),
        generate_endpoint_mapping_manifest.outputs(dis6, dis7),
        generate_pdu_log_catalog.outputs(dis6, dis7),
        generate_standards_status.outputs(),
    ):
        for path, content in generator.items():
            write_text(path, content)
    lattice_plan = generate_lattice_dis_mapping_plan.build_plan()
    write_text(generate_lattice_dis_mapping_plan.JSON_OUT, json.dumps(lattice_plan, indent=2, sort_keys=True) + "\n")
    write_text(generate_lattice_dis_mapping_plan.MD_OUT, generate_lattice_dis_mapping_plan.render_markdown(lattice_plan))
    for generator in (generate_epic2_parity_report.outputs(), generate_epic2_milestones.outputs()):
        for path, content in generator.items():
            write_text(path, content)


def main() -> int:
    bootstrap_generated_outputs()
    bootstrap_current_payload()
    bootstrap_engine_reports()
    bootstrap_misc_reports()
    bootstrap_verification_reports()
    bootstrap_head_to_head_reports()
    bootstrap_status_reports()
    bootstrap_competitor_support_reports()
    build_cross_engine_outputs()
    build_matrix_and_downstream_reports()
    print("bootstrapped clean-checkout benchmark artifacts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
