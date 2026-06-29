This harness expects the Godot FastDIS GDExtension wrapper and the host-native
`libfastdis` shared library under:

```text
addons/fastdis/bin/
```

The wrapper library names must match the `fastdis.gdextension` manifest in this
directory. The repeatable way to populate that folder is:

1. Build `packages/godot/fastdis_gdextension/` with `godot-cpp` and `scons`.
2. Copy the produced `libfastdis_gdextension.*` wrapper into `addons/fastdis/bin/`.
3. Copy the host-native `libfastdis.dylib`, `libfastdis.so`, or `fastdis.dll`
   beside the wrapper.

`tools/run_godot_orientation_verification.py` stages the shared fixture JSON and
the core `libfastdis` dylib when available. When `scons` and `godot-cpp` are
present, it also builds the wrapper in `packages/godot/fastdis_gdextension/`
and copies the resulting `libfastdis_gdextension.*` binary into this harness.
