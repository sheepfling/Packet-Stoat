#!/usr/bin/env python3
"""Build and run the fastdis native + ctypes benchmark suite."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import json

ROOT = Path(__file__).resolve().parents[1]


def run(cmd: list[str], *, env: dict[str, str] | None = None, stdout=None) -> None:
    print("+", " ".join(cmd), file=sys.stderr)
    subprocess.run(cmd, cwd=ROOT, check=True, env=env, stdout=stdout)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def native_exe(build_dir: Path) -> Path:
    name = "fastdis_native_bench.exe" if platform.system().lower() == "windows" else "fastdis_native_bench"
    candidates = list(build_dir.rglob(name))
    if not candidates:
        raise FileNotFoundError(f"could not find {name} under {build_dir}")
    return max(candidates, key=lambda p: p.stat().st_mtime)


def native_lib(build_dir: Path) -> Path:
    names = ["fastdis.dll"] if platform.system().lower() == "windows" else ["libfastdis.dylib", "libfastdis.so"]
    candidates: list[Path] = []
    for name in names:
        candidates.extend(build_dir.rglob(name))
    if not candidates:
        raise FileNotFoundError(f"could not find built fastdis shared library under {build_dir}")
    return max(candidates, key=lambda p: p.stat().st_mtime)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-dir", default="build", help="CMake build directory")
    parser.add_argument("--config", default="Release", help="CMake build configuration")
    parser.add_argument("--native-packets", type=int, default=1_000_000)
    parser.add_argument("--native-rounds", type=int, default=5)
    parser.add_argument("--packet-file", type=Path, help="optional .fastdispkt replay file for the native benchmark")
    parser.add_argument("--ctypes-packets", type=int, default=50_000)
    parser.add_argument("--ctypes-repeats", type=int, default=5)
    parser.add_argument("--format", choices=("table", "csv", "json"), default="table")
    parser.add_argument("--out-dir", type=Path, help="write native/ctypes outputs to files in this directory")
    parser.add_argument("--skip-ctypes", action="store_true")
    args = parser.parse_args(argv)

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
        "-DFASTDIS_BUILD_BENCHMARKS=ON",
        "-DCMAKE_BUILD_TYPE=Release",
    ])
    run(["cmake", "--build", str(build_dir), "--config", args.config])

    out_dir = args.out_dir
    if out_dir:
        out_dir.mkdir(parents=True, exist_ok=True)

    native_out: Path | None = None
    ctypes_out: Path | None = None
    native_cmd = [
        str(native_exe(build_dir)),
        "--packets",
        str(args.native_packets),
        "--rounds",
        str(args.native_rounds),
        "--format",
        args.format,
    ]
    if args.packet_file:
        native_cmd.extend(["--packet-file", str(args.packet_file)])
    if out_dir:
        native_out = out_dir / f"native.{args.format if args.format != 'table' else 'txt'}"
        with native_out.open("w") as fh:
            run(native_cmd, stdout=fh)
        print(f"native benchmark output: {native_out}")
    else:
        run(native_cmd)

    if not args.skip_ctypes:
        env = os.environ.copy()
        env["FASTDIS_LIBRARY"] = str(native_lib(build_dir))
        env["PYTHONPATH"] = str(ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
        ctypes_cmd = [
            sys.executable,
            "benchmarks/bench_ctypes.py",
            "--packets",
            str(args.ctypes_packets),
            "--repeats",
            str(args.ctypes_repeats),
            "--format",
            args.format,
        ]
        if out_dir:
            ctypes_out = out_dir / f"ctypes.{args.format if args.format != 'table' else 'txt'}"
            with ctypes_out.open("w") as fh:
                run(ctypes_cmd, env=env, stdout=fh)
            print(f"ctypes benchmark output: {ctypes_out}")
        else:
            run(ctypes_cmd, env=env)
    if out_dir and args.format == "json":
        summary_md = out_dir / "summary.md"
        combined_json = out_dir / "current.json"
        summary_cmd = [
            sys.executable,
            "tools/summarize_benchmarks.py",
            "--native",
            str(native_out),
            "--out",
            str(summary_md),
        ]
        if not args.skip_ctypes:
            summary_cmd.extend(["--ctypes", str(ctypes_out)])
        run(summary_cmd)
        payload = {
            "native": load_json(native_out),
            "ctypes": None if args.skip_ctypes else load_json(ctypes_out),
        }
        combined_json.write_text(json.dumps(payload, indent=2) + "\n")
        print(f"benchmark summary: {summary_md}")
        print(f"combined benchmark payload: {combined_json}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
