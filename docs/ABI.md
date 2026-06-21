# fastdis C ABI

The native core is implemented in C++ but exposes a stable C ABI through:

```text
include/fastdis/fastdis.h
```

C++ users can also include the header-only wrapper:

```text
include/fastdis/fastdis.hpp
```

`fastdis.hpp` does not add exported C++ symbols; it compiles into the consumer and calls the same C ABI functions.

The ABI is designed for hosts that cannot safely consume C++ classes across a
DLL/shared-object boundary: Unreal, Godot, Unity native plugins, Python ctypes,
C#, Rust, Go, and plain C.

## ABI rules

- Exported symbols are `extern "C"`.
- Public structures are plain-old-data structs.
- No STL containers cross the boundary.
- No C++ exceptions cross the boundary.
- Callers own packet memory.
- `fastdis` never stores packet pointers after the call returns.
- Callbacks return non-zero to stop a scan early.

## ABI change checklist

Every C ABI change must pass this checklist before merge:

- C structs remain POD.
- No STL types cross the C ABI.
- No C++ exceptions cross the C ABI.
- Ownership is explicit and unambiguous.
- Every `create` has a matching `destroy`.
- Every `acquire` has a matching `release`.
- Every borrowed pointer has a documented lifetime.
- Functions tolerate null pointers where documented.
- All status codes returned by new functions are documented.
- Packet memory remains caller-owned.
- Struct fields are only appended, never reordered or removed.
- Struct appends require an ABI version bump unless the struct is opaque.
- New public symbols are visible in shared-library exports.
- C tests cover lifecycle and invalid-input behavior.
- C++ RAII wrappers remain header-only.

Run the export checker after building the shared library:

```bash
python tools/check_exports.py build/libfastdis.dylib
python tools/check_exports.py build/libfastdis.so
python tools/check_exports.py build/Release/fastdis.dll
```

To refresh the bundled Alpha 2 export manifests and summary report from the
current host build:

```bash
python tools/run_export_report.py
```

That command writes:

- `verification_reports/alpha2_sample/expected_exports.txt`
- `verification_reports/alpha2_sample/exported_symbols_<host>.txt`
- `verification_reports/alpha2_sample/export_check_report.json`
- `verification_reports/alpha2_sample/export_check_report.md`

## Shared library names

Typical outputs are:

| Platform | Shared library |
|---|---|
| Windows | `fastdis.dll` plus import library such as `fastdis.lib` |
| Linux | `libfastdis.so` |
| macOS | `libfastdis.dylib` |

## Header-only dispatch path

The first hot path parses only the 12-byte DIS PDU header, applies filters, and
only then invokes a callback. This keeps packet rejection cheap.

```c
fastdis_scan_config_t cfg;
fastdis_scan_config_init(&cfg);

uint8_t versions[] = {6, 7};
fastdis_scan_config_filter_only(&cfg, FASTDIS_FILTER_VERSION, versions, 2);

uint8_t pdu_types[] = {FASTDIS_ENTITY_STATE_PDU_TYPE};
fastdis_scan_config_filter_only(&cfg, FASTDIS_FILTER_PDU_TYPE, pdu_types, 1);

fastdis_scan_config_set_sample(&cfg, 10, 0); /* callback every 10th accepted PDU */
```

## DIS 6 vs DIS 7 header handling

The first 10 bytes are common for the current header parser. Byte 10/11 differ:

```text
DIS 7+: byte 10 = PDU status, byte 11 = padding
DIS 6 : byte 10..11 = 16-bit padding, status is reported as -1
```

The exported `fastdis_header_t` reports both cases with the same struct:

```c
if (header.version >= 7) {
    /* header.status is byte 10 */
} else {
    /* header.status == -1, header.padding is 16-bit padding */
}
```

Prefer the source-level helpers in C/C++:

```c
if (fastdis_header_has_pdu_status(&header)) {
    uint8_t status = fastdis_header_pdu_status(&header);
    uint8_t padding = fastdis_header_padding_octet(&header);
} else {
    uint16_t padding = fastdis_header_legacy_padding(&header);
}
```

Python named headers expose matching properties: `has_pdu_status`,
`pdu_status`, `padding_octet`, and `legacy_padding`. See
`docs/DIS_HEADER_COMPATIBILITY.md` for the Open-DIS cross-check notes.

