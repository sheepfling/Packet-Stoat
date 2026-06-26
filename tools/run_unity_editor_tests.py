#!/usr/bin/env python3
"""Run FastDIS Unity package tests in a scratch Unity project."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import platform as host_platform
import shlex
import shutil
import subprocess
import time
import xml.etree.ElementTree as ET

import load_local_env
import unity_env


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = ROOT / "integrations" / "unity" / "com.sheepfling.fastdis"
DEFAULT_REPORT_DIR = ROOT / "build" / "reports"


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def create_project(project_dir: Path) -> None:
    """Create a minimal project that imports the local UPM package as testable."""
    if project_dir.exists():
        shutil.rmtree(project_dir)
    (project_dir / "Assets").mkdir(parents=True)
    (project_dir / "LocalPackages").mkdir(parents=True)
    (project_dir / "Packages").mkdir(parents=True)
    (project_dir / "ProjectSettings").mkdir(parents=True)
    local_package_root = project_dir / "LocalPackages" / PACKAGE_ROOT.name
    try:
        local_package_root.symlink_to(PACKAGE_ROOT.resolve(), target_is_directory=True)
    except OSError:
        shutil.copytree(PACKAGE_ROOT, local_package_root)
    manifest = {
        "dependencies": {
            "com.sheepfling.fastdis": "file:../LocalPackages/com.sheepfling.fastdis",
            "com.unity.test-framework": "1.1.33",
        },
        "testables": ["com.sheepfling.fastdis"],
    }
    _write_text(project_dir / "Packages" / "manifest.json", json.dumps(manifest, indent=2) + "\n")
    _write_text(
        project_dir / "ProjectSettings" / "ProjectVersion.txt",
        "m_EditorVersion: 6000.5.0f1\nm_EditorVersionWithRevision: 6000.5.0f1\n",
    )


def parse_nunit(path: Path) -> dict[str, object]:
    if not path.is_file():
        return {"status": "missing", "total": 0, "passed": 0, "failed": 0, "skipped": 0}
    root = ET.parse(path).getroot()
    total = int(root.attrib.get("total", root.attrib.get("testcasecount", "0")) or 0)
    failed = int(root.attrib.get("failed", "0") or 0)
    skipped = int(root.attrib.get("skipped", root.attrib.get("inconclusive", "0")) or 0)
    passed = int(root.attrib.get("passed", str(max(total - failed - skipped, 0))) or 0)
    return {
        "status": "pass" if failed == 0 and total > 0 else "fail",
        "total": total,
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
    }


def analyze_log(log_path: Path) -> dict[str, object]:
    result: dict[str, object] = {
        "status": None,
        "code": None,
        "needle": None,
        "detail": None,
        "remediation": [],
    }
    if not log_path.is_file():
        return result
    text = log_path.read_text(encoding="utf-8", errors="replace")
    signatures: list[tuple[str, str, str, str, list[str]]] = [
        (
            "blocked_license",
            "unity_headless_entitlement_missing",
            "'com.unity.editor.headless' was not found",
            "Unity requested the separate headless entitlement. This commonly happens with Unity Personal when using -batchmode/-nographics or Test Runner.",
            [
                "Use the default macOS editor-method runner: python tools/unity_workflow.py runtime-verify --unity-version 6000.5",
                "Unset FASTDIS_UNITY_BATCHMODE and FASTDIS_UNITY_FORCE_NOGRAPHICS for local signed-in Personal installs.",
                "Use FASTDIS_UNITY_BATCHMODE=1 only on machines with a valid Unity headless/batchmode entitlement.",
            ],
        ),
        (
            "blocked_license",
            "unity_ui_entitlement_missing",
            "'com.unity.editor.ui' was not found",
            "Unity requested the interactive UI entitlement but could not see the signed-in Hub license from the current process environment.",
            [
                "Run through tools/unity_workflow.py so macOS uses the login-shell launcher.",
                "If this already used the login-shell launcher, open Unity Hub and this Unity Editor version once from the GUI, then rerun.",
                "If the GUI opens but CLI verification still fails, restart Unity Hub so its LicensingClient matches the installed Editor version.",
                "Do not redirect HOME/TMPDIR for runtime verification; the workflow preserves the Unity Hub login environment automatically.",
                "Confirm the account has an Editor entitlement for this Unity version before treating package/runtime code as the failure.",
            ],
        ),
        (
            "blocked_license",
            "unity_license_missing",
            "No valid Unity Editor license found",
            "Unity could not resolve an active Editor license for this invocation.",
            [
                "Open Unity Hub and confirm the Editor is activated for the signed-in user.",
                "On macOS, prefer the default login-shell runtime verifier instead of direct Python-spawned Unity.",
                "Inspect build/reports/unity_editor_method.log for entitlement-specific lines before assuming the account is unlicensed.",
            ],
        ),
        (
            "blocked_license",
            "unity_license_activation_required",
            "Please activate your license",
            "Unity reported that the Editor needs activation.",
            ["Open Unity Hub, sign in, activate the Editor, then rerun runtime verification."],
        ),
        (
            "package_resolution_failed",
            "unity_package_manager_error",
            "Package Manager Error",
            "Unity Package Manager reported an error while resolving/importing packages.",
            ["Delete the scratch Unity project under the reported work root and rerun runtime verification."],
        ),
        (
            "package_resolution_failed",
            "unity_package_resolution_failed",
            "Failed to resolve packages",
            "Unity failed to resolve packages for the scratch project.",
            ["Check network/package-cache access and rerun python tools/unity_workflow.py runtime-verify."],
        ),
        (
            "compile_error",
            "unity_compile_error",
            "Compiler errors",
            "Unity compiled the project but reported C# compiler errors.",
            ["Open the reported Unity log and fix the first C# compiler error before rerunning."],
        ),
        (
            "unity_asset_meta_invalid",
            "unity_yaml_meta_invalid",
            "YAML Parsing error",
            "Unity could not parse one or more .meta files, commonly due to invalid GUIDs or malformed generated metadata.",
            ["Inspect the following log lines for the asset path, then regenerate or fix that .meta file."],
        ),
        (
            "host_startup_blocked",
            "unity_host_startup_readonly_database",
            "attempt to write a readonly database",
            "Unity hit a readonly database while starting and never reached project import or the FastDIS verifier entrypoint.",
            [
                "Verify the macOS Unity Hub / licensing cache is writable for the current user.",
                "Prefer the default login-shell launcher via python tools/unity_workflow.py runtime-verify --unity-version 6000.5.",
                "If this persists, open the Unity Editor once from the GUI and confirm the signed-in Hub session can write its local cache before rerunning automation.",
            ],
        ),
    ]
    for status, code, needle, detail, remediation in signatures:
        if needle in text:
            result.update(
                {
                    "status": status,
                    "code": code,
                    "needle": needle,
                    "detail": detail,
                    "remediation": remediation,
                }
            )
            return result
    return result


def classify_log(log_path: Path) -> tuple[str | None, str | None]:
    analysis = analyze_log(log_path)
    return analysis["status"], analysis["needle"]


def editor_method_quit_grace_seconds() -> float:
    value = os.environ.get("FASTDIS_UNITY_EDITOR_QUIT_GRACE_SECONDS", "10")
    try:
        return max(0.0, float(value))
    except ValueError:
        return 10.0


def unity_graphics_args() -> list[str]:
    force_nographics = os.environ.get("FASTDIS_UNITY_FORCE_NOGRAPHICS") in {"1", "true", "TRUE", "yes", "YES"}
    disable_nographics = os.environ.get("FASTDIS_UNITY_NO_NOGRAPHICS") in {"1", "true", "TRUE", "yes", "YES"}
    # Unity Personal on macOS can run batchmode editor methods with a signed-in Hub
    # license, but `-nographics` requests the separate headless entitlement.
    if force_nographics or (not disable_nographics and host_platform.system().lower() != "darwin"):
        return ["-nographics"]
    return []


def use_interactive_editor_method() -> bool:
    if os.environ.get("FASTDIS_UNITY_BATCHMODE") in {"1", "true", "TRUE", "yes", "YES"}:
        return False
    if os.environ.get("FASTDIS_UNITY_INTERACTIVE") in {"1", "true", "TRUE", "yes", "YES"}:
        return True
    return host_platform.system().lower() == "darwin"


def unity_runtime_env(report_json: Path) -> dict[str, str]:
    old_preserve = os.environ.get("FASTDIS_UNITY_PRESERVE_HOME")
    os.environ["FASTDIS_UNITY_PRESERVE_HOME"] = "1"
    try:
        env = dict(unity_env.build_env())
    finally:
        if old_preserve is None:
            os.environ.pop("FASTDIS_UNITY_PRESERVE_HOME", None)
        else:
            os.environ["FASTDIS_UNITY_PRESERVE_HOME"] = old_preserve
    env["FASTDIS_UNITY_PRESERVE_HOME"] = "1"
    env["FASTDIS_UNITY_RUNTIME_REPORT_JSON"] = str(report_json)
    return env


def editor_method_unity_command(editor: str, project_dir: Path, result_json: Path, log_path: Path) -> list[str]:
    return [
        editor,
        "-accept-apiupdate",
        "-quit",
        "-projectPath",
        str(project_dir),
        "-executeMethod",
        "FastDIS.Editor.FastDisRuntimeVerification.Run",
        "-fastdisReport",
        str(result_json),
        "-logFile",
        str(log_path),
    ]


def editor_method_attempts(install: unity_env.UnityInstall, project_dir: Path, report_dir: Path) -> list[dict[str, object]]:
    report_dir = report_dir.resolve()
    result_json = (report_dir / "unity_editor_method_report.json").resolve()
    log_path = (report_dir / "unity_editor_method.log").resolve()
    interactive = use_interactive_editor_method()
    unity_cmd = editor_method_unity_command(install.editor_path or "", project_dir, result_json, log_path)

    if interactive and host_platform.system().lower() == "darwin":
        command = " ".join(shlex.quote(part) for part in unity_cmd)
        attempts: list[dict[str, object]] = [
            {
                "mode": "interactive",
                "launch": "login-shell",
                "cmd": ["/bin/zsh", "-lc", command],
                "unity_command": unity_cmd,
                "env": None,
                "results_json": result_json,
                "log": log_path,
                "launcher_log": (report_dir / "unity_editor_method_login_shell_launcher.log").resolve(),
            }
        ]
        if install.editor_app_path:
            attempts.append(
                {
                    "mode": "interactive",
                    "launch": "launch-services",
                    "cmd": ["open", "-W", "-n", "-a", install.editor_app_path, "--args", *unity_cmd[1:]],
                    "unity_command": [install.editor_app_path, *unity_cmd[1:]],
                    "env": None,
                    "results_json": result_json,
                    "log": log_path,
                    "launcher_log": (report_dir / "unity_editor_method_launch_services_launcher.log").resolve(),
                }
            )
        return attempts

    cmd = [install.editor_path or ""]
    if not interactive:
        cmd.extend(["-batchmode", *unity_graphics_args()])
    cmd.extend(unity_cmd[1:])
    return [
        {
            "mode": "interactive" if interactive else "batchmode",
            "launch": "direct",
            "cmd": cmd,
            "unity_command": unity_cmd,
            "env": unity_runtime_env(result_json),
            "results_json": result_json,
            "log": log_path,
            "launcher_log": (report_dir / "unity_editor_method_direct_launcher.log").resolve(),
        }
    ]


def read_editor_method_payload(result_json: Path) -> dict[str, object]:
    if not result_json.is_file():
        return {}
    return json.loads(result_json.read_text(encoding="utf-8-sig"))


def tests_from_editor_method_payload(payload: dict[str, object]) -> dict[str, object]:
    return {
        "status": payload.get("status", "missing"),
        "total": int(payload.get("total", 0) or 0),
        "passed": int(payload.get("passed", 0) or 0),
        "failed": int(payload.get("failed", 0) or 0),
        "skipped": 0,
    }


def _check_status_map(details: dict[str, object]) -> dict[str, str]:
    checks = details.get("checks")
    if not isinstance(checks, list):
        return {}
    status_by_name: dict[str, str] = {}
    for item in checks:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        status = item.get("status")
        if isinstance(name, str) and isinstance(status, str):
            status_by_name[name] = status
    return status_by_name


def _criterion(
    name: str,
    required_checks: list[str],
    check_statuses: dict[str, str],
    note: str,
    *,
    any_of_checks: list[str] | None = None,
) -> dict[str, object]:
    checks = [{"name": item, "status": check_statuses.get(item, "missing")} for item in required_checks]
    if any_of_checks:
        alternative_checks = [{"name": item, "status": check_statuses.get(item, "missing")} for item in any_of_checks]
        checks.extend(alternative_checks)
        required_ok = all(check_statuses.get(item) == "pass" for item in required_checks)
        alternative_ok = any(check_statuses.get(item) == "pass" for item in any_of_checks)
        status = "complete" if required_ok and alternative_ok else "incomplete"
    else:
        status = "complete" if checks and all(item["status"] == "pass" for item in checks) else "incomplete"
    return {
        "name": name,
        "status": status,
        "required_checks": checks,
        "note": note,
    }


def derive_phase1_exit_criteria(report: dict[str, object]) -> list[dict[str, object]]:
    lane_details = {}
    for lane in report.get("lanes", []):
        if not isinstance(lane, dict):
            continue
        details = lane.get("details")
        if isinstance(details, dict) and details.get("schema") == "fastdis.unity_editor_method_verification.v1":
            lane_details = details
            break
    check_statuses = _check_status_map(lane_details)
    return [
        _criterion(
            "Native library stages and loads in Unity",
            ["native_abi_loads"],
            check_statuses,
            "The editor-method verifier must resolve the C ABI and return a nonzero ABI version.",
        ),
        _criterion(
            "Replay demo moves GameObjects",
            [
                "replay_player_parses_fastdispkt_stream",
                "replay_player_steps_world_state",
            ],
            check_statuses,
            "The replay player must parse a FastDIS replay stream and advance world state through replay-driven packet playback.",
        ),
        _criterion(
            "UDP demo receives live Entity State traffic",
            [],
            check_statuses,
            "The runtime receiver path must inject entity-state traffic into the world and increment receive counters.",
            any_of_checks=["receiver_socket_loopback_feeds_world", "receiver_inject_packet_feeds_world"],
        ),
        _criterion(
            "Entity mapper applies transforms to spawned GameObjects",
            [
                "world_processes_entity_state_packet",
                "world_exposes_last_entity_transform",
                "world_auto_spawns_and_positions_actor",
            ],
            check_statuses,
            "The world/entity mapping path must publish the latest transform and position a bound Unity actor.",
        ),
        _criterion(
            "Diagnostics window exposes runtime counters",
            ["remove_entity_request_clears_known_entity"],
            check_statuses,
            "Runtime counters must update during verification so the monitor surface has meaningful world statistics to display.",
        ),
    ]


def run_editor_method_process(
    cmd: list[str],
    result_json: Path,
    log_path: Path,
    *,
    env: dict[str, str] | None,
    launcher_log_path: Path | None,
    timeout: int,
) -> tuple[int, bool, bool, dict[str, object] | None]:
    stdout_target = None
    if launcher_log_path is not None:
        launcher_log_path.parent.mkdir(parents=True, exist_ok=True)
        stdout_target = launcher_log_path.open("w", encoding="utf-8")
    try:
        process = subprocess.Popen(cmd, cwd=ROOT, env=env, stdout=stdout_target, stderr=subprocess.STDOUT, text=True)
    finally:
        if stdout_target is not None:
            stdout_target.close()
    deadline = time.monotonic() + timeout
    pass_seen_at: float | None = None
    diagnostic_seen_at: float | None = None
    diagnostic_info: dict[str, object] | None = None
    quit_grace = editor_method_quit_grace_seconds()
    terminated_after_pass = False
    timed_out = False

    while True:
        returncode = process.poll()
        if returncode is not None:
            return returncode, terminated_after_pass, timed_out, diagnostic_info

        now = time.monotonic()
        payload = read_editor_method_payload(result_json)
        if payload.get("status") == "pass":
            if pass_seen_at is None:
                pass_seen_at = now
            elif now - pass_seen_at >= quit_grace:
                terminated_after_pass = True
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
                return process.returncode if process.returncode is not None else 0, terminated_after_pass, timed_out, diagnostic_info

        if not payload:
            current_diagnostic = analyze_log(log_path)
            if current_diagnostic.get("status") in {
                "blocked_license",
                "package_resolution_failed",
                "compile_error",
                "unity_asset_meta_invalid",
                "host_startup_blocked",
            }:
                if diagnostic_seen_at is None or current_diagnostic.get("code") != (diagnostic_info or {}).get("code"):
                    diagnostic_seen_at = now
                    diagnostic_info = current_diagnostic
                elif now - diagnostic_seen_at >= 2.0:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=5)
                    return process.returncode if process.returncode is not None else 1, terminated_after_pass, timed_out, diagnostic_info

        if now >= deadline:
            timed_out = True
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
            return process.returncode if process.returncode is not None else 1, terminated_after_pass, timed_out, diagnostic_info

        time.sleep(0.5)


def run_unity_editor_method(editor: str, project_dir: Path, report_dir: Path, *, timeout: int) -> dict[str, object]:
    install = unity_env.UnityInstall(
        version="unknown",
        install_root="",
        editor_path=editor,
        editor_app_path=str(Path(editor).parents[2]) if host_platform.system().lower() == "darwin" and Path(editor).name == "Unity" else None,
        source="runtime",
        quirks=(),
    )
    attempts = editor_method_attempts(install, project_dir, report_dir)
    summaries: list[dict[str, object]] = []
    final_lane: dict[str, object] | None = None
    primary_blocked_license_lane: dict[str, object] | None = None

    for index, attempt in enumerate(attempts):
        result_json = attempt["results_json"]
        log_path = attempt["log"]
        launcher_log_path = attempt.get("launcher_log")
        if result_json.exists():
            result_json.unlink()
        if log_path.exists():
            log_path.unlink()
        if isinstance(launcher_log_path, Path) and launcher_log_path.exists():
            launcher_log_path.unlink()
        started = time.monotonic()
        returncode, terminated_after_pass, timed_out, early_diagnostic_info = run_editor_method_process(
            attempt["cmd"],
            result_json,
            log_path,
            env=attempt["env"],
            launcher_log_path=launcher_log_path if isinstance(launcher_log_path, Path) else None,
            timeout=timeout,
        )
        elapsed = round(time.monotonic() - started, 3)
        diagnostic_info = early_diagnostic_info or analyze_log(log_path)
        payload = read_editor_method_payload(result_json)
        tests = tests_from_editor_method_payload(payload)
        if terminated_after_pass and tests["status"] == "pass":
            diagnostic_info = {
                "status": "pass",
                "code": "unity_editor_quit_timeout_after_pass",
                "needle": "Unity wrote a passing FastDIS report but did not exit before the launcher grace period.",
                "detail": "The wrapper terminated only the launched Unity verifier process after the C# verifier wrote a passing report.",
                "remediation": [
                    "Inspect the Unity log for startup/licensing warnings if this becomes frequent.",
                    "Increase FASTDIS_UNITY_EDITOR_QUIT_GRACE_SECONDS if the local Editor needs more time to quit cleanly.",
                ],
            }
        elif timed_out:
            diagnostic_info = {
                "status": "fail",
                "code": "unity_editor_timeout",
                "needle": "Unity verifier exceeded the configured timeout.",
                "detail": f"Unity did not complete within {timeout} seconds.",
                "remediation": [
                    "Inspect build/reports/unity_editor_method.log.",
                    "Rerun with a larger --timeout if Unity is compiling packages for the first time.",
                ],
            }
        elif not payload and not log_path.exists() and returncode != 0:
            launch = str(attempt["launch"])
            launcher_log_path = attempt.get("launcher_log")
            launcher_detail = None
            if isinstance(launcher_log_path, Path) and launcher_log_path.is_file():
                launcher_detail = launcher_log_path.read_text(encoding="utf-8", errors="replace").strip() or None
            diagnostic_info = {
                "status": "fail",
                "code": f"unity_{launch.replace('-', '_')}_launch_failed",
                "needle": f"Unity {launch} launcher failed before the Editor produced a log or verification report.",
                "detail": (
                    f"The {launch} command exited with status {returncode} before Unity wrote {log_path.name}."
                    + (f" Launcher output: {launcher_detail}" if launcher_detail else "")
                ),
                "remediation": [
                    "Confirm the resolved Unity app bundle exists and launches from Finder.",
                    "Rerun runtime verification after opening this Unity version once from the GUI.",
                    "If the launcher path is correct but this persists, inspect the recorded launcher log for macOS Launch Services errors.",
                ],
            }
        diagnostic_status = diagnostic_info["status"]
        diagnostic = diagnostic_info["needle"]
        status = "pass" if tests["status"] == "pass" and not timed_out else (diagnostic_status or "fail")
        lane = {
            "platform": "EditorMethod",
            "status": status,
            "diagnostic": diagnostic,
            "diagnostic_code": diagnostic_info["code"],
            "diagnostic_detail": diagnostic_info["detail"],
            "remediation": diagnostic_info["remediation"],
            "returncode": returncode,
            "elapsed_seconds": elapsed,
            "terminated_after_pass": terminated_after_pass,
            "timed_out": timed_out,
            "mode": attempt["mode"],
            "launch": attempt["launch"],
            "command": attempt["cmd"],
            "unity_command": attempt["unity_command"],
            "results_json": str(result_json),
            "log": str(log_path),
            "launcher_log": str(attempt["launcher_log"]) if attempt.get("launcher_log") else None,
            "tests": tests,
            "details": payload,
        }
        summaries.append(
            {
                "launch": attempt["launch"],
                "status": status,
                "diagnostic_code": diagnostic_info["code"],
                "elapsed_seconds": elapsed,
                "log": str(log_path),
                "launcher_log": str(attempt["launcher_log"]) if attempt.get("launcher_log") else None,
            }
        )
        retryable_ui = (
            status == "blocked_license"
            and diagnostic_info["code"] == "unity_ui_entitlement_missing"
            and attempt["launch"] == "login-shell"
            and index + 1 < len(attempts)
        )
        if retryable_ui:
            primary_blocked_license_lane = lane
            continue
        final_lane = lane
        break

    assert final_lane is not None
    if (
        primary_blocked_license_lane is not None
        and final_lane["status"] == "fail"
        and final_lane["diagnostic_code"] == "unity_launch_services_launch_failed"
    ):
        final_lane["status"] = "blocked_license"
        final_lane["diagnostic"] = primary_blocked_license_lane["diagnostic"]
        final_lane["diagnostic_code"] = primary_blocked_license_lane["diagnostic_code"]
        final_lane["diagnostic_detail"] = (
            f"{primary_blocked_license_lane['diagnostic_detail']} "
            f"Launch Services fallback also failed before Unity started: {final_lane['diagnostic_detail']}"
        )
        final_lane["remediation"] = list(primary_blocked_license_lane["remediation"]) + [
            "Inspect the Launch Services fallback log if Finder can open Unity but the automated fallback still fails.",
        ]
    if len(summaries) > 1:
        final_lane["attempts"] = summaries
    return final_lane


def run_unity_tests(editor: str, project_dir: Path, report_dir: Path, platform: str, *, timeout: int) -> dict[str, object]:
    results_xml = report_dir / f"unity_{platform.lower()}_test_results.xml"
    log_path = report_dir / f"unity_{platform.lower()}_test.log"
    cmd = [
        editor,
        "-batchmode",
    ]
    cmd.extend(unity_graphics_args())
    cmd.extend([
        "-accept-apiupdate",
        "-quit",
        "-projectPath",
        str(project_dir),
        "-runTests",
        "-testPlatform",
        platform,
        "-testResults",
        str(results_xml),
        "-logFile",
        str(log_path),
    ])
    started = time.monotonic()
    env = unity_runtime_env(report_dir / f"unity_{platform.lower()}_method_unused.json")
    completed = subprocess.run(cmd, cwd=ROOT, env=env, timeout=timeout)
    elapsed = round(time.monotonic() - started, 3)
    parsed = parse_nunit(results_xml)
    diagnostic_info = analyze_log(log_path)
    diagnostic_status = diagnostic_info["status"]
    diagnostic = diagnostic_info["needle"]
    status = "pass" if completed.returncode == 0 and parsed["status"] == "pass" else (diagnostic_status or "fail")
    return {
        "platform": platform,
        "status": status,
        "diagnostic": diagnostic,
        "diagnostic_code": diagnostic_info["code"],
        "diagnostic_detail": diagnostic_info["detail"],
        "remediation": diagnostic_info["remediation"],
        "returncode": completed.returncode,
        "elapsed_seconds": elapsed,
        "command": cmd,
        "results_xml": str(results_xml),
        "log": str(log_path),
        "tests": parsed,
    }


def render_markdown(report: dict[str, object]) -> str:
    lines = [
        "# Unity Runtime Verification Report",
        "",
        f"- status: `{report['overall_status']}`",
        f"- unity_version: `{report.get('unity_version', 'unknown')}`",
        f"- editor: `{report.get('editor', 'missing')}`",
        f"- project_dir: `{report['project_dir']}`",
        "",
        "## Phase 1 Exit Criteria",
        "",
    ]
    for criterion in report.get("phase1_exit_criteria", []):
        lines.append(f"- `{criterion['status']}` {criterion['name']}: {criterion['note']}")
        for check in criterion.get("required_checks", []):
            lines.append(f"  check: {check.get('status', 'missing')} {check.get('name', 'unnamed')}")
    lines.extend([
        "",
        "## Test Platforms",
        "",
    ])
    for lane in report["lanes"]:
        tests = lane["tests"]
        diagnostic = f" diagnostic={lane['diagnostic']!r}" if lane.get("diagnostic") else ""
        diagnostic_code = f" code={lane['diagnostic_code']!r}" if lane.get("diagnostic_code") else ""
        lines.append(
            f"- `{lane['status']}` {lane['platform']}: total={tests['total']} "
            f"passed={tests['passed']} failed={tests['failed']} skipped={tests['skipped']}{diagnostic}{diagnostic_code}"
        )
        if lane.get("diagnostic_detail"):
            lines.append(f"  detail: {lane['diagnostic_detail']}")
        for step in lane.get("remediation", []):
            lines.append(f"  remediation: {step}")
        details = lane.get("details") or {}
        if details.get("schema") == "fastdis.unity_editor_method_verification.v1":
            lines.append(f"  verifier: total={details.get('total', 0)} passed={details.get('passed', 0)} failed={details.get('failed', 0)}")
            for check in details.get("checks", []):
                lines.append(f"  check: {check.get('status', 'unknown')} {check.get('name', 'unnamed')}")
        for attempt in lane.get("attempts", []):
            lines.append(
                f"  attempt: launch={attempt.get('launch', 'unknown')} status={attempt.get('status', 'unknown')} "
                f"code={attempt.get('diagnostic_code', 'none')} elapsed={attempt.get('elapsed_seconds', 0)}"
            )
    lines.append("")
    return "\n".join(lines)


def _read_json(path: Path) -> dict[str, object] | None:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _is_transient_failed_attempt(report: dict[str, object]) -> bool:
    if report.get("overall_status") == "pass":
        return False
    lanes = report.get("lanes")
    if not isinstance(lanes, list) or not lanes:
        return True
    for lane in lanes:
        if not isinstance(lane, dict):
            continue
        tests = lane.get("tests")
        details = lane.get("details")
        total = int(tests.get("total", 0) or 0) if isinstance(tests, dict) else 0
        if total > 0:
            return False
        if isinstance(details, dict) and details:
            return False
    return True


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--unity-version", help="Unity editor version prefix, for example 6000.5")
    parser.add_argument("--platform", action="append", choices=("EditMode", "PlayMode"), default=None)
    parser.add_argument("--project-dir", type=Path, help="Scratch project path; defaults under FASTDIS_UNITY_WORK_ROOT")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_REPORT_DIR)
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--runner", choices=("editor-method", "test-framework"), default="editor-method")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    load_local_env.load()
    args = parse_args(argv)
    install = unity_env.resolve_install(args.unity_version)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    project_dir = args.project_dir or (unity_env.work_root() / "runtime_test_project")
    platforms = args.platform or ["EditMode", "PlayMode"]

    if install is None or not install.editor_path:
        report = {
            "overall_status": "skip",
            "reason": "Unity editor not found",
            "requested_version": args.unity_version,
            "project_dir": str(project_dir),
            "lanes": [],
        }
        (args.out_dir / "unity_runtime_verification.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2))
        return 2

    create_project(project_dir)
    lanes: list[dict[str, object]] = []
    if args.dry_run:
        lanes = [
            {
                "platform": platform,
                "status": "dry_run",
                "returncode": 0,
                "elapsed_seconds": 0.0,
                "command": [install.editor_path, "-batchmode", "-runTests", "-testPlatform", platform],
                "tests": {"status": "dry_run", "total": 0, "passed": 0, "failed": 0, "skipped": 0},
            }
            for platform in platforms
        ]
    elif args.runner == "editor-method":
        lanes.append(run_unity_editor_method(install.editor_path, project_dir, args.out_dir, timeout=args.timeout))
    else:
        for platform in platforms:
            lanes.append(run_unity_tests(install.editor_path, project_dir, args.out_dir, platform, timeout=args.timeout))

    if args.dry_run:
        overall = "dry_run"
    elif lanes and all(lane["status"] == "pass" for lane in lanes):
        overall = "pass"
    elif lanes and any(lane["status"] == "blocked_license" for lane in lanes):
        overall = "blocked_license"
    else:
        overall = "fail"
    report = {
        "schema": "fastdis.unity_runtime_verification.v1",
        "overall_status": overall,
        "requested_version": args.unity_version,
        "unity_version": install.version,
        "editor": install.editor_path,
        "package_root": str(PACKAGE_ROOT),
        "project_dir": str(project_dir),
        "runner": args.runner,
        "lanes": lanes,
    }
    report["phase1_exit_criteria"] = derive_phase1_exit_criteria(report)
    json_path = args.out_dir / "unity_runtime_verification.json"
    md_path = args.out_dir / "unity_runtime_verification.md"
    previous_report = _read_json(json_path)
    if previous_report and previous_report.get("overall_status") == "pass" and _is_transient_failed_attempt(report):
        previous_report["phase1_exit_criteria"] = derive_phase1_exit_criteria(previous_report)
        attempt_json_path = args.out_dir / "unity_runtime_verification_attempt.json"
        attempt_md_path = args.out_dir / "unity_runtime_verification_attempt.md"
        attempt_json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        attempt_md_path.write_text(render_markdown(report), encoding="utf-8")
        json_path.write_text(json.dumps(previous_report, indent=2) + "\n", encoding="utf-8")
        md_path.write_text(render_markdown(previous_report), encoding="utf-8")
        print(f"Preserved last known-good runtime report: {json_path}")
        print(f"Recorded failed retry attempt: {attempt_json_path}")
    else:
        json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        md_path.write_text(render_markdown(report), encoding="utf-8")
    print(f"JSON: {json_path}")
    print(f"Markdown: {md_path}")
    return 0 if overall in {"pass", "dry_run"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
