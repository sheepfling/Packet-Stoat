#!/usr/bin/env python3
"""Build the fastdis shared library with CMake.

This is intentionally small and dependency-free; it is a convenience wrapper
around CMake for local development. Packaging wheels can later use cibuildwheel
or scikit-build-core once the native layer is ready to distribute broadly.
"""

from __future__ import annotations

import argparse
import pathlib
import platform
import re
import shutil
import subprocess
import sys

from artifacts import CMAKE_HOST


ROOT = pathlib.Path(__file__).resolve().parents[1]


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, cwd=ROOT, check=True)


def default_generator() -> str | None:
    if platform.system().lower() != "windows":
        return None
    if shutil.which("ninja"):
        return "Ninja"
    if shutil.which("mingw32-make") or shutil.which("make"):
        return "MinGW Makefiles"
    return None


def _latest_shared_library(build_dir: pathlib.Path) -> pathlib.Path | None:
    names = ["fastdis.dll", "libfastdis.so", "libfastdis.dylib"]
    candidates: list[pathlib.Path] = []
    for name in names:
        candidates.extend(build_dir.rglob(name))
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def _stage_default_library(build_dir: pathlib.Path) -> pathlib.Path | None:
    lib = _latest_shared_library(build_dir)
    if lib is None:
        return None
    root_build = ROOT / "build"
    root_build.mkdir(parents=True, exist_ok=True)
    dest = root_build / lib.name
    print(f"stage {lib} -> {dest}")
    shutil.copy2(lib.resolve(), dest)
    return dest


def _cached_generator(build_dir: pathlib.Path) -> str | None:
    cache = build_dir / "CMakeCache.txt"
    if not cache.is_file():
        return None
    text = cache.read_text(encoding="utf-8", errors="ignore")
    match = re.search(r"^CMAKE_GENERATOR:INTERNAL=(.+)$", text, re.MULTILINE)
    if not match:
        return None
    return match.group(1).strip() or None


def _clear_if_incompatible_generator(build_dir: pathlib.Path, generator: str | None) -> None:
    if generator is None or not build_dir.exists():
        return
    cached = _cached_generator(build_dir)
    if cached is None or cached == generator:
        return
    shutil.rmtree(build_dir)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--build-dir", default=str(CMAKE_HOST), help="CMake build directory")
    parser.add_argument("--config", default="Release", help="CMake configuration")
    parser.add_argument("--generator", help="Optional explicit CMake generator")
    parser.add_argument("--build-examples", action="store_true", help="Build native example executables")
    parser.add_argument("--build-benchmarks", action="store_true", help="Build native benchmark executables")
    parser.add_argument("--copy-to-package", action="store_true", help="copy built shared library into src/fastdis")
    args = parser.parse_args()

    if shutil.which("cmake") is None:
        print("cmake was not found on PATH", file=sys.stderr)
        return 2

    build_dir = ROOT / args.build_dir
    generator = args.generator or default_generator()
    _clear_if_incompatible_generator(build_dir, generator)
    cmake_args = [
        "cmake",
        "-S",
        str(ROOT),
        "-B",
        str(build_dir),
        "-DFASTDIS_BUILD_SHARED=ON",
        "-DFASTDIS_BUILD_TESTS=ON",
        f"-DFASTDIS_BUILD_EXAMPLES={'ON' if args.build_examples else 'OFF'}",
        f"-DFASTDIS_BUILD_BENCHMARKS={'ON' if args.build_benchmarks else 'OFF'}",
        f"-DCMAKE_BUILD_TYPE={args.config}",
    ]
    if generator:
        cmake_args[1:1] = ["-G", generator]
    run(cmake_args)
    run(["cmake", "--build", str(build_dir), "--config", args.config])
    _stage_default_library(build_dir)

    if args.copy_to_package:
        lib = _latest_shared_library(build_dir)
        if lib is None:
            print("could not find built shared library", file=sys.stderr)
            return 3
        dest = ROOT / "src" / "fastdis" / lib.name
        print(f"copy {lib} -> {dest}")
        shutil.copy2(lib, dest)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
