from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def test_build_core_cross_platform_harness_report_complete(tmp_path: Path) -> None:
    module = _load_module("build_core_cross_platform_harness_report", ROOT / "tools" / "build_core_cross_platform_harness_report.py")
    matrix = {
        "surfaces": [
            {"surface": "native", "surface_kind": "native", "evidence_kind": "measured_or_verified", "path": "native.json", "scenario_count": 3, "scenarios": ["header_filter_90pct_reject"], "latency_rows": 4, "runtime_metric_rows": 1, "truth_rows": 3},
            {"surface": "c", "surface_kind": "c", "evidence_kind": "measured_or_verified", "path": "c.json", "scenario_count": 3, "scenarios": ["entity_state_1x10hz"], "latency_rows": 0, "runtime_metric_rows": 1, "truth_rows": 3},
            {"surface": "cpp", "surface_kind": "cpp", "evidence_kind": "measured_or_verified", "path": "cpp.json", "scenario_count": 3, "scenarios": ["entity_state_100x30hz"], "latency_rows": 0, "runtime_metric_rows": 1, "truth_rows": 3},
            {"surface": "python_ctypes", "surface_kind": "python", "evidence_kind": "measured_or_verified", "path": "python.json", "scenario_count": 3, "scenarios": ["ctypes_entity_table_ingest_latest"], "latency_rows": 4, "runtime_metric_rows": 1, "truth_rows": 3},
            {"surface": "godot", "surface_kind": "engine", "evidence_kind": "measured_or_verified", "path": "godot.json", "scenario_count": 3, "scenarios": ["godot_replay_latest_state_apply"], "latency_rows": 0, "runtime_metric_rows": 1, "truth_rows": 3},
        ]
    }
    coverage = {
        "surfaces": [
            {"surface": "native", "capabilities": {"ingest": {"covered": True, "shared_contract_covered": True}, "filtering": {"covered": True, "shared_contract_covered": True}, "latest_state": {"covered": True, "shared_contract_covered": True}, "replay": {"covered": True, "shared_contract_covered": True, "shared_contract_defined": True}, "engine_runtime": {"covered": False}}},
            {"surface": "c", "capabilities": {"ingest": {"covered": True, "shared_contract_covered": True}, "filtering": {"covered": True, "shared_contract_covered": True}, "latest_state": {"covered": True, "shared_contract_covered": True}, "replay": {"covered": True, "shared_contract_covered": True, "shared_contract_defined": True}, "engine_runtime": {"covered": False}}},
            {"surface": "cpp", "capabilities": {"ingest": {"covered": True, "shared_contract_covered": True}, "filtering": {"covered": True, "shared_contract_covered": True}, "latest_state": {"covered": True, "shared_contract_covered": True}, "replay": {"covered": True, "shared_contract_covered": True, "shared_contract_defined": True}, "engine_runtime": {"covered": False}}},
            {"surface": "python_ctypes", "capabilities": {"ingest": {"covered": True, "shared_contract_covered": True}, "filtering": {"covered": True, "shared_contract_covered": True}, "latest_state": {"covered": True, "shared_contract_covered": True}, "replay": {"covered": True, "shared_contract_covered": True, "shared_contract_defined": True}, "engine_runtime": {"covered": False}}},
            {"surface": "godot", "capabilities": {"ingest": {"covered": True, "shared_contract_covered": True}, "filtering": {"covered": True, "shared_contract_covered": True}, "latest_state": {"covered": True, "shared_contract_covered": True}, "replay": {"covered": True, "shared_contract_covered": True, "shared_contract_defined": True}, "engine_runtime": {"covered": True}}},
        ]
    }
    cross_engine = {
        "summary": {"benchmark_contract_present": True},
        "deep_surfaces": {
            "c": {"catalog_rows": 141, "deep_rows": 141},
            "cpp": {"catalog_rows": 141, "deep_rows": 141},
            "python": {"catalog_rows": 141, "deep_rows": 141},
            "godot": {"catalog_rows": 141, "deep_rows": 141},
        },
        "benchmark_surfaces": [
            {"surface": "native", "verified_truth_rows": 3},
            {"surface": "c", "verified_truth_rows": 3},
            {"surface": "cpp", "verified_truth_rows": 3},
            {"surface": "python", "verified_truth_rows": 3},
            {"surface": "godot", "verified_truth_rows": 2},
        ],
    }
    surface_claims = {
        "surfaces": [
            {"surface": "native", "safe_claims": ["native ingest"], "boundaries": ["native replay not covered"]},
            {"surface": "c", "safe_claims": ["c truth"], "boundaries": []},
            {"surface": "cpp", "safe_claims": ["cpp truth"], "boundaries": []},
            {"surface": "python_ctypes", "safe_claims": ["python truth"], "boundaries": []},
            {"surface": "godot", "safe_claims": ["godot replay"], "boundaries": []},
        ]
    }

    report = module.build_report(
        tmp_path / "matrix.json",
        matrix,
        tmp_path / "coverage.json",
        coverage,
        tmp_path / "cross_engine.json",
        cross_engine,
        tmp_path / "surface_claims.json",
        surface_claims,
    )

    assert report["schema"] == "fastdis.core_cross_platform_harness_report.v1"
    assert report["status"] == "complete"
    assert report["summary"]["required_surface_complete_count"] == 4
    assert report["summary"]["verified_truth_surface_count"] == 5
    assert report["summary"]["deep_equivalence_complete"] is True
    assert report["summary"]["replay_present"] is True
    assert report["summary"]["shared_contract_replay_defined"] is True
    assert any(row["surface"] == "godot" and row["role"] == "adapter_proof_bridge" for row in report["surfaces"])


