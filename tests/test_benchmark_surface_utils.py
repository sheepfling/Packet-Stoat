from __future__ import annotations

from pathlib import Path
import sys


TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import benchmark_surface_utils as utils


def test_build_scaffold_rows_prefers_shared_case_order() -> None:
    payload = {
        "native": {
            "results": [
                {"case": "header_filter_90pct_reject", "packets": 1000, "avg_ms": 0.5},
                {"case": "entity_state_1x10hz", "packets": 24, "avg_ms": 0.02},
                {"case": "header_all_no_callback", "packets": 1000, "avg_ms": 0.4},
            ]
        }
    }
    rows = utils.build_scaffold_rows(
        payload,
        limit_cases=3,
        default_row={"case": "fallback"},
        row_builder=lambda row: {"case": row["case"]},
    )
    assert [row["case"] for row in rows] == [
        "header_all_no_callback",
        "entity_state_1x10hz",
        "header_filter_90pct_reject",
    ]


def test_report_summary_counts_shared_metrics() -> None:
    rows = [
        {"metrics": {"main_thread_apply_ms": None, "runtime_elapsed_seconds": None}, "truth": {"final_truth_match": True}},
        {"metrics": {"main_thread_apply_ms": 0.5, "runtime_elapsed_seconds": None}, "truth": {"final_truth_match": True}},
        {"metrics": {"main_thread_apply_ms": None, "runtime_elapsed_seconds": 4.0}, "truth": {"final_truth_match": None}},
    ]
    assert utils.report_summary(rows) == {
        "row_count": 3,
        "latency_rows": 1,
        "runtime_metric_rows": 1,
        "truth_rows": 2,
    }
