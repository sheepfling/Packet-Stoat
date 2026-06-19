# Release manifest

This archive is the source-only Alpha 3 bundle for `fastdis v0.13.0-alpha3`.

The bundle also carries `ALPHA3_AUDIT.md`, which records the current
requirement-by-requirement completion status and remaining gaps.

## Version markers

- Bundle label: `fastdis_alpha_v0_13_0`
- Native library version string: `0.13.0-alpha3`
- Python package version: `0.13.0a3`
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
| `generated/message_coverage_manifest.json` | Generated Alpha 3 truth table for catalog coverage, typed coverage, fuzz coverage, and oracle coverage. |
| `generated/differential_report.json` | Machine-readable Open-DIS comparison report for current Alpha 3 differential evidence. |
| `generated/orientation_formulas.json` | Generated orientation formulas derived and checked by the Alpha 3 symbolic/oracle lane. |
| `generated/fuzz_shallow_corpus/manifest.json` | Generated shallow all-PDU fuzz corpus manifest. |
| `docs/MESSAGE_CROSS_LANGUAGE_SET.md` | Generated truth table for catalog/body/adapter coverage across C, C++, Python, Unreal, Godot, and Unity. |
| `docs/MESSAGE_COVERAGE.md` | Alpha 3 human-readable message coverage report. |
| `docs/DIFFERENTIAL_TESTING.md` | Alpha 3 Open-DIS differential testing scope and known divergences. |
| `docs/CROSS_HOST_SIGNOFF.md` | Operator guide for staging host proof bundles and refreshing the Alpha 2 signoff matrix for either host-ready or stricter cross-host aggregation. |
| `src/native/fastdis_core.cpp` | C++ implementation behind the C ABI. |
| `src/fastdis/` | Python fallback, CPython extension source, and ctypes wrapper. |
| `bindings/` | Generated and shared binding-support sources for cross-language message coverage. |
| `tests/` | Python and native test coverage. |
| `benchmarks/` | Native and ctypes benchmark programs. |
| `benchmark_reports/alpha3_smoke/` | Repo-local Alpha 3 benchmark smoke JSON and Markdown output with latency quantiles and qualification JSON. |
| `benchmark_reports/alpha2_sample/` | Checked-in Alpha 2 sample benchmark JSON and Markdown output. |
| `verification_reports/alpha3_current/` | Repo-local Alpha 3 native/oracle, Godot, Unreal, and sanitizer proof artifacts for the current host. |
| `verification_reports/alpha3_hosts/` | Optional staged Alpha 3 host-specific proof bundles produced by `tools/stage_alpha3_host_report.py`. |
| `verification_reports/alpha2_sample/` | Checked-in Alpha 2 sample Unreal/Godot proof reports from real engine workflow runs. |
| `verification_reports/alpha2_hosts/` | Staged host-specific proof bundles used to build an honest host-ready or cross-host signoff matrix. |
| `verification_reports/alpha2_sample/export_check_report.md` | Built-library export proof showing the shared library matches the public C ABI symbol set. |
| `verification_reports/alpha3_current/orientation_verification_report.md` | Shared-fixture/oracle/Cesium orientation proof from deterministic Alpha 3 checks. |
| `verification_reports/alpha3_current/godot_workflow_report.md` | Godot doctor/build/verify/demo proof from the current host. |
| `verification_reports/alpha3_current/unreal_version_matrix.md` | Unreal 5.7/5.8 packaging plus harness status matrix from the current host. |
| `verification_reports/alpha3_current/sanitizer_smoke_report.md` | Alpha 3 ASAN/UBSAN sanitizer smoke result and raw command output. |
| `verification_reports/alpha3_current/io_routes_report.md` | Python localhost UDP/replay helper proof plus Godot plugin replay-route verification. |
| `verification_reports/alpha2_sample/orientation_verification_report.md` | Shared-fixture/oracle/Cesium orientation proof from deterministic Alpha 2 checks. |
| `verification_reports/alpha2_sample/orientation_runtime_report.md` | Live Unreal 5.7/5.8 and Godot runtime orientation proof with parsed numeric PASS lines. |
| `verification_reports/alpha2_sample/orientation_visual_report.md` | Unreal probe-style and Godot visual-scene orientation proof with case-level numeric PASS lines. |
| `verification_reports/alpha2_sample/*orientation*.log` | Raw host-ready runtime/visual logs for the bundled Unreal 5.7/5.8 and Godot orientation proof lanes. |
| `verification_reports/alpha2_sample/unreal_matrix_*_*.log` | Raw host-ready Unreal matrix lane logs for the supported 5.7/5.8 signoff set, with optional 5.6 compatibility evidence available separately when explicitly generated. |
| `verification_reports/alpha2_sample/unreal_host_compat_report.md` | Host/toolchain compatibility report for the supported 5.7/5.8 signoff set, with optional 5.6 compatibility guidance retained as reference. |
| `verification_reports/alpha2_sample/alpha2_signoff_matrix.md` | Signoff aggregator summarizing whether the checked report sets are host-ready, host-partial, host-sample-only, cross-host partial, or cross-host ready. |
| `verification_reports/alpha2_sample/alpha2_release_audit_report.md` | Machine-generated Alpha 2 readiness report that verifies evidence presence against the current signoff scope. |
| `fuzz/` | Header, transform, and entity-table fuzz harnesses. |
| `tools/` | Native build, replay generation, benchmark, and summary helpers. |
| `tools/package_alpha3.py` | Source-bundle packager for the Alpha 3 archive. |
| `tools/run_alpha3_sanitizer_report.py` | One-command sanitizer smoke report generator for Alpha 3 proof artifacts. |
| `tools/stage_alpha3_host_report.py` | Stages one host's Alpha 3 proof artifacts into a reusable host bundle. |
| `tools/capture_alpha2_host_signoff.py` | One-command wrapper that runs local proof generation, stages a host bundle, refreshes signoff/audit reports, and repackages the source bundle. |
| `tools/export_alpha2_host_report.py` | Exports one staged host proof bundle as a portable zip archive. |
| `tools/import_alpha2_host_report.py` | Imports a portable staged host proof archive into `verification_reports/alpha2_hosts/` with manifest validation. |
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

