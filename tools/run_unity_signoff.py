#!/usr/bin/env python3
"""Generate a machine-readable Unity Phase 1 signoff summary."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path

import evidence_layout
import load_local_env
import run_unity_host_matrix


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT_DIR = ROOT / "artifacts" / "reports"
DEFAULT_HOST_ROOT = evidence_layout.UNITY_HOSTS_DIR


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR), help="Directory containing Unity workflow/install reports")
    parser.add_argument("--host-root", default=str(DEFAULT_HOST_ROOT), help="Root directory containing staged Unity host bundles")
    parser.add_argument("--out-dir", default=str(DEFAULT_REPORT_DIR), help="Directory for JSON/Markdown reports")
    return parser.parse_args(argv)


def _read_json(path: Path) -> dict[str, object] | None:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _criterion_status(runtime_report: dict[str, object] | None, name: str) -> str:
    if not runtime_report:
        return "missing"
    criteria = runtime_report.get("phase1_exit_criteria")
    if not isinstance(criteria, list):
        return "missing"
    for item in criteria:
        if isinstance(item, dict) and item.get("name") == name:
            status = item.get("status")
            if isinstance(status, str):
                return status
    return "missing"


def evaluate(report_dir: Path, host_root: Path) -> dict[str, object]:
    workflow = _read_json(report_dir / "unity_workflow_report.json")
    runtime_report = _read_json(report_dir / "unity_runtime_verification.json")
    install_matrix = _read_json(report_dir / "unity_install_matrix.json")
    host_matrix = run_unity_host_matrix.build_report(host_root)

    criteria = [
        {
            "name": "Git/UPM install works on macOS",
            "status": "complete" if workflow and workflow.get("unity_install_status") == "pass" else "incomplete",
            "evidence": [
                str(report_dir / "unity_install_smoke.json"),
                str(report_dir / "unity_workflow_report.json"),
            ],
            "note": "Requires the local macOS Unity install-smoke lane to pass; cross-host install matrices are optional follow-on evidence, not a blocker for the macOS exit.",
        },
        {
            "name": "Native library stages and loads in Unity",
            "status": "complete"
            if _criterion_status(runtime_report, "Native library stages and loads in Unity") == "complete"
            or (workflow and workflow.get("unity_native_status") == "pass")
            else "incomplete",
            "evidence": [
                str(report_dir / "unity_runtime_verification.json"),
                str(report_dir / "unity_workflow_report.json"),
                str(report_dir / "unity_install_smoke.json"),
            ],
            "note": "Host workflow report must show native staging/load success.",
        },
        {
            "name": "Replay demo moves GameObjects",
            "status": "complete"
            if _criterion_status(runtime_report, "Replay demo moves GameObjects") == "complete"
            else "incomplete",
            "evidence": [
                str(report_dir / "unity_runtime_verification.json"),
                str(report_dir / "unity_workflow_report.json"),
            ],
            "note": "Runtime verification covers replay/player state application on the current host.",
        },
        {
            "name": "UDP demo receives live Entity State traffic",
            "status": "complete"
            if _criterion_status(runtime_report, "UDP demo receives live Entity State traffic") == "complete"
            else "incomplete",
            "evidence": [
                str(report_dir / "unity_runtime_verification.json"),
                str(report_dir / "unity_workflow_report.json"),
            ],
            "note": "Runtime verification covers receiver injection/live ingress on the current host.",
        },
        {
            "name": "Orientation verification scene passes",
            "status": "complete" if workflow and workflow.get("unity_orientation_status") == "pass" else "incomplete",
            "evidence": [
                str(report_dir / "unity_orientation_verification.json"),
                str(report_dir / "unity_workflow_report.json"),
            ],
            "note": "Orientation example scene must pass on the current host.",
        },
        {
            "name": "Runtime verification report is generated and human-readable",
            "status": "complete" if (report_dir / "unity_runtime_verification.json").is_file() and (report_dir / "unity_runtime_verification.md").is_file() else "incomplete",
            "evidence": [
                str(report_dir / "unity_runtime_verification.json"),
                str(report_dir / "unity_runtime_verification.md"),
            ],
            "note": "Both JSON and Markdown runtime verification receipts must exist.",
        },
    ]

    overall_status = "ready" if all(item["status"] == "complete" for item in criteria) else "not-fully-signed-off"
    return {
        "schema": "fastdis.unity_signoff.v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "overall_status": overall_status,
        "report_dir": str(report_dir),
        "host_root": str(host_root),
        "workflow_status": workflow.get("unity_workflow_status") if workflow else "missing",
        "install_matrix_status": install_matrix.get("overall_status") if install_matrix else "missing",
        "host_matrix_status": host_matrix.get("overall_status", "missing"),
        "criteria": criteria,
    }


def render_markdown(report: dict[str, object]) -> str:
    lines = [
        "# Unity Phase 1 Signoff",
        "",
        f"- generated_at: `{report['generated_at']}`",
        f"- overall_status: `{report['overall_status']}`",
        f"- workflow_status: `{report['workflow_status']}`",
        f"- install_matrix_status: `{report['install_matrix_status']}`",
        f"- host_matrix_status: `{report['host_matrix_status']}`",
        "",
        "| Criterion | Status | Note |",
        "| --- | --- | --- |",
    ]
    for item in report["criteria"]:
        lines.append(f"| {item['name']} | `{item['status']}` | {item['note']} |")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    load_local_env.load()
    args = parse_args(argv)
    report_dir = Path(args.report_dir).expanduser().resolve()
    host_root = Path(args.host_root).expanduser().resolve()
    out_dir = Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    report = evaluate(report_dir, host_root)
    json_path = out_dir / "unity_signoff_report.json"
    md_path = out_dir / "unity_signoff_report.md"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    print(f"JSON: {json_path}")
    print(f"Markdown: {md_path}")
    return 0 if report["overall_status"] == "ready" else 2


if __name__ == "__main__":
    raise SystemExit(main())
