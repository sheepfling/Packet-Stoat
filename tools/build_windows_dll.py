#!/usr/bin/env python3
"""Cross-build fastdis.dll with MinGW-w64 from macOS or Linux."""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import platform
import subprocess

from artifacts import CMAKE_MINGW_WIN64


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TOOLCHAIN = ROOT / "cmake" / "toolchains" / "mingw-w64-x86_64.cmake"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-dir", default=str(CMAKE_MINGW_WIN64))
    parser.add_argument("--config", default="Release")
    parser.add_argument("--mingw-prefix", default="x86_64-w64-mingw32")
    parser.add_argument(
        "--generator",
        help="Explicit CMake generator. Defaults to MinGW Makefiles on Windows and the native default elsewhere.",
    )
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


def expected_tool_names(prefix: str) -> tuple[str, str]:
    return (f"{prefix}-gcc", f"{prefix}-g++")


def resolve_rc_tool(prefix: str) -> str | None:
    return shutil.which(f"{prefix}-windres") or shutil.which("windres")


def find_windows_dll(build_dir: Path) -> Path:
    matches = list(build_dir.rglob("fastdis.dll")) + list(build_dir.rglob("libfastdis.dll"))
    if not matches:
        raise SystemExit(f"could not find fastdis.dll or libfastdis.dll under {build_dir}")
    return max(matches, key=lambda path: path.stat().st_mtime)


def mingw_runtime_dlls(prefix: str) -> list[Path]:
    compiler = shutil.which(f"{prefix}-g++")
    if compiler is None:
        return []
    bin_dir = Path(compiler).resolve().parent
    names = ("libgcc_s_seh-1.dll", "libstdc++-6.dll", "libwinpthread-1.dll")
    return [bin_dir / name for name in names if (bin_dir / name).is_file()]


def stage_mingw_runtime_dlls(dll: Path, prefix: str) -> list[Path]:
    staged: list[Path] = []
    for source in mingw_runtime_dlls(prefix):
        target = dll.parent / source.name
        if source.resolve() == target.resolve():
            continue
        shutil.copy2(source, target)
        staged.append(target)
    return staged


def main() -> int:
    args = parse_args()
    require_tool("cmake")
    for tool in expected_tool_names(args.mingw_prefix):
        require_tool(tool)
    if resolve_rc_tool(args.mingw_prefix) is None:
        raise SystemExit(f"required tool not found on PATH: {args.mingw_prefix}-windres or windres")

    build_dir = (ROOT / args.build_dir).resolve()
    if args.clean and build_dir.exists():
        shutil.rmtree(build_dir)

    cmake_args = ["cmake"]
    generator = args.generator
    if generator is None and platform.system().lower() == "windows":
        generator = "MinGW Makefiles"
    if generator:
        cmake_args.extend(["-G", generator])
    cmake_args.extend(
        [
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
    )
    run(cmake_args)
    run(["cmake", "--build", str(build_dir), "--config", args.config, "--target", args.target])
    dll = find_windows_dll(build_dir)
    print(dll)
    for runtime_dll in stage_mingw_runtime_dlls(dll, args.mingw_prefix):
        print(runtime_dll)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
