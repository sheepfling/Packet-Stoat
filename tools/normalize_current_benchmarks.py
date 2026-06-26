#!/usr/bin/env python3
"""Normalize current native/cpp/ctypes benchmark payloads into shared engine-benchmark reports."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
DEFAULT_INPUT = ROOT / "build" / "benchmark_results" / "current" / "current.json"
DEFAULT_OUT_DIR = ROOT / "build" / "reports" / "engine_benchmarks"
DEFAULT_NATIVE_CANONICAL_INPUT = ROOT / "build" / "reports" / "engine_benchmark_sources" / "native_canonical_benchmark.json"
CORE_SCENARIO_NAME = "entity_state_1x10hz"
CORE_SCENARIO_SUITE = "core_matrix"
PYTHON_CTYPES_CANONICAL_SCENARIOS = (
    {
        "scenario": "entity_state_1x10hz",
        "count": 24,
        "entity_count": 1,
        "rate_hz": 10.0,
    },
    {
        "scenario": "entity_state_100x30hz",
        "count": 300,
        "entity_count": 100,
        "rate_hz": 30.0,
    },
    {
        "scenario": "entity_state_1000x60hz",
        "count": 1000,
        "entity_count": 1000,
        "rate_hz": 60.0,
    },
)


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


def _to_float(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _to_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    return None


def _native_packets_per_sec(row: dict[str, Any]) -> float | None:
    direct = _to_float(row.get("packets_per_sec"))
    if direct is not None:
        return direct
    packets = _to_float(row.get("packets"))
    avg_ms = _to_float(row.get("avg_ms"))
    if packets is None or avg_ms is None or avg_ms <= 0:
        return None
    return packets / (avg_ms / 1000.0)


def _row_notes(row: dict[str, Any]) -> list[str]:
    note = row.get("notes")
    if note is None:
        return []
    if isinstance(note, str):
        return [note]
    if isinstance(note, list):
        return [str(item) for item in note]
    return [str(note)]


def _build_python_ctypes_canonical_row(
    *,
    scenario: str,
    count: int,
    entity_count: int,
    rate_hz: float,
) -> dict[str, Any] | None:
    try:
        from fastdis import native
        from fastdis.tools import send_entity
        from fastdis.tools.recv import canonical_report, verify_against_truth
    except Exception:
        return None

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

    try:
        packets, _orientation_debug, truth = send_entity.build_packets(args)
        started = time.perf_counter()
        lib = native.load_native()
        scanner = lib.create_scanner()
        scanner.use_entity_transform_profile()
        table = lib.create_entity_table(max(len(packets), 1))
        snapshots = lib.create_snapshot_buffer(max(len(packets), 1), slots=3)
        table_stats = table.ingest(scanner, packets)
        snapshot_view = snapshots.publish_changed(table, clear=True)
        table_snapshots = table.snapshot_all(return_meta=False)
        elapsed = time.perf_counter() - started
        malformed = int(table_stats.get("scan", {}).get("malformed", 0))
        report = canonical_report(
            packets=packets,
            malformed=malformed,
            counts_by_type={1: len(packets)},
            table_snapshots=table_snapshots,
            snapshot_count=snapshot_view.count,
            errors=[],
            surface="python_ctypes",
        )
        truth_errors = verify_against_truth(report, truth)
        packets_received = _to_int(report.get("packets_received"))
        packets_parsed = _to_int(report.get("packets_parsed"))
        packets_accepted = _to_int(report.get("entity_state"))
        malformed_count = _to_int(report.get("malformed"))
        rejected = None
        if packets_parsed is not None and packets_accepted is not None and malformed_count is not None:
            rejected = max(packets_parsed - packets_accepted - malformed_count, 0)
        packets_per_sec = None
        if packets_received is not None and elapsed > 0:
            packets_per_sec = float(packets_received) / float(elapsed)
        notes = [
            "Canonical shared scenario executed through Python ctypes over the native entity-table and snapshot-buffer path.",
            f"scenario_suite={CORE_SCENARIO_SUITE}",
            f"scenario={scenario}",
            "packet_source=fastdis.tools.send_entity.build_packets",
            "verification=latest-state truth comparison via fastdis.tools.recv.verify_against_truth",
        ]
        if truth_errors:
            notes.append("truth verification failed for this row; inspect final_truth_match and latest-state evidence before using it in claims.")
        return {
            "scenario": scenario,
            "metrics": {
                "packets_received": packets_received,
                "packets_parsed": packets_parsed,
                "packets_accepted": packets_accepted,
                "packets_rejected": rejected,
                "malformed": malformed_count,
                "socket_drops": None,
                "queue_drops": None,
                "p50_ingest_ms": None,
                "p95_ingest_ms": None,
                "p99_ingest_ms": None,
                "steady_state_gc_bytes": None,
                "main_thread_apply_ms": None,
                "runtime_elapsed_seconds": float(elapsed),
                "packets_per_sec": packets_per_sec,
                "notes": notes,
            },
            "truth": {
                "final_truth_match": not truth_errors,
                "unique_entities_expected": truth.get("unique_entities"),
                "latest_entities_expected": truth.get("latest_entities"),
                "network_ingest_mode": "in_process",
            },
        }
    except Exception:
        return None


def build_python_ctypes_canonical_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for config in PYTHON_CTYPES_CANONICAL_SCENARIOS:
        row = _build_python_ctypes_canonical_row(
            scenario=str(config["scenario"]),
            count=int(config["count"]),
            entity_count=int(config["entity_count"]),
            rate_hz=float(config["rate_hz"]),
        )
        if row is not None:
            rows.append(row)
    return rows


def load_optional_native_canonical_row(path: Path = DEFAULT_NATIVE_CANONICAL_INPUT) -> list[dict[str, Any]] | dict[str, Any] | None:
    try:
        payload = load_json(path)
    except Exception:
        return None
    if payload.get("schema") != "fastdis.native_canonical_benchmark_sidecar.v1":
        return None
    if payload.get("status") != "ok":
        return None
    canonical_rows = payload.get("canonical_rows")
    if isinstance(canonical_rows, list):
        rows = [
            row
            for row in canonical_rows
            if isinstance(row, dict) and isinstance(row.get("scenario"), str)
        ]
        if rows:
            return rows
    canonical_row = payload.get("canonical_row")
    if not isinstance(canonical_row, dict):
        return None
    return canonical_row


def append_optional_native_canonical_row(
    report: dict[str, Any],
    *,
    loader=load_optional_native_canonical_row,
) -> dict[str, Any]:
    if report.get("surface") != "native":
        return report
    rows = report.get("rows")
    if not isinstance(rows, list):
        return report
    existing = {
        row.get("scenario")
        for row in rows
        if isinstance(row, dict) and isinstance(row.get("scenario"), str)
    }
    canonical_row = loader()
    if canonical_row is None:
        return report
    if isinstance(canonical_row, dict):
        candidates = [canonical_row]
    elif isinstance(canonical_row, list):
        candidates = [row for row in canonical_row if isinstance(row, dict)]
    else:
        candidates = []
    new_rows = [
        row
        for row in candidates
        if isinstance(row.get("scenario"), str) and row["scenario"] not in existing
    ]
    if not new_rows:
        return report
    rows.extend(new_rows)
    summary = report.get("summary")
    if isinstance(summary, dict):
        summary["row_count"] = len(rows)
        summary["latency_rows"] = sum(1 for row in rows if isinstance(row, dict) and isinstance(row.get("metrics"), dict) and row["metrics"].get("p95_ingest_ms") is not None)
        summary["runtime_metric_rows"] = sum(1 for row in rows if isinstance(row, dict) and isinstance(row.get("metrics"), dict) and row["metrics"].get("runtime_elapsed_seconds") is not None)
        summary["truth_rows"] = sum(1 for row in rows if isinstance(row, dict) and isinstance(row.get("truth"), dict) and row["truth"].get("final_truth_match") is not None)
    return report


def append_optional_python_ctypes_canonical_row(
    report: dict[str, Any],
    *,
    builder=build_python_ctypes_canonical_rows,
) -> dict[str, Any]:
    if report.get("surface") != "python_ctypes":
        return report
    rows = report.get("rows")
    if not isinstance(rows, list):
        return report
    existing = {
        row.get("scenario")
        for row in rows
        if isinstance(row, dict) and isinstance(row.get("scenario"), str)
    }
    built_rows = builder()
    if isinstance(built_rows, dict):
        candidates = [built_rows]
    elif isinstance(built_rows, list):
        candidates = [row for row in built_rows if isinstance(row, dict)]
    else:
        candidates = []
    new_rows = [
        row
        for row in candidates
        if isinstance(row.get("scenario"), str) and row["scenario"] not in existing
    ]
    if not new_rows:
        return report
    rows.extend(new_rows)
    summary = report.get("summary")
    if isinstance(summary, dict):
        summary["row_count"] = len(rows)
        summary["latency_rows"] = sum(1 for row in rows if isinstance(row, dict) and isinstance(row.get("metrics"), dict) and row["metrics"].get("p95_ingest_ms") is not None)
        summary["runtime_metric_rows"] = sum(1 for row in rows if isinstance(row, dict) and isinstance(row.get("metrics"), dict) and row["metrics"].get("runtime_elapsed_seconds") is not None)
        summary["truth_rows"] = sum(1 for row in rows if isinstance(row, dict) and isinstance(row.get("truth"), dict) and row["truth"].get("final_truth_match") is not None)
    return report


def normalize_surface(surface: str, surface_kind: str, rows: list[dict[str, Any]], *, generated_at_utc: str, host: dict[str, Any], source_payload: str, source_schema: str | None) -> dict[str, Any]:
    normalized_rows = []
    for row in rows:
        accepted = _to_int(row.get("accepted"))
        emitted = _to_int(row.get("emitted"))
        malformed = _to_int(row.get("malformed"))
        rejected = None
        if emitted is not None and accepted is not None and malformed is not None:
            rejected = max(emitted - accepted - malformed, 0)
        normalized_rows.append(
            {
                "scenario": str(row.get("case") or "unknown"),
                "metrics": {
                    "packets_received": _to_int(row.get("seen")),
                    "packets_parsed": _to_int(row.get("seen")),
                    "packets_accepted": accepted,
                    "packets_rejected": rejected,
                    "malformed": malformed,
                    "socket_drops": None,
                    "queue_drops": None,
                    "p50_ingest_ms": _to_float(row.get("p50_ms")),
                    "p95_ingest_ms": _to_float(row.get("p95_ms")),
                    "p99_ingest_ms": _to_float(row.get("p99_ms")),
                    "steady_state_gc_bytes": None,
                    "main_thread_apply_ms": None,
                    "runtime_elapsed_seconds": None,
                    "packets_per_sec": _native_packets_per_sec(row),
                    "notes": _row_notes(row),
                },
                "truth": {
                    "final_truth_match": None,
                },
            }
        )
    return {
        "schema": "fastdis.engine_benchmark_report.v1",
        "surface": surface,
        "surface_kind": surface_kind,
        "generated_at_utc": generated_at_utc,
        "host": host,
        "source_payload": source_payload,
        "source_schema": source_schema,
        "summary": {
            "row_count": len(normalized_rows),
            "latency_rows": sum(1 for row in normalized_rows if row["metrics"]["p95_ingest_ms"] is not None),
            "runtime_metric_rows": sum(1 for row in normalized_rows if row["metrics"]["runtime_elapsed_seconds"] is not None),
            "truth_rows": sum(1 for row in normalized_rows if row["truth"]["final_truth_match"] is not None),
        },
        "rows": normalized_rows,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# {report['surface']} Engine Benchmark Report",
        "",
        f"- schema: `{report['schema']}`",
        f"- surface_kind: `{report['surface_kind']}`",
        f"- row_count: `{report['summary']['row_count']}`",
        "",
        "| scenario | packets/sec | p50 ms | p95 ms | p99 ms | accepted | malformed |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in report["rows"]:
        metrics = row["metrics"]
        lines.append(
            f"| {row['scenario']} | {metrics['packets_per_sec']} | {metrics['p50_ingest_ms']} | {metrics['p95_ingest_ms']} | {metrics['p99_ingest_ms']} | {metrics['packets_accepted']} | {metrics['malformed']} |"
        )
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    payload = load_json(args.input)
    generated_at_utc = str(payload.get("generated_at_utc") or "")
    host = payload.get("host") if isinstance(payload.get("host"), dict) else {}
    args.out_dir.mkdir(parents=True, exist_ok=True)

    reports = []
    native = payload.get("native")
    if isinstance(native, dict):
        reports.append(
            normalize_surface(
                "native",
                "native",
                list(native.get("results") or []),
                generated_at_utc=generated_at_utc,
                host=host,
                source_payload=display_path(args.input),
                source_schema="fastdis.native_benchmark.current",
            )
        )
    cpp = payload.get("cpp")
    if isinstance(cpp, dict):
        reports.append(
            normalize_surface(
                "cpp",
                "cpp",
                list(cpp.get("results") or []),
                generated_at_utc=generated_at_utc,
                host=host,
                source_payload=display_path(args.input),
                source_schema="fastdis.cpp_benchmark.current",
            )
        )
    ctypes = payload.get("ctypes")
    if isinstance(ctypes, dict):
        reports.append(
            normalize_surface(
                "python_ctypes",
                "python",
                list(ctypes.get("results") or []),
                generated_at_utc=generated_at_utc,
                host=host,
                source_payload=display_path(args.input),
                source_schema="fastdis.ctypes_benchmark.current",
            )
        )

    for report in reports:
        report = append_optional_native_canonical_row(report)
        report = append_optional_python_ctypes_canonical_row(report)
        stem = f"{report['surface']}_engine_benchmark_report"
        json_path = args.out_dir / f"{stem}.json"
        md_path = args.out_dir / f"{stem}.md"
        json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        md_path.write_text(render_markdown(report) + "\n", encoding="utf-8")
        print(f"json: {display_path(json_path)}")
        print(f"md: {display_path(md_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
