#!/usr/bin/env python3
"""Aggregate Alpha 2 engine proof reports across one or more host report sets."""

from __future__ import annotations

import argparse
from datetime import UTC
from datetime import datetime
import json
from pathlib import Path

import load_local_env


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = ROOT / "verification_reports" / "alpha2_sample"
DEFAULT_REPORT_DIR = ROOT / "verification_reports" / "alpha2_sample"
DEFAULT_REQUIRED_UNREAL_VERSIONS = ("5.7", "5.8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--report-dir",
        dest="report_dirs",
        action="append",
        help="Directory containing one host's Alpha 2 JSON proof artifacts; repeat for multiple hosts",
    )
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR), help="Directory for JSON/Markdown reports")
    parser.add_argument("--min-host-count", type=int, default=2, help="Host count needed before cross-host signoff can be considered")
    parser.add_argument(
        "--required-unreal-version",
        dest="required_unreal_versions",
        action="append",
        help="Unreal versions that must pass for a host to count toward engine signoff; repeat as needed",
    )
    return parser.parse_args()


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def load_host_report(report_dir: Path) -> dict[str, object]:
    return {
        "report_dir": str(report_dir),
        "unreal_matrix": load_json(report_dir / "unreal_version_matrix.json"),
        "godot_workflow": load_json(report_dir / "godot_workflow_report.json"),
        "orientation_runtime": load_json(report_dir / "orientation_runtime_report.json"),
        "orientation_visual": load_json(report_dir / "orientation_visual_report.json"),
        "host_compat": load_json(report_dir / "unreal_host_compat_report.json"),
        "release_audit": load_json(report_dir / "alpha2_release_audit_report.json"),
    }


def summarize_host(host: dict[str, object], required_unreal_versions: list[str]) -> dict[str, object]:
    unreal_matrix = host["unreal_matrix"]
    godot_workflow = host["godot_workflow"]
    runtime = host["orientation_runtime"]
    visual = host["orientation_visual"]
    compat = host["host_compat"]

    matrix_results = {item["version"]: item for item in unreal_matrix["results"]}
    unreal_matrix_ok = all(
        version in matrix_results
        and matrix_results[version]["plugin_build"]["status"] == "passed"
        and matrix_results[version]["orientation"]["status"] == "passed"
        and matrix_results[version]["demo"]["status"] == "passed"
        for version in required_unreal_versions
    )
    godot_ok = all(lane["status"] == "passed" for lane in godot_workflow["lanes"].values())
    runtime_unreal = runtime["lanes"]["unreal"]
    runtime_ok = all(runtime_unreal[version]["status"] == "passed" for version in required_unreal_versions) and runtime["lanes"]["godot"]["status"] == "passed"
    visual_unreal = visual["lanes"]["unreal"]
    visual_ok = all(visual_unreal[version]["status"] == "passed" for version in required_unreal_versions) and visual["lanes"]["godot"]["status"] == "passed"

    compat_lanes = {item["version"]: item for item in compat["lanes"]}
    compat_ok = all(compat_lanes[version]["probe"]["status"] == "ok" for version in required_unreal_versions if version in compat_lanes)

    host_ready = unreal_matrix_ok and godot_ok and runtime_ok and visual_ok and compat_ok
    return {
        "report_dir": host["report_dir"],
        "required_unreal_versions": required_unreal_versions,
        "unreal_matrix_ok": unreal_matrix_ok,
        "godot_workflow_ok": godot_ok,
        "orientation_runtime_ok": runtime_ok,
        "orientation_visual_ok": visual_ok,
        "unreal_host_compat_ok": compat_ok,
        "host_ready": host_ready,
        "release_audit_status": host["release_audit"]["overall_status"],
    }


def overall_status(host_summaries: list[dict[str, object]], min_host_count: int) -> str:
    ready_hosts = sum(1 for item in host_summaries if item["host_ready"])
    if not host_summaries:
        return "no-host-reports"
    if len(host_summaries) < min_host_count:
        return "host-sample-only"
    if ready_hosts < min_host_count:
        return "cross-host-partial"
    return "cross-host-ready"


def render_markdown(report: dict[str, object]) -> str:
    lines = [
        "# Alpha 2 Signoff Matrix",
        "",
        f"- generated_at: `{report['generated_at']}`",
        f"- overall_status: `{report['overall_status']}`",
        f"- min_host_count: `{report['min_host_count']}`",
        f"- required_unreal_versions: `{', '.join(report['required_unreal_versions'])}`",
        "",
        "| Host Report Dir | Unreal Matrix | Godot Workflow | Runtime | Visual | Host Compat | Host Ready |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for host in report["hosts"]:
        lines.append(
            f"| {host['report_dir']} | {'yes' if host['unreal_matrix_ok'] else 'no'} | "
            f"{'yes' if host['godot_workflow_ok'] else 'no'} | {'yes' if host['orientation_runtime_ok'] else 'no'} | "
            f"{'yes' if host['orientation_visual_ok'] else 'no'} | {'yes' if host['unreal_host_compat_ok'] else 'no'} | "
            f"{'yes' if host['host_ready'] else 'no'} |"
        )
    lines.extend(["", "## Interpretation", ""])
    if report["overall_status"] == "host-sample-only":
        lines.append("- Only one host report set is present. Alpha 2 engine proof remains host-sample, not cross-host signoff.")
    elif report["overall_status"] == "cross-host-partial":
        lines.append("- Multiple host report sets are present, but not enough hosts satisfy the required Unreal/Godot proof gates yet.")
    elif report["overall_status"] == "cross-host-ready":
        lines.append("- The required number of hosts satisfy the configured Unreal/Godot proof gates.")
    else:
        lines.append("- No usable host report sets were provided.")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    load_local_env.load()
    args = parse_args()
    report_dirs = [Path(path).expanduser().resolve() for path in (args.report_dirs or [DEFAULT_REPORT_DIR])]
    required_unreal_versions = args.required_unreal_versions or list(DEFAULT_REQUIRED_UNREAL_VERSIONS)
    out_dir = Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    hosts = [summarize_host(load_host_report(report_dir), required_unreal_versions) for report_dir in report_dirs]
    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "overall_status": overall_status(hosts, args.min_host_count),
        "min_host_count": args.min_host_count,
        "required_unreal_versions": required_unreal_versions,
        "hosts": hosts,
    }

    json_path = out_dir / "alpha2_signoff_matrix.json"
    md_path = out_dir / "alpha2_signoff_matrix.md"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    print(f"Wrote {display_path(json_path)}")
    print(f"Wrote {display_path(md_path)}")
    return 0 if report["overall_status"] == "cross-host-ready" else 2


if __name__ == "__main__":
    raise SystemExit(main())
