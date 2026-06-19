# FastDIS Godot Orientation Verification

This is an Alpha 2 verification harness for Godot orientation support. It is a
headless numerical test plus a small scene scaffold for visual axis inspection.

## Headless Test

Run from the repo root:

```bash
godot --headless --path examples/godot/fastdis_orientation_verification \
  --script scripts/run_orientation_tests.gd
```

The script loads:

```text
tests/data/orientation_engine_cases.json
```

and validates:

```text
basis.x  against godot_right
basis.y  against godot_up
-basis.z against godot_forward
```

The test uses vector angular comparisons. It does not compare Euler angles.

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
