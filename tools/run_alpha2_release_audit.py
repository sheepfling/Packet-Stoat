#!/usr/bin/env python3
"""Generate a machine-readable Alpha 2 release audit summary."""

from __future__ import annotations

import argparse
from datetime import UTC
from datetime import datetime
import json
from pathlib import Path

import evidence_layout
import load_local_env


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = evidence_layout.ALPHA2_SAMPLE_DIR
DEFAULT_SIGNOFF_MATRIX = "artifacts/verification_reports/alpha2_sample/alpha2_signoff_matrix.json"


SUCCESS_CRITERIA = [
    {
        "name": "C ABI remains stable unless a clearly justified ABI v9 is needed",
        "status": "complete",
        "evidence": [
            "include/fastdis/fastdis.h",
            "docs/API_STABILITY.md",
            "docs/ABI.md",
        ],
        "note": "Current ABI marker remains 8; snapshot expansion stayed additive.",
    },
    {
        "name": "C++ RAII layer remains header-only and first-class",
        "status": "complete",
        "evidence": [
            "include/fastdis/fastdis.hpp",
            "docs/CXX_RAII.md",
            "tests/native/test_cpp_raii.cpp",
        ],
        "note": "Builder/config surface, span overloads, and scoped snapshot helpers are on disk.",
    },
    {
        "name": "Unreal sample plugin builds in a real Unreal project",
        "status": "complete",
        "evidence": [
            "packages/unreal/FastDis/",
            "packages/unreal/FastDisDemo/",
            "artifacts/verification_reports/alpha2_sample/unreal_version_matrix.md",
            "artifacts/verification_reports/alpha2_sample/unreal_host_compat_report.md",
            "artifacts/verification_reports/alpha2_sample/alpha2_signoff_matrix.md",
        ],
        "note": "Supported Alpha 2 Unreal lanes 5.7 and 5.8 are proven on this host. Unreal 5.6 is demoted to optional compatibility evidence rather than a signoff lane.",
    },
    {
        "name": "Godot GDExtension sample builds against godot-cpp",
        "status": "complete",
        "evidence": [
            "packages/godot/fastdis_gdextension/",
            "packages/godot/fastdis_demo/",
            "artifacts/verification_reports/alpha2_sample/godot_workflow_report.md",
        ],
        "note": "Checked-in host-ready report shows doctor/build/verify/demo passed.",
    },
    {
        "name": "Frame transform tests cover ECEF -> ENU -> Unreal/Godot mappings",
        "status": "complete",
        "evidence": [
            "include/fastdis/fastdis_frames.hpp",
            "tests/native/test_frames.cpp",
            "docs/FRAME_TRANSFORMS.md",
        ],
        "note": "Fixtures cover equator, Houston/Ellington-style, mid-latitude, and near-pole origins.",
    },
    {
        "name": "Unreal and Godot orientation harnesses verify engine basis vectors against shared fixtures before orientation is advertised beyond experimental",
        "status": "complete",
        "evidence": [
            "docs/ENGINE_ORIENTATION_VERIFICATION.md",
            "artifacts/verification_reports/alpha2_sample/orientation_runtime_report.md",
            "artifacts/verification_reports/alpha2_sample/orientation_visual_report.md",
            "artifacts/verification_reports/alpha2_sample/alpha2_signoff_matrix.md",
        ],
        "note": "Bundled macOS host-ready runtime and visual reports show passing Unreal 5.7, Unreal 5.8, and Godot lanes against the shared fixture contract.",
    },
    {
        "name": "Snapshot handoff has a clear busy/drop/backpressure story",
        "status": "complete",
        "evidence": [
            "include/fastdis/fastdis.h",
            "include/fastdis/fastdis.hpp",
            "docs/DOUBLE_BUFFER_SNAPSHOTS.md",
        ],
        "note": "Double/triple-slot semantics and pressure stats are documented and tested.",
    },
    {
        "name": "Benchmark report compares Alpha 1 vs Alpha 2 paths",
        "status": "complete",
        "evidence": [
            "benchmarks/native_bench.cpp",
            "tools/run_benchmarks.py",
            "tools/check_benchmark_regression.py",
            "docs/BENCHMARKING.md",
        ],
        "note": "Benchmark harnesses, methodology, and regression checks are on disk; generated outputs are rebuilt locally rather than tracked.",
    },
    {
        "name": "Source bundle includes docs, examples, checksums, and release notes",
        "status": "complete",
        "evidence": [
            "tools/package_alpha2.py",
            "docs/releases/ALPHA2_RELEASE_NOTES.md",
        ],
        "note": "Bundle metadata is generated into the packaged archive rather than tracked at repo root.",
    },
]


