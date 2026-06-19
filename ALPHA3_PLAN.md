# fastdis v0.13.0-alpha3 Plan

Theme: coverage, fuzzing, orientation proof, and performance qualification.

Alpha 1 proved the architecture. Alpha 2 proved the engine-facing workflow.
Alpha 3 should prove message-surface coverage, parser robustness, orientation
correctness, and performance credibility.

The guiding rule is:

```text
Do not claim full typed DIS support before the coverage manifest,
fuzzing depth, and verification evidence can prove what is and is not done.
```

## Release Targets

- Branch: `alpha3/v0.13`
- Version: `fastdis v0.13.0-alpha3`
- Milestone: `Alpha 3`
- Headline: confidence release with explicit message coverage, all-PDU shallow
  fuzzing, deep engine-path hardening, multi-oracle orientation proof, and
  qualified benchmark evidence.

## Honest Product Claim

Alpha 3 should let the project say, precisely:

- Full DIS 6/7 message catalog coverage: yes.
- Safe header and minimum-length handling across all cataloged PDUs: yes.
- Typed semantic body parsing: only for selected PDUs.
- Engine-ready fast path: Entity State first, with explicit follow-on PDU
  expansion after fuzz/coverage infrastructure is in place.
- Orientation support: basis/quaternion driven and verified by native,
  oracle, and in-engine evidence; never raw Euler passthrough.
- Optional UDP/replay tooling: yes, but outside the core parser ABI and
  explicitly separated from the packet-processing SDK contract.

## Success Criteria

- Every known DIS 6/7 catalog entry appears in a generated coverage manifest.
- Every known PDU has shallow fuzz coverage for header/min-length/dispatch
  safety.
- Every typed parser has deep fuzz coverage plus sanitizer coverage.
- C++ orientation math agrees with an independent Python oracle, SciPy basis
  checks, SymPy-derived formulas, and golden DIS fixtures.
- Unreal and Godot in-engine orientation verification remain green using shared
  fixtures.
- Benchmark reports cover throughput and latency for native, Python, snapshot,
  and engine-facing transform paths.
- Optional networking/replay tools exist for capture, replay, smoke, and
  engine/demo workflows without forcing sockets into the core library ABI.
- Release docs and bundle state exactly what is cataloged, shallow-fuzzed,
  deeply parsed, benchmarked, and verified.

## Workseries

### WS1: Release Branch, Scope Guardrails, and Version Bump

Goal: start Alpha 3 from a controlled branch and keep claims tighter than code.

Tasks:
- Create `ALPHA3_PLAN.md`, `ALPHA3_GOAL.md`, and `ALPHA3_RELEASE_NOTES.md`.
- Update `docs/ROADMAP.md` to point at Alpha 3 as the active release target.
- Add a release checklist section for coverage manifest, fuzz corpus, oracle
  evidence, and benchmark qualification.
- Keep the ABI policy conservative; do not change the C ABI without a concrete
  reason and migration note.

Exit criteria:
- Alpha 3 planning docs are on disk.
- Release notes skeleton exists.
- Roadmap points to Alpha 3.

### WS2: Message Coverage Manifest

Goal: make the real DIS surface area explicit and machine-checked.

Tasks:
- Generate `generated/message_coverage_manifest.json`.
- Add `docs/MESSAGE_COVERAGE.md`.
- Define one row per known PDU with fields such as:
  `cataloged`, `header_validated`, `min_length_known`,
  `typed_prefix_parser`, `full_parser`, `serializer`,
  `roundtrip_tested`, `fuzzed_shallow`, `fuzzed_deep`,
  and `differential_oracle`.
- Add a stale-manifest checker so CI can fail when the manifest is not
  regenerated after catalog changes.

Exit criteria:
- Every known PDU appears in the manifest.
- `docs/MESSAGE_COVERAGE.md` is generated from machine data.
- CI can detect stale or incomplete manifest state.

### WS3: All-PDU Shallow Fuzzing

Goal: ensure every cataloged PDU type is safe at the header/dispatch layer.

Tasks:
- Add shallow fuzz targets for:
  `fuzz_header`, `fuzz_scan_many`, `fuzz_catalog_dispatch`,
  `fuzz_min_lengths`, and `fuzz_unknown_pdu`.
- Generate seeds for minimum length, one-byte-short, declared-length-too-small,
  declared-length-too-large, valid-header-random-body, and truncated-body
  cases for DIS 6 and DIS 7 variants.
