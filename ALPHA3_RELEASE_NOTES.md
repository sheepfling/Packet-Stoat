# fastdis v0.13.0-alpha3 Release Notes

Theme: coverage, fuzzing, orientation proof, and performance qualification.

This release is intended to be a confidence release. It should state exactly
what the SDK covers, what has been hardened, what has been verified by
independent oracles, and what remains intentionally partial.

## Planned highlights

- Generated DIS 6/7 message coverage manifest and cross-language catalog docs.
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
- Safe header/dispatch handling across cataloged PDUs: yes.
- Full typed semantic parser coverage for every DIS PDU: no.
- Typed fast path quality focus: Entity State first.
- Orientation API: basis/quaternion driven, not Euler passthrough.

## Proof artifacts

- Coverage manifest: `generated/message_coverage_manifest.json`
- Coverage doc: `docs/MESSAGE_COVERAGE.md`
- Shallow fuzz corpus manifest: `generated/fuzz_shallow_corpus/manifest.json`
- Differential report: `generated/differential_report.json`
- Differential summary: `generated/differential_report.md`
- Orientation formulas: `generated/orientation_formulas.json`
- Native/oracle orientation proof: `verification_reports/alpha3_current/orientation_verification_report.md`
- Godot workflow proof: `verification_reports/alpha3_current/godot_workflow_report.md`
- Unreal version matrix proof: `verification_reports/alpha3_current/unreal_version_matrix.md`
- Benchmark smoke report: `benchmark_reports/alpha3_smoke/summary.md`
- Benchmark qualification: `benchmark_reports/alpha3_smoke/qualification.json`
- Benchmark combined payload: `benchmark_reports/alpha3_smoke/current.json`
- Benchmark matrix report: `benchmark_reports/alpha3_matrix/summary.md`
- Benchmark matrix qualification: `benchmark_reports/alpha3_matrix/qualification.json`
- Sanitizer smoke proof: `verification_reports/alpha3_current/sanitizer_smoke_report.md`
- I/O routes proof: `verification_reports/alpha3_current/io_routes_report.md`
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
- Optional Python-side UDP/replay helpers are implemented and verified through
  a generated Python/Godot I/O routes report.

## Remaining release audit

- Confirm all required Alpha 3 proof artifacts are generated from the current tree.
- Confirm Unreal/Godot verification reports are current and tied to shared fixtures.
- Confirm the release bundle wording does not overstate typed DIS support.
- Refresh staged host bundles and package checksums after final artifact review.
