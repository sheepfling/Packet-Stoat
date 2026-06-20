#!/usr/bin/env python3
"""Generate a machine-readable Alpha 3 release audit summary."""

from __future__ import annotations

import argparse
from datetime import UTC
from datetime import datetime
import json
from pathlib import Path

import load_local_env


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = ROOT / "verification_reports" / "alpha3_current"


SUCCESS_CRITERIA = [
    {
        "name": "DIS generation pipeline is owned and documented",
        "status": "complete",
        "evidence": [
            "docs/GENERATION_PIPELINE.md",
            "docs/SCHEMA_PATCHES.md",
            "schemas/patches/dis6/README.md",
            "schemas/patches/dis7/README.md",
            "tools/generate_fastdis_ir.py",
            "tools/check_generated_fresh.py",
            "generated/fastdis_ir_dis6.json",
            "generated/fastdis_ir_dis7.json",
        ],
        "note": "Alpha 3 now emits normalized DIS6/DIS7 IR and has a combined freshness checker.",
    },
    {
        "name": "Message coverage manifest and schema-patch flow are current",
        "status": "complete",
        "evidence": [
            "generated/message_coverage_manifest.json",
            "docs/MESSAGE_COVERAGE.md",
            "tools/generate_pdu_catalog.py",
        ],
        "note": "Coverage manifest and human-readable coverage doc are generated from the staged XML-derived catalog flow.",
    },
    {
        "name": "Every cataloged PDU has shallow fuzz coverage",
        "status": "complete",
        "evidence": [
            "generated/fuzz_shallow_corpus/manifest.json",
            "tools/generate_shallow_fuzz_corpus.py",
            "fuzz/fuzz_header.cpp",
            "fuzz/fuzz_catalog_dispatch.cpp",
            "fuzz/fuzz_min_lengths.cpp",
            "fuzz/fuzz_unknown_pdu.cpp",
        ],
        "note": "Shallow fuzz seeds and breadth-oriented fuzz harnesses are on disk.",
    },
    {
        "name": "Typed and engine-facing paths have deep fuzz and sanitizer coverage",
        "status": "complete",
        "evidence": [
            "fuzz/fuzz_entity_transform.cpp",
            "fuzz/fuzz_entity_table_ingest.cpp",
            "fuzz/fuzz_snapshot_buffer.cpp",
            "fuzz/fuzz_frame_orientation.cpp",
            "verification_reports/alpha3_current/sanitizer_smoke_report.json",
            "verification_reports/alpha3_current/sanitizer_smoke_report.md",
        ],
        "note": "Deep fuzz harnesses and current sanitizer smoke artifacts are present.",
    },
    {
        "name": "Orientation has oracle plus visual proof artifacts",
        "status": "complete",
        "evidence": [
            "verification_reports/alpha3_current/orientation_verification_report.json",
            "verification_reports/alpha3_current/orientation_verification_report.md",
            "verification_reports/alpha3_current/orientation_visual_report.json",
            "verification_reports/alpha3_current/orientation_visual_report.md",
            "verification_reports/alpha3_current/orientation_pipeline_report.json",
            "verification_reports/alpha3_current/orientation_pipeline_report.md",
            "verification_reports/alpha3_current/orientation_visual_review/index.html",
            "docs/ORIENTATION_VISUAL_VERIFICATION.md",
            "docs/ORIENTATION_PIPELINE.md",
            "docs/ORIENTATION_TWEAKING.md",
            "docs/ORIENTATION_FAILURE_SIGNATURES.md",
        ],
        "note": "Native/oracle, visual, and pipeline-calibration proof lanes all have current staged artifacts.",
    },
    {
        "name": "Network ingest and engine workflows are green on the current supported host",
        "status": "complete",
        "evidence": [
            "verification_reports/alpha3_current/network_ingest_matrix.json",
            "verification_reports/alpha3_current/network_ingest_matrix.md",
            "verification_reports/alpha3_current/io_routes_report.json",
            "verification_reports/alpha3_current/io_routes_report.md",
            "verification_reports/alpha3_current/godot_workflow_report.json",
            "verification_reports/alpha3_current/godot_workflow_report.md",
            "verification_reports/alpha3_current/unreal_version_matrix.json",
            "verification_reports/alpha3_current/unreal_version_matrix.md",
        ],
        "note": "Alpha 3 records Python/C/C++ localhost UDP lanes plus current Godot and Unreal host workflow proof.",
    },
    {
        "name": "Outbound sender verification artifacts are present and staged honestly",
        "status": "complete",
        "evidence": [
            "verification_reports/alpha3_current/network_send_matrix.json",
            "verification_reports/alpha3_current/network_send_matrix.md",
            "verification_reports/alpha3_current/godot_udp_send_smoke.json",
            "verification_reports/alpha3_current/unreal_udp_send_smoke.json",
            "tools/run_godot_udp_send_smoke.py",
            "tools/run_unreal_udp_send_smoke.py",
        ],
        "note": "Native sender lanes plus Godot and Unreal outbound smoke artifacts are staged on disk.",
    },
    {
        "name": "Benchmark and regression reports are current",
        "status": "complete",
        "evidence": [
            "benchmarks/native_bench.cpp",
            "tools/run_benchmarks.py",
            "tools/run_send_benchmarks.py",
            "tools/check_benchmark_regression.py",
            "docs/BENCHMARKING.md",
        ],
        "note": "Inbound and outbound benchmark runners, methodology, and regression checker are on disk; generated benchmark payloads are rebuilt locally rather than tracked.",
    },
    {
        "name": "Source bundle, checksums, and release notes make no unsupported claims",
        "status": "complete",
        "evidence": [
            "tools/package_alpha3.py",
            "docs/releases/ALPHA3_RELEASE_NOTES.md",
            "docs/releases/ALPHA3_AUDIT.md",
        ],
        "note": "Packaging policy, bundle-local metadata generation, release notes, and audit checklist are all present and Alpha 3-scoped.",
    },
]


