#!/usr/bin/env python3
"""Normalize C/C++ localhost UDP ingest matrix routes into shared benchmark reports."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "build" / "reports" / "network_ingest_matrix" / "network_ingest_matrix.json"
DEFAULT_OUT_DIR = ROOT / "build" / "reports" / "engine_benchmarks"


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
    scenario = route.get("scenario") if isinstance(route.get("scenario"), str) else "localhost_udp_ingest_truth"
    truth_match = route.get("status") == "passed" and not route.get("errors")
    notes = [
        "truth-verified localhost UDP ingest route normalized from network_ingest_matrix",
        f"mode={route.get('mode', 'unknown')}",
    ]
    if isinstance(route.get("scenario"), str):
        notes.append(f"canonical_scenario={route['scenario']}")
    return {
        "scenario": scenario,
        "metrics": {
            "packets_received": _to_int(report.get("packets_received")),
            "packets_parsed": _to_int(report.get("packets_parsed")),
            "packets_accepted": _to_int(report.get("entity_state")),
            "packets_rejected": None,
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
            "notes": notes,
        },
        "truth": {
            "final_truth_match": truth_match,
        },
    }


def normalize_surface(surface: str, routes: list[dict[str, Any]], *, generated_at_utc: str, source_payload: str) -> dict[str, Any] | None:
    rows = []
    source_schemas: list[str] = []
    for route in routes:
        row = _row_from_route(route)
        if row is None:
            continue
        rows.append(row)
        report = route.get("report")
        if isinstance(report, dict):
            schema = report.get("schema")
            if isinstance(schema, str) and schema not in source_schemas:
                source_schemas.append(schema)
    if not rows:
        return None
    return {
        "schema": "fastdis.engine_benchmark_report.v1",
        "surface": surface,
        "surface_kind": surface,
        "generated_at_utc": generated_at_utc,
        "host": {},
        "source_payload": source_payload,
        "source_schema": ", ".join(source_schemas) if source_schemas else "fastdis.network_ingest_matrix.route",
        "summary": {
            "row_count": len(rows),
            "latency_rows": 0,
            "runtime_metric_rows": sum(1 for row in rows if _to_float(row["metrics"].get("runtime_elapsed_seconds")) is not None),
            "truth_rows": sum(1 for row in rows if row["truth"]["final_truth_match"] is not None),
        },
        "rows": rows,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# {report['surface']} Engine Benchmark Report",
        "",
        f"- schema: `{report['schema']}`",
        f"- surface_kind: `{report['surface_kind']}`",
        f"- source_schema: `{report['source_schema']}`",
        "",
        "| scenario | packets_received | packets_parsed | runtime_elapsed_seconds | truth_match |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in report["rows"]:
        metrics = row["metrics"]
        lines.append(
            f"| {row['scenario']} | {metrics['packets_received']} | {metrics['packets_parsed']} | {metrics['runtime_elapsed_seconds']} | {row['truth']['final_truth_match']} |"
        )
    lines.extend(["", ""])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if not args.input.exists():
        print(f"skip: missing {display_path(args.input)}")
        return 0
    payload = load_json(args.input)
    generated_at_utc = str(payload.get("generated_at") or payload.get("generated_at_utc") or "")
    routes = payload.get("routes") if isinstance(payload.get("routes"), list) else []
    reports = []
    for surface in ("c", "cpp"):
        surface_routes = [
            route
            for route in routes
            if isinstance(route, dict) and route.get("surface") == surface
        ]
        normalized = normalize_surface(surface, surface_routes, generated_at_utc=generated_at_utc, source_payload=display_path(args.input))
        if normalized is not None:
            reports.append(normalized)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    for report in reports:
        stem = f"{report['surface']}_engine_benchmark_report"
        json_path = args.out_dir / f"{stem}.json"
        md_path = args.out_dir / f"{stem}.md"
        json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        md_path.write_text(render_markdown(report), encoding="utf-8")
        print(f"json: {display_path(json_path)}")
        print(f"md: {display_path(md_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
