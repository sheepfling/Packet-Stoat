# Alpha12 Publish Decision

Version lane: `fastdis v0.17.0-alpha12`
Branch lane: `alpha5/v0.15`

## Decision

`publish_with_caveats`

FastDIS now has the local proof needed for an honest Unreal/Fab alpha candidate.
The remaining caveats are about semantic depth and external publication steps,
not missing local product proof for the current claim set.

## What Is Proven Now

- Version-clean packaging:
  - `pyproject.toml`, `src/fastdis/__init__.py`, and
    `packages/unreal/FastDis/FastDis.uplugin` are aligned on
    `0.17.0-alpha12`.
  - Unreal plugin metadata keeps `IsBetaVersion=true` intentionally for this
    alpha publication lane.
- Fab readiness gate:
  - `python tools/check_unreal_fab_readiness.py --strict`
  - expected local result: `overall_status: fab_ready`
- Packaged plugin install proof:
  - `python tools/build_unreal_plugin.py --engine-version 5.8 --clean-package`
  - `python tools/run_unreal_packaged_install_smoke.py --engine-version 5.8 --clean-project`
  - current receipts: `build/reports/unreal_fab_readiness.md`,
    `build/reports/unreal_packaged_install_smoke.md`
- Unreal product surface:
  - live UDP receive/send
  - replay ingest
  - Entity State and Entity State Update snapshot handling
  - first-seen auto-spawn plus Remove Entity policy
  - Blueprint PDU event surfaces
  - runtime monitor and status widget base
- Honest semantic depth split:
  - [Unreal GRILL parity matrix](../UNREAL_GRILL_PARITY.md) distinguishes
    native snapshot paths from `decoded typed summary + raw sidecar` rows.

## Required Caveats In Listing Or Release Notes

- The GRILL parity PDU set is surfaced in Unreal, but several rows still expose
  compact typed summaries rather than full gameplay-ready semantic models.
- FastDIS does not claim full semantic body decoding for every DIS 6/7 PDU.
- The Unreal plugin descriptor intentionally remains marked beta for this
  submission lane because the package is still alpha and marketplace proof is
  local rather than externally published.
- Debug markers for Fire, Detonation, and Designator prove surfaced events, not
  full production VFX systems.
- The optional georeference adapter is reflection-based; it avoids hard Unreal
  Georeferencing or Cesium dependencies rather than claiming deep typed
  integrations.
- Fab approval, marketplace review, signed release hosting, and external
  account steps remain release operations outside the repository proof.

## Publish-Now Check

Local publish blockers:

- none currently proven

External or operational dependencies:

- Fab review and listing submission
- release artifact upload and release-note publication
- screenshot/media final selection for storefront use

## Holdbacks For The Next Tranche

Keep these out of the alpha12 product claim:

- richer semantic body models for Start/Resume, Stop/Freeze,
  Electromagnetic Emission, Signal, and Designator
- optional hard integrations for Unreal Georeferencing or Cesium
- broader post-Fab differentiators beyond the current Unreal product lane

## Related Docs

- [Alpha12 final polish plan](ALPHA12_FINAL_POLISH_PLAN.md)
- [Alpha12 closeout audit](ALPHA12_CLOSEOUT_AUDIT.md)
- [Product backlog](../PRODUCT_BACKLOG.md)
- [Unreal GRILL parity matrix](../UNREAL_GRILL_PARITY.md)
- [Unreal Fab asset worklist](../UNREAL_FAB_ASSET_WORKLIST.md)
