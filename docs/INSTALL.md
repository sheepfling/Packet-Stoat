# Install

FastDIS Alpha5 exposes several product lanes from one repository.

## Python / CLI

Development install:

```bash
python -m pip install -e '.[dev]'
fastdis doctor
```

On a fresh Windows host, the easiest first step is:

```bash
python tools/bootstrap_local_dev.py
```

That wrapper installs the local dev dependency prefix, sets the workspace
scratch roots, and runs a quick check in one pass.

On Windows, the bootstrap defaults to `C:\tmp\fastdis_dev` so the Unreal,
Godot, Unity, and temp roots stay short even when the repo lives deeper in the
filesystem.

On Windows it expects Scoop-managed host tools to already be present for
`git`, `cmake`, and `pwsh`. If they are missing, the bootstrap blocks clearly
instead of trying to guess how to repair the machine.

It also recognizes semi-configured and fully-configured hosts, so rerunning it
is a safe repair step instead of a one-shot initializer.

If you want the single repo-level entry point instead, use:

```bash
packet-stoat bootstrap
```

That command now prepares the local dev environment first and then runs the
host bootstrap workflow.

If Scoop is not installed yet, install Scoop first and rerun the bootstrap.

That editable dev install also includes `scons`, which the Godot
GDExtension build path uses.

That same dev setup is the easiest way to keep the Mac and Windows engine
bootstrap routes together: `fastdis bootstrap` will detect the host and run the
available Godot and Unreal lanes instead of forcing a separate manual script for
each platform.

If you want the broad host preview first, run `fastdis workspace doctor`.

The current Python support policy for the workspace is:

- supported: `3.12`, `3.13`, `3.14`
- preferred: `3.14`

Some hooks may still be stricter than the broad Python surface. For example,
native wheel/package hooks may require the preferred CPython ABI lane even when
general verify/test hooks support more than one Python minor.

For a compact CI-friendly summary, run:

```bash
fastdis workspace doctor --format summary
```

For a manifest-driven CI route preview, run:

```bash
fastdis workspace ci --host-class windows --include-compat --format summary
fastdis workspace ci-print --section workspace_ci_host_python --format summary
fastdis workspace ci-sync
fastdis workspace ci-check
python tools/generate_workspace_ci_matrix.py check --path .github/workflows/generated/workspace-ci-matrix.json
```

Use `fastdis bootstrap doctor` after that when you specifically want the
Godot/Unreal bootstrap preview.

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
fastdis-lattice sdk-check
```

This lane is mock-first and does not claim live Anduril endpoint verification
without real credentials.
