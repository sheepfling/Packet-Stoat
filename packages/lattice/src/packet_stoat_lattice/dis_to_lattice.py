from __future__ import annotations

from pathlib import Path

from fastdis.interop import CanonicalEntity

from .canonical import canonical_entity_from_fixture
from .payloads import lattice_track_payload_from_entity


def build_publish_report(entities: list[CanonicalEntity], publisher) -> dict[str, object]:
    results = []
    accepted = 0
    for entity in entities:
        payload = lattice_track_payload_from_entity(entity)
        result = publisher.publish_entity(payload)
        results.append(result)
        if result.get("status") == "accepted":
            accepted += 1
    return {
        "attempted": len(entities),
        "accepted": accepted,
        "results": results,
    }


def publish_fixture(path: Path, publisher) -> dict[str, object]:
    return build_publish_report(canonical_entity_from_fixture(path), publisher)
