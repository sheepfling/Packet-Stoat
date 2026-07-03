# Linux ctypes wheels

`fastdis` can now build a Linux wheel in two explicit ways:

1. direct/native via the Zig Linux CMake toolchain
2. Docker via a `linux/amd64` container that builds and packages the wheel

This lane is intentionally for the `ctypes` native-library path, not for a
compiled CPython extension module.

## What this solves

- You can assemble a Linux wheel with a bundled `libfastdis.so`.
- The direct route keeps the existing Zig toolchain workflow explicit.
- The Docker route gives a containerized Linux wheel path when you want Linux
  packaging semantics on any host with Docker.

## What this does not solve

- It does not produce a CPython `.so` extension module.
- It does not claim manylinux compliance by default.
- It does not replace real Linux runtime verification on a target distro.

## Required tools

### Direct backend

Install:

```bash
python3 -m pip install --upgrade build wheel
```

And make sure these are present:

- `cmake`
- `zig`
- `cmake/toolchains/linux-x86_64-zig.cmake`

### Docker backend

Install:

```bash
docker version
```

The container installs its own Linux build and Python packaging dependencies.

## Doctor and workflow wrapper

Use the operator-facing helper when you want a clear ready/not-ready answer:

```bash
python3 tools/linux_wheel_workflow.py discover
python3 tools/linux_wheel_workflow.py doctor
python3 tools/linux_wheel_workflow.py build-lib
python3 tools/linux_wheel_workflow.py build-wheel --no-isolation
python3 tools/linux_wheel_workflow.py full --no-isolation
```

Choose a backend explicitly when you want to pin the route:

```bash
python3 tools/linux_wheel_workflow.py full --backend direct --no-isolation
python3 tools/linux_wheel_workflow.py full --backend docker --no-isolation
```

The `doctor` command reports:

- direct backend readiness (`cmake`, `zig`, toolchain file)
- Docker backend readiness
- whether a Linux shared library already exists
- whether a Linux wheel already exists
- the next explicit command to run

## End-to-end direct wheel build

Build the Linux shared library and package the wheel on the host:

```bash
python3 tools/build_linux_ctypes_wheel.py \
  --backend direct \
  --config Release \
  --no-isolation
```

## End-to-end Docker wheel build

Build and package inside a Linux container:

```bash
python3 tools/build_linux_ctypes_wheel.py \
  --backend docker \
  --config Release \
  --no-isolation
```

Defaults write to `build/cmake/linux-x86_64/` and `artifacts/dist/`.

Expected default wheel shape:

```text
fastdis-<version>-py3-none-linux_x86_64.whl
```

The wheel bundles:

```text
fastdis/libfastdis.so
```

By default this Linux wheel lane builds only the `fastdis_shared` target needed
for wheel packaging.

## Manual packaging from an existing Linux shared library

If you already have a trusted Linux shared library from another machine or CI:

```bash
python3 tools/build_ctypes_wheel.py \
  --native-lib /path/to/libfastdis.so \
  --plat-name linux_x86_64 \
  --outdir artifacts/dist \
  --no-isolation
```

## Platform tags

The default tag is `linux_x86_64`, which is the conservative honest default for
this workflow. If you have a stricter distro/container policy and want a
different tag, override it explicitly:

```bash
python3 tools/linux_wheel_workflow.py full \
  --backend docker \
  --plat-name manylinux_2_28_x86_64 \
  --no-isolation
```

Only use a stricter tag when your actual build and validation policy supports
it.
