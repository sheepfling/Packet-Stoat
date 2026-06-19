#!/usr/bin/env python3
"""Generate an Alpha 3 network-ingest verification matrix."""

from __future__ import annotations

import argparse
from datetime import UTC
from datetime import datetime
import json
import os
from pathlib import Path
import platform
import socket
import subprocess
import sys
import tempfile
import time

import load_local_env


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = ROOT / "verification_reports" / "alpha3_current"
CPP_RECEIVER = ROOT / "build" / "fastdis_udp_burst_cpp"
C_RECEIVER = ROOT / "build" / "fastdis_udp_burst_c"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    parser.add_argument("--count", type=int, default=24)
    parser.add_argument("--entity-count", type=int, default=3)
    parser.add_argument("--engine-entity-count", type=int, default=1)
    parser.add_argument("--timeout", type=float, default=2.0)
    parser.add_argument("--unreal-engine-version", default="5.8")
    return parser.parse_args()


def _python_env() -> dict[str, str]:
    env = os.environ.copy()
    src = ROOT / "src"
    env["PYTHONPATH"] = str(src) + os.pathsep + env.get("PYTHONPATH", "")
    return env


def _ephemeral_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _json_from_stdout(stdout: str) -> dict[str, object]:
    start = stdout.find("{")
    if start < 0:
        raise ValueError("no JSON object found in stdout")
    return json.loads(stdout[start:])


