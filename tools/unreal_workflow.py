#!/usr/bin/env python3
"""Operator-facing Unreal workflow wrapper for discovery, packaging, and verification."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess

import load_local_env
import unreal_env


ROOT = Path(__file__).resolve().parents[1]
ORIENTATION_PROJECT_PATH = ROOT / "examples" / "unreal" / "FastDisOrientationVerification" / "FastDisOrientationVerification.uproject"
DEFAULT_SUPPORTED_VERSIONS = ["5.7", "5.8"]


def _version_label(version: str | None) -> str:
    return version or "default"


def run_step(cmd: list[str]) -> int:
    print("+", " ".join(cmd))
    completed = subprocess.run(cmd, cwd=ROOT)
    return completed.returncode


def install_for_version(version: str | None) -> unreal_env.UnrealInstall | None:
    installs = unreal_env.discover_installs()
    if version is not None:
        for install in installs:
            if install.version == version:
                return install
        return None
    if installs:
        return installs[-1]
    return None


def doctor_payload(version: str | None) -> dict[str, object]:
    install = install_for_version(version)
    payload: dict[str, object] = {
        "requested_version": version,
        "resolved_version": None,
        "status": "ok",
        "install": None,
        "checks": [],
        "next_steps": [],
    }

    if install is None:
        payload["status"] = "missing-install"
        payload["checks"] = [
            {
                "name": "engine install",
                "status": "fail",
                "detail": f"no Unreal install discovered for {_version_label(version)}",
            }
        ]
        payload["next_steps"] = [
            "Set FASTDIS_UNREAL_ENGINE_DIR or FASTDIS_UNREAL_ENGINE_DIR_5_8 style variables in .env.local.",
            "Run `python tools/list_unreal_installs.py` to inspect what this machine can see.",
        ]
        return payload

    checks: list[dict[str, str]] = []

    def add_check(name: str, status: str, detail: str) -> None:
        checks.append({"name": name, "status": status, "detail": detail})

    add_check("engine root", "ok", install.install_root)
    add_check("editor", "ok" if install.editor_path is not None else "fail", install.editor_path or "missing editor executable")
    add_check("automation tool", "ok" if install.uat_path is not None else "fail", install.uat_path or "missing RunUAT")
    add_check("build tool", "ok" if install.ubt_path is not None else "fail", install.ubt_path or "missing UnrealBuildTool.dll")
    add_check("bundled dotnet", "ok" if install.dotnet_path is not None else "fail", install.dotnet_path or "missing bundled dotnet")

    rider = shutil.which("rider")
    add_check("rider", "ok" if rider else "warn", rider or "optional; set FASTDIS_RIDER or put rider on PATH")

    permissions = unreal_env.permission_probe(install)
    for check in permissions["checks"]:
        add_check(f"permission:{check['name']}", str(check["status"]), str(check["detail"]))

    if install.dotnet_path and install.ubt_path:
        probe = unreal_env.probe_host_platform_support(install, ORIENTATION_PROJECT_PATH)
        add_check("host platform probe", str(probe["status"]), str(probe["detail"]))
    else:
        probe = None

    has_failures = any(check["status"] == "fail" for check in checks[:5])
    if probe is not None and probe["status"] == "fail":
        has_failures = True
    payload["resolved_version"] = install.version
    payload["status"] = "ok" if not has_failures else "needs-attention"
    payload["install"] = install.to_dict()
    payload["permissions"] = permissions
    if probe is not None:
        payload["platform_probe"] = probe
    payload["checks"] = checks
    if probe is not None and probe["status"] == "fail":
        payload["next_steps"] = [
            f"Resolve the host/engine compatibility issue for {install.version or 'this lane'} before packaging or automation runs.",
            "Use a passing lane such as 5.7 or 5.8 on this machine, or adjust the host SDK/engine install.",
            "If the issue is permission-related, rerun from a shell that can write Unreal Engine intermediates or prebuild the target outside the sandbox.",
            "Run the full matrix for a cross-version view: python tools/unreal_workflow.py matrix",
        ]
    else:
        payload["next_steps"] = [
            f"Package plugin: python tools/unreal_workflow.py build --engine-version {install.version or '5.8'}",
            f"Run orientation harness: python tools/unreal_workflow.py verify --engine-version {install.version or '5.8'}",
            f"Run replay demo smoke: python tools/unreal_workflow.py demo --engine-version {install.version or '5.8'}",
            "Run the full matrix: python tools/unreal_workflow.py matrix",
        ]
        if any(check["name"] == "permission:engine_intermediate" and check["status"] != "ok" for check in checks):
            payload["next_steps"].insert(
                0,
                "Engine intermediates are not writable in this environment; live Unreal build/verify lanes may need a normal terminal or approved sandbox escalation.",
            )
    return payload


def print_doctor(payload: dict[str, object]) -> None:
    requested = payload["requested_version"] or "default"
    resolved = payload["resolved_version"] or "none"
    print(f"Unreal doctor for {requested}")
    print(f"status: {payload['status']}")
    print(f"resolved_version: {resolved}")
    install = payload["install"]
    if install:
        print(f"install_root: {install['install_root']}")
        if install["quirks"]:
            print("quirks:")
            for quirk in install["quirks"]:
                print(f"  - {quirk}")
        permissions = payload.get("permissions")
        if permissions:
            print(f"work_root: {permissions['work_root']}")
    else:
        print("install_root: missing")
    print("checks:")
    for check in payload["checks"]:
        print(f"  - {check['name']}: {check['status']} ({check['detail']})")
    print("next:")
    for step in payload["next_steps"]:
        print(f"  - {step}")


def add_engine_version(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--engine-version", help="Versioned Unreal env selector, for example 5.7 or 5.8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    discover = subparsers.add_parser("discover", help="List detected Unreal installs")
    discover.add_argument("--format", choices=("table", "json"), default="table")

    doctor = subparsers.add_parser("doctor", help="Check the current machine for Unreal build prerequisites")
    add_engine_version(doctor)
    doctor.add_argument("--format", choices=("text", "json"), default="text")

    build = subparsers.add_parser("build", help="Build and package the FastDis Unreal plugin")
    add_engine_version(build)
    build.add_argument("--open-rider", action="store_true", help="Open the generated host project in Rider")
    build.add_argument("--no-clean-package", action="store_true", help="Keep the existing package directory")

    verify = subparsers.add_parser("verify", help="Run the Unreal orientation verification harness")
    add_engine_version(verify)
    verify.add_argument("--dry-run", action="store_true", help="Print the editor command without executing it")

    demo = subparsers.add_parser("demo", help="Run the Unreal replay/demo smoke harness")
    add_engine_version(demo)
    demo.add_argument("--dry-run", action="store_true", help="Print the editor command without executing it")

    matrix = subparsers.add_parser("matrix", help="Run the configured Unreal version matrix")
    matrix.add_argument("--versions", nargs="+", default=DEFAULT_SUPPORTED_VERSIONS, help="Versions to run")
    matrix.add_argument("--skip-plugin-build", action="store_true", help="Skip the plugin packaging lane")
    matrix.add_argument("--skip-orientation", action="store_true", help="Skip the orientation harness lane")
    matrix.add_argument("--skip-demo", action="store_true", help="Skip the replay/demo smoke lane")

    full = subparsers.add_parser("full", help="Doctor, package, verify orientation, and run the replay demo smoke for one Unreal lane")
    add_engine_version(full)
    full.add_argument("--open-rider", action="store_true", help="Open the generated host project in Rider after packaging")

    return parser.parse_args()


def command_discover(args: argparse.Namespace) -> int:
    installs = [install.to_dict() for install in unreal_env.discover_installs()]
    if args.format == "json":
        print(json.dumps(installs, indent=2))
        return 0 if installs else 1
    if not installs:
        print("No Unreal installs discovered.")
        return 1
    for install in installs:
        version = install["version"] or "unknown"
        quirks = ", ".join(install["quirks"]) if install["quirks"] else "none"
        print(f"{version}: {install['install_root']}")
        print(f"  editor: {install['editor_path'] or 'missing'}")
        print(f"  uat:    {install['uat_path'] or 'missing'}")
        print(f"  ubt:    {install['ubt_path'] or 'missing'}")
        print(f"  dotnet: {install['dotnet_path'] or 'missing'}")
        print(f"  source: {install['source']}")
        print(f"  quirks: {quirks}")
    return 0


def command_doctor(args: argparse.Namespace) -> int:
    payload = doctor_payload(args.engine_version)
    if args.format == "json":
        print(json.dumps(payload, indent=2))
    else:
        print_doctor(payload)
    return 0 if payload["status"] == "ok" else 2


def command_build(args: argparse.Namespace) -> int:
    cmd = unreal_env.python_command() + ["tools/build_unreal_plugin.py"]
    if args.engine_version:
        cmd.extend(["--engine-version", args.engine_version])
    if not args.no_clean_package:
        cmd.append("--clean-package")
    if args.open_rider:
        cmd.append("--open-rider")
    return run_step(cmd)


def command_verify(args: argparse.Namespace) -> int:
    cmd = unreal_env.python_command() + ["tools/run_unreal_orientation_verification.py"]
    if args.engine_version:
        cmd.extend(["--engine-version", args.engine_version])
    if args.dry_run:
        cmd.append("--dry-run")
    return run_step(cmd)


def command_demo(args: argparse.Namespace) -> int:
    cmd = unreal_env.python_command() + ["tools/run_unreal_demo_smoke.py"]
    if args.engine_version:
        cmd.extend(["--engine-version", args.engine_version])
    if args.dry_run:
        cmd.append("--dry-run")
    return run_step(cmd)


def command_matrix(args: argparse.Namespace) -> int:
    cmd = unreal_env.python_command() + ["tools/run_unreal_matrix.py", "--versions", *args.versions]
    if args.skip_plugin_build:
        cmd.append("--skip-plugin-build")
    if args.skip_orientation:
        cmd.append("--skip-orientation")
    if args.skip_demo:
        cmd.append("--skip-demo")
    return run_step(cmd)


def command_full(args: argparse.Namespace) -> int:
    doctor_args = argparse.Namespace(engine_version=args.engine_version, format="text")
    if command_doctor(doctor_args) != 0:
        return 2

    build_args = argparse.Namespace(
        engine_version=args.engine_version,
        open_rider=args.open_rider,
        no_clean_package=False,
    )
    build_code = command_build(build_args)
    if build_code != 0:
        return build_code

    verify_args = argparse.Namespace(engine_version=args.engine_version, dry_run=False)
    verify_code = command_verify(verify_args)
    if verify_code != 0:
        return verify_code

    demo_args = argparse.Namespace(engine_version=args.engine_version, dry_run=False)
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
    if args.command == "matrix":
        return command_matrix(args)
    if args.command == "full":
        return command_full(args)
    raise SystemExit(f"Unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
