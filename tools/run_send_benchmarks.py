#!/usr/bin/env python3
"""Run localhost outbound sender benchmarks for fastdis surfaces."""

from __future__ import annotations

import argparse
from datetime import UTC
from datetime import datetime
import json
import math
import os
from pathlib import Path
import socket
import statistics
import subprocess
import sys
import tempfile
import threading
import time

import godot_env
from run_network_send_matrix import C_SENDER, CPP_SENDER, ROOT, build_truth_and_replay


DEFAULT_OUT_DIR = ROOT / "benchmark_reports" / "alpha3_send_matrix"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    parser.add_argument("--packets", type=int, default=2000)
    parser.add_argument("--entity-count", type=int, default=32)
    parser.add_argument("--rounds", type=int, default=3)
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--skip-godot", action="store_true")
    return parser.parse_args()


def display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def python_env() -> dict[str, str]:
    env = os.environ.copy()
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(ROOT / "src") + (os.pathsep + existing if existing else "")
    return env


def percentile(samples: list[float], q: float) -> float:
    if not samples:
        return 0.0
    ordered = sorted(samples)
    if len(ordered) == 1:
        return ordered[0]
    position = (max(0.0, min(100.0, q)) / 100.0) * (len(ordered) - 1)
    lower = int(math.floor(position))
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * weight


def ephemeral_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def godot_command() -> str | None:
    return godot_env.resolve_godot()


class UdpDrain:
    def __init__(self, port: int, expected_packets: int, timeout: float) -> None:
        self.port = port
        self.expected_packets = expected_packets
        self.timeout = timeout
        self.packets_received = 0
        self.bytes_received = 0
        self.error: str | None = None
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self) -> None:
        self._thread.start()

    def join(self) -> None:
        self._thread.join(timeout=self.timeout + 1.0)

    def _run(self) -> None:
        deadline = time.time() + self.timeout
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.bind(("127.0.0.1", self.port))
            sock.settimeout(0.2)
            while self.packets_received < self.expected_packets and time.time() < deadline:
                try:
                    data, _addr = sock.recvfrom(65535)
                except socket.timeout:
                    continue
                self.packets_received += 1
                self.bytes_received += len(data)
            if self.packets_received < self.expected_packets:
                self.error = f"expected {self.expected_packets} packets, received {self.packets_received}"
        finally:
            sock.close()


