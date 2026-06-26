# Cross-Engine Benchmark Harness Plan

This document is the program-of-record for proving FastDIS against its own
cross-engine claims and, where technically honest, against GRILL in Unreal and
Unity.

The goal is not a pile of one-off benchmark scripts. The goal is one benchmark
system with shared scenarios, shared truth fixtures, shared report contracts,
shared claim rules, and one refresh path that regenerates the current evidence
set.

## Program Goal

Build a shared benchmark harness that drives the same DIS traffic scenarios,
truth fixtures, and report schema across `native`, `cpp`, `python_ctypes`,
`unreal`, `unity`, and `godot`, while also producing same-host direct
comparison reports against `grill_unreal` and `grill_unity` wherever those
competitor plugins can actually install and run.

Completion means FastDIS can publish all of the following from pinned source
artifacts:

- reproducible ingest, filtering, replay, and latest-state reports
- reproducible adapter/runtime reports for Unreal, Unity, and Godot
- cross-engine equivalence evidence for packet truth, lifecycle, and transforms
- same-host Unreal and Unity FastDIS-vs-GRILL reports where competitor installs
  are real
- explicit claim boundaries wherever a comparison is blocked, partial, or
  non-comparable

## Gold Outcome

When this program is complete, FastDIS should be able to say:

> FastDIS is one verified DIS runtime with shared benchmark scenarios, shared
> truth fixtures, and shared reporting across native, C++, Python, Unreal,
> Unity, and Godot. Where direct competitor installs are possible, FastDIS
> publishes same-host head-to-head evidence against GRILL. Where they are not
> possible, FastDIS publishes explicit gaps instead of overstated claims.

That is the finish line. The point is not to collect numbers. The point is to
establish a public claim system the team can defend.

## Executive Summary

FastDIS needs one benchmark program, not separate benchmark stories for each
language binding and engine. The program should prove three things at once:

- the core runtime scales under controlled ingest, filter, latest-state, and
  replay load
- the Unreal, Unity, and Godot adapters preserve shared truth instead of
  drifting into engine-specific semantics
- FastDIS can publish honest head-to-head evidence against GRILL wherever
  direct competitor installs are real and repeatable

The practical objective is to make every public benchmark claim traceable to a
current artifact regenerated from one refresh path.

Use `docs/research/GRILL_COMPARISON_POLICY.md` as the claim-policy companion
for host-blocked or platform-limited GRILL routes.

## Product Questions

This program exists to answer five questions.

1. Is the FastDIS core actually fast under controlled ingest, filtering,
   latest-state, and replay load?
2. Do the Unreal, Unity, and Godot adapters preserve the same packet truth and
   runtime semantics instead of drifting into engine-specific behavior?
3. Can FastDIS beat GRILL on directly comparable Unreal and Unity workflows
   under the same host and scenario conditions?
4. Can FastDIS show meaningful numbers outside the game engines in Python and
   C/C++ so the core scales independently of adapter overhead?
5. Can every published benchmark claim be traced back to a current, pinned,
   reproducible artifact?

## Claim Rules

Allowed:

- "FastDIS beats GRILL in Unreal on scenario X on host Y" when the report is a
  real same-host direct comparison.
- "FastDIS preserves shared truth across native, C++, Python, Unreal, Unity,
  and Godot" when the verified scenario set matches shared truth fixtures.
- "FastDIS has lower adapter overhead than another FastDIS surface" when the
  scenario, host, and metric family are aligned.

Not allowed:

- "FastDIS beats GRILL in Unity" from a host where GRILL does not import or
  run.
- "FastDIS is faster" without a pinned scenario, host, metric family, and
  source revision.
- "Godot proves competitor superiority" because Godot is a FastDIS-only lane.
- ratios or deltas computed from mismatched scenarios, different host classes,
  or different fixture families without explicit normalization notes.
- broad platform-support claims about GRILL that go beyond the pinned public
  route evidence in this repo.

