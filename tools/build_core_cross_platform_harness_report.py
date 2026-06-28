#!/usr/bin/env python3
"""Build a focused core-harness report for native/C/C++/Python/Godot evidence."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = ROOT / "build" / "reports" / "core_cross_platform_harness"
DEFAULT_MATRIX = ROOT / "build" / "reports" / "benchmark_matrix" / "benchmark_matrix.json"
DEFAULT_COVERAGE = ROOT / "build" / "reports" / "benchmark_coverage" / "benchmark_coverage_report.json"
DEFAULT_CROSS_ENGINE = ROOT / "build" / "reports" / "cross_engine_equivalence.json"
DEFAULT_SURFACE_CLAIMS = ROOT / "build" / "reports" / "surface_claim_report" / "surface_claim_report.json"

REFERENCE_SURFACES = ("native",)
REQUIRED_SURFACES = ("c", "cpp", "python_ctypes", "godot")
CORE_SURFACES = REFERENCE_SURFACES + REQUIRED_SURFACES
CAPABILITY_NAMES = ("ingest", "filtering", "latest_state", "replay")
DEEP_EQUIVALENCE_ALIASES = {
    "c": "c",
    "cpp": "cpp",
    "python_ctypes": "python",
    "godot": "godot",
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matrix", type=Path, default=DEFAULT_MATRIX)
    parser.add_argument("--coverage", type=Path, default=DEFAULT_COVERAGE)
    parser.add_argument("--cross-engine", type=Path, default=DEFAULT_CROSS_ENGINE)
    parser.add_argument("--surface-claims", type=Path, default=DEFAULT_SURFACE_CLAIMS)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_OUT_DIR / "core_cross_platform_harness_report.json")
    parser.add_argument("--md-out", type=Path, default=DEFAULT_OUT_DIR / "core_cross_platform_harness_report.md")
    return parser.parse_args(argv)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _matrix_surface_index(matrix: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = matrix.get("surfaces") if isinstance(matrix.get("surfaces"), list) else []
    return {
        row["surface"]: row
        for row in rows
        if isinstance(row, dict) and isinstance(row.get("surface"), str)
    }


def _coverage_index(coverage: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = coverage.get("surfaces") if isinstance(coverage.get("surfaces"), list) else []
    return {
        row["surface"]: row
        for row in rows
        if isinstance(row, dict) and isinstance(row.get("surface"), str)
    }


def _surface_claim_index(surface_claims: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = surface_claims.get("surfaces") if isinstance(surface_claims.get("surfaces"), list) else []
    return {
        row["surface"]: row
        for row in rows
        if isinstance(row, dict) and isinstance(row.get("surface"), str)
    }


def _cross_surface_index(cross_engine: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = cross_engine.get("benchmark_surfaces") if isinstance(cross_engine.get("benchmark_surfaces"), list) else []
    return {
        row["surface"]: row
        for row in rows
        if isinstance(row, dict) and isinstance(row.get("surface"), str)
    }


def _surface_role(surface: str) -> str:
    if surface == "native":
        return "reference_runtime"
    if surface == "godot":
        return "adapter_proof_bridge"
    return "core_runtime"


def _capability_covered(capabilities: dict[str, Any], capability: str) -> bool:
    return bool((capabilities.get(capability) or {}).get("covered"))


def _shared_contract_covered(capabilities: dict[str, Any], capability: str) -> bool:
    return bool((capabilities.get(capability) or {}).get("shared_contract_covered"))


def _shared_contract_defined(capabilities: dict[str, Any], capability: str) -> bool:
    return bool((capabilities.get(capability) or {}).get("shared_contract_defined"))


def _surface_row(
    surface: str,
    matrix_row: dict[str, Any] | None,
    coverage_row: dict[str, Any] | None,
    claim_row: dict[str, Any] | None,
    cross_row: dict[str, Any] | None,
    deep_rows: dict[str, Any],
) -> dict[str, Any]:
    capabilities = coverage_row.get("capabilities") if isinstance(coverage_row, dict) and isinstance(coverage_row.get("capabilities"), dict) else {}
    deep_alias = DEEP_EQUIVALENCE_ALIASES.get(surface)
    deep_row = deep_rows.get(deep_alias) if isinstance(deep_alias, str) and isinstance(deep_rows.get(deep_alias), dict) else None
    missing_measured_capabilities = [capability for capability in CAPABILITY_NAMES if not _capability_covered(capabilities, capability)]
    missing_shared_contract_capabilities = [capability for capability in CAPABILITY_NAMES if not _shared_contract_covered(capabilities, capability)]
    surface_complete = (
        surface in REQUIRED_SURFACES
        and isinstance(matrix_row, dict)
        and isinstance(cross_row, dict)
        and int(cross_row.get("verified_truth_rows", 0) or 0) > 0
        and not missing_shared_contract_capabilities
    )

    boundaries = list(claim_row.get("boundaries") or []) if isinstance(claim_row, dict) else []
    if surface == "godot":
        boundary = "Godot is part of the shared proof-backed harness, not a same-class Unreal/Unity runtime throughput lane."
        if boundary not in boundaries:
            boundaries.append(boundary)
    else:
        boundary = "This surface supports the core harness and does not by itself prove Unreal/Unity or GRILL head-to-head outcomes."
        if boundary not in boundaries:
            boundaries.append(boundary)

    return {
        "surface": surface,
        "role": _surface_role(surface),
        "required_for_completion": surface in REQUIRED_SURFACES,
        "surface_complete": surface_complete,
        "present": isinstance(matrix_row, dict),
        "surface_kind": matrix_row.get("surface_kind") if isinstance(matrix_row, dict) else None,
        "evidence_kind": matrix_row.get("evidence_kind") if isinstance(matrix_row, dict) else None,
        "path": matrix_row.get("path") if isinstance(matrix_row, dict) else None,
        "scenario_count": int(matrix_row.get("scenario_count", 0) or 0) if isinstance(matrix_row, dict) else 0,
        "scenarios": matrix_row.get("scenarios") if isinstance(matrix_row, dict) and isinstance(matrix_row.get("scenarios"), list) else [],
        "latency_rows": int(matrix_row.get("latency_rows", 0) or 0) if isinstance(matrix_row, dict) else 0,
        "runtime_metric_rows": int(matrix_row.get("runtime_metric_rows", 0) or 0) if isinstance(matrix_row, dict) else 0,
        "truth_rows": int(matrix_row.get("truth_rows", 0) or 0) if isinstance(matrix_row, dict) else 0,
        "verified_truth_rows": int(cross_row.get("verified_truth_rows", 0) or 0) if isinstance(cross_row, dict) else 0,
        "deep_catalog_rows": int(deep_row.get("catalog_rows", 0) or 0) if isinstance(deep_row, dict) else 0,
        "deep_rows": int(deep_row.get("deep_rows", 0) or 0) if isinstance(deep_row, dict) else 0,
        "capabilities": {
            capability: _capability_covered(capabilities, capability)
            for capability in CAPABILITY_NAMES + ("engine_runtime",)
        },
        "shared_contract_capabilities": {
            capability: _shared_contract_covered(capabilities, capability)
            for capability in CAPABILITY_NAMES
        },
        "shared_contract_defined": {
            capability: _shared_contract_defined(capabilities, capability)
            for capability in CAPABILITY_NAMES
        },
        "missing_measured_capabilities": missing_measured_capabilities,
        "missing_shared_contract_capabilities": missing_shared_contract_capabilities,
        "safe_claims": list(claim_row.get("safe_claims") or []) if isinstance(claim_row, dict) else [],
        "boundaries": boundaries,
    }


def build_report(
    matrix_path: Path,
    matrix: dict[str, Any],
    coverage_path: Path,
    coverage: dict[str, Any],
    cross_engine_path: Path,
    cross_engine: dict[str, Any],
    surface_claims_path: Path,
    surface_claims: dict[str, Any],
) -> dict[str, Any]:
    matrix_index = _matrix_surface_index(matrix)
    coverage_index = _coverage_index(coverage)
    claim_index = _surface_claim_index(surface_claims)
    cross_index = _cross_surface_index(cross_engine)
    deep_rows = cross_engine.get("deep_surfaces") if isinstance(cross_engine.get("deep_surfaces"), dict) else {}
    cross_summary = cross_engine.get("summary") if isinstance(cross_engine.get("summary"), dict) else {}

    surfaces = [
        _surface_row(
            surface,
            matrix_index.get(surface),
            coverage_index.get(surface),
            claim_index.get(surface),
            cross_index.get("python" if surface == "python_ctypes" else surface),
            deep_rows,
        )
        for surface in CORE_SURFACES
    ]
    required_rows = [row for row in surfaces if row["surface"] in REQUIRED_SURFACES]

    present_surface_count = sum(1 for row in surfaces if row["present"])
    verified_truth_surface_count = sum(1 for row in surfaces if row["verified_truth_rows"] > 0)
    required_surface_complete_count = sum(1 for row in required_rows if row["surface_complete"])
    deep_equivalence_surface_count = sum(1 for row in surfaces if row["deep_rows"] > 0)
    deep_equivalence_complete = all(
        row["deep_catalog_rows"] == 141 and row["deep_rows"] == 141
        for row in required_rows
    )
    all_surfaces_ingest = all(row["capabilities"]["ingest"] for row in required_rows)
    filtering_present = all(row["capabilities"]["filtering"] for row in required_rows)
    latest_state_present = all(row["capabilities"]["latest_state"] for row in required_rows)
    replay_present = all(row["capabilities"]["replay"] for row in required_rows)
    shared_contract_replay_defined = any(
        row["shared_contract_defined"]["replay"] for row in required_rows
    )
    benchmark_contract_present = cross_summary.get("benchmark_contract_present") is True

    status = "complete" if (
        required_surface_complete_count == len(REQUIRED_SURFACES)
        and deep_equivalence_complete
        and shared_contract_replay_defined
        and benchmark_contract_present
    ) else "partial"

    gaps: list[str] = []
    missing_surfaces = [row["surface"] for row in required_rows if not row["present"]]
    if missing_surfaces:
        gaps.append("core harness matrix rows missing for: " + ", ".join(missing_surfaces))
    missing_verified_truth = [row["surface"] for row in required_rows if row["verified_truth_rows"] == 0]
    if missing_verified_truth:
        gaps.append("verified truth rows missing for: " + ", ".join(missing_verified_truth))
    missing_deep = [row["surface"] for row in required_rows if row["deep_catalog_rows"] != 141 or row["deep_rows"] != 141]
    if missing_deep:
        gaps.append("deep equivalence coverage incomplete for: " + ", ".join(missing_deep))
    if not all_surfaces_ingest:
        gaps.append("not every required surface currently exposes measured ingest coverage")
    if not filtering_present:
        missing = [row["surface"] for row in required_rows if not row["capabilities"]["filtering"]]
        gaps.append("measured filtering coverage missing for: " + ", ".join(missing))
    if not latest_state_present:
        missing = [row["surface"] for row in required_rows if not row["capabilities"]["latest_state"]]
        gaps.append("measured latest-state coverage missing for: " + ", ".join(missing))
    if not replay_present:
        missing = [row["surface"] for row in required_rows if not row["capabilities"]["replay"]]
        gaps.append("measured replay coverage missing for: " + ", ".join(missing))
    for row in required_rows:
        if row["missing_shared_contract_capabilities"]:
            gaps.append(
                f"{row['surface']} does not yet publish shared-scenario coverage for: "
                + ", ".join(row["missing_shared_contract_capabilities"])
            )
    if not shared_contract_replay_defined:
        gaps.append("the canonical shared benchmark truth suite does not yet define a replay scenario for the core cross-platform lane")
    if not benchmark_contract_present:
        gaps.append("cross-engine equivalence report does not currently mark the benchmark contract as present")

    claim_blurb = (
        "FastDIS has a shared proof-backed benchmark harness across C, C++, Python, and Godot "
        "with reproducible ingest, filtering, latest-state, replay, and shared-scenario coverage."
    )
    if status != "complete":
        claim_blurb = (
            "FastDIS has a partial shared core harness across C, C++, Python, and Godot; "
            "ingest and truth are in place, but shared filtering/latest-state/replay coverage is not yet complete on every measured surface."
        )

    return {
        "schema": "fastdis.core_cross_platform_harness_report.v1",
        "generated_at_utc": utc_now(),
        "status": status,
        "sources": {
            "matrix": display_path(matrix_path),
            "coverage": display_path(coverage_path),
            "cross_engine": display_path(cross_engine_path),
            "surface_claims": display_path(surface_claims_path),
        },
        "summary": {
            "core_surface_count": len(CORE_SURFACES),
            "required_surface_count": len(REQUIRED_SURFACES),
            "required_surface_complete_count": required_surface_complete_count,
            "present_surface_count": present_surface_count,
            "verified_truth_surface_count": verified_truth_surface_count,
            "deep_equivalence_surface_count": deep_equivalence_surface_count,
            "all_surfaces_ingest": all_surfaces_ingest,
            "filtering_present": filtering_present,
            "latest_state_present": latest_state_present,
            "replay_present": replay_present,
            "deep_equivalence_complete": deep_equivalence_complete,
            "shared_contract_replay_defined": shared_contract_replay_defined,
            "benchmark_contract_present": benchmark_contract_present,
        },
        "claim_blurb": claim_blurb,
        "claim_boundaries": [
            "This report is the core native/binding/Godot packet and equivalence lane, not the Unreal/Unity runtime or GRILL head-to-head lane.",
            "Godot evidence here is verification-backed adapter proof, not a same-class Unreal/Unity runtime throughput comparison.",
            "A surface does not count as complete here unless filtering, latest-state, and replay are all published on that same measured lane with shared-scenario coverage.",
            "Use the top-level matrix and competitor reports for any Unreal, Unity, or GRILL claim.",
        ],
        "surfaces": surfaces,
        "gaps": gaps,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Core Cross-Platform Harness Report",
        "",
        f"- schema: `{report['schema']}`",
        f"- status: `{report['status']}`",
        f"- claim_blurb: {report['claim_blurb']}",
        "",
        "## Summary",
        "",
        f"- core_surface_count: `{report['summary']['core_surface_count']}`",
        f"- required_surface_count: `{report['summary']['required_surface_count']}`",
        f"- required_surface_complete_count: `{report['summary']['required_surface_complete_count']}`",
        f"- present_surface_count: `{report['summary']['present_surface_count']}`",
        f"- verified_truth_surface_count: `{report['summary']['verified_truth_surface_count']}`",
        f"- deep_equivalence_surface_count: `{report['summary']['deep_equivalence_surface_count']}`",
        f"- all_surfaces_ingest: `{report['summary']['all_surfaces_ingest']}`",
        f"- filtering_present: `{report['summary']['filtering_present']}`",
        f"- latest_state_present: `{report['summary']['latest_state_present']}`",
        f"- replay_present: `{report['summary']['replay_present']}`",
        f"- deep_equivalence_complete: `{report['summary']['deep_equivalence_complete']}`",
        f"- shared_contract_replay_defined: `{report['summary']['shared_contract_replay_defined']}`",
        f"- benchmark_contract_present: `{report['summary']['benchmark_contract_present']}`",
        "",
        "## Surfaces",
        "",
        "| surface | role | required | complete | verified_truth_rows | ingest | filtering | latest_state | replay | shared_filtering | shared_latest_state | shared_replay |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in report["surfaces"]:
        caps = row["capabilities"]
        shared = row["shared_contract_capabilities"]
        lines.append(
            f"| {row['surface']} | {row['role']} | {row['required_for_completion']} | {row['surface_complete']} | {row['verified_truth_rows']} | "
            f"{caps['ingest']} | {caps['filtering']} | {caps['latest_state']} | {caps['replay']} | "
            f"{shared['filtering']} | {shared['latest_state']} | {shared['replay']} |"
        )
    lines.extend(["", "## Claim Boundaries", ""])
    for boundary in report["claim_boundaries"]:
        lines.append(f"- {boundary}")
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
    matrix = load_json(args.matrix)
    coverage = load_json(args.coverage)
    cross_engine = load_json(args.cross_engine)
    surface_claims = load_json(args.surface_claims)
    report = build_report(
        args.matrix,
        matrix,
        args.coverage,
        coverage,
        args.cross_engine,
        cross_engine,
        args.surface_claims,
        surface_claims,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.md_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    args.md_out.write_text(render_markdown(report) + "\n", encoding="utf-8")
    print(f"json: {display_path(args.json_out)}")
    print(f"md: {display_path(args.md_out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
