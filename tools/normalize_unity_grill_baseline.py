#!/usr/bin/env python3
"""Normalize a captured GRILL Unity benchmark baseline into the shared engine-benchmark report shape."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "verification_reports" / "unity_grill_baseline" / "grill_unity_benchmark_baseline.json"
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


def _placeholder(value: Any) -> bool:
    return isinstance(value, str) and value.startswith("REPLACE_ME")


def validate_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if payload.get("schema") != "fastdis.unity_grill_benchmark_baseline.v1":
        errors.append("`schema` must equal `fastdis.unity_grill_benchmark_baseline.v1`")
    if payload.get("product") != "GRILL DIS for Unity":
        errors.append("`product` must equal `GRILL DIS for Unity`")
    for field in ("captured_at_utc", "repository", "unity", "host", "scenario", "results"):
        if field not in payload:
            errors.append(f"missing top-level field `{field}`")
    repository = payload.get("repository")
    if isinstance(repository, dict):
        for field in ("url", "commit"):
            value = repository.get(field)
            if not isinstance(value, str) or not value or _placeholder(value):
                errors.append(f"`repository.{field}` must be a populated non-template string")
    else:
        errors.append("`repository` must be an object")
    unity = payload.get("unity")
    if isinstance(unity, dict):
        version = unity.get("version")
        if not isinstance(version, str) or not version or _placeholder(version):
            errors.append("`unity.version` must be a populated non-template string")
    else:
        errors.append("`unity` must be an object")
    host = payload.get("host")
    if isinstance(host, dict):
        for field in ("system", "machine"):
            value = host.get(field)
            if not isinstance(value, str) or not value or _placeholder(value):
                errors.append(f"`host.{field}` must be a populated non-template string")
    else:
        errors.append("`host` must be an object")
    results = payload.get("results")
    if not isinstance(results, list) or not results:
        errors.append("`results` must be a non-empty array")
    return errors


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


def normalize_payload(payload: dict[str, Any], *, source_payload: str) -> dict[str, Any]:
    results = payload.get("results") if isinstance(payload.get("results"), list) else []
    unity = payload.get("unity") if isinstance(payload.get("unity"), dict) else {}
    host = payload.get("host") if isinstance(payload.get("host"), dict) else {}
    scenario = payload.get("scenario") if isinstance(payload.get("scenario"), dict) else {}
    rows = []
    for result in results:
        if not isinstance(result, dict):
            continue
        notes = []
        if isinstance(result.get("notes"), str) and result["notes"]:
            notes.append(str(result["notes"]))
        if isinstance(scenario.get("scene"), str):
            notes.append(f"scene={scenario['scene']}")
        if isinstance(scenario.get("traffic_mix"), str):
            notes.append(f"traffic_mix={scenario['traffic_mix']}")
        if isinstance(result.get("entity_count"), int):
            notes.append(f"entity_count={result['entity_count']}")
        if isinstance(result.get("update_hz"), int):
            notes.append(f"update_hz={result['update_hz']}")
        rows.append(
            {
                "scenario": str(result.get("case") or "unknown"),
                "metrics": {
                    "packets_received": None,
                    "packets_parsed": None,
                    "packets_accepted": None,
                    "packets_rejected": None,
                    "malformed": None,
                    "socket_drops": None,
                    "queue_drops": None,
                    "p50_ingest_ms": None,
                    "p95_ingest_ms": None,
                    "p99_ingest_ms": None,
                    "steady_state_gc_bytes": _to_int(result.get("gc_alloc_bytes_per_frame")),
                    "main_thread_apply_ms": _to_float(result.get("main_thread_ms_avg")),
                    "runtime_elapsed_seconds": None,
                    "packets_per_sec": _to_float(result.get("packets_per_sec")),
                    "notes": notes,
                },
                "truth": {
                    "final_truth_match": None,
                },
            }
        )
    return {
        "schema": "fastdis.engine_benchmark_report.v1",
        "surface": "grill_unity",
        "surface_kind": "competitor",
        "generated_at_utc": payload.get("captured_at_utc"),
        "host": {
            "system": host.get("system"),
            "release": host.get("release"),
            "machine": host.get("machine"),
            "unity_version": unity.get("version"),
        },
        "source_payload": source_payload,
        "source_schema": "fastdis.unity_grill_benchmark_baseline.v1",
        "summary": {
            "row_count": len(rows),
            "latency_rows": sum(1 for row in rows if row["metrics"]["main_thread_apply_ms"] is not None),
            "runtime_metric_rows": 0,
            "truth_rows": 0,
        },
        "rows": rows,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# grill_unity Engine Benchmark Report",
        "",
        f"- schema: `{report['schema']}`",
        f"- source_schema: `{report['source_schema']}`",
        f"- source_payload: `{report['source_payload']}`",
        "",
        "| scenario | packets/sec | main-thread apply ms | gc alloc bytes/frame |",
        "| --- | --- | --- | --- |",
    ]
    for row in report["rows"]:
        metrics = row["metrics"]
        lines.append(
            f"| {row['scenario']} | {metrics['packets_per_sec']} | {metrics['main_thread_apply_ms']} | {metrics['steady_state_gc_bytes']} |"
        )
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if not args.input.exists():
        print(f"skip: missing {display_path(args.input)}")
        return 0
    payload = load_json(args.input)
    errors = validate_payload(payload)
    if errors:
        for error in errors:
            print(error)
        return 1
    report = normalize_payload(payload, source_payload=display_path(args.input))
    args.out_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.out_dir / "grill_unity_engine_benchmark_report.json"
    md_path = args.out_dir / "grill_unity_engine_benchmark_report.md"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report) + "\n", encoding="utf-8")
    print(f"json: {display_path(json_path)}")
    print(f"md: {display_path(md_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
