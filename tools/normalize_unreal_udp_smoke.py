#!/usr/bin/env python3
"""Normalize Unreal UDP smoke output into the shared engine-benchmark report shape."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from proof_context import build_proof_context, current_host_summary, scenario_family_for

DEFAULT_OUT_DIR = ROOT / "build" / "reports" / "engine_benchmarks"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="JSON payload emitted by tools/run_unreal_udp_smoke.py")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--scenario", default="unreal_live_udp_smoke")
    return parser.parse_args(argv)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _to_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    return None


def _load_truth(payload: dict[str, Any]) -> tuple[dict[str, Any], str | None]:
    truth_file = payload.get("truth_file")
    if not isinstance(truth_file, str) or not truth_file:
        return {}, None
    truth_path = Path(truth_file).expanduser()
    if not truth_path.is_absolute():
        truth_path = (ROOT / truth_path).resolve()
    return load_json(truth_path), display_path(truth_path)


def normalize_payload(payload: dict[str, Any], *, scenario: str, source_payload: str) -> dict[str, Any]:
    report = payload.get("report") if isinstance(payload.get("report"), dict) else {}
    truth, truth_path = _load_truth(payload)
    host = current_host_summary()

    packets = _to_int(report.get("packets"))
    malformed = _to_int(truth.get("malformed"))
    packets_parsed = _to_int(truth.get("packets_parsed"))
    packets_accepted = _to_int(truth.get("entity_state"))
    packets_rejected = None
    if packets_parsed is not None and packets_accepted is not None and malformed is not None:
        packets_rejected = max(packets_parsed - packets_accepted - malformed, 0)

    notes = [
        "Normalized from Unreal UDP smoke output rather than the final shared scenario runner.",
        "Latency and main-thread timing fields remain null until the richer Unreal benchmark lane lands.",
    ]
    if truth_path is not None:
        notes.append("Packet and malformed counts are inferred from the canonical sender truth payload.")
    if isinstance(payload.get("mode"), str):
        notes.append(f"source mode: {payload['mode']}")
    known_entities = _to_int(report.get("known_entities"))
    moved_actors = _to_int(report.get("moved_actors"))
    if known_entities is not None:
        notes.append(f"known_entities={known_entities}")
    if moved_actors is not None:
        notes.append(f"moved_actors={moved_actors}")

    final_truth_match = payload.get("status") == "passed" and not list(payload.get("errors") or [])
    normalized_rows = [
        {
            "scenario": scenario,
            "metrics": {
                "packets_received": packets,
                "packets_parsed": packets_parsed if packets_parsed is not None else packets,
                "packets_accepted": packets_accepted,
                "packets_rejected": packets_rejected,
                "malformed": malformed,
                "socket_drops": None,
                "queue_drops": None,
                "p50_ingest_ms": None,
                "p95_ingest_ms": None,
                "p99_ingest_ms": None,
                "steady_state_gc_bytes": None,
                "main_thread_apply_ms": None,
                "runtime_elapsed_seconds": None,
                "packets_per_sec": None,
                "notes": notes,
            },
            "truth": {
                "final_truth_match": final_truth_match,
                "unique_entities_expected": _to_int(truth.get("unique_entities")),
                "latest_entities_expected": truth.get("latest_entities"),
                "source_truth_schema": truth.get("schema"),
                "source_truth_file": truth_path,
            },
        }
    ]

    return {
        "schema": "fastdis.engine_benchmark_report.v1",
        "surface": "unreal",
        "surface_kind": "engine",
        "generated_at_utc": utc_now(),
        "host": host,
        "proof_context": build_proof_context(
            evidence_class="truth_backed_bridge",
            comparison_axis="engine_adapter",
            host=host,
            runtime_kind="engine",
            engine_family="unreal",
            claim_boundary="Unreal UDP smoke proves engine-adapter participation and truth alignment, not a full measured runtime benchmark lane.",
            comparable=False,
            scenario_family=scenario_family_for(scenario),
            truth_backed=True,
            qualification_notes=["smoke_route", "counts_inferred_from_truth_payload"],
        ),
        "source_payload": source_payload,
        "source_schema": "fastdis.unreal_udp_smoke.v1",
        "summary": {
            "row_count": len(normalized_rows),
            "latency_rows": 0,
            "runtime_metric_rows": 0,
            "truth_rows": sum(1 for row in normalized_rows if row["truth"]["final_truth_match"] is not None),
        },
        "rows": normalized_rows,
    }


def render_markdown(report: dict[str, Any]) -> str:
    row = report["rows"][0]
    metrics = row["metrics"]
    truth = row["truth"]
    lines = [
        "# unreal Engine Benchmark Report",
        "",
        f"- schema: `{report['schema']}`",
        f"- source_schema: `{report['source_schema']}`",
        f"- source_payload: `{report['source_payload']}`",
        "",
        "| scenario | packets | parsed | accepted | malformed | truth |",
        "| --- | --- | --- | --- | --- | --- |",
        f"| {row['scenario']} | {metrics['packets_received']} | {metrics['packets_parsed']} | {metrics['packets_accepted']} | {metrics['malformed']} | {truth['final_truth_match']} |",
        "",
    ]
    notes = metrics.get("notes") or []
    if notes:
        lines.append("## Notes")
        lines.append("")
        for note in notes:
            lines.append(f"- {note}")
        lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    payload = load_json(args.input)
    report = normalize_payload(payload, scenario=args.scenario, source_payload=display_path(args.input))

    args.out_dir.mkdir(parents=True, exist_ok=True)
    stem = "unreal_engine_benchmark_report"
    json_path = args.out_dir / f"{stem}.json"
    md_path = args.out_dir / f"{stem}.md"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report) + "\n", encoding="utf-8")
    print(f"json: {display_path(json_path)}")
    print(f"md: {display_path(md_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