Allowed gap statement example:

- "The current public GRILL Unreal source route is Windows-only."

Not allowed gap statement example:

- "GRILL does not support Mac."

## Canonical Surfaces

The benchmark program should measure these surfaces:

- `native`
- `cpp`
- `python_ctypes`
- `unreal`
- `grill_unreal`
- `unity`
- `grill_unity`
- `godot`

They fall into three comparison families.

### Family A: Core Ingest

Purpose:
Measure parser, filter, latest-state, replay-core, and wrapper overhead with
minimal engine cost.

Surfaces:

- `native`
- `cpp`
- `python_ctypes`

### Family B: Engine Runtime

Purpose:
Measure how much overhead each engine adapter adds while preserving shared
truth.

Surfaces:

- `unreal`
- `unity`
- `godot`

### Family C: Competitor Head-To-Head

Purpose:
Measure whether FastDIS beats GRILL on directly comparable workflows.

Surfaces:

- `unreal` vs `grill_unreal`
- `unity` vs `grill_unity`

## Benchmark Principles

Every lane must follow the same rules.

### Same Inputs

Each lane should consume the same:

- scenario name
- entity count
- update rate
- traffic mix
- duration
- fixture family
- truth payload

### Same Report Shape

Each lane should emit one JSON report using the shared report schema.

Current contract artifacts:

- `schemas/json/fastdis.engine_benchmark_scenario.v1.schema.json`
- `schemas/json/fastdis.engine_benchmark_truth.v1.schema.json`
- `schemas/json/fastdis.engine_benchmark_report.v1.schema.json`
- `tests/data/engine_benchmark_scenarios/core_matrix.v1.json`
- `tests/data/engine_benchmark_truth/core_matrix.v1.json`

### Same Comparison Rules

Direct comparison is only allowed when these are equal or intentionally
normalized:

- host or host-class
- engine family and version
- scenario name
- entity count
- update rate
- duration
- traffic source and fixture family

### Honest Missing Data

If a lane cannot measure a field, the field should be omitted or set to `null`.
Missing data is acceptable. Invented equivalence is not.

## Scenario Matrix

The harness should converge on one canonical scenario suite.

### Core Scenarios

- `entity_state_1x10hz`
- `entity_state_100x30hz`
- `entity_state_1000x60hz`
- `mixed_noise_10pct_entity_state`
- `filter_reject_90pct`
- `malformed_10pct`

### Stress Scenarios

- `entity_state_10000_burst`
- `mixed_pdu_family`
- `snapshot_pressure`
- `late_reader_pressure`
- `heartbeat_threshold_send`

### Competitor Scenarios

These are the narrow, repeatable scenarios used for GRILL comparison.

- `udp_entity_state_loopback`
- `udp_entity_state_multicast`
- `spawn_update_remove_loop`
- `replay_latest_state_apply`
- `mixed_noise_accept_reject`

The competitor matrix should stay tight. The first comparison lane should not
depend on every advanced feature being complete.

## Truth Contract

Every scenario should publish a truth payload that records:

- packets sent
- packets expected to parse
- packets expected to reject
- malformed packet count
- unique entity count
- expected latest-state table contents
- expected removals or stale expirations
- expected replay final transforms
- expected cross-engine basis/orientation outcomes where applicable

Truth remains shared across all surfaces. An engine lane does not get a private
definition of correct behavior.

## Report Contract

Each lane should emit one shared benchmark report with, at minimum:

- lane identity and version metadata
- host metadata
- scenario metadata
- traffic metadata
- correctness summary
- throughput metrics
- latency metrics
- allocation or GC metrics when measurable
- queue/drop statistics when applicable
- evidence notes for partial or constrained runs

Head-to-head outputs should remain comparator reports rather than mixing both
sides into a single lane report.

## Program Entry Point

The benchmark system should refresh from one command:

```bash
python tools/refresh_engine_benchmark_artifacts.py
```

That entry point should:

