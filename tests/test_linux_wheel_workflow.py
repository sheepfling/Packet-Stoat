from __future__ import annotations

import argparse
import sys
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import linux_wheel_workflow


def test_doctor_payload_marks_missing_backends(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(linux_wheel_workflow.shutil, "which", lambda name: None)
    monkeypatch.setattr(linux_wheel_workflow, "current_linux_shared_library", lambda path: None)
    monkeypatch.setattr(linux_wheel_workflow, "current_wheel", lambda path: None)

    payload = linux_wheel_workflow.doctor_payload(tmp_path / "linux-zig.cmake", "ubuntu:24.04")

    assert payload["status"] == "missing-prereqs"
    assert any(check["name"] == "backend policy" and check["status"] == "fail" for check in payload["checks"])
    assert any(check["name"] == "direct backend" and "zig=missing" in check["detail"] for check in payload["checks"])


def test_build_lib_command_forwards_args() -> None:
    args = argparse.Namespace(
        build_dir="build/cmake/linux-x86_64",
        config="Release",
        backend="docker",
        toolchain_file="toolchain.cmake",
        generator="Ninja",
        image="ubuntu:24.04",
        clean=True,
        target="fastdis_shared",
    )
    recorded: list[list[str]] = []

    def fake_run_step(cmd: list[str]) -> int:
        recorded.append(cmd)
        return 0

    original = linux_wheel_workflow.run_step
    linux_wheel_workflow.run_step = fake_run_step
    try:
        assert linux_wheel_workflow.command_build_lib(args) == 0
    finally:
        linux_wheel_workflow.run_step = original

    assert recorded == [[
        sys.executable,
        "tools/build_linux_ctypes_wheel.py",
        "--build-dir",
        "build/cmake/linux-x86_64",
        "--config",
        "Release",
        "--backend",
        "docker",
        "--toolchain-file",
        "toolchain.cmake",
        "--image",
        "ubuntu:24.04",
        "--target",
        "fastdis_shared",
        "--generator",
        "Ninja",
        "--clean",
    ]]


def test_build_wheel_requires_existing_lib(tmp_path: Path) -> None:
    args = argparse.Namespace(
        build_dir=str(tmp_path / "build"),
        backend="direct",
        toolchain_file="toolchain.cmake",
        image="ubuntu:24.04",
        outdir="dist",
        plat_name="linux_x86_64",
        python_tag="py3",
        abi_tag="none",
        no_isolation=False,
    )
    assert linux_wheel_workflow.command_build_wheel(args) == 2


def test_build_wheel_forwards_direct_flags(monkeypatch, tmp_path: Path) -> None:
    lib = tmp_path / "libfastdis.so"
    lib.write_bytes(b"linux")
    monkeypatch.setattr(linux_wheel_workflow, "current_linux_shared_library", lambda path: lib)
    recorded: list[list[str]] = []

    def fake_run_step(cmd: list[str]) -> int:
        recorded.append(cmd)
        return 0

    original = linux_wheel_workflow.run_step
    linux_wheel_workflow.run_step = fake_run_step
    try:
        args = argparse.Namespace(
            build_dir=str(tmp_path),
            backend="direct",
            toolchain_file="toolchain.cmake",
            image="ubuntu:24.04",
            outdir="dist",
            plat_name="linux_x86_64",
            python_tag="py3",
            abi_tag="none",
            no_isolation=True,
        )
        assert linux_wheel_workflow.command_build_wheel(args) == 0
    finally:
        linux_wheel_workflow.run_step = original

    assert recorded == [[
        sys.executable,
        "tools/build_ctypes_wheel.py",
        "--native-lib",
        str(lib),
        "--plat-name",
        "linux_x86_64",
        "--outdir",
        "dist",
        "--python-tag",
        "py3",
        "--abi-tag",
        "none",
        "--no-isolation",
    ]]


def test_build_wheel_forwards_docker_flags(monkeypatch, tmp_path: Path) -> None:
    lib = tmp_path / "libfastdis.so"
    lib.write_bytes(b"linux")
    monkeypatch.setattr(linux_wheel_workflow, "current_linux_shared_library", lambda path: lib)
    recorded: list[list[str]] = []

    def fake_run_step(cmd: list[str]) -> int:
        recorded.append(cmd)
        return 0

    original = linux_wheel_workflow.run_step
    linux_wheel_workflow.run_step = fake_run_step
    try:
        args = argparse.Namespace(
            build_dir=str(tmp_path),
            backend="docker",
            toolchain_file="toolchain.cmake",
            image="ubuntu:24.04",
            outdir="dist",
            plat_name="linux_x86_64",
            python_tag="py3",
            abi_tag="none",
            no_isolation=True,
        )
        assert linux_wheel_workflow.command_build_wheel(args) == 0
    finally:
        linux_wheel_workflow.run_step = original

    assert recorded == [[
        sys.executable,
        "tools/build_linux_ctypes_wheel.py",
        "--build-dir",
        str(tmp_path),
        "--backend",
        "docker",
        "--image",
        "ubuntu:24.04",
        "--outdir",
        "dist",
        "--plat-name",
        "linux_x86_64",
        "--python-tag",
        "py3",
        "--abi-tag",
        "none",
        "--no-isolation",
    ]]
