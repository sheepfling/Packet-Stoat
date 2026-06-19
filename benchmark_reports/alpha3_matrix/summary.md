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
| header_all_no_callback                      | 208.52    | 208.48   | 0.096  | 0.096  | 0.096  | 1.00x          | 20,000   | 20,000  | 0         | 12-byte header only; no Python/engine callback                                         |
| synthetic_header_only                       | 207.88    | 207.19   | 0.097  | 0.097  | 0.097  | 1.00x          | 20,000   | 20,000  | 0         | Alpha 2 synthetic header-only baseline                                                 |
| header_all_callback_every                   | 179.98    | 171.04   | 0.120  | 0.120  | 0.120  | 0.86x          | 20,000   | 20,000  | 0         | header callback on every valid packet                                                  |
| header_filter_90pct_reject                  | 202.79    | 202.30   | 0.099  | 0.099  | 0.099  | 0.97x          | 2,000    | 2,000   | 0         | version/exercise/type/family filter; 10% accepted                                      |
| mixed_pdu_noise                             | 203.13    | 202.79   | 0.099  | 0.099  | 0.099  | 0.97x          | 2,000    | 2,000   | 0         | Alpha 2 mixed-PDU noise workload with 10% accepted entity traffic                      |
| header_filter_90pct_reject_cb               | 199.42    | 199.09   | 0.101  | 0.101  | 0.101  | 0.96x          | 2,000    | 2,000   | 0         | same filter; callback only for accepted 10%                                            |
| header_downsample_1pct_cb                   | 167.01    | 166.55   | 0.120  | 0.120  | 0.120  | 0.80x          | 20,000   | 200     | 0         | all accepted; callback every 100th packet                                              |
| header_10pct_malformed                      | 204.08    | 203.42   | 0.098  | 0.099  | 0.099  | 0.98x          | 18,000   | 18,000  | 2,000     | short packets counted as malformed                                                     |
| entity_routing_no_callback                  | 39.05     | 38.97    | 0.512  | 0.515  | 0.515  | 0.19x          | 20,000   | 20,000  | 0         | Entity State fixed prefix: id + force only                                             |
| entity_pose_no_callback                     | 39.73     | 38.75    | 0.509  | 0.533  | 0.536  | 0.19x          | 20,000   | 20,000  | 0         | Entity State id + force + location + orientation                                       |
| synthetic_entity_state_1_entity             | 39.81     | 39.79    | 0.503  | 0.503  | 0.503  | 0.19x          | 20,000   | 20,000  | 0         | Entity State transform workload with one hot entity                                    |
| synthetic_entity_state_100_entities         | 39.81     | 39.36    | 0.504  | 0.517  | 0.518  | 0.19x          | 20,000   | 20,000  | 0         | Entity State transform workload with 100 active entities                               |
| synthetic_entity_state_10k_entities         | 39.83     | 39.80    | 0.502  | 0.503  | 0.503  | 0.19x          | 20,000   | 20,000  | 0         | Entity State transform workload with 10k active entities                               |
| entity_all_no_callback                      | 35.66     | 34.81    | 0.562  | 0.597  | 0.600  | 0.17x          | 20,000   | 20,000  | 0         | Entity State full fixed prefix                                                         |
| entity_pose_callback_every                  | 35.62     | 35.24    | 0.563  | 0.577  | 0.578  | 0.17x          | 20,000   | 20,000  | 0         | pose decode plus callback every packet                                                 |
| entity_pose_downsample_1pct_cb              | 37.65     | 37.21    | 0.532  | 0.548  | 0.549  | 0.18x          | 20,000   | 200     | 0         | pose decode; callback every 100th packet                                               |
| entity_force_filter_25pct                   | 34.32     | 32.81    | 0.598  | 0.643  | 0.647  | 0.16x          | 5,000    | 5,000   | 0         | native force-id filter; force==1                                                       |
| filtered_force_ids                          | 36.29     | 36.16    | 0.553  | 0.554  | 0.555  | 0.17x          | 5,000    | 5,000   | 0         | Alpha 2 named force-ID filter workload                                                 |
| scanner_reuse_pose_no_callback              | 36.06     | 35.70    | 0.556  | 0.569  | 0.570  | 0.17x          | 20,000   | 20,000  | 0         | opaque scanner context reused across rounds                                            |
| scanner_entity_id_allow_32                  | 36.01     | 35.53    | 0.557  | 0.574  | 0.576  | 0.17x          | 640      | 640     | 0         | native unordered_set allowlist: 32 of 1024 entity IDs                                  |
| entity_allowlist_32                         | 38.59     | 22.60    | 0.953  | 1.160  | 1.179  | 0.19x          | 640      | 640     | 0         | Alpha 2 named entity allowlist workload with 32 IDs                                    |
| entity_allowlist_1024                       | 39.29     | 38.02    | 0.533  | 0.536  | 0.536  | 0.19x          | 20,000   | 20,000  | 0         | Alpha 2 named entity allowlist workload with 1024 IDs                                  |
| entity_pose_to_batch                        | 35.88     | 34.68    | 0.571  | 0.598  | 0.601  | 0.17x          | 20,000   | 20,000  | 0         | callback-free Entity State pose decode into caller-owned array                         |
| entity_transform_to_batch                   | 34.21     | 33.90    | 0.589  | 0.596  | 0.596  | 0.16x          | 20,000   | 20,000  | 0         | callback-free compact engine transform output                                          |
| entity_transform_to_batch_50pct_capacity    | 36.18     | 35.55    | 0.559  | 0.574  | 0.575  | 0.17x          | 20,000   | 20,000  | 0         | compact transform output with undersized output buffer                                 |
| scanner_transform_to_batch_allow_32         | 36.26     | 35.48    | 0.561  | 0.577  | 0.579  | 0.17x          | 640      | 640     | 0         | scanner allowlist plus callback-free compact transform output                          |
| entity_table_ingest_latest                  | 27.42     | 19.21    | 0.860  | 1.467  | 1.521  | 0.13x          | 20,000   | 20,000  | 0         | scan transforms directly into native latest-state entity table                         |
| entity_snapshot_publish_changed_dirty       | 132.13    | 91.36    | 0.008  | 0.017  | 0.018  | 0.63x          | 1,024    | 1,024   | 0         | publish already-dirty changed snapshots into double buffer; no packet scan             |
| snapshot_publish_changed                    | 132.85    | 131.42   | 0.008  | 0.008  | 0.008  | 0.64x          | 1,024    | 1,024   | 0         | Alpha 2 named changed-snapshot publish workload                                        |
| entity_snapshot_publish_all                 | 130.03    | 129.81   | 0.008  | 0.008  | 0.008  | 0.62x          | 1,024    | 1,024   | 0         | publish all latest-state snapshots into double buffer; no packet scan                  |
| snapshot_publish_all                        | 132.13    | 131.66   | 0.008  | 0.008  | 0.008  | 0.63x          | 1,024    | 1,024   | 0         | Alpha 2 named publish-all snapshot workload                                            |
| snapshot_acquire_release                    | 130.03    | 128.45   | 0.008  | 0.008  | 0.008  | 0.62x          | 1,024    | 1,024   | 0         | publish changed snapshots, then acquire/release latest view without rescanning packets |
| snapshot_delayed_reader_double              | 65.89     | 65.77    | 0.016  | 0.016  | 0.016  | 0.32x          | 1,024    | 1,024   | 0         | double-slot buffer under delayed reader pressure                                       |
| snapshot_delayed_reader_triple              | 64.68     | 53.70    | 0.016  | 0.024  | 0.025  | 0.31x          | 1,024    | 1,024   | 0         | triple-slot buffer under delayed reader pressure                                       |
| entity_table_ingest_publish_changed         | 12.89     | 12.75    | 1.573  | 1.579  | 1.580  | 0.06x          | 20,000   | 20,000  | 0         | ingest latest-state table, then publish changed snapshots into double buffer           |
| entity_table_ingest_publish_acquire_release | 23.82     | 17.99    | 0.919  | 1.511  | 1.563  | 0.11x          | 20,000   | 20,000  | 0         | ingest, publish changed snapshots, acquire/release latest view                         |
| entity_table_ingest_publish_combined        | 12.80     | 12.76    | 1.568  | 1.570  | 1.570  | 0.06x          | 20,000   | 20,000  | 0         | single ABI call: ingest latest-state table and publish changed double-buffer snapshot  |
| frame_transform_off                         | 256.00    | 253.38   | 0.004  | 0.004  | 0.004  | 1.23x          | 1,024    | 1,024   | 0         | snapshot walk without frame conversion                                                 |
| frame_transform_on                          | 131.42    | 130.96   | 0.008  | 0.008  | 0.008  | 0.63x          | 1,024    | 1,024   | 0         | snapshot walk with ENU-to-Unreal pose conversion                                       |

