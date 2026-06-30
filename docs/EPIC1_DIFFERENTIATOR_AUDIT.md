# Epic 1 Differentiator Audit

This page keeps the "Beat GRILL" milestone honest. Epic 1 can claim a
differentiator only when there is a local source artifact, a runnable command,
or a generated report that backs it.

## Status

| Differentiator | Status | Evidence | Command or gate |
| --- | --- | --- | --- |
| Deterministic replay verification | proven | `.fastdispkt` replay smoke and Unreal automation test `FastDis.Demo.ReplayMovesActors` exercise replay-driven actor updates. | `python tools/unreal_workflow.py demo --engine-version 5.8` |
| Packet monitor / inspector surface | proven | `UFastDisPduEventComponent`, `UFastDisRuntimeMonitorComponent`, `UFastDisRuntimeStatusWidget`, and replay JSON inspection provide packet/event visibility without a full PDU body claim. | `python -m pytest tests/test_unreal_grill_parity.py tests/test_unreal_fab_readiness.py` |
| Runtime logging surface | proven | Generated PDU log catalogs cover Unreal, Godot, and Unity descriptors for all 141 DIS 6/7 rows; Python summary and JSONL event shape are tested. | `python -m pytest tests/test_pdu_logging.py` and `PYTHONPATH=src python3 -m fastdis.tools.logging_check` |
| Fuzz and generated coverage receipts | proven | PDU coverage, typed parser coverage, semantic parser coverage, shallow fuzz corpus, and generated freshness checks are on disk. | `python tools/check_generated_fresh.py` and `python -m pytest tests/test_pdu_coverage_manifest.py tests/test_typed_pdu_parsers.py tests/test_semantic_pdu_parsers.py` |
| Evidence-pack receipts | proven | Local evidence pack generation hashes source manifests and generated charts/tables, then verifies the manifest. | `python tools/generate_evidence_pack.py --clean --render-symbols never` then `python tools/check_evidence_pack.py artifacts/verification_reports/evidence/latest/manifest.json` |
| Optional Unreal Georeferencing / Cesium adapter | proven | `UFastDisGeoreferenceAdapterComponent` reflects optional source objects without making Unreal Georeferencing or Cesium hard dependencies. | `python -m pytest tests/test_unreal_grill_parity.py` |
| Cross-engine generated contracts | proven for generated contracts, not full runtime parity | PDU logging catalogs are generated for Unreal, Godot, and Unity; orientation and frame contracts exist across engines. Full Godot/Unity runtime product parity remains outside Epic 1. | `python -m pytest tests/test_pdu_logging.py tests/test_fastdis_orient.py` |
| Lattice/Zorn optional path | documented optional integration | Zorn/Lattice proof docs and mapping plans document the optional route without making it a core Unreal dependency. Full live Lattice parity is not an Epic 1 claim. | `python -m pytest tests/test_lattice_dis_mapping_plan.py tests/test_zorn_short_matrix.py` |

## Non-Claims

- Epic 1 does not claim full semantic body decoding for every DIS PDU.
- Epic 1 does not claim Unity or Godot product parity with Unreal.
- Epic 1 does not claim final Fab approval or marketplace availability.
- Epic 1 does not claim live private Lattice backend parity.

Those belong to later release work or [Epic 2](PRODUCT_BACKLOG.md#epic-2-full-dis-67-pdu-feature-buildout).

## Release Gate

Before using the "Beat GRILL" language in release copy, run at least:

```bash
python tools/check_unreal_fab_readiness.py --strict
python tools/generate_evidence_pack.py --clean --render-symbols never
python tools/check_evidence_pack.py artifacts/verification_reports/evidence/latest/manifest.json
python -m pytest tests/test_product_backlog.py tests/test_unreal_grill_parity.py tests/test_unreal_fab_readiness.py tests/test_pdu_logging.py tests/test_evidence_pack.py
```
