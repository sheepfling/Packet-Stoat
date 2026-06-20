# Orientation Pipeline Report

- generated_at: `2026-06-19T20:25:16.523007+00:00`
- fixtures: `tests/data/orientation_engine_cases.json`

## Good Configs

- Unreal pass cases: `9` / `9`
- Godot pass cases: `9` / `9`

## Known Bad

- signature: `asset_front_mismatch`
- suggestion: Check asset.forward_axis / asset.up_axis in the config.

## Solver

1. forward=negative_z up=positive_y max_err=0.0000 pass_count=9
2. forward=negative_x up=positive_y max_err=90.0000 pass_count=0
3. forward=positive_x up=positive_y max_err=90.0000 pass_count=0
4. forward=positive_x up=negative_z max_err=90.0000 pass_count=0
5. forward=negative_y up=negative_z max_err=90.0000 pass_count=0

## Config Snapshots

- unreal_good: `configs/orientation/unreal_standalone_neu_cm.yaml` `sha256:7ddcef59770b466a8d275ebeab61a04d47a8bcaaa3d6651846624be6ac46e4d0`
- godot_good: `configs/orientation/godot_standalone_enu_m.yaml` `sha256:e90fd8aceee0d00af42f78193fbb979c5912ac9650676dc0f8ee6ea316e17402`
- godot_known_bad: `tests/orientation_known_bad/godot_forward_inverted.yaml` `sha256:dce2938e363547bbff227eed4857668cabee9e6872e36105c22960f88456ba8c`

## Trace Artifacts

- good_trace: `verification_reports/alpha3_current/orientation_trace_godot_good_level_north.json`
- bad_trace: `verification_reports/alpha3_current/orientation_trace_godot_bad_level_north.json`

## Trace Diff

- changed_vectors: `2`
- diff_artifact: `verification_reports/alpha3_current/orientation_diff_godot_level_north.json`
