# Epic 2 Full DIS Buildout

This page expands
[Epic 2: Full DIS 6/7 PDU Feature Buildout](PRODUCT_BACKLOG.md#epic-2-full-dis-67-pdu-feature-buildout)
into a source-backed execution surface. The backlog keeps the product ordering
clear; this page keeps the 141-row claim measurable.

## Goal

FastDIS should move from a small set of hot-path semantic parsers toward
generated DIS 6/7 product coverage across all standard versioned rows. The
target is not "full hand-written decoding first." The target is generated truth,
safe ingest, generic endpoint behavior, typed semantic waves, cross-language
parity, and evidence-backed release gates that can be rebuilt locally.

## Current Baseline

These counts come from the generated coverage surfaces already checked into the
repo.

| Surface | Current status | Source |
| --- | --- | --- |
| Standard backbone rows | `141 / 141` | [PDU standard backbone](PDU_STANDARD_BACKBONE.md) |
| Safe ingest rows | `141 / 141` | [PDU coverage](PDU_COVERAGE.md) |
| Generic endpoint rows | `141 / 141` | [PDU coverage](PDU_COVERAGE.md) |
| Field visitor rows | `114 / 141` | [PDU coverage](PDU_COVERAGE.md) |
| Typed envelope rows | `141 / 141` | [Typed PDU coverage](TYPED_PDU_COVERAGE.md) |
| Typed structural rows | `114 / 141` | [Typed PDU coverage](TYPED_PDU_COVERAGE.md) |
| Typed semantic entry points | `141 / 141` | [Semantic PDU coverage](SEMANTIC_PDU_COVERAGE.md) |
| Semantic observation rows | `99 / 141` | [Semantic PDU coverage](SEMANTIC_PDU_COVERAGE.md) |
| Semantic decoded Wave 2 rows | `10 / 141` | [Semantic PDU coverage](SEMANTIC_PDU_COVERAGE.md) |
| Fully domain-decoded rows | `42 / 141` | [Semantic PDU coverage](SEMANTIC_PDU_COVERAGE.md) |
| Logging descriptors | `141 / 141` | [PDU logging coverage](PDU_LOGGING_COVERAGE.md) |
| Lattice/Zorn classified rows | `141 / 141` | [Lattice DIS mapping plan](LATTICE_DIS_MAPPING_PLAN.md) |

The baseline says FastDIS already has generated truth surfaces for all 141 rows,
but semantic depth is still concentrated in a small number of domain-decoded
PDUs. Epic 2 is about growing depth without losing generated consistency.

The generated per-row wave assignment lives in
[Epic 2 semantic waves](EPIC2_SEMANTIC_WAVES.md).

## Milestone 1: 141-Row Generated Truth Table

Goal blurb:

The generated manifests become the first release boundary for full DIS buildout.
If a known DIS 6/7 row lacks a product decision, the repo should fail loudly
instead of quietly drifting.

Exit target:

- Each of the 141 standard versioned rows has a stable generated descriptor.
- Each row has a strict product bucket such as `Entity`, `Task`, `Object`,
  `Observation`, `Control`, `Event`, or `RawSidecar`.
- Each row has endpoint behavior for Python, C/C++, Unreal, Godot, Unity, and
  Lattice/Zorn.
- Each row has logging behavior, support level, lossy policy, and unknown-value
  handling policy.
- Generated tables make missing decisions visible by row and by bucket.

Primary proof:

```bash
python -m pytest tests/test_pdu_coverage_manifest.py tests/test_pdu_logging.py tests/test_lattice_dis_mapping_plan.py
python tools/check_generated_fresh.py
```

## Milestone 2: Generic Wire And Field Coverage

Goal blurb:

All known rows should be safe on the wire before they are deep in semantics. A
PDU that is not yet fully decoded should still survive ingest, generic packet
views, field inspection where IR support exists, logging, and endpoint
surfacing.

Exit target:

- Header validation, declared-length checks, and byte-preserving views stay
  green for all standard rows.
- Field visitors and structural parsers continue to expand beyond the current
  `114 / 141` baseline.
- Unknown and locally extended enumerations remain numeric instead of being
  discarded.
- Raw-sidecar policies stay explicit where semantic loss is still possible.
- Generic endpoint behavior remains present across engines and Lattice/Zorn.

Primary proof:

```bash
python -m pytest tests/test_pdu_coverage_manifest.py tests/test_pdu_catalog.py tests/test_typed_pdu_parsers.py tests/test_semantic_pdu_parsers.py
python tools/check_generated_fresh.py
```

## Milestone 3: Typed Semantic PDU Waves

Goal blurb:

Semantic depth should grow in coherent waves that line up with product value
instead of scattered one-off decoders. The current `42 / 141` fully
domain-decoded baseline should move upward in grouped slices that bring parser,
serializer, events, docs, and tests together.

Wave targets:

1. State and lifecycle: Entity State, Entity State Update, Remove Entity,
   Create Entity, and adjacent identity/lifecycle rows.
2. Warfare and effects: Fire, Detonation, Collision, LE variants, Directed
   Energy, and damage-status families.
3. Radio, sensor, EW, IFF, and designator families.
4. Simulation-management families, including reliable variants.
5. Logistics, minefield, environmental, aggregate, relationship, attribute,
   and information-operations families.

Exit target:

- Each wave adds real domain-decoded rows, not only metadata.
- Each wave carries semantic roundtrip tests and fuzz depth.
- Each wave updates endpoint events, generated coverage docs, and evidence
  tables in the same change series.

Primary proof:

```bash
python -m pytest tests/test_typed_pdu_parsers.py tests/test_semantic_pdu_parsers.py
python tools/check_generated_fresh.py
```

## Milestone 4: Cross-Engine And Lattice/Zorn Parity

Goal blurb:

FastDIS should keep one product story across Python, native code, engines, and
Lattice/Zorn instead of letting each endpoint invent different semantics for the
same PDU row.

Exit target:

- Generated catalogs stay shared across Unreal, Godot, Unity, and Python.
- C, C++, Python, Unreal, Godot, and Unity report equivalent results for
  representative typed rows.
- Lattice/Zorn routes stay explicit per row as `full_duplex`,
  `lossy_ingress`, `lossy_egress`, `observation_only`, or `raw_sidecar`.
- Representative parity fixtures compare the same rows across multiple
  languages and endpoints.

Primary proof:

```bash
python -m pytest tests/test_pdu_logging.py tests/test_lattice_dis_mapping_plan.py
python tools/generate_evidence_pack.py --clean --render-symbols never
python tools/check_evidence_pack.py build/verification_reports/evidence/latest/manifest.json
```

## Milestone 5: Evidence And Release Gates

Goal blurb:

Epic 2 is only credible if the build, docs, generated outputs, and release
artifacts keep proving the claims from source-backed receipts.

Exit target:

- Evidence-pack artifacts cover PDU status, endpoint behavior, ABI boundary,
  benchmark receipts, replay receipts, and engine receipts.
- Generated freshness, docs link checks, lint, tests, packaging checks, and
  product inspection are part of repo-green, not optional cleanup.
- Build-product inspection catches stale generated files, secrets, invalid
  versioned outputs, and unexpected cross-compile artifacts before release.

Primary proof:

```bash
python tools/dev_check.py --release-ready
python tools/generate_evidence_pack.py --clean --render-symbols never
python tools/check_evidence_pack.py build/verification_reports/evidence/latest/manifest.json
python tools/check_docs.py
```

## Working Rule

Epic 2 should prefer generated truth over hand-maintained matrices and should
prefer honest generic behavior over pretending a row is semantically complete
when it is not. Claims about "full support" should stay tied to the generated
coverage docs and the verification commands above.
