# fastdis v0.12.0-alpha2 Plan

Theme: engine integration + correctness hardening.

Alpha 1 proved the core architecture: C ABI shared library, header-only C++
RAII wrapper, Entity State fast path, batch output, latest-state entity table,
double-buffer snapshots, Unreal/Godot scaffolds, frame transform helpers, and
benchmark tooling.

Alpha 2 turns that into a credible native SDK preview. The guiding rule is:

```text
Do not expand into a full DIS parser yet.
Make the Entity State / transform / engine path excellent first.
```

## Release Targets

- Branch: `alpha2/v0.12`
- Version: `fastdis v0.12.0-alpha2`
- Milestone: `Alpha 2`
- Headline: first buildable engine preview with validated georeferenced
  transforms, C++ RAII ergonomics, robust snapshot handoff, and repeatable
  benchmarks.

## Success Criteria

- C ABI remains stable unless a clearly justified ABI v9 is needed.
- C++ RAII layer remains header-only and first-class.
- Unreal sample plugin builds in a real Unreal project.
- Godot GDExtension sample builds against `godot-cpp`.
- Frame transform tests cover ECEF -> ENU -> Unreal/Godot mappings.
- Unreal and Godot orientation harnesses verify engine basis vectors against
  shared fixtures before orientation is advertised beyond experimental.
- Snapshot handoff has a clear busy/drop/backpressure story.
- Benchmark report compares Alpha 1 vs Alpha 2 paths.
- Source bundle includes docs, examples, checksums, and release notes.

## Workseries

### WS1: Release Branch and API Hygiene

Goal: start Alpha 2 from a controlled branch and prevent accidental ABI churn.

Tasks:
- Add `ALPHA2_PLAN.md`, `CHANGELOG.md`, `docs/API_STABILITY.md`, and
  `ALPHA2_RELEASE_NOTES.md`.
- Update `docs/ABI.md` with the ABI checklist.
- Add `tools/check_exports.py` to verify public symbols in `libfastdis.so`,
  `libfastdis.dylib`, or `fastdis.dll`.
- Generate an exported symbol list from the built shared library.

Exit criteria:
- C ABI tests pass.
- C++ RAII tests pass.
- Python tests pass.
- Exported symbol list is generated.
- Release notes template exists.

### WS2: Frame Transform Correctness

Goal: make coordinate conversion trustworthy before engine demos depend on it.

Tasks:
- Expand `include/fastdis/fastdis_frames.hpp`.
- Expand `docs/FRAME_TRANSFORMS.md`.
- Expand `tests/native/test_frames.cpp`.
- Add fixtures for geodetic origin -> ECEF, ECEF -> local ENU, ENU -> Unreal,
  ENU -> Godot, roundtrip tolerances, and north/east/up sanity.
- Cover Houston/Ellington-style, equator, mid-latitude, and near-pole origins.
- Add asset-basis configuration and keep orientation opt-in.

Exit criteria:
- Position transform tests pass with strict tolerances.
- Unreal north/east/up mapping is tested.
- Godot north/east/up mapping is tested.
- Orientation remains disabled by default.
- Docs warn clearly about asset axes and DIS orientation validation.

### WS3: Snapshot Buffer Hardening

Goal: make native table/snapshot handoff robust for real engine timing.

Preferred design: N-slot snapshot buffer with 2 slots preserving existing
double-buffer semantics and 3 slots as the engine-friendly default.

Tasks:
- Add `fastdis_entity_snapshot_buffer_create_ex(capacity, slot_count)`. (done)
- Keep `fastdis_entity_snapshot_buffer_create(capacity)` as shorthand for
  two slots. (done)
- Add publish/acquire/release/drop/busy stats. (done: additive stats API)
- Add delayed-reader tests. (done for strict double-buffer busy stats)
- Update the C++ RAII wrapper with slot-count support. (done)
- Document double vs triple buffering. (done)

Exit criteria:
- Delayed-reader tests exist.
- Busy behavior is deterministic.
- Stats expose publish pressure. (done)
- 3-slot buffer avoids the common delayed-reader case. (done)
- C++ RAII wrapper supports slot count. (done)

### WS4: C++ RAII Quality of Life

Goal: make C++ the best native consumer experience.

Tasks:
- Add `fastdis::ScannerBuilder`, `fastdis::EntityTableConfig`, and
  `fastdis::SnapshotBufferConfig`. (done)
- Add C++20 span-like overloads when available with C++17 fallback. (done)
- Add no-exceptions equivalents for convenience calls. (done through existing `try_*` surface and no-exceptions test target)
- Improve `ScopedSnapshotView` with `empty`, `size`, `generation`, `slot`,
  `dropped`, `begin`, and `end`. (done)
- Add engine-friendly snapshot accessors. (done)

