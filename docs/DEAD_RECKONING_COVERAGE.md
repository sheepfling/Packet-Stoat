# Dead-Reckoning Coverage

This report is the generated tracking surface for FastDIS dead-reckoning compliance.
It is intentionally stricter than the current implementation: every standard algorithm row must have explicit behavior across C, C++, Python, Unreal, Godot, Unity, and Lattice before the report reaches 100%.

## Summary

- Overall status: `compliant`
- Algorithm rows: `10`
- Compliant rows: `10`
- Surface compliance: `100.0%`
- Passing surface cells: `120 / 120`

## Surface Legend

- `standard_enum_accounted`
- `c_field_parse`
- `cpp_field_parse`
- `python_field_parse`
- `linear_fallback`
- `algorithmic_c`
- `algorithmic_cpp`
- `algorithmic_python`
- `unreal_runtime_scene`
- `godot_runtime_scene`
- `unity_runtime_scene`
- `lattice_metadata`

## Algorithm Matrix

| Value | Symbol | Status | Name | Passing surfaces | Missing surfaces |
| ---: | --- | --- | --- | ---: | --- |
| 0 | `OTHER` | `compliant` | Other / unspecified | 12/12 | none |
| 1 | `STATIC` | `compliant` | Static | 12/12 | none |
| 2 | `DRM_FPW` | `compliant` | Fixed position, world orientation | 12/12 | none |
| 3 | `DRM_RPW` | `compliant` | Rotation, fixed position, world orientation | 12/12 | none |
| 4 | `DRM_RVW` | `compliant` | Rotation and velocity, world coordinates | 12/12 | none |
| 5 | `DRM_FVW` | `compliant` | Velocity, world coordinates | 12/12 | none |
| 6 | `DRM_FPB` | `compliant` | Fixed position, body orientation | 12/12 | none |
| 7 | `DRM_RPB` | `compliant` | Rotation, fixed position, body orientation | 12/12 | none |
| 8 | `DRM_RVB` | `compliant` | Rotation and velocity, body coordinates | 12/12 | none |
| 9 | `DRM_FVB` | `compliant` | Velocity, body coordinates | 12/12 | none |

## Current Boundary

FastDIS has explicit dead-reckoning behavior for every tracked algorithm row across C, C++, Python, Unreal, Godot, Unity, and Lattice surfaces.

The runtime scenes use the shared native evaluator as the parity oracle; they should not duplicate dead-reckoning math in engine-specific code.
