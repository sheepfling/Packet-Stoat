# fastdis v0.17.0-alpha12 Final Polish Plan

Theme: finish the Unreal/Fab product lane with honest publish polish while
keeping Epic 2 evidence green.

Alpha 12 closes the major Epic 2 parity tranche and leaves FastDIS in a strong
technical position:

- the GRILL-target Unreal runtime surface is present
- the Unreal Fab readiness gate currently reports `fab_ready`
- the 141-row deep/runtime parity lane is green across tracked surfaces

The remaining work should not become "one more feature wave." The goal is to
turn the current state into a publishable, supportable, and conservative public
release candidate.

The guiding rule is:

```text
Prefer release honesty and polish over new surface area.
Do not grow ABI or invent new product claims unless a real publish blocker
requires it.
```

## Current State

- Unreal runtime GRILL-parity surface is tracked in
  [docs/UNREAL_GRILL_PARITY.md](../UNREAL_GRILL_PARITY.md).
- Epic 1 product gate and Epic 2 follow-on are tracked in
  [docs/PRODUCT_BACKLOG.md](../PRODUCT_BACKLOG.md).
- Local Unreal publish shell reports `fab_ready` through
  `python tools/check_unreal_fab_readiness.py --strict`.
- The current remaining caveats are mostly release polish and semantic-depth
  caveats:
  - plugin metadata/version drift
  - Fab package install smoke from packaged artifacts
  - storefront copy/media review
  - typed-summary PDU surfaces that should not be overstated as rich semantic
    gameplay models

## Release Targets

- Branch lane: `alpha5/v0.15`
- Version lane: `fastdis v0.17.0-alpha12`
- Milestone: `Alpha 12 final polish`
- Headline: publish-ready Unreal/Fab candidate with conservative claims,
  version-clean packaging, and release gates that match what is actually
  shipped.

## Goal Blurb

FastDIS finishes the GRILL-parity Unreal product lane to a good degree of
polish: package metadata matches the release, Fab-facing content is coherent,
artifact installs are proven from packaged outputs, public claims stay
conservative, and Epic 2 quality gates remain green while richer semantics stay
explicitly scoped as follow-on work.

## Success Criteria

- Unreal package metadata matches the actual release version and status.
- A packaged Unreal plugin zip can be installed into a clean project and opened
  without repo-local assumptions.
- Fab-facing docs, screenshots, and listing copy are coherent and conservative.
- Public docs distinguish:
  - runtime parity surface
  - deeper semantic decoding
  - release operations that still depend on marketplace review or external
    accounts
- No new ABI version is introduced unless a concrete shipping blocker demands
  it.
- Repo green includes the publish lane:
  - generation
  - docs/link checks
  - lint
  - tests
  - Unreal package verification
  - evidence verification
  - release artifact inspection

## Workseries

### WS1: Version And Metadata Hygiene

Goal: remove release drift so packaged artifacts describe the thing being cut.

Tasks:
- Update Unreal plugin descriptor version fields to match `v0.17.0-alpha12`.
- Review plugin description/category/publisher text for Fab-facing clarity.
- Decide whether `IsBetaVersion` remains appropriate for this submission lane.
- Add a check that fails if release metadata and package version drift.
- Audit docs and screenshots for stale alpha numbers.

Exit criteria:
- The `.uplugin`, Python package version, release docs, and artifact names use a
  coherent alpha label.
- Version drift becomes a gate failure rather than a manual catch.

### WS2: Packaged Artifact Install Proof

Goal: prove the shipped package, not just the repo, is usable.

Tasks:
- Build the Unreal plugin zip through the normal packaging flow.
- Install that packaged zip into a clean Unreal project.
- Open the demo map and exercise:
  - live UDP receive
  - replay ingest
  - entity auto-spawn
  - Remove Entity lifecycle
  - Fire/Detonation/Designator surfaced behavior
