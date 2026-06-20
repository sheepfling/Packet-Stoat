# fastdis benchmark report

This report compares the major choices in the fast path: header-only scanning, callbacks, early rejection, downsampling, Entity State field subscriptions, callback-free batch output, compact transform output, reusable scanners, and native allow/block filters, latest-state tables, snapshot publication, and engine-facing transform conversion.

> Results are machine- and build-dependent. Use the ratios to decide what to benchmark in your target engine/runtime, not as universal throughput guarantees.

## Qualification summary

- Native cases reported: `39`; latency quantiles present: `True`.
- ctypes cases reported: `15`; latency quantiles present: `True`.
- Native hot-path expectation: packet scanning should stay allocation-free once scanners and buffers are created.
- Snapshot/table expectation: runtime cost should be bounded by configured capacities and slot counts rather than hidden growth.
- Python ctypes results intentionally include wrapper overhead; treat them as host-binding qualification rather than the core DLL ceiling.

## Native shared-library benchmark

ABI: `8`; library version: `0.13.0-alpha3`.

| case                                        | best Mpps | avg Mpps | p50 ms | p95 ms | p99 ms | vs header-only | accepted | emitted | malformed | notes                                                                                  |
| ------------------------------------------- | --------- | -------- | ------ | ------ | ------ | -------------- | -------- | ------- | --------- | -------------------------------------------------------------------------------------- |
| header_all_no_callback                      | 68.28     | 68.23    | 0.029  | 0.029  | 0.029  | 1.00x          | 2,000    | 2,000   | 0         | 12-byte header only; no Python/engine callback                                         |
| synthetic_header_only                       | 67.99     | 67.99    | 0.029  | 0.029  | 0.029  | 1.00x          | 2,000    | 2,000   | 0         | Alpha 2 synthetic header-only baseline                                                 |
| header_all_callback_every                   | 62.34     | 62.30    | 0.032  | 0.032  | 0.032  | 0.91x          | 2,000    | 2,000   | 0         | header callback on every valid packet                                                  |
| header_filter_90pct_reject                  | 79.73     | 79.27    | 0.025  | 0.025  | 0.025  | 1.17x          | 200      | 200     | 0         | version/exercise/type/family filter; 10% accepted                                      |
| mixed_pdu_noise                             | 80.00     | 79.74    | 0.025  | 0.025  | 0.025  | 1.17x          | 200      | 200     | 0         | Alpha 2 mixed-PDU noise workload with 10% accepted entity traffic                      |
| header_filter_90pct_reject_cb               | 78.69     | 78.50    | 0.025  | 0.026  | 0.026  | 1.15x          | 200      | 200     | 0         | same filter; callback only for accepted 10%                                            |
| header_downsample_1pct_cb                   | 61.07     | 61.03    | 0.033  | 0.033  | 0.033  | 0.89x          | 2,000    | 20      | 0         | all accepted; callback every 100th packet                                              |
| header_10pct_malformed                      | 69.87     | 69.62    | 0.029  | 0.029  | 0.029  | 1.02x          | 1,800    | 1,800   | 200       | short packets counted as malformed                                                     |
| entity_routing_no_callback                  | 17.82     | 17.77    | 0.113  | 0.113  | 0.113  | 0.26x          | 2,000    | 2,000   | 0         | Entity State fixed prefix: id + force only                                             |
| entity_pose_no_callback                     | 17.52     | 17.48    | 0.114  | 0.115  | 0.115  | 0.26x          | 2,000    | 2,000   | 0         | Entity State id + force + location + orientation                                       |
| synthetic_entity_state_1_entity             | 17.54     | 17.53    | 0.114  | 0.114  | 0.114  | 0.26x          | 2,000    | 2,000   | 0         | Entity State transform workload with one hot entity                                    |
| synthetic_entity_state_100_entities         | 17.54     | 17.53    | 0.114  | 0.114  | 0.114  | 0.26x          | 2,000    | 2,000   | 0         | Entity State transform workload with 100 active entities                               |
| synthetic_entity_state_10k_entities         | 17.52     | 17.52    | 0.114  | 0.114  | 0.114  | 0.26x          | 2,000    | 2,000   | 0         | Entity State transform workload with 10k active entities                               |
| entity_all_no_callback                      | 14.98     | 14.97    | 0.134  | 0.134  | 0.134  | 0.22x          | 2,000    | 2,000   | 0         | Entity State full fixed prefix                                                         |
| entity_pose_callback_every                  | 16.78     | 16.78    | 0.119  | 0.119  | 0.119  | 0.25x          | 2,000    | 2,000   | 0         | pose decode plus callback every packet                                                 |
| entity_pose_downsample_1pct_cb              | 17.75     | 17.74    | 0.113  | 0.113  | 0.113  | 0.26x          | 2,000    | 20      | 0         | pose decode; callback every 100th packet                                               |
| entity_force_filter_25pct                   | 17.43     | 16.32    | 0.123  | 0.130  | 0.130  | 0.26x          | 500      | 500     | 0         | native force-id filter; force==1                                                       |
| filtered_force_ids                          | 17.11     | 15.67    | 0.128  | 0.137  | 0.138  | 0.25x          | 500      | 500     | 0         | Alpha 2 named force-ID filter workload                                                 |
| scanner_reuse_pose_no_callback              | 17.06     | 16.95    | 0.118  | 0.119  | 0.119  | 0.25x          | 2,000    | 2,000   | 0         | opaque scanner context reused across rounds                                            |
| scanner_entity_id_allow_32                  | 16.44     | 16.44    | 0.122  | 0.122  | 0.122  | 0.24x          | 64       | 64      | 0         | native unordered_set allowlist: 32 of 1024 entity IDs                                  |
| entity_allowlist_32                         | 16.23     | 14.14    | 0.141  | 0.158  | 0.159  | 0.24x          | 64       | 64      | 0         | Alpha 2 named entity allowlist workload with 32 IDs                                    |
| entity_allowlist_1024                       | 16.46     | 16.44    | 0.122  | 0.122  | 0.122  | 0.24x          | 2,000    | 2,000   | 0         | Alpha 2 named entity allowlist workload with 1024 IDs                                  |
| entity_pose_to_batch                        | 16.97     | 16.92    | 0.118  | 0.119  | 0.119  | 0.25x          | 2,000    | 2,000   | 0         | callback-free Entity State pose decode into caller-owned array                         |
| entity_transform_to_batch                   | 16.36     | 16.33    | 0.122  | 0.123  | 0.123  | 0.24x          | 2,000    | 2,000   | 0         | callback-free compact engine transform output                                          |
| entity_transform_to_batch_50pct_capacity    | 17.09     | 17.08    | 0.117  | 0.117  | 0.117  | 0.25x          | 2,000    | 2,000   | 0         | compact transform output with undersized output buffer                                 |
| scanner_transform_to_batch_allow_32         | 17.14     | 17.13    | 0.117  | 0.117  | 0.117  | 0.25x          | 64       | 64      | 0         | scanner allowlist plus callback-free compact transform output                          |
| entity_table_ingest_latest                  | 12.90     | 12.89    | 0.155  | 0.155  | 0.155  | 0.19x          | 2,000    | 2,000   | 0         | scan transforms directly into native latest-state entity table                         |
| entity_snapshot_publish_changed_dirty       | 130.73    | 129.35   | 0.008  | 0.008  | 0.008  | 1.91x          | 1,024    | 1,024   | 0         | publish already-dirty changed snapshots into double buffer; no packet scan             |
| snapshot_publish_changed                    | 132.13    | 131.43   | 0.008  | 0.008  | 0.008  | 1.94x          | 1,024    | 1,024   | 0         | Alpha 2 named changed-snapshot publish workload                                        |
| entity_snapshot_publish_all                 | 131.42    | 131.06   | 0.008  | 0.008  | 0.008  | 1.92x          | 1,024    | 1,024   | 0         | publish all latest-state snapshots into double buffer; no packet scan                  |
| snapshot_publish_all                        | 132.13    | 131.78   | 0.008  | 0.008  | 0.008  | 1.94x          | 1,024    | 1,024   | 0         | Alpha 2 named publish-all snapshot workload                                            |
| snapshot_acquire_release                    | 131.42    | 130.72   | 0.008  | 0.008  | 0.008  | 1.92x          | 1,024    | 1,024   | 0         | publish changed snapshots, then acquire/release latest view without rescanning packets |
| snapshot_delayed_reader_double              | 65.89     | 65.71    | 0.016  | 0.016  | 0.016  | 0.96x          | 1,024    | 1,024   | 0         | double-slot buffer under delayed reader pressure                                       |
| snapshot_delayed_reader_triple              | 65.36     | 62.85    | 0.016  | 0.017  | 0.017  | 0.96x          | 1,024    | 1,024   | 0         | triple-slot buffer under delayed reader pressure                                       |
| entity_table_ingest_publish_changed         | 12.31     | 12.25    | 0.163  | 0.164  | 0.164  | 0.18x          | 2,000    | 2,000   | 0         | ingest latest-state table, then publish changed snapshots into double buffer           |
| entity_table_ingest_publish_acquire_release | 12.42     | 12.40    | 0.161  | 0.161  | 0.161  | 0.18x          | 2,000    | 2,000   | 0         | ingest, publish changed snapshots, acquire/release latest view                         |
| entity_table_ingest_publish_combined        | 11.99     | 11.98    | 0.167  | 0.167  | 0.167  | 0.18x          | 2,000    | 2,000   | 0         | single ABI call: ingest latest-state table and publish changed double-buffer snapshot  |
| frame_transform_off                         | 258.65    | 257.32   | 0.004  | 0.004  | 0.004  | 3.79x          | 1,024    | 1,024   | 0         | snapshot walk without frame conversion                                                 |
| frame_transform_on                          | 132.83    | 132.12   | 0.008  | 0.008  | 0.008  | 1.95x          | 1,024    | 1,024   | 0         | snapshot walk with ENU-to-Unreal pose conversion                                       |