WORKSERIES = [
    ("WS1 Release Branch and API Hygiene", "complete", ["docs/releases/ALPHA2_PLAN.md", "docs/API_STABILITY.md", "artifacts/verification_reports/alpha2_sample/export_check_report.md"]),
    ("WS2 Frame Transform Correctness", "complete", ["docs/FRAME_TRANSFORMS.md", "tests/native/test_frames.cpp"]),
    ("WS3 Snapshot Buffer Hardening", "complete", ["docs/DOUBLE_BUFFER_SNAPSHOTS.md", "tests/native/test_c_api.cpp"]),
    ("WS4 C++ RAII Quality of Life", "complete", ["docs/CXX_RAII.md", "examples/cpp/raii_snapshot_buffer.cpp"]),
    ("WS5 Unreal Adapter Runnable Sample", "complete", ["artifacts/verification_reports/alpha2_sample/unreal_version_matrix.md", "artifacts/verification_reports/alpha2_sample/unreal_host_compat_report.md"]),
    ("WS6 Godot GDExtension Runnable Sample", "complete", ["artifacts/verification_reports/alpha2_sample/godot_workflow_report.md"]),
    ("WS7 Replay and Benchmark Expansion", "complete", ["benchmarks/native_bench.cpp", "tools/run_benchmarks.py", "tools/check_benchmark_regression.py", "docs/BENCHMARKING.md"]),
    ("WS8 Native Ingress Helpers", "complete", ["examples/common/replay_reader.hpp", "examples/common/udp_receiver.hpp"]),
    ("WS9 Fuzzing and Malformed Packet Hardening", "complete", ["fuzz/fuzz_header.cpp", "docs/HARDENING.md"]),
    ("WS10 Alpha 2 Packaging", "complete", ["tools/package_alpha2.py", "docs/releases/ALPHA2_RELEASE_NOTES.md"]),
    ("WS11 Orientation Convention Verification", "complete", ["docs/ORIENTATION_VERIFICATION.md", "artifacts/verification_reports/alpha2_sample/orientation_verification_report.md"]),
    ("WS12 In-Engine Orientation Verification", "complete", ["artifacts/verification_reports/alpha2_sample/orientation_runtime_report.md", "artifacts/verification_reports/alpha2_sample/orientation_visual_report.md", "artifacts/verification_reports/alpha2_sample/alpha2_signoff_matrix.md"]),
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


READY_SIGNOFF_STATUSES = {"host-ready", "cross-host-ready"}


def classify_overall(criteria: list[dict[str, object]], signoff_matrix_status: str) -> str:
    statuses = {item["status"] for item in criteria}
    if "missing" in statuses:
        return "missing-evidence"
    if signoff_matrix_status not in READY_SIGNOFF_STATUSES:
        return "not-fully-signed-off"
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


def load_signoff_status(path: Path) -> str:
    if not path.exists():
        return "missing"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return "invalid"
    value = payload.get("overall_status")
    return str(value) if value is not None else "missing-status"


def render_markdown(report: dict[str, object]) -> str:
    lines = [
        "# Alpha 2 Release Audit Report",
        "",
        f"- generated_at: `{report['generated_at']}`",
        f"- overall_status: `{report['overall_status']}`",
        f"- signoff_matrix_status: `{report['signoff_matrix_status']}`",
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
    for item in report["success_criteria"]:
        if item["status"] == "complete":
            continue
        lines.append(f"- {item['name']}: `{item['status']}`")
        lines.append(f"  note: {item['note']}")
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

    signoff_matrix_status = load_signoff_status(ROOT / DEFAULT_SIGNOFF_MATRIX)
    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "overall_status": classify_overall(success_criteria, signoff_matrix_status),
        "signoff_matrix_status": signoff_matrix_status,
        "success_criteria": success_criteria,
        "workseries": workseries_items,
    }

    json_path = out_dir / "alpha2_release_audit_report.json"
    md_path = out_dir / "alpha2_release_audit_report.md"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    print(f"Wrote {display_path(json_path)}")
    print(f"Wrote {display_path(md_path)}")
    return 0 if report["overall_status"] == "ready" else 2


if __name__ == "__main__":
    raise SystemExit(main())
