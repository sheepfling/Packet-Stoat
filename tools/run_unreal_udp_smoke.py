#!/usr/bin/env python3
"""Run the Unreal localhost UDP ingest smoke harness and verify it against canonical sender truth."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import socket
import subprocess
import tempfile
import time

import load_local_env
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
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def ephemeral_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def build_command(unreal_binary: str) -> list[str]:
    return [
        unreal_binary,
        str(ALIAS_PROJECT_PATH),
        "-ExecCmds=Automation RunTests FastDis.Network.LocalhostUdpMovesActors; Quit",
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
    marker = "FASTDIS_UDP_SMOKE "
    for line in text.splitlines():
        if marker not in line:
            continue
        suffix = line.split(marker, 1)[1]
        parts = {}
        for token in suffix.split():
            if "=" not in token:
                continue
            key, value = token.split("=", 1)
            parts[key] = int(value)
        if parts:
            return parts
    raise ValueError("FASTDIS_UDP_SMOKE report line not found in Unreal output")


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
    with tempfile.TemporaryDirectory(prefix="fastdis_unreal_udp_") as tmp:
        truth_path = Path(tmp) / "expected_session.json"
        stdout_path = Path(tmp) / "unreal_stdout.log"
        env = unreal_env.build_env()
        env["FASTDIS_UNREAL_UDP_PORT"] = str(port)
        env["FASTDIS_UNREAL_EXPECTED_PACKETS"] = str(args.count)
        env["FASTDIS_UNREAL_EXPECTED_ENTITIES"] = str(args.entity_count)
        command = build_command(unreal_binary)
        if args.dry_run:
            print(" ".join(command))
            return 0

        with stdout_path.open("w", encoding="utf-8") as stdout_file:
            proc = subprocess.Popen(
                command,
                cwd=ALIAS_ROOT,
                env=env,
                stdout=stdout_file,
                stderr=subprocess.STDOUT,
                text=True,
            )
            try:
                started = wait_for_log_marker(
                    HARNESS_LOG_PATH,
                    "Test Started. Name={LocalhostUdpMovesActors}",
                    timeout=max(60.0, args.timeout + 30.0),
                )
                if not started:
                    raise TimeoutError("Unreal UDP smoke test never reached the started state")
                time.sleep(0.2)
                send_cmd = unreal_env.python_command() + [
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
                    "--entity",
                    "0",
                    "--truth-out",
                    str(truth_path),
                ]
                send_env = dict(env)
                send_env["PYTHONPATH"] = str(ROOT / "src")
                send_completed = subprocess.run(
                    send_cmd,
                    cwd=ROOT,
                    env=send_env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    check=False,
                )
                proc.wait(timeout=args.timeout + 45.0)
            finally:
                if proc.poll() is None:
                    proc.kill()
        stdout = stdout_path.read_text(encoding="utf-8", errors="replace") if stdout_path.is_file() else ""
        log_text = HARNESS_LOG_PATH.read_text(encoding="utf-8", errors="replace") if HARNESS_LOG_PATH.is_file() else ""

        report = extract_report(log_text if "FASTDIS_UDP_SMOKE " in log_text else stdout)
        truth = json.loads(truth_path.read_text(encoding="utf-8"))
        errors: list[str] = []
        if report.get("packets") != truth["packet_count"]:
            errors.append("packet count mismatch")
        if report.get("known_entities", 0) < truth["unique_entities"]:
            errors.append("known entity count mismatch")
        if report.get("moved_actors", 0) < truth["unique_entities"]:
            errors.append("moved actor count mismatch")
        payload = {
            "surface": "unreal",
            "mode": "live_udp",
            "status": "passed" if proc.returncode == 0 and send_completed.returncode == 0 and not errors else "failed",
            "send_command": send_cmd,
            "send_returncode": send_completed.returncode,
            "send_output": send_completed.stdout,
            "recv_command": command,
            "recv_returncode": proc.returncode,
            "recv_output": stdout,
            "recv_log": log_text,
            "report": report,
            "errors": errors,
            "truth_file": str(truth_path),
        }
        print(json.dumps(payload, indent=2))
        return 0 if payload["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
