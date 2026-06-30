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


def test_build_competitor_capture_manifest_contains_lane_requirements(tmp_path: Path) -> None:
    module = _load_module("build_competitor_capture_manifest", ROOT / "tools" / "build_competitor_capture_manifest.py")

    matrix = {"gaps": ["no supported unreal vs grill same-host claim yet"]}
    unreal_status = {"status": "blocked_on_grill_baseline", "blockers": ["missing unreal"]}
    unity_status = {"status": "blocked_on_grill_baseline", "blockers": ["missing unity"]}
    unreal_report = {
        "host": {"system": "Darwin", "engine_version": "5.8"},
        "rows": [{"scenario": "unreal_proof_verification"}, {"scenario": "unreal_packaged_install_runtime"}],
    }
    unity_report = {
        "host": {"system": "Darwin", "unity_version": "6000.5.0f1"},
        "rows": [{"scenario": "unity_runtime_verification"}, {"scenario": "unity_install_smoke_runtime"}],
    }

    manifest = module.build_manifest(matrix, unreal_status, unity_status, unreal_report, unity_report)

    assert manifest["schema"] == "fastdis.competitor_capture_manifest.v1"
    assert manifest["matrix_gaps"] == ["no supported unreal vs grill same-host claim yet"]
    unreal_lane = next(row for row in manifest["lanes"] if row["lane"] == "unreal_vs_grill")
    unity_lane = next(row for row in manifest["lanes"] if row["lane"] == "unity_vs_grill")
    assert "unreal_packaged_install_runtime" in unreal_lane["fastdis_scenarios"]
    assert "unity_install_smoke_runtime" in unity_lane["fastdis_scenarios"]
    assert "artifacts/reports/engine_benchmarks/grill_unreal_engine_benchmark_report.md" in unreal_lane["required_return_artifacts"]
    assert "artifacts/reports/engine_benchmarks/grill_unity_engine_benchmark_report.md" in unity_lane["required_return_artifacts"]
    assert "verification_reports/unreal_grill_baseline/grill_unreal_source_smoke.json" in unreal_lane["required_return_artifacts"]
    assert "verification_reports/unity_grill_baseline/grill_unity_import_smoke.json" in unity_lane["required_return_artifacts"]
    assert "artifacts/reports/engine_head_to_head/unreal_vs_grill.json" in unreal_lane["required_return_artifacts"]
    assert "results[].main_thread_ms_avg" in unity_lane["required_capture_fields"]


def test_build_competitor_capture_manifest_cli_writes_outputs(tmp_path: Path) -> None:
    matrix_path = tmp_path / "benchmark_matrix.json"
    unreal_status_path = tmp_path / "unreal_status.json"
    unity_status_path = tmp_path / "unity_status.json"
    unreal_report_path = tmp_path / "unreal_report.json"
    unity_report_path = tmp_path / "unity_report.json"
    json_out = tmp_path / "out" / "competitor_capture_manifest.json"
    md_out = tmp_path / "out" / "competitor_capture_manifest.md"

    matrix_path.write_text(json.dumps({"gaps": []}) + "\n", encoding="utf-8")
    unreal_status_path.write_text(json.dumps({"status": "blocked_on_grill_baseline", "blockers": ["missing unreal"]}) + "\n", encoding="utf-8")
    unity_status_path.write_text(json.dumps({"status": "blocked_on_grill_baseline", "blockers": ["missing unity"]}) + "\n", encoding="utf-8")
    unreal_report_path.write_text(json.dumps({"rows": [{"scenario": "unreal_proof_verification"}], "host": {"system": "Darwin"}}) + "\n", encoding="utf-8")
    unity_report_path.write_text(json.dumps({"rows": [{"scenario": "unity_runtime_verification"}], "host": {"system": "Darwin"}}) + "\n", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "build_competitor_capture_manifest.py"),
            "--matrix",
            str(matrix_path),
            "--unreal-status",
            str(unreal_status_path),
            "--unity-status",
            str(unity_status_path),
            "--unreal-report",
            str(unreal_report_path),
            "--unity-report",
            str(unity_report_path),
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
    assert json_out.is_file()
    assert md_out.is_file()
    payload = json.loads(json_out.read_text(encoding="utf-8"))
    assert payload["schema"] == "fastdis.competitor_capture_manifest.v1"
    assert "Competitor Capture Manifest" in md_out.read_text(encoding="utf-8")
