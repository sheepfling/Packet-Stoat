#!/usr/bin/env python3
"""Run the local Unity proof flow and stage one host bundle."""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess

import load_local_env
import stage_unity_host_report
import unity_env


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_DIR = ROOT / "artifacts" / "reports"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", default=str(DEFAULT_SOURCE_DIR), help="Directory for the local Unity proof reports")
    parser.add_argument("--host-label", help="Optional host label forwarded to stage-host-report/export-host-report")
    parser.add_argument("--host-platform", choices=("macos", "windows", "linux"), help="Optional host platform forwarded to stage-host-report")
    parser.add_argument("--dest-root", help="Optional host bundle root forwarded to stage-host-report")
    parser.add_argument("--archive-out-dir", help="Optional archive output directory forwarded to export-host-report")
    parser.add_argument("--unity-version", help="Unity editor version prefix, for example 6000.5")
    parser.add_argument("--skip-native-build", action="store_true", help="Forward --skip-native-build to tools/unity_workflow.py full for hosts validating pre-staged plug-ins")
    parser.add_argument("--skip-startup-probe", action="store_true", help="Forward --skip-startup-probe to tools/unity_workflow.py full when the host preflight has already been captured separately")
    parser.add_argument("--skip-full", action="store_true", help="Skip tools/unity_workflow.py full")
    parser.add_argument("--skip-stage", action="store_true", help="Do not run tools/unity_workflow.py stage-host-report")
    parser.add_argument("--skip-export", action="store_true", help="Do not run tools/unity_workflow.py export-host-report after staging")
    parser.add_argument("--skip-install-matrix", action="store_true", help="Do not refresh install-matrix, host-matrix, or signoff after staging")
    return parser.parse_args(argv)


def run_step(cmd: list[str]) -> int:
    print("+", " ".join(cmd))
    completed = subprocess.run(cmd, cwd=ROOT)
    return completed.returncode


def build_steps(args: argparse.Namespace) -> list[list[str]]:
    source_dir = str(Path(args.source_dir).expanduser().resolve())
    py = unity_env.python_command()
    steps: list[list[str]] = []
    host_label = args.host_label or stage_unity_host_report.detect_host_label()

    if not args.skip_full:
        cmd = py + ["tools/unity_workflow.py", "full"]
        if args.unity_version:
            cmd.extend(["--unity-version", args.unity_version])
        if args.skip_native_build:
            cmd.append("--skip-native-build")
        if args.skip_startup_probe:
            cmd.append("--skip-startup-probe")
        steps.append(cmd)

    if not args.skip_stage:
        cmd = py + ["tools/unity_workflow.py", "stage-host-report", "--source-dir", source_dir, "--overwrite"]
        cmd.extend(["--host-label", host_label])
        if args.host_platform:
            cmd.extend(["--host-platform", args.host_platform])
        if args.dest_root:
            cmd.extend(["--dest-root", str(Path(args.dest_root).expanduser().resolve())])
        steps.append(cmd)

    if not args.skip_install_matrix:
        steps.append(py + ["tools/unity_workflow.py", "install-matrix", "--report-dir", source_dir, "--out-dir", source_dir])
        host_root = str(Path(args.dest_root).expanduser().resolve()) if args.dest_root else str((ROOT / "verification_reports" / "unity_hosts").resolve())
        steps.append(py + ["tools/unity_workflow.py", "host-matrix", "--host-root", host_root, "--out-dir", source_dir])
        steps.append(py + ["tools/unity_workflow.py", "signoff", "--report-dir", source_dir, "--host-root", host_root, "--out-dir", source_dir])

    if not args.skip_export:
        cmd = py + ["tools/unity_workflow.py", "export-host-report", host_label]
        if args.dest_root:
            cmd.extend(["--host-root", str(Path(args.dest_root).expanduser().resolve())])
        if args.archive_out_dir:
            cmd.extend(["--out-dir", str(Path(args.archive_out_dir).expanduser().resolve())])
        steps.append(cmd)
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
