import json
import math
import sys
from pathlib import Path

import pytest


FIXTURE = Path(__file__).parent / "data" / "orientation_engine_cases.json"
sys.path.insert(0, str(Path(__file__).parent / "oracles"))
import orientation_oracle as oracle


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def _norm(a: list[float]) -> float:
    return math.sqrt(_dot(a, a))


def _assert_vec_close(actual: list[float], expected: list[float], tol: float = 1e-8) -> None:
    assert len(actual) == 3
    assert len(expected) == 3
    for a, e in zip(actual, expected):
        assert a == pytest.approx(e, abs=tol)


def _enu_to_cesium_js(v: list[float]) -> list[float]:
    east, north, up = v
    return [east, north, up]


def _enu_to_cesium_unity(v: list[float]) -> list[float]:
    east, north, up = v
    return [east, up, north]


def _enu_to_cesium_unreal(v: list[float]) -> list[float]:
    east, north, up = v
    return [east, -north, up]


def _determinant(x: list[float], y: list[float], z: list[float]) -> float:
    return oracle.determinant(x, y, z)


def test_cesium_target_frames_match_shared_fixtures() -> None:
    fixture = json.loads(FIXTURE.read_text())
    assert fixture["schema"] == "fastdis.orientation_engine_cases.v1"

    for case in fixture["cases"]:
        expected = case["expected"]
        forward = expected["body_forward_enu"]
        right = expected["body_right_enu"]
        up = expected["body_up_enu"]

        result = oracle.build_case_result(case)
        cesium_js = result["targets"]["CesiumJsEastNorthUp"]
        cesium_unity = result["targets"]["CesiumUnityEastUpNorth"]
        cesium_unreal = result["targets"]["CesiumUnrealEastSouthUp"]

        _assert_vec_close(cesium_js["forward"], _enu_to_cesium_js(forward))
        _assert_vec_close(cesium_js["right"], _enu_to_cesium_js(right))
        _assert_vec_close(cesium_js["up"], _enu_to_cesium_js(up))

        _assert_vec_close(cesium_unity["forward"], _enu_to_cesium_unity(forward))
        _assert_vec_close(cesium_unity["right"], _enu_to_cesium_unity(right))
        _assert_vec_close(cesium_unity["up"], _enu_to_cesium_unity(up))

        _assert_vec_close(cesium_unreal["forward"], _enu_to_cesium_unreal(forward))
        _assert_vec_close(cesium_unreal["right"], _enu_to_cesium_unreal(right))
        _assert_vec_close(cesium_unreal["up"], _enu_to_cesium_unreal(up))


def test_cesium_target_bases_are_orthonormal_with_expected_handedness() -> None:
    fixture = json.loads(FIXTURE.read_text())
    for case in fixture["cases"]:
        result = oracle.build_case_result(case)
        for target_name in (
            "CesiumJsEastNorthUp",
            "CesiumUnityEastUpNorth",
            "CesiumUnrealEastSouthUp",
        ):
            basis = result["targets"][target_name]
            forward = basis["forward"]
            right = basis["right"]
            up = basis["up"]

            assert _norm(forward) == pytest.approx(1.0, abs=1e-8), (case["name"], target_name)
            assert _norm(right) == pytest.approx(1.0, abs=1e-8), (case["name"], target_name)
            assert _norm(up) == pytest.approx(1.0, abs=1e-8), (case["name"], target_name)
            assert _dot(forward, right) == pytest.approx(0.0, abs=1e-8), (case["name"], target_name)
            assert _dot(forward, up) == pytest.approx(0.0, abs=1e-8), (case["name"], target_name)
            assert _dot(right, up) == pytest.approx(0.0, abs=1e-8), (case["name"], target_name)
            assert abs(_determinant(forward, right, up)) == pytest.approx(1.0, abs=1e-8), (
                case["name"],
                target_name,
            )


def test_cesium_georeference_basis_matches_known_equator_origin() -> None:
    fixture = json.loads(FIXTURE.read_text())
    equator_case = next(case for case in fixture["cases"] if case["name"] == "equator_prime_meridian_level_north")
    result = oracle.build_case_result(equator_case)
    georef = result["georeference"]

    _assert_vec_close(georef["east"], [0.0, 1.0, 0.0], tol=1e-12)
    _assert_vec_close(georef["north"], [0.0, 0.0, 1.0], tol=1e-12)
    _assert_vec_close(georef["up"], [1.0, 0.0, 0.0], tol=1e-12)

    # CesiumJS ENU is the tangent basis itself; the equator/prime-meridian
    # origin is the simplest golden sanity check against ENU fixed-frame docs.
    cesium_js = result["targets"]["CesiumJsEastNorthUp"]
    _assert_vec_close(cesium_js["forward"], [0.0, 1.0, 0.0])
    _assert_vec_close(cesium_js["right"], [1.0, 0.0, 0.0])
    _assert_vec_close(cesium_js["up"], [0.0, 0.0, 1.0])
