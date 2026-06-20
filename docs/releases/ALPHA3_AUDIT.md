# Alpha 3 Audit

Status: complete.

This file is the release-truth checklist for `fastdis v0.13.0-alpha3`. Do not
mark Alpha 3 complete until every required item below has direct evidence from
the current source tree or generated artifacts.

## Coverage

- [x] `generated/fastdis_ir_dis6.json` exists.
- [x] `generated/fastdis_ir_dis7.json` exists.
- [x] `generated/message_coverage_manifest.json` exists.
- [x] `docs/MESSAGE_COVERAGE.md` exists.
- [x] `docs/GENERATION_PIPELINE.md` exists.
- [x] `docs/SCHEMA_PATCHES.md` exists.
- [x] Coverage docs distinguish catalog coverage from typed parser coverage.
- [x] Generated freshness checker exists: `tools/check_generated_fresh.py`.
- [x] Coverage manifest `differential_oracle` fields are populated for the
      Entity State typed fast path that now has independent Open-DIS comparison
      evidence.

## Fuzzing and hardening

- [x] Shallow all-PDU fuzz targets are on disk.
- [x] Shallow fuzz corpus manifest exists at
      `generated/fuzz_shallow_corpus/manifest.json`.
- [x] Deep fuzz targets for typed/engine-facing paths are on disk.
- [x] Final Alpha 3 sanitizer/fuzz smoke report is staged as a release artifact.

## Differential comparison

- [x] Differential tool exists: `tools/run_differential_report.py`.
- [x] Machine-readable differential report exists:
      `generated/differential_report.json`.
- [x] Human-readable differential summary exists:
      `generated/differential_report.md`.
- [x] Known divergences are reflected in `docs/DIFFERENTIAL_TESTING.md` and
      called out for release-audit review.

## Orientation

- [x] SciPy oracle checks are on disk.
- [x] SymPy derivation checks are on disk.
- [x] Generated orientation formulas exist.
- [x] Native/oracle orientation report exists at
      `verification_reports/alpha3_current/orientation_verification_report.md`.
- [x] Godot verification/workflow report exists at
      `verification_reports/alpha3_current/godot_workflow_report.md`.
- [x] Unreal verification report is current for Alpha 3 packaging and either
      passes or is accompanied by an explicit release-blocking note and
      rerun instructions.

## Orientation Visual Verification Expansion

- [x] Visual-verification design doc exists:
      `docs/ORIENTATION_VISUAL_VERIFICATION.md`.
- [x] Alpha 3 plan explicitly tracks screenshot/image-check/contact-sheet work.
- [x] Negative mapping cases are planned as executable failure checks.
- [x] Visual review artifacts exist under
      `verification_reports/alpha3_current/orientation_visual_review/`.
- [x] Visual verification report exists at
      `verification_reports/alpha3_current/orientation_visual_report.md`.
- [x] Future release audit distinguishes numeric engine proof from visual proof.

## Orientation Inspection and Calibration Expansion

- [x] Pipeline design doc exists: `docs/ORIENTATION_PIPELINE.md`.
- [x] Tweak workflow doc exists: `docs/ORIENTATION_TWEAKING.md`.
- [x] Failure-signature doc exists:
      `docs/ORIENTATION_FAILURE_SIGNATURES.md`.
- [x] Alpha 3 plan explicitly tracks pipeline trace / config / solver work.
- [x] Orientation pipeline proof report exists:
      `verification_reports/alpha3_current/orientation_pipeline_report.md`.
- [x] Future release audit checks pipeline traces, config snapshots, and
      known-bad preserved regressions separately from the visual lane.

## Benchmark qualification

- [x] Benchmark report tool emits latency quantiles.
- [x] Benchmark qualification JSON exists.
- [x] Regression checker accepts combined payloads.
- [x] Alpha 3 benchmark runners emit local smoke/matrix artifacts on demand.
- [x] Final benchmark matrix is generated locally rather than staged for the
      release bundle.

## Packaging truthfulness

- [x] `ALPHA3_RELEASE_NOTES.md` exists.
- [x] Release notes reference current Alpha 3 proof artifacts and current host
      evidence status.
- [x] Alpha 3 packaging generates bundle-local `RELEASE_MANIFEST.md`.
- [x] Alpha 3 packaging generates bundle-local `CHECKSUMS.sha256`.
- [x] Alpha 3 packaging excludes unexpected `verification_reports/alpha3_hosts`
      junk and only bundles the canonical staged host proof filenames plus
      host manifests.
- [x] Final bundle excludes build outputs and engine-generated artifacts.
- [x] Final release wording remains honest about partial typed DIS support.

## Optional I/O helper proof

- [x] Python-side UDP/replay helpers are on disk.
- [x] Local network smoke path proves send/receive plus native parser/table/snapshot use.
- [x] At least one plugin/demo route consumes helper-generated replay data as a
      verification path.
- [x] Generated I/O route verification report is staged as a release artifact.
- [x] Canonical sender/truth-file localhost UDP verification passes for the
      Python, C, and C++ receiver routes.
- [x] Canonical replay/truth-file localhost UDP verification passes for the
      Python, C, and C++ sender routes through
      `verification_reports/alpha3_current/network_send_matrix.md`.
- [x] Live UDP engine-ingest verification has executable proof for Godot and
      Unreal through the current one-entity localhost smoke lanes recorded in
      `verification_reports/alpha3_current/network_ingest_matrix.md`.
- [x] Godot localhost outbound UDP replay-send verification has executable
      proof through `verification_reports/alpha3_current/godot_udp_send_smoke.json`.
- [x] Unreal localhost outbound UDP replay-send has executable proof through
      `verification_reports/alpha3_current/unreal_udp_send_smoke.json`.
- [x] Outbound localhost sender benchmark tooling exists beside the inbound
      benchmark suite through `tools/run_send_benchmarks.py`.
- [x] A canonical C receiver verification tool exists and is exercised by the
      generated network-ingest matrix.
