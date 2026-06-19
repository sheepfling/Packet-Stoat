# fastdis benchmark report

This report compares the major choices in the fast path: header-only scanning, callbacks, early rejection, downsampling, Entity State field subscriptions, callback-free batch output, compact transform output, reusable scanners, and native allow/block filters, latest-state tables, and double-buffer snapshot publication.

> Results are machine- and build-dependent. Use the ratios to decide what to benchmark in your target engine/runtime, not as universal throughput guarantees.

## Native shared-library benchmark

ABI: `8`; library version: `0.11.0`.

| case                                        | best Mpps | vs header-only | accepted | emitted | malformed | notes                                                                                  |
| ------------------------------------------- | --------- | -------------- | -------- | ------- | --------- | -------------------------------------------------------------------------------------- |
| header_all_no_callback                      | 180.15    | 1.00x          | 50,000   | 50,000  | 0         | 12-byte header only; no Python/engine callback                                         |
| synthetic_header_only                       | 112.22    | 0.62x          | 50,000   | 50,000  | 0         | Alpha 2 synthetic header-only baseline                                                 |
| header_all_callback_every                   | 156.39    | 0.87x          | 50,000   | 50,000  | 0         | header callback on every valid packet                                                  |
| header_filter_90pct_reject                  | 193.86    | 1.08x          | 5,000    | 5,000   | 0         | version/exercise/type/family filter; 10% accepted                                      |
| mixed_pdu_noise                             | 146.90    | 0.82x          | 5,000    | 5,000   | 0         | Alpha 2 mixed-PDU noise workload with 10% accepted entity traffic                      |
| header_filter_90pct_reject_cb               | 191.63    | 1.06x          | 5,000    | 5,000   | 0         | same filter; callback only for accepted 10%                                            |
| header_downsample_1pct_cb                   | 162.34    | 0.90x          | 50,000   | 500     | 0         | all accepted; callback every 100th packet                                              |
| header_10pct_malformed                      | 194.96    | 1.08x          | 45,000   | 45,000  | 5,000     | short packets counted as malformed                                                     |
| entity_routing_no_callback                  | 27.56     | 0.15x          | 50,000   | 50,000  | 0         | Entity State fixed prefix: id + force only                                             |
| entity_pose_no_callback                     | 27.00     | 0.15x          | 50,000   | 50,000  | 0         | Entity State id + force + location + orientation                                       |
| synthetic_entity_state_1_entity             | 29.71     | 0.16x          | 50,000   | 50,000  | 0         | Entity State transform workload with one hot entity                                    |
| synthetic_entity_state_100_entities         | 29.74     | 0.17x          | 50,000   | 50,000  | 0         | Entity State transform workload with 100 active entities                               |
| synthetic_entity_state_10k_entities         | 33.34     | 0.19x          | 50,000   | 50,000  | 0         | Entity State transform workload with 10k active entities                               |
| entity_all_no_callback                      | 32.88     | 0.18x          | 50,000   | 50,000  | 0         | Entity State full fixed prefix                                                         |
| entity_pose_callback_every                  | 35.38     | 0.20x          | 50,000   | 50,000  | 0         | pose decode plus callback every packet                                                 |
| entity_pose_downsample_1pct_cb              | 40.60     | 0.23x          | 50,000   | 500     | 0         | pose decode; callback every 100th packet                                               |
| entity_force_filter_25pct                   | 39.62     | 0.22x          | 12,500   | 12,500  | 0         | native force-id filter; force==1                                                       |
| filtered_force_ids                          | 42.57     | 0.24x          | 12,500   | 12,500  | 0         | Alpha 2 named force-ID filter workload                                                 |
| scanner_reuse_pose_no_callback              | 41.39     | 0.23x          | 50,000   | 50,000  | 0         | opaque scanner context reused across rounds                                            |
| scanner_entity_id_allow_32                  | 41.68     | 0.23x          | 1,568    | 1,568   | 0         | native unordered_set allowlist: 32 of 1024 entity IDs                                  |
| entity_allowlist_32                         | 45.18     | 0.25x          | 1,568    | 1,568   | 0         | Alpha 2 named entity allowlist workload with 32 IDs                                    |
| entity_allowlist_1024                       | 45.80     | 0.25x          | 50,000   | 50,000  | 0         | Alpha 2 named entity allowlist workload with 1024 IDs                                  |
| entity_pose_to_batch                        | 45.13     | 0.25x          | 50,000   | 50,000  | 0         | callback-free Entity State pose decode into caller-owned array                         |
| entity_transform_to_batch                   | 43.34     | 0.24x          | 50,000   | 50,000  | 0         | callback-free compact engine transform output                                          |
| entity_transform_to_batch_50pct_capacity    | 47.31     | 0.26x          | 50,000   | 50,000  | 0         | compact transform output with undersized output buffer                                 |
| scanner_transform_to_batch_allow_32         | 47.64     | 0.26x          | 1,568    | 1,568   | 0         | scanner allowlist plus callback-free compact transform output                          |
| entity_table_ingest_latest                  | 37.71     | 0.21x          | 50,000   | 50,000  | 0         | scan transforms directly into native latest-state entity table                         |
| entity_snapshot_publish_changed_dirty       | 276.16    | 1.53x          | 1,024    | 1,024   | 0         | publish already-dirty changed snapshots into double buffer; no packet scan             |
| snapshot_publish_changed                    | 279.25    | 1.55x          | 1,024    | 1,024   | 0         | Alpha 2 named changed-snapshot publish workload                                        |
| entity_snapshot_publish_all                 | 279.25    | 1.55x          | 1,024    | 1,024   | 0         | publish all latest-state snapshots into double buffer; no packet scan                  |
| snapshot_publish_all                        | 279.25    | 1.55x          | 1,024    | 1,024   | 0         | Alpha 2 named publish-all snapshot workload                                            |
| snapshot_acquire_release                    | 276.16    | 1.53x          | 1,024    | 1,024   | 0         | publish changed snapshots, then acquire/release latest view without rescanning packets |
| snapshot_delayed_reader_double              | 138.06    | 0.77x          | 1,024    | 1,024   | 0         | double-slot buffer under delayed reader pressure                                       |
| snapshot_delayed_reader_triple              | 138.06    | 0.77x          | 1,024    | 1,024   | 0         | triple-slot buffer under delayed reader pressure                                       |
| entity_table_ingest_publish_changed         | 37.59     | 0.21x          | 50,000   | 50,000  | 0         | ingest latest-state table, then publish changed snapshots into double buffer           |
| entity_table_ingest_publish_acquire_release | 38.34     | 0.21x          | 50,000   | 50,000  | 0         | ingest, publish changed snapshots, acquire/release latest view                         |
| entity_table_ingest_publish_combined        | 38.37     | 0.21x          | 50,000   | 50,000  | 0         | single ABI call: ingest latest-state table and publish changed double-buffer snapshot  |
| frame_transform_off                         | 1365.33   | 7.58x          | 1,024    | 1,024   | 0         | snapshot walk without frame conversion                                                 |
| frame_transform_on                          | 585.14    | 3.25x          | 1,024    | 1,024   | 0         | snapshot walk with ENU-to-Unreal pose conversion                                       |

