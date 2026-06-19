#!/usr/bin/env python3
"""Run the local Alpha 2 engine proof flow and stage one host bundle."""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys

import load_local_env
import unreal_env


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_DIR = ROOT / "verification_reports" / "alpha2_sample"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", default=str(DEFAULT_SOURCE_DIR), help="Directory for the local Alpha 2 proof reports")
    parser.add_argument("--host-label", help="Optional host label forwarded to stage_alpha2_host_report.py")
    parser.add_argument("--skip-unreal-matrix", action="store_true", help="Skip tools/run_unreal_matrix.py")
    parser.add_argument("--skip-godot-report", action="store_true", help="Skip tools/run_godot_report.py")
    parser.add_argument("--skip-orientation-runtime", action="store_true", help="Skip tools/run_orientation_runtime_report.py")
    parser.add_argument("--skip-orientation-visual", action="store_true", help="Skip tools/run_orientation_visual_report.py")
    parser.add_argument("--skip-stage", action="store_true", help="Do not run tools/stage_alpha2_host_report.py")
    parser.add_argument("--skip-package", action="store_true", help="Do not run tools/package_alpha2.py after capture")
    parser.add_argument(
        "--engine-version",
        dest="engine_versions",
        action="append",
        help="Unreal engine version for orientation reports; repeat as needed. Defaults to 5.7 and 5.8.",
    )
    parser.add_argument(
        "--matrix-version",
        dest="matrix_versions",
        action="append",
        help="Unreal version for the matrix lane; repeat as needed. Defaults to 5.6, 5.7, and 5.8.",
    )
    return parser.parse_args()


def run_step(cmd: list[str]) -> int:
    print("+", " ".join(cmd))
    completed = subprocess.run(cmd, cwd=ROOT)
    return completed.returncode


def build_steps(args: argparse.Namespace) -> list[list[str]]:
    source_dir = str(Path(args.source_dir).expanduser().resolve())
    matrix_versions = args.matrix_versions or ["5.6", "5.7", "5.8"]
    engine_versions = args.engine_versions or ["5.7", "5.8"]
    py = unreal_env.python_command()
    steps: list[list[str]] = []

    if not args.skip_unreal_matrix:
        steps.append(py + ["tools/run_unreal_matrix.py", "--out-dir", source_dir, "--versions", *matrix_versions])
    if not args.skip_godot_report:
        steps.append(py + ["tools/run_godot_report.py", "--out-dir", source_dir])
    if not args.skip_orientation_runtime:
        cmd = py + ["tools/run_orientation_runtime_report.py", "--out-dir", source_dir]
        for version in engine_versions:
            cmd.extend(["--engine-version", version])
        steps.append(cmd)
    if not args.skip_orientation_visual:
        cmd = py + ["tools/run_orientation_visual_report.py", "--out-dir", source_dir]
        for version in engine_versions:
            cmd.extend(["--engine-version", version])
        steps.append(cmd)

    steps.append(py + ["tools/run_alpha2_signoff_matrix.py", "--out-dir", source_dir])
    steps.append(py + ["tools/run_alpha2_release_audit.py", "--out-dir", source_dir])

    if not args.skip_stage:
        cmd = py + ["tools/stage_alpha2_host_report.py", "--source-dir", source_dir, "--overwrite"]
        if args.host_label:
            cmd.extend(["--host-label", args.host_label])
        steps.append(cmd)
        steps.append(py + ["tools/run_alpha2_signoff_matrix.py", "--out-dir", source_dir])
        steps.append(py + ["tools/run_alpha2_release_audit.py", "--out-dir", source_dir])

    if not args.skip_package:
        steps.append(py + ["tools/package_alpha2.py", "--write-root-checksums"])
    return steps


def main() -> int:
    load_local_env.load()
    args = parse_args()
    final_code = 0
    for cmd in build_steps(args):
        code = run_step(cmd)
        if code != 0 and final_code == 0:
            final_code = code
    return final_code


if __name__ == "__main__":
    raise SystemExit(main())
