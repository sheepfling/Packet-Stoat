# Unreal GRILL Swap Plan

This document defines how FastDIS should build parallel Unreal functionality so
it can replace GRILL in GRILL-shaped projects without forcing users to rebuild
their content workflow.

## Goal

Make FastDIS swappable into the GRILL Unreal example pattern by preserving the
authoring experience users care about:

- entity-type to actor mapping
- first-packet auto-spawn
- stable Entity ID to actor tracking
- easy actor/mesh reuse
- live receive and send components in a level-driven setup

The point is not to clone GRILL internals. The point is to let a GRILL-style
project move onto the FastDIS runtime with minimal content churn.

## Product Claim

Target claim:

> FastDIS can power the same Unreal object-mapping workflow users expect from
> GRILL while replacing the ingest/runtime path with a verified native-first
> core.

That is stronger than "we also have an Unreal plugin." It means the content and
workflow moat is no longer exclusive to GRILL.

## What Users Actually Care About

From the GRILL Unreal example, the sticky value is not only packet support. The
sticky value is:

- drop a manager into the level
- assign an enumeration mapping asset
- receive traffic
- auto-spawn recognizable actors and meshes
- keep entities bound to stable DIS IDs

FastDIS already has part of this:

- `UFastDisWorldSubsystem`
- `UFastDisEntityManagerComponent`
- `UFastDisEntityMappingDataAsset`
- UDP receiver and sender components
- PDU event components

The missing work is compatibility and polish around the authoring surface.

## Swappability Definition

FastDIS is "swappable" in a GRILL-shaped project when all of the following are
true:

1. A user can reuse the same actor Blueprints and mesh content from a GRILL
   example project.
2. A user can express entity-type mappings with the same level of convenience
   as GRILL's enumeration mapping asset.
3. Live Entity State traffic auto-spawns mapped actors and updates them through
   stable Entity ID bindings.
4. Remove Entity and stale-timeout behavior are configurable and deterministic.
5. The setup path is simple enough that a GRILL user does not feel they are
   rebuilding their project architecture from scratch.

## Compatibility Strategy

Build a parallel FastDIS authoring layer that mirrors the useful GRILL concepts.

### Layer 1: Runtime Equivalence

Use the existing FastDIS runtime as the real backend:

- `UFastDisWorldSubsystem` owns ingest and latest-state application
- `UFastDisEntityManagerComponent` owns spawn/update/remove
- `UFastDisUdpReceiverComponent` and `UFastDisUdpSenderComponent` own transport

Do not replace these with GRILL-like internals.

### Layer 2: Authoring Compatibility

Add a GRILL-shaped surface on top:

- `AFastDisGameManagerActor`
- `UFastDisEnumerationMappingAsset`
- `UFastDisReceiveFacadeComponent`
- `UFastDisSendFacadeComponent`

These should feel familiar to GRILL users while delegating to FastDIS runtime
components.

### Layer 3: Migration Tooling

Add tooling that reduces manual remapping:

- import GRILL mapping definitions from config or source asset exports
- generate a FastDIS mapping asset
- validate referenced actor classes still exist
- report unmapped enumerations

The migration layer is what makes "swappable" real instead of aspirational.

## Required Parallel Features

### 1. FastDIS Game Manager Actor

Provide a single actor that bundles the common FastDIS runtime components for a
GRILL-style level setup.

Responsibilities:

- host receiver, sender, PDU events, entity manager, georeference adapter
- expose one place for network settings
- expose one mapping asset reference
- expose one diagnostics snapshot surface
- provide one-click setup for a level
- expose transport through stable facade components so GRILL-shaped Blueprints
  do not have to bind directly to FastDIS transport classes

This is the GRILL comfort layer. It should not become the authoritative runtime
store. The world subsystem remains authoritative.

### 2. Enumeration Mapping Asset Parity

Extend or complement `UFastDisEntityMappingDataAsset` so it reaches GRILL-grade
utility.

Required behaviors:

- many enumerations may map to one actor class
- actor rows may preserve source class paths without forcing immediate manual rebinding
- wildcard matching
- most-specific match wins
- stable tie-break rules
- optional friendly display name
- optional scale override
- optional fallback actor class

Current FastDIS mapping already supports specificity matching. The next step is
to make migration and authoring as easy as GRILL's mapping asset.

### 3. Entity ID and Lifecycle Parity

FastDIS must preserve the convenience of GRILL's Entity ID tracking while
keeping the cleaner FastDIS architecture.

Requirements:

- stable `EntityId -> Actor` map
- auto-spawn on first relevant packet
- explicit preplaced actor registration path
- explicit Remove Entity handling
- stale timeout handling
- unregister on actor destruction
- deterministic cleanup on shutdown

### 4. Mesh and Blueprint Reuse

The GRILL example's visual appeal comes from content, not parser architecture.

FastDIS should be able to spawn:

- the same Blueprint actor classes
- the same skeletal/static mesh wrappers
- the same missile and vehicle content

This means the swap plan should target reuse of content paths and actor classes,
not replacement of asset libraries.

### 5. Setup Wizard and Importer

Add editor tooling that turns migration into a bounded task.

Desired commands:

- create FastDIS manager in current level
- create FastDIS mapping asset
- import GRILL mapping manifest
- audit actor-class references
- run swap smoke test
- scaffold swap benchmark baseline
- run swap benchmark comparison

The current editor-surface route is now explicit:

- `UFastDisFabAssetLibrary::CreateGameManagerActorInEditorWorld`
- `UFastDisFabAssetLibrary::CreateEnumerationMappingAssetFromJson`
- `AFastDisGameManagerActor::SetEnumerationMappingAsset`
- `AFastDisGameManagerActor::GetEnumerationMappingAsset`