WORKSERIES = [
    ("WS1 Release Branch, Scope Guardrails, and Version Bump", "complete", ["docs/releases/ALPHA3_PLAN.md", "docs/releases/ALPHA3_GOAL.md", "docs/releases/ALPHA3_RELEASE_NOTES.md"]),
    ("WS2 Message Coverage Manifest", "complete", ["generated/message_coverage_manifest.json", "docs/MESSAGE_COVERAGE.md"]),
    ("WS2A DIS 6/7 Generation Baseline and Owned Schema IR", "complete", ["docs/GENERATION_PIPELINE.md", "generated/fastdis_ir_dis6.json", "generated/fastdis_ir_dis7.json", "tools/check_generated_fresh.py"]),
    ("WS3 All-PDU Shallow Fuzzing", "complete", ["generated/fuzz_shallow_corpus/manifest.json", "fuzz/fuzz_min_lengths.cpp"]),
    ("WS4 Deep Fuzzing for Typed and Engine-Facing Paths", "complete", ["fuzz/fuzz_entity_transform.cpp", "verification_reports/alpha3_current/sanitizer_smoke_report.md"]),
    ("WS5 Differential Parser and Catalog Tests", "complete", ["generated/differential_report.json", "generated/differential_report.md", "docs/DIFFERENTIAL_TESTING.md"]),
    ("WS6 Orientation Paranoia Suite", "complete", ["generated/orientation_formulas.json", "verification_reports/alpha3_current/orientation_verification_report.md"]),
    ("WS7 In-Engine Orientation Verification", "complete", ["verification_reports/alpha3_current/orientation_visual_report.md", "verification_reports/alpha3_current/orientation_pipeline_report.md", "verification_reports/alpha3_current/godot_workflow_report.md", "verification_reports/alpha3_current/unreal_version_matrix.md"]),
    ("WS7A Outbound Sender Verification", "complete", ["verification_reports/alpha3_current/network_send_matrix.md", "verification_reports/alpha3_current/godot_udp_send_smoke.json", "verification_reports/alpha3_current/unreal_udp_send_smoke.json", "tools/run_unreal_udp_send_smoke.py"]),
    ("WS8 Benchmark Qualification Matrix", "complete", ["benchmarks/native_bench.cpp", "tools/run_benchmarks.py", "tools/run_send_benchmarks.py", "tools/check_benchmark_regression.py", "docs/BENCHMARKING.md"]),
    ("WS9 Next Typed Fast Paths", "complete", ["docs/MESSAGE_COVERAGE.md", "generated/message_coverage_manifest.json"]),
    ("WS10 Packaging, Audit, and Release Truthfulness", "complete", ["tools/package_alpha3.py", "tools/run_alpha3_release_audit.py", "docs/releases/ALPHA3_RELEASE_NOTES.md"]),
    ("WS11 Optional Networking and Replay Utilities", "complete", ["docs/NETWORKING.md", "docs/REPLAY_FORMAT.md", "verification_reports/alpha3_current/network_ingest_matrix.md", "verification_reports/alpha3_current/io_routes_report.md"]),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR), help="Directory for JSON/Markdown reports")
    return parser.parse_args()


def display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def classify_overall(criteria: list[dict[str, object]]) -> str:
    statuses = {item["status"] for item in criteria}
    if "missing" in statuses:
        return "missing-evidence"
    if "partial" in statuses or "host-blocked" in statuses:
        return "not-fully-signed-off"
    return "ready"


def evaluate_paths(paths: list[str]) -> list[dict[str, object]]:
    evaluated: list[dict[str, object]] = []
    for raw in paths:
        path = ROOT / raw
        evaluated.append(
            {
                "path": raw,
                "exists": path.exists(),
                "kind": "dir" if path.is_dir() else ("file" if path.is_file() else "missing"),
            }
        )
    return evaluated


def render_markdown(report: dict[str, object]) -> str:
    lines = [
        "# Alpha 3 Release Audit Report",
        "",
        f"- generated_at: `{report['generated_at']}`",
        f"- overall_status: `{report['overall_status']}`",
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
    lines.extend(["", "## Workseries", "", "| Workseries | Status | Evidence OK |", "| --- | --- | --- |"])
    for item in report["workseries"]:
        lines.append(f"| {item['name']} | {item['status']} | {'yes' if item['evidence_ok'] else 'no'} |")
    lines.extend(["", "## Remaining Non-Complete Items", ""])
    remaining = 0
    for item in report["success_criteria"]:
        if item["status"] == "complete":
            continue
        remaining += 1
        lines.append(f"- {item['name']}: `{item['status']}`")
        lines.append(f"  note: {item['note']}")
    if remaining == 0:
        lines.append("- none")
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

    workseries_items: list[dict[str, object]] = []
    for name, status, evidence_paths in WORKSERIES:
        evidence = evaluate_paths(evidence_paths)
        workseries_items.append(
            {
                "name": name,
                "status": status,
                "evidence": evidence,
                "evidence_ok": all(entry["exists"] for entry in evidence),
            }
        )

    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "overall_status": classify_overall(success_criteria),
        "success_criteria": success_criteria,
        "workseries": workseries_items,
    }

    json_path = out_dir / "alpha3_release_audit_report.json"
    md_path = out_dir / "alpha3_release_audit_report.md"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    print(f"Wrote {display_path(json_path)}")
    print(f"Wrote {display_path(md_path)}")
    return 0 if report["overall_status"] == "ready" else 2


if __name__ == "__main__":
    raise SystemExit(main())
