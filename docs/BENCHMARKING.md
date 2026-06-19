# Benchmarking fastdis

`fastdis` has two benchmark layers:

1. **Native benchmark**: `benchmarks/native_bench.cpp`, built as `fastdis_native_bench`.
   This measures the DLL/shared-object ABI directly and does not include Python
   packet-view construction or `ctypes` overhead.
2. **Python ctypes benchmark**: `benchmarks/bench_ctypes.py`. This measures what
   a Python host pays when it drives the shared library through `ctypes`.

Use the native benchmark to decide what belongs in the C/C++ hot path. Use the
Python benchmark to decide whether a Python-facing workload needs batching,
downsampling, or a CPython extension.

## Build

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release
```

The native benchmark target is enabled by default through:

```cmake
option(FASTDIS_BUILD_BENCHMARKS "Build native benchmarks" ON)
```

## One-command benchmark run

```bash
python tools/run_benchmarks.py --native-packets 1000000 --native-rounds 5 \
  --ctypes-packets 50000 --ctypes-repeats 5 --format table

python tools/run_benchmarks.py --format json --out-dir bench-results
```

This helper configures CMake, builds the shared library and native benchmark,
then runs both the native benchmark and the Python ctypes benchmark. In JSON
mode it also writes:

- `summary.md`
- `qualification.json`
- `current.json`

where `current.json` contains the combined native + ctypes payload and
`summary.md` is a Markdown report from `tools/summarize_benchmarks.py`.
`qualification.json` is the machine-readable Alpha 3 benchmark qualification
artifact with core-case extracts, latency quantiles, allocation expectations,
and suggested regression-guard cases.

## Native benchmark

```bash
./build/fastdis_native_bench --packets 1000000 --rounds 5 --format table
./build/fastdis_native_bench --packets 1000000 --rounds 5 --format csv > native.csv
./build/fastdis_native_bench --packets 1000000 --rounds 5 --format json > native.json
```

The cases currently separate:

| Case family | What it measures |
|---|---|
| `header_*` | 12-byte DIS header parsing, filtering, malformed rejection, and callback/downsampling cost. |
| `entity_routing_*` | Entity State PDU path with only entity ID and force ID decoded. |
| `entity_pose_*` | Entity State PDU path with entity ID, force ID, location, and orientation decoded. |
| `entity_all_*` | Full fixed 144-byte Entity State prefix decode. |
| `entity_force_filter_*` | C-side force-ID filtering before callbacks. |
| `scanner_*` | Opaque reusable scanner context and native entity-ID allowlist overhead. |
| `synthetic_*` | Alpha 2 named synthetic workloads for 1, 100, and 10k active-entity patterns. |
| `snapshot_*` | Snapshot publish/all/acquire/delayed-reader buffer behavior. |
| `frame_transform_*` | Snapshot walk cost with and without engine-frame conversion. |

Interpretation rules:

- Compare `header_all_no_callback` against `header_all_callback_every` to see the
  raw C callback cost.
- Compare `header_all_callback_every` against `header_downsample_1pct_cb` to see
  how much early downsampling saves callback pressure.
- Compare `entity_routing_no_callback`, `entity_pose_no_callback`, and
  `entity_all_no_callback` to decide whether field subscriptions are worth it.
- Compare `entity_pose_no_callback` against `scanner_entity_id_allow_32` to see
  native entity-ID allowlist overhead and selectivity.
- Use `p50_ms`, `p95_ms`, and `p99_ms` to qualify burst latency, not just
  throughput.
- Always run enough packets/rounds to stabilize CPU frequency and cache effects.

## Python ctypes benchmark

Build the shared library first, then run:

```bash
FASTDIS_LIBRARY=$PWD/build/libfastdis.so \
PYTHONPATH=src \
python benchmarks/bench_ctypes.py --packets 50000 --repeats 5 --format table
```

On macOS/Windows, point `FASTDIS_LIBRARY` at `libfastdis.dylib` or `fastdis.dll`.
CSV/JSON are also available:

```bash
python benchmarks/bench_ctypes.py --format csv --out ctypes.csv
python benchmarks/bench_ctypes.py --format json --out ctypes.json
```

The ctypes benchmark intentionally includes Python overhead:

- building `fastdis_packet_view_t` arrays from Python packets,
- one or more `ctypes` calls,
- optional Python callbacks.

A large gap between native Mpps and ctypes Mpps is expected. That gap is the
reason engine hosts should call the DLL directly and Python hosts should batch
large packet groups. Use the latency quantiles here as well; Alpha 3 claims
should cite both throughput and tail latency.

## Benchmark report generator

To turn JSON outputs into a Markdown summary and qualification artifact:

```bash
python tools/run_benchmarks.py --format json --out-dir benchmark_results
python tools/summarize_benchmarks.py \
  --native benchmark_results/native.json \
  --ctypes benchmark_results/ctypes.json \
  --out benchmark_results/summary.md \
  --json-out benchmark_results/qualification.json
