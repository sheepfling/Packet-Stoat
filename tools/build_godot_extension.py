#!/usr/bin/env python3
"""Build and stage the FastDIS Godot GDExtension plus host-native shared library."""

from __future__ import annotations

import argparse
from pathlib import Path
import platform
import shutil
import subprocess

import godot_env
import load_local_env


ROOT = Path(__file__).resolve().parents[1]
ALIAS_ROOT = godot_env.repo_alias_root(ROOT)
REAL_GDEXTENSION_DIR = ROOT / "examples" / "godot" / "fastdis_gdextension"
ALIAS_GDEXTENSION_DIR = ALIAS_ROOT / "examples" / "godot" / "fastdis_gdextension"
REAL_DEMO_BIN_DIR = ROOT / "examples" / "godot" / "fastdis_demo" / "addons" / "fastdis" / "bin"
REAL_VERIFY_BIN_DIR = ROOT / "examples" / "godot" / "fastdis_orientation_verification" / "addons" / "fastdis" / "bin"
DEFAULT_NATIVE_BUILD_DIR = godot_env.DEFAULT_WORK_ROOT / "native"


def run(cmd: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None) -> None:
    print("+", " ".join(str(part) for part in cmd))
    subprocess.run(cmd, cwd=cwd or ROOT, env=env, check=True)


def find_one(build_dir: Path, patterns: list[str]) -> Path:
    matches: list[Path] = []
    for pattern in patterns:
        matches.extend(build_dir.rglob(pattern))
    existing = [match for match in matches if match.exists()]
    if not existing:
        raise SystemExit(f"Could not find Godot/native artifact in {build_dir} matching {patterns}")
    return max(existing, key=lambda path: path.stat().st_mtime)


def prune_host_artifacts(directory: Path, allowed_names: set[str]) -> None:
    if not directory.exists():
        directory.mkdir(parents=True, exist_ok=True)
        return
    for path in directory.iterdir():
        if not path.is_file():
            continue
        name = path.name
        if "fastdis_gdextension" in name or name.startswith("libfastdis") or name.startswith("fastdis"):
            if name not in allowed_names:
                path.unlink()


def configure_native_build(build_dir: Path, config: str, mac_arches: str, mac_deployment_target: str) -> None:
    cmake_args = [
        "cmake",
        "-S",
        str(ROOT),
        "-B",
        str(build_dir),
        "-DFASTDIS_BUILD_SHARED=ON",
        "-DFASTDIS_BUILD_STATIC=OFF",
        "-DFASTDIS_BUILD_TESTS=OFF",
        "-DFASTDIS_BUILD_EXAMPLES=OFF",
        "-DFASTDIS_BUILD_BENCHMARKS=OFF",
        f"-DCMAKE_BUILD_TYPE={config}",
    ]
    if platform.system().lower() == "darwin":
        cmake_args.append(f"-DCMAKE_OSX_ARCHITECTURES={mac_arches}")
        cmake_args.append(f"-DCMAKE_OSX_DEPLOYMENT_TARGET={mac_deployment_target}")
    run(cmake_args)
    run(["cmake", "--build", str(build_dir), "--config", config])


def stage_shared_library(build_dir: Path) -> list[Path]:
    REAL_DEMO_BIN_DIR.mkdir(parents=True, exist_ok=True)
    REAL_VERIFY_BIN_DIR.mkdir(parents=True, exist_ok=True)

    platform_name = godot_env.host_platform_name()
    if platform_name == "windows":
        source = find_one(build_dir, ["fastdis.dll"])
        runtime_names = {source.name}
    elif platform_name == "macos":
        source = find_one(build_dir, ["libfastdis.*.*.dylib", "libfastdis.*.dylib", "libfastdis.dylib"])
        runtime_names = {source.name, "libfastdis.0.dylib", "libfastdis.dylib"}
    else:
        source = find_one(build_dir, ["libfastdis.so.*", "libfastdis.*.so*", "libfastdis.so"])
        runtime_names = {source.name, "libfastdis.so"}

    staged: list[Path] = []
    for target_dir in (REAL_DEMO_BIN_DIR, REAL_VERIFY_BIN_DIR):
        prune_host_artifacts(target_dir, set(godot_env.wrapper_names()) | runtime_names)
        target = target_dir / source.name
        shutil.copy2(source.resolve(), target)
        staged.append(target)
        if platform_name == "macos":
            for alias_name in ("libfastdis.dylib", "libfastdis.0.dylib"):
                alias_target = target_dir / alias_name
                if alias_target.name != source.name:
                    shutil.copy2(source.resolve(), alias_target)
                    staged.append(alias_target)
        elif platform_name == "linux":
            alias_target = target_dir / "libfastdis.so"
            if alias_target.name != source.name:
                shutil.copy2(source.resolve(), alias_target)
                staged.append(alias_target)
    return staged


