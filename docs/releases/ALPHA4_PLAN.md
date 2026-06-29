# fastdis v0.14.0-alpha4 Plan

Theme: Lattice access-ready lab, shim/proxy seam, canonical entity bridge, and mockable integration surface.

Alpha 1 proved the architecture. Alpha 2 proved the engine-facing workflow.
Alpha 3 proved coverage, robustness, orientation correctness, and release
evidence. Alpha 4 should prove that fastdis can sit beside an external
operations platform and publish a credible entity stream out of DIS without
collapsing the native packet-processing design, while also staying useful
before any real sandbox credentials exist.

The guiding rule is:

```text
Do not weld Lattice-specific assumptions into the fastdis hot path.
Keep the DIS parser/scan/table/snapshot core generic.
Build the Lattice adapter as a separate application-facing layer over a
canonical entity bridge.
Make it access-ready:
  local fixtures, replay files, JSON, and mock services first,
  real sandbox backend later.
```

## Release Targets

- Branch: `alpha4/v0.14`
- Version: `fastdis v0.14.0-alpha4`
- Milestone: `Alpha 4`
- Headline: first access-ready Lattice bridge preview, with canonical entity
  snapshots, local mock and shim/proxy services, DIS Entity State egress, mock
  SDK coverage, and repeatable proof artifacts.

## Honest Product Claim

Alpha 4 should let the project say, precisely:

- fastdis remains a native-first DIS parsing and snapshot SDK.
- A separate Lattice adapter/application layer can publish DIS-derived entity
  state outward using a canonical entity model.
- Alpha 4 builds an access-ready lab around the adapter:
  DIS/replay/native snapshots -> canonical entity bridge -> Lattice-shaped
  payloads -> local mock or future real backend.
- Initial useful transport scope is outbound first:
  DIS/replay/native snapshots -> canonical entity bridge -> mock or real
  Lattice-style publisher.
- Reverse egress is included at fixture/mock level:
  mock Lattice-shaped entity stream -> canonical entity -> DIS Entity State.
- Full live Lattice -> DIS ingress remains future work.
- Real Lattice SDK access is not required to develop the adapter contract; mock
  transports, fixtures, and proof harnesses are first-class in this release.

## Success Criteria

- The repo has a documented Alpha 4 bridge architecture and scope guardrails.
- The repo has an explicit reference stack for:
  - DIS standards and programmer-facing references
  - public Lattice API/SDK references
  - shim compatibility tiers
- A canonical entity snapshot/schema exists between DIS, engines, and Lattice.
- A mockable Lattice adapter API exists with publish/report/error contracts.
- A local mock Lattice-style service exists for entities first, with room for
  tasks and objects.
- A local Lattice-shaped shim/proxy exists with a latest-state entity store,
  append-only event log, stream output, object/report storage, and a thin task
  mailbox.
- DIS/latest-state snapshots can be converted into canonical entities without
  depending on Unreal, Godot, or a real Lattice SDK.
- Deterministic DIS-to-Lattice identity mapping exists and is reversible enough
  for mock/fixture egress.
- An outbound Entity State encoder exists for the first Lattice -> DIS egress
  lane, even if ingress is deferred.
- Mock publisher, truth-file, and replay/UDP egress harnesses prove the bridge
  behavior end to end.
- Alpha 4 docs explain:
  what can be built now with no credentials,
  what requires real sandbox access,
  and where real SDK backends slot in later.
- Release docs clearly distinguish:
  native fastdis core,
  optional Lattice adapter app,
  mock transport,
  and future real SDK integration points.

## Workseries

### WS1: Release Branch, Scope Guardrails, and Version Bump

Goal: start Alpha 4 from a controlled release lane and keep architecture
boundaries explicit.

Tasks:
- Create `ALPHA4_PLAN.md`, `ALPHA4_GOAL.md`, and `ALPHA4_RELEASE_NOTES.md`.
- Update `docs/ROADMAP.md` so Alpha 4 becomes the active release target.
- Add a release checklist for mock SDK proof, canonical bridge evidence, and
  outbound adapter reports.

