#!/usr/bin/env python3
"""Build the fastdis shared library with CMake.

This is intentionally small and dependency-free; it is a convenience wrapper
around CMake for local development. Packaging wheels can later use cibuildwheel
or scikit-build-core once the native layer is ready to distribute broadly.
"""

from __future__ import annotations

import argparse
import os
import pathlib
import shutil
import subprocess
import sys

from artifacts import CMAKE_HOST


ROOT = pathlib.Path(__file__).resolve().parents[1]


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, cwd=ROOT, check=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--build-dir", default=str(CMAKE_HOST), help="CMake build directory")
    parser.add_argument("--config", default="Release", help="CMake configuration")
    parser.add_argument("--copy-to-package", action="store_true", help="copy built shared library into src/fastdis")
    args = parser.parse_args()

    if shutil.which("cmake") is None:
        print("cmake was not found on PATH", file=sys.stderr)
        return 2

    build_dir = ROOT / args.build_dir
    run([
        "cmake",
        "-S",
        str(ROOT),
        "-B",
        str(build_dir),
        "-DFASTDIS_BUILD_SHARED=ON",
        f"-DCMAKE_BUILD_TYPE={args.config}",
    ])
    run(["cmake", "--build", str(build_dir), "--config", args.config])

    if args.copy_to_package:
        names = ["fastdis.dll", "libfastdis.so", "libfastdis.dylib"]
        candidates: list[pathlib.Path] = []
        for name in names:
            candidates.extend(build_dir.rglob(name))
        if not candidates:
            print("could not find built shared library", file=sys.stderr)
            return 3
        lib = max(candidates, key=lambda p: p.stat().st_mtime)
        dest = ROOT / "src" / "fastdis" / lib.name
        print(f"copy {lib} -> {dest}")
        shutil.copy2(lib, dest)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
