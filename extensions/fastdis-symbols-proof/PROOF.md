# M0 Tactical Symbol Handoff Proof

Status: `PASS`

## Claim

FastDIS exposes enough Entity State identity data to drive an external tactical
symbology adapter without adding MIL-STD-2525/App-6 renderer dependencies to
FastDIS core.

## Evidence

- Five demo DIS/SISO entity mappings are defined in
  [demo_fastdis_entities.jsonl](cases/demo_fastdis_entities.jsonl).
- Demo mappings flow through external affiliation and symbol-rule files under
  [rules](rules/).
- A synthetic Entity State PDU is parsed through FastDIS
  `parse_entity_state_prefix`, then converted into a descriptor and rendered
  through `milsymbol` in the end-to-end proof test.
- A transform-only negative test proves compact transform snapshots are
  insufficient for full symbology because they omit `entity_type`,
  `alternate_entity_type`, `marking`, and `capabilities`.
- The live renderer proof emits SVG through the external `milsymbol` package.
- `node_modules/`, SVG output, and npm cache data are ignored local artifacts.
- FastDIS core has no dependency on this proof package or renderer.

## Non-Claims

- This is not complete MIL-STD-2525/App-6 coverage.
- This is not an official tactical mapping from every SISO entity type.
- This is not a production renderer or asset pipeline.
- This does not cover multipoint tactical graphics or control measures.
- This does not cover C2SIM/MSDL/order-of-battle unit context.
- This does not justify moving symbology into FastDIS core.

## Required Proof Lane

The dedicated CI lane should run:

```bash
npm ci --prefix extensions/fastdis-symbols-proof --cache build/npm-cache
python -m pytest tests/test_symbols_proof.py
```

The default local quick gate may skip live rendering when `milsymbol` is not
installed, but the `symbols-proof` CI lane must require it.
