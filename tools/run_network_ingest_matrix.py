#!/usr/bin/env python3
"""Generate an Alpha 3 network-ingest verification matrix."""

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

import load_local_env


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = ROOT / "verification_reports" / "alpha3_current"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    parser.add_argument("--count", type=int, default=24)
    parser.add_argument("--entity-count", type=int, default=3)
    parser.add_argument("--timeout", type=float, default=2.0)
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
    routes = [
        {
            "surface": "python",
            "mode": "localhost_udp",
            "status": python_route["status"],
            "notes": "canonical sender truth file plus Python receiver verification report",
            **python_route,
        },
        {
            "surface": "godot",
            "mode": "live_udp",
            "status": "pending",
            "notes": "replay-driven demo route exists, but live UDP engine ingest verification is not yet wired",
        },
        {
            "surface": "unreal",
            "mode": "live_udp",
            "status": "pending",
            "notes": "replay/demo harness exists, but live UDP plugin ingest verification is not yet wired",
        },
        {
            "surface": "cpp",
            "mode": "localhost_udp",
            "status": "pending",
            "notes": "UDP burst example exists; canonical truth-file verification contract not yet implemented for native CLI output",
        },
        {
            "surface": "c",
            "mode": "localhost_udp",
            "status": "pending",
            "notes": "no canonical C receiver verification tool exists yet",
        },
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
    return 0 if python_route["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
