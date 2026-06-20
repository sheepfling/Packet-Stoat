# Alpha 4 Goal

Objective:
Deliver `fastdis v0.14.0-alpha4` as the first access-ready Lattice bridge
preview: DIS/native snapshots flow through a canonical entity model into a
mockable Lattice-style adapter layer, with local lab backends and a reusable
shim/proxy seam, initial DIS Entity State egress support, and clear proof
artifacts that do not require a real Anduril SDK.

Completion standard:

- Alpha 4 has explicit release docs and architecture notes on disk.
- A canonical entity bridge exists between DIS, engines, and the Lattice
  adapter layer.
- A mock publisher/client contract exists and is testable without SDK access.
- A local mock service/lab path exists so the adapter can behave like an
  integration seam before any real credentials arrive.
- A local shim/proxy path exists so publish, entity streaming, event logging,
  object/report storage, and a tiny task mailbox can be exercised end to end.
- Deterministic DIS-to-Lattice identity mapping exists and can reverse for
  mock/fixture egress.
- Native snapshots can be converted into canonical entities and published
  outward through the adapter workflow.
- Canonical entities can be encoded back into DIS Entity State for first-pass
  egress.
- Alpha 4 reports clearly distinguish mocked Lattice behavior from verified
  fastdis native behavior.

Primary execution order:

1. Put the Alpha 4 release plan and roadmap bump on disk.
2. Define the Lattice mapping and canonical bridge model.
3. Build the mock publisher/app contract.
4. Convert fastdis snapshots into canonical entities.
5. Add the access-ready local lab backends and reports.
6. Add the shim/proxy seam and backend modes.
7. Build outbound publish and DIS egress proof lanes.

Non-goals:

- Do not bake Lattice SDK assumptions into the fastdis parser core.
- Do not claim official SDK parity or ingress support before evidence exists.
- Do not wait for credentials before proving the adapter seams.
- Do not expand into many new DIS PDU writers before Entity State egress is
  solid.

Operator note:

Use this file as the Alpha 4 goal blurb for execution tracking. Use
`ALPHA4_PLAN.md` as the detailed work breakdown and definition of done.
