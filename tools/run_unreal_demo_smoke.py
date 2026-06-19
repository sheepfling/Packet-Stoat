#!/usr/bin/env python3
"""Run the Unreal replay/demo smoke automation harness."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import tempfile

import load_local_env
import run_unreal_orientation_verification as unreal_harness
import unreal_env


ROOT = Path(__file__).resolve().parents[1]
PROJECT_PATH = unreal_harness.PROJECT_PATH
HARNESS_LOG_DIR = unreal_harness.HARNESS_LOG_DIR
HARNESS_LOG_PATH = HARNESS_LOG_DIR / "FastDisDemoSmoke.log"
DEFAULT_UNREAL_WORK_ROOT = Path(tempfile.gettempdir()).resolve() / "fastdis_unreal"
DEFAULT_REPLAY_PATH = DEFAULT_UNREAL_WORK_ROOT / "FastDisDemoSmoke" / "synthetic.fastdispkt"


def resolve_unreal(explicit: str | None, engine_version: str | None) -> str | None:
    return unreal_harness.resolve_unreal(explicit, engine_version)


def build_command(unreal_binary: str) -> list[str]:
    return [
        unreal_binary,
        str(PROJECT_PATH),
        '-ExecCmds=Automation RunTests FastDis.Demo; Quit',
        "-unattended",
        "-nop4",
        "-nosplash",
        "-NullRHI",
        "-NoSound",
        "-stdout",
        "-FullStdOutLogOutput",
        f"-abslog={HARNESS_LOG_PATH}",
    ]


def generate_replay(replay_path: Path, packet_count: int, entity_count: int) -> None:
    replay_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = unreal_env.python_command() + [
        str(ROOT / "tools" / "make_replay.py"),
        str(replay_path),
        "--packets",
        str(packet_count),
        "--entities",
        str(entity_count),
    ]
    subprocess.run(cmd, cwd=ROOT, check=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--unreal", help="Explicit UnrealEditor executable path")
    parser.add_argument("--engine-version", help="Versioned Unreal env selector, for example 5.7 or 5.8")
    parser.add_argument("--dry-run", action="store_true", help="Print the editor command without executing it")
    parser.add_argument("--replay-packets", type=int, default=24, help="Synthetic replay packet count")
    parser.add_argument("--replay-entities", type=int, default=3, help="Synthetic replay entity count")
    parser.add_argument("--replay-path", default=str(DEFAULT_REPLAY_PATH), help="Absolute scratch replay path for the demo harness")
    return parser.parse_args()


def main() -> int:
    load_local_env.load()
    args = parse_args()
    replay_path = Path(args.replay_path).expanduser().resolve()

    if not args.dry_run:
        unreal_harness.ensure_runtime_plugin(args.engine_version)
        unreal_harness.ensure_harness_built(args.engine_version)
        generate_replay(replay_path, args.replay_packets, args.replay_entities)

    unreal_binary = resolve_unreal(args.unreal, args.engine_version)
    if unreal_binary is None:
        if args.dry_run:
            unreal_binary = unreal_env.DEFAULT_BINARIES[0]
        else:
            if args.engine_version:
                raise SystemExit(
                    f"Could not find an Unreal editor executable for version {args.engine_version} "
                    "on PATH or in repo-local .env settings"
                )
            raise SystemExit("Could not find an Unreal editor executable on PATH or in repo-local .env settings")

    command = build_command(unreal_binary)
    print(" ".join(command))
    if args.dry_run:
        return 0

    env = dict(os.environ)
    env["FASTDIS_UNREAL_REPLAY_FILE"] = str(replay_path)
    completed = subprocess.run(command, cwd=ROOT, env=env)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