### Native readout

- Header callback-every-packet throughput vs header-only: `0.91x`.
- Header downsample-before-callback throughput vs callback-every-packet: `0.98x`.
- Entity pose-only decode vs full fixed-prefix decode: `1.17x`.
- Reused scanner pose decode vs one-shot pose decode: `0.97x`.
- Native entity-ID allowlist throughput vs routing-only decode: `0.92x`.
- Callback-free pose batch throughput vs pose callback-every-packet: `1.01x`.
- Compact transform batch throughput vs pose batch throughput: `0.96x`.
- Entity-table ingest + changed publish vs ingest-only: `0.95x`.
- Combined ingest+publish ABI call vs separate ingest+publish: `0.97x`.
- Publish-all snapshot buffer vs publish-changed dirty snapshot buffer: `1.01x`.
- Triple-slot delayed reader vs double-slot delayed reader: `0.99x`.
- Frame transform on vs frame transform off: `0.51x`.

## Python ctypes benchmark

ABI: `8`; library version: `0.13.0-alpha3`.

| case                                       | best Mpps | avg Mpps | p50 ms | p95 ms | p99 ms | vs ctypes header-only | accepted | emitted | callbacks | notes                                                                                          |
| ------------------------------------------ | --------- | -------- | ------ | ------ | ------ | --------------------- | -------- | ------- | --------- | ---------------------------------------------------------------------------------------------- |
| ctypes_header_no_callback                  | 0.275     | 0.202    | 2.471  | 3.060  | 3.113  | 1.00x                 | 1,000    | 1,000   | 0         | includes packet-view setup + one ctypes scan call                                              |
| ctypes_header_callback_every_packet        | 0.191     | 0.174    | 2.877  | 3.106  | 3.127  | 0.69x                 | 1,000    | 1,000   | 1,000     | Python callback for every accepted packet                                                      |
| ctypes_header_callback_sample_100          | 0.250     | 0.160    | 3.124  | 4.135  | 4.225  | 0.91x                 | 1,000    | 10      | 10        | downsample in C before Python callback                                                         |
| ctypes_entity_pose_no_callback             | 0.273     | 0.199    | 2.510  | 3.119  | 3.173  | 0.99x                 | 1,000    | 1,000   | 0         | Entity State pose-only decode through ctypes wrapper                                           |
| ctypes_entity_all_no_callback              | 0.260     | 0.195    | 2.559  | 3.130  | 3.181  | 0.94x                 | 1,000    | 1,000   | 0         | Entity State full fixed-prefix decode through ctypes wrapper                                   |
| ctypes_entity_pose_to_batch                | 0.098     | 0.043    | 11.718 | 17.673 | 18.202 | 0.36x                 | 1,000    | 1,000   | 0         | callback-free native batch, then Python value conversion                                       |
| ctypes_entity_transform_to_batch           | 0.171     | 0.154    | 3.256  | 3.561  | 3.588  | 0.62x                 | 1,000    | 1,000   | 0         | compact transform batch output, then Python value conversion                                   |
| ctypes_entity_force_reject_no_callback     | 0.108     | 0.092    | 5.415  | 6.132  | 6.195  | 0.39x                 | 0        | 0       | 0         | C-side force-ID filter rejects all after minimal decode                                        |
| ctypes_scanner_entity_id_allow_one         | 0.285     | 0.226    | 2.216  | 2.630  | 2.667  | 1.03x                 | 2        | 2       | 0         | reusable scanner + native entity-ID allowlist                                                  |
| ctypes_scanner_transform_batch_allow_one   | 0.119     | 0.090    | 5.540  | 6.744  | 6.852  | 0.43x                 | 2        | 2       | 0         | reusable scanner + entity allowlist + compact transform batch                                  |
| ctypes_entity_table_ingest_latest          | 0.268     | 0.206    | 2.424  | 2.924  | 2.968  | 0.97x                 | 1,000    | 1,000   | 0         | ctypes wrapper updates native latest-state table                                               |
| ctypes_entity_table_ingest_publish_changed | 0.275     | 0.226    | 2.213  | 2.570  | 2.602  | 1.00x                 | 1,000    | 1,000   | 0         | ingest native latest-state table, publish changed snapshots into reusable native double buffer |
| ctypes_snapshot_acquire_copy_release       | 0.284     | 0.117    | 4.266  | 6.520  | 6.720  | 1.03x                 | 1,000    | 1,000   | 0         | publish changed snapshots, acquire latest view, copy to Python tuple, release                  |
| ctypes_ingest_publish_changed_combined     | 0.287     | 0.231    | 2.161  | 2.536  | 2.569  | 1.04x                 | 1,000    | 1,000   | 0         | single ctypes ABI call: ingest table and publish changed snapshot buffer                       |
| ctypes_scanner_chained_filters_callback    | 0.286     | 0.229    | 2.179  | 2.564  | 2.598  | 1.04x                 | 500      | 6       | 6         | chained filter API: force IDs [1,2] + sample 1/100 + Python callback                           |

