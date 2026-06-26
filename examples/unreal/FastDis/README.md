# FastDIS Unreal plugin

This Unreal Runtime plugin consumes the fastdis C++ RAII layer, latest-state
table, and configurable snapshot buffer.

`UFastDisWorldSubsystem` is the shared ingest path for replay, live UDP, and
custom simulation bridges:

```text
packet burst -> native latest-state table -> double-buffer changed snapshots -> registered actors
```

The default demo path uses 3 snapshot slots so a delayed reader does
not immediately block the next publish.

## Live UDP

`UFastDisUdpReceiverComponent` and `UFastDisUdpSenderComponent` provide the
drop-in live DIS path:

- `StartReceiver`, `StopReceiver`, and `IsReceiverRunning`
- Blueprint-configurable bind address, port, receive buffer, and tick budget
- packet, byte, malformed, dropped, and last-endpoint stats
- `SendRawPduBytes` for any DIS packet
- `SendEntityState` for Entity State-only send validation

Attach `UFastDisPduEventComponent` to the same actor to surface Blueprint events
for Entity State, Entity State Update, Remove Entity, Fire, Detonation,
Start/Resume, Stop/Freeze, Electromagnetic Emission, Signal, and Designator
PDUs. The current event layer exposes compact typed summaries for the GRILL
parity PDU set while preserving the full raw PDU bytes on every event.

Attach `UFastDisPduDebugMarkerComponent` to the same actor to turn decoded Fire,
Detonation, and Designator event locations into simple tagged marker actors.
These are debug markers for product proof and screenshots, not full visual
effects.

Attach `UFastDisRuntimeMonitorComponent` to the same actor to expose a
Blueprint-readable status snapshot for demo UI widgets: receiver running state,
packet and byte counters, malformed and dropped counts, known entity count, and
last PDU details.

## GRILL-shaped manager actor

`AFastDisGameManagerActor` is the swappable level-facing setup surface for a
GRILL-shaped project. Place one actor and it bundles:

- `UFastDisUdpReceiverComponent`
- `UFastDisUdpSenderComponent`
- `UFastDisPduEventComponent`
- `UFastDisEntityManagerComponent`
- `UFastDisGeoreferenceAdapterComponent`
- `UFastDisRuntimeMonitorComponent`

It exposes one mapping reference, one remove-entity policy, one receive setup
surface, and one send destination surface while still delegating all ingest and
latest-state behavior to `UFastDisWorldSubsystem`.

It now also mirrors the GRILL manager pattern more directly:

- `GetFastDisGameManager` for one-manager-in-level lookup
- `ExerciseId`, `SiteId`, and `ApplicationId` identity fields
- `AutoConnectReceiveAddresses` plus `ReceiveSocketsToSetup`
- `AutoConnectSendAddresses` plus `SendSocketsToSetup`
- `AddManagedEntityToMap`, `RemoveManagedEntityFromMap`, and `GetManagedEntityActor`
- `SetEnumerationMappingAsset` and `GetEnumerationMappingAsset` for a direct
  GRILL-shaped mapping handoff path

FastDIS currently projects the first configured receive/send socket entry onto
the active shared receiver/sender components. That keeps the level-facing setup
surface swappable now without forking the backend away from
`UFastDisWorldSubsystem`.

The manager also instantiates `UFastDisReceiveFacadeComponent` and
`UFastDisSendFacadeComponent` so GRILL-shaped Blueprints can bind to stable
level-facing transport surfaces without coupling directly to the underlying
FastDIS transport classes.

`UFastDisEnumerationMappingAsset` is the GRILL-shaped asset name for the same
FastDIS wildcard/alias mapping backend. That gives migration tooling a familiar
enumeration-to-actor asset type without forking runtime behavior.

The editor utility library can also materialize that asset directly from an
imported GRILL-source manifest:

- `UFastDisFabAssetLibrary::CreateEnumerationMappingAssetFromJson`
- `UFastDisFabAssetLibrary::CreateGameManagerActorInEditorWorld`
- `python tools/unreal_workflow.py swap-baseline-init --engine-version 5.8 --map LoopbackBench --traffic-mix "100% Entity State" --overwrite`
- `python tools/unreal_workflow.py swap-benchmark`
- `python tools/unreal_workflow.py swap-smoke --engine-version 5.8`
- `python tools/unreal_workflow.py swap-mapping-materialize --engine-version 5.8 --input-manifest build/reports/unreal_grill_swap/fastdis_mapping_manifest.json`
- `python tools/unreal_workflow.py grill-baseline-init --engine-version 5.8 --map LoopbackBench --traffic-mix "100% Entity State" --overwrite`
- `python tools/unreal_workflow.py grill-benchmark`
- `python tools/unreal_workflow.py grill-swap-smoke --engine-version 5.8`
- `python tools/unreal_workflow.py grill-mapping-materialize --engine-version 5.8 --input-manifest build/reports/unreal_grill_swap/fastdis_mapping_manifest.json`

