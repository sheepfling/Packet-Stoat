#!/usr/bin/env python3
"""Run the Unreal orientation verification automation harness."""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

import sync_orientation_fixtures


ROOT = Path(__file__).resolve().parents[1]
PROJECT_PATH = ROOT / "examples" / "unreal" / "FastDisOrientationVerification" / "FastDisOrientationVerification.uproject"
DEFAULT_BINARIES = ("UnrealEditor-Cmd", "UE5Editor-Cmd", "UE4Editor-Cmd")


def resolve_unreal(explicit: str | None) -> str | None:
    if explicit:
        return explicit
    for candidate in DEFAULT_BINARIES:
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    return None


def build_command(unreal_binary: str) -> list[str]:
    return [
        unreal_binary,
        str(PROJECT_PATH),
        '-ExecCmds=Automation RunTests FastDis.Orientation; Quit',
        "-unattended",
        "-nop4",
        "-nosplash",
    ]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--unreal", help="Explicit UnrealEditor-Cmd executable path")
    parser.add_argument("--dry-run", action="store_true", help="Print the command without executing it")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    sync_orientation_fixtures.write_fixture_copy(sync_orientation_fixtures.DESTINATIONS["unreal"])
    unreal_binary = resolve_unreal(args.unreal)
    if unreal_binary is None:
        if args.dry_run:
            unreal_binary = DEFAULT_BINARIES[0]
        else:
            raise SystemExit("Could not find an UnrealEditor-Cmd executable on PATH")
    command = build_command(unreal_binary)
    print(" ".join(command))
    if args.dry_run:
        return 0
    completed = subprocess.run(command, cwd=ROOT)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
