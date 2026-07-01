#!/usr/bin/env python3
"""Normalize Unreal proof artifacts into the shared engine-benchmark report shape."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any

from benchmark_surface_utils import display_path, load_json, load_truth_from_route, report_summary, to_int, utc_now

ROOT = Path(__file__).resolve().parents[1]
TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from proof_context import build_proof_context, current_host_summary, merge_host_summary, scenario_family_for

DEFAULT_READINESS = ROOT / "artifacts" / "reports" / "unreal_fab_readiness.json"
DEFAULT_PACKAGED = ROOT / "artifacts" / "reports" / "unreal_packaged_install_smoke.json"
DEFAULT_ORIENTATION = ROOT / "artifacts" / "reports" / "orientation_assurance_live" / "unreal_good_compare.json"
DEFAULT_NETWORK_INGEST = ROOT / "artifacts" / "reports" / "network_ingest_matrix" / "network_ingest_matrix.json"
DEFAULT_UDP_MATRIX = ROOT / "artifacts" / "reports" / "unreal_udp_matrix" / "unreal_udp_matrix.json"
DEFAULT_OUT_DIR = ROOT / "artifacts" / "reports" / "engine_benchmarks"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--readiness", type=Path, default=DEFAULT_READINESS)
    parser.add_argument("--packaged", type=Path, default=DEFAULT_PACKAGED)
    parser.add_argument("--orientation", type=Path, default=DEFAULT_ORIENTATION)
    parser.add_argument("--network-ingest", type=Path, default=DEFAULT_NETWORK_INGEST)
    parser.add_argument("--udp-matrix", type=Path, default=DEFAULT_UDP_MATRIX)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--scenario", default="unreal_proof_verification")
    return parser.parse_args(argv)



def _orientation_pass(payload: dict[str, Any] | None) -> tuple[bool | None, int | None, int | None]:
    if payload is None:
        return None, None, None
    results = payload.get("results")
    if not isinstance(results, list):
        return None, None, None
    total = len(results)
    passed = sum(1 for row in results if isinstance(row, dict) and row.get("pass") is True)
    return passed == total, passed, total


def _to_int(value: Any) -> int | None:
    return to_int(value)


def _load_truth_from_route(route: dict[str, Any]) -> tuple[dict[str, Any], str | None]:
    return load_truth_from_route(ROOT, route)

def _live_udp_rows(*payloads: dict[str, Any] | None) -> list[dict[str, Any]]:
    routes: list[dict[str, Any]] = []
    for payload in payloads:
        candidate_routes = payload.get("routes") if isinstance(payload, dict) else None
        if not isinstance(candidate_routes, list):
            continue
        for row in candidate_routes:
            if (
                isinstance(row, dict)
                and row.get("surface") == "unreal"
                and row.get("mode") == "live_udp"
                and isinstance(row.get("scenario"), str)
            ):
                routes.append(row)
    if not routes:
        return []
    deduped: dict[str, dict[str, Any]] = {}
    for route in routes:
        deduped[str(route["scenario"])] = route
    normalized_rows: list[dict[str, Any]] = []
    for scenario in sorted(deduped):
        route = deduped[scenario]
        report = route.get("report") if isinstance(route.get("report"), dict) else {}
        truth, truth_path = load_truth_from_route(ROOT, route)
        malformed = _to_int(truth.get("malformed"))
        packets_parsed = _to_int(truth.get("packets_parsed"))
        packets_accepted = _to_int(truth.get("entity_state"))
        packets_rejected = None
        if packets_parsed is not None and packets_accepted is not None and malformed is not None:
            packets_rejected = max(packets_parsed - packets_accepted - malformed, 0)
        notes = [
            "Normalized from the Unreal live UDP smoke lane.",
            "This row uses canonical sender truth plus live engine actor movement verification.",
        ]
        if truth_path is not None:
            notes.append(f"source_truth_file={truth_path}")
        normalized_rows.append(
            {
                "scenario": route["scenario"],
                "metrics": {
                    "packets_received": _to_int(report.get("packets")),
                    "packets_parsed": packets_parsed,
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
                    "final_truth_match": route.get("status") == "passed" and not list(route.get("errors") or []),
                    "unique_entities_expected": _to_int(truth.get("unique_entities")),
                    "latest_entities_expected": truth.get("latest_entities"),
                    "source_truth_schema": truth.get("schema"),
                    "source_truth_file": truth_path,
                    "network_ingest_mode": route.get("mode"),
                },
            }
        )
    return normalized_rows


def normalize_payload(
    readiness_payload: dict[str, Any] | None,
    *,
    packaged_payload: dict[str, Any] | None,
    orientation_payload: dict[str, Any] | None,
    network_ingest_payload: dict[str, Any] | None,
    udp_matrix_payload: dict[str, Any] | None,
    scenario: str,
    source_payload: str,
) -> dict[str, Any]:
    readiness_status = readiness_payload.get("overall_status") if isinstance(readiness_payload, dict) else None
    packaged_status = packaged_payload.get("status") if isinstance(packaged_payload, dict) else None
    orientation_status, orientation_passed, orientation_total = _orientation_pass(orientation_payload)

    notes = [
        "Normalized from Unreal proof artifacts rather than a final shared scenario runner.",
        "Latency, packet-rate, and main-thread apply metrics remain null until the richer Unreal benchmark lane lands.",
    ]
    if isinstance(readiness_status, str):
        notes.append(f"fab_readiness_status={readiness_status}")
    if isinstance(packaged_status, str):
        notes.append(f"packaged_install_status={packaged_status}")
    if orientation_passed is not None and orientation_total is not None:
        notes.append(f"orientation_cases_passed={orientation_passed}/{orientation_total}")
    if isinstance(packaged_payload, dict) and isinstance(packaged_payload.get("engine_version"), str):
        notes.append(f"engine_version={packaged_payload['engine_version']}")

    readiness_pass = readiness_status == "fab_ready"
    packaged_pass = packaged_status == "pass"
    orientation_ok = orientation_status is True
    final_truth_match = readiness_pass and packaged_pass and orientation_ok

    host: dict[str, Any] = current_host_summary()
    command = packaged_payload.get("command") if isinstance(packaged_payload, dict) else None
    if isinstance(command, list) and command:
        first = command[0]
        if isinstance(first, str) and "/Users/Shared/Epic Games/" in first:
            host = merge_host_summary(host, system="Darwin", editor_path=first)
    if isinstance(packaged_payload, dict) and isinstance(packaged_payload.get("engine_version"), str):
        host = merge_host_summary(host, engine_version=packaged_payload["engine_version"])

    normalized_rows = [
        {
            "scenario": scenario,
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
                "steady_state_gc_bytes": None,
                "main_thread_apply_ms": None,
                "runtime_elapsed_seconds": None,
                "packets_per_sec": None,
                "notes": notes,
            },
            "truth": {
                "final_truth_match": final_truth_match,
                "fab_readiness_status": readiness_status,
                "packaged_install_status": packaged_status,
                "orientation_status": orientation_status,
                "fab_summary": readiness_payload.get("summary") if isinstance(readiness_payload, dict) else None,
                "packaged_checks": packaged_payload.get("checks") if isinstance(packaged_payload, dict) else None,
                "orientation_result_count": orientation_total,
            },
        }
    ]
    packaged_elapsed = packaged_payload.get("elapsed_seconds") if isinstance(packaged_payload, dict) else None
    if isinstance(packaged_elapsed, (int, float)):
        runtime_notes = [
            "Normalized from the Unreal packaged install smoke lane.",
            "This row uses wall-clock runtime elapsed time, not ingest latency percentiles.",
        ]
        if isinstance(packaged_status, str):
            runtime_notes.append(f"packaged_install_status={packaged_status}")
        normalized_rows.append(
            {
                "scenario": "unreal_packaged_install_runtime",
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
                    "steady_state_gc_bytes": None,
                    "main_thread_apply_ms": None,
                    "runtime_elapsed_seconds": float(packaged_elapsed),
                    "packets_per_sec": None,
                    "notes": runtime_notes,
                },
                "truth": {
                    "final_truth_match": packaged_status == "pass",
                    "packaged_install_status": packaged_status,
                    "packaged_checks": packaged_payload.get("checks") if isinstance(packaged_payload, dict) else None,
                },
            }
        )
    live_udp_rows = _live_udp_rows(udp_matrix_payload, network_ingest_payload)
    if live_udp_rows:
        normalized_rows[1:1] = live_udp_rows

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
            claim_boundary="Unreal proof normalization proves install/build/orientation coverage plus live UDP smoke participation. Performance claims remain bounded until direct measured Unreal benchmark lanes exist for canonical scenarios.",
            comparable=False,
            scenario_family=scenario_family_for(scenario),
            truth_backed=True,
            qualification_notes=[
                "workflow_and_packaged_bridge",
                "live_udp_rows_are_truth_backed_smoke_not_full_benchmarks",
            ],
        ),
        "source_payload": source_payload,
        "source_schema": "fastdis.unreal_proof_bridge.v1",
        "summary": {
            **report_summary(normalized_rows),
        },
        "rows": normalized_rows,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# unreal Engine Benchmark Report",
        "",
        f"- schema: `{report['schema']}`",
        f"- source_schema: `{report['source_schema']}`",
        f"- source_payload: `{report['source_payload']}`",
        "",
        "| scenario | truth | fab readiness | packaged install | orientation |",
        "| --- | --- | --- | --- | --- |",
        "",
    ]
    for row in report["rows"]:
        truth = row["truth"]
        lines.append(
            f"| {row['scenario']} | {truth['final_truth_match']} | {truth.get('fab_readiness_status')} | {truth.get('packaged_install_status')} | {truth.get('orientation_status')} |"
        )
    lines.append("")
    for row in report["rows"]:
        metrics = row["metrics"]
        if metrics.get("notes"):
            lines.append(f"## Notes: {row['scenario']}")
            lines.append("")
            for note in metrics["notes"]:
                lines.append(f"- {note}")
            lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    readiness_payload = load_json(args.readiness)
    packaged_payload = load_json(args.packaged)
    orientation_payload = load_json(args.orientation)
    network_ingest_payload = load_json(args.network_ingest)
    udp_matrix_payload = load_json(args.udp_matrix)
    report = normalize_payload(
        readiness_payload,
        packaged_payload=packaged_payload,
        orientation_payload=orientation_payload,
        network_ingest_payload=network_ingest_payload,
        udp_matrix_payload=udp_matrix_payload,
        scenario=args.scenario,
        source_payload=display_path(ROOT, args.readiness),
    )
    args.out_dir.mkdir(parents=True, exist_ok=True)
    stem = "unreal_engine_benchmark_report"
    json_path = args.out_dir / f"{stem}.json"
    md_path = args.out_dir / f"{stem}.md"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report) + "\n", encoding="utf-8")
    print(f"json: {display_path(ROOT, json_path)}")
    print(f"md: {display_path(ROOT, md_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
