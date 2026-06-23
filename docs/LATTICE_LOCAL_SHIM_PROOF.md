# Lattice Local Shim Proof

This document is intentionally narrow.

It covers the in-repo FastDIS shim and harness surfaces that exist for:

- deterministic unit tests
- fixture generation
- local fault injection
- FastDIS-only mapping behavior

It does **not** prove Zorn compatibility or real Lattice compatibility.

## What counts as local-only proof

Examples:

- `tests/test_lattice_compatibility_harness.py`
- `tests/test_lattice_shim_tool.py`
- `tests/test_lattice_adapter_scaffold.py`
- `tests/test_lattice_bucket_conformance.py`

Those tests are useful because they keep FastDIS behavior deterministic and fast
to run, but they should be read as:

- local shim proof
- local route-shape proof
- local mapping proof

not as:

- backend compatibility proof
- Zorn proof
- real Lattice proof

## Intended use

Use the local shim when you need:

- stable tests without an external checkout
- explicit state-machine fixtures
- negative-path and malformed-input coverage
- repeatable replay-to-report generation

## Boundaries

If a claim is about:

- official REST SDK behavior
- official Buf gRPC behavior
- REST↔gRPC shared-state parity
- auth/session realism

then the proof should come from the Zorn-backed probes or a real credential-gated
Lattice route, not the local shim.
