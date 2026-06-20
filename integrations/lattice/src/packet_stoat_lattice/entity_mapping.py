from __future__ import annotations

from fastdis.lattice import CanonicalEntity


FORCE_DISPOSITION = {
    0: "unknown",
    1: "friendly",
    2: "opposing",
    3: "neutral",
}

PLATFORM_KIND_BY_ENTITY_TYPE = {
    (1, 2, 840, 1, 2, 3, 4): "aircraft",
    (1, 2, 840, 1, 2, 3, 5): "ground_vehicle",
}


def map_force_disposition(force_id: int) -> str:
    return FORCE_DISPOSITION.get(int(force_id), "unknown")


def map_platform_kind(entity: CanonicalEntity) -> str:
    return PLATFORM_KIND_BY_ENTITY_TYPE.get(tuple(entity.entity_type), "generic")
