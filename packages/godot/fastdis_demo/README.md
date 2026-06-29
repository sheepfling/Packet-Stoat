# FastDIS Godot Demo

This is the Alpha 2 runnable Godot sample project.

It expects the GDExtension wrapper from:

```text
../fastdis_gdextension/
```

The repeatable repo path is:

```bash
python tools/godot_workflow.py build
python tools/godot_workflow.py demo
```

Advanced users can still build the wrapper with SCons from
`packages/godot/fastdis_gdextension/`. The default `SConstruct` target writes
the resulting extension binary directly into:

```text
packages/godot/fastdis_demo/addons/fastdis/bin/
```

The repo build helper also stages the host-native `libfastdis.so`,
`libfastdis.dylib`, or `fastdis.dll` into the same `addons/fastdis/bin/`
directory as the wrapper.

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
python tools/make_replay.py packages/godot/fastdis_demo/data/synthetic.fastdispkt --packets 2048 --entities 3
```

If the extension or native library is missing, the demo prints a clear error and
does not instantiate the bridge node.

For a repeatable Alpha 2 proof that replay input actually moves the registered
`Node3D` markers, run:

```bash
python tools/godot_workflow.py demo
```

That command rebuilds or reuses the staged extension, generates a small
`synthetic.fastdispkt` replay, opens the actual demo scene headlessly, and
checks that `EntityA`, `EntityB`, and `EntityC` leave their initial positions.

For the negative-path proof that a missing host-native `libfastdis` payload
fails clearly without crashing the scene, run:

```bash
python tools/godot_workflow.py missing-lib
```

That workflow lane temporarily hides the staged `libfastdis` files, launches
the same demo scene headlessly, and verifies that `StatusLabel` reports the
extension/native-library load failure.
