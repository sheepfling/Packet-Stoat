# fastdis v0.14.0-alpha4 Release Notes

Theme: access-ready Lattice lab, shim/proxy seam, canonical entity bridge, and mockable adapter backends.

This release is intended to prove that fastdis can sit beside a higher-level
operations platform adapter without compromising the native DIS core.

## Planned highlights

- Canonical entity bridge model between DIS/native snapshots and an external
  app/integration layer.
- Lattice-oriented mapping docs, mock SDK contract, and access-ready lab
  architecture.
- Local shim/proxy seam for high-rate publish, entity streaming, event logging,
  and future real backend insertion.
- Outbound operator workflow for replay/UDP/native snapshots -> JSON/mock
  publisher/service.
- First-pass DIS Entity State egress from canonical entity fixtures and
  Lattice-shaped mock track payloads.
- Deterministic identity mapping and local proof artifacts.
- Proof artifacts and reports that make mocked-vs-real behavior explicit.

## Honest claim template

- fastdis core remains a DIS/native packet-processing SDK: yes.
- Official Anduril SDK integration: no, mocked contract first.
- Access-ready local lab for Lattice-shaped entities: yes, planned for Alpha 4.
- Local shim/proxy seam: yes, planned for Alpha 4.
- Outbound publish path from DIS/native snapshots to a Lattice-style payload:
  yes, planned for Alpha 4.
- Reverse mock/Lattice-shaped entity -> DIS Entity State egress: yes, planned
  for Alpha 4.
- Full live Lattice -> DIS support: not yet.
- DIS writer coverage: Entity State first.
