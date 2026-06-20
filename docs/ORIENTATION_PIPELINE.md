# Orientation Pipeline

Alpha 3 should not treat orientation conversion as one opaque
`DIS -> Unreal/Godot` helper. It should be a named pipeline with explicit
stages, trace output, and adapter configuration.

The rule is:

```text
canonical math stays small, boring, and heavily tested
adapter corrections stay explicit, named, and configurable
```

Do not hide engine/asset fixes inside the canonical DIS decode.

## Named Stages

The pipeline should decompose into:

1. raw DIS orientation
2. canonical body basis in ECEF
3. local ENU body basis
4. target engine basis
5. asset basis correction
6. final actor/node transform

That means the conceptual flow is:

```text
raw DIS psi/theta/phi
  -> canonical body FRD basis in ECEF
  -> body basis in local ENU
  -> target engine basis before asset correction
  -> asset-corrected engine basis
  -> final engine pose
```

## Canonical vs Adapter Layer

Canonical math:

- DIS `psi/theta/phi` -> body FRD basis in ECEF
- ECEF -> local ENU
- ENU -> target engine basis

Adapter layers:

- engine frame profile
- asset forward/up basis
- optional fixed post-engine correction
- Cesium vs standalone profile
- explicit experimental override

If Godot renders mirrored, do not patch the canonical DIS decode blindly.
Prefer adjusting:

- target frame profile
- asset basis
- explicit post-engine correction

## Pipeline Trace

Every conversion should be able to emit a structured trace.

Suggested API shape:

```cpp
fastdis::orientation::PipelineConfig config =
    fastdis::orientation::PipelineConfig::UnrealStandaloneNEU();
fastdis::orientation::PipelineTrace trace;
auto pose = fastdis::orientation::convert(
    snapshot.transform,
    config,
    &trace);
```

Suggested trace fields:

```text
input
stage_1_dis_body_ecef
stage_2_body_enu
stage_3_engine_basis_before_asset
stage_4_asset_corrected_basis
final
```

Each stage should carry:

- basis vectors
- determinant
- handedness
- orthogonality / dot matrix
- optional quaternion or matrix form

The trace must be human-readable enough to diagnose:

- forward/right inversion
- north/east swap
- reflection (`determinant = -1`)
- wrong asset-front assumption

## PipelineConfig

Alpha 3 should move toward a structured orientation recipe object instead of
only hard-coded presets.

Suggested shape:

```cpp
namespace fastdis::orientation {
struct AxisMap {
    AxisTarget east;
    AxisTarget north;
    AxisTarget up;
};

struct AssetBasis {
    SignedAxis forward;
    SignedAxis up;
};

struct Correction {
    bool enabled = false;
    Quat post_engine_rotation;
    std::string reason;
};

struct PipelineConfig {
    Georeference origin;
    TargetEngine engine;
    TargetFrameProfile frame_profile;
    AxisMap axis_map;
    AssetBasis asset_basis;
    Correction correction;
    OrientationPolicy policy;
};

struct PipelineTrace {
    // named intermediate stages and diagnostics
};
}
```

Preset constructors should still exist:

- `PipelineConfig::UnrealStandaloneNEU()`
- `PipelineConfig::UnrealCesiumESU()`
- `PipelineConfig::GodotStandaloneENU()`
- `PipelineConfig::UnityStandaloneEUN()`
- `PipelineConfig::CesiumJsENU()`

But the config must remain inspectable and editable.

## Config Files

Expected config directory:

```text
configs/orientation/
```

Suggested examples:

- `unreal_standalone_neu_cm.yaml`
- `unreal_cesium_esu_cm.yaml`
- `godot_standalone_enu_m.yaml`
- `unity_standalone_eun_m.yaml`
- `cesiumjs_enu_ecef.yaml`

These config files should describe:

- source orientation interpretation
- local frame origin/profile
- target engine axis mapping
- body-to-engine mapping
- asset forward/up conventions
- explicit correction layer

## Scoring

Every fixture/target/config combination should produce numeric scores:

- `forward_angle_error_deg`
- `right_angle_error_deg`
- `up_angle_error_deg`
- `max_axis_error_deg`
- `position_error`
- `orthogonality_error`
- `determinant_error`
- `handedness_ok`
- `visual_projection_error_px`

The report should help diagnose likely problems, not only say PASS/FAIL.
Pipeline reports should also embed the config snapshot that produced the result,
not just a hash or filename, so a review artifact remains self-describing after
it leaves the repo.

## Diffability

Pipeline changes should support before/after trace diffs.

That makes it obvious whether a change affected:

- canonical DIS decode
- local-frame conversion
- engine-frame mapping
- asset correction

If a fix only needs to change asset forward/up basis, the canonical stages
should remain untouched.

## Review Rule

Code review should enforce a bright line:

- if a fix changes canonical DIS decode math, it must be justified by oracle /
  golden / SciPy / SymPy evidence
- if a fix changes only one engine or asset convention, prefer an adapter
  config or preset change

This is how Alpha 3 avoids "fixing Godot by breaking Unreal."
