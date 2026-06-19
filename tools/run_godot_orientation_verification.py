#!/usr/bin/env python3
"""Run the Godot orientation verification harness."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import load_local_env
import sync_orientation_fixtures


ROOT = Path(__file__).resolve().parents[1]
PROJECT_DIR = ROOT / "examples" / "godot" / "fastdis_orientation_verification"
SCRIPT_PATH = PROJECT_DIR / "scripts" / "run_orientation_tests.gd"
ADDON_DIR = PROJECT_DIR / "addons" / "fastdis"
ADDON_BIN_DIR = ADDON_DIR / "bin"
GDEXTENSION_DIR = ROOT / "examples" / "godot" / "fastdis_gdextension"
GDEXTENSION_DEMO_BIN_DIR = ROOT / "examples" / "godot" / "fastdis_demo" / "addons" / "fastdis" / "bin"
DEFAULT_BINARIES = (
    "godot",
    "godot4",
    "godot4.3",
    "godot4.2",
    "/Users/rick/Applications/Godot.app/Contents/MacOS/Godot",
)


def resolve_godot(explicit: str | None) -> str | None:
    if explicit:
        return explicit
    env_candidate = os.environ.get("FASTDIS_GODOT")
    if env_candidate:
        path = Path(env_candidate).expanduser()
        if path.is_file():
            return str(path)
    for candidate in DEFAULT_BINARIES:
        if "/" in candidate and Path(candidate).is_file():
            return candidate
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    return None


def stage_shared_library() -> list[str]:
    staged: list[str] = []
    ADDON_BIN_DIR.mkdir(parents=True, exist_ok=True)
    for candidate in (
        ROOT / "build" / "libfastdis.dylib",
        ROOT / "build" / "libfastdis.0.dylib",
        ROOT / "build" / "libfastdis.0.12.0.dylib",
    ):
        if candidate.is_file():
            target = ADDON_BIN_DIR / candidate.name
            shutil.copy2(candidate, target)
            staged.append(str(target))
    return staged


def stage_wrapper_library() -> list[str]:
    staged: list[str] = []
    ADDON_BIN_DIR.mkdir(parents=True, exist_ok=True)
    for candidate in demo_wrapper_candidates():
        if candidate.is_file():
            target = ADDON_BIN_DIR / candidate.name
            shutil.copy2(candidate, target)
            staged.append(str(target))
    return staged


def wrapper_candidates() -> list[Path]:
    return [
        ADDON_BIN_DIR / "libfastdis_gdextension.macos.template_debug.dylib",
        ADDON_BIN_DIR / "libfastdis_gdextension.macos.template_release.dylib",
    ]


def demo_wrapper_candidates() -> list[Path]:
    return [
        GDEXTENSION_DEMO_BIN_DIR / "libfastdis_gdextension.macos.template_debug.dylib",
        GDEXTENSION_DEMO_BIN_DIR / "libfastdis_gdextension.macos.template_release.dylib",
    ]


def resolve_scons() -> str | None:
    candidates = [str(ROOT / ".venv" / "bin" / "scons")]
    env_candidate = os.environ.get("FASTDIS_SCONS")
    if env_candidate:
        candidates.append(env_candidate)
    candidates.append("scons")
    for candidate in candidates:
        if "/" in candidate and Path(candidate).is_file():
            return candidate
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    return None


def maybe_build_wrapper() -> None:
    if any(path.is_file() for path in wrapper_candidates()) or any(path.is_file() for path in demo_wrapper_candidates()):
        return
    scons = resolve_scons()
    if scons is None:
        return
    command = [
        scons,
        "platform=macos",
        "target=template_debug",
        "arch=arm64",
        "-C",
        str(GDEXTENSION_DIR),
    ]
    subprocess.run(command, cwd=ROOT, check=True)


def build_command(godot_binary: str) -> list[str]:
    return [
        godot_binary,
        "--headless",
        "--path",
        str(PROJECT_DIR),
        "--script",
        str(SCRIPT_PATH),
    ]


def build_env() -> dict[str, str]:
    env = dict(os.environ)
    sandbox_home = Path(tempfile.gettempdir()) / "fastdis_godot_home"
    (sandbox_home / "Library" / "Application Support").mkdir(parents=True, exist_ok=True)
    env["HOME"] = str(sandbox_home)
    return env


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--godot", help="Explicit godot executable path")
    parser.add_argument("--dry-run", action="store_true", help="Print the command without executing it")
    return parser.parse_args()


def main() -> int:
    load_local_env.load()
    args = parse_args()
    sync_orientation_fixtures.write_fixture_copy(sync_orientation_fixtures.DESTINATIONS["godot"])
    staged = stage_shared_library()
    if not args.dry_run:
        maybe_build_wrapper()
    staged_wrappers = stage_wrapper_library()
    godot_binary = resolve_godot(args.godot)
    if godot_binary is None:
        if args.dry_run:
            godot_binary = DEFAULT_BINARIES[0]
        else:
            raise SystemExit("Could not find a godot executable on PATH")
    wrappers = wrapper_candidates()
    wrapper_found = any(path.is_file() for path in wrappers)
    if not wrapper_found and not args.dry_run:
        names = ", ".join(path.name for path in wrappers)
        raise SystemExit(
            "Godot is installed, but the FastDIS GDExtension wrapper is missing. "
            f"Expected one of: {names} under {ADDON_BIN_DIR}. "
            "Build examples/godot/fastdis_gdextension first."
        )
    command = build_command(godot_binary)
    print(" ".join(command))
    if staged:
        print("staged shared libraries:")
        for item in staged:
            print(item)
    if staged_wrappers:
        print("staged wrapper libraries:")
        for item in staged_wrappers:
            print(item)
    if not wrapper_found:
        print(f"wrapper missing under {ADDON_BIN_DIR}")
    if args.dry_run:
        return 0
    completed = subprocess.run(command, cwd=ROOT, env=build_env())
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
