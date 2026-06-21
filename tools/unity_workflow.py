#!/usr/bin/env python3
"""Operator-facing Unity workflow wrapper for discovery, package checks, and reports."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import platform
import subprocess

import load_local_env
import unity_env


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = ROOT / "integrations" / "unity" / "com.sheepfling.fastdis"
DEFAULT_REPORT_DIR = ROOT / "build" / "reports"


def host_native_key() -> str:
    system = platform.system().lower()
    if system == "darwin":
        return "macos_dylib"
    if system == "windows":
        return "windows_dll"
    return "linux_so"


def run_step(cmd: list[str], *, preserve_unity_login: bool = False) -> int:
    print("+", " ".join(cmd))
    if preserve_unity_login:
        old_preserve = os.environ.get("FASTDIS_UNITY_PRESERVE_HOME")
        os.environ["FASTDIS_UNITY_PRESERVE_HOME"] = "1"
        try:
            env = unity_env.build_env()
        finally:
            if old_preserve is None:
                os.environ.pop("FASTDIS_UNITY_PRESERVE_HOME", None)
            else:
                os.environ["FASTDIS_UNITY_PRESERVE_HOME"] = old_preserve
    else:
        env = unity_env.build_env()
    completed = subprocess.run(cmd, cwd=ROOT, env=env)
    return completed.returncode


def package_state() -> dict[str, bool]:
    required = {
        "package_json": PACKAGE_ROOT / "package.json",
        "readme": PACKAGE_ROOT / "README.md",
        "runtime_asmdef": PACKAGE_ROOT / "Runtime" / "FastDIS.Runtime.asmdef",
        "editor_asmdef": PACKAGE_ROOT / "Editor" / "FastDIS.Editor.asmdef",
        "runtime_tests": PACKAGE_ROOT / "Tests" / "Runtime" / "FastDIS.Runtime.Tests.asmdef",
        "editor_tests": PACKAGE_ROOT / "Tests" / "Editor" / "FastDIS.Editor.Tests.asmdef",
        "docs": PACKAGE_ROOT / "Documentation~" / "index.md",
        "minimal_sample": PACKAGE_ROOT / "Samples~" / "Minimal Receiver" / "README.md",
        "udp_sample": PACKAGE_ROOT / "Samples~" / "UDP Loopback" / "README.md",
        "orientation_sample": PACKAGE_ROOT / "Samples~" / "Orientation Verification" / "README.md",
        "lattice_sample": PACKAGE_ROOT / "Samples~" / "Lattice Lab Bridge" / "README.md",
    }
    return {name: path.exists() for name, path in required.items()}


def staged_native_state() -> dict[str, bool]:
    return {
        "windows_dll": (PACKAGE_ROOT / "Runtime" / "Plugins" / "Windows" / "x86_64" / "fastdis.dll").is_file(),
        "macos_dylib": (PACKAGE_ROOT / "Runtime" / "Plugins" / "macOS" / "libfastdis.dylib").is_file(),
        "linux_so": (PACKAGE_ROOT / "Runtime" / "Plugins" / "Linux" / "x86_64" / "libfastdis.so").is_file(),
    }


def truthy_env(name: str) -> bool:
    return os.environ.get(name) in {"1", "true", "TRUE", "yes", "YES"}


def unity_runtime_launcher_mode() -> str:
    if platform.system().lower() == "darwin" and not truthy_env("FASTDIS_UNITY_BATCHMODE"):
        return "macos-login-shell-interactive"
    if truthy_env("FASTDIS_UNITY_FORCE_NOGRAPHICS"):
        return "batchmode-nographics"
    return "batchmode"


def latest_runtime_report(out_dir: Path = DEFAULT_REPORT_DIR) -> dict[str, object] | None:
    path = out_dir / "unity_runtime_verification.json"
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def doctor_payload(version: str | None) -> dict[str, object]:
    install = unity_env.resolve_install(version)
    checks: list[dict[str, str]] = []

    def add_check(name: str, ok: bool, detail: str, *, warn: bool = False) -> None:
        checks.append({"name": name, "status": "ok" if ok else ("warn" if warn else "fail"), "detail": detail})

    add_check("unity editor", install is not None and install.editor_path is not None, install.editor_path if install and install.editor_path else "missing Unity editor")
    if install is not None:
        add_check("unity version", True, install.version)
        for quirk in install.quirks:
            add_check(f"quirk:{quirk}", False, install.install_root, warn=True)

    work_ok, work_detail = unity_env.path_writable(unity_env.work_root())
    add_check("permission:work_root", work_ok, work_detail)
    package_ok, package_detail = unity_env.path_writable(PACKAGE_ROOT / "Runtime" / "Plugins")
    add_check("permission:package_plugins", package_ok, package_detail)

    for name, ok in package_state().items():
        add_check(f"package:{name}", ok, str(PACKAGE_ROOT))

    package = package_state()
    native = staged_native_state()
    current_native_ok = native[host_native_key()]
    add_check("native:current-platform", current_native_ok, host_native_key(), warn=True)
    add_check("native:macos", native["macos_dylib"], "Runtime/Plugins/macOS/libfastdis.dylib", warn=True)
    add_check("native:windows", native["windows_dll"], "Runtime/Plugins/Windows/x86_64/fastdis.dll", warn=True)
    add_check("native:linux", native["linux_so"], "Runtime/Plugins/Linux/x86_64/libfastdis.so", warn=True)
    launcher_mode = unity_runtime_launcher_mode()
    add_check("runtime:launcher", True, launcher_mode)
    if platform.system().lower() == "darwin":
        add_check(
            "runtime:macos-license-path",
            not truthy_env("FASTDIS_UNITY_BATCHMODE") and not truthy_env("FASTDIS_UNITY_FORCE_NOGRAPHICS"),
            "default login-shell interactive launcher avoids Unity Personal headless entitlement",
            warn=True,
        )
    if truthy_env("FASTDIS_UNITY_BATCHMODE"):
        add_check(
            "env:FASTDIS_UNITY_BATCHMODE",
            False,
            "forces batchmode; Unity Personal may fail with com.unity.editor.headless missing",
            warn=True,
        )
    if truthy_env("FASTDIS_UNITY_FORCE_NOGRAPHICS"):
        add_check(
            "env:FASTDIS_UNITY_FORCE_NOGRAPHICS",
            False,
            "forces -nographics; Unity Personal may fail with com.unity.editor.headless missing",
            warn=True,
        )

    runtime_report = latest_runtime_report()
    runtime_status = str(runtime_report.get("overall_status")) if runtime_report else "not_run"
    if runtime_report:
        first_lane = (runtime_report.get("lanes") or [{}])[0]
        runtime_detail = f"{runtime_status}; {first_lane.get('platform', 'unknown')} via {first_lane.get('launch', 'unknown')}"
    else:
        runtime_detail = "no build/reports/unity_runtime_verification.json yet"
    add_check("runtime:last-report", runtime_status == "pass", runtime_detail, warn=True)

    hard_fail = any(check["status"] == "fail" for check in checks)
    workflow_status = "pass" if install is not None and install.editor_path is not None and all(package.values()) else "fail"
    native_status = "pass" if current_native_ok else "not_verified"
    return {
        "requested_version": version,
        "status": "ok" if not hard_fail else "needs-attention",
        "unity_alpha5_result": "pass" if workflow_status == "pass" else "fail",
        "passed_scope": "workflow/package/native-staging parity",
        "next_scope": "Unity Editor runtime verification",
        "unity_workflow_status": workflow_status,
        "unity_native_status": native_status,
        "unity_demo_status": "not_run",
        "unity_runtime_status": runtime_status,
        "unity_runtime_launcher": launcher_mode,
        "native_current_platform": host_native_key(),
        "install": install.to_dict() if install else None,
        "package_root": str(PACKAGE_ROOT),
        "work_root": str(unity_env.work_root()),
        "work_root_has_spaces": " " in str(unity_env.work_root()),
        "checks": checks,
        "runtime_notes": [
            "Unity 6000 Personal on macOS may report com.unity.editor.headless missing when launched with -batchmode/-nographics or Unity Test Runner.",
            "The default runtime verifier uses an Editor executeMethod harness through a login shell so the signed-in Unity Hub license is visible.",
            "Use FASTDIS_UNITY_BATCHMODE=1 or FASTDIS_UNITY_FORCE_NOGRAPHICS=1 only on machines with a valid headless/batchmode entitlement.",
            "If a run fails, inspect build/reports/unity_runtime_verification.json and build/reports/unity_editor_method.log for diagnostic_code/remediation.",
        ],
        "next_steps": [
            "Run package checks: python tools/unity_workflow.py verify",
            "Stage host native library: python tools/unity_workflow.py build",
            "Run a Unity lane report: python tools/unity_workflow.py report",
            "Run Unity Editor runtime tests: python tools/unity_workflow.py runtime-verify --unity-version 6000.5",
            "Install in Unity Package Manager from the Git URL with ?path=integrations/unity/com.sheepfling.fastdis",
        ],
    }


def print_doctor(payload: dict[str, object]) -> None:
    print("Unity doctor")
    print(f"status: {payload['status']}")
    print(f"unity_workflow_status: {payload['unity_workflow_status']}")
    print(f"unity_native_status: {payload['unity_native_status']}")
    print(f"unity_runtime_status: {payload['unity_runtime_status']}")
    print(f"unity_runtime_launcher: {payload['unity_runtime_launcher']}")
    print(f"unity_demo_status: {payload['unity_demo_status']}")
    print(f"requested_version: {payload['requested_version'] or 'default'}")
    install = payload["install"]
    if install:
        print(f"resolved_version: {install['version']}")
        print(f"install_root: {install['install_root']}")
        print(f"editor: {install['editor_path'] or 'missing'}")
    else:
        print("resolved_version: none")
    print(f"package_root: {payload['package_root']}")
    print(f"work_root: {payload['work_root']}")
    print("checks:")
    for check in payload["checks"]:
        print(f"  - {check['name']}: {check['status']} ({check['detail']})")
    print("next:")
    for step in payload["next_steps"]:
        print(f"  - {step}")
    print("runtime notes:")
    for note in payload["runtime_notes"]:
        print(f"  - {note}")


def write_report(payload: dict[str, object], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "unity_workflow_report.json"
    md_path = out_dir / "unity_workflow_report.md"
    json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Unity Workflow Report",
        "",
        f"- status: `{payload['status']}`",
        f"- unity_workflow_status: `{payload['unity_workflow_status']}`",
        f"- unity_native_status: `{payload['unity_native_status']}`",
        f"- unity_runtime_status: `{payload['unity_runtime_status']}`",
        f"- unity_runtime_launcher: `{payload['unity_runtime_launcher']}`",
        f"- unity_demo_status: `{payload['unity_demo_status']}`",
        f"- passed_scope: `{payload['passed_scope']}`",
        f"- next_scope: `{payload['next_scope']}`",
        f"- package_root: `{payload['package_root']}`",
        "",
        "## Checks",
        "",
    ]
    for check in payload["checks"]:
        lines.append(f"- `{check['status']}` {check['name']}: {check['detail']}")
    lines.extend(["", "## Runtime Notes", ""])
    for note in payload["runtime_notes"]:
        lines.append(f"- {note}")
    lines.append("")
    md_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"JSON: {json_path}")
    print(f"Markdown: {md_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    discover = subparsers.add_parser("discover", help="List detected Unity installs")
    discover.add_argument("--format", choices=("text", "json"), default="text")

    doctor = subparsers.add_parser("doctor", help="Check Unity install and package prerequisites")
    doctor.add_argument("--unity-version", help="Unity editor version prefix, for example 6000.5")
    doctor.add_argument("--format", choices=("text", "json"), default="text")

    verify = subparsers.add_parser("verify", help="Run Unity package structure tests")
    verify.add_argument("--unity-version", help="Accepted for workflow parity; package checks do not launch Unity")

    runtime_verify = subparsers.add_parser("runtime-verify", help="Run Unity package tests in a scratch Unity project")
    runtime_verify.add_argument("--unity-version", help="Unity editor version prefix, for example 6000.5")
    runtime_verify.add_argument("--platform", action="append", choices=("EditMode", "PlayMode"), help="Test platform to run; defaults to both")
    runtime_verify.add_argument("--project-dir", help="Scratch Unity project directory")
    runtime_verify.add_argument("--out-dir", default=str(ROOT / "build" / "reports"))
    runtime_verify.add_argument("--timeout", type=int, default=600)
    runtime_verify.add_argument("--dry-run", action="store_true")

    build = subparsers.add_parser("build", help="Build native FastDIS and stage Unity native plug-ins")
    build.add_argument("--unity-version", help="Accepted for workflow parity")
    build.add_argument("--skip-native-build", action="store_true", help="Only stage an existing build/libfastdis artifact")
    build.add_argument("--all-native", action="store_true", help="Build/stage macOS, Windows, and Linux native plug-ins when toolchains are available")

    report = subparsers.add_parser("report", help="Write Unity workflow report")
    report.add_argument("--unity-version", help="Unity editor version prefix, for example 6000.5")
    report.add_argument("--out-dir", default=str(ROOT / "build" / "reports"))

    full = subparsers.add_parser("full", help="Doctor, verify, run Unity runtime tests, and write a report")
    full.add_argument("--unity-version", help="Unity editor version prefix, for example 6000.5")
    full.add_argument("--skip-runtime", action="store_true", help="Skip Unity Editor batchmode runtime tests")
    return parser.parse_args()


def command_discover(args: argparse.Namespace) -> int:
    payload = unity_env.describe_host()
    if args.format == "json":
        print(json.dumps(payload, indent=2))
    else:
        installs = payload["installs"]
        if not installs:
            print("No Unity installs discovered.")
            return 1
        for install in installs:
            print(f"{install['version']}: {install['install_root']}")
            print(f"  editor: {install['editor_path'] or 'missing'}")
            print(f"  source: {install['source']}")
            quirks = ", ".join(install["quirks"]) if install["quirks"] else "none"
            print(f"  quirks: {quirks}")
    return 0


def command_doctor(args: argparse.Namespace) -> int:
    payload = doctor_payload(args.unity_version)
    if args.format == "json":
        print(json.dumps(payload, indent=2))
    else:
        print_doctor(payload)
    return 0 if payload["status"] == "ok" else 2


def command_verify(_args: argparse.Namespace) -> int:
    return run_step(unity_env.python_command() + ["-m", "pytest", "tests/test_unity_upm_package.py"])


def command_runtime_verify(args: argparse.Namespace) -> int:
    cmd = unity_env.python_command() + ["tools/run_unity_editor_tests.py"]
    if args.unity_version:
        cmd.extend(["--unity-version", args.unity_version])
    if args.project_dir:
        cmd.extend(["--project-dir", args.project_dir])
    if args.out_dir:
        cmd.extend(["--out-dir", args.out_dir])
    if args.timeout:
        cmd.extend(["--timeout", str(args.timeout)])
    for platform_name in args.platform or []:
        cmd.extend(["--platform", platform_name])
    if args.dry_run:
        cmd.append("--dry-run")
    return run_step(cmd, preserve_unity_login=True)


def command_build(args: argparse.Namespace) -> int:
    if args.all_native:
        matrix_code = run_step(unity_env.python_command() + ["tools/build_unity_native_matrix.py", "build"])
        if matrix_code != 0:
            return matrix_code
        return command_verify(args)
    if not args.skip_native_build:
        native_code = run_step(unity_env.python_command() + ["tools/build_native.py"])
        if native_code != 0:
            return native_code
    stage_code = run_step(unity_env.python_command() + ["tools/stage_unity_native.py"])
    if stage_code != 0:
        return stage_code
    return command_verify(args)


def command_report(args: argparse.Namespace) -> int:
    payload = doctor_payload(args.unity_version)
    write_report(payload, Path(args.out_dir))
    return 0 if payload["status"] == "ok" else 2


def command_full(args: argparse.Namespace) -> int:
    doctor_args = argparse.Namespace(unity_version=args.unity_version, format="text")
    doctor_code = command_doctor(doctor_args)
    build_args = argparse.Namespace(unity_version=args.unity_version, skip_native_build=True, all_native=False)
    build_code = command_build(build_args)
    verify_code = command_verify(args)
    runtime_code = 0
    if not args.skip_runtime:
        runtime_args = argparse.Namespace(
            unity_version=args.unity_version,
            platform=None,
            project_dir=None,
            out_dir=str(ROOT / "build" / "reports"),
            timeout=600,
            dry_run=False,
        )
        runtime_code = command_runtime_verify(runtime_args)
    report_args = argparse.Namespace(unity_version=args.unity_version, out_dir=str(ROOT / "build" / "reports"))
    report_code = command_report(report_args)
    return doctor_code or build_code or verify_code or runtime_code or report_code


def main() -> int:
    load_local_env.load()
    args = parse_args()
    if args.command == "discover":
        return command_discover(args)
    if args.command == "doctor":
        return command_doctor(args)
    if args.command == "verify":
        return command_verify(args)
    if args.command == "runtime-verify":
        return command_runtime_verify(args)
    if args.command == "build":
        return command_build(args)
    if args.command == "report":
        return command_report(args)
    if args.command == "full":
        return command_full(args)
    raise SystemExit(f"Unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
