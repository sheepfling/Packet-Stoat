# Orientation Visual Report

- generated_at: `2026-06-19T20:25:16.605706+00:00`
- host_platform: `macos`
- unreal_engine_versions: `5.8`

| Lane | Status | Cases | Max Angle (deg) | Min Dot | Notes |
| --- | --- | --- | --- | --- | --- |
| unreal-5.8 | passed | 9 | 0.00000764 | 1.00000000 | none |
| godot | passed | 9 | 0.00000771 | 1.00000000 | none |

## Projection Reviews

| Review | Status | Images | Max Projection Error (px) | Notes |
| --- | --- | --- | --- | --- |
| unreal/good | passed | 27 | 0.000 | none |
| godot/good | passed | 27 | 0.000 | none |
| unreal/known_bad | expected-fail-observed | 27 | 206.732 | known-bad signature should fail: north_east_swap |
| godot/known_bad | expected-fail-observed | 27 | 220.000 | known-bad signature should fail: asset_front_mismatch |

## Config Snapshots

- unreal_good: `configs/orientation/unreal_standalone_neu_cm.yaml` `sha256:7ddcef59770b466a8d275ebeab61a04d47a8bcaaa3d6651846624be6ac46e4d0`
- godot_good: `configs/orientation/godot_standalone_enu_m.yaml` `sha256:e90fd8aceee0d00af42f78193fbb979c5912ac9650676dc0f8ee6ea316e17402`
- unreal_known_bad: `tests/orientation_known_bad/unreal_north_east_swap.yaml` `sha256:33dcbdaf79477a22fd944e87b15f153d7a9c07cf8befbf37b0a082a84901d943`
- godot_known_bad: `tests/orientation_known_bad/godot_forward_inverted.yaml` `sha256:dce2938e363547bbff227eed4857668cabee9e6872e36105c22960f88456ba8c`

## Raw Artifacts

- unreal 5.8 raw output: `verification_reports/alpha3_current/unreal_orientation_visual_5_8.log`
- unreal 5.8 harness log: `verification_reports/alpha3_current/unreal_orientation_visual_harness_5_8.log`
- godot raw output: `verification_reports/alpha3_current/godot_orientation_visual.log`
- visual contact sheet: `verification_reports/alpha3_current/orientation_visual_review/index.html`
