#!/usr/bin/env python3
"""Generate symbolic orientation/frame formulas used by Alpha 3 verification."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import sympy as sp


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "generated" / "orientation_formulas.json"


def build_payload() -> dict[str, object]:
    psi, theta, phi = sp.symbols("psi theta phi", real=True)
    lat, lon = sp.symbols("lat lon", real=True)

    rot_z = sp.Matrix(
        [
            [sp.cos(psi), -sp.sin(psi), 0],
            [sp.sin(psi), sp.cos(psi), 0],
            [0, 0, 1],
        ]
    )
    rot_y = sp.Matrix(
        [
            [sp.cos(theta), 0, sp.sin(theta)],
            [0, 1, 0],
            [-sp.sin(theta), 0, sp.cos(theta)],
        ]
    )
    rot_x = sp.Matrix(
        [
            [1, 0, 0],
            [0, sp.cos(phi), -sp.sin(phi)],
            [0, sp.sin(phi), sp.cos(phi)],
        ]
    )
    dis_matrix = sp.simplify(rot_z * rot_y * rot_x)

    east = sp.Matrix([-sp.sin(lon), sp.cos(lon), 0])
    north = sp.Matrix([-sp.sin(lat) * sp.cos(lon), -sp.sin(lat) * sp.sin(lon), sp.cos(lat)])
    up = sp.Matrix([sp.cos(lat) * sp.cos(lon), sp.cos(lat) * sp.sin(lon), sp.sin(lat)])
    enu_from_ecef = sp.Matrix.vstack(east.T, north.T, up.T)

    orthogonality = sp.simplify(dis_matrix.T * dis_matrix)
    determinant = sp.simplify(dis_matrix.det())

    sample_values = {
        psi: sp.Float("-122.969920706961") * sp.pi / 180,
        theta: sp.Float("47.786474780005") * sp.pi / 180,
        phi: sp.Float("-29.670167146766") * sp.pi / 180,
        lat: sp.Float("-34.9") * sp.pi / 180,
        lon: sp.Float("138.5") * sp.pi / 180,
    }

    def matrix_to_strings(matrix: sp.Matrix) -> list[list[str]]:
        return [[sp.srepr(sp.simplify(matrix[r, c])) for c in range(matrix.cols)] for r in range(matrix.rows)]

    def matrix_to_eval(matrix: sp.Matrix) -> list[list[float]]:
        evaluated = matrix.subs(sample_values).evalf()
        return [[float(evaluated[r, c]) for c in range(evaluated.cols)] for r in range(evaluated.rows)]

    return {
        "schema": "fastdis.orientation_formulas.v1",
        "notes": [
            "DIS orientation matrix is Rz(psi) * Ry(theta) * Rx(phi).",
            "Matrix columns are body +X/+Y/+Z expressed in ECEF.",
            "ENU basis rows map ECEF vectors into local east/north/up components.",
        ],
        "symbols": {
            "psi": "DIS rotation about ECEF Z, radians",
            "theta": "DIS rotation about rotated Y, radians",
            "phi": "DIS rotation about rotated X, radians",
            "lat": "geodetic latitude, radians",
            "lon": "geodetic longitude, radians",
        },
        "dis_body_matrix_ecef": {
            "entries_srepr": matrix_to_strings(dis_matrix),
            "sample_eval": matrix_to_eval(dis_matrix),
        },
        "enu_from_ecef_matrix": {
            "entries_srepr": matrix_to_strings(enu_from_ecef),
            "sample_eval": matrix_to_eval(enu_from_ecef),
        },
        "proofs": {
            "dis_body_matrix_transpose_times_self_srepr": matrix_to_strings(orthogonality),
            "dis_body_matrix_determinant_srepr": sp.srepr(determinant),
        },
        "sample_case": {
            "name": "adelaide_heading_135_pitch_20_roll_30",
            "psi_deg": -122.969920706961,
            "theta_deg": 47.786474780005,
            "phi_deg": -29.670167146766,
            "lat_deg": -34.9,
            "lon_deg": 138.5,
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--check", action="store_true", help="Verify the generated file is up to date.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = build_payload()
    text = json.dumps(payload, indent=2) + "\n"
    if args.check:
        if not args.out.exists():
            print(f"missing generated file: {args.out.relative_to(ROOT)}", file=sys.stderr)
            return 1
        if args.out.read_text(encoding="utf-8") != text:
            print(f"stale generated file: {args.out.relative_to(ROOT)}", file=sys.stderr)
            return 1
        print("orientation formulas are up to date")
        return 0
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(text, encoding="utf-8")
    print(f"wrote {args.out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
