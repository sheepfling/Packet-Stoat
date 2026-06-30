# Core Cross-Platform Harness

This page is the publication-facing summary for the proven FastDIS core
cross-platform benchmark lane.

It covers only the shared `c`, `cpp`, `python_ctypes`, and `godot` lane, with
`native` treated as the reference runtime. It does not claim Unreal runtime
parity, Unity runtime parity, or GRILL head-to-head results.

## What This Lane Proves

FastDIS currently publishes shared, truth-backed evidence for:

- ingest
- filtering
- latest-state behavior
- replay behavior
- claim-bounded cross-surface reporting

Measured surfaces in this lane:

- `c`
- `cpp`
- `python_ctypes`
- `godot`

Reference-only surface:

- `native`

`native` is the baseline runtime and oracle layer. It is useful evidence, but
it is not counted as a completion surface by itself.

## What This Lane Does Not Prove

This lane does not prove:

- Unreal product-runtime parity
- Unity product-runtime parity
- GRILL Unreal head-to-head comparison
- GRILL Unity head-to-head comparison
- marketplace-ready end-user installation across every engine

Those are separate execution lanes and should remain separate in messaging and
acceptance criteria.

## Operator Command

Use this command to refresh only the shared core lane and its downstream
reports:

```bash
python tools/refresh_engine_benchmark_artifacts.py --core-only
```

This path intentionally excludes still-blocked Unreal, Unity, and competitor
execution work so the core lane can refresh deterministically.

## Primary Evidence Files

Scenario contract:

- `tests/data/engine_benchmark_scenarios/core_matrix.v1.json`

Truth contract:

- `tests/data/engine_benchmark_truth/core_matrix.v1.json`

Surface reports:

- `artifacts/reports/engine_benchmarks/c_engine_benchmark_report.json`
- `artifacts/reports/engine_benchmarks/cpp_engine_benchmark_report.json`
- `artifacts/reports/engine_benchmarks/python_ctypes_engine_benchmark_report.json`
- `artifacts/reports/engine_benchmarks/godot_engine_benchmark_report.json`

Top-level summaries:

- `artifacts/reports/benchmark_matrix/benchmark_matrix.json`
- `artifacts/reports/benchmark_coverage/benchmark_coverage_report.json`
- `artifacts/reports/scenario_contract/scenario_contract_report.json`
- `artifacts/reports/core_cross_platform_harness/core_cross_platform_harness_report.json`
- `artifacts/reports/benchmark_contract_stack/benchmark_contract_stack.json`

## Stress Scenarios In Contract

The shared canonical contract already includes stress/performance-facing
scenario names beyond the base ingest/replay proof:

- `filter_reject_90pct`
- `malformed_10pct`
- `entity_state_10000_burst`
- `mixed_pdu_family`
- `snapshot_pressure`
- `late_reader_pressure`

These scenario names live in:

- `tests/data/engine_benchmark_scenarios/core_matrix.v1.json`
- `tests/data/engine_benchmark_truth/core_matrix.v1.json`

Not every surface publishes every stress scenario yet. Claims should stay tied
to the matrix and coverage artifacts for the specific surfaces that currently
emit them.

Current measured expansion target:

- `native`: `entity_state_10000_burst`
- `python_ctypes`: `entity_state_10000_burst`

That is useful stress evidence for the core lane, but it is not the same as
claiming every measured surface publishes the full stress suite yet.

## Current Claim Boundary

Safe claim:

> FastDIS has a shared proof-backed benchmark harness across `c`, `cpp`,
> `python_ctypes`, and `godot` with reproducible ingest, filtering,
> latest-state, replay, and claim-bounded reporting.

Do not claim from this lane alone:

- that FastDIS has beaten GRILL in Unreal or Unity
- that Unreal and Unity product lanes are complete
- that parser-speed or throughput leadership is proven from wall-clock runtime
  rows alone

## Required Green Checks

The core lane should only be presented as current when all of these are true:

```bash
python tools/refresh_engine_benchmark_artifacts.py --core-only
python tools/check_benchmark_contract_stack.py --fail-missing
```

And the resulting report:

- `artifacts/reports/core_cross_platform_harness/core_cross_platform_harness_report.json`

must remain `complete`.