Exit criteria:
- C++ examples no longer need raw C calls except where intentionally shown. (done)
- No-exceptions build still passes. (done)
- RAII wrappers do not expose C++ ABI through DLL boundaries.
- Docs include a one-page C++ quickstart. (done)

### WS5: Unreal Adapter Runnable Sample

Goal: make the Unreal adapter a real small plugin demo.

Tasks:
- Add `examples/unreal/FastDisDemo/`.
- Include plugin, module, simple actor registration, replay-file loader actor,
  WorldSubsystem integration, and ThirdParty layout docs. (plugin sample,
  replay actor, and packaging docs done)
- Add editor-exposed georeference, orientation, scale, slot, and stale settings.
  (done)
- Add transform application modes: snap, interpolate, position-only, and
  position plus experimental rotation. (done)

Exit criteria:
- A user can drop the plugin into a UE project.
- A replay file can move a few actors.
- Position-only mode works.
- Orientation remains opt-in.
- Docs explain where to put `fastdis.dll`, `libfastdis.so`, or
  `libfastdis.dylib`.

### WS6: Godot GDExtension Runnable Sample

Goal: make the Godot adapter a real runnable extension sample.

Tasks:
- Add `examples/godot/fastdis_demo/`. (done)
- Include `project.godot`, `FastDisWorld` node, demo scene, replay loader
  script, and registered `Node3D` entities. (done)
- Add GDExtension API for georeference, entity registration, packet/replay
  ingest, and latest snapshot application. (done)
- Add position-only and experimental yaw/pitch/roll transform modes. (done)

Exit criteria:
- Godot project opens.
- Extension loads.
- Replay data moves `Node3D` objects.
- Docs explain `godot-cpp` build requirements.
- Missing native library errors are clear and do not crash the engine.

### WS7: Replay and Benchmark Expansion

Goal: make performance evaluation credible and repeatable.

Tasks:
- Add synthetic and mixed workloads for header scan, Entity State, filtering,
  snapshot publishing, delayed readers, and frame transforms.
- Add `tools/check_benchmark_regression.py`.
- Report header scan Mpps, transform decode Mpps, table ingest Mpps, snapshot
  publish records/sec, engine transform records/sec, and path ratios.

Exit criteria:
- Benchmark report generated as Markdown and JSON.
- Alpha 2 includes a sample benchmark report.
- Frame transform overhead is measured.
- Snapshot slot-count behavior is measured.
- Regression script exists.

### WS8: Native Ingress Helpers

Goal: make examples easier without bloating the core C ABI.

Tasks:
- Add optional shared example helpers under `examples/common/`.
- Support `.fastdispkt` replay, UDP burst receive, and batching into
  `fastdis_packet_view_t`.
- Keep OS networking out of the core parser library.

Exit criteria:
- Unreal, Godot, and C++ examples can share replay reader logic.
- UDP example exists.
- Core C ABI stays clean.
- No mandatory `libpcap` dependency.

### WS9: Fuzzing and Malformed Packet Hardening

Goal: make the native parser safe against bad network input.

Tasks:
- Add fuzz targets for header, Entity State transform, and table ingest.
- Add ASAN, UBSAN, and TSAN where applicable.
- Add malformed packet tests for short, inconsistent, invalid, truncated,
  oversized, zero-length, and null-input cases.

Exit criteria:
- Fuzz targets compile.
- Sanitizer test job passes.
- Malformed packet tests pass.
- No crashes on random byte input.

### WS10: Alpha 2 Packaging

Goal: ship a clean second alpha bundle.

Tasks:
- Bundle source-only `fastdis_alpha_v0_12_0/` with release notes, manifest,
  checksums, headers, source, tests, benchmarks, tools, docs, examples, and
  benchmark reports.
- Include C ABI version, C++ RAII version, known limitations, build
  instructions, Unreal/Godot quickstarts, benchmark summary, and frame transform
  warning.
- Exclude build directories, dist outputs, native binaries, and engine build
  artifacts.

Exit criteria:
- Zip integrity verified.
- Checksums generated.
- Source-only bundle.
- Release notes complete.
- Sample benchmark report included.

### WS11: Orientation Convention Verification

Goal: prevent DIS orientation from becoming a loose Euler-angle convenience
mapping. The canonical pipeline is body-FRD basis in ECEF, then direction-only
conversion to local ENU, then target engine basis/quaternion construction.

Tasks:
- Add `docs/ORIENTATION_CONVENTIONS.md`.
- Add `docs/ORIENTATION_VERIFICATION.md`.
- Add `include/fastdis/fastdis_orientation.hpp`.
- Add `tests/native/test_orientation_conventions.cpp`.
- Decode DIS `psi/theta/phi` into `BodyFrdBasisEcef`.
- Map body FRD ECEF to body FRU ENU using direction-only transforms.
- Define target frame names for standalone Unreal, Unity, Godot, CesiumJS,
  Cesium Unity, and Cesium Unreal.
