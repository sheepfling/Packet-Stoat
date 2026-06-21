#!/usr/bin/env python3
"""Generate the Alpha5 end-to-end integration proof matrix."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path
import platform
import sys
from typing import Any

from artifacts import REPORTS_DIR, rel


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = REPORTS_DIR


def _exists(path: str) -> bool:
    return (ROOT / path).exists()


def _status(required_paths: tuple[str, ...], *, gated: bool = False, partial: bool = False) -> str:
    if gated:
        return "credential_or_host_gated"
    if partial:
        return "partial"
    return "ready" if all(_exists(path) for path in required_paths) else "missing_artifact"


def matrix_rows() -> list[dict[str, Any]]:
    return [
        {
            "area": "DIS 6/7 catalog",
            "capability": "Standard PDU backbone, safe ingest rows, typed envelopes, semantic entry points, logging descriptors",
            "surfaces": ["python", "generated", "unreal", "godot", "unity"],
            "status": _status(
                (
                    "tools/generate_pdu_coverage.py",
                    "tools/generate_typed_pdu_parsers.py",
                    "tools/generate_semantic_pdu_parsers.py",
                    "tools/generate_pdu_log_catalog.py",
                    "docs/PDU_COVERAGE.md",
                    "docs/PDU_LOGGING_COVERAGE.md",
                )
            ),
            "confirmation": "141/141 standard versioned PDU rows are represented in generated coverage, typed envelope, semantic entry point, and logging descriptor surfaces.",
            "commands": [
                "python tools/check_generated_fresh.py",
                "python -m fastdis logging check",
                "python -m pytest tests/test_pdu_coverage_manifest.py tests/test_typed_pdu_parsers.py tests/test_semantic_pdu_parsers.py tests/test_pdu_logging.py",
            ],
            "gaps": [],
        },
        {
            "area": "DIS 6/7 ingress",
            "capability": "Header-safe packet recognition, Entity State extraction, replay/UDP receive, JSON inspection",
            "surfaces": ["python", "c", "cpp", "unreal", "godot"],
            "status": _status(("tools/run_network_ingest_matrix.py", "src/fastdis/tools/recv.py", "examples/c/udp_burst.c", "examples/cpp/udp_burst.cpp")),
            "confirmation": "Python/C/C++ localhost UDP receive routes are scripted; Unreal/Godot live UDP routes are represented in the ingest matrix and gated by local engine availability.",
            "commands": [
                "python tools/run_network_ingest_matrix.py --out-dir build/reports",
                "python -m pytest tests/test_network_ingest_matrix.py tests/test_python_io_tools.py tests/test_pdu_json_roundtrip.py",
            ],
            "gaps": ["Unity live UDP ingress should be promoted from package/runtime tests into the shared ingest matrix."],
        },
        {
            "area": "DIS 6/7 egress",
            "capability": "Entity State packet construction, replay send, UDP send, JSON/replay round-trip",
            "surfaces": ["python", "c", "cpp", "unreal", "godot", "lattice_lab"],
            "status": _status(("tools/run_network_send_matrix.py", "src/fastdis/tools/send_entity.py", "examples/c/udp_send.c", "examples/cpp/udp_send.cpp")),
            "confirmation": "Python/C/C++ localhost UDP send routes are scripted; Unreal/Godot outbound smoke tools exist; Lattice Lab has lattice-to-DIS conversion tests.",
            "commands": [
                "python tools/run_network_send_matrix.py --out-dir build/reports",
                "python tools/run_unreal_udp_send_smoke.py --dry-run",
                "python tools/run_godot_udp_send_smoke.py --dry-run",
                "python -m pytest tests/test_network_send_matrix.py tests/test_replay_json_roundtrip.py tests/test_lattice_adapter_scaffold.py",
            ],
            "gaps": ["Unity outbound DIS egress is not yet represented as a shared send matrix row."],
        },
        {
            "area": "Filtering",
            "capability": "Version, PDU type, protocol family, exercise ID, entity ID, force ID, sampling and downsampling filters",
            "surfaces": ["python", "c", "cpp", "native"],
            "status": _status(("include/fastdis/fastdis.h", "src/fastdis/_fallback.py", "src/native/fastdis_core.cpp")),
            "confirmation": "Python scan tests and native ctypes/C API tests exercise filter configuration and early packet rejection.",
            "commands": [
                "python -m pytest tests/test_scan.py tests/test_native_ctypes.py",
                "ctest --test-dir build/cmake/host --build-config Release --output-on-failure",
            ],
            "gaps": ["Add explicit engine UI tests that prove filter profile changes are reflected in monitor/log output."],
        },
        {
            "area": "Buffering",
            "capability": "Entity table, changed/stale snapshots, snapshot buffer publish/acquire/release, pressure stats",
            "surfaces": ["native", "c", "cpp", "unreal", "godot"],
            "status": _status(("include/fastdis/fastdis.h", "include/fastdis/fastdis.hpp", "examples/c/snapshot_buffer.c", "examples/cpp/raii_snapshot_buffer.cpp")),
            "confirmation": "Native C/C++ tests and examples cover snapshot buffer APIs; engine examples consume the latest-state snapshot contract.",
            "commands": [
                "python -m pytest tests/test_native_ctypes.py",
                "ctest --test-dir build/cmake/host --build-config Release --output-on-failure",
            ],
            "gaps": ["Add an engine stress test that asserts dropped snapshot counters and monitor summaries under artificial overload."],
        },
        {
            "area": "Robustness",
            "capability": "Malformed packet handling, length checks, unknown PDU handling, shallow fuzz corpus, generated freshness",
            "surfaces": ["python", "native", "generated"],
            "status": _status(("tools/generate_shallow_fuzz_corpus.py", "fuzz/fuzz_min_lengths.cpp", "tests/test_shallow_fuzz_corpus.py")),
            "confirmation": "Malformed headers and all cataloged shallow seed packets are covered; unknown/schema-gap PDUs are routed to generic events rather than silently disappearing.",
            "commands": [
                "python tools/generate_shallow_fuzz_corpus.py --check",
                "python -m pytest tests/test_shallow_fuzz_corpus.py tests/test_header.py tests/test_pdu_logging.py",
            ],
            "gaps": ["Run sanitizer/fuzzer jobs as an explicit release-ready lane before publishing binaries."],
        },
        {
            "area": "Dead reckoning",
            "capability": "Parse Entity State dead-reckoning algorithm, parameters, acceleration, and angular velocity",
            "surfaces": ["native", "python_ctypes"],
            "status": _status(("include/fastdis/fastdis.h", "src/native/fastdis_core.cpp", "tests/test_native_ctypes.py"), partial=True),
            "confirmation": "Dead-reckoning fields are parsed and exposed through the native/Python Entity State surfaces.",
            "commands": [
                "python -m pytest tests/test_native_ctypes.py",
                "ctest --test-dir build/cmake/host --build-config Release --output-on-failure",
            ],
            "gaps": [
                "No predictive extrapolation oracle yet.",
                "No Unreal/Godot/Unity dead-reckoning runtime verification scene yet.",
                "No dead-reckoning log-event trigger beyond diagnostic code reservation yet.",
            ],
        },
        {
            "area": "Logging",
            "capability": "Generated 141-row PDU log descriptors, human summaries, JSONL events, engine descriptor tables",
            "surfaces": ["python", "unreal", "godot", "unity"],
            "status": _status(
                (
                    "src/fastdis/pdu_logging.py",
                    "src/fastdis/tools/logging_check.py",
                    "examples/unreal/FastDis/Source/FastDisUnreal/Public/FastDisPduLogCatalog.h",
                    "examples/godot/fastdis_demo/addons/fastdis/fastdis_pdu_log_catalog.gd",
                    "integrations/unity/com.sheepfling.fastdis/Runtime/Logging/FastDisPduLogCatalog.cs",
                )
            ),
            "confirmation": "The generated logging contract covers all 141 DIS 6/7 versioned rows and is gated by dev_check.",
            "commands": [
                "python -m fastdis logging check",
                "python -m pytest tests/test_pdu_logging.py",
            ],
            "gaps": ["Thin runtime sinks still need to consume the generated descriptors inside active Unreal/Godot/Unity monitor panels."],
        },
        {
            "area": "Engine example projects",
            "capability": "Runnable Unreal, Godot, and Unity sample/plugin projects with doctor/build/verify entry points",
            "surfaces": ["unreal", "godot", "unity"],
            "status": _status(
                (
                    "examples/unreal/FastDis/FastDis.uplugin",
                    "examples/godot/fastdis_demo/project.godot",
                    "integrations/unity/com.sheepfling.fastdis/package.json",
                    "tools/unreal_workflow.py",
                    "tools/godot_workflow.py",
                    "tools/unity_workflow.py",
                )
            ),
            "confirmation": "Example projects and workflow wrappers exist; runtime pass/fail depends on local engine installs and license state.",
            "commands": [
                "python tools/unreal_workflow.py full --engine-version 5.8",
                "python tools/godot_workflow.py full",
                "python tools/unity_workflow.py runtime-verify --unity-version 6000.5",
                "python tools/dev_check.py --engine-doctors",
            ],
            "gaps": [
                "Unity runtime verification can be blocked by Editor licensing/batchmode activation.",
                "Unreal/Godot runtime checks are host-install dependent.",
            ],
        },
    ]


def overall_status(rows: list[dict[str, Any]]) -> str:
    if any(row["status"] == "missing_artifact" for row in rows):
        return "fail"
    if any(row["status"] in {"partial", "credential_or_host_gated"} for row in rows):
        return "partial"
    return "ready"


def build_report() -> dict[str, Any]:
    rows = matrix_rows()
    return {
        "schema": "fastdis.alpha5_integration_matrix.v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "host": {
            "platform": platform.platform(),
            "python": sys.version.split()[0],
        },
        "overall_status": overall_status(rows),
        "summary": {
            "rows": len(rows),
            "ready": sum(1 for row in rows if row["status"] == "ready"),
            "partial": sum(1 for row in rows if row["status"] == "partial"),
            "credential_or_host_gated": sum(1 for row in rows if row["status"] == "credential_or_host_gated"),
            "missing_artifact": sum(1 for row in rows if row["status"] == "missing_artifact"),
        },
        "rows": rows,
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Alpha5 Integration Proof Matrix",
        "",
        f"- generated_at: `{report['generated_at']}`",
        f"- overall_status: `{report['overall_status']}`",
        f"- rows: `{summary['rows']}`",
        f"- ready: `{summary['ready']}`",
        f"- partial: `{summary['partial']}`",
        f"- host/license gated: `{summary['credential_or_host_gated']}`",
        f"- missing artifacts: `{summary['missing_artifact']}`",
        "",
        "## Matrix",
        "",
        "| Area | Status | Surfaces | Confirmation | Primary commands | Gaps |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in report["rows"]:
        commands = "<br>".join(f"`{command}`" for command in row["commands"])
        gaps = "<br>".join(row["gaps"]) if row["gaps"] else "none"
        lines.append(
            f"| {row['area']} | `{row['status']}` | {', '.join(row['surfaces'])} | "
            f"{row['confirmation']} | {commands} | {gaps} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "`ready` means the repo has the source artifact and a runnable command or test lane. `partial` means a lower-level proof exists but the full product behavior is not yet proven. `credential_or_host_gated` means the lane requires a local engine install, license, marketplace credential, or vendor endpoint.",
            "",
            "For Alpha5, dead reckoning is intentionally marked partial: FastDIS parses the fields, but predictive extrapolation and engine-scene verification are not complete.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_report(out_dir: Path) -> dict[str, Path]:
    report = build_report()
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "alpha5_integration_matrix.json"
    md_path = out_dir / "alpha5_integration_matrix.md"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    return {"json": json_path, "markdown": md_path}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--json", action="store_true", help="Print the report JSON to stdout")
    args = parser.parse_args()

    if args.json:
        print(json.dumps(build_report(), indent=2))
        return 0
    paths = write_report(args.out_dir)
    print(f"JSON: {rel(paths['json'])}")
    print(f"Markdown: {rel(paths['markdown'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