def run_case(name: str, cmd_builder, *, rounds: int, packets: int, timeout: float, env_builder=None) -> dict[str, object]:
    round_ms: list[float] = []
    bytes_received = 0
    packets_received = 0
    last_cmd: list[str] = []
    errors: list[str] = []
    for _round in range(rounds):
        port = ephemeral_port()
        drain = UdpDrain(port, packets, timeout)
        cmd = cmd_builder(port)
        env = python_env()
        if env_builder is not None:
            env.update(env_builder(port))
        last_cmd = cmd
        drain.start()
        start = time.perf_counter()
        completed = subprocess.run(
            cmd,
            cwd=ROOT,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        drain.join()
        if completed.returncode != 0:
            errors.append(f"command failed: {completed.returncode}")
            errors.append(completed.stdout.strip())
            break
        if drain.error:
            errors.append(drain.error)
            break
        round_ms.append(elapsed_ms)
        bytes_received = drain.bytes_received
        packets_received = drain.packets_received

    if round_ms:
        best_ms = min(round_ms)
        avg_ms = statistics.fmean(round_ms)
        best_pps = packets / (best_ms / 1000.0)
        avg_pps = packets / (avg_ms / 1000.0)
        mbps = (bytes_received / (best_ms / 1000.0)) / (1024.0 * 1024.0)
    else:
        best_ms = avg_ms = best_pps = avg_pps = mbps = 0.0

    return {
        "case": name,
        "command": last_cmd,
        "rounds": rounds,
        "packets": packets,
        "packets_received": packets_received,
        "bytes_received": bytes_received,
        "best_ms": best_ms,
        "avg_ms": avg_ms,
        "p50_ms": percentile(round_ms, 50.0),
        "p95_ms": percentile(round_ms, 95.0),
        "p99_ms": percentile(round_ms, 99.0),
        "worst_ms": max(round_ms) if round_ms else 0.0,
        "best_mpps": best_pps / 1_000_000.0,
        "avg_mpps": avg_pps / 1_000_000.0,
        "best_mbytes_per_sec": mbps,
        "status": "passed" if round_ms and not errors else "failed",
        "errors": errors,
    }


def render_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Alpha 3 Outbound Benchmark Report",
        "",
        f"- generated_at: `{payload['generated_at']}`",
        "",
        "| case | status | best Mpps | avg Mpps | p50 ms | p95 ms | MiB/s | packets |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in payload["results"]:
        lines.append(
            f"| {row['case']} | {row['status']} | {row['best_mpps']:.3f} | {row['avg_mpps']:.3f} | "
            f"{row['p50_ms']:.3f} | {row['p95_ms']:.3f} | {row['best_mbytes_per_sec']:.2f} | {row['packets_received']} |"
        )
    lines.extend(["", "## Notes", ""])
    lines.append("- These are localhost end-to-end sender benchmarks, not core parser hot-path benchmarks.")
    lines.append("- Unreal outbound remains a verification/smoke lane and is not included in this report.")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    out_dir = Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="fastdis_send_bench_") as tmp:
        truth_path, replay_path = build_truth_and_replay(Path(tmp), count=args.packets, entity_count=args.entity_count)
        _ = truth_path

        results: list[dict[str, object]] = []
        results.append(
            run_case(
                "python_send_entity",
                lambda port: [
                    sys.executable,
                    "-m",
                    "fastdis.tools.send_entity",
                    "--dst",
                    "127.0.0.1",
                    "--port",
                    str(port),
                    "--count",
                    str(args.packets),
                    "--entity-count",
                    str(args.entity_count),
                    "--entity",
                    "0",
                ],
                rounds=args.rounds,
                packets=args.packets,
                timeout=args.timeout,
            )
        )
        results.append(
            run_case(
                "python_replay_send",
                lambda port: [
                    sys.executable,
                    "-m",
                    "fastdis.tools.replay_send",
                    str(replay_path),
                    "--dst",
                    "127.0.0.1",
                    "--port",
                    str(port),
                ],
                rounds=args.rounds,
                packets=args.packets,
                timeout=args.timeout,
            )
        )
        if C_SENDER.is_file():
            results.append(
                run_case(
                    "c_udp_send",
                    lambda port: [str(C_SENDER), "127.0.0.1", str(port), str(replay_path), "--json"],
                    rounds=args.rounds,
                    packets=args.packets,
                    timeout=args.timeout,
                )
            )
        if CPP_SENDER.is_file():
            results.append(
                run_case(
                    "cpp_udp_send",
                    lambda port: [str(CPP_SENDER), "127.0.0.1", str(port), str(replay_path), "--json"],
                    rounds=args.rounds,
                    packets=args.packets,
                    timeout=args.timeout,
                )
            )
        if not args.skip_godot:
            godot = godot_command()
            if godot is not None:
                alias_root = godot_env.repo_alias_root(ROOT)
                results.append(
                    run_case(
                        "godot_udp_send",
                        lambda port: [
                            godot,
                            "--headless",
                            "--path",
                            str(alias_root / "packages" / "godot" / "fastdis_demo"),
                            "--script",
                            str(alias_root / "packages" / "godot" / "fastdis_demo" / "scripts" / "run_udp_send_smoke.gd"),
                        ],
                        rounds=args.rounds,
                        packets=args.packets,
                        timeout=max(args.timeout, 20.0),
                        env_builder=lambda port: {
                            **godot_env.build_env(),
                            "FASTDIS_GODOT_SEND_HOST": "127.0.0.1",
                            "FASTDIS_GODOT_SEND_PORT": str(port),
                            "FASTDIS_GODOT_SEND_REPLAY_PATH": str(replay_path),
                            "FASTDIS_GODOT_SEND_EXPECTED_PACKETS": str(args.packets),
                        },
                    )
                )

        payload = {
            "generated_at": datetime.now(UTC).isoformat(),
            "schema": "fastdis.send_benchmark_report.v1",
            "packets": args.packets,
            "entity_count": args.entity_count,
            "rounds": args.rounds,
            "results": results,
        }

        json_path = out_dir / "current.json"
        md_path = out_dir / "summary.md"
        json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        md_path.write_text(render_markdown(payload), encoding="utf-8")
        print(f"Wrote {display_path(json_path)}")
        print(f"Wrote {display_path(md_path)}")
        return 0 if all(row["status"] == "passed" for row in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
