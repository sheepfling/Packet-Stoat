#!/usr/bin/env python3
"""Aggregate staged Unity host bundles into a cross-host host-matrix report."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path

import load_local_env
import stage_unity_host_report


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_HOST_ROOT = ROOT / "verification_reports" / "unity_hosts"
DEFAULT_OUT_DIR = ROOT / "build" / "reports"
REQUIRED_HOSTS = ("macos", "windows", "linux")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host-root", default=str(DEFAULT_HOST_ROOT), help="Root directory containing staged Unity host bundles")
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR), help="Directory for JSON/Markdown reports")
    return parser.parse_args(argv)


def load_manifest(host_dir: Path) -> dict[str, object]:
    manifest_path = host_dir / stage_unity_host_report.HOST_MANIFEST
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Host bundle is missing {stage_unity_host_report.HOST_MANIFEST}: {host_dir}")
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def discover_host_dirs(host_root: Path) -> list[Path]:
    if not host_root.is_dir():
        return []
    return sorted(child for child in host_root.iterdir() if child.is_dir() and (child / stage_unity_host_report.HOST_MANIFEST).is_file())


def summarize_host(host_dir: Path) -> dict[str, object]:
    manifest = load_manifest(host_dir)
    host_platform = str(manifest.get("host_platform") or "").strip()
    if host_platform not in REQUIRED_HOSTS:
        raise ValueError(f"Unexpected Unity host_platform in {host_dir}: {host_platform!r}")
    workflow_ok = manifest.get("unity_workflow_status") == "pass"
    runtime_ok = manifest.get("unity_runtime_status") == "pass"
    orientation_ok = manifest.get("unity_orientation_status") == "pass"
    startup_probe_ok = manifest.get("unity_startup_probe_status") == "pass"
    install_ok = manifest.get("unity_install_status") == "pass"
    host_ready = workflow_ok and runtime_ok and orientation_ok and startup_probe_ok and install_ok
    return {
        "host_label": manifest.get("host_label", host_dir.name),
        "host_dir": str(host_dir),
        "host_platform": host_platform,
        "hostname": manifest.get("hostname", host_dir.name),
        "host_fingerprint": manifest.get("host_fingerprint", ""),
        "report_digest_sha256": manifest.get("report_digest_sha256", ""),
        "unity_workflow_status": manifest.get("unity_workflow_status", "missing"),
        "unity_runtime_status": manifest.get("unity_runtime_status", "missing"),
        "unity_orientation_status": manifest.get("unity_orientation_status", "missing"),
        "unity_startup_probe_status": manifest.get("unity_startup_probe_status", "missing"),
        "unity_install_status": manifest.get("unity_install_status", "missing"),
        "workflow_ok": workflow_ok,
        "runtime_ok": runtime_ok,
        "orientation_ok": orientation_ok,
        "startup_probe_ok": startup_probe_ok,
        "install_ok": install_ok,
        "identity_unique": True,
        "report_unique": True,
        "host_ready": host_ready,
    }


def apply_duplicate_detection(hosts: list[dict[str, object]]) -> None:
    fingerprint_counts: dict[str, int] = {}
    report_digest_counts: dict[str, int] = {}
    platform_counts: dict[str, int] = {}
    for host in hosts:
        fingerprint = str(host.get("host_fingerprint") or "")
        report_digest = str(host.get("report_digest_sha256") or "")
        platform_name = str(host["host_platform"])
        if fingerprint:
            fingerprint_counts[fingerprint] = fingerprint_counts.get(fingerprint, 0) + 1
        if report_digest:
            report_digest_counts[report_digest] = report_digest_counts.get(report_digest, 0) + 1
        platform_counts[platform_name] = platform_counts.get(platform_name, 0) + 1
    for host in hosts:
        fingerprint = str(host.get("host_fingerprint") or "")
        report_digest = str(host.get("report_digest_sha256") or "")
        platform_name = str(host["host_platform"])
        host["identity_unique"] = not fingerprint or fingerprint_counts.get(fingerprint, 0) == 1
        host["report_unique"] = not report_digest or report_digest_counts.get(report_digest, 0) == 1
        host["platform_unique"] = platform_counts.get(platform_name, 0) == 1
        host["host_ready"] = bool(host["host_ready"] and host["identity_unique"] and host["report_unique"] and host["platform_unique"])


def overall_status(hosts: list[dict[str, object]]) -> str:
    if not hosts:
        return "no-host-reports"
    ready_platforms = {str(host["host_platform"]) for host in hosts if host["host_ready"]}
    if ready_platforms == set(REQUIRED_HOSTS):
        return "cross-host-ready"
    if any(host["host_ready"] for host in hosts):
        return "cross-host-incomplete"
    return "cross-host-failed"


def build_report(host_root: Path) -> dict[str, object]:
    host_dirs = discover_host_dirs(host_root)
    hosts = [summarize_host(host_dir) for host_dir in host_dirs]
    apply_duplicate_detection(hosts)
    ready_platforms = sorted({str(host["host_platform"]) for host in hosts if host["host_ready"]})
    return {
        "schema": "fastdis.unity_host_matrix.v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "host_root": str(host_root),
        "required_hosts": list(REQUIRED_HOSTS),
        "overall_status": overall_status(hosts),
        "ready_platforms": ready_platforms,
        "missing_platforms": [platform_name for platform_name in REQUIRED_HOSTS if platform_name not in ready_platforms],
        "hosts": hosts,
    }


def render_markdown(report: dict[str, object]) -> str:
    lines = [
        "# Unity Host Matrix",
        "",
        f"- generated_at: `{report['generated_at']}`",
        f"- overall_status: `{report['overall_status']}`",
        f"- ready_platforms: `{','.join(report['ready_platforms']) or 'none'}`",
        f"- missing_platforms: `{','.join(report['missing_platforms']) or 'none'}`",
        f"- host_root: `{report['host_root']}`",
        "",
        "| Host | Platform | Workflow | Runtime | Orientation | Startup Probe | Install | Unique Host | Unique Report | Unique Platform | Host Ready |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for host in report["hosts"]:
        lines.append(
            f"| {host['host_label']} | {host['host_platform']} | {host['unity_workflow_status']} | {host['unity_runtime_status']} | {host['unity_orientation_status']} | {host['unity_startup_probe_status']} | {host['unity_install_status']} | "
            f"{'yes' if host['identity_unique'] else 'no'} | {'yes' if host['report_unique'] else 'no'} | {'yes' if host['platform_unique'] else 'no'} | {'yes' if host['host_ready'] else 'no'} |"
        )
    lines.extend(["", "## Interpretation", ""])
    if report["overall_status"] == "cross-host-ready":
        lines.append("- macOS, Windows, and Linux all have unique staged Unity host bundles with passing workflow/runtime/orientation/install status.")
    elif report["overall_status"] == "cross-host-incomplete":
        lines.append("- At least one staged Unity host bundle is ready, but the required three-platform matrix is not complete yet.")
    elif report["overall_status"] == "cross-host-failed":
        lines.append("- Staged Unity host bundles are present, but none currently satisfy the required host-ready criteria.")
    else:
        lines.append("- No staged Unity host bundles were found.")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    load_local_env.load()
    args = parse_args(argv)
    host_root = Path(args.host_root).expanduser().resolve()
    out_dir = Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    report = build_report(host_root)
    json_path = out_dir / "unity_host_matrix.json"
    md_path = out_dir / "unity_host_matrix.md"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    print(f"JSON: {json_path}")
    print(f"Markdown: {md_path}")
    return 0 if report["overall_status"] == "cross-host-ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