- Includes only source, docs, tests, generated proof artifacts, benchmark reports, and metadata.
- Excludes build trees, `dist/`, compiled `.so`/`.dylib`/`.dll` outputs,
  temporary engine artifacts, virtual environments, caches, and
  `benchmark_results/`.

## Quickstarts

- Native build and tests: `cmake --build build --config Release`, then
  `ctest --test-dir build --build-config Release --output-on-failure`.
- Python validation: `python -m pytest`.
- Alpha 3 sanitizer smoke: `python tools/run_alpha3_sanitizer_report.py`.
- Alpha 3 packaging: `python tools/package_alpha3.py --write-root-checksums`.
- Unreal sample: start with `examples/unreal/FastDisDemo/README.md`.
- Godot sample: start with `examples/godot/fastdis_demo/README.md`.
- Alpha 3 coverage readout: inspect `docs/MESSAGE_COVERAGE.md`.
- Alpha 3 differential readout: inspect `generated/differential_report.md`.
- Benchmark readout: start with `benchmark_reports/alpha2_sample/summary.md`.
- Alpha 3 benchmark readout: start with `benchmark_reports/alpha3_smoke/summary.md`.
- Engine proof readout: start with `verification_reports/alpha2_sample/unreal_version_matrix.md` and `verification_reports/alpha2_sample/godot_workflow_report.md`.
- Alpha 3 engine proof readout: inspect `verification_reports/alpha3_current/unreal_version_matrix.md` and `verification_reports/alpha3_current/godot_workflow_report.md`.
- Unreal host-compat readout: inspect `verification_reports/alpha2_sample/unreal_host_compat_report.md`.
- Generated readiness readout: inspect `verification_reports/alpha2_sample/alpha2_release_audit_report.md`.
- Signoff readout: inspect `verification_reports/alpha2_sample/alpha2_signoff_matrix.md`.
- Host/cross-host staging guide: inspect `docs/CROSS_HOST_SIGNOFF.md`.
- Unreal matrix raw evidence: inspect `verification_reports/alpha2_sample/unreal_matrix_5_6_plugin_build.log`, `verification_reports/alpha2_sample/unreal_matrix_5_7_*.log`, and `verification_reports/alpha2_sample/unreal_matrix_5_8_*.log`.
- ABI export proof: `verification_reports/alpha2_sample/export_check_report.md`.
- Orientation proof: `verification_reports/alpha2_sample/orientation_verification_report.md`.
- Orientation runtime proof: `verification_reports/alpha2_sample/orientation_runtime_report.md`.
- Orientation visual proof: `verification_reports/alpha2_sample/orientation_visual_report.md`.
- Alpha 3 native/oracle orientation proof: `verification_reports/alpha3_current/orientation_verification_report.md`.
- Alpha 3 sanitizer proof: `verification_reports/alpha3_current/sanitizer_smoke_report.md`.

## Warnings

- Full DIS 6/7 catalog coverage does not mean full typed parser coverage.
  Alpha 3 exposes the complete message catalog across C, C++, Python, Unreal,
  and Godot, but typed body/adapter support remains Entity State first.
- Position transforms are validated against shared fixtures.
- Orientation remains basis/quaternion driven; raw DIS Euler passthrough is not
  the supported engine API.
- The current Unreal 5.7/5.8 plugin packaging lanes are green on the managed
  macOS host, but the in-engine orientation/demo harness lanes are currently
  blocked here by denied writes under `/Users/Shared/Epic Games/.../Engine/Intermediate/...`.
- Checked-in engine proof reports are host evidence for the packaged scope, not
  a guarantee that every machine will match the same Unreal/Godot lane status.
- `tools/package_alpha3.py` writes a source-only Alpha 3 archive and excludes
  generated build products and engine artifacts by policy.
