#!/usr/bin/env python3
"""Generate slotted semantic PDU parser entry points for every DIS 6/7 PDU row."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

from generate_pdu_catalog import DEFAULT_DIS6, DEFAULT_DIS7, ROOT
from generate_typed_pdu_parsers import typed_rows


FULLY_DOMAIN_DECODED_ROWS = {
    (6, 1),
    (6, 2),
    (6, 3),
    (6, 4),
    (6, 13),
    (6, 14),
    (6, 15),
    (6, 16),
    (6, 17),
    (6, 11),
    (6, 12),
    (6, 51),
    (6, 52),
    (6, 53),
    (6, 54),
    (6, 55),
    (6, 56),
    (6, 57),
    (6, 66),
    (6, 67),
    (7, 1),
    (7, 2),
    (7, 3),
    (7, 4),
    (7, 13),
    (7, 14),
    (7, 15),
    (7, 16),
    (7, 17),
    (7, 11),
    (7, 12),
    (7, 51),
    (7, 52),
    (7, 53),
    (7, 54),
    (7, 55),
    (7, 56),
    (7, 57),
    (7, 66),
    (7, 67),
    (7, 68),
    (7, 69),
}


def semantic_rows(dis6: Path, dis7: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in typed_rows(dis6, dis7):
        key = (int(row["protocol_version"]), int(row["pdu_type"]))
        typed_semantic = bool(row["typed_semantic"])
        fully_domain_decoded = key in FULLY_DOMAIN_DECODED_ROWS
        if typed_semantic:
            semantic_level = "semantic_prefix"
        elif fully_domain_decoded:
            semantic_level = "semantic_decoded"
        else:
            semantic_level = "semantic_observation"
        semantic_class = str(row["parser_class"]).replace("Pdu", "SemanticPdu")
        if semantic_class == row["parser_class"]:
            semantic_class = f"{row['parser_class']}Semantic"
        rows.append(
            {
                **row,
                "semantic_class": semantic_class,
                "semantic_parser": True,
                "semantic_level": semantic_level,
                "fully_domain_decoded": fully_domain_decoded,
                "diagnostic_policy": (
                    "domain_prefix_available"
                    if typed_semantic
                    else "decoded_fixed_fields_available"
                    if fully_domain_decoded
                    else "typed observation preserves raw body and exposes schema/field metadata"
                ),
            }
        )
    return rows


def _descriptor_literal(row: dict[str, Any]) -> str:
    return (
        "    SemanticPduDescriptor("
        f"{row['protocol_version']}, {row['pdu_type']}, {row['protocol_family']}, "
        f"{row['standard_name']!r}, {row['standard_class_name']!r}, {row['semantic_class']!r}, "
        f"{row['parser_class']!r}, {row['family_name']!r}, {row['schema_status']!r}, "
        f"{row['catalog_status']!r}, {tuple(row['declared_fields'])!r}, {row['semantic_level']!r}, "
        f"{bool(row['fully_domain_decoded'])!r}),"
    )


def generate_python(rows: list[dict[str, Any]]) -> str:
    class_defs = "\n\n".join(
        f"@dataclass(frozen=True, slots=True)\nclass {row['semantic_class']}(SemanticPdu):\n    pass"
        for row in rows
    )
    descriptors = "\n".join(_descriptor_literal(row) for row in rows)
    class_map_entries = "\n".join(f"    {row['semantic_class']!r}: {row['semantic_class']}," for row in rows)
    return (
        '"""Generated slotted semantic DIS PDU parser entry points.\n\n'
        "Every standard DIS 6/7 PDU row gets a semantic parser class. Rows without\n"
        "full domain decoding are represented as explicit semantic observations\n"
        "with raw-body preservation and diagnostics.\n"
        '"""\n\n'
        "from __future__ import annotations\n\n"
        "import struct\n"
        "from dataclasses import dataclass\n"
        "from types import MappingProxyType\n"
        "from typing import Mapping\n\n"
        "from .typed_pdus import TypedPdu, parse_typed_pdu, serialize_typed_pdu\n\n\n"
        "@dataclass(frozen=True, slots=True)\n"
        "class SemanticPduDescriptor:\n"
        "    protocol_version: int\n"
        "    pdu_type: int\n"
        "    protocol_family: int\n"
        "    standard_name: str\n"
        "    standard_class_name: str\n"
        "    semantic_class: str\n"
        "    typed_class: str\n"
        "    family_name: str\n"
        "    schema_status: str\n"
        "    catalog_status: str\n"
        "    declared_fields: tuple[str, ...]\n"
        "    semantic_level: str\n"
        "    fully_domain_decoded: bool\n\n\n"
        "@dataclass(frozen=True, slots=True)\n"
        "class SemanticPdu:\n"
        "    descriptor: SemanticPduDescriptor\n"
        "    typed: TypedPdu\n"
        "    semantic_fields: Mapping[str, object]\n"
        "    diagnostics: tuple[str, ...]\n\n"
        "    @property\n"
        "    def header(self):\n"
        "        return self.typed.header\n\n"
        "    @property\n"
        "    def packet(self) -> bytes:\n"
        "        return self.typed.packet\n\n"
        "    @property\n"
        "    def body(self) -> bytes:\n"
        "        return self.typed.body\n\n"
        "    @property\n"
        "    def semantic_level(self) -> str:\n"
        "        return self.descriptor.semantic_level\n\n\n"
        + class_defs
        + "\n\n\n"
        "SEMANTIC_PDU_DESCRIPTORS: tuple[SemanticPduDescriptor, ...] = (\n"
        + descriptors
        + "\n)\n\n"
        "_DESCRIPTORS_BY_KEY = {(item.protocol_version, item.pdu_type): item for item in SEMANTIC_PDU_DESCRIPTORS}\n"
        "_CLASS_BY_NAME: dict[str, type[SemanticPdu]] = {\n"
        + class_map_entries
        + "\n}\n\n\n"
        "def _entity_id(body: bytes, offset: int) -> tuple[dict[str, int], int]:\n"
        "    site, application, entity = struct.unpack_from('>HHH', body, offset)\n"
        "    return ({'site': int(site), 'application': int(application), 'entity': int(entity)}, offset + 6)\n\n\n"
        "def _event_id(body: bytes, offset: int) -> tuple[dict[str, int], int]:\n"
        "    site, application, event_number = struct.unpack_from('>HHH', body, offset)\n"
        "    return ({'site': int(site), 'application': int(application), 'event_number': int(event_number)}, offset + 6)\n\n\n"
        "def _entity_type(body: bytes, offset: int) -> tuple[dict[str, int], int]:\n"
        "    kind, domain, country, category, subcategory, specific, extra = struct.unpack_from('>BBHBBBB', body, offset)\n"
        "    return ({'kind': int(kind), 'domain': int(domain), 'country': int(country), 'category': int(category), 'subcategory': int(subcategory), 'specific': int(specific), 'extra': int(extra)}, offset + 8)\n\n\n"
        "def _vec3f(body: bytes, offset: int) -> tuple[dict[str, float], int]:\n"
        "    x, y, z = struct.unpack_from('>fff', body, offset)\n"
        "    return ({'x': float(x), 'y': float(y), 'z': float(z)}, offset + 12)\n\n\n"
        "def _vec3d(body: bytes, offset: int) -> tuple[dict[str, float], int]:\n"
        "    x, y, z = struct.unpack_from('>ddd', body, offset)\n"
        "    return ({'x': float(x), 'y': float(y), 'z': float(z)}, offset + 24)\n\n\n"
        "def _clock_time(body: bytes, offset: int) -> tuple[dict[str, int], int]:\n"
        "    hour, time_past_hour = struct.unpack_from('>II', body, offset)\n"
        "    return ({'hour': int(hour), 'time_past_hour': int(time_past_hour)}, offset + 8)\n\n\n"
        "def _munition_descriptor(body: bytes, offset: int) -> tuple[dict[str, object], int]:\n"
        "    munition_type, offset = _entity_type(body, offset)\n"
        "    warhead, fuse, quantity, rate = struct.unpack_from('>HHHH', body, offset)\n"
        "    return ({'munition_type': munition_type, 'warhead': int(warhead), 'fuse': int(fuse), 'quantity': int(quantity), 'rate': int(rate)}, offset + 8)\n\n\n"
        "def _decode_create_remove_entity(typed: TypedPdu) -> Mapping[str, object]:\n"
        "    body = typed.body\n"
        "    offset = 0\n"
        "    originating_entity_id, offset = _entity_id(body, offset)\n"
        "    receiving_entity_id, offset = _entity_id(body, offset)\n"
        "    request_id = int(struct.unpack_from('>I', body, offset)[0])\n"
        "    return MappingProxyType({\n"
        "        'originating_entity_id': originating_entity_id,\n"
        "        'receiving_entity_id': receiving_entity_id,\n"
        "        'request_id': request_id,\n"
        "    })\n\n\n"
        "def _decode_create_remove_entity_reliable(typed: TypedPdu) -> Mapping[str, object]:\n"
        "    body = typed.body\n"
        "    offset = 0\n"
        "    originating_entity_id, offset = _entity_id(body, offset)\n"
        "    receiving_entity_id, offset = _entity_id(body, offset)\n"
        "    required_reliability_service = int(struct.unpack_from('>B', body, offset)[0])\n"
        "    offset += 1\n"
        "    pad1 = int(struct.unpack_from('>H', body, offset)[0])\n"
        "    offset += 2\n"
        "    pad2 = int(struct.unpack_from('>B', body, offset)[0])\n"
        "    offset += 1\n"
        "    request_id = int(struct.unpack_from('>I', body, offset)[0])\n"
        "    return MappingProxyType({\n"
        "        'originating_entity_id': originating_entity_id,\n"
        "        'receiving_entity_id': receiving_entity_id,\n"
        "        'required_reliability_service': required_reliability_service,\n"
        "        'pad1': pad1,\n"
        "        'pad2': pad2,\n"
        "        'request_id': request_id,\n"
        "    })\n\n\n"
        "def _decode_start_resume(typed: TypedPdu) -> Mapping[str, object]:\n"
        "    body = typed.body\n"
        "    offset = 0\n"
        "    originating_entity_id, offset = _entity_id(body, offset)\n"
        "    receiving_entity_id, offset = _entity_id(body, offset)\n"
        "    real_world_time, offset = _clock_time(body, offset)\n"
        "    simulation_time, offset = _clock_time(body, offset)\n"
        "    request_id = int(struct.unpack_from('>I', body, offset)[0])\n"
        "    return MappingProxyType({\n"
        "        'originating_entity_id': originating_entity_id,\n"
        "        'receiving_entity_id': receiving_entity_id,\n"
        "        'real_world_time': real_world_time,\n"
        "        'simulation_time': simulation_time,\n"
        "        'request_id': request_id,\n"
        "    })\n\n\n"
        "def _decode_stop_freeze(typed: TypedPdu) -> Mapping[str, object]:\n"
        "    body = typed.body\n"
        "    offset = 0\n"
        "    originating_entity_id, offset = _entity_id(body, offset)\n"
        "    receiving_entity_id, offset = _entity_id(body, offset)\n"
        "    real_world_time, offset = _clock_time(body, offset)\n"
        "    reason = int(struct.unpack_from('>B', body, offset)[0])\n"
        "    offset += 1\n"
        "    frozen_behavior = int(struct.unpack_from('>B', body, offset)[0])\n"
        "    offset += 1\n"
        "    padding1 = int(struct.unpack_from('>H', body, offset)[0])\n"
        "    offset += 2\n"
        "    request_id = int(struct.unpack_from('>I', body, offset)[0])\n"
        "    return MappingProxyType({\n"
        "        'originating_entity_id': originating_entity_id,\n"
        "        'receiving_entity_id': receiving_entity_id,\n"
        "        'real_world_time': real_world_time,\n"
        "        'reason': reason,\n"
        "        'frozen_behavior': frozen_behavior,\n"
        "        'padding1': padding1,\n"
        "        'request_id': request_id,\n"
        "    })\n\n\n"
        "def _decode_acknowledge(typed: TypedPdu) -> Mapping[str, object]:\n"
        "    body = typed.body\n"
        "    offset = 0\n"
        "    originating_entity_id, offset = _entity_id(body, offset)\n"
        "    receiving_entity_id, offset = _entity_id(body, offset)\n"
        "    acknowledge_flag = int(struct.unpack_from('>H', body, offset)[0])\n"
        "    offset += 2\n"
        "    response_flag = int(struct.unpack_from('>H', body, offset)[0])\n"
        "    offset += 2\n"
        "    request_id = int(struct.unpack_from('>I', body, offset)[0])\n"
        "    return MappingProxyType({\n"
        "        'originating_entity_id': originating_entity_id,\n"
        "        'receiving_entity_id': receiving_entity_id,\n"
        "        'acknowledge_flag': acknowledge_flag,\n"
        "        'response_flag': response_flag,\n"
        "        'request_id': request_id,\n"
        "    })\n\n\n"
        "def _decode_start_resume_reliable(typed: TypedPdu) -> Mapping[str, object]:\n"
        "    body = typed.body\n"
        "    offset = 0\n"
        "    originating_entity_id, offset = _entity_id(body, offset)\n"
        "    receiving_entity_id, offset = _entity_id(body, offset)\n"
        "    real_world_time, offset = _clock_time(body, offset)\n"
        "    simulation_time, offset = _clock_time(body, offset)\n"
        "    required_reliability_service = int(struct.unpack_from('>B', body, offset)[0])\n"
        "    offset += 1\n"
        "    pad1 = int(struct.unpack_from('>H', body, offset)[0])\n"
        "    offset += 2\n"
        "    pad2 = int(struct.unpack_from('>B', body, offset)[0])\n"
        "    offset += 1\n"
        "    request_id = int(struct.unpack_from('>I', body, offset)[0])\n"
        "    return MappingProxyType({\n"
        "        'originating_entity_id': originating_entity_id,\n"
        "        'receiving_entity_id': receiving_entity_id,\n"
        "        'real_world_time': real_world_time,\n"
        "        'simulation_time': simulation_time,\n"
        "        'required_reliability_service': required_reliability_service,\n"
        "        'pad1': pad1,\n"
        "        'pad2': pad2,\n"
        "        'request_id': request_id,\n"
        "    })\n\n\n"
        "def _decode_stop_freeze_reliable(typed: TypedPdu) -> Mapping[str, object]:\n"
        "    body = typed.body\n"
        "    offset = 0\n"
        "    originating_entity_id, offset = _entity_id(body, offset)\n"
        "    receiving_entity_id, offset = _entity_id(body, offset)\n"
        "    real_world_time, offset = _clock_time(body, offset)\n"
        "    reason = int(struct.unpack_from('>B', body, offset)[0])\n"
        "    offset += 1\n"
        "    frozen_behavior = int(struct.unpack_from('>B', body, offset)[0])\n"
        "    offset += 1\n"
        "    required_reliablity_service = int(struct.unpack_from('>B', body, offset)[0])\n"
        "    offset += 1\n"
        "    pad1 = int(struct.unpack_from('>B', body, offset)[0])\n"
        "    offset += 1\n"
        "    request_id = int(struct.unpack_from('>I', body, offset)[0])\n"
        "    return MappingProxyType({\n"
        "        'originating_entity_id': originating_entity_id,\n"
        "        'receiving_entity_id': receiving_entity_id,\n"
        "        'real_world_time': real_world_time,\n"
        "        'reason': reason,\n"
        "        'frozen_behavior': frozen_behavior,\n"
        "        'required_reliablity_service': required_reliablity_service,\n"
        "        'pad1': pad1,\n"
        "        'request_id': request_id,\n"
        "    })\n\n\n"
        "def _decode_acknowledge_reliable(typed: TypedPdu) -> Mapping[str, object]:\n"
        "    return _decode_acknowledge(typed)\n\n\n"
        "def _decode_action_request(typed: TypedPdu) -> Mapping[str, object]:\n"
        "    body = typed.body\n"
        "    offset = 0\n"
        "    originating_entity_id, offset = _entity_id(body, offset)\n"
        "    receiving_entity_id, offset = _entity_id(body, offset)\n"
        "    request_id = int(struct.unpack_from('>I', body, offset)[0])\n"
        "    offset += 4\n"
        "    action_id = int(struct.unpack_from('>I', body, offset)[0])\n"
        "    offset += 4\n"
        "    number_of_fixed_datum_records = int(struct.unpack_from('>I', body, offset)[0])\n"
        "    offset += 4\n"
        "    number_of_variable_datum_records = int(struct.unpack_from('>I', body, offset)[0])\n"
        "    offset += 4\n"
        "    datum_record_bytes = body[offset:]\n"
        "    return MappingProxyType({\n"
        "        'originating_entity_id': originating_entity_id,\n"
        "        'receiving_entity_id': receiving_entity_id,\n"
        "        'request_id': request_id,\n"
        "        'action_id': action_id,\n"
        "        'number_of_fixed_datum_records': number_of_fixed_datum_records,\n"
        "        'number_of_variable_datum_records': number_of_variable_datum_records,\n"
        "        'datum_record_bytes': datum_record_bytes,\n"
        "    })\n\n\n"
        "def _decode_action_response(typed: TypedPdu) -> Mapping[str, object]:\n"
        "    body = typed.body\n"
        "    offset = 0\n"
        "    originating_entity_id, offset = _entity_id(body, offset)\n"
        "    receiving_entity_id, offset = _entity_id(body, offset)\n"
        "    request_id = int(struct.unpack_from('>I', body, offset)[0])\n"
        "    offset += 4\n"
        "    request_status = int(struct.unpack_from('>I', body, offset)[0])\n"
        "    offset += 4\n"
        "    number_of_fixed_datum_records = int(struct.unpack_from('>I', body, offset)[0])\n"
        "    offset += 4\n"
        "    number_of_variable_datum_records = int(struct.unpack_from('>I', body, offset)[0])\n"
        "    offset += 4\n"
        "    datum_record_bytes = body[offset:]\n"
        "    return MappingProxyType({\n"
        "        'originating_entity_id': originating_entity_id,\n"
        "        'receiving_entity_id': receiving_entity_id,\n"
        "        'request_id': request_id,\n"
        "        'request_status': request_status,\n"
        "        'number_of_fixed_datum_records': number_of_fixed_datum_records,\n"
        "        'number_of_variable_datum_records': number_of_variable_datum_records,\n"
        "        'datum_record_bytes': datum_record_bytes,\n"
        "    })\n\n\n"
        "def _decode_action_request_reliable(typed: TypedPdu) -> Mapping[str, object]:\n"
        "    body = typed.body\n"
        "    offset = 0\n"
        "    originating_entity_id, offset = _entity_id(body, offset)\n"
        "    receiving_entity_id, offset = _entity_id(body, offset)\n"
        "    required_reliability_service = int(struct.unpack_from('>B', body, offset)[0])\n"
        "    offset += 1\n"
        "    pad1 = int(struct.unpack_from('>H', body, offset)[0])\n"
        "    offset += 2\n"
        "    pad2 = int(struct.unpack_from('>B', body, offset)[0])\n"
        "    offset += 1\n"
        "    request_id = int(struct.unpack_from('>I', body, offset)[0])\n"
        "    offset += 4\n"
        "    action_id = int(struct.unpack_from('>I', body, offset)[0])\n"
        "    offset += 4\n"
        "    number_of_fixed_datum_records = int(struct.unpack_from('>I', body, offset)[0])\n"
        "    offset += 4\n"
        "    number_of_variable_datum_records = int(struct.unpack_from('>I', body, offset)[0])\n"
        "    offset += 4\n"
        "    datum_record_bytes = body[offset:]\n"
        "    return MappingProxyType({\n"
        "        'originating_entity_id': originating_entity_id,\n"
        "        'receiving_entity_id': receiving_entity_id,\n"
        "        'required_reliability_service': required_reliability_service,\n"
        "        'pad1': pad1,\n"
        "        'pad2': pad2,\n"
        "        'request_id': request_id,\n"
        "        'action_id': action_id,\n"
        "        'number_of_fixed_datum_records': number_of_fixed_datum_records,\n"
        "        'number_of_variable_datum_records': number_of_variable_datum_records,\n"
        "        'datum_record_bytes': datum_record_bytes,\n"
        "    })\n\n\n"
        "def _decode_action_response_reliable(typed: TypedPdu) -> Mapping[str, object]:\n"
        "    body = typed.body\n"
        "    offset = 0\n"
        "    originating_entity_id, offset = _entity_id(body, offset)\n"
        "    receiving_entity_id, offset = _entity_id(body, offset)\n"
        "    request_id = int(struct.unpack_from('>I', body, offset)[0])\n"
        "    offset += 4\n"
        "    response_status = int(struct.unpack_from('>I', body, offset)[0])\n"
        "    offset += 4\n"
        "    number_of_fixed_datum_records = int(struct.unpack_from('>I', body, offset)[0])\n"
        "    offset += 4\n"
        "    number_of_variable_datum_records = int(struct.unpack_from('>I', body, offset)[0])\n"
        "    offset += 4\n"
        "    datum_record_bytes = body[offset:]\n"
        "    return MappingProxyType({\n"
        "        'originating_entity_id': originating_entity_id,\n"
        "        'receiving_entity_id': receiving_entity_id,\n"
        "        'request_id': request_id,\n"
        "        'response_status': response_status,\n"
        "        'number_of_fixed_datum_records': number_of_fixed_datum_records,\n"
        "        'number_of_variable_datum_records': number_of_variable_datum_records,\n"
        "        'datum_record_bytes': datum_record_bytes,\n"
        "    })\n\n\n"
        "def _decode_fire(typed: TypedPdu) -> Mapping[str, object]:\n"
        "    body = typed.body\n"
        "    offset = 0\n"
        "    firing_entity_id, offset = _entity_id(body, offset)\n"
        "    target_entity_id, offset = _entity_id(body, offset)\n"
        "    munition_entity_id, offset = _entity_id(body, offset)\n"
        "    event_id, offset = _event_id(body, offset)\n"
        "    fire_mission_index = int(struct.unpack_from('>I', body, offset)[0])\n"
        "    offset += 4\n"
        "    world_location, offset = _vec3d(body, offset)\n"
        "    munition_descriptor, offset = _munition_descriptor(body, offset)\n"
        "    velocity, offset = _vec3f(body, offset)\n"
        "    range_to_target_m = float(struct.unpack_from('>f', body, offset)[0])\n"
        "    return MappingProxyType({\n"
        "        'firing_entity_id': firing_entity_id,\n"
        "        'target_entity_id': target_entity_id,\n"
        "        'munition_entity_id': munition_entity_id,\n"
        "        'event_id': event_id,\n"
        "        'fire_mission_index': fire_mission_index,\n"
        "        'world_location': world_location,\n"
        "        'munition_descriptor': munition_descriptor,\n"
        "        'velocity': velocity,\n"
        "        'range_to_target_m': range_to_target_m,\n"
        "    })\n\n\n"
        "def _decode_collision(typed: TypedPdu) -> Mapping[str, object]:\n"
        "    body = typed.body\n"
        "    offset = 0\n"
        "    issuing_entity_id, offset = _entity_id(body, offset)\n"
        "    colliding_entity_id, offset = _entity_id(body, offset)\n"
        "    event_id, offset = _event_id(body, offset)\n"
        "    collision_type = int(struct.unpack_from('>B', body, offset)[0])\n"
        "    offset += 1\n"
        "    padding = int(struct.unpack_from('>B', body, offset)[0])\n"
        "    offset += 1\n"
        "    velocity, offset = _vec3f(body, offset)\n"
        "    mass_kg = float(struct.unpack_from('>f', body, offset)[0])\n"
        "    offset += 4\n"
        "    location, offset = _vec3f(body, offset)\n"
        "    return MappingProxyType({\n"
        "        'issuing_entity_id': issuing_entity_id,\n"
        "        'colliding_entity_id': colliding_entity_id,\n"
        "        'event_id': event_id,\n"
        "        'collision_type': collision_type,\n"
        "        'padding': padding,\n"
        "        'velocity': velocity,\n"
        "        'mass_kg': mass_kg,\n"
        "        'location': location,\n"
        "    })\n\n\n"
        "def _decode_detonation(typed: TypedPdu) -> Mapping[str, object]:\n"
        "    body = typed.body\n"
        "    offset = 0\n"
        "    firing_entity_id, offset = _entity_id(body, offset)\n"
        "    target_entity_id, offset = _entity_id(body, offset)\n"
        "    exploding_entity_id, offset = _entity_id(body, offset)\n"
        "    event_id, offset = _event_id(body, offset)\n"
        "    velocity, offset = _vec3f(body, offset)\n"
        "    world_location, offset = _vec3d(body, offset)\n"
        "    munition_descriptor, offset = _munition_descriptor(body, offset)\n"
        "    location_in_entity_coordinates, offset = _vec3f(body, offset)\n"
        "    detonation_result = int(struct.unpack_from('>B', body, offset)[0])\n"
        "    offset += 1\n"
        "    variable_parameter_count = int(struct.unpack_from('>B', body, offset)[0])\n"
        "    offset += 1\n"
        "    padding = int(struct.unpack_from('>H', body, offset)[0])\n"
        "    offset += 2\n"
        "    variable_parameter_bytes = body[offset:]\n"
        "    return MappingProxyType({\n"
        "        'firing_entity_id': firing_entity_id,\n"
        "        'target_entity_id': target_entity_id,\n"
        "        'exploding_entity_id': exploding_entity_id,\n"
        "        'event_id': event_id,\n"
        "        'velocity': velocity,\n"
        "        'world_location': world_location,\n"
        "        'munition_descriptor': munition_descriptor,\n"
        "        'location_in_entity_coordinates': location_in_entity_coordinates,\n"
        "        'detonation_result': detonation_result,\n"
        "        'variable_parameter_count': variable_parameter_count,\n"
        "        'padding': padding,\n"
        "        'variable_parameter_bytes': variable_parameter_bytes,\n"
        "    })\n\n\n"
        "def _decode_directed_energy_fire(typed: TypedPdu) -> Mapping[str, object]:\n"
        "    body = typed.body\n"
        "    offset = 0\n"
        "    firing_entity_id, offset = _entity_id(body, offset)\n"
        "    target_entity_id, offset = _entity_id(body, offset)\n"
        "    munition_type, offset = _entity_type(body, offset)\n"
        "    shot_start_time, offset = _clock_time(body, offset)\n"
        "    cumulative_shot_time_s = float(struct.unpack_from('>f', body, offset)[0])\n"
        "    offset += 4\n"
        "    aperture_emitter_location, offset = _vec3f(body, offset)\n"
        "    aperture_diameter_m = float(struct.unpack_from('>f', body, offset)[0])\n"
        "    offset += 4\n"
        "    wavelength_m = float(struct.unpack_from('>f', body, offset)[0])\n"
        "    offset += 4\n"
        "    peak_irradiance_w_m2 = float(struct.unpack_from('>f', body, offset)[0])\n"
        "    offset += 4\n"
        "    pulse_repetition_frequency_hz = float(struct.unpack_from('>f', body, offset)[0])\n"
        "    offset += 4\n"
        "    pulse_width = int(struct.unpack_from('>I', body, offset)[0])\n"
        "    offset += 4\n"
        "    flags = int(struct.unpack_from('>I', body, offset)[0])\n"
        "    offset += 4\n"
        "    pulse_shape = int(struct.unpack_from('>B', body, offset)[0])\n"
        "    offset += 1\n"
        "    padding1 = int(struct.unpack_from('>B', body, offset)[0])\n"
        "    offset += 1\n"
        "    padding2 = int(struct.unpack_from('>I', body, offset)[0])\n"
        "    offset += 4\n"
        "    padding3 = int(struct.unpack_from('>H', body, offset)[0])\n"
        "    offset += 2\n"
        "    number_of_de_records = int(struct.unpack_from('>H', body, offset)[0])\n"
        "    offset += 2\n"
        "    de_record_bytes = body[offset:]\n"
        "    return MappingProxyType({\n"
        "        'firing_entity_id': firing_entity_id,\n"
        "        'target_entity_id': target_entity_id,\n"
        "        'munition_type': munition_type,\n"
        "        'shot_start_time': shot_start_time,\n"
        "        'cumulative_shot_time_s': cumulative_shot_time_s,\n"
        "        'aperture_emitter_location': aperture_emitter_location,\n"
        "        'aperture_diameter_m': aperture_diameter_m,\n"
        "        'wavelength_m': wavelength_m,\n"
        "        'peak_irradiance_w_m2': peak_irradiance_w_m2,\n"
        "        'pulse_repetition_frequency_hz': pulse_repetition_frequency_hz,\n"
        "        'pulse_width': pulse_width,\n"
        "        'flags': flags,\n"
        "        'pulse_shape': pulse_shape,\n"
        "        'padding1': padding1,\n"
        "        'padding2': padding2,\n"
        "        'padding3': padding3,\n"
        "        'number_of_de_records': number_of_de_records,\n"
        "        'de_record_bytes': de_record_bytes,\n"
        "    })\n\n\n"
        "def _decode_collision_elastic(typed: TypedPdu) -> Mapping[str, object]:\n"
        "    body = typed.body\n"
        "    offset = 0\n"
        "    issuing_entity_id, offset = _entity_id(body, offset)\n"
        "    colliding_entity_id, offset = _entity_id(body, offset)\n"
        "    event_id, offset = _event_id(body, offset)\n"
        "    padding = int(struct.unpack_from('>H', body, offset)[0])\n"
        "    offset += 2\n"
        "    contact_velocity, offset = _vec3f(body, offset)\n"
        "    mass_kg = float(struct.unpack_from('>f', body, offset)[0])\n"
        "    offset += 4\n"
        "    location, offset = _vec3f(body, offset)\n"
        "    tensor = struct.unpack_from('>ffffff', body, offset)\n"
        "    offset += 24\n"
        "    unit_surface_normal, offset = _vec3f(body, offset)\n"
        "    coefficient_of_restitution = float(struct.unpack_from('>f', body, offset)[0])\n"
        "    return MappingProxyType({\n"
        "        'issuing_entity_id': issuing_entity_id,\n"
        "        'colliding_entity_id': colliding_entity_id,\n"
        "        'event_id': event_id,\n"
        "        'padding': padding,\n"
        "        'contact_velocity': contact_velocity,\n"
        "        'mass_kg': mass_kg,\n"
        "        'location': location,\n"
        "        'collision_tensor': {\n"
        "            'xx': float(tensor[0]),\n"
        "            'xy': float(tensor[1]),\n"
        "            'xz': float(tensor[2]),\n"
        "            'yy': float(tensor[3]),\n"
        "            'yz': float(tensor[4]),\n"
        "            'zz': float(tensor[5]),\n"
        "        },\n"
        "        'unit_surface_normal': unit_surface_normal,\n"
        "        'coefficient_of_restitution': coefficient_of_restitution,\n"
        "    })\n\n\n"
        "def _decode_entity_damage_status(typed: TypedPdu) -> Mapping[str, object]:\n"
        "    body = typed.body\n"
        "    offset = 0\n"
        "    firing_entity_id, offset = _entity_id(body, offset)\n"
        "    target_entity_id, offset = _entity_id(body, offset)\n"
        "    damaged_entity_id, offset = _entity_id(body, offset)\n"
        "    padding1 = int(struct.unpack_from('>H', body, offset)[0])\n"
        "    offset += 2\n"
        "    padding2 = int(struct.unpack_from('>H', body, offset)[0])\n"
        "    offset += 2\n"
        "    number_of_damage_description = int(struct.unpack_from('>H', body, offset)[0])\n"
        "    offset += 2\n"
        "    damage_description_record_bytes = body[offset:]\n"
        "    return MappingProxyType({\n"
        "        'firing_entity_id': firing_entity_id,\n"
        "        'target_entity_id': target_entity_id,\n"
        "        'damaged_entity_id': damaged_entity_id,\n"
        "        'padding1': padding1,\n"
        "        'padding2': padding2,\n"
        "        'number_of_damage_description': number_of_damage_description,\n"
        "        'damage_description_record_bytes': damage_description_record_bytes,\n"
        "    })\n\n\n"
        "_SEMANTIC_DECODERS = {\n"
        "    (6, 11): _decode_create_remove_entity,\n"
        "    (6, 12): _decode_create_remove_entity,\n"
        "    (6, 13): _decode_start_resume,\n"
        "    (6, 14): _decode_stop_freeze,\n"
        "    (6, 15): _decode_acknowledge,\n"
        "    (6, 16): _decode_action_request,\n"
        "    (6, 17): _decode_action_response,\n"
        "    (6, 2): _decode_fire,\n"
        "    (6, 3): _decode_detonation,\n"
        "    (6, 4): _decode_collision,\n"
        "    (6, 51): _decode_create_remove_entity_reliable,\n"
        "    (6, 52): _decode_create_remove_entity_reliable,\n"
        "    (6, 53): _decode_start_resume_reliable,\n"
        "    (6, 54): _decode_stop_freeze_reliable,\n"
        "    (6, 55): _decode_acknowledge_reliable,\n"
        "    (6, 56): _decode_action_request_reliable,\n"
        "    (6, 57): _decode_action_response_reliable,\n"
        "    (6, 66): _decode_collision_elastic,\n"
        "    (7, 11): _decode_create_remove_entity,\n"
        "    (7, 12): _decode_create_remove_entity,\n"
        "    (7, 13): _decode_start_resume,\n"
        "    (7, 14): _decode_stop_freeze,\n"
        "    (7, 15): _decode_acknowledge,\n"
        "    (7, 16): _decode_action_request,\n"
        "    (7, 17): _decode_action_response,\n"
        "    (7, 2): _decode_fire,\n"
        "    (7, 3): _decode_detonation,\n"
        "    (7, 4): _decode_collision,\n"
        "    (7, 51): _decode_create_remove_entity_reliable,\n"
        "    (7, 52): _decode_create_remove_entity_reliable,\n"
        "    (7, 53): _decode_start_resume_reliable,\n"
        "    (7, 54): _decode_stop_freeze_reliable,\n"
        "    (7, 55): _decode_acknowledge_reliable,\n"
        "    (7, 56): _decode_action_request_reliable,\n"
        "    (7, 57): _decode_action_response_reliable,\n"
        "    (7, 66): _decode_collision_elastic,\n"
        "    (7, 68): _decode_directed_energy_fire,\n"
        "    (7, 69): _decode_entity_damage_status,\n"
        "}\n\n\n"
        "def find_semantic_pdu_descriptor(protocol_version: int, pdu_type: int) -> SemanticPduDescriptor | None:\n"
        "    return _DESCRIPTORS_BY_KEY.get((protocol_version, pdu_type))\n\n\n"
        "def _semantic_fields(descriptor: SemanticPduDescriptor, typed: TypedPdu) -> Mapping[str, object]:\n"
        "    fields = {\n"
        "        'protocol_version': typed.header[0],\n"
        "        'exercise_id': typed.header[1],\n"
        "        'pdu_type': typed.header[2],\n"
        "        'protocol_family': typed.header[3],\n"
        "        'timestamp': typed.header[4],\n"
        "        'declared_length': typed.header[5],\n"
        "        'standard_name': descriptor.standard_name,\n"
        "        'standard_class_name': descriptor.standard_class_name,\n"
        "        'schema_status': descriptor.schema_status,\n"
        "        'catalog_status': descriptor.catalog_status,\n"
        "        'declared_fields': descriptor.declared_fields,\n"
        "        'raw_body_size': len(typed.body),\n"
        "        'raw_body': typed.body,\n"
        "        'typed_parse_level': typed.parse_level,\n"
        "        'fully_domain_decoded': descriptor.fully_domain_decoded,\n"
        "    }\n"
        "    decoder = _SEMANTIC_DECODERS.get((typed.header[0], typed.header[2]))\n"
        "    if decoder is not None:\n"
        "        fields['semantic_decode_status'] = 'decoded'\n"
        "        fields.update(decoder(typed))\n"
        "    elif descriptor.semantic_level == 'semantic_prefix':\n"
        "        fields['semantic_prefix_available'] = True\n"
        "        fields['semantic_decode_status'] = 'prefix'\n"
        "    else:\n"
        "        fields['semantic_decode_status'] = 'observation'\n"
        "    return MappingProxyType(fields)\n\n\n"
        "def _diagnostics(descriptor: SemanticPduDescriptor) -> tuple[str, ...]:\n"
        "    if descriptor.semantic_level == 'semantic_decoded':\n"
        "        return ('full domain decode available',)\n"
        "    if descriptor.semantic_level == 'semantic_prefix':\n"
        "        return ('semantic prefix parser available',)\n"
        "    return (\n"
        "        'semantic observation parser: full domain semantics not yet implemented',\n"
        "        f'schema_status={descriptor.schema_status}',\n"
        "    )\n\n\n"
        "def parse_semantic_pdu(data: bytes | bytearray | memoryview, *, strict: bool = True) -> SemanticPdu | None:\n"
        "    typed = parse_typed_pdu(data, strict=strict)\n"
        "    if typed is None:\n"
        "        return None\n"
        "    descriptor = find_semantic_pdu_descriptor(typed.header[0], typed.header[2])\n"
        "    if descriptor is None:\n"
        "        if strict:\n"
        "            raise ValueError(f'unknown DIS PDU type {typed.header[2]} for protocol version {typed.header[0]}')\n"
        "        return None\n"
        "    cls = _CLASS_BY_NAME[descriptor.semantic_class]\n"
        "    return cls(\n"
        "        descriptor=descriptor,\n"
        "        typed=typed,\n"
        "        semantic_fields=_semantic_fields(descriptor, typed),\n"
        "        diagnostics=_diagnostics(descriptor),\n"
        "    )\n\n\n"
        "def serialize_semantic_pdu(view: SemanticPdu) -> bytes:\n"
        "    if not isinstance(view, SemanticPdu):\n"
        "        raise TypeError('serialize_semantic_pdu expects a SemanticPdu')\n"
        "    return serialize_typed_pdu(view.typed)\n\n\n"
        "def parse_many_semantic(packets: list[bytes] | tuple[bytes, ...], *, strict: bool = False) -> list[SemanticPdu]:\n"
        "    out: list[SemanticPdu] = []\n"
        "    for packet in packets:\n"
        "        view = parse_semantic_pdu(packet, strict=strict)\n"
        "        if view is not None:\n"
        "            out.append(view)\n"
        "    return out\n\n\n"
        "SEMANTIC_PDU_PARSERS = {(item.protocol_version, item.pdu_type): parse_semantic_pdu for item in SEMANTIC_PDU_DESCRIPTORS}\n"
        "SEMANTIC_PDU_SERIALIZERS = {(item.protocol_version, item.pdu_type): serialize_semantic_pdu for item in SEMANTIC_PDU_DESCRIPTORS}\n"
    )


