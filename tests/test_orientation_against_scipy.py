from __future__ import annotations

import json
import math
from pathlib import Path
import random
import sys

import pytest
from scipy.spatial.transform import Rotation as R


TESTS_DIR = Path(__file__).parent
GOLDEN_FIXTURE = TESTS_DIR / "data" / "orientation_golden_cases.json"
sys.path.insert(0, str(TESTS_DIR / "oracles"))
import orientation_oracle as oracle


def _cols_from_rotation(rotation: R) -> dict[str, list[float]]:
    matrix = rotation.as_matrix()
    return {
        "forward_ecef": [float(matrix[0, 0]), float(matrix[1, 0]), float(matrix[2, 0])],
        "right_ecef": [float(matrix[0, 1]), float(matrix[1, 1]), float(matrix[2, 1])],
        "down_ecef": [float(matrix[0, 2]), float(matrix[1, 2]), float(matrix[2, 2])],
    }


def _angle_between(a: list[float], b: list[float]) -> float:
    da = oracle.normalize(a)
    db = oracle.normalize(b)
    dot = max(-1.0, min(1.0, oracle.dot(da, db)))
    return math.acos(dot)


def _assert_same_basis(actual: dict[str, list[float]], expected: dict[str, list[float]], tol_rad: float) -> None:
    assert _angle_between(actual["forward_ecef"], expected["forward_ecef"]) <= tol_rad
    assert _angle_between(actual["right_ecef"], expected["right_ecef"]) <= tol_rad
    assert _angle_between(actual["down_ecef"], expected["down_ecef"]) <= tol_rad


def test_golden_fixtures_match_scipy_intrinsic_zyx_interpretation() -> None:
    fixture = json.loads(GOLDEN_FIXTURE.read_text())
    for case in fixture["cases"]:
        result = oracle.build_case_result(case)
        dis_deg = result["dis_deg"]
        scipy_basis = _cols_from_rotation(R.from_euler("ZYX", [dis_deg["psi"], dis_deg["theta"], dis_deg["phi"]], degrees=True))
        expected_basis = oracle.dis_psi_theta_phi_to_body_frd_ecef(
            dis_deg["psi"], dis_deg["theta"], dis_deg["phi"]
        )
        _assert_same_basis(scipy_basis, expected_basis, 1e-12)


def test_randomized_dis_basis_matches_scipy_intrinsic_and_extrinsic_equivalents() -> None:
    random.seed(127801)
    for _ in range(250):
        psi = random.uniform(-180.0, 180.0)
        theta = random.uniform(-89.9, 89.9)
        phi = random.uniform(-180.0, 180.0)
        expected_basis = oracle.dis_psi_theta_phi_to_body_frd_ecef(psi, theta, phi)

        intrinsic = _cols_from_rotation(R.from_euler("ZYX", [psi, theta, phi], degrees=True))
        extrinsic = _cols_from_rotation(R.from_euler("xyz", [phi, theta, psi], degrees=True))

        _assert_same_basis(intrinsic, expected_basis, 1e-7)
        _assert_same_basis(extrinsic, expected_basis, 1e-7)


def test_scipy_matrix_roundtrip_preserves_basis_columns() -> None:
    fixture = json.loads(GOLDEN_FIXTURE.read_text())
    for case in fixture["cases"]:
        result = oracle.build_case_result(case)
        dis_deg = result["dis_deg"]
        rotation = R.from_euler("ZYX", [dis_deg["psi"], dis_deg["theta"], dis_deg["phi"]], degrees=True)
        roundtrip = R.from_matrix(rotation.as_matrix())
        _assert_same_basis(_cols_from_rotation(roundtrip), _cols_from_rotation(rotation), 1e-12)
