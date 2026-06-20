# Generation Pipeline

Alpha 3 should treat DIS 6/7 generation as a real product surface, not just a
helper script that happens to emit useful tables.

The current repo already generates catalog and coverage artifacts from Open-DIS
XML descriptions:

- `references/open-dis/DIS6.xml`
- `references/open-dis/DIS7.xml`
- `tools/generate_pdu_catalog.py`

That is a good start, but it is not yet the full baseline fastdis should own.

## Current state

Current generated outputs include:

- `docs/DIS_PDU_CATALOG.md`
- `docs/MESSAGE_COVERAGE.md`
- `docs/MESSAGE_CROSS_LANGUAGE_SET.md`
- `generated/fastdis_ir_dis6.json`
- `generated/fastdis_ir_dis7.json`
- `generated/message_coverage_manifest.json`
- `generated/fuzz_shallow_corpus/manifest.json`

Current strengths:

- DIS 6/7 catalog metadata is already machine-generated.
- A normalized fastdis-owned IR is now emitted for DIS6 and DIS7.
- The message coverage manifest is already tied to generated catalog data.
- The shallow fuzz corpus already spans the known PDU catalog breadth.
- A single freshness checker can verify the current catalog, IR, and shallow
  fuzz outputs together.

Current gaps:

- No formal schema patch layer exists yet.
- Generated provenance headers and patch-application mechanics are still
  minimal.
- The current generator focuses on catalog/coverage output rather than future
  flat parser generation.

## Design rule

Use XML-derived generation to expand coverage without replacing the fastdis
runtime architecture.

Good uses of generation:

- catalog metadata
- safe header/min-length validation tables
- shallow fuzz seeds
- docs and coverage manifests
- optional flat prefix parsers
- optional field visitors or cursors

Bad use of generation:

- replacing the hot path with nested object trees
- forcing allocation-heavy full-message runtime models into the core C ABI
- exposing generated C++ object graphs across ABI boundaries

## Target pipeline

The owned target shape should be:

```text
Open-DIS XML descriptions
  -> fastdis normalized IR
  -> generated catalog / coverage / fuzz artifacts
  -> generated flat parser helpers
  -> optional future full-message visitors
```

Concretely:

```text
references/open-dis/DIS6.xml
references/open-dis/DIS7.xml
  -> tools/generate_fastdis_ir.py
  -> generated/fastdis_ir_dis6.json
  -> generated/fastdis_ir_dis7.json
  -> tools/generate_fastdis_catalog.py
  -> generated/message_coverage_manifest.json
  -> docs/MESSAGE_COVERAGE.md
  -> docs/DIS_PDU_CATALOG.md
  -> tools/generate_fastdis_fuzz_seeds.py
  -> generated/fuzz_shallow_corpus/*
  -> tools/generate_fastdis_parsers.py
  -> generated flat parser tables / prototypes
```

## Owned IR

The fastdis IR is the source of truth fastdis should own.

It should normalize:

- PDU identity:
  protocol version, family, type, class name, display name
- inheritance:
  base record / inherited initial values
- fields:
  name, primitive/record/list kind, count-field relationships
- fixed layout facts:
  static offsets where known, static minimum size, known prefix lengths
- variable-layout facts:
  variable lists, count fields, padding rules, alignment notes
- support metadata:
  generated support status, parser status, fuzz status, oracle status

Representative target artifact names:

- `generated/fastdis_ir_dis6.json`
- `generated/fastdis_ir_dis7.json`

## Schema patch layer

The upstream XML should be treated as a bootstrap/reference input, not an
unquestioned normative truth source.

All fastdis-local corrections should go into:

- `schemas/patches/dis6/`
- `schemas/patches/dis7/`

Examples of patch-worthy adjustments:

- corrected family/type naming
- known minimum-size clarifications
- variable-record padding notes
- field-name normalization for generated code
- downstream interoperability notes backed by fixtures or differential reports

The rule is simple:

- do not hide local schema corrections in generated files
- do not hand-edit generated coverage/catalog outputs
- do record every correction in the patch layer with a reason

## Freshness and provenance

Generated artifacts should carry enough provenance to answer:

- which upstream schema files produced this output?
- which patch set was applied?
- which generator revision produced this file?

Generated-file headers should move toward:

```text
GENERATED FILE - DO NOT EDIT
Source: references/open-dis/DIS7.xml
Patch set: schemas/patches/dis7/
Generator: tools/generate_fastdis_catalog.py
```

Alpha 3 should also add a freshness check tool, planned as:

- `tools/check_generated_fresh.py`

The current checker should fail when:

- generated outputs are stale relative to the generator
- generated outputs are stale relative to schema inputs
- generated outputs are stale relative to patch files, once patch application
  is wired into the generators

## Parser-generation direction

fastdis should not jump straight from XML to full object parsers for every PDU.

Preferred generation order:

1. catalog and coverage outputs
2. safe validation/min-length tables
3. shallow fuzz seed metadata
4. flat prefix parsers for high-value PDUs
5. optional visitor/cursor-style full-message inspection helpers

Priority PDU candidates after Entity State:

- Fire
- Detonation
- Collision
- Transmitter
- Signal
- Receiver
- Electromagnetic Emission
- Designator

## Differential role

Open-DIS and related generated implementations are useful as:

- field-order references
- fixture sources
- catalog-overlap oracles
- semantic disagreement detectors

They are not the fastdis runtime model.

See also:

- `docs/DIFFERENTIAL_TESTING.md`
- `docs/MESSAGE_COVERAGE.md`
- `docs/SCHEMA_PATCHES.md`