### Native readout

- Header callback-every-packet throughput vs header-only: `0.86x`.
- Header downsample-before-callback throughput vs callback-every-packet: `0.93x`.
- Entity pose-only decode vs full fixed-prefix decode: `1.11x`.
- Reused scanner pose decode vs one-shot pose decode: `0.91x`.
- Native entity-ID allowlist throughput vs routing-only decode: `0.92x`.
- Callback-free pose batch throughput vs pose callback-every-packet: `1.01x`.
- Compact transform batch throughput vs pose batch throughput: `0.95x`.
- Entity-table ingest + changed publish vs ingest-only: `0.47x`.
- Combined ingest+publish ABI call vs separate ingest+publish: `0.99x`.
- Publish-all snapshot buffer vs publish-changed dirty snapshot buffer: `0.98x`.
- Triple-slot delayed reader vs double-slot delayed reader: `0.98x`.
- Frame transform on vs frame transform off: `0.51x`.

## Python ctypes benchmark

ABI: `8`; library version: `0.13.0-alpha3`.

| case                                       | best Mpps | avg Mpps | p50 ms | p95 ms  | p99 ms  | vs ctypes header-only | accepted | emitted | callbacks | notes                                                                                          |
| ------------------------------------------ | --------- | -------- | ------ | ------- | ------- | --------------------- | -------- | ------- | --------- | ---------------------------------------------------------------------------------------------- |
| ctypes_header_no_callback                  | 0.185     | 0.116    | 44.069 | 56.781  | 57.911  | 1.00x                 | 15,000   | 15,000  | 0         | includes packet-view setup + one ctypes scan call                                              |
| ctypes_header_callback_every_packet        | 0.171     | 0.067    | 40.041 | 142.807 | 151.941 | 0.92x                 | 15,000   | 15,000  | 15,000    | Python callback for every accepted packet                                                      |
| ctypes_header_callback_sample_100          | 0.235     | 0.158    | 23.347 | 47.518  | 49.666  | 1.27x                 | 15,000   | 150     | 150       | downsample in C before Python callback                                                         |
| ctypes_entity_pose_no_callback             | 0.199     | 0.138    | 28.959 | 51.894  | 53.933  | 1.08x                 | 15,000   | 15,000  | 0         | Entity State pose-only decode through ctypes wrapper                                           |
| ctypes_entity_all_no_callback              | 0.224     | 0.122    | 35.745 | 61.768  | 64.081  | 1.21x                 | 15,000   | 15,000  | 0         | Entity State full fixed-prefix decode through ctypes wrapper                                   |
| ctypes_entity_pose_to_batch                | 0.073     | 0.069    | 74.338 | 74.982  | 75.040  | 0.39x                 | 15,000   | 15,000  | 0         | callback-free native batch, then Python value conversion                                       |
| ctypes_entity_transform_to_batch           | 0.153     | 0.101    | 50.095 | 64.545  | 65.829  | 0.83x                 | 15,000   | 15,000  | 0         | compact transform batch output, then Python value conversion                                   |
| ctypes_entity_force_reject_no_callback     | 0.243     | 0.138    | 27.896 | 57.192  | 59.797  | 1.31x                 | 0        | 0       | 0         | C-side force-ID filter rejects all after minimal decode                                        |
| ctypes_scanner_entity_id_allow_one         | 0.261     | 0.133    | 20.830 | 67.532  | 71.683  | 1.41x                 | 15       | 15      | 0         | reusable scanner + native entity-ID allowlist                                                  |
| ctypes_scanner_transform_batch_allow_one   | 0.254     | 0.137    | 41.547 | 47.770  | 48.323  | 1.37x                 | 15       | 15      | 0         | reusable scanner + entity allowlist + compact transform batch                                  |
| ctypes_entity_table_ingest_latest          | 0.253     | 0.139    | 42.375 | 45.646  | 45.936  | 1.37x                 | 15,000   | 15,000  | 0         | ctypes wrapper updates native latest-state table                                               |
| ctypes_entity_table_ingest_publish_changed | 0.211     | 0.133    | 43.197 | 45.616  | 45.831  | 1.14x                 | 15,000   | 15,000  | 0         | ingest native latest-state table, publish changed snapshots into reusable native double buffer |
| ctypes_snapshot_acquire_copy_release       | 0.188     | 0.136    | 38.274 | 44.828  | 45.410  | 1.01x                 | 15,000   | 15,000  | 0         | publish changed snapshots, acquire latest view, copy to Python tuple, release                  |
| ctypes_ingest_publish_changed_combined     | 0.220     | 0.167    | 23.239 | 41.826  | 43.479  | 1.19x                 | 15,000   | 15,000  | 0         | single ctypes ABI call: ingest table and publish changed snapshot buffer                       |
| ctypes_scanner_chained_filters_callback    | 0.254     | 0.188    | 19.982 | 38.034  | 39.639  | 1.37x                 | 7,500    | 75      | 75        | chained filter API: force IDs [1,2] + sample 1/100 + Python callback                           |

### ctypes readout

- Python callback-every-packet throughput vs ctypes header-only: `0.92x`.
- C-side downsample before Python callback vs callback-every-packet: `1.37x`.
- ctypes pose-only Entity State decode vs full fixed-prefix decode: `0.89x`.
- chained filters + downsample callback vs callback-every-packet: `1.49x`.
- ctypes transform batch vs ctypes pose callback-free scan: `0.77x`.
- ctypes table ingest + snapshot-buffer publish vs table ingest-only: `0.83x`.
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

