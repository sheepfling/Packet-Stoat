# fastdis benchmark report

This report compares the major choices in the fast path: header-only scanning, callbacks, early rejection, downsampling, Entity State field subscriptions, callback-free batch output, compact transform output, reusable scanners, and native allow/block filters, latest-state tables, and double-buffer snapshot publication.

> Results are machine- and build-dependent. Use the ratios to decide what to benchmark in your target engine/runtime, not as universal throughput guarantees.

## Native shared-library benchmark

ABI: `8`; library version: `0.9.0`.

| case                                        | best Mpps | vs header-only | accepted | emitted | malformed | notes                                                                                 |
| ------------------------------------------- | --------- | -------------- | -------- | ------- | --------- | ------------------------------------------------------------------------------------- |
| header_all_no_callback                      | 94.16     | 1.00x          | 200,000  | 200,000 | 0         | 12-byte header only; no Python/engine callback                                        |
| header_all_callback_every                   | 91.40     | 0.97x          | 200,000  | 200,000 | 0         | header callback on every valid packet                                                 |
| header_filter_90pct_reject                  | 76.89     | 0.82x          | 20,000   | 20,000  | 0         | version/exercise/type/family filter; 10% accepted                                     |
| header_filter_90pct_reject_cb               | 79.58     | 0.85x          | 20,000   | 20,000  | 0         | same filter; callback only for accepted 10%                                           |
| header_downsample_1pct_cb                   | 73.59     | 0.78x          | 200,000  | 2,000   | 0         | all accepted; callback every 100th packet                                             |
| header_10pct_malformed                      | 82.56     | 0.88x          | 180,000  | 180,000 | 20,000    | short packets counted as malformed                                                    |
| entity_routing_no_callback                  | 18.04     | 0.19x          | 200,000  | 200,000 | 0         | Entity State fixed prefix: id + force only                                            |
| entity_pose_no_callback                     | 18.29     | 0.19x          | 200,000  | 200,000 | 0         | Entity State id + force + location + orientation                                      |
| entity_all_no_callback                      | 17.72     | 0.19x          | 200,000  | 200,000 | 0         | Entity State full fixed prefix                                                        |
| entity_pose_callback_every                  | 18.06     | 0.19x          | 200,000  | 200,000 | 0         | pose decode plus callback every packet                                                |
| entity_pose_downsample_1pct_cb              | 18.50     | 0.20x          | 200,000  | 2,000   | 0         | pose decode; callback every 100th packet                                              |
| entity_force_filter_25pct                   | 18.39     | 0.20x          | 50,000   | 50,000  | 0         | native force-id filter; force==1                                                      |
| scanner_reuse_pose_no_callback              | 18.48     | 0.20x          | 200,000  | 200,000 | 0         | opaque scanner context reused across rounds                                           |
| scanner_entity_id_allow_32                  | 18.05     | 0.19x          | 6,272    | 6,272   | 0         | native unordered_set allowlist: 32 of 1024 entity IDs                                 |
| entity_pose_to_batch                        | 17.59     | 0.19x          | 200,000  | 200,000 | 0         | callback-free Entity State pose decode into caller-owned array                        |
| entity_transform_to_batch                   | 13.77     | 0.15x          | 200,000  | 200,000 | 0         | callback-free compact engine transform output                                         |
| entity_transform_to_batch_50pct_capacity    | 14.86     | 0.16x          | 200,000  | 200,000 | 0         | compact transform output with undersized output buffer                                |
| scanner_transform_to_batch_allow_32         | 17.59     | 0.19x          | 6,272    | 6,272   | 0         | scanner allowlist plus callback-free compact transform output                         |
| entity_table_ingest_latest                  | 12.95     | 0.14x          | 200,000  | 200,000 | 0         | scan transforms directly into native latest-state entity table                        |
| entity_snapshot_publish_changed_dirty       | 141.03    | 1.50x          | 1,024    | 1,024   | 0         | publish already-dirty changed snapshots into double buffer; no packet scan            |
| entity_snapshot_publish_all                 | 94.84     | 1.01x          | 1,024    | 1,024   | 0         | publish all latest-state snapshots into double buffer; no packet scan                 |
| entity_table_ingest_publish_changed         | 12.94     | 0.14x          | 200,000  | 200,000 | 0         | ingest latest-state table, then publish changed snapshots into double buffer          |
| entity_table_ingest_publish_acquire_release | 13.03     | 0.14x          | 200,000  | 200,000 | 0         | ingest, publish changed snapshots, acquire/release latest view                        |
| entity_table_ingest_publish_combined        | 13.03     | 0.14x          | 200,000  | 200,000 | 0         | single ABI call: ingest latest-state table and publish changed double-buffer snapshot |

### Native readout

