#!/usr/bin/env python3
"""Generate a source-backed Epic 2 milestone report from current audit/manifests."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import run_epic2_audit


JSON_OUT = ROOT / "generated" / "epic2_milestones.json"
MD_OUT = ROOT / "docs" / "EPIC2_MILESTONES.md"


MILESTONES: tuple[dict[str, object], ...] = (
    {
        "id": "milestone1",
        "name": "Milestone 1: 141-Row Generated Truth Table",
        "criterion_name": "141-row generated truth",
        "goal_blurb": (
            "The generated manifests become the first release boundary for full DIS buildout. "
            "If a known DIS 6/7 row lacks a product decision, the repo should fail loudly instead of quietly drifting."
        ),
        "exit_focus": [
            "141 standard rows are explicit across coverage, endpoint, logging, and Lattice/Zorn manifests.",
            "No row is left without an explicit generated product decision.",
        ],
        "proof_commands": [
            "python -m pytest tests/test_pdu_coverage_manifest.py tests/test_pdu_logging.py tests/test_lattice_dis_mapping_plan.py",
            "python tools/check_generated_fresh.py",
        ],
    },
    {
        "id": "milestone2",
        "name": "Milestone 2: Generic Wire And Field Coverage",
        "criterion_name": "Generic wire and field coverage",
        "goal_blurb": (
            "All known rows should be safe on the wire before they are deep in semantics. "
            "A PDU that is not yet fully decoded should still survive ingest, generic packet views, field inspection, logging, and endpoint surfacing."
        ),
        "exit_focus": [
            "Safe ingest, generic endpoint behavior, field visitors, translation, and shallow fuzz stay at full-row coverage.",
            "Unknown and extended values remain preserved rather than dropped.",
        ],
        "proof_commands": [
            "python -m pytest tests/test_pdu_coverage_manifest.py tests/test_pdu_catalog.py tests/test_typed_pdu_parsers.py tests/test_semantic_pdu_parsers.py",
            "python tools/check_generated_fresh.py",
        ],
    },
    {
        "id": "milestone3",
        "name": "Milestone 3: Typed Semantic PDU Waves",
        "criterion_name": "Typed semantic waves",
        "goal_blurb": (
            "Semantic depth should grow in coherent waves that line up with product value instead of scattered one-off decoders. "
            "The wave map should stay measurable as parser, serializer, docs, and tests move together."
        ),
        "exit_focus": [
            "All 141 rows stay assigned to one of five semantic waves.",
            "Wave counts and decoded/prefix totals remain generated and auditable.",
        ],
        "proof_commands": [
            "python -m pytest tests/test_typed_pdu_parsers.py tests/test_semantic_pdu_parsers.py",
            "python tools/check_generated_fresh.py",
        ],
    },
    {
        "id": "milestone4",
        "name": "Milestone 4: Cross-Engine And Lattice/Zorn Parity",
        "criterion_name": "Cross-engine and Lattice/Zorn parity",
        "goal_blurb": (
            "FastDIS should keep one product story across Python, native code, engines, and Lattice/Zorn "
            "instead of letting each endpoint invent different semantics for the same row."
        ),
        "exit_focus": [
            "Catalog visibility remains shared across C, C++, Python, Unreal, Godot, Unity, and Lattice/Zorn routing.",
            "Deep/runtime parity grows from the current representative rows toward all 141 rows.",
        ],
        "proof_commands": [
            "python tools/unity_workflow.py bridge-probe",
            "python tools/generate_evidence_pack.py --clean --render-symbols never",
            "python tools/check_evidence_pack.py artifacts/verification_reports/evidence/latest/manifest.json",
        ],
    },
    {
        "id": "milestone5",
        "name": "Milestone 5: Evidence And Release Gates",
        "criterion_name": "Evidence and release gates",
        "goal_blurb": (
            "Epic 2 is only credible if build, docs, generated outputs, and release artifacts keep proving the claims from source-backed receipts."
        ),
        "exit_focus": [
            "Evidence pack, docs audit, release inspection, and current release-ready receipt stay green.",
            "Repo-green includes generated freshness and product inspection rather than treating them as optional cleanup.",
        ],
        "proof_commands": [
            "python tools/dev_check.py --release-ready",
            "python tools/check_docs.py",
            "python tools/check_evidence_pack.py artifacts/verification_reports/evidence/latest/manifest.json",
        ],
    },
)


def _display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def _criterion_index(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(item["name"]): item for item in report["criteria"]}


def _progress_summary(criterion: dict[str, Any]) -> list[str]:
    name = str(criterion["name"])
    metrics = criterion.get("metrics", {})
    if name == "141-row generated truth":
        return [
            f"standard_total_rows={metrics.get('standard_total_rows')}",
            f"catalog_gap_rows={metrics.get('catalog_gap_rows')}",
            f"missing_endpoint_behavior={metrics.get('missing_endpoint_behavior')}",
        ]
    if name == "Generic wire and field coverage":
        return [
            f"safe_ingest_rows={metrics.get('safe_ingest_rows')}",
            f"field_visitor_rows={metrics.get('field_visitor_rows')}",
            f"translation_rows={metrics.get('translation_rows')}",
            f"fuzz_seed_count={metrics.get('fuzz_seed_count')}",
        ]
    if name == "Typed semantic waves":
        return [
            f"wave_count={metrics.get('wave_count')}",
            f"wave1_rows={metrics.get('wave1_rows')}",
            f"wave2_rows={metrics.get('wave2_rows')}",
            f"wave3_rows={metrics.get('wave3_rows')}",
            f"wave4_rows={metrics.get('wave4_rows')}",
            f"wave5_rows={metrics.get('wave5_rows')}",
            f"fully_domain_decoded_rows={metrics.get('fully_domain_decoded_rows')}",
        ]
    if name == "Cross-engine and Lattice/Zorn parity":
        language_rows = metrics.get("language_rows", {})
        unity = language_rows.get("unity", {}) if isinstance(language_rows, dict) else {}
        python_rows = language_rows.get("python", {}) if isinstance(language_rows, dict) else {}
        unreal = language_rows.get("unreal", {}) if isinstance(language_rows, dict) else {}
        return [
            f"unity_catalog_rows={unity.get('catalog_rows')}",
            f"unity_deep_rows={unity.get('deep_rows')}",
            f"python_deep_rows={python_rows.get('deep_rows')}",
            f"unreal_deep_rows={unreal.get('deep_rows')}",
            f"unity_csharp_bridge_probe_status={metrics.get('unity_csharp_bridge_probe_status')}",
        ]
    if name == "Evidence and release gates":
        return [
            f"evidence_pack_manifest_status={metrics.get('evidence_pack_manifest_status')}",
            f"release_ready_receipt_status={metrics.get('release_ready_receipt_status')}",
            f"release_ready_receipt_mode={metrics.get('release_ready_receipt_mode')}",
        ]
    return []


def build_report() -> dict[str, Any]:
    audit = run_epic2_audit.build_report()
    criteria = _criterion_index(audit)
    rows: list[dict[str, Any]] = []
    for milestone in MILESTONES:
        criterion = criteria[str(milestone["criterion_name"])]
        rows.append(
            {
                "id": milestone["id"],
                "name": milestone["name"],
                "criterion_name": milestone["criterion_name"],
                "status": criterion["status"],
                "goal_blurb": milestone["goal_blurb"],
                "current_note": criterion["note"],
                "progress_summary": _progress_summary(criterion),
                "exit_focus": list(milestone["exit_focus"]),
                "proof_commands": list(milestone["proof_commands"]),
                "evidence": criterion["evidence"],
            }
        )
    return {
        "schema": "fastdis.epic2.milestones.v1",
        "overall_status": audit["overall_status"],
        "source_audit": "artifacts/reports/epic2/epic2_audit_report.json",
        "milestones": rows,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Epic 2 Milestones",
        "",
        "This generated report turns the Epic 2 milestone blurbs into current, source-backed status rows.",
        "",
        f"- overall_status: `{report['overall_status']}`",
        f"- source_audit: `{report['source_audit']}`",
        "",
        "| Milestone | Status | Current note |",
        "| --- | --- | --- |",
    ]
    for row in report["milestones"]:
        lines.append(f"| {row['name']} | `{row['status']}` | {row['current_note']} |")
    for row in report["milestones"]:
        lines.extend(
            [
                "",
                f"## {row['name']}",
                "",
                "Goal blurb:",
                "",
                row["goal_blurb"],
                "",
                f"- status: `{row['status']}`",
                f"- current_note: {row['current_note']}",
                "- progress_summary:",
            ]
        )
        for item in row["progress_summary"]:
            lines.append(f"  - `{item}`")
        lines.append("- exit_focus:")
        for item in row["exit_focus"]:
            lines.append(f"  - {item}")
        lines.append("- proof_commands:")
        for item in row["proof_commands"]:
            lines.append(f"  - `{item}`")
    lines.append("")
    return "\n".join(lines)


def outputs() -> dict[Path, str]:
    report = build_report()
    return {
        JSON_OUT: json.dumps(report, indent=2, sort_keys=True) + "\n",
        MD_OUT: render_markdown(report) + "\n",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rendered = outputs()
    if args.check:
        stale: list[Path] = []
        for path, content in rendered.items():
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                stale.append(path)
        if stale:
            print("stale Epic 2 milestone artifacts:", file=sys.stderr)
            for path in stale:
                print(f"  {_display_path(path)}", file=sys.stderr)
            return 1
        return 0

    for path, content in rendered.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    print("generated Epic 2 milestone report")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
