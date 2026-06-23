#!/usr/bin/env python3
"""Probe the pinned Zorn REST route through the official-style Python SDK surface."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import importlib
import json
import os
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from artifacts import VERIFICATION_REPORTS_DIR
from fastdis.lattice_backend import load_lattice_backend_config


DEFAULT_OUT_DIR = VERIFICATION_REPORTS_DIR / "alpha5" / "lattice_zorn_rest_sdk"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args()


def _check(name: str, status: str, detail: str = "") -> dict[str, str]:
    return {"name": name, "status": status, "detail": detail}


def build_report() -> dict[str, Any]:
    config = load_lattice_backend_config()
    checkout = config.checkout_path
    checks: list[dict[str, str]] = [
        _check("backend_config_loaded", "passed", f"config={config.config_path}"),
        _check("zorn_checkout_present", "passed" if checkout.exists() else "failed", str(checkout)),
    ]
    gaps: list[str] = []

    try:
        module = importlib.import_module("anduril")
    except ModuleNotFoundError as exc:
        checks.append(_check("official_python_sdk_import", "skipped", str(exc)))
        gaps.append(str(exc))
        sdk_client_status = "skipped"
        sdk_client_detail = "official SDK is not installed locally"
    else:
        checks.append(_check("official_python_sdk_import", "passed", getattr(module, "__file__", "imported")))
        endpoint = (
            os.environ.get("FASTDIS_LATTICE_BASE_URL")
            or os.environ.get("LATTICE_ENDPOINT")
            or os.environ.get("LATTICE_BASE_URL")
            or "http://127.0.0.1:8000"
        )
        token = (
            os.environ.get("FASTDIS_LATTICE_TOKEN")
            or os.environ.get("LATTICE_TOKEN")
            or os.environ.get("LATTICE_BEARER_TOKEN")
            or "zorn-local-token"
        )
        headers: dict[str, str] = {}
        sandbox_token = os.environ.get("LATTICE_SANDBOX_TOKEN")
        if sandbox_token:
            headers["Anduril-Sandbox-Authorization"] = f"Bearer {sandbox_token}"
        try:
            client = module.Lattice(base_url=endpoint, token=lambda: token, headers=headers)
        except Exception as exc:  # pragma: no cover - environment dependent
            sdk_client_status = "failed"
            sdk_client_detail = f"{type(exc).__name__}: {exc}"
            gaps.append(sdk_client_detail)
        else:
            sdk_client_status = "passed"
            sdk_client_detail = f"constructed {type(client).__name__} for {endpoint}"
    checks.append(_check("official_python_sdk_client_construct", sdk_client_status, sdk_client_detail))

    overall_status = "ready" if all(item["status"] == "passed" for item in checks) else "ready-with-gaps"
    return {
        "schema": "fastdis.zorn.rest_sdk_probe.v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "backend": config.backend,
        "transport": config.transport,
        "zorn_tag": config.tag,
        "zorn_checkout": str(checkout),
        "proof_source": "zorn-rest-sdk-compatible-route",
        "real_lattice_verified": False,
        "overall_status": overall_status,
        "checks": checks,
        "gaps": gaps,
    }


def write_report(report: dict[str, Any], out_dir: Path) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "zorn_rest_sdk_probe_report.json"
    md_path = out_dir / "zorn_rest_sdk_probe_report.md"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(_render_markdown(report), encoding="utf-8")
    return json_path, md_path


def _render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Zorn REST SDK Probe",
        "",
        f"- overall_status: `{report.get('overall_status', 'unknown')}`",
        f"- proof_source: `{report.get('proof_source', 'unknown')}`",
        f"- real_lattice_verified: `{report.get('real_lattice_verified', False)}`",
        "",
        "## Checks",
        "",
    ]
    for item in report.get("checks", []):
        if not isinstance(item, dict):
            continue
        lines.append(f"- `{item.get('name', 'unknown')}`: `{item.get('status', 'unknown')}`")
        detail = item.get("detail")
        if detail:
            lines.append(f"  - {detail}")
    gaps = report.get("gaps", [])
    if isinstance(gaps, list) and gaps:
        lines.extend(["", "## Gaps", ""])
        for gap in gaps:
            lines.append(f"- {gap}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    report = build_report()
    json_path, md_path = write_report(report, args.out_dir)
    print(f"JSON: {json_path}")
    print(f"Markdown: {md_path}")
    print(f"status: {report['overall_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
