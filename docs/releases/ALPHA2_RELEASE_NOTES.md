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
  verification case data plus repeatable engine runner scripts, staged fixture
  copies for the harness projects, and adapter-side debug transform helpers for
  Unreal `FTransform` and Godot `Transform3D` verification.
- Snapshot handoff now exposes publish/acquire/release pressure stats and
  supports configurable slot counts, including a safer 3-slot engine default.
- The header-only C++ layer now includes `ScannerBuilder`,
  `EntityTableConfig`, `SnapshotBufferConfig`, span-friendly scan overloads,
  and richer scoped snapshot helpers.
- Unreal and Godot have replay-driven sample plugin/demo paths on disk, with
  shared replay-reader and UDP-ingress helpers for native examples.
- Benchmarking now includes Alpha 2 workload names, regression checks, and
  repeatable JSON/Markdown report generation through the benchmark tooling.
- Malformed-packet tests, standalone fuzz harnesses, and repeatable
  ASAN/UBSAN builds are part of the workspace.

## ABI

- `FASTDIS_ABI_VERSION == 8`
- Native library version string: `0.12.0-alpha2`
- Python package version: `0.12.0a2`
- C++ RAII layer remains header-only in `include/fastdis/fastdis.hpp`
- Any future ABI change must pass the checklist in `docs/API_STABILITY.md`
- DIS 6/7 message catalog coverage is generated across C, C++, Python, Unreal,
  and Godot, but typed body/adapter support remains Entity State only.

## Known Limitations

- Entity State remains the only body fast path.
- The checked-in DIS 6/7 cross-language catalog is complete for message
  identification, but Alpha 2 is not a full typed parser for every DIS body.
- Orientation application remains opt-in. Native convention tests and engine
  verification scaffolds are in place, but full engine-run signoff still
  depends on running Unreal/Godot locally with installed editor binaries.
- Native ingress helpers are example utilities, not part of the core C ABI.
- The Unreal and Godot sample paths are source-complete, but this release did
  include checked host-ready engine workflow reports under
  `verification_reports/alpha2_sample/`.
  Current host-ready state on this machine:
  - Unreal 5.7: plugin build passed, orientation passed, demo passed
  - Unreal 5.8: plugin build passed, orientation passed, demo passed
  - Unreal 5.6: demoted to optional compatibility-only evidence on this host
  - Godot: doctor/build/verify/demo/missing-lib all passed

## Build Verification

```text
cmake --build build --config Release
python -m pytest
ctest --test-dir build --build-config Release --output-on-failure
python tools/check_exports.py build/libfastdis.0.12.0.dylib
python tools/run_sanitizers.py --build-dir build-sanitizers --sanitizers asan,ubsan
python tools/unreal_workflow.py matrix --versions 5.7 5.8
python tools/godot_workflow.py report
python tools/capture_alpha2_host_signoff.py
python tools/package_alpha2.py --write-root-checksums
```

## Benchmark Summary

Generate current benchmark outputs locally with `python tools/run_benchmarks.py`
and use `docs/BENCHMARKING.md` as the methodology reference.

Engine proof readouts live in:

- `verification_reports/alpha2_sample/export_check_report.md`
- `verification_reports/alpha2_sample/orientation_verification_report.md`
- `verification_reports/alpha2_sample/orientation_runtime_report.md`
- `verification_reports/alpha2_sample/orientation_visual_report.md`
- `verification_reports/alpha2_sample/unreal_version_matrix.md`
- `verification_reports/alpha2_sample/unreal_host_compat_report.md`
- `verification_reports/alpha2_sample/alpha2_signoff_matrix.md`
- `verification_reports/alpha2_sample/alpha2_release_audit_report.md`
- `verification_reports/alpha2_sample/godot_workflow_report.md`
- `verification_reports/alpha2_hosts/`
- `verification_reports/alpha2_sample/unreal_orientation_runtime_5_7.log`
- `verification_reports/alpha2_sample/unreal_matrix_5_6_plugin_build.log`
- `verification_reports/alpha2_sample/unreal_matrix_5_7_plugin_build.log`
- `verification_reports/alpha2_sample/unreal_matrix_5_7_orientation.log`
- `verification_reports/alpha2_sample/unreal_matrix_5_7_demo.log`
- `verification_reports/alpha2_sample/unreal_orientation_harness_5_7.log`
- `verification_reports/alpha2_sample/unreal_matrix_5_8_plugin_build.log`
- `verification_reports/alpha2_sample/unreal_matrix_5_8_orientation.log`
- `verification_reports/alpha2_sample/unreal_matrix_5_8_demo.log`
- `verification_reports/alpha2_sample/unreal_orientation_visual_5_7.log`
- `verification_reports/alpha2_sample/unreal_orientation_visual_harness_5_7.log`
- `ALPHA2_AUDIT.md`

