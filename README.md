# fastdis

`fastdis` is a callback-first DIS packet scanner. It is designed for high-rate
UDP pipelines where creating a deep Python object tree for every PDU is too
expensive.

The repo now has three host-facing layers:

1. **Portable engine ABI**: `libfastdis.so`, `libfastdis.dylib`, or
   `fastdis.dll`, built from C++ but exported through a stable C ABI in
   `include/fastdis/fastdis.h`.
2. **Header-only C++ RAII wrapper**: `include/fastdis/fastdis.hpp`, which wraps
   the C ABI with move-only handles, scoped snapshot views, fluent filters, and
   no-exceptions build support for engine modules.
3. **Python convenience API**: pure-Python fallback plus an optional CPython
   extension for fast in-process scanning.

The native ABI is the path intended for Unreal, Godot, Unity native plugins,
Python `ctypes`, Rust, C#, Go, and plain C/C++ hosts. C++ hosts should usually
include `fastdis.hpp` while still linking against the same C ABI shared library.

## Header-first design

The current fast path starts with the fixed 12-byte DIS PDU header:

```text
byte 0     protocol version
byte 1     exercise ID
byte 2     PDU type
byte 3     protocol family
bytes 4-7  timestamp, big-endian uint32
bytes 8-9  PDU length, big-endian uint16
byte 10    DIS 7+ PDU status, or high byte of DIS 6 padding
byte 11    DIS 7+ padding, or low byte of DIS 6 padding
```

For DIS 6 / pre-DIS7 packets, `status` is reported as `-1` and `padding` is the
16-bit padding field. For DIS 7+ packets, `status` is byte 10 and `padding` is
byte 11.

## Design goals

- **Filter early.** Drop packets by protocol version, PDU type, protocol family,
  or exercise ID before building objects.
- **Downsample early.** Keep only every Nth accepted packet before invoking
  Python or engine callbacks.
- **Stable engine boundary.** The shared library exports C structs/functions,
  not C++ classes.
- **No full PDU allocation in the hot path.** The scanner calls callbacks with
  fixed scalar fields and the original packet pointer, or fills caller-owned batch arrays with no per-packet callback.
- **Portable.** Pure-Python fallback, optional CPython extension, and a CMake
  native library for DLL/shared-object use.
- **Upgradeable.** The first native layer handles header parsing and dispatch.
  Hot PDU bodies can be added as specialized paths; Entity State prefix and compact transform output are implemented.

## Build the Python package

```bash
python -m pip install -e '.[dev]'
python -m pytest
```

If the CPython extension builds, `fastdis.HAS_C_ACCELERATOR` is `True`. If not,
the same API falls back to pure Python.

## Build the shared library / DLL

```bash
python tools/build_native.py --build-dir build
ctest --test-dir build --build-config Release --output-on-failure
```

