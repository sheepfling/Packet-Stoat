# Alpha 3 Audit

Status: in progress.

This file is the release-truth checklist for `fastdis v0.13.0-alpha3`. Do not
mark Alpha 3 complete until every required item below has direct evidence from
the current source tree or generated artifacts.

## Coverage

- [x] `generated/message_coverage_manifest.json` exists.
- [x] `docs/MESSAGE_COVERAGE.md` exists.
- [x] Coverage docs distinguish catalog coverage from typed parser coverage.
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

## Benchmark qualification

- [x] Benchmark report tool emits latency quantiles.
- [x] Benchmark qualification JSON exists.
- [x] Regression checker accepts combined payloads.
- [x] Repo-local Alpha 3 smoke benchmark artifacts exist under
      `benchmark_reports/alpha3_smoke/`.
- [x] Final benchmark matrix goes beyond smoke coverage and is staged for the
      release bundle.

## Packaging truthfulness

- [x] `ALPHA3_RELEASE_NOTES.md` exists.
- [x] Release notes reference current Alpha 3 proof artifacts and current host
      evidence status.
- [x] `RELEASE_MANIFEST.md` is updated for Alpha 3.
- [x] `CHECKSUMS.sha256` is updated for Alpha 3.
- [x] Final bundle excludes build outputs and engine-generated artifacts.
- [x] Final release wording remains honest about partial typed DIS support.

## Optional I/O helper proof

- [ ] Python-side UDP/replay helpers are on disk.
- [ ] Local network smoke path proves send/receive plus native parser/table/snapshot use.
- [ ] At least one plugin/demo route consumes helper-generated replay data as a
      verification path.
- [ ] Generated I/O route verification report is staged as a release artifact.
