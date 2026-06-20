#!/usr/bin/env python3
"""Cross-build fastdis.dll with MinGW-w64 from macOS or Linux."""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TOOLCHAIN = ROOT / "cmake" / "toolchains" / "mingw-w64-x86_64.cmake"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-dir", default="build-mingw-win64")
    parser.add_argument("--config", default="Release")
    parser.add_argument("--mingw-prefix", default="x86_64-w64-mingw32")
    parser.add_argument("--toolchain-file", default=str(DEFAULT_TOOLCHAIN))
    parser.add_argument("--clean", action="store_true")
    parser.add_argument("--build-examples", action="store_true")
    parser.add_argument("--build-benchmarks", action="store_true")
    parser.add_argument(
        "--target",
        default="fastdis_shared",
        help="CMake target to build. Default builds only the shared library needed for wheel packaging.",
    )
    return parser.parse_args()


def require_tool(name: str) -> None:
    if shutil.which(name) is None:
        raise SystemExit(f"required tool not found on PATH: {name}")


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, cwd=ROOT, check=True)


def expected_tool_names(prefix: str) -> tuple[str, str, str]:
    return (f"{prefix}-gcc", f"{prefix}-g++", f"{prefix}-windres")


def find_windows_dll(build_dir: Path) -> Path:
    matches = list(build_dir.rglob("fastdis.dll")) + list(build_dir.rglob("libfastdis.dll"))
    if not matches:
        raise SystemExit(f"could not find fastdis.dll or libfastdis.dll under {build_dir}")
    return max(matches, key=lambda path: path.stat().st_mtime)


def main() -> int:
    args = parse_args()
    require_tool("cmake")
    for tool in expected_tool_names(args.mingw_prefix):
        require_tool(tool)

    build_dir = (ROOT / args.build_dir).resolve()
    if args.clean and build_dir.exists():
        shutil.rmtree(build_dir)

    cmake_args = [
        "cmake",
        "-S",
        str(ROOT),
        "-B",
        str(build_dir),
        f"-DCMAKE_TOOLCHAIN_FILE={Path(args.toolchain_file).resolve()}",
        f"-DFASTDIS_MINGW_PREFIX={args.mingw_prefix}",
        "-DFASTDIS_BUILD_SHARED=ON",
        "-DFASTDIS_BUILD_STATIC=OFF",
        "-DFASTDIS_BUILD_TESTS=OFF",
        f"-DFASTDIS_BUILD_EXAMPLES={'ON' if args.build_examples else 'OFF'}",
        f"-DFASTDIS_BUILD_BENCHMARKS={'ON' if args.build_benchmarks else 'OFF'}",
        f"-DCMAKE_BUILD_TYPE={args.config}",
    ]
    run(cmake_args)
    run(["cmake", "--build", str(build_dir), "--config", args.config, "--target", args.target])
    dll = find_windows_dll(build_dir)
    print(dll)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
