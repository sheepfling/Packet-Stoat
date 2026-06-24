# FastDIS Roadmap

## Active Product Backlog

The active backlog is organized around two epics:

- Epic 1: [Unreal GRILL DIS Parity First](PRODUCT_BACKLOG.md#epic-1-unreal-grill-dis-parity-first)
- Epic 2: [Full DIS 6/7 PDU Feature Buildout](PRODUCT_BACKLOG.md#epic-2-full-dis-67-pdu-feature-buildout)

The ordering rule is deliberate: FastDIS should reach Unreal GRILL DIS parity as
the first product gate, then expand all generated PDU surfaces toward full DIS
6/7 feature coverage.

Supporting plans:

- [Unreal GRILL parity matrix](UNREAL_GRILL_PARITY.md)
- [Unreal Fab asset worklist](UNREAL_FAB_ASSET_WORKLIST.md)
- [Epic 1 differentiator audit](EPIC1_DIFFERENTIATOR_AUDIT.md)
- [Epic 2 full DIS buildout](EPIC2_FULL_DIS_BUILDOUT.md)
- [Epic 2 audit](EPIC2_AUDIT.md)
- [Epic 2 parity](EPIC2_PARITY.md)
- [DIS 6/7 full coverage plan](DIS_FULL_COVERAGE_PLAN.md)

## Completed Release Tracks

Historical release plans remain under [Release And Publishing](README.md#release-and-publishing).

- `v0.13.0-alpha3`
- Plan: [ALPHA3_PLAN.md](releases/ALPHA3_PLAN.md)
- Goal blurb: [ALPHA3_GOAL.md](releases/ALPHA3_GOAL.md)

- Header-only DIS packet scanner.
- Pure-Python fallback.
- Optional CPython header scanner.
- Portable C ABI exported from a C++ implementation.
- CMake shared-library build for `libfastdis.so`, `libfastdis.dylib`, and `fastdis.dll`.
- ctypes wrapper for ABI validation.
- Entity State PDU fixed-prefix parser and scanner.
- Early C-side downselect by header fields, sample rate, Entity State force ID, and entity ID.
- Entity State field subscriptions.
- Opaque scanner context with entity-ID allow/block filters.
- Native and ctypes benchmark harnesses.
- Callback-free Entity State batch output.
- Engine-shaped compact transform batch output.
- Simple `.fastdispkt` replay-file benchmark input format.
- Config/scanner profiles for common scan modes.
- Native latest-state cache / entity table.
- Changed/stale/all snapshots and stale eviction.
- Python ctypes wrapper for the entity table.
- ABI v8 double-buffered snapshot handoff.
- Combined ingest-and-publish helper for high-FFI-cost hosts.
- Header-only C++17 RAII wrapper over the C ABI.
- Move-only C++ wrappers for scanner, latest-state table, and snapshot buffer.
- Scoped C++ snapshot views that release double-buffer read slots automatically.
- C++ RAII example and tests, including a no-exceptions compile target.

## Historical Next 1: engine adapters and thread-handoff demos

The C++ RAII wrapper now covers the native handoff primitive. Next engine work should add complete host integrations:

- Unreal module wrapper around `fastdis::Scanner`, `fastdis::EntityTable`, and `fastdis::SnapshotBuffer`,
- Godot GDExtension wrapper around acquired `fastdis::ScopedSnapshotView` records,
- network/update thread example that publishes snapshots while render/game thread consumes them,
- documented handling for `FASTDIS_ERR_BUSY` back-pressure.

## Historical Next 2: more subscribed Entity State filters

The scanner can now store large entity-ID sets. Next useful filters are numeric
ranges and low-cardinality fields that engines often route on:

- force ID is already implemented with a byte filter.
- exercise ID is already implemented with a byte filter.
- entity kind/domain/category filters.
- country/category allowlists for synthetic traffic shaping.

## Historical Next 3: transport helpers

Keep packet ingestion outside the core ABI, but provide examples for:

- UDP socket receive loops.
- lock-free or ring-buffer handoff into Unreal/Godot update ticks.
- packet burst scanning from pcap-like buffers.

## Historical Next 4: hot PDU body decoders

After Entity State, useful next decoders are:

- Fire PDU
- Detonation PDU
- Collision PDU
- Entity State Update PDU
- Electromagnetic Emission PDU prefix

## Historical Next 5: packaging and release artifacts

- Add `cibuildwheel` for Python wheels.
- Add native release artifacts for engine users.
- Add CMake package config/version files.
- Add Windows CI for DLL exports.

## Historical Next 6: benchmark corpus and profiling

The synthetic benchmark harness exists. Next benchmark work should add:

- replay from captured packet bursts or pcap-like fixtures.
- configurable entity-ID allowlist sizes: 1, 32, 1k, 10k, 100k.
- mixed PDU-family distributions that look like real exercises.
- per-platform CI benchmark smoke tests.
- optional perf/VTune/Tracy markers around parse, filter, and callback stages.


## v0.11.0: Engine adapter scaffolding

Implemented:

- Header-only `fastdis_frames.hpp` for ECEF -> local ENU -> Unreal/Godot mappings.
- Unreal Runtime plugin scaffold with `UFastDisWorldSubsystem`.
- Godot GDExtension scaffold with `FastDisWorld` node.
- Position-first engine transform policy with orientation opt-in.

Next:

- Validate orientation against known DIS traffic/reference viewer.
- Add native UDP receiver examples for Unreal and Godot.
- Add interpolation/extrapolation policies for render smoothing.
- Add engine-specific stale/removal callbacks.
