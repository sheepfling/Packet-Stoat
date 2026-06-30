#!/usr/bin/env python3
"""Scaffold a GRILL Unreal benchmark baseline JSON from the tracked template."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
from typing import Any

from benchmark_surface_utils import build_scaffold_rows, display_path, load_json


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "artifacts" / "verification_reports" / "unreal_grill_baseline" / "grill_unreal_benchmark_baseline.template.json"
DEFAULT_FASTDIS = ROOT / "artifacts" / "benchmark_results" / "current" / "current.json"
DEFAULT_OUT = ROOT / "artifacts" / "verification_reports" / "unreal_grill_baseline" / "grill_unreal_benchmark_baseline.json"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", type=Path, default=TEMPLATE)
    parser.add_argument("--fastdis", type=Path, default=DEFAULT_FASTDIS)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--engine-version", default="REPLACE_ME_ENGINE_VERSION")
    parser.add_argument("--map", default="REPLACE_ME_MAP_NAME")
    parser.add_argument("--traffic-mix", default="REPLACE_ME_TRAFFIC_MIX")
    parser.add_argument("--commit", default="REPLACE_ME_COMMIT")
    parser.add_argument("--limit-cases", type=int, default=12)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args(argv)


def _fastdis_packets_per_sec(row: dict[str, Any]) -> float | None:
    packets = row.get("packets")
    avg_ms = row.get("avg_ms")
    if not isinstance(packets, (int, float)) or not isinstance(avg_ms, (int, float)) or avg_ms <= 0:
        return None
    return float(packets) / (float(avg_ms) / 1000.0)


def build_result_rows(fastdis_payload: dict[str, Any] | None, limit_cases: int) -> list[dict[str, Any]]:
    default_row = {
        "scenario": "REPLACE_ME_SHARED_SCENARIO_NAME",
        "packets_received": 0,
        "packets_parsed": 0,
        "packets_accepted": 0,
        "packets_rejected": 0,
        "malformed": 0,
        "socket_drops": 0,
        "queue_drops": 0,
        "p50_ingest_ms": 0.0,
        "p95_ingest_ms": 0.0,
        "p99_ingest_ms": 0.0,
        "steady_state_gc_bytes": 0,
        "main_thread_apply_ms": 0.0,
        "packets_per_sec": 0.0,
        "notes": "Replace this template row with measured data on the same host used for the FastDIS comparison run.",
    }
    def row_builder(row: dict[str, Any]) -> dict[str, Any]:
        case = str(row["case"])
        return {
            "scenario": case,
            "packets_received": 0,
            "packets_parsed": 0,
            "packets_accepted": 0,
            "packets_rejected": 0,
            "malformed": 0,
            "socket_drops": 0,
            "queue_drops": 0,
            "p50_ingest_ms": 0.0,
            "p95_ingest_ms": 0.0,
            "p99_ingest_ms": 0.0,
            "steady_state_gc_bytes": 0,
            "main_thread_apply_ms": 0.0,
            "packets_per_sec": _fastdis_packets_per_sec(row) or 0.0,
            "notes": f"Populate this GRILL Unreal measurement for the FastDIS case `{case}`.",
        }
    return build_scaffold_rows(
        fastdis_payload,
        limit_cases=limit_cases,
        row_builder=row_builder,
        default_row=default_row,
    )


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.out.exists() and not args.overwrite:
        raise SystemExit(f"Refusing to overwrite existing file: {args.out}")
    payload = load_json(args.template)
    assert payload is not None
    fastdis_payload = load_json(args.fastdis)
    payload["captured_at_utc"] = datetime.now(timezone.utc).isoformat()
    payload["repository"]["commit"] = args.commit
    payload["engine"]["version"] = args.engine_version
    payload["host"]["system"] = platform.system()
    payload["host"]["release"] = platform.release()
    payload["host"]["machine"] = platform.machine()
    payload["scenario"]["map"] = args.map
    payload["scenario"]["traffic_mix"] = args.traffic_mix
    payload["results"] = build_result_rows(fastdis_payload, args.limit_cases)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"unreal grill baseline scaffold: {display_path(ROOT, args.out)}")
    print(f"template: {display_path(ROOT, args.template)}")
    print(f"fastdis benchmark source: {display_path(ROOT, args.fastdis)} exists={args.fastdis.exists()}")
    print(f"scaffolded result rows: {len(payload['results'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
