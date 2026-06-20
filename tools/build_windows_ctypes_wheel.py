#!/usr/bin/env python3
"""Cross-build fastdis.dll with MinGW-w64 and package a Windows ctypes wheel."""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import packaging_helpers


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-dir", default="build-mingw-win64")
    parser.add_argument("--config", default="Release")
    parser.add_argument("--mingw-prefix", default="x86_64-w64-mingw32")
    parser.add_argument("--toolchain-file", default=str(ROOT / "cmake" / "toolchains" / "mingw-w64-x86_64.cmake"))
    parser.add_argument("--outdir", default="dist")
    parser.add_argument("--plat-name", default="win_amd64")
    parser.add_argument("--python-tag", default="py3")
    parser.add_argument("--abi-tag", default="none")
    parser.add_argument("--clean", action="store_true")
    parser.add_argument("--no-isolation", action="store_true")
    parser.add_argument("--build-examples", action="store_true")
    parser.add_argument("--build-benchmarks", action="store_true")
    parser.add_argument("--target", default="fastdis_shared")
    return parser.parse_args()


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, cwd=ROOT, check=True)


def find_windows_dll(build_dir: Path) -> Path:
    matches = list(build_dir.rglob("fastdis.dll")) + list(build_dir.rglob("libfastdis.dll"))
    if not matches:
        raise SystemExit(f"could not find fastdis.dll or libfastdis.dll under {build_dir}")
    return max(matches, key=lambda path: path.stat().st_mtime)


def main() -> int:
    args = parse_args()
    build_cmd = [
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
        "--target",
        args.target,
    ]
    if args.clean:
        build_cmd.append("--clean")
    if args.build_examples:
        build_cmd.append("--build-examples")
    if args.build_benchmarks:
        build_cmd.append("--build-benchmarks")
    run(build_cmd)

    dll = find_windows_dll((ROOT / args.build_dir).resolve())
    packaging_helpers.validate_wheel_env
    wheel_cmd = [
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
        wheel_cmd.append("--no-isolation")
    run(wheel_cmd)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
