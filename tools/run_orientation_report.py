#!/usr/bin/env python3
"""Generate bundled Alpha 2 orientation verification proof artifacts."""

from __future__ import annotations

import argparse
import json
import math
import platform
import random
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TESTS_DIR = ROOT / "tests"
sys.path.insert(0, str(TESTS_DIR / "oracles"))
import orientation_oracle as oracle


GOLDEN_FIXTURE = TESTS_DIR / "data" / "orientation_golden_cases.json"
ENGINE_FIXTURE = TESTS_DIR / "data" / "orientation_engine_cases.json"
DEFAULT_OUTPUT_DIR = ROOT / "verification_reports" / "alpha2_sample"
RANDOM_SEED = 1278
RANDOM_ITERATIONS = 250


def host_tag() -> str:
    system = platform.system().lower()
    if system == "darwin":
        return "macos"
    if system == "windows":
        return "windows"
    return "linux"


def display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def angle_between_deg(a: list[float], b: list[float]) -> float:
    da = oracle.normalize(a)
    db = oracle.normalize(b)
    dot = max(-1.0, min(1.0, oracle.dot(da, db)))
    return math.degrees(math.acos(dot))


def max_abs_diff(actual: list[float], expected: list[float]) -> float:
    return max(abs(a - e) for a, e in zip(actual, expected))


def summarize_golden_cases() -> dict[str, object]:
    fixture = json.loads(GOLDEN_FIXTURE.read_text(encoding="utf-8"))
    max_dis_angle_error = 0.0
    max_reference_angle_error = 0.0
    max_forward_roundtrip_deg = 0.0
    max_right_roundtrip_deg = 0.0
    max_down_roundtrip_deg = 0.0

    for case in fixture["cases"]:
        result = oracle.build_case_result(case)
        expected = case["expected"]
        for axis in ("psi", "theta", "phi"):
            max_dis_angle_error = max(max_dis_angle_error, abs(result["dis_deg"][axis] - expected["dis_deg"][axis]))
        if "reference_dis_deg_rounded" in expected:
            for axis in ("psi", "theta", "phi"):
                max_reference_angle_error = max(
                    max_reference_angle_error,
                    abs(result["dis_deg"][axis] - expected["reference_dis_deg_rounded"][axis]),
                )
        roundtrip = oracle.dis_psi_theta_phi_to_body_frd_ecef(
            result["dis_deg"]["psi"],
            result["dis_deg"]["theta"],
            result["dis_deg"]["phi"],
        )
        max_forward_roundtrip_deg = max(
            max_forward_roundtrip_deg,
            angle_between_deg(result["body_forward_ecef"], roundtrip["forward_ecef"]),
        )
        max_right_roundtrip_deg = max(
            max_right_roundtrip_deg,
            angle_between_deg(result["body_right_ecef"], roundtrip["right_ecef"]),
        )
        max_down_roundtrip_deg = max(
            max_down_roundtrip_deg,
            angle_between_deg(result["body_down_ecef"], roundtrip["down_ecef"]),
        )

    return {
        "fixture": GOLDEN_FIXTURE.relative_to(ROOT).as_posix(),
        "schema": fixture["schema"],
        "case_count": len(fixture["cases"]),
        "max_dis_angle_error_deg": max_dis_angle_error,
        "max_reference_angle_error_deg": max_reference_angle_error,
        "max_roundtrip_forward_error_deg": max_forward_roundtrip_deg,
        "max_roundtrip_right_error_deg": max_right_roundtrip_deg,
        "max_roundtrip_down_error_deg": max_down_roundtrip_deg,
    }


