#!/usr/bin/env python3
"""Verify the Godot demo reports a clear error when the host fastdis library is missing."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from pathlib import Path
import shutil
import subprocess

import build_godot_extension
import godot_env
import load_local_env


ROOT = Path(__file__).resolve().parents[1]
ALIAS_ROOT = godot_env.repo_alias_root(ROOT)
PROJECT_DIR = ROOT / "examples" / "godot" / "fastdis_demo"
ALIAS_PROJECT_DIR = ALIAS_ROOT / "examples" / "godot" / "fastdis_demo"
ALIAS_SCRIPT_PATH = ALIAS_PROJECT_DIR / "scripts" / "run_missing_library_check.gd"
ADDON_BIN_DIR = PROJECT_DIR / "addons" / "fastdis" / "bin"
HIDDEN_LIB_DIR = godot_env.DEFAULT_WORK_ROOT / "hidden_libs"


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


def shared_library_candidates() -> list[Path]:
    return [ADDON_BIN_DIR / name for name in godot_env.shared_library_names()]


def staged_build_complete() -> bool:
    return (
        all(path.is_file() for path in wrapper_candidates())
        and any(path.is_file() for path in shared_library_candidates())
        and build_godot_extension.manifest_is_current(ADDON_BIN_DIR)
    )


@contextmanager
def temporarily_hide_shared_libraries() -> None:
    present = [path for path in shared_library_candidates() if path.is_file()]
    if not present:
        raise SystemExit(
            "Could not find any staged host fastdis shared libraries under "
            f"{ADDON_BIN_DIR}. Run `python tools/godot_workflow.py build` first."
        )

    HIDDEN_LIB_DIR.mkdir(parents=True, exist_ok=True)
    hidden_paths: list[tuple[Path, Path]] = []
    try:
        for source in present:
            target = HIDDEN_LIB_DIR / source.name
            if target.exists():
                target.unlink()
            shutil.move(str(source), str(target))
            hidden_paths.append((source, target))
        yield
    finally:
        for destination, source in reversed(hidden_paths):
            if source.exists():
                shutil.move(str(source), str(destination))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--godot", help="Explicit godot executable path")
    parser.add_argument("--skip-build", action="store_true", help="Do not rebuild/stage before running")
    parser.add_argument("--dry-run", action="store_true", help="Print the command without executing it")
    return parser.parse_args()


def main() -> int:
    load_local_env.load()
    args = parse_args()
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
    if not all(path.is_file() for path in wrappers) and not args.dry_run:
        names = ", ".join(path.name for path in wrappers)
        raise SystemExit(
            "Godot is installed, but the FastDIS GDExtension wrapper set is incomplete or stale. "
            f"Expected one of: {names} under {ADDON_BIN_DIR}. "
            "Run `python tools/godot_workflow.py build` first."
        )

    command = build_command(godot_binary)
    print(" ".join(command))
    if args.dry_run:
        return 0

    with temporarily_hide_shared_libraries():
        completed = subprocess.run(command, cwd=ALIAS_ROOT, env=godot_env.build_env())
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
