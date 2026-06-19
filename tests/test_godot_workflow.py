from __future__ import annotations

import argparse
import sys
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import godot_env
import godot_workflow


def test_windows_wrapper_names() -> None:
    assert godot_env.wrapper_names("windows") == [
        "fastdis_gdextension.windows.template_debug.x86_64.dll",
        "fastdis_gdextension.windows.template_release.x86_64.dll",
    ]


def test_windows_shared_library_names() -> None:
    assert godot_env.shared_library_names("windows") == ["fastdis.dll"]


def test_build_command_defaults() -> None:
    args = argparse.Namespace(skip_native_build=False)
    recorded: list[list[str]] = []

    def fake_run_step(cmd: list[str]) -> int:
        recorded.append(cmd)
        return 0

    original = godot_workflow.run_step
    godot_workflow.run_step = fake_run_step
    try:
        assert godot_workflow.command_build(args) == 0
    finally:
        godot_workflow.run_step = original

    assert recorded == [["python3", "tools/build_godot_extension.py"]]


def test_verify_command_forwards_flags() -> None:
    args = argparse.Namespace(dry_run=True, skip_build=True)
    recorded: list[list[str]] = []

    def fake_run_step(cmd: list[str]) -> int:
        recorded.append(cmd)
        return 0

    original = godot_workflow.run_step
    godot_workflow.run_step = fake_run_step
    try:
        assert godot_workflow.command_verify(args) == 0
    finally:
        godot_workflow.run_step = original

    assert recorded == [["python3", "tools/run_godot_orientation_verification.py", "--dry-run", "--skip-build"]]
