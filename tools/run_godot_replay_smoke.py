#!/usr/bin/env python3
"""Run a headless Godot replay-driven canonical scenario smoke test."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import tempfile

import build_godot_extension
import godot_env
import load_local_env


ROOT = Path(__file__).resolve().parents[1]
PROJECT_DIR = ROOT / "examples" / "godot" / "fastdis_demo"
ADDON_BIN_DIR = PROJECT_DIR / "addons" / "fastdis" / "bin"
CORE_SCENARIO_SUITE = "core_matrix"


def alias_root() -> Path:
    return godot_env.repo_alias_root(ROOT)


def alias_project_dir() -> Path:
    return alias_root() / "examples" / "godot" / "fastdis_demo"


def alias_script_path() -> Path:
    return alias_project_dir() / "scripts" / "run_replay_matrix.gd"


def build_command(godot_binary: str) -> list[str]:
    return [
        godot_binary,
        "--headless",
        "--path",
        str(alias_project_dir()),
        "--script",
        str(alias_script_path()),
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--godot", help="Explicit godot executable path")
    parser.add_argument("--skip-build", action="store_true", help="Do not rebuild/stage the Godot extension before running")
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--count", type=int, required=True)
    parser.add_argument("--entity-count", type=int, required=True)
    parser.add_argument("--rate-hz", type=float, required=True)
    parser.add_argument("--packet-budget", type=int, default=128)
    return parser.parse_args()


def extract_json(stdout: str) -> dict[str, object]:
    start = stdout.find("{")
    if start < 0:
        raise ValueError("no JSON object found in Godot stdout")
    decoder = json.JSONDecoder()
    payload, _ = decoder.raw_decode(stdout[start:])
    return payload


def build_truth_and_replay(
    *,
    replay_path: Path,
    truth_path: Path,
    count: int,
    entity_count: int,
    rate_hz: float,
) -> dict[str, object]:
    from fastdis.tools import send_entity

    send_args = argparse.Namespace(
        count=count,
        entity_count=entity_count,
        rate_hz=rate_hz,
        site=100,
        application=1,
        entity=0,
        force_id=1,
        exercise_id=3,
        marking="FASTDIS",
        lat=29.5597,
        lon=-95.0831,
        alt=100.0,
        heading=90.0,
        pitch=0.0,
        roll=0.0,
        print_orientation_debug=False,
        truth_out=None,
    )
    packets, _orientation_debug, truth = send_entity.build_packets(send_args)
    with replay_path.open("wb") as handle:
        for packet in packets:
            handle.write(len(packet).to_bytes(4, byteorder="big"))
            handle.write(packet)
    truth_path.write_text(json.dumps(truth, indent=2) + "\n", encoding="utf-8")
    return truth


def main() -> int:
    load_local_env.load()
    args = parse_args()
    build_required = not staged_build_complete()
    if not args.skip_build and build_required:
        subprocess.run(godot_env.python_command() + [str(ROOT / "tools" / "build_godot_extension.py")], cwd=ROOT, check=True)

    godot_binary = godot_env.resolve_godot(args.godot)
    if godot_binary is None:
        raise SystemExit("Could not find a godot executable on PATH or in FASTDIS_GODOT")

    wrappers = wrapper_candidates()
    if not all(path.is_file() for path in wrappers):
        names = ", ".join(path.name for path in wrappers)
        raise SystemExit(
            "Godot is installed, but the FastDIS GDExtension wrapper set is incomplete or stale. "
            f"Expected one of: {names} under {ADDON_BIN_DIR}. "
            "Run `python tools/godot_workflow.py build` first."
        )

    with tempfile.TemporaryDirectory(prefix="fastdis_godot_replay_") as tmp:
        replay_path = Path(tmp) / f"{args.scenario}.fastdispkt"
        truth_path = Path(tmp) / f"{args.scenario}.truth.json"
        truth = build_truth_and_replay(
            replay_path=replay_path,
            truth_path=truth_path,
            count=args.count,
            entity_count=args.entity_count,
            rate_hz=args.rate_hz,
        )

        env = godot_env.build_env()
        env["FASTDIS_GODOT_REPLAY_PATH"] = str(replay_path)
        env["FASTDIS_GODOT_EXPECTED_PACKETS"] = str(args.count)
        env["FASTDIS_GODOT_EXPECTED_ENTITIES"] = str(args.entity_count)
        env["FASTDIS_GODOT_REPLAY_PACKET_BUDGET"] = str(args.packet_budget)
        command = build_command(godot_binary)
        completed = subprocess.run(
            command,
            cwd=alias_root(),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
        report = extract_json(completed.stdout)
        errors: list[str] = []
        if int(report.get("loaded_packets", 0)) != int(truth["packet_count"]):
            errors.append("loaded packet count mismatch")
        if int(report.get("known_entities", 0)) < int(truth["unique_entities"]):
            errors.append("known entity count mismatch")
        if int(report.get("moved_entity_count", 0)) < int(truth["unique_entities"]):
            errors.append("moved entity count mismatch")

        payload = {
            "surface": "godot",
            "mode": "replay",
            "scenario": args.scenario,
            "scenario_suite": CORE_SCENARIO_SUITE,
            "recv_command": command,
            "recv_returncode": completed.returncode,
            "recv_output": completed.stdout,
            "report": report,
            "errors": errors,
            "truth": truth,
            "truth_file": str(truth_path),
            "replay_file": str(replay_path),
            "status": "passed" if completed.returncode == 0 and not errors else "failed",
        }
        print(json.dumps(payload, indent=2))
        return 0 if payload["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