- Add golden DIS attitude fixtures and an independent Python oracle.
- Add engine basis tests and visual verification scenes before enabling
  orientation in adapters.

Exit criteria:
- Orientation remains disabled by default.
- Native basis tests verify unit length, orthogonality, and determinant.
- Golden DIS fixtures pass.
- Independent oracle agrees.
- Engine basis tests pass.
- Cesium comparison tests pass.
- Visual scenes report numeric axis dot-products.

### WS12: In-Engine Orientation Verification

Goal: verify orientation inside Unreal and Godot transform systems before
claiming adapter orientation support. Native math tests are necessary but not
sufficient; actor/node basis vectors must match shared fixtures after transforms
are applied in-engine.

Tasks:
- Add `docs/ENGINE_ORIENTATION_VERIFICATION.md`.
- Add `tests/data/orientation_engine_cases.json` as the shared fixture contract.
- Add `examples/unreal/FastDisOrientationVerification/` with automation-test
  and probe-actor scaffolds.
- Add `examples/godot/fastdis_orientation_verification/` with headless and
  visual-scene scaffolds.
- Compare Unreal `GetActorForwardVector`, `GetActorRightVector`, and
  `GetActorUpVector` against fixture axes.
- Compare Godot `basis.x`, `basis.y`, and `-basis.z` against fixture axes.
- Add asset-basis verification for Unreal marker components and Godot
  node-forward vs model-front modes.
- Keep orientation opt-in until the adapter-produced `FTransform` and
  `Transform3D` paths pass these tests.

Exit criteria:
- Unreal `FastDis.Orientation` automation tests pass from command line.
- Godot headless orientation script passes from command line.
- Both engines consume the same fixture file as native tests.
- All comparisons are vector/quaternion based, not Euler based.
- Visual scenes report numeric axis dot-products and PASS/FAIL.
- Asset-basis correction tests exist.

## Issue Breakdown

- A2-001 Release branch and API stability checklist
- A2-002 Exported symbol checker
- A2-003 Frame transform fixture tests
- A2-004 Asset basis and orientation policy docs
- A2-005 Snapshot buffer stats (done)
- A2-006 Optional triple-buffer snapshot support (done)
- A2-007 C++ ScannerBuilder / config builders
- A2-008 Improve ScopedSnapshotView ergonomics
- A2-009 Unreal plugin buildable sample
- A2-010 Unreal replay actor demo
- A2-011 Godot GDExtension buildable sample
- A2-012 Godot replay scene demo
- A2-013 Replay/UDP common helpers
- A2-014 Expanded benchmark workloads
- A2-015 Benchmark regression checker
- A2-016 Sanitizer builds
- A2-017 Fuzz targets
- A2-018 Alpha 2 release bundle
- A2-019 Orientation convention study
- A2-020 Canonical body-FRD-in-ECEF orientation API
- A2-021 DIS psi/theta/phi golden fixtures
- A2-022 Engine target-frame mapping tests
- A2-023 Cesium ENU/ESU/EUN verification
- A2-024 Unreal orientation verification actor
- A2-025 Unity adapter scaffold + orientation verification scene
- A2-026 Godot orientation verification scene
- A2-027 Orientation fuzz/property tests
- A2-028 Shared in-engine orientation fixture contract
- A2-029 Unreal automation orientation basis tests
- A2-030 Unreal orientation probe actor and visual map
- A2-031 Godot headless orientation basis tests
- A2-032 Godot orientation visual scene
- A2-033 Engine asset-basis verification tests

## Scope

Must have:
- Frame transform validation.
- Shared in-engine orientation fixture contract.
- C++ RAII improvements.
- Snapshot buffer stats or triple-buffer support.
- Expanded benchmarks.
- Alpha 2 source bundle.

Should have:
- Buildable Unreal sample.
- Buildable Godot sample.
- Unreal/Godot in-engine orientation numerical tests.
- Replay-driven engine demos.
- Benchmark regression checker.
- Malformed packet hardening.

Could have:
- UDP receiver helper.
- Basic Fire/Detonation prefix exploration.
- Python convenience improvements.
- CI matrix for all platforms.

## Implementation Order

1. API hygiene and branch setup.
2. Frame transform correctness tests.
3. Snapshot buffer stats / triple-buffer support.
4. C++ RAII builder ergonomics.
5. Benchmark expansion.
6. Unreal runnable sample.
7. Godot runnable sample.
8. Orientation convention verification.
9. In-engine orientation verification.
10. Fuzz/sanitizer hardening.
11. Alpha 2 packaging.

The engine adapters depend on frame transforms and snapshot semantics, so those
must stabilize before deeper Unreal/Godot demo work.

## Definition of Done

Alpha 2 is ready when this shape works:

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

The final bundle must state what got faster, what did not matter, the cost of
frame transforms, the cost of entity-table updates, the cost of snapshot
handoff, and the difference between callback, batch, and latest-state paths.