Exit criteria:
- Alpha 4 planning docs are on disk.
- Roadmap points to Alpha 4.
- Scope language explicitly says outbound first, ingress later.

### WS2: Lattice Integration Architecture and Mapping Docs

Goal: define the bridge before writing SDK-specific code.

Tasks:
- Add:
  - `docs/LATTICE_INTEGRATION.md`
  - `docs/LATTICE_ENTITY_MAPPING.md`
  - `docs/LATTICE_MOCKING.md`
  - `docs/LATTICE_DIS_BRIDGE_PLAN.md`
  - `docs/LATTICE_LAB.md`
  - `docs/LATTICE_REFERENCE_STACK.md`
- Define the first useful mappings:
  - DIS Entity State -> canonical entity
  - canonical entity -> Lattice Track-like entity payload
  - canonical entity -> DIS Entity State egress payload
- Define the shim/proxy seam:
  - publish stream semantics
  - stream/heartbeat semantics
  - object store semantics
  - task mailbox semantics
- Document the access boundary:
  - installable/public package surface vs real sandbox access
  - local mock backends vs real backend
  - entities first, tasks/objects next
- Document the compatibility policy:
  - behavior-compatible first
  - endpoint-complete never required for Alpha 4
  - wire-compatible gRPC only after semantics work
- Call out the minimum public-API-aligned field sets for:
  - entities
  - tasks
  - objects
- Keep the docs explicit that Lattice nomenclature here is an adapter/app
  contract, not a claim of official SDK parity.

Exit criteria:
- The bridge architecture is documented.
- Mapping docs exist on disk.
- Mock-vs-real SDK boundaries are explicit.
- The access-ready lab concept is documented.
- Reference-stack and compatibility-tier docs are explicit.

### WS3: Canonical Entity Bridge Model

Goal: add one stable internal/external model between DIS and higher-level
 integrations.

Tasks:
- Add canonical entity schemas/types such as:
  - `fastdis_canonical_entity_t`
  - `fastdis_canonical_track_t`
  - provenance/source metadata
- Keep the shape flat and ABI-friendly.
- Include fields for:
  - source kind/key
  - stable bridge entity ID / reverse DIS tuple identity
  - DIS site/application/entity ID
  - exercise ID
  - entity type / marking / force ID
  - world position / velocity / orientation
  - stale/live state
  - provenance timestamps
- Add JSON schema and fixture coverage.
- Add deterministic identity rules for:
  - DIS tuple -> Lattice-style `entityId`
  - mock Lattice-style entity -> DIS tuple

Exit criteria:
- Canonical entity schema exists.
- Native and Python helpers can serialize/inspect it.
- It is documented as the bridge surface between DIS, Lattice, and engines.
- Identity mapping is deterministic and testable.

### WS4: Mockable Lattice Publisher Surface

Goal: develop the adapter against a stable contract without requiring the real
 SDK.

Tasks:
- Add a mock publisher/client interface under a separate adapter namespace.
- Support:
  - publish entity
  - publish batch
  - capture sent payloads
  - inject deterministic failures/timeouts
- Split semantics explicitly:
  - `PublishEntity`-like path for validation-rich lower-rate testing
  - `PublishEntities`-like path for higher-rate/coalesced streaming
- Add backend split:
  - JSONL/local file backend
  - in-process/local HTTP mock backend
  - real backend stub gated on credentials
- Produce machine-readable report artifacts for publish attempts, successes, and
  dropped/error cases.
- Keep auth/config placeholders explicit and injectable.

Exit criteria:
- Mock publisher exists.
- Contract tests exist.
- Report artifacts make failure modes obvious.
- The real backend insertion point is obvious but not overstated.
- Single-entity vs high-rate publish semantics are documented and testable.

### WS4.5: Local Mock Lattice Service

Goal: reproduce the integration seam without real sandbox access.

Tasks:
- Add a local mock service/lab mode under `packages/lattice` or
  `packages/lattice_lab`.