Message-surface truth tables live in:

- `docs/MESSAGE_CROSS_LANGUAGE_SET.md`
- `docs/message_cross_language_set.json`

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

- `ALPHA2_AUDIT.md`
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
- `verification_reports/alpha2_sample/`
- `verification_reports/alpha2_hosts/`
- `verification_reports/alpha2_sample/unreal_orientation_runtime_5_8.log`
- `verification_reports/alpha2_sample/unreal_orientation_harness_5_8.log`
- `verification_reports/alpha2_sample/godot_orientation_runtime.log`
- `verification_reports/alpha2_sample/unreal_orientation_runtime_5_7.log`
- `verification_reports/alpha2_sample/unreal_orientation_harness_5_7.log`
- `verification_reports/alpha2_sample/unreal_orientation_visual_5_8.log`
- `verification_reports/alpha2_sample/unreal_orientation_visual_harness_5_8.log`
- `verification_reports/alpha2_sample/godot_orientation_visual.log`
- `verification_reports/alpha2_sample/unreal_orientation_visual_5_7.log`
- `verification_reports/alpha2_sample/unreal_orientation_visual_harness_5_7.log`
- `verification_reports/alpha2_sample/unreal_matrix_5_6_plugin_build.log`
- `verification_reports/alpha2_sample/unreal_matrix_5_7_plugin_build.log`
- `verification_reports/alpha2_sample/unreal_matrix_5_7_orientation.log`
- `verification_reports/alpha2_sample/unreal_matrix_5_7_demo.log`
- `verification_reports/alpha2_sample/unreal_matrix_5_8_plugin_build.log`
- `verification_reports/alpha2_sample/unreal_matrix_5_8_orientation.log`
- `verification_reports/alpha2_sample/unreal_matrix_5_8_demo.log`
- `docs/MESSAGE_CROSS_LANGUAGE_SET.md`
- `docs/message_cross_language_set.json`
- `.github/workflows/`

The bundle excludes build trees, `dist/`, compiled shared libraries, temporary
engine artifacts, virtual environments, caches, `benchmark_results/`, and
historical `release_artifacts/`.

## Signoff State

- `tools/run_alpha2_signoff_matrix.py` now aggregates one or more host report
  sets into a machine-readable signoff result. The default packaged macOS flow
  is host-ready with one verified host; pass `--min-host-count 2` or more when
  you want stricter cross-host signoff.
- `tools/stage_alpha2_host_report.py` captures one host's proof reports into a
  normalized `verification_reports/alpha2_hosts/<host-label>/` bundle so a
  second machine can contribute evidence without hand-copying files.
- `tools/capture_alpha2_host_signoff.py` is the one-command operator wrapper
  that runs the local proof generators, stages the host bundle, refreshes the
  aggregate signoff/audit reports, and updates the source bundle checksums.
- `tools/export_alpha2_host_report.py` and
  `tools/import_alpha2_host_report.py` now provide a portable zip-based
  transfer path for getting a second machine's staged host bundle back into the
  main repo without manual file copying, including `.sha256` sidecar
  verification during import when the checksum file is present.
- The staged host manifest now carries a stable machine fingerprint and an
  aggregate proof-payload digest so copied aliases from the same host/report
  set do not count as independent signoff evidence.
- The checked-in sample result is currently `host-ready`, which matches the
  real macOS scope of the evidence bundle: this machine has full Godot proof
  plus passing Unreal 5.7/5.8 lanes. Cross-host aggregation still remains
  available by re-running the signoff flow with `--min-host-count 2` or more.
- `tools/package_alpha2.py` refreshes both the release audit and signoff matrix
  before packaging so the bundle reflects the latest tracked proof state.
- `docs/CROSS_HOST_SIGNOFF.md` is the operator runbook for that staging and
  aggregation flow.