def build_wrapper(build_dir: Path, config: str) -> None:
    scons = godot_env.resolve_scons()
    if scons is None:
        raise SystemExit("Could not find scons. Set FASTDIS_SCONS or install scons on PATH.")
    if not (REAL_GDEXTENSION_DIR / "godot-cpp" / "SConstruct").is_file():
        raise SystemExit(
            "Could not find godot-cpp under examples/godot/fastdis_gdextension/godot-cpp. "
            "Initialize or vendor godot-cpp before building the wrapper."
        )

    env = godot_env.build_env()
    env["FASTDIS_INCLUDE"] = str((ALIAS_ROOT / "include").resolve())
    env["FASTDIS_LIB_DIR"] = str(build_dir.resolve())
    allowed_names = set(godot_env.wrapper_names()) | set(godot_env.shared_library_names())
    prune_host_artifacts(REAL_DEMO_BIN_DIR, allowed_names)
    prune_host_artifacts(REAL_VERIFY_BIN_DIR, allowed_names)
    command = [
        scons,
        f"platform={godot_env.host_platform_name()}",
        f"target={'template_release' if config.lower() == 'release' else 'template_debug'}",
        f"arch={godot_env.host_arch_name()}",
        "-C",
        str(ALIAS_GDEXTENSION_DIR),
    ]
    run(command, cwd=ALIAS_ROOT, env=env)


def verify_staged_outputs() -> None:
    missing: list[str] = []
    for directory in (REAL_DEMO_BIN_DIR, REAL_VERIFY_BIN_DIR):
        if not any((directory / name).is_file() for name in godot_env.wrapper_names()):
            missing.append(f"missing wrapper under {directory}")
        if not any((directory / name).is_file() for name in godot_env.shared_library_names()):
            missing.append(f"missing host-native shared library under {directory}")
    if missing:
        raise SystemExit("\n".join(missing))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native-build-dir", default=str(DEFAULT_NATIVE_BUILD_DIR), help="CMake build directory for libfastdis")
    parser.add_argument("--config", default="Release", help="Build configuration")
    parser.add_argument("--skip-native-build", action="store_true", help="Do not rebuild libfastdis before staging")
    parser.add_argument("--verify-only", action="store_true", help="Verify staged outputs without rebuilding")
    parser.add_argument("--mac-architectures", default="arm64;x86_64", help="macOS native library architectures")
    parser.add_argument("--macos-deployment-target", default="14.0", help="macOS deployment target for libfastdis")
    return parser.parse_args()


def main() -> int:
    load_local_env.load()
    args = parse_args()
    native_build_dir = Path(args.native_build_dir).expanduser().resolve()

    if args.verify_only:
        verify_staged_outputs()
        print("Verified staged Godot demo and verification bins.")
        return 0

    if not args.skip_native_build:
        configure_native_build(native_build_dir, args.config, args.mac_architectures, args.macos_deployment_target)
    staged = stage_shared_library(native_build_dir)
    build_wrapper(native_build_dir, args.config)
    verify_staged_outputs()

    print("Staged shared libraries:")
    for path in staged:
        print(path)
    print(f"Built/staged Godot wrapper for {godot_env.host_platform_name()} {godot_env.host_arch_name()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
