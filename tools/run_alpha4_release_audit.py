#!/usr/bin/env python3
"""Generate a machine-readable Alpha 4 release audit summary."""

from __future__ import annotations

import argparse
from datetime import UTC
from datetime import datetime
import json
from pathlib import Path
from typing import Any

import load_local_env


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = ROOT / "verification_reports" / "alpha4" / "lattice"


SUCCESS_CRITERIA = [
    {
        "name": "Alpha 4 bridge architecture and scope guardrails are documented",
        "status": "complete",
        "evidence": [
            "docs/releases/ALPHA4_PLAN.md",
            "docs/releases/ALPHA4_GOAL.md",
            "docs/ROADMAP.md",
            "docs/LATTICE_INTEGRATION.md",
            "docs/LATTICE_LAB.md",
        ],
        "note": "Alpha 4 remains outbound first, ingress later, with the native core kept generic.",
    },
    {
        "name": "Reference stack, compatibility tiers, and mocked-vs-real boundaries are explicit",
        "status": "complete",
        "evidence": [
            "docs/LATTICE_REFERENCE_STACK.md",
            "docs/LATTICE_MOCKING.md",
            "docs/LATTICE_DIS_BRIDGE_PLAN.md",
            "docs/LATTICE_ENTITY_MAPPING.md",
        ],
        "note": "The repo states clearly what is behavior-compatible, shape-compatible, and still requires real sandbox access.",
    },
    {
        "name": "Canonical entity bridge exists as a generic fastdis surface",
        "status": "complete",
        "evidence": [
            "src/fastdis/lattice.py",
            "src/fastdis/__init__.py",
            "integrations/lattice/src/packet_stoat_lattice/canonical.py",
            "integrations/lattice/examples/dis_entity_fixture.json",
        ],
        "note": "Canonical entity helpers are outside the hot-path ABI and bridge DIS/native snapshots to adapter-facing payloads.",
    },
    {
        "name": "Mockable publisher backends and local shim seams exist",
        "status": "complete",
        "evidence": [
            "integrations/lattice/src/packet_stoat_lattice/publishers.py",
            "integrations/lattice/src/packet_stoat_lattice/mock_shim.py",
            "integrations/lattice/README.md",
            "tests/test_lattice_mock.py",
            "tests/test_lattice_adapter_scaffold.py",
        ],
        "note": "JSONL, local HTTP mock, and credential-gated real backend stub exist beside the local shim store/stream seams.",
    },
    {
        "name": "DIS/latest-state to canonical entity conversion works without a real SDK",
        "status": "complete",
        "evidence": [
            "src/fastdis/lattice.py",
            "src/fastdis/tools/lattice_shim.py",
            "tests/test_lattice_shim_tool.py",
        ],
        "note": "The shim supports native snapshot conversion when available and a Python replay fallback for DIS 7 Entity State return-lane proof.",
    },
    {
        "name": "Deterministic identity mapping and Entity State egress are implemented",
        "status": "complete",
        "evidence": [
            "src/fastdis/lattice.py",
            "integrations/lattice/src/packet_stoat_lattice/lattice_to_dis.py",
            "tests/test_lattice_mock.py",
            "tests/test_lattice_adapter_scaffold.py",
        ],
        "note": "Canonical entities map to stable Packet-Stoat entity IDs and back into DIS Entity State packets.",
    },
    {
        "name": "Operator workflow, reports, and bounded object/task lanes are runnable from the current tree",
        "status": "complete",
        "evidence": [
            "tools/lattice_workflow.py",
            "verification_reports/alpha4/lattice/dis_to_shim/dis_to_shim_report.json",
            "verification_reports/alpha4/lattice/shim_to_dis/shim_to_dis_report.json",
            "verification_reports/alpha4/lattice/lab_state/lab_state_report.json",
            "verification_reports/alpha4/lattice/alpha4_lattice_report.json",
        ],
        "note": "The current workflow regenerates all operator-facing Alpha 4 reports locally instead of relying on tracked artifacts.",
    },
    {
        "name": "Unreal, Godot, and Open-DIS-friendly verification artifacts are present and honestly scoped",
        "status": "complete",
        "evidence": [
            "verification_reports/alpha4/lattice/shim_to_dis/shim_to_dis.fastdispkt",
            "verification_reports/alpha4/lattice/shim_to_dis/canonical_entities.json",
            "verification_reports/alpha4/lattice/alpha4_lattice_report.md",
            "docs/releases/ALPHA4_RELEASE_NOTES.md",
        ],
        "note": "The replay artifact is friendly to replay/UDP consumers including Open-DIS and engine-facing test harnesses; this is not yet a real Lattice runtime integration inside Unreal or Godot.",
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR), help="Directory holding Alpha 4 generated reports")
    return parser.parse_args()


