from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastdis.interop import CanonicalEntity, canonical_entity_from_dict, canonical_entity_to_dict


def canonical_entity_from_fixture(path: Path) -> list[CanonicalEntity]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        rows = payload
    elif isinstance(payload, dict) and "entities" in payload:
        rows = payload["entities"]
    else:
        rows = [payload]
    return [canonical_entity_from_dict(dict(row)) for row in rows]


def canonical_entity_to_fixture(entities: list[CanonicalEntity], path: Path) -> None:
    payload = {"entities": [canonical_entity_to_dict(entity) for entity in entities]}
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def canonical_entity_from_fastdis(payload: dict[str, Any]) -> CanonicalEntity:
    return canonical_entity_from_dict(payload)
