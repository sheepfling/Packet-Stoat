# Lattice reference stack

Alpha 4 should be built against explicit sources of truth instead of an
informal idea of what "Lattice-shaped" means.

## Ordering

Use references in this order:

1. Public Lattice API overview and developer guides
2. Public Lattice endpoint/API references for Entities, Tasks, and Objects
3. Public Lattice SDK/package samples and examples
4. Public gRPC/protobuf surface after local publish/stream semantics are stable
5. fastdis-owned shim contracts and fixtures

For the DIS side:

1. IEEE 1278.1 / DIS
2. Open-DIS and similar programmer-facing references
3. fastdis-owned generated/message coverage docs

## Alpha 4 compatibility tiers

Alpha 4 uses three compatibility tiers:

- behavior-compatible
  enough semantic alignment to test the bridge honestly
- shape-compatible
  payload fields and stream controls resemble the public docs closely
- wire-compatible
  actual official REST/gRPC endpoint and protobuf fidelity

Alpha 4 target:

- entities: behavior-compatible and shape-compatible
- objects: behavior-compatible and shape-compatible
- tasks: behavior-compatible only, explicitly experimental
- wire-compatible gRPC: deferred

Alpha 4.1 gRPC target:

- Packet-Stoat-owned proto and local streaming behavior: yes
- official-stub import/serialization checks: optional
- full official wire/API fidelity: deferred

## Entity minimum

The minimum entity contract for Alpha 4 should include:

- `entityId`
- `isLive`
- `expiryTime`
- `aliases.name`
- `ontology.template`
- `provenance.integrationName`

Useful DIS-aligned additions:

- `location.position`
- velocity/orientation sidecar fields
- `milView.disposition`
- `milView.environment`
- `ontology.platformType`

## Publish semantics

Alpha 4 should model two publish lanes:

- single-entity publish
  validation-rich, lower-rate, test-friendly
- batch/stream publish
  higher-rate, reduced per-entity feedback, throughput-oriented

This is a semantic split, not a claim of official wire compatibility.

## Stream semantics

The minimal stream contract should include:

- entity events
- heartbeat events
- optional stale/delete events
- `preExistingOnly`
- `heartbeatIntervalMs`
- `componentsToInclude`

Do not add broader query/search semantics in Alpha 4.

Alpha 4.1 extends this with a gRPC-shaped stream contract:

- `PREEXISTING`
- `UPDATE`
- `DELETED`
- `HEARTBEAT`
- per-entity rate limiting

## Tasks and Objects

Objects:

- local file/object storage only
- path, checksum, size, update time, expiry time metadata

Tasks:

- tiny mailbox only
- create task
- stream tasks
- update task status

Task behavior should be marked experimental where it relies on publicly Beta
concepts.

## Non-goals

Alpha 4 should not attempt to provide:

- full endpoint coverage
- full SDK compatibility
- auth/permissions parity
- fake COP/UI behavior
- fake platform fusion/correlation logic
- official protobuf wire compatibility everywhere
- full official gRPC service emulation before the local contract is proven
