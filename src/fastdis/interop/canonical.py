from __future__ import annotations

import json
import math
import struct
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable

from fastdis._fallback import parse_header as parse_header_tuple
from fastdis.tools._shared import EntityStateSpec, make_entity_state_packet


FASTDIS_PROTOCOL_VERSION_DIS7 = 7
EntityTypeTuple = tuple[int, int, int, int, int, int, int]
Vec3Tuple = tuple[float, float, float]


@dataclass(frozen=True)
class CanonicalEntityId:
    site: int
    application: int
    entity: int


@dataclass(frozen=True)
class CanonicalEntity:
    entity_id: CanonicalEntityId
    source: str = "mock-lattice"
    exercise_id: int = 1
    force_id: int = 0
    marking: str = "FASTDIS"
    entity_type: tuple[int, int, int, int, int, int, int] = (1, 2, 840, 3, 4, 5, 6)
    alternate_entity_type: tuple[int, int, int, int, int, int, int] = (1, 2, 840, 3, 4, 5, 6)
    timestamp: int = 0x10000000
    location_ecef_m: tuple[float, float, float] = (0.0, 0.0, 0.0)
    orientation_dis_deg: tuple[float, float, float] = (0.0, 0.0, 0.0)
    velocity_mps: tuple[float, float, float] = (0.0, 0.0, 0.0)
    appearance: int = 0
    stale: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def key(self) -> str:
        return f"{self.entity_id.site}:{self.entity_id.application}:{self.entity_id.entity}"


def entity_type_tuple(values: Iterable[Any]) -> EntityTypeTuple:
    items = tuple(int(value) for value in values)
    if len(items) != 7:
        raise ValueError("entity type must have 7 components")
    return (items[0], items[1], items[2], items[3], items[4], items[5], items[6])


def vec3_tuple(values: Iterable[Any]) -> Vec3Tuple:
    items = tuple(float(value) for value in values)
    if len(items) != 3:
        raise ValueError("vector values must have 3 components")
    return (items[0], items[1], items[2])


def canonical_entity_from_dict(payload: dict[str, Any]) -> CanonicalEntity:
    entity_id_payload = payload["entity_id"]
    entity_type = entity_type_tuple(payload.get("entity_type", (1, 2, 840, 3, 4, 5, 6)))
    return CanonicalEntity(
        entity_id=CanonicalEntityId(
            site=int(entity_id_payload["site"]),
            application=int(entity_id_payload["application"]),
            entity=int(entity_id_payload["entity"]),
        ),
        source=str(payload.get("source", "mock-lattice")),
        exercise_id=int(payload.get("exercise_id", 1)),
        force_id=int(payload.get("force_id", 0)),
        marking=str(payload.get("marking", "FASTDIS")),
        entity_type=entity_type,
        alternate_entity_type=entity_type_tuple(payload.get("alternate_entity_type", entity_type)),
        timestamp=int(payload.get("timestamp", 0x10000000)),
        location_ecef_m=vec3_tuple(payload.get("location_ecef_m", (0.0, 0.0, 0.0))),
        orientation_dis_deg=vec3_tuple(payload.get("orientation_dis_deg", (0.0, 0.0, 0.0))),
        velocity_mps=vec3_tuple(payload.get("velocity_mps", (0.0, 0.0, 0.0))),
        appearance=int(payload.get("appearance", 0)),
        stale=bool(payload.get("stale", False)),
        metadata=dict(payload.get("metadata", {})),
    )


def canonical_entity_to_dict(entity: CanonicalEntity) -> dict[str, Any]:
    payload = asdict(entity)
    payload["entity_id"] = asdict(entity.entity_id)
    return payload


def canonical_entity_to_entity_state_spec(entity: CanonicalEntity) -> EntityStateSpec:
    return EntityStateSpec(
        site=entity.entity_id.site,
        application=entity.entity_id.application,
        entity=entity.entity_id.entity,
        force_id=entity.force_id,
        exercise_id=entity.exercise_id,
        marking=entity.marking,
        entity_type=entity.entity_type,
        alternate_entity_type=entity.alternate_entity_type,
        velocity_mps=entity.velocity_mps,
        location_ecef_m=entity.location_ecef_m,
        orientation_dis_deg=entity.orientation_dis_deg,
        appearance=entity.appearance,
        timestamp=entity.timestamp,
    )


def canonical_entity_to_entity_state_packet(entity: CanonicalEntity) -> bytes:
    return make_entity_state_packet(canonical_entity_to_entity_state_spec(entity))


