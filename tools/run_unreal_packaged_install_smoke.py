#!/usr/bin/env python3
"""Install a packaged FastDIS Unreal plugin into a clean scratch project and smoke it."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path
import shutil
import subprocess
import time
from typing import Any

from artifacts import REPORTS_DIR, rel
import load_local_env
import run_unreal_orientation_verification as unreal_harness
import unreal_env


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "tools" / "unreal" / "verify_packaged_install.py"
ALIAS_ROOT = unreal_harness.ALIAS_ROOT
ALIAS_SCRIPT_PATH = unreal_env.alias_repo_path(SCRIPT_PATH)
DEFAULT_PACKAGE_DIR = unreal_env.DEFAULT_WORK_ROOT / "FastDisPackage"
DEFAULT_PROJECT_DIR = unreal_env.DEFAULT_WORK_ROOT / "FastDisPackagedInstallSmoke"
DEFAULT_LOG_DIR = unreal_env.DEFAULT_WORK_ROOT / "logs" / "packaged_install_smoke"
DEFAULT_LOG_PATH = DEFAULT_LOG_DIR / "FastDisPackagedInstallSmoke.log"
DEFAULT_REPORT_JSON = REPORTS_DIR / "unreal_packaged_install_smoke.json"
DEFAULT_REPORT_MD = REPORTS_DIR / "unreal_packaged_install_smoke.md"
PLUGIN_MOUNT_MAP = "/FastDis/Examples/FastDis_Demo"
DEFAULT_TIMEOUT_SECONDS = 300.0
DEFAULT_REPORT_GRACE_SECONDS = 5.0
DEFAULT_POLL_INTERVAL_SECONDS = 0.25


def _now() -> str:
    return datetime.now(UTC).isoformat()


def resolve_unreal(explicit: str | None, engine_version: str | None) -> str | None:
    path = unreal_env.resolve_editor(engine_version, explicit)
    return str(path) if path else None


def make_project_descriptor() -> dict[str, Any]:
    return {
        "FileVersion": 3,
        "EngineAssociation": "",
        "Category": "",
        "Description": "Scratch project for packaged FastDIS Unreal plugin install smoke.",
        "Plugins": [
            {"Name": "FastDis", "Enabled": True},
            {"Name": "PythonScriptPlugin", "Enabled": True},
        ],
    }


def create_scratch_project(project_dir: Path, package_dir: Path, *, clean: bool) -> Path:
    if clean and project_dir.exists():
        shutil.rmtree(project_dir)
    project_dir.mkdir(parents=True, exist_ok=True)
    plugins_dir = project_dir / "Plugins"
    plugins_dir.mkdir(parents=True, exist_ok=True)
    installed_plugin_dir = plugins_dir / "FastDis"
    if installed_plugin_dir.exists():
        shutil.rmtree(installed_plugin_dir)
    shutil.copytree(package_dir, installed_plugin_dir)
    project_path = project_dir / "FastDisPackagedInstallSmoke.uproject"
    project_path.write_text(json.dumps(make_project_descriptor(), indent=2) + "\n", encoding="utf-8")
    return project_path


def build_command(unreal_binary: str, project_path: Path) -> list[str]:
    DEFAULT_LOG_DIR.mkdir(parents=True, exist_ok=True)
    if DEFAULT_LOG_PATH.exists():
        DEFAULT_LOG_PATH.unlink()
    return [
        unreal_binary,
        str(project_path),
        f"-ExecutePythonScript={ALIAS_SCRIPT_PATH}",
        "-unattended",
        "-nop4",
        "-nosplash",
        "-RenderOffscreen",
        "-NoSound",
        "-stdout",
        "-FullStdOutLogOutput",
        f"-abslog={DEFAULT_LOG_PATH}",
    ]


def run_editor_until_report(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
    report_path: Path,
    timeout_seconds: float,
    report_grace_seconds: float,
    poll_interval_seconds: float = DEFAULT_POLL_INTERVAL_SECONDS,
) -> tuple[int, float, bool, bool]:
    started = time.monotonic()
    process = subprocess.Popen(command, cwd=cwd, env=env)
    terminated_after_report = False
    timed_out = False
    returncode: int | None = None
    report_seen_at: float | None = None

    while True:
        returncode = process.poll()
        now = time.monotonic()
        elapsed = round(now - started, 3)
        if returncode is not None:
            return returncode, elapsed, terminated_after_report, timed_out
        if report_path.exists():
            if report_seen_at is None:
                report_seen_at = now
            elif now - report_seen_at >= report_grace_seconds:
                process.terminate()
                terminated_after_report = True
                try:
                    returncode = process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    returncode = process.wait(timeout=10)
                elapsed = round(time.monotonic() - started, 3)
                return returncode, elapsed, terminated_after_report, timed_out
        if now - started >= timeout_seconds:
            timed_out = True
            process.terminate()
            try:
                returncode = process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                returncode = process.wait(timeout=10)
            elapsed = round(time.monotonic() - started, 3)
            return returncode, elapsed, terminated_after_report, timed_out
        time.sleep(poll_interval_seconds)


def write_report(report: dict[str, Any], json_path: Path, markdown_path: Path) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Unreal Packaged Install Smoke",
        "",
        f"- generated_at: `{report['generated_at']}`",
        f"- status: `{report['status']}`",
        f"- engine_version: `{report.get('engine_version')}`",
        f"- package_dir: `{report.get('package_dir')}`",
        f"- project_dir: `{report.get('project_dir')}`",
        f"- demo_map: `{report.get('demo_map')}`",
        "",
    ]
    details = report.get("details") or []
    if details:
        lines.extend(["## Details", ""])
        for detail in details:
            lines.append(f"- {detail}")
        lines.append("")
    command = report.get("command")
    if command:
        lines.extend(["## Command", "", "```text", " ".join(command), "```", ""])
    result = report.get("result")
    if isinstance(result, dict):
        lines.extend(["## Result", "", "```json", json.dumps(result, indent=2), "```", ""])
    markdown_path.write_text("\n".join(lines), encoding="utf-8")


def base_report(args: argparse.Namespace, *, status: str, details: list[str] | None = None) -> dict[str, Any]:
    return {
        "schema": "fastdis.unreal_packaged_install_smoke.v1",
        "generated_at": _now(),
        "status": status,
        "engine_version": args.engine_version,
        "package_dir": rel(Path(args.package_dir).expanduser().resolve()),
        "project_dir": rel(Path(args.project_dir).expanduser().resolve()),
        "demo_map": PLUGIN_MOUNT_MAP,
        "details": details or [],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--unreal", help="Explicit UnrealEditor executable path")
    parser.add_argument("--engine-version", help="Versioned Unreal env selector, for example 5.7 or 5.8")
    parser.add_argument("--package-dir", default=str(DEFAULT_PACKAGE_DIR), help="Packaged plugin directory produced by BuildPlugin")
    parser.add_argument("--project-dir", default=str(DEFAULT_PROJECT_DIR), help="Scratch clean project directory for install smoke")
    parser.add_argument("--json-out", default=str(DEFAULT_REPORT_JSON), help="JSON report output path")
    parser.add_argument("--markdown-out", default=str(DEFAULT_REPORT_MD), help="Markdown report output path")
    parser.add_argument("--dry-run", action="store_true", help="Write a dry-run report and print the editor command without executing it")
    parser.add_argument("--clean-project", action="store_true", help="Delete any existing scratch project before installing the packaged plugin")
    parser.add_argument("--timeout-seconds", type=float, default=DEFAULT_TIMEOUT_SECONDS, help="Maximum wall-clock time to wait for the editor/report")
    parser.add_argument("--report-grace-seconds", type=float, default=DEFAULT_REPORT_GRACE_SECONDS, help="How long to wait after the report appears before terminating the editor")
    return parser.parse_args()


def main() -> int:
    load_local_env.load()
    args = parse_args()
    package_dir = Path(args.package_dir).expanduser().resolve()
    project_dir = Path(args.project_dir).expanduser().resolve()
    json_out = Path(args.json_out).expanduser().resolve()
    markdown_out = Path(args.markdown_out).expanduser().resolve()

    if not package_dir.exists():
        report = base_report(args, status="missing-package", details=["Packaged plugin directory does not exist. Run the Unreal packaging flow first."])
        write_report(report, json_out, markdown_out)
        print(f"JSON: {json_out}")
        print(f"Markdown: {markdown_out}")
        print(f"status: {report['status']}")
        return 2

    project_path = create_scratch_project(project_dir, package_dir, clean=args.clean_project)
    unreal_binary = resolve_unreal(args.unreal, args.engine_version)
    if unreal_binary is None:
        report = base_report(
            args,
            status="missing-install",
            details=["Could not resolve an Unreal editor executable for this lane."],
        )
        report["installed_plugin_dir"] = rel(project_dir / "Plugins" / "FastDis")
        write_report(report, json_out, markdown_out)
        print(f"JSON: {json_out}")
        print(f"Markdown: {markdown_out}")
        print(f"status: {report['status']}")
        return 3

    command = build_command(unreal_binary, project_path)
    report = base_report(args, status="dry-run" if args.dry_run else "running")
    report["command"] = command
    report["project_file"] = rel(project_path)
    report["installed_plugin_dir"] = rel(project_dir / "Plugins" / "FastDis")
    report["log_path"] = rel(DEFAULT_LOG_PATH)
    if args.dry_run:
        write_report(report, json_out, markdown_out)
        print(" ".join(command))
        print(f"JSON: {json_out}")
        print(f"Markdown: {markdown_out}")
        print(f"status: {report['status']}")
        return 0

    env = unreal_env.build_env()
    env["FASTDIS_PACKAGED_INSTALL_REPORT"] = str(json_out)
    env["FASTDIS_PACKAGED_INSTALL_MARKDOWN"] = str(markdown_out)
    env["FASTDIS_PACKAGED_INSTALL_PROJECT_DIR"] = str(project_dir)
    env["FASTDIS_PACKAGED_INSTALL_PACKAGE_DIR"] = str(package_dir)
    env["FASTDIS_PACKAGED_INSTALL_DEMO_MAP"] = PLUGIN_MOUNT_MAP

    returncode, elapsed, terminated_after_report, timed_out = run_editor_until_report(
        command,
        cwd=ALIAS_ROOT,
        env=env,
        report_path=json_out,
        timeout_seconds=args.timeout_seconds,
        report_grace_seconds=args.report_grace_seconds,
    )
    if not json_out.exists():
        report = base_report(
            args,
            status="missing-report",
            details=["Unreal exited without writing the packaged install smoke report."],
        )
        report["command"] = command
        report["returncode"] = returncode
        report["elapsed_seconds"] = elapsed
        report["terminated_after_report"] = terminated_after_report
        report["timed_out"] = timed_out
        write_report(report, json_out, markdown_out)
    else:
        report = json.loads(json_out.read_text(encoding="utf-8"))
        report.setdefault("generated_at", _now())
        report.setdefault("engine_version", args.engine_version)
        report.setdefault("package_dir", rel(package_dir))
        report.setdefault("project_dir", rel(project_dir))
        report.setdefault("demo_map", PLUGIN_MOUNT_MAP)
        report.setdefault("details", [])
        report["command"] = command
        report["returncode"] = returncode
        report["elapsed_seconds"] = elapsed
        report["terminated_after_report"] = terminated_after_report
        report["timed_out"] = timed_out
        if timed_out and report["status"] == "pass":
            report["status"] = "editor-timeout-after-pass"
            report.setdefault("details", []).append("Unreal wrote a passing report but exceeded the wrapper timeout budget.")
        elif returncode != 0 and not terminated_after_report and report["status"] == "pass":
            report["status"] = "editor-returned-failure"
            report.setdefault("details", []).append("Unreal returned a nonzero exit code even though the script reported pass.")
        write_report(report, json_out, markdown_out)

    print(f"JSON: {json_out}")
    print(f"Markdown: {markdown_out}")
    print(f"status: {report['status']}")
    successful_statuses = {"pass", "editor-timeout-after-pass"}
    return 0 if report["status"] in successful_statuses and (returncode == 0 or terminated_after_report or timed_out) else returncode or 1


if __name__ == "__main__":
    raise SystemExit(main())
