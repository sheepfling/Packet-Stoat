# Install

FastDIS Alpha5 exposes several product lanes from one repository.

## Python / CLI

Development install:

```bash
python -m pip install -e '.[dev]'
fastdis doctor
```

That editable dev install also includes `scons`, which the Godot
GDExtension build path uses.

That same dev setup is the easiest way to keep the Mac and Windows engine
bootstrap routes together: `fastdis bootstrap` will detect the host and run the
available Godot and Unreal lanes instead of forcing a separate manual script for
each platform.

If you want the quick host preview first, run `fastdis bootstrap doctor`.

Published-package target:

```bash
python -m pip install fastdis
fastdis doctor
```

If the `fastdis` distribution name is unavailable on PyPI, the fallback
distribution name is `packet-stoat`; the import package and CLI should remain
`fastdis`.

## Native SDK

Build locally:

```bash
python tools/build_native.py --build-dir build
ctest --test-dir build --build-config Release --output-on-failure
```

Published-sdk target:

```bash
cmake -S . -B build -DCMAKE_PREFIX_PATH=/path/to/fastdis-native
cmake --build build
```

## Unreal

Local workflow:

```bash
fastdis engine unreal doctor --engine-version 5.8
fastdis engine unreal build --engine-version 5.8
```

Published-plugin target:

```text
unzip FastDIS Unreal release zip into Project/Plugins/FastDIS/
```

## Godot

Local workflow:

```bash
fastdis engine godot bootstrap
fastdis engine godot doctor
fastdis engine godot build
```

On Windows, Godot is the intended engine path here. It still expects a Godot
executable. If `examples/godot/fastdis_gdextension/godot-cpp` is missing, the
bootstrap lane will fetch it automatically before the wrapper compiles and
stages.

Published-addon target:

```text
unzip FastDIS Godot release zip into project addons/fastdis/
```

## Lattice Lab

Local workflow:

```bash
python -m build packages/lattice
fastdis lattice sdk-check
```

This lane is mock-first and does not claim live Anduril endpoint verification
without real credentials.
