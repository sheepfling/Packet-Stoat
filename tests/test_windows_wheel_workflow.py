from __future__ import annotations

import argparse
import sys
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import windows_wheel_workflow


def test_doctor_payload_marks_missing_tools(monkeypatch) -> None:
    monkeypatch.setattr(windows_wheel_workflow.shutil, "which", lambda name: None)
    monkeypatch.setattr(windows_wheel_workflow, "current_windows_dll", lambda path: None)
    monkeypatch.setattr(windows_wheel_workflow, "current_wheel", lambda path: None)

    payload = windows_wheel_workflow.doctor_payload("x86_64-w64-mingw32")

    assert payload["status"] == "missing-prereqs"
    assert any(check["name"] == "cmake" and check["status"] == "fail" for check in payload["checks"])
    assert any(check["name"] == "backend policy" and "Docker is not treated" in check["detail"] for check in payload["checks"])


def test_build_dll_command_forwards_args() -> None:
    args = argparse.Namespace(
        build_dir="build-mingw-win64",
        config="Release",
        mingw_prefix="x86_64-w64-mingw32",
        toolchain_file="toolchain.cmake",
        clean=True,
    )
    recorded: list[list[str]] = []

    def fake_run_step(cmd: list[str]) -> int:
        recorded.append(cmd)
        return 0

    original = windows_wheel_workflow.run_step
    windows_wheel_workflow.run_step = fake_run_step
    try:
        assert windows_wheel_workflow.command_build_dll(args) == 0
    finally:
        windows_wheel_workflow.run_step = original

    assert recorded == [[
        sys.executable,
        "tools/build_windows_dll.py",
        "--build-dir",
        "build-mingw-win64",
        "--config",
        "Release",
        "--mingw-prefix",
        "x86_64-w64-mingw32",
        "--toolchain-file",
        "toolchain.cmake",
        "--clean",
    ]]


def test_build_wheel_requires_existing_dll(tmp_path: Path) -> None:
    args = argparse.Namespace(
        build_dir=str(tmp_path / "build"),
        outdir="dist",
        plat_name="win_amd64",
        python_tag="py3",
        abi_tag="none",
        no_isolation=False,
    )
    assert windows_wheel_workflow.command_build_wheel(args) == 2


def test_build_wheel_forwards_flags(monkeypatch, tmp_path: Path) -> None:
    dll = tmp_path / "libfastdis.dll"
    dll.write_bytes(b"dll")
    monkeypatch.setattr(windows_wheel_workflow, "current_windows_dll", lambda path: dll)
    recorded: list[list[str]] = []

    def fake_run_step(cmd: list[str]) -> int:
        recorded.append(cmd)
        return 0

    original = windows_wheel_workflow.run_step
    windows_wheel_workflow.run_step = fake_run_step
    try:
        args = argparse.Namespace(
            build_dir=str(tmp_path),
            outdir="dist",
            plat_name="win_amd64",
            python_tag="py3",
            abi_tag="none",
            no_isolation=True,
        )
        assert windows_wheel_workflow.command_build_wheel(args) == 0
    finally:
        windows_wheel_workflow.run_step = original

    assert recorded == [[
        sys.executable,
        "tools/build_ctypes_wheel.py",
        "--native-lib",
        str(dll),
        "--plat-name",
        "win_amd64",
        "--outdir",
        "dist",
        "--python-tag",
        "py3",
        "--abi-tag",
        "none",
        "--no-isolation",
    ]]
