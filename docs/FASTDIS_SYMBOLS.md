# FastDIS Symbols Extension

FastDIS Symbols is the planned sibling extension for tactical symbology. It
should remain separate from the FastDIS core because MIL-STD-2525/App-6 mapping
is visualization policy, not DIS wire-format parsing.

## Boundary

FastDIS core owns:

- DIS header parsing and PDU catalog metadata.
- Entity State identity, pose, appearance, marking, and SISO enum exposure.
- Native C ABI, C++ wrapper, Python core wrappers, replay, filtering, and engine
  snapshot handoff.

FastDIS Symbols owns:

- DIS/SISO entity identity to symbol descriptor rules.
- Force ID to tactical affiliation policy.
- MIL-STD-2525/App-6 SIDC mapping policy.
- Symbol descriptor and SIDC schemas.
- Optional SVG/PNG/atlas baking tools.
- Optional Unreal/Godot/Unity tactical-symbol display wrappers.

The dependency direction is strict:

```text
fastdis-symbols -> fastdis
fastdis         -> no fastdis-symbols dependency
```

Do not add MIL-STD-2525 renderer dependencies, symbol fonts, texture atlases,
Node/Java renderers, or SIDC mapping tables to `src/fastdis` or
`include/fastdis`.

## Current Scaffold

The first scaffold lives in [extensions/fastdis-symbols](../extensions/fastdis-symbols/README.md).

The disposable renderer proof harness lives in
[extensions/fastdis-symbols-proof](../extensions/fastdis-symbols-proof/README.md).

It contains:

- Python package metadata for a future separately installable
  `fastdis-symbols` distribution.
- A renderer-neutral `SymbolDescriptor` helper.
- A separate C ABI boundary header under
  `extensions/fastdis-symbols/include/fastdis_symbols/`.
- JSON schemas for symbol descriptors and SIDC policy values.
- Policy scaffolds for Force ID affiliation and DIS entity type fallback.
- Golden mapping cases for future resolver tests.

## Runtime Shape

```text
DIS packet burst
  -> fastdis scanner
  -> fastdis_entity_state_prefix_t or generic entity identity
  -> fastdis-symbols resolver
  -> SymbolDescriptor / SIDC + renderer modifiers
  -> atlas lookup or engine-native renderer
```

Engine runtime packages should not need Python, Node, Java, or live SVG
generation. They should consume the core FastDIS C ABI, the FastDIS Symbols C
ABI, and optional prebuilt atlas assets.

## Handoff Contract

The first handoff contract is deliberately small:

```text
FastDIS entity identity
  force_id
  entity_type
  alternate_entity_type
  marking
  appearance
  capabilities
  location
  orientation
  linear_velocity

FastDIS Symbols output
  SymbolDescriptor
    standard
    sidc
    affiliation
    symbol_set
    entity_type
    label
    confidence
    rule_id
  SymbolModifiers
    unique_designation
    direction_degrees
    quantity
    staff_comments
    status
  position_ecef_m
  atlas_key
```

Do not pass only `fastdis_entity_transform_t` into the symbology layer. The
compact transform output is useful for actor placement, but it omits
`entity_type`, `alternate_entity_type`, `marking`, and `capabilities`, so it
cannot derive a tactical symbol from scratch. Use
`fastdis_entity_state_prefix_t` or a future generic identity snapshot.

## Sufficiency

FastDIS Entity State metadata is enough for useful first-pass point symbols:

- Force ID maps to affiliation by policy.
- Entity type kind/domain/category fields choose a platform symbol family.
- Marking becomes a unique designation modifier.
- Orientation can provide a heading/direction modifier.
- Location places the symbol on a map or engine billboard.

It is not enough by itself for complete order-of-battle symbology, echelon
accuracy, unit hierarchy, control measures, routes, boundaries, phase lines, or
mission graphics. Those need scenario/C2 context outside DIS Entity State.

## Core Addition Policy

A future generic identity record may be added to core if needed:

```text
fastdis_entity_identity_t
  entity_id
  force_id
  entity_type
  alternate_entity_type
  appearance
  marking
  capabilities
```

That record remains DIS-native. It must not contain SIDC fields, MIL-STD-2525
names, renderer state, atlas keys, symbol fonts, or texture handles.

## Release Plan

Keep FastDIS Symbols in this repository until the identity boundary and rule
schemas stabilize. Publish it separately when it becomes useful as its own
artifact:

- `fastdis-symbols-spec`: schemas, rule tables, and golden cases.
- `fastdis-symbols`: Python helpers and resolver tooling.
- `fastdis-symbols-capi`: native ABI for engine runtimes.
- `fastdis-symbols-assets-basic`: optional prebuilt atlas assets.
- engine display wrappers as separate optional packages.
