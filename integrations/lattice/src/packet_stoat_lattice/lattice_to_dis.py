from __future__ import annotations

import json
from pathlib import Path

from fastdis.lattice import (
    canonical_entity_from_dict,
    canonical_entity_from_lattice_payload,
    canonical_entity_to_entity_state_packet,
)


def entity_state_packet_from_track_payload(payload: dict[str, object]) -> bytes:
    return canonical_entity_to_entity_state_packet(canonical_entity_from_lattice_payload(payload))


def entity_state_packet_from_fixture(path: Path) -> bytes:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if "schema" in payload:
        return entity_state_packet_from_track_payload(payload)
    entities = payload.get("entities")
    if entities:
        return canonical_entity_to_entity_state_packet(canonical_entity_from_dict(dict(entities[0])))
    return canonical_entity_to_entity_state_packet(canonical_entity_from_dict(payload))
