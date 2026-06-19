from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


TARGET_FRAMES = (
    "StandaloneUnrealNorthEastUp",
    "StandaloneUnityEastUpNorth",
    "StandaloneGodotEastUpMinusNorth",
    "CesiumJsEastNorthUp",
    "CesiumUnityEastUpNorth",
    "CesiumUnrealEastSouthUp",
)


def dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def cross(a: list[float], b: list[float]) -> list[float]:
    return [
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    ]


def norm(a: list[float]) -> float:
    return math.sqrt(dot(a, a))


def normalize(a: list[float]) -> list[float]:
    n = norm(a)
    if n == 0.0:
        return [0.0, 0.0, 0.0]
    return [x / n for x in a]


def determinant(x: list[float], y: list[float], z: list[float]) -> float:
    return dot(x, cross(y, z))


def rodrigues_rotate(v: list[float], axis: list[float], angle_rad: float) -> list[float]:
    unit_axis = normalize(axis)
    c = math.cos(angle_rad)
    s = math.sin(angle_rad)
    axis_cross_v = cross(unit_axis, v)
    axis_dot_v = dot(unit_axis, v)
    return [
        v[0] * c + axis_cross_v[0] * s + unit_axis[0] * axis_dot_v * (1.0 - c),
        v[1] * c + axis_cross_v[1] * s + unit_axis[1] * axis_dot_v * (1.0 - c),
        v[2] * c + axis_cross_v[2] * s + unit_axis[2] * axis_dot_v * (1.0 - c),
    ]


def geodetic_to_ecef(lat_deg: float, lon_deg: float, height_m: float) -> list[float]:
    a = 6378137.0
    inv_f = 298.257223563
    f = 1.0 / inv_f
    e2 = f * (2.0 - f)
    lat = math.radians(lat_deg)
    lon = math.radians(lon_deg)
    sin_lat = math.sin(lat)
    cos_lat = math.cos(lat)
    sin_lon = math.sin(lon)
    cos_lon = math.cos(lon)
    n = a / math.sqrt(1.0 - e2 * sin_lat * sin_lat)
    return [
        (n + height_m) * cos_lat * cos_lon,
        (n + height_m) * cos_lat * sin_lon,
        (n * (1.0 - e2) + height_m) * sin_lat,
    ]


def local_enu_basis(lat_deg: float, lon_deg: float) -> dict[str, list[float]]:
    lat = math.radians(lat_deg)
    lon = math.radians(lon_deg)
    sin_lat = math.sin(lat)
    cos_lat = math.cos(lat)
    sin_lon = math.sin(lon)
    cos_lon = math.cos(lon)
    east = [-sin_lon, cos_lon, 0.0]
    north = [-sin_lat * cos_lon, -sin_lat * sin_lon, cos_lat]
    up = [cos_lat * cos_lon, cos_lat * sin_lon, sin_lat]
    return {
        "east": east,
        "north": north,
        "up": up,
        "origin_ecef": geodetic_to_ecef(lat_deg, lon_deg, 0.0),
    }


def enu_direction_to_ecef(v_enu: list[float], basis: dict[str, list[float]]) -> list[float]:
    east = basis["east"]
    north = basis["north"]
    up = basis["up"]
    return [
        v_enu[0] * east[0] + v_enu[1] * north[0] + v_enu[2] * up[0],
        v_enu[0] * east[1] + v_enu[1] * north[1] + v_enu[2] * up[1],
        v_enu[0] * east[2] + v_enu[1] * north[2] + v_enu[2] * up[2],
    ]


def ecef_direction_to_enu(v_ecef: list[float], basis: dict[str, list[float]]) -> list[float]:
    return [
        dot(v_ecef, basis["east"]),
        dot(v_ecef, basis["north"]),
        dot(v_ecef, basis["up"]),
    ]


