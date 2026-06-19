# Native latest-state entity table

ABI v7 adds `fastdis_entity_table_t`, an opaque C ABI object that stores the
latest compact `fastdis_entity_transform_t` per DIS Entity ID.

The table is designed for game engines and simulation visualizers where the hot
loop should be:

```text
packet burst -> native filters -> compact transform decode -> latest-state table
             -> changed/stale snapshots -> engine actor table
```

No Python objects, no C++ objects exposed across the ABI, and no per-packet
engine callback is required.

## Tick model

The table does not read wall-clock time. Instead it owns a monotonic `tick`.
Callers decide what a tick means. Common choices are:

- one network receive burst,
- one simulation frame,
- one Unreal/Godot update tick.

`fastdis_entity_table_ingest_packets(..., advance_tick=1, ...)` advances the
table tick once before applying that packet burst. `fastdis_entity_table_advance_tick`
can advance time even when no packets arrived.

## Change flags

Snapshots use these flags:

```c
FASTDIS_ENTITY_CHANGE_NEW
FASTDIS_ENTITY_CHANGE_UPDATED
FASTDIS_ENTITY_CHANGE_STALE
FASTDIS_ENTITY_CHANGE_REMOVED
FASTDIS_ENTITY_CHANGE_UNCHANGED
```

`fastdis_entity_table_snapshot_changed(table, &batch, clear_flags)` returns only
entities whose NEW/UPDATED flags are pending. When `clear_flags != 0`, emitted
records are marked clean. Records that do not fit in the caller-owned batch are
not cleared.

## Stale entities

`fastdis_entity_table_snapshot_stale(table, stale_after_ticks, &batch)` returns
entities where:

```text
table_tick - last_seen_tick >= stale_after_ticks
```

`fastdis_entity_table_evict_stale` returns the stale snapshots and removes all
stale entities from the table. If the output batch is undersized, the table still
evicts all stale entities and increments `batch.dropped` for snapshots that did
not fit.

## C example

```c
fastdis_scan_config_t cfg;
fastdis_scan_config_init(&cfg);
fastdis_scan_config_use_profile(&cfg, FASTDIS_PROFILE_ENTITY_TRANSFORM);

fastdis_scanner_t *scanner = fastdis_scanner_create(&cfg);
fastdis_entity_table_t *table = fastdis_entity_table_create(4096);

fastdis_entity_table_update_stats_t stats;
fastdis_entity_table_update_stats_init(&stats);

fastdis_entity_table_ingest_packets(table, scanner, packets, count, 1, &stats);

fastdis_entity_snapshot_t out[4096];
fastdis_entity_snapshot_batch_t batch = {out, 4096, 0, 0};
fastdis_entity_table_snapshot_changed(table, &batch, 1);
```

## Python example

```python
lib = native.load_native("./build/libfastdis.so")
scanner = lib.create_scanner().use_entity_transform_profile()
table = lib.create_entity_table(reserve=4096)

stats = table.ingest(scanner, packets, advance_tick=True)
changed = table.snapshot_changed(clear=True)
stale = table.snapshot_stale(120)
```

## Threading and handoff

The entity table itself is not internally synchronized. Treat it as owned by one
producer/update thread, or guard table calls with your own lock. ABI v8 adds
`fastdis_entity_snapshot_buffer_t` for lock-minimized handoff to an engine/render
thread: the producer publishes changed/stale/all snapshots into an inactive
buffer slot, the consumer acquires the latest stable view, and the buffer returns
`FASTDIS_ERR_BUSY` rather than allocating or overwriting a pinned slot. See
`docs/DOUBLE_BUFFER_SNAPSHOTS.md`.
