# Product Backlog

FastDIS uses two product epics to keep near-term Unreal work and long-term DIS
coverage from competing for the same definition of done.

## Epic 1: Unreal GRILL DIS Parity First

Goal blurb:

FastDIS becomes a drop-in Unreal DIS runtime product comparable to GRILL DIS for
the publicly visible Unreal/Fab surface: live UDP receive/send, auto-spawned
entity lifecycle, Blueprint and C++ events for the GRILL PDU set, practical
georeference options, a polished demo map, installable plugin packaging, and
clear setup documentation.

This epic is first because it turns the Unreal plugin from a scaffold into a
usable product. Full DIS semantics continue in Epic 2, but GRILL parity is the
first product gate.

### Milestone 1: GRILL Core Receive Parity

Goal blurb:

An Unreal user can install the plugin, receive live DIS UDP traffic, watch
Entity State traffic create and update actors, and see entity removal handled by
an explicit lifecycle policy. Replay and UDP traffic share the same ingest path.

Acceptance:

- `UFastDisUdpReceiverComponent` receives live UDP and feeds
  `UFastDisWorldSubsystem`.
- `UFastDisUdpSenderComponent` sends raw PDUs and validated Entity State sample
  traffic.
- `UFastDisEntityManagerComponent` auto-spawns actors from first-seen Entity
  State traffic.
- `UFastDisEntityMappingDataAsset` supports hierarchical Entity Type matching
  and fallback actor classes.
- Remove Entity supports Destroy, Hide, MarkStale, and Ignore policies.
- Entity State and Entity State Update both reach the native table/snapshot
  path.
- Blueprint events exist for entity discovered, updated, removed, and malformed
  PDU paths.

### Milestone 2: GRILL PDU Surface Parity

Goal blurb:

The Unreal plugin surfaces the same practical PDU families GRILL advertises,
even when some PDUs initially expose typed event summaries instead of full
semantic body models.

Acceptance:

- Entity State updates actor transforms through the native prefix/snapshot path.
- Entity State Update patches existing entity snapshots without erasing fields
  the update PDU does not carry.
- Remove Entity emits decoded lifecycle events and applies the configured
  policy.
- Fire and Detonation emit decoded gameplay-friendly event structs.
- Start/Resume and Stop/Freeze emit typed exercise-control events.
- Electromagnetic Emission, Signal, and Designator emit typed event structs with
  raw-sidecar preservation for fields that are not semantically decoded yet.
- `UFastDisPduEventComponent` exposes the GRILL parity PDU list to Blueprint and
  C++.

### Milestone 3: Fab Product Parity

Goal blurb:

FastDIS ships as a real Unreal plugin package, not a repo-local development
artifact. A user can unzip it into a project, open the demo map, start live or
replay traffic, and verify behavior without running repository build scripts.

Acceptance:

- The packaged plugin zip has polished metadata and no sample-only wording.
- Sample content is included behind `CanContainContent=true`, with
  `AFastDisDemoController` as the source-backed demo entry point.
- A demo map shows live UDP, replay ingest, actor auto-spawn, Fire, Detonation,
  Remove Entity, and a Designator marker.
- A UI widget shows receiver state, packet rate, known entities, malformed
  count, and last PDU type using `UFastDisRuntimeStatusWidget` and
  `UFastDisRuntimeMonitorComponent`.
- Georeference setup works with native FastDIS WGS-84 settings and an optional
  reflection adapter for Unreal/Cesium georeference source objects.
- A five-minute setup guide, screenshots, and release packaging notes exist.
- The [Unreal Fab asset worklist](UNREAL_FAB_ASSET_WORKLIST.md) is complete.
- Supported Unreal versions are explicit.
- The GitHub release artifact and Fab candidate package are produced by the same
  packaging flow.
- `python tools/check_unreal_fab_readiness.py` reports
  `fab_ready`, and `python tools/check_unreal_fab_readiness.py --strict`
  passes when required authored assets, screenshots, docs, package metadata,
  and verification hooks are present.

### Milestone 4: Beat GRILL Differentiators

Goal blurb:

After parity is credible, FastDIS should win on evidence, determinism,
performance, and cross-engine portability rather than only matching GRILL's PDU
surface.

Acceptance:

- Deterministic replay verification is documented and runnable.
- Packet inspector and runtime logging surfaces are available.
- Fuzz, generated coverage, and evidence-pack receipts back published claims.
- Optional Unreal Georeferencing and Cesium adapters exist without making either
  dependency mandatory.
