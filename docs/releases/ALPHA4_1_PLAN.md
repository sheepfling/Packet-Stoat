# fastdis v0.14.1-alpha4.1 Plan

Theme: Lattice SDK and gRPC contract tightening without credentials.

Alpha 4 proved the local bridge seam:

- DIS/native snapshots can become canonical entities.
- Canonical entities can become Lattice-shaped payloads.
- The local shim can publish, stream, store bounded objects, and round-trip
  mock entities back to DIS Entity State.

Alpha 4.1 should not become "more mock Lattice." It should reduce the gap
between Packet-Stoat's local bridge and the public Lattice SDK/docs while
staying honest that real sandbox transport still requires credentials.

Alpha 4.1 should also prove the high-rate contract shape that a real Lattice
integration would likely depend on:

- client-streaming publish semantics
- server-streaming entity-component semantics
- retry/reconnect policy owned by the integration

The gRPC goal is not "implement Lattice gRPC." The gRPC goal is:

```text
Prove Packet-Stoat's mock/shim can exercise the same publish and stream
behaviors that a real high-rate Lattice integration would rely on,
without claiming official vendor wire compatibility.
```

The guiding rule is:

```text
Do not claim real Lattice verification without sandbox credentials.
Do tighten the public-doc and SDK-shape contract until the remaining unknowns
are genuinely auth/transport dependent.
```

## Release Targets

- Branch lane: `alpha4/v0.14`
- Version lane: `fastdis v0.14.1-alpha4.1`
- Milestone: `Alpha 4.1`
- Headline: no-credential SDK compatibility audit, contract gap report, and
  public-sample parity evidence for the Alpha 4 bridge.

## Success Criteria

- Alpha 4.1 docs explain the no-credential boundary clearly.
- A machine-readable contract audit exists for emitted Lattice-shaped payloads.
- A machine-readable sample/SDK parity audit exists for the adapter surface.
- A machine-readable gRPC contract audit/report exists for publish and stream
  behavior.
- The real backend stub supports dry-run-safe construction and SDK-like config
  names without making network calls.
- Optional SDK import tests exist and skip cleanly when the public package is
  not installed.
- Optional official gRPC stub import/serialization checks are scoped as a
  follow-on, not required for the first useful pass.
- A generated gap report says exactly what is proven locally and what still
  requires real sandbox credentials.

## Workseries

### WS1: Alpha 4.1 scope and release docs

Goal: document Alpha 4.1 as a bounded compatibility-tightening pass.

Tasks:
- Add `docs/releases/ALPHA4_1_PLAN.md`
- Add `docs/releases/ALPHA4_1_GOAL.md`
- Add `docs/LATTICE_CONTRACT_AUDIT.md`
- Add `docs/LATTICE_SAMPLE_PARITY.md`
- Add `docs/LATTICE_GRPC_CONTRACT.md`

Exit criteria:
- The repo has an explicit Alpha 4.1 scope doc.
- The public-doc/SDK/gRPC audit lane is described without overstating proof.

### WS2: Payload contract audit

Goal: score current emitted payloads against public-facing field expectations.

Tasks:
- Add `tools/lattice_contract_audit.py`
- Audit:
  - required public-leaning fields
  - bridge-sidecar fields
  - missing/gap fields
  - loop-suppression provenance markers
- Emit JSON and Markdown reports under:
  - `verification_reports/alpha4_1/lattice/`

Exit criteria:
- The repo can generate one contract audit report from current fixtures.
- Missing fields become explicit evidence instead of tribal knowledge.

### WS3: SDK/sample parity audit

Goal: make the future real backend SDK-shaped before credentials exist.

Tasks:
- Add a dry-run-safe real backend config surface with:
  - endpoint
  - client_id
  - client_secret
  - token
  - dry_run
- Add `tools/lattice_sample_parity_audit.py`
- Add `tools/run_alpha4_1_sdk_gap_report.py`
- Check:
  - config name parity
  - adapter method parity
  - optional SDK import availability
  - expected local-vs-real boundary

Exit criteria:
- The real backend can be instantiated safely with no credentials in dry-run.
- The SDK gap report names the remaining credential-gated work explicitly.

### WS4: gRPC shim contract

Goal: prove the high-rate publish/stream seam locally with a Packet-Stoat-owned
proto before attempting official vendor wire compatibility.

Tasks:
- Add a Packet-Stoat-owned proto under:
  - `packages/lattice/proto/packetstoat/lattice_shim/v1/`
- Scope the local gRPC seam to:
  - client-streaming `PublishEntities`
  - server-streaming `StreamEntityComponents`
- Keep the first proto intentionally small:
  - JSON payload carriage is acceptable for the first pass
  - summary counts are required
  - heartbeats and per-entity update throttling are required
- Treat objects as out of scope for gRPC in this lane.

Exit criteria:
- The Alpha 4.1 plan has a concrete Packet-Stoat-owned gRPC seam.
- The repo explicitly treats object transport as REST-oriented, not a gRPC goal.

### WS5: Publish/stream semantics and chaos policy

Goal: define the behavior contract before implementation details sprawl.

Tasks:
- Publish path acceptance:
  - 50 entities x 10 Hz x 60 seconds
  - 500 entities x 20 Hz short soak
  - stable per-entity ordering
  - coalesce-by-entity under overload
  - summary counts: received, accepted, rejected, coalesced, dropped
- Stream path acceptance:
  - preexisting entities first
  - update events
  - deleted/stale events
  - heartbeats while idle
  - component filtering
  - per-entity rate limiting
- Retry/chaos cases:
  - `UNAVAILABLE`
  - `DEADLINE_EXCEEDED`
  - `RESOURCE_EXHAUSTED`
  - `INVALID_ARGUMENT`
  - `CANCELLED`
  - `UNAUTHENTICATED` as explicit credential-gated terminal behavior

Exit criteria:
- The plan names the intended stream/event contract and failure policy.
- Retry/backoff responsibility is explicitly owned by Packet-Stoat integration
  code, not assumed to belong to the SDK.

### WS6: Optional official-stub compatibility check

Goal: tighten the no-credential proof without overcommitting to full vendor
service emulation.

Tasks:
- Treat official Buf/protobuf checks as optional in Alpha 4.1.
- Scope the optional check to:
  - stub import
  - request object construction
  - serialization/deserialization
  - local fake response consumption
- Do not make a full fake vendor API server a requirement.

Exit criteria:
- The repo has a documented path for official-stub checks.
- Full vendor wire/API emulation remains explicitly deferred.

### WS7: Verification

Goal: prove the Alpha 4.1 lane is runnable and honest.

Tasks:
- Add tests for:
  - contract audit
  - sample parity audit
  - dry-run real backend
  - optional SDK import contract
  - planned gRPC publish/stream contract surface
- Run the new tests locally.

Exit criteria:
- The Alpha 4.1 audit tools pass locally.
- SDK import tests skip cleanly if `anduril-lattice-sdk` is absent.
- The gRPC lane has explicit acceptance targets and planned report artifacts.

## Definition Of Done

Alpha 4.1 is done when this sentence is true:

```text
Packet-Stoat is locally end-to-end proven for the Alpha 4 bridge, and the
remaining gap to real Lattice is reduced to public-SDK/sample alignment,
high-rate gRPC contract proof, plus credential-gated auth/transport behavior
that is explicitly reported.
```
