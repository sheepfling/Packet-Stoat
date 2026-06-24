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

- `build/reports/unreal_fab_readiness.md`
- `build/reports/unreal_packaged_install_smoke.md`
- `build/reports/release_artifact_smoke.json`
- `build/reports/release_artifact_inspection.json`
- `build/reports/docs_audit.json`

## Success Criteria Audit

| Success criterion | Status | Evidence |
| --- | --- | --- |
| Unreal package metadata matches the release version and status. | proven | `pyproject.toml` uses `0.17.0a12`; `src/fastdis/__init__.py` falls back to `0.17.0a12`; `examples/unreal/FastDis/FastDis.uplugin` uses `Version=12` and `VersionName=0.17.0-alpha12`; `build/reports/unreal_fab_readiness.md` reports both descriptor version checks as `ready`. |
| A packaged Unreal plugin zip installs into a clean project without repo-local runtime assumptions. | proven | `build/reports/unreal_packaged_install_smoke.md` reports `status: pass` for Unreal 5.8 from the packaged plugin boundary and opens `/FastDis/Examples/FastDis_Demo`. |
| Fab-facing docs and listing copy are coherent and conservative. | proven with caveats | `examples/unreal/FastDis/Docs/FAB_DRAFT.md` now leads with live UDP, replay, Entity State/ESU, auto-spawn lifecycle, runtime monitoring, and typed-summary PDU events with raw sidecars; `examples/unreal/FastDis/Docs/FIVE_MINUTE_SETUP.md` matches packaged-install flow; `docs/UNREAL_GRILL_PARITY.md` keeps rich native paths separate from typed summaries. |
| Public docs distinguish runtime parity, deeper semantic decoding, and external release operations. | proven | `docs/UNREAL_GRILL_PARITY.md` separates GRILL PDU surface from body depth; `docs/releases/ALPHA12_PUBLISH_DECISION.md` lists semantic-depth and external-marketplace caveats explicitly; this audit keeps local proof separate from publish operations. |
| No new ABI version was introduced unless a concrete blocker required it. | proven | `include/fastdis/fastdis.h` and the staged Unreal ThirdParty header still report `FASTDIS_ABI_EPOCH 0`, `FASTDIS_ABI_REVISION 16`, and `FASTDIS_ABI_VERSION FASTDIS_ABI_REVISION`; `docs/API_STABILITY.md` still describes the ABI as unpublished/internal. |
| Repo green includes the publish lane rather than only source tests. | proven with one non-blocking warning | `build/reports/docs_audit.json`, `build/reports/release_artifact_smoke.json`, and `build/reports/release_artifact_inspection.json` report `overall_status: pass`; `build/reports/unreal_fab_readiness.md` reports `fab_ready`; `build/reports/deliverables_report.md` is only `warn` because of duplicate local build artifacts, not checked-in source drift. |

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
- `build/reports/deliverables_report.md` is a warning report because local
  duplicate build outputs still exist. That is a local artifact hygiene issue,
  not a checked-in source correctness issue.
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

## Related Docs

- [Alpha12 final polish plan](ALPHA12_FINAL_POLISH_PLAN.md)
- [Alpha12 publish decision](ALPHA12_PUBLISH_DECISION.md)
- [Unreal GRILL parity matrix](../UNREAL_GRILL_PARITY.md)
- [Unreal Fab asset worklist](../UNREAL_FAB_ASSET_WORKLIST.md)
