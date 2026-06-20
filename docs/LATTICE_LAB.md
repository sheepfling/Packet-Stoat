# Lattice lab architecture

Alpha 4 should be useful even with zero real sandbox credentials.

The correct model is an access-ready lab:

```text
fastdis core
  -> canonical entity bridge
  -> Lattice-shaped adapter contract
  -> local lab backend now
  -> real backend later
```

Alpha 4 should also treat the local service as a future shim/proxy seam:

```text
Packet-Stoat adapter
  -> EntityPublisher / EntityStream / ObjectStore / TaskMailbox ports
  -> mock / record / replay / real backend modes
```

## Why this exists

There are two different readiness levels:

1. Can we build and test the adapter seam locally?
2. Can we call a real sandbox endpoint with real credentials?

Alpha 4 must solve the first one completely.

See also:

- `docs/LATTICE_REFERENCE_STACK.md`
- `docs/LATTICE_ENTITY_MAPPING.md`
- `docs/LATTICE_DIS_BRIDGE_PLAN.md`

## Supported lab modes

- `dis-to-json`
  replay/UDP/native snapshots -> canonical entity -> stable JSON payloads
- `dis-to-mock`
  replay/UDP/native snapshots -> canonical entity -> local mock publish/service
- `mock-to-dis`
  mock Lattice-shaped entity stream/fixture -> canonical entity -> DIS Entity State
- `dis-to-shim`
  replay/UDP/native snapshots -> canonical entity -> shim publish stream
- `shim-to-dis`
  shim entity stream -> canonical entity -> DIS Entity State
- `lab-state`
  bounded object/task fixtures -> local shim object store/task mailbox -> JSON reports

Current operator commands:

```bash
python tools/lattice_workflow.py doctor
python tools/lattice_workflow.py dis-to-shim
python tools/lattice_workflow.py shim-to-dis
python tools/lattice_workflow.py lab-state
python tools/lattice_workflow.py full
```

Replay-backed `dis-to-shim` uses the native fastdis entity-table/snapshot lane,
so `python tools/lattice_workflow.py doctor` should report a discoverable native
library before relying on `.fastdispkt` replay input.

Current artifact root:

```text
verification_reports/alpha4/lattice/
```

The current operator lane now writes:

- `dis_to_shim/`
  - accepted entity store
  - stream events
  - append-only event log
- `shim_to_dis/`
  - stream events
  - canonical entities recovered from stream payloads
  - loop suppression report
  - replay `.fastdispkt` output
- `lab_state/`
  - object store manifest
  - task mailbox/status view
  - task stream events
  - append-only event log

## Compatibility target

Alpha 4 should be:

- behavior-compatible for the bridge seam
- shape-compatible with the public docs for key entity/task/object fields
- not required to be fully endpoint-complete
- not required to be fully wire-compatible yet

## Backend split

- `JsonlPublisher`
  local payload capture and artifact-friendly output
- `HttpMockPublisher`
  in-process or local HTTP seam reproduction
- `RealLatticePublisher`
  credential-gated backend stub until sandbox access exists

Recommended shim backend modes:

- `mock`
  in-memory/latest-state, fast developer loop
- `record`
  same semantics plus append-only run/event log
- `replay`
  replay prior logged sessions as if they were live streams
- `real`
  future backend that binds to actual credentials and endpoints

The mock should expose only the seams the bridge needs, not the whole platform.

## Shim responsibilities

The local shim should not try to impersonate all of Lattice.
It should mimic the integration seams that the bridge needs:

- high-rate entity publish
- entity stream with heartbeats
- latest-state entity table
- append-only event log
- local objects/report store
- tiny task mailbox
- metrics, chaos, and replay hooks

The shim should not grow into:

- a fake UI/COP
- a fake auth/permissions system
- a fake mission/autonomy engine
- a fake correlation/fusion engine
- a fake object CDN

## Entities, tasks, objects

Implementation priority for Alpha 4:

- entities: must
- objects: should
- tasks: could

Entities are the first real traffic lane.
Objects should carry evidence artifacts such as screenshots, trajectory reports,
and benchmark summaries.
Tasks should start as thin contract placeholders only.

## Internal ports

The bridge should depend on local interfaces, not a vendor SDK import:

- `EntityPublisher`
- `EntityStream`
- `ObjectStore`
- `TaskMailbox`

These ports exist so the bridge depends on local contracts first and can adopt
official SDK/protobuf bindings later without contaminating the core parser.

## Readiness matrix

| capability | no credentials | public package only | real sandbox required |
|---|---|---|---|
| canonical entity mapping | yes | no | no |
| JSON payload generation | yes | no | no |
| local mock publish | yes | no | no |
| local mock stream | yes | no | no |
| local shim/proxy publish stream | yes | no | no |
| local shim/proxy replay mode | yes | no | no |
| real backend transport stub | yes | no | no |
| actual sandbox publish | no | maybe | yes |
| actual sandbox entity stream | no | maybe | yes |

## Definition of useful

Alpha 4 is useful before credentials if:

- one DIS fixture becomes one stable Lattice-shaped entity payload
- a replay can populate the local mock service
- a mock entity stream can emit Entity State PDUs
- a shim/proxy run can loop DIS -> shim -> DIS with provenance/loop suppression
- proof artifacts make the adapter seams obvious

## Loop suppression

The return lane must not blindly re-emit DIS-ingress entities back into DIS.

Current rule:

- if `packetStoat.source == "dis-ingress"`, the entity is suppressed on the
  shim-to-DIS return lane
- if provenance identifies the payload as a direct DIS-ingress Packet-Stoat
  record, the entity is suppressed
- mock/Lattice-shaped tracks that originate as higher-level adapter payloads
  remain exportable

This keeps the lab honest about the difference between:

- DIS -> canonical -> shim publish
- shim stream -> canonical -> DIS egress

without letting replayed DIS traffic bounce forever through the local lab.

## Minimum entity expectation

Alpha 4 entity payloads should minimally carry:

- deterministic `entityId`
- liveness/expiry
- a human-readable alias/name
- ontology template
- provenance integration/source update fields

Location, disposition, environment, and platform type should be added where the
DIS mapping has enough information to support them cleanly.
