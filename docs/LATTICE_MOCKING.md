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
- `tests/test_lattice_mock.py` covers accept, reject, timeout, and DIS Entity State egress conversion.
