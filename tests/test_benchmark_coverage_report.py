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
            {"surface": "native", "surface_kind": "native", "path": "native.json", "latency_rows": 2, "runtime_metric_rows": 0, "scenarios": ["header_filter_90pct_reject", "entity_table_ingest_latest", "snapshot_publish_changed"]},
            {"surface": "c", "surface_kind": "c", "path": "c.json", "latency_rows": 0, "runtime_metric_rows": 1, "scenarios": ["c_localhost_udp_ingest_truth"]},
            {"surface": "cpp", "surface_kind": "cpp", "path": "cpp.json", "latency_rows": 2, "runtime_metric_rows": 0, "scenarios": ["cpp_header_filter_90pct_reject"]},
            {"surface": "python_ctypes", "surface_kind": "python_ctypes", "path": "py.json", "latency_rows": 2, "runtime_metric_rows": 0, "scenarios": ["ctypes_entity_table_ingest_latest"]},
            {"surface": "unity", "surface_kind": "engine", "path": "unity.json", "latency_rows": 2, "runtime_metric_rows": 0, "scenarios": ["unity_replay_latest_state_apply"]},
            {"surface": "unreal", "surface_kind": "engine", "path": "unreal.json", "latency_rows": 2, "runtime_metric_rows": 0, "scenarios": ["unreal_replay_latest_state_apply"]},
            {"surface": "godot", "surface_kind": "engine", "path": "godot.json", "latency_rows": 2, "runtime_metric_rows": 0, "scenarios": ["godot_replay_latest_state_apply"]},
        ]
    }

    report = module.build_report(tmp_path / "benchmark_matrix.json", matrix)

    assert report["schema"] == "fastdis.benchmark_coverage_report.v1"
    assert report["status"] == "complete"
    assert report["summary"]["ingest"]["surface_count"] >= 4
    assert report["summary"]["filtering"]["surface_count"] >= 1
    assert report["summary"]["latest_state"]["surface_count"] >= 1
    assert report["summary"]["replay"]["surface_count"] >= 1
    assert set(report["summary"]["engine_runtime"]["surfaces"]) == {"unreal", "unity", "godot"}


def test_benchmark_coverage_report_cli_writes_outputs(tmp_path: Path) -> None:
    matrix_path = _write(
        tmp_path / "benchmark_matrix.json",
        {
            "surfaces": [
                {"surface": "native", "surface_kind": "native", "path": "native.json", "latency_rows": 1, "runtime_metric_rows": 0, "scenarios": ["header_filter_90pct_reject"]},
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
