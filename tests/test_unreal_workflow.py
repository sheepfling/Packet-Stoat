from __future__ import annotations

import sys
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import unreal_workflow


def test_doctor_payload_reports_missing_install() -> None:
    payload = unreal_workflow.doctor_payload("9.9")

    assert payload["status"] == "missing-install"
    assert payload["checks"][0]["status"] == "fail"
    assert "no Unreal install discovered" in payload["checks"][0]["detail"]


def test_build_command_defaults_to_clean_package() -> None:
    args = unreal_workflow.parse_args.__globals__["argparse"].Namespace(
        engine_version="5.8",
        open_rider=False,
        no_clean_package=False,
    )

    recorded: list[list[str]] = []

    def fake_run_step(cmd: list[str]) -> int:
        recorded.append(cmd)
        return 0

    original = unreal_workflow.run_step
    unreal_workflow.run_step = fake_run_step
    try:
        assert unreal_workflow.command_build(args) == 0
    finally:
        unreal_workflow.run_step = original

    assert recorded == [[sys.executable, "tools/build_unreal_plugin.py", "--engine-version", "5.8", "--clean-package"]]


def test_verify_command_forwards_dry_run() -> None:
    args = unreal_workflow.parse_args.__globals__["argparse"].Namespace(
        engine_version="5.7",
        dry_run=True,
    )

    recorded: list[list[str]] = []

    def fake_run_step(cmd: list[str]) -> int:
        recorded.append(cmd)
        return 0

    original = unreal_workflow.run_step
    unreal_workflow.run_step = fake_run_step
    try:
        assert unreal_workflow.command_verify(args) == 0
    finally:
        unreal_workflow.run_step = original

    assert recorded == [[sys.executable, "tools/run_unreal_orientation_verification.py", "--engine-version", "5.7", "--dry-run"]]


def test_demo_command_forwards_dry_run() -> None:
    args = unreal_workflow.parse_args.__globals__["argparse"].Namespace(
        engine_version="5.8",
        dry_run=True,
    )

    recorded: list[list[str]] = []

    def fake_run_step(cmd: list[str]) -> int:
        recorded.append(cmd)
        return 0

    original = unreal_workflow.run_step
    unreal_workflow.run_step = fake_run_step
    try:
        assert unreal_workflow.command_demo(args) == 0
    finally:
        unreal_workflow.run_step = original

    assert recorded == [[sys.executable, "tools/run_unreal_demo_smoke.py", "--engine-version", "5.8", "--dry-run"]]


def test_matrix_command_forwards_skip_flags() -> None:
    args = unreal_workflow.parse_args.__globals__["argparse"].Namespace(
        versions=["5.6", "5.7", "5.8"],
        skip_plugin_build=True,
        skip_orientation=False,
        skip_demo=True,
    )

    recorded: list[list[str]] = []

    def fake_run_step(cmd: list[str]) -> int:
        recorded.append(cmd)
        return 0

    original = unreal_workflow.run_step
    unreal_workflow.run_step = fake_run_step
    try:
        assert unreal_workflow.command_matrix(args) == 0
    finally:
        unreal_workflow.run_step = original

    assert recorded == [[
        sys.executable,
        "tools/run_unreal_matrix.py",
        "--versions",
        "5.6",
        "5.7",
        "5.8",
        "--skip-plugin-build",
        "--skip-demo",
    ]]
