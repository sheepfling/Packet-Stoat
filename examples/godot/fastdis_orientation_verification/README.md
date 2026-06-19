# FastDIS Godot Orientation Verification

This is an Alpha 2 verification harness for Godot orientation support. It is a
headless numerical test plus a real fixture-driven scene for visual axis
inspection.

## Headless Test

Run from the repo root:

```bash
python tools/godot_workflow.py doctor
python tools/godot_workflow.py verify
python tools/godot_workflow.py full
```

The workflow wrapper is the preferred operator path. The lower-level runner
still exists when you want to invoke the harness directly:

```bash
python tools/run_godot_orientation_verification.py
```

The script loads the shared fixture source or the staged copy created by
`tools/sync_orientation_fixtures.py`:

```text
tests/orientation_engine_cases.json
tests/data/orientation_engine_cases.json
```

and validates:

```text
basis.x  against godot_right
basis.y  against godot_up
-basis.z against godot_forward
```

The runner now verifies that the staged copy and its
`orientation_engine_cases.json.sha256` sidecar still match the canonical
`tests/data/orientation_engine_cases.json` payload before Godot launches.

The test uses vector angular comparisons. It does not compare Euler angles.
It also checks the node-forward (`-basis.z`) and model-front (`basis.z`)
interpretations explicitly so asset-axis assumptions stay visible.

When the extension is available, the headless script now instantiates
`FastDisWorld`, sets the case georeference, and calls:

```text
FastDisWorld.build_debug_transform_from_dis(psi_degrees, theta_degrees, phi_degrees)
```

That keeps the numerical verification on the adapter-produced `Transform3D`
path by loading `expected.dis_deg` from the shared fixture and exercising the
validated DIS body-frame route instead of a fixture-constructed `Basis`.

The project now includes the tracked `addons/fastdis/fastdis.gdextension`
manifest. The workflow/build helpers stage the built wrapper plus the
host-native `fastdis` shared library into `addons/fastdis/bin/` automatically
when `godot-cpp`, `scons`, and `cmake` are available.

## Visual Scene

Open:

```text
scenes/orientation_verification.tscn
```

The scene now loads the selected fixture case, instantiates `FastDisWorld`,
builds the adapter-produced `Transform3D`, and renders both the expected and
actual basis frames side by side:

```text
left frame  = expected basis from fixture
right frame = actual basis from FastDisWorld.build_debug_transform_from_dis(...)
red         = forward
green       = right
blue        = up
```

It also prints an in-scene `Label3D` summary with:

```text
PASS / FAIL
forward/right/up angular error
forward/right/up dot products
model-front angular error and dot product
```

The runner script supports `--dry-run` when `godot` is not on PATH, and when
Godot is installed it emits a precise error if the GDExtension wrapper has not
been built yet.