## Batch API

For engines or network bridges that already receive packet batches:

```c
fastdis_packet_view_t packets[N];
fastdis_scan_stats_t stats;
fastdis_scan_stats_init(&stats);

fastdis_status_t rc = fastdis_scan_packets(
    packets,
    N,
    &cfg,
    on_packet,
    callback_state,
    &stats);
```

`stats.accepted` counts packets that matched filters before downsampling.
`stats.emitted` counts callbacks after downsampling.


### ABI v7 filter helpers

ABI v7 adds generic filter helpers so engine bindings do not need to write into
`fastdis_scan_config_t` fields directly:

```c
uint8_t force_ids[] = {1, 2};
fastdis_scan_config_filter_only(&cfg, FASTDIS_FILTER_ENTITY_FORCE_ID, force_ids, 2);
fastdis_scan_config_set_entity_state_fields(&cfg, FASTDIS_ES_FIELD_POSE);
fastdis_scan_config_set_sample(&cfg, 100, 0);
```

Reusable scanners can update filters in place. Prefer `fastdis_scanner_filter_only`
when setting a complete allow-list in one call:

```c
uint8_t pdu_types[] = {FASTDIS_ENTITY_STATE_PDU_TYPE};
fastdis_scanner_filter_only(scanner, FASTDIS_FILTER_PDU_TYPE, pdu_types, 1);
fastdis_scanner_set_sample(scanner, 100, 0);
fastdis_scanner_set_entity_state_fields(scanner, FASTDIS_ES_FIELD_POSE);
```

The lower-level clear/allow calls still exist for bindings that want to build a
filter incrementally:

```c
fastdis_scanner_filter_clear(scanner, FASTDIS_FILTER_PDU_TYPE);
fastdis_scanner_filter_allow(scanner, FASTDIS_FILTER_PDU_TYPE, FASTDIS_ENTITY_STATE_PDU_TYPE);
```

For bulk entity-ID filters, use one call instead of many single inserts:

```c
fastdis_entity_id_t ids[] = {{100, 1, 42}, {100, 1, 43}};
fastdis_scanner_set_entity_ids(scanner, FASTDIS_ENTITY_ID_FILTER_ALLOW, ids, 2);
```

## Versioning

Use:

```c
if (fastdis_abi_version() != FASTDIS_ABI_VERSION) {
    /* reject unsupported binary */
}
```

The ABI version changes only when binary-incompatible changes are made to the C
interface.

## ABI v2: Entity State PDU fixed-prefix parser

ABI v2 adds `fastdis_entity_state_prefix_t` and the following functions:

```c
fastdis_parse_entity_state_prefix(...);
fastdis_scan_entity_state_packet(...);
fastdis_scan_entity_state_packets(...);
```

The parser is intentionally fixed-prefix only. It parses the first 144 bytes of
an Entity State PDU, which includes the fixed header and all standard ESPDU
fields through capabilities. It does not allocate or parse variable parameters.

`fastdis_scan_config_t` also gained `entity_force_ids` at the end of the struct.
This filter is ignored by the generic header scanner and applied by the
entity-state scanner after decoding the fixed prefix.

The engine integration rule stays the same: own packet memory on the engine
side, pass `const uint8_t*` + size into fastdis, and treat callback pointers as
borrowed for the duration of the callback only.

## ABI v7: field subscriptions and opaque scanner contexts

ABI v7 adds two performance-oriented pieces:

1. `fastdis_parse_entity_state_fields(...)` and `fastdis_scan_config_t.entity_state_fields`.
2. `fastdis_scanner_t`, an opaque native scanner/context object.

### Entity State field mask

The field mask lets callers decode only the fixed-prefix fields they need:

```c
cfg.entity_state_fields = FASTDIS_ES_FIELD_LOCATION | FASTDIS_ES_FIELD_ORIENTATION;
```

Available masks include:

```c
FASTDIS_ES_FIELD_ROUTING     /* header + entity ID + force ID */
FASTDIS_ES_FIELD_POSE        /* entity ID + force ID + location + orientation */
FASTDIS_ES_FIELD_KINEMATICS  /* linear velocity + dead-reckoning vectors */
FASTDIS_ES_FIELD_ALL         /* every fixed-prefix field */
```

