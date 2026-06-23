# Lattice Real Route Proof

This document is for the credential-gated live route only.

It should answer one question:

What has FastDIS actually proven against a real Lattice endpoint?

## Current posture

Today the checked-in repo is primarily:

- local shim proof
- external Zorn-backed proof

The live route is intentionally separated so FastDIS does not treat mock-backed
success as vendor proof.

The live bridge entry point is:

- `tools/lattice_live_bridge.py`

The starter config is:

- `configs/lattice_backend.real.example.json`

## Until credentials exist

These surfaces remain `unknown` until run against a real endpoint:

- auth expiry and refresh behavior
- real sandbox authorization requirements
- real stream timing, reconnect, and ordering behavior
- vendor-side task execution side effects
- vendor-side object storage semantics
- vendor-only fields and backend policies

## Required discipline

When a proof artifact is created from the live route, mark it clearly as:

- `real-lattice`

and do not mix it with:

- `local`
- `zorn-backed`

That separation is what keeps the compatibility claims honest.
