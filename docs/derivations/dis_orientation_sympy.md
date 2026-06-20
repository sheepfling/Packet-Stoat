# DIS Orientation SymPy Derivation

Alpha 3 adds a symbolic verification lane for the DIS orientation matrix and
the ENU basis transform.

Generated artifact:

- `generated/orientation_formulas.json`

Generator:

```bash
python tools/derive_orientation_matrices.py
python tools/derive_orientation_matrices.py --check
```

What it proves:

- the DIS body-in-ECEF rotation matrix is `Rz(psi) * Ry(theta) * Rx(phi)`
- the matrix columns are body `+X/+Y/+Z` in ECEF coordinates
- `RᵀR = I`
- `det(R) = 1`
- the ENU-from-ECEF basis rows match the standard east/north/up formulas

The generated JSON stores:

- symbolic matrix entries as SymPy `srepr` strings
- symbolic orthogonality and determinant proof artifacts
- one concrete evaluated sample for the Adelaide golden case

The runtime tests compare that generated symbolic output back against the
independent Python oracle. This keeps SymPy as a derivation/proof dependency,
not a runtime dependency of the fastdis library itself.