def local_ned_attitude_to_body_fru_enu(heading_deg: float, pitch_deg: float, roll_deg: float) -> dict[str, list[float]]:
    heading = math.radians(heading_deg)
    pitch = math.radians(pitch_deg)
    roll = math.radians(roll_deg)

    forward0 = [math.sin(heading), math.cos(heading), 0.0]
    right0 = [math.cos(heading), -math.sin(heading), 0.0]
    up0 = [0.0, 0.0, 1.0]

    forward1 = normalize(rodrigues_rotate(forward0, right0, pitch))
    up1 = normalize(rodrigues_rotate(up0, right0, pitch))
    right1 = normalize(right0)

    right2 = normalize(rodrigues_rotate(right1, forward1, roll))
    up2 = normalize(rodrigues_rotate(up1, forward1, roll))
    return {
        "forward_enu": forward1,
        "right_enu": right2,
        "up_enu": up2,
    }


def body_fru_enu_to_body_frd_ecef(body_fru_enu: dict[str, list[float]], lat_deg: float, lon_deg: float) -> dict[str, list[float]]:
    basis = local_enu_basis(lat_deg, lon_deg)
    return {
        "forward_ecef": normalize(enu_direction_to_ecef(body_fru_enu["forward_enu"], basis)),
        "right_ecef": normalize(enu_direction_to_ecef(body_fru_enu["right_enu"], basis)),
        "down_ecef": normalize([-x for x in enu_direction_to_ecef(body_fru_enu["up_enu"], basis)]),
    }


def dis_psi_theta_phi_to_body_frd_ecef(psi_deg: float, theta_deg: float, phi_deg: float) -> dict[str, list[float]]:
    psi = math.radians(psi_deg)
    theta = math.radians(theta_deg)
    phi = math.radians(phi_deg)
    cpsi, spsi = math.cos(psi), math.sin(psi)
    ctheta, stheta = math.cos(theta), math.sin(theta)
    cphi, sphi = math.cos(phi), math.sin(phi)
    matrix = [
        [cpsi * ctheta, cpsi * stheta * sphi - spsi * cphi, cpsi * stheta * cphi + spsi * sphi],
        [spsi * ctheta, spsi * stheta * sphi + cpsi * cphi, spsi * stheta * cphi - cpsi * sphi],
        [-stheta, ctheta * sphi, ctheta * cphi],
    ]
    return {
        "forward_ecef": [matrix[0][0], matrix[1][0], matrix[2][0]],
        "right_ecef": [matrix[0][1], matrix[1][1], matrix[2][1]],
        "down_ecef": [matrix[0][2], matrix[1][2], matrix[2][2]],
    }


def body_frd_ecef_to_dis_psi_theta_phi(body_frd_ecef: dict[str, list[float]]) -> dict[str, float]:
    forward = body_frd_ecef["forward_ecef"]
    right = body_frd_ecef["right_ecef"]
    down = body_frd_ecef["down_ecef"]
    matrix = [
        [forward[0], right[0], down[0]],
        [forward[1], right[1], down[1]],
        [forward[2], right[2], down[2]],
    ]
    theta = math.asin(-matrix[2][0])
    psi = math.atan2(matrix[1][0], matrix[0][0])
    phi = math.atan2(matrix[2][1], matrix[2][2])
    return {
        "psi": math.degrees(psi),
        "theta": math.degrees(theta),
        "phi": math.degrees(phi),
    }


def body_frd_ecef_to_body_fru_enu(body_frd_ecef: dict[str, list[float]], lat_deg: float, lon_deg: float) -> dict[str, list[float]]:
    basis = local_enu_basis(lat_deg, lon_deg)
    return {
        "forward_enu": normalize(ecef_direction_to_enu(body_frd_ecef["forward_ecef"], basis)),
        "right_enu": normalize(ecef_direction_to_enu(body_frd_ecef["right_ecef"], basis)),
        "up_enu": normalize(ecef_direction_to_enu([-x for x in body_frd_ecef["down_ecef"]], basis)),
    }


