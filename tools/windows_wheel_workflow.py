#!/usr/bin/env python3
"""Operator-facing workflow wrapper for Windows ctypes wheel cross-builds."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys

from artifacts import CMAKE_MINGW_WIN64, DIST_DIR
import load_local_env


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BUILD_DIR = CMAKE_MINGW_WIN64
DEFAULT_OUT_DIR = DIST_DIR
DEFAULT_MINGW_PREFIX = "x86_64-w64-mingw32"


def run_step(cmd: list[str]) -> int:
    print("+", " ".join(cmd))
    completed = subprocess.run(cmd, cwd=ROOT)
    return completed.returncode


def expected_tool_names(prefix: str) -> tuple[str, str]:
    return (f"{prefix}-gcc", f"{prefix}-g++")


def resolve_rc_tool(prefix: str) -> str | None:
    return shutil.which(f"{prefix}-windres") or shutil.which("windres")


def current_wheel(out_dir: Path) -> Path | None:
    wheels = sorted(out_dir.glob("fastdis-*-win_amd64.whl"), key=lambda path: path.stat().st_mtime)
    return wheels[-1] if wheels else None


def current_windows_dll(build_dir: Path) -> Path | None:
    matches = list(build_dir.rglob("fastdis.dll")) + list(build_dir.rglob("libfastdis.dll"))
    if not matches:
        return None
    return max(matches, key=lambda path: path.stat().st_mtime)


def discover_payload(prefix: str) -> dict[str, object]:
    host = {
        "platform": platform.system(),
        "arch": platform.machine(),
        "python": sys.executable,
        "cmake": shutil.which("cmake"),
        "mingw_prefix": prefix,
        "tools": {
            name: shutil.which(name)
            for name in expected_tool_names(prefix)
        },
        "rc_tool": resolve_rc_tool(prefix),
        "build_module": shutil.which(sys.executable) is not None,
        "build_dir": str(DEFAULT_BUILD_DIR),
        "out_dir": str(DEFAULT_OUT_DIR),
        "current_dll": str(current_windows_dll(DEFAULT_BUILD_DIR)) if current_windows_dll(DEFAULT_BUILD_DIR) else None,
        "current_wheel": str(current_wheel(DEFAULT_OUT_DIR)) if current_wheel(DEFAULT_OUT_DIR) else None,
    }
    return host


def doctor_payload(prefix: str) -> dict[str, object]:
    host = discover_payload(prefix)
    checks: list[dict[str, str]] = []

    def add_check(name: str, ok: bool, detail: str, *, warn: bool = False) -> None:
        checks.append(
            {
                "name": name,
                "status": "warn" if warn and not ok else ("ok" if ok else "fail"),
                "detail": detail,
            }
        )

    add_check("host platform", host["platform"] in {"Darwin", "Linux"}, str(host["platform"]), warn=True)
    add_check("cmake", bool(host["cmake"]), str(host["cmake"] or "missing cmake executable"))
    for tool_name, tool_path in host["tools"].items():
        add_check(tool_name, bool(tool_path), str(tool_path or f"missing {tool_name}"))
    add_check(
        f"{prefix}-windres or windres",
        bool(host["rc_tool"]),
        str(host["rc_tool"] or f"missing {prefix}-windres or windres"),
    )
    add_check("build dir", DEFAULT_BUILD_DIR.parent.exists(), str(DEFAULT_BUILD_DIR.parent))
    add_check("dist dir", DEFAULT_OUT_DIR.exists(), str(DEFAULT_OUT_DIR), warn=True)
    add_check(
        "current cross-built dll",
        host["current_dll"] is not None,
        str(host["current_dll"] or "no cross-built Windows DLL found yet"),
        warn=True,
    )
    add_check(
        "current windows wheel",
        host["current_wheel"] is not None,
        str(host["current_wheel"] or "no Windows wheel found yet"),
        warn=True,
    )

    hard_failures = [check for check in checks if check["status"] == "fail"]
    if hard_failures:
        status = "missing-prereqs"
    elif any(check["status"] == "warn" for check in checks):
        status = "ready-with-gaps"
    else:
        status = "ready"

    return {
        "status": status,
        "host": host,
        "checks": checks,
        "next_steps": [
            "Inspect tool discovery: python tools/windows_wheel_workflow.py discover",
            "Build the DLL: python tools/windows_wheel_workflow.py build-dll",
            "Build the wheel: python tools/windows_wheel_workflow.py build-wheel --no-isolation",
            "Run the full lane: python tools/windows_wheel_workflow.py full --no-isolation",
        ],
    }


def print_doctor(payload: dict[str, object]) -> None:
    host = payload["host"]
    print("Windows wheel doctor")
    print(f"status: {payload['status']}")
    print(f"platform: {host['platform']}")
    print(f"arch: {host['arch']}")
    print(f"mingw_prefix: {host['mingw_prefix']}")
    print(f"cmake: {host['cmake'] or 'missing'}")
    print("checks:")
    for check in payload["checks"]:
        print(f"  - {check['name']}: {check['status']} ({check['detail']})")
    print("next:")
    for step in payload["next_steps"]:
        print(f"  - {step}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    discover = subparsers.add_parser("discover", help="List detected MinGW wheel-build tools")
    discover.add_argument("--format", choices=("text", "json"), default="text")
    discover.add_argument("--mingw-prefix", default=DEFAULT_MINGW_PREFIX)

    doctor = subparsers.add_parser("doctor", help="Check the current machine for Windows wheel prerequisites")
    doctor.add_argument("--format", choices=("text", "json"), default="text")
    doctor.add_argument("--mingw-prefix", default=DEFAULT_MINGW_PREFIX)

    build_dll = subparsers.add_parser("build-dll", help="Cross-build fastdis.dll with MinGW-w64")
    build_dll.add_argument("--build-dir", default=str(DEFAULT_BUILD_DIR))
    build_dll.add_argument("--config", default="Release")
    build_dll.add_argument("--mingw-prefix", default=DEFAULT_MINGW_PREFIX)
    build_dll.add_argument("--toolchain-file", default=str(ROOT / "cmake" / "toolchains" / "mingw-w64-x86_64.cmake"))
    build_dll.add_argument("--clean", action="store_true")

    build_wheel = subparsers.add_parser("build-wheel", help="Build a Windows ctypes wheel from the cross-built DLL")
    build_wheel.add_argument("--build-dir", default=str(DEFAULT_BUILD_DIR))
    build_wheel.add_argument("--outdir", default=str(DEFAULT_OUT_DIR))
    build_wheel.add_argument("--plat-name", default="win_amd64")
    build_wheel.add_argument("--python-tag", default="py3")
    build_wheel.add_argument("--abi-tag", default="none")
    build_wheel.add_argument("--no-isolation", action="store_true")

    full = subparsers.add_parser("full", help="Doctor, build the DLL, then build the Windows ctypes wheel")
    full.add_argument("--build-dir", default=str(DEFAULT_BUILD_DIR))
    full.add_argument("--outdir", default=str(DEFAULT_OUT_DIR))
    full.add_argument("--config", default="Release")
    full.add_argument("--mingw-prefix", default=DEFAULT_MINGW_PREFIX)
    full.add_argument("--toolchain-file", default=str(ROOT / "cmake" / "toolchains" / "mingw-w64-x86_64.cmake"))
    full.add_argument("--plat-name", default="win_amd64")
    full.add_argument("--python-tag", default="py3")
    full.add_argument("--abi-tag", default="none")
    full.add_argument("--clean", action="store_true")
    full.add_argument("--no-isolation", action="store_true")

    return parser.parse_args()


def command_discover(args: argparse.Namespace) -> int:
    payload = discover_payload(args.mingw_prefix)
    if args.format == "json":
        print(json.dumps(payload, indent=2))
    else:
        for key, value in payload.items():
            print(f"{key}: {value}")
    return 0 if payload["cmake"] and all(payload["tools"].values()) else 1


def command_doctor(args: argparse.Namespace) -> int:
    payload = doctor_payload(args.mingw_prefix)
    if args.format == "json":
        print(json.dumps(payload, indent=2))
    else:
        print_doctor(payload)
    return 0 if payload["status"] in {"ready", "ready-with-gaps"} else 2


def command_build_dll(args: argparse.Namespace) -> int:
    cmd = [
        sys.executable,
        "tools/build_windows_dll.py",
        "--build-dir",
        args.build_dir,
        "--config",
        args.config,
        "--mingw-prefix",
        args.mingw_prefix,
        "--toolchain-file",
        args.toolchain_file,
    ]
    if args.clean:
        cmd.append("--clean")
    return run_step(cmd)


def command_build_wheel(args: argparse.Namespace) -> int:
    dll = current_windows_dll(Path(args.build_dir))
    if dll is None:
        print(
            "No cross-built Windows DLL was found. Run "
            "`python tools/windows_wheel_workflow.py build-dll` first.",
            file=sys.stderr,
        )
        return 2
    cmd = [
        sys.executable,
        "tools/build_ctypes_wheel.py",
        "--native-lib",
        str(dll),
        "--plat-name",
        args.plat_name,
        "--outdir",
        args.outdir,
        "--python-tag",
        args.python_tag,
        "--abi-tag",
        args.abi_tag,
    ]
    if args.no_isolation:
        cmd.append("--no-isolation")
    return run_step(cmd)


def command_full(args: argparse.Namespace) -> int:
    doctor_args = argparse.Namespace(format="text", mingw_prefix=args.mingw_prefix)
    if command_doctor(doctor_args) == 2:
        return 2
    build_dll_args = argparse.Namespace(
        build_dir=args.build_dir,
        config=args.config,
        mingw_prefix=args.mingw_prefix,
        toolchain_file=args.toolchain_file,
        clean=args.clean,
    )
    build_dll_code = command_build_dll(build_dll_args)
    if build_dll_code != 0:
        return build_dll_code
    build_wheel_args = argparse.Namespace(
        build_dir=args.build_dir,
        outdir=args.outdir,
        plat_name=args.plat_name,
        python_tag=args.python_tag,
        abi_tag=args.abi_tag,
        no_isolation=args.no_isolation,
    )
    return command_build_wheel(build_wheel_args)


def main() -> int:
    load_local_env.load()
    args = parse_args()
    if args.command == "discover":
        return command_discover(args)
    if args.command == "doctor":
        return command_doctor(args)
    if args.command == "build-dll":
        return command_build_dll(args)
    if args.command == "build-wheel":
        return command_build_wheel(args)
    if args.command == "full":
        return command_full(args)
    raise SystemExit(f"Unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
