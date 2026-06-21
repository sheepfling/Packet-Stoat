"""Human-readable JSON envelopes for DIS packets and FastDIS replays."""

from __future__ import annotations

import base64
import hashlib
import math
from typing import Any, Literal, Mapping, cast

from . import parse_header, parse_semantic_pdu
from .interop import canonical_entity_from_entity_state_packet, canonical_entity_to_dict
from .tools._shared import EntityStateSpec, make_entity_state_packet


DecodeLevel = Literal["header", "typed", "semantic"]
RawPolicy = Literal["include", "omit"]

PACKET_SCHEMA = "fastdis.packet.v1"
ENTITY_STATE_SCHEMA = "fastdis.pdu.entity_state.v1"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def _unb64(data: str) -> bytes:
    return base64.b64decode(data.encode("ascii"), validate=True)


def _to_int(value: object) -> int:
    return int(cast(Any, value))


def _to_float(value: object) -> float:
    return float(cast(Any, value))


def _json_safe(value: object) -> object:
    if isinstance(value, bytes):
        return {"encoding": "base64", "data": _b64(value), "size": len(value)}
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    return value


def _header_record(packet: bytes) -> tuple[dict[str, object], list[dict[str, object]]]:
    diagnostics: list[dict[str, object]] = []
    header = parse_header(packet, strict=False)
    if header is None:
        diagnostics.append(
            {
                "code": "HEADER_PARSE_FAILED",
                "severity": "error",
                "message": "Packet is shorter than a valid DIS header or has an invalid declared length.",
            }
        )
        return {}, diagnostics

    if header.length != len(packet):
        diagnostics.append(
            {
                "code": "DECLARED_LENGTH_MISMATCH",
                "severity": "warning",
                "message": "Declared PDU length differs from the supplied packet size.",
                "declared_length": header.length,
                "packet_size": len(packet),
            }
        )

    return (
        {
            "protocol_version": header.version,
            "exercise_id": header.exercise_id,
            "pdu_type": header.pdu_type,
            "protocol_family": header.protocol_family,
            "timestamp": header.timestamp,
            "declared_length": header.length,
            "pdu_status": header.pdu_status,
            "padding": header.padding,
        },
        diagnostics,
    )


def packet_to_json_record(
    packet: bytes | bytearray | memoryview,
    *,
    record_index: int | None = None,
    source_format: str = "binary",
    decode_level: DecodeLevel = "semantic",
    raw_policy: RawPolicy = "include",
) -> dict[str, object]:
    """Convert one raw DIS packet to a JSON-safe FastDIS packet envelope."""

    blob = bytes(packet)
    header, diagnostics = _header_record(blob)
    record: dict[str, object] = {
        "fastdis_schema": PACKET_SCHEMA,
        "source_format": source_format,
        "packet": {
            "size": len(blob),
            "sha256": _sha256(blob),
        },
        "header": header,
        "support": {
            "cataloged": False,
            "safe_ingest": bool(header),
            "field_visitor": False,
            "typed_parser": False,
            "serializer": True,
        },
        "diagnostics": diagnostics,
    }
    if record_index is not None:
        record["record_index"] = record_index
    if raw_policy == "include":
        cast(dict[str, object], record["packet"])["raw_base64"] = _b64(blob)

    if not header or decode_level == "header":
        return record

    semantic = parse_semantic_pdu(blob, strict=False)
    if semantic is None:
        diagnostics.append(
            {
                "code": "SEMANTIC_PARSE_UNAVAILABLE",
                "severity": "warning",
                "message": "No FastDIS semantic parser entry point accepted this packet.",
            }
        )
        return record

    descriptor = semantic.descriptor
    record["support"] = {
        "cataloged": True,
        "safe_ingest": True,
        "field_visitor": bool(descriptor.declared_fields),
        "typed_parser": True,
        "serializer": True,
        "semantic_level": descriptor.semantic_level,
        "fully_domain_decoded": descriptor.fully_domain_decoded,
    }
    header["pdu_name"] = descriptor.standard_name
    header["standard_class_name"] = descriptor.standard_class_name
    header["family_name"] = descriptor.family_name
    header["schema_status"] = descriptor.schema_status
    header["catalog_status"] = descriptor.catalog_status
    diagnostics.extend(
        {"code": "SEMANTIC_DIAGNOSTIC", "severity": "info", "message": message}
        for message in semantic.diagnostics
    )
    if decode_level in {"typed", "semantic"}:
        record["typed"] = {
            "parser_class": semantic.typed.descriptor.parser_class,
            "parse_level": semantic.typed.parse_level,
            "declared_fields": list(semantic.typed.descriptor.declared_fields),
            "fields": _json_safe(semantic.typed.fields),
        }
    if decode_level == "semantic":
        record["semantic"] = {
            "semantic_class": descriptor.semantic_class,
            "semantic_level": descriptor.semantic_level,
            "fields": _json_safe(semantic.semantic_fields),
        }
    return record


