from __future__ import annotations

import json
from pathlib import Path
import sys
import zipfile


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import export_competitor_benchmark_handoff
import refresh_engine_benchmark_artifacts


def test_export_competitor_benchmark_handoff_archive_contains_expected_payload(tmp_path: Path) -> None:
    archive_path = tmp_path / "out" / f"fastdis-competitor-benchmark-handoff-{export_competitor_benchmark_handoff.package_stamp()}.zip"

    export_competitor_benchmark_handoff.export_archive(archive_path)

    assert archive_path.is_file()
    prefix = f"fastdis-competitor-benchmark-handoff-{export_competitor_benchmark_handoff.package_stamp()}/"
    with zipfile.ZipFile(archive_path) as archive:
        names = set(archive.namelist())
        assert prefix + "README.md" in names
        assert prefix + "MANIFEST.json" in names
        assert prefix + "tools/build_competitor_capture_manifest.py" in names
        assert prefix + "tools/validate_competitor_capture_bundle.py" in names
        assert prefix + "tools/check_competitor_handoff_workbench.py" in names
        assert prefix + "tools/init_unreal_grill_benchmark_baseline.py" in names
        assert prefix + "tools/init_unity_grill_benchmark_baseline.py" in names
        assert prefix + "tools/run_grill_unreal_source_smoke.py" in names
        assert prefix + "tools/run_grill_unity_import_smoke.py" in names
        assert prefix + "tools/build_unreal_grill_baseline_status.py" in names
        assert prefix + "tools/build_unity_grill_baseline_status.py" in names
        assert prefix + "tools/build_benchmark_coverage_report.py" in names
        assert prefix + "tools/build_scenario_contract_report.py" in names
        assert prefix + "tools/build_surface_claim_report.py" in names
        assert prefix + "tools/build_competitor_lane_summary.py" in names
        assert prefix + "tools/normalize_current_benchmarks.py" in names
        assert prefix + "tools/run_network_ingest_matrix.py" in names
        assert prefix + "tools/normalize_network_ingest_matrix.py" in names
        assert prefix + "tools/normalize_unreal_grill_baseline.py" in names
        assert prefix + "tools/normalize_unity_grill_baseline.py" in names
        assert prefix + "tools/normalize_unreal_proof_reports.py" in names
        assert prefix + "tools/normalize_godot_proof_reports.py" in names
        assert prefix + "tools/normalize_unity_runtime_verification.py" in names
        assert prefix + "tools/run_unreal_grill_benchmark.py" in names
        assert prefix + "tools/run_unity_grill_benchmark.py" in names
        assert prefix + "tools/refresh_engine_benchmark_artifacts.py" in names
        assert prefix + "tools/build_cross_engine_equivalence_report.py" in names
        assert prefix + "tools/audit_engine_benchmark_completion.py" in names
        assert prefix + "tools/build_benchmark_claim_summary.py" in names
        assert prefix + "schemas/json/fastdis.engine_benchmark_report.v1.schema.json" in names
        assert prefix + "schemas/json/fastdis.engine_head_to_head_report.v1.schema.json" in names
        assert prefix + "schemas/json/fastdis.engine_benchmark_matrix.v1.schema.json" in names
        assert prefix + "schemas/json/fastdis.benchmark_coverage_report.v1.schema.json" in names
        assert prefix + "schemas/json/fastdis.scenario_contract_report.v1.schema.json" in names
        assert prefix + "schemas/json/fastdis.surface_claim_report.v1.schema.json" in names
        assert prefix + "schemas/json/fastdis.benchmark_claim_summary.v1.schema.json" in names
        assert prefix + "schemas/json/fastdis.competitor_lane_summary.v1.schema.json" in names
        assert prefix + "schemas/json/fastdis.competitor_benchmark_handoff_manifest.v1.schema.json" in names
        assert prefix + "schemas/json/fastdis.competitor_capture_validation.v1.schema.json" in names
        assert prefix + "tests/data/engine_benchmark_scenarios/core_matrix.v1.json" in names
        assert prefix + "tests/data/engine_benchmark_truth/core_matrix.v1.json" in names
        assert prefix + "docs/research/GRILL_COMPARISON_POLICY.md" in names
        assert prefix + "docs/research/grill_source_route.md" in names
        assert prefix + "verification_reports/unreal_grill_baseline/grill_unreal_benchmark_baseline.template.json" in names
        assert prefix + "verification_reports/unity_grill_baseline/grill_unity_benchmark_baseline.template.json" in names
        assert prefix + "verification_reports/unreal_grill_baseline/grill_unreal_source_smoke.json" in names
        assert prefix + "verification_reports/unreal_grill_baseline/grill_unreal_source_smoke.md" in names
        assert prefix + "verification_reports/unity_grill_baseline/grill_unity_import_smoke.json" in names
        assert prefix + "verification_reports/unity_grill_baseline/grill_unity_import_smoke.md" in names
        assert prefix + "build/benchmark_results/current/current.json" in names
        assert prefix + "build/reports/engine_benchmarks/native_engine_benchmark_report.md" in names
        assert prefix + "build/reports/engine_benchmarks/c_engine_benchmark_report.json" in names
        assert prefix + "build/reports/engine_benchmarks/c_engine_benchmark_report.md" in names
        assert prefix + "build/reports/engine_benchmarks/cpp_engine_benchmark_report.json" in names
        assert prefix + "build/reports/engine_benchmarks/cpp_engine_benchmark_report.md" in names
        assert prefix + "build/reports/engine_benchmarks/python_ctypes_engine_benchmark_report.md" in names
        assert prefix + "build/reports/engine_benchmarks/unreal_engine_benchmark_report.md" in names
        assert prefix + "build/reports/engine_benchmarks/unity_engine_benchmark_report.md" in names
        assert prefix + "build/reports/engine_benchmarks/godot_engine_benchmark_report.md" in names
        assert prefix + "build/reports/network_ingest_matrix/network_ingest_matrix.json" in names
        assert prefix + "build/reports/network_ingest_matrix/network_ingest_matrix.md" in names
        assert prefix + "build/reports/cross_engine_equivalence.md" in names
        assert prefix + "build/reports/unity_cross_engine_equivalence.json" in names
        assert prefix + "build/reports/unity_cross_engine_equivalence.md" in names
        assert prefix + "build/reports/benchmark_matrix/benchmark_matrix.json" in names
        assert prefix + "build/reports/benchmark_matrix/benchmark_matrix.md" in names
        assert prefix + "build/reports/benchmark_coverage/benchmark_coverage_report.json" in names
        assert prefix + "build/reports/benchmark_coverage/benchmark_coverage_report.md" in names
        assert prefix + "build/reports/scenario_contract/scenario_contract_report.json" in names
        assert prefix + "build/reports/scenario_contract/scenario_contract_report.md" in names
        assert prefix + "build/reports/surface_claim_report/surface_claim_report.json" in names
        assert prefix + "build/reports/surface_claim_report/surface_claim_report.md" in names
        assert prefix + "build/reports/engine_head_to_head/unreal_vs_grill_status.json" in names
        assert prefix + "build/reports/engine_head_to_head/unreal_vs_grill_status.md" in names
        assert prefix + "build/reports/engine_head_to_head/unity_vs_grill_status.json" in names
        assert prefix + "build/reports/engine_head_to_head/unity_vs_grill_status.md" in names
        assert prefix + "build/reports/competitor_capture_manifest.json" in names
        assert prefix + "build/reports/competitor_capture_manifest.md" in names
        assert prefix + "build/reports/competitor_capture_validation.json" in names
        assert prefix + "build/reports/competitor_capture_validation.md" in names
        assert prefix + "build/reports/benchmark_completion_audit/benchmark_completion_audit.json" in names
        assert prefix + "build/reports/benchmark_completion_audit/benchmark_completion_audit.md" in names
        assert prefix + "build/reports/benchmark_claim_summary/benchmark_claim_summary.json" in names
        assert prefix + "build/reports/benchmark_claim_summary/benchmark_claim_summary.md" in names
        assert prefix + "build/reports/competitor_lane_summary/competitor_lane_summary.json" in names
        assert prefix + "build/reports/competitor_lane_summary/competitor_lane_summary.md" in names
        assert prefix + "build/reports/benchmark_contract_stack/benchmark_contract_stack.json" in names
        assert prefix + "build/reports/benchmark_contract_stack/benchmark_contract_stack.md" in names
        readme = archive.read(prefix + "README.md").decode("utf-8")
        assert "build_competitor_capture_manifest.py" in readme
        assert "validate_competitor_capture_bundle.py" in readme
        assert "check_competitor_handoff_workbench.py" in readme
        assert "init_unreal_grill_benchmark_baseline.py" in readme
        assert "init_unity_grill_benchmark_baseline.py" in readme
        assert "run_grill_unreal_source_smoke.py" in readme
        assert "run_grill_unity_import_smoke.py" in readme
        assert "build_unreal_grill_baseline_status.py" in readme
        assert "build_unity_grill_baseline_status.py" in readme
        assert "build_benchmark_coverage_report.py" in readme
        assert "build_scenario_contract_report.py" in readme
        assert "build_surface_claim_report.py" in readme
        assert "build_competitor_lane_summary.py" in readme
        assert "normalize_current_benchmarks.py" in readme or "current benchmark normalization" in readme
        assert "normalize_unreal_grill_baseline.py" in readme
        assert "normalize_unity_grill_baseline.py" in readme
        assert "run_unreal_grill_benchmark.py" in readme
        assert "run_unity_grill_benchmark.py" in readme
        assert "refresh_engine_benchmark_artifacts.py" in readme
        assert "build_cross_engine_equivalence_report.py" in readme
        assert "audit_engine_benchmark_completion.py" in readme
        assert "build_benchmark_claim_summary.py" in readme
        assert "MANIFEST.json" in readme
        assert "native, C, C++, Python, Unreal, Unity, and Godot in both JSON and markdown form" in readme
        assert "localhost UDP ingest matrix artifact in both JSON and markdown form" in readme
        assert "Unity-specific cross-engine equivalence summaries" in readme
        assert "benchmark capability coverage report" in readme
        assert "per-surface claim-boundary report" in readme
        assert "competitor capture validation artifact" in readme
        assert "benchmark completion audit" in readme
        assert "benchmark claim summary" in readme
        assert "competitor lane summary" in readme
        assert "benchmark contract-stack audit" in readme
        assert "check_benchmark_contract_stack.py" in readme
        assert "benchmark contract schema files" in readme
        assert "canonical benchmark scenario suite and truth suite fixtures" in readme
        assert "scenario/truth fixtures" in readme
        assert "shared benchmark refresh entrypoint" in readme
        assert "Preferred: rerun the shared refresh entrypoint" in readme
        assert "proof-bridge tools used by the shared refresh entrypoint" in readme
        assert "benchmark-matrix, coverage, scenario-contract, surface-claim, completion-audit, and claim-summary tools" in readme
        assert "competitor lane summary tool" in readme
        assert "benchmark schema definitions" in readme
        assert "workbench self-check tool" in readme
        assert "import-competitor-handoff" in readme
        assert "source-smoke" in readme
        assert "import-smoke" in readme
        manifest = json.loads(archive.read(prefix + "MANIFEST.json").decode("utf-8"))
        assert manifest["schema"] == "fastdis.competitor_benchmark_handoff_manifest.v1"
        assert manifest["bundle_root"] == prefix.rstrip("/")
        manifest_paths = {entry["path"] for entry in manifest["files"]}
        assert "README.md" in manifest_paths
        assert "tools/check_competitor_handoff_workbench.py" in manifest_paths
        assert "build/reports/benchmark_claim_summary/benchmark_claim_summary.json" in manifest_paths

        refresh_args = export_competitor_benchmark_handoff._refresh_default_args()
        refresh_tools = {
            step[1]
            for step in refresh_engine_benchmark_artifacts.build_steps(refresh_args)
            if len(step) >= 2 and isinstance(step[1], str) and step[1].startswith("tools/")
        }
        for tool_path in refresh_tools:
            assert prefix + tool_path in names
