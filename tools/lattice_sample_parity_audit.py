#!/usr/bin/env python3
"""Audit Packet-Stoat's Lattice adapter surface against public-SDK/sample expectations."""

from __future__ import annotations

import importlib
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
ADAPTER_SRC = ROOT / "packages" / "lattice" / "src"
for candidate in (SRC, ADAPTER_SRC):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from artifacts import VERIFICATION_REPORTS_DIR
from packet_stoat_lattice import RealLatticeConfig, RealLatticePublisher, build_sdk_mock_transport


DEFAULT_OUT_DIR = VERIFICATION_REPORTS_DIR / "alpha4_1" / "lattice"
DEFAULT_REPORT_BASENAME = "lattice_sample_parity_report"


def sdk_import_status() -> dict[str, Any]:
    try:
        module = importlib.import_module("anduril")
    except ModuleNotFoundError:
        return {"installed": False, "status": "not-installed", "module": "anduril"}
    lattice = getattr(module, "Lattice", None)
    return {
        "installed": True,
        "status": "available" if lattice is not None else "partial",
        "module": "anduril",
        "has_lattice_client": lattice is not None,
    }


def build_report() -> dict[str, Any]:
    expected_config = ["endpoint", "client_id", "client_secret", "token", "dry_run"]
    config = RealLatticeConfig()
    publisher = RealLatticePublisher(config)
    supported_methods = [
        "publish_entity",
        "publish_entities",
        "stream_entities",
        "put_object",
        "stream_tasks",
        "config_snapshot",
    ]
    parity_rows = []
    for name in expected_config:
        parity_rows.append(
            {
                "kind": "config",
                "name": name,
                "status": "pass" if hasattr(config, name) else "missing",
            }
        )
    for name in supported_methods:
        parity_rows.append(
            {
                "kind": "method",
                "name": name,
                "status": "pass" if hasattr(publisher, name) else "missing",
            }
        )
    transport = build_sdk_mock_transport()
    sdk_rest_mock_transport = {
        "status": "pass" if transport is not None else "missing",
        "transport": "httpx.MockTransport",
        "official_sdk_client": "anduril.Lattice",
        "sdk_required_for_client_test": True,
    }
    sdk_status = sdk_import_status()
    overall_status = "sdk-shaped" if all(row["status"] == "pass" for row in parity_rows) else "gaps-detected"
    return {
        "overall_status": overall_status,
        "real_backend": publisher.config_snapshot(),
        "sdk_import": sdk_status,
        "sdk_rest_mock_transport": sdk_rest_mock_transport,
        "parity_rows": parity_rows,
        "remaining_real_sandbox_gaps": [
            "live authentication flow",
            "real entity publish transport",
            "real entity stream transport",
            "real objects API calls",
            "real task streaming behavior",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Lattice Sample Parity Audit",
        "",
        f"- overall_status: `{report['overall_status']}`",
        f"- sdk_import_status: `{report['sdk_import']['status']}`",
        f"- sdk_rest_mock_transport: `{report['sdk_rest_mock_transport']['status']}`",
        "",
        "| Kind | Name | Status |",
        "| --- | --- | --- |",
    ]
    for row in report["parity_rows"]:
        lines.append(f"| {row['kind']} | {row['name']} | {row['status']} |")
    lines.extend(["", "## Remaining Real-Sandbox Gaps", ""])
    for gap in report["remaining_real_sandbox_gaps"]:
        lines.append(f"- {gap}")
    return "\n".join(lines)


def write_report(report: dict[str, Any], out_dir: Path = DEFAULT_OUT_DIR) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"{DEFAULT_REPORT_BASENAME}.json"
    md_path = out_dir / f"{DEFAULT_REPORT_BASENAME}.md"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    return json_path, md_path


def main() -> int:
    report = build_report()
    json_path, md_path = write_report(report)
    print(json.dumps({"overall_status": report["overall_status"], "json": str(json_path), "markdown": str(md_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
