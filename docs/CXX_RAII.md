# C++ RAII wrapper

`include/fastdis/fastdis.hpp` is a header-only C++17 convenience layer over the
stable C ABI in `fastdis.h`.

The shared-library/DLL boundary is still plain C. The C++ header does not export
C++ classes from the library and does not require C++ callers to link against a
C++ ABI that differs across compilers. It simply wraps opaque C handles with
move-only RAII objects and safer lifetime patterns.

## What it wraps

The main C++ types are:

```cpp
fastdis::ScanConfig
fastdis::Scanner
fastdis::PacketViews
fastdis::EntityStateBatch
fastdis::TransformBatch
fastdis::EntityTable
fastdis::SnapshotBatch
fastdis::SnapshotBuffer
fastdis::SnapshotView
fastdis::ScopedSnapshotView
```

The POD structs are still the C ABI structs, aliased for convenience:

```cpp
fastdis::Header
fastdis::EntityId
fastdis::EntityTransform
fastdis::EntitySnapshot
fastdis::ScanStats
fastdis::EntityTableUpdateStats
```

## Exceptions and no-exceptions builds

By default, convenience methods throw `fastdis::Error` when a native call returns
an error. Every major operation also has a `try_*` variant that returns the raw
`fastdis_status_t` instead.

For Unreal-style or engine builds where exceptions are disabled, define:

```cpp
#define FASTDIS_CPP_NO_EXCEPTIONS
#include <fastdis/fastdis.hpp>
```

In that mode, the convenience checks assert on unexpected errors; use `try_*`
methods in production hot paths when you want explicit error handling.

The CMake test suite compiles the same RAII test twice:

```text
fastdis_cpp_raii_tests
fastdis_cpp_raii_noexcept_tests  // FASTDIS_CPP_NO_EXCEPTIONS + -fno-exceptions on GCC/Clang
```

## Basic transform batch scan

```cpp
#include <fastdis/fastdis.hpp>

fastdis::ScanConfig cfg = fastdis::ScanConfig::entity_transform();
cfg.only_versions({6, 7})
   .only_pdu_types({FASTDIS_ENTITY_STATE_PDU_TYPE})
   .only_protocol_families({FASTDIS_ENTITY_INFORMATION_FAMILY})
   .only_entity_force_ids({1, 2});

fastdis::Scanner scanner(cfg);

fastdis::PacketViews packets;
packets.add(packet0.data(), packet0.size())
       .add(packet1.data(), packet1.size());

fastdis::TransformBatch transforms(4096);
fastdis::ScanStats stats = scanner.scan_transforms(packets, transforms);

for (const fastdis::EntityTransform& transform : transforms) {
    // Update an engine-side transform table.
}
```

## Entity-ID allowlist

```cpp
scanner.allow_entity_ids({
    fastdis::make_entity_id(100, 1, 42),
    fastdis::make_entity_id(100, 1, 43),
});

scanner.entity_id_filter_mode(fastdis::EntityIdFilterMode::Allow);
```

Use the corresponding `try_*` calls when you want status returns instead of
exceptions/asserts:

```cpp
fastdis::Status status = scanner.try_scan_transforms(
    packets.data(), packets.size(), transforms, &stats);

if (status != FASTDIS_OK) {
    // status_string(status) is safe for logging.
}
```

## Latest-state table + double-buffer handoff

This is the preferred C++/engine shape:

```cpp
fastdis::ScanConfig cfg = fastdis::ScanConfig::entity_transform();
fastdis::Scanner scanner(cfg);
fastdis::EntityTable table(4096);
fastdis::SnapshotBuffer snapshots(4096);

fastdis::EntityTableUpdateStats stats{};
fastdis_entity_table_update_stats_init(&stats);

fastdis::SnapshotView published = snapshots.ingest_and_publish_changed(
    table,
    scanner,
    packets,
    true,   // advance entity-table tick once for this burst/frame
    true,   // clear emitted change flags after publishing
    &stats);

{
    fastdis::ScopedSnapshotView view = snapshots.acquire_latest();
    for (const fastdis::EntitySnapshot& snapshot : view) {
        const fastdis::EntityTransform& transform = snapshot.transform;
        // Apply transform to the engine actor/node/entity.
    }
} // view releases the pinned snapshot slot here
```

`ScopedSnapshotView` is move-only. It automatically calls
`fastdis_entity_snapshot_buffer_release()` in its destructor.

## Back-pressure behavior

The snapshot buffer owns two internal slots. If a reader pins one slot and the
producer publishes into the other, the next publish will return `FASTDIS_ERR_BUSY`
until a pinned view is released. The wrapper does not hide this behavior.

```cpp
fastdis::ScopedSnapshotView held = snapshots.acquire_latest();

fastdis::SnapshotView tmp;
fastdis::Status s1 = snapshots.try_publish_all(table, &tmp); // likely OK
fastdis::Status s2 = snapshots.try_publish_all(table, &tmp); // FASTDIS_ERR_BUSY if both slots are pinned
```

For engine timing tolerance, use the config builder with three slots:

```cpp
fastdis::SnapshotBuffer snapshots =
    fastdis::SnapshotBufferConfig()
        .capacity(4096)
        .slots(3)
        .build();
```

Alpha 2 exposes the pressure signal directly:

```cpp
fastdis::SnapshotBufferStats pressure = snapshots.stats();
snapshots.reset_stats();
```

`pressure.publish_busy` counts pinned-slot back-pressure. `pressure.dropped_snapshots`
counts records skipped because the fixed-capacity output slot was too small.

This is intentional. It prevents the producer from overwriting a view still being
read by the engine/render side.

## Example

The example below reads the dependency-free `.fastdispkt` replay format and uses
the RAII wrapper all the way through scanner, table, snapshot buffer, and scoped
view acquisition:

```bash
python tools/make_replay.py benchmark_results/synthetic.fastdispkt --packets 100000
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release
./build/fastdis_raii_snapshot_buffer_cpp benchmark_results/synthetic.fastdispkt
```

Source:

```text
examples/cpp/raii_snapshot_buffer.cpp
```

## ABI rule

Do not pass C++ wrapper objects across DLL/shared-library boundaries. Pass the C
ABI structs and opaque handles from `fastdis.h`. The wrapper is for C++ callers
on their side of the boundary.
