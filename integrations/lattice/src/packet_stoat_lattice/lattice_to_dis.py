from __future__ import annotations

import json
from pathlib import Path

from fastdis.lattice import canonical_entity_from_dict, canonical_entity_to_entity_state_packet


def entity_state_packet_from_track_payload(payload: dict[str, object]) -> bytes:
    canonical_payload = {
        "entity_id": {
            "site": int(str(payload["entity_key"]).split(":")[0]),
            "application": int(str(payload["entity_key"]).split(":")[1]),
            "entity": int(str(payload["entity_key"]).split(":")[2]),
        },
        "source": payload.get("source", "mock-lattice"),
        "exercise_id": payload.get("exercise_id", 1),
        "force_id": payload.get("force_id", 0),
        "marking": payload.get("marking", "FASTDIS"),
        "entity_type": payload.get("entity_type", [1, 2, 840, 3, 4, 5, 6]),
        "alternate_entity_type": payload.get("entity_type", [1, 2, 840, 3, 4, 5, 6]),
        "timestamp": payload.get("timestamp", 0x10000000),
        "location_ecef_m": payload.get("pose", {}).get("location_ecef_m", [0.0, 0.0, 0.0]),
        "orientation_dis_deg": [
            payload.get("pose", {}).get("orientation_dis_deg", {}).get("psi", 0.0),
            payload.get("pose", {}).get("orientation_dis_deg", {}).get("theta", 0.0),
            payload.get("pose", {}).get("orientation_dis_deg", {}).get("phi", 0.0),
        ],
        "velocity_mps": payload.get("pose", {}).get("velocity_mps", [0.0, 0.0, 0.0]),
        "metadata": payload.get("metadata", {}),
    }
    return canonical_entity_to_entity_state_packet(canonical_entity_from_dict(canonical_payload))


def entity_state_packet_from_fixture(path: Path) -> bytes:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if "schema" in payload:
        return entity_state_packet_from_track_payload(payload)
    entities = payload.get("entities")
    if entities:
        return canonical_entity_to_entity_state_packet(canonical_entity_from_dict(dict(entities[0])))
    return canonical_entity_to_entity_state_packet(canonical_entity_from_dict(payload))
