# Orientation Verification Report

- generated_at: `2026-06-19T20:25:16.449919+00:00`
- host_platform: `macos`
- status: `passed`

## Golden Fixture

- fixture: `tests/data/orientation_golden_cases.json`
- schema: `fastdis.orientation_golden_cases.v1`
- case_count: `6`
- max DIS angle error: `0.000000000000 deg`
- max reference DIS angle error: `0.030079293039 deg`
- max forward roundtrip error: `0.000000000000 deg`
- max right roundtrip error: `0.000000000000 deg`
- max down roundtrip error: `0.000000000000 deg`

## Shared Engine Fixture

- fixture: `tests/data/orientation_engine_cases.json`
- schema: `fastdis.orientation_engine_cases.v1`
- case_count: `9`
- max standalone Unreal basis error: `0.000000000000 deg`
- max standalone Godot basis error: `0.000000000000 deg`
- max CesiumJS basis error: `0.000000000000 deg`
- max Cesium Unity basis error: `0.000000000000 deg`
- max Cesium Unreal basis error: `0.000000000000 deg`
- equator georeference component error: `0.000000000000e+00`

## Randomized Properties

- seed: `1278`
- iterations: `250`
- max forward roundtrip error: `0.000000000000 deg`
- max right roundtrip error: `0.000000853774 deg`
- max down roundtrip error: `0.000000000000 deg`
- min basis determinant: `1.000000000000`
- max basis determinant deviation: `4.440892098501e-16`

This report proves the shared orientation fixtures, independent oracle, Cesium target-frame mappings, and randomized roundtrip properties from the current source tree. It does not replace Unreal/Godot runtime harness reports.
