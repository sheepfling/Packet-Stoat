#!/usr/bin/env python3
"""Compare two shared engine benchmark reports and emit a head-to-head report."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = ROOT / "artifacts" / "reports" / "engine_head_to_head"

HIGHER_IS_BETTER = {"packets_per_sec"}
LOWER_IS_BETTER = {
    "p50_ingest_ms",
    "p95_ingest_ms",
    "p99_ingest_ms",
    "steady_state_gc_bytes",
    "main_thread_apply_ms",
    "socket_drops",
    "queue_drops",
    "malformed",
}
DIRECT_MATCH = {
    "packets_received",
    "packets_parsed",
    "packets_accepted",
    "packets_rejected",
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--left", type=Path, required=True)
    parser.add_argument("--right", type=Path, required=True)
    parser.add_argument("--left-label")
    parser.add_argument("--right-label")
    parser.add_argument("--json-out", type=Path, default=DEFAULT_OUT_DIR / "engine_head_to_head.json")
    parser.add_argument("--md-out", type=Path, default=DEFAULT_OUT_DIR / "engine_head_to_head.md")
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


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def validate_report(payload: dict[str, Any] | None, side: str) -> list[str]:
    if payload is None:
        return [f"{side}: missing payload"]
    errors: list[str] = []
    if payload.get("schema") != "fastdis.engine_benchmark_report.v1":
        errors.append(f"{side}: schema must equal fastdis.engine_benchmark_report.v1")
    for field in ("surface", "surface_kind", "generated_at_utc", "rows"):
        if field not in payload:
            errors.append(f"{side}: missing top-level field `{field}`")
    rows = payload.get("rows")
    if not isinstance(rows, list) or not rows:
        errors.append(f"{side}: `rows` must be a non-empty array")
        return errors
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            errors.append(f"{side}: rows[{index}] must be an object")
            continue
        if not isinstance(row.get("scenario"), str) or not row["scenario"]:
            errors.append(f"{side}: rows[{index}].scenario must be a populated string")
        metrics = row.get("metrics")
        truth = row.get("truth")
        if not isinstance(metrics, dict):
            errors.append(f"{side}: rows[{index}].metrics must be an object")
        if not isinstance(truth, dict):
            errors.append(f"{side}: rows[{index}].truth must be an object")
    return errors


def host_fingerprint(payload: dict[str, Any]) -> dict[str, Any]:
    host = payload.get("host")
    if not isinstance(host, dict):
        return {}
    return {key: host.get(key) for key in ("system", "release", "machine")}


def hosts_comparable(left: dict[str, Any], right: dict[str, Any]) -> bool:
    left_fp = host_fingerprint(left)
    right_fp = host_fingerprint(right)
    if not left_fp or not right_fp:
        return False
    return left_fp == right_fp


def _ratio(left_value: Any, right_value: Any, *, higher_is_better: bool) -> float | None:
    if not _is_number(left_value) or not _is_number(right_value):
        return None
    left_num = float(left_value)
    right_num = float(right_value)
    if left_num <= 0 or right_num <= 0:
        return None
    return (left_num / right_num) if higher_is_better else (right_num / left_num)


def _metric_compare(metric: str, left_value: Any, right_value: Any) -> dict[str, Any]:
    comparison: dict[str, Any] = {
        "left": left_value,
        "right": right_value,
        "comparable": False,
        "comparison_kind": "unavailable",
    }
    if metric in HIGHER_IS_BETTER:
        comparison["comparison_kind"] = "higher_is_better_ratio"
        comparison["ratio"] = _ratio(left_value, right_value, higher_is_better=True)
        comparison["comparable"] = comparison["ratio"] is not None
        return comparison
    if metric in LOWER_IS_BETTER:
        comparison["comparison_kind"] = "lower_is_better_ratio"
        comparison["ratio"] = _ratio(left_value, right_value, higher_is_better=False)
        comparison["comparable"] = comparison["ratio"] is not None
        return comparison
    if metric in DIRECT_MATCH:
        comparison["comparison_kind"] = "direct_match"
        comparison["equal"] = left_value == right_value and left_value is not None and right_value is not None
        comparison["comparable"] = left_value is not None and right_value is not None
        return comparison
    return comparison


def build_comparison(left: dict[str, Any], right: dict[str, Any], *, left_label: str, right_label: str) -> dict[str, Any]:
    left_rows = {
        str(row["scenario"]): row
        for row in left.get("rows", [])
        if isinstance(row, dict) and isinstance(row.get("scenario"), str)
    }
    right_rows = {
        str(row["scenario"]): row
        for row in right.get("rows", [])
        if isinstance(row, dict) and isinstance(row.get("scenario"), str)
    }
    shared = sorted(set(left_rows) & set(right_rows))
    left_only = sorted(set(left_rows) - set(right_rows))
    right_only = sorted(set(right_rows) - set(left_rows))

    rows: list[dict[str, Any]] = []
    comparable_metric_rows = 0
    metrics_to_compare = sorted(HIGHER_IS_BETTER | LOWER_IS_BETTER | DIRECT_MATCH)
    for scenario in shared:
        left_row = left_rows[scenario]
        right_row = right_rows[scenario]
        left_metrics = left_row.get("metrics") if isinstance(left_row.get("metrics"), dict) else {}
        right_metrics = right_row.get("metrics") if isinstance(right_row.get("metrics"), dict) else {}
        metric_rows = {
            metric: _metric_compare(metric, left_metrics.get(metric), right_metrics.get(metric))
            for metric in metrics_to_compare
        }
        if any(details["comparable"] for details in metric_rows.values()):
            comparable_metric_rows += 1
        rows.append(
            {
                "scenario": scenario,
                "left_truth_match": (left_row.get("truth") or {}).get("final_truth_match"),
                "right_truth_match": (right_row.get("truth") or {}).get("final_truth_match"),
                "metrics": metric_rows,
            }
        )

    claim_boundaries = [
        "Direct competitor claims require same-host evidence and matched scenario names.",
        "Rows without measured comparable metrics remain directional only, even when scenario names match.",
        "Missing or null metrics are rendered explicitly and do not count as a win or loss.",
    ]
    same_host = hosts_comparable(left, right)
    status = "comparable" if same_host and rows and comparable_metric_rows > 0 else "directional_only"
    if not rows:
        status = "incomplete"

    return {
        "status": status,
        "claim_boundaries": claim_boundaries,
        "same_host": same_host,
        "left_label": left_label,
        "right_label": right_label,
        "matched_scenarios": len(rows),
        "left_only_scenarios": left_only,
        "right_only_scenarios": right_only,
        "comparable_metric_rows": comparable_metric_rows,
        "rows": rows,
    }


def build_report(left: dict[str, Any], right: dict[str, Any], *, left_path: Path, right_path: Path, left_label: str, right_label: str) -> dict[str, Any]:
    validation_errors = validate_report(left, "left") + validate_report(right, "right")
    comparison = build_comparison(left, right, left_label=left_label, right_label=right_label) if not validation_errors else {
        "status": "invalid",
        "claim_boundaries": [
            "Invalid inputs are not comparable.",
        ],
        "same_host": False,
        "left_label": left_label,
        "right_label": right_label,
        "matched_scenarios": 0,
        "left_only_scenarios": [],
        "right_only_scenarios": [],
        "comparable_metric_rows": 0,
        "rows": [],
    }
    return {
        "schema": "fastdis.engine_head_to_head_report.v1",
        "generated_at_utc": utc_now(),
        "status": comparison["status"],
        "inputs": {
            "left": display_path(left_path),
            "right": display_path(right_path),
            "left_surface": left.get("surface"),
            "right_surface": right.get("surface"),
            "left_host": host_fingerprint(left),
            "right_host": host_fingerprint(right),
            "left_proof_context": left.get("proof_context") if isinstance(left.get("proof_context"), dict) else None,
            "right_proof_context": right.get("proof_context") if isinstance(right.get("proof_context"), dict) else None,
        },
        "validation_errors": validation_errors,
        "comparison": comparison,
    }


def render_markdown(report: dict[str, Any]) -> str:
    comparison = report["comparison"]
    lines = [
        "# Engine Head-to-Head Report",
        "",
        f"- status: `{report['status']}`",
        f"- left: `{report['inputs']['left']}`",
        f"- right: `{report['inputs']['right']}`",
        f"- same_host: `{comparison['same_host']}`",
        f"- matched_scenarios: `{comparison['matched_scenarios']}`",
        f"- comparable_metric_rows: `{comparison['comparable_metric_rows']}`",
        "",
        "## Claim Boundaries",
        "",
    ]
    for note in comparison["claim_boundaries"]:
        lines.append(f"- {note}")
    lines.extend(["", "## Validation", ""])
    if report["validation_errors"]:
        for error in report["validation_errors"]:
            lines.append(f"- `{error}`")
    else:
        lines.append("- `inputs valid`")
    lines.extend(
        [
            "",
            "## Scenario Coverage",
            "",
            f"- left_only: `{comparison['left_only_scenarios']}`",
            f"- right_only: `{comparison['right_only_scenarios']}`",
            "",
            "| scenario | truth(left/right) | packets/sec ratio | p95 ratio | main-thread ratio | packets accepted equal |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in comparison["rows"]:
        metrics = row["metrics"]
        packets_ratio = metrics["packets_per_sec"].get("ratio")
        p95_ratio = metrics["p95_ingest_ms"].get("ratio")
        main_thread_ratio = metrics["main_thread_apply_ms"].get("ratio")
        packets_accepted_equal = metrics["packets_accepted"].get("equal")
        lines.append(
            f"| {row['scenario']} | {row['left_truth_match']}/{row['right_truth_match']} | {packets_ratio} | {p95_ratio} | {main_thread_ratio} | {packets_accepted_equal} |"
        )
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    left = load_json(args.left)
    right = load_json(args.right)
    left_label = args.left_label or str(left.get("surface") or "left")
    right_label = args.right_label or str(right.get("surface") or "right")
    report = build_report(left, right, left_path=args.left, right_path=args.right, left_label=left_label, right_label=right_label)

    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.md_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    args.md_out.write_text(render_markdown(report) + "\n", encoding="utf-8")
    print(f"json: {display_path(args.json_out)}")
    print(f"md: {display_path(args.md_out)}")
    return 0 if not report["validation_errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
