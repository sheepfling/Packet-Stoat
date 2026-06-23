#!/usr/bin/env python3
"""Generate the current Zorn proof and gap manifest."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from fastdis.lattice_backend import load_lattice_backend_config


DEFAULT_JSON_PATH = ROOT / "generated" / "zorn_gap_manifest.json"
DEFAULT_MD_PATH = ROOT / "docs" / "ZORN_GAP_MANIFEST.md"
DEFAULT_REPORT_ROOT = ROOT / "build" / "verification_reports" / "alpha5"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_PATH)
    parser.add_argument("--md-out", type=Path, default=DEFAULT_MD_PATH)
    parser.add_argument("--report-root", type=Path, default=DEFAULT_REPORT_ROOT)
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def _load_report(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else None


def _surface_status(name: str, report: dict[str, Any] | None) -> dict[str, Any]:
    if report is None:
        return {"name": name, "status": "unknown", "report_present": False}
    overall = str(report.get("overall_status", "unknown"))
    checks = report.get("checks", [])
    passed = [check["name"] for check in checks if isinstance(check, dict) and check.get("status") == "passed"]
    failed = [check["name"] for check in checks if isinstance(check, dict) and check.get("status") == "failed"]
    gaps = list(report.get("gaps", []))
    status = "proven" if overall == "ready" else "gap" if overall == "ready-with-gaps" else "failed"
    return {
        "name": name,
        "status": status,
        "report_present": True,
        "overall_status": overall,
        "passed_checks": passed,
        "failed_checks": failed,
        "gaps": gaps,
    }


def build_manifest(report_root: Path) -> dict[str, Any]:
    config = load_lattice_backend_config()
    reports = {
        "rest_sdk": _load_report(report_root / "lattice_zorn_rest_sdk_alpha1_4" / "zorn_rest_sdk_probe_report.json")
        or _load_report(report_root / "lattice_zorn_rest_sdk_alpha1_3" / "zorn_rest_sdk_probe_report.json")
        or _load_report(report_root / "lattice_zorn_rest_sdk_alpha1_2" / "zorn_rest_sdk_probe_report.json")
        or _load_report(report_root / "lattice_zorn_rest_sdk_alpha1_1" / "zorn_rest_sdk_probe_report.json")
        or _load_report(report_root / "lattice_zorn_rest_sdk" / "zorn_rest_sdk_probe_report.json"),
        "grpc": _load_report(report_root / "lattice_zorn_grpc_alpha1_4" / "zorn_grpc_probe_report.json")
        or _load_report(report_root / "lattice_zorn_grpc_alpha1_3" / "zorn_grpc_probe_report.json")
        or _load_report(report_root / "lattice_zorn_grpc_alpha1_2" / "zorn_grpc_probe_report.json")
        or _load_report(report_root / "lattice_zorn_grpc_full_task_alpha1_1" / "zorn_grpc_probe_report.json")
        or _load_report(report_root / "lattice_zorn_grpc_alpha1_1" / "zorn_grpc_probe_report.json")
        or _load_report(report_root / "lattice_zorn_grpc" / "zorn_grpc_probe_report.json"),
        "entity_parity": _load_report(report_root / "lattice_zorn_entity_parity_alpha1_4" / "zorn_entity_parity_probe_report.json")
        or _load_report(report_root / "lattice_zorn_entity_parity_alpha1_3" / "zorn_entity_parity_probe_report.json")
        or _load_report(report_root / "lattice_zorn_entity_parity_alpha1_2" / "zorn_entity_parity_probe_report.json")
        or _load_report(report_root / "lattice_zorn_entity_parity" / "zorn_entity_parity_probe_report.json"),
        "auth_lifecycle": _load_report(report_root / "lattice_zorn_auth_lifecycle_alpha1_4" / "zorn_auth_lifecycle_probe_report.json")
        or _load_report(report_root / "lattice_zorn_auth_lifecycle_alpha1_3" / "zorn_auth_lifecycle_probe_report.json")
        or _load_report(report_root / "lattice_zorn_auth_lifecycle_alpha1_2" / "zorn_auth_lifecycle_probe_report.json")
        or _load_report(report_root / "lattice_zorn_auth_lifecycle" / "zorn_auth_lifecycle_probe_report.json"),
    }
    surfaces = [_surface_status(name, report) for name, report in reports.items()]

    proven = [surface["name"] for surface in surfaces if surface["status"] == "proven"]
    gaps: list[dict[str, Any]] = []
    for surface in surfaces:
        if surface["status"] in {"gap", "failed", "unknown"}:
            gaps.append(
                {
                    "surface": surface["name"],
                    "status": surface["status"],
                    "failed_checks": surface.get("failed_checks", []),
                    "details": surface.get("gaps", []),
                }
            )
    for cheat in config.cheat_surfaces:
        gaps.append({"surface": "backend_cheat_surface", "status": "gap", "details": [cheat]})

    unknown_real = [
        "Real Lattice auth expiry, refresh, and scope semantics remain unknown until a live credential-gated route is exercised.",
        "Vendor-only stream timing, routing, and backend side effects remain unknown where Zorn does not expose them.",
        "Objects and tasks are proven only against Zorn's local state machines, not a live vendor backend.",
    ]

    return {
        "schema": "fastdis.zorn.gap_manifest.v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "backend": config.backend,
        "transport": config.transport,
        "zorn_tag": config.tag,
        "zorn_checkout": str(config.checkout_path),
        "swappable_to_real_lattice": config.swappable_to_real_lattice,
        "proven_surfaces": proven,
        "surface_statuses": surfaces,
        "gaps": gaps,
        "unknown_real_lattice_surfaces": unknown_real,
    }


def _normalized_manifest_for_check(payload: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(payload)
    normalized.pop("generated_at", None)
    return normalized


def _render_markdown(manifest: dict[str, Any]) -> str:
    lines = [
        "# Zorn Gap Manifest",
        "",
        f"- backend: `{manifest.get('backend')}`",
        f"- transport: `{manifest.get('transport')}`",
        f"- zorn_tag: `{manifest.get('zorn_tag')}`",
        "",
        "## Surface Status",
        "",
    ]
    for surface in manifest.get("surface_statuses", []):
        lines.append(f"- `{surface['name']}`: `{surface['status']}`")
        if surface.get("report_present"):
            lines.append(f"  overall_status={surface.get('overall_status', 'unknown')}")
    lines.extend(["", "## Gaps", ""])
    for gap in manifest.get("gaps", []):
        details = gap.get("details", [])
        if details:
            lines.append(f"- `{gap.get('surface')}`:")
            for detail in details:
                lines.append(f"  - {detail}")
        else:
            lines.append(f"- `{gap.get('surface')}`: `{gap.get('status')}`")
    lines.extend(["", "## Real Lattice Unknowns", ""])
    for unknown in manifest.get("unknown_real_lattice_surfaces", []):
        lines.append(f"- {unknown}")
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    manifest = build_manifest(args.report_root)
    json_payload = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    md_payload = _render_markdown(manifest)
    if args.check:
        current_json = json.loads(args.json_out.read_text(encoding="utf-8")) if args.json_out.is_file() else None
        current_md = args.md_out.read_text(encoding="utf-8") if args.md_out.is_file() else None
        if (
            current_json is None
            or _normalized_manifest_for_check(current_json) != _normalized_manifest_for_check(manifest)
            or current_md != md_payload
        ):
            print("zorn gap manifest outputs are stale")
            return 1
        print("zorn gap manifest outputs are up to date")
        return 0
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.md_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json_payload, encoding="utf-8")
    args.md_out.write_text(md_payload, encoding="utf-8")
    print(json.dumps({"json": str(args.json_out), "markdown": str(args.md_out)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