def test_build_core_cross_platform_harness_report_partial_when_truth_missing(tmp_path: Path) -> None:
    module = _load_module("build_core_cross_platform_harness_report", ROOT / "tools" / "build_core_cross_platform_harness_report.py")
    matrix = {
        "surfaces": [
            {"surface": "native", "surface_kind": "native", "evidence_kind": "measured_or_verified", "path": "native.json", "scenario_count": 1, "scenarios": ["header_filter_90pct_reject"], "latency_rows": 1, "runtime_metric_rows": 0, "truth_rows": 1},
            {"surface": "c", "surface_kind": "c", "evidence_kind": "measured_or_verified", "path": "c.json", "scenario_count": 1, "scenarios": ["entity_state_1x10hz"], "latency_rows": 0, "runtime_metric_rows": 1, "truth_rows": 1},
        ]
    }
    coverage = {
        "surfaces": [
            {"surface": "native", "capabilities": {"ingest": {"covered": True, "shared_contract_covered": True}, "filtering": {"covered": False, "shared_contract_covered": False}, "latest_state": {"covered": False, "shared_contract_covered": False}, "replay": {"covered": False, "shared_contract_covered": False, "shared_contract_defined": False}, "engine_runtime": {"covered": False}}},
            {"surface": "c", "capabilities": {"ingest": {"covered": True, "shared_contract_covered": True}, "filtering": {"covered": False, "shared_contract_covered": False}, "latest_state": {"covered": False, "shared_contract_covered": False}, "replay": {"covered": False, "shared_contract_covered": False, "shared_contract_defined": False}, "engine_runtime": {"covered": False}}},
        ]
    }
    cross_engine = {
        "summary": {"benchmark_contract_present": False},
        "deep_surfaces": {"c": {"catalog_rows": 141, "deep_rows": 141}},
        "benchmark_surfaces": [{"surface": "native", "verified_truth_rows": 1}],
    }
    surface_claims = {"surfaces": [{"surface": "native", "safe_claims": [], "boundaries": []}]}

    report = module.build_report(
        tmp_path / "matrix.json",
        matrix,
        tmp_path / "coverage.json",
        coverage,
        tmp_path / "cross_engine.json",
        cross_engine,
        tmp_path / "surface_claims.json",
        surface_claims,
    )

    assert report["status"] == "partial"
    assert report["summary"]["required_surface_complete_count"] == 0
    assert any("missing for: cpp, python_ctypes, godot" in gap for gap in report["gaps"])
    assert any("shared-scenario coverage" in gap for gap in report["gaps"])