Or call CMake directly:

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release
```

Expected outputs:

| Platform | Shared library |
|---|---|
| Windows | `fastdis.dll` plus an import library |
| Linux | `libfastdis.so` |
| macOS | `libfastdis.dylib` |

The public C header is:

```text
include/fastdis/fastdis.h
```

The header-only C++ RAII wrapper is:

```text
include/fastdis/fastdis.hpp
```

## Unreal Plugin Workflow

The repo now has one operator-facing Unreal entry point:

```bash
python tools/unreal_workflow.py doctor
python tools/unreal_workflow.py full --engine-version 5.8
```

Use `doctor` first on a new machine. It tells you what Unreal install was
found, what is missing, and what command to run next. Use `full` when you want
the normal end-to-end lane:

```text
doctor -> package plugin -> run orientation verification
```

The workflow is host-oriented rather than cross-compiling:

- macOS hosts build/stage a universal `arm64 + x86_64` `libfastdis.dylib`
- Windows hosts build/stage `fastdis.dll` plus `fastdis.lib`
- Linux hosts build/stage `libfastdis.so`

Useful commands:

```bash
python tools/unreal_workflow.py discover
python tools/unreal_workflow.py doctor --engine-version 5.8
python tools/unreal_workflow.py build --engine-version 5.8
python tools/unreal_workflow.py verify --engine-version 5.8
python tools/unreal_workflow.py matrix
```

Under the hood, the build lane will:

- detect the local Unreal Engine install or use `FASTDIS_UNREAL_ENGINE_DIR`,
- build the host-native `fastdis` shared library,
- stage headers and native binaries into `examples/unreal/FastDis/ThirdParty/fastdis`,
- package the plugin with Unreal `BuildPlugin`,
- create a local Unreal host project under the Unreal scratch root for IDE/editor use.

The default Unreal scratch root is outside the repo at a short no-space path so Unreal
packaging works even when the repo lives in an iCloud or other space-containing
directory:

```text
/tmp/fastdis_unreal/
```

If you want Rider to open the host project after setup:

```bash
python tools/unreal_workflow.py build --engine-version 5.8 --open-rider
```

If Rider is not on `PATH`, set `FASTDIS_RIDER` to the Rider launcher path.
If Unreal is not auto-detected, set `FASTDIS_UNREAL_ENGINE_DIR`.
If you keep multiple Unreal installs, prefer versioned variables such as
`FASTDIS_UNREAL_ENGINE_DIR_5_6`, `FASTDIS_UNREAL_ENGINE_DIR_5_7`, and
`FASTDIS_UNREAL_ENGINE_DIR_5_8`, then pass `--engine-version`.

To inspect detected installs and run the current matrix:

```bash
python tools/unreal_workflow.py discover
python tools/unreal_workflow.py matrix
```

Advanced users can still call the lower-level scripts directly:

```bash
python tools/list_unreal_installs.py
python tools/build_unreal_plugin.py --engine-version 5.8 --clean-package
python tools/run_unreal_orientation_verification.py --engine-version 5.8
python tools/run_unreal_matrix.py
```

See [docs/UNREAL_VERSION_MATRIX.md](/Users/rick/Library/Mobile%20Documents/com~apple~CloudDocs/GIT/fastdis/docs/UNREAL_VERSION_MATRIX.md) for the discovery rules, recorded quirks, and matrix report outputs.

## Benchmarks

Build in Release mode, then run the native benchmark for true DLL/shared-object
throughput:

```bash
./build/fastdis_native_bench --packets 1000000 --rounds 5 --format table
./build/fastdis_native_bench --packets 1000000 --rounds 5 --format csv > native.csv
```

Run the Python/ctypes benchmark when you want to measure wrapper overhead:

```bash
FASTDIS_LIBRARY=$PWD/build/libfastdis.so PYTHONPATH=src \
python benchmarks/bench_ctypes.py --packets 50000 --repeats 5 --format table
```

Or build and run both native and ctypes layers with one command:

```bash
python tools/run_benchmarks.py --native-packets 1000000 --native-rounds 5 \
  --ctypes-packets 50000 --ctypes-repeats 5 --format table
```

Generate a Markdown comparison report from JSON outputs:

```bash
python tools/run_benchmarks.py --format json --out-dir benchmark_results
python tools/summarize_benchmarks.py --native benchmark_results/native.json \
  --ctypes benchmark_results/ctypes.json --out benchmark_results/summary.md
```

See `docs/BENCHMARKING.md` for interpretation guidance and `docs/SAMPLE_BENCHMARK_REPORT.md` for one sample run generated in this development environment.

## C++ RAII quick use

C++ consumers can keep the DLL/shared-object boundary as C while using move-only
RAII wrappers for scanner/table/snapshot-buffer ownership:

```cpp
#include <fastdis/fastdis.hpp>

fastdis::ScanConfig cfg = fastdis::ScanConfig::entity_transform()
    .only_versions({6, 7})
    .only_pdu_types({FASTDIS_ENTITY_STATE_PDU_TYPE})
    .only_protocol_families({FASTDIS_ENTITY_INFORMATION_FAMILY});

fastdis::Scanner scanner(cfg);
fastdis::EntityTable table(4096);
fastdis::SnapshotBuffer snapshots(4096);

fastdis::PacketViews packets;
packets.add(packet_data, packet_size);

fastdis::EntityTableUpdateStats stats{};
fastdis_entity_table_update_stats_init(&stats);

fastdis::ScopedSnapshotView view = snapshots.ingest_publish_changed_and_acquire(
    table,
    scanner,
    packets,
    true,   // advance table tick
    true,   // clear emitted change flags
    &stats);