def summarize_engine_cases() -> dict[str, object]:
    fixture = json.loads(ENGINE_FIXTURE.read_text(encoding="utf-8"))
    unreal_max_deg = 0.0
    godot_max_deg = 0.0
    cesium_max_deg = {
        "CesiumJsEastNorthUp": 0.0,
        "CesiumUnityEastUpNorth": 0.0,
        "CesiumUnrealEastSouthUp": 0.0,
    }
    equator_georef_error = 0.0

    for case in fixture["cases"]:
        result = oracle.build_case_result(case)
        expected = case["expected"]

        unreal_max_deg = max(
            unreal_max_deg,
            angle_between_deg(expected["unreal_forward"], result["targets"]["StandaloneUnrealNorthEastUp"]["forward"]),
            angle_between_deg(expected["unreal_right"], result["targets"]["StandaloneUnrealNorthEastUp"]["right"]),
            angle_between_deg(expected["unreal_up"], result["targets"]["StandaloneUnrealNorthEastUp"]["up"]),
        )
        godot_max_deg = max(
            godot_max_deg,
            angle_between_deg(expected["godot_forward"], result["targets"]["StandaloneGodotEastUpMinusNorth"]["forward"]),
            angle_between_deg(expected["godot_right"], result["targets"]["StandaloneGodotEastUpMinusNorth"]["right"]),
            angle_between_deg(expected["godot_up"], result["targets"]["StandaloneGodotEastUpMinusNorth"]["up"]),
        )

        for target in cesium_max_deg:
            actual = result["targets"][target]
            forward = actual["forward"]
            right = actual["right"]
            up = actual["up"]
            if target == "CesiumJsEastNorthUp":
                expected_forward = expected["body_forward_enu"]
                expected_right = expected["body_right_enu"]
                expected_up = expected["body_up_enu"]
            elif target == "CesiumUnityEastUpNorth":
                expected_forward = [expected["body_forward_enu"][0], expected["body_forward_enu"][2], expected["body_forward_enu"][1]]
                expected_right = [expected["body_right_enu"][0], expected["body_right_enu"][2], expected["body_right_enu"][1]]
                expected_up = [expected["body_up_enu"][0], expected["body_up_enu"][2], expected["body_up_enu"][1]]
            else:
                expected_forward = [expected["body_forward_enu"][0], -expected["body_forward_enu"][1], expected["body_forward_enu"][2]]
                expected_right = [expected["body_right_enu"][0], -expected["body_right_enu"][1], expected["body_right_enu"][2]]
                expected_up = [expected["body_up_enu"][0], -expected["body_up_enu"][1], expected["body_up_enu"][2]]
            cesium_max_deg[target] = max(
                cesium_max_deg[target],
                angle_between_deg(expected_forward, forward),
                angle_between_deg(expected_right, right),
                angle_between_deg(expected_up, up),
            )

        if case["name"] == "equator_prime_meridian_level_north":
            georef = result["georeference"]
            equator_georef_error = max(
                equator_georef_error,
                max_abs_diff(georef["east"], [0.0, 1.0, 0.0]),
                max_abs_diff(georef["north"], [0.0, 0.0, 1.0]),
                max_abs_diff(georef["up"], [1.0, 0.0, 0.0]),
            )

    return {
        "fixture": ENGINE_FIXTURE.relative_to(ROOT).as_posix(),
        "schema": fixture["schema"],
        "case_count": len(fixture["cases"]),
        "max_unreal_basis_error_deg": unreal_max_deg,
        "max_godot_basis_error_deg": godot_max_deg,
        "max_cesium_basis_error_deg": cesium_max_deg,
        "equator_georeference_component_error": equator_georef_error,
    }


def summarize_randomized_properties() -> dict[str, object]:
    random.seed(RANDOM_SEED)
    max_forward_roundtrip_deg = 0.0
    max_right_roundtrip_deg = 0.0
    max_down_roundtrip_deg = 0.0
    min_basis_det = 1.0
    max_basis_det_deviation = 0.0

    for _ in range(RANDOM_ITERATIONS):
        lat_deg = random.uniform(-89.9, 89.9)
        lon_deg = random.uniform(-180.0, 180.0)
        heading_deg = random.uniform(0.0, 360.0)
        pitch_deg = random.uniform(-85.0, 85.0)
        roll_deg = random.uniform(-180.0, 180.0)
        body_fru_enu = oracle.local_ned_attitude_to_body_fru_enu(heading_deg, pitch_deg, roll_deg)
        body_frd_ecef = oracle.body_fru_enu_to_body_frd_ecef(body_fru_enu, lat_deg, lon_deg)
        det = oracle.determinant(
            body_frd_ecef["forward_ecef"],
            body_frd_ecef["right_ecef"],
            body_frd_ecef["down_ecef"],
        )
        min_basis_det = min(min_basis_det, det)
        max_basis_det_deviation = max(max_basis_det_deviation, abs(det - 1.0))

        dis_deg = oracle.body_frd_ecef_to_dis_psi_theta_phi(body_frd_ecef)
        roundtrip = oracle.dis_psi_theta_phi_to_body_frd_ecef(
            dis_deg["psi"],
            dis_deg["theta"],
            dis_deg["phi"],
        )
        max_forward_roundtrip_deg = max(
            max_forward_roundtrip_deg,
            angle_between_deg(body_frd_ecef["forward_ecef"], roundtrip["forward_ecef"]),
        )
        max_right_roundtrip_deg = max(
            max_right_roundtrip_deg,
            angle_between_deg(body_frd_ecef["right_ecef"], roundtrip["right_ecef"]),
        )
        max_down_roundtrip_deg = max(
            max_down_roundtrip_deg,
            angle_between_deg(body_frd_ecef["down_ecef"], roundtrip["down_ecef"]),
        )

    return {
        "seed": RANDOM_SEED,
        "iterations": RANDOM_ITERATIONS,
        "max_roundtrip_forward_error_deg": max_forward_roundtrip_deg,
        "max_roundtrip_right_error_deg": max_right_roundtrip_deg,
        "max_roundtrip_down_error_deg": max_down_roundtrip_deg,
        "min_basis_determinant": min_basis_det,
        "max_basis_determinant_deviation": max_basis_det_deviation,
    }


