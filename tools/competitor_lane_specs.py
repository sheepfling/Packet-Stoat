#!/usr/bin/env python3
"""Shared lane descriptors for competitor/GRILL capture workflows."""

from __future__ import annotations

from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = Path("artifacts")
VERIFICATION_REPORTS = ARTIFACTS / "verification_reports"
ENGINE_BENCHMARKS = ARTIFACTS / "reports" / "engine_benchmarks"
HEAD_TO_HEAD = ARTIFACTS / "reports" / "engine_head_to_head"


LANE_SPECS: dict[str, dict[str, Any]] = {
    "unreal_vs_grill": {
        "surface": "grill_unreal",
        "host_version_key": "engine_version",
        "version_path": ("engine", "version"),
        "fastdis_report": ENGINE_BENCHMARKS / "unreal_engine_benchmark_report.json",
        "raw_baseline": VERIFICATION_REPORTS / "unreal_grill_baseline" / "grill_unreal_benchmark_baseline.json",
        "blocked_smoke": VERIFICATION_REPORTS / "unreal_grill_baseline" / "grill_unreal_source_smoke.json",
        "blocked_smoke_md": VERIFICATION_REPORTS / "unreal_grill_baseline" / "grill_unreal_source_smoke.md",
        "normalized_report": ENGINE_BENCHMARKS / "grill_unreal_engine_benchmark_report.json",
        "normalized_report_md": ENGINE_BENCHMARKS / "grill_unreal_engine_benchmark_report.md",
        "head_to_head": HEAD_TO_HEAD / "unreal_vs_grill.json",
        "head_to_head_md": HEAD_TO_HEAD / "unreal_vs_grill.md",
        "status_report": HEAD_TO_HEAD / "unreal_vs_grill_status.json",
        "status_report_md": HEAD_TO_HEAD / "unreal_vs_grill_status.md",
        "required_capture_fields": [
            "host.system",
            "host.machine",
            "engine.version",
            "scenario.map",
            "scenario.traffic_mix",
            "results[].scenario",
            "results[].packets_per_sec",
            "results[].main_thread_apply_ms",
        ],
    },
    "unity_vs_grill": {
        "surface": "grill_unity",
        "host_version_key": "unity_version",
        "version_path": ("unity", "version"),
        "fastdis_report": ENGINE_BENCHMARKS / "unity_engine_benchmark_report.json",
        "raw_baseline": VERIFICATION_REPORTS / "unity_grill_baseline" / "grill_unity_benchmark_baseline.json",
        "blocked_smoke": VERIFICATION_REPORTS / "unity_grill_baseline" / "grill_unity_import_smoke.json",
        "blocked_smoke_md": VERIFICATION_REPORTS / "unity_grill_baseline" / "grill_unity_import_smoke.md",
        "normalized_report": ENGINE_BENCHMARKS / "grill_unity_engine_benchmark_report.json",
        "normalized_report_md": ENGINE_BENCHMARKS / "grill_unity_engine_benchmark_report.md",
        "head_to_head": HEAD_TO_HEAD / "unity_vs_grill.json",
        "head_to_head_md": HEAD_TO_HEAD / "unity_vs_grill.md",
        "status_report": HEAD_TO_HEAD / "unity_vs_grill_status.json",
        "status_report_md": HEAD_TO_HEAD / "unity_vs_grill_status.md",
        "required_capture_fields": [
            "host.system",
            "host.machine",
            "unity.version",
            "scenario.scene",
            "scenario.traffic_mix",
            "results[].case",
            "results[].packets_per_sec",
            "results[].main_thread_ms_avg",
            "results[].gc_alloc_bytes_per_frame",
        ],
    },
}


def lane_spec(lane_name: str) -> dict[str, Any]:
    return dict(LANE_SPECS[lane_name])


def lane_required_return_artifacts(lane_name: str) -> list[str]:
    spec = LANE_SPECS[lane_name]
    return [
        spec["blocked_smoke"].as_posix(),
        spec["blocked_smoke_md"].as_posix(),
        spec["raw_baseline"].as_posix(),
        spec["normalized_report"].as_posix(),
        spec["normalized_report_md"].as_posix(),
        spec["head_to_head"].as_posix(),
        spec["head_to_head_md"].as_posix(),
        spec["status_report"].as_posix(),
        spec["status_report_md"].as_posix(),
    ]
