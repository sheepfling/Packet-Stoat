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


def test_build_benchmark_coverage_report_summarizes_capabilities(tmp_path: Path) -> None:
    module = _load_module("build_benchmark_coverage_report", ROOT / "tools" / "build_benchmark_coverage_report.py")
    matrix = {
        "surfaces": [
            {"surface": "native", "surface_kind": "native", "path": "native.json", "latency_rows": 2, "runtime_metric_rows": 0, "scenarios": ["header_filter_90pct_reject", "entity_state_1x10hz", "snapshot_publish_changed"], "truth_supported_scenarios": ["entity_state_1x10hz"]},
            {"surface": "c", "surface_kind": "c", "path": "c.json", "latency_rows": 0, "runtime_metric_rows": 1, "scenarios": ["entity_state_1x10hz"], "truth_supported_scenarios": ["entity_state_1x10hz"]},
            {"surface": "cpp", "surface_kind": "cpp", "path": "cpp.json", "latency_rows": 2, "runtime_metric_rows": 0, "scenarios": ["filter_reject_90pct"], "truth_supported_scenarios": ["filter_reject_90pct"]},
            {"surface": "python_ctypes", "surface_kind": "python_ctypes", "path": "py.json", "latency_rows": 2, "runtime_metric_rows": 0, "scenarios": ["ctypes_entity_force_reject_no_callback", "entity_state_100x30hz"], "truth_supported_scenarios": ["entity_state_100x30hz"]},
            {"surface": "unity", "surface_kind": "engine", "path": "unity.json", "latency_rows": 2, "runtime_metric_rows": 0, "scenarios": ["unity_replay_latest_state_apply"]},
            {"surface": "unreal", "surface_kind": "engine", "path": "unreal.json", "latency_rows": 2, "runtime_metric_rows": 0, "scenarios": ["unreal_replay_latest_state_apply"]},
            {"surface": "godot", "surface_kind": "engine", "path": "godot.json", "latency_rows": 2, "runtime_metric_rows": 0, "scenarios": ["godot_replay_latest_state_apply"]},
        ]
    }
    truth = {
        "truths": [
            {"scenario": "entity_state_1x10hz", "expectations": {"latest_state_required": True, "replay_final_transform_required": False}},
            {"scenario": "entity_state_100x30hz", "expectations": {"latest_state_required": True, "replay_final_transform_required": False}},
            {"scenario": "filter_reject_90pct", "expectations": {"latest_state_required": False, "replay_final_transform_required": False}},
        ]
    }
    aliases = {
        "aliases": [
            {"surface": "native", "observed": "header_filter_90pct_reject", "canonical": "filter_reject_90pct", "alignment": "family"},
            {"surface": "python_ctypes", "observed": "ctypes_entity_force_reject_no_callback", "canonical": "filter_reject_90pct", "alignment": "family"},
        ]
    }

    report = module.build_report(tmp_path / "benchmark_matrix.json", matrix, tmp_path / "truth.json", truth, tmp_path / "aliases.json", aliases)

    assert report["schema"] == "fastdis.benchmark_coverage_report.v1"
    assert report["status"] == "complete"
    assert report["summary"]["ingest"]["surface_count"] >= 4
    assert report["summary"]["filtering"]["surface_count"] >= 1
    assert report["summary"]["latest_state"]["surface_count"] >= 1
    assert report["summary"]["replay"]["surface_count"] >= 1
    assert report["summary"]["latest_state"]["shared_contract_surface_count"] >= 2
    assert set(report["summary"]["engine_runtime"]["surfaces"]) == {"unreal", "unity", "godot"}
    c_row = next(row for row in report["surfaces"] if row["surface"] == "c")
    assert c_row["capabilities"]["latest_state"]["shared_contract_covered"] is True
    python_row = next(row for row in report["surfaces"] if row["surface"] == "python_ctypes")
    assert python_row["capabilities"]["filtering"]["family_scenarios"] == ["filter_reject_90pct"]


def test_benchmark_coverage_report_cli_writes_outputs(tmp_path: Path) -> None:
    matrix_path = _write(
        tmp_path / "benchmark_matrix.json",
        {
            "surfaces": [
                {"surface": "native", "surface_kind": "native", "path": "native.json", "latency_rows": 1, "runtime_metric_rows": 0, "scenarios": ["header_filter_90pct_reject"], "truth_supported_scenarios": []},
            ]
        },
    )
    truth_path = _write(
        tmp_path / "truth.json",
        {
            "truths": [
                {"scenario": "filter_reject_90pct", "expectations": {"latest_state_required": False, "replay_final_transform_required": False}},
            ]
        },
    )
    aliases_path = _write(
        tmp_path / "aliases.json",
        {
            "aliases": [
                {"surface": "native", "observed": "header_filter_90pct_reject", "canonical": "filter_reject_90pct", "alignment": "family"},
            ]
        },
    )
    json_out = tmp_path / "out" / "benchmark_coverage_report.json"
    md_out = tmp_path / "out" / "benchmark_coverage_report.md"

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "build_benchmark_coverage_report.py"),
            "--matrix",
            str(matrix_path),
            "--truth",
            str(truth_path),
            "--aliases",
            str(aliases_path),
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
    assert payload["schema"] == "fastdis.benchmark_coverage_report.v1"
    assert "Benchmark Coverage Report" in md_out.read_text(encoding="utf-8")