for (const fastdis::EntitySnapshot& snapshot : view) {
    // Update Unreal actor / Godot node / native component transform.
}
// view automatically releases the snapshot-buffer read slot here.
```

The C++ layer is header-only and does not add a C++ shared-library ABI. Define
`FASTDIS_CPP_NO_EXCEPTIONS` for no-exception engine builds and use the `try_*`
methods when you want explicit `fastdis_status_t` handling. See
`docs/CPP_RAII.md` and `examples/cpp/raii_snapshot_buffer.cpp`.

## C ABI quick use

```c
#include "fastdis/fastdis.h"

static int FASTDIS_CALL on_packet(const fastdis_header_t *h,
                                  const uint8_t *data,
                                  size_t size,
                                  void *packet_user,
                                  void *callback_user) {
    (void)data;
    (void)size;
    (void)packet_user;
    uint64_t *count = (uint64_t *)callback_user;
    *count += 1;
    return 0; /* non-zero stops the scan */
}

void scan_one_datagram(const uint8_t *packet, size_t packet_size) {
    fastdis_scan_config_t config;
    fastdis_scan_config_init(&config);

    uint8_t versions[] = {6, 7};
    fastdis_scan_config_filter_only(&config, FASTDIS_FILTER_VERSION, versions, 2);

    uint8_t pdu_types[] = {FASTDIS_ENTITY_STATE_PDU_TYPE};
    fastdis_scan_config_filter_only(&config, FASTDIS_FILTER_PDU_TYPE, pdu_types, 1);

    fastdis_scan_config_set_sample(&config, 100, 0); /* callback every 100th accepted PDU */

    uint64_t callback_count = 0;
    fastdis_scan_stats_t stats;
    fastdis_scan_stats_init(&stats);

    fastdis_status_t rc = fastdis_scan_packet(
        packet,
        packet_size,
        &config,
        on_packet,
        &callback_count,
        &stats);

    if (rc != FASTDIS_OK) {
        /* use fastdis_status_string(rc) */
    }
}
```

## DIS PDU catalog

Alpha 2 exposes generated DIS 6/7 PDU metadata across C, C++, and Python:

- C: `#include <fastdis/fastdis_pdu_catalog.h>`
- C++: `#include <fastdis/fastdis_pdu_catalog.hpp>`
- Python: `fastdis.PDU_CATALOG`, `fastdis.find_pdu(...)`,
  `fastdis.known_pdu_types(...)`

The catalog identifies known PDU types and whether fastdis currently implements
a body decoder. Today, only Entity State has a body decoder; other messages are
known for filtering/counting/cataloging and are intentionally marked
unsupported for body parsing. See `docs/LANGUAGE_COVERAGE.md` and
`docs/DIS_PDU_CATALOG.md`.


### Callback-free engine batch output

For Unreal/Godot-style update loops, prefer a reusable scanner plus a caller-owned
output array:

```c
fastdis_scan_config_t cfg;
fastdis_scan_config_init(&cfg);
fastdis_scan_config_use_profile(&cfg, FASTDIS_PROFILE_ENTITY_TRANSFORM);

fastdis_scanner_t *scanner = fastdis_scanner_create(&cfg);

fastdis_entity_transform_t transforms[4096];
fastdis_entity_transform_batch_t batch = {transforms, 4096, 0, 0};
fastdis_scan_stats_t stats;
fastdis_scan_stats_init(&stats);

fastdis_scanner_scan_entity_transforms_to_batch(
    scanner,
    packets,
    packet_count,
    &batch,
    &stats);

/* batch.count stored records; batch.dropped records did not fit. */
fastdis_scanner_destroy(scanner);
```

This keeps the hot path as:

```text
packet burst -> filter in native code -> decode selected fields -> fill POD array -> engine consumes array
```

No Python objects and no per-packet engine callback are required.

## Python quick use

```python
import fastdis


def on_packet(version, exercise_id, pdu_type, protocol_family, timestamp, length, status, packet):
    # `packet` is the original bytes/bytearray/memoryview object, not a copy.
    print(version, pdu_type, length, len(packet))

seen, accepted, emitted = fastdis.scan_many(
    packets,
    on_packet,
    versions={6, 7},
    pdu_types={1},       # Entity State PDU
    families=None,
    exercise_ids=None,
    sample_every=10,     # callback for every 10th accepted packet
    strict=False,        # reject bad packets instead of raising
)
```

The Python package can also load the shared library directly:

```python
import fastdis.native as native

lib = native.load_native("/path/to/libfastdis.so")
print(lib.abi_version(), lib.version_string())
print(lib.parse_header_tuple(packet))

scanner = lib.create_scanner().use_entity_transform_profile()
transforms, stats = scanner.scan_entity_transforms_to_batch(packets, return_stats=True)
print(stats, transforms[:3])
```

The `ctypes` path is for ABI validation and interoperability. For maximum Python
throughput, prefer `fastdis.scan_many`.

## API

### Python `parse_header_tuple(data, strict=True)`

Returns:

```python
(version, exercise_id, pdu_type, protocol_family, timestamp, length, status, padding)
```

or `None` if `strict=False` and the packet is malformed.

### Python `parse_header(data, strict=True)`

Returns a `Header` named tuple for ergonomic non-hot-path use.

### Python `scan_many(packets, callback, **filters)`

Callback signature:

```python
callback(version, exercise_id, pdu_type, protocol_family, timestamp, length, status, packet)
```

The packet is passed through without copying. `scan_many` returns:

```python
(seen, accepted, emitted)
```

where:

- `seen`: total iterable items scanned
- `accepted`: packets matching header and filters before downsampling
- `emitted`: callbacks that would be/were emitted after downsampling

Use `callback=None` to count matching/downsampled packets with no callback calls.

### C ABI `fastdis_parse_header(...)`

Parses the 12-byte DIS PDU header into `fastdis_header_t`.

### C ABI `fastdis_scan_packet(...)`

Scans one datagram, filters/downsamples, and optionally invokes a C callback.

### C ABI `fastdis_scan_packets(...)`

Scans a batch of packet views. Each packet view can carry an opaque `user`
pointer back to the callback.

## Engine integration

See:

```text
docs/ENGINE_INTEGRATION.md
examples/unreal/FastDisThirdParty.Build.cs.sample
examples/godot/fastdis.gdextension.sample
```

The intended engine shape is:

```text
network thread receives packet
  -> call fastdis_scan_packet / fastdis_scan_packets
  -> reject/filter/downsample in native code
  -> enqueue only retained events for game-thread consumption
```

## Next native layers

This prototype deliberately avoids full DIS body parsing in C++. The likely order
is:

1. Header decode, validation, filtering, and downsampling. **Implemented.**
2. Entity State fixed-prefix parsing. **Implemented.**
3. Entity State field subscriptions and entity-ID allow/block filters. **Implemented.**
4. Callback-free batch arrays and compact transform output. **Implemented.**
5. Latest-state entity table with changed/stale snapshots. **Implemented in ABI v7.**
6. Double-buffered snapshot handoff for engine update/render separation. **Implemented in ABI v8.**
7. Header-only C++ RAII wrapper for first-class C++ consumers. **Implemented in v0.10.0.**
8. Engine adapter scaffolding plus explicit DIS-to-engine frame helpers. **Expanded in v0.12.0-alpha2.**
8. Hot-body fast paths for Fire, Detonation, Collision, and other common PDUs.
9. Optional bridge to a full object parser only for retained packets.

## Repository status

This is a starter scaffold, not a complete DIS implementation. It is intended as
an upstreamable/performance-oriented base for experiments around Open-DIS-style
packet handling.

## Entity State fast path

Version `0.12.0-alpha2` uses ABI v8. The Entity State decoder targets the fixed
144-byte ESPDU prefix, supports field-subscription masks, and can emit compact
engine transform records. ABI v7 adds the native latest-state entity table, and
ABI v8 adds reusable snapshot handoff for update/render separation, including
N-slot buffer support.

Native ABI entry points:

```c
fastdis_parse_entity_state_prefix(...)
fastdis_parse_entity_state_fields(...)
fastdis_scan_entity_state_packet(...)
fastdis_scan_entity_state_packets(...)
fastdis_scanner_create(...)
fastdis_scanner_scan_entity_state_packets(...)
fastdis_scan_entity_state_to_batch(...)
fastdis_scan_entity_transforms_to_batch(...)
fastdis_scanner_scan_entity_state_to_batch(...)
fastdis_scanner_scan_entity_transforms_to_batch(...)
```

The callback receives:

```c
typedef int (FASTDIS_CALL *fastdis_entity_state_callback_t)(
    const fastdis_entity_state_prefix_t* entity_state,
    const uint8_t* data,
    size_t size,
    void* packet_user,
    void* callback_user);
```

When `FASTDIS_ES_FIELD_ALL` is requested, the fixed prefix includes:

