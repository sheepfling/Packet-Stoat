# Godot GDExtension scaffold

The Godot scaffold lives in:

```text
examples/godot/fastdis_gdextension/
```

It defines a `FastDisWorld` node backed by the fastdis C++ RAII layer:

```text
FastDisWorld
  -> fastdis::Scanner
  -> fastdis::EntityTable
  -> fastdis::SnapshotBuffer
```

The demo-friendly method accepts one `PackedByteArray` packet at a time:

```gdscript
fastdis_world.ingest_packet(packet_bytes)
```

For a production high-rate path, write a native UDP/replay bridge that builds a
batch of `fastdis_packet_view_t` records and calls the native scanner/table path
without going through script for every packet.

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

## Build shape

The scaffold expects `godot-cpp` and fastdis include/lib paths to be configured
for your platform. Environment variables are supported by `SConstruct`:

```bash
export FASTDIS_INCLUDE=/path/to/fastdis/include
export FASTDIS_LIB_DIR=/path/to/fastdis/build
```

Then use your normal Godot-cpp/SCons platform target. Copy the resulting
GDExtension shared library and `fastdis.gdextension` into the Godot project under
`addons/fastdis/`.