```

The report highlights the questions we actually care about: callback overhead,
filter rejection benefit, downsampling benefit, field-subscription benefit,
scanner/allowlist overhead, latest-state table overhead, snapshot publication
cost, frame-transform cost, and latency quantiles across the same cases.

## Easy filter setup

The ABI v7 helpers let a host configure filters without directly modifying the
layout of `fastdis_scan_config_t`:

```c
fastdis_scan_config_t cfg;
fastdis_scan_config_init(&cfg);

uint8_t versions[] = {6, 7};
fastdis_scan_config_filter_only(&cfg, FASTDIS_FILTER_VERSION, versions, 2);

uint8_t pdu_types[] = {FASTDIS_ENTITY_STATE_PDU_TYPE};
fastdis_scan_config_filter_only(&cfg, FASTDIS_FILTER_PDU_TYPE, pdu_types, 1);

fastdis_scan_config_set_sample(&cfg, 100, 0);
fastdis_scan_config_set_entity_state_fields(&cfg, FASTDIS_ES_FIELD_POSE);
```

For reusable scanners:

```c
fastdis_scanner_t *scanner = fastdis_scanner_create(&cfg);

fastdis_entity_id_t ids[] = {
    {100, 1, 42},
    {100, 1, 43},
};
fastdis_scanner_set_entity_ids(scanner, FASTDIS_ENTITY_ID_FILTER_ALLOW, ids, 2);
fastdis_scanner_set_sample(scanner, 10, 0);
fastdis_scanner_set_entity_state_fields(scanner, FASTDIS_ES_FIELD_POSE);

fastdis_scanner_scan_entity_state_packets(scanner, packets, count, callback, user, &stats);
fastdis_scanner_destroy(scanner);
```

Python has chainable equivalents:

```python
scanner = lib.create_scanner(versions=7, entity_state_fields=native.FASTDIS_ES_FIELD_POSE)
scanner.only_pdu_types(1).only_entity_force_ids([1, 2]).set_sample(100)
scanner.allow_entity_ids([(100, 1, 42), (100, 1, 43)])
```

## Replay packet files

The native benchmark can read a simple dependency-free replay format:

```text
uint32_be packet_length
packet bytes
uint32_be packet_length
packet bytes
...
```

Generate a synthetic replay file:

```bash
python tools/make_replay.py benchmark_results/synthetic.fastdispkt --packets 100000
```

Benchmark it:

```bash
./build/fastdis_native_bench --packet-file benchmark_results/synthetic.fastdispkt \
  --packets 100000 --rounds 5 --format table
```

The core library intentionally does not depend on libpcap. A capture converter
can be built outside the ABI by writing each UDP payload into `.fastdispkt`.

Alpha 3 keeps that layering explicit. See:

- `docs/NETWORKING.md`
- `docs/REPLAY_FORMAT.md`

The shared example reader lives at:

```text
examples/common/replay_reader.hpp
```

and the optional UDP burst helper lives at:

```text
examples/common/udp_receiver.hpp
examples/cpp/udp_burst.cpp
```

## Batch-output cases

ABI v7 introduced callback-free batch-output cases:

| Case | What it measures |
|---|---|
| `entity_pose_to_batch` | Entity State pose decode into a caller-owned POD array with no per-packet callback. |
| `entity_transform_to_batch` | Engine-shaped compact transform output. |
| `entity_transform_to_batch_50pct_capacity` | Output-buffer overflow accounting without allocation. |
| `scanner_transform_to_batch_allow_32` | Scanner allowlist plus compact transform output. |

Batch output is the preferred shape for Unreal/Godot because it keeps the FFI
boundary coarse: one scan call per packet burst, followed by one array walk in
engine code.

## Latest-state and double-buffer cases

ABI v8 adds these native benchmark cases:

| Case | What it measures |
|---|---|
| `entity_table_ingest_latest` | Scan compact transforms directly into the native latest-state entity table. |
| `entity_snapshot_publish_changed_dirty` | Publish already-dirty changed snapshots into a double buffer; no packet scan. |
| `entity_snapshot_publish_all` | Publish every latest-state entry into a double buffer; no packet scan. |
| `entity_table_ingest_publish_changed` | Packet scan + table update + changed snapshot publish as separate native calls. |
| `entity_table_ingest_publish_acquire_release` | Same as above, plus acquire/release of the latest read view. |
| `entity_table_ingest_publish_combined` | Single ABI call that ingests a burst and publishes changed snapshots. |

Use these together to answer whether snapshot publication is a real bottleneck.
In the sample run, publication was effectively free compared with Entity State
transform decode plus latest-state table updates.

## Regression checks

To fail CI or a local release check when throughput drops too far:

```bash
python tools/check_benchmark_regression.py \
  benchmark_results/baseline.json \
  benchmark_results/current.json \
  --max-regression-percent 10
```

Pass `--only-case` multiple times if you want to gate only a subset of cases.
The checker accepts either a single benchmark payload with a top-level
`results` list or the combined `current.json` payload emitted by
`tools/run_benchmarks.py`.
