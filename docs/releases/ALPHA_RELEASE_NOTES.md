# fastdis alpha bundle — v0.11.0 source alpha

This alpha bundle collects the current fastdis work into one source tree for review, testing, and engine-integration experiments.

## Included

- Portable shared-library/DLL core built from C++ with a stable C ABI.
- Header-only C++17 RAII wrapper over the C ABI.
- Pure-Python fallback, optional CPython accelerator, and ctypes wrapper.
- Header-first DIS scan/filter/downsample path.
- Entity State PDU fixed-prefix parser.
- Entity State field subscriptions.
- Easy filters for protocol version, PDU type, protocol family, exercise ID, force ID, entity-ID allow/block sets, and sampling.
- Callback-free batch output for Entity State records and compact engine transforms.
- Native latest-state entity table keyed by DIS entity ID.
- Changed/stale/all snapshot extraction and stale eviction.
- Double-buffer snapshot handoff for update-thread/render-thread style consumption.
- C++ RAII wrappers for scanner, entity table, snapshot buffer, scoped snapshot views, packet views, and batches.
- Frame transform helper layer for DIS ECEF -> local ENU -> Unreal/Godot coordinate conventions.
- Unreal Runtime plugin scaffold with `UFastDisWorldSubsystem`.
- Godot GDExtension scaffold with `FastDisWorld` node.
- Native and Python/ctypes benchmark harnesses.
- Simple `.fastdispkt` replay benchmark format.

## Not included

This is a source-only alpha bundle. It intentionally does **not** include:

- compiled `.so`, `.dylib`, or `.dll` binaries,
- Python wheels,
- `build/` or `dist/` directories,
- Unreal Engine SDK outputs,
- Godot `godot-cpp` build artifacts,
- captured real-world DIS traffic.

## Build quick start

Native shared library and tests:

```bash
python tools/build_native.py --build-dir build
ctest --test-dir build --build-config Release --output-on-failure
```

Python package/tests:

```bash
python -m pip install -e '.[dev]'
python -m pytest
```

Native benchmark smoke run:

```bash
python tools/run_benchmarks.py --native-packets 100000 --native-rounds 3 --ctypes-packets 10000 --ctypes-repeats 3 --format table
```

Replay benchmark fixture:

```bash
python tools/make_replay.py benchmark_results/synthetic.fastdispkt --packets 100000
./build/fastdis_native_bench --packet-file benchmark_results/synthetic.fastdispkt --packets 100000 --rounds 5 --format table
```

## Primary integration headers

C ABI:

```cpp
#include <fastdis/fastdis.h>
```

C++ RAII:

```cpp
#include <fastdis/fastdis.hpp>
```

Frame transforms:

```cpp
#include <fastdis/fastdis_frames.hpp>
```

## Alpha cautions

- The Unreal and Godot integrations are scaffolds/templates. They were not compiled against local Unreal or Godot SDKs in this environment.
- Position conversion is implemented as an explicit georeferenced transform path. Rotation/orientation application is intentionally opt-in until validated against known-good DIS traffic and engine asset-axis conventions.
- The public C ABI remains the stable engine boundary. The C++ RAII layer is header-only convenience over that ABI.
- Treat benchmark numbers in `docs/SAMPLE_BENCHMARK_REPORT.md` and locally generated benchmark outputs as development-environment samples, not hardware-independent promises.

## Suggested next validation checklist

1. Build the shared library on Linux, Windows, and macOS.
2. Run native tests and benchmarks on target hardware.
3. Compile the Unreal plugin scaffold against your Unreal version.
4. Compile the Godot GDExtension scaffold against your Godot/godot-cpp version.
5. Validate frame transforms with a known scenario origin and one or more known entity positions.
6. Validate DIS orientation with a reference viewer before enabling orientation application by default.
7. Replay captured traffic and compare entity counts, update rates, stale handling, and transform placement.
