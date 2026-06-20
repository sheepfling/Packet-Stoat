#!/usr/bin/env python3
"""Build a platform wheel that bundles a prebuilt ctypes native library."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import packaging_helpers


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--native-lib",
        required=True,
        help="Prebuilt native library to bundle, for example fastdis.dll",
    )
    parser.add_argument(
        "--plat-name",
        required=True,
        help="Wheel platform tag, for example win_amd64 or manylinux_2_28_x86_64",
    )
    parser.add_argument(
        "--outdir",
        default="dist",
        help="Build output directory",
    )
    parser.add_argument(
        "--python-tag",
        default="py3",
        help="Wheel python tag to emit for bundled-ctypes wheels",
    )
    parser.add_argument(
        "--abi-tag",
        default="none",
        help="Wheel ABI tag to emit for bundled-ctypes wheels",
    )
    parser.add_argument(
        "--no-isolation",
        action="store_true",
        help="Pass --no-isolation through to python -m build",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    native_lib = Path(args.native_lib).expanduser().resolve()
    if not native_lib.is_file():
        print(f"native library does not exist: {native_lib}", file=sys.stderr)
        return 2

    env = os.environ.copy()
    env["FASTDIS_WHEEL_NATIVE_LIB"] = str(native_lib)
    env["FASTDIS_WHEEL_PLAT_NAME"] = args.plat_name
    env["FASTDIS_WHEEL_PYTHON_TAG"] = args.python_tag
    env["FASTDIS_WHEEL_ABI_TAG"] = args.abi_tag
    env["FASTDIS_SKIP_CFAST"] = "1"
    packaging_helpers.validate_wheel_env()

    cmd = [sys.executable, "-m", "build", "--wheel", "--outdir", args.outdir]
    if args.no_isolation:
        cmd.append("--no-isolation")
    print("+", " ".join(cmd))
    subprocess.run(cmd, cwd=ROOT, check=True, env=env)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