### Native readout

- Header callback-every-packet throughput vs header-only: `0.87x`.
- Header downsample-before-callback throughput vs callback-every-packet: `1.04x`.
- Entity pose-only decode vs full fixed-prefix decode: `0.82x`.
- Reused scanner pose decode vs one-shot pose decode: `1.53x`.
- Native entity-ID allowlist throughput vs routing-only decode: `1.51x`.
- Callback-free pose batch throughput vs pose callback-every-packet: `1.28x`.
- Compact transform batch throughput vs pose batch throughput: `0.96x`.
- Entity-table ingest + changed publish vs ingest-only: `1.00x`.
- Combined ingest+publish ABI call vs separate ingest+publish: `1.02x`.
- Publish-all snapshot buffer vs publish-changed dirty snapshot buffer: `1.01x`.
- Triple-slot delayed reader vs double-slot delayed reader: `1.00x`.
- Frame transform on vs frame transform off: `0.43x`.

## Python ctypes benchmark

ABI: `8`; library version: `0.11.0`.

| case                                       | Mpps  | vs ctypes header-only | accepted | emitted | callbacks | notes                                                                                          |
| ------------------------------------------ | ----- | --------------------- | -------- | ------- | --------- | ---------------------------------------------------------------------------------------------- |
| ctypes_header_no_callback                  | 0.272 | 1.00x                 | 10,000   | 10,000  | 0         | includes packet-view setup + one ctypes scan call                                              |
| ctypes_header_callback_every_packet        | 0.164 | 0.60x                 | 10,000   | 10,000  | 10,000    | Python callback for every accepted packet                                                      |
| ctypes_header_callback_sample_100          | 0.189 | 0.69x                 | 10,000   | 100     | 100       | downsample in C before Python callback                                                         |
| ctypes_entity_pose_no_callback             | 0.241 | 0.89x                 | 10,000   | 10,000  | 0         | Entity State pose-only decode through ctypes wrapper                                           |
| ctypes_entity_all_no_callback              | 0.230 | 0.85x                 | 10,000   | 10,000  | 0         | Entity State full fixed-prefix decode through ctypes wrapper                                   |
| ctypes_entity_pose_to_batch                | 0.092 | 0.34x                 | 10,000   | 10,000  | 0         | callback-free native batch, then Python value conversion                                       |
| ctypes_entity_transform_to_batch           | 0.117 | 0.43x                 | 10,000   | 10,000  | 0         | compact transform batch output, then Python value conversion                                   |
| ctypes_entity_force_reject_no_callback     | 0.219 | 0.81x                 | 0        | 0       | 0         | C-side force-ID filter rejects all after minimal decode                                        |
| ctypes_scanner_entity_id_allow_one         | 0.216 | 0.79x                 | 10       | 10      | 0         | reusable scanner + native entity-ID allowlist                                                  |
| ctypes_scanner_transform_batch_allow_one   | 0.209 | 0.77x                 | 10       | 10      | 0         | reusable scanner + entity allowlist + compact transform batch                                  |
| ctypes_entity_table_ingest_latest          | 0.213 | 0.78x                 | 10,000   | 10,000  | 0         | ctypes wrapper updates native latest-state table                                               |
| ctypes_entity_table_ingest_publish_changed | 0.179 | 0.66x                 | 10,000   | 10,000  | 0         | ingest native latest-state table, publish changed snapshots into reusable native double buffer |
| ctypes_snapshot_acquire_copy_release       | 0.177 | 0.65x                 | 10,000   | 10,000  | 0         | publish changed snapshots, acquire latest view, copy to Python tuple, release                  |
| ctypes_ingest_publish_changed_combined     | 0.178 | 0.65x                 | 10,000   | 10,000  | 0         | single ctypes ABI call: ingest table and publish changed snapshot buffer                       |
| ctypes_scanner_chained_filters_callback    | 0.204 | 0.75x                 | 5,000    | 50      | 50        | chained filter API: force IDs [1,2] + sample 1/100 + Python callback                           |

### ctypes readout

- Python callback-every-packet throughput vs ctypes header-only: `0.60x`.
- C-side downsample before Python callback vs callback-every-packet: `1.15x`.
- ctypes pose-only Entity State decode vs full fixed-prefix decode: `1.05x`.
- chained filters + downsample callback vs callback-every-packet: `1.24x`.
- ctypes transform batch vs ctypes pose callback-free scan: `0.48x`.
- ctypes table ingest + snapshot-buffer publish vs table ingest-only: `0.84x`.
- ctypes combined ingest+publish vs separate ingest+publish: `1.00x`.

## Practical conclusions to look for

- If callback-every-packet is much slower than no-callback scanning, move more filtering/downsampling into C before the callback.
- If pose-only and full-prefix Entity State decode are close, memory/cache effects may dominate and field masks matter less for your traffic.
- If ctypes is far slower than native, that is expected; Unreal/Godot should call the DLL directly, while Python should batch large packet groups.
- If combined ingest+publish is not meaningfully faster than separate calls, keep the separate calls for clearer engine integration unless your FFI boundary is expensive.
- If entity-ID allowlists are costly at large set sizes, the next optimization is a sorted/vectorized set or fixed-domain bitmap for known site/application pairs.

