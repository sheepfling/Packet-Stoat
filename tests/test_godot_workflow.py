from __future__ import annotations

import argparse
import sys
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import build_godot_extension
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

    assert recorded == [[sys.executable, "tools/build_godot_extension.py"]]


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

    assert recorded == [[sys.executable, "tools/run_godot_orientation_verification.py", "--dry-run", "--skip-build"]]


def test_demo_command_forwards_flags() -> None:
    args = argparse.Namespace(dry_run=True, skip_build=True)
    recorded: list[list[str]] = []

    def fake_run_step(cmd: list[str]) -> int:
        recorded.append(cmd)
        return 0

    original = godot_workflow.run_step
    godot_workflow.run_step = fake_run_step
    try:
        assert godot_workflow.command_demo(args) == 0
    finally:
        godot_workflow.run_step = original

    assert recorded == [[sys.executable, "tools/run_godot_demo_smoke.py", "--dry-run", "--skip-build"]]


def test_python_command_prefers_current_interpreter() -> None:
    assert godot_env.python_command() == [sys.executable]


def test_windows_scons_candidates_include_current_python_scripts() -> None:
    original = godot_env.platform.system
    try:
        godot_env.platform.system = lambda: "Windows"
        candidates = godot_env.default_scons_candidates()
    finally:
        godot_env.platform.system = original

    executable_dir = Path(sys.executable).resolve().parent
    assert str(executable_dir / "scons.exe") in candidates
    assert str(executable_dir / "Scripts" / "scons.exe") in candidates


def test_prune_host_artifacts_removes_stale_fastdis_binaries(tmp_path: Path) -> None:
    good = tmp_path / "libfastdis.dylib"
    stale_shared = tmp_path / "libfastdis 2.dylib"
    stale_wrapper = tmp_path / "libfastdis_gdextension.macos.template_debug 2.dylib"
    unrelated = tmp_path / "README.txt"
    for path in (good, stale_shared, stale_wrapper, unrelated):
        path.write_text("x", encoding="utf-8")

    build_godot_extension.prune_host_artifacts(tmp_path, {"libfastdis.dylib"})

    assert good.exists()
    assert unrelated.exists()
    assert not stale_shared.exists()
    assert not stale_wrapper.exists()
