#!/usr/bin/env python3
"""Operator-facing workflow wrapper for the Alpha 4 Lattice shim/mock lanes."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import load_local_env
from fastdis.native import find_native_library

DEFAULT_OUT_ROOT = ROOT / "verification_reports" / "alpha4" / "lattice"
DEFAULT_DIS_FIXTURE = ROOT / "integrations" / "lattice" / "examples" / "dis_entity_fixture.json"
DEFAULT_TRACK_FIXTURE = ROOT / "integrations" / "lattice" / "examples" / "lattice_track_fixture.json"
DEFAULT_OBJECT_FIXTURE = ROOT / "integrations" / "lattice" / "examples" / "object_fixture.json"
DEFAULT_TASK_FIXTURE = ROOT / "integrations" / "lattice" / "examples" / "task_fixture.json"
DEFAULT_EVENT_LOG = "shim_event_log.jsonl"


def run_step(cmd: list[str]) -> int:
    print("+", " ".join(cmd))
    env = os.environ.copy()
    pythonpath = env.get("PYTHONPATH")
    src = str(ROOT / "src")
    env["PYTHONPATH"] = src if not pythonpath else f"{src}{os.pathsep}{pythonpath}"
    completed = subprocess.run(cmd, cwd=ROOT, env=env)
    return completed.returncode


def discover_payload() -> dict[str, object]:
    return {
        "python": sys.executable,
        "repo_root": str(ROOT),
        "integration_src": str(ROOT / "integrations" / "lattice" / "src"),
        "default_out_root": str(DEFAULT_OUT_ROOT),
        "dis_fixture": str(DEFAULT_DIS_FIXTURE),
        "track_fixture": str(DEFAULT_TRACK_FIXTURE),
        "object_fixture": str(DEFAULT_OBJECT_FIXTURE),
        "task_fixture": str(DEFAULT_TASK_FIXTURE),
        "tools": {
            "lattice_shim_module": "fastdis.tools.lattice_shim",
            "lattice_publish_module": "fastdis.tools.lattice_publish",
        },
    }


def doctor_payload() -> dict[str, object]:
    checks: list[dict[str, str]] = []

    def add_check(name: str, ok: bool, detail: str, *, warn: bool = False) -> None:
        checks.append(
            {
                "name": name,
                "status": "warn" if warn and not ok else ("ok" if ok else "fail"),
                "detail": detail,
            }
        )

    add_check("python", shutil.which(Path(sys.executable).name) is not None, sys.executable)
    add_check("src package", (ROOT / "src" / "fastdis").is_dir(), str(ROOT / "src" / "fastdis"))
    add_check("integration adapter", (ROOT / "integrations" / "lattice" / "src" / "packet_stoat_lattice").is_dir(), str(ROOT / "integrations" / "lattice" / "src" / "packet_stoat_lattice"))
    add_check("native fastdis library", find_native_library() is not None, str(find_native_library() or "native library not found"), warn=True)
    add_check("dis fixture", DEFAULT_DIS_FIXTURE.is_file(), str(DEFAULT_DIS_FIXTURE))
    add_check("track fixture", DEFAULT_TRACK_FIXTURE.is_file(), str(DEFAULT_TRACK_FIXTURE))
    add_check("object fixture", DEFAULT_OBJECT_FIXTURE.is_file(), str(DEFAULT_OBJECT_FIXTURE))
    add_check("task fixture", DEFAULT_TASK_FIXTURE.is_file(), str(DEFAULT_TASK_FIXTURE))
    add_check("verification root", DEFAULT_OUT_ROOT.parent.exists(), str(DEFAULT_OUT_ROOT.parent), warn=True)

    hard_failures = [check for check in checks if check["status"] == "fail"]
    if hard_failures:
        status = "missing-prereqs"
    elif any(check["status"] == "warn" for check in checks):
        status = "ready-with-gaps"
    else:
        status = "ready"

    return {
        "status": status,
        "checks": checks,
        "next_steps": [
            "Inspect the lane: python tools/lattice_workflow.py discover",
            "Run DIS to shim: python tools/lattice_workflow.py dis-to-shim",
            "Run shim to DIS: python tools/lattice_workflow.py shim-to-dis",
            "Exercise bounded objects/tasks: python tools/lattice_workflow.py lab-state",
            "Run the end-to-end lane: python tools/lattice_workflow.py full",
        ],
    }


def print_doctor(payload: dict[str, object]) -> None:
    print("Lattice workflow doctor")
    print(f"status: {payload['status']}")
    print("checks:")
    for check in payload["checks"]:
        print(f"  - {check['name']}: {check['status']} ({check['detail']})")
    print("next:")
    for step in payload["next_steps"]:
        print(f"  - {step}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    discover = subparsers.add_parser("discover", help="List discovered Alpha 4 lattice workflow inputs")
    discover.add_argument("--format", choices=("text", "json"), default="text")

    doctor = subparsers.add_parser("doctor", help="Check the current machine and repo for Alpha 4 lattice prerequisites")
    doctor.add_argument("--format", choices=("text", "json"), default="text")

    dis_to_shim = subparsers.add_parser("dis-to-shim", help="Run canonical/DIS fixture entities into the shim lane")
    dis_to_shim.add_argument("--fixture", default=str(DEFAULT_DIS_FIXTURE))
    dis_to_shim.add_argument("--out-dir", default=str(DEFAULT_OUT_ROOT / "dis_to_shim"))

    shim_to_dis = subparsers.add_parser("shim-to-dis", help="Run shim export back into DIS Entity State replay output")
    shim_to_dis.add_argument("--fixture", default=str(DEFAULT_TRACK_FIXTURE))
    shim_to_dis.add_argument("--out-dir", default=str(DEFAULT_OUT_ROOT / "shim_to_dis"))

    lab_state = subparsers.add_parser("lab-state", help="Exercise bounded object/task seam and emit local lab-state reports")
    lab_state.add_argument("--object-fixture", default=str(DEFAULT_OBJECT_FIXTURE))
    lab_state.add_argument("--task-fixture", default=str(DEFAULT_TASK_FIXTURE))
    lab_state.add_argument("--out-dir", default=str(DEFAULT_OUT_ROOT / "lab_state"))

    full = subparsers.add_parser("full", help="Doctor, then run dis-to-shim, shim-to-dis, and lab-state")
    full.add_argument("--dis-fixture", default=str(DEFAULT_DIS_FIXTURE))
    full.add_argument("--track-fixture", default=str(DEFAULT_TRACK_FIXTURE))
    full.add_argument("--object-fixture", default=str(DEFAULT_OBJECT_FIXTURE))
    full.add_argument("--task-fixture", default=str(DEFAULT_TASK_FIXTURE))
    full.add_argument("--out-root", default=str(DEFAULT_OUT_ROOT))

    return parser.parse_args()


def command_discover(args: argparse.Namespace) -> int:
    payload = discover_payload()
    if args.format == "json":
        print(json.dumps(payload, indent=2))
    else:
        for key, value in payload.items():
            print(f"{key}: {value}")
    return 0


def command_doctor(args: argparse.Namespace) -> int:
    payload = doctor_payload()
    if args.format == "json":
        print(json.dumps(payload, indent=2))
    else:
        print_doctor(payload)
    return 0 if payload["status"] in {"ready", "ready-with-gaps"} else 2


def command_dis_to_shim(args: argparse.Namespace) -> int:
    return run_step(
        [
            sys.executable,
            "-m",
            "fastdis.tools.lattice_shim",
            "dis-to-shim",
            str(Path(args.fixture)),
            "--out-dir",
            str(Path(args.out_dir)),
        ]
    )


def command_shim_to_dis(args: argparse.Namespace) -> int:
    return run_step(
        [
            sys.executable,
            "-m",
            "fastdis.tools.lattice_shim",
            "shim-to-dis",
            str(Path(args.fixture)),
            "--out-dir",
            str(Path(args.out_dir)),
        ]
    )


def command_lab_state(args: argparse.Namespace) -> int:
    return run_step(
        [
            sys.executable,
            "-m",
            "fastdis.tools.lattice_shim",
            "lab-state",
            "--object-fixture",
            str(Path(args.object_fixture)),
            "--task-fixture",
            str(Path(args.task_fixture)),
            "--out-dir",
            str(Path(args.out_dir)),
        ]
    )


def command_full(args: argparse.Namespace) -> int:
    if command_doctor(argparse.Namespace(format="text")) == 2:
        return 2
    out_root = Path(args.out_root)
    dis_code = command_dis_to_shim(argparse.Namespace(fixture=args.dis_fixture, out_dir=str(out_root / "dis_to_shim")))
    if dis_code != 0:
        return dis_code
    shim_code = command_shim_to_dis(argparse.Namespace(fixture=args.track_fixture, out_dir=str(out_root / "shim_to_dis")))
    if shim_code != 0:
        return shim_code
    return command_lab_state(
        argparse.Namespace(
            object_fixture=args.object_fixture,
            task_fixture=args.task_fixture,
            out_dir=str(out_root / "lab_state"),
        )
    )


def main() -> int:
    load_local_env.load()
    args = parse_args()
    if args.command == "discover":
        return command_discover(args)
    if args.command == "doctor":
        return command_doctor(args)
    if args.command == "dis-to-shim":
        return command_dis_to_shim(args)
    if args.command == "shim-to-dis":
        return command_shim_to_dis(args)
    if args.command == "lab-state":
        return command_lab_state(args)
    if args.command == "full":
        return command_full(args)
    raise SystemExit(f"Unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
