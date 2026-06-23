# Orientation Scenario Harness

This folder is the small, deterministic orientation regression harness described
by the Alpha5 engine-verification plan.

The broader repo already has:

- canonical orientation fixtures in `tests/data/orientation_engine_cases.json`
- SciPy/SymPy/oracle checks
- Unreal, Godot, and Unity fixture sync
- runtime report parsers and visual projection reports

This harness adds a simple scenario/baseline interface:

```bash
python -m tests.orientation.harness.run_scenario --engine headless --all-quick
python -m tests.orientation.harness.run_scenario \
  --scenario tests/orientation/scenarios/level_flight.json \
  --engine headless
python -m tests.orientation.harness.compare \
  --scenario tests/orientation/scenarios/level_flight.json \
  --run-dir build/orientation/runs/level_flight_headless \
  --baseline-dir tests/orientation/baselines/level_flight/golden
```

Engine adapters are intentionally thin. The headless adapter is the PR-safe gate;
Unreal/Godot/Unity runtime lanes can emit the same snapshot JSON files and reuse
`compare.py`.
