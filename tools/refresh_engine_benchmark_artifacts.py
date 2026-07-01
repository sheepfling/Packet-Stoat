#!/usr/bin/env python3
"""Refresh the current shared engine benchmark artifact set.

Operator guidance:
- Use `--list-steps` first to preview the exact commands for the current host.
- Use `--core-only` when the host only has core/native/Godot lanes available.
- The script continues after failures so downstream reports can still capture
  blocked evidence. Always check the final exit code and the generated reports.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys

import load_local_env


ROOT = Path(__file__).resolve().parents[1]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog=(
            "Examples:\n"
            "  python tools/refresh_engine_benchmark_artifacts.py --list-steps\n"
            "  python tools/refresh_engine_benchmark_artifacts.py --core-only\n"
            "  python tools/refresh_engine_benchmark_artifacts.py\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--list-steps",
        action="store_true",
        help="Print the exact commands that would run, then exit without executing them",
    )
    parser.add_argument(
        "--core-only",
        action="store_true",
        help="Refresh only the shared core c/cpp/python_ctypes/godot lane and its downstream reports",
    )
    parser.add_argument("--skip-native-canonical", action="store_true", help="Skip tools/run_native_canonical_benchmark.py --if-available")
    parser.add_argument("--skip-run-benchmarks", action="store_true", help="Skip tools/run_benchmarks.py --format json --out-dir artifacts/benchmark_results/current")
    parser.add_argument("--skip-current-benchmarks", action="store_true", help="Skip tools/normalize_current_benchmarks.py")
    parser.add_argument("--skip-network-ingest-matrix", action="store_true", help="Skip tools/run_network_ingest_matrix.py --if-available")
    parser.add_argument("--skip-network-ingest-normalize", action="store_true", help="Skip tools/normalize_network_ingest_matrix.py")
    parser.add_argument("--skip-core-filter-matrix", action="store_true", help="Skip tools/run_core_filter_matrix.py --if-available")
    parser.add_argument("--skip-core-filter-normalize", action="store_true", help="Skip tools/normalize_core_filter_matrix.py")
    parser.add_argument("--skip-core-replay-matrix", action="store_true", help="Skip tools/run_core_replay_matrix.py --if-available")
    parser.add_argument("--skip-core-replay-normalize", action="store_true", help="Skip tools/normalize_core_replay_matrix.py")
    parser.add_argument("--skip-unreal-grill-baseline", action="store_true", help="Skip tools/normalize_unreal_grill_baseline.py")
    parser.add_argument("--skip-unity-grill-baseline", action="store_true", help="Skip tools/normalize_unity_grill_baseline.py")
    parser.add_argument("--skip-unreal-proof", action="store_true", help="Skip tools/normalize_unreal_proof_reports.py")
    parser.add_argument("--skip-godot-proof", action="store_true", help="Skip tools/normalize_godot_proof_reports.py")
    parser.add_argument("--skip-unity-proof", action="store_true", help="Skip tools/normalize_unity_runtime_verification.py")
    parser.add_argument("--skip-cross-engine-equivalence", action="store_true", help="Skip tools/build_cross_engine_equivalence_report.py")
    parser.add_argument("--skip-unreal-compare", action="store_true", help="Skip tools/run_unreal_grill_benchmark.py --if-available")
    parser.add_argument("--skip-unity-compare", action="store_true", help="Skip tools/run_unity_grill_benchmark.py --if-available")
    parser.add_argument("--skip-unreal-status", action="store_true", help="Skip tools/build_unreal_grill_baseline_status.py")
    parser.add_argument("--skip-unity-status", action="store_true", help="Skip tools/build_unity_grill_baseline_status.py")
    parser.add_argument("--skip-competitor-manifest", action="store_true", help="Skip tools/build_competitor_capture_manifest.py")
    parser.add_argument("--skip-competitor-validation", action="store_true", help="Skip tools/validate_competitor_capture_bundle.py . --if-available")
    parser.add_argument("--skip-matrix", action="store_true", help="Skip tools/build_benchmark_matrix_report.py")
    parser.add_argument("--skip-coverage", action="store_true", help="Skip tools/build_benchmark_coverage_report.py")
    parser.add_argument("--skip-scenario-contract", action="store_true", help="Skip tools/build_scenario_contract_report.py")
    parser.add_argument("--skip-surface-claims", action="store_true", help="Skip tools/build_surface_claim_report.py")
    parser.add_argument("--skip-core-cross-platform-harness", action="store_true", help="Skip tools/build_core_cross_platform_harness_report.py")
    parser.add_argument("--skip-completion-audit", action="store_true", help="Skip tools/audit_engine_benchmark_completion.py")
    parser.add_argument("--skip-claim-summary", action="store_true", help="Skip tools/build_benchmark_claim_summary.py")
    parser.add_argument("--skip-competitor-lane-summary", action="store_true", help="Skip tools/build_competitor_lane_summary.py")
    parser.add_argument("--skip-contract-check", action="store_true", help="Skip tools/check_benchmark_contract_stack.py --fail-missing")
    return parser.parse_args(argv)


def run_step(cmd: list[str]) -> int:
    print("+", " ".join(cmd))
    completed = subprocess.run(cmd, cwd=ROOT)
    return completed.returncode


def render_steps(steps: list[list[str]]) -> list[str]:
    return [" ".join(cmd) for cmd in steps]


def build_steps(args: argparse.Namespace) -> list[list[str]]:
    py = [sys.executable]
    steps: list[list[str]] = []
    core_only = bool(args.core_only)
    if not args.skip_native_canonical:
        steps.append(py + ["tools/run_native_canonical_benchmark.py", "--if-available"])
    if not args.skip_run_benchmarks:
        steps.append(py + ["tools/run_benchmarks.py", "--format", "json", "--out-dir", "artifacts/benchmark_results/current"])
    if not args.skip_current_benchmarks:
        steps.append(py + ["tools/normalize_current_benchmarks.py"])
    if not args.skip_network_ingest_matrix:
        network_ingest_cmd = py + ["tools/run_network_ingest_matrix.py", "--if-available", "--out-dir", "artifacts/reports/network_ingest_matrix"]
        if core_only:
            network_ingest_cmd.append("--core-only")
        steps.append(network_ingest_cmd)
    if not args.skip_network_ingest_normalize:
        steps.append(py + ["tools/normalize_network_ingest_matrix.py", "--input", "artifacts/reports/network_ingest_matrix/network_ingest_matrix.json"])
    if not args.skip_core_filter_matrix:
        steps.append(py + ["tools/run_core_filter_matrix.py", "--if-available", "--out-dir", "artifacts/reports/core_filter_matrix"])
    if not args.skip_core_filter_normalize:
        steps.append(py + ["tools/normalize_core_filter_matrix.py", "--input", "artifacts/reports/core_filter_matrix/core_filter_matrix.json"])
    if not args.skip_core_replay_matrix:
        steps.append(py + ["tools/run_core_replay_matrix.py", "--if-available", "--out-dir", "artifacts/reports/core_replay_matrix"])
    if not args.skip_core_replay_normalize:
        steps.append(py + ["tools/normalize_core_replay_matrix.py", "--input", "artifacts/reports/core_replay_matrix/core_replay_matrix.json"])
    if not core_only and not args.skip_unreal_grill_baseline:
        steps.append(py + ["tools/normalize_grill_harness_capture.py", "--input", "verification_reports/unreal_grill_baseline/grill_unreal_benchmark_baseline.json"])
    if not core_only and not args.skip_unity_grill_baseline:
        steps.append(py + ["tools/normalize_grill_harness_capture.py", "--input", "verification_reports/unity_grill_baseline/grill_unity_benchmark_baseline.json"])
    if not core_only and not args.skip_unreal_proof:
        steps.append(py + ["tools/normalize_unreal_proof_reports.py"])
    if not args.skip_godot_proof:
        steps.append(py + ["tools/normalize_godot_proof_reports.py"])
    if not core_only and not args.skip_unity_proof:
        steps.append(py + ["tools/normalize_unity_runtime_verification.py"])
    if not core_only and not args.skip_cross_engine_equivalence:
        steps.append(py + ["tools/build_cross_engine_equivalence_report.py"])
    if not core_only and not args.skip_unreal_compare:
        steps.append(py + ["tools/run_unreal_grill_benchmark.py", "--if-available"])
    if not core_only and not args.skip_unity_compare:
        steps.append(py + ["tools/run_unity_grill_benchmark.py", "--if-available"])
    if not core_only and not args.skip_unreal_status:
        steps.append(py + ["tools/build_unreal_grill_baseline_status.py"])
    if not core_only and not args.skip_unity_status:
        steps.append(py + ["tools/build_unity_grill_baseline_status.py"])
    if not core_only and not args.skip_competitor_manifest:
        steps.append(py + ["tools/build_competitor_capture_manifest.py"])
    if not core_only and not args.skip_competitor_validation:
        steps.append(py + ["tools/validate_competitor_capture_bundle.py", ".", "--if-available"])
    if not args.skip_matrix:
        steps.append(py + ["tools/build_benchmark_matrix_report.py"])
    if not args.skip_coverage:
        steps.append(py + ["tools/build_benchmark_coverage_report.py"])
    if not args.skip_scenario_contract:
        steps.append(py + ["tools/build_scenario_contract_report.py"])
    if not args.skip_surface_claims:
        steps.append(py + ["tools/build_surface_claim_report.py"])
    if not args.skip_core_cross_platform_harness:
        steps.append(py + ["tools/build_core_cross_platform_harness_report.py"])
    if not core_only and not args.skip_completion_audit:
        steps.append(py + ["tools/audit_engine_benchmark_completion.py"])
    if not core_only and not args.skip_claim_summary:
        steps.append(py + ["tools/build_benchmark_claim_summary.py"])
    if not core_only and not args.skip_competitor_lane_summary:
        steps.append(py + ["tools/build_competitor_lane_summary.py"])
    if not core_only and not args.skip_contract_check:
        steps.append(py + ["tools/check_benchmark_contract_stack.py", "--fail-missing"])
    return steps


def main(argv: list[str] | None = None) -> int:
    load_local_env.load()
    args = parse_args(argv)
    steps = build_steps(args)
    if args.list_steps:
        print("# refresh_engine_benchmark_artifacts planned steps")
        for index, rendered in enumerate(render_steps(steps), start=1):
            print(f"{index}. {rendered}")
        return 0
    final_code = 0
    for cmd in steps:
        code = run_step(cmd)
        if code != 0 and final_code == 0:
            final_code = code
    if final_code == 0:
        print("refresh complete: all steps exited with code 0")
    else:
        print(f"refresh complete: first failing step exit code = {final_code}")
    return final_code


if __name__ == "__main__":
    raise SystemExit(main())
