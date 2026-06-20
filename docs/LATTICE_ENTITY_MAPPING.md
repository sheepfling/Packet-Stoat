# Lattice entity mapping

Alpha 4 maps the existing fastdis Entity State fast path into a higher-level
canonical entity surface that can then be published by a Lattice-style app.

## First mapping focus

Use Entity State PDU and latest-state snapshots first.

```text
DIS Entity State
  -> fastdis_entity_transform_t / fastdis_entity_snapshot_t
  -> canonical entity
  -> Lattice-style Track/Asset payload
```

## Canonical bridge fields

Planned bridge fields include:

- source kind / stable source key
- source timestamp
- DIS site/application/entity ID
- exercise ID
- entity type
- force ID
- marking
- world position
- velocity
- orientation
- appearance
- live/stale/removed state
- provenance metadata

## Outbound mapping guidance

Suggested initial mapping:

| fastdis / DIS | canonical entity | Lattice-style payload |
| --- | --- | --- |
| site/application/entity | `dis_id` | stable entity ID / alias set |
| marking | `marking` | display name / alias |
| force ID | `force_id` | disposition / affiliation |
| entity type | `entity_type` | platform/ontology fields |
| world coordinates | `world_location` | location component |
| velocity | `linear_velocity` | velocity component |
| orientation | `orientation` | attitude/orientation component |
| stale/remove transitions | `lifecycle_state` | liveness / expiry handling |

Alpha 4 should keep this mapping explicit and configurable rather than hiding it
inside one opaque publisher implementation.
