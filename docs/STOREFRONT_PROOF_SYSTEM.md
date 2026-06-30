# Storefront Proof System

This page defines the reusable proof-panel system for FastDIS storefront and
release visuals.

The purpose is consistency:

- Unreal
- Unity
- Godot

should all use the same composition language for positive and negative proof.

## Why This Exists

FastDIS already has proof artifacts that are stronger than generic marketing
copy:

- orientation verification
- live UDP and replay evidence
- benchmark coverage and contract reports
- package/runtime workflow proof
- known-bad fixtures and blocked-lane evidence

If each engine gets a different layout, the result is harder to compare and
harder to trust. The storefront system should make the engines feel like one
verified family.

## Two Panel Types

### 1. Positive Proof Grid

Use one engine card per engine with the same three rows:

1. Orientation / basis proof
2. Ingest / replay / filtering proof
3. Package / runtime / adapter proof

Suggested evidence sources:

- `artifacts/reports/engine_orientation_summary/<engine>/`
- `artifacts/reports/network_ingest_matrix/`
- `artifacts/reports/core_cross_platform_harness/`
- engine workflow or package reports

### 2. Proof Polarity Panel

Use this when the story needs both:

- what is proven
- what is intentionally bounded, blocked, or known-bad

Left side:

- positive proof
- current safe claim

Right side:

- negative proof or bounded evidence
- explicit non-claim or blocker reason

This is the right format for:

- known-bad orientation fixtures
- blocked GRILL capture lanes
- partial product surfaces
- pending runtime packaging

## Shared Visual Grammar

Every engine should use the same:

- title style
- badge colors
- tile sizes
- proof-row order
- terminology

Recommended proof-row order:

1. Orientation verified
2. Live/replay/filtering verified
3. Adapter/runtime/package verified

Recommended badge meanings:

- green: `proven`
- amber: `bounded`
- red: `known bad`

## Text Discipline

Allowed positive language:

- `verified`
- `proof-backed`
- `bounded`
- `known bad`
- `pending`
- `not a claim`

Avoid vague marketplace language like:

- `best`
- `perfect`
- `fully complete`
- `beats everything`

unless a specific verified artifact supports it.

## Composition Rules

- Do not use raw terminal or markdown screenshots as the lead visual.
- Prefer rendered engine images, matrix summaries, and short proof captions.
- Keep each proof tile to one claim.
- Keep negative proof explicit instead of hiding it.
- When a lane is blocked, say why.

## Current Source Assets

- [Cross-engine positive proof grid](../media/storefront/fab/08_cross_engine_proof_grid_1920x1080.svg)
- [Positive / negative proof panel](../media/storefront/fab/09_proof_polarity_panel_1920x1080.svg)

These are source templates. They should be duplicated or edited per storefront
campaign, while preserving the same visual grammar.

## Current Derived Engine Cards

Current concrete examples built from the shared system:

- [Unreal proof card](../media/storefront/fab/10_unreal_proof_card_1920x1080.svg)
- [Unity bounded proof card](../media/storefront/fab/11_unity_bounded_proof_card_1920x1080.svg)
- [Godot proof card](../media/storefront/fab/12_godot_proof_card_1920x1080.svg)

These are not just mockups. They are intended to mirror the current evidence
state:

- Unreal: positive source/package/runtime shell proof
- Unity: mixed-status runtime proof with explicit bounded gaps
- Godot: positive orientation + ingest/filtering/replay + adapter proof
