# Storefront Visuals

FastDIS visuals should make the architecture clear without inflating protocol
coverage claims.

The source SVG kit lives in [media/storefront](../media/storefront/README.md).
Marketplace PNG/JPEG exports should be generated under `build/` and kept out of
source control unless a specific rendered asset is promoted intentionally.

## Visual Set

| Asset | Use | Claim |
| --- | --- | --- |
| [01 hero](../media/storefront/fab/01_hero_1920x1080.svg) | storefront lead image | FastDIS turns packet bursts into engine-ready state. |
| [02 pipeline](../media/storefront/fab/02_pipeline_1920x1080.svg) | README/release pipeline | UDP/replay bytes flow through scanner, Entity State fast path, entity table, snapshots, and adapters. |
| [03 coverage ladder](../media/storefront/fab/03_coverage_ladder_1920x1080.svg) | technical credibility | PDU catalog/filter/count coverage is distinct from body decoder and engine snapshot support. |
| [04 symbols handoff](../media/storefront/fab/04_symbols_handoff_1920x1080.svg) | symbols extension/proof | Entity State identity can flow through a sibling proof harness into `milsymbol` SVG output. |
| [05 C ABI portability](../media/storefront/fab/05_cabi_portability_1920x1080.svg) | cross-host positioning | One C ABI core supports thin host adapters. |
| [06 core/plugin boundary](../media/storefront/fab/06_core_plugin_boundary_1920x1080.svg) | adapter/product docs | FastDIS core owns packets and snapshots; plugins own visuals, transports, and vendor semantics. |
| [07 Unreal GRILL parity](../media/storefront/fab/07_unreal_grill_parity_1920x1080.svg) | Unreal Fab draft | Unreal plugin surface includes live UDP, auto-spawn, typed event summaries, demo controller, monitor widget base, georeference adapter, and package verification. |

## Required Message Discipline

Use this phrase consistently:

> Boring core. Useful adapters. Honest coverage.

Do not claim:

- all DIS PDU bodies are fully decoded
- FastDIS is a full OpenDIS object-model replacement
- MIL-STD-2525/App-6 rendering lives in core
- the symbols proof is a production symbology library
- every SISO entity type has an official tactical symbol mapping

Do claim:

- broad DIS 6/7 header/catalog/filter/count awareness
- implemented Entity State fast path
- implemented transform/entity-table/snapshot handoff
- sibling tactical-symbol proof/plugin boundary
- renderer dependencies stay out of FastDIS core

## Marketplace Targets

Fab source set:

- `01_hero_1920x1080.svg`
- `02_pipeline_1920x1080.svg`
- `03_coverage_ladder_1920x1080.svg`
- `04_symbols_handoff_1920x1080.svg`
- `05_cabi_portability_1920x1080.svg`
- `06_core_plugin_boundary_1920x1080.svg`
- `07_unreal_grill_parity_1920x1080.svg`

Export target for Fab: `1920x1080` PNG or JPEG under the marketplace file-size
limits.

Unity and Godot marketplace-specific icon/card exports should be generated from
this source kit or a later dedicated icon source, then staged under `build/`.
