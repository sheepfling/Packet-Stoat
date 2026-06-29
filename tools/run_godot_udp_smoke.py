#!/usr/bin/env python3
"""Run a headless Godot localhost UDP ingest smoke test against FastDisWorld."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import math

import build_godot_extension
import godot_env
import load_local_env


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from fastdis.tools import send_entity
from fastdis.tools._shared import write_session_truth


PROJECT_DIR = ROOT / "examples" / "godot" / "fastdis_demo"
ADDON_BIN_DIR = PROJECT_DIR / "addons" / "fastdis" / "bin"
CORE_SCENARIO_NAME = "entity_state_1x10hz"
CORE_SCENARIO_SUITE = "core_matrix"
CORE_SCENARIO_RATE_HZ = 10.0


def alias_root() -> Path:
    return godot_env.repo_alias_root(ROOT)


def alias_project_dir() -> Path:
    return alias_root() / "examples" / "godot" / "fastdis_demo"


def alias_script_path() -> Path:
    return alias_project_dir() / "scripts" / "run_udp_smoke.gd"


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


def ephemeral_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--godot", help="Explicit godot executable path")
    parser.add_argument("--skip-build", action="store_true", help="Do not rebuild/stage the Godot extension before running")
    parser.add_argument("--scenario", default=CORE_SCENARIO_NAME)
    parser.add_argument("--count", type=int, default=24)
    parser.add_argument("--entity-count", type=int, default=1)
    parser.add_argument("--rate-hz", type=float, default=CORE_SCENARIO_RATE_HZ)
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--allowed-force-id", action="append", type=int, default=[])
    parser.add_argument("--rejected-count", type=int, default=0)
    parser.add_argument("--rejected-entity-count", type=int, default=0)
    parser.add_argument("--rejected-entity-start", type=int, default=1000)
    parser.add_argument("--rejected-force-id", type=int, default=3)
    return parser.parse_args()


def extract_json(stdout: str) -> dict[str, object]:
    start = stdout.find("{")
    if start < 0:
        raise ValueError("no JSON object found in Godot stdout")
    decoder = json.JSONDecoder()
    payload, _ = decoder.raw_decode(stdout[start:])
    return payload


def wait_for_ready_file(path: Path, timeout: float) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if path.is_file():
            return True
        time.sleep(0.05)
    return False


def _send_args(*, count: int, entity_count: int, entity: int, force_id: int, rate_hz: float) -> argparse.Namespace:
    return argparse.Namespace(
        count=count,
        entity_count=entity_count,
        rate_hz=rate_hz,
        site=100,
        application=1,
        entity=entity,
        force_id=force_id,
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


def _merge_truths(accepted_truth: dict[str, object], rejected_truth: dict[str, object], packets_sent: int) -> dict[str, object]:
    return {
        "schema": "fastdis.recv_truth.v1",
        "packet_count": packets_sent,
        "packets_parsed": packets_sent,
        "entity_state": int(accepted_truth["entity_state"]),
        "malformed": 0,
        "unique_entities": int(accepted_truth["unique_entities"]),
        "latest_entities": accepted_truth["latest_entities"],
    }


def _build_packets_and_truth(args: argparse.Namespace, truth_path: Path) -> tuple[list[bytes], dict[str, object]]:
    accepted_packets, _accepted_debug, accepted_truth = send_entity.build_packets(
        _send_args(
            count=args.count,
            entity_count=args.entity_count,
            entity=0,
            force_id=args.allowed_force_id[0] if args.allowed_force_id else 1,
            rate_hz=args.rate_hz,
        )
    )
    packets = list(accepted_packets)
    truth: dict[str, object] = dict(accepted_truth)
    if args.rejected_count > 0:
        rejected_entity_count = args.rejected_entity_count if args.rejected_entity_count > 0 else args.rejected_count
        rejected_packets, _rejected_debug, rejected_truth = send_entity.build_packets(
            _send_args(
                count=args.rejected_count,
                entity_count=rejected_entity_count,
                entity=args.rejected_entity_start,
                force_id=args.rejected_force_id,
                rate_hz=args.rate_hz,
            )
        )
        packets = list(rejected_packets) + list(accepted_packets)
        truth = _merge_truths(accepted_truth, rejected_truth, len(packets))
    write_session_truth(truth_path, truth)
    return packets, truth


def _send_packets(dst: str, port: int, packets: list[bytes], *, rate_hz: float) -> tuple[int, str]:
    started = time.perf_counter()
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        for packet in packets:
            sock.sendto(packet, (dst, port))
    elapsed = time.perf_counter() - started
    return 0, f"sent {len(packets)} packets to {dst}:{port} in {elapsed:.6f}s"


def main() -> int:
    load_local_env.load()
    args = parse_args()
    build_required = not staged_build_complete()
    if args.skip_build and build_required:
        raise SystemExit("Godot extension staging is stale. Re-run without --skip-build or refresh the staged wrapper first.")
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

    port = ephemeral_port()
    with tempfile.TemporaryDirectory(prefix="fastdis_godot_udp_") as tmp:
        truth_path = Path(tmp) / "expected_session.json"
        ready_path = Path(tmp) / "godot_ready.txt"
        env = godot_env.build_env()
        env["FASTDIS_GODOT_UDP_PORT"] = str(port)
        env["FASTDIS_GODOT_EXPECTED_PACKETS"] = str(args.count)
        env["FASTDIS_GODOT_EXPECTED_ENTITIES"] = str(args.entity_count)
        env["FASTDIS_GODOT_EXPECTED_KNOWN_ENTITIES"] = str(args.entity_count)
        env["FASTDIS_GODOT_STALE_AFTER_TICKS"] = str(max(1000, args.count + args.rejected_count + 32))
        if args.allowed_force_id:
            env["FASTDIS_GODOT_ALLOWED_FORCE_IDS"] = ",".join(str(value) for value in args.allowed_force_id)
        else:
            env.pop("FASTDIS_GODOT_ALLOWED_FORCE_IDS", None)
        expected_stream_seconds = float(args.count) / max(float(args.rate_hz), 1.0)
        if args.rejected_count > 0:
            total_packets = args.count + args.rejected_count
            expected_stream_seconds = float(total_packets) / max(float(args.rate_hz), 1.0)
            env["FASTDIS_GODOT_EXPECTED_PACKETS"] = str(total_packets)
        guard_frames = max(600, int(math.ceil((max(float(args.timeout), expected_stream_seconds) + 2.0) * 120.0)))
        env["FASTDIS_GODOT_GUARD_FRAMES"] = str(guard_frames)
        env["FASTDIS_GODOT_READY_FILE"] = str(ready_path)
        command = build_command(godot_binary)
        proc = subprocess.Popen(
            command,
            cwd=alias_root(),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        try:
            if not wait_for_ready_file(ready_path, timeout=max(5.0, args.timeout)):
                raise TimeoutError("Godot UDP smoke did not signal readiness before send")
            packets, truth = _build_packets_and_truth(args, truth_path)
            send_cmd = [
                "internal_python_sender",
                "--dst",
                "127.0.0.1",
                "--port",
                str(port),
                "--count",
                str(len(packets)),
                "--scenario",
                str(args.scenario),
            ]
            send_returncode, send_output = _send_packets("127.0.0.1", port, packets, rate_hz=args.rate_hz)
            stdout, _ = proc.communicate(timeout=args.timeout + 5.0)
        finally:
            if proc.poll() is None:
                proc.kill()

        report = extract_json(stdout)
        if not isinstance(locals().get("truth"), dict):
            truth = json.loads(truth_path.read_text(encoding="utf-8"))
        errors: list[str] = []
        if int(report.get("packets_received", 0)) != int(truth["packet_count"]):
            errors.append("packet count mismatch")
        if int(report.get("known_entities", 0)) < int(truth["unique_entities"]):
            errors.append("known entity count mismatch")
        if int(report.get("moved_entity_count", 0)) < int(truth["unique_entities"]):
            errors.append("moved entity count mismatch")

        payload = {
            "surface": "godot",
            "mode": "live_udp",
            "scenario": args.scenario,
            "scenario_suite": CORE_SCENARIO_SUITE,
            "status": "passed" if proc.returncode == 0 and send_returncode == 0 and not errors else "failed",
            "send_command": send_cmd,
            "send_returncode": send_returncode,
            "send_output": send_output,
            "recv_command": command,
            "recv_returncode": proc.returncode,
            "recv_output": stdout,
            "report": report,
            "errors": errors,
            "truth": truth,
            "truth_file": str(truth_path),
        }
        print(json.dumps(payload, indent=2))
        return 0 if payload["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
