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
import re
import socket
import subprocess
import sys
import tempfile
import time

import evidence_layout
import load_local_env


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = evidence_layout.ALPHA3_CURRENT_DIR
CPP_RECEIVER = ROOT / "build" / "fastdis_udp_burst_cpp"
C_RECEIVER = ROOT / "build" / "fastdis_udp_burst_c"
CORE_SCENARIO_NAME = "entity_state_1x10hz"
CORE_SCENARIO_SUITE = "core_matrix"
CORE_SCENARIO_RATE_HZ = 10.0
CORE_ROUTE_CONFIGS = (
    {
        "scenario": "entity_state_1x10hz",
        "count": 24,
        "entity_count": 1,
        "rate_hz": 10.0,
        "timeout": 2.0,
    },
    {
        "scenario": "entity_state_100x30hz",
        "count": 300,
        "entity_count": 100,
        "rate_hz": 30.0,
        "timeout": 5.0,
    },
    {
        "scenario": "entity_state_1000x60hz",
        "count": 1000,
        "entity_count": 1000,
        "rate_hz": 60.0,
        "timeout": 12.0,
    },
)
GODOT_FILTER_ROUTE = {
    "scenario": "filter_reject_90pct",
    "accepted_count": 30,
    "accepted_entity_count": 30,
    "rejected_count": 270,
    "rejected_entity_count": 270,
    "rate_hz": 30.0,
    "timeout": 12.0,
    "allowed_force_ids": (1,),
    "rejected_force_id": 3,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    parser.add_argument("--count", type=int, default=24)
    parser.add_argument("--entity-count", type=int, default=1)
    parser.add_argument("--core-rate-hz", type=float, default=CORE_SCENARIO_RATE_HZ)
    parser.add_argument("--engine-entity-count", type=int, default=1)
    parser.add_argument("--timeout", type=float, default=2.0)
    parser.add_argument("--unreal-engine-version", default="5.8")
    parser.add_argument(
        "--core-only",
        action="store_true",
        help="Run only the shared core lane: python/c/cpp localhost UDP plus Godot live UDP, while skipping Unreal",
    )
    parser.add_argument(
        "--if-available",
        action="store_true",
        help="Exit successfully when the required core localhost routes pass even if optional engine routes are pending, skipped, or failed with captured evidence",
    )
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


def _live_runner_wall_timeout(*, count: int, rate_hz: float, smoke_timeout: float) -> float:
    expected_duration = 0.0
    if rate_hz > 0.0 and count > 0:
        expected_duration = count / rate_hz
    return max(smoke_timeout + 120.0, expected_duration + smoke_timeout + 150.0)


def _slug(value: object) -> str:
    text = str(value or "unknown").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_") or "unknown"


def _persist_route_truth(route: dict[str, object], out_dir: Path) -> dict[str, object]:
    truth = route.get("truth")
    if not isinstance(truth, dict):
        return route
    truth_dir = out_dir / "truth"
    truth_dir.mkdir(parents=True, exist_ok=True)
    truth_path = truth_dir / f"{_slug(route.get('surface'))}_{_slug(route.get('mode'))}_{_slug(route.get('scenario'))}.truth.json"
    truth_path.write_text(json.dumps(truth, indent=2) + "\n", encoding="utf-8")
    updated = dict(route)
    updated["truth"] = truth
    updated["truth_file"] = str(truth_path)
    return updated


def run_python_udp_route(*, count: int, entity_count: int, timeout: float, rate_hz: float, scenario: str) -> dict[str, object]:
    port = _ephemeral_port()
    started = time.perf_counter()
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
                "--rate-hz",
                str(rate_hz),
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
            truth = json.loads(truth_path.read_text(encoding="utf-8"))
        except Exception as exc:  # pragma: no cover - defensive path for report generation
            errors.append(f"receiver JSON parse failed: {exc}")
        return {
            "surface": "python",
            "mode": "localhost_udp",
            "scenario": scenario,
            "scenario_suite": CORE_SCENARIO_SUITE,
            "status": status if not errors else "failed",
            "elapsed_seconds": time.perf_counter() - started,
            "truth_file": str(truth_path),
            "send_command": send_cmd,
            "recv_command": recv_cmd,
            "send_returncode": send_completed.returncode,
            "recv_returncode": recv_proc.returncode,
            "send_output": send_completed.stdout,
            "recv_output": recv_stdout,
            "report": report,
            "errors": errors,
            "truth": truth if "truth" in locals() else None,
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


def run_cpp_udp_route(*, count: int, entity_count: int, timeout: float, rate_hz: float, scenario: str) -> dict[str, object]:
    if not CPP_RECEIVER.is_file():
        return {
            "surface": "cpp",
            "mode": "localhost_udp",
            "status": "pending",
            "notes": "build/fastdis_udp_burst_cpp is not available yet",
        }
    port = _ephemeral_port()
    started = time.perf_counter()
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
                "--rate-hz",
                str(rate_hz),
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
            "scenario": scenario,
            "scenario_suite": CORE_SCENARIO_SUITE,
            "status": "passed" if recv_proc.returncode == 0 and send_completed.returncode == 0 and not errors else "failed",
            "elapsed_seconds": time.perf_counter() - started,
            "truth_file": str(truth_path),
            "send_command": send_cmd,
            "recv_command": recv_cmd,
            "send_returncode": send_completed.returncode,
            "recv_returncode": recv_proc.returncode,
            "send_output": send_completed.stdout,
            "recv_output": recv_stdout,
            "report": report,
            "errors": errors,
            "truth": truth if "truth" in locals() else None,
        }


def run_c_udp_route(*, count: int, entity_count: int, timeout: float, rate_hz: float, scenario: str) -> dict[str, object]:
    if not C_RECEIVER.is_file():
        return {
            "surface": "c",
            "mode": "localhost_udp",
            "status": "pending",
            "notes": "build/fastdis_udp_burst_c is not available yet",
        }
    port = _ephemeral_port()
    started = time.perf_counter()
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
                "--rate-hz",
                str(rate_hz),
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
            "scenario": scenario,
            "scenario_suite": CORE_SCENARIO_SUITE,
            "status": "passed" if recv_proc.returncode == 0 and send_completed.returncode == 0 and not errors else "failed",
            "elapsed_seconds": time.perf_counter() - started,
            "truth_file": str(truth_path),
            "send_command": send_cmd,
            "recv_command": recv_cmd,
            "send_returncode": send_completed.returncode,
            "recv_returncode": recv_proc.returncode,
            "send_output": send_completed.stdout,
            "recv_output": recv_stdout,
            "report": report,
            "errors": errors,
            "truth": truth if "truth" in locals() else None,
        }


