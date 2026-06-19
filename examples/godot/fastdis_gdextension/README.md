# FastDIS Godot GDExtension scaffold

This is a tiny Godot 4 GDExtension scaffold that consumes the fastdis C++ RAII
layer and double-buffer snapshots.

It exposes a `FastDisWorld` node. The demo API accepts packet byte arrays one at
a time for clarity; a production bridge should batch `fastdis_packet_view_t`
arrays from a native UDP receiver or replay reader.

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
fastdis_world.register_entity(100, 1, 42, NodePath("/root/World/Tank42"))

# Later, from a UDP/replay bridge:
fastdis_world.ingest_packet(packet_bytes)
```

## Building

This scaffold expects `godot-cpp` beside `SConstruct` or configured through
environment variables. It also expects the fastdis headers and shared library to
be discoverable through:

```bash
export FASTDIS_INCLUDE=/path/to/fastdis/include
export FASTDIS_LIB_DIR=/path/to/fastdis/build
```

Then build with your usual Godot-cpp/SCons platform arguments.
