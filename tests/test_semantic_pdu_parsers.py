from __future__ import annotations

import json
from pathlib import Path
import struct
import subprocess
import sys

import fastdis


ROOT = Path(__file__).resolve().parents[1]


def _ensure_manifest() -> dict[str, object]:
    path = ROOT / "generated" / "semantic_pdu_parser_manifest.json"
    if not path.exists():
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "generate_semantic_pdu_parsers.py")],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
    return json.loads(path.read_text(encoding="utf-8"))


def _packet(version: int, pdu_type: int, family: int, *, body: bytes = b"") -> bytes:
    length = 12 + len(body)
    return struct.pack(">BBBBIHH", version, 1, pdu_type, family, 0x10203040, length, 0) + body


def _entity_id(site: int, application: int, entity: int) -> bytes:
    return struct.pack(">HHH", site, application, entity)


def _event_id(site: int, application: int, event_number: int) -> bytes:
    return struct.pack(">HHH", site, application, event_number)


def _entity_type(kind: int, domain: int, country: int, category: int, subcategory: int, specific: int, extra: int) -> bytes:
    return struct.pack(">BBHBBBB", kind, domain, country, category, subcategory, specific, extra)


def _vec3f(x: float, y: float, z: float) -> bytes:
    return struct.pack(">fff", x, y, z)


def _vec3d(x: float, y: float, z: float) -> bytes:
    return struct.pack(">ddd", x, y, z)


def _munition_descriptor() -> bytes:
    return _entity_type(2, 1, 225, 4, 5, 6, 7) + struct.pack(">HHHH", 101, 202, 3, 600)


def _fire_body() -> bytes:
    return b"".join(
        [
            _entity_id(1, 2, 3),
            _entity_id(4, 5, 6),
            _entity_id(7, 8, 9),
            _event_id(10, 11, 12),
            struct.pack(">I", 99),
            _vec3d(1000.5, 2000.25, 3000.75),
            _munition_descriptor(),
            _vec3f(1.5, 2.5, 3.5),
            struct.pack(">f", 4444.5),
        ]
    )


def _collision_body() -> bytes:
    return b"".join(
        [
            _entity_id(1, 2, 3),
            _entity_id(4, 5, 6),
            _event_id(7, 8, 9),
            struct.pack(">BB", 13, 0),
            _vec3f(10.0, 20.0, 30.0),
            struct.pack(">f", 1250.0),
            _vec3f(-1.0, -2.0, -3.0),
        ]
    )


def _detonation_body() -> bytes:
    return b"".join(
        [
            _entity_id(1, 2, 3),
            _entity_id(4, 5, 6),
            _entity_id(7, 8, 9),
            _event_id(10, 11, 12),
            _vec3f(11.0, 22.0, 33.0),
            _vec3d(111.5, 222.25, 333.75),
            _munition_descriptor(),
            _vec3f(-4.0, -5.0, -6.0),
            struct.pack(">BBH", 17, 1, 0),
            bytes.fromhex("0102030405060708090a0b0c0d0e0f10"),
        ]
    )


def _directed_energy_fire_body() -> bytes:
    return b"".join(
        [
            _entity_id(1, 2, 3),
            _entity_id(4, 5, 6),
            _entity_type(9, 8, 840, 7, 6, 5, 4),
            struct.pack(">II", 123456, 7890),
            struct.pack(">f", 1.25),
            _vec3f(0.5, 1.5, 2.5),
            struct.pack(">f", 0.75),
            struct.pack(">f", 1.064e-6),
            struct.pack(">f", 5000.0),
            struct.pack(">f", 60.0),
            struct.pack(">I", 42),
            struct.pack(">I", 0x12),
            struct.pack(">BBIHH", 3, 0, 0, 0, 1),
            bytes.fromhex("00112233445566778899aabbccddeeff"),
        ]
    )


