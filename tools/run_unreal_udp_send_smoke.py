#!/usr/bin/env python3
"""Run the Unreal localhost UDP outbound smoke harness against the canonical Python verifier."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time

import load_local_env
from run_network_send_matrix import build_truth_and_replay
import unreal_env
from run_unreal_orientation_verification import (
    ALIAS_PROJECT_PATH,
    ALIAS_ROOT,
    HARNESS_LOG_PATH,
    clear_harness_log,
    ensure_harness_built,
    ensure_runtime_plugin,
    resolve_unreal,
)


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--unreal", help="Explicit UnrealEditor-Cmd executable path")
    parser.add_argument("--engine-version", default="5.8")
    parser.add_argument("--count", type=int, default=24)
    parser.add_argument("--entity-count", type=int, default=3)
    parser.add_argument("--timeout", type=float, default=8.0)
    parser.add_argument("--out", help="Optional JSON output path")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def ephemeral_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def python_env(base_env: dict[str, str]) -> dict[str, str]:
    env = dict(base_env)
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(ROOT / "src") + (os.pathsep + existing if existing else "")
    return env


def build_command(unreal_binary: str) -> list[str]:
    return [
        unreal_binary,
        str(ALIAS_PROJECT_PATH),
        "-ExecCmds=Automation RunTests FastDis.Network.OutboundReplaySend; Quit",
        "-unattended",
        "-nop4",
        "-nosplash",
        "-NullRHI",
        "-NoSound",
        "-stdout",
        "-FullStdOutLogOutput",
        f"-abslog={HARNESS_LOG_PATH}",
    ]


def extract_report(text: str) -> dict[str, int]:
    marker = "FASTDIS_UDP_SEND_SMOKE "
    for line in text.splitlines():
        if marker not in line:
            continue
        suffix = line.split(marker, 1)[1]
        parts: dict[str, int] = {}
        for token in suffix.split():
            if "=" not in token:
                continue
            key, value = token.split("=", 1)
            parts[key] = int(value)
        if parts:
            return parts
    raise ValueError("FASTDIS_UDP_SEND_SMOKE report line not found in Unreal output")


def json_from_stdout(stdout: str) -> dict[str, object]:
    start = stdout.find("{")
    if start < 0:
        raise ValueError("no JSON object found in stdout")
    return json.loads(stdout[start:])


def wait_for_log_marker(log_path: Path, marker: str, timeout: float) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if log_path.is_file():
            text = log_path.read_text(encoding="utf-8", errors="replace")
            if marker in text:
                return True
        time.sleep(0.1)
    return False


def main() -> int:
    load_local_env.load()
    args = parse_args()
    if not args.dry_run:
        clear_harness_log()
        ensure_runtime_plugin(args.engine_version)
        ensure_harness_built(args.engine_version)

    unreal_binary = resolve_unreal(args.unreal, args.engine_version)
    if unreal_binary is None:
        raise SystemExit(f"Could not find an Unreal editor executable for version {args.engine_version}")

    port = ephemeral_port()
    with tempfile.TemporaryDirectory(prefix="fastdis_unreal_udp_send_") as tmp:
        truth_path, replay_path = build_truth_and_replay(Path(tmp), count=args.count, entity_count=args.entity_count)
        stdout_path = Path(tmp) / "unreal_stdout.log"
        env = unreal_env.build_env()
        env["FASTDIS_UNREAL_SEND_HOST"] = "127.0.0.1"
        env["FASTDIS_UNREAL_SEND_PORT"] = str(port)
        env["FASTDIS_UNREAL_SEND_REPLAY_PATH"] = str(replay_path)
        env["FASTDIS_UNREAL_SEND_EXPECTED_PACKETS"] = str(args.count)
        command = build_command(unreal_binary)
        recv_cmd = unreal_env.python_command() + [
            "-m",
            "fastdis.tools.recv",
            "--bind",
            "127.0.0.1",
            "--port",
            str(port),
            "--max-packets",
            str(args.count),
            "--timeout",
            str(max(420.0, args.timeout + 420.0)),
            "--surface",
            "unreal-send-smoke",
            "--verify",
            str(truth_path),
        ]
        if args.dry_run:
            print("recv:", " ".join(recv_cmd))
            print("send:", " ".join(command))
            return 0

        recv_proc = subprocess.Popen(
            recv_cmd,
            cwd=ROOT,
            env=python_env(env),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        with stdout_path.open("w", encoding="utf-8") as stdout_file:
            try:
                time.sleep(0.2)
                send_proc = subprocess.Popen(
                    command,
                    cwd=ALIAS_ROOT,
                    env=env,
                    stdout=stdout_file,
                    stderr=subprocess.STDOUT,
                    text=True,
                )
                started = wait_for_log_marker(
                    HARNESS_LOG_PATH,
                    "Test Started. Name={OutboundReplaySend}",
                    timeout=max(360.0, args.timeout + 300.0),
                )
                if not started:
                    raise TimeoutError("Unreal outbound UDP smoke never reached the started automation state")
                finished = wait_for_log_marker(
                    HARNESS_LOG_PATH,
                    "FASTDIS_UDP_SEND_SMOKE ",
                    timeout=max(180.0, args.timeout + 180.0),
                )
                if not finished:
                    raise TimeoutError("Unreal outbound UDP smoke never emitted the FASTDIS_UDP_SEND_SMOKE marker")
                try:
                    send_proc.wait(timeout=30.0)
                except subprocess.TimeoutExpired:
                    send_proc.kill()
                    send_proc.wait(timeout=5.0)
                recv_stdout, _ = recv_proc.communicate(timeout=max(60.0, args.timeout + 45.0))
            finally:
                if recv_proc.poll() is None:
                    recv_proc.kill()
                if 'send_proc' in locals() and send_proc.poll() is None:
                    send_proc.kill()

        send_stdout = stdout_path.read_text(encoding="utf-8", errors="replace") if stdout_path.is_file() else ""
        log_text = HARNESS_LOG_PATH.read_text(encoding="utf-8", errors="replace") if HARNESS_LOG_PATH.is_file() else ""
        errors: list[str] = []
        try:
            unreal_report = extract_report(log_text if "FASTDIS_UDP_SEND_SMOKE " in log_text else send_stdout)
        except Exception as exc:
            unreal_report = None
            errors.append(f"unreal report parse failed: {exc}")
        try:
            recv_report = json_from_stdout(recv_stdout)
        except Exception as exc:
            recv_report = None
            errors.append(f"receiver JSON parse failed: {exc}")

        payload = {
            "surface": "unreal",
            "mode": "live_udp_send",
            "status": "passed" if recv_proc.returncode == 0 and not errors else "failed",
            "send_command": command,
            "send_returncode": send_proc.returncode,
            "send_output": send_stdout,
            "send_log": log_text,
            "recv_command": recv_cmd,
            "recv_returncode": recv_proc.returncode,
            "recv_output": recv_stdout,
            "send_report": unreal_report,
            "recv_report": recv_report,
            "truth_file": str(truth_path),
            "replay_file": str(replay_path),
            "errors": errors,
        }
        if args.out:
            out_path = Path(args.out).expanduser().resolve()
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(payload, indent=2))
        return 0 if payload["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