- normalize current native and Python baselines
- normalize current Unreal, Unity, and Godot proof-backed reports
- refresh cross-engine equivalence outputs
- refresh current competitor baseline status
- run competitor comparison wrappers where evidence is available
- rebuild the top-level benchmark matrix
- leave blocked competitor claims visibly blocked instead of failing silently

## Definition Of Done

The benchmark program is done only when these artifacts exist and refresh from
the shared entry point:

- shared scenario, truth, and report contracts
- current shared-schema reports for `native`, `cpp`, `python_ctypes`,
  `unreal`, `unity`, and `godot`
- current cross-engine equivalence reports for correctness, lifecycle, and
  transform/orientation semantics
- at least one same-host Unreal FastDIS-vs-GRILL report
- at least one same-host Unity FastDIS-vs-GRILL report on a GRILL-compatible
  host
- a top-level benchmark matrix with explicit claim status for every surface
- a completion audit that marks every claim as `supported`, `partial`,
  `blocked`, or `not comparable`

If a claim cannot be regenerated from source inputs and current reports, it is
not complete.

## Workstreams

The program is split into eight workstreams.

### Workstream A: Shared Contracts

Objective:
Freeze the scenario, truth, report, and comparator contracts so every lane is
speaking the same language.

Deliverables:

- canonical scenario suite
- truth schema
- report schema
- comparator schema and comparison rules
- scenario versioning policy

Exit gate:

- every current lane emits or normalizes into the shared report shape
- head-to-head comparison consumes only shared reports

### Workstream B: Native, C++, And Python Baselines

Objective:
Establish core ingest reference numbers and wrapper overhead numbers outside the
engine adapters.

Deliverables:

- native benchmark report family
- C++ benchmark report family
- Python benchmark report family
- baseline markdown summary
- scenario-level ingest, reject, malformed, and latest-state reference numbers

Exit gate:

- native, C++, and Python cover the canonical scenario suite
- reports use the shared schema
- baseline comparison report is generated automatically

### Workstream C: Unreal FastDIS Lane

Objective:
Make Unreal a first-class benchmarked runtime lane, not just a proof lane.

Deliverables:

- shared Unreal scenario runner
- Unreal runtime ingest/apply metrics
- Unreal truth verification output
- Unreal report in the shared schema

Exit gate:

- Unreal can run the canonical scenario family
- Unreal report contains both correctness and runtime metrics

### Workstream D: Unity FastDIS Lane

Objective:
Make Unity a first-class benchmarked runtime lane with the same benchmark
contract as Unreal.

Deliverables:

- shared Unity scenario runner
- Unity runtime ingest/apply metrics
- Unity truth verification output
- Unity report in the shared schema

Exit gate:

- Unity can run the canonical scenario family
- Unity report contains both correctness and runtime metrics

### Workstream E: Godot FastDIS Lane

Objective:
Use Godot to prove adapter quality and cross-engine consistency, not to invent
competitor claims.

Deliverables:

- shared Godot scenario runner
- Godot runtime report in the shared schema
- Godot truth verification output
- FastDIS-only comparison against native/C++/Python baselines

Exit gate:

- Godot reports exist for the canonical scenario family
- truth equivalence is published

### Workstream F: Unreal And Unity GRILL Lanes

Objective:
Create direct competitor lanes only where GRILL can really install and run.

Deliverables:

- pinned GRILL Unreal baseline inputs
- pinned GRILL Unity baseline inputs
- same-scenario FastDIS and GRILL runs
- same-host comparator reports
- explicit status reports when competitor proof is blocked

Exit gate:

- same-host direct Unreal report exists for at least one canonical scenario
- same-host direct Unity report exists for at least one canonical scenario on a
  GRILL-compatible host

### Workstream G: Cross-Engine Equivalence

Objective:
Prove that packet truth, lifecycle behavior, and orientation semantics match
across FastDIS surfaces.

Deliverables:

- cross-engine equivalence report
- scenario-level truth comparisons
- lifecycle equivalence output
- transform/orientation equivalence output

Exit gate:

- native/C++/Python/Unreal/Unity/Godot all publish aligned truth for the
  supported scenario set

### Workstream H: Evidence Packaging

Objective:
Turn all of the above into a publishable, claim-bounded evidence package.

Deliverables:

- top-level benchmark matrix
- cross-engine equivalence report
- Unreal head-to-head report
- Unity head-to-head report
- completion audit
- product-facing claim boundary summary
- competitor capture handoff and validation path

Exit gate:

- product can link each benchmark claim to one current artifact

## Delivery Phases

### Phase 1: Contract Freeze

Ship:

- pinned scenario suite
- pinned truth suite
- pinned report schema
- one artifact refresh path

Exit:

- current reports regenerate from source artifacts
- the top-level matrix is reproducible

### Phase 2: FastDIS Surface Coverage

Ship:

- native reference numbers
- C++ reference numbers
- Python reference numbers
- Unreal current runtime lane
- Unity current runtime lane
- Godot current runtime lane

Exit:

- every FastDIS surface appears in the matrix
- each surface is labeled truthfully as `supported`, `partial`, `sample`, or
  `blocked`

### Phase 3: Unreal Competitor Proof

Ship:

- same-host GRILL Unreal baseline
- same-scenario FastDIS Unreal run
- shared Unreal head-to-head report

Exit:

- at least one Unreal competitor claim is supported by a real direct report

### Phase 4: Unity Competitor Proof

Ship:

- pinned GRILL-compatible Unity host
- GRILL import proof on that host
- same-scenario FastDIS Unity run
- same-scenario GRILL Unity run
- shared Unity head-to-head report

Exit:

- at least one Unity competitor claim is supported by a real direct report

### Phase 5: Publishable Evidence Package

Ship:

- benchmark matrix
- cross-engine equivalence report
- Unreal and Unity competitor reports
- completion audit
- claim-boundary summary

Exit:

- FastDIS can make benchmarked product claims without hand-waving

## Execution Order

This is the shortest defensible path to completion from the current state.

### Step 1: Freeze The Shared Benchmark Contract

Deliver:

- canonical scenario set
- canonical truth fixtures
- shared benchmark report schema
- shared comparison rules
- lane normalization rules for partial hosts

Why first:

Without a frozen contract, every new lane creates more cleanup work later.

### Step 2: Keep All FastDIS-Only Lanes Current

Deliver:

- refreshed `native`, `cpp`, `python_ctypes`, `unreal`, `unity`, and `godot`
  reports
- refreshed cross-engine equivalence reports
- refreshed benchmark matrix and completion audit

Why second:

This keeps the internal evidence package current while competitor capture work
is pending.

### Step 3: Close Unreal Competitor Proof

Deliver:

- pinned GRILL Unreal revision or package source
- same-host Unreal scenario capture for GRILL
- normalized Unreal head-to-head report
- matrix upgrade from directional to supported Unreal competitor claim

Why third:

Unreal competitor proof is the fastest path to a fully supported external
comparison lane.

### Step 4: Close Unity Competitor Proof

Deliver:

- pinned Unity editor version and host constraints
- GRILL-compatible Unity install proof
- same-host Unity scenario capture for both FastDIS and GRILL
- normalized Unity head-to-head report
- matrix upgrade from blocked to supported Unity competitor claim

Why fourth:

Unity comparison is strategically important, but it is only credible on a host
where GRILL actually imports and runs.

### Step 5: Package The Publishable Program

Deliver:

- benchmark matrix JSON and markdown
- cross-engine equivalence JSON and markdown
- Unreal and Unity head-to-head JSON and markdown
- competitor validation manifest
- completion audit
- claim-boundary summary

Why fifth:

The program is only useful when product, engineering, and external reviewers
can consume the same evidence set.

## Milestones

### Milestone 0: Contract Freeze

Exit:

