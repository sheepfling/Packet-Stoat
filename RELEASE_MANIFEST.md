# Release manifest

This archive is a source alpha for fastdis v0.11.0.

## Key directories

| Path | Purpose |
|---|---|
| `include/fastdis/fastdis.h` | Public C ABI for DLL/shared-object consumers. |
| `include/fastdis/fastdis.hpp` | Header-only C++17 RAII wrapper. |
| `include/fastdis/fastdis_frames.hpp` | DIS ECEF/local ENU/Unreal/Godot frame helpers. |
| `src/native/fastdis_core.cpp` | C++ implementation behind the C ABI. |
| `src/fastdis/` | Python fallback, CPython extension source, and ctypes wrapper. |
| `tests/` | Python and native test coverage. |
| `benchmarks/` | Native and ctypes benchmark programs. |
| `tools/` | Native build, replay generation, benchmark, and summary helpers. |
| `examples/c/` | Plain C examples. |
| `examples/cpp/` | C++ RAII examples. |
| `examples/unreal/FastDis/` | Unreal Runtime plugin scaffold. |
| `examples/godot/fastdis_gdextension/` | Godot GDExtension scaffold. |
| `docs/` | ABI, entity table, snapshots, frame transforms, engine adapter, benchmarking, and roadmap docs. |
| `release_artifacts/benchmark_reports/` | Standalone sample benchmark reports from recent milestones. |

## Version markers

- Python package version: `0.11.0`
- C ABI version: `8`
- Source bundle label: `alpha-v0.11.0`
