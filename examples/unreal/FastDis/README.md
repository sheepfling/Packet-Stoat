# FastDIS Unreal sample plugin

This is a small Unreal Runtime plugin sample that consumes the fastdis C++ RAII
layer, latest-state table, and configurable snapshot buffer.

It is intentionally not a full networking plugin. Feed `UFastDisWorldSubsystem`
packet views from your preferred UDP receiver, replay reader, or simulation
bridge. The subsystem does the fastdis portion:

```text
packet burst -> native latest-state table -> double-buffer changed snapshots -> registered actors
```

The default Alpha 2 sample path uses 3 snapshot slots so a delayed reader does
not immediately block the next publish.

## Replay actor demo

`AFastDisReplayActor` turns the plugin into a runnable sample. Drop it into a
host project or a real UE project, point `ReplayFile` at a `.fastdispkt`
capture, configure entity-to-actor bindings, and press Play.

Editor-facing runtime settings now include:

- georeference origin
- position-only vs snap vs interpolate vs experimental-rotation modes
- meters-to-Unreal scale
- snapshot slot count
- stale-after-ticks eviction

The replay actor uses the same dependency-free replay format as the native C/C++
examples:

```text
repeated uint32_be packet_length + packet bytes
```

You can generate a deterministic sample replay with:

```bash
python tools/make_replay.py benchmark_results/synthetic.fastdispkt --packets 2048 --entities 8
```

Then set `ReplayFile` to `benchmark_results/synthetic.fastdispkt`, assign a few
actors in `ActorBindings`, and let the replay actor drive the subsystem each
tick.

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

When you package or manually copy the plugin into another project, keep those
host-native binaries in the plugin `ThirdParty` tree. Unreal then stages them
into `Binaries/ThirdParty/fastdis/...` for the target project at build/package
time.

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
traffic. `SnapPositionAndExperimentalRotation` is the only mode that applies
rotation today; the other modes remain position-only.
