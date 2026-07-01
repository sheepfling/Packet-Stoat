#!/usr/bin/env python3
"""Sync staged Unity host bundles into the local report directory and refresh aggregates."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil

import import_unity_host_report
import load_local_env
import stage_unity_host_report


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_HOST_ROOT = ROOT / "verification_reports" / "unity_hosts"
DEFAULT_REPORT_DIR = ROOT / "artifacts" / "reports"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host-root", default=str(DEFAULT_HOST_ROOT), help="Root directory containing staged Unity host bundles")
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR), help="Directory that will receive adopted unity_install_smoke_<host>.json evidence")
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


def sync_host_bundle(host_dir: Path, report_dir: Path) -> tuple[str, Path]:
    manifest = load_manifest(host_dir)
    host_platform = str(manifest.get("host_platform") or "").strip()
    if host_platform not in {"macos", "windows", "linux"}:
        raise ValueError(f"Unexpected Unity host_platform in {host_dir}: {host_platform!r}")
    source_json = host_dir / f"unity_install_smoke_{host_platform}.json"
    source_md = host_dir / f"unity_install_smoke_{host_platform}.md"
    if not source_json.is_file() or not source_md.is_file():
        raise FileNotFoundError(f"Host bundle is missing install smoke artifacts for {host_platform}: {host_dir}")
    dest_json = report_dir / source_json.name
    dest_md = report_dir / source_md.name
    shutil.copy2(source_json, dest_json)
    shutil.copy2(source_md, dest_md)
    return host_platform, dest_json


def main(argv: list[str] | None = None) -> int:
    load_local_env.load()
    args = parse_args(argv)
    host_root = Path(args.host_root).expanduser().resolve()
    report_dir = Path(args.report_dir).expanduser().resolve()
    report_dir.mkdir(parents=True, exist_ok=True)
    host_dirs = discover_host_dirs(host_root)
    if not host_dirs:
        raise FileNotFoundError(f"No Unity host bundles found under {host_root}")

    seen_platforms: dict[str, Path] = {}
    for host_dir in host_dirs:
        host_platform, dest_json = sync_host_bundle(host_dir, report_dir)
        if host_platform in seen_platforms:
            raise ValueError(f"Duplicate Unity host bundle for platform {host_platform}: {seen_platforms[host_platform]} and {host_dir}")
        seen_platforms[host_platform] = host_dir
        print(f"Synced {host_platform}: {dest_json}")

    matrix_json, matrix_md, host_matrix_json, host_matrix_md, workflow_json, workflow_md, signoff_json, signoff_md = import_unity_host_report.refresh_aggregate_reports(report_dir, host_root)
    print(f"Refreshed install matrix: {matrix_json}")
    print(f"Refreshed install matrix summary: {matrix_md}")
    print(f"Refreshed host matrix: {host_matrix_json}")
    print(f"Refreshed host matrix summary: {host_matrix_md}")
    print(f"Refreshed workflow report: {workflow_json}")
    print(f"Refreshed workflow summary: {workflow_md}")
    print(f"Refreshed signoff report: {signoff_json}")
    print(f"Refreshed signoff summary: {signoff_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
