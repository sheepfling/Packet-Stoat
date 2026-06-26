#!/usr/bin/env python3
"""Build a Unity-facing head-to-head benchmark readiness report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FASTDIS = ROOT / "build" / "benchmark_results" / "current" / "current.json"
DEFAULT_GRILL = ROOT / "verification_reports" / "unity_grill_baseline" / "grill_unity_benchmark_baseline.json"
GRILL_TEMPLATE = ROOT / "verification_reports" / "unity_grill_baseline" / "grill_unity_benchmark_baseline.template.json"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fastdis", type=Path, default=DEFAULT_FASTDIS)
    parser.add_argument("--grill", type=Path, default=DEFAULT_GRILL)
    parser.add_argument("--json-out", type=Path, default=ROOT / "build" / "reports" / "unity_head_to_head_benchmark.json")
    parser.add_argument("--md-out", type=Path, default=ROOT / "build" / "reports" / "unity_head_to_head_benchmark.md")
    return parser.parse_args(argv)


def load_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def summarize_fastdis(payload: dict | None) -> dict[str, object]:
    if payload is None:
        return {"available": False, "native_case_count": 0, "ctypes_case_count": 0}
    native_results = payload.get("native", {}).get("results", [])
    ctypes_results = payload.get("ctypes", {}).get("results", []) if payload.get("ctypes") else []
    return {
        "available": True,
        "native_case_count": len(native_results),
        "ctypes_case_count": len(ctypes_results),
        "host_system": payload.get("host", {}).get("system"),
        "host_machine": payload.get("host", {}).get("machine"),
    }


def validate_fastdis(payload: dict[str, Any] | None) -> list[str]:
    if payload is None:
        return ["missing payload"]
    errors: list[str] = []
    required_top_level = ("host", "native", "qualification")
    for field in required_top_level:
        if field not in payload:
            errors.append(f"missing top-level field `{field}`")
    native = payload.get("native")
    if not isinstance(native, dict):
        errors.append("`native` must be an object")
    else:
        results = native.get("results")
        if not isinstance(results, list) or not results:
            errors.append("`native.results` must be a non-empty array")
    qualification = payload.get("qualification")
    if not isinstance(qualification, dict):
        errors.append("`qualification` must be an object")
    else:
        summary = qualification.get("summary")
        if not isinstance(summary, dict):
            errors.append("`qualification.summary` must be an object")
        elif not isinstance(summary.get("native_case_count"), int):
            errors.append("`qualification.summary.native_case_count` must be an integer")
    return errors


def validate_grill(payload: dict[str, Any] | None) -> list[str]:
    if payload is None:
        return ["missing payload"]
    errors: list[str] = []
    if payload.get("schema") != "fastdis.unity_grill_benchmark_baseline.v1":
        errors.append("`schema` must equal `fastdis.unity_grill_benchmark_baseline.v1`")
    for field in ("product", "captured_at_utc", "repository", "unity", "host", "scenario", "results"):
        if field not in payload:
            errors.append(f"missing top-level field `{field}`")
    if payload.get("product") != "GRILL DIS for Unity":
        errors.append("`product` must equal `GRILL DIS for Unity`")
    repository = payload.get("repository")
    if not isinstance(repository, dict):
        errors.append("`repository` must be an object")
    else:
        for field in ("url", "commit"):
            value = repository.get(field)
            if not isinstance(value, str) or not value or value.startswith("REPLACE_ME"):
                errors.append(f"`repository.{field}` must be a populated string")
    unity = payload.get("unity")
    if not isinstance(unity, dict):
        errors.append("`unity` must be an object")
    else:
        version = unity.get("version")
        if not isinstance(version, str) or not version or version.startswith("REPLACE_ME"):
            errors.append("`unity.version` must be a populated string")
    host = payload.get("host")
    if not isinstance(host, dict):
        errors.append("`host` must be an object")
    else:
        for field in ("system", "machine"):
            value = host.get(field)
            if not isinstance(value, str) or not value or value.startswith("REPLACE_ME"):
                errors.append(f"`host.{field}` must be a populated string")
    scenario = payload.get("scenario")
    if not isinstance(scenario, dict):
        errors.append("`scenario` must be an object")
    else:
        for field in ("scene", "traffic_mix"):
            value = scenario.get(field)
            if not isinstance(value, str) or not value or value.startswith("REPLACE_ME"):
                errors.append(f"`scenario.{field}` must be a populated string")
        for field in ("entity_counts", "update_hz"):
            value = scenario.get(field)
            if not isinstance(value, list) or not value:
                errors.append(f"`scenario.{field}` must be a non-empty array")
    results = payload.get("results")
    if not isinstance(results, list) or not results:
        errors.append("`results` must be a non-empty array")
    else:
        sample = results[0]
        if not isinstance(sample, dict):
            errors.append("`results[0]` must be an object")
        else:
            required_row_fields = ("case", "entity_count", "update_hz", "packets_per_sec", "main_thread_ms_avg", "gc_alloc_bytes_per_frame")
            for field in required_row_fields:
                if field not in sample:
                    errors.append(f"`results[0].{field}` is required")
    return errors


def summarize_grill(payload: dict[str, Any] | None) -> dict[str, object]:
    if payload is None:
        return {"available": False, "result_count": 0}
    results = payload.get("results")
    if not isinstance(results, list):
        results = []
    unity = payload.get("unity") if isinstance(payload.get("unity"), dict) else {}
    repository = payload.get("repository") if isinstance(payload.get("repository"), dict) else {}
    return {
        "available": True,
        "result_count": len(results),
        "unity_version": unity.get("version"),
        "repository_commit": repository.get("commit"),
        "scene": (payload.get("scenario") or {}).get("scene") if isinstance(payload.get("scenario"), dict) else None,
    }


def _to_float(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _fastdis_packets_per_sec(row: dict[str, Any]) -> float | None:
    direct = _to_float(row.get("packets_per_sec"))
    if direct is not None:
        return direct
    packets = _to_float(row.get("packets"))
    avg_ms = _to_float(row.get("avg_ms"))
    if packets is None or avg_ms is None or avg_ms <= 0:
        return None
    return packets / (avg_ms / 1000.0)


def _ratio(fastdis_value: float | None, grill_value: float | None, *, larger_is_better: bool) -> float | None:
    if fastdis_value is None or grill_value is None or fastdis_value <= 0 or grill_value <= 0:
        return None
    return (fastdis_value / grill_value) if larger_is_better else (grill_value / fastdis_value)


def build_comparison(payload_fastdis: dict[str, Any] | None, payload_grill: dict[str, Any] | None) -> dict[str, Any]:
    if payload_fastdis is None or payload_grill is None:
        return {"matched_cases": 0, "fastdis_native_cases": 0, "grill_cases": 0, "rows": []}
    fastdis_rows = (payload_fastdis.get("native") or {}).get("results") or []
    grill_rows = payload_grill.get("results") or []
    if not isinstance(fastdis_rows, list) or not isinstance(grill_rows, list):
        return {"matched_cases": 0, "fastdis_native_cases": 0, "grill_cases": 0, "rows": []}
    fastdis_by_case = {
        str(row.get("case")): row
        for row in fastdis_rows
        if isinstance(row, dict) and isinstance(row.get("case"), str)
    }
    rows: list[dict[str, Any]] = []
    for grill_row in grill_rows:
        if not isinstance(grill_row, dict):
            continue
        case = grill_row.get("case")
        if not isinstance(case, str):
            continue
        fastdis_row = fastdis_by_case.get(case)
        if fastdis_row is None:
            continue
        fastdis_pps = _fastdis_packets_per_sec(fastdis_row)
        grill_pps = _to_float(grill_row.get("packets_per_sec"))
        fastdis_avg_ms = _to_float(fastdis_row.get("avg_ms"))
        grill_main_thread_ms = _to_float(grill_row.get("main_thread_ms_avg"))
        rows.append(
            {
                "case": case,
                "fastdis": {
                    "packets_per_sec": fastdis_pps,
                    "avg_ms": fastdis_avg_ms,
                    "p95_ms": _to_float(fastdis_row.get("p95_ms")),
                },
                "grill": {
                    "packets_per_sec": grill_pps,
                    "main_thread_ms_avg": grill_main_thread_ms,
                    "gc_alloc_bytes_per_frame": grill_row.get("gc_alloc_bytes_per_frame"),
                },
                "ratios": {
                    "packets_per_sec": _ratio(fastdis_pps, grill_pps, larger_is_better=True),
                    "reported_ms": _ratio(fastdis_avg_ms, grill_main_thread_ms, larger_is_better=False),
                },
            }
        )
    return {
        "matched_cases": len(rows),
        "fastdis_native_cases": len(fastdis_by_case),
        "grill_cases": len([row for row in grill_rows if isinstance(row, dict)]),
        "rows": rows,
    }


def render_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Unity Head-to-Head Benchmark Readiness",
        "",
        f"- status: `{payload['status']}`",
        "",
        payload["note"],
        "",
        "## Inputs",
        "",
        f"- fastdis: `{payload['inputs']['fastdis']}` exists=`{payload['inputs']['fastdis_exists']}` valid=`{payload['inputs']['fastdis_valid']}`",
        f"- grill: `{payload['inputs']['grill']}` exists=`{payload['inputs']['grill_exists']}` valid=`{payload['inputs']['grill_valid']}`",
        f"- grill_template: `{payload['inputs']['grill_template']}` exists=`{payload['inputs']['grill_template_exists']}`",
        "",
        "## FastDIS Snapshot",
        "",
        f"- native_case_count: `{payload['fastdis_summary']['native_case_count']}`",
        f"- ctypes_case_count: `{payload['fastdis_summary']['ctypes_case_count']}`",
        f"- host_system: `{payload['fastdis_summary'].get('host_system')}`",
        f"- host_machine: `{payload['fastdis_summary'].get('host_machine')}`",
        "",
        "## GRILL Snapshot",
        "",
        f"- result_count: `{payload['grill_summary']['result_count']}`",
        f"- unity_version: `{payload['grill_summary'].get('unity_version')}`",
        f"- repository_commit: `{payload['grill_summary'].get('repository_commit')}`",
        f"- scene: `{payload['grill_summary'].get('scene')}`",
        "",
        "## Validation",
        "",
    ]
    for error in payload["validation"]["fastdis_errors"]:
        lines.append(f"- fastdis_error: `{error}`")
    for error in payload["validation"]["grill_errors"]:
        lines.append(f"- grill_error: `{error}`")
    if not payload["validation"]["fastdis_errors"] and not payload["validation"]["grill_errors"]:
        lines.append("- validation: `all required fields present`")
    lines.extend(
        [
            "",
            "## Comparison",
            "",
            f"- matched_cases: `{payload['comparison']['matched_cases']}`",
            f"- fastdis_native_cases: `{payload['comparison']['fastdis_native_cases']}`",
            f"- grill_cases: `{payload['comparison']['grill_cases']}`",
            "- `packets_per_sec` ratio uses larger-is-better math: `FastDIS / GRILL`.",
            "- `reported_ms` ratio uses lower-is-better math: `GRILL / FastDIS` so values above `1.0` favor FastDIS.",
            "- `reported_ms` compares FastDIS native benchmark `avg_ms` against GRILL-reported Unity main-thread average only when both are present. Treat it as directional evidence, not a full pipeline equivalence claim.",
            "",
            "## Capture Contract",
            "",
            "- Use the template in `verification_reports/unity_grill_baseline/grill_unity_benchmark_baseline.template.json`.",
            "- Replace every `REPLACE_ME` field and record at least one real benchmark row in `results`.",
            "- Keep the benchmark scene, traffic mix, entity counts, and update rates aligned with the FastDIS comparison run.",
            "",
        ]
    )
    if payload["comparison"]["rows"]:
        lines.extend(
            [
                "### Matched Cases",
                "",
                "| case | fastdis packets/sec | grill packets/sec | packets/sec ratio | fastdis avg ms | grill main-thread avg ms | reported ms ratio |",
                "| --- | --- | --- | --- | --- | --- | --- |",
            ]
        )
        for row in payload["comparison"]["rows"]:
            lines.append(
                "| {case} | {fd_pps} | {gr_pps} | {pps_ratio} | {fd_ms} | {gr_ms} | {ms_ratio} |".format(
                    case=row["case"],
                    fd_pps=row["fastdis"]["packets_per_sec"],
                    gr_pps=row["grill"]["packets_per_sec"],
                    pps_ratio=row["ratios"]["packets_per_sec"],
                    fd_ms=row["fastdis"]["avg_ms"],
                    gr_ms=row["grill"]["main_thread_ms_avg"],
                    ms_ratio=row["ratios"]["reported_ms"],
                )
            )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    fastdis_payload = load_json(args.fastdis)
    grill_payload = load_json(args.grill)
    fastdis_errors = validate_fastdis(fastdis_payload)
    grill_errors = validate_grill(grill_payload)
    fastdis_summary = summarize_fastdis(fastdis_payload)
    grill_summary = summarize_grill(grill_payload)
    comparison = build_comparison(fastdis_payload, grill_payload)
    complete = not fastdis_errors and not grill_errors
    payload = {
        "schema": "fastdis.unity_head_to_head_benchmark.v1",
        "status": "complete" if complete else "incomplete",
        "note": (
            "FastDIS and GRILL baseline benchmark payloads are both present and ready for side-by-side comparison."
            if complete
            else "A side-by-side claim is blocked until both the FastDIS benchmark payload and a valid GRILL Unity baseline payload satisfy the capture contract."
        ),
        "inputs": {
            "fastdis": display_path(args.fastdis),
            "fastdis_exists": args.fastdis.exists(),
            "fastdis_valid": not fastdis_errors,
            "grill": display_path(args.grill),
            "grill_exists": args.grill.exists(),
            "grill_valid": not grill_errors,
            "grill_template": display_path(GRILL_TEMPLATE),
            "grill_template_exists": GRILL_TEMPLATE.exists(),
        },
        "fastdis_summary": fastdis_summary,
        "grill_summary": grill_summary,
        "comparison": comparison,
        "validation": {
            "fastdis_errors": fastdis_errors,
            "grill_errors": grill_errors,
        },
    }
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    args.md_out.write_text(render_markdown(payload) + "\n", encoding="utf-8")
    print(f"unity benchmark json: {display_path(args.json_out)}")
    print(f"unity benchmark md: {display_path(args.md_out)}")
    return 0 if complete else 1


if __name__ == "__main__":
    raise SystemExit(main())
