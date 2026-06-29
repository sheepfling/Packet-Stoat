# GRILL Comparison Policy

This note defines how FastDIS should treat GRILL source-route gaps in testing,
benchmarking, and product messaging.

## Current Verified Gaps

As of 2026-06-26, the current public GRILL source routes show two different
comparison boundaries on the local Mac benchmark host:

- Unity public source route now imports and benchmark-captures on the current
  Unity `6000.5.0f1` host/editor combination, but the direct FastDIS-vs-GRILL
  Unity comparator still lacks publishable matched metrics.
- Unreal public source route is source-available but Windows-only in the
  checked-in public plugin payload.

Pinned evidence:

- Unity import smoke:
  `verification_reports/unity_grill_baseline/grill_unity_import_smoke.json`
- Unity benchmark baseline:
  `verification_reports/unity_grill_baseline/grill_unity_benchmark_baseline.json`
- Unity `.unitypackage` import smoke:
  `verification_reports/unity_grill_baseline/unitypackage_probe/grill_unity_import_smoke.json`
- Unreal Linux package proof:
  `verification_reports/unreal_grill_baseline/grill_unreal_linux_build_proof.json`
- Unreal source smoke:
  `verification_reports/unreal_grill_baseline/grill_unreal_source_smoke.json`
- Unreal mapping export failure:
  `verification_reports/unreal_grill_baseline/grill_mapping_export_report.json`
- Unreal mapping materialize failure:
  `verification_reports/unreal_grill_baseline/grill_mapping_materialize_report.json`

The Unreal finding is not speculative. The public source route itself shows:

- `WhitelistPlatforms = Win64` in the plugin modules
- Win64-only third-party binary payload
- Win64-only OpenDIS import-library linkage in `DISRuntime.Build.cs`
- live UE `5.8` Mac runs fail with `missing-game-module` after Unreal skips the
  public GRILL plugins as engine-version incompatible and reports unloadable
  GRILL example assets

Separately, the local portability branch has now proven that the GRILL Unreal
plugin can be repackaged for Linux from a Mac host via Docker. That is valid
installability evidence, but it is not yet runtime benchmark evidence and must
not be conflated with same-host FastDIS-vs-GRILL performance claims.

## What Counts As A Real Gap

FastDIS may treat a GRILL limitation as a product gap when all of the
following are true:

1. The limitation is observed on GRILL's pinned public source route or pinned
   official package route.
2. The failure is recorded by a reproducible artifact in this repo.
3. The statement is scoped to the route that was actually tested.

Valid example:

- "The current public GRILL Unreal source route is Windows-only."

Invalid example:

- "GRILL does not support Mac."

The second claim is broader than the evidence.

## Testing Workaround Policy

Two workaround paths are allowed, but they serve different purposes.

### 1. Honest Competitor Capture

Use a GRILL-compatible host and capture the competitor there.

This is the preferred path for publishable benchmark evidence.

Examples:

- run `grill_unreal` on Windows
- run `grill_unity` on a Unity host/editor combination where the public route
  imports and produces a matched benchmark scenario with comparable metrics

This preserves the integrity of same-host or same-host-class head-to-head
reports.

### 2. Research Port

Locally patch the GRILL source route to explore feasibility on another host.

Examples:

- remove Unreal `Win64` allowlists
- swap in Mac or Linux third-party binaries
- adjust Unity import path or legacy project settings

This path is allowed for internal research only. It does not count as GRILL's
public product surface and must not be used for public head-to-head claims
without very explicit labeling.

## Messaging Policy

The gap is useful in product messaging, but only if phrased precisely.

Safe claim patterns:

- "FastDIS publishes source-first cross-engine benchmark evidence, while the
  current public GRILL Unreal source route is Windows-only."
- "FastDIS can be built and verified from a Mac host across more target lanes."
- "FastDIS favors pinned, reproducible build and verification workflows across
  engines."

Unsafe claim patterns:

- "GRILL Unreal has no Mac support."
- "FastDIS is better than GRILL because GRILL is Windows-only."
- "FastDIS beats GRILL everywhere."

The safe angle is installability, reproducibility, and claim discipline, not
vague superiority language.

## Advertising Angle

This gap should be treated as a differentiator in three specific areas:

- installability: FastDIS aims to prove more host/build routes from one
  workstation
- verification: FastDIS publishes failure artifacts when competitor routes do
  not run
- cross-engine consistency: FastDIS is building one benchmark program and one
  report contract across all supported surfaces

That is stronger than saying only that FastDIS is "cross-platform."

## Required Benchmark Behavior

When a GRILL route fails on the current host:

- keep the FastDIS engine report current
- publish the GRILL failure artifact
- mark the head-to-head lane blocked
- avoid ratio claims from non-comparable runs
- capture the GRILL lane later on a compatible host

This keeps the benchmark program honest while still turning the gap into
useful evidence.