def test_core_cross_platform_harness_report_cli_writes_outputs(tmp_path: Path) -> None:
    matrix_path = _write(
        tmp_path / "benchmark_matrix.json",
        {
            "surfaces": [
                {"surface": "native", "surface_kind": "native", "evidence_kind": "measured_or_verified", "path": "native.json", "scenario_count": 1, "scenarios": ["header_filter_90pct_reject"], "latency_rows": 1, "runtime_metric_rows": 0, "truth_rows": 1},
                {"surface": "c", "surface_kind": "c", "evidence_kind": "measured_or_verified", "path": "c.json", "scenario_count": 1, "scenarios": ["entity_state_1x10hz"], "latency_rows": 0, "runtime_metric_rows": 1, "truth_rows": 1},
                {"surface": "cpp", "surface_kind": "cpp", "evidence_kind": "measured_or_verified", "path": "cpp.json", "scenario_count": 1, "scenarios": ["entity_state_100x30hz"], "latency_rows": 0, "runtime_metric_rows": 1, "truth_rows": 1},
                {"surface": "python_ctypes", "surface_kind": "python", "evidence_kind": "measured_or_verified", "path": "python.json", "scenario_count": 1, "scenarios": ["ctypes_entity_table_ingest_latest"], "latency_rows": 1, "runtime_metric_rows": 0, "truth_rows": 1},
                {"surface": "godot", "surface_kind": "engine", "evidence_kind": "measured_or_verified", "path": "godot.json", "scenario_count": 1, "scenarios": ["godot_replay_latest_state_apply"], "latency_rows": 0, "runtime_metric_rows": 1, "truth_rows": 1},
            ]
        },
    )
    coverage_path = _write(
        tmp_path / "benchmark_coverage_report.json",
        {
            "surfaces": [
                {"surface": "native", "capabilities": {"ingest": {"covered": True, "shared_contract_covered": True}, "filtering": {"covered": True, "shared_contract_covered": True}, "latest_state": {"covered": True, "shared_contract_covered": True}, "replay": {"covered": False, "shared_contract_covered": False, "shared_contract_defined": False}, "engine_runtime": {"covered": False}}},
                {"surface": "c", "capabilities": {"ingest": {"covered": True, "shared_contract_covered": True}, "filtering": {"covered": False, "shared_contract_covered": False}, "latest_state": {"covered": False, "shared_contract_covered": False}, "replay": {"covered": False, "shared_contract_covered": False, "shared_contract_defined": False}, "engine_runtime": {"covered": False}}},
                {"surface": "cpp", "capabilities": {"ingest": {"covered": True, "shared_contract_covered": True}, "filtering": {"covered": False, "shared_contract_covered": False}, "latest_state": {"covered": False, "shared_contract_covered": False}, "replay": {"covered": False, "shared_contract_covered": False, "shared_contract_defined": False}, "engine_runtime": {"covered": False}}},
                {"surface": "python_ctypes", "capabilities": {"ingest": {"covered": True, "shared_contract_covered": True}, "filtering": {"covered": True, "shared_contract_covered": True}, "latest_state": {"covered": True, "shared_contract_covered": True}, "replay": {"covered": False, "shared_contract_covered": False, "shared_contract_defined": False}, "engine_runtime": {"covered": False}}},
                {"surface": "godot", "capabilities": {"ingest": {"covered": True, "shared_contract_covered": True}, "filtering": {"covered": False, "shared_contract_covered": False}, "latest_state": {"covered": True, "shared_contract_covered": True}, "replay": {"covered": True, "shared_contract_covered": False, "shared_contract_defined": False}, "engine_runtime": {"covered": True}}},
            ]
        },
    )
    cross_path = _write(
        tmp_path / "cross_engine_equivalence.json",
        {
            "summary": {"benchmark_contract_present": True},
            "deep_surfaces": {
                "c": {"catalog_rows": 141, "deep_rows": 141},
                "cpp": {"catalog_rows": 141, "deep_rows": 141},
                "python": {"catalog_rows": 141, "deep_rows": 141},
                "godot": {"catalog_rows": 141, "deep_rows": 141},
            },
            "benchmark_surfaces": [
                {"surface": "native", "verified_truth_rows": 1},
                {"surface": "c", "verified_truth_rows": 1},
                {"surface": "cpp", "verified_truth_rows": 1},
                {"surface": "python", "verified_truth_rows": 1},
                {"surface": "godot", "verified_truth_rows": 1},
            ],
        },
    )
    claims_path = _write(
        tmp_path / "surface_claim_report.json",
        {
            "surfaces": [
                {"surface": "native", "safe_claims": [], "boundaries": []},
                {"surface": "c", "safe_claims": [], "boundaries": []},
                {"surface": "cpp", "safe_claims": [], "boundaries": []},
                {"surface": "python_ctypes", "safe_claims": [], "boundaries": []},
                {"surface": "godot", "safe_claims": [], "boundaries": []},
            ]
        },
    )
    json_out = tmp_path / "out" / "core_cross_platform_harness_report.json"
    md_out = tmp_path / "out" / "core_cross_platform_harness_report.md"

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "build_core_cross_platform_harness_report.py"),
            "--matrix",
            str(matrix_path),
            "--coverage",
            str(coverage_path),
            "--cross-engine",
            str(cross_path),
            "--surface-claims",
            str(claims_path),
            "--json-out",
            str(json_out),
            "--md-out",
            str(md_out),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    payload = json.loads(json_out.read_text(encoding="utf-8"))
    assert payload["schema"] == "fastdis.core_cross_platform_harness_report.v1"
    assert "Core Cross-Platform Harness Report" in md_out.read_text(encoding="utf-8")
