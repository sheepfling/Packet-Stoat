# C++ RAII wrappers

`include/fastdis/fastdis.hpp` is a header-only C++17 convenience layer over the
stable `fastdis.h` C ABI. It does not add a new binary ABI: your DLL/shared
object boundary remains plain C, while C++ callers get move-only ownership,
range-friendly batches, and scoped snapshot-buffer acquisition.

## Design goals

- Keep `libfastdis.so` / `fastdis.dll` exported as a plain C ABI.
- Make C++ consumers first-class without exposing STL containers across the DLL boundary.
- Destroy opaque native handles automatically.
- Release acquired double-buffer snapshot views automatically.
- Offer both throwing convenience methods and `try_*` no-throw methods.

By default, convenience methods call `detail::check` and throw `fastdis::Error`
on failure. Define `FASTDIS_CPP_NO_EXCEPTIONS` before including the header if
your host disables exceptions, as many game-engine builds do. In that mode, use
the `try_*` methods in production code and reserve convenience methods for cases
where failure is a programmer error.

```cpp
#define FASTDIS_CPP_NO_EXCEPTIONS
#include <fastdis/fastdis.hpp>
```

## Basic scanner setup

```cpp
fastdis::ScanConfig cfg = fastdis::ScanConfig::entity_transform();
cfg.only_versions({6, 7})
   .only_pdu_types({FASTDIS_ENTITY_STATE_PDU_TYPE})
   .only_protocol_families({FASTDIS_ENTITY_INFORMATION_FAMILY})
   .sample(1);

fastdis::Scanner scanner(cfg);
scanner.allow_entity_ids({
    fastdis::make_entity_id(100, 1, 42),
    fastdis::make_entity_id(100, 1, 43),
});
```

No C++ object is passed across the shared-library boundary. `Scanner` owns a
`fastdis_scanner_t*` and destroys it in its destructor.

## Packet views

Use `PacketViews` to build a reusable array of non-owning packet pointers:

```cpp
fastdis::PacketViews packets;
packets.reserve(1024);
packets.add(packet_bytes.data(), packet_bytes.size());
```

The packet bytes must remain alive while the scan runs. `PacketViews` owns only
the pointer/size/user triples, not the payloads.

## Callback-free transform batches

```cpp
fastdis::TransformBatch transforms(4096);
fastdis::ScanStats stats = scanner.scan_transforms(packets, transforms);

for (const auto& transform : transforms) {
    // Update native engine-side entity data.
}
```

For no-throw code:

```cpp
fastdis::TransformBatch transforms(4096);
fastdis::ScanStats stats{};
fastdis_scan_stats_init(&stats);

fastdis::Status rc = scanner.try_scan_transforms(
    packets.data(), packets.size(), transforms, &stats);
if (rc != FASTDIS_OK) {
    // fastdis::status_string(rc)
}
```

## Latest-state table

`EntityTable` owns a `fastdis_entity_table_t*` and stores the latest transform
per DIS Entity ID:

```cpp
fastdis::EntityTable table(4096);
fastdis::EntityTableUpdateStats stats = table.ingest(scanner, packets, true);

fastdis::SnapshotBatch changed = table.snapshot_changed(4096, true);
for (const auto& snapshot : changed) {
    // snapshot.transform is the latest compact transform for that entity.
}
```

## Double-buffer snapshot handoff

`SnapshotBuffer` owns a `fastdis_entity_snapshot_buffer_t*`. `ScopedSnapshotView`
pins the latest published read slot and releases it automatically at scope exit:

```cpp
fastdis::SnapshotBuffer snapshots(4096);
fastdis::SnapshotBuffer engine_snapshots =
    fastdis::SnapshotBufferConfig()
        .capacity(4096)
        .slots(3)
        .build();

fastdis::EntityTableUpdateStats stats{};
fastdis_entity_table_update_stats_init(&stats);

fastdis::SnapshotView published;
fastdis::Status rc = snapshots.try_ingest_and_publish_changed(
    table,
    scanner,
    packets.data(),
    packets.size(),
    true,   // advance entity-table tick once for this burst
    true,   // clear emitted change flags
    &stats,
    &published);

if (rc == FASTDIS_OK) {
    fastdis::ScopedSnapshotView view;
    rc = snapshots.try_acquire_latest(&view);
    if (rc == FASTDIS_OK) {
        for (const auto& snapshot : view) {
            // Render/update thread consumes a stable borrowed view.
        }
        // view releases automatically here.
    }
}
```

Alpha 2 exposes publish-pressure counters through the same wrapper:

```cpp
fastdis::SnapshotBufferStats pressure = snapshots.stats();
if (pressure.publish_busy != 0) {
    // The producer hit a pinned write slot. Drop, retry, or slow the producer.
}
snapshots.reset_stats();
```

If both internal slots are pinned, publishing returns `FASTDIS_ERR_BUSY`. The
RAII layer preserves that native back-pressure behavior rather than allocating or
blocking behind your back.

## Move-only semantics

The owning types are move-only:

```cpp
fastdis::Scanner scanner(cfg);
fastdis::Scanner moved = std::move(scanner);
```

Moved-from handles become empty. This mirrors `std::unique_ptr` and prevents
double-destroying native resources.

## Included example

See:

```text
examples/cpp/raii_snapshot_buffer.cpp
```

It reads `.fastdispkt` replay files, ingests packets into an `EntityTable`,
publishes changed snapshots through a `SnapshotBuffer`, and acquires a scoped
view that would map directly to an Unreal/Godot actor-update loop.
