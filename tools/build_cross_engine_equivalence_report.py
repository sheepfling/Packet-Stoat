#!/usr/bin/env python3
"""Build a shared cross-engine equivalence summary from current benchmark and audit evidence."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = ROOT / "build" / "reports"
DEFAULT_UNITY_EQUIVALENCE = ROOT / "build" / "reports" / "unity_cross_engine_equivalence.json"
DEFAULT_ENGINE_REPORTS = {
    "native": ROOT / "build" / "reports" / "engine_benchmarks" / "native_engine_benchmark_report.json",
    "c": ROOT / "build" / "reports" / "engine_benchmarks" / "c_engine_benchmark_report.json",
    "cpp": ROOT / "build" / "reports" / "engine_benchmarks" / "cpp_engine_benchmark_report.json",
    "python": ROOT / "build" / "reports" / "engine_benchmarks" / "python_ctypes_engine_benchmark_report.json",
    "unreal": ROOT / "build" / "reports" / "engine_benchmarks" / "unreal_engine_benchmark_report.json",
    "godot": ROOT / "build" / "reports" / "engine_benchmarks" / "godot_engine_benchmark_report.json",
    "unity": ROOT / "build" / "reports" / "engine_benchmarks" / "unity_engine_benchmark_report.json",
}
DEEP_SURFACES = ("c", "cpp", "python", "unreal", "godot", "unity")
RUNTIME_TRUTH_SURFACES = ("unreal", "godot", "unity")
BENCHMARK_REPORT_SURFACES = ("native", "c", "cpp", "python", "unreal", "godot", "unity")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--unity-equivalence", type=Path, default=DEFAULT_UNITY_EQUIVALENCE)
    parser.add_argument("--native", type=Path, default=DEFAULT_ENGINE_REPORTS["native"])
    parser.add_argument("--c", dest="c_report", type=Path, default=DEFAULT_ENGINE_REPORTS["c"])
    parser.add_argument("--cpp", dest="cpp_report", type=Path, default=DEFAULT_ENGINE_REPORTS["cpp"])
    parser.add_argument("--python", dest="python_report", type=Path, default=DEFAULT_ENGINE_REPORTS["python"])
    parser.add_argument("--unreal", type=Path, default=DEFAULT_ENGINE_REPORTS["unreal"])
    parser.add_argument("--godot", type=Path, default=DEFAULT_ENGINE_REPORTS["godot"])
    parser.add_argument("--unity", type=Path, default=DEFAULT_ENGINE_REPORTS["unity"])
    parser.add_argument("--json-out", type=Path, default=DEFAULT_OUT_DIR / "cross_engine_equivalence.json")
    parser.add_argument("--md-out", type=Path, default=DEFAULT_OUT_DIR / "cross_engine_equivalence.md")
    return parser.parse_args(argv)


def load_json(path: Path | None) -> dict[str, Any] | None:
    if path is None or not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _surface_summary(name: str, payload: dict[str, Any] | None, path: Path) -> dict[str, Any]:
    rows = payload.get("rows") if isinstance(payload, dict) and isinstance(payload.get("rows"), list) else []
    truth_rows = 0
    verified_truth_rows = 0
    for row in rows:
        if not isinstance(row, dict):
            continue
        truth = row.get("truth")
        if isinstance(truth, dict) and truth.get("final_truth_match") is not None:
            truth_rows += 1
            if truth.get("final_truth_match") is True:
                verified_truth_rows += 1
    return {
        "surface": name,
        "path": display_path(path),
        "exists": payload is not None,
        "row_count": len(rows),
        "truth_rows": truth_rows,
        "verified_truth_rows": verified_truth_rows,
        "source_schema": payload.get("source_schema") if isinstance(payload, dict) else None,
    }


def build_report(
    unity_equivalence_payload: dict[str, Any] | None,
    unity_equivalence_path: Path,
    engine_payloads: dict[str, tuple[Path, dict[str, Any] | None]],
) -> dict[str, Any]:
    deep_metrics = {}
    unity_status = None
    if isinstance(unity_equivalence_payload, dict):
        unity_status = unity_equivalence_payload.get("status")
        metrics = unity_equivalence_payload.get("metrics")
        if isinstance(metrics, dict) and isinstance(metrics.get("language_rows"), dict):
            for surface in DEEP_SURFACES:
                row = metrics["language_rows"].get(surface)
                if isinstance(row, dict):
                    deep_metrics[surface] = {
                        "catalog_rows": row.get("catalog_rows"),
                        "deep_rows": row.get("deep_rows"),
                    }

    surface_rows = [
        _surface_summary(name, payload, path)
        for name, (path, payload) in engine_payloads.items()
    ]
    surface_index = {row["surface"]: row for row in surface_rows}

    deep_complete = (
        unity_status == "complete"
        and all(deep_metrics.get(surface, {}).get("catalog_rows") == 141 for surface in DEEP_SURFACES)
        and all(deep_metrics.get(surface, {}).get("deep_rows") == 141 for surface in DEEP_SURFACES)
    )
    runtime_truth_complete = all(
        surface_index.get(surface, {}).get("verified_truth_rows", 0) > 0
        for surface in RUNTIME_TRUTH_SURFACES
    )
    benchmark_contract_present = all(
        surface_index.get(surface, {}).get("row_count", 0) > 0
        for surface in BENCHMARK_REPORT_SURFACES
    )

    gaps: list[str] = []
    if unity_status != "complete":
        gaps.append("unity-facing cross-engine audit is not complete")
    for surface in DEEP_SURFACES:
        if deep_metrics.get(surface, {}).get("deep_rows") != 141:
            gaps.append(f"{surface} deep-row coverage is not 141")
    for surface in BENCHMARK_REPORT_SURFACES:
        if surface_index.get(surface, {}).get("row_count", 0) == 0:
            gaps.append(f"{surface} shared engine benchmark report missing or empty")
    for surface in RUNTIME_TRUTH_SURFACES:
        if surface_index.get(surface, {}).get("verified_truth_rows", 0) == 0:
            gaps.append(f"{surface} has no verified runtime truth rows in the shared benchmark report")

    status = "complete" if deep_complete and runtime_truth_complete and benchmark_contract_present else "partial"
    note = (
        "Shared deep-surface parity is complete across C, C++, Python, Unreal, Godot, and Unity, and current Unreal/Godot/Unity benchmark bridges all carry verified runtime truth rows."
        if status == "complete"
        else "Cross-engine equivalence evidence exists, but one or more deep-surface or runtime-truth conditions are still incomplete."
    )

    claim_boundaries = [
        "Deep-row equivalence comes from the shared cross-language Unity-facing audit, not from per-engine benchmark timing runs.",
        "Runtime truth verification currently comes from the Unreal, Godot, and Unity benchmark bridges; C and C++ truth verification comes from the shared localhost UDP ingest matrix, while native and Python benchmark reports still lack complete scenario-truth coverage across every canonical scenario.",
        "C and C++ benchmark rows currently come from the shared localhost UDP truth routes, while native and Python also carry direct benchmark rows from the benchmark runner path.",
        "This report supports cross-engine consistency claims. It does not support competitor-performance claims.",
    ]

    evidence = [
        {
            "path": display_path(unity_equivalence_path),
            "exists": unity_equivalence_payload is not None,
            "kind": "unity_cross_engine_audit",
        }
    ]
    evidence.extend(
        {
            "path": row["path"],
            "exists": row["exists"],
            "kind": f"{row['surface']}_engine_benchmark_report",
        }
        for row in surface_rows
    )

    return {
        "schema": "fastdis.cross_engine_equivalence_report.v1",
        "generated_at_utc": utc_now(),
        "status": status,
        "note": note,
        "claim_boundaries": claim_boundaries,
        "summary": {
            "benchmark_surface_count": len(BENCHMARK_REPORT_SURFACES),
            "deep_surface_count": len(DEEP_SURFACES),
            "runtime_truth_surface_count": len(RUNTIME_TRUTH_SURFACES),
            "deep_complete": deep_complete,
            "runtime_truth_complete": runtime_truth_complete,
            "benchmark_contract_present": benchmark_contract_present,
        },
        "deep_surfaces": deep_metrics,
        "benchmark_surfaces": surface_rows,
        "evidence": evidence,
        "gaps": gaps,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Cross-Engine Equivalence",
        "",
        f"- schema: `{report['schema']}`",
        f"- status: `{report['status']}`",
        "",
        report["note"],
        "",
        "## Claim Boundaries",
        "",
    ]
    for note in report["claim_boundaries"]:
        lines.append(f"- {note}")
    lines.extend(
        [
            "",
            "## Deep Surfaces",
            "",
            "| surface | catalog rows | deep rows |",
            "| --- | --- | --- |",
        ]
    )
    for surface in DEEP_SURFACES:
        row = report["deep_surfaces"].get(surface, {})
        lines.append(f"| {surface} | {row.get('catalog_rows')} | {row.get('deep_rows')} |")
    lines.extend(
        [
            "",
            "## Benchmark Surfaces",
            "",
            "| surface | rows | truth rows | verified truth rows | source schema |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for row in report["benchmark_surfaces"]:
        lines.append(
            f"| {row['surface']} | {row['row_count']} | {row['truth_rows']} | {row['verified_truth_rows']} | {row['source_schema']} |"
        )
    lines.extend(["", "## Gaps", ""])
    if report["gaps"]:
        for gap in report["gaps"]:
            lines.append(f"- {gap}")
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    unity_equivalence_payload = load_json(args.unity_equivalence)
    engine_payloads = {
        "native": (args.native, load_json(args.native)),
        "c": (args.c_report, load_json(args.c_report)),
        "cpp": (args.cpp_report, load_json(args.cpp_report)),
        "python": (args.python_report, load_json(args.python_report)),
        "unreal": (args.unreal, load_json(args.unreal)),
        "godot": (args.godot, load_json(args.godot)),
        "unity": (args.unity, load_json(args.unity)),
    }
    report = build_report(unity_equivalence_payload, args.unity_equivalence, engine_payloads)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.md_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    args.md_out.write_text(render_markdown(report) + "\n", encoding="utf-8")
    print(f"json: {display_path(args.json_out)}")
    print(f"md: {display_path(args.md_out)}")
    return 0 if report["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