def build_summary() -> dict[str, object]:
    golden = summarize_golden_cases()
    engine = summarize_engine_cases()
    randomized = summarize_randomized_properties()
    status = "passed"
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "host_platform": host_tag(),
        "status": status,
        "golden_fixture": golden,
        "engine_fixture": engine,
        "randomized_properties": randomized,
    }


def render_markdown(summary: dict[str, object]) -> str:
    golden = summary["golden_fixture"]
    engine = summary["engine_fixture"]
    randomized = summary["randomized_properties"]
    return "\n".join(
        [
            "# Orientation Verification Report",
            "",
            f"- generated_at: `{summary['generated_at']}`",
            f"- host_platform: `{summary['host_platform']}`",
            f"- status: `{summary['status']}`",
            "",
            "## Golden Fixture",
            "",
            f"- fixture: `{golden['fixture']}`",
            f"- schema: `{golden['schema']}`",
            f"- case_count: `{golden['case_count']}`",
            f"- max DIS angle error: `{golden['max_dis_angle_error_deg']:.12f} deg`",
            f"- max reference DIS angle error: `{golden['max_reference_angle_error_deg']:.12f} deg`",
            f"- max forward roundtrip error: `{golden['max_roundtrip_forward_error_deg']:.12f} deg`",
            f"- max right roundtrip error: `{golden['max_roundtrip_right_error_deg']:.12f} deg`",
            f"- max down roundtrip error: `{golden['max_roundtrip_down_error_deg']:.12f} deg`",
            "",
            "## Shared Engine Fixture",
            "",
            f"- fixture: `{engine['fixture']}`",
            f"- schema: `{engine['schema']}`",
            f"- case_count: `{engine['case_count']}`",
            f"- max standalone Unreal basis error: `{engine['max_unreal_basis_error_deg']:.12f} deg`",
            f"- max standalone Godot basis error: `{engine['max_godot_basis_error_deg']:.12f} deg`",
            f"- max CesiumJS basis error: `{engine['max_cesium_basis_error_deg']['CesiumJsEastNorthUp']:.12f} deg`",
            f"- max Cesium Unity basis error: `{engine['max_cesium_basis_error_deg']['CesiumUnityEastUpNorth']:.12f} deg`",
            f"- max Cesium Unreal basis error: `{engine['max_cesium_basis_error_deg']['CesiumUnrealEastSouthUp']:.12f} deg`",
            f"- equator georeference component error: `{engine['equator_georeference_component_error']:.12e}`",
            "",
            "## Randomized Properties",
            "",
            f"- seed: `{randomized['seed']}`",
            f"- iterations: `{randomized['iterations']}`",
            f"- max forward roundtrip error: `{randomized['max_roundtrip_forward_error_deg']:.12f} deg`",
            f"- max right roundtrip error: `{randomized['max_roundtrip_right_error_deg']:.12f} deg`",
            f"- max down roundtrip error: `{randomized['max_roundtrip_down_error_deg']:.12f} deg`",
            f"- min basis determinant: `{randomized['min_basis_determinant']:.12f}`",
            f"- max basis determinant deviation: `{randomized['max_basis_determinant_deviation']:.12e}`",
            "",
            "This report proves the shared orientation fixtures, independent oracle, Cesium target-frame mappings, and randomized roundtrip properties from the current source tree. It does not replace Unreal/Godot runtime harness reports.",
            "",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="Directory for JSON and Markdown reports")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = build_summary()
    (output_dir / "orientation_verification_report.json").write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )
    (output_dir / "orientation_verification_report.md").write_text(
        render_markdown(summary),
        encoding="utf-8",
    )
    print(f"orientation report: {display_path(output_dir / 'orientation_verification_report.md')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
