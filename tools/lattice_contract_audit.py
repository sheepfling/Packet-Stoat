#!/usr/bin/env python3
"""Audit current Lattice-shaped bridge payloads against public-field expectations."""

from __future__ import annotations

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
from packet_stoat_lattice import canonical_entity_from_fixture, lattice_track_payload_from_entity


DEFAULT_FIXTURE = ROOT / "packages" / "lattice" / "examples" / "dis_entity_fixture.json"
DEFAULT_OUT_DIR = VERIFICATION_REPORTS_DIR / "alpha4_1" / "lattice"
DEFAULT_REPORT_BASENAME = "lattice_contract_audit_report"


def nested_get(payload: dict[str, Any], dotted_path: str) -> Any:
    current: Any = payload
    for part in dotted_path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def audit_payload(payload: dict[str, Any]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    direct_expectations = {
        "entityId": "public entity identifier",
        "isLive": "public entity liveness flag",
        "expiryTime": "public entity expiry time",
        "aliases.name": "human-readable entity alias",
        "ontology.template": "public ontology template",
        "provenance.integrationName": "publishing integration name",
        "provenance.sourceUpdateTime": "source update time",
        "location.position": "public location position",
        "milView.disposition": "public disposition field",
        "ontology.platformType": "public platform type field",
    }
    for path, reason in direct_expectations.items():
        value = nested_get(payload, path)
        checks.append(
            {
                "field": path,
                "status": "pass" if value not in (None, "", []) else "missing",
                "reason": reason,
                "value_present": value not in (None, "", []),
            }
        )

    sidecar_checks = [
        {
            "field": "orientation",
            "status": "bridge-sidecar" if nested_get(payload, "pose.orientation_dis_deg") is not None else "missing",
            "reason": "DIS orientation is preserved in the mock bridge pose sidecar",
        },
        {
            "field": "velocity",
            "status": "bridge-sidecar" if nested_get(payload, "pose.velocity_mps") is not None else "missing",
            "reason": "velocity is preserved in the mock bridge pose sidecar",
        },
    ]
    checks.extend(sidecar_checks)

    loop_suppression = nested_get(payload, "packetStoat.source")
    checks.append(
        {
            "field": "packetStoat.source",
            "status": "pass" if loop_suppression is not None else "missing",
            "reason": "loop suppression provenance marker",
            "value_present": loop_suppression is not None,
        }
    )

    summary = {
        "pass_count": sum(1 for check in checks if check["status"] == "pass"),
        "bridge_sidecar_count": sum(1 for check in checks if check["status"] == "bridge-sidecar"),
        "missing_count": sum(1 for check in checks if check["status"] == "missing"),
    }
    summary["overall_status"] = "aligned" if summary["missing_count"] == 0 else "gaps-detected"
    return {"payload": payload, "checks": checks, "summary": summary}


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Lattice Contract Audit",
        "",
        f"- overall_status: `{report['overall_status']}`",
        f"- fixture: `{report['fixture']}`",
        f"- payload_count: `{report['payload_count']}`",
        "",
        "| Field | Status | Reason |",
        "| --- | --- | --- |",
    ]
    first_payload = report["payload_audits"][0]
    for check in first_payload["checks"]:
        lines.append(f"| {check['field']} | {check['status']} | {check['reason']} |")
    lines.extend(
        [
            "",
            "## Summary",
            "",
            f"- pass_count: `{first_payload['summary']['pass_count']}`",
            f"- bridge_sidecar_count: `{first_payload['summary']['bridge_sidecar_count']}`",
            f"- missing_count: `{first_payload['summary']['missing_count']}`",
        ]
    )
    return "\n".join(lines)


def build_report(fixture: Path = DEFAULT_FIXTURE) -> dict[str, Any]:
    entities = canonical_entity_from_fixture(fixture)
    payload_audits = [audit_payload(lattice_track_payload_from_entity(entity)) for entity in entities]
    overall_status = "aligned" if all(audit["summary"]["missing_count"] == 0 for audit in payload_audits) else "gaps-detected"
    return {
        "overall_status": overall_status,
        "fixture": str(fixture),
        "payload_count": len(payload_audits),
        "payload_audits": payload_audits,
    }


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
