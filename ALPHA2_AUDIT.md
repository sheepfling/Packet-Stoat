# fastdis v0.12.0-alpha2 Audit

Audit date: `2026-06-19`

This document maps the Alpha 2 plan to the current repository state. It is an
evidence-backed audit, not a promise that every item is fully signed off.

Status legend:

- `complete`: the current tree contains direct evidence for the requirement.
- `partial`: substantial implementation exists, but at least one explicit exit
  criterion is still unproven, missing, or only indirectly supported.
- `host-blocked`: the implementation exists, but local engine proof on this
  host is blocked by an external install or platform constraint.
- `missing`: the required implementation or proof artifact is not present.

## Success Criteria

| Criterion | Status | Evidence | Notes |
|---|---|---|---|
| C ABI remains stable unless a clearly justified ABI v9 is needed | `complete` | `include/fastdis/fastdis.h`, `docs/API_STABILITY.md`, `docs/ABI.md` | Current ABI marker remains `8`; snapshot expansion stayed additive. |
| C++ RAII layer remains header-only and first-class | `complete` | `include/fastdis/fastdis.hpp`, `docs/CXX_RAII.md`, `tests/native/test_cpp_raii.cpp` | Builder/config surface, span overloads, and scoped snapshot helpers are on disk. |
| Unreal sample plugin builds in a real Unreal project | `partial` | `examples/unreal/FastDis/`, `examples/unreal/FastDisDemo/`, `verification_reports/alpha2_sample/unreal_version_matrix.md` | Proven on this host for Unreal 5.7 and 5.8. Unreal 5.6 is host-blocked by engine/Xcode/macOS compatibility before plugin code compiled. |
| Godot GDExtension sample builds against `godot-cpp` | `complete` | `examples/godot/fastdis_gdextension/`, `examples/godot/fastdis_demo/`, `verification_reports/alpha2_sample/godot_workflow_report.md` | Checked-in host-sample report shows doctor/build/verify/demo passed. |
| Frame transform tests cover ECEF -> ENU -> Unreal/Godot mappings | `complete` | `include/fastdis/fastdis_frames.hpp`, `tests/native/test_frames.cpp`, `docs/FRAME_TRANSFORMS.md` | Fixtures cover equator, Houston/Ellington-style, mid-latitude, and near-pole origins. |
| Unreal and Godot orientation harnesses verify engine basis vectors against shared fixtures before orientation is advertised beyond experimental | `partial` | `tests/data/orientation_engine_cases.json`, `examples/unreal/FastDisOrientationVerification/`, `examples/godot/fastdis_orientation_verification/`, `docs/ENGINE_ORIENTATION_VERIFICATION.md` | Harnesses and shared fixtures exist; host-sample Unreal 5.7/5.8 and Godot lanes passed. Orientation still remains opt-in because proof is host-sample rather than matrix-wide signoff. |
| Snapshot handoff has a clear busy/drop/backpressure story | `complete` | `include/fastdis/fastdis.h`, `include/fastdis/fastdis.hpp`, `docs/DOUBLE_BUFFER_SNAPSHOTS.md`, `tests/native/test_c_api.cpp`, `tests/native/test_cpp_raii.cpp`, `tests/test_native_ctypes.py` | Double/triple-slot semantics and pressure stats are documented and tested. |
| Benchmark report compares Alpha 1 vs Alpha 2 paths | `complete` | `benchmark_reports/alpha2_sample/summary.md`, `benchmark_reports/alpha2_sample/current.json`, `tools/check_benchmark_regression.py`, `docs/BENCHMARKING.md` | Sample report and regression checker are checked in. |
| Source bundle includes docs, examples, checksums, and release notes | `complete` | `tools/package_alpha2.py`, `CHECKSUMS.sha256`, `RELEASE_MANIFEST.md`, `ALPHA2_RELEASE_NOTES.md` | Bundle metadata and sample benchmark/verification reports are tracked. |

## Workseries

### WS1: Release Branch and API Hygiene

Status: `partial`

Evidence:

- `ALPHA2_PLAN.md`
- `CHANGELOG.md`
- `ALPHA2_RELEASE_NOTES.md`
- `docs/API_STABILITY.md`
- `docs/ABI.md`
- `tools/check_exports.py`
- `tests/test_export_checker.py`

What is proven:

- The branch/version plan and API-stability docs are present.
- ABI checklist text exists.
- Export checking logic and tests exist.

Remaining gap:

- The plan called for a generated exported-symbol list from the built shared
  library. The checker can write one, but no tracked exported-symbol manifest is
  currently present in the repo or bundle.

### WS2: Frame Transform Correctness

Status: `complete`

Evidence:

- `include/fastdis/fastdis_frames.hpp`
- `docs/FRAME_TRANSFORMS.md`
- `tests/native/test_frames.cpp`
- `tests/native/test_orientation_conventions.cpp`

What is proven:

- ECEF, ENU, Unreal, and Godot mappings are implemented.
- Asset-basis and orientation-policy surfaces are explicit.
- Equator, Houston/Ellington-style, mid-latitude, and near-pole cases are on
  disk in native tests.

### WS3: Snapshot Buffer Hardening

Status: `complete`

Evidence:

- `include/fastdis/fastdis.h`
- `include/fastdis/fastdis.hpp`
- `src/native/fastdis_core.cpp`
- `docs/DOUBLE_BUFFER_SNAPSHOTS.md`
- `tests/native/test_c_api.cpp`
- `tests/native/test_cpp_raii.cpp`
- `tests/test_native_ctypes.py`

What is proven:

- `fastdis_entity_snapshot_buffer_create_ex(capacity, slot_count)` exists.
- Two-slot shorthand remains available.
- Pressure stats exist and are exposed in C, C++, and Python surfaces.
- Triple-slot delayed-reader behavior is tested.

### WS4: C++ RAII Quality of Life

Status: `complete`

Evidence:

- `include/fastdis/fastdis.hpp`
- `docs/CXX_RAII.md`
- `examples/cpp/raii_snapshot_buffer.cpp`
- `examples/cpp/udp_burst.cpp`
- `tests/native/test_cpp_raii.cpp`

What is proven:

- `ScannerBuilder`, `EntityTableConfig`, and `SnapshotBufferConfig` exist.
- C++20 `std::span` overloads coexist with pointer/count fallbacks.
- `try_*` no-exception paths exist.
- `ScopedSnapshotView` exposes the intended convenience surface.

### WS5: Unreal Adapter Runnable Sample

Status: `partial`

Evidence:

- `examples/unreal/FastDis/`
- `examples/unreal/FastDisDemo/`
- `docs/UNREAL_ADAPTER.md`
- `docs/UNREAL_VERSION_MATRIX.md`
- `verification_reports/alpha2_sample/unreal_version_matrix.md`

What is proven:

- The plugin, sample docs, replay-driven demo path, and workflow scripts exist.
- Host-sample proof shows plugin/orientation/demo passed for Unreal 5.7 and 5.8.

Remaining gap:

- The plan target was broader than one host. Unreal 5.6 currently fails on this
  host before plugin compilation, so the matrix is not uniformly green.

### WS6: Godot GDExtension Runnable Sample

Status: `complete`

Evidence:

- `examples/godot/fastdis_gdextension/`
- `examples/godot/fastdis_demo/`
- `docs/GODOT_ADAPTER.md`
- `docs/GODOT_WORKFLOW.md`
- `verification_reports/alpha2_sample/godot_workflow_report.md`

What is proven:

- GDExtension wrapper, demo project, replay-loader path, and workflow scripts
  exist.
- Checked-in host-sample report shows doctor/build/verify/demo/missing-lib
  lanes passed.

### WS7: Replay and Benchmark Expansion

Status: `complete`

Evidence:

- `benchmarks/native_bench.cpp`
- `tools/run_benchmarks.py`
- `tools/summarize_benchmarks.py`
- `tools/check_benchmark_regression.py`
- `docs/BENCHMARKING.md`
- `benchmark_reports/alpha2_sample/summary.md`

What is proven:

- Alpha 2 workload names and report generation paths are on disk.
- Sample JSON and Markdown benchmark outputs are checked in.
- Slot-count and frame-transform overhead are represented in the summary
  tooling.

### WS8: Native Ingress Helpers

Status: `complete`

Evidence:

- `examples/common/replay_reader.hpp`
- `examples/common/udp_receiver.hpp`
- `examples/common/README.md`
- `examples/cpp/raii_snapshot_buffer.cpp`
- `examples/cpp/udp_burst.cpp`

What is proven:

- Replay-reader and UDP burst helpers exist under `examples/common/`.
- Core parser headers and docs still keep networking out of the core C ABI.

### WS9: Fuzzing and Malformed Packet Hardening

Status: `complete`

Evidence:

