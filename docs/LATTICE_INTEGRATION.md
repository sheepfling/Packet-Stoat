# Lattice integration overview

Alpha 4 introduces a separate adapter/application layer for Lattice-style
integration work.

See also:

- `docs/LATTICE_LAB.md`
- `docs/LATTICE_ENTITY_MAPPING.md`
- `docs/LATTICE_DIS_BRIDGE_PLAN.md`

The layering rule is:

```text
fastdis core
  DIS parsing
  filtering
  entity table
  snapshot buffer
  transforms / orientation support

canonical entity bridge
  flat, portable entity representation
  bridge between DIS/native snapshots and higher-level apps

lattice adapter app
  publish outward
  mock or real SDK transport shim
  auth/config/reporting
```

This keeps the fastdis native core generic and lets the Lattice adapter evolve
without contaminating the C ABI hot path with SDK-specific assumptions.

It also means Alpha 4 can be useful before credentials exist:
the adapter can run against fixtures, replay files, JSON outputs, and local mock
services long before a real sandbox backend is available.

## Alpha 4 scope

Outbound only for the initial preview:

- replay or UDP DIS
- native snapshots
- canonical entity conversion
- mock Lattice-style publish flow

Ingress from Lattice-style sources back into DIS/native state is explicitly
deferred after the outbound bridge is credible.

However, Alpha 4 does include reverse mock-level egress:

- mock Lattice-shaped entity fixture or stream
- canonical entity bridge
- DIS Entity State bytes

That gives the repo a credible return path without claiming full live ingress.

## Naming note

The phrase "Lattice integration" in Alpha 4 should be read as:

- adapter/app contract
- mockable transport/client interface
- mapping and workflow proof

It should not be read as a claim that the repo currently ships an official
Anduril SDK implementation.

## Adapter scaffold

Alpha 4 now also carries a separate adapter scaffold under:

```text
integrations/lattice/
```

That scaffold is for:

- canonical entity fixture handling
- Lattice-shaped payload generation
- JSONL and local mock publish backends
- future real SDK transport insertion
- Lattice-shaped fixture back to DIS Entity State egress

The intent is to let the repo prove the mapping and workflow before any real
sandbox credentials exist.
