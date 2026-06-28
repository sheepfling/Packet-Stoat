# Core Harness Stabilization Plan

This document defines the next completion program for the shared
`c` / `cpp` / `python_ctypes` / `godot` benchmark harness after the core
cross-platform lane first reached `complete`.

This is the active `1 / 2 / 3 / 5` plan:

- `1`: commit hygiene
- `2`: deterministic refresh
- `3`: publishable documentation
- `5`: performance and stress scenario expansion

Workstream `4` remains blocked. Unreal-vs-GRILL and Unity-vs-GRILL head-to-head
execution work should not be mixed into the acceptance criteria below.

## Scope

In scope:

- clean commit preparation for the completed core harness work
- deterministic one-command artifact refresh
- publication-grade documentation for the proven core lane
- additional performance and stress scenarios inside the same shared contract

Out of scope:

- Unreal competitor execution
- Unity competitor execution
- marketplace messaging that depends on competitor head-to-head capture
- claiming product-wide parity from the core lane alone

Blocked:

- `4`: competitor/runtime proof lanes that still depend on blocked Unreal and
  Unity capture and validation work

## Program Goal

FastDIS should be able to refresh, verify, and publish the shared core
benchmark harness from one deterministic entrypoint, with stable artifacts,
clear claim boundaries, and an expanded stress/performance scenario set across
`c`, `cpp`, `python_ctypes`, and `godot`.

## Workstreams

### 1. Commit Hygiene

Objective:

- turn the current completed harness work into clean, reviewable commit units

Required outputs:

- one commit for core harness scenario/report plumbing
- one commit for Godot filtering/runtime proof support
- one commit for follow-on report or documentation hardening if needed

Rules:

- do not mix unrelated Unreal or Unity edits into the core harness commits
- do not collapse behavioral work and documentation-only work unless the diff
  is genuinely inseparable
- preserve generated artifacts only where the repo already treats them as
  versioned benchmark evidence

Acceptance:

- `git status --short` is clean except for intentionally deferred unrelated work
- commit boundaries match the actual technical units of change
- each commit message explains the proof or harness effect, not just file churn

### 2. Deterministic Refresh

Objective:

- make one refresh path produce the final core harness outputs in the correct
  order every time

Primary entrypoint:

```bash
python tools/refresh_engine_benchmark_artifacts.py
```

Hard requirements:

- refresh steps execute in dependency order, not in an order that can leave
  stale downstream artifacts
- `benchmark_matrix`
- `benchmark_coverage`
- `scenario_contract`
- `core_cross_platform_harness`
- `benchmark_contract_stack`
  must all reflect the latest engine benchmark reports from the same run
- optional blocked engine lanes must not prevent the core lane from refreshing
  honestly

Required implementation checks:

- no report rebuild relies on parallel execution ordering
- Godot build freshness is handled explicitly when the GDExtension source
  changes
- normalizers append or merge rows without silently dropping canonical
  scenarios

Acceptance:

- a single sequential refresh produces:
  - `build/reports/benchmark_matrix/benchmark_matrix.json`
  - `build/reports/benchmark_coverage/benchmark_coverage_report.json`
  - `build/reports/scenario_contract/scenario_contract_report.json`
  - `build/reports/core_cross_platform_harness/core_cross_platform_harness_report.json`
  - `build/reports/benchmark_contract_stack/benchmark_contract_stack.json`
- `core_cross_platform_harness_report.json` remains `complete`
- `check_benchmark_contract_stack.py --fail-missing` exits `0`

### 3. Publishable Documentation

Objective:

- document exactly what the shared core harness proves, and what it does not

Required doc updates:

- one primary doc for the core lane publication story
- one short operator section describing the refresh command and evidence files
- one explicit claim-boundary section separating:
  - core harness proof
  - Unreal/Unity product proof
  - GRILL competitor proof

Required content:

- proven capabilities:
  - ingest
  - filtering
  - latest-state
  - replay
- measured surfaces:
  - `c`
  - `cpp`
  - `python_ctypes`
  - `godot`
- reference role of `native`
- exact report paths used for evidence
- explicit non-claims:
  - not a GRILL head-to-head result
  - not an Unreal runtime parity result
  - not a Unity runtime parity result

Acceptance:

- docs point at current commands and current artifact paths
- docs do not over-claim beyond the core lane evidence
- a reviewer can tell, in one pass, what is proven and what remains blocked

### 5. Performance and Stress Scenario Expansion

Objective:

- extend the shared scenario contract beyond correctness-only proof into
  performance and stress evidence without breaking claim discipline

New scenario families to add:

- high-entity burst ingest
- mixed accepted/rejected traffic
- malformed traffic
- replay stress
- bounded queue or pressure scenarios where a surface can support them honestly