- Record corpus management rules and fuzz smoke commands.

Exit criteria:
- Every known PDU has shallow fuzz coverage.
- Random and malformed inputs do not crash, hang, or read out of bounds.
- Corpus seeds are tracked and reusable.

### WS4: Deep Fuzzing for Typed and Engine-Facing Paths

Goal: harden the code that converts raw packets into typed records and engine
 transforms.

Tasks:
- Expand deep fuzz targets for:
  `entity_state_prefix`, `entity_transform`, `entity_table`,
  `snapshot_buffer`, `frame_transform`, and `orientation`.
- Run ASAN and UBSAN routinely; keep TSAN optional where practical.
- Add a short CI fuzz smoke lane and a longer pre-release/nightly lane.
- Track corpus retention and crash triage policy.

Exit criteria:
- Typed fast paths all have deep fuzz targets.
- Sanitizer fuzz smoke passes.
- No known crashing corpus remains unresolved.

### WS5: Differential Parser and Catalog Tests

Goal: compare fastdis against independent implementations without copying their
 APIs or claiming they are normative.

Tasks:
- Add differential tests against Open-DIS Python where practical.
- Compare header interpretation, catalog identity, minimum lengths, and typed
  Entity State behavior.
- Keep a clear distinction between authoritative standard behavior and
  implementation-oracle disagreement reports.

Exit criteria:
- Differential comparison tooling exists.
- Mismatches are surfaced in a machine-readable report.
- Known divergences are documented.

### WS6: Orientation Paranoia Suite

Goal: move orientation from "carefully experimental" to "proven by multiple
 independent oracles."

Tasks:
- Add `tests/oracles/scipy_orientation_oracle.py`.
- Add `tools/derive_orientation_matrices.py`.
- Add `docs/derivations/dis_orientation_sympy.md`.
- Add `generated/orientation_formulas.json`.
- Compare basis/quaternion behavior across:
  native C++ implementation,
  independent Python hand-derived oracle,
  SciPy rotation checks,
  SymPy symbolic derivation,
  and Koks/OpenDIS golden fixtures.
- Expand randomized and near-singularity cases.

Exit criteria:
- Native/oracle/SciPy/SymPy results agree within defined tolerances.
- Golden DIS orientation cases pass.
- Orientation APIs remain basis/quaternion centered.

### WS7: In-Engine Orientation Verification

Goal: prove orientation inside each engine transform system, not only in native
 math tests.

Tasks:
- Keep Unreal and Godot numerical axis checks driven by shared fixtures.
- Keep Unreal and Godot visual verification scenes current with the fixture
  set.
- Add Unity and Cesium convention-study docs plus at least scaffolded
  verification assets and fixture targets.
- Extend reports so runtime and visual verification are part of release proof.

Exit criteria:
- Unreal in-engine axis tests pass.
- Godot in-engine basis tests pass.
- Shared fixtures drive native and engine verification.
- Unity and Cesium convention work is on disk and linked from docs.

### WS8: Benchmark Qualification Matrix

Goal: support honest performance claims with repeatable evidence, not only
 development guidance.

Tasks:
- Expand workloads for:
  1 / 100 / 10k / 100k entities,
  sparse updates,
  mixed traffic,
  accepted-after-filter traffic,
  snapshot slot-count behavior,
  position-only transforms,
  position-plus-orientation transforms,
  and engine-side apply cost.
- Add latency reporting:
  p50 / p95 / p99 ingest, publish, acquire/apply/release.
- Record allocation behavior and bounded-allocation expectations.
- Add regression gates for core native paths.

Exit criteria:
- Benchmark reports cover throughput and latency.
- Regression checker enforces Alpha 3 thresholds.
- Orientation and engine transform cost is measured explicitly.

### WS9: Next Typed Fast Paths

Goal: extend typed support only after the coverage and fuzz harness can absorb
 the risk.

Suggested order:
- Fire
- Detonation
- Collision
- Transmitter
- Signal
- Receiver
- Electromagnetic Emission
- Designator

Tasks:
- Choose the first next PDU family with clear engine/runtime value.
- Add typed prefix parse, tests, fuzz seeds, and coverage-manifest status.
- Do not batch-claim "full support" for families that lack typed coverage.

Exit criteria:
- At least one post-Entity-State typed path lands with full Alpha 3 discipline.
- Coverage manifest and docs reflect the exact status.

