# fastdis benchmark report

This report compares the major choices in the fast path: header-only scanning, callbacks, early rejection, downsampling, Entity State field subscriptions, reusable scanners, and native allow/block filters.

> Results are machine- and build-dependent. Use the ratios to decide what to benchmark in your target engine/runtime, not as universal throughput guarantees.

## Native shared-library benchmark

ABI: `5`; library version: `0.6.0`.

| case                           | best Mpps | vs header-only | accepted | emitted | malformed | notes                                                 |
| ------------------------------ | --------- | -------------- | -------- | ------- | --------- | ----------------------------------------------------- |
| header_all_no_callback         | 85.64     | 1.00x          | 300,000  | 300,000 | 0         | 12-byte header only; no Python/engine callback        |
| header_all_callback_every      | 83.42     | 0.97x          | 300,000  | 300,000 | 0         | header callback on every valid packet                 |
| header_filter_90pct_reject     | 73.01     | 0.85x          | 30,000   | 30,000  | 0         | version/exercise/type/family filter; 10% accepted     |
| header_filter_90pct_reject_cb  | 75.41     | 0.88x          | 30,000   | 30,000  | 0         | same filter; callback only for accepted 10%           |
| header_downsample_1pct_cb      | 65.49     | 0.76x          | 300,000  | 3,000   | 0         | all accepted; callback every 100th packet             |
| header_10pct_malformed         | 52.89     | 0.62x          | 270,000  | 270,000 | 30,000    | short packets counted as malformed                    |
| entity_routing_no_callback     | 18.45     | 0.22x          | 300,000  | 300,000 | 0         | Entity State fixed prefix: id + force only            |
| entity_pose_no_callback        | 18.37     | 0.21x          | 300,000  | 300,000 | 0         | Entity State id + force + location + orientation      |
| entity_all_no_callback         | 17.51     | 0.20x          | 300,000  | 300,000 | 0         | Entity State full fixed prefix                        |
| entity_pose_callback_every     | 17.95     | 0.21x          | 300,000  | 300,000 | 0         | pose decode plus callback every packet                |
| entity_pose_downsample_1pct_cb | 17.55     | 0.20x          | 300,000  | 3,000   | 0         | pose decode; callback every 100th packet              |
| entity_force_filter_25pct      | 18.33     | 0.21x          | 75,000   | 75,000  | 0         | native force-id filter; force==1                      |
| scanner_reuse_pose_no_callback | 18.01     | 0.21x          | 300,000  | 300,000 | 0         | opaque scanner context reused across rounds           |
| scanner_entity_id_allow_32     | 17.79     | 0.21x          | 9,376    | 9,376   | 0         | native unordered_set allowlist: 32 of 1024 entity IDs |

### Native readout

- Header callback-every-packet throughput vs header-only: `0.97x`.
- Header downsample-before-callback throughput vs callback-every-packet: `0.79x`.
- Entity pose-only decode vs full fixed-prefix decode: `1.05x`.
- Reused scanner pose decode vs one-shot pose decode: `0.98x`.
- Native entity-ID allowlist throughput vs routing-only decode: `0.96x`.

## Python ctypes benchmark

ABI: `5`; library version: `0.6.0`.

| case                                    | Mpps  | vs ctypes header-only | accepted | emitted | callbacks | notes                                                                |
| --------------------------------------- | ----- | --------------------- | -------- | ------- | --------- | -------------------------------------------------------------------- |
| ctypes_header_no_callback               | 0.086 | 1.00x                 | 90,000   | 90,000  | 0         | includes packet-view setup + one ctypes scan call                    |
| ctypes_header_callback_every_packet     | 0.073 | 0.85x                 | 90,000   | 90,000  | 90,000    | Python callback for every accepted packet                            |
| ctypes_header_callback_sample_100       | 0.076 | 0.89x                 | 90,000   | 900     | 900       | downsample in C before Python callback                               |
| ctypes_entity_pose_no_callback          | 0.079 | 0.92x                 | 90,000   | 90,000  | 0         | Entity State pose-only decode through ctypes wrapper                 |
| ctypes_entity_all_no_callback           | 0.059 | 0.68x                 | 90,000   | 90,000  | 0         | Entity State full fixed-prefix decode through ctypes wrapper         |
| ctypes_entity_force_reject_no_callback  | 0.044 | 0.51x                 | 0        | 0       | 0         | C-side force-ID filter rejects all after minimal decode              |
| ctypes_scanner_entity_id_allow_one      | 0.043 | 0.50x                 | 90       | 90      | 0         | reusable scanner + native entity-ID allowlist                        |
| ctypes_scanner_chained_filters_callback | 0.046 | 0.53x                 | 45,000   | 450     | 450       | chained filter API: force IDs [1,2] + sample 1/100 + Python callback |

### ctypes readout

- Python callback-every-packet throughput vs ctypes header-only: `0.85x`.
- C-side downsample before Python callback vs callback-every-packet: `1.05x`.
- ctypes pose-only Entity State decode vs full fixed-prefix decode: `1.34x`.
- chained filters + downsample callback vs callback-every-packet: `0.63x`.

## Practical conclusions to look for

- If callback-every-packet is much slower than no-callback scanning, move more filtering/downsampling into C before the callback.
- If pose-only and full-prefix Entity State decode are close, memory/cache effects may dominate and field masks matter less for your traffic.
- If ctypes is far slower than native, that is expected; Unreal/Godot should call the DLL directly, while Python should batch large packet groups.
- If entity-ID allowlists are costly at large set sizes, the next optimization is a sorted/vectorized set or fixed-domain bitmap for known site/application pairs.