- Start with entities-first support:
  - store/publish entity payloads
  - list current entities
  - stream entity updates and heartbeats
- Support only the minimal entity stream controls:
  - `preExistingOnly`
  - `heartbeatIntervalMs`
  - `componentsToInclude`
- Keep tasks/objects in scope as lab placeholders:
  - objects report/object store contract
  - tasks create/update/status contract
- Persist lab artifacts under a local scratch/report directory.

Exit criteria:
- Local mock entity service exists.
- Entity updates can be published and observed by a separate consumer.
- Tasks/objects placeholders are documented even if thinly implemented.
- Event log and stream semantics are explicit enough to back a later real
  backend.
- Entity stream controls are minimal, explicit, and proven in tests.

### WS4.6: Lattice Shim / Proxy Work Packet

Goal: stand up a high-speed local Lattice-shaped shim so fastdis can run end to
end without credentials.

Tasks:
- Add `packages/lattice_shim/` as the future real-backend seam, not just a
  throwaway test tool.
- Define local ports/interfaces:
  - `EntityPublisher`
  - `EntityStream`
  - `ObjectStore`
  - `TaskMailbox`
- Support backend modes:
  - `mock`
  - `record`
  - `replay`
  - `real`
- Keep the first implementation Python-first; only move lower-level if evidence
  requires it.

Exit criteria:
- Shim/proxy package layout exists on disk.
- Backend modes are documented.
- The bridge depends on local interfaces, not on a vendor SDK import.

### WS5: DIS / Snapshot -> Canonical Entity Conversion

Goal: make the current fastdis hot path useful to the Lattice adapter.

Tasks:
- Convert:
  - `fastdis_entity_transform_t`
  - `fastdis_entity_snapshot_t`
  into canonical entities.
- Preserve current frame/orientation caution:
  orientation should stay basis/quaternion aware, not naive Euler passthrough.
- Add fixtures for marking, force ID, entity type, stale transitions, and
  provenance timestamps.

Exit criteria:
- Conversion helpers exist.
- Tests cover new/updated/stale canonical entity output.
- The adapter does not need to parse raw DIS bytes itself.

### WS6: Outbound Lattice Egress Application

Goal: create the first operator-facing app that publishes outward.

Tasks:
- Add an operator-facing application/workflow such as:
  - `tools/lattice_workflow.py`
  - `python -m fastdis.tools.lattice_publish`
- Add operator-facing lab modes such as:
  - `dis-to-json`
  - `dis-to-mock`
  - `mock-to-dis`
  - `dis-to-shim`
  - `shim-to-dis`
- Support inputs:
  - replay file
  - localhost UDP DIS
  - native snapshot batch
- Support outputs:
  - mock publisher payload log
  - JSON report
  - optional future real SDK transport shim

Exit criteria:
- One-command outbound publish workflow exists.
- Replay -> canonical -> mock publisher path is green.
- Operator docs are clear.
- The same workflow can run entirely without SDK credentials.
- Shim/proxy-backed loop is runnable end to end.

### WS7: Canonical Entity -> DIS Entity State Egress

Goal: prepare the return path without claiming full ingress.

Tasks:
- Add an Entity State writer/encoder for the first outbound bridge path.
- Support:
  - canonical entity -> DIS Entity State bytes
  - Lattice-shaped entity/track JSON -> canonical entity -> DIS Entity State
  - replay/UDP send through existing optional networking layer
- Keep scope narrow:
  Entity State first, not all PDUs.

Exit criteria:
- Valid Entity State egress bytes can be emitted.
- Mock Lattice-style entity inputs can drive DIS UDP output.
- Tests verify header/length/basic field correctness.
- Wireshark/Open-DIS friendly verification path is documented.

### WS8: Proof, Benchmarking, and Packaging

Goal: keep Alpha 4 as evidence-driven as Alpha 3.

Tasks:
- Add proof artifacts for:
  - mock publish report
  - egress send report
  - canonical entity conversion report
  - failure injection report
  - lab entity stream report
  - identity registry report
  - shim/proxy run log
  - loop suppression report
