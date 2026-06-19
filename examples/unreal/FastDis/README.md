# FastDIS Unreal scaffold

This is a tiny Unreal Runtime plugin scaffold that consumes the fastdis C++ RAII
layer and double-buffer snapshots.

It is intentionally not a full networking plugin. Feed `UFastDisWorldSubsystem`
packet views from your preferred UDP receiver, replay reader, or simulation
bridge. The subsystem does the fastdis portion:

```text
packet burst -> native latest-state table -> double-buffer changed snapshots -> registered actors
```

## Sample Traffic Component

`UFastDisSampleTrafficComponent` is a small runtime smoke path for Rider and
editor bring-up. Add it to an actor in the generated host project or a real
project, then call `InjectSamplePacket` from Blueprint or C++. The component
registers its owner with `UFastDisWorldSubsystem`, builds a synthetic DIS 7
Entity State PDU, feeds it through the native scanner, and applies the resulting
snapshot.

## Third-party layout

The repo helper can stage this layout for you:

```bash
python tools/build_unreal_plugin.py --clean-package
```

That command builds/stages the current host-native fastdis library and packages
the plugin through Unreal AutomationTool. It also creates a stable local host
project for Rider/editor use at:

```text
build/unreal/FastDisHostProject/HostProject.uproject
```

If you want Rider to open that host project after packaging:

```bash
python tools/build_unreal_plugin.py --clean-package --open-rider
```

The staged third-party payload lives under:

```text
Plugins/FastDis/ThirdParty/fastdis/include/fastdis/*.h(pp)
Plugins/FastDis/ThirdParty/fastdis/lib/Win64/fastdis.lib
Plugins/FastDis/ThirdParty/fastdis/bin/Win64/fastdis.dll
Plugins/FastDis/ThirdParty/fastdis/lib/Linux/libfastdis.so
Plugins/FastDis/ThirdParty/fastdis/lib/Mac/libfastdis.dylib
```

## Frame mapping

DIS Entity State `location` is ECEF/geocentric meters. Unreal is local
left-handed Z-up centimeters. This scaffold therefore requires a WGS-84 origin:

```cpp
FFastDisGeoreference Ref;
Ref.LatitudeDegrees = 29.5597;
Ref.LongitudeDegrees = -95.0831;
Ref.HeightMeters = 0.0;
Ref.bApplyOrientation = false;
Subsystem->ConfigureGeoreference(Ref);
```

The default mapping is position-only:

```text
local ENU meters -> Unreal centimeters
north -> +X
 east -> +Y
   up -> +Z
```

Orientation is intentionally opt-in. Set `bApplyOrientation=true` only after
validating your DIS orientation convention and asset forward axes against known
traffic.
