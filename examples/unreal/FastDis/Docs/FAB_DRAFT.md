# FastDIS Unreal Fab Draft

This is draft copy for an alpha Fab submission candidate. It must stay
conservative until the packaged plug-in, listing media, and external review
path are finalized outside the repository.

Authored assets and captures are tracked in
[Unreal Fab Asset Worklist](../../../../docs/UNREAL_FAB_ASSET_WORKLIST.md).
Regenerate or refresh them with
`python tools/create_unreal_fab_demo_assets.py --engine-version 5.8` and
`python tools/capture_unreal_fab_screenshots.py --engine-version 5.8` when the
demo changes.

## Short Description

FastDIS is a DIS networking plugin for Unreal Engine with live UDP ingest and
send, replay ingest, Entity State and Entity State Update handling, auto-spawn
actor lifecycle, typed-summary Blueprint PDU event summaries with raw sidecars,
runtime status monitoring, and an optional georeference adapter.

## Claim Line

Boring core. Useful adapters. Honest coverage.

## Current Product Claims

- GRILL-target Unreal runtime parity for the practical plug-in surface:
  live UDP receive/send, replay ingest, Entity State and Entity State Update
  handling, auto-spawn lifecycle, Remove Entity policy, Blueprint PDU events,
  and runtime monitoring.
- Live UDP receive and send components.
- Replay and live traffic share the same `UFastDisWorldSubsystem` ingest path.
- Entity State and Entity State Update update actor snapshots through the native
  FastDIS table path.
- First-seen Entity State traffic can auto-spawn mapped or fallback actors.
- Remove Entity supports Destroy, Hide, MarkStale, and Ignore policies.
- Fire, Detonation, Start/Resume, Stop/Freeze, Electromagnetic Emission, Signal,
  and Designator have compact Blueprint event summaries with raw PDU bytes
  preserved.
- `UFastDisPduDebugMarkerComponent` can visualize decoded Fire, Detonation, and
  Designator event locations as source-backed debug markers.
- `AFastDisDemoController` wires receiver, sender, PDU events, georeference,
  sample traffic, runtime monitor, and status widget support.
- `UFastDisGeoreferenceAdapterComponent` can apply manual WGS-84 settings or
  reflect latitude, longitude, and height from project georeference objects.
- The Fab demo package includes `FastDis_Demo.umap`, a demo controller
  Blueprint, a runtime status widget Blueprint, an entity mapping data asset,
  setup docs, and real Unreal screenshot captures.
- Packaged-install proof exists for the shipped plugin boundary, not only the
  source tree.

## Do Not Claim Yet

- Full semantic body decoding for every DIS PDU.
- Rich gameplay-ready semantic models for every surfaced PDU event.
- A production tactical symbology renderer in core.
- Final Fab approval or marketplace availability.
- Marketplace review, signing, or externally hosted release artifacts.

## Required Final Screenshots

- Live UDP controller in the demo level.
- Runtime status widget showing receiver state, known entities, packet counts,
  malformed count, and last PDU.
- Auto-spawned entities moving from replay or live traffic.
- Fire/Detonation/Designator event debug markers.
- Plugin settings or setup view showing georeference configuration.

## Source Visuals

Use [Storefront Visuals](../../../../docs/STOREFRONT_VISUALS.md) and the source SVG
kit under `media/storefront/fab/`. Export generated PNG/JPEG files under
`build/`; do not commit rendered marketplace exports by default.
