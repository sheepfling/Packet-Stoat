#!/usr/bin/env python3
"""Build a combined Phase 2 host-evidence summary from imported Unity and Alpha2 bundles."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

import evidence_layout
import load_local_env
import run_alpha2_signoff_matrix
import run_unity_host_matrix


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = ROOT / "artifacts" / "reports"
DEFAULT_UNITY_HOST_ROOT = evidence_layout.UNITY_HOSTS_DIR
DEFAULT_ALPHA2_HOST_ROOT = evidence_layout.ALPHA2_HOSTS_DIR


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--unity-host-root", type=Path, default=DEFAULT_UNITY_HOST_ROOT)
    parser.add_argument("--alpha2-host-root", type=Path, default=DEFAULT_ALPHA2_HOST_ROOT)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--alpha2-min-host-count", type=int, default=2)
    parser.add_argument(
        "--alpha2-required-unreal-version",
        dest="alpha2_required_unreal_versions",
        action="append",
        help="Unreal versions that an Alpha2 host must satisfy; repeat as needed",
    )
    return parser.parse_args(argv)


def display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_markdown(path: Path, markdown: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(markdown + "\n", encoding="utf-8")


def _unity_lane_row(report: dict[str, Any], host_root: Path, out_dir: Path) -> dict[str, Any]:
    hosts = report.get("hosts") if isinstance(report.get("hosts"), list) else []
    ready_platforms = report.get("ready_platforms") if isinstance(report.get("ready_platforms"), list) else []
    return {
        "lane": "unity",
        "status": report.get("overall_status", "no-host-reports"),
        "host_root": display_path(host_root),
        "json_report": display_path(out_dir / "unity_host_matrix.json"),
        "md_report": display_path(out_dir / "unity_host_matrix.md"),
        "host_count": len(hosts),
        "ready_count": len(ready_platforms),
        "ready_platforms": list(ready_platforms),
        "claim_boundary": (
            "Unity host bundles prove install/runtime/orientation/startup status across imported hosts. "
            "They do not by themselves prove GRILL head-to-head or same-host competitor parity."
        ),
    }


def _alpha2_lane_row(report: dict[str, Any], host_root: Path, out_dir: Path) -> dict[str, Any]:
    hosts = report.get("hosts") if isinstance(report.get("hosts"), list) else []
    ready_count = sum(1 for host in hosts if isinstance(host, dict) and host.get("host_ready") is True)
    required_versions = report.get("required_unreal_versions") if isinstance(report.get("required_unreal_versions"), list) else []
    return {
        "lane": "alpha2",
        "status": report.get("overall_status", "no-host-reports"),
        "host_root": display_path(host_root),
        "json_report": display_path(out_dir / "alpha2_signoff_matrix.json"),
        "md_report": display_path(out_dir / "alpha2_signoff_matrix.md"),
        "host_count": len(hosts),
        "ready_count": ready_count,
        "required_unreal_versions": list(required_versions),
        "claim_boundary": (
            "Alpha2 host bundles prove Unreal/Godot compatibility and proof lanes across imported hosts. "
            "They do not by themselves prove same-host GRILL parity or full Phase 2 completion."
        ),
    }


def _discover_alpha2_host_dirs(host_root: Path) -> list[Path]:
    if not host_root.is_dir():
        return []
    host_dirs: list[Path] = []
    for child in sorted(host_root.iterdir()):
        if child.is_dir() and (
            (child / run_alpha2_signoff_matrix.HOST_MANIFEST).exists()
            or run_alpha2_signoff_matrix.has_required_host_files(child)
        ):
            host_dirs.append(child.resolve())
    return host_dirs


def build_report(
    *,
    unity_host_root: Path,
    alpha2_host_root: Path,
    out_dir: Path,
    alpha2_min_host_count: int,
    alpha2_required_unreal_versions: list[str],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    unity_report = run_unity_host_matrix.build_report(unity_host_root)
    alpha2_report_dirs = _discover_alpha2_host_dirs(alpha2_host_root)
    alpha2_report = run_alpha2_signoff_matrix.build_report(
        report_dirs=alpha2_report_dirs,
        report_root=alpha2_host_root,
        min_host_count=alpha2_min_host_count,
        required_unreal_versions=alpha2_required_unreal_versions,
    )
    lanes = [
        _unity_lane_row(unity_report, unity_host_root, out_dir),
        _alpha2_lane_row(alpha2_report, alpha2_host_root, out_dir),
    ]
    host_rows: list[dict[str, Any]] = []
    for host in unity_report.get("hosts") if isinstance(unity_report.get("hosts"), list) else []:
        if not isinstance(host, dict):
            continue
        host_rows.append(
            {
                "lane": "unity",
                "host_label": host.get("host_label"),
                "platform": host.get("host_platform"),
                "status": "ready" if host.get("host_ready") is True else "not_ready",
                "host_ready": host.get("host_ready") is True,
                "report_dir": host.get("host_dir"),
            }
        )
    for host in alpha2_report.get("hosts") if isinstance(alpha2_report.get("hosts"), list) else []:
        if not isinstance(host, dict):
            continue
        host_rows.append(
            {
                "lane": "alpha2",
                "host_label": host.get("host_label"),
                "platform": host.get("platform"),
                "status": "ready" if host.get("host_ready") is True else "not_ready",
                "host_ready": host.get("host_ready") is True,
                "report_dir": host.get("report_dir"),
            }
        )
    summary = {
        "unity_status": lanes[0]["status"],
        "unity_host_count": lanes[0]["host_count"],
        "unity_ready_count": lanes[0]["ready_count"],
        "alpha2_status": lanes[1]["status"],
        "alpha2_host_count": lanes[1]["host_count"],
        "alpha2_ready_count": lanes[1]["ready_count"],
        "combined_host_count": len(host_rows),
        "combined_ready_count": sum(1 for row in host_rows if row["host_ready"]),
    }
    report = {
        "schema": "fastdis.phase2_host_evidence_summary.v1",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "sources": {
            "unity_host_root": display_path(unity_host_root),
            "alpha2_host_root": display_path(alpha2_host_root),
            "unity_host_matrix_json": display_path(out_dir / "unity_host_matrix.json"),
            "alpha2_signoff_matrix_json": display_path(out_dir / "alpha2_signoff_matrix.json"),
        },
        "summary": summary,
        "lanes": lanes,
        "hosts": host_rows,
        "claim_boundaries": [
            "This summary aggregates imported host bundles. It is a portability/status artifact, not a same-host benchmark or GRILL head-to-head proof artifact.",
            "Use the benchmark matrix and engine head-to-head reports for direct performance or competitor claims.",
        ],
    }
    return unity_report, alpha2_report, report


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Phase 2 Host Evidence Summary",
        "",
        f"- schema: `{report['schema']}`",
        f"- unity_status: `{report['summary']['unity_status']}`",
        f"- unity_host_count: `{report['summary']['unity_host_count']}`",
        f"- alpha2_status: `{report['summary']['alpha2_status']}`",
        f"- alpha2_host_count: `{report['summary']['alpha2_host_count']}`",
        f"- combined_ready_count: `{report['summary']['combined_ready_count']}`",
        "",
        "## Lanes",
        "",
        "| lane | status | host_count | ready_count | report |",
        "| --- | --- | --- | --- | --- |",
    ]
    for lane in report["lanes"]:
        lines.append(
            f"| {lane['lane']} | {lane['status']} | {lane['host_count']} | {lane['ready_count']} | {lane['json_report']} |"
        )
    lines.extend(["", "## Hosts", "", "| lane | host_label | platform | status | report_dir |", "| --- | --- | --- | --- | --- |"])
    if report["hosts"]:
        for host in report["hosts"]:
            lines.append(
                f"| {host['lane']} | {host['host_label']} | {host['platform']} | {host['status']} | {host['report_dir']} |"
            )
    else:
        lines.append("| none | none | none | none | none |")
    lines.extend(["", "## Claim Boundaries", ""])
    for boundary in report["claim_boundaries"]:
        lines.append(f"- {boundary}")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    load_local_env.load()
    args = parse_args(argv)
    out_dir = args.out_dir.expanduser().resolve()
    unity_host_root = args.unity_host_root.expanduser().resolve()
    alpha2_host_root = args.alpha2_host_root.expanduser().resolve()
    alpha2_required = args.alpha2_required_unreal_versions or list(run_alpha2_signoff_matrix.DEFAULT_REQUIRED_UNREAL_VERSIONS)
    unity_report, alpha2_report, report = build_report(
        unity_host_root=unity_host_root,
        alpha2_host_root=alpha2_host_root,
        out_dir=out_dir,
        alpha2_min_host_count=args.alpha2_min_host_count,
        alpha2_required_unreal_versions=alpha2_required,
    )
    write_json(out_dir / "unity_host_matrix.json", unity_report)
    write_markdown(out_dir / "unity_host_matrix.md", run_unity_host_matrix.render_markdown(unity_report))
    write_json(out_dir / "alpha2_signoff_matrix.json", alpha2_report)
    write_markdown(out_dir / "alpha2_signoff_matrix.md", run_alpha2_signoff_matrix.render_markdown(alpha2_report))
    write_json(out_dir / "phase2_host_evidence_summary.json", report)
    write_markdown(out_dir / "phase2_host_evidence_summary.md", render_markdown(report))
    print(f"json: {display_path(out_dir / 'unity_host_matrix.json')}")
    print(f"md: {display_path(out_dir / 'unity_host_matrix.md')}")
    print(f"json: {display_path(out_dir / 'alpha2_signoff_matrix.json')}")
    print(f"md: {display_path(out_dir / 'alpha2_signoff_matrix.md')}")
    print(f"json: {display_path(out_dir / 'phase2_host_evidence_summary.json')}")
    print(f"md: {display_path(out_dir / 'phase2_host_evidence_summary.md')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
