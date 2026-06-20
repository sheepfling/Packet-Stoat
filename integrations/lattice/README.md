# Lattice Adapter Scaffold

This directory holds the Alpha 4 Lattice-shaped adapter layer.

It is intentionally separate from the `fastdis` parser/runtime core.

## Layering

```text
DIS / replay / native snapshots
  -> fastdis core
  -> canonical entity bridge
  -> packet_stoat_lattice adapter
  -> mock or real Lattice transport backend
```

## Current status

The initial scaffold is mock-first:

- canonical entity helpers
- DIS-to-Lattice payload shaping
- Lattice-shaped fixture to DIS Entity State egress
- JSONL/mock transport backends
- real transport stub gated on credentials
- Alpha 4.1 contract and SDK-gap audit tooling

No real Anduril or Lattice SDK access is required for this layer to be useful.

## Intended workflow

1. Build canonical entities from replay, UDP, or fixtures.
2. Convert those entities into Lattice-shaped payloads.
3. Publish with:
   - `JsonlPublisher`
   - `HttpMockPublisher`
   - later `RealLatticePublisher`
4. Verify deterministic reports and golden JSON artifacts.
5. Run the Alpha 4.1 audits:
   - `python tools/lattice_contract_audit.py`
   - `python tools/lattice_sample_parity_audit.py`
   - `python tools/run_alpha4_1_sdk_gap_report.py`
