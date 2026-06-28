# Core Harness Execution Goal

This is the execution goal for the unblocked `1 / 2 / 3 / 5` program while `4`
remains blocked.

## Goal Statement

Execute the FastDIS core cross-platform harness to completion by finishing
clean commit boundaries, locking `tools/refresh_engine_benchmark_artifacts.py`
into a deterministic one-command core-lane refresh, publishing claim-bounded
documentation for the proven `c` / `cpp` / `python_ctypes` / `godot` lane, and
expanding the shared benchmark contract with additional measured
performance/stress scenarios, while keeping the downstream matrix, coverage,
scenario-contract, and core-harness reports green and explicitly excluding the
still-blocked Unreal/Unity competitor lane.

## Completion Gate

The goal is complete when all of the following are true:

1. The harness changes are split into clean reviewable commits without mixing
   blocked Unreal/Unity competitor work.
2. `python tools/refresh_engine_benchmark_artifacts.py --core-only` refreshes
   the current core lane deterministically from one command.
3. The refreshed outputs regenerate the downstream contract stack without stale
   ordering or missing dependencies.
4. The docs clearly state what the core lane proves, what it does not prove,
   and which artifacts support each safe claim.
5. Additional shared stress/performance scenarios are measured and surfaced in
   the matrix and coverage reports without regressing current completion status.

## Operator Command

```bash
python tools/refresh_engine_benchmark_artifacts.py --core-only
python tools/check_benchmark_contract_stack.py --fail-missing
```
