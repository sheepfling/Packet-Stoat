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

The current bundled runtime proof artifact is:

```text
verification_reports/alpha2_sample/orientation_runtime_report.md
```

Generate it with:

```bash
python tools/run_orientation_runtime_report.py --engine-version 5.8
```

That report captures structured `FASTDIS_ORIENTATION_PASS/FAIL` lines from the
Unreal and Godot runtime harnesses, plus raw log artifacts with per-case
angular error and dot-product values.

The current bundled visual-scene style proof artifact is:

```text
verification_reports/alpha2_sample/orientation_visual_report.md
```

Generate it with:

```bash
python tools/run_orientation_visual_report.py --engine-version 5.8
```

That report captures structured `FASTDIS_ORIENTATION_SCENE` lines from the
Unreal probe-style output and the Godot visual scene runner, plus raw logs for
those scene-style passes.

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

The current Alpha 2 harnesses now synthesize a snapshot at the local origin and
run it through the adapter-produced transform helpers:

- Unreal: `UFastDisWorldSubsystem::BuildDebugTransformForDisOrientation(...)`
- Godot: `FastDisWorld.build_debug_transform_from_dis(...)`

The harnesses load `expected.dis_deg` from the shared fixture and drive the
validated DIS body-frame path directly. That keeps the verification path on the
real adapter math instead of a fixture-constructed basis matrix or a local HPR
approximation.

Before either engine harness launches, the runner now refreshes the staged
fixture copy and verifies both:

- the staged JSON still matches `tests/data/orientation_engine_cases.json`
- the staged `.sha256` sidecar still matches the staged bytes

That turns the shared-fixture contract into an executable preflight instead of
documentation only.

The initial fixture set covers axis-aligned local ENU cases, climb, bank,
equator/prime-meridian basis sanity, and near-pole stress. DIS `psi/theta/phi`
golden values are added by the independent oracle workstream.

Asset-basis verification is now split into two executable checks:

- Unreal automation composes the actor rotation with explicit
  `AssetForwardAxis` / `AssetUpAxis` correction matrices and verifies the
  resulting local `+X`, `+Y`, and `+Z` marker directions numerically.
- Godot headless verification treats node forward (`-basis.z`) and model front
  (`basis.z`) as separate assertions so `MODEL_FRONT` regressions surface
  independently from node-basis regressions.

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

The same automation spec now also verifies three asset-basis correction cases
per orientation fixture:

- identity asset basis (`+X` forward, `+Z` up)
- model-front style (`+Z` forward, `+Y` up)
- side-authored asset (`+Y` forward, `+Z` up)

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

Bundled runtime proof uses:

`python tools/run_orientation_runtime_report.py --engine-version 5.8`

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

The automation spec now emits structured runtime lines in the form:

```text
FASTDIS_ORIENTATION_PASS case=<name> axis=<axis> angle_deg=<value> dot=<value> threshold_deg=<value>
```

Those lines are captured in:

```text
verification_reports/alpha2_sample/unreal_orientation_runtime_5_8.log
verification_reports/alpha2_sample/unreal_orientation_harness_5_8.log
```

The same Unreal lane now also emits structured scene-style summaries:

```text
FASTDIS_ORIENTATION_SCENE case=<name> status=<PASS|FAIL> ...
```

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

GDScript tests read the `Transform3D` returned by the extension helper and then
inspect `basis.x`, `basis.y`, and `-basis.z`. The visual scene can still wait a
frame if it wants to validate a live `Node3D`.

Required artifacts:

```text
examples/godot/fastdis_orientation_verification/
  project.godot
  scenes/orientation_verification.tscn
  scripts/run_orientation_tests.gd
  tests/orientation_engine_cases.json
```

Unity scaffold artifacts:

```text
examples/unity/FastDisOrientationVerification/
  Assets/Scenes/OrientationVerification.unity
  Assets/Scripts/FastDisOrientationVerifier.cs
  Assets/StreamingAssets/orientation_engine_cases.json
```

The current Unity scaffold verifies Unity target-frame interpretation with the
shared fixture contract and `Quaternion.LookRotation(forward, up)`. It is not
yet a native fastdis Unity adapter.

Headless target:

`python tools/run_godot_orientation_verification.py`

Bundled runtime proof uses:

`python tools/run_orientation_runtime_report.py --engine-version 5.8`

The runner stages the shared fixture JSON and the host-native `libfastdis`
shared library into `addons/fastdis/bin/` when available. The remaining manual
step is the actual GDExtension wrapper build, because that still depends on
`godot-cpp` and `scons`.

The visual scene should draw:

```text
red    actual forward = -basis.z
green  actual right   = basis.x
blue   actual up      = basis.y
dashed expected axes
```

It should display case name, basis determinant, dot products,
`max_angle_error_deg`, and PASS/FAIL.

The current Alpha 2 scaffolds now move beyond placeholder docs:

- Godot `orientation_verification.tscn` renders expected and actual basis
  frames side by side and prints PASS/FAIL, angular error, and dot-product
  summaries in-scene.
- Unreal `AFastDisOrientationProbeActor` draws the expected/actual axes and a
  world-space debug-text summary with PASS/FAIL plus numeric axis metrics.
- Godot headless verification emits the same structured
  `FASTDIS_ORIENTATION_PASS/FAIL` lines, captured in:

```text
verification_reports/alpha2_sample/godot_orientation_runtime.log
```

- Godot visual-scene verification is runnable headlessly via:

```text
python tools/run_godot_orientation_visual_scene.py --skip-build
```

  and its bundled raw capture lives at:

```text
verification_reports/alpha2_sample/godot_orientation_visual.log
```

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

The current headless runner already executes both checks numerically by
comparing `-basis.z` against the expected node forward and `basis.z` against
the expected model-front direction.

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