def run_python_udp_route(*, count: int, entity_count: int, timeout: float) -> dict[str, object]:
    port = _ephemeral_port()
    with tempfile.TemporaryDirectory(prefix="fastdis_net_matrix_") as tmp:
        truth_path = Path(tmp) / "expected_session.json"
        recv_cmd = [
            sys.executable,
            "-m",
            "fastdis.tools.recv",
            "--bind",
            "127.0.0.1",
            "--port",
            str(port),
            "--max-packets",
            str(count),
            "--timeout",
            str(timeout),
            "--surface",
            "python",
            "--verify",
            str(truth_path),
        ]
        recv_proc = subprocess.Popen(
            recv_cmd,
            cwd=ROOT,
            env=_python_env(),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        try:
            time.sleep(0.2)
            send_cmd = [
                sys.executable,
                "-m",
                "fastdis.tools.send_entity",
                "--dst",
                "127.0.0.1",
                "--port",
                str(port),
                "--count",
                str(count),
                "--entity-count",
                str(entity_count),
                "--entity",
                "0",
                "--truth-out",
                str(truth_path),
            ]
            send_completed = subprocess.run(
                send_cmd,
                cwd=ROOT,
                env=_python_env(),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                check=False,
            )
            recv_stdout, _ = recv_proc.communicate(timeout=timeout + 2.0)
        finally:
            if recv_proc.poll() is None:
                recv_proc.kill()
        status = "passed" if recv_proc.returncode == 0 and send_completed.returncode == 0 else "failed"
        report = None
        errors: list[str] = []
        try:
            report = _json_from_stdout(recv_stdout)
        except Exception as exc:  # pragma: no cover - defensive path for report generation
            errors.append(f"receiver JSON parse failed: {exc}")
        return {
            "surface": "python",
            "mode": "localhost_udp",
            "status": status if not errors else "failed",
            "truth_file": str(truth_path),
            "send_command": send_cmd,
            "recv_command": recv_cmd,
            "send_returncode": send_completed.returncode,
            "recv_returncode": recv_proc.returncode,
            "send_output": send_completed.stdout,
            "recv_output": recv_stdout,
            "report": report,
            "errors": errors,
        }


def verify_against_truth(report: dict[str, object], truth: dict[str, object]) -> list[str]:
    errors: list[str] = []
    field_map = {
        "packet_count": "packets_received",
        "packets_parsed": "packets_parsed",
        "malformed": "malformed",
        "entity_state": "entity_state",
        "unique_entities": "unique_entities",
    }
    for truth_field, report_field in field_map.items():
        if report.get(report_field) != truth.get(truth_field):
            errors.append(f"{report_field}: expected {truth.get(truth_field)}, got {report.get(report_field)}")
    expected_entities = sorted(
        [
            (
                entity["site"],
                entity["application"],
                entity["entity"],
                entity["force_id"],
            )
            for entity in truth.get("latest_entities", [])
        ]
    )
    actual_entities = sorted(
        [
            (
                entity["site"],
                entity["application"],
                entity["entity"],
                entity["force_id"],
            )
            for entity in report.get("latest_entities", [])
        ]
    )
    if actual_entities != expected_entities:
        errors.append("latest_entities mismatch")
    return errors


def run_cpp_udp_route(*, count: int, entity_count: int, timeout: float) -> dict[str, object]:
    if not CPP_RECEIVER.is_file():
        return {
            "surface": "cpp",
            "mode": "localhost_udp",
            "status": "pending",
            "notes": "build/fastdis_udp_burst_cpp is not available yet",
        }
    port = _ephemeral_port()
    with tempfile.TemporaryDirectory(prefix="fastdis_cpp_net_matrix_") as tmp:
        truth_path = Path(tmp) / "expected_session.json"
        recv_cmd = [
            str(CPP_RECEIVER),
            str(port),
            "--max-packets",
            str(count),
            "--idle-polls",
            str(max(200, int(timeout * 400))),
            "--json",
        ]
        recv_proc = subprocess.Popen(
            recv_cmd,
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        try:
            time.sleep(0.15)
            send_cmd = [
                sys.executable,
                "-m",
                "fastdis.tools.send_entity",
                "--dst",
                "127.0.0.1",
                "--port",
                str(port),
                "--count",
                str(count),
                "--entity-count",
                str(entity_count),
                "--entity",
                "0",
                "--truth-out",
                str(truth_path),
            ]
            send_completed = subprocess.run(
                send_cmd,
                cwd=ROOT,
                env=_python_env(),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                check=False,
            )
            recv_stdout, _ = recv_proc.communicate(timeout=timeout + 5.0)
        finally:
            if recv_proc.poll() is None:
                recv_proc.kill()
        errors: list[str] = []
        report = None
        try:
            report = _json_from_stdout(recv_stdout)
            truth = json.loads(truth_path.read_text(encoding="utf-8"))
            errors.extend(verify_against_truth(report, truth))
        except Exception as exc:
            errors.append(f"cpp receiver JSON parse/verify failed: {exc}")
        return {
            "surface": "cpp",
            "mode": "localhost_udp",
            "status": "passed" if recv_proc.returncode == 0 and send_completed.returncode == 0 and not errors else "failed",
            "truth_file": str(truth_path),
            "send_command": send_cmd,
            "recv_command": recv_cmd,
            "send_returncode": send_completed.returncode,
            "recv_returncode": recv_proc.returncode,
            "send_output": send_completed.stdout,
            "recv_output": recv_stdout,
            "report": report,
            "errors": errors,
        }


def run_c_udp_route(*, count: int, entity_count: int, timeout: float) -> dict[str, object]:
    if not C_RECEIVER.is_file():
        return {
            "surface": "c",
            "mode": "localhost_udp",
            "status": "pending",
            "notes": "build/fastdis_udp_burst_c is not available yet",
        }
    port = _ephemeral_port()
    with tempfile.TemporaryDirectory(prefix="fastdis_c_net_matrix_") as tmp:
        truth_path = Path(tmp) / "expected_session.json"
        recv_cmd = [
            str(C_RECEIVER),
            str(port),
            "--max-packets",
            str(count),
            "--idle-polls",
            str(max(200, int(timeout * 400))),
            "--json",
        ]
        recv_proc = subprocess.Popen(
            recv_cmd,
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        try:
            time.sleep(0.15)
            send_cmd = [
                sys.executable,
                "-m",
                "fastdis.tools.send_entity",
                "--dst",
                "127.0.0.1",
                "--port",
                str(port),
                "--count",
                str(count),
                "--entity-count",
                str(entity_count),
                "--entity",
                "0",
                "--truth-out",
                str(truth_path),
            ]
            send_completed = subprocess.run(
                send_cmd,
                cwd=ROOT,
                env=_python_env(),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                check=False,
            )
            recv_stdout, _ = recv_proc.communicate(timeout=timeout + 5.0)
        finally:
            if recv_proc.poll() is None:
                recv_proc.kill()
        errors: list[str] = []
        report = None
        try:
            report = _json_from_stdout(recv_stdout)
            truth = json.loads(truth_path.read_text(encoding="utf-8"))
            errors.extend(verify_against_truth(report, truth))
        except Exception as exc:
            errors.append(f"c receiver JSON parse/verify failed: {exc}")
        return {
            "surface": "c",
            "mode": "localhost_udp",
            "status": "passed" if recv_proc.returncode == 0 and send_completed.returncode == 0 and not errors else "failed",
            "truth_file": str(truth_path),
            "send_command": send_cmd,
            "recv_command": recv_cmd,
            "send_returncode": send_completed.returncode,
            "recv_returncode": recv_proc.returncode,
            "send_output": send_completed.stdout,
            "recv_output": recv_stdout,
            "report": report,
            "errors": errors,
        }


def _runner_payload(command: list[str]) -> dict[str, object]:
    completed = subprocess.run(
        command,
        cwd=ROOT,
        env=_python_env(),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    payload = None
    errors: list[str] = []
    try:
        payload = _json_from_stdout(completed.stdout)
    except Exception as exc:
        errors.append(f"runner JSON parse failed: {exc}")
    return {
        "command": command,
        "returncode": completed.returncode,
        "output": completed.stdout,
        "payload": payload,
        "errors": errors,
    }


def run_godot_live_udp_route(*, count: int, entity_count: int, timeout: float) -> dict[str, object]:
    command = [
        sys.executable,
        str(ROOT / "tools" / "run_godot_udp_smoke.py"),
        "--skip-build",
        "--count",
        str(count),
        "--entity-count",
        str(entity_count),
        "--timeout",
        str(max(5.0, timeout + 3.0)),
    ]
    result = _runner_payload(command)
    if result["payload"] is None:
        return {
            "surface": "godot",
            "mode": "live_udp",
            "status": "failed" if result["returncode"] else "pending",
            "notes": "Godot runner did not emit a parseable JSON payload",
            "recv_command": command,
            "recv_returncode": result["returncode"],
            "recv_output": result["output"],
            "errors": result["errors"],
        }
    payload = result["payload"]
    return {
        "surface": "godot",
        "mode": "live_udp",
        "status": payload.get("status", "failed"),
        "notes": "headless Godot localhost UDP smoke route using FastDisWorld; currently proven as a one-entity engine lane",
        "recv_command": command,
        "recv_returncode": result["returncode"],
        "recv_output": result["output"],
        **payload,
    }


def run_unreal_live_udp_route(*, count: int, entity_count: int, timeout: float, engine_version: str) -> dict[str, object]:
    if platform.system().lower() != "darwin":
        return {
            "surface": "unreal",
            "mode": "live_udp",
            "status": "skipped-by-platform",
            "notes": "Unreal automation smoke runner is only wired on macOS in this repo today",
        }
    command = [
        sys.executable,
        str(ROOT / "tools" / "run_unreal_udp_smoke.py"),
        "--engine-version",
        engine_version,
        "--count",
        str(count),
        "--entity-count",
        str(entity_count),
        "--timeout",
        str(max(20.0, timeout + 18.0)),
    ]
    result = _runner_payload(command)
    if result["payload"] is None:
        return {
            "surface": "unreal",
            "mode": "live_udp",
            "status": "failed" if result["returncode"] else "pending",
            "notes": "Unreal runner did not emit a parseable JSON payload",
            "recv_command": command,
            "recv_returncode": result["returncode"],
            "recv_output": result["output"],
            "errors": result["errors"],
        }
    payload = result["payload"]
    return {
        "surface": "unreal",
        "mode": "live_udp",
        "status": payload.get("status", "failed"),
        "notes": f"Unreal {engine_version} localhost UDP automation smoke route using UFastDisWorldSubsystem; currently proven as a one-entity engine lane",
        "recv_command": command,
        "recv_returncode": result["returncode"],
        "recv_output": result["output"],
        **payload,
    }


def render_markdown(report: dict[str, object]) -> str:
    lines = [
        "# Alpha 3 Network Ingest Matrix",
        "",
        f"- generated_at: `{report['generated_at']}`",
        "",
        "| Surface | Mode | Status | Notes |",
        "| --- | --- | --- | --- |",
    ]
    for row in report["routes"]:
        lines.append(f"| {row['surface']} | {row['mode']} | {row['status']} | {row['notes']} |")
    lines.extend(["", "## Route Details", ""])
    for row in report["routes"]:
        lines.extend(
            [
                f"### {row['surface']} / {row['mode']}",
                "",
                f"- status: `{row['status']}`",
                f"- notes: {row['notes']}",
            ]
        )
        if "send_command" in row:
            lines.append(f"- send_command: `{' '.join(row['send_command'])}`")
        if "recv_command" in row:
            lines.append(f"- recv_command: `{' '.join(row['recv_command'])}`")
        if row.get("report") is not None:
            lines.extend(
                [
                    "",
                    "```json",
                    json.dumps(row["report"], indent=2),
                    "```",
                ]
            )
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    load_local_env.load()
    args = parse_args()
    out_dir = Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    python_route = run_python_udp_route(count=args.count, entity_count=args.entity_count, timeout=args.timeout)
    c_route = run_c_udp_route(count=args.count, entity_count=args.entity_count, timeout=args.timeout)
    cpp_route = run_cpp_udp_route(count=args.count, entity_count=args.entity_count, timeout=args.timeout)
    godot_route = run_godot_live_udp_route(
        count=args.count,
        entity_count=args.engine_entity_count,
        timeout=args.timeout,
    )
    unreal_route = run_unreal_live_udp_route(
        count=args.count,
        entity_count=args.engine_entity_count,
        timeout=args.timeout,
        engine_version=args.unreal_engine_version,
    )
    routes = [
        {
            "surface": "python",
            "mode": "localhost_udp",
            "status": python_route["status"],
            "notes": "canonical sender truth file plus Python receiver verification report",
            **python_route,
        },
        {
            "surface": "c",
            "mode": "localhost_udp",
            "status": c_route["status"],
            "notes": "canonical sender truth file plus C UDP receiver verification report"
            if "report" in c_route
            else c_route["notes"],
            **c_route,
        },
        {
            "surface": "cpp",
            "mode": "localhost_udp",
            "status": cpp_route["status"],
            "notes": "canonical sender truth file plus C++ native UDP receiver verification report"
            if "report" in cpp_route
            else cpp_route["notes"],
            **cpp_route,
        },
        godot_route,
        unreal_route,
    ]
    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "routes": routes,
    }
    json_path = out_dir / "network_ingest_matrix.json"
    md_path = out_dir / "network_ingest_matrix.md"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    failing_statuses = {row["status"] for row in routes if row["status"] == "failed"}
    return 0 if not failing_statuses and python_route["status"] == "passed" and c_route["status"] in {"passed", "pending"} and cpp_route["status"] in {"passed", "pending"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
