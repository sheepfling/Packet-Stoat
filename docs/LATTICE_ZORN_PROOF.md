# Lattice Zorn Proof

This document tracks the external Zorn-backed proof surface.

Zorn is the current pinned external backend for FastDIS:

- backend: `external-zorn`
- tag: `Alpha1.4`

The goal here is to prove what FastDIS can exercise against a shared external
mock backend without overstating that as live vendor proof.

## Proven through Zorn

Current probe families:

- official REST SDK route:
  - `python tools/lattice_zorn_rest_sdk_probe.py`
- official Buf gRPC route:
  - `python tools/lattice_zorn_grpc_probe.py`
- entity REST↔gRPC parity:
  - `python tools/lattice_zorn_entity_parity_probe.py`
- auth lifecycle realism:
  - `python tools/lattice_zorn_auth_lifecycle_probe.py`
- auth edge matrix:
  - `python tools/generate_zorn_auth_edge_matrix.py`

Generate the current gap summary with:

```bash
python tools/generate_zorn_gap_manifest.py
```

## What this proof can support

- official-style REST auth/connect/publish/get/events
- official-style gRPC entity/task calls
- REST↔gRPC shared-state parity where Zorn exposes it
- explicit Zorn-backed gap reporting
- setup-heavy auth surfaces such as `x-api-key`, `auth_mode=none`, and
  sandbox-header permutations

## What this proof does not mean

Zorn-backed proof does not mean:

- real Lattice behavior is verified
- vendor-only backend semantics are known
- auth expiry/refresh semantics match production
- stream timing and operational routing match production

Those areas should remain labeled as `gap` or `unknown` until a real
credential-gated route is exercised.

## Canonical gap source

Use these generated artifacts as the current source of truth:

- [`generated/zorn_gap_manifest.json`](../generated/zorn_gap_manifest.json)
- [`docs/ZORN_GAP_MANIFEST.md`](ZORN_GAP_MANIFEST.md)
