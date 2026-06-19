#!/usr/bin/env python3
"""Configure and run sanitizer-backed fastdis native tests."""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd), file=sys.stderr)
    subprocess.run(cmd, cwd=ROOT, check=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-dir", default="build-sanitizers")
    parser.add_argument("--config", default="Debug")
    parser.add_argument("--sanitizers", default="asan,ubsan")
    args = parser.parse_args(argv)

    requested = {item.strip().lower() for item in args.sanitizers.split(",") if item.strip()}
    if not requested:
        parser.error("at least one sanitizer must be selected")

    if shutil.which("cmake") is None:
        print("cmake was not found on PATH", file=sys.stderr)
        return 2

    build_dir = ROOT / args.build_dir
    cmake_cmd = [
        "cmake",
        "-S",
        str(ROOT),
        "-B",
        str(build_dir),
        f"-DCMAKE_BUILD_TYPE={args.config}",
        "-DFASTDIS_BUILD_SHARED=ON",
        "-DFASTDIS_BUILD_TESTS=ON",
        "-DFASTDIS_BUILD_EXAMPLES=OFF",
        "-DFASTDIS_BUILD_BENCHMARKS=OFF",
        "-DFASTDIS_BUILD_FUZZERS=ON",
        f"-DFASTDIS_ENABLE_ASAN={'ON' if 'asan' in requested else 'OFF'}",
        f"-DFASTDIS_ENABLE_UBSAN={'ON' if 'ubsan' in requested else 'OFF'}",
        f"-DFASTDIS_ENABLE_TSAN={'ON' if 'tsan' in requested else 'OFF'}",
    ]
    run(cmake_cmd)
    run(["cmake", "--build", str(build_dir), "--config", args.config])
    run(["ctest", "--test-dir", str(build_dir), "--build-config", args.config, "--output-on-failure"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