def entity_state_packet_to_json(packet: bytes | bytearray | memoryview) -> dict[str, object]:
    """Convert a DIS 7 Entity State PDU into editable FastDIS Entity State JSON."""

    entity = canonical_entity_from_entity_state_packet(packet)
    payload = canonical_entity_to_dict(entity)
    orientation_deg = tuple(float(value) for value in payload["orientation_dis_deg"])
    return {
        "fastdis_schema": ENTITY_STATE_SCHEMA,
        "target_dis_version": 7,
        "header": {
            "protocol_version": 7,
            "exercise_id": payload["exercise_id"],
            "pdu_type": 1,
            "protocol_family": 1,
            "timestamp": payload["timestamp"],
        },
        "entity_state": {
            "entity_id": payload["entity_id"],
            "force_id": payload["force_id"],
            "entity_type": list(payload["entity_type"]),
            "alternate_entity_type": list(payload["alternate_entity_type"]),
            "location_ecef_m": _vec3_dict(payload["location_ecef_m"]),
            "orientation_rad": {
                "psi": math.radians(orientation_deg[0]),
                "theta": math.radians(orientation_deg[1]),
                "phi": math.radians(orientation_deg[2]),
            },
            "linear_velocity_mps": _vec3_dict(payload["velocity_mps"]),
            "appearance": payload["appearance"],
            "marking": payload["marking"],
        },
    }


def _vec3_dict(values: object) -> dict[str, float]:
    x, y, z = (_to_float(item) for item in cast(tuple[object, object, object], tuple(cast(Any, values))))
    return {"x": x, "y": y, "z": z}


def _vec3_from_dict(payload: Mapping[str, object], *, keys: tuple[str, str, str] = ("x", "y", "z")) -> tuple[float, float, float]:
    return (_to_float(payload[keys[0]]), _to_float(payload[keys[1]]), _to_float(payload[keys[2]]))


def _entity_type(values: object) -> tuple[int, int, int, int, int, int, int]:
    items = tuple(_to_int(value) for value in cast(list[object] | tuple[object, ...], values))
    if len(items) != 7:
        raise ValueError("entity_type must contain seven components")
    return (items[0], items[1], items[2], items[3], items[4], items[5], items[6])


def entity_state_packet_from_json(record: Mapping[str, object]) -> bytes:
    """Build a DIS 7 Entity State PDU from editable FastDIS Entity State JSON."""

    entity_state = cast(Mapping[str, object], record["entity_state"])
    entity_id = cast(Mapping[str, object], entity_state["entity_id"])
    header = cast(Mapping[str, object], record.get("header", {}))
    orientation_rad = cast(Mapping[str, object], entity_state.get("orientation_rad", {}))
    location = cast(Mapping[str, object], entity_state["location_ecef_m"])
    velocity = cast(Mapping[str, object], entity_state.get("linear_velocity_mps", {"x": 0.0, "y": 0.0, "z": 0.0}))
    entity_type = _entity_type(entity_state.get("entity_type", [1, 2, 840, 3, 4, 5, 6]))
    alternate_entity_type = _entity_type(entity_state.get("alternate_entity_type", entity_type))
    spec = EntityStateSpec(
        site=_to_int(entity_id["site"]),
        application=_to_int(entity_id["application"]),
        entity=_to_int(entity_id["entity"]),
        force_id=_to_int(entity_state.get("force_id", 0)),
        exercise_id=_to_int(header.get("exercise_id", 1)),
        timestamp=_to_int(header.get("timestamp", 0x10000000)),
        marking=str(entity_state.get("marking", "FASTDIS")),
        entity_type=entity_type,
        alternate_entity_type=alternate_entity_type,
        velocity_mps=_vec3_from_dict(velocity),
        location_ecef_m=_vec3_from_dict(location),
        orientation_dis_deg=(
            math.degrees(_to_float(orientation_rad.get("psi", 0.0))),
            math.degrees(_to_float(orientation_rad.get("theta", 0.0))),
            math.degrees(_to_float(orientation_rad.get("phi", 0.0))),
        ),
        appearance=_to_int(entity_state.get("appearance", 0)),
    )
    return make_entity_state_packet(spec)


def packet_from_json_record(record: Mapping[str, object], *, prefer_raw: bool = True) -> bytes:
    """Rebuild packet bytes from a FastDIS packet or editable PDU JSON record."""

    schema = str(record.get("fastdis_schema", ""))
    packet = cast(Mapping[str, object], record.get("packet", {}))
    raw = packet.get("raw_base64")
    if prefer_raw and isinstance(raw, str):
        blob = _unb64(raw)
        expected_size = packet.get("size")
        if expected_size is not None and len(blob) != _to_int(expected_size):
            raise ValueError("raw_base64 size does not match packet.size")
        expected_sha = packet.get("sha256")
        if expected_sha is not None and _sha256(blob) != str(expected_sha):
            raise ValueError("raw_base64 sha256 does not match packet.sha256")
        return blob
    if schema == ENTITY_STATE_SCHEMA:
        return entity_state_packet_from_json(record)
    raise ValueError("JSON record does not contain raw packet bytes or a supported editable schema")


def packet_summary(record: Mapping[str, object]) -> str:
    """Return a compact human-readable summary for one packet JSON record."""

    header = cast(Mapping[str, object], record.get("header", {}))
    packet = cast(Mapping[str, object], record.get("packet", {}))
    support = cast(Mapping[str, object], record.get("support", {}))
    diagnostics = cast(list[object], record.get("diagnostics", []))
    name = header.get("pdu_name", "unknown")
    return (
        f"DIS v{header.get('protocol_version', '?')} PDU {header.get('pdu_type', '?')} ({name}) "
        f"family={header.get('protocol_family', '?')} length={header.get('declared_length', '?')} "
        f"size={packet.get('size', '?')} sha256={packet.get('sha256', '?')} "
        f"semantic={support.get('semantic_level', 'unavailable')} diagnostics={len(diagnostics)}"
    )
