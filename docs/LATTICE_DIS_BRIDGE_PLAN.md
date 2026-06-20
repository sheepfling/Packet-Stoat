# Lattice <-> DIS bridge plan

## Phase 1: outbound publish

Start with:

```text
DIS replay or UDP
  -> fastdis snapshots
  -> canonical entity bridge
  -> mock Lattice-style publisher or local shim/proxy
```

This is the fastest path to a credible integration story because the DIS side
already exists in fastdis.

## Phase 1.5: shim/proxy seam

Add:

```text
DIS replay or UDP
  -> canonical entity bridge
  -> local shim publish stream
  -> latest-state store / event log / mock stream
```

This is the access-ready seam that lets Alpha 4 prove streaming and run-log
behavior without real credentials.

## Phase 2: DIS egress from canonical entities

Add:

```text
canonical entity fixture or mock Lattice event
  -> DIS Entity State encode
  -> UDP/replay egress
```

This creates the first return path without requiring real Lattice ingress.

The preferred Alpha 4 return path is:

```text
shim/mock entity stream
  -> canonical entity
  -> DIS Entity State encode
  -> UDP/replay egress
```

## Phase 3: future ingress

Only after the outbound and egress paths are solid:

```text
real or mock Lattice stream
  -> canonical entity bridge
  -> DIS encode and/or native snapshot update
```

This sequence keeps Alpha 4 focused and avoids overclaiming SDK coverage.