### ctypes readout

- Python callback-every-packet throughput vs ctypes header-only: `0.69x`.
- C-side downsample before Python callback vs callback-every-packet: `1.31x`.
- ctypes pose-only Entity State decode vs full fixed-prefix decode: `1.05x`.
- chained filters + downsample callback vs callback-every-packet: `1.50x`.
- ctypes transform batch vs ctypes pose callback-free scan: `0.63x`.
- ctypes table ingest + snapshot-buffer publish vs table ingest-only: `1.03x`.
- ctypes combined ingest+publish vs separate ingest+publish: `1.04x`.

## Allocation expectations

- `native header/entity scan cases`: Hot-path scanning should remain allocation-free after packet buffers, config, and scanners are constructed.
- `native batch output and frame-transform cases`: Output uses caller-owned or pre-sized native buffers; overflow should be reported without heap growth in the scan loop.
- `entity table and snapshot publication`: Allocation is bounded by create-time capacity and snapshot slot count; publish/acquire/release should not resize at runtime.
- `Python ctypes cases`: Python-facing runs include wrapper and conversion overhead, so they are interoperability measurements rather than pure hot-path allocation proofs.

## Practical conclusions to look for

- If callback-every-packet is much slower than no-callback scanning, move more filtering/downsampling into C before the callback.
- If pose-only and full-prefix Entity State decode are close, memory/cache effects may dominate and field masks matter less for your traffic.
- If ctypes is far slower than native, that is expected; Unreal/Godot should call the DLL directly, while Python should batch large packet groups.
- If combined ingest+publish is not meaningfully faster than separate calls, keep the separate calls for clearer engine integration unless your FFI boundary is expensive.
- If entity-ID allowlists are costly at large set sizes, the next optimization is a sorted/vectorized set or fixed-domain bitmap for known site/application pairs.

