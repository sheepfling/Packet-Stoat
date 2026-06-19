#!/usr/bin/env python3
"""Run the Unreal orientation verification automation harness."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
from pathlib import Path

import load_local_env
import sync_orientation_fixtures


ROOT = Path(__file__).resolve().parents[1]
PROJECT_PATH = ROOT / "examples" / "unreal" / "FastDisOrientationVerification" / "FastDisOrientationVerification.uproject"
DEFAULT_BINARIES = ("UnrealEditor-Cmd", "UnrealEditor", "UE5Editor-Cmd", "UE5Editor", "UE4Editor-Cmd", "UE4Editor")


def resolve_unreal(explicit: str | None) -> str | None:
    if explicit:
        return explicit
    for env_name in ("FASTDIS_UNREAL_EDITOR_CMD", "FASTDIS_UNREAL_EDITOR"):
        candidate = os.environ.get(env_name)
        if not candidate:
            continue
        path = Path(candidate).expanduser()
        if path.is_file():
            return str(path)
    for candidate in DEFAULT_BINARIES:
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    engine_dir = os.environ.get("FASTDIS_UNREAL_ENGINE_DIR") or os.environ.get("UNREAL_ENGINE_DIR") or os.environ.get("UE_ROOT")
    if engine_dir:
        root = Path(engine_dir).expanduser()
        for name in ("UnrealEditor-Cmd", "UnrealEditor", "UE5Editor-Cmd", "UE5Editor"):
            candidate = root / "Engine" / "Binaries" / "Mac" / name
            if candidate.is_file():
                return str(candidate)
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
    load_local_env.load()
    args = parse_args()
    sync_orientation_fixtures.write_fixture_copy(sync_orientation_fixtures.DESTINATIONS["unreal"])
    unreal_binary = resolve_unreal(args.unreal)
    if unreal_binary is None:
        if args.dry_run:
            unreal_binary = DEFAULT_BINARIES[0]
        else:
            raise SystemExit("Could not find an Unreal editor executable on PATH or in repo-local .env settings")
    command = build_command(unreal_binary)
    print(" ".join(command))
    if args.dry_run:
        return 0
    completed = subprocess.run(command, cwd=ROOT)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
