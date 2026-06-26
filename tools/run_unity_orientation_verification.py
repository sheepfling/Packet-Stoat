#!/usr/bin/env python3
"""Run the Unity orientation verification example project and write a report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import platform as host_platform
import shlex
import subprocess
import time

import load_local_env
import unity_env


ROOT = Path(__file__).resolve().parents[1]
PROJECT_DIR = ROOT / "examples" / "unity" / "FastDisOrientationVerification"
DEFAULT_OUT_DIR = ROOT / "build" / "reports"


def report_paths(out_dir: Path) -> tuple[Path, Path, Path]:
    return (
        out_dir / "unity_orientation_verification.json",
        out_dir / "unity_orientation_verification.md",
        out_dir / "unity_orientation_verification.log",
    )


def render_markdown(report: dict[str, object]) -> str:
    lines = [
        "# Unity Orientation Verification Report",
        "",
        f"- status: `{report['status']}`",
        f"- unity_version: `{report.get('unity_version', 'unknown')}`",
        f"- scene: `{report.get('scene', 'unknown')}`",
        f"- total: `{report.get('total', 0)}`",
        f"- failed: `{report.get('failed', 0)}`",
        f"- detail: `{report.get('detail', '')}`",
        f"- log: `{report.get('log', '')}`",
        "",
    ]
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--unity-version", help="Unity editor version prefix, for example 6000.5")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--timeout", type=int, default=600)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    load_local_env.load()
    args = parse_args(argv)
    install = unity_env.resolve_install(args.unity_version)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    json_path, md_path, log_path = report_paths(args.out_dir)

    if install is None or not install.editor_path:
        report = {
            "schema": "fastdis.unity_orientation_verification.v1",
            "status": "skip",
            "requested_version": args.unity_version,
            "detail": "Unity editor not found",
            "log": str(log_path),
        }
        json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        md_path.write_text(render_markdown(report), encoding="utf-8")
        print(f"JSON: {json_path}")
        print(f"Markdown: {md_path}")
        return 2

    unity_cmd = [
        install.editor_path,
        "-batchmode",
        "-accept-apiupdate",
        "-quit",
        "-projectPath",
        str(PROJECT_DIR),
        "-executeMethod",
        "FastDisOrientationVerificationRunner.Run",
        "-fastdisReport",
        str(json_path),
        "-logFile",
        str(log_path),
    ]
    if host_platform.system().lower() == "darwin":
        cmd = ["/bin/zsh", "-lc", " ".join(shlex.quote(part) for part in unity_cmd)]
        env = None
    else:
        cmd = unity_cmd
        env = unity_env.build_env()

    started = time.monotonic()
    completed = subprocess.run(cmd, cwd=ROOT, env=env, timeout=args.timeout)
    elapsed = round(time.monotonic() - started, 3)

    if json_path.is_file():
        report = json.loads(json_path.read_text(encoding="utf-8-sig"))
    else:
        report = {
            "schema": "fastdis.unity_orientation_verification.v1",
            "status": "fail",
            "unity_version": install.version,
            "scene": "Assets/Scenes/OrientationVerification.unity",
            "total": 0,
            "failed": 1,
            "detail": "Unity did not write an orientation verification report.",
        }

    report["requested_version"] = args.unity_version
    report["editor"] = install.editor_path
    report["project_dir"] = str(PROJECT_DIR)
    report["returncode"] = completed.returncode
    report["elapsed_seconds"] = elapsed
    report["log"] = str(log_path)

    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    print(f"JSON: {json_path}")
    print(f"Markdown: {md_path}")
    return 0 if report.get("status") == "pass" and completed.returncode == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
