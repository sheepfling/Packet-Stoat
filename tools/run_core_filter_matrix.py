#!/usr/bin/env python3
"""Run the canonical core filtering matrix for C, C++, and Python ctypes."""

from __future__ import annotations

import argparse
from datetime import UTC
from datetime import datetime
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from fastdis import native
from fastdis import replay as replay_io
from fastdis.tools import send_entity
from fastdis.tools._shared import write_session_truth


DEFAULT_OUT_DIR = ROOT / "build" / "reports" / "core_filter_matrix"
C_FILTER = ROOT / "build" / "fastdis_entity_state_scan_c"
CPP_FILTER = ROOT / "build" / "fastdis_scan_file_cpp"
SCENARIO = "filter_reject_90pct"
SCENARIO_SUITE = "core_matrix"
ALLOWED_FORCE_ID = 1
REJECTED_FORCE_ID = 3


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--if-available", action="store_true")
    parser.add_argument("--count", type=int, default=300)
    parser.add_argument("--accepted-count", type=int, default=30)
    return parser.parse_args(argv)


def display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def _send_args(*, count: int, entity_count: int, entity: int, force_id: int) -> argparse.Namespace:
    return argparse.Namespace(
        count=count,
        entity_count=entity_count,
        rate_hz=30.0,
        site=100,
        application=1,
        entity=entity,
        force_id=force_id,
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


def _build_truth_and_replay(*, count: int, accepted_count: int, out_dir: Path) -> tuple[Path, Path, dict[str, Any]]:
    rejected_count = count - accepted_count
    accepted_packets, _debug, accepted_truth = send_entity.build_packets(
        _send_args(
            count=accepted_count,
            entity_count=max(accepted_count, 1),
            entity=1,
            force_id=ALLOWED_FORCE_ID,
        )
    )
    rejected_packets, _debug, _rejected_truth = send_entity.build_packets(
        _send_args(
            count=max(rejected_count, 0),
            entity_count=max(rejected_count, 1),
            entity=1000,
            force_id=REJECTED_FORCE_ID,
        )
    )
    packets = list(accepted_packets) + list(rejected_packets)
    replay_path = out_dir / f"{SCENARIO}.fastdispkt"
    truth_path = out_dir / f"{SCENARIO}.truth.json"
    truth = {
        "schema": "fastdis.recv_truth.v1",
        "packet_count": len(packets),
        "packets_parsed": len(packets),
        "entity_state": len(accepted_packets),
        "malformed": 0,
        "unique_entities": accepted_truth["unique_entities"],
        "latest_entities": accepted_truth["latest_entities"],
        "scenario": SCENARIO,
        "scenario_suite": SCENARIO_SUITE,
        "allowed_force_ids": [ALLOWED_FORCE_ID],
    }
    replay_io.write_v1_packets(replay_path, packets)
    write_session_truth(truth_path, truth)
    return truth_path, replay_path, truth


def _json_from_output(output: str) -> dict[str, Any]:
    start = output.find("{")
    if start < 0:
        raise ValueError("no JSON object found in process output")
    return json.loads(output[start:])


def _sort_latest_entities(payload: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(payload, dict):
        return payload
    rows = payload.get("latest_entities")
    if not isinstance(rows, list):
        return payload
    payload["latest_entities"] = sorted(
        [row for row in rows if isinstance(row, dict)],
        key=lambda row: (
            int(row.get("site", 0)),
            int(row.get("application", 0)),
            int(row.get("entity", 0)),
        ),
    )
    return payload


def _verify_against_truth(report: dict[str, Any], truth: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    checks = {
        "packets_received": truth["packet_count"],
        "packets_parsed": truth["packets_parsed"],
        "packets_accepted": truth["entity_state"],
        "malformed": truth["malformed"],
        "unique_entities": truth["unique_entities"],
    }
    for field, expected in checks.items():
        if report.get(field) != expected:
            errors.append(f"{field}: expected {expected}, got {report.get(field)}")
    expected_rejected = truth["packets_parsed"] - truth["entity_state"] - truth["malformed"]
    if report.get("packets_rejected") != expected_rejected:
        errors.append(f"packets_rejected: expected {expected_rejected}, got {report.get('packets_rejected')}")
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


def _run_native_python_filter(truth: dict[str, Any], replay_path: Path) -> dict[str, Any]:
    started = time.perf_counter()
    packets = replay_io.read_v1_packets(replay_path)
    lib = native.load_native()
    config = lib.new_config(entity_state_fields=native.FASTDIS_ES_FIELD_POSE, entity_force_ids=[ALLOWED_FORCE_ID])
    rows, stats = lib.scan_entity_state_to_batch(packets, config=config, return_stats=True)
    elapsed_seconds = time.perf_counter() - started
    report = {
        "surface": "python_ctypes",
        "mode": "filtering",
        "packets_received": len(packets),
        "packets_parsed": int(stats["seen"]),
        "packets_accepted": int(stats["accepted"]),
        "packets_rejected": int(stats["seen"] - stats["accepted"] - stats["malformed"]),
        "malformed": int(stats["malformed"]),
        "unique_entities": len(rows),
        "latest_entities": [
            {
                "site": int(row.entity_id[0]),
                "application": int(row.entity_id[1]),
                "entity": int(row.entity_id[2]),
                "force_id": int(row.force_id),
                "location_ecef_m": [float(row.location[0]), float(row.location[1]), float(row.location[2])],
                "orientation_dis_rad": [
                    float(row.orientation[0]),
                    float(row.orientation[1]),
                    float(row.orientation[2]),
                ],
            }
            for row in rows
        ],
        "errors": [],
    }
    errors = _verify_against_truth(_sort_latest_entities(report) or {}, truth)
    return {
        "surface": "python_ctypes",
        "mode": "filtering",
        "scenario": SCENARIO,
        "scenario_suite": SCENARIO_SUITE,
        "status": "passed" if not errors else "failed",
        "elapsed_seconds": elapsed_seconds,
        "report": report,
        "errors": errors,
        "truth": truth,
    }


def _run_native_python_filter_if_available(
    truth: dict[str, Any],
    replay_path: Path,
    *,
    if_available: bool,
) -> dict[str, Any]:
    try:
        return _run_native_python_filter(truth, replay_path)
    except Exception as exc:
        if not if_available:
            raise
        return {
            "surface": "python_ctypes",
            "mode": "filtering",
            "scenario": SCENARIO,
            "scenario_suite": SCENARIO_SUITE,
            "status": "pending",
            "notes": f"python ctypes filter lane unavailable on this host: {type(exc).__name__}: {exc}",
            "errors": [f"{type(exc).__name__}: {exc}"],
            "truth": truth,
        }


def _run_binary_surface(surface: str, binary: Path, replay_path: Path, truth: dict[str, Any]) -> dict[str, Any]:
    if not binary.is_file():
        return {
            "surface": surface,
            "mode": "filtering",
            "scenario": SCENARIO,
            "scenario_suite": SCENARIO_SUITE,
            "status": "pending",
            "notes": f"{display_path(binary)} is not available yet",
        }
    cmd = [str(binary), str(replay_path), "--json", "--allow-force-id", str(ALLOWED_FORCE_ID)]
    started = time.perf_counter()
    completed = subprocess.run(
        cmd,
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    elapsed_seconds = time.perf_counter() - started
    errors: list[str] = []
    report = None
    try:
        report = _sort_latest_entities(_json_from_output(completed.stdout))
        errors.extend(_verify_against_truth(report or {}, truth))
    except Exception as exc:
        errors.append(f"{surface} filtering JSON parse/verify failed: {exc}")
    return {
        "surface": surface,
        "mode": "filtering",
        "scenario": SCENARIO,
        "scenario_suite": SCENARIO_SUITE,
        "status": "passed" if completed.returncode == 0 and not errors else "failed",
        "elapsed_seconds": elapsed_seconds,
        "command": cmd,
        "returncode": completed.returncode,
        "output": completed.stdout,
        "report": report,
        "errors": errors,
        "truth": truth,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Core Filter Matrix",
        "",
        f"- generated_at: `{payload['generated_at']}`",
        "",
        "| surface | scenario | status | accepted | rejected | malformed | errors |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for route in payload["routes"]:
        report = route.get("report") if isinstance(route.get("report"), dict) else {}
        errors = route.get("errors") if isinstance(route.get("errors"), list) else []
        lines.append(
            f"| {route.get('surface')} | {route.get('scenario')} | {route.get('status')} | "
            f"{report.get('packets_accepted')} | {report.get('packets_rejected')} | {report.get('malformed')} | {len(errors)} |"
        )
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="fastdis_core_filter_") as tmp:
        truth_path, replay_path, truth = _build_truth_and_replay(
            count=args.count,
            accepted_count=args.accepted_count,
            out_dir=Path(tmp),
        )
        routes = [
            {
                **_run_binary_surface("c", C_FILTER, replay_path, truth),
                "truth_file": str(truth_path),
                "replay_file": str(replay_path),
            },
            {
                **_run_binary_surface("cpp", CPP_FILTER, replay_path, truth),
                "truth_file": str(truth_path),
                "replay_file": str(replay_path),
            },
            {
                **_run_native_python_filter_if_available(
                    truth,
                    replay_path,
                    if_available=bool(args.if_available),
                ),
                "truth_file": str(truth_path),
                "replay_file": str(replay_path),
            },
        ]

    payload = {
        "schema": "fastdis.core_filter_matrix.v1",
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "scenario": SCENARIO,
        "scenario_suite": SCENARIO_SUITE,
        "routes": routes,
    }
    json_path = args.out_dir / "core_filter_matrix.json"
    md_path = args.out_dir / "core_filter_matrix.md"
    json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(payload) + "\n", encoding="utf-8")
    print(f"json: {display_path(json_path)}")
    print(f"md: {display_path(md_path)}")

    failing = [route for route in routes if route.get("status") not in {"passed", "pending"}]
    pending = [route for route in routes if route.get("status") == "pending"]
    if failing:
        return 1
    if pending and not args.if_available:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
