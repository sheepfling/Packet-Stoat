#!/usr/bin/env python3
"""Summarize the current Unity-vs-GRILL baseline readiness state."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FASTDIS = ROOT / "artifacts" / "reports" / "engine_benchmarks" / "unity_engine_benchmark_report.json"
DEFAULT_HEAD_TO_HEAD = ROOT / "artifacts" / "reports" / "engine_head_to_head" / "unity_vs_grill.json"
DEFAULT_IMPORT_SMOKE = ROOT / "verification_reports" / "unity_grill_baseline" / "grill_unity_import_smoke.json"
DEFAULT_OUT_DIR = ROOT / "artifacts" / "reports" / "engine_head_to_head"
DEFAULT_GRILL_CANDIDATES = [
    ROOT / "artifacts" / "reports" / "engine_benchmarks" / "grill_unity_engine_benchmark_report.json",
    ROOT / "verification_reports" / "unity_grill_baseline" / "grill_unity_benchmark_baseline.json",
    ROOT / "verification_reports" / "unity_grill_baseline" / "grill_unity_benchmark_baseline.template.json",
]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fastdis", type=Path, default=DEFAULT_FASTDIS)
    parser.add_argument("--head-to-head", type=Path, default=DEFAULT_HEAD_TO_HEAD)
    parser.add_argument("--import-smoke", type=Path, default=DEFAULT_IMPORT_SMOKE)
    parser.add_argument("--grill-report", dest="grill_reports", type=Path, action="append", help="Candidate GRILL Unity report path")
    parser.add_argument("--json-out", type=Path, default=DEFAULT_OUT_DIR / "unity_vs_grill_status.json")
    parser.add_argument("--md-out", type=Path, default=DEFAULT_OUT_DIR / "unity_vs_grill_status.md")
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


def classify_path(path: Path) -> str:
    if "/samples/" in path.as_posix() or ".sample." in path.name:
        return "sample"
    if path.name.endswith(".template.json"):
        return "template"
    return "current"


def build_report(
    fastdis_path: Path,
    *,
    head_to_head_path: Path,
    import_smoke_path: Path,
    grill_candidates: list[Path],
) -> dict[str, Any]:
    fastdis_exists = fastdis_path.exists()
    fastdis_payload = load_json(fastdis_path) if fastdis_exists else None
    head_to_head_payload = load_json(head_to_head_path)
    import_smoke_payload = load_json(import_smoke_path)

    grill_present = []
    for candidate in grill_candidates:
        if candidate.exists():
            grill_present.append(
                {
                    "path": display_path(candidate),
                    "classification": classify_path(candidate),
                }
            )

    blockers: list[str] = []
    if not fastdis_exists:
        blockers.append("current FastDIS Unity shared report missing")
    if not any(row["classification"] == "current" for row in grill_present):
        blockers.append("no current GRILL Unity shared benchmark report present")

    import_smoke_status = import_smoke_payload.get("status") if isinstance(import_smoke_payload, dict) else None
    import_smoke_failure_stage = import_smoke_payload.get("failure_stage") if isinstance(import_smoke_payload, dict) else None
    if import_smoke_status in {"blocked-host-startup"} or import_smoke_failure_stage == "host-startup":
        blockers.append("current host Unity startup baseline failed before GRILL import could be tested")
    elif import_smoke_status in {"fail", "failed"}:
        blockers.append("current host GRILL Unity import smoke failed")

    status = "ready" if not blockers else "blocked_on_grill_baseline"
    note = (
        "A real Unity-vs-GRILL same-host head-to-head report requires a current GRILL Unity shared benchmark report and a GRILL-compatible host."
        if blockers
        else "Both sides have current shared benchmark reports and the current host can proceed to direct comparison work."
    )

    next_steps = [
        (
            "Fix the current host Unity startup route or switch to a Unity host/editor combination "
            "that can import a blank scratch project and the public GRILL route."
            if import_smoke_failure_stage == "host-startup" or import_smoke_status == "blocked-host-startup"
            else "Capture a current GRILL Unity shared benchmark report on a GRILL-compatible Unity host."
        ),
        "Rerun the shared head-to-head comparator with current FastDIS and GRILL Unity reports.",
    ]
    if not blockers:
        comparison_status = head_to_head_payload.get("status") if isinstance(head_to_head_payload, dict) else None
        next_steps = [
            "Align the FastDIS Unity shared benchmark report with the canonical GRILL scenario set so the direct comparator has at least one matched scenario.",
            "Publish same-host comparable Unity metrics for the matched canonical scenario rows and rerun the shared head-to-head comparator.",
        ]
        if comparison_status == "comparable":
            next_steps = [
                "Review the direct Unity-vs-GRILL comparison outputs and decide which proof-backed claims are publishable.",
            ]

    return {
        "schema": "fastdis.unity_grill_baseline_status.v1",
        "generated_at_utc": utc_now(),
        "status": status,
        "note": note,
        "fastdis": {
            "path": display_path(fastdis_path),
            "exists": fastdis_exists,
            "surface": fastdis_payload.get("surface") if isinstance(fastdis_payload, dict) else None,
            "evidence_kind": classify_path(fastdis_path) if fastdis_exists else None,
        },
        "head_to_head_readiness": {
            "path": display_path(head_to_head_path),
            "status": head_to_head_payload.get("status") if isinstance(head_to_head_payload, dict) else None,
            "note": head_to_head_payload.get("note") if isinstance(head_to_head_payload, dict) else None,
        },
        "import_smoke": {
            "path": display_path(import_smoke_path),
            "status": import_smoke_status,
            "failure_stage": import_smoke_failure_stage,
        },
        "grill_candidates": grill_present,
        "blockers": blockers,
        "next_steps": next_steps,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Unity vs GRILL Baseline Status",
        "",
        f"- status: `{report['status']}`",
        "",
        report["note"],
        "",
        "## FastDIS",
        "",
        f"- path: `{report['fastdis']['path']}`",
        f"- exists: `{report['fastdis']['exists']}`",
        f"- surface: `{report['fastdis']['surface']}`",
        "",
        "## Head-to-Head Readiness",
        "",
        f"- path: `{report['head_to_head_readiness']['path']}`",
        f"- status: `{report['head_to_head_readiness']['status']}`",
        "",
        "## Import Smoke",
        "",
        f"- path: `{report['import_smoke']['path']}`",
        f"- status: `{report['import_smoke']['status']}`",
        f"- failure_stage: `{report['import_smoke'].get('failure_stage')}`",
        "",
        "## GRILL Candidates",
        "",
    ]
    if report["grill_candidates"]:
        for row in report["grill_candidates"]:
            lines.append(f"- `{row['path']}` classification=`{row['classification']}`")
    else:
        lines.append("- none")
    lines.extend(["", "## Blockers", ""])
    if report["blockers"]:
        for blocker in report["blockers"]:
            lines.append(f"- {blocker}")
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    grill_candidates = args.grill_reports or DEFAULT_GRILL_CANDIDATES
    report = build_report(
        args.fastdis,
        head_to_head_path=args.head_to_head,
        import_smoke_path=args.import_smoke,
        grill_candidates=grill_candidates,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.md_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    args.md_out.write_text(render_markdown(report) + "\n", encoding="utf-8")
    print(f"json: {display_path(args.json_out)}")
    print(f"md: {display_path(args.md_out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
