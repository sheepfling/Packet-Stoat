#!/usr/bin/env python3
"""Run a headless Godot localhost UDP ingest smoke test against FastDisWorld."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import socket
import subprocess
import tempfile
import time
import math

import build_godot_extension
import godot_env
import load_local_env


ROOT = Path(__file__).resolve().parents[1]
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

    port = ephemeral_port()
    with tempfile.TemporaryDirectory(prefix="fastdis_godot_udp_") as tmp:
        truth_path = Path(tmp) / "expected_session.json"
        ready_path = Path(tmp) / "godot_ready.txt"
        env = godot_env.build_env()
        env["FASTDIS_GODOT_UDP_PORT"] = str(port)
        env["FASTDIS_GODOT_EXPECTED_PACKETS"] = str(args.count)
        env["FASTDIS_GODOT_EXPECTED_ENTITIES"] = str(args.entity_count)
        expected_stream_seconds = float(args.count) / max(float(args.rate_hz), 1.0)
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
            send_cmd = godot_env.python_command() + [
                "-m",
                "fastdis.tools.send_entity",
                "--dst",
                "127.0.0.1",
                "--port",
                str(port),
                "--count",
                str(args.count),
                "--entity-count",
                str(args.entity_count),
                "--rate-hz",
                str(args.rate_hz),
                "--entity",
                "0",
                "--truth-out",
                str(truth_path),
            ]
            send_completed = subprocess.run(
                send_cmd,
                cwd=ROOT,
                env={**env, "PYTHONPATH": str(ROOT / "src")},
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                check=False,
            )
            stdout, _ = proc.communicate(timeout=args.timeout + 5.0)
        finally:
            if proc.poll() is None:
                proc.kill()

        report = extract_json(stdout)
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
            "status": "passed" if proc.returncode == 0 and send_completed.returncode == 0 and not errors else "failed",
            "send_command": send_cmd,
            "send_returncode": send_completed.returncode,
            "send_output": send_completed.stdout,
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
