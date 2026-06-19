# In-Engine Orientation Verification

Alpha 2 does not treat orientation as complete until it passes inside the target
engine transform systems. Native math tests prove the fastdis basis pipeline;
engine tests prove the final actor/node transforms survive each engine's
handedness, axis, unit, import, and frame-timing rules.

## Layers

1. Native math tests verify ECEF, ENU, DIS body-FRD, and target-frame mapping
   outside any engine.
2. In-engine numerical tests spawn actors/nodes, apply fastdis poses, read
   engine basis vectors, and compare against shared fixtures.
3. In-engine visual scenes draw expected and actual body axes with numeric
   pass/fail overlays.

Layer 2 is mandatory. Visual scenes are diagnostic; they are not the authority.

## Shared Fixtures

Both engines must load:

```text
tests/data/orientation_engine_cases.json
```

Each case defines expected canonical outputs:

```text
body_forward_enu
body_right_enu
body_up_enu
unreal_forward/right/up
godot_forward/right/up
```

Engine tests must not recompute expected values independently. They should apply
the fastdis transform path to an actor/node, read the engine's actual basis, and
compare against the JSON fixture.

The initial fixture set covers axis-aligned local ENU cases, climb, bank,
equator/prime-meridian basis sanity, and near-pole stress. DIS `psi/theta/phi`
golden values are added by the independent oracle workstream.

## Unreal Verification

Unreal standalone mapping:

```text
local ENU meters -> Unreal centimeters
north -> +X
 east -> +Y
   up -> +Z
```

The numerical test reads:

```cpp
Actor->GetActorForwardVector(); // actor local +X
Actor->GetActorRightVector();   // actor local +Y
Actor->GetActorUpVector();      // actor local +Z
```

Those vectors are compared to the fixture's `unreal_forward`, `unreal_right`,
and `unreal_up` entries using angular error, not Euler triples.

Required artifacts:

```text
examples/unreal/FastDisOrientationVerification/
  FastDisOrientationVerification.uproject
  Source/FastDisOrientationTests/
    FastDisOrientationTests.Build.cs
    Public/FastDisOrientationProbeActor.h
    Private/FastDisOrientation.spec.cpp
    Private/FastDisOrientationProbeActor.cpp
```

Command-line target:

`python tools/run_unreal_orientation_verification.py`

The verification actor should draw:

```text
solid red    actual forward
solid green  actual right
solid blue   actual up
dashed red   expected forward
dashed green expected right
dashed blue  expected up
```

It should print per-case dot products, angular errors, and PASS/FAIL.

## Godot Verification

Godot standalone mapping:

```text
local ENU meters -> Godot meters
 east -> +X
   up -> +Y
north -> -Z
```

The numerical test reads:

```cpp
Basis basis = node->get_global_transform().basis;
Vector3 right = basis.x;
Vector3 up = basis.y;
Vector3 forward = -basis.z;
```

GDScript tests should read the same basis after one process frame or after an
explicit transform flush path, because immediate global transform reads can be
frame-timing dependent.

Required artifacts:

```text
examples/godot/fastdis_orientation_verification/
  project.godot
  scenes/orientation_verification.tscn
  scripts/run_orientation_tests.gd
  tests/orientation_engine_cases.json
```

Headless target:

`python tools/run_godot_orientation_verification.py`

The visual scene should draw:

```text
red    actual forward = -basis.z
green  actual right   = basis.x
blue   actual up      = basis.y
dashed expected axes
```

It should display case name, basis determinant, dot products,
`max_angle_error_deg`, and PASS/FAIL.

## Asset-Basis Verification

Engine basis correctness is not enough. Meshes may be authored with a different
front/up convention than the actor/node basis.

Unreal asset probe:

```text
NoseMarker      local +X
RightWingMarker local +Y
TopMarker       local +Z
```

Godot asset probe:

```text
Node forward mode:  Vector3.FORWARD = (0, 0, -1)
Model front mode:   Vector3.MODEL_FRONT = (0, 0, 1)
```

Every imported asset path must declare:

```text
AssetForwardAxis = +X / -X / +Y / -Y / +Z / -Z
AssetUpAxis      = +Z / +Y / ...
```

No hidden mesh correction is allowed. If an adapter applies an asset correction,
the test must verify marker world directions against expected body axes.

## Tolerances

Engine-facing tests:

```text
axis angular error <= 0.01 degree
axis component error <= 1e-5
basis orthogonality error <= 1e-5
location error near origin <= 1 cm
```

The primary direction assertion is:

```text
angle = acos(clamp(dot(normalize(actual), normalize(expected)), -1, 1))
```

Euler comparisons are not accepted as primary correctness checks.

## Alpha 2 Done Criteria

Unreal:

- `FastDis.Orientation` automation spec passes from command line.
- Probe actor reports actor forward/right/up vectors matching fixtures.
- Visual scene shows expected and actual axes.
- Asset-basis correction test exists.

Godot:

- Headless orientation script passes.
- Visual scene reports expected and actual axes.
- Basis `x`, `y`, and `-z` match fixtures.
- Node-forward vs model-front asset test exists.

Shared:

- Native, Unreal, and Godot tests consume the same fixture file.
- All comparisons are vector/quaternion based.
- Orientation remains opt-in until these checks pass.
