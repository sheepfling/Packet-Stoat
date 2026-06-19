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
content out of the source bundle; create `Content/Maps/OrientationVerification`
inside Unreal when the visual scene is implemented.

## Command-Line Shape

```bash
python tools/run_unreal_orientation_verification.py
```

The helper scripts load repo-local `.env` or `.env.local` files before they
resolve Unreal paths. A minimal local setup is:

```bash
FASTDIS_UNREAL_EDITOR="/Users/Shared/Epic Games/UE_5.7/Engine/Binaries/Mac/UnrealEditor"
FASTDIS_UNREAL_ENGINE_DIR="/Users/Shared/Epic Games/UE_5.7"
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

The current automation spec now drives the real adapter helper:

```text
UFastDisWorldSubsystem::BuildDebugTransformForLocalAttitude(...)
```

It synthesizes a snapshot at the local origin, applies the Unreal adapter's
experimental local heading/pitch/roll path, and compares the resulting
transform axes to the shared fixture.

The runner script supports `--dry-run` when `UnrealEditor-Cmd` is not on PATH.
