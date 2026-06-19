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

| case                                        | best Mpps | avg Mpps | p50 ms | p95 ms | p99 ms | vs header-only | accepted  | emitted   | malformed | notes                                                                                  |
| ------------------------------------------- | --------- | -------- | ------ | ------ | ------ | -------------- | --------- | --------- | --------- | -------------------------------------------------------------------------------------- |
| header_all_no_callback                      | 55.68     | 52.65    | 19.123 | 20.172 | 20.368 | 1.00x          | 1,000,000 | 1,000,000 | 0         | 12-byte header only; no Python/engine callback                                         |
| synthetic_header_only                       | 51.09     | 48.72    | 20.727 | 21.049 | 21.077 | 0.92x          | 1,000,000 | 1,000,000 | 0         | Alpha 2 synthetic header-only baseline                                                 |
| header_all_callback_every                   | 51.14     | 47.90    | 20.703 | 22.200 | 22.458 | 0.92x          | 1,000,000 | 1,000,000 | 0         | header callback on every valid packet                                                  |
| header_filter_90pct_reject                  | 51.79     | 50.01    | 19.921 | 20.661 | 20.704 | 0.93x          | 100,000   | 100,000   | 0         | version/exercise/type/family filter; 10% accepted                                      |
| mixed_pdu_noise                             | 48.36     | 41.25    | 25.151 | 26.037 | 26.043 | 0.87x          | 100,000   | 100,000   | 0         | Alpha 2 mixed-PDU noise workload with 10% accepted entity traffic                      |
| header_filter_90pct_reject_cb               | 48.31     | 47.66    | 20.925 | 21.250 | 21.277 | 0.87x          | 100,000   | 100,000   | 0         | same filter; callback only for accepted 10%                                            |
| header_downsample_1pct_cb                   | 46.80     | 45.58    | 21.617 | 22.848 | 22.958 | 0.84x          | 1,000,000 | 10,000    | 0         | all accepted; callback every 100th packet                                              |
| header_10pct_malformed                      | 61.29     | 56.14    | 18.000 | 18.714 | 18.834 | 1.10x          | 900,000   | 900,000   | 100,000   | short packets counted as malformed                                                     |
| entity_routing_no_callback                  | 29.50     | 28.37    | 34.700 | 37.148 | 37.353 | 0.53x          | 1,000,000 | 1,000,000 | 0         | Entity State fixed prefix: id + force only                                             |
| entity_pose_no_callback                     | 39.15     | 38.05    | 26.381 | 26.741 | 26.769 | 0.70x          | 1,000,000 | 1,000,000 | 0         | Entity State id + force + location + orientation                                       |
| synthetic_entity_state_1_entity             | 38.17     | 37.76    | 26.522 | 26.841 | 26.899 | 0.69x          | 1,000,000 | 1,000,000 | 0         | Entity State transform workload with one hot entity                                    |
| synthetic_entity_state_100_entities         | 37.83     | 37.77    | 26.496 | 26.499 | 26.499 | 0.68x          | 1,000,000 | 1,000,000 | 0         | Entity State transform workload with 100 active entities                               |
| synthetic_entity_state_10k_entities         | 38.29     | 38.01    | 26.339 | 26.416 | 26.428 | 0.69x          | 1,000,000 | 1,000,000 | 0         | Entity State transform workload with 10k active entities                               |
| entity_all_no_callback                      | 33.95     | 33.33    | 29.817 | 30.827 | 30.930 | 0.61x          | 1,000,000 | 1,000,000 | 0         | Entity State full fixed prefix                                                         |
| entity_pose_callback_every                  | 36.61     | 36.05    | 27.761 | 28.144 | 28.176 | 0.66x          | 1,000,000 | 1,000,000 | 0         | pose decode plus callback every packet                                                 |
| entity_pose_downsample_1pct_cb              | 40.70     | 39.78    | 24.987 | 25.690 | 25.745 | 0.73x          | 1,000,000 | 10,000    | 0         | pose decode; callback every 100th packet                                               |
| entity_force_filter_25pct                   | 28.93     | 28.12    | 35.441 | 36.331 | 36.379 | 0.52x          | 250,000   | 250,000   | 0         | native force-id filter; force==1                                                       |
| filtered_force_ids                          | 29.14     | 28.74    | 34.816 | 35.097 | 35.115 | 0.52x          | 250,000   | 250,000   | 0         | Alpha 2 named force-ID filter workload                                                 |
| scanner_reuse_pose_no_callback              | 38.55     | 37.85    | 26.501 | 26.701 | 26.727 | 0.69x          | 1,000,000 | 1,000,000 | 0         | opaque scanner context reused across rounds                                            |
| scanner_entity_id_allow_32                  | 26.73     | 19.19    | 50.869 | 66.374 | 69.246 | 0.48x          | 31,264    | 31,264    | 0         | native unordered_set allowlist: 32 of 1024 entity IDs                                  |
| entity_allowlist_32                         | 27.16     | 25.86    | 37.372 | 43.167 | 44.315 | 0.49x          | 31,264    | 31,264    | 0         | Alpha 2 named entity allowlist workload with 32 IDs                                    |
| entity_allowlist_1024                       | 29.28     | 28.05    | 35.066 | 37.113 | 37.146 | 0.53x          | 1,000,000 | 1,000,000 | 0         | Alpha 2 named entity allowlist workload with 1024 IDs                                  |
| entity_pose_to_batch                        | 36.79     | 36.32    | 27.250 | 28.462 | 28.700 | 0.66x          | 1,000,000 | 1,000,000 | 0         | callback-free Entity State pose decode into caller-owned array                         |
| entity_transform_to_batch                   | 36.92     | 35.74    | 27.963 | 28.950 | 29.061 | 0.66x          | 1,000,000 | 1,000,000 | 0         | callback-free compact engine transform output                                          |
| entity_transform_to_batch_50pct_capacity    | 36.96     | 34.86    | 28.988 | 29.685 | 29.704 | 0.66x          | 1,000,000 | 1,000,000 | 0         | compact transform output with undersized output buffer                                 |
| scanner_transform_to_batch_allow_32         | 36.97     | 36.91    | 27.090 | 27.150 | 27.155 | 0.66x          | 31,264    | 31,264    | 0         | scanner allowlist plus callback-free compact transform output                          |
| entity_table_ingest_latest                  | 29.53     | 29.05    | 34.689 | 34.707 | 34.709 | 0.53x          | 1,000,000 | 1,000,000 | 0         | scan transforms directly into native latest-state entity table                         |
| entity_snapshot_publish_changed_dirty       | 213.69    | 208.98   | 0.005  | 0.005  | 0.005  | 3.84x          | 1,024     | 1,024     | 0         | publish already-dirty changed snapshots into double buffer; no packet scan             |
| snapshot_publish_changed                    | 215.58    | 213.33   | 0.005  | 0.005  | 0.005  | 3.87x          | 1,024     | 1,024     | 0         | Alpha 2 named changed-snapshot publish workload                                        |
| entity_snapshot_publish_all                 | 215.58    | 212.22   | 0.005  | 0.005  | 0.005  | 3.87x          | 1,024     | 1,024     | 0         | publish all latest-state snapshots into double buffer; no packet scan                  |
| snapshot_publish_all                        | 213.73    | 212.24   | 0.005  | 0.005  | 0.005  | 3.84x          | 1,024     | 1,024     | 0         | Alpha 2 named publish-all snapshot workload                                            |
| snapshot_acquire_release                    | 215.58    | 210.41   | 0.005  | 0.005  | 0.005  | 3.87x          | 1,024     | 1,024     | 0         | publish changed snapshots, then acquire/release latest view without rescanning packets |
| snapshot_delayed_reader_double              | 107.32    | 105.84   | 0.010  | 0.010  | 0.010  | 1.93x          | 1,024     | 1,024     | 0         | double-slot buffer under delayed reader pressure                                       |
| snapshot_delayed_reader_triple              | 104.13    | 102.57   | 0.010  | 0.010  | 0.010  | 1.87x          | 1,024     | 1,024     | 0         | triple-slot buffer under delayed reader pressure                                       |
| entity_table_ingest_publish_changed         | 30.43     | 29.35    | 34.361 | 34.790 | 34.795 | 0.55x          | 1,000,000 | 1,000,000 | 0         | ingest latest-state table, then publish changed snapshots into double buffer           |
| entity_table_ingest_publish_acquire_release | 30.82     | 30.71    | 32.522 | 32.751 | 32.781 | 0.55x          | 1,000,000 | 1,000,000 | 0         | ingest, publish changed snapshots, acquire/release latest view                         |
| entity_table_ingest_publish_combined        | 30.21     | 28.34    | 35.260 | 37.180 | 37.398 | 0.54x          | 1,000,000 | 1,000,000 | 0         | single ABI call: ingest latest-state table and publish changed double-buffer snapshot  |
| frame_transform_off                         | 1024.00   | 999.02   | 0.001  | 0.001  | 0.001  | 18.39x         | 1,024     | 1,024     | 0         | snapshot walk without frame conversion                                                 |
| frame_transform_on                          | 446.97    | 438.84   | 0.002  | 0.002  | 0.002  | 8.03x          | 1,024     | 1,024     | 0         | snapshot walk with ENU-to-Unreal pose conversion                                       |

