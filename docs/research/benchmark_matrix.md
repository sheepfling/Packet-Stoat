# Benchmark Matrix

This page defines the first shared contract for the cross-engine benchmark
harness.

Current contract artifacts:

- scenario suite schema:
  `schemas/json/fastdis.engine_benchmark_scenario.v1.schema.json`
- truth suite schema:
  `schemas/json/fastdis.engine_benchmark_truth.v1.schema.json`
- benchmark report schema:
  `schemas/json/fastdis.engine_benchmark_report.v1.schema.json`
- proof context schema:
  `schemas/json/fastdis.proof_context.v1.schema.json`
- benchmark matrix schema:
  `schemas/json/fastdis.engine_benchmark_matrix.v1.schema.json`
- benchmark completion-audit schema:
  `schemas/json/fastdis.engine_benchmark_completion_audit.v1.schema.json`
- benchmark claim-summary schema:
  `schemas/json/fastdis.benchmark_claim_summary.v1.schema.json`
- core cross-platform harness schema:
  `schemas/json/fastdis.core_cross_platform_harness_report.v1.schema.json`
- head-to-head report schema:
  `schemas/json/fastdis.engine_head_to_head_report.v1.schema.json`
- cross-engine equivalence schema:
  `schemas/json/fastdis.cross_engine_equivalence_report.v1.schema.json`
- competitor capture manifest schema:
  `schemas/json/fastdis.competitor_capture_manifest.v1.schema.json`
- competitor capture validation schema:
  `schemas/json/fastdis.competitor_capture_validation.v1.schema.json`
- canonical scenario suite:
  `tests/data/engine_benchmark_scenarios/core_matrix.v1.json`
- canonical truth suite:
  `tests/data/engine_benchmark_truth/core_matrix.v1.json`

Current normalization command:

```bash
python tools/normalize_current_benchmarks.py
```

That command does not run new benchmarks. It converts the current native and
`ctypes` benchmark payloads into the shared engine-benchmark report shape so
later Unreal, Unity, Godot, and competitor harnesses can emit the same top-level
contract.

The truth suite is the matching verification contract for those scenarios. It
pins which scenarios require final truth equality, latest-state verification,
and replay-final-transform checks so each engine adapter can prove the same
outcomes rather than inventing per-engine pass criteria.

Common proof qualification envelope:

- optional `proof_context` object on benchmark reports
- optional `left_proof_context` / `right_proof_context` on head-to-head inputs
- optional `proof_context` summaries in matrix surface/comparison rows

That envelope is where routes should converge on:

- evidence class
- comparison axis
- scenario family
- normalized host summary
- normalized platform summary
- claim/qualification boundaries

Legacy top-level `host` objects remain valid for current emitters. The
`proof_context` envelope is the stricter common format for future route
normalizers and benchmark capture lanes.

Current artifact refresh command:

```bash
python tools/refresh_engine_benchmark_artifacts.py
fastdis release benchmark-refresh
```

Preview the exact commands first:

```bash
python tools/refresh_engine_benchmark_artifacts.py --list-steps
```

Current core-lane-only refresh command:

```bash
python tools/refresh_engine_benchmark_artifacts.py --core-only
```

That command refreshes the current native/Python normalization, Unreal/Godot/
Unity proof bridges, the shared cross-engine equivalence summary, competitor
baseline-status reports, the top-level benchmark matrix, the benchmark
completion audit, and the benchmark claim summary in one sequential pass. It
does not fabricate missing GRILL reports; it makes those gaps explicit in the
generated status and matrix artifacts.

The `--core-only` path is the deterministic operator entrypoint for the shared
`c` / `cpp` / `python_ctypes` / `godot` lane. It intentionally excludes the
still-blocked Unreal, Unity, and competitor execution routes while preserving
the same downstream matrix, coverage, scenario-contract, and core-harness
reports.

Operator runbook:

- `docs/research/CROSS_PLATFORM_EVIDENCE_RERUN_RUNBOOK.md`

Current cross-engine equivalence summary:

```bash
python tools/build_cross_engine_equivalence_report.py
```

That report ties the Unity-facing deep-surface parity audit to the current
shared engine benchmark reports for native, C, C++, Python, Unreal, Godot, and
Unity, so FastDIS can publish one claim-bounded cross-engine summary instead of
scattering equivalence evidence across separate surface-specific files.

Current focused core-harness summary:

```bash
python tools/build_core_cross_platform_harness_report.py
```

That report narrows the public story to the shared `native`/`c`/`cpp`/
`python_ctypes`/`godot` verification lane. It is the claim-bounded answer for
core ingest, truth, filtering, latest-state, replay, and deep-equivalence
evidence while Unreal, Unity, and GRILL competitor routes continue to mature.

The focused report is intentionally stricter than the older aggregate coverage
view:

- `c`, `cpp`, `python_ctypes`, and `godot` are the measured surfaces that count
  toward completion
- `native` remains a reference/runtime baseline, not a completion lane by itself
- a surface is only complete when ingest, filtering, latest-state, and replay
  are all present on that same lane
- family-aligned or surface-local scenarios are useful evidence, but they do not
  satisfy the shared-scenario requirement by themselves
- if the canonical truth suite does not define a shared replay scenario yet, the
  focused report must remain `partial`

Current coverage summary:

```bash
python tools/build_benchmark_coverage_report.py
```

That coverage layer now combines:

