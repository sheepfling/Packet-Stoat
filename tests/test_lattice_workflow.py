from __future__ import annotations

import argparse
import sys
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import lattice_workflow


def test_doctor_payload_detects_expected_artifacts() -> None:
    payload = lattice_workflow.doctor_payload()

    assert payload["status"] in {"ready", "ready-with-gaps"}
    assert any(check["name"] == "native fastdis library" for check in payload["checks"])
    assert any(check["name"] == "dis fixture" and check["status"] == "ok" for check in payload["checks"])
    assert any(check["name"] == "track fixture" and check["status"] == "ok" for check in payload["checks"])


def test_dis_to_shim_command_forwards_args() -> None:
    recorded: list[list[str]] = []

    def fake_run_step(cmd: list[str]) -> int:
        recorded.append(cmd)
        return 0

    original = lattice_workflow.run_step
    lattice_workflow.run_step = fake_run_step
    try:
        args = argparse.Namespace(fixture="fixture.json", out_dir="out/dis")
        assert lattice_workflow.command_dis_to_shim(args) == 0
    finally:
        lattice_workflow.run_step = original

    assert recorded == [[
        sys.executable,
        "-m",
        "fastdis.tools.lattice_shim",
        "dis-to-shim",
        "fixture.json",
        "--out-dir",
        "out/dis",
    ]]


def test_shim_to_dis_command_forwards_args() -> None:
    recorded: list[list[str]] = []

    def fake_run_step(cmd: list[str]) -> int:
        recorded.append(cmd)
        return 0

    original = lattice_workflow.run_step
    lattice_workflow.run_step = fake_run_step
    try:
        args = argparse.Namespace(fixture="track.json", out_dir="out/replay")
        assert lattice_workflow.command_shim_to_dis(args) == 0
    finally:
        lattice_workflow.run_step = original

    assert recorded == [[
        sys.executable,
        "-m",
        "fastdis.tools.lattice_shim",
        "shim-to-dis",
        "track.json",
        "--out-dir",
        "out/replay",
    ]]


def test_full_command_runs_both_lanes() -> None:
    steps: list[str] = []

    def fake_doctor(_args: argparse.Namespace) -> int:
        steps.append("doctor")
        return 0

    def fake_dis(args: argparse.Namespace) -> int:
        steps.append(f"dis:{args.fixture}:{args.out_dir}")
        return 0

    def fake_shim(args: argparse.Namespace) -> int:
        steps.append(f"shim:{args.fixture}:{args.out_dir}")
        return 0

    original_doctor = lattice_workflow.command_doctor
    original_dis = lattice_workflow.command_dis_to_shim
    original_shim = lattice_workflow.command_shim_to_dis
    lattice_workflow.command_doctor = fake_doctor
    lattice_workflow.command_dis_to_shim = fake_dis
    lattice_workflow.command_shim_to_dis = fake_shim
    try:
        args = argparse.Namespace(
            dis_fixture="a.json",
            track_fixture="b.json",
            out_root="reports/lattice",
        )
        assert lattice_workflow.command_full(args) == 0
    finally:
        lattice_workflow.command_doctor = original_doctor
        lattice_workflow.command_dis_to_shim = original_dis
        lattice_workflow.command_shim_to_dis = original_shim

    assert steps == [
        "doctor",
        "dis:a.json:reports/lattice/dis_to_shim",
        "shim:b.json:reports/lattice/shim_to_dis",
    ]
