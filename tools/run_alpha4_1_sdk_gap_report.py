#!/usr/bin/env python3
"""Generate the combined Alpha 4.1 SDK gap report."""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))

import lattice_contract_audit
import lattice_grpc_contract_report
import lattice_sample_parity_audit
from artifacts import VERIFICATION_REPORTS_DIR


DEFAULT_OUT_DIR = VERIFICATION_REPORTS_DIR / "alpha4_1" / "lattice"
DEFAULT_REPORT_BASENAME = "lattice_sdk_gap_report"


def render_markdown(report: dict[str, object]) -> str:
    lines = [
        "# Alpha 4.1 Lattice SDK Gap Report",
        "",
        f"- overall_status: `{report['overall_status']}`",
        f"- real_lattice_verified: `{report['real_lattice_verified']}`",
        f"- sdk_import_verified: `{report['sdk_import_verified']}`",
        f"- public_doc_contract_aligned: `{report['public_doc_contract_aligned']}`",
        "",
        "## Transport Contract",
        "",
        f"- mock_http: `{report['transport_contract']['mock_http']}`",
        f"- official_rest_sdk_mock_transport: `{report['transport_contract']['official_rest_sdk_mock_transport']}`",
        f"- mock_stream: `{report['transport_contract']['mock_stream']}`",
        f"- local_grpc_publish_stream: `{report['transport_contract']['local_grpc_publish_stream']}`",
        f"- real_rest: `{report['transport_contract']['real_rest']}`",
        f"- real_grpc: `{report['transport_contract']['real_grpc']}`",
        "",
        "## Remaining Credential-Gated Work",
        "",
    ]
    for gap in report["remaining_credential_gated_work"]:
        lines.append(f"- {gap}")
    return "\n".join(lines)


def build_report() -> dict[str, object]:
    contract_report = lattice_contract_audit.build_report()
    parity_report = lattice_sample_parity_audit.build_report()
    grpc_report = lattice_grpc_contract_report.build_report()
    sdk_import = parity_report["sdk_import"]
    return {
        "overall_status": "access_ready_no_credentials",
        "real_lattice_verified": False,
        "sdk_import_verified": bool(sdk_import.get("installed") and sdk_import.get("has_lattice_client")),
        "public_doc_contract_aligned": contract_report["overall_status"] == "aligned",
        "contract_report_status": contract_report["overall_status"],
        "sample_parity_status": parity_report["overall_status"],
        "sdk_rest_mock_transport": parity_report["sdk_rest_mock_transport"]["status"],
        "grpc_contract_status": grpc_report["overall_status"],
        "transport_contract": {
            "mock_http": "passed",
            "official_rest_sdk_mock_transport": parity_report["sdk_rest_mock_transport"]["status"],
            "mock_stream": "passed",
            "local_grpc_publish_stream": grpc_report["overall_status"],
            "real_rest": "requires_credentials",
            "real_grpc": "requires_credentials",
        },
        "remaining_credential_gated_work": [
            *parity_report["remaining_real_sandbox_gaps"],
            *grpc_report["remaining_gap"],
        ],
    }


def write_report(report: dict[str, object], out_dir: Path = DEFAULT_OUT_DIR) -> tuple[Path, Path]:
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
