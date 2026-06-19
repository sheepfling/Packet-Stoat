# fastdis v0.12.0-alpha2 Release Notes

Status: source release candidate.

Theme: engine integration + correctness hardening.

## Headline

fastdis Alpha 2 is the first buildable engine preview with validated
georeferenced transforms, C++ RAII ergonomics, robust snapshot handoff, and
repeatable benchmarks.

## Highlights

- Frame transform coverage now includes fixed geodetic/ECEF/ENU fixtures,
  orientation convention tests, an independent Python oracle with golden DIS
  fixtures and randomized roundtrip/property checks, and shared Unreal/Godot
  verification case data plus repeatable engine runner scripts and staged
  fixture copies for the harness projects.
- Snapshot handoff now exposes publish/acquire/release pressure stats and
  supports configurable slot counts, including a safer 3-slot engine default.
- The header-only C++ layer now includes `ScannerBuilder`,
  `EntityTableConfig`, `SnapshotBufferConfig`, span-friendly scan overloads,
  and richer scoped snapshot helpers.
- Unreal and Godot have replay-driven sample plugin/demo paths on disk, with
  shared replay-reader and UDP-ingress helpers for native examples.
- Benchmarking now includes Alpha 2 workload names, regression checks, JSON and
  Markdown output, and a checked-in sample report in `benchmark_reports/alpha2_sample/`.
- Malformed-packet tests, standalone fuzz harnesses, and repeatable
  ASAN/UBSAN builds are part of the workspace.

## ABI

- `FASTDIS_ABI_VERSION == 8`
- Native library version string: `0.12.0-alpha2`
- Python package version: `0.12.0a2`
- C++ RAII layer remains header-only in `include/fastdis/fastdis.hpp`
- Any future ABI change must pass the checklist in `docs/API_STABILITY.md`

## Known Limitations

- Entity State remains the only body fast path.
- Orientation application remains opt-in. Native convention tests and engine
  verification scaffolds are in place, but full engine-run signoff still
  depends on running Unreal/Godot locally with installed editor binaries.
- Native ingress helpers are example utilities, not part of the core C ABI.
- The Unreal and Godot sample paths are source-complete, but this release did
  not include a checked engine build on this machine because `UnrealEditor`,
  `UnrealEditor-Cmd`, `godot`, and `scons` were not available on `PATH`.

## Build Verification

```text
cmake --build build --config Release
python -m pytest
ctest --test-dir build --build-config Release --output-on-failure
python tools/check_exports.py build/libfastdis.0.12.0.dylib
python tools/run_sanitizers.py --build-dir build-sanitizers --sanitizers asan,ubsan
python tools/package_alpha2.py --write-root-checksums
```

## Benchmark Summary

See `benchmark_reports/alpha2_sample/summary.md`, `native.json`, `ctypes.json`,
and `current.json`.

Current sample readouts:

- Header-only native scanning peaked at `105.12 Mpps` on the sample run.
- Entity State transform decode workloads landed around `29-33 Mpps`.
- Snapshot publish workloads landed around `253-273 Mpps`.
- ENU-to-Unreal frame conversion reduced snapshot-walk throughput to `0.44x` of
  the no-transform baseline in the sample run.
- Triple-slot delayed-reader behavior stayed at `0.97x` of double-slot
  throughput in the sample run while giving the producer another publish slot
  before `BUSY`.

## Bundle Contents

The source bundle includes:

- `ALPHA2_RELEASE_NOTES.md`
- `RELEASE_MANIFEST.md`
- `CHECKSUMS.sha256`
- `README.md`, `CHANGELOG.md`, `LICENSE`, `CMakeLists.txt`, `pyproject.toml`
- `include/`
- `src/`
- `tests/`
- `benchmarks/`
- `fuzz/`
- `tools/`
- `docs/`
- `examples/`
- `benchmark_reports/alpha2_sample/`
- `.github/workflows/`

The bundle excludes build trees, `dist/`, compiled shared libraries, temporary
engine artifacts, virtual environments, caches, `benchmark_results/`, and
historical `release_artifacts/`.
