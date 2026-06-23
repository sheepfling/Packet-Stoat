# FastDIS Symbols

FastDIS Symbols is a sibling extension package for tactical symbology. It maps
DIS/SISO entity identity metadata into a renderer-neutral symbol descriptor and
optional MIL-STD-2525/App-6 SIDC policy outputs.

This is not part of the FastDIS core package. The dependency direction is:

```text
fastdis-symbols -> fastdis
fastdis         -> no symbols dependency
```

## Scope

FastDIS core answers: what DIS traffic was received and what stable protocol
fields can be exposed quickly.

FastDIS Symbols answers: given DIS/SISO entity metadata, what tactical symbol
should a map or engine draw.

The extension owns:

- DIS entity type tuple to symbol descriptor rules.
- Force ID to affiliation policy.
- MIL-STD-2525/App-6 SIDC mapping policy.
- Symbol descriptor schemas and golden mapping cases.
- Optional atlas lookup and renderer/baker tooling.

The extension must not require renderer dependencies in the core runtime. Node,
Java, SVG/PNG baking, texture atlases, and engine-specific display wrappers stay
in this extension or downstream packages.

## Proposed Runtime Flow

```text
DIS packet burst
  -> fastdis scanner
  -> Entity State prefix / entity identity
  -> fastdis-symbols resolver
  -> SymbolDescriptor / SIDC + renderer modifiers
  -> atlas lookup or engine renderer
```

Do not feed only compact transform records into this package. Transform records
are enough for placement, but symbology needs `entity_type`,
`alternate_entity_type`, `marking`, and appearance/capability identity fields.

## Files

- [Symbol descriptor schema](spec/symbol_descriptor.schema.json)
- [Symbol handoff schema](spec/symbol_handoff.schema.json)
- [SIDC schema](spec/sidc.schema.json)
- [DIS-to-symbol rules](spec/dis_to_2525_rules.json)
- [Affiliation policy](spec/affiliation_policy.json)
- [Golden cases](spec/golden_cases.jsonl)
- [C ABI boundary header](include/fastdis_symbols/fastdis_symbols.h)

See [FastDIS Symbols Extension](../../docs/FASTDIS_SYMBOLS.md) for the repo
boundary and release plan.
