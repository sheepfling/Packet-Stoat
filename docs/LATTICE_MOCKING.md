# Lattice mocking strategy

Alpha 4 assumes real SDK access may be unavailable during most of development.

That is acceptable if mocking is treated as a first-class design constraint
instead of a temporary hack.

## Mocking rules

- The mock publisher contract must be explicit and versioned.
- Mock payloads should be machine-readable and easy to diff.
- Failure injection should be deliberate:
  - timeout
  - partial publish
  - rejected payload
  - invalid config
- Reports should distinguish:
  - payload generation succeeded
  - transport mock accepted payload
  - transport mock rejected payload

## Why this matters

The fastdis side should be provable without an external vendor dependency.
Alpha 4 is successful if the adapter contract, proof artifacts, and outbound
workflow are credible enough that a real SDK transport shim can be dropped in
later without redesigning the bridge model.

## First implementation slice

The first Alpha 4 mock surface lives in Python so it can be exercised on any
developer machine without an SDK, Unreal, or Godot.

- `fastdis.lattice.CanonicalEntity` is the bridge record for outbound adapter work.
- `fastdis.lattice.MockLatticePublisher` accepts deterministic failure injection.
- `python -m fastdis.tools.lattice_publish <fixture.json>` publishes fixture entities into stable JSON reports.
- `python tools/lattice_workflow.py full` exercises:
  - `dis-to-shim`
  - `shim-to-dis`
  - bounded `lab-state` object/task seams
- `tests/test_lattice_mock.py` covers accept, reject, timeout, payload
  roundtrip, and DIS Entity State egress conversion.
- `tests/test_lattice_shim_tool.py` covers stream-backed shim-to-DIS export,
  loop suppression, and bounded object/task lab reports.

## Current mock truth

What is mocked today:

- publish acceptance/rejection/failure behavior
- entity latest-state store
- entity stream events and heartbeats
- append-only event log
- object/report store
- task mailbox create/status/stream behavior

What is shape-compatible today:

- entity payload fields
- bounded object records
- bounded task records

What still requires real sandbox access:

- real transport/auth
- real stream semantics against an external endpoint
- real object upload/download APIs
- real task execution/task status protocols outside the local mailbox
