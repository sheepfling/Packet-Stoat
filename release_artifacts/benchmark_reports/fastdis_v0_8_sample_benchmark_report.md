# fastdis benchmark report

This report compares the major choices in the fast path: header-only scanning, callbacks, early rejection, downsampling, Entity State field subscriptions, callback-free batch output, compact transform output, reusable scanners, and native allow/block filters.

> Results are machine- and build-dependent. Use the ratios to decide what to benchmark in your target engine/runtime, not as universal throughput guarantees.

## Native shared-library benchmark

ABI: `7`; library version: `0.8.0`.

| case                                     | best Mpps | vs header-only | accepted | emitted | malformed | notes                                                          |
| ---------------------------------------- | --------- | -------------- | -------- | ------- | --------- | -------------------------------------------------------------- |
| header_all_no_callback                   | 93.69     | 1.00x          | 20,000   | 20,000  | 0         | 12-byte header only; no Python/engine callback                 |
| header_all_callback_every                | 89.37     | 0.95x          | 20,000   | 20,000  | 0         | header callback on every valid packet                          |
| header_filter_90pct_reject               | 78.28     | 0.84x          | 2,000    | 2,000   | 0         | version/exercise/type/family filter; 10% accepted              |
| header_filter_90pct_reject_cb            | 79.71     | 0.85x          | 2,000    | 2,000   | 0         | same filter; callback only for accepted 10%                    |
| header_downsample_1pct_cb                | 75.19     | 0.80x          | 20,000   | 200     | 0         | all accepted; callback every 100th packet                      |
| header_10pct_malformed                   | 68.73     | 0.73x          | 18,000   | 18,000  | 2,000     | short packets counted as malformed                             |
| entity_routing_no_callback               | 18.08     | 0.19x          | 20,000   | 20,000  | 0         | Entity State fixed prefix: id + force only                     |
| entity_pose_no_callback                  | 18.29     | 0.20x          | 20,000   | 20,000  | 0         | Entity State id + force + location + orientation               |
| entity_all_no_callback                   | 17.83     | 0.19x          | 20,000   | 20,000  | 0         | Entity State full fixed prefix                                 |
| entity_pose_callback_every               | 18.09     | 0.19x          | 20,000   | 20,000  | 0         | pose decode plus callback every packet                         |
| entity_pose_downsample_1pct_cb           | 18.17     | 0.19x          | 20,000   | 200     | 0         | pose decode; callback every 100th packet                       |
| entity_force_filter_25pct                | 18.50     | 0.20x          | 5,000    | 5,000   | 0         | native force-id filter; force==1                               |
| scanner_reuse_pose_no_callback           | 18.42     | 0.20x          | 20,000   | 20,000  | 0         | opaque scanner context reused across rounds                    |
| scanner_entity_id_allow_32               | 18.14     | 0.19x          | 640      | 640     | 0         | native unordered_set allowlist: 32 of 1024 entity IDs          |
| entity_pose_to_batch                     | 17.54     | 0.19x          | 20,000   | 20,000  | 0         | callback-free Entity State pose decode into caller-owned array |
| entity_transform_to_batch                | 14.06     | 0.15x          | 20,000   | 20,000  | 0         | callback-free compact engine transform output                  |
| entity_transform_to_batch_50pct_capacity | 15.15     | 0.16x          | 20,000   | 20,000  | 0         | compact transform output with undersized output buffer         |
| scanner_transform_to_batch_allow_32      | 17.29     | 0.18x          | 640      | 640     | 0         | scanner allowlist plus callback-free compact transform output  |
| entity_table_ingest_latest               | 13.04     | 0.14x          | 20,000   | 20,000  | 0         | scan transforms directly into native latest-state entity table |

### Native readout

- Header callback-every-packet throughput vs header-only: `0.95x`.
- Header downsample-before-callback throughput vs callback-every-packet: `0.84x`.
- Entity pose-only decode vs full fixed-prefix decode: `1.03x`.
- Reused scanner pose decode vs one-shot pose decode: `1.01x`.
- Native entity-ID allowlist throughput vs routing-only decode: `1.00x`.
- Callback-free pose batch throughput vs pose callback-every-packet: `0.97x`.
- Compact transform batch throughput vs pose batch throughput: `0.80x`.

## Python ctypes benchmark

ABI: `7`; library version: `0.8.0`.

| case                                     | Mpps  | vs ctypes header-only | accepted | emitted | callbacks | notes                                                                |
| ---------------------------------------- | ----- | --------------------- | -------- | ------- | --------- | -------------------------------------------------------------------- |
| ctypes_header_no_callback                | 0.063 | 1.00x                 | 4,000    | 4,000   | 0         | includes packet-view setup + one ctypes scan call                    |
| ctypes_header_callback_every_packet      | 0.141 | 2.26x                 | 4,000    | 4,000   | 4,000     | Python callback for every accepted packet                            |
| ctypes_header_callback_sample_100        | 0.151 | 2.42x                 | 4,000    | 40      | 40        | downsample in C before Python callback                               |
| ctypes_entity_pose_no_callback           | 0.154 | 2.46x                 | 4,000    | 4,000   | 0         | Entity State pose-only decode through ctypes wrapper                 |
| ctypes_entity_all_no_callback            | 0.153 | 2.45x                 | 4,000    | 4,000   | 0         | Entity State full fixed-prefix decode through ctypes wrapper         |
| ctypes_entity_pose_to_batch              | 0.037 | 0.58x                 | 4,000    | 4,000   | 0         | callback-free native batch, then Python value conversion             |
| ctypes_entity_transform_to_batch         | 0.146 | 2.33x                 | 4,000    | 4,000   | 0         | compact transform batch output, then Python value conversion         |
| ctypes_entity_force_reject_no_callback   | 0.158 | 2.54x                 | 0        | 0       | 0         | C-side force-ID filter rejects all after minimal decode              |
| ctypes_scanner_entity_id_allow_one       | 0.155 | 2.49x                 | 4        | 4       | 0         | reusable scanner + native entity-ID allowlist                        |
| ctypes_scanner_transform_batch_allow_one | 0.122 | 1.95x                 | 4        | 4       | 0         | reusable scanner + entity allowlist + compact transform batch        |
| ctypes_entity_table_ingest_latest        | 0.217 | 3.47x                 | 4,000    | 4,000   | 0         | ctypes wrapper updates native latest-state table                     |
| ctypes_scanner_chained_filters_callback  | 0.209 | 3.35x                 | 2,000    | 20      | 20        | chained filter API: force IDs [1,2] + sample 1/100 + Python callback |

### ctypes readout

- Python callback-every-packet throughput vs ctypes header-only: `2.26x`.
- C-side downsample before Python callback vs callback-every-packet: `1.07x`.
- ctypes pose-only Entity State decode vs full fixed-prefix decode: `1.00x`.
- chained filters + downsample callback vs callback-every-packet: `1.48x`.
- ctypes transform batch vs ctypes pose callback-free scan: `0.95x`.

## Practical conclusions to look for

- If callback-every-packet is much slower than no-callback scanning, move more filtering/downsampling into C before the callback.
- If pose-only and full-prefix Entity State decode are close, memory/cache effects may dominate and field masks matter less for your traffic.
- If ctypes is far slower than native, that is expected; Unreal/Godot should call the DLL directly, while Python should batch large packet groups.
- If entity-ID allowlists are costly at large set sizes, the next optimization is a sorted/vectorized set or fixed-domain bitmap for known site/application pairs.

