#!/usr/bin/env python3
"""Generate source-backed Unreal Fab demo assets through Unreal Editor Python."""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess

import load_local_env
import run_unreal_orientation_verification as unreal_harness
import unreal_env


ROOT = Path(__file__).resolve().parents[1]
PROJECT_PATH = unreal_harness.PROJECT_PATH
ALIAS_ROOT = unreal_harness.ALIAS_ROOT
ALIAS_PROJECT_PATH = unreal_harness.ALIAS_PROJECT_PATH
SCRIPT_PATH = ROOT / "tools" / "unreal" / "create_fab_demo_assets.py"
ALIAS_SCRIPT_PATH = unreal_env.alias_repo_path(SCRIPT_PATH)
LOG_DIR = unreal_env.DEFAULT_WORK_ROOT / "logs" / "fab_assets"
LOG_PATH = LOG_DIR / "CreateFastDisFabDemoAssets.log"
GENERATED_DEMO_MAP = ROOT / "packages" / "unreal" / "FastDis" / "Content" / "Examples" / "FastDis_Demo.umap"
GENERATED_MAPPING_ASSET = ROOT / "packages" / "unreal" / "FastDis" / "Content" / "Examples" / "DA_FastDisEntityMappings.uasset"
GENERATED_DEMO_CONTROLLER_BP = ROOT / "packages" / "unreal" / "FastDis" / "Content" / "Examples" / "BP_FastDisDemoController.uasset"
GENERATED_STATUS_WIDGET_BP = ROOT / "packages" / "unreal" / "FastDis" / "Content" / "Examples" / "WBP_FastDisRuntimeStatus.uasset"
SUCCESS_MARKER = "FASTDIS_FAB_ASSET_GEN complete"
GENERATED_ASSETS = (
    GENERATED_DEMO_MAP,
    GENERATED_MAPPING_ASSET,
    GENERATED_DEMO_CONTROLLER_BP,
    GENERATED_STATUS_WIDGET_BP,
)


def resolve_unreal(explicit: str | None, engine_version: str | None) -> str | None:
    path = unreal_env.resolve_editor(engine_version, explicit)
    return str(path) if path else None


def build_command(unreal_binary: str) -> list[str]:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    if LOG_PATH.exists():
        LOG_PATH.unlink()
    return [
        unreal_binary,
        str(ALIAS_PROJECT_PATH),
        f"-ExecutePythonScript={ALIAS_SCRIPT_PATH}",
        "-unattended",
        "-nop4",
        "-nosplash",
        "-NullRHI",
        "-NoSound",
        "-stdout",
        "-FullStdOutLogOutput",
        f"-abslog={LOG_PATH}",
    ]


def unreal_python_log_failed(log_path: Path) -> bool:
    if not log_path.exists():
        return False
    text = log_path.read_text(encoding="utf-8", errors="replace")
    return "Traceback (most recent call last)" in text or "Python script executed with errors" in text


def unreal_python_log_succeeded(log_path: Path) -> bool:
    if not log_path.exists():
        return False
    text = log_path.read_text(encoding="utf-8", errors="replace")
    return SUCCESS_MARKER in text


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--unreal", help="Explicit UnrealEditor-Cmd executable path")
    parser.add_argument("--engine-version", help="Versioned Unreal env selector, for example 5.7 or 5.8")
    parser.add_argument("--dry-run", action="store_true", help="Print the editor command without executing it")
    parser.add_argument("--skip-build", action="store_true", help="Skip plugin staging and harness build before launching Unreal")
    return parser.parse_args()


def main() -> int:
    load_local_env.load()
    args = parse_args()

    if not args.dry_run and not args.skip_build:
        unreal_harness.ensure_runtime_plugin(args.engine_version)
        unreal_harness.ensure_harness_built(args.engine_version)
    if not args.dry_run:
        for generated_asset in GENERATED_ASSETS:
            if generated_asset.exists():
                generated_asset.unlink()

    unreal_binary = resolve_unreal(args.unreal, args.engine_version)
    if unreal_binary is None:
        if args.dry_run:
            unreal_binary = unreal_env.DEFAULT_BINARIES[0]
        else:
            raise SystemExit("Could not find an Unreal editor executable")

    command = build_command(unreal_binary)
    if args.dry_run:
        print(f"# script: {SCRIPT_PATH.relative_to(ROOT).as_posix()}")
    print(" ".join(command))
    if args.dry_run:
        return 0

    completed = subprocess.run(command, cwd=ALIAS_ROOT, env=unreal_env.build_env())
    if unreal_python_log_failed(LOG_PATH):
        print(f"Unreal Python asset generation reported errors; see {LOG_PATH}")
        return 1
    if all(path.exists() for path in GENERATED_ASSETS) and unreal_python_log_succeeded(LOG_PATH):
        return 0
    if completed.returncode != 0:
        return completed.returncode
    print(
        "Unreal Python asset generation did not produce all expected assets: "
        f"{', '.join(str(path) for path in GENERATED_ASSETS)}; see {LOG_PATH}"
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
