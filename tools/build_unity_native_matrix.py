#!/usr/bin/env python3
"""Build and stage Unity native plug-in payloads for macOS, Windows, and Linux."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

from artifacts import CMAKE_HOST, CMAKE_LINUX_X86_64, CMAKE_MINGW_WIN64, REPORTS_DIR
import stage_unity_native


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = REPORTS_DIR
DEFAULT_LINUX_IMAGE = "ubuntu:24.04"


def run(cmd: list[str], *, required: bool = True) -> int:
    print("+", " ".join(cmd))
    completed = subprocess.run(cmd, cwd=ROOT, check=False)
    if required and completed.returncode != 0:
        raise SystemExit(completed.returncode)
    return completed.returncode


def tool_status(name: str) -> dict[str, object]:
    path = shutil.which(name)
    return {"tool": name, "path": path, "available": path is not None}


def doctor_payload() -> dict[str, object]:
    tools = {
        "cmake": tool_status("cmake"),
        "docker": tool_status("docker"),
        "mingw_gcc": tool_status("x86_64-w64-mingw32-gcc"),
        "mingw_gxx": tool_status("x86_64-w64-mingw32-g++"),
        "mingw_windres": tool_status("x86_64-w64-mingw32-windres"),
    }
    return {
        "status": "ok" if tools["cmake"]["available"] else "needs-attention",
        "targets": {
            "macos": {"available": tools["cmake"]["available"], "method": "host CMake"},
            "windows": {
                "available": all(tools[name]["available"] for name in ("cmake", "mingw_gcc", "mingw_gxx", "mingw_windres")),
                "method": "MinGW-w64 cross compile",
            },
            "linux": {
                "available": tools["docker"]["available"],
                "method": "Docker linux/amd64 CMake build",
            },
        },
        "tools": tools,
    }


def build_macos(config: str) -> Path:
    build_dir = CMAKE_HOST
    run(
        [
            sys.executable,
            "tools/build_native.py",
            "--build-dir",
            str(build_dir),
            "--config",
            config,
        ]
    )
    lib = build_dir / "libfastdis.dylib"
    if not lib.is_file():
        matches = sorted(build_dir.rglob("libfastdis.dylib"))
        if not matches:
            raise SystemExit("macOS build completed but libfastdis.dylib was not found")
        lib = matches[-1]
    return lib


def build_windows(config: str, mingw_prefix: str) -> Path:
    build_dir = CMAKE_MINGW_WIN64
    run(
        [
            sys.executable,
            "tools/build_windows_dll.py",
            "--build-dir",
            str(build_dir),
            "--config",
            config,
            "--mingw-prefix",
            mingw_prefix,
        ]
    )
    matches = sorted(build_dir.rglob("fastdis.dll")) + sorted(build_dir.rglob("libfastdis.dll"))
    if not matches:
        raise SystemExit("Windows build completed but fastdis.dll was not found")
    return matches[-1]


def build_linux_docker(config: str, image: str) -> Path:
    build_dir = CMAKE_LINUX_X86_64
    script = (
        "set -euo pipefail\n"
        "export DEBIAN_FRONTEND=noninteractive\n"
        "apt-get update\n"
        "apt-get install -y --no-install-recommends cmake g++ make ninja-build ca-certificates\n"
        f"cmake -S /src -B /src/{build_dir.name} "
        "-DFASTDIS_BUILD_SHARED=ON "
        "-DFASTDIS_BUILD_STATIC=OFF "
        "-DFASTDIS_BUILD_TESTS=OFF "
        "-DFASTDIS_BUILD_EXAMPLES=OFF "
        "-DFASTDIS_BUILD_BENCHMARKS=OFF "
        f"-DCMAKE_BUILD_TYPE={config}\n"
        f"cmake --build /src/{build_dir.name} --config {config} --target fastdis_shared\n"
    )
    run(
        [
            "docker",
            "run",
            "--rm",
            "--platform",
            "linux/amd64",
            "-v",
            f"{ROOT}:/src",
            "-w",
            "/src",
            image,
            "bash",
            "-lc",
            script,
        ]
    )
    lib = build_dir / "libfastdis.so"
    if not lib.is_file():
        matches = sorted(build_dir.rglob("libfastdis.so"))
        if not matches:
            raise SystemExit("Linux Docker build completed but libfastdis.so was not found")
        lib = matches[-1]
    return lib


def stage_targets(targets: list[str], out_dir: Path) -> list[dict[str, object]]:
    reports: list[dict[str, object]] = []
    for target in targets:
        native_build = {
            "macos": CMAKE_HOST,
            "windows": CMAKE_MINGW_WIN64,
            "linux": CMAKE_LINUX_X86_64,
        }[target]
        reports.append(stage_unity_native.stage(target, stage_unity_native.DEFAULT_PACKAGE, native_build, out_dir))
    return reports


def build_targets(args: argparse.Namespace) -> dict[str, object]:
    results: dict[str, object] = {"status": "pass", "targets": {}}
    built: list[str] = []
    for target in args.targets:
        try:
            if target == "macos":
                artifact = build_macos(args.config)
            elif target == "windows":
                artifact = build_windows(args.config, args.mingw_prefix)
            elif target == "linux":
                artifact = build_linux_docker(args.config, args.linux_image)
            else:
                raise ValueError(f"unknown target: {target}")
        except SystemExit as exc:
            results["status"] = "fail"
            results["targets"][target] = {"status": "fail", "code": exc.code}
            if not args.keep_going:
                raise
            continue
        built.append(target)
        results["targets"][target] = {"status": "pass", "artifact": str(artifact)}
    if built:
        results["staged"] = stage_targets(built, Path(args.out_dir))
    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor = subparsers.add_parser("doctor", help="Show local cross-build readiness")
    doctor.add_argument("--format", choices=("text", "json"), default="text")

    build = subparsers.add_parser("build", help="Build and stage selected Unity native targets")
    build.add_argument("--targets", nargs="+", choices=("macos", "windows", "linux"), default=["macos", "windows", "linux"])
    build.add_argument("--config", default="Release")
    build.add_argument("--mingw-prefix", default="x86_64-w64-mingw32")
    build.add_argument("--linux-image", default=DEFAULT_LINUX_IMAGE)
    build.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    build.add_argument("--keep-going", action="store_true", help="Continue building other targets after a target failure")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.command == "doctor":
        payload = doctor_payload()
        if args.format == "json":
            print(json.dumps(payload, indent=2))
        else:
            print("Unity native matrix doctor")
            print(f"status: {payload['status']}")
            for name, target in payload["targets"].items():
                print(f"{name}: {'ok' if target['available'] else 'missing'} ({target['method']})")
            print("tools:")
            for tool in payload["tools"].values():
                print(f"  - {tool['tool']}: {tool['path'] or 'missing'}")
        return 0 if payload["status"] == "ok" else 2
    if args.command == "build":
        results = build_targets(args)
        print(json.dumps(results, indent=2))
        return 0 if results["status"] == "pass" else 1
    raise SystemExit(f"Unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