def canonical_entity_from_entity_state_packet(
    packet: bytes | bytearray | memoryview,
    *,
    source: str = "dis-ingress",
    metadata: dict[str, Any] | None = None,
) -> CanonicalEntity:
    parsed = parse_header_tuple(packet, strict=True)
    if parsed is None:
        raise ValueError("could not parse DIS header")
    version, exercise_id, pdu_type, protocol_family, timestamp, length, _status, _padding = parsed
    if pdu_type != 1 or protocol_family != 1:
        raise ValueError("packet is not a DIS Entity State PDU")
    if version < FASTDIS_PROTOCOL_VERSION_DIS7:
        raise ValueError("only DIS 7 Entity State replay fallback is currently supported")
    if length < 144:
        raise ValueError("Entity State PDU is shorter than the fixed 144-byte layout")

    data = memoryview(packet)[:length].cast("B")
    base = 12
    site, application, entity = struct.unpack_from(">HHH", data, base + 0)
    force_id = int(data[base + 6])
    entity_type = struct.unpack_from(">BBHBBBB", data, base + 8)
    alternate_entity_type = struct.unpack_from(">BBHBBBB", data, base + 16)
    velocity = struct.unpack_from(">fff", data, base + 24)
    location = struct.unpack_from(">ddd", data, base + 36)
    orientation_rad = struct.unpack_from(">fff", data, base + 60)
    appearance = int.from_bytes(bytes(data[base + 72 : base + 76]), "big")
    dead_reckoning_algorithm = int(data[base + 76])
    dead_reckoning_parameters = list(bytes(data[base + 77 : base + 92]))
    dead_reckoning_linear_acceleration = struct.unpack_from(">fff", data, base + 92)
    dead_reckoning_angular_velocity = struct.unpack_from(">fff", data, base + 104)
    marking_bytes = bytes(data[base + 117 : base + 128]).split(b"\x00", 1)[0]
    marking = marking_bytes.decode("ascii", errors="replace") or "DIS"
    merged_metadata = dict(metadata or {})
    merged_metadata.setdefault(
        "dead_reckoning",
        {
            "algorithm": dead_reckoning_algorithm,
            "parameters": dead_reckoning_parameters,
            "linear_acceleration_mps2": list(vec3_tuple(dead_reckoning_linear_acceleration)),
            "angular_velocity_rps": list(vec3_tuple(dead_reckoning_angular_velocity)),
            "extrapolated": False,
        },
    )

    return CanonicalEntity(
        entity_id=CanonicalEntityId(site=site, application=application, entity=entity),
        source=source,
        exercise_id=int(exercise_id),
        force_id=force_id,
        marking=marking,
        entity_type=entity_type_tuple(entity_type),
        alternate_entity_type=entity_type_tuple(alternate_entity_type),
        timestamp=int(timestamp),
        location_ecef_m=vec3_tuple(location),
        orientation_dis_deg=vec3_tuple(math.degrees(float(value)) for value in orientation_rad),
        velocity_mps=vec3_tuple(velocity),
        appearance=appearance,
        metadata=merged_metadata,
    )


def canonical_entity_from_transform(
    transform,
    *,
    source: str = "dis-ingress",
    metadata: dict[str, Any] | None = None,
) -> CanonicalEntity:
    entity_id = CanonicalEntityId(
        site=int(transform.entity_id[0]),
        application=int(transform.entity_id[1]),
        entity=int(transform.entity_id[2]),
    )
    return CanonicalEntity(
        entity_id=entity_id,
        source=source,
        exercise_id=int(transform.exercise_id),
        force_id=int(transform.force_id),
        marking=f"DIS-{entity_id.site}-{entity_id.application}-{entity_id.entity}",
        timestamp=int(transform.timestamp),
        location_ecef_m=vec3_tuple(transform.location),
        orientation_dis_deg=vec3_tuple(math.degrees(float(value)) for value in transform.orientation),
        velocity_mps=vec3_tuple(transform.linear_velocity),
        appearance=int(transform.appearance),
        metadata=dict(metadata or {}),
    )


def canonical_entity_from_snapshot(
    snapshot,
    *,
    source: str = "dis-ingress",
    metadata: dict[str, Any] | None = None,
) -> CanonicalEntity:
    combined_metadata = {
        "first_seen_tick": int(snapshot.first_seen_tick),
        "last_seen_tick": int(snapshot.last_seen_tick),
        "update_count": int(snapshot.update_count),
        "change_flags": int(snapshot.change_flags),
    }
    if metadata:
        combined_metadata.update(metadata)
    return canonical_entity_from_transform(snapshot.transform, source=source, metadata=combined_metadata)


def load_canonical_entities(path: Path) -> list[CanonicalEntity]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        rows = payload.get("entities", [])
    else:
        rows = payload
    return [canonical_entity_from_dict(dict(row)) for row in rows]


__all__ = [
    "CanonicalEntity",
    "CanonicalEntityId",
    "canonical_entity_from_dict",
    "canonical_entity_from_entity_state_packet",
    "canonical_entity_from_snapshot",
    "canonical_entity_from_transform",
    "canonical_entity_to_dict",
    "canonical_entity_to_entity_state_packet",
    "canonical_entity_to_entity_state_spec",
    "entity_type_tuple",
    "load_canonical_entities",
    "vec3_tuple",
]