- scenario schema pinned
- truth schema pinned
- report schema pinned
- comparator rules pinned

### Milestone 1: Core Baselines

Exit:

- native, C++, and Python canonical reports exist
- baseline comparison summary exists

### Milestone 2: Engine Runtime Coverage

Exit:

- Unreal, Unity, and Godot runtime reports exist in the shared schema
- cross-engine equivalence report is current

### Milestone 3: Unreal Competitor Lane

Exit:

- same-host Unreal FastDIS-vs-GRILL report exists
- matrix upgrades Unreal from directional to supported claim

### Milestone 4: Unity Competitor Lane

Exit:

- same-host Unity FastDIS-vs-GRILL report exists
- matrix upgrades Unity from blocked to supported claim

### Milestone 5: Program Finish

Exit:

- matrix, equivalence, competitor reports, and completion audit are current
- every public claim has a linked evidence artifact

## Required Harnesses

The minimum runnable harness set is:

- native ingest/filter/latest-state runner
- C++ ingest/filter/latest-state runner
- Python ctypes ingest/filter/latest-state runner
- Unreal scenario runner
- Unity scenario runner
- Godot scenario runner
- Unreal GRILL comparison runner
- Unity GRILL comparison runner
- shared matrix refresh runner
- competitor capture export/import/validation runner

## Required Metrics

Every lane should emit the maximum subset it can measure from this shared
metric family:

- packets received
- packets parsed
- packets rejected
- malformed packets
- unique entities observed
- latest-state correctness
- replay final-state correctness
- throughput in packets per second
- throughput in entities per second where applicable
- p50, p95, and p99 ingest latency where measurable
- adapter apply cost where measurable
- queue depth and queue drops where applicable
- socket drops where applicable
- managed allocation or GC metrics where measurable
- evidence notes for host or toolchain limits

## Evidence Gates

A surface is not complete because code exists. A surface is complete when all
of these exist:

- implementation
- pinned scenario coverage
- automated verification
- normalized shared-schema report
- current artifact in the matrix
- documented claim boundary

A competitor comparison is not complete because a benchmark script ran once. It
is complete when all of these exist:

- competitor revision/version pin
- same-host or explicitly normalized host metadata
- same-scenario FastDIS and competitor runs
- shared comparator report
- claim-ready markdown summary

## Current Finish Condition

This program is complete only when all of the following are true:

- the canonical scenario, truth, and report contracts are pinned
- `native`, `cpp`, `python_ctypes`, `unreal`, `unity`, and `godot` all publish
  current shared-schema benchmark reports
- cross-engine equivalence is current for the supported scenario set
- FastDIS publishes at least one same-host Unreal comparison against GRILL
- FastDIS publishes at least one same-host Unity comparison against GRILL on a
  host where GRILL actually installs and runs
- the benchmark matrix, competitor reports, and completion audit refresh from
  the single program entry point
- every externally usable claim has a current evidence artifact and a clear
  boundary statement

## Current Priority Scoreboard

Program status should be read in this order:

1. Contract health:
   scenario, truth, report, and comparator contracts are pinned and validated.
2. FastDIS lane health:
   all internal surfaces refresh cleanly into the matrix.
3. Competitor evidence health:
   same-host GRILL Unreal and Unity evidence is captured, validated, and
   normalized.
4. Publication health:
   every supported claim has a human-readable summary and machine-readable
   artifact.

If competitor evidence is missing, the program is still useful internally, but
it is not yet complete as an external comparison system.

## Gold Next Step

The highest-leverage sequence from the current state is:

1. finish contract and validation hardening around competitor capture bundles
2. keep Unreal, Unity, and Godot runtime evidence current through the shared
   refresh path
3. capture a same-host GRILL Unreal benchmark bundle and normalize it into the
   matrix
4. capture a GRILL-compatible Unity host bundle and normalize it into the
   matrix
5. lock the publishable benchmark matrix and claim summary around current
   evidence only
