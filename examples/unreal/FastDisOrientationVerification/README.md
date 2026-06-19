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
UnrealEditor-Cmd FastDisOrientationVerification.uproject \
  -ExecCmds="Automation RunTests FastDis.Orientation; Quit" \
  -unattended -nop4 -nosplash
```

## Verification Contract

The test module must load:

```text
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
