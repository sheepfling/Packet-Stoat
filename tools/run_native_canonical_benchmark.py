#!/usr/bin/env python3
"""Generate a truth-backed native canonical benchmark sidecar for the shared engine matrix."""

from __future__ import annotations

import argparse
import json
import platform
from pathlib import Path
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from fastdis import replay
from fastdis.tools import send_entity
from fastdis.tools.recv import verify_against_truth


DEFAULT_BUILD_DIR = ROOT / "build"
DEFAULT_REPLAY_PATH = ROOT / "build" / "reports" / "engine_benchmark_sources" / "native_canonical_entity_state_1x10hz.fastdispkt"
DEFAULT_JSON_OUT = ROOT / "build" / "reports" / "engine_benchmark_sources" / "native_canonical_benchmark.json"
TARGET_NAME = "fastdis_native_canonical_benchmark"
SCENARIO_SUITE = "core_matrix"
SCENARIO_CONFIGS = (
    {"scenario": "entity_state_1x10hz", "count": 24, "entity_count": 1, "rate_hz": 10.0},
    {"scenario": "entity_state_100x30hz", "count": 300, "entity_count": 100, "rate_hz": 30.0},
    {"scenario": "entity_state_1000x60hz", "count": 1000, "entity_count": 1000, "rate_hz": 60.0},
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-dir", type=Path, default=DEFAULT_BUILD_DIR)
    parser.add_argument("--config", default="Release")
    parser.add_argument("--replay-out", type=Path, default=DEFAULT_REPLAY_PATH)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--if-available", action="store_true", help="Return success instead of failing when the native benchmark lane cannot be built or run")
    return parser.parse_args(argv)


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    print("+", " ".join(cmd), file=sys.stderr)
    return subprocess.run(
        cmd,
        cwd=ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def native_executable_name() -> str:
    return f"{TARGET_NAME}.exe" if platform.system().lower() == "windows" else TARGET_NAME


def find_native_executable(build_dir: Path) -> Path:
    candidates = list(build_dir.rglob(native_executable_name()))
    if not candidates:
        raise FileNotFoundError(f"could not find {native_executable_name()} under {build_dir}")
    return max(candidates, key=lambda item: item.stat().st_mtime)


def build_truth_packets(*, count: int, entity_count: int, rate_hz: float) -> tuple[list[bytes], dict[str, Any]]:
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
    return packets, truth


def replay_path_for_scenario(base_path: Path, scenario: str) -> Path:
    stem = base_path.stem
    scenario_suffix = scenario
    if stem.endswith("entity_state_1x10hz"):
        prefix = stem[: -len("entity_state_1x10hz")]
        stem = f"{prefix}{scenario_suffix}"
    else:
        stem = f"{stem}_{scenario_suffix}"
    return base_path.with_name(f"{stem}{base_path.suffix}")


def build_canonical_row(
    report: dict[str, Any],
    truth: dict[str, Any],
    truth_errors: list[str],
    replay_path: Path,
    *,
    scenario: str,
) -> dict[str, Any]:
    packets_received = int(report.get("packets_received", 0))
    packets_parsed = int(report.get("packets_parsed", 0))
    packets_accepted = int(report.get("entity_state", 0))
    malformed = int(report.get("malformed", 0))
    elapsed_seconds = float(report.get("elapsed_seconds", 0.0))
    packets_per_sec = (float(packets_received) / elapsed_seconds) if elapsed_seconds > 0 else None
    return {
        "scenario": scenario,
        "metrics": {
            "packets_received": packets_received,
            "packets_parsed": packets_parsed,
            "packets_accepted": packets_accepted,
            "packets_rejected": max(packets_parsed - packets_accepted, 0),
            "malformed": malformed,
            "socket_drops": None,
            "queue_drops": None,
            "p50_ingest_ms": None,
            "p95_ingest_ms": None,
            "p99_ingest_ms": None,
            "steady_state_gc_bytes": None,
            "main_thread_apply_ms": None,
            "runtime_elapsed_seconds": elapsed_seconds,
            "packets_per_sec": packets_per_sec,
            "notes": [
                "Canonical shared scenario executed through the native benchmark executable over the native entity-table and snapshot-buffer path.",
                f"scenario_suite={SCENARIO_SUITE}",
                "packet_source=fastdis.tools.send_entity.build_packets",
                f"replay_file={replay_path.relative_to(ROOT).as_posix() if replay_path.is_relative_to(ROOT) else str(replay_path)}",
                "verification=latest-state truth comparison via fastdis.tools.recv.verify_against_truth",
            ]
            + (["truth verification failed for this row; inspect final_truth_match and latest-state evidence before using it in claims."] if truth_errors else []),
        },
        "truth": {
            "final_truth_match": not truth_errors,
            "unique_entities_expected": truth.get("unique_entities"),
            "latest_entities_expected": truth.get("latest_entities"),
            "network_ingest_mode": "replay_native_entity_table",
        },
    }


def write_payload(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def run_lane(args: argparse.Namespace) -> dict[str, Any]:
    run([
        "cmake",
        "-S",
        str(ROOT),
        "-B",
        str(args.build_dir),
        "-DFASTDIS_BUILD_SHARED=ON",
        "-DFASTDIS_BUILD_BENCHMARKS=ON",
        "-DCMAKE_BUILD_TYPE=Release",
    ])
    run([
        "cmake",
        "--build",
        str(args.build_dir),
        "--config",
        args.config,
        "--target",
        TARGET_NAME,
    ])

    executable = find_native_executable(args.build_dir)
    scenario_runs: list[dict[str, Any]] = []
    canonical_rows: list[dict[str, Any]] = []
    overall_truth_errors: list[str] = []
    for config in SCENARIO_CONFIGS:
        scenario = str(config["scenario"])
        replay_path = replay_path_for_scenario(args.replay_out, scenario)
        packets, truth = build_truth_packets(
            count=int(config["count"]),
            entity_count=int(config["entity_count"]),
            rate_hz=float(config["rate_hz"]),
        )
        replay.write_v1_packets(replay_path, packets)
        completed = run([str(executable), "--packet-file", str(replay_path)])
        native_report = json.loads(completed.stdout)
        truth_errors = verify_against_truth(native_report, truth)
        canonical_row = build_canonical_row(
            native_report,
            truth,
            truth_errors,
            replay_path,
            scenario=scenario,
        )
        scenario_runs.append(
            {
                "scenario": scenario,
                "replay_path": str(replay_path),
                "native_report": native_report,
                "truth_errors": truth_errors,
            }
        )
        canonical_rows.append(canonical_row)
        overall_truth_errors.extend(f"{scenario}: {error}" for error in truth_errors)
    payload = {
        "schema": "fastdis.native_canonical_benchmark_sidecar.v1",
        "surface": "native",
        "scenario": str(SCENARIO_CONFIGS[0]["scenario"]),
        "scenario_suite": SCENARIO_SUITE,
        "status": "ok" if not overall_truth_errors else "truth-failed",
        "build_dir": str(args.build_dir),
        "config": args.config,
        "executable": str(executable),
        "replay_path": str(replay_path_for_scenario(args.replay_out, str(SCENARIO_CONFIGS[0]["scenario"]))),
        "scenario_runs": scenario_runs,
        "truth_errors": overall_truth_errors,
        "canonical_row": canonical_rows[0],
        "canonical_rows": canonical_rows,
    }
    write_payload(args.json_out, payload)
    return payload


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        payload = run_lane(args)
    except Exception as exc:
        if not args.if_available:
            raise
        payload = {
            "schema": "fastdis.native_canonical_benchmark_sidecar.v1",
            "surface": "native",
            "scenario": str(SCENARIO_CONFIGS[0]["scenario"]),
            "scenario_suite": SCENARIO_SUITE,
            "status": "unavailable",
            "error": f"{type(exc).__name__}: {exc}",
        }
        write_payload(args.json_out, payload)
        print(f"json: {args.json_out}")
        return 0

    print(f"json: {args.json_out}")
    return 0 if payload.get("status") == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
