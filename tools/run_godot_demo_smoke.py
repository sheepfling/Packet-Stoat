#!/usr/bin/env python3
"""Run a headless Godot smoke test against the FastDIS demo scene."""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess

import godot_env
import load_local_env


ROOT = Path(__file__).resolve().parents[1]
ALIAS_ROOT = godot_env.repo_alias_root(ROOT)
PROJECT_DIR = ROOT / "examples" / "godot" / "fastdis_demo"
ALIAS_PROJECT_DIR = ALIAS_ROOT / "examples" / "godot" / "fastdis_demo"
ALIAS_SCRIPT_PATH = ALIAS_PROJECT_DIR / "scripts" / "run_demo_smoke.gd"
REPLAY_PATH = ROOT / "examples" / "godot" / "fastdis_demo" / "data" / "synthetic.fastdispkt"
ADDON_BIN_DIR = PROJECT_DIR / "addons" / "fastdis" / "bin"


def build_command(godot_binary: str) -> list[str]:
    return [
        godot_binary,
        "--headless",
        "--path",
        str(ALIAS_PROJECT_DIR),
        "--script",
        str(ALIAS_SCRIPT_PATH),
    ]


def wrapper_candidates() -> list[Path]:
    return [ADDON_BIN_DIR / name for name in godot_env.wrapper_names()]


def generate_replay(packet_count: int, entity_count: int) -> None:
    cmd = godot_env.python_command() + [
        str(ROOT / "tools" / "make_replay.py"),
        str(REPLAY_PATH),
        "--packets",
        str(packet_count),
        "--entities",
        str(entity_count),
    ]
    subprocess.run(cmd, cwd=ROOT, check=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--godot", help="Explicit godot executable path")
    parser.add_argument("--skip-build", action="store_true", help="Do not rebuild/stage the Godot extension before running")
    parser.add_argument("--dry-run", action="store_true", help="Print the command without executing it")
    parser.add_argument("--replay-packets", type=int, default=24, help="Synthetic replay packet count")
    parser.add_argument("--replay-entities", type=int, default=3, help="Synthetic replay entity count")
    return parser.parse_args()


def main() -> int:
    load_local_env.load()
    args = parse_args()
    if not args.dry_run and not args.skip_build:
        subprocess.run(godot_env.python_command() + [str(ROOT / "tools" / "build_godot_extension.py")], cwd=ROOT, check=True)
    if not args.dry_run:
        generate_replay(args.replay_packets, args.replay_entities)

    godot_binary = godot_env.resolve_godot(args.godot)
    if godot_binary is None:
        if args.dry_run:
            godot_binary = "godot"
        else:
            raise SystemExit("Could not find a godot executable on PATH or in FASTDIS_GODOT")

    wrappers = wrapper_candidates()
    if not any(path.is_file() for path in wrappers) and not args.dry_run:
        names = ", ".join(path.name for path in wrappers)
        raise SystemExit(
            "Godot is installed, but the FastDIS GDExtension wrapper is missing. "
            f"Expected one of: {names} under {ADDON_BIN_DIR}. "
            "Run `python tools/godot_workflow.py build` first."
        )

    command = build_command(godot_binary)
    print(" ".join(command))
    if args.dry_run:
        return 0
    completed = subprocess.run(command, cwd=ALIAS_ROOT, env=godot_env.build_env())
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