- Add benchmark lanes for:
  - snapshot -> canonical entity conversion
  - canonical entity -> mock publish payload generation
  - canonical entity -> DIS egress encoding
  - shim publish throughput
  - shim stream throughput
  - DIS -> shim -> DIS overhead
- Add a readiness matrix:
  - works with no credentials
  - needs public package only
  - needs real sandbox token/endpoint
- Add packaging/audit docs so Alpha 4 does not overstate real SDK coverage.

Exit criteria:
- Alpha 4 proof artifact set is defined.
- Release notes call out mock-vs-real behavior honestly.
- Packaging excludes any fake secrets or host-local SDK placeholders.
- Readiness matrix is documented.

### WS9: Tasks, Objects, and Future Backend Hooks

Goal: keep Alpha 4 credible as a platform-adapter lab, not just one publisher.

Tasks:
- Define thin placeholder contracts for:
  - entities
  - tasks
  - objects
- Keep implementation priorities explicit:
  - entities: must
  - objects: should
  - tasks: could
- Mark task stream behavior as experimental where it leans on publicly Beta
  surfaces.
- Add object report examples:
  - trajectory summaries
  - orientation screenshots
  - benchmark snapshots

Exit criteria:
- Alpha 4 docs and scaffold clearly show where entities, tasks, and objects fit.
- Entities-first implementation remains the active build lane.
- Tasks/objects expectations are honest and bounded.

## Recommended Implementation Order

1. release docs and roadmap bump
2. Lattice integration + mapping docs
3. canonical entity bridge model
4. mock publisher surface
5. snapshot -> canonical conversion
6. local mock service / access-ready lab
7. shim/proxy package and interfaces
8. outbound operator workflow
9. canonical entity -> DIS egress
10. benchmarks, proof, packaging

## Initial Issue Breakdown

- `A4-001` Alpha 4 branch and release docs
- `A4-002` Lattice integration architecture docs
- `A4-003` canonical entity schema and fixtures
- `A4-004` mock publisher/client contract
- `A4-005` snapshot-to-canonical conversion helpers
- `A4-006` outbound publish workflow and JSON reports
- `A4-007` Entity State writer/egress encoder
- `A4-008` mock failure injection and retry/error reports
- `A4-009` outbound bridge benchmarks
- `A4-010` Alpha 4 release audit and bundle truthfulness
- `A4-011` local mock entity service and stream
- `A4-012` deterministic identity registry
- `A4-013` tasks/objects lab placeholders
- `A4-014` access-ready readiness matrix
- `A4-015` lattice shim/proxy package and backend modes
- `A4-016` entity stream event log and replay mode
- `A4-017` loop suppression and provenance guardrails
- `A4-018` object/report store
- `A4-019` task mailbox and task-agent skeleton
- `A4-020` shim throughput and backpressure benchmarks
- `A4-021` reference stack and compatibility policy docs
- `A4-022` public-API-minimum entity payload contract
- `A4-023` stream controls and heartbeat compatibility tests

## Definition of Done

Alpha 4 is ready when this works:

```text
DIS replay or UDP
  -> fastdis scanner/entity table/snapshots
  -> canonical entity bridge
  -> mock Lattice publish app, local mock service, or shim/proxy
  -> machine-readable proof report

mock Lattice entity fixture
  -> canonical entity
  -> DIS Entity State encode
  -> UDP/replay egress
  -> machine-readable proof report

shim/proxy task or object request
  -> local mailbox/object store
  -> evidence artifact or command event
  -> machine-readable proof report

local mock entity stream
  -> canonical entity
  -> DIS Entity State encode
  -> Unreal/Godot/Open-DIS friendly verification path
  -> machine-readable proof report
```

and the release notes can say, clearly:

- here is the canonical bridge model
- here is the access-ready lab
- here is what is mocked
- here is what is real
- here is what publishes outward today
- here is what can be proven without credentials
- here is what ingress will add later