- `fuzz/fuzz_header.cpp`
- `fuzz/fuzz_entity_transform.cpp`
- `fuzz/fuzz_entity_table_ingest.cpp`
- `tools/run_sanitizers.py`
- `docs/HARDENING.md`
- `tests/native/test_c_api.cpp`

What is proven:

- Standalone fuzz harnesses exist.
- Sanitizer runner supports `asan`, `ubsan`, and `tsan`.
- Native tests cover malformed/null/short packet handling.

### WS10: Alpha 2 Packaging

Status: `complete`

Evidence:

- `tools/package_alpha2.py`
- `ALPHA2_RELEASE_NOTES.md`
- `RELEASE_MANIFEST.md`
- `CHECKSUMS.sha256`
- `benchmark_reports/alpha2_sample/`
- `verification_reports/alpha2_sample/`

What is proven:

- Packaging metadata exists and is source-only.
- Sample benchmark and engine proof reports are included in the tracked source
  set.

### WS11: Orientation Convention Verification

Status: `partial`

Evidence:

- `include/fastdis/fastdis_orientation.hpp`
- `docs/ORIENTATION_CONVENTIONS.md`
- `docs/ORIENTATION_VERIFICATION.md`
- `tests/native/test_orientation_conventions.cpp`
- `tests/oracles/orientation_oracle.py`
- `tests/data/orientation_golden_cases.json`
- `tests/data/orientation_engine_cases.json`
- `tests/test_orientation_engine_cases.py`
- `tests/test_orientation_cesium.py`

What is proven:

- Canonical body-FRD/ECEF orientation math exists.
- Golden fixtures and a Python oracle exist.
- Shared engine-fixture data includes Unreal, Godot, Unity, and Cesium target
  expectations.

Remaining gap:

- The plan explicitly called for Cesium comparison tests and numeric visual-scene
  reporting. The fixture/oracle layer exists, but there is no checked-in
  command-output artifact proving a full Cesium runtime comparison or a visual
  scene report.

### WS12: In-Engine Orientation Verification

Status: `partial`

Evidence:

- `docs/ENGINE_ORIENTATION_VERIFICATION.md`
- `tests/data/orientation_engine_cases.json`
- `examples/unreal/FastDisOrientationVerification/`
- `examples/godot/fastdis_orientation_verification/`
- `verification_reports/alpha2_sample/unreal_version_matrix.md`
- `verification_reports/alpha2_sample/godot_workflow_report.md`

What is proven:

- Unreal automation harness, probe actor, and shared fixtures are on disk.
- Godot headless/visual verification harness and shared fixtures are on disk.
- Host-sample workflow reports show passing orientation lanes for Unreal 5.7,
  Unreal 5.8, and Godot on this machine.

Remaining gaps:

- Unreal command-line pass evidence is host-sample rather than a generalized
  cross-host signoff.
- The checked-in reports summarize pass/fail lanes but do not themselves embed
  the numeric axis dot-product output from the visual scenes.

## Definition-of-Done Audit

Planned shape:

```cpp
auto scanner = fastdis::ScannerBuilder()
    .entity_transform_profile()
    .versions({6, 7})
    .build();
fastdis::EntityTable table(4096);
fastdis::SnapshotBuffer snapshots =
    fastdis::SnapshotBufferConfig()
        .capacity(4096)
        .slots(3)
        .build();
auto stats = table.ingest(scanner, packets, true);
auto published = snapshots.publish_changed(table, true);
auto view = snapshots.acquire_latest();
for (const auto& snapshot : view) {
    auto pose = fastdis::frames::to_unreal_pose(snapshot.transform, georef);
    // Apply to actor.
}
```

Status: `complete`

Evidence:

- `include/fastdis/fastdis.hpp`
- `examples/cpp/raii_snapshot_buffer.cpp`
- `examples/unreal/FastDis/Source/FastDisUnreal/Private/FastDisWorldSubsystem.cpp`

The code shape described by the plan is supported by the current C++ surface.

## Remaining Alpha 2 Risks

- WS1 still lacks a tracked exported-symbol manifest generated from a real
  shared-library build.
- Unreal matrix coverage is not uniformly green because Unreal 5.6 is blocked by
  host compatibility on this machine.
- Orientation remains correctly opt-in, but WS11/WS12 still rely on host-sample
  proof rather than a fully generalized engine/Cesium verification record.
- Full DIS 6/7 message catalog coverage is present across languages, but typed
  body/adapter support remains Entity State only. That is documented and should
  not be overstated elsewhere in the release materials.