- observed scenario names from the matrix
- canonical truth requirements from `tests/data/engine_benchmark_truth/core_matrix.v1.json`
- scenario-family aliases from `tests/data/engine_benchmark_scenarios/core_matrix_aliases.v1.json`

This keeps `latest_state` coverage honest for exact canonical `entity_state_*`
rows on `c` and `cpp`, while still distinguishing surface-local filtering or
replay evidence from shared-scenario completion.

Initial comparable surfaces:

- `native`
- `c`
- `cpp`
- `python_ctypes`
- `godot`

Current verification-backed engine surfaces:

- `unreal`
- `unity`

Competitor / head-to-head surfaces remain separate:

- `grill_unreal`
- `grill_unity`

Current Unreal bridge:

- `python tools/normalize_unreal_udp_smoke.py --input <payload.json>`

That bridge is intentionally narrow. It converts the existing Unreal UDP ingest
smoke payload into the shared engine-benchmark report shape so the Unreal lane
can join the common reporting contract before the richer same-scenario Unreal
benchmark runner is complete.

Current Godot bridge:

- `python tools/normalize_godot_udp_smoke.py --input <payload.json>`

That bridge does the same job for the existing Godot UDP ingest smoke lane so
Godot can emit the shared benchmark-report contract before a fuller scenario
runner exists.

Current Unity bridge:

- `python tools/normalize_unity_runtime_verification.py`

That bridge converts verified Unity runtime/workflow/equivalence evidence into
the shared benchmark-report contract. It is intentionally verification-first:
truth can be asserted, but packet-rate and frame-time fields remain null until a
real Unity benchmark scenario runner is emitting those measurements directly.

Current Unreal proof bridge:

- `python tools/normalize_unreal_proof_reports.py`

That bridge converts current Unreal Fab readiness, packaged install, and
orientation proof artifacts into the shared benchmark-report contract. Like the
Unity bridge, it is verification-first until the richer Unreal benchmark runner
is producing direct timing and throughput metrics in the shared scenario suite.

Current Godot proof bridge:

- `python tools/normalize_godot_proof_reports.py`

That bridge converts current Godot workflow and orientation proof artifacts into
the shared benchmark-report contract. It promotes Godot from a sample ingest
bridge to a current verification-backed engine report, while still leaving
timing and throughput fields null until the direct scenario runner exists.

Shared comparison layer:

- `python tools/run_engine_head_to_head_matrix.py --left <report.json> --right <report.json>`

That comparator consumes two `fastdis.engine_benchmark_report.v1` inputs and
emits one shared head-to-head report with explicit claim boundaries. Same-host
matching is required for the report to classify as directly comparable rather
than directional-only.

Top-level matrix layer:

- `python tools/build_benchmark_matrix_report.py`
- `fastdis release benchmark-matrix`

That aggregator summarizes all currently available shared engine benchmark
reports and head-to-head comparison reports into one claim-bounded matrix. It
does not invent completion; it calls out missing Unity, missing same-host
competitor evidence, and sample-only artifacts explicitly.

Current comparison evidence kinds:

- `measured`: a current comparison artifact backed by current left/right inputs
- `sample`: a comparison artifact that depends on sample fixture input and
  cannot support product claims
- `blocked`: a current comparison artifact whose honest outcome is that the
  competitor lane is unavailable or incompatible on the current host

Blocked comparison artifacts are intentional. They keep the benchmark packet
current even when GRILL cannot yet be captured on the same host.

Completion-audit layer:

- `python tools/audit_engine_benchmark_completion.py`
- `fastdis release benchmark-audit`

That audit checks the benchmark-program objective requirement by requirement. It
is the gate that distinguishes "current artifacts exist" from "the overall
cross-engine benchmark objective is actually proven."

Publication-summary layer:

- `python tools/build_benchmark_claim_summary.py`
- `fastdis release benchmark-claim-summary`

That summary is the operator-facing publication artifact. It reduces the matrix
and completion audit down to three practical questions:

- what FastDIS can claim today
- which competitor claims remain blocked
- which artifacts support each currently publishable statement

For GRILL route-specific claim wording and allowed workaround policy, use:

- `docs/research/GRILL_COMPARISON_POLICY.md`
- `docs/research/grill_source_route.md`

Current generated outputs:

- `build/reports/benchmark_matrix/benchmark_matrix.json`
- `build/reports/benchmark_matrix/benchmark_matrix.md`
- `build/reports/benchmark_completion_audit/benchmark_completion_audit.json`
- `build/reports/benchmark_completion_audit/benchmark_completion_audit.md`
- `build/reports/benchmark_claim_summary/benchmark_claim_summary.json`
- `build/reports/benchmark_claim_summary/benchmark_claim_summary.md`
- `build/reports/core_cross_platform_harness/core_cross_platform_harness_report.json`
- `build/reports/core_cross_platform_harness/core_cross_platform_harness_report.md`

Contract-stack check:

- `python tools/check_benchmark_contract_stack.py --fail-missing`
- `fastdis release benchmark-contract-check --fail-missing`

That check validates the benchmark contract family as a stack:

- the schema files exist
- the current benchmark artifacts exist
- each current artifact declares the expected schema id

Current generated outputs:

- `build/reports/benchmark_contract_stack/benchmark_contract_stack.json`
- `build/reports/benchmark_contract_stack/benchmark_contract_stack.md`

The canonical scenario names live in the scenario suite and should remain
stable once engine harnesses start consuming them.
