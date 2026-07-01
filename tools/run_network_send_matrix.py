#!/usr/bin/env python3
"""Generate an Alpha 3 network-send verification matrix."""

from __future__ import annotations

import argparse
from datetime import UTC
from datetime import datetime
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time

import evidence_layout

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from fastdis.replay import write_v1_packets  # noqa: E402
from fastdis.tools.send_entity import build_packets  # noqa: E402


DEFAULT_OUT_DIR = evidence_layout.ALPHA3_CURRENT_DIR
C_SENDER = ROOT / "build" / "fastdis_udp_send_c"
CPP_SENDER = ROOT / "build" / "fastdis_udp_send_cpp"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    parser.add_argument("--count", type=int, default=24)
    parser.add_argument("--entity-count", type=int, default=3)
    parser.add_argument("--timeout", type=float, default=2.0)
    return parser.parse_args()


def display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def _python_env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC) + os.pathsep + env.get("PYTHONPATH", "")
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


def build_truth_and_replay(tmp: Path, *, count: int, entity_count: int) -> tuple[Path, Path]:
    args = argparse.Namespace(
        dst="127.0.0.1",
        port=0,
        count=count,
        entity_count=entity_count,
        rate_hz=0.0,
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
    packets, _orientation, truth = build_packets(args)
    truth_path = tmp / "expected_session.json"
    replay_path = tmp / "expected_session.fastdispkt"
    truth_path.write_text(json.dumps(truth, indent=2) + "\n", encoding="utf-8")
    write_v1_packets(replay_path, packets)
    return truth_path, replay_path


def run_verified_send(send_cmd: list[str], *, truth_path: Path, port: int, count: int, timeout: float) -> dict[str, object]:
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
        "send-matrix",
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
        send_completed = subprocess.run(
            send_cmd,
            cwd=ROOT,
            env=_python_env(),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
        recv_stdout, _ = recv_proc.communicate(timeout=timeout + 3.0)
    finally:
        if recv_proc.poll() is None:
            recv_proc.kill()
    errors: list[str] = []
    recv_report = None
    try:
        recv_report = _json_from_stdout(recv_stdout)
    except Exception as exc:
        errors.append(f"receiver JSON parse failed: {exc}")
    send_report = None
    try:
        send_report = _json_from_stdout(send_completed.stdout)
    except Exception:
        send_report = None
    return {
        "status": "passed" if recv_proc.returncode == 0 and send_completed.returncode == 0 and not errors else "failed",
        "truth_file": str(truth_path),
        "send_command": send_cmd,
        "recv_command": recv_cmd,
        "send_returncode": send_completed.returncode,
        "recv_returncode": recv_proc.returncode,
        "send_output": send_completed.stdout,
        "recv_output": recv_stdout,
        "send_report": send_report,
        "recv_report": recv_report,
        "errors": errors,
    }


def run_python_send_route(*, count: int, entity_count: int, timeout: float) -> dict[str, object]:
    port = _ephemeral_port()
    with tempfile.TemporaryDirectory(prefix="fastdis_send_matrix_py_") as tmp:
        truth_path, _replay_path = build_truth_and_replay(Path(tmp), count=count, entity_count=entity_count)
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
        route = run_verified_send(send_cmd, truth_path=truth_path, port=port, count=count, timeout=timeout)
        return {"surface": "python", "mode": "localhost_udp_send", **route}


def run_c_send_route(*, count: int, entity_count: int, timeout: float) -> dict[str, object]:
    if not C_SENDER.is_file():
        return {"surface": "c", "mode": "localhost_udp_send", "status": "pending", "notes": "build/fastdis_udp_send_c is not available yet"}
    port = _ephemeral_port()
    with tempfile.TemporaryDirectory(prefix="fastdis_send_matrix_c_") as tmp:
        truth_path, replay_path = build_truth_and_replay(Path(tmp), count=count, entity_count=entity_count)
        send_cmd = [str(C_SENDER), "127.0.0.1", str(port), str(replay_path), "--json"]
        route = run_verified_send(send_cmd, truth_path=truth_path, port=port, count=count, timeout=timeout)
        return {"surface": "c", "mode": "localhost_udp_send", **route}


def run_cpp_send_route(*, count: int, entity_count: int, timeout: float) -> dict[str, object]:
    if not CPP_SENDER.is_file():
        return {"surface": "cpp", "mode": "localhost_udp_send", "status": "pending", "notes": "build/fastdis_udp_send_cpp is not available yet"}
    port = _ephemeral_port()
    with tempfile.TemporaryDirectory(prefix="fastdis_send_matrix_cpp_") as tmp:
        truth_path, replay_path = build_truth_and_replay(Path(tmp), count=count, entity_count=entity_count)
        send_cmd = [str(CPP_SENDER), "127.0.0.1", str(port), str(replay_path), "--json"]
        route = run_verified_send(send_cmd, truth_path=truth_path, port=port, count=count, timeout=timeout)
        return {"surface": "cpp", "mode": "localhost_udp_send", **route}


def render_markdown(report: dict[str, object]) -> str:
    lines = [
        "# Alpha 3 Network Send Matrix",
        "",
        f"- generated_at: `{report['generated_at']}`",
        "",
        "| Surface | Mode | Status | Notes |",
        "| --- | --- | --- | --- |",
    ]
    for route in report["routes"]:
        lines.append(f"| {route['surface']} | {route['mode']} | {route['status']} | {route.get('notes', 'truth-based sender verification route')} |")
    lines.extend(["", "## Route Details", ""])
    for route in report["routes"]:
        lines.append(f"### {route['surface']} / {route['mode']}")
        lines.append("")
        lines.append(f"- status: `{route['status']}`")
        if "notes" in route:
            lines.append(f"- notes: {route['notes']}")
        if "send_command" in route:
            lines.append(f"- send_command: `{' '.join(route['send_command'])}`")
        if "recv_command" in route:
            lines.append(f"- recv_command: `{' '.join(route['recv_command'])}`")
        recv_report = route.get("recv_report")
        if recv_report is not None:
            lines.extend(["", "```json", json.dumps(recv_report, indent=2), "```"])
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    out_dir = Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    routes = [
        run_python_send_route(count=args.count, entity_count=args.entity_count, timeout=args.timeout),
        run_c_send_route(count=args.count, entity_count=args.entity_count, timeout=args.timeout),
        run_cpp_send_route(count=args.count, entity_count=args.entity_count, timeout=args.timeout),
    ]
    overall_status = "passed" if all(route["status"] == "passed" for route in routes) else "failed"
    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "overall_status": overall_status,
        "routes": routes,
    }
    json_path = out_dir / "network_send_matrix.json"
    md_path = out_dir / "network_send_matrix.md"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    print(f"Wrote {display_path(json_path)}")
    print(f"Wrote {display_path(md_path)}")
    return 0 if overall_status == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
