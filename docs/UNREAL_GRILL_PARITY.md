# Unreal GRILL Parity Matrix

FastDIS treats GRILL parity as a product-runtime target, not just a plugin
scaffold target. The Unreal plugin now has live UDP receive/send components,
Blueprint PDU event surfaces, replay ingest, Entity State snapshot application,
and first-seen Entity State auto-spawn support.

The backlog owner for this work is
[Epic 1: Unreal GRILL DIS Parity First](PRODUCT_BACKLOG.md#epic-1-unreal-grill-dis-parity-first).

This matrix is intentionally strict about the difference between a surfaced PDU
event and a rich body decoder.

| Capability | Unreal surface | Status | Notes |
| --- | --- | --- | --- |
| Fab-installable plugin zip | `tools/build_unreal_plugin.py`, `tools/unreal_workflow.py` | present | Package tooling builds the plugin with sample content, screenshots, docs, metadata, and ThirdParty native payloads. Publication is still a release action, not a runtime capability. |
| Live UDP receive | `UFastDisUdpReceiverComponent` | present | Nonblocking socket pump feeds `UFastDisWorldSubsystem` and Blueprint PDU events. |
| Live UDP send | `UFastDisUdpSenderComponent` | present | Raw DIS send plus Entity State send validation. |
| Replay ingest | `AFastDisReplayActor` | present | Replay and UDP feed the same subsystem ingest path. |
| Entity State update | `UFastDisWorldSubsystem` | present | Native scanner/table/snapshot path updates registered actors. |
| Entity State Update | native compact transform path | present | ESU patches the existing entity table snapshot without wiping fields ESU does not carry. |
| Entity State auto-spawn | `UFastDisEntityManagerComponent` | present | First-seen Entity State transform events resolve mapping rows or spawn a default actor class. |
| Preplaced actor / ID registration | `UFastDisEntityManagerComponent` | present | Explicit `RegisterManagedActor`, `UnregisterManagedActor`, and lookup helpers preserve object-to-Entity-ID workflows when content should stay in place rather than auto-spawn. |
| Remove Entity lifecycle | `EFastDisRemoveEntityPolicy` | present | Supports Destroy, Hide, MarkStale, and Ignore policies. |
| Entity Type mapping | `UFastDisEntityMappingDataAsset` | present | Hierarchical wildcard rows resolve actor classes from hard refs or soft class paths before falling back to the default class. |
| GRILL-shaped mapping asset | `UFastDisEnumerationMappingAsset` | present | Familiar enumeration-to-actor asset name delegates to the same FastDIS mapping resolution path, and can now be materialized from imported GRILL JSON through `UFastDisFabAssetLibrary`. |
| GRILL-shaped manager actor | `AFastDisGameManagerActor` | present | One level actor bundles receive, send, PDU events, entity manager, georeference, and runtime monitoring. It now also mirrors GRILL's manager lookup, entity-map helpers, identity fields, socket-list setup surface, and direct enumeration-mapping handoff through `GetFastDisGameManager`, `AddManagedEntityToMap`, `RemoveManagedEntityFromMap`, `ReceiveSocketsToSetup`, `SendSocketsToSetup`, `SetEnumerationMappingAsset`, and `GetEnumerationMappingAsset`. |
| GRILL-shaped transport facades | `UFastDisReceiveFacadeComponent`, `UFastDisSendFacadeComponent` | present | Stable level-facing receive/send surfaces mirror the common UDP settings while delegating to the shared FastDIS transport components. |
| GRILL-shaped editor setup helper | `UFastDisFabAssetLibrary::CreateGameManagerActorInEditorWorld` | present | The editor library can now spawn a prewired FastDIS manager actor in the current world and optionally bind a materialized `UFastDisEnumerationMappingAsset`, which makes the swap lane reproducible as a concrete authoring flow instead of just a runtime claim. |
| GRILL-shaped swap smoke lane | `python tools/unreal_workflow.py swap-smoke --engine-version 5.8` | present | One command now exports the public GRILL mapping asset, imports it into the FastDIS manifest shape, and materializes a real `UFastDisEnumerationMappingAsset` so the swap path stays reproducible. The older `grill-swap-smoke` name remains as an explicit source-route alias. |
| GRILL-shaped swap benchmark lane | `python tools/unreal_workflow.py swap-baseline-init`, `python tools/unreal_workflow.py swap-benchmark` | present | The comparison/bootstrap commands now follow the same neutral `swap-*` naming as the mapping lane. The older `grill-baseline-init` and `grill-benchmark` names remain as explicit source-route aliases because the current benchmark baseline still comes from the public GRILL route. |
| Blueprint PDU events | `UFastDisPduEventComponent` | present | Typed summary event layer for the GRILL PDU list, with raw sidecars preserved. |
| Runtime monitor | `UFastDisRuntimeMonitorComponent` | present | Blueprint-readable receiver state, packet counters, malformed counters, known entities, and last PDU details for demo/UI widgets. |
| Runtime status widget | `UFastDisRuntimeStatusWidget` | present | Code-backed UMG base widget exposes monitor text and snapshot data for the Fab demo UI. |
| Georeference | `FFastDisGeoreference`, `UFastDisGeoreferenceAdapterComponent` | present | Native WGS-84/ECEF to Unreal local frame exists; optional Unreal/Cesium georeference sources can be reflected without hard dependencies. |
| PDU debug markers | `UFastDisPduDebugMarkerComponent` | present | Source-backed Fire, Detonation, and Designator marker actors demonstrate decoded event surfacing without claiming full effects. |
| Demo controller | `AFastDisDemoController` | present | Placeable source-backed actor wires receiver, sender, PDU events, sample traffic, and runtime monitor. |
| Demo source-shell automation | `FastDis.Demo.FabSourceShell` | present | Editor automation verifies the source-backed controller, status widget, sample Entity State packet, georeference adapter, and monitor path without requiring pending binary assets. |
| Demo map/content | plugin content | present | Descriptor has `CanContainContent=true`; the package includes the demo map, controller Blueprint, status widget Blueprint, mapping data asset, screenshots, and setup docs. |
| Fab readiness report | `tools/check_unreal_fab_readiness.py` | present | Strict readiness reports `fab_ready` when the source shell, authored demo assets, screenshots, docs, package metadata, and verification hooks are present. |

The remaining authored content is tracked in the
[Unreal Fab asset worklist](UNREAL_FAB_ASSET_WORKLIST.md).
Differentiator claims are tracked in the
[Epic 1 differentiator audit](EPIC1_DIFFERENTIATOR_AUDIT.md).

## PDU Surface

| PDU | PDU type | Runtime surface | Body depth |
| --- | ---: | --- | --- |
| Entity State | 1 | actor transform + Blueprint event | native Entity State prefix/snapshot |
| Fire | 2 | Blueprint event | decoded typed summary + raw sidecar |
| Detonation | 3 | Blueprint event | decoded typed summary + raw sidecar |
| Start/Resume | 7 | Blueprint event | decoded typed summary + raw sidecar |
| Stop/Freeze | 8 | Blueprint event | decoded typed summary + raw sidecar |
| Remove Entity | 12 | Blueprint event | decoded typed summary + raw sidecar |
| Electromagnetic Emission | 23 | Blueprint event | decoded typed summary + raw sidecar |
| Designator | 24 | Blueprint event | decoded typed summary + raw sidecar |
| Signal | 26 | Blueprint event | decoded typed summary + raw sidecar |
| Entity State Update | 67 | actor transform + decoded Blueprint event | native compact transform patch |

## Remaining Work

- Keep the [Fab Product Parity](PRODUCT_BACKLOG.md#milestone-3-fab-product-parity)
  package green as Unreal versions and generated native payloads change.
- Expand Start/Resume, Stop/Freeze, Electromagnetic Emission, Signal, and
  Designator from compact typed summaries into richer semantic body models when
  native generated parsers land.
- Add typed hard integrations for Unreal Georeferencing and Cesium only if the
  project later needs compile-time integration beyond the current reflection
  adapter.
- Treat Fab publication, release signing, marketplace review, and externally
  hosted release artifacts as release operations beyond this local readiness
  matrix.
- Continue Epic 2 for all-PDU semantic depth; this page only claims the GRILL
  parity PDU surface and honest typed-summary behavior.
