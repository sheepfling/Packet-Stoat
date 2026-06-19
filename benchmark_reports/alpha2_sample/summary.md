# fastdis benchmark report

This report compares the major choices in the fast path: header-only scanning, callbacks, early rejection, downsampling, Entity State field subscriptions, callback-free batch output, compact transform output, reusable scanners, and native allow/block filters, latest-state tables, and double-buffer snapshot publication.

> Results are machine- and build-dependent. Use the ratios to decide what to benchmark in your target engine/runtime, not as universal throughput guarantees.

## Native shared-library benchmark

ABI: `8`; library version: `0.12.0-alpha2`.

| case                                        | best Mpps | vs header-only | accepted | emitted | malformed | notes                                                                                  |
| ------------------------------------------- | --------- | -------------- | -------- | ------- | --------- | -------------------------------------------------------------------------------------- |
| header_all_no_callback                      | 105.12    | 1.00x          | 50,000   | 50,000  | 0         | 12-byte header only; no Python/engine callback                                         |
| synthetic_header_only                       | 97.14     | 0.92x          | 50,000   | 50,000  | 0         | Alpha 2 synthetic header-only baseline                                                 |
| header_all_callback_every                   | 96.42     | 0.92x          | 50,000   | 50,000  | 0         | header callback on every valid packet                                                  |
| header_filter_90pct_reject                  | 117.97    | 1.12x          | 5,000    | 5,000   | 0         | version/exercise/type/family filter; 10% accepted                                      |
| mixed_pdu_noise                             | 118.19    | 1.12x          | 5,000    | 5,000   | 0         | Alpha 2 mixed-PDU noise workload with 10% accepted entity traffic                      |
| header_filter_90pct_reject_cb               | 115.26    | 1.10x          | 5,000    | 5,000   | 0         | same filter; callback only for accepted 10%                                            |
| header_downsample_1pct_cb                   | 109.59    | 1.04x          | 50,000   | 500     | 0         | all accepted; callback every 100th packet                                              |
| header_10pct_malformed                      | 142.50    | 1.36x          | 45,000   | 45,000  | 5,000     | short packets counted as malformed                                                     |
| entity_routing_no_callback                  | 28.29     | 0.27x          | 50,000   | 50,000  | 0         | Entity State fixed prefix: id + force only                                             |
| entity_pose_no_callback                     | 29.81     | 0.28x          | 50,000   | 50,000  | 0         | Entity State id + force + location + orientation                                       |
| synthetic_entity_state_1_entity             | 29.93     | 0.28x          | 50,000   | 50,000  | 0         | Entity State transform workload with one hot entity                                    |
| synthetic_entity_state_100_entities         | 33.38     | 0.32x          | 50,000   | 50,000  | 0         | Entity State transform workload with 100 active entities                               |
| synthetic_entity_state_10k_entities         | 33.40     | 0.32x          | 50,000   | 50,000  | 0         | Entity State transform workload with 10k active entities                               |
| entity_all_no_callback                      | 32.74     | 0.31x          | 50,000   | 50,000  | 0         | Entity State full fixed prefix                                                         |
| entity_pose_callback_every                  | 38.27     | 0.36x          | 50,000   | 50,000  | 0         | pose decode plus callback every packet                                                 |
| entity_pose_downsample_1pct_cb              | 40.51     | 0.39x          | 50,000   | 500     | 0         | pose decode; callback every 100th packet                                               |
| entity_force_filter_25pct                   | 42.40     | 0.40x          | 12,500   | 12,500  | 0         | native force-id filter; force==1                                                       |
| filtered_force_ids                          | 42.48     | 0.40x          | 12,500   | 12,500  | 0         | Alpha 2 named force-ID filter workload                                                 |
| scanner_reuse_pose_no_callback              | 41.49     | 0.39x          | 50,000   | 50,000  | 0         | opaque scanner context reused across rounds                                            |
| scanner_entity_id_allow_32                  | 45.12     | 0.43x          | 1,568    | 1,568   | 0         | native unordered_set allowlist: 32 of 1024 entity IDs                                  |
| entity_allowlist_32                         | 45.11     | 0.43x          | 1,568    | 1,568   | 0         | Alpha 2 named entity allowlist workload with 32 IDs                                    |
| entity_allowlist_1024                       | 45.58     | 0.43x          | 50,000   | 50,000  | 0         | Alpha 2 named entity allowlist workload with 1024 IDs                                  |
| entity_pose_to_batch                        | 45.17     | 0.43x          | 50,000   | 50,000  | 0         | callback-free Entity State pose decode into caller-owned array                         |
| entity_transform_to_batch                   | 45.00     | 0.43x          | 50,000   | 50,000  | 0         | callback-free compact engine transform output                                          |
| entity_transform_to_batch_50pct_capacity    | 47.19     | 0.45x          | 50,000   | 50,000  | 0         | compact transform output with undersized output buffer                                 |
| scanner_transform_to_batch_allow_32         | 48.23     | 0.46x          | 1,568    | 1,568   | 0         | scanner allowlist plus callback-free compact transform output                          |
| entity_table_ingest_latest                  | 37.49     | 0.36x          | 50,000   | 50,000  | 0         | scan transforms directly into native latest-state entity table                         |
| entity_snapshot_publish_changed_dirty       | 253.40    | 2.41x          | 1,024    | 1,024   | 0         | publish already-dirty changed snapshots into double buffer; no packet scan             |
| snapshot_publish_changed                    | 273.07    | 2.60x          | 1,024    | 1,024   | 0         | Alpha 2 named changed-snapshot publish workload                                        |
| entity_snapshot_publish_all                 | 273.07    | 2.60x          | 1,024    | 1,024   | 0         | publish all latest-state snapshots into double buffer; no packet scan                  |
| snapshot_publish_all                        | 273.07    | 2.60x          | 1,024    | 1,024   | 0         | Alpha 2 named publish-all snapshot workload                                            |
| snapshot_acquire_release                    | 273.07    | 2.60x          | 1,024    | 1,024   | 0         | publish changed snapshots, then acquire/release latest view without rescanning packets |
| snapshot_delayed_reader_double              | 127.33    | 1.21x          | 1,024    | 1,024   | 0         | double-slot buffer under delayed reader pressure                                       |
| snapshot_delayed_reader_triple              | 124.12    | 1.18x          | 1,024    | 1,024   | 0         | triple-slot buffer under delayed reader pressure                                       |
| entity_table_ingest_publish_changed         | 38.21     | 0.36x          | 50,000   | 50,000  | 0         | ingest latest-state table, then publish changed snapshots into double buffer           |
| entity_table_ingest_publish_acquire_release | 38.16     | 0.36x          | 50,000   | 50,000  | 0         | ingest, publish changed snapshots, acquire/release latest view                         |
| entity_table_ingest_publish_combined        | 38.15     | 0.36x          | 50,000   | 50,000  | 0         | single ABI call: ingest latest-state table and publish changed double-buffer snapshot  |
| frame_transform_off                         | 1365.33   | 12.99x         | 1,024    | 1,024   | 0         | snapshot walk without frame conversion                                                 |
| frame_transform_on                          | 599.53    | 5.70x          | 1,024    | 1,024   | 0         | snapshot walk with ENU-to-Unreal pose conversion                                       |

