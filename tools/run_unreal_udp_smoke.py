#!/usr/bin/env python3
"""Run the Unreal localhost UDP ingest smoke harness and verify it against canonical sender truth."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import platform
import socket
import subprocess
import tempfile
import time
from typing import Any

import load_local_env
import unreal_env
from run_unreal_orientation_verification import (
    ALIAS_PROJECT_PATH,
    ALIAS_ROOT,
    HARNESS_LOG_PATH,
    PROJECT_PATH,
    clear_harness_log,
    ensure_harness_built,
    ensure_runtime_plugin,
    resolve_unreal,
)


ROOT = Path(__file__).resolve().parents[1]
CORE_SCENARIO_NAME = "entity_state_1x10hz"
CORE_SCENARIO_SUITE = "core_matrix"
CORE_SCENARIO_RATE_HZ = 10.0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--unreal", help="Explicit UnrealEditor-Cmd executable path")
    parser.add_argument("--engine-version", default="5.8")
    parser.add_argument("--count", type=int, default=24)
    parser.add_argument("--entity-count", type=int, default=1)
    parser.add_argument("--rate-hz", type=float, default=CORE_SCENARIO_RATE_HZ)
    parser.add_argument("--scenario", default=CORE_SCENARIO_NAME)
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


def _host_blocking_status(failure_kind: str | None) -> str:
    if failure_kind in {
        "engine-intermediate-write-denied",
        "sandbox-home-write-denied",
        "host-mac-platform-unavailable",
        "host-win64-platform-unavailable",
        "host-linux-platform-unavailable",
    }:
        return "pending"
    return "failed"


def _failure_payload(
    *,
    args: argparse.Namespace,
    recv_command: list[str] | None,
    recv_output: str,
    errors: list[str],
    failure_kind: str | None = None,
    report: dict[str, Any] | None = None,
    truth: dict[str, Any] | None = None,
    truth_file: str | None = None,
    send_command: list[str] | None = None,
    send_returncode: int | None = None,
    send_output: str | None = None,
    recv_returncode: int | None = None,
    recv_log: str | None = None,
) -> dict[str, Any]:
    note = unreal_env.probe_failure_note(failure_kind)
    merged_errors = list(errors)
    if note and note not in merged_errors:
        merged_errors.append(note)
    return {
        "surface": "unreal",
        "mode": "live_udp",
        "scenario": args.scenario,
        "scenario_suite": CORE_SCENARIO_SUITE,
        "status": _host_blocking_status(failure_kind),
        "failure_kind": failure_kind,
        "send_command": send_command,
        "send_returncode": send_returncode,
        "send_output": send_output,
        "recv_command": recv_command,
        "recv_returncode": recv_returncode,
        "recv_output": recv_output,
        "recv_log": recv_log,
        "report": report or {},
        "errors": merged_errors,
        "truth": truth or {},
        "truth_file": truth_file,
    }


def _discover_install(version: str | None) -> unreal_env.UnrealInstall | None:
    installs = unreal_env.discover_installs()
    if version is not None:
        for install in installs:
            if install.version == version:
                return install
    return installs[0] if installs else None


def _engine_target_intermediate_dir(install: unreal_env.UnrealInstall) -> Path:
    engine_dir = Path(install.engine_dir)
    platform_dir = unreal_env.platform_dir_name()
    arch_dir = "x64" if platform.system().lower() == "darwin" else platform_dir
    return engine_dir / "Intermediate" / "Build" / platform_dir / arch_dir / "UnrealEditor"


def main() -> int:
    load_local_env.load()
    args = parse_args()
    if not args.dry_run:
        clear_harness_log()

    unreal_binary = resolve_unreal(args.unreal, args.engine_version)
    if unreal_binary is None:
        raise SystemExit(f"Could not find an Unreal editor executable for version {args.engine_version}")

    command = build_command(unreal_binary)
    if args.dry_run:
        print(" ".join(command))
        return 0

    install = _discover_install(args.engine_version)
    if install is not None:
        target_intermediate = _engine_target_intermediate_dir(install)
        target_ok, target_detail = unreal_env.path_writable(target_intermediate)
        if not target_ok:
            payload = _failure_payload(
                args=args,
                recv_command=command,
                recv_output="",
                recv_returncode=None,
                failure_kind="engine-intermediate-write-denied",
                errors=[target_detail],
            )
            print(json.dumps(payload, indent=2))
            return 1
    host_probe = unreal_env.probe_host_platform_support(install, PROJECT_PATH) if install is not None else None
    host_failure_kind = host_probe.get("failure_kind") if isinstance(host_probe, dict) else None
    if host_failure_kind in {
        "engine-intermediate-write-denied",
        "sandbox-home-write-denied",
        "host-mac-platform-unavailable",
        "host-win64-platform-unavailable",
        "host-linux-platform-unavailable",
    }:
        payload = _failure_payload(
            args=args,
            recv_command=command,
            recv_output=str(host_probe.get("output") or "") if isinstance(host_probe, dict) else "",
            recv_returncode=None,
            failure_kind=host_failure_kind,
            errors=[str(host_probe.get("detail") or "Unreal host probe blocked this lane")],
        )
        print(json.dumps(payload, indent=2))
        return 1

    try:
        ensure_runtime_plugin(args.engine_version)
        ensure_harness_built(args.engine_version)
    except subprocess.CalledProcessError as exc:
        output = ""
        if isinstance(exc.stdout, str):
            output = exc.stdout
        elif isinstance(exc.output, str):
            output = exc.output
        failure_kind = unreal_env.classify_probe_failure(output)
        payload = _failure_payload(
            args=args,
            recv_command=command,
            recv_output=output,
            recv_returncode=exc.returncode,
            failure_kind=failure_kind,
            errors=[f"Unreal harness setup failed with exit status {exc.returncode}"],
        )
        print(json.dumps(payload, indent=2))
        return 1

    port = ephemeral_port()
    with tempfile.TemporaryDirectory(prefix="fastdis_unreal_udp_") as tmp:
        truth_path = Path(tmp) / "expected_session.json"
        stdout_path = Path(tmp) / "unreal_stdout.log"
        env = unreal_env.build_env()
        env["FASTDIS_UNREAL_UDP_PORT"] = str(port)
        env["FASTDIS_UNREAL_EXPECTED_PACKETS"] = str(args.count)
        env["FASTDIS_UNREAL_EXPECTED_ENTITIES"] = str(args.entity_count)
        env["FASTDIS_UNREAL_EXPECTED_RATE_HZ"] = str(args.rate_hz)
        send_cmd: list[str] | None = None
        send_completed: subprocess.CompletedProcess[str] | None = None
        stdout = ""
        log_text = ""
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
                "--rate-hz",
                str(args.rate_hz),
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
        failure_kind = unreal_env.classify_probe_failure(stdout + "\n" + log_text)
        truth = json.loads(truth_path.read_text(encoding="utf-8")) if truth_path.is_file() else {}
        try:
            report = extract_report(log_text if "FASTDIS_UDP_SMOKE " in log_text else stdout)
        except ValueError as exc:
            payload = _failure_payload(
                args=args,
                recv_command=command,
                recv_output=stdout,
                recv_log=log_text,
                recv_returncode=proc.returncode,
                failure_kind=failure_kind,
                errors=[str(exc)],
                truth=truth,
                truth_file=str(truth_path) if truth_path.is_file() else None,
                send_command=send_cmd,
                send_returncode=send_completed.returncode if send_completed is not None else None,
                send_output=send_completed.stdout if send_completed is not None else None,
            )
            print(json.dumps(payload, indent=2))
            return 1

        errors: list[str] = []
        if report.get("packets") != truth.get("packet_count"):
            errors.append("packet count mismatch")
        if report.get("known_entities", 0) < truth.get("unique_entities", 0):
            errors.append("known entity count mismatch")
        if report.get("moved_actors", 0) < truth.get("unique_entities", 0):
            errors.append("moved actor count mismatch")
        payload = {
            "surface": "unreal",
            "mode": "live_udp",
            "scenario": args.scenario,
            "scenario_suite": CORE_SCENARIO_SUITE,
            "status": "passed" if proc.returncode == 0 and send_completed and send_completed.returncode == 0 and not errors else "failed",
            "failure_kind": failure_kind,
            "send_command": send_cmd,
            "send_returncode": send_completed.returncode if send_completed is not None else None,
            "send_output": send_completed.stdout if send_completed is not None else None,
            "recv_command": command,
            "recv_returncode": proc.returncode,
            "recv_output": stdout,
            "recv_log": log_text,
            "report": report,
            "errors": errors,
            "truth": truth,
            "truth_file": str(truth_path),
        }
        print(json.dumps(payload, indent=2))
        return 0 if payload["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
