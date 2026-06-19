# FastDIS Unreal Orientation Verification

This is an Alpha 2 verification harness for Unreal orientation support. It is
not a gameplay demo. Its job is to prove that fastdis target-frame output
matches Unreal actor basis vectors after the transform is applied inside Unreal.

## Expected Layout

Place or symlink the runtime plugin here when running the project:

```text
examples/unreal/FastDisOrientationVerification/Plugins/FastDis/
```

The source-controlled `Source/FastDisOrientationTests` module contains the
automation-test and probe-actor scaffold. The project intentionally keeps binary
content out of the source bundle, but the visual route is now usable without a
custom map asset: open any empty level, place `AFastDisOrientationProbeActor`,
set the expected axes, and the actor will draw both basis frames plus a numeric
PASS/FAIL overlay in-world.

## Command-Line Shape

```bash
python tools/unreal_workflow.py doctor
python tools/unreal_workflow.py verify --engine-version 5.8
python tools/unreal_workflow.py full --engine-version 5.8
```

The wrapper is the preferred operator path. The lower-level runner still exists
when you want to call the harness directly:

```bash
python tools/run_unreal_orientation_verification.py
python tools/run_unreal_orientation_verification.py --engine-version 5.7
```

The helper scripts load repo-local `.env` or `.env.local` files before they
resolve Unreal paths. A minimal local setup is:

```bash
FASTDIS_UNREAL_EDITOR="/Users/Shared/Epic Games/UE_5.7/Engine/Binaries/Mac/UnrealEditor"
FASTDIS_UNREAL_ENGINE_DIR="/Users/Shared/Epic Games/UE_5.7"
```

If you keep multiple Unreal installs on one machine, add versioned variables in
`.env` or `.env.local`:

```bash
FASTDIS_UNREAL_EDITOR_5_6="/Users/Shared/Epic Games/UE_5.6/Engine/Binaries/Mac/UnrealEditor"
FASTDIS_UNREAL_ENGINE_DIR_5_6="/Users/Shared/Epic Games/UE_5.6"
FASTDIS_UNREAL_EDITOR_5_7="/Users/Shared/Epic Games/UE_5.7/Engine/Binaries/Mac/UnrealEditor"
FASTDIS_UNREAL_ENGINE_DIR_5_7="/Users/Shared/Epic Games/UE_5.7"
FASTDIS_UNREAL_EDITOR_5_8="/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor"
FASTDIS_UNREAL_ENGINE_DIR_5_8="/Users/Shared/Epic Games/UE_5.8"
```

Both `tools/run_unreal_orientation_verification.py` and
`tools/build_unreal_plugin.py` accept `--engine-version 5.6`, `5.7`, or `5.8`
and prefer the matching versioned variables before they fall back to the
default `FASTDIS_UNREAL_*` pair.

To inspect what the helper actually discovered on the current machine:

```bash
python tools/unreal_workflow.py discover
```

To run the current supported version matrix and capture a report:

```bash
python tools/unreal_workflow.py matrix
```

## Verification Contract

The test module must load the shared fixture source or the staged copy created
by `tools/sync_orientation_fixtures.py`:

```text
Tests/orientation_engine_cases.json
../../tests/data/orientation_engine_cases.json
```

For every case, apply the fastdis pose to an actor, then compare:

```text
Actor->GetActorForwardVector() against unreal_forward
Actor->GetActorRightVector()   against unreal_right
Actor->GetActorUpVector()      against unreal_up
```

Use angular vector comparisons. Do not compare Unreal Euler rotations to DIS
`psi/theta/phi`.

The runner now refreshes and verifies the staged Unreal copy plus its
`.sha256` sidecar before Unreal launches, so the automation spec cannot
silently run against stale fixture content.

The current automation spec now drives the real adapter helper:

```text
UFastDisWorldSubsystem::BuildDebugTransformForDisOrientation(...)
```

It synthesizes a snapshot at the local origin, loads `expected.dis_deg` from
the shared fixture, applies the Unreal adapter's validated DIS body-frame path,
and compares the resulting transform axes to the shared fixture.

For visual verification, `AFastDisOrientationProbeActor` now renders:

```text
solid arrows: actual forward/right/up
short arrows: expected forward/right/up
debug text: PASS/FAIL, angular errors, dot products, threshold
```

The runner script supports `--dry-run` when `UnrealEditor-Cmd` is not on PATH.