## Implementation Plan

### Phase A: Mapping Surface Parity

Ship a stronger FastDIS mapping asset and resolution path.

Exit criteria:

- one actor class may represent many entity types
- wildcard matching is supported
- specificity rules are deterministic
- mapping resolution is covered by automated tests

### Phase B: GRILL-Shaped Manager Actor

Ship `AFastDisGameManagerActor` as the level-facing setup surface.

Exit criteria:

- one actor exposes receive/send/mapping/georeference basics
- auto-spawn path works without manual subsystem wiring
- demo level can be configured from this actor alone

### Phase C: GRILL Mapping Import Route

Build a source-route importer for GRILL mappings.

Candidate inputs:

- `DefaultGame.ini` `DISClassMappings`
- exported asset metadata
- hand-authored YAML/JSON manifest

Exit criteria:

- importer creates a FastDIS mapping asset or intermediate manifest
- report shows imported, missing, and unresolved actor classes

### Phase D: Neutral Swap Operator Surface

Make the whole lane read like a FastDIS swap workflow instead of a one-off
competitor bridge.

Required operator commands:

- `python tools/unreal_workflow.py swap-baseline-init`
- `python tools/unreal_workflow.py swap-smoke`
- `python tools/unreal_workflow.py swap-benchmark`

The `grill-*` command names should remain supported as explicit aliases because
the current public source route is still GRILL. The recommended operator path,
docs, and automation should prefer the neutral `swap-*` names so the lane stays
parallel and swappable end to end.

Current implementation:

- `tools/run_grill_unreal_mapping_export.py`
- `tools/import_unreal_grill_mapping_manifest.py`
- `UFastDisEntityMappingDataAsset` rows can now preserve GRILL source class
  paths alongside hard actor references
- `UFastDisFabAssetLibrary::CreateEnumerationMappingAssetFromJson`
- `python tools/unreal_workflow.py swap-smoke --engine-version 5.8`
- `python tools/unreal_workflow.py swap-mapping-materialize --engine-version 5.8 --input-manifest artifacts/reports/unreal_grill_swap/fastdis_mapping_manifest.json`
- `python tools/unreal_workflow.py swap-mapping-export --engine-version 5.8`
- `python tools/unreal_workflow.py swap-mapping-import --input path/to/grill_mapping_export.json`
- `python tools/unreal_workflow.py grill-swap-smoke --engine-version 5.8`
- `python tools/unreal_workflow.py grill-mapping-materialize --engine-version 5.8 --input-manifest artifacts/reports/unreal_grill_swap/fastdis_mapping_manifest.json`
- `python tools/unreal_workflow.py grill-mapping-export --engine-version 5.8`
- `python tools/unreal_workflow.py grill-mapping-import --input path/to/grill_mapping_export.json`

The `swap-*` names are the preferred operator-facing entrypoints because they
describe the product behavior instead of the competitor. The `grill-*` names
remain as explicit aliases for source-route work and historical reproducibility.

Current scope:

- exports the public GRILL Unreal mapping asset from a real Unreal project
  through Unreal Python into normalized JSON
- accepts an exported JSON manifest mirroring `UDISClassEnumMappings`
- emits a FastDIS-ready intermediate mapping manifest
- provides a one-command swap smoke lane that runs export, import, and
  materialization in order
- emits JSON/Markdown audit reports
- preserves GRILL's later-row duplicate override behavior through FastDIS row
  priorities
- can validate imported actor-class paths against one or more host project or
  plugin roots
- can materialize a real `UFastDisEnumerationMappingAsset` inside a GRILL-shaped
  temp project with the FastDIS plugin mounted in parallel

Still missing:

- richer project-aware validation beyond on-disk actor-class existence

### Phase D: Example Project Swap Proof

Prove the concept in a GRILL-shaped host project.

Preferred proof:

- reuse GRILL example actor classes and content
- disable GRILL runtime path
- enable FastDIS runtime path
- drive the same sample traffic
- verify spawn/update/remove behavior

Exit criteria:

- mapped actors spawn under FastDIS
- entity IDs remain stable
- at least one aircraft and one ground unit prove visual reuse

### Phase E: Benchmark Harness Integration

Fold the swap layer into the competitor benchmark program.

Required outputs:

- `swappable_demo_smoke.json`
- `mapping_import_report.json`
- `grill_content_reuse_report.json`

This lets FastDIS prove not only speed, but migration viability.

## Verification

Automated checks should cover:

- mapping resolution precedence
- wildcard resolution
- entity spawn on first packet
- actor reuse after repeated updates
- Remove Entity handling
- stale timeout behavior
- actor destruction unregister path
- importer correctness from a pinned GRILL source manifest

Manual/demo checks should cover:

- aircraft mapping
- ground vehicle mapping
- missile mapping
- diagnostics visibility
- same actor content moving under FastDIS

## Advertising Angle

If this lands, the message is simple and strong:

- GRILL showed the market the right Unreal workflow
- FastDIS keeps that workflow
- FastDIS replaces the backend with a verified native-first runtime
- FastDIS is therefore easier to adopt than a from-scratch alternative

That is a much better position than arguing only about parser speed.

## Gold Blurb

FastDIS for Unreal should not force teams to choose between a modern verified
runtime and the easy object-mapping workflow that made GRILL compelling. The
goal is a swappable FastDIS Unreal lane that preserves GRILL-style
enumeration-to-actor mapping, first-packet spawning, stable Entity ID tracking,
and content reuse, while moving ingest, latest-state handling, and verification
onto the FastDIS core. When complete, a GRILL-shaped Unreal project should be
able to keep its meshes, Blueprints, and mapping habits and simply change the
runtime underneath.
