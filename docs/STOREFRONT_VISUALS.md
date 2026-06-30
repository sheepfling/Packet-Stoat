# Storefront Visuals

FastDIS visuals should make the architecture clear without inflating protocol
coverage claims.

The source SVG kit lives in [media/storefront](../media/storefront/README.md).
Marketplace PNG/JPEG exports should be generated under `artifacts/` and kept
out of source control unless a specific rendered asset is promoted
intentionally.

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
| [08 cross-engine proof grid](../media/storefront/fab/08_cross_engine_proof_grid_1920x1080.svg) | shared engine proof collage | Unreal, Unity, and Godot can be presented with the same positive-proof card structure. |
| [09 proof polarity panel](../media/storefront/fab/09_proof_polarity_panel_1920x1080.svg) | honest proof storytelling | Positive and negative evidence can be shown with the same visual grammar instead of hiding bounded failures. |
| [10 Unreal proof card](../media/storefront/fab/10_unreal_proof_card_1920x1080.svg) | derived storefront example | Unreal positive proof card using the shared cross-engine composition system. |
| [11 Unity bounded proof card](../media/storefront/fab/11_unity_bounded_proof_card_1920x1080.svg) | derived storefront example | Unity mixed-status card showing proven sub-lanes and bounded runtime gaps without over-claiming. |
| [12 Godot proof card](../media/storefront/fab/12_godot_proof_card_1920x1080.svg) | derived storefront example | Godot positive proof card using orientation, ingest, filtering, replay, and adapter workflow evidence. |
| `build/storefront/benchmark_charts/measured_throughput_by_surface_1920x1080.png` | measured performance hero | Best measured `packets/sec` row by surface, omitting surfaces without audited throughput metrics. |
| `build/storefront/benchmark_charts/benchmark_coverage_by_surface_1920x1080.png` | proof maturity chart | Surface row counts, runtime-metric rows, and truth rows from the shared benchmark matrix. |
| `build/storefront/benchmark_charts/unity_vs_grill_same_host_1920x1080.png` | competitor proof card | Same-host Unity FastDIS-vs-GRILL comparison using only comparable audited metrics. |

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
- `08_cross_engine_proof_grid_1920x1080.svg`
- `09_proof_polarity_panel_1920x1080.svg`
- `10_unreal_proof_card_1920x1080.svg`
- `11_unity_bounded_proof_card_1920x1080.svg`
- `12_godot_proof_card_1920x1080.svg`

Export target for Fab: `1920x1080` PNG or JPEG under the marketplace file-size
limits.

Unity and Godot marketplace-specific icon/card exports should be generated from
this source kit or a later dedicated icon source, then staged under
`artifacts/`.

Benchmark storefront charts are generated from audited report JSON, not
hand-entered numbers:

```bash
python tools/render_benchmark_storefront_charts.py
```

Outputs land under:

- `artifacts/storefront/benchmark_charts/`

The renderer intentionally follows the benchmark claim boundaries:

- throughput charts include only surfaces with real measured `packets/sec`
- coverage charts express proof maturity, not speed
- competitor charts require same-host comparable metrics and should remain
  omitted or explicitly blocked when that evidence lane is unavailable

## Cross-Engine Proof Rules

When composing Unreal, Unity, and Godot into the same visual family:

- keep the card geometry identical across engines
- use the same three proof buckets:
  - orientation / basis proof
  - ingest / replay / filtering proof
  - packaging / runtime / adapter proof
- use the same badge meanings:
  - green: proven
  - amber: bounded / pending / partial
  - red: known-bad / intentionally failing negative fixture
- do not turn a blocked competitor lane into a generic red X without text
- always label the reason for a negative tile:
  - `known bad fixture`
  - `blocked on competitor host`
  - `pending product surface`
  - `not a claim`

The goal is not just attractive collage work. The goal is a reusable proof
language that stays consistent across engines and survives audit.
