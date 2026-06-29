# GRILL Harness Capture Standard

GRILL Unity and Unreal comparison lanes now have a shared raw capture contract:

- `schemas/json/fastdis.grill_harness_capture.v1.schema.json`

This is the raw competitor-harness layer that sits before:

- `fastdis.engine_benchmark_report.v1`
- `fastdis.engine_head_to_head_report.v1`
- benchmark matrix and storefront comparison outputs

## Purpose

The raw GRILL capture contract exists so Unity and Unreal harnesses emit one
typed shape for:

- pinned repository and plugin provenance
- host and engine/runtime version
- scenario/environment labeling
- measured benchmark rows

That prevents each engine route from inventing its own baseline JSON.

## Required Top-Level Fields

- `schema`
- `lane`
- `product`
- `captured_at_utc`
- `repository`
- `host`
- `runtime`
- `scenario`
- `results`

## Lane Values

- `unity_vs_grill`
- `unreal_vs_grill`

## Runtime Fields

Required:

- `engine_family`
- `version`

Optional:

- `render_pipeline`
- `scripting_backend`
- `build_configuration`
- `plugin_commit`
- `plugin_version`

## Scenario Fields

Required:

- `environment_name`
- `traffic_mix`

Optional:

- `entity_counts`
- `update_hz`
- `notes`

## Result Row Fields

Every row must have:

- `scenario`

Rows may then populate the measured fields that apply on that engine route:

- packet counts
- queue/drop counts
- ingest latency percentiles
- `main_thread_apply_ms`
- `steady_state_gc_bytes`
- `packets_per_sec`

Unity and Unreal do not need to invent separate row field names anymore.

## Migration

Legacy files remain accepted:

- `fastdis.unity_grill_benchmark_baseline.v1`
- `fastdis.unreal_grill_benchmark_baseline.v1`

They are canonicalized into `fastdis.grill_harness_capture.v1` during
normalization so current workflows keep working.

New harness and addon routes should emit `fastdis.grill_harness_capture.v1`
directly.
