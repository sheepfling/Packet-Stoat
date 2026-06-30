#!/usr/bin/env python3
"""Normalize Unity runtime verification evidence into the shared engine-benchmark report shape."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import sys
from typing import Any

from benchmark_surface_utils import display_path, load_json, load_truth_from_route, report_summary, to_float, to_int, utc_now

ROOT = Path(__file__).resolve().parents[1]
TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from proof_context import build_proof_context, current_host_summary, merge_host_summary, scenario_family_for

DEFAULT_RUNTIME = ROOT / "build" / "reports" / "unity_runtime_verification.json"
DEFAULT_WORKFLOW = ROOT / "build" / "reports" / "unity_workflow_report.json"
DEFAULT_EQUIVALENCE = ROOT / "build" / "reports" / "unity_cross_engine_equivalence.json"
DEFAULT_INSTALL_SMOKE = ROOT / "build" / "reports" / "unity_install_smoke.json"
DEFAULT_REPLAY_MATRIX = ROOT / "build" / "reports" / "unity_replay_matrix" / "unity_replay_matrix.json"
DEFAULT_OUT_DIR = ROOT / "build" / "reports" / "engine_benchmarks"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", type=Path, default=DEFAULT_RUNTIME)
    parser.add_argument("--workflow", type=Path, default=DEFAULT_WORKFLOW)
    parser.add_argument("--equivalence", type=Path, default=DEFAULT_EQUIVALENCE)
    parser.add_argument("--install-smoke", type=Path, default=DEFAULT_INSTALL_SMOKE)
    parser.add_argument("--replay-matrix", type=Path, default=DEFAULT_REPLAY_MATRIX)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--scenario", default="unity_runtime_verification")
    return parser.parse_args(argv)



def _lane_status(payload: dict[str, Any] | None) -> str | None:
    if payload is None:
        return None
    for key in ("unity_workflow_status", "overall_status", "status"):
        if isinstance(payload.get(key), str):
            return str(payload[key])
    return None


def _phase1_criterion(payload: dict[str, Any], name: str) -> dict[str, Any] | None:
    criteria = payload.get("phase1_exit_criteria")
    if not isinstance(criteria, list):
        return None
    for row in criteria:
        if isinstance(row, dict) and row.get("name") == name:
            return row
    return None


def _to_float(value: Any) -> float | None:
    return to_float(value)


def _to_int(value: Any) -> int | None:
    return to_int(value)


def _load_truth_from_route(route: dict[str, Any]) -> tuple[dict[str, Any], str | None]:
    return load_truth_from_route(ROOT, route)


def _criterion_complete(payload: dict[str, Any], name: str) -> bool:
    criterion = _phase1_criterion(payload, name)
    return isinstance(criterion, dict) and criterion.get("status") == "complete"


def _editor_method_details(payload: dict[str, Any]) -> dict[str, Any]:
    lanes = payload.get("lanes")
    if not isinstance(lanes, list):
        return {}
    for lane in lanes:
        if not isinstance(lane, dict):
            continue
        details = lane.get("details")
        if isinstance(details, dict) and details.get("schema") == "fastdis.unity_editor_method_verification.v1":
            return details
    return {}


def _benchmark_row(details: dict[str, Any], scenario: str) -> dict[str, Any] | None:
    rows = details.get("benchmark_rows")
    if not isinstance(rows, list):
        return None
    for row in rows:
        if isinstance(row, dict) and row.get("scenario") == scenario:
            return row
    return None


def _canonical_benchmark_rows(details: dict[str, Any]) -> list[dict[str, Any]]:
    rows = details.get("benchmark_rows")
    if not isinstance(rows, list):
        return []
    return [
        row
        for row in rows
        if isinstance(row, dict)
        and isinstance(row.get("scenario"), str)
        and row.get("scenario", "").startswith("entity_state_")
    ]


def _required_criteria(payload: dict[str, Any], names: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for name in names:
        criterion = _phase1_criterion(payload, name)
        if isinstance(criterion, dict):
            rows.append(criterion)
    return rows


def _check_status_map(details: dict[str, Any]) -> dict[str, str]:
    rows = details.get("checks")
    if not isinstance(rows, list):
        return {}
    status_map: dict[str, str] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        name = row.get("name")
        status = row.get("status")
        if isinstance(name, str) and isinstance(status, str):
            status_map[name] = status
    return status_map

def _replay_rows(
    replay_matrix_payload: dict[str, Any] | None,
    *,
    benchmark_rows_by_scenario: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    routes = replay_matrix_payload.get("routes") if isinstance(replay_matrix_payload, dict) else None
    if not isinstance(routes, list):
        return []
    benchmark_rows_by_scenario = benchmark_rows_by_scenario or {}
    rows: list[dict[str, Any]] = []
    for route in routes:
        if not (
            isinstance(route, dict)
            and route.get("surface") == "unity"
            and route.get("mode") == "replay"
            and isinstance(route.get("scenario"), str)
        ):
            continue
        report = route.get("report") if isinstance(route.get("report"), dict) else {}
        truth, truth_path = load_truth_from_route(ROOT, route)
        benchmark_row = benchmark_rows_by_scenario.get(route["scenario"])
        benchmark_packet_total = _to_int(benchmark_row.get("packets_received")) if isinstance(benchmark_row, dict) else None
        truth_packet_total = _to_int(truth.get("packets_parsed"))
        benchmark_matches_truth = (
            isinstance(benchmark_row, dict)
            and benchmark_packet_total is not None
            and truth_packet_total is not None
            and benchmark_packet_total == truth_packet_total
        )
        notes = [
            "Normalized from the Unity replay matrix lane.",
            "This row uses canonical replay packets plus replay-driven Unity world-state verification.",
        ]
        if benchmark_matches_truth:
            notes.append("Merged with matching Unity editor-method benchmark metrics for the same canonical scenario.")
        if truth_path is not None:
            notes.append(f"source_truth_file={truth_path}")
        rows.append(
            {
                "scenario": route["scenario"],
                "metrics": {
                    "packets_received": _to_int(report.get("loaded_packets")),
                    "packets_parsed": _to_int(truth.get("packets_parsed")),
                    "packets_accepted": _to_int(truth.get("entity_state")),
                    "packets_rejected": 0,
                    "malformed": _to_int(truth.get("malformed")),
                    "socket_drops": None,
                    "queue_drops": None,
                    "p50_ingest_ms": None,
                    "p95_ingest_ms": None,
                    "p99_ingest_ms": None,
                    "steady_state_gc_bytes": _to_int(benchmark_row.get("steady_state_gc_bytes")) if benchmark_matches_truth else None,
                    "main_thread_apply_ms": _to_float(benchmark_row.get("main_thread_apply_ms")) if benchmark_matches_truth else None,
                    "runtime_elapsed_seconds": None,
                    "packets_per_sec": _to_float(benchmark_row.get("packets_per_sec")) if benchmark_matches_truth else None,
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
    return rows


def normalize_payload(
    runtime_payload: dict[str, Any],
    *,
    workflow_payload: dict[str, Any] | None,
    equivalence_payload: dict[str, Any] | None,
    install_smoke_payload: dict[str, Any] | None,
    replay_matrix_payload: dict[str, Any] | None,
    scenario: str,
    source_payload: str,
) -> dict[str, Any]:
    workflow_status = _lane_status(workflow_payload)
    equivalence_status = _lane_status(equivalence_payload)
    runtime_status = _lane_status(runtime_payload)
    details = _editor_method_details(runtime_payload)
    canonical_benchmark = _benchmark_row(details, "entity_state_1x10hz")
    canonical_benchmarks = _canonical_benchmark_rows(details)
    benchmark_rows_by_scenario = {
        str(row["scenario"]): row
        for row in canonical_benchmarks
        if isinstance(row, dict) and isinstance(row.get("scenario"), str)
    }
    replay_rows = _replay_rows(replay_matrix_payload, benchmark_rows_by_scenario=benchmark_rows_by_scenario)
    replay_scenarios = {row["scenario"] for row in replay_rows}

    tests = {}
    lanes = runtime_payload.get("lanes")
    if isinstance(lanes, list) and lanes:
        first_lane = lanes[0]
        if isinstance(first_lane, dict) and isinstance(first_lane.get("tests"), dict):
            tests = first_lane["tests"]

    notes = [
        "Normalized from Unity runtime verification evidence rather than a final shared scenario runner.",
    ]
    if canonical_benchmark is None:
        notes.append("Latency, packet-rate, and main-thread apply metrics remain null until the richer Unity benchmark lane lands.")
    else:
        notes.append(f"{len(canonical_benchmarks)} canonical Unity runtime benchmark row(s) are available from the Unity editor-method verification lane; broader Unity benchmark coverage is still pending.")
    if replay_rows:
        notes.append(f"{len(replay_rows)} canonical Unity replay-matrix row(s) are available from the shared scratch-project replay lane.")
    if isinstance(runtime_payload.get("unity_version"), str):
        notes.append(f"unity_version={runtime_payload['unity_version']}")
    if isinstance(tests.get("total"), int):
        notes.append(f"runtime_tests_total={tests['total']}")
    if isinstance(tests.get("passed"), int):
        notes.append(f"runtime_tests_passed={tests['passed']}")
    if workflow_status is not None:
        notes.append(f"workflow_status={workflow_status}")
    if equivalence_status is not None:
        notes.append(f"cross_engine_equivalence_status={equivalence_status}")

    runtime_pass = runtime_status == "pass"
    equivalence_pass = equivalence_status in {None, "pass", "complete"}
    workflow_pass = workflow_status in {None, "pass", "ok"}
    final_truth_match = runtime_pass and workflow_pass and equivalence_pass
    replay_criterion = _phase1_criterion(runtime_payload, "Replay demo moves GameObjects")
    replay_status = replay_criterion.get("status") if isinstance(replay_criterion, dict) else None
    scenario_truth_basis = [
        "Native library stages and loads in Unity",
        "UDP demo receives live Entity State traffic",
        "Entity mapper applies transforms to spawned GameObjects",
    ]
    benchmark_required_criteria = _required_criteria(runtime_payload, scenario_truth_basis)
    check_status_map = _check_status_map(details)
    benchmark_required_checks = []
    benchmark_required_check_names: set[str] = set()
    for criterion in benchmark_required_criteria:
        criterion_checks = criterion.get("required_checks")
        if not isinstance(criterion_checks, list):
            continue
        for row in criterion_checks:
            if not isinstance(row, dict):
                continue
            name = row.get("name")
            if not isinstance(name, str):
                continue
            benchmark_required_check_names.add(name)
            benchmark_required_checks.append(
                {
                    "name": name,
                    "status": check_status_map.get(name, row.get("status")),
                    "criterion": criterion.get("name"),
                }
            )
    failed_checks_outside_scope = sorted(
        name
        for name, status in check_status_map.items()
        if status == "fail" and name not in benchmark_required_check_names
    )

    benchmark_truth_match = (
        canonical_benchmark is not None
        and _criterion_complete(runtime_payload, "Native library stages and loads in Unity")
        and _criterion_complete(runtime_payload, "UDP demo receives live Entity State traffic")
        and _criterion_complete(runtime_payload, "Entity mapper applies transforms to spawned GameObjects")
    )

    host = merge_host_summary(
        current_host_summary(),
        system=platform.system(),
        release=platform.release(),
        machine=platform.machine(),
    )
    editor = runtime_payload.get("editor")
    if isinstance(editor, str) and editor:
        host["unity_editor"] = editor
    if isinstance(runtime_payload.get("unity_version"), str):
        host["unity_version"] = runtime_payload["unity_version"]

    primary_metrics = {
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
    }
    primary_truth = {
        "final_truth_match": final_truth_match,
        "runtime_overall_status": runtime_status,
        "workflow_status": workflow_status,
        "cross_engine_equivalence_status": equivalence_status,
        "phase1_exit_criteria": runtime_payload.get("phase1_exit_criteria"),
    }

    normalized_rows = [
        {
            "scenario": scenario,
            "metrics": primary_metrics,
            "truth": primary_truth,
        },
    ]
    for benchmark_row in canonical_benchmarks:
        benchmark_scenario = str(benchmark_row["scenario"])
        if benchmark_scenario in replay_scenarios:
            continue
        normalized_rows.append(
            {
                "scenario": benchmark_scenario,
                "metrics": {
                    **primary_metrics,
                    "packets_received": _to_int(benchmark_row.get("packets_received")),
                    "packets_parsed": _to_int(benchmark_row.get("packets_parsed")),
                    "packets_accepted": _to_int(benchmark_row.get("packets_accepted")),
                    "packets_rejected": _to_int(benchmark_row.get("packets_rejected")),
                    "malformed": _to_int(benchmark_row.get("malformed")),
                    "steady_state_gc_bytes": _to_int(benchmark_row.get("steady_state_gc_bytes")),
                    "main_thread_apply_ms": _to_float(benchmark_row.get("main_thread_apply_ms")),
                    "packets_per_sec": _to_float(benchmark_row.get("packets_per_sec")),
                    "notes": [
                        *notes,
                        f"canonical_alias_of={scenario}",
                        benchmark_row.get("notes")
                        if isinstance(benchmark_row.get("notes"), str)
                        else "This canonical alias row matches the shared benchmark scenario name, but still carries proof-only metrics until the richer Unity benchmark lane lands.",
                    ],
                },
                "truth": {
                    **primary_truth,
                    "final_truth_match": benchmark_truth_match,
                    "canonical_alias_of": scenario,
                    "benchmark_source": "unity_editor_method_verification",
                    "source_truth_schema": details.get("schema"),
                    "source_truth_file": source_payload,
                    "scenario_truth_basis": scenario_truth_basis,
                    "benchmark_required_criteria": benchmark_required_criteria,
                    "benchmark_required_checks": benchmark_required_checks,
                    "failed_checks_outside_benchmark_scope": failed_checks_outside_scope,
                    "suite_overall_status": runtime_status,
                },
            }
        )
    if replay_rows:
        normalized_rows[1:1] = replay_rows
    if isinstance(replay_criterion, dict):
        replay_notes = [
            "Normalized from the Unity runtime verification replay exit criterion.",
            "This row proves replay-driven world-state stepping, not measured replay throughput.",
        ]
        if isinstance(replay_criterion.get("note"), str):
            replay_notes.append(replay_criterion["note"])
        normalized_rows.append(
            {
                "scenario": "unity_replay_latest_state_apply",
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
                    "notes": replay_notes,
                },
                "truth": {
                    "final_truth_match": replay_status == "complete",
                    "runtime_overall_status": runtime_status,
                    "workflow_status": workflow_status,
                    "cross_engine_equivalence_status": equivalence_status,
                    "phase1_requirement_name": replay_criterion.get("name"),
                    "phase1_requirement_status": replay_status,
                    "phase1_required_checks": replay_criterion.get("required_checks"),
                },
            }
        )
    install_smoke_status = install_smoke_payload.get("status") if isinstance(install_smoke_payload, dict) else None
    install_elapsed = install_smoke_payload.get("elapsed_seconds") if isinstance(install_smoke_payload, dict) else None
    if isinstance(install_elapsed, (int, float)):
        runtime_notes = [
            "Normalized from the Unity install smoke lane.",
            "This row uses wall-clock runtime elapsed time, not ingest latency percentiles.",
        ]
        if isinstance(install_smoke_status, str):
            runtime_notes.append(f"install_smoke_status={install_smoke_status}")
        normalized_rows.append(
            {
                "scenario": "unity_install_smoke_runtime",
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
                    "runtime_elapsed_seconds": float(install_elapsed),
                    "packets_per_sec": None,
                    "notes": runtime_notes,
                },
                "truth": {
                    "final_truth_match": install_smoke_status == "pass",
                    "install_smoke_status": install_smoke_status,
                    "install_checks": install_smoke_payload.get("checks"),
                },
            }
        )

    return {
        "schema": "fastdis.engine_benchmark_report.v1",
        "surface": "unity",
        "surface_kind": "engine",
        "generated_at_utc": utc_now(),
        "host": host,
        "proof_context": build_proof_context(
            evidence_class="truth_backed_bridge",
            comparison_axis="engine_adapter",
            host=host,
            runtime_kind="engine",
            engine_family="unity",
            claim_boundary="Unity runtime verification proves installability, replay/world-state behavior, and selected canonical benchmark rows. Full runtime performance claims stay bounded to the scenarios directly measured in the Unity editor-method lane.",
            comparable=False,
            scenario_family=scenario_family_for(scenario),
            truth_backed=True,
            qualification_notes=[
                "workflow_and_runtime_bridge",
                "canonical_rows_only_for_measured_performance_claims",
            ],
        ),
        "source_payload": source_payload,
        "source_schema": "fastdis.unity_runtime_verification_bridge.v1",
        "summary": {
            **report_summary(normalized_rows),
        },
        "rows": normalized_rows,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# unity Engine Benchmark Report",
        "",
        f"- schema: `{report['schema']}`",
        f"- source_schema: `{report['source_schema']}`",
        f"- source_payload: `{report['source_payload']}`",
        "",
        "| scenario | truth | runtime status | workflow status | equivalence status |",
        "| --- | --- | --- | --- | --- |",
        "",
    ]
    for row in report["rows"]:
        truth = row["truth"]
        lines.append(
            f"| {row['scenario']} | {truth['final_truth_match']} | {truth.get('runtime_overall_status')} | {truth.get('workflow_status')} | {truth.get('cross_engine_equivalence_status')} |"
        )
    lines.append("")
    for row in report["rows"]:
        notes = row["metrics"].get("notes") or []
        if not notes:
            continue
        lines.append(f"## Notes: {row['scenario']}")
        lines.append("")
        for note in notes:
            lines.append(f"- {note}")
        lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    runtime_payload = load_json(args.runtime)
    if runtime_payload is None:
        raise SystemExit(f"runtime payload not found: {args.runtime}")
    workflow_payload = load_json(args.workflow)
    equivalence_payload = load_json(args.equivalence)
    install_smoke_payload = load_json(args.install_smoke)
    replay_matrix_payload = load_json(args.replay_matrix)
    report = normalize_payload(
        runtime_payload,
        workflow_payload=workflow_payload,
        equivalence_payload=equivalence_payload,
        install_smoke_payload=install_smoke_payload,
        replay_matrix_payload=replay_matrix_payload,
        scenario=args.scenario,
        source_payload=display_path(ROOT, args.runtime),
    )
    args.out_dir.mkdir(parents=True, exist_ok=True)
    stem = "unity_engine_benchmark_report"
    json_path = args.out_dir / f"{stem}.json"
    md_path = args.out_dir / f"{stem}.md"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report) + "\n", encoding="utf-8")
    print(f"json: {display_path(ROOT, json_path)}")
    print(f"md: {display_path(ROOT, md_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
