from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_collect_measured_throughput_uses_best_packets_per_second(tmp_path: Path) -> None:
    module = _load_module("render_benchmark_storefront_charts", ROOT / "tools" / "render_benchmark_storefront_charts.py")

    report_dir = tmp_path / "engine_benchmarks"
    report_dir.mkdir()
    (report_dir / "native_engine_benchmark_report.json").write_text(
        json.dumps(
            {
                "rows": [
                    {"scenario": "slow", "metrics": {"packets_per_sec": 1000.0}},
                    {"scenario": "fast", "metrics": {"packets_per_sec": 2500.0}},
                ]
            }
        ),
        encoding="utf-8",
    )
    (report_dir / "unity_engine_benchmark_report.json").write_text(
        json.dumps(
            {
                "rows": [
                    {"scenario": "entity_state_1x10hz", "metrics": {"packets_per_sec": 900.0}},
                ]
            }
        ),
        encoding="utf-8",
    )

    rows = module.collect_measured_throughput(report_dir)

    assert rows[0]["surface"] == "native"
    assert rows[0]["scenario"] == "fast"
    assert rows[0]["packets_per_sec"] == 2500.0
    assert rows[1]["surface"] == "unity"


def test_collect_surface_coverage_reads_matrix_rows(tmp_path: Path) -> None:
    module = _load_module("render_benchmark_storefront_charts", ROOT / "tools" / "render_benchmark_storefront_charts.py")

    matrix_path = tmp_path / "benchmark_matrix.json"
    matrix_path.write_text(
        json.dumps(
            {
                "surfaces": [
                    {"surface": "native", "row_count": 4, "runtime_metric_rows": 2, "truth_rows": 1},
                    {"surface": "unity", "row_count": 3, "runtime_metric_rows": 1, "truth_rows": 3},
                ]
            }
        ),
        encoding="utf-8",
    )

    rows = module.collect_surface_coverage(matrix_path)

    assert rows == [
        {"surface": "native", "label": "Native", "row_count": 4, "runtime_metric_rows": 2, "truth_rows": 1},
        {"surface": "unity", "label": "Unity", "row_count": 3, "runtime_metric_rows": 1, "truth_rows": 3},
    ]


def test_extract_unity_head_to_head_reads_comparable_metrics(tmp_path: Path) -> None:
    module = _load_module("render_benchmark_storefront_charts", ROOT / "tools" / "render_benchmark_storefront_charts.py")

    report_path = tmp_path / "unity_vs_grill.json"
    report_path.write_text(
        json.dumps(
            {
                "comparison": {
                    "same_host": True,
                    "status": "comparable",
                    "left_label": "FastDIS Unity",
                    "right_label": "GRILL Unity",
                    "rows": [
                        {
                            "scenario": "entity_state_1x10hz",
                            "metrics": {
                                "packets_per_sec": {"left": 10.0, "right": 2.0, "ratio": 5.0},
                                "main_thread_apply_ms": {"left": 1.0, "right": 4.0, "ratio": 4.0},
                                "steady_state_gc_bytes": {"left": 0, "right": 12, "ratio": None},
                            },
                        }
                    ],
                }
            }
        ),
        encoding="utf-8",
    )

    summary = module.extract_unity_head_to_head(report_path)

    assert summary["same_host"] is True
    assert summary["packets_per_sec"]["ratio"] == 5.0
    assert summary["steady_state_gc_bytes"]["right"] == 12


def test_build_manifest_records_expected_chart_paths(tmp_path: Path) -> None:
    module = _load_module("render_benchmark_storefront_charts", ROOT / "tools" / "render_benchmark_storefront_charts.py")

    manifest = module.build_manifest(
        [{"surface": "native", "label": "Native", "scenario": "fast", "packets_per_sec": 1.0}],
        [{"surface": "native", "label": "Native", "row_count": 1, "runtime_metric_rows": 1, "truth_rows": 1}],
        {"scenario": "entity_state_1x10hz", "same_host": True, "status": "comparable"},
        tmp_path,
    )

    assert manifest["schema"] == "fastdis.storefront_benchmark_chart_manifest.v1"
    assert manifest["charts"][0]["name"] == "measured_throughput_by_surface"
    assert manifest["charts"][2]["present"] is True
