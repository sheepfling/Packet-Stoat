#!/usr/bin/env python3
"""Audit the benchmark contract stack: schema files plus current benchmark artifacts."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = ROOT / "build" / "reports" / "benchmark_contract_stack"

SCHEMA_SPECS = (
    ("schemas/json/fastdis.engine_benchmark_scenario.v1.schema.json", "fastdis.engine_benchmark_scenario.v1"),
    ("schemas/json/fastdis.engine_benchmark_truth.v1.schema.json", "fastdis.engine_benchmark_truth.v1"),
    ("schemas/json/fastdis.engine_benchmark_report.v1.schema.json", "fastdis.engine_benchmark_report.v1"),
    ("schemas/json/fastdis.engine_head_to_head_report.v1.schema.json", "fastdis.engine_head_to_head_report.v1"),
    ("schemas/json/fastdis.cross_engine_equivalence_report.v1.schema.json", "fastdis.cross_engine_equivalence_report.v1"),
    ("schemas/json/fastdis.engine_benchmark_matrix.v1.schema.json", "fastdis.engine_benchmark_matrix.v1"),
    ("schemas/json/fastdis.benchmark_coverage_report.v1.schema.json", "fastdis.benchmark_coverage_report.v1"),
    ("schemas/json/fastdis.scenario_contract_report.v1.schema.json", "fastdis.scenario_contract_report.v1"),
    ("schemas/json/fastdis.surface_claim_report.v1.schema.json", "fastdis.surface_claim_report.v1"),
    ("schemas/json/fastdis.core_cross_platform_harness_report.v1.schema.json", "fastdis.core_cross_platform_harness_report.v1"),
    ("schemas/json/fastdis.engine_benchmark_completion_audit.v1.schema.json", "fastdis.engine_benchmark_completion_audit.v1"),
    ("schemas/json/fastdis.benchmark_claim_summary.v1.schema.json", "fastdis.benchmark_claim_summary.v1"),
    ("schemas/json/fastdis.competitor_lane_summary.v1.schema.json", "fastdis.competitor_lane_summary.v1"),
    ("schemas/json/fastdis.competitor_benchmark_handoff_manifest.v1.schema.json", "fastdis.competitor_benchmark_handoff_manifest.v1"),
    ("schemas/json/fastdis.competitor_capture_manifest.v1.schema.json", "fastdis.competitor_capture_manifest.v1"),
    ("schemas/json/fastdis.competitor_capture_validation.v1.schema.json", "fastdis.competitor_capture_validation.v1"),
)

ARTIFACT_SPECS = (
    ("tests/data/engine_benchmark_scenarios/core_matrix.v1.json", "fastdis.engine_benchmark_scenario.v1"),
    ("tests/data/engine_benchmark_truth/core_matrix.v1.json", "fastdis.engine_benchmark_truth.v1"),
    ("build/reports/engine_benchmarks/native_engine_benchmark_report.json", "fastdis.engine_benchmark_report.v1"),
    ("build/reports/engine_benchmarks/c_engine_benchmark_report.json", "fastdis.engine_benchmark_report.v1"),
    ("build/reports/engine_benchmarks/cpp_engine_benchmark_report.json", "fastdis.engine_benchmark_report.v1"),
    ("build/reports/engine_benchmarks/python_ctypes_engine_benchmark_report.json", "fastdis.engine_benchmark_report.v1"),
    ("build/reports/engine_benchmarks/unreal_engine_benchmark_report.json", "fastdis.engine_benchmark_report.v1"),
    ("build/reports/engine_benchmarks/unity_engine_benchmark_report.json", "fastdis.engine_benchmark_report.v1"),
    ("build/reports/engine_benchmarks/godot_engine_benchmark_report.json", "fastdis.engine_benchmark_report.v1"),
    ("build/reports/engine_head_to_head/unreal_vs_grill.json", "fastdis.engine_head_to_head_report.v1"),
    ("build/reports/cross_engine_equivalence.json", "fastdis.cross_engine_equivalence_report.v1"),
    ("build/reports/benchmark_matrix/benchmark_matrix.json", "fastdis.engine_benchmark_matrix.v1"),
    ("build/reports/benchmark_coverage/benchmark_coverage_report.json", "fastdis.benchmark_coverage_report.v1"),
    ("build/reports/scenario_contract/scenario_contract_report.json", "fastdis.scenario_contract_report.v1"),
    ("build/reports/surface_claim_report/surface_claim_report.json", "fastdis.surface_claim_report.v1"),
    ("build/reports/core_cross_platform_harness/core_cross_platform_harness_report.json", "fastdis.core_cross_platform_harness_report.v1"),
    ("build/reports/benchmark_completion_audit/benchmark_completion_audit.json", "fastdis.engine_benchmark_completion_audit.v1"),
    ("build/reports/benchmark_claim_summary/benchmark_claim_summary.json", "fastdis.benchmark_claim_summary.v1"),
    ("build/reports/competitor_lane_summary/competitor_lane_summary.json", "fastdis.competitor_lane_summary.v1"),
    ("build/reports/competitor_capture_manifest.json", "fastdis.competitor_capture_manifest.v1"),
    ("build/reports/competitor_capture_validation.json", "fastdis.competitor_capture_validation.v1"),
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_OUT_DIR / "benchmark_contract_stack.json")
    parser.add_argument("--md-out", type=Path, default=DEFAULT_OUT_DIR / "benchmark_contract_stack.md")
    parser.add_argument("--fail-missing", action="store_true", help="Return nonzero when any schema or artifact is missing or mismatched")
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


def _schema_row(relative: str, expected_schema: str) -> dict[str, Any]:
    path = ROOT / relative
    exists = path.is_file()
    row = {
        "kind": "schema",
        "path": relative,
        "expected_schema": expected_schema,
        "exists": exists,
        "status": "missing" if not exists else "pass",
        "issues": [],
    }
    if not exists:
        row["issues"].append("schema file missing")
        return row
    payload = load_json(path)
    observed_id = payload.get("$id")
    observed_const = (((payload.get("properties") or {}).get("schema") or {}).get("const"))
    row["schema_id"] = observed_id
    row["observed_schema"] = observed_const
    if observed_const != expected_schema:
        row["status"] = "fail"
        row["issues"].append(f"schema const mismatch: expected `{expected_schema}`, got `{observed_const}`")
    if not isinstance(observed_id, str) or expected_schema not in observed_id:
        row["status"] = "fail"
        row["issues"].append("schema $id does not include expected schema name")
    return row


def _artifact_row(relative: str, expected_schema: str) -> dict[str, Any]:
    path = ROOT / relative
    exists = path.is_file()
    row = {
        "kind": "artifact",
        "path": relative,
        "expected_schema": expected_schema,
        "exists": exists,
        "status": "missing" if not exists else "pass",
        "issues": [],
    }
    if not exists:
        row["issues"].append("artifact file missing")
        return row
    payload = load_json(path)
    observed = payload.get("schema")
    row["observed_schema"] = observed
    if observed != expected_schema:
        row["status"] = "fail"
        row["issues"].append(f"artifact schema mismatch: expected `{expected_schema}`, got `{observed}`")
    return row


def build_report() -> dict[str, Any]:
    schema_rows = [_schema_row(relative, expected) for relative, expected in SCHEMA_SPECS]
    artifact_rows = [_artifact_row(relative, expected) for relative, expected in ARTIFACT_SPECS]
    all_rows = schema_rows + artifact_rows
    fail_count = sum(1 for row in all_rows if row["status"] == "fail")
    missing_count = sum(1 for row in all_rows if row["status"] == "missing")
    pass_count = sum(1 for row in all_rows if row["status"] == "pass")
    status = "pass" if fail_count == 0 and missing_count == 0 else "fail"
    return {
        "schema": "fastdis.benchmark_contract_stack.v1",
        "generated_at_utc": utc_now(),
        "status": status,
        "summary": {
            "schema_count": len(schema_rows),
            "artifact_count": len(artifact_rows),
            "pass_count": pass_count,
            "fail_count": fail_count,
            "missing_count": missing_count,
        },
        "rows": all_rows,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Benchmark Contract Stack",
        "",
        f"- schema: `{report['schema']}`",
        f"- status: `{report['status']}`",
        f"- schema_count: `{report['summary']['schema_count']}`",
        f"- artifact_count: `{report['summary']['artifact_count']}`",
        f"- pass_count: `{report['summary']['pass_count']}`",
        f"- fail_count: `{report['summary']['fail_count']}`",
        f"- missing_count: `{report['summary']['missing_count']}`",
        "",
        "| kind | path | expected | observed | status | issues |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in report["rows"]:
        issues = "; ".join(row["issues"]) if row["issues"] else "none"
        observed = row.get("observed_schema", row.get("schema_id", "n/a"))
        lines.append(
            f"| {row['kind']} | {row['path']} | {row['expected_schema']} | {observed} | {row['status']} | {issues} |"
        )
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report = build_report()
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.md_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    args.md_out.write_text(render_markdown(report) + "\n", encoding="utf-8")
    print(f"json: {display_path(args.json_out)}")
    print(f"md: {display_path(args.md_out)}")
    return 1 if args.fail_missing and report["status"] != "pass" else 0


if __name__ == "__main__":
    raise SystemExit(main())
