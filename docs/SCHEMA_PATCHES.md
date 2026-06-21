# Schema Patches

FastDIS keeps schema corrections explicit and reviewable.

The current repo generates DIS catalog and coverage artifacts from:

- `references/open-dis/DIS6.xml`
- `references/open-dis/DIS7.xml`

Those upstream XML descriptions are useful, but fastdis should not hide local
corrections inside generated outputs or scattered script logic.

## Patch directories

Use:

- `schemas/patches/dis6/`
- `schemas/patches/dis7/`
- `schemas/patches/pdu_catalog_overrides.yaml`

for fastdis-owned schema corrections and annotations.

## What belongs in a patch

Examples:

- corrected field naming for generated outputs
- clarified minimum-size or prefix-size knowledge
- variable-list padding/alignment notes
- interoperability quirks validated by fixtures or differential reports
- code-generation hints that should not live in the upstream XML itself

## What does not belong in a patch

- handwritten edits to generated files
- runtime-specific hacks with no schema meaning
- vague comments with no source, fixture, or issue reference

## Patch record expectations

Each patch file should make these things obvious:

- target schema version
- target PDU or record
- exact correction
- reason
- evidence source
- fastdis issue or audit reference, when applicable

Representative shape:

```yaml
pdu: SignalPdu
fix:
  variable_length_padding: true
reason: "Validated against downstream fixtures and differential report."
source: "A3 differential audit"
```

## Review rule

If the project learns something new about the DIS schema, the change should go
into the patch layer first and then flow back through generation.

That keeps:

- generated artifacts reproducible
- schema corrections diffable
- future IR/parser generation explainable

## Alpha 3 baseline

For Alpha 3, the immediate requirement is modest:

- patch directories exist on disk
- policy is documented
- future generator work has a clear, owned home for corrections

The full IR + patch application machinery can land incrementally after the
baseline is documented.

See also:

- `docs/GENERATION_PIPELINE.md`
- `docs/MESSAGE_COVERAGE.md`
- `docs/PDU_COVERAGE.md`
- `docs/DIFFERENTIAL_TESTING.md`
