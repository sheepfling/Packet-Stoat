#!/usr/bin/env python3
"""Operator-facing workflow wrapper for Linux ctypes wheels."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys

from artifacts import CMAKE_LINUX_X86_64, DIST_DIR
import load_local_env


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BUILD_DIR = CMAKE_LINUX_X86_64
DEFAULT_OUT_DIR = DIST_DIR
DEFAULT_TOOLCHAIN = ROOT / "cmake" / "toolchains" / "linux-x86_64-zig.cmake"
DEFAULT_IMAGE = "ubuntu:24.04"


def run_step(cmd: list[str]) -> int:
    print("+", " ".join(cmd))
    completed = subprocess.run(cmd, cwd=ROOT)
    return completed.returncode


def direct_backend_payload(toolchain_file: Path) -> dict[str, object]:
    cmake = shutil.which("cmake")
    zig = shutil.which("zig")
    available = bool(cmake and zig and toolchain_file.is_file())
    return {
        "available": available,
        "status": "ready" if available else "partial",
        "cmake": cmake,
        "zig": zig,
        "toolchain_file": str(toolchain_file),
        "detail": "; ".join(
            [
                f"cmake={'ok' if cmake else 'missing'}",
                f"zig={'ok' if zig else 'missing'}",
                f"toolchain={'ok' if toolchain_file.is_file() else 'missing'}",
            ]
        ),
    }


def docker_backend_payload() -> dict[str, object]:
    docker = shutil.which("docker")
    return {
        "available": docker is not None,
        "status": "ready" if docker is not None else "partial",
        "docker": docker,
        "detail": f"docker={'ok' if docker else 'missing'}",
    }


def current_wheel(out_dir: Path) -> Path | None:
    wheels = sorted(out_dir.glob("fastdis-*-linux_x86_64.whl"), key=lambda path: path.stat().st_mtime)
    return wheels[-1] if wheels else None


def current_linux_shared_library(build_dir: Path) -> Path | None:
    matches = list(build_dir.rglob("libfastdis.so.*")) + list(build_dir.rglob("libfastdis.so"))
    existing = [path for path in matches if path.is_file()]
    if not existing:
        return None
    return max(existing, key=lambda path: path.stat().st_mtime)


def discover_payload(toolchain_file: Path, image: str) -> dict[str, object]:
    direct = direct_backend_payload(toolchain_file)
    docker = docker_backend_payload()
    host = {
        "platform": platform.system(),
        "arch": platform.machine(),
        "python": sys.executable,
        "toolchain_file": str(toolchain_file),
        "docker_image": image,
        "backends": {
            "direct": direct,
            "docker": docker,
        },
        "build_dir": str(DEFAULT_BUILD_DIR),
        "out_dir": str(DEFAULT_OUT_DIR),
        "current_lib": str(current_linux_shared_library(DEFAULT_BUILD_DIR)) if current_linux_shared_library(DEFAULT_BUILD_DIR) else None,
        "current_wheel": str(current_wheel(DEFAULT_OUT_DIR)) if current_wheel(DEFAULT_OUT_DIR) else None,
    }
    return host


def doctor_payload(toolchain_file: Path, image: str) -> dict[str, object]:
    host = discover_payload(toolchain_file, image)
    direct = host["backends"]["direct"]
    docker = host["backends"]["docker"]
    checks: list[dict[str, str]] = []

    def add_check(name: str, ok: bool, detail: str, *, warn: bool = False) -> None:
        checks.append(
            {
                "name": name,
                "status": "warn" if warn and not ok else ("ok" if ok else "fail"),
                "detail": detail,
            }
        )

    add_check(
        "host platform",
        host["platform"] in {"Linux", "Darwin", "Windows"},
        f"{host['platform']} (Linux wheels can be built via direct Zig toolchain or Docker linux/amd64 backend)",
        warn=True,
    )
    add_check("direct backend", bool(direct["available"]), str(direct["detail"]), warn=True)
    add_check("docker backend", bool(docker["available"]), str(docker["detail"]), warn=True)
    add_check(
        "backend policy",
        bool(direct["available"] or docker["available"]),
        "Linux targets keep an explicit workflow: direct Zig toolchain for native/cross builds or Docker linux/amd64 for containerized builds.",
    )
    add_check(
        "current linux shared library",
        host["current_lib"] is not None,
        str(host["current_lib"] or "no Linux shared library found yet"),
        warn=True,
    )
    add_check(
        "current linux wheel",
        host["current_wheel"] is not None,
        str(host["current_wheel"] or "no Linux wheel found yet"),
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
            "Inspect tool discovery: python tools/linux_wheel_workflow.py discover",
            "Check both explicit Linux backends: python tools/linux_wheel_workflow.py doctor",
            "Build the Linux shared library: python tools/linux_wheel_workflow.py build-lib",
            "Build the Linux wheel: python tools/linux_wheel_workflow.py build-wheel --no-isolation",
            "Run the full lane: python tools/linux_wheel_workflow.py full --no-isolation",
        ],
    }


def print_doctor(payload: dict[str, object]) -> None:
    host = payload["host"]
    print("Linux wheel doctor")
    print(f"status: {payload['status']}")
    print(f"platform: {host['platform']}")
    print(f"arch: {host['arch']}")
    print(f"toolchain_file: {host['toolchain_file']}")
    print(f"docker_image: {host['docker_image']}")
    print("checks:")
    for check in payload["checks"]:
        print(f"  - {check['name']}: {check['status']} ({check['detail']})")
    print("next:")
    for step in payload["next_steps"]:
        print(f"  - {step}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    discover = subparsers.add_parser("discover", help="List detected Linux wheel-build backends")
    discover.add_argument("--format", choices=("text", "json"), default="text")
    discover.add_argument("--toolchain-file", default=str(DEFAULT_TOOLCHAIN))
    discover.add_argument("--image", default=DEFAULT_IMAGE)

    doctor = subparsers.add_parser("doctor", help="Check the current machine for Linux wheel prerequisites")
    doctor.add_argument("--format", choices=("text", "json"), default="text")
    doctor.add_argument("--toolchain-file", default=str(DEFAULT_TOOLCHAIN))
    doctor.add_argument("--image", default=DEFAULT_IMAGE)

    build_lib = subparsers.add_parser("build-lib", help="Build libfastdis.so with the direct or Docker backend")
    build_lib.add_argument("--build-dir", default=str(DEFAULT_BUILD_DIR))
    build_lib.add_argument("--config", default="Release")
    build_lib.add_argument("--backend", choices=("auto", "direct", "docker"), default="auto")
    build_lib.add_argument("--toolchain-file", default=str(DEFAULT_TOOLCHAIN))
    build_lib.add_argument("--generator")
    build_lib.add_argument("--image", default=DEFAULT_IMAGE)
    build_lib.add_argument("--clean", action="store_true")
    build_lib.add_argument("--target", default="fastdis_shared")

    build_wheel = subparsers.add_parser("build-wheel", help="Build a Linux ctypes wheel from the built shared library")
    build_wheel.add_argument("--build-dir", default=str(DEFAULT_BUILD_DIR))
    build_wheel.add_argument("--backend", choices=("auto", "direct", "docker"), default="auto")
    build_wheel.add_argument("--toolchain-file", default=str(DEFAULT_TOOLCHAIN))
    build_wheel.add_argument("--image", default=DEFAULT_IMAGE)
    build_wheel.add_argument("--outdir", default=str(DEFAULT_OUT_DIR))
    build_wheel.add_argument("--plat-name", default="linux_x86_64")
    build_wheel.add_argument("--python-tag", default="py3")
    build_wheel.add_argument("--abi-tag", default="none")
    build_wheel.add_argument("--no-isolation", action="store_true")

    full = subparsers.add_parser("full", help="Doctor, build the shared library, then build the Linux ctypes wheel")
    full.add_argument("--build-dir", default=str(DEFAULT_BUILD_DIR))
    full.add_argument("--config", default="Release")
    full.add_argument("--backend", choices=("auto", "direct", "docker"), default="auto")
    full.add_argument("--toolchain-file", default=str(DEFAULT_TOOLCHAIN))
    full.add_argument("--generator")
    full.add_argument("--image", default=DEFAULT_IMAGE)
    full.add_argument("--outdir", default=str(DEFAULT_OUT_DIR))
    full.add_argument("--plat-name", default="linux_x86_64")
    full.add_argument("--python-tag", default="py3")
    full.add_argument("--abi-tag", default="none")
    full.add_argument("--clean", action="store_true")
    full.add_argument("--no-isolation", action="store_true")
    full.add_argument("--target", default="fastdis_shared")

    return parser.parse_args()


def command_discover(args: argparse.Namespace) -> int:
    payload = discover_payload(Path(args.toolchain_file), args.image)
    if args.format == "json":
        print(json.dumps(payload, indent=2))
    else:
        for key, value in payload.items():
            print(f"{key}: {value}")
    backends = payload["backends"]
    return 0 if backends["direct"]["available"] or backends["docker"]["available"] else 1


def command_doctor(args: argparse.Namespace) -> int:
    payload = doctor_payload(Path(args.toolchain_file), args.image)
    if args.format == "json":
        print(json.dumps(payload, indent=2))
    else:
        print_doctor(payload)
    return 0 if payload["status"] in {"ready", "ready-with-gaps"} else 2


def command_build_lib(args: argparse.Namespace) -> int:
    cmd = [
        sys.executable,
        "tools/build_linux_ctypes_wheel.py",
        "--build-dir",
        args.build_dir,
        "--config",
        args.config,
        "--backend",
        args.backend,
        "--toolchain-file",
        args.toolchain_file,
        "--image",
        args.image,
        "--target",
        args.target,
    ]
    if getattr(args, "generator", None):
        cmd.extend(["--generator", args.generator])
    if args.clean:
        cmd.append("--clean")
    return run_step(cmd)


def command_build_wheel(args: argparse.Namespace) -> int:
    backend = args.backend
    if backend == "auto":
        backend = "direct" if direct_backend_payload(Path(args.toolchain_file))["available"] else "docker"
    lib = current_linux_shared_library(Path(args.build_dir))
    if lib is None:
        print(
            "No Linux shared library was found. Run "
            "`python tools/linux_wheel_workflow.py build-lib` first.",
            file=sys.stderr,
        )
        return 2
    cmd = [
        sys.executable,
        "tools/build_ctypes_wheel.py" if backend == "direct" else "tools/build_linux_ctypes_wheel.py",
    ]
    if backend == "direct":
        cmd.extend(
            [
                "--native-lib",
                str(lib),
                "--plat-name",
                args.plat_name,
                "--outdir",
                args.outdir,
                "--python-tag",
                args.python_tag,
                "--abi-tag",
                args.abi_tag,
            ]
        )
        if args.no_isolation:
            cmd.append("--no-isolation")
    else:
        cmd.extend(
            [
                "--build-dir",
                args.build_dir,
                "--backend",
                "docker",
                "--image",
                args.image,
                "--outdir",
                args.outdir,
                "--plat-name",
                args.plat_name,
                "--python-tag",
                args.python_tag,
                "--abi-tag",
                args.abi_tag,
            ]
        )
        if args.no_isolation:
            cmd.append("--no-isolation")
    return run_step(cmd)


def command_full(args: argparse.Namespace) -> int:
    doctor_args = argparse.Namespace(format="text", toolchain_file=args.toolchain_file, image=args.image)
    if command_doctor(doctor_args) == 2:
        return 2
    build_lib_args = argparse.Namespace(
        build_dir=args.build_dir,
        config=args.config,
        backend=args.backend,
        toolchain_file=args.toolchain_file,
        generator=args.generator,
        image=args.image,
        clean=args.clean,
        target=args.target,
    )
    build_lib_code = command_build_lib(build_lib_args)
    if build_lib_code != 0:
        return build_lib_code
    build_wheel_args = argparse.Namespace(
        build_dir=args.build_dir,
        backend=args.backend,
        toolchain_file=args.toolchain_file,
        image=args.image,
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
    if args.command == "build-lib":
        return command_build_lib(args)
    if args.command == "build-wheel":
        return command_build_wheel(args)
    if args.command == "full":
        return command_full(args)
    raise SystemExit(f"Unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
