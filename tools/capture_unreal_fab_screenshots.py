#!/usr/bin/env python3
"""Capture the required Unreal Fab screenshots from the generated demo map."""

from __future__ import annotations

import argparse
from pathlib import Path
import struct
import subprocess

import load_local_env
import run_unreal_orientation_verification as unreal_harness
import unreal_env


ROOT = Path(__file__).resolve().parents[1]
ALIAS_ROOT = unreal_harness.ALIAS_ROOT
ALIAS_PROJECT_PATH = unreal_harness.ALIAS_PROJECT_PATH
SCRIPT_PATH = ROOT / "tools" / "unreal" / "capture_fab_demo_screenshots.py"
ALIAS_SCRIPT_PATH = unreal_env.alias_repo_path(SCRIPT_PATH)
LOG_DIR = unreal_env.DEFAULT_WORK_ROOT / "logs" / "fab_screenshots"
LOG_PATH = LOG_DIR / "CaptureFastDisFabScreenshots.log"
SCREENSHOT_DIR = ROOT / "packages" / "unreal" / "FastDis" / "Content" / "Examples" / "Screenshots"
CAPTURES = (
    "live_udp_status",
    "entity_spawn",
    "pdu_event_marker",
    "setup_view",
)
SCREENSHOTS = tuple(SCREENSHOT_DIR / f"{capture}.png" for capture in CAPTURES)


def resolve_unreal(explicit: str | None, engine_version: str | None) -> str | None:
    path = unreal_env.resolve_editor(engine_version, explicit)
    return str(path) if path else None


def log_path_for_capture(capture_name: str | None) -> Path:
    return LOG_PATH if capture_name is None else LOG_DIR / f"CaptureFastDisFabScreenshots_{capture_name}.log"


def build_command(unreal_binary: str, capture_name: str | None = None) -> list[str]:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = log_path_for_capture(capture_name)
    if log_path.exists():
        log_path.unlink()
    return [
        unreal_binary,
        str(ALIAS_PROJECT_PATH),
        f"-ExecutePythonScript={ALIAS_SCRIPT_PATH}",
        "-unattended",
        "-nop4",
        "-nosplash",
        "-RenderOffscreen",
        "-NoSound",
        "-stdout",
        "-FullStdOutLogOutput",
        f"-abslog={log_path}",
    ]


def unreal_python_log_failed(log_path: Path) -> bool:
    if not log_path.exists():
        return False
    text = log_path.read_text(encoding="utf-8", errors="replace")
    return "Traceback (most recent call last)" in text or "Python script executed with errors" in text


def unreal_python_log_captured(log_path: Path, screenshot: Path) -> bool:
    if not log_path.exists():
        return False
    text = log_path.read_text(encoding="utf-8", errors="replace")
    return "FASTDIS_FAB_SCREENSHOT captured" in text and screenshot.name in text


def png_dimensions(path: Path) -> tuple[int, int]:
    with path.open("rb") as handle:
        header = handle.read(24)
    if len(header) < 24 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        raise ValueError(f"{path} is not a PNG file")
    width, height = struct.unpack(">II", header[16:24])
    return width, height


def screenshots_are_valid() -> bool:
    for screenshot in SCREENSHOTS:
        if not screenshot.exists() or screenshot.stat().st_size <= 0:
            return False
        width, height = png_dimensions(screenshot)
        if width <= 0 or height <= 0:
            return False
    return True


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
        SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
        for screenshot in SCREENSHOTS:
            if screenshot.exists():
                screenshot.unlink()

    unreal_binary = resolve_unreal(args.unreal, args.engine_version)
    if unreal_binary is None:
        if args.dry_run:
            unreal_binary = unreal_env.DEFAULT_BINARIES[0]
        else:
            raise SystemExit("Could not find an Unreal editor executable")

    command = build_command(unreal_binary)
    print(" ".join(command))
    if args.dry_run:
        return 0

    base_env = unreal_env.build_env()
    for capture_name, screenshot in zip(CAPTURES, SCREENSHOTS, strict=True):
        capture_command = build_command(unreal_binary, capture_name)
        log_path = log_path_for_capture(capture_name)
        env = dict(base_env)
        env["FASTDIS_FAB_CAPTURE_NAME"] = capture_name
        print(" ".join(capture_command))
        completed = subprocess.run(capture_command, cwd=ALIAS_ROOT, env=env)
        if unreal_python_log_failed(log_path):
            print(f"Unreal Python screenshot capture reported errors; see {log_path}")
            return 1
        if not unreal_python_log_captured(log_path, screenshot):
            print(f"Unreal screenshot capture was not completed for {screenshot}; see {log_path}")
            if completed.returncode != 0:
                return completed.returncode
            return 1
        try:
            width, height = png_dimensions(screenshot)
        except (OSError, ValueError) as exc:
            print(f"Unreal screenshot capture wrote an invalid PNG for {screenshot}: {exc}")
            return completed.returncode if completed.returncode != 0 else 1
        if width <= 0 or height <= 0:
            print(f"Unreal screenshot capture wrote an invalid PNG size for {screenshot}: {width}x{height}")
            return completed.returncode if completed.returncode != 0 else 1

    if screenshots_are_valid():
        return 0
    print(f"Unreal screenshot capture did not produce all expected screenshots; see {LOG_DIR}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
