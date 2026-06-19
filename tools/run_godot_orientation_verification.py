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
DEFAULT_BINARIES = ("godot", "godot4", "godot4.3", "godot4.2")


def resolve_godot(explicit: str | None) -> str | None:
    if explicit:
        return explicit
    for candidate in DEFAULT_BINARIES:
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    return None


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
    godot_binary = resolve_godot(args.godot)
    if godot_binary is None:
        if args.dry_run:
            godot_binary = DEFAULT_BINARIES[0]
        else:
            raise SystemExit("Could not find a godot executable on PATH")
    command = build_command(godot_binary)
    print(" ".join(command))
    if args.dry_run:
        return 0
    completed = subprocess.run(command, cwd=ROOT)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
