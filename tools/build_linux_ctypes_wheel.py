#!/usr/bin/env python3
"""Build a Linux ctypes wheel via a direct toolchain or Docker backend."""

from __future__ import annotations

import argparse
from pathlib import Path
import shlex
import shutil
import subprocess
import sys

from artifacts import CMAKE_LINUX_X86_64, DIST_DIR
from linux_native_build import (
    DEFAULT_IMAGE,
    DEFAULT_TOOLCHAIN,
    ROOT,
    build_direct,
    build_docker,
    resolve_backend,
)
import load_local_env


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-dir", default=str(CMAKE_LINUX_X86_64))
    parser.add_argument("--config", default="Release")
    parser.add_argument("--backend", choices=("auto", "direct", "docker"), default="auto")
    parser.add_argument("--toolchain-file", default=str(DEFAULT_TOOLCHAIN))
    parser.add_argument("--generator", help="Optional explicit CMake generator for the direct backend")
    parser.add_argument("--image", default=DEFAULT_IMAGE)
    parser.add_argument("--outdir", default=str(DIST_DIR))
    parser.add_argument("--plat-name", default="linux_x86_64")
    parser.add_argument("--python-tag", default="py3")
    parser.add_argument("--abi-tag", default="none")
    parser.add_argument("--clean", action="store_true")
    parser.add_argument("--no-isolation", action="store_true")
    parser.add_argument("--target", default="fastdis_shared")
    return parser.parse_args()


def run(cmd: list[str], *, env: dict[str, str] | None = None) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, cwd=ROOT, check=True, env=env)


def package_on_host(
    *,
    native_lib: Path,
    outdir: str,
    plat_name: str,
    python_tag: str,
    abi_tag: str,
    no_isolation: bool,
) -> None:
    cmd = [
        sys.executable,
        "tools/build_ctypes_wheel.py",
        "--native-lib",
        str(native_lib),
        "--plat-name",
        plat_name,
        "--outdir",
        outdir,
        "--python-tag",
        python_tag,
        "--abi-tag",
        abi_tag,
    ]
    if no_isolation:
        cmd.append("--no-isolation")
    run(cmd)


def package_in_docker(
    *,
    native_lib: Path,
    image: str,
    outdir: Path,
    plat_name: str,
    python_tag: str,
    abi_tag: str,
    no_isolation: bool,
) -> None:
    if shutil.which("docker") is None:
        raise SystemExit("Linux Docker backend is not ready: docker is missing")
    outdir.mkdir(parents=True, exist_ok=True)
    container_native = f"/src/{native_lib.relative_to(ROOT).as_posix()}"
    container_outdir = f"/src/{outdir.relative_to(ROOT).as_posix()}"
    no_isolation_flag = " --no-isolation" if no_isolation else ""
    script = (
        "set -euo pipefail\n"
        "export DEBIAN_FRONTEND=noninteractive\n"
        "apt-get update\n"
        "apt-get install -y --no-install-recommends python3 python3-pip python3-venv ca-certificates\n"
        "python3 -m pip install --upgrade pip build wheel setuptools\n"
        f"python3 tools/build_ctypes_wheel.py --native-lib {shlex.quote(container_native)} "
        f"--plat-name {shlex.quote(plat_name)} "
        f"--outdir {shlex.quote(container_outdir)} "
        f"--python-tag {shlex.quote(python_tag)} "
        f"--abi-tag {shlex.quote(abi_tag)}{no_isolation_flag}\n"
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


def main() -> int:
    load_local_env.load()
    args = parse_args()
    build_dir = (ROOT / args.build_dir).resolve()
    toolchain_file = Path(args.toolchain_file).resolve()
    backend = resolve_backend(args.backend, toolchain_file)

    if backend == "direct":
        native_lib = build_direct(
            build_dir=build_dir,
            config=args.config,
            toolchain_file=toolchain_file,
            generator=args.generator,
            clean=args.clean,
            target=args.target,
            root=ROOT,
        )
        package_on_host(
            native_lib=native_lib,
            outdir=args.outdir,
            plat_name=args.plat_name,
            python_tag=args.python_tag,
            abi_tag=args.abi_tag,
            no_isolation=args.no_isolation,
        )
        return 0

    native_lib = build_docker(
        build_dir=build_dir,
        config=args.config,
        image=args.image,
        clean=args.clean,
        target=args.target,
        root=ROOT,
        install_packages="build-essential cmake ninja-build python3 python3-pip ca-certificates",
    )
    package_in_docker(
        native_lib=native_lib,
        image=args.image,
        outdir=(ROOT / args.outdir).resolve(),
        plat_name=args.plat_name,
        python_tag=args.python_tag,
        abi_tag=args.abi_tag,
        no_isolation=args.no_isolation,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