`swap-smoke` is the first-class FastDIS swap lane. The `grill-*` commands remain
as explicit source-route aliases, but the neutral `swap-*` names are the
recommended operator entrypoints. Both forms run GRILL mapping export, FastDIS
import/audit, and FastDIS materialization in sequence so the GRILL-shaped
authoring surface stays parallel to the FastDIS runtime backend.
Use `swap-baseline-init` and `swap-benchmark` for the same reason: they keep the
operator surface neutral even though the current comparison baseline is still
the public GRILL source route.

Useful Blueprint calls:

- `GetFastDisGameManager`
- `ApplyManagerSettings`
- `PullManagerSettingsFromComponents`
- `SetEnumerationMappingAsset`
- `GetEnumerationMappingAsset`
- `StartLiveReceive`
- `StopLiveReceive`
- `IsLiveReceiveRunning`
- `RefreshMonitorSnapshot`
- `GetManagedEntityCount`
- `AddManagedEntityToMap`
- `RemoveManagedEntityFromMap`
- `GetManagedEntityActor`

For a swap-style editor setup, call
`UFastDisFabAssetLibrary::CreateGameManagerActorInEditorWorld` after importing
or materializing a `UFastDisEnumerationMappingAsset`. That yields the same
"manager actor plus mapping asset" authoring shape without forking the
underlying FastDIS runtime.

## Drop-in demo controller

`AFastDisDemoController` is the source-backed Fab demo entry point. Place it in
a level to get a pre-wired receiver, sender, PDU event component, sample traffic
component, georeference adapter, and runtime monitor on one actor.

Useful Blueprint calls:

- `StartLiveReceive`
- `StopLiveReceive`
- `InjectLocalEntityState`
- `SendSampleEntityState`
- `RefreshMonitorSnapshot`

`UFastDisRuntimeStatusWidget` is a code-backed UMG widget base that can
auto-bind to the first `AFastDisDemoController` in the level, poll the runtime
monitor, and expose `GetStatusText` plus the full monitor snapshot for a custom
Blueprint widget.

The content-capable plugin also includes [five-minute setup docs](Docs/FIVE_MINUTE_SETUP.md),
[Fab draft copy](Docs/FAB_DRAFT.md), and an
[example content guide](Content/Examples/README.md) for the packaged demo map,
Blueprint assets, and screenshot captures.

## Auto-spawn entity management

`UFastDisEntityManagerComponent` listens to Entity State transform snapshots,
resolves `UFastDisEntityMappingDataAsset` rows when present, and spawns
`DefaultActorClass` as fallback for first-seen entities. It then registers those
actors with `UFastDisWorldSubsystem` so subsequent Entity State packets update
the actor through the same snapshot application path used by manually registered
actors.

Mapping rows support GRILL-shaped authoring patterns:

- one primary entity type plus alias entity types per actor class
- hard actor refs or soft class paths per mapping row
- wildcard matching through negative enum fields
- most-specific match wins
- explicit row priority breaks ties before declaration order
- optional source-route metadata so imported GRILL rows stay auditable

For swappable projects that already have placed actors or custom Blueprint
ownership rules, `UFastDisEntityManagerComponent` also exposes explicit
`RegisterManagedActor`, `UnregisterManagedActor`, `GetManagedActor`, and
`IsManagedActorRegistered` calls so an existing object/ID mapping workflow can
stay intact while the backend moves to FastDIS.

Remove Entity can be configured as `Destroy`, `Hide`, `MarkStale`, or `Ignore`.
The manager listens to decoded Remove Entity events from `UFastDisPduEventComponent`
when both components are attached to the same actor.

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
python tools/unreal_workflow.py build --engine-version 5.8
```

That command builds/stages the current host-native fastdis library and packages
the plugin through Unreal AutomationTool. It also creates a stable local host
project for Rider/editor use under the Unreal scratch root, typically:

```text
$FASTDIS_UNREAL_WORK_ROOT/FastDisHostProject/HostProject.uproject
```

If you want Rider to open that host project after packaging:

```bash
python tools/unreal_workflow.py build --engine-version 5.8 --open-rider
```

## Runtime Verification

- [Dead Reckoning Runtime Scene](RuntimeVerification/DeadReckoningRuntimeScene.md)

To prove the runnable replay path end to end from the command line:

```bash
python tools/unreal_workflow.py demo --engine-version 5.8
```

That lane generates a small synthetic replay under the Unreal scratch root and
runs an automation test that verifies `AFastDisReplayActor` moves registered
actors numerically.

The demo automation suite also includes `FastDis.Demo.FabSourceShell`, which
checks the source-backed Fab shell before authored `.umap`/Blueprint assets are
available: `AFastDisDemoController`, UDP send/receive components, Blueprint PDU
events, the georeference adapter, runtime monitor, status widget, and sample
Entity State packet.

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
left-handed Z-up centimeters. This plugin therefore requires a WGS-84 origin:

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

## Optional georeference adapter

`UFastDisGeoreferenceAdapterComponent` applies native FastDIS WGS-84
georeference settings to `UFastDisWorldSubsystem`.

Use it in either mode:

- Leave `GeoreferenceSource` unset and configure `ManualGeoreference`.
- Point `GeoreferenceSource` at an optional Unreal Georeferencing, Cesium, or
  project-specific object and set the latitude, longitude, height, and
  orientation property names.

The adapter uses Unreal reflection and does not add hard module dependencies on
Unreal Georeferencing or Cesium.
