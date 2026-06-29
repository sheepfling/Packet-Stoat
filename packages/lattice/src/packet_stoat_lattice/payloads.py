from __future__ import annotations

from fastdis.interop import CanonicalEntity
from fastdis.lattice import canonical_entity_to_lattice_payload

from .entity_mapping import map_force_disposition, map_platform_kind


def lattice_track_payload_from_entity(entity: CanonicalEntity) -> dict[str, object]:
    payload = canonical_entity_to_lattice_payload(entity)
    payload["track"] = {
        "platform_kind": map_platform_kind(entity),
        "disposition": map_force_disposition(entity.force_id),
    }
    return payload