- Header callback-every-packet throughput vs header-only: `0.97x`.
- Header downsample-before-callback throughput vs callback-every-packet: `0.81x`.
- Entity pose-only decode vs full fixed-prefix decode: `1.03x`.
- Reused scanner pose decode vs one-shot pose decode: `1.01x`.
- Native entity-ID allowlist throughput vs routing-only decode: `1.00x`.
- Callback-free pose batch throughput vs pose callback-every-packet: `0.97x`.
- Compact transform batch throughput vs pose batch throughput: `0.78x`.
- Entity-table ingest + changed publish vs ingest-only: `1.00x`.
- Combined ingest+publish ABI call vs separate ingest+publish: `1.01x`.
- Publish-all snapshot buffer vs publish-changed dirty snapshot buffer: `0.67x`.

## Python ctypes benchmark

ABI: `8`; library version: `0.9.0`.

| case                                       | Mpps  | vs ctypes header-only | accepted | emitted | callbacks | notes                                                                                          |
| ------------------------------------------ | ----- | --------------------- | -------- | ------- | --------- | ---------------------------------------------------------------------------------------------- |
| ctypes_header_no_callback                  | 0.079 | 1.00x                 | 30,000   | 30,000  | 0         | includes packet-view setup + one ctypes scan call                                              |
| ctypes_header_callback_every_packet        | 0.072 | 0.91x                 | 30,000   | 30,000  | 30,000    | Python callback for every accepted packet                                                      |
| ctypes_header_callback_sample_100          | 0.064 | 0.81x                 | 30,000   | 300     | 300       | downsample in C before Python callback                                                         |
| ctypes_entity_pose_no_callback             | 0.085 | 1.08x                 | 30,000   | 30,000  | 0         | Entity State pose-only decode through ctypes wrapper                                           |
| ctypes_entity_all_no_callback              | 0.081 | 1.03x                 | 30,000   | 30,000  | 0         | Entity State full fixed-prefix decode through ctypes wrapper                                   |
| ctypes_entity_pose_to_batch                | 0.052 | 0.66x                 | 30,000   | 30,000  | 0         | callback-free native batch, then Python value conversion                                       |
| ctypes_entity_transform_to_batch           | 0.064 | 0.80x                 | 30,000   | 30,000  | 0         | compact transform batch output, then Python value conversion                                   |
| ctypes_entity_force_reject_no_callback     | 0.093 | 1.18x                 | 0        | 0       | 0         | C-side force-ID filter rejects all after minimal decode                                        |
| ctypes_scanner_entity_id_allow_one         | 0.082 | 1.04x                 | 30       | 30      | 0         | reusable scanner + native entity-ID allowlist                                                  |
| ctypes_scanner_transform_batch_allow_one   | 0.099 | 1.25x                 | 30       | 30      | 0         | reusable scanner + entity allowlist + compact transform batch                                  |
| ctypes_entity_table_ingest_latest          | 0.096 | 1.22x                 | 30,000   | 30,000  | 0         | ctypes wrapper updates native latest-state table                                               |
| ctypes_entity_table_ingest_publish_changed | 0.067 | 0.85x                 | 30,000   | 30,000  | 0         | ingest native latest-state table, publish changed snapshots into reusable native double buffer |
| ctypes_snapshot_acquire_copy_release       | 0.072 | 0.91x                 | 30,000   | 30,000  | 0         | publish changed snapshots, acquire latest view, copy to Python tuple, release                  |
| ctypes_ingest_publish_changed_combined     | 0.083 | 1.05x                 | 30,000   | 30,000  | 0         | single ctypes ABI call: ingest table and publish changed snapshot buffer                       |
| ctypes_scanner_chained_filters_callback    | 0.092 | 1.17x                 | 15,000   | 150     | 150       | chained filter API: force IDs [1,2] + sample 1/100 + Python callback                           |

### ctypes readout

- Python callback-every-packet throughput vs ctypes header-only: `0.91x`.
- C-side downsample before Python callback vs callback-every-packet: `0.89x`.
- ctypes pose-only Entity State decode vs full fixed-prefix decode: `1.04x`.
- chained filters + downsample callback vs callback-every-packet: `1.29x`.
- ctypes transform batch vs ctypes pose callback-free scan: `0.75x`.
- ctypes table ingest + snapshot-buffer publish vs table ingest-only: `0.70x`.
- ctypes combined ingest+publish vs separate ingest+publish: `1.24x`.

## Practical conclusions to look for

- If callback-every-packet is much slower than no-callback scanning, move more filtering/downsampling into C before the callback.
- If pose-only and full-prefix Entity State decode are close, memory/cache effects may dominate and field masks matter less for your traffic.
- If ctypes is far slower than native, that is expected; Unreal/Godot should call the DLL directly, while Python should batch large packet groups.
- If combined ingest+publish is not meaningfully faster than separate calls, keep the separate calls for clearer engine integration unless your FFI boundary is expensive.
- If entity-ID allowlists are costly at large set sizes, the next optimization is a sorted/vectorized set or fixed-domain bitmap for known site/application pairs.

