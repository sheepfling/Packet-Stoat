import json
import math
from pathlib import Path

import pytest


FIXTURE = Path(__file__).parent / "data" / "orientation_engine_cases.json"


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def _norm(a: list[float]) -> float:
    return math.sqrt(_dot(a, a))


def _assert_vec_close(actual: list[float], expected: list[float], tol: float = 1e-8) -> None:
    assert len(actual) == 3
    assert len(expected) == 3
    for a, e in zip(actual, expected):
        assert a == pytest.approx(e, abs=tol)


def _enu_to_unreal(v: list[float]) -> list[float]:
    east, north, up = v
    return [north, east, up]


def _enu_to_godot(v: list[float]) -> list[float]:
    east, north, up = v
    return [east, up, -north]


def test_orientation_engine_fixture_schema_and_basis_vectors() -> None:
    fixture = json.loads(FIXTURE.read_text())
    assert fixture["schema"] == "fastdis.orientation_engine_cases.v1"
    assert fixture["cases"]

    for case in fixture["cases"]:
        expected = case["expected"]
        forward = expected["body_forward_enu"]
        right = expected["body_right_enu"]
        up = expected["body_up_enu"]

        assert _norm(forward) == pytest.approx(1.0, abs=1e-8), case["name"]
        assert _norm(right) == pytest.approx(1.0, abs=1e-8), case["name"]
        assert _norm(up) == pytest.approx(1.0, abs=1e-8), case["name"]
        assert _dot(forward, right) == pytest.approx(0.0, abs=1e-8), case["name"]
        assert _dot(forward, up) == pytest.approx(0.0, abs=1e-8), case["name"]
        assert _dot(right, up) == pytest.approx(0.0, abs=1e-8), case["name"]

        _assert_vec_close(expected["unreal_forward"], _enu_to_unreal(forward))
        _assert_vec_close(expected["unreal_right"], _enu_to_unreal(right))
        _assert_vec_close(expected["unreal_up"], _enu_to_unreal(up))

        _assert_vec_close(expected["godot_forward"], _enu_to_godot(forward))
        _assert_vec_close(expected["godot_right"], _enu_to_godot(right))
        _assert_vec_close(expected["godot_up"], _enu_to_godot(up))
