# All-Platform Harness Goal

This is the execution goal for the full FastDIS proof and benchmark harness
across host platforms, language surfaces, and engine adapters.

## Goal Statement

Build one rerunnable FastDIS test harness that can execute and report shared
DIS ingest, filtering, latest-state, replay, orientation, and adapter/runtime
scenarios across macOS, Windows, and Linux, using the same scenario ids,
shared truth fixtures, and proof schema for `c`, `cpp`, `python_ctypes`,
`godot`, `unreal`, and `unity`, while also capturing claim-bounded GRILL
comparison evidence for Unreal and Unity wherever the competitor route
actually installs, packages, and runs on the same host class.

## Scope

In scope:

- macOS host execution for native, C/C++, Python, Godot, Unreal, and Unity
- Windows host execution for Unreal and Unity competitor-comparable lanes
- Linux execution through direct host runs where available and Docker-backed
  proof/build routes where that is the honest current path
- one shared proof schema, one scenario contract, and one normalization path
- one operator-facing rerun workflow per surface

Out of scope:

- marketing claims that outrun the captured artifacts
- broad "faster than GRILL" statements without same-host matched evidence
- treating Linux package proof as Linux runtime proof

## Completion Gate

The goal is complete when all of the following are true:

1. Every FastDIS surface publishes a current normalized report under the shared
   benchmark/proof schema.
2. Every supported host lane has a documented rerun command and a bounded claim
   statement.
3. Unreal and Unity both have:
   - install or package proof
   - runnable harness proof on the supported host lanes
   - normalized same-host GRILL comparison artifacts where GRILL runs
4. Linux Unreal and Linux Unity lanes clearly separate:
   - package/install proof
   - runnable editor/runtime proof
   - benchmark/head-to-head proof
5. `tools/refresh_engine_benchmark_artifacts.py` and the engine workflow
   wrappers are sufficient for a junior operator to rerun the current evidence
   without ad hoc shell surgery.
6. The downstream benchmark matrix, equivalence reports, completion audit, and
   claim summary regenerate cleanly from the captured inputs.

## Operator Shape

The harness should converge on this operator model:

```bash
python tools/refresh_engine_benchmark_artifacts.py
python tools/check_benchmark_contract_stack.py --fail-missing
python tools/unreal_workflow.py doctor
python tools/unity_workflow.py doctor
python tools/godot_workflow.py verify
```

Platform-specific engine routes may still require host-local commands, but the
goal is that every such route is wrapped, documented, and normalized back into
the same report contract.

## Current Honest State

Currently proven:

- shared core lane for `c`, `cpp`, `python_ctypes`, and `godot`
- macOS Unreal harness entrypoints for orientation, replay/demo, install smoke,
  and GRILL swap/mapping work
- Linux Unreal package/build proof for both FastDIS and GRILL via Docker

Not yet complete:

- Linux Unreal live harness execution equivalent to the macOS Unreal harness
- same-host Unreal GRILL benchmark rows
- same-host Unity GRILL benchmark rows
- full Windows host capture for the competitor lanes

## Gold Blurb

FastDIS is building one all-platform harness, not a pile of one-off demos. The
finish line is a rerunnable proof and benchmark system that exercises the same
DIS scenarios and truth fixtures across macOS, Windows, and Linux for native,
C++, Python, Godot, Unreal, and Unity, then folds those runs into one typed
evidence contract with honest same-host GRILL comparisons where they are
actually supported.
