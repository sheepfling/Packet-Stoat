import json
import math
import random
import sys
from pathlib import Path

import pytest


TESTS_DIR = Path(__file__).parent
GOLDEN_FIXTURE = TESTS_DIR / "data" / "orientation_golden_cases.json"
sys.path.insert(0, str(TESTS_DIR / "oracles"))
import orientation_oracle as oracle


def _angle_between(a: list[float], b: list[float]) -> float:
    da = oracle.normalize(a)
    db = oracle.normalize(b)
    dot = max(-1.0, min(1.0, oracle.dot(da, db)))
    return math.degrees(math.acos(dot))


def _assert_basis(body: dict[str, list[float]]) -> None:
    forward = body["forward_ecef"]
    right = body["right_ecef"]
    down = body["down_ecef"]
    assert oracle.norm(forward) == pytest.approx(1.0, abs=1e-12)
    assert oracle.norm(right) == pytest.approx(1.0, abs=1e-12)
    assert oracle.norm(down) == pytest.approx(1.0, abs=1e-12)
    assert oracle.dot(forward, right) == pytest.approx(0.0, abs=1e-12)
    assert oracle.dot(forward, down) == pytest.approx(0.0, abs=1e-12)
    assert oracle.dot(right, down) == pytest.approx(0.0, abs=1e-12)
    assert oracle.determinant(forward, right, down) == pytest.approx(1.0, abs=1e-12)


def test_orientation_golden_fixture_matches_oracle() -> None:
    fixture = json.loads(GOLDEN_FIXTURE.read_text())
    assert fixture["schema"] == "fastdis.orientation_golden_cases.v1"

    for case in fixture["cases"]:
        result = oracle.build_case_result(case)
        expected = case["expected"]
        for key in ("body_forward_enu", "body_right_enu", "body_up_enu"):
            for actual, want in zip(result[key], expected[key]):
                assert actual == pytest.approx(want, abs=1e-9), case["name"]
        for axis in ("psi", "theta", "phi"):
            assert result["dis_deg"][axis] == pytest.approx(expected["dis_deg"][axis], abs=1e-9), case["name"]
        if "reference_dis_deg_rounded" in expected:
            for axis in ("psi", "theta", "phi"):
                assert result["dis_deg"][axis] == pytest.approx(expected["reference_dis_deg_rounded"][axis], abs=0.05), case["name"]


def test_orientation_oracle_roundtrip_matches_dis_convention() -> None:
    fixture = json.loads(GOLDEN_FIXTURE.read_text())
    for case in fixture["cases"]:
        result = oracle.build_case_result(case)
        body_from_dis = oracle.dis_psi_theta_phi_to_body_frd_ecef(
            result["dis_deg"]["psi"],
            result["dis_deg"]["theta"],
            result["dis_deg"]["phi"],
        )
        _assert_basis(body_from_dis)
        assert _angle_between(result["body_forward_ecef"], body_from_dis["forward_ecef"]) <= 1e-9
        if abs(abs(result["dis_deg"]["theta"]) - 90.0) > 1e-6:
            assert _angle_between(result["body_right_ecef"], body_from_dis["right_ecef"]) <= 1e-9
            assert _angle_between(result["body_down_ecef"], body_from_dis["down_ecef"]) <= 1e-9


def test_orientation_oracle_randomized_roundtrip_properties() -> None:
    random.seed(1278)
    for _ in range(250):
        lat_deg = random.uniform(-89.9, 89.9)
        lon_deg = random.uniform(-180.0, 180.0)
        heading_deg = random.uniform(0.0, 360.0)
        pitch_deg = random.uniform(-85.0, 85.0)
        roll_deg = random.uniform(-180.0, 180.0)
        body_fru_enu = oracle.local_ned_attitude_to_body_fru_enu(heading_deg, pitch_deg, roll_deg)
        body_frd_ecef = oracle.body_fru_enu_to_body_frd_ecef(body_fru_enu, lat_deg, lon_deg)
        _assert_basis(body_frd_ecef)

        dis_deg = oracle.body_frd_ecef_to_dis_psi_theta_phi(body_frd_ecef)
        roundtrip = oracle.dis_psi_theta_phi_to_body_frd_ecef(
            dis_deg["psi"],
            dis_deg["theta"],
            dis_deg["phi"],
        )
        _assert_basis(roundtrip)
        assert _angle_between(body_frd_ecef["forward_ecef"], roundtrip["forward_ecef"]) <= 1e-8
        if abs(abs(dis_deg["theta"]) - 90.0) > 1e-6:
            assert _angle_between(body_frd_ecef["right_ecef"], roundtrip["right_ecef"]) <= 1e-5
            assert _angle_between(body_frd_ecef["down_ecef"], roundtrip["down_ecef"]) <= 1e-5

        for target in oracle.TARGET_FRAMES:
            target_basis = oracle.map_body_fru_enu_to_target_basis(body_fru_enu, target)
            assert oracle.norm(target_basis["forward"]) == pytest.approx(1.0, abs=1e-12)
            assert oracle.norm(target_basis["right"]) == pytest.approx(1.0, abs=1e-12)
            assert oracle.norm(target_basis["up"]) == pytest.approx(1.0, abs=1e-12)
