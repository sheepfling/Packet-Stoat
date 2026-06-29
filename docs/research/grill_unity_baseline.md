# GRILL Unity Baseline

This file freezes the public comparison frame for the Unity parity lane. It is
not a marketing claim; it is the baseline FastDIS must meet or exceed before it
claims Unity product parity.

## Baseline Pin

- Repository: `AF-GRILL/DISPluginForUnity`
- Observed commit: `e362bb477cc84806db783830443974db70284f8b`
- Asset Store version: `pin-required`
- Unity editor version used for comparison: `6000.5.0f1` for current local import smoke
- Capture date: `2026-06-25`

Until those pins are filled in, this document is a planning baseline rather
than a release-proof baseline.

## Current Local Import Smoke

Current local Mac evidence is captured in:

- `verification_reports/unity_grill_baseline/grill_unity_import_smoke.json`
- `verification_reports/unity_grill_baseline/grill_unity_import_smoke.md`

Current result:

- GRILL was cloned and imported into a scratch Unity project on macOS.
- With the available local editor (`6000.5.0f1`), Unity never created the
  project `Library/` directory.
- The login-shell launch timed out after emitting `attempt to write a readonly database`.
- The Launch Services fallback failed immediately with `kLSNoExecutableErr`.

This is installation evidence, not a throughput benchmark. A real GRILL
benchmark baseline still requires a host/editor combination that can complete
project import.

## Source Route

The benchmark program should now treat the AF-GRILL GitHub organization as the
primary public source route for GRILL, not just the Unity package drop.

Current relevant public repos:

- `AF-GRILL/DISPluginForUnity`
- `AF-GRILL/DISForUnityExample`

Current local evidence now includes both:

- a source checkout at `external/grill/GRILL_DISPluginForUnity`
- a Unity package at `/Users/rick/Downloads/grill_dis_for_unity.unitypackage`

Both routes currently fail import smoke on this Mac with Unity `6000.5.0f1`,
which means the Unity lane is source-available but still host-blocked rather
than blocked on missing GRILL source.

## Publicly Documented GRILL Surface

The public baseline captured for planning is:

- UDP receive over unicast, multicast, and broadcast-shaped workflows
- Entity spawning and Entity ID to GameObject mapping
- Dead reckoning and smoothing
- Ground clamping and georeference conversion helpers
- Timeout and removal behavior
- Threshold and heartbeat-based Entity State transmission

The documented core PDU set to match first is:

- `Entity State`
- `Entity State Update`
- `Remove Entity`
- `Fire`
- `Detonation`
- `Designator`
- `Electromagnetic Emission`
- `Signal`
- `Start/Resume`
- `Stop/Freeze`

## FastDIS Current Read

The current FastDIS Unity lane already proves a smaller but real runtime slice:

- native C ABI packaged through UPM
- loopback UDP receive into `FastDisWorld`
- replay ingest through `FastDisReplayPlayer`
- `Entity State`, `Entity State Update`, and `Remove Entity` handling through
  the native scanner and latest-state table
- basic auto-spawn and simple entity-to-prefab mapping
- package doctor, startup probe, install smoke, runtime verification, and
  orientation verification entrypoints

The current gap is that networking parity and gameplay-workflow parity are not
yet complete. There is no finished multicast/broadcast/send lane, no verified
stale-timeout lifecycle, and no finished dead-reckoning/heartbeat publisher
surface.

## Exit Discipline

A Unity feature is not done because a class exists. A row is only parity-ready
when all of these are true:

- implementation exists
- automated test exists
- verification entrypoint exists
- sample or demo exists
- documentation exists

The machine-readable gate for that rule lives in
`docs/research/unity_grill_parity.yaml` and is enforced by
`python tools/check_unity_parity.py --milestone <milestone>`.

## Repro Commands

```bash
python tools/run_grill_unity_import_smoke.py --unity-version 6000.5
python tools/init_unity_grill_benchmark_baseline.py --unity-version 6000.5.0f1 --scene LoopbackBench --traffic-mix "100% Entity State" --overwrite
```

Unity package route:

```bash
python tools/run_grill_unity_import_smoke.py \
  --unity-version 6000.5.0f1 \
  --plugin-root /Users/rick/Downloads/grill_dis_for_unity.unitypackage \
  --out-dir verification_reports/unity_grill_baseline/unitypackage_probe
```
