#!/usr/bin/env python3
"""Aggregate Alpha 2 engine proof reports across one or more host report sets."""

from __future__ import annotations

import argparse
from datetime import UTC
from datetime import datetime
import json
from pathlib import Path
from typing import Any

import load_local_env


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = ROOT / "verification_reports" / "alpha2_sample"
DEFAULT_REPORT_DIR = ROOT / "verification_reports" / "alpha2_sample"
DEFAULT_REPORT_ROOT = ROOT / "verification_reports" / "alpha2_hosts"
DEFAULT_REQUIRED_UNREAL_VERSIONS = ("5.7", "5.8")
HOST_MANIFEST = "host_report_manifest.json"
REQUIRED_HOST_FILES = (
    "unreal_version_matrix.json",
    "godot_workflow_report.json",
    "orientation_runtime_report.json",
    "orientation_visual_report.json",
    "unreal_host_compat_report.json",
    "alpha2_release_audit_report.json",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--report-dir",
        dest="report_dirs",
        action="append",
        help="Directory containing one host's Alpha 2 JSON proof artifacts; repeat for multiple hosts",
    )
    parser.add_argument(
        "--report-root",
        default=str(DEFAULT_REPORT_ROOT),
        help="Root directory containing staged host report subdirectories",
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


def has_required_host_files(report_dir: Path) -> bool:
    return all((report_dir / name).exists() for name in REQUIRED_HOST_FILES)


def discover_report_dirs(explicit_report_dirs: list[str] | None, report_root: Path) -> list[Path]:
    if explicit_report_dirs:
        return [Path(path).expanduser().resolve() for path in explicit_report_dirs]
    if report_root.exists():
        discovered = []
        for child in sorted(report_root.iterdir()):
            if child.is_dir() and ((child / HOST_MANIFEST).exists() or has_required_host_files(child)):
                discovered.append(child.resolve())
        if discovered:
            return discovered
    return [DEFAULT_REPORT_DIR]


def load_host_manifest(report_dir: Path) -> dict[str, Any]:
    manifest_path = report_dir / HOST_MANIFEST
    if manifest_path.exists():
        return json.loads(manifest_path.read_text(encoding="utf-8"))
    return {
        "host_label": report_dir.name,
        "hostname": report_dir.name,
        "platform": "unknown",
        "host_fingerprint": "",
        "report_digest_sha256": "",
        "source_report_dir": str(report_dir),
    }


def load_host_report(report_dir: Path) -> dict[str, object]:
    manifest = load_host_manifest(report_dir)
    return {
        "report_dir": str(report_dir),
        "host_label": manifest.get("host_label", report_dir.name),
        "hostname": manifest.get("hostname", report_dir.name),
        "platform": manifest.get("platform", "unknown"),
        "host_fingerprint": manifest.get("host_fingerprint", ""),
        "report_digest_sha256": manifest.get("report_digest_sha256", ""),
        "manifest": manifest,
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
        "host_label": host["host_label"],
        "hostname": host["hostname"],
        "platform": host["platform"],
        "host_fingerprint": host["host_fingerprint"],
        "report_digest_sha256": host["report_digest_sha256"],
        "required_unreal_versions": required_unreal_versions,
        "unreal_matrix_ok": unreal_matrix_ok,
        "godot_workflow_ok": godot_ok,
        "orientation_runtime_ok": runtime_ok,
        "orientation_visual_ok": visual_ok,
        "unreal_host_compat_ok": compat_ok,
        "identity_unique": True,
        "report_unique": True,
        "host_ready": host_ready,
        "release_audit_status": host["release_audit"]["overall_status"],
    }


def apply_duplicate_detection(host_summaries: list[dict[str, object]]) -> None:
    fingerprint_counts: dict[str, int] = {}
    report_digest_counts: dict[str, int] = {}
    for host in host_summaries:
        fingerprint = str(host.get("host_fingerprint") or "")
        report_digest = str(host.get("report_digest_sha256") or "")
        if fingerprint:
            fingerprint_counts[fingerprint] = fingerprint_counts.get(fingerprint, 0) + 1
        if report_digest:
            report_digest_counts[report_digest] = report_digest_counts.get(report_digest, 0) + 1
    for host in host_summaries:
        fingerprint = str(host.get("host_fingerprint") or "")
        report_digest = str(host.get("report_digest_sha256") or "")
        host["identity_unique"] = not fingerprint or fingerprint_counts.get(fingerprint, 0) == 1
        host["report_unique"] = not report_digest or report_digest_counts.get(report_digest, 0) == 1
        host["host_ready"] = bool(host["host_ready"] and host["identity_unique"] and host["report_unique"])


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
        "| Host | Platform | Host Report Dir | Unreal Matrix | Godot Workflow | Runtime | Visual | Host Compat | Unique Host | Unique Report | Host Ready |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for host in report["hosts"]:
        lines.append(
            f"| {host['host_label']} | {host['platform']} | {host['report_dir']} | {'yes' if host['unreal_matrix_ok'] else 'no'} | "
            f"{'yes' if host['godot_workflow_ok'] else 'no'} | {'yes' if host['orientation_runtime_ok'] else 'no'} | "
            f"{'yes' if host['orientation_visual_ok'] else 'no'} | {'yes' if host['unreal_host_compat_ok'] else 'no'} | "
            f"{'yes' if host['identity_unique'] else 'no'} | {'yes' if host['report_unique'] else 'no'} | "
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
    duplicate_hosts = [host for host in report["hosts"] if not host["identity_unique"]]
    duplicate_reports = [host for host in report["hosts"] if not host["report_unique"]]
    if duplicate_hosts or duplicate_reports:
        lines.extend(["", "## Duplicate Detection", ""])
        if duplicate_hosts:
            lines.append("- Duplicate host identities were detected and do not count toward cross-host signoff.")
        if duplicate_reports:
            lines.append("- Duplicate report payloads were detected and do not count toward cross-host signoff.")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    load_local_env.load()
    args = parse_args()
    report_root = Path(getattr(args, "report_root", DEFAULT_REPORT_ROOT)).expanduser().resolve()
    report_dirs = discover_report_dirs(getattr(args, "report_dirs", None), report_root)
    required_unreal_versions = args.required_unreal_versions or list(DEFAULT_REQUIRED_UNREAL_VERSIONS)
    out_dir = Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    hosts = [summarize_host(load_host_report(report_dir), required_unreal_versions) for report_dir in report_dirs]
    apply_duplicate_detection(hosts)
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
