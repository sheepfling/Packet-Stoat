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
    (project_dir / "Packages").mkdir(parents=True)
    (project_dir / "ProjectSettings").mkdir(parents=True)
    package_uri = PACKAGE_ROOT.as_posix()
    manifest = {
        "dependencies": {
            "com.sheepfling.fastdis": f"file:{package_uri}",
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


def run_editor_method_process(
    cmd: list[str],
    result_json: Path,
    log_path: Path,
    *,
    env: dict[str, str] | None,
    timeout: int,
) -> tuple[int, bool, bool, dict[str, object] | None]:
    process = subprocess.Popen(cmd, cwd=ROOT, env=env)
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
    result_json = report_dir / "unity_editor_method_report.json"
    log_path = report_dir / "unity_editor_method.log"
    if result_json.exists():
        result_json.unlink()
    if log_path.exists():
        log_path.unlink()
    interactive = use_interactive_editor_method()
    unity_cmd = [
        editor,
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
    launch_via_shell = interactive and host_platform.system().lower() == "darwin"
    if launch_via_shell:
        command = " ".join(shlex.quote(part) for part in unity_cmd)
        cmd = ["/bin/zsh", "-lc", command]
    else:
        cmd = [editor]
        if not interactive:
            cmd.extend(["-batchmode", *unity_graphics_args()])
        cmd.extend(unity_cmd[1:])
    started = time.monotonic()
    env = None if launch_via_shell else unity_runtime_env(result_json)
    returncode, terminated_after_pass, timed_out, early_diagnostic_info = run_editor_method_process(
        cmd,
        result_json,
        log_path,
        env=env,
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
    diagnostic_status = diagnostic_info["status"]
    diagnostic = diagnostic_info["needle"]
    status = "pass" if tests["status"] == "pass" and not timed_out else (diagnostic_status or "fail")
    return {
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
        "mode": "interactive" if interactive else "batchmode",
        "launch": "login-shell" if launch_via_shell else "direct",
        "command": cmd,
        "unity_command": unity_cmd,
        "results_json": str(result_json),
        "log": str(log_path),
        "tests": tests,
        "details": payload,
    }


def run_unity_tests(editor: str, project_dir: Path, report_dir: Path, platform: str, *, timeout: int) -> dict[str, object]:
    results_xml = report_dir / f"unity_{platform.lower()}_test_results.xml"
    log_path = report_dir / f"unity_{platform.lower()}_test.log"
    cmd = [
        editor,
        "-batchmode",
    ]
    cmd.extend(unity_graphics_args())
    cmd.extend([
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
        "## Test Platforms",
        "",
    ]
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
    lines.append("")
    return "\n".join(lines)


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
    json_path = args.out_dir / "unity_runtime_verification.json"
    md_path = args.out_dir / "unity_runtime_verification.md"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    print(f"JSON: {json_path}")
    print(f"Markdown: {md_path}")
    return 0 if overall in {"pass", "dry_run"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
