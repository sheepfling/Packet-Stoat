# Benchmark Comparison Scaffold

This document defines how FastDIS should present benchmark evidence coherently
across:

- language surface
- platform / host class
- game engine adapter
- competitor head-to-head

It is a scaffold, not a claim upgrade. The purpose is to make future proofs,
charts, and scorecards read cleanly without mixing incomparable evidence.

Use this with:

- `docs/research/benchmark_matrix.md`
- `docs/research/CROSS_ENGINE_BENCHMARK_EXECUTION_PLAN.md`
- `tests/data/engine_benchmark_scenarios/core_matrix.v1.json`
- `tests/data/engine_benchmark_scenarios/comparison_axes.v1.json`

## Core Rule

Every public comparison must answer all four questions:

1. What is being compared?
2. Under which scenario family?
3. Which evidence class supports the comparison?
4. What claim boundary applies?

If any of those are ambiguous, the comparison should remain internal-only or be
rendered as blocked / directional / truth-only.

## Comparison Axes

### 1. Language Surface

Purpose:

- show how the FastDIS core behaves across `native`, `c`, `cpp`, and
  `python_ctypes`

Allowed evidence:

- direct measured throughput
- latency / ingest timing
- filtering cost
- latest-state truth
- replay truth

Required controls:

- same canonical scenario name
- same packet fixture family
- same host class
- same build class where practical

Safe chart types:

- packets/sec by surface
- latency by surface
- truth/coverage matrix by surface

### 2. Platform / Host Class

Purpose:

- show how one FastDIS surface behaves across macOS, Windows, and Linux

Allowed evidence:

- measured rows for the same surface on different hosts
- install/runtime workflow proofs
- platform staging proofs

Required controls:

- same FastDIS version
- same scenario family
- explicit host metadata
- explicit build mode

Safe chart types:

- per-platform packets/sec for one surface
- per-platform install/runtime readiness matrix
- platform artifact staging matrix

Do not mix platform claims with language claims unless both axes are pinned in
the chart subtitle or report metadata.

### 3. Game Engine Adapter

Purpose:

- show how `godot`, `unity`, and `unreal` compare as FastDIS adapters

Allowed evidence:

- measured engine runtime rows where available
- truth-backed ingest / replay / latest-state rows
- orientation assurance
- install / workflow proof

Required controls:

- same canonical or family-aligned scenario
- explicit note when a surface is truth-backed but not fully timed
- engine-private workflow proof kept separate from throughput claims

Safe chart types:

- engine coverage / proof maturity matrix
- engine runtime metric availability matrix
- engine orientation proof family

Do not publish a single engine-throughput ranking unless the compared rows are
all directly measured under aligned scenario names and host classes.

### 4. Competitor Head-To-Head

Purpose:

- show FastDIS vs GRILL within the same engine

Allowed evidence:

- same-host comparable head-to-head report
- matched scenario name
- matched metric kind

Required controls:

- same host or explicitly normalized host class
- same engine version family
- same scenario
- same measurement meaning
- current competitor-capture validation pass

Safe chart types:

- Unity same-host metric triptych
- Unreal same-host metric triptych
- competitor lane status card when blocked

Never combine competitor rows with generic cross-language or cross-engine
rankings. Competitor proof is its own lane.

## Evidence Classes

These classes should be rendered explicitly in future charts and summaries.

### `direct_measured`

Meaning:

- the compared row has real measured runtime metrics

Examples:

- `native` packets/sec
- `python_ctypes` packets/sec
- Unity canonical runtime row with measured packets/sec and apply time

### `truth_backed_bridge`

Meaning:

- the surface proves correctness and scenario participation, but timing fields
  are sparse or null

Examples:

- current `c` and `cpp` shared truth rows
- current Unreal/Godot/Unity proof-bridge rows without full timing

### `family_aligned`

Meaning:

- the surface overlaps the same scenario family, but does not yet publish the
  exact canonical scenario name

This is useful for scaffolding, not for strong cross-surface ranking.

### `same_host_competitor`

Meaning:

- a direct FastDIS-vs-GRILL comparison row exists with same-host comparable
  metrics

### `blocked`

Meaning:

- the route is intentionally shown as unavailable or not yet comparable

Blocked is a valid benchmark state. It should appear in reports instead of
being hidden.

## Scenario Families

Future visuals should group scenarios into families before they become chart
series.

### `ingest_baseline`

- `entity_state_1x10hz`
- `entity_state_100x30hz`
- `entity_state_1000x60hz`

### `filtering`

- `filter_reject_90pct`
- `mixed_noise_10pct_entity_state`

### `malformed_resilience`

- `malformed_10pct`

### `burst_latest_state`

- `entity_state_10000_burst`
- `snapshot_pressure`
- `late_reader_pressure`

### `replay`

- `replay_latest_state_apply`

### `engine_runtime`

- engine-local canonical runtime apply rows that map back to the ingest family

### `orientation_assurance`

- `level_north`
- `level_east`
- `equator_prime_meridian_level_north`
- `adelaide_heading_135_pitch_20_roll_30`

### `workflow_install`

- install smoke
- package import
- native stage/load

### `competitor_minimum`

- Unity same-host loopback
- Unity latest-state apply
- Unreal same-host loopback
- Unreal spawn/update/remove

## Scorecard Layers

The benchmark story should be built in layers, not one giant scoreboard.

### Layer A: Core Runtime

Shows:

- `native`
- `c`
- `cpp`
- `python_ctypes`

Primary claim:

- FastDIS has measured cross-language ingest and replay evidence.

### Layer B: Cross-Platform

Shows:

- one surface across macOS / Windows / Linux

Primary claim:

- FastDIS behavior is portable across host classes.

### Layer C: Engine Adapters

Shows:

- `godot`
- `unity`
- `unreal`

Primary claim:

- FastDIS has bounded, proof-backed engine adapter evidence.

### Layer D: Competitor

Shows:

- `FastDIS Unity` vs `GRILL Unity`
- `FastDIS Unreal` vs `GRILL Unreal`

Primary claim:

- only whatever same-host comparable evidence actually supports

## Immediate Scaffolding Goals

The next safe expansion is:

1. make every chart source carry a declared comparison axis
2. add platform-oriented scenario rows once Windows/Linux measurements exist
3. keep engine throughput charts separate from engine proof-maturity charts
4. upgrade Unity competitor comparison from one matched row to a small family
5. keep Unreal competitor output blocked until same-host runnable evidence
   exists

## Gold Outcome

The benchmark program becomes coherent when FastDIS can publish all of the
following without mixing claim classes:

- cross-language measured core runtime chart
- cross-platform chart for at least one shared surface
- cross-engine proof-maturity chart
- cross-engine measured runtime chart where rows are actually comparable
- Unity same-host FastDIS-vs-GRILL chart
- Unreal same-host FastDIS-vs-GRILL chart or an explicit blocked-lane card
