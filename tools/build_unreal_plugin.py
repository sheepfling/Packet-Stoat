#!/usr/bin/env python3
"""Build and package the FastDIS Unreal plugin for the current machine.

This helper is host-oriented rather than cross-compiling. Run it on macOS for
Mac plugin artifacts, on Windows for Win64 artifacts, and on Linux for Linux
artifacts. It stages the current repo headers/native library into the plugin's
ThirdParty layout, then runs Unreal's BuildPlugin flow.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile

import load_local_env
import unreal_env

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PLUGIN_DIR = ROOT / "examples" / "unreal" / "FastDis"
DEFAULT_UNREAL_WORK_ROOT = Path(tempfile.gettempdir()).resolve() / "fastdis_unreal"
DEFAULT_PACKAGE_DIR = DEFAULT_UNREAL_WORK_ROOT / "FastDisPackage"
DEFAULT_HOST_PROJECT_DIR = DEFAULT_UNREAL_WORK_ROOT / "FastDisHostProject"
DEFAULT_NATIVE_BUILD_DIR = DEFAULT_UNREAL_WORK_ROOT / "native"


def run(cmd: list[str], *, cwd: Path | None = None) -> None:
    print("+", " ".join(str(part) for part in cmd))
    completed = subprocess.run(
        cmd,
        cwd=cwd or ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if completed.stdout:
        print(completed.stdout, end="")
    if completed.returncode == 0:
        return
    if "A conflicting instance of AutomationTool is already running" in completed.stdout:
        raise SystemExit(
            "Unreal AutomationTool is already running for another build on this machine. "
            "Wait for the other Unreal build to finish, or terminate the stale AutomationTool process, then rerun "
            "`python tools/unreal_workflow.py build --engine-version ...`."
        )
    raise subprocess.CalledProcessError(completed.returncode, cmd)


def host_platform_name() -> str:
    system = platform.system().lower()
    if system == "darwin":
        return "Mac"
    if system == "windows":
        return "Win64"
    if system == "linux":
        return "Linux"
    raise SystemExit(f"Unsupported host platform: {platform.system()}")


def default_unreal_engine_dir() -> Path | None:
    return unreal_env.resolve_engine_dir()


def uat_path(engine_dir: Path) -> Path:
    system = platform.system().lower()
    if system == "windows":
        path = engine_dir / "Engine" / "Build" / "BatchFiles" / "RunUAT.bat"
    else:
        path = engine_dir / "Engine" / "Build" / "BatchFiles" / "RunUAT.sh"
    if not path.exists():
        raise SystemExit(f"Could not find Unreal AutomationTool launcher at {path}")
    return path


def rider_path() -> Path | None:
    env = os.environ.get("FASTDIS_RIDER")
    if env:
        path = Path(env).expanduser()
        if path.exists():
            return path

    found = shutil.which("rider")
    if found:
        return Path(found)

    system = platform.system().lower()
    candidates: list[Path]
    if system == "darwin":
        candidates = [
            Path.home() / "Library" / "Application Support" / "JetBrains" / "Toolbox" / "scripts" / "rider",
            Path.home() / "Applications" / "Rider.app" / "Contents" / "MacOS" / "rider",
            Path("/Applications/Rider.app/Contents/MacOS/rider"),
        ]
    elif system == "windows":
        candidates = [
            Path.home() / "AppData" / "Local" / "JetBrains" / "Toolbox" / "scripts" / "rider64.exe",
            Path("C:/Program Files/JetBrains/JetBrains Rider/bin/rider64.exe"),
        ]
    else:
        candidates = [
            Path.home() / ".local" / "share" / "JetBrains" / "Toolbox" / "scripts" / "rider",
            Path("/opt/JetBrains Rider/bin/rider.sh"),
        ]

    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def ensure_clean_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def create_host_project(plugin_dir: Path, host_project_dir: Path) -> Path:
    host_project_dir.mkdir(parents=True, exist_ok=True)
    plugins_dir = host_project_dir / "Plugins"
    plugins_dir.mkdir(parents=True, exist_ok=True)

    project_file = host_project_dir / "HostProject.uproject"
    project_data = {
        "FileVersion": 3,
        "EngineAssociation": "",
        "Category": "",
        "Description": "Local FastDIS Unreal host project for Rider indexing and manual editor bring-up.",
        "Plugins": [
            {
                "Name": "FastDis",
                "Enabled": True,
            }
        ],
    }
    project_file.write_text(json.dumps(project_data, indent=2) + "\n", encoding="utf-8")

    linked_plugin_dir = plugins_dir / "FastDis"
    if linked_plugin_dir.exists() or linked_plugin_dir.is_symlink():
        if linked_plugin_dir.is_symlink() or linked_plugin_dir.is_file():
            linked_plugin_dir.unlink()
        else:
            shutil.rmtree(linked_plugin_dir)

    try:
        linked_plugin_dir.symlink_to(plugin_dir, target_is_directory=True)
    except OSError:
        shutil.copytree(plugin_dir, linked_plugin_dir)
        print(f"warning: symlink creation failed; copied plugin into {linked_plugin_dir}")

    return project_file


def configure_native_build(build_dir: Path, config: str, host_platform: str, mac_arches: str, mac_deployment_target: str) -> None:
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
    if host_platform == "Mac":
        cmake_args.append(f"-DCMAKE_OSX_ARCHITECTURES={mac_arches}")
        cmake_args.append(f"-DCMAKE_OSX_DEPLOYMENT_TARGET={mac_deployment_target}")
    run(cmake_args)
    run(["cmake", "--build", str(build_dir), "--config", config])


def copy_file_resolved(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src.resolve(), dst)


def find_one(build_dir: Path, patterns: list[str]) -> Path:
    matches: list[Path] = []
    for pattern in patterns:
        matches.extend(build_dir.rglob(pattern))
    existing = [match for match in matches if match.exists()]
    if not existing:
        raise SystemExit(f"Could not find native artifact in {build_dir} matching {patterns}")
    return max(existing, key=lambda path: path.stat().st_mtime)


def stage_headers(plugin_dir: Path) -> None:
    dst = plugin_dir / "ThirdParty" / "fastdis" / "include" / "fastdis"
    dst.mkdir(parents=True, exist_ok=True)
    for header in sorted((ROOT / "include" / "fastdis").iterdir()):
        if header.is_file():
            shutil.copy2(header, dst / header.name)


def stage_mac_libs(build_dir: Path, plugin_dir: Path) -> None:
    lib_dir = plugin_dir / "ThirdParty" / "fastdis" / "lib" / "Mac"
    lib_dir.mkdir(parents=True, exist_ok=True)
    versioned = find_one(build_dir, ["libfastdis.*.*.dylib", "libfastdis.*.dylib"])
    copy_file_resolved(versioned, lib_dir / versioned.name)
    copy_file_resolved(versioned, lib_dir / "libfastdis.0.dylib")
    copy_file_resolved(versioned, lib_dir / "libfastdis.dylib")


def stage_linux_libs(build_dir: Path, plugin_dir: Path) -> None:
    lib_dir = plugin_dir / "ThirdParty" / "fastdis" / "lib" / "Linux"
    lib_dir.mkdir(parents=True, exist_ok=True)
    soname = find_one(build_dir, ["libfastdis.so*", "libfastdis.*.so*"])
    copy_file_resolved(soname, lib_dir / soname.name)
    copy_file_resolved(soname, lib_dir / "libfastdis.so")


def stage_windows_libs(build_dir: Path, plugin_dir: Path) -> None:
    lib_dir = plugin_dir / "ThirdParty" / "fastdis" / "lib" / "Win64"
    bin_dir = plugin_dir / "ThirdParty" / "fastdis" / "bin" / "Win64"
    lib_dir.mkdir(parents=True, exist_ok=True)
    bin_dir.mkdir(parents=True, exist_ok=True)
    dll = find_one(build_dir, ["fastdis.dll"])
    import_lib = find_one(build_dir, ["fastdis.lib", "libfastdis.lib"])
    shutil.copy2(dll, bin_dir / "fastdis.dll")
    shutil.copy2(import_lib, lib_dir / "fastdis.lib")


def stage_host_native(build_dir: Path, plugin_dir: Path, host_platform: str) -> None:
    stage_headers(plugin_dir)
    if host_platform == "Mac":
        stage_mac_libs(build_dir, plugin_dir)
    elif host_platform == "Linux":
        stage_linux_libs(build_dir, plugin_dir)
    elif host_platform == "Win64":
        stage_windows_libs(build_dir, plugin_dir)
    else:
        raise SystemExit(f"Unsupported host platform for staging: {host_platform}")


def build_plugin(engine_dir: Path, plugin_dir: Path, package_dir: Path, target_platforms: list[str]) -> None:
    cmd = [
        str(uat_path(engine_dir)),
        "BuildPlugin",
        f"-Plugin={plugin_dir / 'FastDis.uplugin'}",
        f"-Package={package_dir}",
        f"-TargetPlatforms={'+'.join(target_platforms)}",
    ]
    run(cmd)


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def require_packaged_file(plugin_dir: Path, package_dir: Path, relative_path: str, errors: list[str], compare_hash: bool = True) -> None:
    source = plugin_dir / relative_path
    packaged = package_dir / relative_path
    if not packaged.exists():
        errors.append(f"missing packaged file: {relative_path}")
        return
    if compare_hash and source.exists() and sha256_file(source) != sha256_file(packaged):
        errors.append(f"packaged file differs from staged plugin source: {relative_path}")


def verify_plugin_descriptor(package_dir: Path, errors: list[str]) -> None:
    descriptor = package_dir / "FastDis.uplugin"
    if not descriptor.exists():
        errors.append("missing packaged file: FastDis.uplugin")
        return
    try:
        data = json.loads(descriptor.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"packaged FastDis.uplugin is not valid JSON: {exc}")
        return
    modules = data.get("Modules", [])
    has_runtime_module = any(
        module.get("Name") == "FastDisUnreal" and module.get("Type") == "Runtime"
        for module in modules
        if isinstance(module, dict)
    )
    if data.get("FriendlyName") != "FastDIS":
        errors.append("packaged FastDis.uplugin has unexpected FriendlyName")
    if not has_runtime_module:
        errors.append("packaged FastDis.uplugin is missing FastDisUnreal Runtime module")


def verify_macos_dylib(package_dir: Path, required_arches: str, errors: list[str]) -> None:
    dylib = package_dir / "ThirdParty" / "fastdis" / "lib" / "Mac" / "libfastdis.dylib"
    if platform.system().lower() != "darwin" or not dylib.exists():
        return

    try:
        result = subprocess.run(["lipo", "-info", str(dylib)], check=True, capture_output=True, text=True)
    except (OSError, subprocess.CalledProcessError) as exc:
        errors.append(f"could not inspect packaged macOS dylib architectures: {exc}")
        return

    output = result.stdout.strip()
    for arch in [item.strip() for item in required_arches.replace(",", ";").split(";") if item.strip()]:
        if arch not in output:
            errors.append(f"packaged macOS libfastdis.dylib missing architecture {arch}: {output}")


def verify_packaged_plugin(plugin_dir: Path, package_dir: Path, target_platforms: list[str], mac_arches: str) -> None:
    errors: list[str] = []
    common_required = [
        "README.md",
        "Config/FilterPlugin.ini",
        "Source/FastDisUnreal/FastDisUnreal.Build.cs",
        "Source/FastDisUnreal/Private/FastDisModule.cpp",
        "Source/FastDisUnreal/Private/FastDisReplayActor.cpp",
        "Source/FastDisUnreal/Private/FastDisSampleTrafficComponent.cpp",
        "Source/FastDisUnreal/Private/FastDisWorldSubsystem.cpp",
        "Source/FastDisUnreal/Public/FastDisReplayActor.h",
        "Source/FastDisUnreal/Public/FastDisSampleTrafficComponent.h",
        "Source/FastDisUnreal/Public/FastDisTypes.h",
        "Source/FastDisUnreal/Public/FastDisWorldSubsystem.h",
        "ThirdParty/fastdis/include/fastdis/fastdis.h",
        "ThirdParty/fastdis/include/fastdis/fastdis.hpp",
        "ThirdParty/fastdis/include/fastdis/fastdis_frames.hpp",
    ]
    verify_plugin_descriptor(package_dir, errors)
    for relative_path in common_required:
        require_packaged_file(plugin_dir, package_dir, relative_path, errors)

    if "Mac" in target_platforms:
        for relative_path in [
            "ThirdParty/fastdis/lib/Mac/libfastdis.dylib",
            "ThirdParty/fastdis/lib/Mac/libfastdis.0.dylib",
        ]:
            require_packaged_file(plugin_dir, package_dir, relative_path, errors)
        if not list((package_dir / "ThirdParty" / "fastdis" / "lib" / "Mac").glob("libfastdis.*.*.dylib")):
            errors.append("missing packaged versioned macOS dylib: ThirdParty/fastdis/lib/Mac/libfastdis.*.*.dylib")
        verify_macos_dylib(package_dir, mac_arches, errors)

    if "Linux" in target_platforms:
        require_packaged_file(plugin_dir, package_dir, "ThirdParty/fastdis/lib/Linux/libfastdis.so", errors)

    if "Win64" in target_platforms:
        require_packaged_file(plugin_dir, package_dir, "ThirdParty/fastdis/lib/Win64/fastdis.lib", errors)
        require_packaged_file(plugin_dir, package_dir, "ThirdParty/fastdis/bin/Win64/fastdis.dll", errors)

    if errors:
        print("Packaged plugin verification failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        raise SystemExit(4)

    print(f"Verified packaged plugin payload for {', '.join(target_platforms)}: {package_dir}")


def open_in_rider(project_path: Path) -> None:
    rider = rider_path()
    if rider is None:
        raise SystemExit(
            "Could not find Rider. Set FASTDIS_RIDER or put rider on PATH before using --open-rider."
        )
    print(f"+ opening Rider: {rider} {project_path}")
    subprocess.Popen([str(rider), str(project_path)], cwd=ROOT)


def parse_target_platforms(raw: str | None, host_platform: str) -> list[str]:
    if not raw:
        return [host_platform]
    values = [item.strip() for item in raw.replace(",", "+").split("+") if item.strip()]
    if not values:
        return [host_platform]
    return values


def unreal_safe_dir(path: Path, label: str) -> Path:
    resolved = path.expanduser().resolve()
    if " " not in str(resolved):
        return resolved

    alias_root = DEFAULT_UNREAL_WORK_ROOT / "aliases"
    alias_root.mkdir(parents=True, exist_ok=True)
    alias = alias_root / label

    if alias.exists() or alias.is_symlink():
        if alias.is_symlink() or alias.is_file():
            alias.unlink()
        else:
            shutil.rmtree(alias)

    try:
        alias.symlink_to(resolved, target_is_directory=True)
        print(f"Using Unreal-safe alias: {alias} -> {resolved}")
        return alias
    except OSError:
        print(
            "warning: could not create a no-space alias for Unreal packaging. "
            f"Continuing with the original path: {resolved}"
        )
        return resolved


def main() -> int:
    load_local_env.load()
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine-dir", help="Path to the Unreal Engine root (for example /Users/Shared/Epic Games/UE_5.7)")
    parser.add_argument("--engine-version", help="Versioned Unreal env selector, for example 5.7 or 5.8")
    parser.add_argument("--plugin-dir", default=str(DEFAULT_PLUGIN_DIR), help="Path to the FastDis Unreal plugin directory")
    parser.add_argument("--package-dir", default=str(DEFAULT_PACKAGE_DIR), help="Output directory for Unreal BuildPlugin packaging")
    parser.add_argument("--host-project-dir", default=str(DEFAULT_HOST_PROJECT_DIR), help="Persistent local host project for Rider/editor use")
    parser.add_argument("--native-build-dir", default=str(DEFAULT_NATIVE_BUILD_DIR), help="CMake build directory for the native fastdis library")
    parser.add_argument("--config", default="Release", help="CMake/Unreal build configuration")
    parser.add_argument("--target-platforms", help="Unreal BuildPlugin target platforms, for example Mac or Win64+Linux")
    parser.add_argument("--mac-architectures", default="arm64;x86_64", help="macOS native library architectures")
    parser.add_argument("--macos-deployment-target", default="14.0", help="macOS deployment target for Unreal plugin dylib builds")
    parser.add_argument("--skip-native-build", action="store_true", help="Do not rebuild the native fastdis library before staging")
    parser.add_argument("--skip-package", action="store_true", help="Stop after staging the ThirdParty payload")
    parser.add_argument("--verify-only", action="store_true", help="Verify an existing packaged plugin without rebuilding it")
    parser.add_argument("--clean-package", action="store_true", help="Delete the package directory before BuildPlugin")
    parser.add_argument("--open-rider", action="store_true", help="Open the generated HostProject.uproject in Rider after packaging")
    args = parser.parse_args()

    host_platform = host_platform_name()
    target_platforms = parse_target_platforms(args.target_platforms, host_platform)

    if any(target != host_platform for target in target_platforms):
        raise SystemExit(
            "This helper is host-oriented. Run it on the target OS or pass only the host target platform. "
            f"Host platform is {host_platform}; requested targets were {target_platforms}."
        )

    if args.engine_dir:
        engine_dir = Path(args.engine_dir).expanduser()
    else:
        engine_dir = unreal_env.resolve_engine_dir(args.engine_version)
        if engine_dir is None:
            engine_dir = default_unreal_engine_dir()
    if engine_dir is None or not engine_dir.exists():
        raise SystemExit(
            "Could not locate an Unreal Engine install. Set --engine-dir, "
            "FASTDIS_UNREAL_ENGINE_DIR, or a versioned FASTDIS_UNREAL_ENGINE_DIR_5_7 style variable."
        )

    plugin_dir = Path(args.plugin_dir).expanduser().resolve()
    package_dir = Path(args.package_dir).expanduser().resolve()
    host_project_dir = Path(args.host_project_dir).expanduser().resolve()
    native_build_dir = Path(args.native_build_dir).expanduser().resolve()
    package_dir_for_uat = unreal_safe_dir(package_dir, "FastDisPackage")

    if not (plugin_dir / "FastDis.uplugin").exists():
        raise SystemExit(f"Could not find FastDis.uplugin under {plugin_dir}")

    if args.verify_only:
        verify_packaged_plugin(plugin_dir, package_dir, target_platforms, args.mac_architectures)
        return 0

    if not args.skip_native_build:
        configure_native_build(native_build_dir, args.config, host_platform, args.mac_architectures, args.macos_deployment_target)

    stage_host_native(native_build_dir, plugin_dir, host_platform)
    host_project = create_host_project(plugin_dir, host_project_dir)
    print(f"Host project: {host_project}")

    if args.skip_package:
        print(f"Staged Unreal ThirdParty payload under {plugin_dir / 'ThirdParty' / 'fastdis'}")
        if args.open_rider:
            open_in_rider(host_project)
        return 0

    if args.clean_package and package_dir.exists():
        shutil.rmtree(package_dir)
    if package_dir_for_uat != package_dir and package_dir_for_uat.exists():
        shutil.rmtree(package_dir_for_uat)

    build_plugin(engine_dir, plugin_dir, package_dir_for_uat, target_platforms)
    verify_packaged_plugin(plugin_dir, package_dir, target_platforms, args.mac_architectures)

    print(f"Packaged plugin: {package_dir}")
    if args.open_rider:
        open_in_rider(host_project)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
