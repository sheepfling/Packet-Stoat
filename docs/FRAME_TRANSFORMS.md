# Frame transforms

DIS Entity State PDU locations are not ordinary game-world coordinates. The
`location` field in the fastdis transform/snapshot structs is parsed as
geocentric Cartesian / ECEF meters. A game engine usually wants a local world
space near an exercise area.

`include/fastdis/fastdis_frames.hpp` adds a header-only conversion layer:

```text
ECEF meters -> local ENU meters about explicit WGS-84 origin -> engine axes/units
```

## Frame definitions

fastdis uses these definitions for engine integration:

| Source/target | Axes and units |
|---|---|
| DIS Entity State location | ECEF / geocentric Cartesian meters |
| Local scenario frame | ENU meters about an explicit WGS-84 origin |
| Unreal | `+X` north, `+Y` east, `+Z` up, centimeters |
| Godot | `+X` east, `+Y` up, `-Z` north, meters |

## WGS-84 origin

Choose an origin near the exercise area:

```cpp
fastdis::frames::LocalEnuFrame frame =
    fastdis::frames::LocalEnuFrame::from_degrees(29.5597, -95.0831, 0.0);
```

The origin should be stable for a scenario. Moving it while entities are active
will move the whole rendered world unless the engine also performs an origin
rebasing step.

Current tests cover:

- Houston / Ellington-style origin.
- Equator and prime meridian origin.
- Mid-latitude origin.
- Near-pole stress origin.
- ECEF -> ENU -> ECEF roundtrips.
- Local north/east/up sanity checks.

## Unreal mapping

Unreal default world space is treated as:

```text
+X = north / forward
+Y = east / right
+Z = up
units = centimeters
```

So local ENU meters map to Unreal like this:

```text
ENU east  -> Unreal +Y * 100
ENU north -> Unreal +X * 100
ENU up    -> Unreal +Z * 100
```

Usage:

```cpp
fastdis::frames::UnrealPoseData pose =
    fastdis::frames::to_unreal_pose(frame, snapshot);
```

## Godot mapping

Godot default 3D world space is treated as:

```text
+X = east / right
+Y = up
-Z = north / forward
units = meters
```

So local ENU meters map to Godot like this:

```text
ENU east  -> Godot +X
ENU north -> Godot -Z
ENU up    -> Godot +Y
```

Usage:

```cpp
fastdis::frames::GodotPoseData pose =
    fastdis::frames::to_godot_pose(frame, snapshot);
```

## Orientation policy

Position conversion is deterministic. Rotation conversion is not enabled by
default because the DIS orientation fields, entity model forward axes, and engine
asset forward axes must all agree.

The safe default is:

```cpp
fastdis::frames::OrientationPolicy::PositionOnly
```

An opt-in approximation is available:

```cpp
fastdis::frames::OrientationPolicy::ExperimentalLocalYawPitchRoll
```

This interprets `psi/theta/phi` as local yaw/pitch/roll in the local ENU frame
and converts the result into engine axes. Treat this as a useful starter until it
is validated against known-good traffic, instrumented traces, or a reference DIS
viewer.

The API also exposes:

```cpp
fastdis::frames::OrientationPolicy::ValidatedDisBodyFrame
```

That policy now routes through the canonical DIS body-frame pipeline:

```text
DIS psi/theta/phi -> body FRD in ECEF -> body FRU in local ENU -> engine basis/quaternion
```

It is still not the default engine-adapter path. Treat it as the strict
body-frame interpretation for cases where you want DIS-referenced orientation
instead of the local heading/pitch/roll approximation, and keep validating it
against known-good exercise traces before advertising it as generally safe for
all assets and traffic profiles.

## Asset basis

Engine transforms are only half of the orientation problem. Meshes and prefabs
can use different forward/up axes. The frame helpers expose explicit asset-basis
types so adapters can require a deliberate choice:

```cpp
enum class AssetForwardAxis {
    PositiveX,
    NegativeX,
    PositiveY,
    NegativeY,
    PositiveZ,
    NegativeZ
};

enum class AssetUpAxis {
    PositiveX,
    NegativeX,
    PositiveY,
    NegativeY,
    PositiveZ,
    NegativeZ
};
```

Unreal samples should default to `+X` forward and `+Z` up. Godot samples should
document the imported model basis and remap explicitly when it differs from the
engine convention. Do not enable orientation in demos without stating the asset
basis.

## Why explicit frames matter

Avoid this anti-pattern:

```cpp
ActorLocation = FVector(dis.location.x, dis.location.y, dis.location.z);
```

That puts ECEF meters directly into a centimeter or meter game world, usually
millions of units from the origin. It also ignores handedness and up-axis
differences. Always choose a georeference origin and convert through local ENU.
