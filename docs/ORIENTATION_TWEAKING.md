# Orientation Tweaking Workflow

Assume the first end-to-end orientation flow will be close but wrong in one
painful way.

Alpha 3 should therefore optimize for:

- traceability
- explicit config
- deterministic scoring
- controlled experimentation

The goal is to make orientation fixes debuggable without turning the code into
untraceable sign flips.

## Stable Tweak Loop

The intended operator/developer loop is:

1. generate or load known fixtures
2. run native orientation comparison
3. run engine verification
4. generate screenshots
5. compare screenshots / axis masks
6. try named candidate config variants
7. apply an accepted config patch
8. diff traces before and after

Conceptually:

```text
fixtures
 -> compare
 -> engine verify
 -> screenshots
 -> solve candidates
 -> apply config patch
 -> diff trace
```

## Trace First

Before changing math, export a pipeline trace:

```text
fastdis-orient trace --packet <fixture> --target godot --config <config>
```

The trace should make it obvious where the error enters:

- canonical ECEF body basis
- ENU body basis
- engine basis before asset correction
- asset-corrected basis

If the determinant becomes `-1`, the issue is likely a reflection or handedness
mistake, not a valid rotation.

## Safe Tweak Layers

Alpha 3 should allow exactly three correction layers, in order:

1. engine frame profile
2. asset basis correction
3. explicit post-engine correction quaternion

The third layer should require a human-readable reason string.

Example:

```yaml
correction:
  enabled: true
  reason: "Imported aircraft asset has a baked 90 degree yaw offset."
  post_engine_euler_deg:
    yaw: 90
    pitch: 0
    roll: 0
```

Mystery rotations should never accumulate silently.

## Candidate Solver

Alpha 3 should provide a debugging tool that tries only safe, named adapter
variants and ranks them by error.

The solver must not silently mutate runtime behavior. It should only emit a
suggested config patch.

Safe search categories:

- asset forward axis candidates
- asset up axis candidates
- engine-axis sign/profile candidates
- fixed 90/180/270 degree post-rotations

The best result should be reported as a suggested config update, not applied
automatically.

## Config Snapshot in Reports

Every orientation verification report should embed the exact config used plus a
stable config hash.

Without that, a screenshot or PASS result is not reproducible.

Required report fields:

- target engine/profile
- config hash
- full config snapshot
- per-case scores

## When to Change Math vs Config

Change canonical math only when:

- SciPy/oracle/SymPy/golden fixtures prove the math is wrong

Change adapter config when:

- one engine is wrong
- one asset is wrong
- a model-import convention is wrong
- a Cesium/standalone frame profile differs

This is the main safeguard against regression across engines.
