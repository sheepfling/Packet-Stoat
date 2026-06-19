# Unreal adapter scaffold

The Unreal scaffold lives in:

```text
examples/unreal/FastDis/
```

It is a Runtime plugin skeleton with one module, `FastDisUnreal`, and a world
subsystem:

```cpp
UFastDisWorldSubsystem
```

The subsystem owns:

```text
fastdis::Scanner
fastdis::EntityTable
fastdis::SnapshotBuffer
```

and applies changed snapshots to actors registered by DIS Entity ID.

## Important naming detail

The Unreal module is named `FastDisUnreal`, not `FastDis`, to avoid a macro name
collision. Unreal generates a module export macro such as `FASTDISUNREAL_API`,
while `fastdis/fastdis.h` defines its own C ABI macro named `FASTDIS_API`.

## Third-party layout

Copy fastdis headers and binaries into the plugin:

```text
Plugins/FastDis/ThirdParty/fastdis/include/fastdis/*.h(pp)
Plugins/FastDis/ThirdParty/fastdis/lib/Win64/fastdis.lib
Plugins/FastDis/ThirdParty/fastdis/bin/Win64/fastdis.dll
Plugins/FastDis/ThirdParty/fastdis/lib/Linux/libfastdis.so
Plugins/FastDis/ThirdParty/fastdis/lib/Mac/libfastdis.dylib
```

`FastDisUnreal.Build.cs` stages the platform dynamic library and links the import
library/shared object.

## Runtime flow

```text
UDP/replay bridge
  -> fastdis packet views
  -> UFastDisWorldSubsystem::IngestPacketViews
  -> native latest-state table
  -> double-buffer changed snapshots
  -> UFastDisWorldSubsystem::ApplyLatestSnapshots
  -> registered AActor transforms
```

## Frame conversion

Configure a WGS-84 origin before applying traffic:

```cpp
FFastDisGeoreference Ref;
Ref.LatitudeDegrees = 29.5597;
Ref.LongitudeDegrees = -95.0831;
Ref.HeightMeters = 0.0;
Ref.bApplyOrientation = false;
Subsystem->ConfigureGeoreference(Ref);
```

Default mapping:

```text
local ENU meters -> Unreal centimeters
north -> +X
 east -> +Y
   up -> +Z
```

Keep `bApplyOrientation=false` until the orientation convention is validated for
your exercise and content pipeline.

## Orientation verification

Alpha 2 tracks in-engine orientation verification separately from native math
tests. The Unreal harness lives at:

```text
examples/unreal/FastDisOrientationVerification/
```

It loads shared fixtures from `tests/data/orientation_engine_cases.json` and
compares Unreal actor basis vectors numerically:

```text
GetActorForwardVector() -> unreal_forward
GetActorRightVector()   -> unreal_right
GetActorUpVector()      -> unreal_up
```

Run shape:

```bash
UnrealEditor-Cmd FastDisOrientationVerification.uproject \
  -ExecCmds="Automation RunTests FastDis.Orientation; Quit" \
  -unattended -nop4 -nosplash
```

Orientation remains opt-in until this harness validates the adapter-produced
`FTransform`, not just the standalone frame math.
