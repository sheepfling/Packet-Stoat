#!/usr/bin/env python3
"""Run the Unreal orientation verification automation harness."""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import subprocess

import load_local_env
import sync_orientation_fixtures
import unreal_env


ROOT = Path(__file__).resolve().parents[1]
PROJECT_PATH = ROOT / "examples" / "unreal" / "FastDisOrientationVerification" / "FastDisOrientationVerification.uproject"
PLUGIN_SOURCE_DIR = ROOT / "examples" / "unreal" / "FastDis"
HARNESS_PLUGINS_DIR = ROOT / "examples" / "unreal" / "FastDisOrientationVerification" / "Plugins"
HARNESS_PLUGIN_DIR = HARNESS_PLUGINS_DIR / "FastDis"
HARNESS_LOG_DIR = ROOT / "examples" / "unreal" / "FastDisOrientationVerification" / "Saved" / "Logs"
HARNESS_LOG_PATH = HARNESS_LOG_DIR / "FastDisOrientationVerification.log"
DEFAULT_BINARIES = unreal_env.DEFAULT_BINARIES


def resolve_unreal(explicit: str | None, engine_version: str | None) -> str | None:
    path = unreal_env.resolve_editor(engine_version, explicit)
    if path is None:
        return None
    return str(path)


def build_command(unreal_binary: str) -> list[str]:
    return [
        unreal_binary,
        str(PROJECT_PATH),
        '-ExecCmds=Automation RunTests FastDis.Orientation; Quit',
        "-unattended",
        "-nop4",
        "-nosplash",
        "-NullRHI",
        "-NoSound",
        "-stdout",
        "-FullStdOutLogOutput",
        f"-abslog={HARNESS_LOG_PATH}",
    ]


def ensure_runtime_plugin(engine_version: str | None) -> None:
    if not (PLUGIN_SOURCE_DIR / "FastDis.uplugin").is_file():
        raise SystemExit(f"Could not find FastDis.uplugin under {PLUGIN_SOURCE_DIR}")

    cmd = [
        "python3",
        str(ROOT / "tools" / "build_unreal_plugin.py"),
        "--skip-package",
        "--target-platforms",
        "Mac",
    ]
    if engine_version:
        cmd.extend(["--engine-version", engine_version])
    subprocess.run(cmd, cwd=ROOT, check=True)

    HARNESS_PLUGINS_DIR.mkdir(parents=True, exist_ok=True)
    if HARNESS_PLUGIN_DIR.exists() or HARNESS_PLUGIN_DIR.is_symlink():
        if HARNESS_PLUGIN_DIR.is_symlink() or HARNESS_PLUGIN_DIR.is_file():
            HARNESS_PLUGIN_DIR.unlink()
        else:
            shutil.rmtree(HARNESS_PLUGIN_DIR)

    try:
        HARNESS_PLUGIN_DIR.symlink_to(PLUGIN_SOURCE_DIR, target_is_directory=True)
    except OSError:
        shutil.copytree(PLUGIN_SOURCE_DIR, HARNESS_PLUGIN_DIR)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--unreal", help="Explicit UnrealEditor-Cmd executable path")
    parser.add_argument("--engine-version", help="Versioned Unreal env selector, for example 5.7 or 5.8")
    parser.add_argument("--dry-run", action="store_true", help="Print the command without executing it")
    return parser.parse_args()


def main() -> int:
    load_local_env.load()
    args = parse_args()
    sync_orientation_fixtures.write_fixture_copy(sync_orientation_fixtures.DESTINATIONS["unreal"])
    if not args.dry_run:
        ensure_runtime_plugin(args.engine_version)
    unreal_binary = resolve_unreal(args.unreal, args.engine_version)
    if unreal_binary is None:
        if args.dry_run:
            unreal_binary = DEFAULT_BINARIES[0]
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
    completed = subprocess.run(command, cwd=ROOT)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