```text
header
entity ID: site, application, entity
force ID
variable-parameter count
entity type and alternate entity type
linear velocity
world location
orientation
appearance
dead-reckoning algorithm, parameters, acceleration, angular velocity
marking
capabilities
```

Entity-state scans enforce protocol family `1` and PDU type `1` in C. The scan
config also has `entity_force_ids`, which is applied after reading force ID but
before the callback. ABI v7 adds `entity_state_fields` so engines can request
only routing fields, pose fields, marking, kinematics, or the full prefix. A
callback can check `entity->fields_present` to know exactly what was decoded.

Python ctypes example:

```python
import fastdis.native as native

lib = native.load_native("/path/to/libfastdis.so")

entity = lib.parse_entity_state_prefix(packet)
print(entity.entity_id, entity.force_id, entity.location, entity.orientation)

stats = lib.scan_entity_state_many(
    packets,
    lambda entity, packet: print(entity.entity_id, entity.marking_text),
    versions={6, 7},
    entity_force_ids={1, 2},
    sample_every=10,
    return_stats=True,
)
```


## ABI v7 field subscriptions and scanner context

For engine loops, the lower-overhead pattern is: configure once, scan many times.
The opaque scanner owns native filter state such as large entity-ID sets; no STL
containers cross the DLL/shared-object boundary.

```c
fastdis_scan_config_t cfg;
fastdis_scan_config_init(&cfg);
cfg.entity_state_fields = FASTDIS_ES_FIELD_POSE; /* ID + force + location + orientation */

fastdis_scanner_t *scanner = fastdis_scanner_create(&cfg);
fastdis_scanner_add_entity_id(scanner, 100, 1, 42);
fastdis_scanner_set_entity_id_filter_mode(scanner, FASTDIS_ENTITY_ID_FILTER_ALLOW);

fastdis_scan_stats_t stats;
fastdis_scan_stats_init(&stats);
fastdis_scanner_scan_entity_state_packets(
    scanner,
    packets,
    packet_count,
    on_entity_state,
    user_state,
    &stats);

fastdis_scanner_destroy(scanner);
```

Python ctypes has the same shape:

```python
import fastdis.native as native

lib = native.load_native("/path/to/libfastdis.so")
scanner = lib.create_scanner(
    versions=7,
    entity_state_fields=native.FASTDIS_ES_FIELD_POSE,
)
scanner.allow_entity_ids((100, 1, 42))

stats = scanner.scan_entity_state_many(
    packets,
    lambda entity, packet: print(entity.entity_id, entity.location, entity.orientation),
    return_stats=True,
)
```

Use `FASTDIS_ES_FIELD_ALL` for full fixed-prefix parsing, or compose smaller
masks such as `FASTDIS_ES_FIELD_LOCATION | FASTDIS_ES_FIELD_ORIENTATION` when the
host only needs pose data.


## Double-buffered snapshot handoff

Version `0.12.0-alpha2` / ABI v8 keeps `fastdis_entity_snapshot_buffer_t`, a
reusable native snapshot handoff object for publishing entity-table snapshots
to an engine thread. The network/update side can ingest packets into
`fastdis_entity_table_t`, publish changed snapshots into an inactive buffer
slot, and let the engine acquire a stable read view for the frame. Two slots
preserve strict double-buffer behavior; three or more slots tolerate delayed
engine readers while exposing publish/busy/drop counters.

The combined hot-path helper is:

```c
fastdis_entity_table_ingest_packets_publish_changed(
    table, scanner, packets, packet_count,
    1, 1, snapshot_buffer, &stats, &view);
```

Python ctypes exposes the same flow as:

```python
view, stats = snapshots.ingest_and_publish_changed(
    table, scanner, packets, return_stats=True
)
with snapshots.acquire_latest() as read:
    for snapshot in read.snapshots:
        ...
```

See `docs/DOUBLE_BUFFER_SNAPSHOTS.md` and `docs/CPP_RAII.md`.

## Native latest-state entity table

For engines, the highest-value path is often not “one output per packet,” but
“latest transform per entity.” ABI v7 adds an opaque native entity table:

```c
fastdis_scan_config_t cfg;
fastdis_scan_config_init(&cfg);
fastdis_scan_config_use_profile(&cfg, FASTDIS_PROFILE_ENTITY_TRANSFORM);

fastdis_scanner_t *scanner = fastdis_scanner_create(&cfg);
fastdis_entity_table_t *table = fastdis_entity_table_create(4096);

fastdis_entity_table_update_stats_t stats;
fastdis_entity_table_update_stats_init(&stats);

fastdis_entity_table_ingest_packets(
    table,
    scanner,
    packets,
    packet_count,
    1,      /* advance table tick once for this burst/frame */
    &stats);
```

Then the engine can ask for just the changed entities:

```c
fastdis_entity_snapshot_t snapshots[4096];
fastdis_entity_snapshot_batch_t batch = {snapshots, 4096, 0, 0};

fastdis_entity_table_snapshot_changed(table, &batch, 1 /* clear flags */);
```

or stale entities:

```c
fastdis_entity_table_advance_tick(table, 1);
fastdis_entity_table_snapshot_stale(table, 120, &batch);
fastdis_entity_table_evict_stale(table, 120, &batch);
```

The Python ctypes wrapper exposes the same pattern:

```python
import fastdis.native as native

lib = native.load_native("./build/libfastdis.so")
scanner = lib.create_scanner().use_entity_transform_profile()
table = lib.create_entity_table(reserve=4096)

stats = table.ingest(scanner, packets, advance_tick=True)
changed = table.snapshot_changed(clear=True)
stale = table.snapshot_stale(stale_after_ticks=120)
```

This is the intended Unreal/Godot flow: native code receives packet bursts,
filters/decodes only Entity State transforms, updates a compact native table,
and the engine consumes changed/stale snapshots once per tick.


## Engine adapter scaffolding and frame transforms

Version `0.12.0-alpha2` keeps `include/fastdis/fastdis_frames.hpp` as the
header-only helper for taking DIS Entity State ECEF/geocentric meter positions
into local engine spaces. It also adds replay-driven sample adapters for Unreal
and Godot:

```text
examples/unreal/FastDis/
examples/godot/fastdis_gdextension/
examples/godot/fastdis_demo/
```

The default conversion is position-only and requires an explicit WGS-84 origin.
For Unreal, local ENU meters are mapped to centimeters as north -> +X, east ->
+Y, up -> +Z. For Godot, local ENU meters are mapped as east -> +X, up -> +Y,
north -> -Z. Orientation is opt-in through `OrientationPolicy::ExperimentalLocalYawPitchRoll`
because DIS orientation conventions and asset forward axes should be validated
against known exercise traffic before driving engine rotations. The Godot sample
expects the built GDExtension wrapper plus the host-native `fastdis` shared
library to sit together under `addons/fastdis/bin/`.

## Godot Workflow

The repo now has one operator-facing Godot entry point:

```bash
python tools/godot_workflow.py doctor
python tools/godot_workflow.py full
```

Useful commands:

```bash
python tools/godot_workflow.py discover
python tools/godot_workflow.py build
python tools/godot_workflow.py verify
python tools/godot_workflow.py report
python tools/godot_workflow.py full
```

The Godot build lane will:

- detect `godot` and `scons` from repo-local env, `PATH`, and common host paths,
- build the host-native `fastdis` shared library,
- build the `fastdis_gdextension` wrapper with SCons,
- stage the wrapper plus host-native shared library into both:
  `examples/godot/fastdis_demo/addons/fastdis/bin/`
  `examples/godot/fastdis_orientation_verification/addons/fastdis/bin/`
- run the headless orientation verification harness.

The default Godot scratch root is a no-space temp path:

```text
/private/tmp/fastdis_godot/
```

That keeps the native build output and Godot home/config/cache state away from
space-containing repo paths. When the repo itself lives under a path with
spaces, the Godot helpers also try to use a no-space repo alias for the
`godot --path` and SCons working directory.

Advanced users can still call the lower-level scripts directly:

```bash
python tools/build_godot_extension.py
python tools/run_godot_orientation_verification.py
```

The Godot proof surface can also be written to report artifacts:

```bash
python tools/godot_workflow.py report
```

This updates:

- [godot_workflow_report.json](/Users/rick/Library/Mobile%20Documents/com~apple~CloudDocs/GIT/fastdis/build/reports/godot_workflow_report.json)
- [godot_workflow_report.md](/Users/rick/Library/Mobile%20Documents/com~apple~CloudDocs/GIT/fastdis/build/reports/godot_workflow_report.md)
