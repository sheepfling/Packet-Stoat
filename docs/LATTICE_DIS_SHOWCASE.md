# Lattice DIS Showcase

This report ties together the generated DIS classification plan with the current
Zorn-backed ingress and egress workflow.

## What it proves

- All 141 standard DIS 6/7 rows are classified into strict `Entity`, `Task`,
  or `Object` buckets.
- All 141 rows have byte-preserving semantic parser entry points, so the
  parser layer is byte-duplex across the full catalog.
- Only 2 rows are currently semantic-duplex in the strict sense:
  `Entity State` for DIS 6/7.
- The showcase distinguishes row egress profiles:
  - `structured` rows are byte-for-byte round-trip eligible.
  - `diagnostic` rows are ingress/egress visible but carry explicit
    diagnostics or loss notes.
  - `raw_required` rows keep the raw packet as a sidecar for lossless
    preservation.
- DIS Entity State is shown round-tripping through the current Zorn-backed
  entity lane.
- Non-Entity rows are shown as classified ingress/egress rows with explicit
  routes, loss policies, and raw-sidecar handling where needed.

## Run It

```bash
python tools/lattice_workflow.py showcase
```

The showcase writes:

- `alpha5_lattice_showcase.json`
- `alpha5_lattice_showcase.md`

under the chosen `--out-root` directory.

## Source Material

- [PDU coverage](PDU_COVERAGE.md)
- [Lattice backend contract](LATTICE_BACKEND.md)
- [Lattice DIS bridge plan](LATTICE_DIS_BRIDGE_PLAN.md)
- [Lattice Zorn proof](LATTICE_ZORN_PROOF.md)

## Scope

This is a showcase, not a claim that every DIS PDU round-trips losslessly
through the Lattice/Zorn route. The current round-trip proof is strongest for
Entity State. Other PDUs are classified, routed, and preserved or summarized
according to the generated mapping plan.
