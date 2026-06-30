# Alpha12 Closeout Audit

This audit ties the
[Alpha12 final polish plan](ALPHA12_FINAL_POLISH_PLAN.md) to current local
evidence. It is the release-closeout proof surface for the Unreal/Fab alpha
candidate, not a claim that external marketplace publication has already
happened.

Version lane: `fastdis v0.17.0-alpha12`

Branch lane: `alpha5/v0.15`

Current publish call:
[publish with caveats](ALPHA12_PUBLISH_DECISION.md#decision)

## Evidence Date

The primary local receipts referenced here were regenerated on June 24, 2026:

- `artifacts/reports/unreal_fab_readiness.md`
- `artifacts/reports/unreal_packaged_install_smoke.md`
- `artifacts/reports/release_artifact_smoke.json`
- `artifacts/reports/release_artifact_inspection.json`
- `artifacts/reports/docs_audit.json`

## Success Criteria Audit

| Success criterion | Status | Evidence |
| --- | --- | --- |
| Unreal package metadata matches the release version and status. | proven | `pyproject.toml` uses `0.17.0a12`; `src/fastdis/__init__.py` falls back to `0.17.0a12`; `packages/unreal/FastDis/FastDis.uplugin` uses `Version=12`, `VersionName=0.17.0-alpha12`, `CreatedBy=SheepFling Labs`, and intentionally keeps `IsBetaVersion=true`; `artifacts/reports/unreal_fab_readiness.md` reports those descriptor metadata checks as `ready`. |
| A packaged Unreal plugin zip installs into a clean project without repo-local runtime assumptions. | proven | `artifacts/reports/unreal_packaged_install_smoke.md` reports `status: pass` for Unreal 5.8 from the packaged plugin boundary and opens `/FastDis/Examples/FastDis_Demo`. |
| Fab-facing docs and listing copy are coherent and conservative. | proven with caveats | `packages/unreal/FastDis/Docs/FAB_DRAFT.md` now leads with live UDP, replay, Entity State/ESU, auto-spawn lifecycle, runtime monitoring, and typed-summary PDU events with raw sidecars; `packages/unreal/FastDis/Docs/FIVE_MINUTE_SETUP.md` matches packaged-install flow; `docs/UNREAL_GRILL_PARITY.md` keeps rich native paths separate from typed summaries. |
| Public docs distinguish runtime parity, deeper semantic decoding, and external release operations. | proven | `docs/UNREAL_GRILL_PARITY.md` separates GRILL PDU surface from body depth; `docs/releases/ALPHA12_PUBLISH_DECISION.md` lists semantic-depth and external-marketplace caveats explicitly; this audit keeps local proof separate from publish operations. |
| No new ABI version was introduced unless a concrete blocker required it. | proven | `include/fastdis/fastdis.h` and the staged Unreal ThirdParty header still report `FASTDIS_ABI_EPOCH 0`, `FASTDIS_ABI_REVISION 16`, and `FASTDIS_ABI_VERSION FASTDIS_ABI_REVISION`; `docs/API_STABILITY.md` still describes the ABI as unpublished/internal. |
| Repo green includes the publish lane rather than only source tests. | proven | `artifacts/reports/docs_audit.json`, `artifacts/reports/release_artifact_smoke.json`, `artifacts/reports/release_artifact_inspection.json`, and `artifacts/reports/deliverables_report.json` report `overall_status: pass`; `artifacts/reports/unreal_fab_readiness.md` reports `fab_ready`. |

## Workseries Audit

| Workseries | Status | Evidence |
| --- | --- | --- |
| WS1: Version and metadata hygiene | proven | Python package version, fallback import version, Unreal plugin version fields, publisher text, and intentional beta posture are aligned and checked by `artifacts/reports/unreal_fab_readiness.md`. |
| WS2: Packaged artifact install proof | proven with bounded scope | `artifacts/reports/unreal_packaged_install_smoke.json` proves the packaged plugin installs into a clean project, required authored assets exist, the demo map loads, and the packaged demo map contains a `FastDisDemoController` actor. |
| WS3: Fab listing and media polish | proven for first-draft scope | `packages/unreal/FastDis/Docs/FAB_DRAFT.md`, `packages/unreal/FastDis/Docs/FIVE_MINUTE_SETUP.md`, `docs/UNREAL_FAB_ASSET_WORKLIST.md`, and `artifacts/reports/unreal_fab_readiness.md` keep the listing shell, screenshots, and setup flow aligned to the current package. |
| WS4: Honest surface tightening | proven | `docs/UNREAL_GRILL_PARITY.md`, `packages/unreal/FastDis/Docs/FAB_DRAFT.md`, and `docs/releases/ALPHA12_PUBLISH_DECISION.md` consistently distinguish native snapshot paths from typed-summary Blueprint events with raw sidecars. |
| WS5: Release gates and cleanliness | proven | `python3 tools/dev_check.py --package --release-artifacts` passes from a clean start; docs audit, deliverables report, release artifact smoke, and release artifact inspection all report pass. |
| WS6: Publish decision and follow-on boundary | proven | `docs/releases/ALPHA12_PUBLISH_DECISION.md` records `publish_with_caveats`, and the non-blocking follow-ons stay parked in `docs/PRODUCT_BACKLOG.md` and related Epic 1 / Epic 2 docs rather than leaking into release copy. |

## Publish-Green Interpretation

What the current evidence does prove:

- the Unreal/Fab source shell is `fab_ready`
- the packaged Unreal plugin survives clean install smoke
- docs and generated coverage surfaces are aligned with current generators
- source and release-artifact audits are passing

What the current evidence does not prove by itself:

- Fab marketplace review or listing approval
- hosted release upload completion
- live external account publishing steps

## Non-Blocking Caveats

- Several GRILL-parity PDUs are surfaced as compact typed summaries with raw
  sidecars rather than richer gameplay-ready semantic models. That distinction
  remains explicit in
  [Unreal GRILL parity matrix](../UNREAL_GRILL_PARITY.md).
- The Unreal plugin descriptor intentionally keeps the beta flag set for this
  alpha candidate even though the local publish lane is green.
- Historical helper names such as `build_alpha5_release_artifacts.py` remain in
  lower-level release tooling. They are implementation history, not the current
  public version lane.

## Recommended Ship Boundary

Alpha12 is ready to be presented as a first-draft Unreal/Fab candidate if the
listing and release notes keep these constraints:

- claim the proven Unreal runtime surface
- describe several non-Entity-State PDUs as typed-summary Blueprint events
- avoid claiming full semantic decoding for all 141 DIS 6/7 rows
- keep marketplace submission and hosted-release work framed as external release
  operations

## Definition Of Done Audit

Plan sentence:

> FastDIS can be presented as a polished Unreal/Fab candidate with version-clean
> artifacts, a real packaged-install proof, conservative storefront claims, and
> green release gates, while the remaining semantic-depth caveats are clearly
> documented as follow-on work rather than hidden debt.

Current audit result:

- version-clean artifacts: proven
- real packaged-install proof: proven
- conservative storefront claims: proven
- green release gates: proven
- semantic-depth caveats documented as follow-on work: proven

This means the plan's definition of done is satisfied for a first-draft Fab
candidate, with explicit caveats preserved for external publication steps and
post-alpha semantic depth.

## Related Docs

- [Alpha12 final polish plan](ALPHA12_FINAL_POLISH_PLAN.md)
- [Alpha12 publish decision](ALPHA12_PUBLISH_DECISION.md)
- [Unreal GRILL parity matrix](../UNREAL_GRILL_PARITY.md)
- [Unreal Fab asset worklist](../UNREAL_FAB_ASSET_WORKLIST.md)
