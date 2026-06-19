# FastDIS Godot GDExtension sample

This is the native side of the Alpha 2 Godot 4 sample. It consumes the fastdis
C++ RAII layer, latest-state table, and configurable snapshot buffer.

It exposes a `FastDisWorld` node. The API now supports:

- georeference configuration
- entity registration by `NodePath`
- position-only and experimental-rotation transform modes
- configurable snapshot slots and stale eviction
- `.fastdispkt` replay loading and frame stepping
- single-packet ingest for simple bridges and tests

The runnable Godot sample project lives at:

```text
../fastdis_demo/
```

## Frame mapping

DIS Entity State `location` is ECEF/geocentric meters. Godot uses a Y-up,
right-handed 3D coordinate system. This scaffold requires an explicit WGS-84
origin and maps local ENU meters like this:

```text
 east -> +X
   up -> +Y
north -> -Z
```

Orientation is opt-in because DIS profile conventions and asset forward axes must
be validated with known traffic. Keep `apply_orientation=false` until then.

## Example GDScript shape

```gdscript
var fastdis_world := FastDisWorld.new()
add_child(fastdis_world)
fastdis_world.set_georeference(29.5597, -95.0831, 0.0)
fastdis_world.apply_orientation = false
fastdis_world.snapshot_slots = 3
fastdis_world.stale_after_ticks = 120
fastdis_world.register_entity(100, 1, 42, NodePath("/root/World/Tank42"))

# Later, from a replay bridge:
fastdis_world.load_replay_file("res://data/synthetic.fastdispkt")
fastdis_world.ingest_replay_frame(64, true)
```

## Building

This sample expects `godot-cpp` beside `SConstruct` or configured through
environment variables. It also expects the fastdis headers and shared library to
be discoverable through:

```bash
export FASTDIS_INCLUDE=/path/to/fastdis/include
export FASTDIS_LIB_DIR=/path/to/fastdis/build
```

Then build with your usual Godot-cpp/SCons platform arguments. The default
`SConstruct` output path writes the wrapper directly into:

```text
../fastdis_demo/addons/fastdis/bin/
```

At runtime, copy the host-native `libfastdis.so`, `libfastdis.dylib`, or
`fastdis.dll` into that same `addons/fastdis/bin/` directory so the wrapper can
resolve the shared library load.
