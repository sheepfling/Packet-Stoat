# Godot GDExtension sample

The Godot native adapter lives in:

```text
examples/godot/fastdis_gdextension/
```

The runnable sample project lives in:

```text
examples/godot/fastdis_demo/
```

`FastDisWorld` is backed by the fastdis C++ RAII layer:

```text
FastDisWorld
  -> fastdis::Scanner
  -> fastdis::EntityTable
  -> fastdis::SnapshotBuffer
```

The extension supports direct packet ingest plus replay-file stepping:

```gdscript
fastdis_world.ingest_packet(packet_bytes)
fastdis_world.load_replay_file("res://data/synthetic.fastdispkt")
fastdis_world.ingest_replay_frame(64, true)
```

The sample exposes runtime knobs for:

- `transform_mode`
- `snapshot_slots`
- `stale_after_ticks`
- `meters_to_godot_scale`
- `apply_orientation`

## Frame conversion

Configure a WGS-84 origin:

```gdscript
fastdis_world.set_georeference(29.5597, -95.0831, 0.0)
fastdis_world.apply_orientation = false
```

Default mapping:

```text
local ENU meters -> Godot meters
 east -> +X
   up -> +Y
north -> -Z
```

Keep `apply_orientation=false` until the orientation convention is validated for
your exercise and asset forward axes.

## Orientation verification

Alpha 2 tracks in-engine orientation verification separately from native math
tests. The Godot harness lives at:

```text
examples/godot/fastdis_orientation_verification/
```

It loads shared fixtures from `tests/data/orientation_engine_cases.json` and
compares Godot basis vectors numerically:

```text
basis.x  -> godot_right
basis.y  -> godot_up
-basis.z -> godot_forward
```

Run shape:

```bash
godot --headless --path examples/godot/fastdis_orientation_verification \
  --script scripts/run_orientation_tests.gd
```

Orientation remains opt-in until this harness validates the adapter-produced
`Transform3D`, not just the standalone frame math.

## Build shape

The native build expects `godot-cpp` and fastdis include/lib paths to be
configured for your platform. Environment variables are supported by
`SConstruct`:

```bash
export FASTDIS_INCLUDE=/path/to/fastdis/include
export FASTDIS_LIB_DIR=/path/to/fastdis/build
```

Then use your normal Godot-cpp/SCons platform target from
`examples/godot/fastdis_gdextension/`. The default output path writes the wrapper
into `../fastdis_demo/addons/fastdis/bin/`.

At runtime, place the host-native `libfastdis.so`, `libfastdis.dylib`, or
`fastdis.dll` in that same `addons/fastdis/bin/` directory so the wrapper can
resolve the shared library dependency.

If the extension class does not load, the demo scene prints a clear status
message instead of instantiating the bridge node.
