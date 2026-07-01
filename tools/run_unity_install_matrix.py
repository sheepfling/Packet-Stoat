#!/usr/bin/env python3
"""Aggregate Unity Git/UPM install-smoke host reports into a signoff matrix."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import load_local_env


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT_DIR = ROOT / "artifacts" / "reports"
REQUIRED_HOSTS = ("macos", "windows", "linux")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR, help="Directory containing unity_install_smoke_<host>.json reports")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_REPORT_DIR, help="Directory to write the aggregate matrix")
    return parser.parse_args(argv)


def load_json(path: Path) -> dict[str, object] | None:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return None


def classify_payload(payload: dict[str, object]) -> tuple[str | None, str | None]:
    failure_stage = payload.get("failure_stage")
    failure_reason = payload.get("failure_reason")
    if isinstance(failure_stage, str) and isinstance(failure_reason, str):
        return failure_stage, failure_reason
    project_state = payload.get("project_state")
    if isinstance(project_state, dict) and not project_state.get("library_exists", False):
        return "host-startup", "project-import-never-started"
    if not payload.get("package_cache_locations"):
        return "package-install", "package-cache-missing"
    return None, None


def host_row(report_dir: Path, host: str) -> dict[str, object]:
    path = report_dir / f"unity_install_smoke_{host}.json"
    payload = load_json(path)
    if payload is None:
        return {
            "host": host,
            "status": "missing",
            "detail": f"missing {path.name}",
            "report": str(path),
        }
    status = str(payload.get("status") or "invalid")
    detail = str(payload.get("detail") or status)
    if status == "pass":
        row_status = "pass"
    elif status in {"fail", "skip"}:
        row_status = status
    else:
        row_status = "invalid"
        detail = f"unexpected status: {status}"
    failure_stage, failure_reason = classify_payload(payload)
    return {
        "host": host,
        "status": row_status,
        "detail": detail,
        "report": str(path),
        "unity_version": payload.get("unity_version"),
        "failure_stage": failure_stage,
        "failure_reason": failure_reason,
        "manifest_git_url": payload.get("manifest_git_url"),
        "package_cache_locations": payload.get("package_cache_locations", []),
        "plugin_inventory": payload.get("plugin_inventory", {}),
        "adopted_from": payload.get("adopted_from"),
    }


def overall_status(rows: list[dict[str, object]]) -> str:
    statuses = {str(row["status"]) for row in rows}
    if statuses == {"pass"}:
        return "cross-host-ready"
    if "fail" in statuses or "skip" in statuses or "invalid" in statuses:
        return "cross-host-failed"
    if "pass" in statuses:
        return "cross-host-incomplete"
    if "missing" in statuses:
        return "no-host-reports"
    return "cross-host-invalid"


def build_report(report_dir: Path) -> dict[str, object]:
    rows = [host_row(report_dir, host) for host in REQUIRED_HOSTS]
    return {
        "schema": "fastdis.unity_install_matrix.v1",
        "report_dir": str(report_dir),
        "required_hosts": list(REQUIRED_HOSTS),
        "overall_status": overall_status(rows),
        "ready_hosts": [row["host"] for row in rows if row["status"] == "pass"],
        "missing_hosts": [row["host"] for row in rows if row["status"] == "missing"],
        "rows": rows,
    }


def render_markdown(report: dict[str, object]) -> str:
    lines = [
        "# Unity Install Signoff Matrix",
        "",
        f"- overall_status: `{report['overall_status']}`",
        f"- ready_hosts: `{','.join(report['ready_hosts']) or 'none'}`",
        f"- missing_hosts: `{','.join(report['missing_hosts']) or 'none'}`",
        f"- report_dir: `{report['report_dir']}`",
        "",
        "## Hosts",
        "",
    ]
    for row in report["rows"]:
        suffix = ""
        if row.get("failure_stage") or row.get("failure_reason"):
            suffix = f" stage={row.get('failure_stage', 'unknown')} reason={row.get('failure_reason', 'unknown')}"
        lines.append(f"- `{row['host']}` `{row['status']}`: {row['detail']}{suffix}")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- `cross-host-ready` means macOS, Windows, and Linux all have passing Unity Git/UPM install-smoke reports.",
            "- `cross-host-incomplete` means at least one host passed, but the required three-host matrix is not complete.",
            "- `cross-host-failed` means at least one host report exists but is failing, skipped, or invalid.",
            "- `no-host-reports` means the required host reports were not found.",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    load_local_env.load()
    args = parse_args(argv)
    report = build_report(args.report_dir)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.out_dir / "unity_install_matrix.json"
    md_path = args.out_dir / "unity_install_matrix.md"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    print(f"JSON: {json_path}")
    print(f"Markdown: {md_path}")
    return 0 if report["overall_status"] == "cross-host-ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
