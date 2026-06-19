# Orientation Verification Plan

Orientation is a formal Alpha 2 workstream. The goal is not a convenience Euler
mapping; it is a basis/quaternion pipeline with named physical axes at every
step.

## Phase 1: API Contract

Add:

- `docs/ORIENTATION_CONVENTIONS.md`
- `docs/ORIENTATION_VERIFICATION.md`
- `include/fastdis/fastdis_orientation.hpp`
- `tests/native/test_orientation_conventions.cpp`

Contract:

- Internal orientation is body-FRD basis expressed in ECEF.
- Engine orientation output is basis/quaternion only.
- Euler output is diagnostic only.
- Position-only integration remains stable.
- Orientation integration remains experimental.

## Phase 2: Math-Kernel Tests

Native tests must verify:

- ECEF basis orthonormality.
- ENU basis orthonormality.
- Body FRD determinant is `+1`.
- DIS `psi/theta/phi` -> body basis determinant is `+1`.
- Body basis vectors remain unit length.
- Forward/right/down are mutually orthogonal.

Compare vectors and quaternions, not Euler triples.

## Phase 3: Golden Georeference Fixtures

Required origins:

- `0, 0, 0`: equator / prime meridian.
- `0, 90, 0`: equator / 90E.
- `45, 45, 0`: mid-latitude.
- `-34.9, 138.5`: Adelaide / Open-DIS tutorial-style case.
- `29.5597, -95.0831`: Houston / Ellington-style scenario.
- `89.999, 0`: near north pole.
- `-89.999, 45`: near south pole.

At `lat=0, lon=0`, expected ECEF basis:

```text
east_ecef  = (0, 1, 0)
north_ecef = (0, 0, 1)
up_ecef    = (1, 0, 0)
```

## Phase 4: DIS <-> Local NED Attitude Fixtures

Fixtures:

- level north.
- level east.
- level south.
- level west.
- climb north 20 degrees.
- bank right 30 degrees.
- combined heading 135, pitch 20, roll 30.

The Adelaide combined case should reproduce the Open-DIS tutorial result
approximately:

```text
psi   = -123.0 degrees
theta =   47.8 degrees
phi   =  -29.7 degrees
```

Then convert back and confirm heading/pitch/roll.

## Phase 5: Independent Oracle

Implemented:

- `tests/oracles/orientation_oracle.py`
- `tests/data/orientation_golden_cases.json`
- `tests/data/orientation_engine_cases.json` now carries oracle-verified ENU,
  ECEF, target-frame, and DIS-angle expectations shared by native, Unreal, and
  Godot tests.

The oracle should independently implement geodetic/ECEF bases, NED/ENU bases,
DIS `psi/theta/phi`, body basis conversion, and engine mappings.

## Phase 6: Target Engine Basis Tests

See `docs/ENGINE_ORIENTATION_VERIFICATION.md` for the in-engine test contract,
fixture format, command-line runner shape, and adapter done criteria.

Unreal:

- Standalone: body forward north -> actor `+X`; body right east -> `+Y`; body
  up -> `+Z`.
- Cesium Unreal ESU: body forward east -> `+X`; body forward south -> `+Y`;
  body up -> `+Z`.

Unity:

- Use `Quaternion.LookRotation(forward, up)`.
- Assert `transform.forward/right/up` against mapped expected vectors.

Godot:

- Use `Basis(right, up, back)`.
- Assert `basis.x`, `basis.y`, and `-basis.z`.
- Test node forward `-Z` and imported model front `+Z` modes.

Cesium:

- CesiumJS ENU matrix should match `eastNorthUpToFixedFrame`.
- Cesium Unity ECEF direction transform should match Cesium georeference output.
- Cesium Unreal ESU behavior should match GlobeAnchor / East-South-Up behavior.
- Alpha 2 now exercises these target-frame mappings in native/oracle tests via
  `tests/test_orientation_cesium.py`, using the shared orientation fixture set
  and explicit ENU -> CesiumJS / Cesium Unity / Cesium Unreal basis checks.

## Phase 7: Property Tests

Randomize:

- latitude in `[-89.9, 89.9]`.
- longitude in `[-180, 180]`.
- height in `[-1000 m, 100000 m]`.
- random unit quaternion body attitudes.
- heading/pitch/roll excluding singularity bands.
- near-singularity pitch cases.

Implemented in Python property tests with randomized latitude, longitude,
heading, pitch, and roll cases. The oracle verifies orthonormality,
determinant, finite output, DIS-angle roundtrips, and target-frame mappings.

Assertions:

- finite values.
- unit basis vectors.
- orthonormal bases.
- correct determinant.
- angular roundtrip error below threshold.
- no NaNs.

Primary angular error:

```text
2 * acos(abs(dot(q_expected, q_actual)))
```

## Phase 8: Visual Validation Scenes

Add scenes:

- `examples/unreal/FastDisOrientationVerification/`
- `examples/unity/FastDisOrientationVerification/`
- `examples/godot/fastdis_orientation_verification/`
- `examples/cesium/cesiumjs_orientation_verify/`

Each scene should render:

- red arrow: body forward / nose.
- green arrow: body right / starboard.
- blue arrow: body up.
- gray arrow: local north.
- yellow arrow: local east.
- cyan arrow: local up.

Visual pass/fail must be numeric dot products, not eyeballing.

## Phase 9: In-Engine Numerical Harnesses

Alpha 2 adds source-controlled harnesses:

- `examples/unreal/FastDisOrientationVerification/`
- `examples/godot/fastdis_orientation_verification/`
- `tests/data/orientation_engine_cases.json`

The current implementation validates each engine's basis-vector interpretation
against shared fixtures that include oracle-derived DIS `psi/theta/phi`, ECEF
body basis vectors, and target-frame outputs. The next implementation step is
to replace any remaining fixture-constructed basis use with the
adapter-produced `FTransform` or `Transform3D` after applying a fastdis
snapshot.

## Tolerances

Native double tests:

- basis norm error: `< 1e-12`.
- dot orthogonality error: `< 1e-12`.
- quaternion angular error: `< 1e-10 rad`.
- ECEF/ENU direction error: `< 1e-12`.

Engine float tests:

- axis component error: `< 1e-5`.
- angular error: `< 0.01 degree`.
- position error near origin: `1 mm` to `1 cm`, engine-dependent.