Callbacks receive the same `fastdis_entity_state_prefix_t` POD struct either way.
Fields that were not requested are zero-filled. The struct's `fields_present`
mask tells callers which fields are valid.

The scanner always fills `FASTDIS_ES_FIELD_HEADER` and `FASTDIS_ES_FIELD_FORCE_ID`
because header and force ID are used for routing and filtering. If an entity-ID
allow/block filter is active, the scanner also decodes `FASTDIS_ES_FIELD_ENTITY_ID`
even if the callback did not explicitly request it.

### Opaque scanner context

`fastdis_scanner_t` is an owning native handle:

```c
fastdis_scan_config_t cfg;
fastdis_scan_config_init(&cfg);
cfg.entity_state_fields = FASTDIS_ES_FIELD_POSE;

fastdis_scanner_t *scanner = fastdis_scanner_create(&cfg);
fastdis_scanner_destroy(scanner);
```

The handle copies the scan config and can store native-side entity-ID sets:

```c
fastdis_scanner_add_entity_id(scanner, 100, 1, 42);
fastdis_scanner_set_entity_id_filter_mode(scanner, FASTDIS_ENTITY_ID_FILTER_ALLOW);
```

Modes are:

```c
FASTDIS_ENTITY_ID_FILTER_DISABLED
FASTDIS_ENTITY_ID_FILTER_ALLOW
FASTDIS_ENTITY_ID_FILTER_BLOCK
```

This is intended for engines where rebuilding filters every frame would be
wasteful. The context does not store packet pointers and does not take ownership
of packet memory.

### Threading note

A scanner handle is not internally synchronized. Use one scanner per network
thread, or protect a shared scanner with the host's lock if filters/config can be
mutated while another thread scans.

## ABI v7 callback-free batch outputs

ABI v7 adds callback-free output buffers for the engine hot path. The caller owns
all output memory; `fastdis` fills as many records as fit and reports overflow in
`dropped` rather than allocating.

```c
fastdis_entity_state_prefix_t entities[4096];
fastdis_entity_state_batch_t batch = {entities, 4096, 0, 0};
fastdis_scan_stats_t stats;
fastdis_scan_stats_init(&stats);

fastdis_scan_entity_state_to_batch(packets, packet_count, &cfg, &batch, &stats);
```

`stats.emitted` counts every packet that survived filters and downsampling.
`batch.count` is how many records were actually stored. `batch.dropped` is the
number that would have been stored if the caller-provided capacity had been
larger.

For game engines, prefer the compact transform output when you only need actor
updates:

```c
fastdis_entity_transform_t transforms[4096];
fastdis_entity_transform_batch_t transform_batch = {transforms, 4096, 0, 0};

fastdis_scan_entity_transforms_to_batch(
    packets,
    packet_count,
    &cfg,
    &transform_batch,
    &stats);
```

The transform record contains entity ID, force ID, exercise/version/timestamp,
appearance, world location, orientation, and linear velocity.

## ABI v7 profiles

Profiles configure common scan shapes without exposing config layout details to
engine bindings:

```c
fastdis_scan_config_use_profile(&cfg, FASTDIS_PROFILE_ENTITY_TRANSFORM);
fastdis_scanner_use_profile(scanner, FASTDIS_PROFILE_ENTITY_STATE_POSE);
```

Available profiles:

```c
FASTDIS_PROFILE_HEADER_COUNTING
FASTDIS_PROFILE_ENTITY_STATE_ROUTING
FASTDIS_PROFILE_ENTITY_STATE_POSE
FASTDIS_PROFILE_ENTITY_STATE_FULL
FASTDIS_PROFILE_ENTITY_TRANSFORM
```

## ABI v7: native latest-state entity table

ABI v7 introduces an opaque latest-state cache:

```c
typedef struct fastdis_entity_table_s fastdis_entity_table_t;
```

The table stores one `fastdis_entity_transform_t` per Entity ID and exposes
caller-owned snapshot output buffers:

```c
fastdis_entity_table_create(...)
fastdis_entity_table_destroy(...)
fastdis_entity_table_ingest_packets(...)
fastdis_entity_table_snapshot_all(...)
fastdis_entity_table_snapshot_changed(...)
fastdis_entity_table_snapshot_stale(...)
fastdis_entity_table_evict_stale(...)
```