- Record the install-smoke result in a generated report.
- Confirm the packaged plugin does not depend on repo-local generated files or
  scripts at runtime.

Exit criteria:
- A packaged-plugin install smoke is reproducible.
- The shipped plugin can be demonstrated from its own artifact boundary.

### WS3: Fab Listing And Media Polish

Goal: make the marketplace presentation match the actual product surface.

Tasks:
- Review `Docs/FAB_DRAFT.md`, screenshots, and store visuals for conservative
  wording.
- Ensure screenshots come from the real demo map and current plugin state.
- Tighten the five-minute setup doc so it matches the packaged install flow.
- Prepare a short feature list that leads with:
  - live UDP receive/send
  - replay ingest
  - Entity State and ESU handling
  - auto-spawn and Remove Entity policy
  - Blueprint event surfaces
  - runtime monitoring
- Avoid claiming richer semantics where the current behavior is typed-summary
  plus raw sidecar.

Exit criteria:
- Storefront media and text match current runtime truth.
- A reviewer or user can understand the product quickly without being misled.

### WS4: Honest Surface Tightening

Goal: reduce the biggest remaining parity caveats without turning the lane back
into a broad feature program.

Tasks:
- Review Start/Resume, Stop/Freeze, Electromagnetic Emission, Signal, and
  Designator wording across docs.
- Standardize the distinction between:
  - rich native semantic model
  - typed summary event
  - raw-sidecar-preserving event
- Fix any places that read as fuller support than the runtime currently proves.
- Optionally deepen one or two high-value event structs only if it removes
  product confusion without forcing new ABI churn.

Exit criteria:
- The publish story stays honest about current semantic depth.
- Any additional event-depth work is small, targeted, and evidence-backed.

### WS5: Release Gates And Cleanliness

Goal: make repo green mean publish-green for this lane.

Tasks:
- Ensure docs link/orphan checks cover the new release plan and Fab docs.
- Re-run:
  - generated artifact checks
  - Epic 2 parity/audit checks
  - evidence pack generation and verification
  - Unreal Fab readiness check
  - packaged plugin verification
- Inspect staged release outputs for:
  - stale generated files
  - accidental cross-compile products
  - unexpected versioned artifacts
  - secrets or local-only files
- Confirm checked-in generated files are intentional inputs to user experience
  or documentation, not transient scratch output.

Exit criteria:
- "Green" includes the actual publish lane, not only source tests.
- Artifact inspection and documentation checks are part of the closeout proof.

### WS6: Publish Decision And Follow-On Boundary

Goal: separate what should ship now from what belongs to the next tranche.

Tasks:
- Produce a short publish decision memo:
  - publish now
  - publish with caveats
  - hold for blockers
- List any remaining GRILL-vs-FastDIS caveats that should stay explicit in the
  listing or release notes.
- Move non-blocking follow-ons into backlog items, especially:
  - deeper semantic models for typed-summary PDUs
  - hard Unreal Georeferencing/Cesium integrations if later needed
  - broader post-Fab differentiator work

Exit criteria:
- The publish/no-publish call is explicit.
- Remaining work is parked in the backlog instead of leaking into release copy.

## Non-Goals

- No broad new Unreal feature wave.
- No new 141-row expansion campaign; Epic 2 remains green and honest, but this
  plan is not another coverage push.
- No ABI churn unless a shipping blocker demonstrates the need.
- No stronger marketplace claim than the current runtime and packaged artifact
  proof support.

## Definition Of Done

Alpha 12 final polish is done when this sentence is true:

```text
FastDIS can be presented as a polished Unreal/Fab candidate with version-clean
artifacts, a real packaged-install proof, conservative storefront claims, and
green release gates, while the remaining semantic-depth caveats are clearly
documented as follow-on work rather than hidden debt.
```

Current closeout evidence is tracked in
[Alpha12 closeout audit](ALPHA12_CLOSEOUT_AUDIT.md).
