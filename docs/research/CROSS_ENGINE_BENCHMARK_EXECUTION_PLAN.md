# Cross-Engine Benchmark Execution Plan

This document is the execution plan for finishing the FastDIS benchmark
program. The harness architecture already exists. The remaining work is to turn
that architecture into a completed, claim-safe evidence pipeline that produces
real same-host competitor comparisons for Unreal and Unity and a stable
cross-engine scorecard for native, C/C++, Python, Godot, Unreal, and Unity.

Use this plan with:

- `docs/research/CROSS_ENGINE_BENCHMARK_HARNESS_PLAN.md`
- `docs/research/benchmark_matrix.md`
- `docs/research/CROSS_ENGINE_BENCHMARK_PROGRAM_BLURB.md`

## Objective

Finish one benchmark program that can:

- run shared ingest and filtering scenarios across `native`, `cpp`,
  `python_ctypes`, `godot`, `unreal`, and `unity`
- publish shared-truth equivalence reports across all FastDIS surfaces
- publish same-host FastDIS-vs-GRILL head-to-head reports for Unreal and Unity
- make missing or blocked evidence explicit instead of overstating results

## Gold Finish

This work is complete when FastDIS can regenerate a current benchmark packet
containing:

- shared scenario and truth contracts
- current benchmark reports for all FastDIS surfaces
- current cross-engine equivalence reports
- current same-host Unreal head-to-head report against GRILL
- current same-host Unity head-to-head report against GRILL
- a completion audit that marks the benchmark program `PASS`
- a claim summary that states exactly what FastDIS can publish

## Claim Standard

The program only counts as complete if every strong claim has pinned evidence.

Allowed:

- FastDIS beats GRILL in Unreal on scenario `X` on host `Y`
- FastDIS beats GRILL in Unity on scenario `X` on host `Y`
- FastDIS preserves shared truth across native, C++, Python, Godot, Unreal, and
  Unity
- FastDIS shows lower adapter overhead than another FastDIS surface under the
  same scenario family

Not allowed:

- broad "faster than GRILL" claims without same-host comparable evidence
- Unity competitor claims from a host where GRILL does not import or run
- Unreal competitor claims from different scene, fixture, or host classes
- cross-engine claims based on sample-only data when the truth contract is not
  satisfied

## Workstreams

### 1. Shared Scenario Completion

Finish the canonical scenario set and make every surface consume the same named
cases.

Required outputs:

- stable scenario suite in
  `tests/data/engine_benchmark_scenarios/core_matrix.v1.json`
- stable truth suite in
  `tests/data/engine_benchmark_truth/core_matrix.v1.json`
- scenario-to-report normalization with no surface-private case names

Exit gate:

- every benchmark lane reports the same scenario ids for directly comparable
  cases

### 2. Core Runtime Benchmark Completion

Strengthen the non-engine numbers first so the core runtime is independently
measured.

Required surfaces:

- `native`
- `cpp`
- `python_ctypes`

Required metrics:

- packets per second
- entities per second
- parse latency or ingest timing
- filter accept/reject totals
- latest-state correctness
- malformed packet handling

Exit gate:

- shared reports exist for all three surfaces
- cross-surface scenario names align
- truth checks pass on the canonical suite

### 3. Engine Adapter Proof Completion

Move the engine lanes from proof-only and sample-only evidence to direct
scenario evidence wherever practical.

Required surfaces:

- `godot`
- `unreal`
- `unity`

Required evidence per engine:

- ingest scenario evidence
- latest-state or runtime-apply evidence
- orientation or transform evidence where applicable
- workflow or install proof
- normalized shared benchmark report

Exit gate:

- each engine emits a current
  `fastdis.engine_benchmark_report.v1` artifact
- each engine contributes to cross-engine equivalence output

### 4. Unreal Head-To-Head Completion

Produce a real same-host Unreal comparison against the GRILL Unreal plugin.

Required steps:

- pin GRILL Unreal source or distributable version
- define a minimal comparable scenario set
- capture GRILL Unreal report on the same host class as FastDIS Unreal
- normalize the GRILL payload into the shared report shape
- generate the same-host head-to-head report

Minimum comparable scenarios:

- UDP entity-state loopback
- spawn/update/remove loop
- mixed accept/reject traffic

