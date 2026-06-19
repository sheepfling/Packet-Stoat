#!/usr/bin/env python3
"""Run the Godot orientation verification harness."""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

import sync_orientation_fixtures


ROOT = Path(__file__).resolve().parents[1]
PROJECT_DIR = ROOT / "examples" / "godot" / "fastdis_orientation_verification"
SCRIPT_PATH = PROJECT_DIR / "scripts" / "run_orientation_tests.gd"
ADDON_DIR = PROJECT_DIR / "addons" / "fastdis"
ADDON_BIN_DIR = ADDON_DIR / "bin"
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
        ROOT / "build" / "libfastdis.0.12.0.dylib",
    ):
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


def build_command(godot_binary: str) -> list[str]:
    return [
        godot_binary,
        "--headless",
        "--path",
        str(PROJECT_DIR),
        "--script",
        str(SCRIPT_PATH),
    ]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--godot", help="Explicit godot executable path")
    parser.add_argument("--dry-run", action="store_true", help="Print the command without executing it")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    sync_orientation_fixtures.write_fixture_copy(sync_orientation_fixtures.DESTINATIONS["godot"])
    staged = stage_shared_library()
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
    if not wrapper_found:
        print(f"wrapper missing under {ADDON_BIN_DIR}")
    if args.dry_run:
        return 0
    completed = subprocess.run(command, cwd=ROOT)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
