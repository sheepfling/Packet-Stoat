# FastDIS Symbols Proof

This is a disposable proof harness for the tactical-symbol handoff boundary.
It validates that FastDIS Entity State identity fields can be converted into a
renderer-facing descriptor and passed to an external MIL-STD-2525/App-6 renderer.

This package is intentionally separate from both FastDIS core and the longer
lived [FastDIS Symbols extension](../fastdis-symbols/README.md).

The proof status and non-claims are tracked in [PROOF.md](PROOF.md).

## Claim Under Test

```text
Entity State PDU
  -> FastDIS entity-state identity fields
  -> demo DIS-to-symbol mapping
  -> SIDC + modifiers
  -> external renderer
  -> SVG artifact
```

The proof validates field sufficiency and adapter shape. It does not claim a
complete official DIS/SISO-to-MIL-STD-2525 mapping, tactical correctness for
every entity tuple, multipoint tactical graphics, order-of-battle context, or
any reason to move symbology into FastDIS core.

## Renderer

The first renderer target is `milsymbol`, used only from this proof package. It
is not a FastDIS core dependency.

Install proof dependencies when you want the live SVG renderer check:

```bash
npm install --prefix extensions/fastdis-symbols-proof --cache build/npm-cache
```

Render the demo descriptor cases:

```bash
node extensions/fastdis-symbols-proof/render_milsymbol.mjs \
  extensions/fastdis-symbols-proof/cases/demo_symbol_descriptors.jsonl \
  build/symbols-proof/svg
```

The pytest suite skips the live renderer check when `milsymbol` has not been
installed, while still validating the descriptor mapping and FastDIS identity
sufficiency path.

The dedicated CI proof lane uses `npm ci` and must run the live renderer tests.

## Files

- [demo descriptors](cases/demo_symbol_descriptors.jsonl)
- [demo FastDIS entities](cases/demo_fastdis_entities.jsonl)
- [affiliation policy](rules/affiliation_policy.json)
- [demo DIS-to-symbol rules](rules/demo_dis_to_symbol_rules.json)
- [milsymbol renderer script](render_milsymbol.mjs)