- Godot and Unity adapters reuse the same generated contracts.
- Lattice/Zorn bridge behavior is documented as an optional integration path.
- The [Epic 1 differentiator audit](EPIC1_DIFFERENTIATOR_AUDIT.md) lists each
  differentiator, its evidence, and the command that verifies it.

## Epic 2: Full DIS 6/7 PDU Feature Buildout

Goal blurb:

FastDIS grows from GRILL-parity Unreal product into generated full DIS 6/7
product coverage. Every one of the 141 versioned DIS 6/7 PDU rows has a strict
classification, safe ingest, endpoint behavior, logging behavior, unknown-value
policy, test coverage, and a path toward typed semantic parse/serialize
support.

This epic should not wait for perfect body decoding of every message. The first
target is honest generated coverage for all rows; semantic depth grows by PDU
wave.

### Milestone 1: 141-Row Generated Truth Table

Goal blurb:

The generated manifests are the source of truth for every DIS 6/7 row and fail
the build when a row lacks an explicit product decision.

Acceptance:

- Every row has a strict Entity, Task, Object, Observation, Control, Event, or
  RawSidecar classification.
- Every row has endpoint behavior for Python, Unreal, Godot, Unity, and
  Lattice/Zorn.
- Every row has logging behavior, support level, lossy policy, and unknown enum
  policy.
- Generated docs report gaps by row, bucket, endpoint, and support level.
- CI fails if a known row has `none` behavior.

### Milestone 2: Generic Wire And Field Coverage

Goal blurb:

Every known PDU can be received, header-validated, length-checked, field-visited
where the IR supports it, roundtripped byte-preserving where safe, logged, and
surfaced to endpoints without crashing or silently disappearing.

Acceptance:

- Generic packet views exist for all cataloged rows.
- Shallow fuzz fixtures cover every row.
- Unknown and locally extended enum values are preserved numerically.
- Raw-sidecar preservation exists for rows that cannot yet be losslessly mapped.
- Python, Unreal, Godot, Unity, and Lattice/Zorn have at least generic behavior
  for every row.

### Milestone 3: Typed Semantic PDU Waves

Goal blurb:

Typed parse/serialize support grows in product-useful waves rather than by
hand-written one-offs.

Acceptance:

- Wave 1 covers state and lifecycle PDUs.
- Wave 2 covers warfare and visual-effect PDUs.
- Wave 3 covers radio, sensor, EW, IFF, and designator PDUs.
- Wave 4 covers simulation-management PDUs.
- Wave 5 covers logistics, minefield, environmental, aggregate, relationship,
  and information-operations PDUs.
- Each typed wave includes semantic roundtrip tests, fuzz coverage, generated
  docs, and endpoint events.

### Milestone 4: Cross-Engine And Lattice/Zorn Parity

Goal blurb:

Generated contracts keep Unreal, Godot, Unity, Python, C, C++, and Lattice/Zorn
surfaces consistent instead of letting each endpoint invent its own PDU behavior.

Acceptance:

- Engine adapters consume the same generated PDU catalog and logging catalog.
- C, C++, Python, Unreal, Godot, and Unity expose equivalent result semantics
  for typed rows.
- Lattice/Zorn mappings declare strict full-duplex, lossy ingress, lossy egress,
  observation-only, or raw-sidecar behavior for every row.
- Parity tests compare representative outputs across languages and endpoints.

### Milestone 5: Evidence And Release Gates

Goal blurb:

Published claims are backed by generated artifacts that a user can rebuild
locally.

Acceptance:

- Evidence-pack generation includes PDU status, endpoint behavior, ABI surface,
  benchmark receipts, replay receipts, and engine verification receipts.
- Docs link checks, generated freshness checks, lint, native tests, Python
  tests, Unreal package verification, and product inspection run as release
  gates.
- Build products are inspected for secrets, stale generated files, invalid
  cross-compile outputs, and unexpected versioned artifacts.

## Ordering Rule

Epic 1 is the first product gate. Epic 2 continues in parallel where it feeds
Epic 1, but FastDIS should not claim full product readiness until Unreal GRILL
parity is demonstrable through the Fab-style package and demo workflow.
Full DIS 6/7 product coverage remains an Epic 2 claim even after Epic 1 is
green.
