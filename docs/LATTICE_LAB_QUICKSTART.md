# Lattice Lab Quickstart

The FastDIS Lattice Lab maps DIS/native simulation state into
public-docs-aligned, Lattice-shaped Entities, Objects, and Tasks workflows. It
is not an official Anduril integration and does not claim live sandbox behavior
without credentials.

## Modes

mock:

No Anduril SDK or credentials required. Uses local JSON fixtures, JSONL reports,
and the mock shim/state store.

sdk-dryrun:

Imports the official REST SDK if installed and checks that Packet Stoat's
configuration and mock transport seams are compatible. No real endpoint is
called.

live:

Skipped unless explicit environment variables and opt-in flags are present.
This is reserved for future sandbox credentials.

## Commands

```bash
fastdis lattice doctor
fastdis lattice dis-to-shim
fastdis lattice shim-to-dis
fastdis lattice lab-state
fastdis lattice report
fastdis lattice sdk-check
fastdis lattice full
```

The `sdk-check` command writes the Alpha 4.1 SDK gap report and records what is
mock-compatible, shape-compatible, and still credential-gated.

## Demo Flow

```text
DIS replay / UDP
  -> fastdis Entity State decode
  -> canonical entity bridge
  -> Lattice-shaped Entity payload
  -> mock stream / JSONL / optional SDK seam
```

Reverse flow:

```text
Lattice-shaped fixture
  -> canonical entity
  -> DIS Entity State egress
  -> fastdis recv / engine demo
```