def _collision_elastic_body() -> bytes:
    return b"".join(
        [
            _entity_id(1, 2, 3),
            _entity_id(4, 5, 6),
            _event_id(7, 8, 9),
            struct.pack(">H", 0),
            _vec3f(10.0, 20.0, 30.0),
            struct.pack(">f", 1250.0),
            _vec3f(-1.0, -2.0, -3.0),
            struct.pack(">ffffff", 1.0, 0.1, 0.2, 2.0, 0.3, 3.0),
            _vec3f(0.0, 1.0, 0.0),
            struct.pack(">f", 0.85),
        ]
    )


def _body_for_descriptor(descriptor: object) -> bytes:
    protocol_version = descriptor.protocol_version
    pdu_type = descriptor.pdu_type
    if (protocol_version, pdu_type) in {(6, 2), (7, 2)}:
        return _fire_body()
    if (protocol_version, pdu_type) in {(6, 3), (7, 3)}:
        return _detonation_body()
    if (protocol_version, pdu_type) in {(6, 4), (7, 4)}:
        return _collision_body()
    if (protocol_version, pdu_type) in {(6, 66), (7, 66)}:
        return _collision_elastic_body()
    if (protocol_version, pdu_type) == (7, 68):
        return _directed_energy_fire_body()
    if (protocol_version, pdu_type) == (7, 1):
        return b"\x00" * 132
    return b"\x01\x02"


def test_semantic_parser_manifest_has_141_entry_points() -> None:
    manifest = _ensure_manifest()
    summary = manifest["summary"]
    assert summary["records"] == 141
    assert summary["semantic_parsers"] == 141
    assert summary["semantic_observation"] == 128
    assert summary["semantic_prefix"] == 4
    assert summary["semantic_decoded"] == 9
    assert summary["fully_domain_decoded"] == 13
    assert len(fastdis.SEMANTIC_PDU_DESCRIPTORS) == 141


def test_every_standard_pdu_dispatches_to_a_semantic_slotted_class() -> None:
    for descriptor in fastdis.SEMANTIC_PDU_DESCRIPTORS:
        body = _body_for_descriptor(descriptor)
        packet = _packet(
            descriptor.protocol_version,
            descriptor.pdu_type,
            descriptor.protocol_family,
            body=body,
        )
        view = fastdis.parse_semantic_pdu(packet)
        assert view is not None
        assert view.descriptor == descriptor
        assert view.header[0] == descriptor.protocol_version
        assert view.header[2] == descriptor.pdu_type
        assert view.header[3] == descriptor.protocol_family
        assert view.body == body
        assert view.semantic_level == descriptor.semantic_level
        assert fastdis.serialize_semantic_pdu(view) == packet
        assert not hasattr(view, "__dict__")
        assert hasattr(type(view), "__slots__")
        assert type(view).__name__ == descriptor.semantic_class


def test_semantic_observation_rows_are_explicit_and_diagnostic() -> None:
    designator = fastdis.parse_semantic_pdu(_packet(7, 24, 6, body=b"abc"))
    assert designator is not None
    assert designator.semantic_level == "semantic_observation"
    assert not designator.descriptor.fully_domain_decoded
    assert designator.semantic_fields["standard_name"] == "Designator"
    assert designator.semantic_fields["raw_body"] == b"abc"
    assert any("full domain semantics not yet implemented" in item for item in designator.diagnostics)


def test_fire_rows_expose_decoded_semantic_fields() -> None:
    fire = fastdis.parse_semantic_pdu(_packet(7, 2, 2, body=_fire_body()))
    assert fire is not None
    assert fire.semantic_level == "semantic_decoded"
    assert fire.descriptor.fully_domain_decoded
    assert fire.semantic_fields["semantic_decode_status"] == "decoded"
    assert fire.semantic_fields["firing_entity_id"] == {"site": 1, "application": 2, "entity": 3}
    assert fire.semantic_fields["target_entity_id"] == {"site": 4, "application": 5, "entity": 6}
    assert fire.semantic_fields["munition_entity_id"] == {"site": 7, "application": 8, "entity": 9}
    assert fire.semantic_fields["event_id"] == {"site": 10, "application": 11, "event_number": 12}
    assert fire.semantic_fields["fire_mission_index"] == 99
    assert fire.semantic_fields["munition_descriptor"]["quantity"] == 3
    assert abs(fire.semantic_fields["range_to_target_m"] - 4444.5) < 1e-3
    assert fire.diagnostics == ("full domain decode available",)