Exit gate:

- `grill_unreal` report exists
- same-host comparator classifies the matched rows as directly comparable
- claim summary can publish at least one honest Unreal competitor statement

### 5. Unity Head-To-Head Completion

Produce a real same-host Unity comparison against the GRILL Unity plugin.

Required steps:

- pin the GRILL Unity repository or package source and Unity version
- capture import/install evidence on the actual benchmark host
- run the agreed comparison scene with matching case names
- normalize the GRILL payload into the shared report shape
- generate the same-host head-to-head report

Minimum comparable scenarios:

- UDP entity-state loopback
- replay/latest-state apply
- spawn/update/remove loop

Exit gate:

- `grill_unity` report exists
- same-host comparator marks the aligned rows directly comparable
- claim summary can publish at least one honest Unity competitor statement

### 6. Cross-Engine Equivalence Completion

Turn the current equivalence reporting into a real release gate.

Required equivalence families:

- packet truth
- latest-state truth
- lifecycle truth
- replay final transform truth
- orientation basis truth where applicable

Exit gate:

- one current equivalence artifact covers all FastDIS surfaces
- deviations are surfaced as failures, not prose notes

### 7. Publication and Audit Completion

Finish the reporting layer that converts raw runs into publishable proof.

Required outputs:

- benchmark matrix
- completion audit
- claim summary
- competitor capture manifest
- competitor capture validation
- competitor handoff bundle

Exit gate:

- `fastdis release benchmark-refresh` regenerates the entire current evidence
  set
- completion audit returns `PASS`

## Milestones

### Milestone A: Shared Core Numbers

Deliver:

- completed `native`, `cpp`, and `python_ctypes` shared reports
- refreshed benchmark matrix
- refreshed claim summary with core-runtime statements

Completion test:

- core scenarios are green and comparable across the three non-engine surfaces

### Milestone B: Engine Parity Evidence

Deliver:

- current `godot`, `unreal`, and `unity` engine reports
- current cross-engine equivalence report

Completion test:

- FastDIS can publish engine-truth and adapter-evidence statements without
  competitor claims

### Milestone C: Unreal Competitor Proof

Deliver:

- pinned GRILL Unreal baseline
- current Unreal head-to-head report

Completion test:

- at least one same-host Unreal competitor claim is publishable

### Milestone D: Unity Competitor Proof

Deliver:

- pinned GRILL Unity baseline
- current Unity head-to-head report

Completion test:

- at least one same-host Unity competitor claim is publishable

### Milestone E: Program Closure

Deliver:

- refreshed benchmark matrix
- refreshed completion audit
- refreshed claim summary
- refreshed competitor handoff bundle

Completion test:

- benchmark completion audit marks the program complete

## Operator Loop

The working loop should stay simple:

1. update scenarios or lane runners
2. regenerate lane artifacts
3. run `python tools/refresh_engine_benchmark_artifacts.py`
4. inspect matrix, audit, and claim summary
5. fix the next blocked lane

Preferred entrypoint:

```bash
fastdis release benchmark-refresh
```

## Current Highest-Leverage Sequence

If the team wants the shortest path to a defensible finish, do the work in this
order:

1. lock the comparable Unreal and Unity scenario ids
2. finish direct scenario reports for `cpp` and `python_ctypes` if any metrics
   are still thin
3. finish current normalized engine reports for Godot, Unreal, and Unity
4. capture GRILL Unreal same-host baseline and publish the Unreal comparison
5. capture GRILL Unity same-host baseline and publish the Unity comparison
6. refresh the full artifact stack and drive the completion audit to `PASS`

## Risks

- competitor install drift can block same-host evidence
- engine-version drift can invalidate direct comparison
- sample-only reports can look complete unless the audit remains strict
- different case labels across lanes can silently break comparisons

The fix for all four is the same: pin versions, keep the scenario ids stable,
and let the shared audit fail loudly.

## Definition of Done

The benchmark program is done when:

- FastDIS has current shared reports for native, C++, Python, Godot, Unreal,
  and Unity
- FastDIS has current same-host GRILL comparison reports for Unreal and Unity
- FastDIS has a current cross-engine equivalence report across all FastDIS
  surfaces
- the completion audit marks the program complete
- the claim summary can be published without caveats that hide missing data
