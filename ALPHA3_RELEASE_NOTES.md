# fastdis v0.13.0-alpha3 Release Notes

Theme: coverage, fuzzing, orientation proof, and performance qualification.

This release is intended to be a confidence release. It should state exactly
what the SDK covers, what has been hardened, what has been verified by
independent oracles, and what remains intentionally partial.

## Planned highlights

- Generated DIS 6/7 message coverage manifest and cross-language catalog docs.
- Documented DIS 6/7 generation pipeline with an owned patch/IR baseline for
  future flat parser expansion.
- All-PDU shallow fuzz corpus and fuzz smoke targets.
- Deep fuzz + sanitizer coverage on typed and engine-facing paths.
- Multi-oracle orientation verification:
  native C++, independent Python, SciPy, SymPy, golden fixtures, and
  in-engine Unreal/Godot harnesses.
- Differential comparison report against Open-DIS Python where practical.
- Benchmark qualification report with throughput, latency quantiles, and
  allocation-expectation notes.

## Honest claim template

- Full DIS 6/7 catalog metadata coverage: yes.
- DIS 6/7 generation baseline owned by fastdis: yes, at the schema/patch/doc
  level; full IR- and parser-generation rollout remains in progress.
- Safe header/dispatch handling across cataloged PDUs: yes.
- Full typed semantic parser coverage for every DIS PDU: no.
- Typed fast path quality focus: Entity State first.
- Orientation API: basis/quaternion driven, not Euler passthrough.

## Proof artifacts

- Normalized DIS IR: `generated/fastdis_ir_dis6.json`
- Normalized DIS IR: `generated/fastdis_ir_dis7.json`
- Coverage manifest: `generated/message_coverage_manifest.json`
- Coverage doc: `docs/MESSAGE_COVERAGE.md`
- Generation pipeline doc: `docs/GENERATION_PIPELINE.md`
- Schema patch policy: `docs/SCHEMA_PATCHES.md`
- Generated freshness checker: `tools/check_generated_fresh.py`
- Shallow fuzz corpus manifest: `generated/fuzz_shallow_corpus/manifest.json`
- Differential report: `generated/differential_report.json`
- Differential summary: `generated/differential_report.md`
- Orientation formulas: `generated/orientation_formulas.json`
- Native/oracle orientation proof: `verification_reports/alpha3_current/orientation_verification_report.md`
- Visual orientation proof: `verification_reports/alpha3_current/orientation_visual_report.md`
- Orientation pipeline proof: `verification_reports/alpha3_current/orientation_pipeline_report.md`
- Godot workflow proof: `verification_reports/alpha3_current/godot_workflow_report.md`
- Unreal version matrix proof: `verification_reports/alpha3_current/unreal_version_matrix.md`
- Benchmark smoke report: `benchmark_reports/alpha3_smoke/summary.md`
- Benchmark qualification: `benchmark_reports/alpha3_smoke/qualification.json`
- Benchmark combined payload: `benchmark_reports/alpha3_smoke/current.json`
- Benchmark matrix report: `benchmark_reports/alpha3_matrix/summary.md`
- Benchmark matrix qualification: `benchmark_reports/alpha3_matrix/qualification.json`
- Outbound sender benchmark report: `benchmark_reports/alpha3_send_matrix/summary.md`
- Outbound sender benchmark payload: `benchmark_reports/alpha3_send_matrix/current.json`
- Sanitizer smoke proof: `verification_reports/alpha3_current/sanitizer_smoke_report.md`
- I/O routes proof: `verification_reports/alpha3_current/io_routes_report.md`
- Network ingest matrix: `verification_reports/alpha3_current/network_ingest_matrix.md`
- Network send matrix: `verification_reports/alpha3_current/network_send_matrix.md`
- Unreal outbound smoke artifact: `verification_reports/alpha3_current/unreal_udp_send_smoke.json`
- Godot outbound smoke artifact: `verification_reports/alpha3_current/godot_udp_send_smoke.json`
- One-command closeout runner: `tools/run_alpha3_verification_closeout.py`
- Machine-readable release audit: `verification_reports/alpha3_current/alpha3_release_audit_report.md`
- Staged Alpha 3 host bundle: `verification_reports/alpha3_hosts/`
- Source bundle manifest: `RELEASE_MANIFEST.md`
- Source checksums: `CHECKSUMS.sha256`

## Current host evidence

- Native orientation/oracle proof is green on the current macOS host.
- Godot build, verification, demo smoke, and missing-library lanes are green on
  the current macOS host.
- Unreal 5.7 and 5.8 plugin packaging lanes are green on the current macOS
  host.
- Unreal 5.7 and 5.8 orientation/demo harness lanes are green on the current
  macOS host when run with access to the installed Unreal engine tree.
- Alpha 3 sanitizer smoke is green on the current macOS host.
- Alpha 3 benchmark matrix artifacts now extend beyond the earlier smoke-only
  run.
- Outbound localhost sender benchmarks now exist beside the inbound benchmark
  suite for Python, C, C++, and Godot sender surfaces.
- Optional Python-side UDP/replay helpers are implemented and verified through
  a generated Python/Godot I/O routes report.
- The canonical sender/truth-file UDP ingest matrix is green for the Python,
  C, and native C++ localhost receiver lanes, plus current one-entity localhost
  live UDP smoke lanes for Godot and Unreal 5.8.
- The canonical outbound/send matrix is green for the Python, C, and native
  C++ localhost sender lanes.
- Godot outbound localhost UDP replay-send verification is green through the
  headless demo project and the canonical Python verifier.
- Unreal outbound localhost UDP replay-send verification is green through the
  staged automation harness and the canonical Python verifier.
- The engine live UDP matrix should still be described as one-entity smoke
  coverage rather than full multi-entity qualification.

## Remaining release audit

- Confirm all required Alpha 3 proof artifacts are generated from the current tree.
- Confirm Unreal/Godot verification reports are current and tied to shared fixtures.
- Confirm the release bundle wording does not overstate typed DIS support.
- Refresh staged host bundles and package checksums after final artifact review.
