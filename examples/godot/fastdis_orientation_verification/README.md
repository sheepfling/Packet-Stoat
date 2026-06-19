# FastDIS Godot Orientation Verification

This is an Alpha 2 verification harness for Godot orientation support. It is a
headless numerical test plus a small scene scaffold for visual axis inspection.

## Headless Test

Run from the repo root:

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

The test uses vector angular comparisons. It does not compare Euler angles.
It also checks the node-forward (`-basis.z`) and model-front (`basis.z`)
interpretations explicitly so asset-axis assumptions stay visible.

When the extension is available, the headless script now instantiates
`FastDisWorld`, sets the case georeference, and calls:

```text
FastDisWorld.build_debug_transform(heading_degrees, pitch_degrees, roll_degrees)
```

That keeps the numerical verification on the adapter-produced `Transform3D`
path instead of a fixture-constructed `Basis`.

The project now includes the tracked `addons/fastdis/fastdis.gdextension`
manifest. The verification runner stages the built wrapper into
`addons/fastdis/bin/` automatically when `godot-cpp` and `scons` are available.

## Visual Scene

Open:

```text
scenes/orientation_verification.tscn
```

The scene is intentionally minimal until the GDExtension orientation output is
wired into the adapter. It provides a stable place to render expected and actual
axes:

```text
red    actual forward = -basis.z
green  actual right   = basis.x
blue   actual up      = basis.y
dashed expected axes
```

The runner script supports `--dry-run` when `godot` is not on PATH, and when
Godot is installed it emits a precise error if the GDExtension wrapper has not
been built yet.
