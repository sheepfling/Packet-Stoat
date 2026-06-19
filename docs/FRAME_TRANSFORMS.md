# Frame transforms

DIS Entity State PDU locations are not ordinary game-world coordinates. The
`location` field in the fastdis transform/snapshot structs is parsed as
geocentric Cartesian / ECEF meters. A game engine usually wants a local world
space near an exercise area.

`include/fastdis/fastdis_frames.hpp` adds a header-only conversion layer:

```text
ECEF meters -> local ENU meters about explicit WGS-84 origin -> engine axes/units
```

## WGS-84 origin

Choose an origin near the exercise area:

```cpp
fastdis::frames::LocalEnuFrame frame =
    fastdis::frames::LocalEnuFrame::from_degrees(29.5597, -95.0831, 0.0);
```

The origin should be stable for a scenario. Moving it while entities are active
will move the whole rendered world unless the engine also performs an origin
rebasing step.

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
fastdis::frames::OrientationPolicy::LocalYawPitchRoll
```

This interprets `psi/theta/phi` as local yaw/pitch/roll in the local ENU frame
and converts the result into engine axes. Treat this as a useful starter until it
is validated against known-good traffic, instrumented traces, or a reference DIS
viewer.

## Why explicit frames matter

Avoid this anti-pattern:

```cpp
ActorLocation = FVector(dis.location.x, dis.location.y, dis.location.z);
```

That puts ECEF meters directly into a centimeter or meter game world, usually
millions of units from the origin. It also ignores handedness and up-axis
differences. Always choose a georeference origin and convert through local ENU.
