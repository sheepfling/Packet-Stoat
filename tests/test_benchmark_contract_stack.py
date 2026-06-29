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


def test_build_benchmark_contract_stack_report_passes_with_current_artifacts() -> None:
    module = _load_module("check_benchmark_contract_stack", ROOT / "tools" / "check_benchmark_contract_stack.py")

    report = module.build_report()

    assert report["schema"] == "fastdis.benchmark_contract_stack.v1"
    assert report["status"] == "pass"
    assert report["summary"]["schema_count"] >= 15
    assert report["summary"]["artifact_count"] >= 13
    assert report["summary"]["fail_count"] == 0
    assert report["summary"]["missing_count"] == 0
    assert any(row["kind"] == "schema" and row["expected_schema"] == "fastdis.engine_benchmark_report.v1" for row in report["rows"])
    assert any(
        row["kind"] == "schema"
        and row["path"] == "schemas/json/fastdis.grill_harness_capture.v1.schema.json"
        and row["expected_schema"] == "fastdis.grill_harness_capture.v1"
        for row in report["rows"]
    )
    assert any(
        row["kind"] == "schema"
        and row["path"] == "schemas/json/fastdis.proof_context.v1.schema.json"
        and row["expected_schema"] == "fastdis.proof_context.v1"
        for row in report["rows"]
    )
    assert any(
        row["kind"] == "schema"
        and row["path"] == "schemas/json/fastdis.competitor_benchmark_handoff_manifest.v1.schema.json"
        and row["expected_schema"] == "fastdis.competitor_benchmark_handoff_manifest.v1"
        for row in report["rows"]
    )
    assert any(
        row["kind"] == "artifact"
        and row["path"] == "build/reports/benchmark_coverage/benchmark_coverage_report.json"
        and row["expected_schema"] == "fastdis.benchmark_coverage_report.v1"
        for row in report["rows"]
    )
    assert any(
        row["kind"] == "artifact"
        and row["path"] == "build/reports/scenario_contract/scenario_contract_report.json"
        and row["expected_schema"] == "fastdis.scenario_contract_report.v1"
        for row in report["rows"]
    )
    assert any(
        row["kind"] == "artifact"
        and row["path"] == "build/reports/surface_claim_report/surface_claim_report.json"
        and row["expected_schema"] == "fastdis.surface_claim_report.v1"
        for row in report["rows"]
    )
    assert any(
        row["kind"] == "artifact"
        and row["path"] == "build/reports/core_cross_platform_harness/core_cross_platform_harness_report.json"
        and row["expected_schema"] == "fastdis.core_cross_platform_harness_report.v1"
        for row in report["rows"]
    )
    assert any(
        row["kind"] == "artifact"
        and row["path"] == "build/reports/competitor_lane_summary/competitor_lane_summary.json"
        and row["expected_schema"] == "fastdis.competitor_lane_summary.v1"
        for row in report["rows"]
    )
    assert any(row["kind"] == "artifact" and row["path"] == "build/reports/benchmark_matrix/benchmark_matrix.json" for row in report["rows"])


def test_benchmark_contract_stack_cli_writes_outputs(tmp_path: Path) -> None:
    json_out = tmp_path / "benchmark_contract_stack.json"
    md_out = tmp_path / "benchmark_contract_stack.md"
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "check_benchmark_contract_stack.py"),
            "--json-out",
            str(json_out),
            "--md-out",
            str(md_out),
            "--fail-missing",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert json_out.is_file()
    assert md_out.is_file()
    payload = json.loads(json_out.read_text(encoding="utf-8"))
    assert payload["schema"] == "fastdis.benchmark_contract_stack.v1"
    assert payload["status"] == "pass"
    assert "Benchmark Contract Stack" in md_out.read_text(encoding="utf-8")
