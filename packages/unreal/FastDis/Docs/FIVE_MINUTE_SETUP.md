# FastDIS Unreal Five-Minute Setup

## Install

1. Unzip or copy the packaged `FastDis` plugin folder into
   `Project/Plugins/FastDis`.
2. Enable the plugin in Unreal and restart the editor if prompted.
3. Open or create a level for DIS testing.

You do not need repository build scripts to use the packaged plug-in.

For packaged-install proof from the shipped plugin boundary, run:

```bash
fastdis engine unreal install-smoke --engine-version 5.8
```

For repo-local demo asset regeneration while maintaining the plugin source, run:

```bash
python tools/create_unreal_fab_demo_assets.py --engine-version 5.8
```

## Add The Demo Controller

1. Place `AFastDisDemoController` in the level.
2. On `UdpReceiver`, set `BindAddress` and `Port`.
3. On `UdpSender`, set `RemoteAddress` and `RemotePort`.
4. On `GeoreferenceAdapter`, set `ManualGeoreference` or point
   `GeoreferenceSource` at an optional Unreal/Cesium georeference object.
5. On `SampleTraffic`, set `Georeference` and the sample `EntityId`.
6. Leave `DebugMarkers` enabled to visualize decoded Fire, Detonation, and
   Designator event summaries through `UFastDisPduDebugMarkerComponent`.

## Verify Local Ingest

1. Press Play.
2. Call `InjectLocalEntityState` on the demo controller from Blueprint or the
   details panel.
3. Read `RuntimeMonitor.GetLastSnapshot`.
4. Confirm `KnownEntities`, `PduEvents`, and `LastPduName` update.

## Verify Live UDP

1. Call `StartLiveReceive`.
2. Send DIS UDP traffic to the configured port.
3. Confirm packet counters, malformed counters, known entities, and last PDU
   details update in the runtime monitor.
4. Call `StopLiveReceive` when done.

## Verify Egress

1. Configure `UdpSender.RemoteAddress` and `UdpSender.RemotePort`.
2. Call `SendSampleEntityState`.
3. Confirm `PacketsSent` and `BytesSent` update in the runtime monitor.

## Next UI Step

Create a Blueprint widget derived from `UFastDisRuntimeStatusWidget`, or add the
widget class directly while prototyping. It can auto-bind to the first
`AFastDisDemoController` in the level and exposes `GetStatusText` plus the full
monitor snapshot.

Display:

- receiver running state
- packet rate
- known entities
- malformed count
- dropped count
- last PDU type and name
- Fire/Detonation/Designator debug marker count or scene markers

## Swap-Style Setup

If the goal is GRILL-style swappability rather than the demo shell:

1. Materialize or import a `UFastDisEnumerationMappingAsset`.
2. Call `UFastDisFabAssetLibrary::CreateGameManagerActorInEditorWorld`.
3. Pass the imported mapping asset path if you want the spawned manager wired in
   one step.
4. Use `SetEnumerationMappingAsset` or `GetEnumerationMappingAsset` on
   `AFastDisGameManagerActor` to keep Blueprint setup parallel to the GRILL
   manager-plus-mapping workflow.
