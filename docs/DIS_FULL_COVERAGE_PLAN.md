# DIS 6/7 Full Coverage Plan

FastDIS should move from hand-authored parser growth to a generated coverage
pipeline.

The backlog owner for this work is
[Epic 2: Full DIS 6/7 PDU Feature Buildout](PRODUCT_BACKLOG.md#epic-2-full-dis-67-pdu-feature-buildout).
Use [Epic 2 full DIS buildout](EPIC2_FULL_DIS_BUILDOUT.md) for the active
milestone exits and proof commands.
Use [Epic 2 milestones](EPIC2_MILESTONES.md) for the generated milestone blurbs
and current completion rollup.

```text
DIS catalog
  -> normalized IR
  -> safe parser / serializer / visitor generation
  -> fuzz and golden fixtures
  -> endpoint behavior manifest
  -> Python / C / C++ / Unreal / Godot / Unity / Lattice Lab outputs
```

## Coverage Types

Full wire coverage:

Every PDU is known, header-validated, length-checked, safely parsed or skipped,
serializable where the IR supports it, fuzzed, and visible.

Full product coverage:

Every PDU has defined behavior in Python, Unreal, Godot, Unity, and Lattice
Lab. Generic behavior is acceptable; missing behavior is not.

Full semantic coverage:

Every field of every PDU has a typed parser, serializer, round-trip tests, fuzz
coverage, and reference validation.

Alpha/Beta should target full wire coverage and full product coverage first.
Full semantic coverage can grow by PDU wave.

## Support Levels

```text
0 Unknown
1 Cataloged
2 HeaderValidated
3 MinLengthValidated
4 FieldVisited
5 TypedPrefixParsed
6 FullParsed
7 Serializable
8 EndpointMapped
9 DifferentiallyVerified
10 ProductionSupported
```

Baseline target for known DIS 6/7 PDUs:

- cataloged
- header-validated
- generic packet-view parsed
- generic field/body visited
- byte-preserving serialized
- parse/serialize roundtrip-tested
- shallow-fuzzed
- visible through every product endpoint
- safely skipped or field-visited when typed parsing is not available

## Generic Field Visitor

The generated field visitor is the coverage bridge between raw packet visibility
and full semantic parsing.

Target C ABI:

```c
typedef struct fastdis_field_view_s {
    uint32_t field_id;
    const char* name;
    uint32_t type;
    uint32_t offset;
    uint32_t size;
    uint32_t element_count;
    uint32_t flags;
} fastdis_field_view_t;

typedef int (*fastdis_field_callback_t)(
    const fastdis_field_view_t* field,
    const uint8_t* packet,
    size_t packet_size,
    void* user);

fastdis_status_t fastdis_visit_pdu_fields(
    const uint8_t* data,
    size_t size,
    fastdis_field_callback_t callback,
    void* user);
```

Python now has this generic coverage through generated message views:

- `fastdis.parse_pdu(packet)`
- `fastdis.visit_pdu_fields(packet)`
- `fastdis.serialize_pdu(view)`
- `fastdis.roundtrip_packet(packet)`

Endpoint behavior can then be generic before it is typed:

- Python: `visit_fields(packet)` / `to_dict(packet)`
- Unreal: `OnFastDisPduReceived`
- Godot: `pdu_received`
- Unity: generic monitor event once the adapter is runnable
- Lattice Lab: `SimulationPduObservation`

## Product Endpoint Rules

Every generated catalog row must have behavior for:

- Python
- Unreal
- Godot
- Lattice Lab

Unity joins this gate once its adapter moves from scaffold to runnable preview.

Behavior levels:

```text
none
generic_raw_event
generic_field_event
typed_event
state_update
lattice_entity_mapping
lattice_task_mapping
lattice_object_mapping
engine_actor_mapping
engine_visual_effect
```

`none` is not acceptable for known PDUs.

## PDU Waves

Wave 1: production state behavior

- Entity State
- Entity State Update
- Remove Entity
- Create Entity

Wave 2: event and visual-effect behavior

- Fire
- Detonation
- Collision
- Collision-Elastic
- LE Fire
- LE Detonation
- Directed Energy Fire
- Entity Damage Status

Wave 3: radio, sensor, and EW behavior

- Electromagnetic Emission
- Designator
- Transmitter
- Signal
- Receiver
- IFF
- Underwater Acoustic
- Supplemental Emission / Entity State
- Intercom Signal
- Intercom Control

Wave 4: simulation management

- Start/Resume
- Stop/Freeze
- Acknowledge
- Action Request
- Action Response
- Data Query
- Set Data
- Data
- Event Report
- Comment
- reliable variants

Wave 5: logistics, minefield, synthetic environment, aggregate, relationship,
and information-operations PDUs

These start as generic field events and become typed only when product use
justifies it.

## Generated Outputs

Current and planned generated files:

- `generated/message_coverage_manifest.json`
- `generated/message_views_manifest.json`
- `generated/version_translation_manifest.json`
- `generated/endpoint_mapping_manifest.json`
- `docs/MESSAGE_COVERAGE.md`
- `docs/GENERATED_MESSAGE_VIEWS.md`
- `docs/DIS_VERSION_TRANSLATION.md`
- `docs/DIS6_DIS7_TRANSLATION_MATRIX.md`
- `docs/ENDPOINT_COVERAGE.md`
- `generated/fastdis_ir_dis6.json`
- `generated/fastdis_ir_dis7.json`

Freshness command:

```bash
python tools/check_generated_fresh.py
```

Endpoint generation:

```bash
python tools/generate_endpoint_mapping_manifest.py
```

Message-view generation:

```bash
python tools/generate_message_views.py
```

DIS 6/7 translation-rule generation:

```bash
python tools/generate_version_translation_manifest.py
```

## CI Gates

1. Every DIS 6 PDU value represented by upstream catalog data has a row.
2. Every DIS 7 PDU value represented by upstream catalog data has a row.
3. Every catalog row has Python behavior.
4. Every catalog row has Unreal behavior.
5. Every catalog row has Godot behavior.
6. Every catalog row has Lattice Lab behavior.
7. Every catalog row has shallow fuzz coverage.
8. Every catalog row has a generated generic parser, visitor, serializer, and
   packet-view roundtrip test.
9. Every catalog row has a DIS 6 -> DIS 7 or DIS 7 -> DIS 6 translation
   rule with explicit strict/tolerant/preserve-raw behavior.
10. Every typed semantic parser has deep fuzz and semantic round-trip tests.
11. `docs/MESSAGE_COVERAGE.md`, `docs/GENERATED_MESSAGE_VIEWS.md`,
    `docs/DIS_VERSION_TRANSLATION.md`, `docs/DIS6_DIS7_TRANSLATION_MATRIX.md`,
    and `docs/ENDPOINT_COVERAGE.md` are fresh.

## Done Definitions

Catalog done:

DIS 6/7 known PDU rows are represented, name differences and aliases are
captured, and coverage manifests regenerate cleanly.

Safe-ingest done:

Every known or unknown PDU can be received, header-validated, length-checked,
counted, fuzzed, and safely skipped or visited.

Endpoint done:

Every known PDU has Python, Unreal, Godot, and Lattice Lab behavior. Generic
behavior is acceptable. Missing behavior is not.

Semantic full-parse done:

Every PDU has full field parse, full serialize, round-trip tests, fuzzing, and
differential verification.