def test_collision_elastic_rows_expose_decoded_semantic_fields() -> None:
    collision = fastdis.parse_semantic_pdu(_packet(7, 66, 1, body=_collision_elastic_body()))
    assert collision is not None
    assert collision.semantic_level == "semantic_decoded"
    assert collision.descriptor.fully_domain_decoded
    assert collision.semantic_fields["semantic_decode_status"] == "decoded"
    assert collision.semantic_fields["contact_velocity"] == {"x": 10.0, "y": 20.0, "z": 30.0}
    assert collision.semantic_fields["collision_tensor"]["yy"] == 2.0
    assert collision.semantic_fields["unit_surface_normal"] == {"x": 0.0, "y": 1.0, "z": 0.0}
    assert abs(collision.semantic_fields["coefficient_of_restitution"] - 0.85) < 1e-6


def test_detonation_rows_expose_decoded_semantic_core_and_preserve_tail() -> None:
    detonation = fastdis.parse_semantic_pdu(_packet(7, 3, 2, body=_detonation_body()))
    assert detonation is not None
    assert detonation.semantic_level == "semantic_decoded"
    assert detonation.descriptor.fully_domain_decoded
    assert detonation.semantic_fields["semantic_decode_status"] == "decoded"
    assert detonation.semantic_fields["firing_entity_id"] == {"site": 1, "application": 2, "entity": 3}
    assert detonation.semantic_fields["target_entity_id"] == {"site": 4, "application": 5, "entity": 6}
    assert detonation.semantic_fields["exploding_entity_id"] == {"site": 7, "application": 8, "entity": 9}
    assert detonation.semantic_fields["event_id"] == {"site": 10, "application": 11, "event_number": 12}
    assert detonation.semantic_fields["detonation_result"] == 17
    assert detonation.semantic_fields["variable_parameter_count"] == 1
    assert detonation.semantic_fields["variable_parameter_bytes"] == bytes.fromhex("0102030405060708090a0b0c0d0e0f10")
    assert detonation.diagnostics == ("full domain decode available",)


def test_directed_energy_fire_rows_expose_decoded_core_and_preserve_records() -> None:
    directed_energy = fastdis.parse_semantic_pdu(_packet(7, 68, 2, body=_directed_energy_fire_body()))
    assert directed_energy is not None
    assert directed_energy.semantic_level == "semantic_decoded"
    assert directed_energy.descriptor.fully_domain_decoded
    assert directed_energy.semantic_fields["semantic_decode_status"] == "decoded"
    assert directed_energy.semantic_fields["firing_entity_id"] == {"site": 1, "application": 2, "entity": 3}
    assert directed_energy.semantic_fields["target_entity_id"] == {"site": 4, "application": 5, "entity": 6}
    assert directed_energy.semantic_fields["munition_type"]["country"] == 840
    assert directed_energy.semantic_fields["shot_start_time"] == {"hour": 123456, "time_past_hour": 7890}
    assert abs(directed_energy.semantic_fields["cumulative_shot_time_s"] - 1.25) < 1e-6
    assert directed_energy.semantic_fields["aperture_emitter_location"] == {"x": 0.5, "y": 1.5, "z": 2.5}
    assert directed_energy.semantic_fields["number_of_de_records"] == 1
    assert directed_energy.semantic_fields["de_record_bytes"] == bytes.fromhex("00112233445566778899aabbccddeeff")
    assert directed_energy.diagnostics == ("full domain decode available",)


def test_semantic_prefix_rows_remain_marked_for_entity_state() -> None:
    entity_state = fastdis.parse_semantic_pdu(_packet(7, 1, 1, body=b"\x00" * 132))
    assert entity_state is not None
    assert entity_state.semantic_level == "semantic_prefix"
    assert entity_state.descriptor.fully_domain_decoded
    assert entity_state.semantic_fields["semantic_prefix_available"] is True


def test_generate_semantic_pdu_parsers_check_passes_for_current_tree() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "generate_semantic_pdu_parsers.py"), "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
