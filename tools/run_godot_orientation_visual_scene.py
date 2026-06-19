#!/usr/bin/env python3
"""Run the Godot visual orientation verification scene headlessly."""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess

import build_godot_extension
import godot_env
import load_local_env
import sync_orientation_fixtures
from run_godot_orientation_verification import ADDON_BIN_DIR, shared_library_candidates, staged_build_complete, wrapper_candidates


ROOT = Path(__file__).resolve().parents[1]
ALIAS_ROOT = godot_env.repo_alias_root(ROOT)
PROJECT_DIR = ROOT / "examples" / "godot" / "fastdis_orientation_verification"
ALIAS_PROJECT_DIR = ALIAS_ROOT / "examples" / "godot" / "fastdis_orientation_verification"
ALIAS_SCRIPT_PATH = ALIAS_PROJECT_DIR / "scripts" / "run_orientation_visual_scene.gd"


def build_command(godot_binary: str) -> list[str]:
    return [
        godot_binary,
        "--headless",
        "--path",
        str(ALIAS_PROJECT_DIR),
        "--script",
        str(ALIAS_SCRIPT_PATH),
    ]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--godot", help="Explicit godot executable path")
    parser.add_argument("--skip-build", action="store_true", help="Do not rebuild/stage the Godot extension before running")
    parser.add_argument("--dry-run", action="store_true", help="Print the command without executing it")
    return parser.parse_args()


def main() -> int:
    load_local_env.load()
    args = parse_args()
    fixture_destination = sync_orientation_fixtures.DESTINATIONS["godot"]
    sync_orientation_fixtures.write_fixture_copy(fixture_destination)
    sync_orientation_fixtures.verify_fixture_copy(fixture_destination)
    build_required = not staged_build_complete()
    if not args.dry_run and not args.skip_build and build_required:
        subprocess.run(godot_env.python_command() + [str(ROOT / "tools" / "build_godot_extension.py")], cwd=ROOT, check=True)
    godot_binary = godot_env.resolve_godot(args.godot)
    if godot_binary is None:
        if args.dry_run:
            godot_binary = "godot"
        else:
            raise SystemExit("Could not find a godot executable on PATH or in FASTDIS_GODOT")
    wrappers = wrapper_candidates()
    wrapper_found = all(path.is_file() for path in wrappers)
    if not wrapper_found and not args.dry_run:
        names = ", ".join(path.name for path in wrappers)
        raise SystemExit(
            "Godot is installed, but the FastDIS GDExtension wrapper set is incomplete or stale. "
            f"Expected one of: {names} under {ADDON_BIN_DIR}. "
            "Run `python tools/godot_workflow.py build` first."
        )
    if not any(path.is_file() for path in shared_library_candidates()) and not args.dry_run:
        raise SystemExit(
            "Godot orientation visual scene verification requires a staged libfastdis shared library under "
            f"{ADDON_BIN_DIR}."
        )
    command = build_command(godot_binary)
    print(" ".join(command))
    if args.dry_run:
        return 0
    completed = subprocess.run(command, cwd=ALIAS_ROOT, env=godot_env.build_env())
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