The ABI remains plain C. The implementation currently uses C++ internally, but
no C++ classes, STL containers, or exceptions cross the shared-library boundary.

Typical engine pattern:

```c
fastdis_entity_table_ingest_packets(table, scanner, packets, count, 1, &stats);
fastdis_entity_table_snapshot_changed(table, &changed_batch, 1);
fastdis_entity_table_snapshot_stale(table, stale_after_ticks, &stale_batch);
```

`advance_tick` is caller-defined. A common convention is one tick per game frame
or one tick per receive burst. Stale detection is based on table ticks, not wall
clock time.


## ABI v8: double-buffered snapshot handoff

ABI v8 adds `fastdis_entity_snapshot_buffer_t`, an opaque native object that owns
two reusable snapshot arrays. Publish functions write table snapshots into the
inactive slot, swap it to the read slot, and return a borrowed
`fastdis_entity_snapshot_view_t`.

New functions include:

```c
fastdis_entity_snapshot_buffer_create
fastdis_entity_snapshot_buffer_create_ex
fastdis_entity_snapshot_buffer_destroy
fastdis_entity_snapshot_buffer_slot_count
fastdis_entity_snapshot_buffer_publish_all
fastdis_entity_snapshot_buffer_publish_changed
fastdis_entity_snapshot_buffer_publish_stale
fastdis_entity_snapshot_buffer_publish_evict_stale
fastdis_entity_snapshot_buffer_acquire_latest
fastdis_entity_snapshot_buffer_release
fastdis_entity_snapshot_buffer_copy_latest
fastdis_entity_snapshot_buffer_stats_init
fastdis_entity_snapshot_buffer_get_stats
fastdis_entity_snapshot_buffer_reset_stats
fastdis_entity_table_ingest_packets_publish_changed
```

`fastdis_entity_table_ingest_packets_publish_changed()` is the preferred FFI
hot path for Python/C#/engine bindings because it updates the latest-state table
and publishes changed snapshots through one ABI call. If an acquired read view
pins both backing slots, publish functions return `FASTDIS_ERR_BUSY`.

`fastdis_entity_snapshot_buffer_stats_t` exposes publish pressure without
changing existing function signatures. `publish_busy` counts slot-pinning
back-pressure; `dropped_snapshots` counts snapshot records skipped because the
fixed-capacity output slot was too small.

`fastdis_entity_snapshot_buffer_create(capacity)` is shorthand for
`fastdis_entity_snapshot_buffer_create_ex(capacity, 2)`. Slot counts below two
are rejected by returning `NULL`. Existing two-slot behavior remains strict
double-buffering; three or more slots allow delayed engine readers to pin older
views without immediately blocking the next publish.

## ABI v9: shared dead-reckoning evaluator

ABI v9 appends DIS Entity State dead-reckoning metadata to
`fastdis_entity_transform_t`:

```c
uint8_t dead_reckoning_algorithm;
uint8_t dead_reckoning_parameters[15];
fastdis_vec3f_t dead_reckoning_linear_acceleration;
fastdis_vec3f_t dead_reckoning_angular_velocity;
```

The native library now exposes one deterministic dead-reckoning evaluator for
C, C++, Python, and engine bindings:

```c
fastdis_dead_reckoning_algorithm_name
fastdis_dead_reckoning_algorithm_known
fastdis_extrapolate_entity_transform_dead_reckoning
fastdis_extrapolate_entity_snapshot_dead_reckoning
fastdis_entity_snapshot_buffer_copy_latest_dead_reckoned
```

The intent is parity, not duplicated engine math. Unreal, Godot, Unity, Python,
and Lattice-facing code should preserve DR metadata and call the shared native
evaluator when extrapolating buffered or stale entity state.

## C++ RAII wrapper

`include/fastdis/fastdis.hpp` is a header-only C++17 wrapper over this C ABI.
It does not expose C++ symbols from the shared library and does not change
`FASTDIS_ABI_VERSION`. The wrapper owns opaque C handles with move-only RAII
classes and provides `ScopedSnapshotView` for automatic double-buffer release.

Use `fastdis.h` for ABI-stable FFI and `fastdis.hpp` for first-class C++ call
sites. See `docs/CPP_RAII.md`.
