#!/usr/bin/env python3
"""Launch a minimal Unity scratch project and verify that import begins."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import platform as host_platform
import shlex
import shutil
import subprocess
import time

import load_local_env
import run_unity_editor_tests
import run_unity_install_smoke
import unity_env


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = ROOT / "build" / "reports"


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def create_project(project_dir: Path) -> None:
    if project_dir.exists():
        shutil.rmtree(project_dir)
    (project_dir / "Assets").mkdir(parents=True)
    (project_dir / "Packages").mkdir(parents=True)
    (project_dir / "ProjectSettings").mkdir(parents=True)
    _write_text(project_dir / "Packages" / "manifest.json", json.dumps({"dependencies": {}}, indent=2) + "\n")
    _write_text(
        project_dir / "ProjectSettings" / "ProjectVersion.txt",
        "m_EditorVersion: 6000.5.0f1\nm_EditorVersionWithRevision: 6000.5.0f1\n",
    )


def startup_unity_command(editor: str, project_dir: Path, log_path: Path, *, batchmode: bool) -> list[str]:
    cmd = [editor]
    if batchmode:
        cmd.extend(["-batchmode", *run_unity_editor_tests.unity_graphics_args()])
    cmd.extend([
        "-accept-apiupdate",
        "-quit",
        "-projectPath",
        str(project_dir),
        "-logFile",
        str(log_path),
    ])
    return cmd


def startup_attempts(install: unity_env.UnityInstall, project_dir: Path, out_dir: Path) -> list[dict[str, object]]:
    log_path = out_dir / "unity_startup_probe.log"
    attempts: list[dict[str, object]] = []
    interactive_cmd = startup_unity_command(install.editor_path or "", project_dir, log_path, batchmode=False)
    if host_platform.system().lower() == "darwin":
        attempts.append(
            {
                "mode": "interactive",
                "launch": "login-shell",
                "cmd": ["/bin/zsh", "-lc", " ".join(shlex.quote(part) for part in interactive_cmd)],
                "env": None,
                "log": log_path,
                "launcher_log": out_dir / "unity_startup_probe_login_shell_launcher.log",
            }
        )
        if install.editor_app_path:
            attempts.append(
                {
                    "mode": "interactive",
                    "launch": "launch-services",
                    "cmd": ["open", "-W", "-n", "-a", install.editor_app_path, "--args", *interactive_cmd[1:]],
                    "env": None,
                    "log": log_path,
                    "launcher_log": out_dir / "unity_startup_probe_launch_services_launcher.log",
                }
            )
    attempts.append(
        {
            "mode": "batchmode",
            "launch": "direct",
            "cmd": startup_unity_command(install.editor_path or "", project_dir, log_path, batchmode=True),
            "env": run_unity_editor_tests.unity_runtime_env(out_dir / "unity_startup_probe_unused.json"),
            "log": log_path,
            "launcher_log": out_dir / "unity_startup_probe_direct_launcher.log",
        }
    )
    return attempts


def attempt_timeout_budget(total_timeout: int, attempts: list[dict[str, object]], index: int) -> int:
    remaining = len(attempts) - index
    if remaining <= 1:
        return max(30, total_timeout)
    if str(attempts[index].get("launch") or "") != "direct":
        reserve_for_later = max(30, total_timeout - 20)
        return min(20, max(15, total_timeout - reserve_for_later))
    return max(30, total_timeout)


def run_attempt(cmd: list[str], *, env: dict[str, str] | None, launcher_log_path: Path, timeout: int) -> tuple[int, bool]:
    launcher_log_path.parent.mkdir(parents=True, exist_ok=True)
    with launcher_log_path.open("w", encoding="utf-8") as handle:
        try:
            completed = subprocess.run(cmd, cwd=ROOT, env=env, stdout=handle, stderr=subprocess.STDOUT, text=True, timeout=timeout)
            return completed.returncode, False
        except subprocess.TimeoutExpired:
            return -15, True


def launcher_failure_hint(*paths: Path) -> str | None:
    for path in paths:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if "kLSNoExecutableErr" in text or "The executable is missing" in text:
            return "launch-services reported kLSNoExecutableErr; verify the Unity.app bundle path and executable layout"
        if "attempt to write a readonly database" in text:
            return "Unity hit a readonly database while starting; verify the macOS Unity Hub / licensing cache and home-directory write access"
    return None


def render_markdown(report: dict[str, object]) -> str:
    state = report.get("project_state") or {}
    lines = [
        "# Unity Startup Probe Report",
        "",
        f"- status: `{report['status']}`",
        f"- host_platform: `{report.get('host_platform', 'unknown')}`",
        f"- unity_version: `{report.get('unity_version', 'unknown')}`",
        f"- detail: `{report.get('detail', '')}`",
        f"- launch: `{report.get('launch', 'unknown')}`",
        f"- log: `{report.get('log', '')}`",
        f"- launcher_log: `{report.get('launcher_log', '')}`",
        "",
        "## Evidence",
        "",
        f"- project_state.library_exists: `{state.get('library_exists', False)}`",
        f"- project_state.package_cache_exists: `{state.get('package_cache_exists', False)}`",
        f"- project_state.script_assemblies_exists: `{state.get('script_assemblies_exists', False)}`",
        "",
        "## Attempts",
        "",
    ]
    for attempt in report.get("attempts", []):
        if isinstance(attempt, dict):
            lines.append(
                f"- launch={attempt.get('launch', 'unknown')} status={attempt.get('status', 'unknown')} "
                f"returncode={attempt.get('returncode', 'unknown')} timed_out={attempt.get('timed_out', False)} "
                f"elapsed={attempt.get('elapsed_seconds', 0)}"
            )
    lines.append("")
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--unity-version", help="Unity editor version prefix, for example 6000.5")
    parser.add_argument("--project-dir", type=Path, help="Scratch Unity project path")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--timeout", type=int, default=120)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    load_local_env.load()
    args = parse_args(argv)
    install = unity_env.resolve_install(args.unity_version)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.out_dir / "unity_startup_probe.json"
    md_path = args.out_dir / "unity_startup_probe.md"
    log_path = args.out_dir / "unity_startup_probe.log"
    project_dir = args.project_dir or (unity_env.work_root() / "unity_startup_probe_project")

    if install is None or not install.editor_path:
        report = {
            "schema": "fastdis.unity_startup_probe.v1",
            "status": "skip",
            "requested_version": args.unity_version,
            "host_platform": run_unity_install_smoke.host_label(),
            "detail": "Unity editor not found",
            "log": str(log_path),
            "project_dir": str(project_dir),
            "project_state": run_unity_install_smoke.project_state(project_dir),
            "attempts": [],
        }
        json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        md_path.write_text(render_markdown(report), encoding="utf-8")
        print(f"JSON: {json_path}")
        print(f"Markdown: {md_path}")
        return 2

    create_project(project_dir)
    attempts = startup_attempts(install, project_dir, args.out_dir)
    run_unity_install_smoke.clear_previous_artifacts(
        json_path,
        md_path,
        log_path,
        *[attempt["launcher_log"] for attempt in attempts if isinstance(attempt.get("launcher_log"), Path)],
    )

    attempt_summaries: list[dict[str, object]] = []
    selected_attempt: dict[str, object] | None = None
    remaining_timeout = args.timeout
    passed = False
    for index, attempt in enumerate(attempts):
        run_unity_install_smoke.clear_previous_artifacts(log_path, attempt["launcher_log"])
        attempt_timeout = attempt_timeout_budget(remaining_timeout, attempts, index)
        started = time.monotonic()
        returncode, timed_out = run_attempt(
            attempt["cmd"],
            env=attempt["env"] if isinstance(attempt.get("env"), dict) or attempt.get("env") is None else None,
            launcher_log_path=attempt["launcher_log"],
            timeout=attempt_timeout,
        )
        elapsed = round(time.monotonic() - started, 3)
        remaining_timeout = max(30, remaining_timeout - attempt_timeout)
        state = run_unity_install_smoke.project_state(project_dir)
        status = "pass" if state["library_exists"] else ("timeout" if timed_out else "fail")
        attempt_summaries.append(
            {
                "launch": attempt["launch"],
                "mode": attempt["mode"],
                "status": status,
                "returncode": returncode,
                "timed_out": timed_out,
                "elapsed_seconds": elapsed,
                "timeout_budget_seconds": attempt_timeout,
            }
        )
        selected_attempt = attempt
        if state["library_exists"]:
            passed = True
            break

    state = run_unity_install_smoke.project_state(project_dir)
    if passed:
        report = {
            "schema": "fastdis.unity_startup_probe.v1",
            "status": "pass",
            "unity_version": install.version,
            "detail": "Unity created the scratch project Library/ directory.",
        }
    else:
        hint = launcher_failure_hint(*(attempt["launcher_log"] for attempt in attempts if isinstance(attempt.get("launcher_log"), Path)))
        report = {
            "schema": "fastdis.unity_startup_probe.v1",
            "status": "fail",
            "unity_version": install.version,
            "detail": (
                "Unity did not begin importing the scratch startup-probe project before the timeout; "
                "the project Library/ directory was never created."
                + (f" Diagnostic hint: {hint}." if hint else "")
            ),
        }
    report["requested_version"] = args.unity_version
    report["host_platform"] = run_unity_install_smoke.host_label()
    report["editor"] = install.editor_path
    report["project_dir"] = str(project_dir)
    report["project_state"] = state
    report["log"] = str(log_path)
    report["launch"] = str(selected_attempt.get("launch") or "unknown") if selected_attempt else "unknown"
    report["mode"] = str(selected_attempt.get("mode") or "unknown") if selected_attempt else "unknown"
    if selected_attempt is not None:
        report["launcher_log"] = str(selected_attempt["launcher_log"])
    report["attempts"] = attempt_summaries

    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    print(f"JSON: {json_path}")
    print(f"Markdown: {md_path}")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
