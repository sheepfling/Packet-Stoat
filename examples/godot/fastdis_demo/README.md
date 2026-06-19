# FastDIS Godot Demo

This is the Alpha 2 runnable Godot sample project.

It expects the GDExtension wrapper from:

```text
../fastdis_gdextension/
```

Build the wrapper with SCons from `examples/godot/fastdis_gdextension/`. The
default `SConstruct` target writes the resulting extension binary directly into:

```text
examples/godot/fastdis_demo/addons/fastdis/bin/
```

At runtime the wrapper library must also be able to load the host-native
`fastdis` shared library. The simplest route is to copy the host-native
`libfastdis.so`, `libfastdis.dylib`, or `fastdis.dll` into the same
`addons/fastdis/bin/` directory as the wrapper.

The demo scene:

1. checks whether the `FastDisWorld` extension class loaded
2. creates a `FastDisWorld` node if available
3. registers a few `Node3D` markers by DIS entity ID
4. loads a `.fastdispkt` replay file if present
5. advances the replay and applies snapshots every frame

Place a replay at:

```text
res://data/synthetic.fastdispkt
```

You can generate one from the repo root with:

```bash
python tools/make_replay.py examples/godot/fastdis_demo/data/synthetic.fastdispkt --packets 2048 --entities 3
```

If the extension or native library is missing, the demo prints a clear error and
does not instantiate the bridge node.
