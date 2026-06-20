from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest
import sympy as sp


ROOT = Path(__file__).resolve().parents[1]
TESTS_DIR = Path(__file__).parent
sys.path.insert(0, str(TESTS_DIR / "oracles"))
import orientation_oracle as oracle


def _ensure_orientation_formulas() -> Path:
    path = ROOT / "generated" / "orientation_formulas.json"
    if path.exists():
        return path
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "derive_orientation_matrices.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return path


_SP_NAMESPACE = {name: getattr(sp, name) for name in dir(sp) if not name.startswith("_")}
PSI = sp.Symbol("psi", real=True)
THETA = sp.Symbol("theta", real=True)
PHI = sp.Symbol("phi", real=True)
LAT = sp.Symbol("lat", real=True)
LON = sp.Symbol("lon", real=True)


def _expr_from_srepr(value: str) -> sp.Expr:
    return eval(value, {"__builtins__": {}}, _SP_NAMESPACE)


def _matrix_from_srepr(entries: list[list[str]]) -> sp.Matrix:
    return sp.Matrix([[_expr_from_srepr(value) for value in row] for row in entries])


def test_derived_orientation_formulas_match_current_generator() -> None:
    _ensure_orientation_formulas()
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "derive_orientation_matrices.py"), "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_sympy_generated_rotation_matrix_matches_python_oracle_sample() -> None:
    payload = json.loads(_ensure_orientation_formulas().read_text(encoding="utf-8"))
    matrix = _matrix_from_srepr(payload["dis_body_matrix_ecef"]["entries_srepr"])
    sample = payload["sample_case"]
    psi = sp.Float(sample["psi_deg"]) * sp.pi / 180
    theta = sp.Float(sample["theta_deg"]) * sp.pi / 180
    phi = sp.Float(sample["phi_deg"]) * sp.pi / 180
    evaluated = matrix.subs({PSI: psi, THETA: theta, PHI: phi}).evalf()

    expected = oracle.dis_psi_theta_phi_to_body_frd_ecef(
        sample["psi_deg"], sample["theta_deg"], sample["phi_deg"]
    )
    for col, key in enumerate(("forward_ecef", "right_ecef", "down_ecef")):
        for row in range(3):
            assert float(evaluated[row, col]) == pytest.approx(expected[key][row], abs=1e-12)


def test_sympy_generated_enu_basis_matches_python_oracle_sample() -> None:
    payload = json.loads(_ensure_orientation_formulas().read_text(encoding="utf-8"))
    matrix = _matrix_from_srepr(payload["enu_from_ecef_matrix"]["entries_srepr"])
    sample = payload["sample_case"]
    lat = sp.Float(sample["lat_deg"]) * sp.pi / 180
    lon = sp.Float(sample["lon_deg"]) * sp.pi / 180
    evaluated = matrix.subs({LAT: lat, LON: lon}).evalf()

    basis = oracle.local_enu_basis(sample["lat_deg"], sample["lon_deg"])
    expected_rows = [basis["east"], basis["north"], basis["up"]]
    for row in range(3):
        for col in range(3):
            assert float(evaluated[row, col]) == pytest.approx(expected_rows[row][col], abs=1e-12)


def test_sympy_proofs_encode_orthonormal_rotation() -> None:
    payload = json.loads(_ensure_orientation_formulas().read_text(encoding="utf-8"))
    orthogonality = _matrix_from_srepr(payload["proofs"]["dis_body_matrix_transpose_times_self_srepr"])
    determinant = _expr_from_srepr(payload["proofs"]["dis_body_matrix_determinant_srepr"])
    assert orthogonality == sp.eye(3)
    assert sp.simplify(determinant - 1) == 0