### Native readout

- Header callback-every-packet throughput vs header-only: `0.92x`.
- Header downsample-before-callback throughput vs callback-every-packet: `0.91x`.
- Entity pose-only decode vs full fixed-prefix decode: `1.15x`.
- Reused scanner pose decode vs one-shot pose decode: `0.98x`.
- Native entity-ID allowlist throughput vs routing-only decode: `0.91x`.
- Callback-free pose batch throughput vs pose callback-every-packet: `1.00x`.
- Compact transform batch throughput vs pose batch throughput: `1.00x`.
- Entity-table ingest + changed publish vs ingest-only: `1.03x`.
- Combined ingest+publish ABI call vs separate ingest+publish: `0.99x`.
- Publish-all snapshot buffer vs publish-changed dirty snapshot buffer: `1.01x`.
- Triple-slot delayed reader vs double-slot delayed reader: `0.97x`.
- Frame transform on vs frame transform off: `0.44x`.

## Python ctypes benchmark

ABI: `8`; library version: `0.13.0-alpha3`.

| case                                       | best Mpps | avg Mpps | p50 ms  | p95 ms   | p99 ms   | vs ctypes header-only | accepted | emitted | callbacks | notes                                                                                          |
| ------------------------------------------ | --------- | -------- | ------- | -------- | -------- | --------------------- | -------- | ------- | --------- | ---------------------------------------------------------------------------------------------- |
| ctypes_header_no_callback                  | 0.088     | 0.081    | 614.517 | 671.208  | 678.790  | 1.00x                 | 250,000  | 250,000 | 0         | includes packet-view setup + one ctypes scan call                                              |
| ctypes_header_callback_every_packet        | 0.078     | 0.073    | 670.766 | 728.066  | 730.802  | 0.88x                 | 250,000  | 250,000 | 250,000   | Python callback for every accepted packet                                                      |
| ctypes_header_callback_sample_100          | 0.095     | 0.085    | 597.444 | 622.362  | 625.320  | 1.07x                 | 250,000  | 2,500   | 2,500     | downsample in C before Python callback                                                         |
| ctypes_entity_pose_no_callback             | 0.085     | 0.080    | 617.814 | 663.540  | 665.765  | 0.96x                 | 250,000  | 250,000 | 0         | Entity State pose-only decode through ctypes wrapper                                           |
| ctypes_entity_all_no_callback              | 0.090     | 0.082    | 609.683 | 665.132  | 672.610  | 1.01x                 | 250,000  | 250,000 | 0         | Entity State full fixed-prefix decode through ctypes wrapper                                   |
| ctypes_entity_pose_to_batch                | 0.055     | 0.049    | 989.108 | 1135.858 | 1148.593 | 0.62x                 | 250,000  | 250,000 | 0         | callback-free native batch, then Python value conversion                                       |
| ctypes_entity_transform_to_batch           | 0.068     | 0.061    | 782.084 | 926.256  | 934.283  | 0.77x                 | 250,000  | 250,000 | 0         | compact transform batch output, then Python value conversion                                   |
| ctypes_entity_force_reject_no_callback     | 0.095     | 0.088    | 567.982 | 589.718  | 591.701  | 1.08x                 | 0        | 0       | 0         | C-side force-ID filter rejects all after minimal decode                                        |
| ctypes_scanner_entity_id_allow_one         | 0.079     | 0.075    | 666.824 | 686.068  | 689.638  | 0.89x                 | 245      | 245     | 0         | reusable scanner + native entity-ID allowlist                                                  |
| ctypes_scanner_transform_batch_allow_one   | 0.084     | 0.082    | 613.286 | 629.013  | 629.930  | 0.95x                 | 245      | 245     | 0         | reusable scanner + entity allowlist + compact transform batch                                  |
| ctypes_entity_table_ingest_latest          | 0.081     | 0.077    | 657.926 | 671.785  | 672.605  | 0.91x                 | 250,000  | 250,000 | 0         | ctypes wrapper updates native latest-state table                                               |
| ctypes_entity_table_ingest_publish_changed | 0.093     | 0.086    | 573.175 | 620.922  | 628.411  | 1.05x                 | 250,000  | 250,000 | 0         | ingest native latest-state table, publish changed snapshots into reusable native double buffer |
| ctypes_snapshot_acquire_copy_release       | 0.077     | 0.072    | 694.706 | 719.239  | 720.006  | 0.87x                 | 250,000  | 250,000 | 0         | publish changed snapshots, acquire latest view, copy to Python tuple, release                  |
| ctypes_ingest_publish_changed_combined     | 0.094     | 0.081    | 589.396 | 727.977  | 744.905  | 1.06x                 | 250,000  | 250,000 | 0         | single ctypes ABI call: ingest table and publish changed snapshot buffer                       |
| ctypes_scanner_chained_filters_callback    | 0.095     | 0.087    | 568.788 | 612.331  | 616.771  | 1.07x                 | 125,000  | 1,250   | 1,250     | chained filter API: force IDs [1,2] + sample 1/100 + Python callback                           |

### ctypes readout

- Python callback-every-packet throughput vs ctypes header-only: `0.88x`.
- C-side downsample before Python callback vs callback-every-packet: `1.21x`.
- ctypes pose-only Entity State decode vs full fixed-prefix decode: `0.95x`.
- chained filters + downsample callback vs callback-every-packet: `1.22x`.
- ctypes transform batch vs ctypes pose callback-free scan: `0.80x`.
- ctypes table ingest + snapshot-buffer publish vs table ingest-only: `1.15x`.
- ctypes combined ingest+publish vs separate ingest+publish: `1.01x`.

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

