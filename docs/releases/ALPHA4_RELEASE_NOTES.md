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
- Access-ready local lab for Lattice-shaped entities: yes.
- Local shim/proxy seam: yes.
- Outbound publish path from DIS/native snapshots to a Lattice-style payload:
  yes.
- Reverse mock/Lattice-shaped entity -> DIS Entity State egress: yes.
- Full live Lattice -> DIS support: not yet.
- DIS writer coverage: Entity State first.

## Current proof artifacts

Running `python tools/lattice_workflow.py full` generates local proof artifacts
under `verification_reports/alpha4/lattice/`, including:

- `dis_to_shim/dis_to_shim_report.json`
- `dis_to_shim/stream_events.json`
- `shim_to_dis/shim_to_dis_report.json`
- `shim_to_dis/canonical_entities.json`
- `shim_to_dis/shim_to_dis.fastdispkt`
- `lab_state/lab_state_report.json`
- `lab_state/objects.json`
- `lab_state/tasks.json`
- `lab_state/task_events.json`
- `alpha4_lattice_report.json`
- `alpha4_lattice_report.md`

These are operator-generated outputs and are intentionally not tracked in git.

## Current mocked vs real boundary

Mocked today:

- entity publish/store/stream
- heartbeats
- object/report storage
- task mailbox create/status/stream
- loop suppression and replay-safe return-lane logic

Not mocked as real parity:

- vendor auth/session setup
- real sandbox transport
- full task semantics
- full object API semantics
- live inbound Lattice -> DIS ingestion
