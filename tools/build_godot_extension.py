#!/usr/bin/env python3
"""Build and stage the FastDIS Godot GDExtension plus host-native shared library."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path
import platform
import shutil
import subprocess

import godot_env
import load_local_env


ROOT = Path(__file__).resolve().parents[1]
REAL_GDEXTENSION_DIR = ROOT / "packages" / "godot" / "fastdis_gdextension"
REAL_DEMO_BIN_DIR = ROOT / "packages" / "godot" / "fastdis_demo" / "addons" / "fastdis" / "bin"
REAL_VERIFY_BIN_DIR = ROOT / "packages" / "godot" / "fastdis_orientation_verification" / "addons" / "fastdis" / "bin"
BUILD_MANIFEST_NAME = "fastdis_godot_build_manifest.json"
BUILD_MANIFEST_SCHEMA = "fastdis.godot_build_manifest.v1"
GODOT_CPP_REMOTE_URL = os.environ.get("FASTDIS_GODOT_CPP_URL", "https://github.com/godotengine/godot-cpp.git")
GODOT_CPP_REF_FALLBACKS = ("4.7", "4.6", "4.5", "4.4", "master")
BUILD_MANIFEST_SOURCES = (
    ROOT / "packages" / "godot" / "fastdis_gdextension" / "SConstruct",
    ROOT / "packages" / "godot" / "fastdis_gdextension" / "src" / "fastdis_world.cpp",
    ROOT / "packages" / "godot" / "fastdis_gdextension" / "src" / "fastdis_world.h",
    ROOT / "packages" / "godot" / "fastdis_gdextension" / "src" / "register_types.cpp",
    ROOT / "packages" / "godot" / "fastdis_gdextension" / "src" / "register_types.h",
    ROOT / "packages" / "godot" / "fastdis_demo" / "addons" / "fastdis" / "fastdis.gdextension",
    ROOT / "packages" / "godot" / "fastdis_orientation_verification" / "addons" / "fastdis" / "fastdis.gdextension",
    ROOT / "include" / "fastdis" / "fastdis_frames.hpp",
    ROOT / "include" / "fastdis" / "fastdis_orientation.hpp",
)


def run(cmd: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None) -> None:
    print("+", " ".join(str(part) for part in cmd))
    subprocess.run(cmd, cwd=cwd or ROOT, env=env, check=True)


def alias_root() -> Path:
    return godot_env.repo_alias_root(ROOT)


def alias_gdextension_dir() -> Path:
    return alias_root() / "packages" / "godot" / "fastdis_gdextension"


def default_native_build_dir() -> Path:
    return godot_env.work_root() / "native"


def hash_files(paths: tuple[Path, ...]) -> str:
    digest = hashlib.sha256()
    for path in paths:
        digest.update(str(path.relative_to(ROOT)).encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def godot_cpp_dir() -> Path:
    return REAL_GDEXTENSION_DIR / "godot-cpp"


def godot_cpp_is_ready() -> bool:
    return (godot_cpp_dir() / "SConstruct").is_file()


def detected_godot_version() -> str | None:
    godot = godot_env.resolve_godot()
    if not godot:
        return None
    try:
        completed = subprocess.run(
            [godot, "--version"],
            cwd=ROOT,
            env=godot_env.build_env(),
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    raw = (completed.stdout or completed.stderr or "").strip()
    match = re.search(r"(\d+\.\d+)", raw)
    return match.group(1) if match else None


def godot_cpp_ref_candidates() -> list[str]:
    override = os.environ.get("FASTDIS_GODOT_CPP_REF")
    if override:
        return [override]

    candidates: list[str] = []
    version = detected_godot_version()
    if version:
        candidates.append(version)
    candidates.extend(GODOT_CPP_REF_FALLBACKS)
    return list(dict.fromkeys(candidates))


def bootstrap_godot_cpp() -> Path:
    checkout = godot_cpp_dir()
    if godot_cpp_is_ready():
        return checkout

    git = shutil.which("git")
    if git is None:
        raise SystemExit(
            "Could not find git to bootstrap godot-cpp. Install git or vendor "
            "examples/godot/fastdis_gdextension/godot-cpp before building the wrapper."
        )

    if checkout.exists():
        raise SystemExit(
            "examples/godot/fastdis_gdextension/godot-cpp already exists but is not a usable checkout. "
            "Fix that tree or remove it before re-running bootstrap."
        )

    checkout.parent.mkdir(parents=True, exist_ok=True)
    errors: list[str] = []
    for ref in godot_cpp_ref_candidates():
        try:
            run([git, "clone", "--depth", "1", "--branch", ref, GODOT_CPP_REMOTE_URL, str(checkout)])
        except subprocess.CalledProcessError as exc:
            errors.append(f"{ref}: git clone exited {exc.returncode}")
            shutil.rmtree(checkout, ignore_errors=True)
            continue
        if godot_cpp_is_ready():
            return checkout
        errors.append(f"{ref}: clone completed but SConstruct was not found")
        shutil.rmtree(checkout, ignore_errors=True)

    tried = ", ".join(godot_cpp_ref_candidates())
    detail = "; ".join(errors) if errors else "no matching refs were attempted"
    raise SystemExit(
        "Could not bootstrap godot-cpp from the official repository. "
        f"Tried refs: {tried}. Details: {detail}"
    )


def build_manifest_payload() -> dict[str, object]:
    return {
        "schema": BUILD_MANIFEST_SCHEMA,
        "source_sha256": hash_files(BUILD_MANIFEST_SOURCES),
        "wrapper_names": godot_env.wrapper_names(),
        "shared_library_names": godot_env.shared_library_names(),
    }


def manifest_path(directory: Path) -> Path:
    return directory / BUILD_MANIFEST_NAME


def write_build_manifest() -> list[Path]:
    payload = build_manifest_payload()
    staged: list[Path] = []
    for directory in (REAL_DEMO_BIN_DIR, REAL_VERIFY_BIN_DIR):
        directory.mkdir(parents=True, exist_ok=True)
        path = manifest_path(directory)
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        staged.append(path)
    return staged


def manifest_is_current(directory: Path) -> bool:
    path = manifest_path(directory)
    if not path.is_file():
        return False
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    return payload == build_manifest_payload()


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
        runtime_names = set(godot_env.shared_library_names(platform_name)) | {source.name}
    elif platform_name == "macos":
        source = find_one(build_dir, ["libfastdis.*.*.dylib", "libfastdis.*.dylib", "libfastdis.dylib"])
        runtime_names = set(godot_env.shared_library_names(platform_name)) | {source.name}
    else:
        source = find_one(build_dir, ["libfastdis.so.*", "libfastdis.*.so*", "libfastdis.so"])
        runtime_names = set(godot_env.shared_library_names(platform_name)) | {source.name}

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


def native_link_dir(build_dir: Path) -> Path:
    platform_name = godot_env.host_platform_name()
    if platform_name == "windows":
        return find_one(build_dir, ["fastdis.lib", "libfastdis.dll.a"]).parent
    if platform_name == "macos":
        return find_one(build_dir, ["libfastdis.*.*.dylib", "libfastdis.*.dylib", "libfastdis.dylib"]).parent
    return find_one(build_dir, ["libfastdis.so.*", "libfastdis.*.so*", "libfastdis.so"]).parent


def stage_wrapper_artifacts() -> list[Path]:
    REAL_DEMO_BIN_DIR.mkdir(parents=True, exist_ok=True)
    REAL_VERIFY_BIN_DIR.mkdir(parents=True, exist_ok=True)

    wrapper_names = set(godot_env.wrapper_names())
    staged: list[Path] = []
    for name in wrapper_names:
        source = REAL_DEMO_BIN_DIR / name
        if not source.is_file():
            continue
        for target_dir in (REAL_DEMO_BIN_DIR, REAL_VERIFY_BIN_DIR):
            target = target_dir / name
            if target_dir == REAL_DEMO_BIN_DIR:
                staged.append(target)
                continue
            shutil.copy2(source.resolve(), target)
            staged.append(target)
    if not all((REAL_VERIFY_BIN_DIR / name).is_file() for name in wrapper_names):
        names = ", ".join(sorted(wrapper_names))
        raise SystemExit(
            "Could not stage Godot wrapper artifacts into the verification project. "
            f"Expected one of: {names}"
        )
    return staged


def parse_wrapper_targets(raw: str) -> tuple[str, ...]:
    normalized: list[str] = []
    for item in raw.split(","):
        name = item.strip().lower()
        if not name:
            continue
        if name in {"debug", "template_debug"}:
            normalized.append("template_debug")
        elif name in {"release", "template_release"}:
            normalized.append("template_release")
        else:
            raise SystemExit(
                f"Unsupported Godot wrapper target '{item}'. "
                "Use debug, release, template_debug, or template_release."
            )
    deduped = tuple(dict.fromkeys(normalized))
    if not deduped:
        raise SystemExit("At least one Godot wrapper target must be requested.")
    return deduped


def build_wrapper(build_dir: Path, wrapper_targets: tuple[str, ...], scons_jobs: int) -> None:
    scons = godot_env.resolve_scons()
    if scons is None:
        raise SystemExit("Could not find scons. Set FASTDIS_SCONS or install scons on PATH.")
    bootstrap_godot_cpp()

    env = godot_env.build_env()
    current_alias_root = alias_root()
    env["FASTDIS_INCLUDE"] = str((current_alias_root / "include").resolve())
    env["FASTDIS_LIB_DIR"] = str(native_link_dir(build_dir).resolve())
    allowed_names = set(godot_env.wrapper_names()) | set(godot_env.shared_library_names())
    prune_host_artifacts(REAL_DEMO_BIN_DIR, allowed_names)
    prune_host_artifacts(REAL_VERIFY_BIN_DIR, allowed_names)
    for wrapper_target in wrapper_targets:
        command = [
            scons,
            f"platform={godot_env.host_platform_name()}",
            f"target={wrapper_target}",
            f"arch={godot_env.host_arch_name()}",
            f"-j{max(1, scons_jobs)}",
            "-C",
            str(alias_gdextension_dir()),
        ]
        run(command, cwd=current_alias_root, env=env)


def verify_staged_outputs() -> None:
    missing: list[str] = []
    for directory in (REAL_DEMO_BIN_DIR, REAL_VERIFY_BIN_DIR):
        missing_wrappers = [name for name in godot_env.wrapper_names() if not (directory / name).is_file()]
        if missing_wrappers:
            missing.append(f"missing wrappers under {directory}: {', '.join(missing_wrappers)}")
        if not any((directory / name).is_file() for name in godot_env.shared_library_names()):
            missing.append(f"missing host-native shared library under {directory}")
        if not manifest_is_current(directory):
            missing.append(f"stale or missing build manifest under {directory}: {manifest_path(directory).name}")
    if missing:
        raise SystemExit("\n".join(missing))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native-build-dir", default=str(default_native_build_dir()), help="CMake build directory for libfastdis")
    parser.add_argument("--config", default="Release", help="Build configuration")
    parser.add_argument("--skip-native-build", action="store_true", help="Do not rebuild libfastdis before staging")
    parser.add_argument("--verify-only", action="store_true", help="Verify staged outputs without rebuilding")
    parser.add_argument(
        "--wrapper-targets",
        default="debug,release",
        help="Comma-separated Godot wrapper variants to build: debug,release by default",
    )
    parser.add_argument(
        "--scons-jobs",
        type=int,
        default=1,
        help="SCons parallelism for the Godot wrapper build; defaults to 1 for deterministic generated-header builds",
    )
    parser.add_argument("--mac-architectures", default="arm64;x86_64", help="macOS native library architectures")
    parser.add_argument("--macos-deployment-target", default="14.0", help="macOS deployment target for libfastdis")
    return parser.parse_args()


def main() -> int:
    load_local_env.load()
    args = parse_args()
    native_build_dir = Path(args.native_build_dir).expanduser().resolve()
    wrapper_targets = parse_wrapper_targets(args.wrapper_targets)

    if args.verify_only:
        verify_staged_outputs()
        print("Verified staged Godot demo and verification bins.")
        return 0

    if not args.skip_native_build:
        configure_native_build(native_build_dir, args.config, args.mac_architectures, args.macos_deployment_target)
    staged = stage_shared_library(native_build_dir)
    build_wrapper(native_build_dir, wrapper_targets, args.scons_jobs)
    staged.extend(stage_wrapper_artifacts())
    staged.extend(write_build_manifest())
    verify_staged_outputs()

    print("Staged shared libraries:")
    for path in staged:
        print(path)
    print(f"Built/staged Godot wrapper for {godot_env.host_platform_name()} {godot_env.host_arch_name()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
