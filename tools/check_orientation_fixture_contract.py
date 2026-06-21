#!/usr/bin/env python3
"""Validate the canonical engine orientation fixture contract."""

from __future__ import annotations

import argparse
from datetime import UTC
from datetime import datetime
import json
import math
from pathlib import Path
from typing import Any

from artifacts import VERIFICATION_REPORTS_DIR


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FIXTURE = ROOT / "tests" / "data" / "orientation_engine_cases.json"
DEFAULT_OUT_DIR = VERIFICATION_REPORTS_DIR / "orientation_current"

REQUIRED_CASE_KEYS = {
    "name",
    "lat_deg",
    "lon_deg",
    "height_m",
    "local_ned_attitude_deg",
    "expected",
}
REQUIRED_ATTITUDE_KEYS = {"heading", "pitch", "roll"}
REQUIRED_EXPECTED_KEYS = {
    "body_forward_ecef",
    "body_right_ecef",
    "body_down_ecef",
    "body_forward_enu",
    "body_right_enu",
    "body_up_enu",
    "dis_deg",
    "unreal_forward",
    "unreal_right",
    "unreal_up",
    "godot_forward",
    "godot_right",
    "godot_up",
    "unity_forward",
    "unity_right",
    "unity_up",
}
REQUIRED_DIS_KEYS = {"psi", "theta", "phi"}
REQUIRED_TOLERANCE_KEYS = {
    "engine_axis_angular_error_deg",
    "engine_axis_component_error",
    "engine_position_error_cm",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    return parser.parse_args()


def dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def norm(v: list[float]) -> float:
    return math.sqrt(dot(v, v))


def determinant(a: list[float], b: list[float], c: list[float]) -> float:
    return (
        a[0] * (b[1] * c[2] - b[2] * c[1])
        - b[0] * (a[1] * c[2] - a[2] * c[1])
        + c[0] * (a[1] * b[2] - a[2] * b[1])
    )


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def is_number(value: object) -> bool:
    return isinstance(value, int | float) and math.isfinite(float(value))


def validate_vector(path: str, value: object, errors: list[str]) -> list[float] | None:
    if not isinstance(value, list) or len(value) != 3:
        errors.append(f"{path}: expected 3-vector")
        return None
    if not all(is_number(item) for item in value):
        errors.append(f"{path}: vector contains non-finite values")
        return None
    return [float(item) for item in value]


def validate_unit_vector(path: str, value: object, errors: list[str], *, tolerance: float = 1e-8) -> list[float] | None:
    vector = validate_vector(path, value, errors)
    if vector is None:
        return None
    length = norm(vector)
    if abs(length - 1.0) > tolerance:
        errors.append(f"{path}: norm {length:.12g} is not unit length")
    return vector


def validate_basis(case_name: str, label: str, vectors: dict[str, list[float]], errors: list[str]) -> dict[str, float]:
    names = list(vectors)
    max_dot = 0.0
    for i, left in enumerate(names):
        for right in names[i + 1 :]:
            value = abs(dot(vectors[left], vectors[right]))
            max_dot = max(max_dot, value)
            if value > 1e-8:
                errors.append(f"{case_name}.{label}: {left} dot {right} = {value:.12g}")
    det = determinant(vectors[names[0]], vectors[names[1]], vectors[names[2]])
    if abs(abs(det) - 1.0) > 1e-8:
        errors.append(f"{case_name}.{label}: determinant {det:.12g} is not +/-1")
    return {"max_abs_dot": max_dot, "determinant": det}


def validate_fixture(fixture_path: Path) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    fixture = load_json(fixture_path)

    if fixture.get("schema") != "fastdis.orientation_engine_cases.v1":
        errors.append("schema must be fastdis.orientation_engine_cases.v1")

    tolerances = fixture.get("tolerances")
    if not isinstance(tolerances, dict):
        errors.append("tolerances must be present")
    else:
        missing = REQUIRED_TOLERANCE_KEYS - set(tolerances)
        if missing:
            errors.append(f"tolerances missing keys: {sorted(missing)}")

    cases = fixture.get("cases")
    if not isinstance(cases, list) or not cases:
        errors.append("cases must be a non-empty list")
        cases = []

    seen_names: set[str] = set()
    case_summaries: list[dict[str, Any]] = []
    max_abs_dot = 0.0
    min_abs_det = 1.0

    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            errors.append(f"cases[{index}]: expected object")
            continue
        name = str(case.get("name", f"cases[{index}]"))
        if name in seen_names:
            errors.append(f"{name}: duplicate case name")
        seen_names.add(name)

        missing_case_keys = REQUIRED_CASE_KEYS - set(case)
        if missing_case_keys:
            errors.append(f"{name}: missing keys: {sorted(missing_case_keys)}")

        attitude = case.get("local_ned_attitude_deg")
        if not isinstance(attitude, dict):
            errors.append(f"{name}.local_ned_attitude_deg: expected object")
        else:
            missing_attitude_keys = REQUIRED_ATTITUDE_KEYS - set(attitude)
            if missing_attitude_keys:
                errors.append(f"{name}.local_ned_attitude_deg missing keys: {sorted(missing_attitude_keys)}")
            for key in REQUIRED_ATTITUDE_KEYS & set(attitude):
                if not is_number(attitude[key]):
                    errors.append(f"{name}.local_ned_attitude_deg.{key}: expected finite number")

        expected = case.get("expected")
        if not isinstance(expected, dict):
            errors.append(f"{name}.expected: expected object")
            continue
        missing_expected_keys = REQUIRED_EXPECTED_KEYS - set(expected)
        if missing_expected_keys:
            errors.append(f"{name}.expected missing keys: {sorted(missing_expected_keys)}")

        dis = expected.get("dis_deg")
        if not isinstance(dis, dict):
            errors.append(f"{name}.expected.dis_deg: expected object")
        else:
            missing_dis_keys = REQUIRED_DIS_KEYS - set(dis)
            if missing_dis_keys:
                errors.append(f"{name}.expected.dis_deg missing keys: {sorted(missing_dis_keys)}")
            for key in REQUIRED_DIS_KEYS & set(dis):
                if not is_number(dis[key]):
                    errors.append(f"{name}.expected.dis_deg.{key}: expected finite number")

        vectors: dict[str, list[float]] = {}
        for key in REQUIRED_EXPECTED_KEYS - {"dis_deg"}:
            vector = validate_unit_vector(f"{name}.expected.{key}", expected.get(key), errors)
            if vector is not None:
                vectors[key] = vector

        basis_specs = {
            "body_frd_ecef": ("body_forward_ecef", "body_right_ecef", "body_down_ecef"),
            "body_fru_enu": ("body_forward_enu", "body_right_enu", "body_up_enu"),
            "unreal": ("unreal_forward", "unreal_right", "unreal_up"),
            "godot": ("godot_forward", "godot_right", "godot_up"),
            "unity": ("unity_forward", "unity_right", "unity_up"),
        }
        basis_summary: dict[str, dict[str, float]] = {}
        for label, keys in basis_specs.items():
            if all(key in vectors for key in keys):
                summary = validate_basis(name, label, {key: vectors[key] for key in keys}, errors)
                basis_summary[label] = summary
                max_abs_dot = max(max_abs_dot, summary["max_abs_dot"])
                min_abs_det = min(min_abs_det, abs(summary["determinant"]))

        if "east_ecef" in expected:
            for key in ("east_ecef", "north_ecef", "up_ecef"):
                validate_unit_vector(f"{name}.expected.{key}", expected.get(key), errors)
        elif name.startswith("equator_"):
            warnings.append(f"{name}: equator/pole sanity case has no explicit georeference basis vectors")

        case_summaries.append({"name": name, "basis": basis_summary})

    status = "pass" if not errors else "fail"
    return {
        "schema": "fastdis.orientation_fixture_contract_report.v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "fixture": display_path(fixture_path),
        "status": status,
        "case_count": len(cases),
        "max_abs_basis_dot": max_abs_dot,
        "min_abs_basis_determinant": min_abs_det,
        "errors": errors,
        "warnings": warnings,
        "cases": case_summaries,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Orientation Fixture Contract Report",
        "",
        f"- generated_at: `{report['generated_at']}`",
        f"- fixture: `{report['fixture']}`",
        f"- status: `{report['status']}`",
        f"- case_count: `{report['case_count']}`",
        f"- max_abs_basis_dot: `{report['max_abs_basis_dot']:.12e}`",
        f"- min_abs_basis_determinant: `{report['min_abs_basis_determinant']:.12f}`",
        "",
        "## Errors",
        "",
    ]
    if report["errors"]:
        lines.extend(f"- {error}" for error in report["errors"])
    else:
        lines.append("- none")
    lines.extend(["", "## Warnings", ""])
    if report["warnings"]:
        lines.extend(f"- {warning}" for warning in report["warnings"])
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    out_dir = args.out_dir.expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    report = validate_fixture(args.fixture.expanduser().resolve())
    json_path = out_dir / "fixture_contract_report.json"
    md_path = out_dir / "fixture_contract_report.md"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(f"orientation fixture contract: {report['status']}")
        print(f"report: {display_path(md_path)}")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
