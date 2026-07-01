#!/usr/bin/env python3
"""Run the Phase 2 multi-host evidence refresh/import/render workflow."""

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
            "  python tools/run_phase2_evidence_matrix.py --list-steps\n"
            "  python tools/run_phase2_evidence_matrix.py --core-only\n"
            "  python tools/run_phase2_evidence_matrix.py \\\n"
            "    --unity-host-report dist/unity_host_reports/windows-lab-a.zip \\\n"
            "    --competitor-handoff returned-competitor.zip\n"
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
        help="Refresh only the shared core benchmark/proof lanes before storefront rendering",
    )
    parser.add_argument(
        "--unity-host-report",
        action="append",
        default=[],
        help="Portable Unity host bundle archive(s) to import before the refresh",
    )
    parser.add_argument(
        "--alpha2-host-report",
        action="append",
        default=[],
        help="Portable Alpha 2 Unreal/Godot host bundle archive(s) to import before the refresh",
    )
    parser.add_argument(
        "--competitor-handoff",
        action="append",
        default=[],
        help="Returned competitor benchmark handoff archive(s) to import before the refresh",
    )
    parser.add_argument("--skip-refresh", action="store_true", help="Skip tools/refresh_engine_benchmark_artifacts.py")
    parser.add_argument(
        "--refresh-arg",
        action="append",
        default=[],
        help="Extra argument forwarded to tools/refresh_engine_benchmark_artifacts.py; repeat as needed",
    )
    parser.add_argument("--skip-host-summary", action="store_true", help="Skip tools/build_phase2_host_evidence_summary.py")
    parser.add_argument("--skip-benchmark-charts", action="store_true", help="Skip tools/render_benchmark_storefront_charts.py")
    parser.add_argument("--skip-orientation-collages", action="store_true", help="Skip tools/render_orientation_storefront_collages.py")
    return parser.parse_args(argv)


def build_steps(args: argparse.Namespace) -> list[list[str]]:
    py = [sys.executable]
    steps: list[list[str]] = []

    for archive in args.unity_host_report:
        steps.append(py + ["tools/import_unity_host_report.py", archive, "--overwrite"])
    for archive in args.alpha2_host_report:
        steps.append(py + ["tools/import_alpha2_host_report.py", archive, "--overwrite"])
    for archive in args.competitor_handoff:
        steps.append(py + ["tools/import_competitor_benchmark_handoff.py", archive, "--overwrite", "--skip-refresh"])

    if not args.skip_refresh:
        refresh = py + ["tools/refresh_engine_benchmark_artifacts.py"]
        if args.core_only:
            refresh.append("--core-only")
        refresh.extend(args.refresh_arg)
        steps.append(refresh)

    if not args.skip_host_summary:
        steps.append(py + ["tools/build_phase2_host_evidence_summary.py"])

    if not args.skip_benchmark_charts:
        steps.append(py + ["tools/render_benchmark_storefront_charts.py"])

    if not args.skip_orientation_collages:
        steps.append(py + ["tools/render_orientation_storefront_collages.py"])

    return steps


def render_steps(steps: list[list[str]]) -> list[str]:
    return [" ".join(step) for step in steps]


def run_step(cmd: list[str]) -> int:
    print("+", " ".join(cmd))
    completed = subprocess.run(cmd, cwd=ROOT)
    return completed.returncode


def main(argv: list[str] | None = None) -> int:
    load_local_env.load()
    args = parse_args(argv)
    steps = build_steps(args)
    if args.list_steps:
        print("# run_phase2_evidence_matrix planned steps")
        for index, rendered in enumerate(render_steps(steps), start=1):
            print(f"{index}. {rendered}")
        return 0

    final_code = 0
    for cmd in steps:
        code = run_step(cmd)
        if code != 0 and final_code == 0:
            final_code = code

    if final_code == 0:
        print("phase2 evidence refresh complete: all steps exited with code 0")
    else:
        print(f"phase2 evidence refresh complete: first failing step exit code = {final_code}")
    return final_code


if __name__ == "__main__":
    raise SystemExit(main())
