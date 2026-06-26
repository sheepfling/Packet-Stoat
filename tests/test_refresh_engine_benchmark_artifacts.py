from __future__ import annotations

import sys
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import refresh_engine_benchmark_artifacts


def test_build_steps_defaults_cover_current_refresh_sequence() -> None:
    args = refresh_engine_benchmark_artifacts.argparse.Namespace(
        skip_native_canonical=False,
        skip_current_benchmarks=False,
        skip_network_ingest_matrix=False,
        skip_network_ingest_normalize=False,
        skip_unreal_grill_baseline=False,
        skip_unity_grill_baseline=False,
        skip_unreal_proof=False,
        skip_godot_proof=False,
        skip_unity_proof=False,
        skip_cross_engine_equivalence=False,
        skip_unreal_compare=False,
        skip_unity_compare=False,
        skip_unreal_status=False,
        skip_unity_status=False,
        skip_competitor_manifest=False,
        skip_competitor_validation=False,
        skip_matrix=False,
        skip_coverage=False,
        skip_scenario_contract=False,
        skip_surface_claims=False,
        skip_completion_audit=False,
        skip_claim_summary=False,
        skip_competitor_lane_summary=False,
        skip_contract_check=False,
    )

    steps = refresh_engine_benchmark_artifacts.build_steps(args)

    assert steps == [
        [sys.executable, "tools/run_native_canonical_benchmark.py", "--if-available"],
        [sys.executable, "tools/normalize_current_benchmarks.py"],
        [sys.executable, "tools/run_network_ingest_matrix.py", "--if-available", "--out-dir", "build/reports/network_ingest_matrix"],
        [sys.executable, "tools/normalize_network_ingest_matrix.py", "--input", "build/reports/network_ingest_matrix/network_ingest_matrix.json"],
        [sys.executable, "tools/normalize_unreal_grill_baseline.py"],
        [sys.executable, "tools/normalize_unity_grill_baseline.py"],
        [sys.executable, "tools/normalize_unreal_proof_reports.py"],
        [sys.executable, "tools/normalize_godot_proof_reports.py"],
        [sys.executable, "tools/normalize_unity_runtime_verification.py"],
        [sys.executable, "tools/build_cross_engine_equivalence_report.py"],
        [sys.executable, "tools/run_unreal_grill_benchmark.py", "--if-available"],
        [sys.executable, "tools/run_unity_grill_benchmark.py", "--if-available"],
        [sys.executable, "tools/build_unreal_grill_baseline_status.py"],
        [sys.executable, "tools/build_unity_grill_baseline_status.py"],
        [sys.executable, "tools/build_competitor_capture_manifest.py"],
        [sys.executable, "tools/validate_competitor_capture_bundle.py", ".", "--if-available"],
        [sys.executable, "tools/build_benchmark_matrix_report.py"],
        [sys.executable, "tools/build_benchmark_coverage_report.py"],
        [sys.executable, "tools/build_scenario_contract_report.py"],
        [sys.executable, "tools/build_surface_claim_report.py"],
        [sys.executable, "tools/audit_engine_benchmark_completion.py"],
        [sys.executable, "tools/build_benchmark_claim_summary.py"],
        [sys.executable, "tools/build_competitor_lane_summary.py"],
        [sys.executable, "tools/check_benchmark_contract_stack.py", "--fail-missing"],
    ]


def test_build_steps_respects_skip_flags() -> None:
    args = refresh_engine_benchmark_artifacts.argparse.Namespace(
        skip_native_canonical=True,
        skip_current_benchmarks=True,
        skip_network_ingest_matrix=True,
        skip_network_ingest_normalize=False,
        skip_unreal_grill_baseline=True,
        skip_unity_grill_baseline=True,
        skip_unreal_proof=False,
        skip_godot_proof=True,
        skip_unity_proof=False,
        skip_cross_engine_equivalence=True,
        skip_unreal_compare=True,
        skip_unity_compare=True,
        skip_unreal_status=True,
        skip_unity_status=False,
        skip_competitor_manifest=True,
        skip_competitor_validation=False,
        skip_matrix=False,
        skip_coverage=True,
        skip_scenario_contract=True,
        skip_surface_claims=True,
        skip_completion_audit=True,
        skip_claim_summary=True,
        skip_competitor_lane_summary=True,
        skip_contract_check=True,
    )

    steps = refresh_engine_benchmark_artifacts.build_steps(args)

    assert steps == [
        [sys.executable, "tools/normalize_network_ingest_matrix.py", "--input", "build/reports/network_ingest_matrix/network_ingest_matrix.json"],
        [sys.executable, "tools/normalize_unreal_proof_reports.py"],
        [sys.executable, "tools/normalize_unity_runtime_verification.py"],
        [sys.executable, "tools/build_unity_grill_baseline_status.py"],
        [sys.executable, "tools/validate_competitor_capture_bundle.py", ".", "--if-available"],
        [sys.executable, "tools/build_benchmark_matrix_report.py"],
    ]


def test_main_returns_first_nonzero_exit_and_keeps_refreshing(monkeypatch) -> None:
    args = refresh_engine_benchmark_artifacts.argparse.Namespace(
        skip_native_canonical=False,
        skip_current_benchmarks=False,
        skip_network_ingest_matrix=False,
        skip_network_ingest_normalize=False,
        skip_unreal_grill_baseline=False,
        skip_unity_grill_baseline=False,
        skip_unreal_proof=False,
        skip_godot_proof=False,
        skip_unity_proof=False,
        skip_cross_engine_equivalence=False,
        skip_unreal_compare=False,
        skip_unity_compare=False,
        skip_unreal_status=False,
        skip_unity_status=False,
        skip_competitor_manifest=False,
        skip_competitor_validation=False,
        skip_matrix=False,
        skip_coverage=False,
        skip_scenario_contract=False,
        skip_surface_claims=False,
        skip_completion_audit=False,
        skip_claim_summary=False,
        skip_competitor_lane_summary=False,
        skip_contract_check=False,
    )
    monkeypatch.setattr(refresh_engine_benchmark_artifacts, "parse_args", lambda argv=None: args)
    monkeypatch.setattr(refresh_engine_benchmark_artifacts.load_local_env, "load", lambda: None)
    recorded: list[list[str]] = []
    codes = iter([0, 0, 0, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])

    def fake_run_step(cmd: list[str]) -> int:
        recorded.append(cmd)
        return next(codes)

    monkeypatch.setattr(refresh_engine_benchmark_artifacts, "run_step", fake_run_step)

    rc = refresh_engine_benchmark_artifacts.main()

    assert rc == 3
    assert len(recorded) == 24
    assert recorded[-1] == [sys.executable, "tools/check_benchmark_contract_stack.py", "--fail-missing"]
