#!/usr/bin/env python3
"""Refresh the current shared engine benchmark artifact set."""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys

import load_local_env


ROOT = Path(__file__).resolve().parents[1]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-native-canonical", action="store_true", help="Skip tools/run_native_canonical_benchmark.py --if-available")
    parser.add_argument("--skip-current-benchmarks", action="store_true", help="Skip tools/normalize_current_benchmarks.py")
    parser.add_argument("--skip-network-ingest-matrix", action="store_true", help="Skip tools/run_network_ingest_matrix.py --if-available")
    parser.add_argument("--skip-network-ingest-normalize", action="store_true", help="Skip tools/normalize_network_ingest_matrix.py")
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
    parser.add_argument("--skip-completion-audit", action="store_true", help="Skip tools/audit_engine_benchmark_completion.py")
    parser.add_argument("--skip-claim-summary", action="store_true", help="Skip tools/build_benchmark_claim_summary.py")
    parser.add_argument("--skip-competitor-lane-summary", action="store_true", help="Skip tools/build_competitor_lane_summary.py")
    parser.add_argument("--skip-contract-check", action="store_true", help="Skip tools/check_benchmark_contract_stack.py --fail-missing")
    return parser.parse_args(argv)


def run_step(cmd: list[str]) -> int:
    print("+", " ".join(cmd))
    completed = subprocess.run(cmd, cwd=ROOT)
    return completed.returncode


def build_steps(args: argparse.Namespace) -> list[list[str]]:
    py = [sys.executable]
    steps: list[list[str]] = []
    if not args.skip_native_canonical:
        steps.append(py + ["tools/run_native_canonical_benchmark.py", "--if-available"])
    if not args.skip_current_benchmarks:
        steps.append(py + ["tools/normalize_current_benchmarks.py"])
    if not args.skip_network_ingest_matrix:
        steps.append(py + ["tools/run_network_ingest_matrix.py", "--if-available", "--out-dir", "build/reports/network_ingest_matrix"])
    if not args.skip_network_ingest_normalize:
        steps.append(py + ["tools/normalize_network_ingest_matrix.py", "--input", "build/reports/network_ingest_matrix/network_ingest_matrix.json"])
    if not args.skip_unreal_grill_baseline:
        steps.append(py + ["tools/normalize_unreal_grill_baseline.py"])
    if not args.skip_unity_grill_baseline:
        steps.append(py + ["tools/normalize_unity_grill_baseline.py"])
    if not args.skip_unreal_proof:
        steps.append(py + ["tools/normalize_unreal_proof_reports.py"])
    if not args.skip_godot_proof:
        steps.append(py + ["tools/normalize_godot_proof_reports.py"])
    if not args.skip_unity_proof:
        steps.append(py + ["tools/normalize_unity_runtime_verification.py"])
    if not args.skip_cross_engine_equivalence:
        steps.append(py + ["tools/build_cross_engine_equivalence_report.py"])
    if not args.skip_unreal_compare:
        steps.append(py + ["tools/run_unreal_grill_benchmark.py", "--if-available"])
    if not args.skip_unity_compare:
        steps.append(py + ["tools/run_unity_grill_benchmark.py", "--if-available"])
    if not args.skip_unreal_status:
        steps.append(py + ["tools/build_unreal_grill_baseline_status.py"])
    if not args.skip_unity_status:
        steps.append(py + ["tools/build_unity_grill_baseline_status.py"])
    if not args.skip_competitor_manifest:
        steps.append(py + ["tools/build_competitor_capture_manifest.py"])
    if not args.skip_competitor_validation:
        steps.append(py + ["tools/validate_competitor_capture_bundle.py", ".", "--if-available"])
    if not args.skip_matrix:
        steps.append(py + ["tools/build_benchmark_matrix_report.py"])
    if not args.skip_coverage:
        steps.append(py + ["tools/build_benchmark_coverage_report.py"])
    if not args.skip_scenario_contract:
        steps.append(py + ["tools/build_scenario_contract_report.py"])
    if not args.skip_surface_claims:
        steps.append(py + ["tools/build_surface_claim_report.py"])
    if not args.skip_completion_audit:
        steps.append(py + ["tools/audit_engine_benchmark_completion.py"])
    if not args.skip_claim_summary:
        steps.append(py + ["tools/build_benchmark_claim_summary.py"])
    if not args.skip_competitor_lane_summary:
        steps.append(py + ["tools/build_competitor_lane_summary.py"])
    if not args.skip_contract_check:
        steps.append(py + ["tools/check_benchmark_contract_stack.py", "--fail-missing"])
    return steps


def main(argv: list[str] | None = None) -> int:
    load_local_env.load()
    args = parse_args(argv)
    final_code = 0
    for cmd in build_steps(args):
        code = run_step(cmd)
        if code != 0 and final_code == 0:
            final_code = code
    return final_code


if __name__ == "__main__":
    raise SystemExit(main())
