# Release manifest

This archive is the source-only Alpha 2 bundle for `fastdis v0.12.0-alpha2`.

## Version markers

- Bundle label: `fastdis_alpha_v0_12_0`
- Native library version string: `0.12.0-alpha2`
- Python package version: `0.12.0a2`
- C ABI version: `8`
- C++ RAII surface: header-only `include/fastdis/fastdis.hpp`

## Key directories

| Path | Purpose |
|---|---|
| `include/fastdis/fastdis.h` | Public C ABI for DLL/shared-object consumers. |
| `include/fastdis/fastdis.hpp` | Header-only C++17 RAII wrapper. |
| `include/fastdis/fastdis_frames.hpp` | DIS ECEF/local ENU/Unreal/Godot frame helpers. |
| `include/fastdis/fastdis_orientation.hpp` | Canonical orientation basis helpers and target-frame mapping surfaces. |
| `include/fastdis/fastdis_pdu_catalog.h` | Plain-C DIS 6/7 PDU catalog for header/message coverage. |
| `src/native/fastdis_core.cpp` | C++ implementation behind the C ABI. |
| `src/fastdis/` | Python fallback, CPython extension source, and ctypes wrapper. |
| `bindings/` | Generated and shared binding-support sources for cross-language message coverage. |
| `tests/` | Python and native test coverage. |
| `benchmarks/` | Native and ctypes benchmark programs. |
| `benchmark_reports/alpha2_sample/` | Checked-in Alpha 2 sample benchmark JSON and Markdown output. |
| `verification_reports/alpha2_sample/` | Checked-in Alpha 2 sample Unreal/Godot proof reports from real engine workflow runs. |
| `fuzz/` | Header, transform, and entity-table fuzz harnesses. |
| `tools/` | Native build, replay generation, benchmark, and summary helpers. |
| `examples/c/` | Plain C examples. |
| `examples/cpp/` | C++ RAII examples. |
| `examples/unreal/FastDis/` | Unreal Runtime plugin plus replay-driven sample adapter path. |
| `examples/unreal/FastDisDemo/` | Unreal quickstart/demo project notes for plugin drop-in use. |
| `examples/unreal/FastDisOrientationVerification/` | Unreal in-engine orientation verification harness scaffold. |
| `examples/godot/fastdis_gdextension/` | Godot GDExtension runtime wrapper. |
| `examples/godot/fastdis_demo/` | Replay-driven Godot demo project path. |
| `examples/godot/fastdis_orientation_verification/` | Godot in-engine orientation verification harness scaffold. |
| `examples/common/` | Shared replay-reader and UDP-receiver helpers used by native/engine demos. |
| `docs/` | ABI, stability, snapshot, frame transform, orientation, engine adapter, benchmarking, and hardening docs. |

## Bundle policy

- Includes only source, docs, tests, benchmark reports, and metadata.
- Excludes build trees, `dist/`, compiled `.so`/`.dylib`/`.dll` outputs,
  temporary engine artifacts, virtual environments, caches, and
  `benchmark_results/`.

## Quickstarts

- Native build and tests: `cmake --build build --config Release`, then
  `ctest --test-dir build --build-config Release --output-on-failure`.
- Python validation: `python -m pytest`.
- Unreal sample: start with `examples/unreal/FastDisDemo/README.md`.
- Godot sample: start with `examples/godot/fastdis_demo/README.md`.
- Benchmark readout: start with `benchmark_reports/alpha2_sample/summary.md`.
- Engine proof readout: start with `verification_reports/alpha2_sample/unreal_version_matrix.md` and `verification_reports/alpha2_sample/godot_workflow_report.md`.

## Warnings

- Position transforms are validated against shared fixtures.
- Orientation remains opt-in until the engine harnesses are run with local
  editor binaries and asset-axis conventions are signed off.
- Checked-in engine proof reports are host-sample evidence, not a guarantee
  that every machine will match the same Unreal/Godot lane statuses.
