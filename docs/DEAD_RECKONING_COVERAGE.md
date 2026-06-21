# Dead-Reckoning Coverage

This report is the generated tracking surface for FastDIS dead-reckoning compliance.
It is intentionally stricter than the current implementation: every standard algorithm row must have explicit behavior across C, C++, Python, Unreal, Godot, Unity, and Lattice before the report reaches 100%.

## Summary

- Overall status: `partial`
- Algorithm rows: `10`
- Compliant rows: `0`
- Surface compliance: `41.67%`
- Passing surface cells: `50 / 120`

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
| 0 | `OTHER` | `partial` | Other / unspecified | 5/12 | `algorithmic_c`, `algorithmic_cpp`, `algorithmic_python`, `unreal_runtime_scene`, `godot_runtime_scene`, `unity_runtime_scene`, `lattice_metadata` |
| 1 | `STATIC` | `partial` | Static | 5/12 | `algorithmic_c`, `algorithmic_cpp`, `algorithmic_python`, `unreal_runtime_scene`, `godot_runtime_scene`, `unity_runtime_scene`, `lattice_metadata` |
| 2 | `DRM_FPW` | `partial` | Fixed position, world orientation | 5/12 | `algorithmic_c`, `algorithmic_cpp`, `algorithmic_python`, `unreal_runtime_scene`, `godot_runtime_scene`, `unity_runtime_scene`, `lattice_metadata` |
| 3 | `DRM_RPW` | `partial` | Rotation, fixed position, world orientation | 5/12 | `algorithmic_c`, `algorithmic_cpp`, `algorithmic_python`, `unreal_runtime_scene`, `godot_runtime_scene`, `unity_runtime_scene`, `lattice_metadata` |
| 4 | `DRM_RVW` | `partial` | Rotation and velocity, world coordinates | 5/12 | `algorithmic_c`, `algorithmic_cpp`, `algorithmic_python`, `unreal_runtime_scene`, `godot_runtime_scene`, `unity_runtime_scene`, `lattice_metadata` |
| 5 | `DRM_FVW` | `partial` | Velocity, world coordinates | 5/12 | `algorithmic_c`, `algorithmic_cpp`, `algorithmic_python`, `unreal_runtime_scene`, `godot_runtime_scene`, `unity_runtime_scene`, `lattice_metadata` |
| 6 | `DRM_FPB` | `partial` | Fixed position, body orientation | 5/12 | `algorithmic_c`, `algorithmic_cpp`, `algorithmic_python`, `unreal_runtime_scene`, `godot_runtime_scene`, `unity_runtime_scene`, `lattice_metadata` |
| 7 | `DRM_RPB` | `partial` | Rotation, fixed position, body orientation | 5/12 | `algorithmic_c`, `algorithmic_cpp`, `algorithmic_python`, `unreal_runtime_scene`, `godot_runtime_scene`, `unity_runtime_scene`, `lattice_metadata` |
| 8 | `DRM_RVB` | `partial` | Rotation and velocity, body coordinates | 5/12 | `algorithmic_c`, `algorithmic_cpp`, `algorithmic_python`, `unreal_runtime_scene`, `godot_runtime_scene`, `unity_runtime_scene`, `lattice_metadata` |
| 9 | `DRM_FVB` | `partial` | Velocity, body coordinates | 5/12 | `algorithmic_c`, `algorithmic_cpp`, `algorithmic_python`, `unreal_runtime_scene`, `godot_runtime_scene`, `unity_runtime_scene`, `lattice_metadata` |

## Current Boundary

FastDIS currently proves field parsing and first-stage linear snapshot extrapolation. It does not yet prove full DIS algorithm-specific dead reckoning, runtime engine scenes, or Lattice dead-reckoning metadata propagation.

To drive this to 100%, implement the missing surfaces listed above and rerun:

```bash
python tools/generate_dead_reckoning_coverage.py
python tools/check_generated_fresh.py
```
