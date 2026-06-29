#!/usr/bin/env python3
"""Run a headless Godot localhost UDP outbound smoke test against the canonical Python verifier."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import socket
import subprocess
import tempfile

import godot_env
import load_local_env
from run_network_send_matrix import build_truth_and_replay


ROOT = Path(__file__).resolve().parents[1]
PROJECT_DIR = ROOT / "packages" / "godot" / "fastdis_demo"


def alias_root() -> Path:
    return godot_env.repo_alias_root(ROOT)


def alias_project_dir() -> Path:
    return alias_root() / "packages" / "godot" / "fastdis_demo"


def alias_script_path() -> Path:
    return alias_project_dir() / "scripts" / "run_udp_send_smoke.gd"


def build_command(godot_binary: str) -> list[str]:
    return [
        godot_binary,
        "--headless",
        "--path",
        str(alias_project_dir()),
        "--script",
        str(alias_script_path()),
    ]


def ephemeral_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--godot", help="Explicit godot executable path")
    parser.add_argument("--count", type=int, default=24)
    parser.add_argument("--entity-count", type=int, default=3)
    parser.add_argument("--timeout", type=float, default=5.0)
    return parser.parse_args()


def python_env(base_env: dict[str, str]) -> dict[str, str]:
    env = dict(base_env)
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(ROOT / "src") + (os.pathsep + existing if existing else "")
    return env


def extract_json(stdout: str) -> dict[str, object]:
    start = stdout.find("{")
    if start < 0:
        raise ValueError("no JSON object found in stdout")
    decoder = json.JSONDecoder()
    payload, _ = decoder.raw_decode(stdout[start:])
    return payload


def main() -> int:
    load_local_env.load()
    args = parse_args()

    godot_binary = godot_env.resolve_godot(args.godot)
    if godot_binary is None:
        raise SystemExit("Could not find a godot executable on PATH or in FASTDIS_GODOT")

    port = ephemeral_port()
    with tempfile.TemporaryDirectory(prefix="fastdis_godot_udp_send_") as tmp:
        truth_path, replay_path = build_truth_and_replay(Path(tmp), count=args.count, entity_count=args.entity_count)
        env = godot_env.build_env()
        env["FASTDIS_GODOT_SEND_HOST"] = "127.0.0.1"
        env["FASTDIS_GODOT_SEND_PORT"] = str(port)
        env["FASTDIS_GODOT_SEND_REPLAY_PATH"] = str(replay_path)
        env["FASTDIS_GODOT_SEND_EXPECTED_PACKETS"] = str(args.count)
        recv_cmd = godot_env.python_command() + [
            "-m",
            "fastdis.tools.recv",
            "--bind",
            "127.0.0.1",
            "--port",
            str(port),
            "--max-packets",
            str(args.count),
            "--timeout",
            str(args.timeout),
            "--surface",
            "godot-send-smoke",
            "--verify",
            str(truth_path),
        ]
        recv_proc = subprocess.Popen(
            recv_cmd,
            cwd=ROOT,
            env=python_env(env),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        try:
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
            recv_stdout, _ = recv_proc.communicate(timeout=args.timeout + 5.0)
        finally:
            if recv_proc.poll() is None:
                recv_proc.kill()

        errors: list[str] = []
        try:
            send_report = extract_json(completed.stdout)
        except Exception as exc:
            send_report = None
            errors.append(f"godot send report parse failed: {exc}")
        try:
            recv_report = extract_json(recv_stdout)
        except Exception as exc:
            recv_report = None
            errors.append(f"receiver JSON parse failed: {exc}")

        payload = {
            "surface": "godot",
            "mode": "live_udp_send",
            "status": "passed" if completed.returncode == 0 and recv_proc.returncode == 0 and not errors else "failed",
            "send_command": command,
            "send_returncode": completed.returncode,
            "send_output": completed.stdout,
            "recv_command": recv_cmd,
            "recv_returncode": recv_proc.returncode,
            "recv_output": recv_stdout,
            "send_report": send_report,
            "recv_report": recv_report,
            "truth_file": str(truth_path),
            "replay_file": str(replay_path),
            "errors": errors,
        }
        print(json.dumps(payload, indent=2))
        return 0 if payload["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
