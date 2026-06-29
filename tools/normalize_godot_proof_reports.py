#!/usr/bin/env python3
"""Normalize Godot proof artifacts into the shared engine-benchmark report shape."""

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

from proof_context import build_proof_context, current_host_summary, merge_host_summary, scenario_family_for

DEFAULT_WORKFLOW = ROOT / "build" / "reports" / "godot_workflow_report.json"
DEFAULT_ORIENTATION = ROOT / "build" / "reports" / "orientation_assurance_live" / "godot_good_compare.json"
DEFAULT_NETWORK_INGEST = ROOT / "build" / "reports" / "network_ingest_matrix" / "network_ingest_matrix.json"
DEFAULT_REPLAY_MATRIX = ROOT / "build" / "reports" / "godot_replay_matrix" / "godot_replay_matrix.json"
DEFAULT_OUT_DIR = ROOT / "build" / "reports" / "engine_benchmarks"
CANONICAL_REPLAY_SCENARIO = "replay_latest_state_apply"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workflow", type=Path, default=DEFAULT_WORKFLOW)
    parser.add_argument("--orientation", type=Path, default=DEFAULT_ORIENTATION)
    parser.add_argument("--network-ingest", type=Path, default=DEFAULT_NETWORK_INGEST)
    parser.add_argument("--replay-matrix", type=Path, default=DEFAULT_REPLAY_MATRIX)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--scenario", default="godot_proof_verification")
    return parser.parse_args(argv)


def load_json(path: Path | None) -> dict[str, Any] | None:
    if path is None or not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


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
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    return None


def _load_truth_from_route(route: dict[str, Any]) -> tuple[dict[str, Any], str | None]:
    inline_truth = route.get("truth")
    if isinstance(inline_truth, dict):
        truth_file = route.get("truth_file")
        truth_label = None
        if isinstance(truth_file, str) and truth_file:
            truth_path = Path(truth_file).expanduser()
            truth_label = display_path(truth_path if truth_path.is_absolute() else (ROOT / truth_path).resolve())
        return inline_truth, truth_label
    truth_file = route.get("truth_file")
    if not isinstance(truth_file, str) or not truth_file:
        return {}, None
    truth_path = Path(truth_file).expanduser()
    if not truth_path.is_absolute():
        truth_path = (ROOT / truth_path).resolve()
    if not truth_path.exists():
        return {}, display_path(truth_path)
    loaded = load_json(truth_path)
    return (loaded or {}), display_path(truth_path)


