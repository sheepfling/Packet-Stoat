#!/usr/bin/env python3
"""Audit canonical JSON report freshness and metadata without reading Markdown."""

from __future__ import annotations

import argparse
from datetime import UTC
from datetime import datetime
import json
from pathlib import Path
from typing import Any

from artifacts import REPORTS_DIR, rel
from report_envelope import utc_now
from report_envelope import write_json_report


ROOT = Path(__file__).resolve().parents[1]
REPORT_JSON = REPORTS_DIR / "json_report_freshness_audit.json"
REPORT_MD = REPORTS_DIR / "json_report_freshness_audit.md"

TARGETS: dict[str, dict[str, str]] = {
    "benchmark_matrix": {
        "path": "artifacts/reports/benchmark_matrix/benchmark_matrix.json",
        "schema": "fastdis.engine_benchmark_matrix.v1",
        "generated_at_field": "generated_at_utc",
    },
    "benchmark_coverage": {
        "path": "artifacts/reports/benchmark_coverage/benchmark_coverage_report.json",
        "schema": "fastdis.benchmark_coverage_report.v1",
        "generated_at_field": "generated_at_utc",
    },
    "core_cross_platform_harness": {
        "path": "artifacts/reports/core_cross_platform_harness/core_cross_platform_harness_report.json",
        "schema": "fastdis.core_cross_platform_harness_report.v1",
        "generated_at_field": "generated_at_utc",
    },
    "scenario_contract": {
        "path": "artifacts/reports/scenario_contract/scenario_contract_report.json",
        "schema": "fastdis.scenario_contract_report.v1",
        "generated_at_field": "generated_at_utc",
    },
    "surface_claim_report": {
        "path": "artifacts/reports/surface_claim_report/surface_claim_report.json",
        "schema": "fastdis.surface_claim_report.v1",
        "generated_at_field": "generated_at_utc",
    },
    "benchmark_claim_summary": {
        "path": "artifacts/reports/benchmark_claim_summary/benchmark_claim_summary.json",
        "schema": "fastdis.benchmark_claim_summary.v1",
        "generated_at_field": "generated_at_utc",
    },
    "competitor_lane_summary": {
        "path": "artifacts/reports/competitor_lane_summary/competitor_lane_summary.json",
        "schema": "fastdis.competitor_lane_summary.v1",
        "generated_at_field": "generated_at_utc",
    },
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", action="append", choices=sorted(TARGETS), help="Named freshness target to audit")
    parser.add_argument("--path", dest="paths", type=Path, action="append", help="Additional JSON report path to audit")
    parser.add_argument("--max-age-hours", type=float, default=168.0, help="Fail when generated_at is older than this many hours")
    parser.add_argument("--ignore-missing", action="store_true", help="Treat missing reports as skipped instead of failing")
    parser.add_argument("--no-write", action="store_true", help="Do not write artifacts/reports outputs")
    return parser.parse_args(argv)


def _parse_timestamp(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _target_rows(args: argparse.Namespace) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for name in args.target or []:
        spec = TARGETS[name]
        rows.append({"name": name, **spec})
    for path in args.paths or []:
        rows.append({"name": rel(path), "path": str(path), "schema": "", "generated_at_field": ""})
    if rows:
        return rows
    return [{"name": name, **spec} for name, spec in TARGETS.items()]


def _issue(name: str, path: Path, reason: str, *, status: str = "fail") -> dict[str, str]:
    return {
        "target": name,
        "path": rel(path),
        "status": status,
        "reason": reason,
    }


def _validate_payload(
    *,
    name: str,
    path: Path,
    payload: dict[str, Any],
    expected_schema: str,
    generated_at_field: str,
    max_age_hours: float,
) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if expected_schema and payload.get("schema") != expected_schema:
        issues.append(_issue(name, path, f"schema mismatch: expected `{expected_schema}`, found `{payload.get('schema')}`"))
    meta = payload.get("report_meta")
    if not isinstance(meta, dict):
        issues.append(_issue(name, path, "missing report_meta"))
    else:
        if meta.get("canonical_format") != "json":
            issues.append(_issue(name, path, "report_meta.canonical_format must be `json`"))
        if meta.get("markdown_policy") != "leaf-only":
            issues.append(_issue(name, path, "report_meta.markdown_policy must be `leaf-only`"))
        if generated_at_field and meta.get("generated_at_field") != generated_at_field:
            issues.append(_issue(name, path, f"report_meta.generated_at_field must be `{generated_at_field}`"))
    field_name = generated_at_field or str((meta or {}).get("generated_at_field") or "")
    if not field_name:
        for candidate in ("generated_at_utc", "generated_at"):
            if isinstance(payload.get(candidate), str) and payload.get(candidate):
                field_name = candidate
                break
    if not field_name:
        issues.append(_issue(name, path, "no generated_at field declared"))
        return issues
    raw_timestamp = payload.get(field_name)
    if not isinstance(raw_timestamp, str) or not raw_timestamp:
        issues.append(_issue(name, path, f"missing `{field_name}` timestamp"))
        return issues
    try:
        generated_at = _parse_timestamp(raw_timestamp)
    except ValueError:
        issues.append(_issue(name, path, f"invalid `{field_name}` timestamp: `{raw_timestamp}`"))
        return issues
    age_hours = (datetime.now(UTC) - generated_at).total_seconds() / 3600.0
    if age_hours > max_age_hours:
        issues.append(_issue(name, path, f"stale report: age {age_hours:.1f}h exceeds limit {max_age_hours:.1f}h"))
    return issues


def audit(args: argparse.Namespace) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    rows: list[dict[str, Any]] = []
    issues: list[dict[str, str]] = []
    for spec in _target_rows(args):
        path = Path(str(spec["path"]))
        if not path.is_absolute():
            path = ROOT / path
        if not path.is_file():
            status = "skipped" if args.ignore_missing else "fail"
            reason = "missing report" if args.ignore_missing else "missing report"
            rows.append({"target": spec["name"], "path": rel(path), "status": status})
            if not args.ignore_missing:
                issues.append(_issue(str(spec["name"]), path, reason))
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            rows.append({"target": spec["name"], "path": rel(path), "status": "fail"})
            issues.append(_issue(str(spec["name"]), path, f"invalid json: {exc}"))
            continue
        row_issues = _validate_payload(
            name=str(spec["name"]),
            path=path,
            payload=payload,
            expected_schema=str(spec.get("schema") or ""),
            generated_at_field=str(spec.get("generated_at_field") or ""),
            max_age_hours=float(args.max_age_hours),
        )
        rows.append(
            {
                "target": spec["name"],
                "path": rel(path),
                "status": "pass" if not row_issues else "fail",
                "schema": payload.get("schema"),
                "generated_at_field": spec.get("generated_at_field") or (payload.get("report_meta") or {}).get("generated_at_field"),
            }
        )
        issues.extend(row_issues)
    return rows, issues


def render_markdown(rows: list[dict[str, Any]], issues: list[dict[str, str]], *, max_age_hours: float) -> str:
    lines = [
        "# JSON Report Freshness Audit",
        "",
        "- policy: `JSON is canonical; Markdown is leaf output only`",
        f"- generated_at_utc: `{utc_now()}`",
        f"- max_age_hours: `{max_age_hours}`",
        f"- issue_count: `{len(issues)}`",
        "",
        "## Targets",
        "",
    ]
    for row in rows:
        lines.append(f"- `{row['target']}` `{row['status']}`: `{row['path']}`")
    lines.extend(["", "## Issues", ""])
    if issues:
        for issue in issues:
            lines.append(f"- `{issue['target']}` `{issue['path']}`: {issue['reason']}")
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    rows, issues = audit(args)
    payload = {
        "schema": "fastdis.json_report_freshness_audit.v1",
        "generated_at_utc": utc_now(),
        "status": "pass" if not issues else "fail",
        "max_age_hours": float(args.max_age_hours),
        "rows": rows,
        "issues": issues,
    }
    if not args.no_write:
        write_json_report(
            REPORT_JSON,
            payload,
            schema="fastdis.json_report_freshness_audit.v1",
            producer="tools/check_json_report_freshness.py",
        )
        REPORT_MD.write_text(render_markdown(rows, issues, max_age_hours=float(args.max_age_hours)), encoding="utf-8")
        print(f"json: {REPORT_JSON}")
        print(f"md: {REPORT_MD}")
    if issues:
        for issue in issues:
            print(f"{issue['target']}: {issue['reason']}")
        return 1
    print("json report freshness audit: pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
