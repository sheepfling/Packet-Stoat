# FastDIS vs GRILL Unity Benchmark Lane

This note defines the current Unity head-to-head benchmark proof lane.

Current FastDIS input:

- `build/benchmark_results/current/current.json`

Expected GRILL baseline input:

- `verification_reports/unity_grill_baseline/grill_unity_benchmark_baseline.json`
- template: `verification_reports/unity_grill_baseline/grill_unity_benchmark_baseline.template.json`

Current report command:

```bash
python tools/build_unity_head_to_head_benchmark_report.py
```

Preferred operator-facing workflow:

```bash
python tools/unity_workflow.py swap-import-smoke --unity-version 6000.5
python tools/unity_workflow.py swap-baseline-init \
  --unity-version 6000.5.0f1 \
  --scene LoopbackBench \
  --traffic-mix "100% Entity State" \
  --overwrite
python tools/unity_workflow.py swap-benchmark
```

The `swap-*` names are the preferred operator surface because they keep Unity
parallel with the Unreal swap lane and frame the work as a swappable FastDIS
route rather than a one-off competitor script. The older `grill-*` names remain
supported as explicit aliases because the current public baseline still comes
from the GRILL source route.

Current report outputs:

- `build/reports/unity_head_to_head_benchmark.json`
- `build/reports/unity_head_to_head_benchmark.md`

The report must remain `incomplete` until a GRILL Unity benchmark payload is on
disk. FastDIS-only throughput evidence is useful for local tuning, but it is
not an honest head-to-head claim.

Minimum GRILL payload contract:

- `schema = fastdis.unity_grill_benchmark_baseline.v1`
- `product = GRILL DIS for Unity`
- pinned repository URL and commit
- pinned Unity version and host details
- pinned benchmark scenario: scene, traffic mix, entity counts, update rates
- at least one measured `results[]` row with:
  - `case`
  - `entity_count`
  - `update_hz`
  - `packets_per_sec`
  - `main_thread_ms_avg`
  - `gc_alloc_bytes_per_frame`

Suggested capture flow:

```bash
python tools/unity_workflow.py swap-import-smoke --unity-version 6000.5
python tools/unity_workflow.py swap-baseline-init \
  --unity-version 6000.5.0f1 \
  --scene LoopbackBench \
  --traffic-mix "100% Entity State" \
  --overwrite
python tools/unity_workflow.py swap-benchmark
```

Comparison notes:

- the side-by-side report matches GRILL rows to FastDIS rows by `case`
- use the same `case` labels as the FastDIS comparison run when you want
  automatic ratio output
- if cases do not align, the report still validates both payloads but shows
  zero matched comparison rows