Rules:

- every added scenario must have:
  - scenario contract row
  - truth contract row where applicable
  - normalized report coverage
  - clear claim boundary if a metric is partial or null on some surfaces
- do not publish parser-speed claims from wall-clock runtime rows alone
- keep scenario names canonical across surfaces whenever behavior is genuinely
  the same

Target first additions:

- `entity_state_10000_burst`
- `malformed_10pct`
- `filter_reject_90pct` on every eligible measured surface
- replay pressure scenario with bounded packet budget

Acceptance:

- the canonical scenario suite expands without regressing current complete status
- new scenarios appear in the matrix and coverage reports
- documentation explains which scenarios are throughput-facing versus
  correctness-facing

## Exit Criteria

This program is complete when all of the following are true:

1. The harness work is split into clean commits with unrelated engine work
   excluded.
2. `python tools/refresh_engine_benchmark_artifacts.py` is a reliable
   sequential refresh path for the current core lane.
3. The refresh path regenerates the final downstream reports without stale-order
   mismatches.
4. The core lane documentation is publication-grade and explicitly
   claim-bounded.
5. The shared scenario suite includes additional stress/performance scenarios
   with corresponding truth and report coverage.
6. The resulting artifacts still prove the core lane as `complete` for
   `c`, `cpp`, `python_ctypes`, and `godot`.

## Current Verified State

As of the current refresh route:

- `python tools/refresh_engine_benchmark_artifacts.py --core-only` completes
- `python tools/check_benchmark_contract_stack.py --fail-missing` exits `0`
- `build/reports/core_cross_platform_harness/core_cross_platform_harness_report.json`
  is back to `complete`
- `entity_state_10000_burst` is measured on `native` and `python_ctypes`
- the `--core-only` network ingest route now includes Godot live UDP and the
  Godot `filter_reject_90pct` lane while still excluding blocked Unreal work

That means the deterministic refresh requirement is currently proven again.
The remaining work is commit hygiene plus further measured stress expansion.

## Recommended Commit Split

If the current worktree is committed from here, keep the split aligned to the
 technical units below.

Commit 1:

- core filter/replay benchmark lane plumbing
- shared scenario/truth contract additions
- C/C++ report normalization and contract-stack updates

Suggested file family:

- `examples/c/*`
- `examples/cpp/*`
- `tests/data/engine_benchmark_scenarios/*`
- `tests/data/engine_benchmark_truth/*`
- `tools/run_core_filter_matrix.py`
- `tools/normalize_core_filter_matrix.py`
- `tools/run_core_replay_matrix.py`
- `tools/normalize_core_replay_matrix.py`
- `tools/build_scenario_contract_report.py`
- `tools/check_benchmark_contract_stack.py`
- matching `tests/test_*contract*`, `tests/test_core_filter_matrix_tools.py`,
  `tests/test_core_replay_matrix_tools.py`

Commit 2:

- Godot filter/runtime proof support and Godot-inclusive core-only ingest route

Suggested file family:

- `examples/godot/*`
- `tools/run_godot_udp_smoke.py`
- `tools/run_network_ingest_matrix.py`
- `tools/normalize_godot_proof_reports.py`
- matching Godot/network tests

Commit 3:

- deterministic refresh, focused core-harness reporting, docs, and current
  burst-scenario expansion

Suggested file family:

- `tools/refresh_engine_benchmark_artifacts.py`
- `tools/run_native_canonical_benchmark.py`
- `tools/normalize_current_benchmarks.py`
- `tools/build_benchmark_coverage_report.py`
- `tools/build_benchmark_matrix_report.py`
- `tools/build_core_cross_platform_harness_report.py`
- `schemas/json/fastdis.core_cross_platform_harness_report.v1.schema.json`
- `docs/research/benchmark_matrix.md`
- `docs/research/CORE_CROSS_PLATFORM_HARNESS.md`
- `docs/research/CORE_HARNESS_STABILIZATION_PLAN.md`
- `docs/research/CORE_HARNESS_EXECUTION_GOAL.md`
- matching refresh/core-harness/coverage tests

Do not mix these commits with the currently modified Unreal or Unity runtime
files unless they are intentionally being landed as part of a separate lane.

## Execution Goal Statement

Use this goal statement for the next execution phase:

> Stabilize the completed FastDIS core cross-platform benchmark harness by
> splitting the work into clean commits, making
> `tools/refresh_engine_benchmark_artifacts.py` a deterministic one-command
> refresh path, publishing clear claim-bounded documentation for the proven
> `c`/`cpp`/`python_ctypes`/`godot` lane, and expanding the shared scenario
> contract with additional performance and stress scenarios, while keeping the
> core harness reports green and excluding still-blocked Unreal/Unity competitor
> execution work.