def map_enu_direction_to_target(v_enu: list[float], target_frame: str) -> list[float]:
    east, north, up = v_enu
    if target_frame == "StandaloneUnrealNorthEastUp":
        return [north, east, up]
    if target_frame in {"StandaloneUnityEastUpNorth", "CesiumUnityEastUpNorth"}:
        return [east, up, north]
    if target_frame == "StandaloneGodotEastUpMinusNorth":
        return [east, up, -north]
    if target_frame == "CesiumJsEastNorthUp":
        return [east, north, up]
    if target_frame == "CesiumUnrealEastSouthUp":
        return [east, -north, up]
    raise ValueError(f"unknown target frame: {target_frame}")


def map_body_fru_enu_to_target_basis(body_fru_enu: dict[str, list[float]], target_frame: str) -> dict[str, list[float]]:
    return {
        "forward": normalize(map_enu_direction_to_target(body_fru_enu["forward_enu"], target_frame)),
        "right": normalize(map_enu_direction_to_target(body_fru_enu["right_enu"], target_frame)),
        "up": normalize(map_enu_direction_to_target(body_fru_enu["up_enu"], target_frame)),
    }


def build_case_result(case: dict[str, object]) -> dict[str, object]:
    attitude = case["local_ned_attitude_deg"]
    lat_deg = float(case["lat_deg"])
    lon_deg = float(case["lon_deg"])
    body_fru_enu = local_ned_attitude_to_body_fru_enu(
        float(attitude["heading"]),
        float(attitude["pitch"]),
        float(attitude["roll"]),
    )
    body_frd_ecef = body_fru_enu_to_body_frd_ecef(body_fru_enu, lat_deg, lon_deg)
    dis_deg = body_frd_ecef_to_dis_psi_theta_phi(body_frd_ecef)
    target_bases = {
        target: map_body_fru_enu_to_target_basis(body_fru_enu, target)
        for target in TARGET_FRAMES
    }
    return {
        "georeference": local_enu_basis(lat_deg, lon_deg),
        "body_forward_enu": body_fru_enu["forward_enu"],
        "body_right_enu": body_fru_enu["right_enu"],
        "body_up_enu": body_fru_enu["up_enu"],
        "body_forward_ecef": body_frd_ecef["forward_ecef"],
        "body_right_ecef": body_frd_ecef["right_ecef"],
        "body_down_ecef": body_frd_ecef["down_ecef"],
        "dis_deg": dis_deg,
        "targets": target_bases,
    }


def verify_fixture(path: Path) -> None:
    fixture = json.loads(path.read_text())
    for case in fixture["cases"]:
        result = build_case_result(case)
        expected = case["expected"]
        if "body_forward_enu" in expected:
            assert_vectors_close(result["body_forward_enu"], expected["body_forward_enu"], 1e-9, case["name"])
        if "body_right_enu" in expected:
            assert_vectors_close(result["body_right_enu"], expected["body_right_enu"], 1e-9, case["name"])
        if "body_up_enu" in expected:
            assert_vectors_close(result["body_up_enu"], expected["body_up_enu"], 1e-9, case["name"])
        if "dis_deg" in expected:
            assert_degrees_close(result["dis_deg"], expected["dis_deg"], 1e-9, case["name"])


def assert_vectors_close(actual: list[float], expected: list[float], tol: float, name: str) -> None:
    for a, e in zip(actual, expected):
        if abs(a - e) > tol:
            raise AssertionError(f"{name}: vector mismatch {actual} != {expected}")


def assert_degrees_close(actual: dict[str, float], expected: dict[str, float], tol: float, name: str) -> None:
    for key, value in expected.items():
        if abs(actual[key] - value) > tol:
            raise AssertionError(f"{name}: {key} mismatch {actual[key]} != {value}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fixture", type=Path, help="Fixture JSON file to verify or emit")
    parser.add_argument("--check", action="store_true", help="Verify the fixture instead of emitting computed values")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.check:
        verify_fixture(args.fixture)
        print(f"verified {args.fixture}")
        return 0

    fixture = json.loads(args.fixture.read_text())
    payload = {
        "schema": fixture["schema"],
        "cases": [
            {
                "name": case["name"],
                "computed": build_case_result(case),
            }
            for case in fixture["cases"]
        ],
    }
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