### WS10: Packaging, Audit, and Release Truthfulness

Goal: ship a source bundle whose claims are backed by generated proof.

Tasks:
- Add `ALPHA3_AUDIT.md`.
- Add release-bundle sections for:
  coverage manifest,
  fuzz report,
  differential report,
  orientation verification report,
  and benchmark qualification report.
- Keep the bundle source-only.
- Ensure docs clearly separate catalog coverage from typed parser coverage.

Exit criteria:
- Bundle contains machine-generated proof artifacts.
- Checksums and release manifest are complete.
- Release notes make no unsupported claims.

### WS11: Optional Networking and Replay Utilities

Goal: add practical sender/receiver/capture/replay tooling without expanding
the core parser ABI or conflating convenience I/O with the deterministic
packet-processing surface.

Tasks:
- Keep the layering explicit:
  `libfastdis` = parser/scanner/table/snapshot/orientation, no sockets
  required.
  optional `fastdis_io` / helper layer = UDP, multicast, replay, capture, CLI
  utilities.
- Add architecture docs:
  `docs/NETWORKING.md` and `docs/REPLAY_FORMAT.md`.
- Define optional C++ I/O surfaces for:
  `UdpReceiver`, `UdpSender`, `ReplayReader`, `ReplayWriter`,
  `ReplaySender`, and portable config types.
- Add CLI/tooling plan for:
  `fastdis-recv`,
  `fastdis-send-entity`,
  `fastdis-capture`,
  `fastdis-replay-send`,
  and `fastdis-net-smoke`.
- Keep Python wrappers as convenience/debug tooling, not the engine fast path.
- Extend `.fastdispkt` planning to support replay v2 with timestamps and
  source metadata while preserving v1 reader compatibility.
- Add a portability matrix for unicast/multicast and host-specific quirks.

Exit criteria:
- Networking/replay scope, layering, and non-goals are documented.
- Replay v1 versus v2 expectations are documented.
- Alpha 3 issue breakdown includes optional UDP/replay work without claiming it
  as part of the core C ABI.
- Build/config docs describe how optional I/O and tools remain separable from
  the core library build.

## Recommended Execution Order

1. WS1 release setup and scope guardrails.
2. WS2 message coverage manifest.
3. WS3 all-PDU shallow fuzzing.
4. WS4 deep fuzzing for typed and engine-facing paths.
5. WS5 differential parser checks.
6. WS6 orientation paranoia suite.
7. WS7 in-engine orientation verification expansion.
8. WS8 benchmark qualification matrix.
9. WS11 optional networking/replay utilities.
10. WS9 next typed fast paths.
11. WS10 packaging and release audit.

The networking/replay lane belongs after the coverage/fuzz/orientation
baseline is in place so demos and smoke tools consume the same validated packet
pipeline instead of becoming a second parser architecture.

## Alpha 3 Optional I/O Issue Breakdown

- `A3-030` optional `fastdis_io` C++ UDP sender/receiver layer
- `A3-031` `fastdis-recv` CLI
- `A3-032` `fastdis-send-entity` CLI
- `A3-033` `fastdis-capture` CLI
- `A3-034` `fastdis-replay-send` CLI
- `A3-035` `.fastdispkt` v2 timestamps/source metadata
- `A3-036` local network smoke test
- `A3-037` Python `tools.recv` / `send_entity` / `capture` / `replay_send`
- `A3-038` `docs/NETWORKING.md`
- `A3-039` `docs/REPLAY_FORMAT.md`
- `A3-040` UDP/multicast portability matrix

## Alpha 3 Definition of Done

Alpha 3 is ready when this is true:

- Every cataloged PDU appears in `docs/MESSAGE_COVERAGE.md`.
- Every cataloged PDU has shallow fuzz coverage.
- Every typed parser has deep fuzz and sanitizer coverage.
- Orientation math is proven by native, Python, SciPy, SymPy, and golden-case
  agreement.
- Unreal and Godot engine verification pass from shared fixtures.
- Benchmark reports explain throughput, latency, transform cost, and snapshot
  pressure.
- The source bundle includes coverage, fuzz, benchmark, and orientation proof
  artifacts with checksums.

## Immediate Next Task

Start with WS2: generate the message coverage manifest. That becomes the truth
table for fuzzing depth, parser claims, docs, benchmarks, and release honesty.
