# Alpha5 Integration Matrix

FastDIS has enough individual verification lanes that the project needs one
cross-product matrix. Generate it with:

```bash
python tools/run_alpha5_integration_matrix.py
```

Outputs:

- `build/reports/alpha5_integration_matrix.json`
- `build/reports/alpha5_integration_matrix.md`

## What It Proves

The matrix maps each consumer-facing claim to a command or test lane:

- DIS 6/7 catalog, typed envelope, semantic entry point, and logging coverage.
- Ingress through Python/C/C++ and engine workflow routes.
- Egress through Python/C/C++ and engine outbound smoke routes.
- Filtering and downsampling.
- Entity table and snapshot buffering.
- Robustness against malformed packets and schema gaps.
- Dead-reckoning field parsing.
- Generated logging contract for Unreal, Godot, and Unity.

## Current Honest Boundary

Dead reckoning is currently a partial proof. FastDIS parses the DIS Entity State
dead-reckoning fields through native and Python ctypes surfaces and supports a
first-stage linear snapshot extrapolator from the latest buffer state. Full
DIS algorithm-specific dead reckoning and engine runtime verification scenes
are not yet complete.

Engine runtime verification is host-gated. The example projects and workflow
commands exist, but Unreal/Godot/Unity pass/fail depends on local installs,
permissions, and Unity license state.
