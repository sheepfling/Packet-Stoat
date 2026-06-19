# fastdis benchmark report

This report compares the major choices in the fast path: header-only scanning, callbacks, early rejection, downsampling, Entity State field subscriptions, callback-free batch output, compact transform output, reusable scanners, and native allow/block filters.

> Results are machine- and build-dependent. Use the ratios to decide what to benchmark in your target engine/runtime, not as universal throughput guarantees.

## Native shared-library benchmark

ABI: `6`; library version: `0.7.0`.

| case                                     | best Mpps | vs header-only | accepted | emitted | malformed | notes                                                          |
| ---------------------------------------- | --------- | -------------- | -------- | ------- | --------- | -------------------------------------------------------------- |
| header_all_no_callback                   | 38.97     | 1.00x          | 30,000   | 30,000  | 0         | 12-byte header only; no Python/engine callback                 |
| header_all_callback_every                | 34.84     | 0.89x          | 30,000   | 30,000  | 0         | header callback on every valid packet                          |
| header_filter_90pct_reject               | 48.14     | 1.24x          | 3,000    | 3,000   | 0         | version/exercise/type/family filter; 10% accepted              |
| header_filter_90pct_reject_cb            | 48.20     | 1.24x          | 3,000    | 3,000   | 0         | same filter; callback only for accepted 10%                    |
| header_downsample_1pct_cb                | 33.59     | 0.86x          | 30,000   | 300     | 0         | all accepted; callback every 100th packet                      |
| header_10pct_malformed                   | 41.66     | 1.07x          | 27,000   | 27,000  | 3,000     | short packets counted as malformed                             |
| entity_routing_no_callback               | 10.16     | 0.26x          | 30,000   | 30,000  | 0         | Entity State fixed prefix: id + force only                     |
| entity_pose_no_callback                  | 10.38     | 0.27x          | 30,000   | 30,000  | 0         | Entity State id + force + location + orientation               |
| entity_all_no_callback                   | 9.54      | 0.24x          | 30,000   | 30,000  | 0         | Entity State full fixed prefix                                 |
| entity_pose_callback_every               | 9.97      | 0.26x          | 30,000   | 30,000  | 0         | pose decode plus callback every packet                         |
| entity_pose_downsample_1pct_cb           | 10.18     | 0.26x          | 30,000   | 300     | 0         | pose decode; callback every 100th packet                       |
| entity_force_filter_25pct                | 10.52     | 0.27x          | 7,500    | 7,500   | 0         | native force-id filter; force==1                               |
| scanner_reuse_pose_no_callback           | 9.59      | 0.25x          | 30,000   | 30,000  | 0         | opaque scanner context reused across rounds                    |
| scanner_entity_id_allow_32               | 7.85      | 0.20x          | 960      | 960     | 0         | native unordered_set allowlist: 32 of 1024 entity IDs          |
| entity_pose_to_batch                     | 9.15      | 0.23x          | 30,000   | 30,000  | 0         | callback-free Entity State pose decode into caller-owned array |
| entity_transform_to_batch                | 8.32      | 0.21x          | 30,000   | 30,000  | 0         | callback-free compact engine transform output                  |
| entity_transform_to_batch_50pct_capacity | 8.34      | 0.21x          | 30,000   | 30,000  | 0         | compact transform output with undersized output buffer         |
| scanner_transform_to_batch_allow_32      | 7.13      | 0.18x          | 960      | 960     | 0         | scanner allowlist plus callback-free compact transform output  |

### Native readout

- Header callback-every-packet throughput vs header-only: `0.89x`.
- Header downsample-before-callback throughput vs callback-every-packet: `0.96x`.
- Entity pose-only decode vs full fixed-prefix decode: `1.09x`.
- Reused scanner pose decode vs one-shot pose decode: `0.92x`.
- Native entity-ID allowlist throughput vs routing-only decode: `0.77x`.
- Callback-free pose batch throughput vs pose callback-every-packet: `0.92x`.
- Compact transform batch throughput vs pose batch throughput: `0.91x`.

## Python ctypes benchmark

ABI: `6`; library version: `0.7.0`.

| case                                     | Mpps  | vs ctypes header-only | accepted | emitted | callbacks | notes                                                                |
| ---------------------------------------- | ----- | --------------------- | -------- | ------- | --------- | -------------------------------------------------------------------- |
| ctypes_header_no_callback                | 0.040 | 1.00x                 | 6,000    | 6,000   | 0         | includes packet-view setup + one ctypes scan call                    |
| ctypes_header_callback_every_packet      | 0.060 | 1.50x                 | 6,000    | 6,000   | 6,000     | Python callback for every accepted packet                            |
| ctypes_header_callback_sample_100        | 0.068 | 1.68x                 | 6,000    | 60      | 60        | downsample in C before Python callback                               |
| ctypes_entity_pose_no_callback           | 0.017 | 0.43x                 | 6,000    | 6,000   | 0         | Entity State pose-only decode through ctypes wrapper                 |
| ctypes_entity_all_no_callback            | 0.085 | 2.11x                 | 6,000    | 6,000   | 0         | Entity State full fixed-prefix decode through ctypes wrapper         |
| ctypes_entity_pose_to_batch              | 0.039 | 0.98x                 | 6,000    | 6,000   | 0         | callback-free native batch, then Python value conversion             |
| ctypes_entity_transform_to_batch         | 0.060 | 1.49x                 | 6,000    | 6,000   | 0         | compact transform batch output, then Python value conversion         |
| ctypes_entity_force_reject_no_callback   | 0.093 | 2.32x                 | 0        | 0       | 0         | C-side force-ID filter rejects all after minimal decode              |
| ctypes_scanner_entity_id_allow_one       | 0.069 | 1.72x                 | 6        | 6       | 0         | reusable scanner + native entity-ID allowlist                        |
| ctypes_scanner_transform_batch_allow_one | 0.072 | 1.78x                 | 6        | 6       | 0         | reusable scanner + entity allowlist + compact transform batch        |
| ctypes_scanner_chained_filters_callback  | 0.084 | 2.10x                 | 3,000    | 30      | 30        | chained filter API: force IDs [1,2] + sample 1/100 + Python callback |

### ctypes readout

- Python callback-every-packet throughput vs ctypes header-only: `1.50x`.
- C-side downsample before Python callback vs callback-every-packet: `1.12x`.
- ctypes pose-only Entity State decode vs full fixed-prefix decode: `0.20x`.
- chained filters + downsample callback vs callback-every-packet: `1.40x`.
- ctypes transform batch vs ctypes pose callback-free scan: `3.47x`.

## Practical conclusions to look for

- If callback-every-packet is much slower than no-callback scanning, move more filtering/downsampling into C before the callback.
- If pose-only and full-prefix Entity State decode are close, memory/cache effects may dominate and field masks matter less for your traffic.
- If ctypes is far slower than native, that is expected; Unreal/Godot should call the DLL directly, while Python should batch large packet groups.
- If entity-ID allowlists are costly at large set sizes, the next optimization is a sorted/vectorized set or fixed-domain bitmap for known site/application pairs.

