# Double-buffered entity snapshots

ABI v8 adds `fastdis_entity_snapshot_buffer_t`, a reusable native handoff object
for publishing snapshots from a latest-state entity table without allocating or
calling back once per entity.

The intended engine loop is:

```text
network thread / update phase
  -> ingest packet burst into fastdis_entity_table_t
  -> publish changed snapshots into inactive snapshot-buffer slot
  -> swap inactive slot to latest read slot

engine / render phase
  -> acquire latest view
  -> apply transform updates
  -> release view
```

The snapshot buffer owns two fixed-capacity arrays. A publish operation writes to
the inactive slot and swaps it to become the current read view. If the slot that
would be overwritten is still acquired by a reader, publish returns
`FASTDIS_ERR_BUSY` instead of allocating, blocking, or overwriting data that an
engine thread may still be consuming.

## C ABI

```c
fastdis_entity_snapshot_buffer_t *buffer =
    fastdis_entity_snapshot_buffer_create(4096);

fastdis_entity_table_update_stats_t stats;
fastdis_entity_snapshot_view_t view;

fastdis_entity_table_update_stats_init(&stats);
fastdis_entity_table_ingest_packets_publish_changed(
    table,
    scanner,
    packets,
    packet_count,
    1,      /* advance table tick */
    1,      /* clear table change flags after publish */
    buffer,
    &stats,
    &view);
```

`view.snapshots` is borrowed storage owned by `buffer`. The returned view is valid
until the next publish. For a stable handoff across threads, acquire and release:

```c
fastdis_entity_snapshot_view_t read_view;
fastdis_entity_snapshot_buffer_acquire_latest(buffer, &read_view);

for (size_t i = 0; i < read_view.count; ++i) {
    const fastdis_entity_snapshot_t *snapshot = &read_view.snapshots[i];
    /* push transform to engine actor table */
}

fastdis_entity_snapshot_buffer_release(buffer, &read_view);
```

## Publish variants

```c
fastdis_entity_snapshot_buffer_publish_all(buffer, table, &view);
fastdis_entity_snapshot_buffer_publish_changed(buffer, table, 1, &view);
fastdis_entity_snapshot_buffer_publish_stale(buffer, table, 120, &view);
fastdis_entity_snapshot_buffer_publish_evict_stale(buffer, table, 120, &view);
```

The combined ingest/publish helper removes one FFI call for Python, C#, and other
bindings:

```c
fastdis_entity_table_ingest_packets_publish_changed(
    table, scanner, packets, packet_count,
    1, 1, buffer, &stats, &view);
```

## Python ctypes wrapper

```python
lib = native.load_native("./build/libfastdis.so")
scanner = lib.create_scanner().use_entity_transform_profile()
table = lib.create_entity_table(reserve=4096)
snapshots = lib.create_snapshot_buffer(4096)

view, stats = snapshots.ingest_and_publish_changed(
    table,
    scanner,
    packets,
    return_stats=True,
)

with snapshots.acquire_latest() as read:
    for snapshot in read.snapshots:
        print(snapshot.transform.entity_id, snapshot.transform.location)
```

The Python wrapper copies native snapshots into Python tuples when returning
values. Engine integrations should prefer the C ABI view directly so the engine
can consume native POD memory without Python value conversion.

## Threading notes

`fastdis_entity_snapshot_buffer_t` protects its own slot metadata with a mutex,
but `fastdis_entity_table_t` is still a mutable table object and should be used
from one producer/update thread or protected by the host engine. The buffer is a
handoff mechanism, not a full concurrent ECS.

The double buffer is deliberately strict: if a reader lags by more than one
publish interval and both slots are pinned, the producer sees `FASTDIS_ERR_BUSY`.
That makes back-pressure visible and avoids surprise allocations in the frame hot
path.