def _runner_payload(command: list[str], *, wall_timeout: float | None = None) -> dict[str, object]:
    completed = subprocess.run(
        command,
        cwd=ROOT,
        env=_python_env(),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
        timeout=wall_timeout,
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


def run_godot_live_udp_route(
    *,
    count: int,
    entity_count: int,
    timeout: float,
    rate_hz: float,
    scenario: str,
    allowed_force_ids: tuple[int, ...] = (),
    rejected_count: int = 0,
    rejected_entity_count: int = 0,
    rejected_force_id: int = 3,
) -> dict[str, object]:
    command = [
        sys.executable,
        str(ROOT / "tools" / "run_godot_udp_smoke.py"),
        "--scenario",
        scenario,
        "--count",
        str(count),
        "--entity-count",
        str(entity_count),
        "--rate-hz",
        str(rate_hz),
        "--timeout",
        str(max(5.0, timeout + 3.0)),
    ]
    for force_id in allowed_force_ids:
        command.extend(["--allowed-force-id", str(force_id)])
    if rejected_count > 0:
        command.extend(["--rejected-count", str(rejected_count)])
    if rejected_entity_count > 0:
        command.extend(["--rejected-entity-count", str(rejected_entity_count)])
    if rejected_force_id != 3:
        command.extend(["--rejected-force-id", str(rejected_force_id)])
    result = _runner_payload(
        command,
        wall_timeout=_live_runner_wall_timeout(
            count=count + max(rejected_count, 0),
            rate_hz=rate_hz,
            smoke_timeout=max(5.0, timeout + 3.0),
        ),
    )
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
        "scenario": scenario,
        "scenario_suite": CORE_SCENARIO_SUITE,
        "status": payload.get("status", "failed"),
        "notes": f"headless Godot localhost UDP smoke route using FastDisWorld for {scenario}",
        "recv_command": command,
        "recv_returncode": result["returncode"],
        "recv_output": result["output"],
        **payload,
    }


