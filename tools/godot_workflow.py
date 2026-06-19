#!/usr/bin/env python3
"""Operator-facing Godot workflow wrapper for discovery, build, and verification."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess

import godot_env
import load_local_env


ROOT = Path(__file__).resolve().parents[1]
GDEXTENSION_DIR = ROOT / "examples" / "godot" / "fastdis_gdextension"
DEMO_BIN_DIR = ROOT / "examples" / "godot" / "fastdis_demo" / "addons" / "fastdis" / "bin"
VERIFY_BIN_DIR = ROOT / "examples" / "godot" / "fastdis_orientation_verification" / "addons" / "fastdis" / "bin"


def run_step(cmd: list[str]) -> int:
    print("+", " ".join(cmd))
    completed = subprocess.run(cmd, cwd=ROOT)
    return completed.returncode


def staged_state() -> dict[str, bool]:
    wrapper_present = any((DEMO_BIN_DIR / name).is_file() for name in godot_env.wrapper_names())
    verify_wrapper_present = any((VERIFY_BIN_DIR / name).is_file() for name in godot_env.wrapper_names())
    shared_present = any((DEMO_BIN_DIR / name).is_file() for name in godot_env.shared_library_names())
    verify_shared_present = any((VERIFY_BIN_DIR / name).is_file() for name in godot_env.shared_library_names())
    return {
        "demo_wrapper_present": wrapper_present,
        "verify_wrapper_present": verify_wrapper_present,
        "demo_shared_present": shared_present,
        "verify_shared_present": verify_shared_present,
    }


def doctor_payload() -> dict[str, object]:
    host = godot_env.describe_host()
    checks: list[dict[str, str]] = []

    def add_check(name: str, ok: bool, detail: str) -> None:
        checks.append({"name": name, "status": "ok" if ok else "fail", "detail": detail})

    add_check("godot", bool(host["godot"]), str(host["godot"] or "missing godot executable"))
    add_check("scons", bool(host["scons"]), str(host["scons"] or "missing scons executable"))
    add_check(
        "cmake",
        shutil.which("cmake") is not None,
        shutil.which("cmake") or "missing cmake executable",
    )
    add_check(
        "godot-cpp",
        (GDEXTENSION_DIR / "godot-cpp" / "SConstruct").is_file(),
        "examples/godot/fastdis_gdextension/godot-cpp/SConstruct",
    )
    staged = staged_state()
    add_check("demo wrapper", staged["demo_wrapper_present"], str(DEMO_BIN_DIR))
    add_check("verify wrapper", staged["verify_wrapper_present"], str(VERIFY_BIN_DIR))
    add_check("demo shared lib", staged["demo_shared_present"], str(DEMO_BIN_DIR))
    add_check("verify shared lib", staged["verify_shared_present"], str(VERIFY_BIN_DIR))

    critical = checks[:4]
    status = "ok" if all(check["status"] == "ok" for check in critical) else "needs-attention"
    return {
        "status": status,
        "host": host,
        "checks": checks,
        "next_steps": [
            "Build the extension: python tools/godot_workflow.py build",
            "Run the harness: python tools/godot_workflow.py verify",
            "Run the demo smoke: python tools/godot_workflow.py demo",
            "Run everything: python tools/godot_workflow.py full",
        ],
    }


def print_doctor(payload: dict[str, object]) -> None:
    host = payload["host"]
    print("Godot doctor")
    print(f"status: {payload['status']}")
    print(f"platform: {host['platform']}")
    print(f"arch: {host['arch']}")
    print(f"godot: {host['godot'] or 'missing'}")
    print(f"scons: {host['scons'] or 'missing'}")
    print(f"repo_root: {host['repo_root']}")
    print(f"repo_alias_root: {host['repo_alias_root']}")
    print(f"uses_repo_alias: {'yes' if host['uses_repo_alias'] else 'no'}")
    print("checks:")
    for check in payload["checks"]:
        print(f"  - {check['name']}: {check['status']} ({check['detail']})")
    print("next:")
    for step in payload["next_steps"]:
        print(f"  - {step}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    discover = subparsers.add_parser("discover", help="List discovered Godot/SCons tools and host settings")
    discover.add_argument("--format", choices=("text", "json"), default="text")

    doctor = subparsers.add_parser("doctor", help="Check the current machine for Godot build prerequisites")
    doctor.add_argument("--format", choices=("text", "json"), default="text")

    build = subparsers.add_parser("build", help="Build/stage the FastDIS Godot extension and native library")
    build.add_argument("--skip-native-build", action="store_true", help="Skip the libfastdis rebuild")

    verify = subparsers.add_parser("verify", help="Run the Godot orientation verification harness")
    verify.add_argument("--dry-run", action="store_true", help="Print the command without executing it")
    verify.add_argument("--skip-build", action="store_true", help="Do not rebuild/stage before running the harness")

    demo = subparsers.add_parser("demo", help="Run the Godot demo replay smoke test")
    demo.add_argument("--dry-run", action="store_true", help="Print the command without executing it")
    demo.add_argument("--skip-build", action="store_true", help="Do not rebuild/stage before running the smoke test")

    subparsers.add_parser("full", help="Doctor, build, verify orientation, and run the demo smoke test")
    return parser.parse_args()


def command_discover(args: argparse.Namespace) -> int:
    payload = godot_env.describe_host()
    if args.format == "json":
        print(json.dumps(payload, indent=2))
    else:
        for key, value in payload.items():
            print(f"{key}: {value}")
    return 0 if payload["godot"] else 1


def command_doctor(args: argparse.Namespace) -> int:
    payload = doctor_payload()
    if args.format == "json":
        print(json.dumps(payload, indent=2))
    else:
        print_doctor(payload)
    return 0 if payload["status"] == "ok" else 2


def command_build(args: argparse.Namespace) -> int:
    cmd = godot_env.python_command() + ["tools/build_godot_extension.py"]
    if args.skip_native_build:
        cmd.append("--skip-native-build")
    return run_step(cmd)


def command_verify(args: argparse.Namespace) -> int:
    cmd = godot_env.python_command() + ["tools/run_godot_orientation_verification.py"]
    if args.dry_run:
        cmd.append("--dry-run")
    if args.skip_build:
        cmd.append("--skip-build")
    return run_step(cmd)


def command_demo(args: argparse.Namespace) -> int:
    cmd = godot_env.python_command() + ["tools/run_godot_demo_smoke.py"]
    if args.dry_run:
        cmd.append("--dry-run")
    if args.skip_build:
        cmd.append("--skip-build")
    return run_step(cmd)


def command_full() -> int:
    doctor_args = argparse.Namespace(format="text")
    if command_doctor(doctor_args) != 0:
        return 2
    build_args = argparse.Namespace(skip_native_build=False)
    build_code = command_build(build_args)
    if build_code != 0:
        return build_code
    verify_args = argparse.Namespace(dry_run=False, skip_build=True)
    verify_code = command_verify(verify_args)
    if verify_code != 0:
        return verify_code
    demo_args = argparse.Namespace(dry_run=False, skip_build=True)
    return command_demo(demo_args)


def main() -> int:
    load_local_env.load()
    args = parse_args()
    if args.command == "discover":
        return command_discover(args)
    if args.command == "doctor":
        return command_doctor(args)
    if args.command == "build":
        return command_build(args)
    if args.command == "verify":
        return command_verify(args)
    if args.command == "demo":
        return command_demo(args)
    if args.command == "full":
        return command_full()
    raise SystemExit(f"Unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