def display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def evaluate_paths(paths: list[str]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for raw in paths:
        path = ROOT / raw
        rows.append(
            {
                "path": raw,
                "exists": path.exists(),
                "kind": "dir" if path.is_dir() else ("file" if path.is_file() else "missing"),
            }
        )
    return rows


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def audit_generated_outputs(out_dir: Path) -> dict[str, Any]:
    dis_report_path = out_dir / "dis_to_shim" / "dis_to_shim_report.json"
    shim_report_path = out_dir / "shim_to_dis" / "shim_to_dis_report.json"
    lab_report_path = out_dir / "lab_state" / "lab_state_report.json"
    summary_path = out_dir / "alpha4_lattice_report.json"
    replay_path = out_dir / "shim_to_dis" / "shim_to_dis.fastdispkt"
    canonical_path = out_dir / "shim_to_dis" / "canonical_entities.json"

    report: dict[str, Any] = {
        "generated_outputs_ready": False,
        "issues": [],
        "consumer_compatibility": {},
    }
    required = [dis_report_path, shim_report_path, lab_report_path, summary_path, replay_path, canonical_path]
    missing = [display_path(path) for path in required if not path.exists()]
    if missing:
        report["issues"].append({"kind": "missing_outputs", "paths": missing})
        return report

    from fastdis import parse_header
    from fastdis.replay import read_v1_packets

    dis_report = load_json(dis_report_path)
    shim_report = load_json(shim_report_path)
    lab_report = load_json(lab_report_path)
    summary_report = load_json(summary_path)
    packets = read_v1_packets(replay_path)
    headers = [parse_header(packet, strict=True) for packet in packets]
    canonical_payload = load_json(canonical_path)
    canonical_entities = canonical_payload.get("entities", []) if isinstance(canonical_payload, dict) else canonical_payload

    if int(dis_report.get("accepted", 0)) < 1:
        report["issues"].append({"kind": "dis_to_shim_acceptance", "detail": dis_report})
    if int(shim_report.get("packet_count", 0)) != len(packets):
        report["issues"].append({"kind": "shim_to_dis_packet_count", "detail": shim_report})
    if int(lab_report.get("object_count", 0)) < 1 or int(lab_report.get("task_count", 0)) < 1:
        report["issues"].append({"kind": "lab_state_counts", "detail": lab_report})
    if summary_report.get("overall_status") != "ready":
        report["issues"].append({"kind": "summary_not_ready", "detail": summary_report})
    if len(canonical_entities) != int(shim_report.get("exportable_entity_count", 0)):
        report["issues"].append(
            {
                "kind": "canonical_entity_count_mismatch",
                "canonical_entities": len(canonical_entities),
                "exportable_entity_count": int(shim_report.get("exportable_entity_count", 0)),
            }
        )
    if any(header is None or header.pdu_type != 1 or header.protocol_family != 1 or header.length < 144 for header in headers):
        report["issues"].append({"kind": "replay_packet_shape", "packet_count": len(headers)})

    report["generated_outputs_ready"] = not report["issues"]
    report["consumer_compatibility"] = {
        "open_dis": {
            "status": "friendly" if not report["issues"] else "incomplete",
            "reason": "Replay output is .fastdispkt carrying DIS Entity State PDUs with standard 12-byte headers and 144-byte fixed bodies.",
        },
        "unreal": {
            "status": "friendly" if replay_path.exists() and canonical_path.exists() else "incomplete",
            "reason": "Artifacts are suitable for replay/UDP-fed engine consumers, but Alpha 4 does not claim a live Lattice runtime inside Unreal.",
        },
        "godot": {
            "status": "friendly" if replay_path.exists() and canonical_path.exists() else "incomplete",
            "reason": "Artifacts are suitable for replay/UDP-fed engine consumers, but Alpha 4 does not claim a live Lattice runtime inside Godot.",
        },
    }
    return report


def classify_overall(criteria: list[dict[str, object]], generated: dict[str, Any]) -> str:
    if generated.get("issues"):
        return "missing-evidence"
    if any(not item["evidence_ok"] for item in criteria):
        return "missing-evidence"
    return "ready"


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Alpha 4 Release Audit Report",
        "",
        f"- generated_at: `{report['generated_at']}`",
        f"- overall_status: `{report['overall_status']}`",
        f"- out_dir: `{report['out_dir']}`",
        "",
        "## Success Criteria",
        "",
        "| Criterion | Status | Evidence OK | Notes |",
        "| --- | --- | --- | --- |",
    ]
    for item in report["success_criteria"]:
        lines.append(
            f"| {item['name']} | {item['status']} | {'yes' if item['evidence_ok'] else 'no'} | {item['note']} |"
        )
    lines.extend(["", "## Generated Output Audit", ""])
    generated = report["generated_output_audit"]
    lines.append(f"- generated_outputs_ready: `{generated['generated_outputs_ready']}`")
    for name, compat in generated["consumer_compatibility"].items():
        lines.append(f"- {name}: `{compat['status']}` - {compat['reason']}")
    if generated["issues"]:
        lines.extend(["", "## Issues", ""])
        for issue in generated["issues"]:
            lines.append(f"- `{issue['kind']}`: `{json.dumps(issue, sort_keys=True)}`")
    else:
        lines.extend(["", "## Issues", "", "- none"])
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    load_local_env.load()
    args = parse_args()
    out_dir = Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    success_criteria: list[dict[str, object]] = []
    for item in SUCCESS_CRITERIA:
        evidence = evaluate_paths(item["evidence"])
        success_criteria.append(
            {
                **item,
                "evidence": evidence,
                "evidence_ok": all(entry["exists"] for entry in evidence),
            }
        )

    generated_output_audit = audit_generated_outputs(out_dir)
    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "out_dir": display_path(out_dir),
        "overall_status": classify_overall(success_criteria, generated_output_audit),
        "success_criteria": success_criteria,
        "generated_output_audit": generated_output_audit,
    }

    json_path = out_dir / "alpha4_release_audit_report.json"
    md_path = out_dir / "alpha4_release_audit_report.md"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    print(f"Wrote {display_path(json_path)}")
    print(f"Wrote {display_path(md_path)}")
    return 0 if report["overall_status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
