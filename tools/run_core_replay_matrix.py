#!/usr/bin/env python3
"""Run the canonical core replay matrix for C and C++ surfaces."""

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

from fastdis import replay as replay_io
from fastdis.tools import send_entity
from fastdis.tools._shared import write_session_truth
from fastdis.tools.recv import verify_against_truth


DEFAULT_OUT_DIR = ROOT / "build" / "reports" / "core_replay_matrix"
C_REPLAY = ROOT / "build" / "fastdis_entity_table_c"
CPP_REPLAY = ROOT / "build" / "fastdis_raii_snapshot_buffer_cpp"
SCENARIO = "replay_latest_state_apply"
SCENARIO_SUITE = "core_matrix"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--if-available", action="store_true")
    parser.add_argument("--count", type=int, default=300)
    parser.add_argument("--entity-count", type=int, default=100)
    parser.add_argument("--rate-hz", type=float, default=30.0)
    return parser.parse_args(argv)


def display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def _build_truth_and_replay(*, scenario: str, count: int, entity_count: int, rate_hz: float, out_dir: Path) -> tuple[Path, Path, dict[str, Any]]:
    args = argparse.Namespace(
        count=count,
        entity_count=entity_count,
        rate_hz=rate_hz,
        site=100,
        application=1,
        entity=1,
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
    packets, _orientation_debug, truth = send_entity.build_packets(args)
    replay_path = out_dir / f"{scenario}.fastdispkt"
    truth_path = out_dir / f"{scenario}.truth.json"
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


def _run_surface(surface: str, binary: Path, replay_path: Path, truth: dict[str, Any]) -> dict[str, Any]:
    if not binary.is_file():
        return {
            "surface": surface,
            "mode": "replay",
            "scenario": SCENARIO,
            "scenario_suite": SCENARIO_SUITE,
            "status": "pending",
            "notes": f"{display_path(binary)} is not available yet",
        }
    cmd = [str(binary), str(replay_path), "--json"]
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
    payload = None
    try:
        payload = _json_from_output(completed.stdout)
        payload = _sort_latest_entities(payload)
        errors.extend(verify_against_truth(payload, truth))
    except Exception as exc:
        errors.append(f"{surface} replay JSON parse/verify failed: {exc}")
    return {
        "surface": surface,
        "mode": "replay",
        "scenario": SCENARIO,
        "scenario_suite": SCENARIO_SUITE,
        "status": "passed" if completed.returncode == 0 and not errors else "failed",
        "elapsed_seconds": elapsed_seconds,
        "command": cmd,
        "returncode": completed.returncode,
        "output": completed.stdout,
        "report": payload,
        "errors": errors,
        "truth": truth,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Core Replay Matrix",
        "",
        f"- generated_at: `{payload['generated_at']}`",
        "",
        "| surface | scenario | status | packets | unique_entities | errors |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for route in payload["routes"]:
        report = route.get("report") if isinstance(route.get("report"), dict) else {}
        errors = route.get("errors") if isinstance(route.get("errors"), list) else []
        lines.append(
            f"| {route.get('surface')} | {route.get('scenario')} | {route.get('status')} | "
            f"{report.get('packets_received')} | {report.get('unique_entities')} | {len(errors)} |"
        )
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="fastdis_core_replay_") as tmp:
        truth_path, replay_path, truth = _build_truth_and_replay(
            scenario=SCENARIO,
            count=args.count,
            entity_count=args.entity_count,
            rate_hz=args.rate_hz,
            out_dir=Path(tmp),
        )
        routes = [
            {
                **_run_surface("c", C_REPLAY, replay_path, truth),
                "truth_file": str(truth_path),
                "replay_file": str(replay_path),
            },
            {
                **_run_surface("cpp", CPP_REPLAY, replay_path, truth),
                "truth_file": str(truth_path),
                "replay_file": str(replay_path),
            },
        ]

    payload = {
        "schema": "fastdis.core_replay_matrix.v1",
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "scenario": SCENARIO,
        "scenario_suite": SCENARIO_SUITE,
        "routes": routes,
    }
    json_path = out_dir / "core_replay_matrix.json"
    md_path = out_dir / "core_replay_matrix.md"
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
