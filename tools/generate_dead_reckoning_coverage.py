#!/usr/bin/env python3
"""Generate the FastDIS dead-reckoning coverage manifest and report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "build" / "reports" / "dead_reckoning_coverage_manifest.json"
DOC_PATH = ROOT / "docs" / "DEAD_RECKONING_COVERAGE.md"

ALGORITHMS = (
    {
        "value": 0,
        "symbol": "OTHER",
        "name": "Other / unspecified",
        "motion_frame": "unknown",
        "rotation_frame": "unknown",
        "notes": "Explicitly recognized so unknown or non-standard algorithm values are not silently treated as supported.",
    },
    {
        "value": 1,
        "symbol": "STATIC",
        "name": "Static",
        "motion_frame": "none",
        "rotation_frame": "none",
        "notes": "Entity is expected to remain fixed unless a new Entity State PDU arrives.",
    },
    {
        "value": 2,
        "symbol": "DRM_FPW",
        "name": "Fixed position, world orientation",
        "motion_frame": "fixed_position",
        "rotation_frame": "world",
        "notes": "No translational extrapolation should be applied by a full standard-aware implementation.",
    },
    {
        "value": 3,
        "symbol": "DRM_RPW",
        "name": "Rotation, fixed position, world orientation",
        "motion_frame": "fixed_position",
        "rotation_frame": "world",
        "notes": "Full implementation must apply angular velocity without translational drift.",
    },
    {
        "value": 4,
        "symbol": "DRM_RVW",
        "name": "Rotation and velocity, world coordinates",
        "motion_frame": "world_velocity",
        "rotation_frame": "world",
        "notes": "Full implementation must apply world-frame velocity and angular velocity.",
    },
    {
        "value": 5,
        "symbol": "DRM_FVW",
        "name": "Velocity, world coordinates",
        "motion_frame": "world_velocity",
        "rotation_frame": "fixed",
        "notes": "Full implementation must apply world-frame velocity without angular extrapolation.",
    },
    {
        "value": 6,
        "symbol": "DRM_FPB",
        "name": "Fixed position, body orientation",
        "motion_frame": "fixed_position",
        "rotation_frame": "body",
        "notes": "Full implementation must preserve position and account for body-frame orientation semantics.",
    },
    {
        "value": 7,
        "symbol": "DRM_RPB",
        "name": "Rotation, fixed position, body orientation",
        "motion_frame": "fixed_position",
        "rotation_frame": "body",
        "notes": "Full implementation must apply angular velocity in the documented body-frame convention.",
    },
    {
        "value": 8,
        "symbol": "DRM_RVB",
        "name": "Rotation and velocity, body coordinates",
        "motion_frame": "body_velocity",
        "rotation_frame": "body",
        "notes": "Full implementation must rotate body-frame velocity into world/ECEF before extrapolating.",
    },
    {
        "value": 9,
        "symbol": "DRM_FVB",
        "name": "Velocity, body coordinates",
        "motion_frame": "body_velocity",
        "rotation_frame": "fixed",
        "notes": "Full implementation must rotate body-frame velocity into world/ECEF without angular extrapolation.",
    },
)

REQUIRED_SURFACES = (
    "standard_enum_accounted",
    "c_field_parse",
    "cpp_field_parse",
    "python_field_parse",
    "linear_fallback",
    "algorithmic_c",
    "algorithmic_cpp",
    "algorithmic_python",
    "unreal_runtime_scene",
    "godot_runtime_scene",
    "unity_runtime_scene",
    "lattice_metadata",
)


def _read(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _evidence() -> dict[str, bool]:
    header = _read(ROOT / "include" / "fastdis" / "fastdis.h")
    hpp = _read(ROOT / "include" / "fastdis" / "fastdis.hpp")
    native_py = _read(ROOT / "src" / "fastdis" / "native.py")
    core = _read(ROOT / "src" / "native" / "fastdis_core.cpp")
    ctypes_tests = _read(ROOT / "tests" / "test_native_ctypes.py")
    c_tests = _read(ROOT / "tests" / "native" / "test_c_api.cpp")
    unreal = "\n".join(
        _read(path)
        for path in (ROOT / "examples" / "unreal").rglob("*")
        if path.is_file() and "ThirdParty" not in path.parts and path.suffix in {".cpp", ".h", ".hpp", ".cs", ".md"}
    )
    godot = "\n".join(
        _read(path)
        for path in (ROOT / "examples" / "godot").rglob("*")
        if path.is_file() and path.suffix in {".gd", ".cpp", ".h", ".hpp", ".md", ".tscn"}
    )
    unity = "\n".join(
        _read(path)
        for path in (ROOT / "integrations" / "unity").rglob("*")
        if path.is_file() and path.suffix in {".cs", ".md", ".json"}
    )
    lattice_paths = [ROOT / "src" / "fastdis" / "lattice.py"]
    lattice_paths.extend(
        path
        for path in (ROOT / "packages" / "lattice").rglob("*")
        if path.is_file() and path.suffix in {".py", ".md", ".json", ".yaml"}
    )
    lattice = "\n".join(_read(path) for path in lattice_paths)
    parse_needles = (
        "dead_reckoning_algorithm",
        "dead_reckoning_parameters",
        "dead_reckoning_linear_acceleration",
        "dead_reckoning_angular_velocity",
    )
    return {
        "c_field_parse": all(needle in header and needle in core for needle in parse_needles)
        and "entity.dead_reckoning_algorithm == 4u" in c_tests,
        "cpp_field_parse": "using EntityStatePrefix = fastdis_entity_state_prefix_t" in hpp,
        "python_field_parse": all(needle in native_py for needle in parse_needles)
        and "entity.dead_reckoning_algorithm == 4" in ctypes_tests,
        "linear_fallback": "fastdis_extrapolate_entity_snapshot_linear" in header
        and "FASTDIS_ENTITY_CHANGE_EXTRAPOLATED" in header
        and "copy_latest_extrapolated" in native_py
        and "fastdis_extrapolate_entity_snapshot_linear" in c_tests,
        "algorithmic_c": "fastdis_extrapolate_entity_transform_dead_reckoning" in header
        and "extrapolate_transform_dead_reckoning_value" in core
        and "FASTDIS_DR_FVB" in core
        and "for (uint8_t algorithm = FASTDIS_DR_OTHER" in c_tests,
        "algorithmic_cpp": "extrapolate_entity_transform_dead_reckoning" in hpp
        and "copy_latest_dead_reckoned" in hpp
        and "dr_fvb" in hpp,
        "algorithmic_python": "extrapolate_transform_dead_reckoning" in native_py
        and "copy_latest_dead_reckoned" in native_py
        and "FASTDIS_DR_FVB" in native_py
        and "for algorithm in range(native.FASTDIS_DR_OTHER" in ctypes_tests,
        "unreal_runtime_scene": "fastdis.unreal.dead_reckoning_runtime.v1" in unreal
        and "fastdis_extrapolate_entity_transform_dead_reckoning" in unreal,
        "godot_runtime_scene": "fastdis.godot.dead_reckoning_runtime.v1" in godot
        and "fastdis_extrapolate_entity_transform_dead_reckoning" in godot,
        "unity_runtime_scene": "fastdis.unity.dead_reckoning_runtime.v1" in unity
        and "fastdis_extrapolate_entity_transform_dead_reckoning" in unity,
        "lattice_metadata": "deadReckoning" in lattice and "dead_reckoning" in lattice,
    }


def _row_status(row: dict[str, Any]) -> str:
    if all(bool(row["surfaces"][surface]) for surface in REQUIRED_SURFACES):
        return "compliant"
    if row["surfaces"]["standard_enum_accounted"] and row["surfaces"]["c_field_parse"] and row["surfaces"]["python_field_parse"]:
        return "partial"
    return "gap"


def build_manifest() -> dict[str, Any]:
    evidence = _evidence()
    rows: list[dict[str, Any]] = []
    for algorithm in ALGORITHMS:
        surfaces = {
            "standard_enum_accounted": True,
            "c_field_parse": evidence["c_field_parse"],
            "cpp_field_parse": evidence["cpp_field_parse"],
            "python_field_parse": evidence["python_field_parse"],
            "linear_fallback": evidence["linear_fallback"],
            "algorithmic_c": evidence["algorithmic_c"],
            "algorithmic_cpp": evidence["algorithmic_cpp"],
            "algorithmic_python": evidence["algorithmic_python"],
            "unreal_runtime_scene": evidence["unreal_runtime_scene"],
            "godot_runtime_scene": evidence["godot_runtime_scene"],
            "unity_runtime_scene": evidence["unity_runtime_scene"],
            "lattice_metadata": evidence["lattice_metadata"],
        }
        missing = [surface for surface in REQUIRED_SURFACES if not surfaces[surface]]
        row = {
            **algorithm,
            "surfaces": surfaces,
            "missing_surfaces": missing,
        }
        row["status"] = _row_status(row)
        rows.append(row)

    total_cells = len(rows) * len(REQUIRED_SURFACES)
    passed_cells = sum(1 for row in rows for surface in REQUIRED_SURFACES if row["surfaces"][surface])
    compliant_rows = sum(1 for row in rows if row["status"] == "compliant")
    manifest = {
        "schema": "fastdis.dead_reckoning_coverage.v1",
        "overall_status": "compliant" if compliant_rows == len(rows) else "partial",
        "target": "100_percent_surface_compliance",
        "summary": {
            "algorithm_rows": len(rows),
            "compliant_rows": compliant_rows,
            "required_surfaces": list(REQUIRED_SURFACES),
            "surface_cells": total_cells,
            "passing_surface_cells": passed_cells,
            "surface_compliance_percent": round((passed_cells / total_cells) * 100.0, 2),
        },
        "rows": rows,
    }
    return manifest


def render_markdown(manifest: dict[str, Any]) -> str:
    summary = manifest["summary"]
    if manifest["overall_status"] == "compliant":
        boundary_lines = [
            "FastDIS has explicit dead-reckoning behavior for every tracked algorithm row across C, C++, Python, Unreal, Godot, Unity, and Lattice surfaces.",
            "",
            "The runtime scenes use the shared native evaluator as the parity oracle; they should not duplicate dead-reckoning math in engine-specific code.",
        ]
    else:
        boundary_lines = [
            "FastDIS currently proves field parsing and first-stage linear snapshot extrapolation. It does not yet prove full DIS algorithm-specific dead reckoning, runtime engine scenes, or Lattice dead-reckoning metadata propagation.",
            "",
            "To drive this to 100%, implement the missing surfaces listed above and rerun:",
            "",
            "```bash",
            "python tools/generate_dead_reckoning_coverage.py",
            "python tools/check_generated_fresh.py",
            "```",
        ]
    lines = [
        "# Dead-Reckoning Coverage",
        "",
        "This report is the generated tracking surface for FastDIS dead-reckoning compliance.",
        "It is intentionally stricter than the current implementation: every standard algorithm row must have explicit behavior across C, C++, Python, Unreal, Godot, Unity, and Lattice before the report reaches 100%.",
        "",
        "## Summary",
        "",
        f"- Overall status: `{manifest['overall_status']}`",
        f"- Algorithm rows: `{summary['algorithm_rows']}`",
        f"- Compliant rows: `{summary['compliant_rows']}`",
        f"- Surface compliance: `{summary['surface_compliance_percent']}%`",
        f"- Passing surface cells: `{summary['passing_surface_cells']} / {summary['surface_cells']}`",
        "",
        "## Surface Legend",
        "",
    ]
    for surface in REQUIRED_SURFACES:
        lines.append(f"- `{surface}`")
    lines.extend(
        [
            "",
            "## Algorithm Matrix",
            "",
            "| Value | Symbol | Status | Name | Passing surfaces | Missing surfaces |",
            "| ---: | --- | --- | --- | ---: | --- |",
        ]
    )
    for row in manifest["rows"]:
        passing = sum(1 for surface in REQUIRED_SURFACES if row["surfaces"][surface])
        missing = ", ".join(f"`{surface}`" for surface in row["missing_surfaces"]) or "none"
        lines.append(
            f"| {row['value']} | `{row['symbol']}` | `{row['status']}` | {row['name']} | "
            f"{passing}/{len(REQUIRED_SURFACES)} | {missing} |"
        )
    lines.extend(
        [
            "",
            "## Current Boundary",
            "",
            *boundary_lines,
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(manifest: dict[str, Any]) -> None:
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    DOC_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    DOC_PATH.write_text(render_markdown(manifest), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail if generated files are stale")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest = build_manifest()
    if args.check:
        expected_doc = render_markdown(manifest)
        stale = []
        if not DOC_PATH.exists() or DOC_PATH.read_text(encoding="utf-8") != expected_doc:
            stale.append(str(DOC_PATH.relative_to(ROOT)))
        if stale:
            print("dead-reckoning coverage is stale:", ", ".join(stale))
            return 1
        print(
            "dead-reckoning coverage fresh "
            f"status={manifest['overall_status']} compliance={manifest['summary']['surface_compliance_percent']}%"
        )
        return 0
    write_outputs(manifest)
    print(
        "generated dead-reckoning coverage "
        f"rows={manifest['summary']['algorithm_rows']} "
        f"compliance={manifest['summary']['surface_compliance_percent']}%"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
