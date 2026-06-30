# Windows ctypes wheels from macOS/Linux

`fastdis` can now build a Windows wheel in two stages:

1. build `fastdis.dll`
2. package that DLL into a `py3-none-win_amd64` wheel

This lane is intentionally for the `ctypes` native-library path, not for a
compiled CPython `.pyd` extension.

## What this solves

- You can assemble a Windows wheel on macOS or Linux.
- The wheel can bundle `fastdis.dll`.
- The packaged wheel does not need to be tied to a single CPython ABI.

## What this does not solve

- It does not produce a Windows `.pyd` extension.
- It does not replace real Windows runtime validation.
- Unreal and Godot should still be treated as host-native build lanes.

## Required tools

### Linux

Install:

```bash
sudo apt-get update
sudo apt-get install -y cmake ninja-build gcc-mingw-w64 g++-mingw-w64 mingw-w64-tools
python3 -m pip install --upgrade build wheel
```

Expected cross tools:

- `x86_64-w64-mingw32-gcc`
- `x86_64-w64-mingw32-g++`
- `x86_64-w64-mingw32-windres`

## Doctor and workflow wrapper

Use the operator-facing helper when you want a clear ready/not-ready answer:

```bash
python3 tools/windows_wheel_workflow.py discover
python3 tools/windows_wheel_workflow.py doctor
python3 tools/windows_wheel_workflow.py build-dll
python3 tools/windows_wheel_workflow.py build-wheel --no-isolation
python3 tools/windows_wheel_workflow.py full --no-isolation
```

The `doctor` command reports:

- missing `cmake`
- missing MinGW tools
- whether a cross-built Windows DLL already exists
- whether a Windows wheel already exists
- the next command to run

### macOS

Install:

```bash
brew install cmake mingw-w64
python3 -m pip install --upgrade build wheel
```

Expected cross tools:

- `x86_64-w64-mingw32-gcc`
- `x86_64-w64-mingw32-g++`
- `x86_64-w64-mingw32-windres`

## Raw DLL build

Cross-build just the DLL:

```bash
python3 tools/build_windows_dll.py \
  --config Release \
  --clean
```

Default toolchain file:

```text
cmake/toolchains/mingw-w64-x86_64.cmake
```

## End-to-end wheel build

Build the DLL and package the wheel:

```bash
python3 tools/build_windows_ctypes_wheel.py \
  --config Release \
  --clean \
  --no-isolation
```

Defaults write to `build/cmake/mingw-win64/` and `artifacts/dist/`.

Expected wheel shape:

```text
fastdis-<version>-py3-none-win_amd64.whl
```

The wheel bundles:

```text
fastdis/fastdis.dll
```

and deliberately skips `_cfast` for this lane.

By default this cross-build lane builds only the `fastdis_shared` target needed
for wheel packaging. That avoids unrelated Windows example-link quirks from
blocking the DLL/wheel path.

## Manual packaging from an existing DLL

If you already have a trusted Windows DLL from another machine or CI:

```bash
python3 tools/build_ctypes_wheel.py \
  --native-lib /path/to/fastdis.dll \
  --plat-name win_amd64 \
  --outdir dist \
  --no-isolation
```

## Recommended release policy

Use this cross-build lane for developer convenience and pre-release rehearsal.
Use a real Windows CI runner as the final source of truth for:

- DLL build correctness
- wheel install/import
- runtime load verification

The repo CI already includes a Windows-native proof lane for bundled ctypes
wheels.