### Native readout

- Header callback-every-packet throughput vs header-only: `0.92x`.
- Header downsample-before-callback throughput vs callback-every-packet: `1.14x`.
- Entity pose-only decode vs full fixed-prefix decode: `0.91x`.
- Reused scanner pose decode vs one-shot pose decode: `1.39x`.
- Native entity-ID allowlist throughput vs routing-only decode: `1.60x`.
- Callback-free pose batch throughput vs pose callback-every-packet: `1.18x`.
- Compact transform batch throughput vs pose batch throughput: `1.00x`.
- Entity-table ingest + changed publish vs ingest-only: `1.02x`.
- Combined ingest+publish ABI call vs separate ingest+publish: `1.00x`.
- Publish-all snapshot buffer vs publish-changed dirty snapshot buffer: `1.08x`.
- Triple-slot delayed reader vs double-slot delayed reader: `0.97x`.
- Frame transform on vs frame transform off: `0.44x`.

## Python ctypes benchmark

ABI: `8`; library version: `0.12.0-alpha2`.

| case                                       | Mpps  | vs ctypes header-only | accepted | emitted | callbacks | notes                                                                                          |
| ------------------------------------------ | ----- | --------------------- | -------- | ------- | --------- | ---------------------------------------------------------------------------------------------- |
| ctypes_header_no_callback                  | 0.223 | 1.00x                 | 10,000   | 10,000  | 0         | includes packet-view setup + one ctypes scan call                                              |
| ctypes_header_callback_every_packet        | 0.153 | 0.69x                 | 10,000   | 10,000  | 10,000    | Python callback for every accepted packet                                                      |
| ctypes_header_callback_sample_100          | 0.154 | 0.69x                 | 10,000   | 100     | 100       | downsample in C before Python callback                                                         |
| ctypes_entity_pose_no_callback             | 0.228 | 1.02x                 | 10,000   | 10,000  | 0         | Entity State pose-only decode through ctypes wrapper                                           |
| ctypes_entity_all_no_callback              | 0.223 | 1.00x                 | 10,000   | 10,000  | 0         | Entity State full fixed-prefix decode through ctypes wrapper                                   |
| ctypes_entity_pose_to_batch                | 0.090 | 0.40x                 | 10,000   | 10,000  | 0         | callback-free native batch, then Python value conversion                                       |
| ctypes_entity_transform_to_batch           | 0.117 | 0.53x                 | 10,000   | 10,000  | 0         | compact transform batch output, then Python value conversion                                   |
| ctypes_entity_force_reject_no_callback     | 0.219 | 0.99x                 | 0        | 0       | 0         | C-side force-ID filter rejects all after minimal decode                                        |
| ctypes_scanner_entity_id_allow_one         | 0.206 | 0.93x                 | 10       | 10      | 0         | reusable scanner + native entity-ID allowlist                                                  |
| ctypes_scanner_transform_batch_allow_one   | 0.211 | 0.95x                 | 10       | 10      | 0         | reusable scanner + entity allowlist + compact transform batch                                  |
| ctypes_entity_table_ingest_latest          | 0.204 | 0.92x                 | 10,000   | 10,000  | 0         | ctypes wrapper updates native latest-state table                                               |
| ctypes_entity_table_ingest_publish_changed | 0.179 | 0.80x                 | 10,000   | 10,000  | 0         | ingest native latest-state table, publish changed snapshots into reusable native double buffer |
| ctypes_snapshot_acquire_copy_release       | 0.146 | 0.66x                 | 10,000   | 10,000  | 0         | publish changed snapshots, acquire latest view, copy to Python tuple, release                  |
| ctypes_ingest_publish_changed_combined     | 0.160 | 0.72x                 | 10,000   | 10,000  | 0         | single ctypes ABI call: ingest table and publish changed snapshot buffer                       |
| ctypes_scanner_chained_filters_callback    | 0.184 | 0.83x                 | 5,000    | 50      | 50        | chained filter API: force IDs [1,2] + sample 1/100 + Python callback                           |

### ctypes readout

- Python callback-every-packet throughput vs ctypes header-only: `0.69x`.
- C-side downsample before Python callback vs callback-every-packet: `1.00x`.
- ctypes pose-only Entity State decode vs full fixed-prefix decode: `1.02x`.
- chained filters + downsample callback vs callback-every-packet: `1.20x`.
- ctypes transform batch vs ctypes pose callback-free scan: `0.51x`.
- ctypes table ingest + snapshot-buffer publish vs table ingest-only: `0.88x`.
- ctypes combined ingest+publish vs separate ingest+publish: `0.90x`.

## Practical conclusions to look for

- If callback-every-packet is much slower than no-callback scanning, move more filtering/downsampling into C before the callback.
- If pose-only and full-prefix Entity State decode are close, memory/cache effects may dominate and field masks matter less for your traffic.
- If ctypes is far slower than native, that is expected; Unreal/Godot should call the DLL directly, while Python should batch large packet groups.
- If combined ingest+publish is not meaningfully faster than separate calls, keep the separate calls for clearer engine integration unless your FFI boundary is expensive.
- If entity-ID allowlists are costly at large set sizes, the next optimization is a sorted/vectorized set or fixed-domain bitmap for known site/application pairs.