def _live_udp_rows(network_ingest_payload: dict[str, Any] | None) -> list[dict[str, Any]]:
    routes = network_ingest_payload.get("routes") if isinstance(network_ingest_payload, dict) else None
    if not isinstance(routes, list):
        return []
    rows: list[dict[str, Any]] = []
    for route in routes:
        if not (
            isinstance(route, dict)
            and route.get("surface") == "godot"
            and route.get("mode") == "live_udp"
            and isinstance(route.get("scenario"), str)
        ):
            continue
        report = route.get("report") if isinstance(route.get("report"), dict) else {}
        truth, truth_path = _load_truth_from_route(route)
        malformed = _to_int(truth.get("malformed"))
        packets_parsed = _to_int(truth.get("packets_parsed"))
        packets_accepted = _to_int(truth.get("entity_state"))
        packets_rejected = None
        if packets_parsed is not None and packets_accepted is not None and malformed is not None:
            packets_rejected = max(packets_parsed - packets_accepted - malformed, 0)
        notes = [
            "Normalized from the Godot live UDP smoke lane.",
            "This row uses canonical sender truth plus live engine entity movement verification.",
        ]
        if truth_path is not None:
            notes.append(f"source_truth_file={truth_path}")
        rows.append(
            {
                "scenario": route["scenario"],
                "metrics": {
                    "packets_received": _to_int(report.get("packets_received")),
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
    return rows


def _replay_rows(replay_matrix_payload: dict[str, Any] | None) -> list[dict[str, Any]]:
    routes = replay_matrix_payload.get("routes") if isinstance(replay_matrix_payload, dict) else None
    if not isinstance(routes, list):
        return []
    rows: list[dict[str, Any]] = []
    for route in routes:
        if not (
            isinstance(route, dict)
            and route.get("surface") == "godot"
            and route.get("mode") == "replay"
            and isinstance(route.get("scenario"), str)
        ):
            continue
        report = route.get("report") if isinstance(route.get("report"), dict) else {}
        truth, truth_path = _load_truth_from_route(route)
        notes = [
            "Normalized from the Godot replay matrix lane.",
            "This row uses canonical replay packets plus live engine entity movement verification.",
        ]
        if truth_path is not None:
            notes.append(f"source_truth_file={truth_path}")
        rows.append(
            {
                "scenario": CANONICAL_REPLAY_SCENARIO,
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
    return rows


def normalize_payload(
    workflow_payload: dict[str, Any],
    *,
    orientation_payload: dict[str, Any] | None,
    network_ingest_payload: dict[str, Any] | None,
    replay_matrix_payload: dict[str, Any] | None,
    scenario: str,
    source_payload: str,
) -> dict[str, Any]:
    doctor = workflow_payload.get("doctor") if isinstance(workflow_payload.get("doctor"), dict) else {}
    lanes = workflow_payload.get("lanes") if isinstance(workflow_payload.get("lanes"), dict) else {}
    doctor_status = doctor.get("status")
    build_status = (lanes.get("build") or {}).get("status") if isinstance(lanes.get("build"), dict) else None
    verify_status = (lanes.get("verify") or {}).get("status") if isinstance(lanes.get("verify"), dict) else None
    demo_status = (lanes.get("demo") or {}).get("status") if isinstance(lanes.get("demo"), dict) else None
    missing_lib_status = (lanes.get("missing_lib") or {}).get("status") if isinstance(lanes.get("missing_lib"), dict) else None
    orientation_status, orientation_passed, orientation_total = _orientation_pass(orientation_payload)

    notes = [
        "Normalized from Godot proof artifacts rather than a final shared scenario runner.",
        "Latency, packet-rate, and main-thread apply metrics remain null until the richer Godot benchmark lane lands.",
    ]
    if isinstance(doctor_status, str):
        notes.append(f"doctor_status={doctor_status}")
    if isinstance(build_status, str):
        notes.append(f"build_status={build_status}")
    if isinstance(verify_status, str):
        notes.append(f"verify_status={verify_status}")
    if isinstance(demo_status, str):
        notes.append(f"demo_status={demo_status}")
    if isinstance(missing_lib_status, str):
        notes.append(f"missing_lib_status={missing_lib_status}")
    if orientation_passed is not None and orientation_total is not None:
        notes.append(f"orientation_cases_passed={orientation_passed}/{orientation_total}")

    doctor_host = doctor.get("host") if isinstance(doctor.get("host"), dict) else {}
    host: dict[str, Any] = current_host_summary()
    for key in ("platform", "arch", "godot"):
        if key in doctor_host:
            mapped = "system" if key == "platform" else ("godot_path" if key == "godot" else key)
            host = merge_host_summary(host, **{mapped: doctor_host[key]})

    final_truth_match = (
        doctor_status == "passed"
        and build_status == "passed"
        and verify_status == "passed"
        and demo_status == "passed"
        and missing_lib_status == "passed"
        and orientation_status is True
    )

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
                "doctor_status": doctor_status,
                "build_status": build_status,
                "verify_status": verify_status,
                "demo_status": demo_status,
                "missing_lib_status": missing_lib_status,
                "orientation_status": orientation_status,
                "doctor_checks": doctor.get("checks"),
                "orientation_result_count": orientation_total,
            },
        }
    ]
    if demo_status is not None:
        demo_elapsed = (lanes.get("demo") or {}).get("elapsed_seconds") if isinstance(lanes.get("demo"), dict) else None
        replay_notes = [
            "Normalized from the Godot demo replay smoke lane.",
            "This row proves replay-driven entity motion, not measured replay throughput.",
        ]
        normalized_rows.append(
            {
                "scenario": CANONICAL_REPLAY_SCENARIO,
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
                    "final_truth_match": demo_status == "passed",
                    "doctor_status": doctor_status,
                    "build_status": build_status,
                    "verify_status": verify_status,
                    "demo_status": demo_status,
                    "missing_lib_status": missing_lib_status,
                    "orientation_status": orientation_status,
                    "doctor_checks": doctor.get("checks"),
                    "orientation_result_count": orientation_total,
                },
            }
        )
        if isinstance(demo_elapsed, (int, float)):
            runtime_notes = [
                "Normalized from the Godot demo lane wall-clock runtime.",
                "This row uses wall-clock runtime elapsed time, not ingest latency percentiles.",
                f"demo_status={demo_status}",
            ]
            normalized_rows.append(
                {
                    "scenario": "godot_demo_runtime",
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
                        "runtime_elapsed_seconds": float(demo_elapsed),
                        "packets_per_sec": None,
                        "notes": runtime_notes,
                    },
                    "truth": {
                        "final_truth_match": demo_status == "passed",
                        "demo_status": demo_status,
                    },
                }
            )
    live_udp_rows = _live_udp_rows(network_ingest_payload)
    if live_udp_rows:
        normalized_rows[1:1] = live_udp_rows
    replay_rows = _replay_rows(replay_matrix_payload)
    if replay_rows:
        normalized_rows[1:1] = replay_rows

    return {
        "schema": "fastdis.engine_benchmark_report.v1",
        "surface": "godot",
        "surface_kind": "engine",
        "generated_at_utc": utc_now(),
        "host": host,
        "proof_context": build_proof_context(
            evidence_class="truth_backed_bridge",
            comparison_axis="engine_adapter",
            host=host,
            runtime_kind="engine",
            engine_family="godot",
            claim_boundary="Godot proof normalization proves install/build/replay/orientation coverage plus live UDP smoke participation. Performance claims remain bounded until direct measured Godot benchmark lanes exist for canonical scenarios.",
            comparable=False,
            scenario_family=scenario_family_for(scenario),
            truth_backed=True,
            qualification_notes=[
                "workflow_bridge",
                "replay_and_live_udp_rows_are_verification_evidence_not_full_benchmarks",
            ],
        ),
        "source_payload": source_payload,
        "source_schema": "fastdis.godot_proof_bridge.v1",
        "summary": {
            "row_count": len(normalized_rows),
            "latency_rows": 0,
            "runtime_metric_rows": sum(1 for row in normalized_rows if row["metrics"]["runtime_elapsed_seconds"] is not None),
            "truth_rows": sum(1 for row in normalized_rows if row["truth"]["final_truth_match"] is not None),
        },
        "rows": normalized_rows,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# godot Engine Benchmark Report",
        "",
        f"- schema: `{report['schema']}`",
        f"- source_schema: `{report['source_schema']}`",
        f"- source_payload: `{report['source_payload']}`",
        "",
        "| scenario | truth | doctor | build | verify | demo | missing-lib | orientation |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
        "",
    ]
    for row in report["rows"]:
        truth = row["truth"]
        lines.append(
            f"| {row['scenario']} | {truth['final_truth_match']} | {truth.get('doctor_status')} | {truth.get('build_status')} | {truth.get('verify_status')} | {truth.get('demo_status')} | {truth.get('missing_lib_status')} | {truth.get('orientation_status')} |"
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
    workflow_payload = load_json(args.workflow)
    if workflow_payload is None:
        raise SystemExit(f"workflow payload not found: {args.workflow}")
    orientation_payload = load_json(args.orientation)
    network_ingest_payload = load_json(args.network_ingest)
    replay_matrix_payload = load_json(args.replay_matrix)
    report = normalize_payload(
        workflow_payload,
        orientation_payload=orientation_payload,
        network_ingest_payload=network_ingest_payload,
        replay_matrix_payload=replay_matrix_payload,
        scenario=args.scenario,
        source_payload=display_path(args.workflow),
    )
    args.out_dir.mkdir(parents=True, exist_ok=True)
    stem = "godot_engine_benchmark_report"
    json_path = args.out_dir / f"{stem}.json"
    md_path = args.out_dir / f"{stem}.md"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report) + "\n", encoding="utf-8")
    print(f"json: {display_path(json_path)}")
    print(f"md: {display_path(md_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