def run_unreal_live_udp_route(*, count: int, entity_count: int, timeout: float, engine_version: str, rate_hz: float, scenario: str) -> dict[str, object]:
    if platform.system().lower() != "darwin":
        return {
            "surface": "unreal",
            "mode": "live_udp",
            "scenario": scenario,
            "scenario_suite": CORE_SCENARIO_SUITE,
            "status": "skipped-by-platform",
            "notes": "Unreal automation smoke runner is only wired on macOS in this repo today",
        }
    smoke_timeout = max(20.0, timeout + 18.0)
    command = [
        sys.executable,
        str(ROOT / "tools" / "run_unreal_udp_smoke.py"),
        "--engine-version",
        engine_version,
        "--scenario",
        scenario,
        "--count",
        str(count),
        "--entity-count",
        str(entity_count),
        "--rate-hz",
        str(rate_hz),
        "--timeout",
        str(smoke_timeout),
    ]
    result = _runner_payload(
        command,
        wall_timeout=_live_runner_wall_timeout(count=count, rate_hz=rate_hz, smoke_timeout=smoke_timeout),
    )
    if result["payload"] is None:
        output = result["output"]
        blocked = (
            "Operation not permitted" in output
            or "Access to the path" in output
            or "UnauthorizedAccessException" in output
        )
        return {
            "surface": "unreal",
            "mode": "live_udp",
            "scenario": scenario,
            "scenario_suite": CORE_SCENARIO_SUITE,
            "status": "pending" if blocked else ("failed" if result["returncode"] else "pending"),
            "notes": (
                "Unreal runner could not build or launch the UDP smoke harness on this host; treat as pending host-environment work."
                if blocked
                else "Unreal runner did not emit a parseable JSON payload"
            ),
            "recv_command": command,
            "recv_returncode": result["returncode"],
            "recv_output": output,
            "errors": result["errors"],
        }
    payload = result["payload"]
    return {
        "surface": "unreal",
        "mode": "live_udp",
        "scenario": scenario,
        "scenario_suite": CORE_SCENARIO_SUITE,
        "status": payload.get("status", "failed"),
        "notes": f"Unreal {engine_version} localhost UDP automation smoke route using UFastDisWorldSubsystem for {scenario}",
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
        "| Surface | Mode | Scenario | Status | Notes |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in report["routes"]:
        lines.append(f"| {row['surface']} | {row['mode']} | {row.get('scenario')} | {row['status']} | {row['notes']} |")
    lines.extend(["", "## Route Details", ""])
    for row in report["routes"]:
        lines.extend(
            [
                f"### {row['surface']} / {row['mode']} / {row.get('scenario')}",
                "",
                f"- status: `{row['status']}`",
                f"- scenario: `{row.get('scenario')}`",
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


def _core_route_specs(args: argparse.Namespace) -> list[dict[str, object]]:
    specs: list[dict[str, object]] = []
    for config in CORE_ROUTE_CONFIGS:
        specs.append(
            {
                "scenario": str(config["scenario"]),
                "count": int(config["count"]),
                "entity_count": int(config["entity_count"]),
                "rate_hz": float(config["rate_hz"]),
                "timeout": max(float(args.timeout), float(config["timeout"])),
            }
        )
    return specs


def main() -> int:
    load_local_env.load()
    args = parse_args()
    out_dir = Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    routes: list[dict[str, object]] = []
    core_specs = _core_route_specs(args)
    for spec in core_specs:
        python_route = run_python_udp_route(
            count=int(spec["count"]),
            entity_count=int(spec["entity_count"]),
            timeout=float(spec["timeout"]),
            rate_hz=float(spec["rate_hz"]),
            scenario=str(spec["scenario"]),
        )
        c_route = run_c_udp_route(
            count=int(spec["count"]),
            entity_count=int(spec["entity_count"]),
            timeout=float(spec["timeout"]),
            rate_hz=float(spec["rate_hz"]),
            scenario=str(spec["scenario"]),
        )
        cpp_route = run_cpp_udp_route(
            count=int(spec["count"]),
            entity_count=int(spec["entity_count"]),
            timeout=float(spec["timeout"]),
            rate_hz=float(spec["rate_hz"]),
            scenario=str(spec["scenario"]),
        )
        routes.extend(
            [
                {
                    "surface": "python",
                    "mode": "localhost_udp",
                    "status": python_route["status"],
                    "notes": f"canonical sender truth file plus Python receiver verification report for {spec['scenario']}",
                    **python_route,
                },
                {
                    "surface": "c",
                    "mode": "localhost_udp",
                    "status": c_route["status"],
                    "notes": f"canonical sender truth file plus C UDP receiver verification report for {spec['scenario']}"
                    if "report" in c_route
                    else c_route["notes"],
                    **c_route,
                },
                {
                    "surface": "cpp",
                    "mode": "localhost_udp",
                    "status": cpp_route["status"],
                    "notes": f"canonical sender truth file plus C++ native UDP receiver verification report for {spec['scenario']}"
                    if "report" in cpp_route
                    else cpp_route["notes"],
                    **cpp_route,
                },
            ]
        )
    for spec in core_specs:
        routes.append(
            run_godot_live_udp_route(
                count=int(spec["count"]),
                entity_count=int(spec["entity_count"]),
                timeout=float(spec["timeout"]),
                rate_hz=float(spec["rate_hz"]),
                scenario=str(spec["scenario"]),
            )
        )
    routes.append(
        run_godot_live_udp_route(
            count=int(GODOT_FILTER_ROUTE["accepted_count"]),
            entity_count=int(GODOT_FILTER_ROUTE["accepted_entity_count"]),
            timeout=max(float(args.timeout), float(GODOT_FILTER_ROUTE["timeout"])),
            rate_hz=float(GODOT_FILTER_ROUTE["rate_hz"]),
            scenario=str(GODOT_FILTER_ROUTE["scenario"]),
            allowed_force_ids=tuple(int(value) for value in GODOT_FILTER_ROUTE["allowed_force_ids"]),
            rejected_count=int(GODOT_FILTER_ROUTE["rejected_count"]),
            rejected_entity_count=int(GODOT_FILTER_ROUTE["rejected_entity_count"]),
            rejected_force_id=int(GODOT_FILTER_ROUTE["rejected_force_id"]),
        )
    )
    if not args.core_only:
        for spec in core_specs:
            routes.append(
                run_unreal_live_udp_route(
                    count=int(spec["count"]),
                    entity_count=int(spec["entity_count"]),
                    timeout=float(spec["timeout"]),
                    engine_version=args.unreal_engine_version,
                    rate_hz=float(spec["rate_hz"]),
                    scenario=str(spec["scenario"]),
                )
            )
    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "routes": [_persist_route_truth(route, out_dir) for route in routes],
    }
    json_path = out_dir / "network_ingest_matrix.json"
    md_path = out_dir / "network_ingest_matrix.md"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    python_routes = [row for row in routes if row["surface"] == "python" and row["mode"] == "localhost_udp"]
    c_routes = [row for row in routes if row["surface"] == "c" and row["mode"] == "localhost_udp"]
    cpp_routes = [row for row in routes if row["surface"] == "cpp" and row["mode"] == "localhost_udp"]
    failing_statuses = {row["status"] for row in routes if row["status"] == "failed"}
    if (
        not failing_statuses
        and python_routes
        and all(row["status"] == "passed" for row in python_routes)
        and all(row["status"] in {"passed", "pending"} for row in c_routes)
        and all(row["status"] in {"passed", "pending"} for row in cpp_routes)
    ):
        return 0
    if args.if_available:
        optional_routes = [row for row in routes if row["surface"] not in {"python", "c", "cpp"}]
        if (
            python_routes
            and all(row["status"] == "passed" for row in python_routes)
            and all(row["status"] in {"passed", "pending"} for row in c_routes)
            and all(row["status"] in {"passed", "pending"} for row in cpp_routes)
            and all(str(row["status"]) in {"passed", "pending", "skipped-by-platform", "failed"} for row in optional_routes)
        ):
            return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
