#!/usr/bin/env python3
"""Shared Linux native build helpers for direct and Docker backends."""

from __future__ import annotations

import os
from pathlib import Path
import platform
import shlex
import shutil
import subprocess
from typing import Callable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_IMAGE = "ubuntu:24.04"
DEFAULT_TOOLCHAIN = ROOT / "cmake" / "toolchains" / "linux-x86_64-zig.cmake"


def run(cmd: list[str], *, cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    print("+", " ".join(cmd))
    return subprocess.run(cmd, cwd=cwd or ROOT, check=check, text=True)


def direct_backend_probe(toolchain_file: Path) -> dict[str, object]:
    cmake = shutil.which("cmake")
    zig = shutil.which("zig")
    available = bool(cmake and zig and toolchain_file.is_file())
    detail_parts: list[str] = [
        f"cmake={'ok' if cmake else 'missing'}",
        f"zig={'ok' if zig else 'missing'}",
        f"toolchain={'ok' if toolchain_file.is_file() else 'missing'}",
    ]
    return {
        "status": "ready" if available else "partial",
        "available": available,
        "detail": "; ".join(detail_parts),
        "toolchain_file": str(toolchain_file),
        "cmake": cmake or "",
        "zig": zig or "",
    }


def docker_backend_probe() -> dict[str, object]:
    docker = shutil.which("docker")
    return {
        "status": "ready" if docker else "partial",
        "available": docker is not None,
        "docker": docker or "",
        "detail": f"docker={'ok' if docker else 'missing'}",
    }


def resolve_backend(requested: str, toolchain_file: Path) -> str:
    if requested in {"direct", "docker"}:
        return requested
    probe = direct_backend_probe(toolchain_file)
    return "direct" if probe["available"] else "docker"


def path_is_file(path: Path) -> bool:
    try:
        return path.is_file()
    except OSError:
        return False


def latest_linux_shared_library(build_dir: Path) -> Path | None:
    preferred = sorted(
        [path for path in build_dir.rglob("libfastdis.so.*") if path_is_file(path)],
        key=lambda path: path.stat().st_mtime,
    )
    if preferred:
        return preferred[-1]
    direct = sorted(
        [path for path in build_dir.rglob("libfastdis.so") if path_is_file(path)],
        key=lambda path: path.stat().st_mtime,
    )
    if direct:
        return direct[-1]
    return None


def remove_if_present(path: Path) -> None:
    if not os.path.lexists(path):
        return
    try:
        path.unlink()
    except FileNotFoundError:
        return


def clear_if_incompatible_cmake_cache(build_dir: Path, expected_source_dir: str, expected_build_dir: str) -> None:
    cache = build_dir / "CMakeCache.txt"
    if not cache.is_file():
        return
    text = cache.read_text(encoding="utf-8", errors="ignore").replace("\\", "/")
    source_dir = expected_source_dir.replace("\\", "/")
    build_dir_text = expected_build_dir.replace("\\", "/")
    if source_dir in text and build_dir_text in text:
        return
    shutil.rmtree(build_dir)


def materialize_linux_alias(build_dir: Path) -> Path:
    lib = latest_linux_shared_library(build_dir)
    if lib is None:
        raise SystemExit("Linux build completed but libfastdis.so was not found")
    alias = build_dir / "libfastdis.so"
    if alias != lib or not path_is_file(alias):
        remove_if_present(alias)
        shutil.copy2(lib, alias)
    return alias


def build_direct(
    *,
    build_dir: Path,
    config: str,
    toolchain_file: Path,
    generator: str | None,
    clean: bool,
    target: str,
    root: Path | None = None,
    extra_cmake_args: list[str] | None = None,
    run_fn: Callable[[list[str]], object] | None = None,
    probe_fn: Callable[[Path], dict[str, object]] | None = None,
    clear_cache_fn: Callable[[Path, str, str], None] | None = None,
    materialize_alias_fn: Callable[[Path], Path] | None = None,
) -> Path:
    root = root or ROOT
    run_fn = run_fn or (lambda cmd: run(cmd, cwd=root))
    probe_fn = probe_fn or direct_backend_probe
    clear_cache_fn = clear_cache_fn or clear_if_incompatible_cmake_cache
    materialize_alias_fn = materialize_alias_fn or materialize_linux_alias
    probe = probe_fn(toolchain_file)
    if not probe["available"]:
        raise SystemExit(f"Linux direct toolchain is not ready: {probe['detail']}")
    if clean and build_dir.exists():
        shutil.rmtree(build_dir)
    clear_cache_fn(build_dir, str(root), str(build_dir))

    cmake_args = ["cmake"]
    chosen_generator = generator
    if chosen_generator is None and platform.system().lower() == "windows" and shutil.which("ninja"):
        chosen_generator = "Ninja"
    if chosen_generator:
        cmake_args.extend(["-G", chosen_generator])
    cmake_args.extend(
        [
            "-S",
            str(root),
            "-B",
            str(build_dir),
            f"-DCMAKE_TOOLCHAIN_FILE={toolchain_file.resolve()}",
            "-DFASTDIS_BUILD_SHARED=ON",
            "-DFASTDIS_BUILD_STATIC=OFF",
            "-DFASTDIS_BUILD_TESTS=OFF",
            "-DFASTDIS_BUILD_EXAMPLES=OFF",
            "-DFASTDIS_BUILD_BENCHMARKS=OFF",
            f"-DCMAKE_BUILD_TYPE={config}",
        ]
    )
    if extra_cmake_args:
        cmake_args.extend(extra_cmake_args)
    run_fn(cmake_args)
    run_fn(["cmake", "--build", str(build_dir), "--config", config, "--target", target])
    return materialize_alias_fn(build_dir)


def build_docker(
    *,
    build_dir: Path,
    config: str,
    image: str,
    clean: bool,
    target: str,
    root: Path | None = None,
    install_packages: str = "cmake g++ make ninja-build ca-certificates",
    extra_cmake_args: list[str] | None = None,
    run_fn: Callable[[list[str]], object] | None = None,
    clear_cache_fn: Callable[[Path, str, str], None] | None = None,
    materialize_alias_fn: Callable[[Path], Path] | None = None,
) -> Path:
    root = root or ROOT
    run_fn = run_fn or (lambda cmd: run(cmd, cwd=root))
    clear_cache_fn = clear_cache_fn or clear_if_incompatible_cmake_cache
    materialize_alias_fn = materialize_alias_fn or materialize_linux_alias
    if shutil.which("docker") is None:
        raise SystemExit("Linux Docker backend is not ready: docker is missing")
    if clean and build_dir.exists():
        shutil.rmtree(build_dir)

    container_build_dir = build_dir.relative_to(root)
    container_build_dir_quoted = shlex.quote(f"/src/{container_build_dir.as_posix()}")
    clear_cache_fn(build_dir, "/src", f"/src/{container_build_dir.as_posix()}")
    cmake_extra = ""
    if extra_cmake_args:
        cmake_extra = " " + " ".join(shlex.quote(arg) for arg in extra_cmake_args)
    script = (
        "set -euo pipefail\n"
        "export DEBIAN_FRONTEND=noninteractive\n"
        "apt-get update\n"
        f"apt-get install -y --no-install-recommends {install_packages}\n"
        f"cmake -S /src -B {container_build_dir_quoted} "
        "-DFASTDIS_BUILD_SHARED=ON "
        "-DFASTDIS_BUILD_STATIC=OFF "
        "-DFASTDIS_BUILD_TESTS=OFF "
        "-DFASTDIS_BUILD_EXAMPLES=OFF "
        "-DFASTDIS_BUILD_BENCHMARKS=OFF "
        f"-DCMAKE_BUILD_TYPE={config}{cmake_extra}\n"
        f"cmake --build {container_build_dir_quoted} --config {config} --target {shlex.quote(target)}\n"
    )
    run_fn(
        [
            "docker",
            "run",
            "--rm",
            "--platform",
            "linux/amd64",
            "-v",
            f"{root}:/src",
            "-w",
            "/src",
            image,
            "bash",
            "-lc",
            script,
        ]
    )
    return materialize_alias_fn(build_dir)
