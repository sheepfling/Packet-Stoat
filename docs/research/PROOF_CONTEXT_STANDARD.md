# Proof Context Standard

FastDIS benchmark and proof routes need one common qualification envelope so
results from native, Python, Godot, Unity, Unreal, and competitor captures can
be compared and rendered consistently.

The standard schema is:

- `schemas/json/fastdis.proof_context.v1.schema.json`

## Purpose

The `proof_context` object exists to answer the questions that the metric row
alone cannot answer:

- what class of evidence is this
- what axis is being compared
- what scenario family does this belong to
- what host and platform class produced it
- what claim boundary applies

That makes it suitable for:

- benchmark reports
- head-to-head reports
- matrix summaries
- storefront charts
- handoff bundles

## Standard Fields

### `evidence_class`

Allowed values:

- `direct_measured`
- `truth_backed_bridge`
- `family_aligned`
- `same_host_competitor`
- `blocked`
- `workflow_install`

### `comparison_axis`

Allowed values:

- `language_surface`
- `platform_host_class`
- `engine_adapter`
- `competitor_same_host`

### `scenario_family`

Examples:

- `ingest_baseline`
- `filtering`
- `burst_latest_state`
- `replay`
- `orientation_assurance`
- `workflow_install`

### `host`

This is the normalized host summary. Use the common fields whenever known:

- `host_id`
- `host_class`
- `system`
- `system_family`
- `release`
- `machine`
- `arch`
- `python`
- `unity_version`
- `engine_version`
- `editor_path`
- `godot_path`
- `plugin_version`
- `plugin_commit`

This may still carry route-specific extensions, but the standard keys above
should be preferred.

### `platform`

Required:

- `os`
- `arch`

Recommended:

- `os_family`
- `runtime_kind`
- `engine_family`
- `build_configuration`
- `cross_compiled`

### `qualification`

Required:

- `claim_boundary`
- `comparable`

Recommended:

- `same_host`
- `same_host_class`
- `same_scenario`
- `same_metric_meaning`
- `truth_backed`
- `blocked_reason`
- `qualification_notes`

## Emission Rules

### Benchmark reports

Every route should keep the legacy top-level `host` object for compatibility.
New or upgraded routes should also emit `proof_context`.

Recommended defaults:

- `native` / `python_ctypes` measured rows:
  - `evidence_class = direct_measured`
  - `comparison_axis = language_surface`
- current `c` / `cpp` truth routes:
  - `evidence_class = truth_backed_bridge`
  - `comparison_axis = language_surface`
- current engine proof bridges:
  - `evidence_class = truth_backed_bridge`
  - `comparison_axis = engine_adapter`

### Head-to-head reports

Use:

- `left_proof_context`
- `right_proof_context`

Those should describe the host, platform, and claim qualifications for each
side before the comparator decides whether the row is directly publishable.

### Matrix summaries

Matrix surface and comparison rows should surface the normalized
`proof_context` where available, even if the source routes still carry older
host-only payloads.

## Qualification Discipline

The `proof_context` object should never be used to inflate a claim. It should
make the claim boundary more explicit.

Examples:

- a truth-backed engine route with null timing remains `truth_backed_bridge`
- a blocked GRILL Unreal route remains `blocked`
- a same-host Unity competitor row with aligned metrics becomes
  `same_host_competitor`

## Migration Path

1. Keep existing `host` fields valid in current reports.
2. Add `proof_context` to all new route normalizers.
3. Backfill matrix and chart renderers to prefer `proof_context` when present.
4. Once every route emits it, tighten more schemas around normalized host and
   qualification data.
