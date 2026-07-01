#!/usr/bin/env python3
"""Append canonical core filtering rows to shared benchmark reports."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "artifacts" / "reports" / "core_filter_matrix" / "core_filter_matrix.json"
DEFAULT_OUT_DIR = ROOT / "artifacts" / "reports" / "engine_benchmarks"
SCENARIO = "filter_reject_90pct"
SURFACES = ("c", "cpp", "python_ctypes")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args(argv)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def _to_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    return None


def _to_float(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _row_from_route(route: dict[str, Any]) -> dict[str, Any] | None:
    report = route.get("report")
    if not isinstance(report, dict):
        return None
    truth_match = route.get("status") == "passed" and not list(route.get("errors") or [])
    return {
        "scenario": SCENARIO,
        "metrics": {
            "packets_received": _to_int(report.get("packets_received")),
            "packets_parsed": _to_int(report.get("packets_parsed")),
            "packets_accepted": _to_int(report.get("packets_accepted")),
            "packets_rejected": _to_int(report.get("packets_rejected")),
            "malformed": _to_int(report.get("malformed")),
            "socket_drops": None,
            "queue_drops": None,
            "p50_ingest_ms": None,
            "p95_ingest_ms": None,
            "p99_ingest_ms": None,
            "steady_state_gc_bytes": None,
            "main_thread_apply_ms": None,
            "runtime_elapsed_seconds": _to_float(route.get("elapsed_seconds")),
            "packets_per_sec": None,
            "notes": [
                "truth-verified canonical filtering route normalized from core_filter_matrix",
                f"mode={route.get('mode', 'unknown')}",
                f"scenario_suite={route.get('scenario_suite', 'unknown')}",
            ],
        },
        "truth": {
            "final_truth_match": truth_match,
            "network_ingest_mode": "filtering",
        },
    }


def _append_row(report: dict[str, Any], row: dict[str, Any]) -> dict[str, Any]:
    rows = report.get("rows") if isinstance(report.get("rows"), list) else []
    existing = {
        entry.get("scenario")
        for entry in rows
        if isinstance(entry, dict) and isinstance(entry.get("scenario"), str)
    }
    if row["scenario"] not in existing:
        rows.append(row)
    report["rows"] = rows
    summary = report.get("summary")
    if not isinstance(summary, dict):
        summary = {}
        report["summary"] = summary
    summary["row_count"] = len(rows)
    summary["latency_rows"] = sum(1 for entry in rows if isinstance(entry, dict) and isinstance(entry.get("metrics"), dict) and entry["metrics"].get("p95_ingest_ms") is not None)
    summary["runtime_metric_rows"] = sum(1 for entry in rows if isinstance(entry, dict) and isinstance(entry.get("metrics"), dict) and entry["metrics"].get("runtime_elapsed_seconds") is not None)
    summary["truth_rows"] = sum(1 for entry in rows if isinstance(entry, dict) and isinstance(entry.get("truth"), dict) and entry["truth"].get("final_truth_match") is not None)
    return report


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if not args.input.exists():
        print(f"skip: missing {display_path(args.input)}")
        return 0
    payload = load_json(args.input)
    routes = payload.get("routes") if isinstance(payload.get("routes"), list) else []
    for surface in SURFACES:
        report_path = args.out_dir / f"{surface}_engine_benchmark_report.json"
        if not report_path.exists():
            continue
        report = load_json(report_path)
        route = next((route for route in routes if isinstance(route, dict) and route.get("surface") == surface and route.get("status") == "passed"), None)
        if route is None:
            continue
        row = _row_from_route(route)
        if row is None:
            continue
        updated = _append_row(report, row)
        report_path.write_text(json.dumps(updated, indent=2) + "\n", encoding="utf-8")
        print(f"json: {display_path(report_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