def generate_manifest(rows: list[dict[str, Any]]) -> str:
    payload = {
        "schema": "fastdis.semantic_pdu_parser_manifest.v1",
        "policy": {
            "semantic_parser": "Every standard DIS 6/7 PDU row has a generated semantic parser entry point.",
            "semantic_observation": "Rows without full domain decoding produce explicit semantic observations with diagnostics.",
            "semantic_prefix": "Rows with current typed semantic support expose semantic-prefix availability.",
            "semantic_decoded": "Rows with fixed-field semantic decoders expose decoded domain fields beyond metadata-only observations.",
        },
        "summary": {
            "records": len(rows),
            "semantic_parsers": sum(1 for row in rows if row["semantic_parser"]),
            "semantic_observation": sum(1 for row in rows if row["semantic_level"] == "semantic_observation"),
            "semantic_prefix": sum(1 for row in rows if row["semantic_level"] == "semantic_prefix"),
            "semantic_decoded": sum(1 for row in rows if row["semantic_level"] == "semantic_decoded"),
            "fully_domain_decoded": sum(1 for row in rows if row["fully_domain_decoded"]),
        },
        "records": rows,
    }
    return json.dumps(payload, indent=2) + "\n"


def generate_markdown(rows: list[dict[str, Any]]) -> str:
    semantic_parsers = sum(1 for row in rows if row["semantic_parser"])
    semantic_observation = sum(1 for row in rows if row["semantic_level"] == "semantic_observation")
    semantic_prefix = sum(1 for row in rows if row["semantic_level"] == "semantic_prefix")
    semantic_decoded = sum(1 for row in rows if row["semantic_level"] == "semantic_decoded")
    fully_domain_decoded = sum(1 for row in rows if row["fully_domain_decoded"])
    lines = [
        "# Semantic PDU Coverage",
        "",
        "FastDIS generates semantic parser entry points for every standard DIS 6/7 PDU row.",
        "",
        "## Summary",
        "",
        f"- Semantic parser entry points: `{semantic_parsers} / 141`",
        f"- Semantic observation parsers: `{semantic_observation} / 141`",
        f"- Semantic prefix parsers: `{semantic_prefix} / 141`",
        f"- Semantic decoded parsers: `{semantic_decoded} / 141`",
        f"- Fully domain-decoded semantic parsers: `{fully_domain_decoded} / 141`",
        "",
        "A semantic observation is a real parser entry point with a named slotted class, header identity, raw body preservation, declared-field metadata where available, and diagnostics that say full domain decoding is not implemented yet. Semantic decoded rows go further and expose decoded fixed-field domain structures. This avoids silent overclaiming while still giving every PDU a typed semantic surface.",
        "",
        "| DIS | PDU | Name | Semantic class | Level | Fully decoded |",
        "| ---: | ---: | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {row['protocol_version']} | {row['pdu_type']} | {row['standard_name']} | "
            f"`{row['semantic_class']}` | `{row['semantic_level']}` | "
            f"{'yes' if row['fully_domain_decoded'] else 'no'} |"
        )
    return "\n".join(lines) + "\n"


def outputs(dis6: Path, dis7: Path) -> dict[Path, str]:
    rows = semantic_rows(dis6, dis7)
    return {
        ROOT / "src" / "fastdis" / "semantic_pdus.py": generate_python(rows),
        ROOT / "generated" / "semantic_pdu_parser_manifest.json": generate_manifest(rows),
        ROOT / "docs" / "SEMANTIC_PDU_COVERAGE.md": generate_markdown(rows),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dis6", type=Path, default=DEFAULT_DIS6)
    parser.add_argument("--dis7", type=Path, default=DEFAULT_DIS7)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    rendered = outputs(args.dis6, args.dis7)
    if args.check:
        stale: list[Path] = []
        for path, content in rendered.items():
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                stale.append(path)
        if stale:
            print("stale generated semantic PDU parser artifacts:", file=sys.stderr)
            for path in stale:
                print(f"  {path.relative_to(ROOT)}", file=sys.stderr)
            return 1
        return 0

    for path, content in rendered.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    rows = semantic_rows(args.dis6, args.dis7)
    print(
        "generated semantic PDU parsers "
        f"semantic_parsers={len(rows)} fully_domain_decoded={sum(1 for row in rows if row['fully_domain_decoded'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
