# Storefront Visual Source Kit

These SVG files are source artwork for FastDIS storefronts, README visuals, and
release pages. Export PNG/JPEG marketplace assets under `build/`; do not commit
rendered storefront outputs unless they become deliberate source assets.

## Fab 1920x1080 Source Images

- [Hero: packet burst to engine-ready state](fab/01_hero_1920x1080.svg)
- [Pipeline: core runtime flow](fab/02_pipeline_1920x1080.svg)
- [Truthful coverage ladder](fab/03_coverage_ladder_1920x1080.svg)
- [MIL-STD-2525 handoff proof](fab/04_symbols_handoff_1920x1080.svg)
- [C ABI portability hub](fab/05_cabi_portability_1920x1080.svg)
- [Core/plugin boundary](fab/06_core_plugin_boundary_1920x1080.svg)
- [Unreal runtime parity surface](fab/07_unreal_grill_parity_1920x1080.svg)
- [Cross-engine positive proof grid](fab/08_cross_engine_proof_grid_1920x1080.svg)
- [Positive / negative proof panel system](fab/09_proof_polarity_panel_1920x1080.svg)
- [Unreal proof card](fab/10_unreal_proof_card_1920x1080.svg)
- [Unity bounded proof card](fab/11_unity_bounded_proof_card_1920x1080.svg)
- [Godot proof card](fab/12_godot_proof_card_1920x1080.svg)

## Reusable Proof Composition

The `08_*` and `09_*` sources are intentionally engine-neutral composition
frames rather than one-engine ads.

Use them to present Unreal, Unity, and Godot with the same structure:

- same title block
- same proof rows
- same badge semantics
- same positive vs negative framing

Positive proof slots should come from current generated evidence such as:

- `build/reports/core_cross_platform_harness/`
- `build/reports/benchmark_coverage/`
- `build/reports/network_ingest_matrix/`
- `build/reports/engine_orientation_evidence/`
- `build/reports/engine_orientation_summary/`

Negative proof slots should show bounded, honest failure evidence such as:

- known-bad orientation fixtures
- blocked competitor lanes
- pending package/runtime features
- explicit non-claims

## Message Discipline

- Do not claim all PDU bodies are fully decoded.
- Distinguish catalog/filter/count coverage from body decoder and engine
  snapshot support.
- Present MIL-STD-2525/App-6 display as a sibling proof/plugin lane, not a core
  parser feature.
- Avoid real locations, operational unit names, or realistic mission graphics.
