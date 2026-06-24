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


def _supply_quantity(kind: int, domain: int, country: int, category: int, subcategory: int, specific: int, extra: int, quantity: float) -> bytes:
    return _entity_type(kind, domain, country, category, subcategory, specific, extra) + struct.pack(">f", quantity)


def _service_request_body() -> bytes:
    return b"".join(
        [
            _entity_id(1, 2, 3),
            _entity_id(4, 5, 6),
            struct.pack(">BBh", 7, 2, 0),
            _supply_quantity(1, 2, 225, 3, 4, 5, 6, 10.5),
            _supply_quantity(2, 3, 840, 7, 8, 9, 10, 20.25),
        ]
    )


def _resupply_offer_or_received_body() -> bytes:
    return b"".join(
        [
            _entity_id(11, 12, 13),
            _entity_id(14, 15, 16),
            struct.pack(">Bbh", 2, 0, 0),
            _supply_quantity(3, 4, 124, 11, 12, 13, 14, 30.5),
            _supply_quantity(4, 5, 826, 15, 16, 17, 18, 40.75),
        ]
    )


def _resupply_cancel_body() -> bytes:
    return b"".join(
        [
            _entity_id(21, 22, 23),
            _entity_id(24, 25, 26),
        ]
    )


def _repair_complete_body() -> bytes:
    return b"".join(
        [
            _entity_id(31, 32, 33),
            _entity_id(34, 35, 36),
            struct.pack(">Hh", 37, 0),
        ]
    )


def _repair_response_body() -> bytes:
    return b"".join(
        [
            _entity_id(41, 42, 43),
            _entity_id(44, 45, 46),
            struct.pack(">Bbh", 47, 0, 0),
        ]
    )


def _relationship(nature: int, position: int) -> bytes:
    return struct.pack(">HH", nature, position)


def _named_location(station_name: int, station_number: int) -> bytes:
    return struct.pack(">HH", station_name, station_number)


def _simulation_address(site: int, application: int) -> bytes:
    return struct.pack(">HH", site, application)


def _object_type_dis6(entity_kind: int, domain: int, country: int, category: int, subcategory: int) -> bytes:
    return struct.pack(">BBHBB", entity_kind, domain, country, category, subcategory)


def _object_type_dis7(domain: int, object_kind: int, category: int, subcategory: int) -> bytes:
    return struct.pack(">BBBB", domain, object_kind, category, subcategory)


def _point_object_state_dis6_body() -> bytes:
    return b"".join(
        [
            _entity_id(51, 52, 53),
            _entity_id(54, 55, 56),
            struct.pack(">HBB", 57, 58, 59),
            _object_type_dis6(1, 2, 840, 3, 4),
            _vec3d(100.25, 200.5, 300.75),
            struct.pack(">fff", 0.1, 0.2, 0.3),
            struct.pack(">d", 1234.5),
            _simulation_address(60, 61),
            _simulation_address(62, 63),
            struct.pack(">I", 64),
        ]
    )


def _point_object_state_dis7_body() -> bytes:
    return b"".join(
        [
            _entity_id(71, 72, 73),
            _entity_id(74, 75, 76),
            struct.pack(">HBB", 77, 78, 79),
            _object_type_dis7(4, 5, 6, 7),
            _vec3d(400.25, 500.5, 600.75),
            struct.pack(">fff", 0.4, 0.5, 0.6),
            struct.pack(">d", 2345.5),
            _simulation_address(80, 81),
            _simulation_address(82, 83),
            struct.pack(">I", 84),
        ]
    )


def _linear_segment_parameter_dis6(
    segment_number: int,
    segment_appearance: bytes,
    location: tuple[float, float, float],
    orientation: tuple[float, float, float],
    lengths: tuple[int, int, int, int],
    pad1: int,
) -> bytes:
    return b"".join(
        [
            struct.pack(">B", segment_number),
            segment_appearance,
            _vec3d(*location),
            struct.pack(">fff", *orientation),
            struct.pack(">HHHHI", *lengths, pad1),
        ]
    )


def _linear_segment_parameter_dis7(
    segment_number: int,
    segment_modification: int,
    general_segment_appearance: int,
    specific_segment_appearance: int,
    location: tuple[float, float, float],
    orientation: tuple[float, float, float],
    dimensions: tuple[float, float, float, float],
    padding: int,
) -> bytes:
    return b"".join(
        [
            struct.pack(">BBHI", segment_number, segment_modification, general_segment_appearance, specific_segment_appearance),
            _vec3d(*location),
            struct.pack(">fff", *orientation),
            struct.pack(">ffff", *dimensions),
            struct.pack(">I", padding),
        ]
    )


def _linear_object_state_dis6_body() -> bytes:
    return b"".join(
        [
            _entity_id(131, 132, 133),
            _entity_id(134, 135, 136),
            struct.pack(">HBB", 137, 138, 2),
            _simulation_address(139, 140),
            _simulation_address(141, 142),
            _object_type_dis6(9, 10, 840, 11, 12),
            _linear_segment_parameter_dis6(
                1,
                bytes.fromhex("010203040506"),
                (1000.25, 1001.5, 1002.75),
                (0.1, 0.2, 0.3),
                (25, 26, 27, 28),
                29,
            ),
            _linear_segment_parameter_dis6(
                2,
                bytes.fromhex("0a0b0c0d0e0f"),
                (2000.25, 2001.5, 2002.75),
                (0.4, 0.5, 0.6),
                (35, 36, 37, 38),
                39,
            ),
        ]
    )


def _linear_object_state_dis7_body() -> bytes:
    return b"".join(
        [
            _entity_id(151, 152, 153),
            _entity_id(154, 155, 156),
            struct.pack(">HBB", 157, 158, 2),
            _simulation_address(159, 160),
            _simulation_address(161, 162),
            _object_type_dis7(13, 14, 15, 16),
            _linear_segment_parameter_dis7(
                3,
                4,
                0x0506,
                0x0708090A,
                (3000.25, 3001.5, 3002.75),
                (0.7, 0.8, 0.9),
                (45.5, 46.5, 47.5, 48.5),
                49,
            ),
            _linear_segment_parameter_dis7(
                5,
                6,
                0x0B0C,
                0x0D0E0F10,
                (4000.25, 4001.5, 4002.75),
                (1.0, 1.1, 1.2),
                (55.5, 56.5, 57.5, 58.5),
                59,
            ),
        ]
    )


def _areal_object_state_dis6_body() -> bytes:
    return b"".join(
        [
            _entity_id(91, 92, 93),
            _entity_id(94, 95, 96),
            struct.pack(">HBB", 97, 98, 99),
            _entity_type(3, 4, 225, 5, 6, 7, 8),
            bytes.fromhex("010203040506"),
            struct.pack(">H", 2),
            _simulation_address(100, 101),
            _simulation_address(102, 103),
            _vec3d(1.0, 2.0, 3.0),
            _vec3d(4.0, 5.0, 6.0),
        ]
    )


def _areal_object_state_dis7_body() -> bytes:
    return b"".join(
        [
            _entity_id(111, 112, 113),
            _entity_id(114, 115, 116),
            struct.pack(">HBB", 117, 118, 119),
            _entity_type(6, 7, 124, 8, 9, 10, 11),
            struct.pack(">IH", 120, 121),
            struct.pack(">H", 2),
            _simulation_address(122, 123),
            _simulation_address(124, 125),
            _vec3d(7.0, 8.0, 9.0),
            _vec3d(10.0, 11.0, 12.0),
        ]
    )


def _is_part_of_body() -> bytes:
    return b"".join(
        [
            _entity_id(171, 172, 173),
            _entity_id(174, 175, 176),
            _relationship(177, 178),
            _vec3f(1.25, 2.5, 3.75),
            _named_location(179, 180),
            _entity_type(5, 6, 225, 7, 8, 9, 10),
        ]
    )


def _minefield_response_nack_body() -> bytes:
    return b"".join(
        [
            _entity_id(181, 182, 183),
            _entity_id(184, 185, 186),
            struct.pack(">BB", 187, 2),
            bytes.fromhex("0102030405060708"),
            bytes.fromhex("1112131415161718"),
        ]
    )


def _transfer_control_body() -> bytes:
    return b"".join(
        [
            _entity_id(191, 192, 193),
            _entity_id(194, 195, 196),
            struct.pack(">IBB", 0xA1A2A3A4, 7, 8),
            _entity_id(197, 198, 199),
            struct.pack(">B", 2),
            bytes.fromhex("0102030405060708090a0b0c"),
        ]
    )


def _minefield_query_body() -> bytes:
    return b"".join(
        [
            _entity_id(201, 202, 203),
            _entity_id(204, 205, 206),
            struct.pack(">BBBBI", 207, 2, 0, 2, 0x01020304),
            _entity_type(3, 4, 225, 5, 6, 7, 8),
            struct.pack(">ff", 1.5, 2.5),
            struct.pack(">ff", 3.5, 4.5),
            bytes.fromhex("1112"),
            bytes.fromhex("2122"),
        ]
    )


def _environmental_process_body() -> bytes:
    return b"".join(
        [
            _entity_id(211, 212, 213),
            _entity_type(9, 10, 840, 11, 12, 13, 14),
            struct.pack(">BBBH", 15, 16, 2, 0x1718),
            bytes.fromhex("3132333435363738393a"),
        ]
    )


def _minefield_state_dis6_body() -> bytes:
    return b"".join(
        [
            _entity_id(221, 222, 223),
            struct.pack(">HBB", 224, 225, 2),
            _entity_type(1, 2, 840, 3, 4, 5, 6),
            struct.pack(">H", 2),
            _vec3d(10.25, 20.5, 30.75),
            struct.pack(">fff", 0.1, 0.2, 0.3),
            struct.pack(">HH", 226, 227),
            struct.pack(">ff", 1.5, 2.5),
            struct.pack(">ff", 3.5, 4.5),
            _entity_type(7, 8, 124, 9, 10, 11, 12),
            _entity_type(13, 14, 225, 15, 16, 17, 18),
        ]
    )


def _minefield_state_dis7_body() -> bytes:
    return b"".join(
        [
            _simulation_address(231, 232),
            struct.pack(">H", 233),
            struct.pack(">HBB", 234, 235, 2),
            _entity_type(19, 20, 225, 21, 22, 23, 24),
            struct.pack(">H", 2),
            _vec3d(40.25, 50.5, 60.75),
            struct.pack(">fff", 0.4, 0.5, 0.6),
            struct.pack(">HH", 236, 237),
            struct.pack(">ff", 5.5, 6.5),
            struct.pack(">ff", 7.5, 8.5),
            _entity_type(25, 26, 840, 27, 28, 29, 30),
            _entity_type(31, 32, 124, 33, 34, 35, 36),
        ]
    )


def _is_group_of_dis6_body() -> bytes:
    return b"".join(
        [
            _entity_id(241, 242, 243),
            struct.pack(">BBI", 244, 2, 245),
            struct.pack(">d", 46.125),
            struct.pack(">d", -93.5),
            bytes.fromhex("4142434445464748494a"),
        ]
    )


def _minefield_data_dis6_body() -> bytes:
    return b"".join(
        [
            _entity_id(251, 252, 253),
            _entity_id(254, 255, 256),
            struct.pack(">HBBBBBBI", 257, 200, 3, 2, 2, 2, 0, 0x01020304),
            _entity_type(37, 38, 225, 39, 40, 41, 42),
            bytes.fromhex("3132"),
            bytes.fromhex("4142"),
            struct.pack(">B", 0),
            _vec3f(9.5, 10.5, 11.5),
            _vec3f(12.5, 13.5, 14.5),
        ]
    )


def _gridded_data_dis6_body() -> bytes:
    return b"".join(
        [
            _entity_id(261, 262, 263),
            struct.pack(">HHHHBB", 264, 265, 266, 267, 3, 1),
            _entity_type(43, 44, 840, 45, 46, 47, 48),
            struct.pack(">fff", 0.7, 0.8, 0.9),
            struct.pack(">q", 0x0102030405060708),
            struct.pack(">IBHB", 269, 4, 270, 0),
            bytes.fromhex("5152535455565758595a"),
        ]
    )


def _aggregate_id(site: int, application: int, aggregate_id: int) -> bytes:
    return struct.pack(">HHH", site, application, aggregate_id)


def _aggregate_marking(character_set: int, characters: bytes) -> bytes:
    return struct.pack(">B", character_set) + characters


def _aggregate_state_dis6_body() -> bytes:
    return b"".join(
        [
            _aggregate_id(271, 272, 273),
            struct.pack(">BB", 200, 201),
            _entity_type(49, 50, 840, 51, 52, 53, 54),
            struct.pack(">I", 0x11121314),
            _aggregate_marking(55, bytes(range(31))),
            _vec3f(1.0, 2.0, 3.0),
            struct.pack(">fff", 0.11, 0.22, 0.33),
            _vec3d(100.25, 200.5, 300.75),
            _vec3f(4.0, 5.0, 6.0),
            struct.pack(">HHHH", 1, 0, 1, 1),
            _aggregate_id(281, 282, 283),
            bytes.fromhex("aaee"),
            _entity_type(56, 57, 225, 58, 59, 60, 61),
            _entity_type(62, 63, 124, 64, 65, 66, 67),
            struct.pack(">I", 1),
            bytes.fromhex("6162636465666768"),
        ]
    )


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


def _create_remove_entity_body() -> bytes:
    return b"".join(
        [
            _entity_id(1, 2, 3),
            _entity_id(4, 5, 6),
            struct.pack(">I", 0x01020304),
        ]
    )


def _create_remove_entity_reliable_body() -> bytes:
    return b"".join(
        [
            _entity_id(1, 2, 3),
            _entity_id(4, 5, 6),
            struct.pack(">BHBI", 7, 0, 0, 0x0A0B0C0D),
        ]
    )


def _start_resume_body() -> bytes:
    return b"".join(
        [
            _entity_id(1, 2, 3),
            _entity_id(4, 5, 6),
            struct.pack(">II", 123456, 7890),
            struct.pack(">II", 222222, 3333),
            struct.pack(">I", 0x01020304),
        ]
    )


def _stop_freeze_body() -> bytes:
    return b"".join(
        [
            _entity_id(1, 2, 3),
            _entity_id(4, 5, 6),
            struct.pack(">II", 444444, 5555),
            struct.pack(">BBH", 7, 9, 0),
            struct.pack(">I", 0x0A0B0C0D),
        ]
    )


def _acknowledge_body() -> bytes:
    return b"".join(
        [
            _entity_id(1, 2, 3),
            _entity_id(4, 5, 6),
            struct.pack(">HHI", 11, 12, 0x10203040),
        ]
    )


def _start_resume_reliable_body() -> bytes:
    return b"".join(
        [
            _entity_id(1, 2, 3),
            _entity_id(4, 5, 6),
            struct.pack(">II", 123456, 7890),
            struct.pack(">II", 222222, 3333),
            struct.pack(">BHBI", 5, 0, 0, 0x11121314),
        ]
    )


def _stop_freeze_reliable_body() -> bytes:
    return b"".join(
        [
            _entity_id(1, 2, 3),
            _entity_id(4, 5, 6),
            struct.pack(">II", 444444, 5555),
            struct.pack(">BBBBI", 7, 9, 3, 0, 0x21222324),
        ]
    )


def _action_request_body() -> bytes:
    return b"".join(
        [
            _entity_id(1, 2, 3),
            _entity_id(4, 5, 6),
            struct.pack(">IIII", 0x01020304, 0x11121314, 1, 1),
            bytes.fromhex("00112233445566778899aabbccddeeff"),
        ]
    )


def _action_response_body() -> bytes:
    return b"".join(
        [
            _entity_id(1, 2, 3),
            _entity_id(4, 5, 6),
            struct.pack(">IIII", 0x21222324, 0x31323334, 2, 1),
            bytes.fromhex("ffeeddccbbaa99887766554433221100"),
        ]
    )


def _action_request_reliable_body() -> bytes:
    return b"".join(
        [
            _entity_id(1, 2, 3),
            _entity_id(4, 5, 6),
            struct.pack(">BHBIIII", 5, 0, 0, 0x41424344, 0x51525354, 3, 1),
            bytes.fromhex("01010101020202020303030304040404"),
        ]
    )


def _action_response_reliable_body() -> bytes:
    return b"".join(
        [
            _entity_id(1, 2, 3),
            _entity_id(4, 5, 6),
            struct.pack(">IIII", 0x61626364, 0x71727374, 4, 2),
            bytes.fromhex("0a0b0c0d0e0f10111213141516171819"),
        ]
    )


def _data_query_body() -> bytes:
    return b"".join(
        [
            _entity_id(1, 2, 3),
            _entity_id(4, 5, 6),
            struct.pack(">I", 0x01020304),
            struct.pack(">II", 123456, 7890),
            struct.pack(">II", 1, 2),
            bytes.fromhex("aa00bb11cc22dd33ee44ff5566778899"),
        ]
    )


def _set_data_body() -> bytes:
    return b"".join(
        [
            _entity_id(1, 2, 3),
            _entity_id(4, 5, 6),
            struct.pack(">IIII", 0x11121314, 0, 2, 1),
            bytes.fromhex("101112131415161718191a1b1c1d1e1f"),
        ]
    )


def _data_reliable_body() -> bytes:
    return b"".join(
        [
            _entity_id(1, 2, 3),
            _entity_id(4, 5, 6),
            struct.pack(">IBHBI", 0x31323334, 6, 0, 0, 3),
            struct.pack(">I", 1),
            bytes.fromhex("2122232425262728292a2b2c2d2e2f30"),
        ]
    )


def _data_query_reliable_body() -> bytes:
    return b"".join(
        [
            _entity_id(1, 2, 3),
            _entity_id(4, 5, 6),
            struct.pack(">BHBI", 5, 0, 0, 0x41424344),
            struct.pack(">II", 222222, 3333),
            struct.pack(">II", 2, 1),
            bytes.fromhex("3132333435363738393a3b3c3d3e3f40"),
        ]
    )


def _set_data_reliable_body() -> bytes:
    return b"".join(
        [
            _entity_id(1, 2, 3),
            _entity_id(4, 5, 6),
            struct.pack(">BHBI", 7, 0, 0, 0x51525354),
            struct.pack(">II", 4, 2),
            bytes.fromhex("4142434445464748494a4b4c4d4e4f50"),
        ]
    )


def _event_report_body() -> bytes:
    return b"".join(
        [
            _entity_id(1, 2, 3),
            _entity_id(4, 5, 6),
            struct.pack(">IIII", 0x61626364, 0, 1, 3),
            bytes.fromhex("5152535455565758595a5b5c5d5e5f60"),
        ]
    )


def _comment_body() -> bytes:
    return b"".join(
        [
            _entity_id(1, 2, 3),
            _entity_id(4, 5, 6),
            struct.pack(">II", 2, 2),
            bytes.fromhex("6162636465666768696a6b6c6d6e6f70"),
        ]
    )


def _event_report_reliable_body() -> bytes:
    return b"".join(
        [
            _entity_id(1, 2, 3),
            _entity_id(4, 5, 6),
            struct.pack(">IIII", 0x71727374, 0, 3, 1),
            bytes.fromhex("7172737475767778797a7b7c7d7e7f80"),
        ]
    )


def _designator_body() -> bytes:
    return b"".join(
        [
            _entity_id(1, 2, 3),
            struct.pack(">H", 17),
            _entity_id(4, 5, 6),
            struct.pack(">Hff", 18, 55.5, 1.064),
            _vec3f(7.5, 8.5, 9.5),
            _vec3d(1000.25, 2000.5, 3000.75),
            struct.pack(">BHB", 4, 0, 0),
            _vec3f(0.25, 0.5, 0.75),
        ]
    )


def _transmitter_dis6_body() -> bytes:
    return b"".join(
        [
            _entity_id(1, 2, 3),
            struct.pack(">HBBHBBH", 7, 1, 2, 840, 3, 4, 5),
            struct.pack(">BBH", 6, 8, 0),
            _vec3d(100.5, 200.25, 300.75),
            _vec3f(1.5, 2.5, 3.5),
            struct.pack(">HHIffHHHHHHBHB", 9, 2, 123456789, 25.5, 40.25, 0x0101, 0x0202, 0x0303, 0x0404, 0x0505, 0x0606, 3, 0, 0),
            bytes.fromhex("4142434445464748"),
        ]
    )


def _signal_dis6_body() -> bytes:
    return b"".join(
        [
            _entity_id(1, 2, 3),
            struct.pack(">HHHIHH", 7, 0x0102, 0x0304, 44100, 16, 2),
            bytes.fromhex("0102030405060708"),
        ]
    )


def _transmitter_dis7_body() -> bytes:
    return b"".join(
        [
            _entity_id(4, 5, 6),
            struct.pack(">HBBHBBBB", 11, 1, 2, 840, 3, 4, 5, 6),
            struct.pack(">BBH", 7, 9, 2),
            _vec3d(400.5, 500.25, 600.75),
            _vec3f(4.5, 5.5, 6.5),
            struct.pack(">HHIffHHHHHHBHB", 10, 3, 987654321, 12.75, 18.5, 0x1111, 0x1212, 0x1313, 0x1414, 0x1515, 0x1616, 4, 0, 0),
            bytes.fromhex("5152535455565758"),
        ]
    )


def _signal_dis7_body() -> bytes:
    return b"".join(
        [
            struct.pack(">HHIHH", 0x1112, 0x1314, 22050, 24, 3),
            bytes.fromhex("1112131415161718"),
        ]
    )


def _receiver_dis6_body() -> bytes:
    return b"".join(
        [
            _entity_id(1, 2, 3),
            struct.pack(">HHHf", 9, 5, 0, 12.5),
            _entity_id(4, 5, 6),
            struct.pack(">H", 10),
        ]
    )


def _receiver_dis7_body() -> bytes:
    return b"".join(
        [
            struct.pack(">HHf", 6, 0, 7.25),
            _entity_id(4, 5, 6),
            struct.pack(">H", 11),
        ]
    )


def _intercom_signal_dis6_body() -> bytes:
    return b"".join(
        [
            _entity_id(1, 2, 3),
            struct.pack(">HHHIHH", 12, 0x2122, 0x2324, 16000, 12, 1),
            bytes.fromhex("2122232425262728"),
        ]
    )


def _intercom_signal_dis7_body() -> bytes:
    return b"".join(
        [
            _entity_id(1, 2, 3),
            struct.pack(">HHHIHH", 13, 0x3132, 0x3334, 8000, 8, 1),
            bytes.fromhex("3132333435363738"),
        ]
    )


def _intercom_control_body() -> bytes:
    return b"".join(
        [
            struct.pack(">BB", 5, 6),
            _entity_id(1, 2, 3),
            struct.pack(">BBBBB", 7, 8, 9, 10, 11),
            _entity_id(4, 5, 6),
            struct.pack(">HI", 12, 2),
            bytes.fromhex("4142434445464748"),
        ]
    )


def _sees_body() -> bytes:
    return b"".join(
        [
            _entity_id(1, 2, 3),
            struct.pack(">HHHHH", 10, 11, 12, 2, 1),
            struct.pack(">ff", 0.25, 1100.5),
            struct.pack(">ff", 0.5, 2200.75),
            struct.pack(">ff", 1.25, -2.5),
        ]
    )


def _electromagnetic_emission_dis6_body() -> bytes:
    return b"".join(
        [
            _entity_id(1, 2, 3),
            _event_id(4, 5, 6),
            struct.pack(">BBH", 7, 2, 0),
            bytes.fromhex("0102030405060708"),
        ]
    )


def _electromagnetic_emission_dis7_body() -> bytes:
    return b"".join(
        [
            _entity_id(1, 2, 3),
            _event_id(4, 5, 6),
            struct.pack(">BBHBBHBB", 8, 3, 0, 9, 10, 0x1112, 13, 14),
            _vec3f(15.5, 16.5, 17.5),
            bytes.fromhex("2122232425262728"),
        ]
    )


def _iff_atc_navaids_dis6_body() -> bytes:
    return b"".join(
        [
            _entity_id(1, 2, 3),
            _event_id(4, 5, 6),
            _vec3f(7.5, 8.5, 9.5),
            struct.pack(">HHBB", 10, 11, 12, 13),
            struct.pack(">HBBBBHHHHHH", 0, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23),
        ]
    )


def _underwater_acoustic_body() -> bytes:
    return b"".join(
        [
            _entity_id(1, 2, 3),
            _event_id(4, 5, 6),
            struct.pack(">BBHBBBB", 7, 0, 8, 9, 1, 2, 1),
            struct.pack(">hhf", 100, 120, 1.5),
            struct.pack(">Hh", 13, -14),
            struct.pack(">Hh", 15, -16),
            bytes.fromhex("3132333435363738"),
        ]
    )


def _set_record_reliable_body() -> bytes:
    return b"".join(
        [
            _entity_id(1, 2, 3),
            _entity_id(4, 5, 6),
            struct.pack(">IBHBI", 0x81828384, 8, 0, 0, 2),
            bytes.fromhex("8182838485868788898a8b8c8d8e8f90"),
        ]
    )


def _record_reliable_body() -> bytes:
    return b"".join(
        [
            _entity_id(1, 2, 3),
            _entity_id(4, 5, 6),
            struct.pack(">IBBHI", 0x71727374, 7, 0, 0x0102, 2),
            bytes.fromhex("7172737475767778797a7b7c7d7e7f80"),
        ]
    )


def _record_query_reliable_body() -> bytes:
    return b"".join(
        [
            _entity_id(1, 2, 3),
            _entity_id(4, 5, 6),
            struct.pack(">IBHBI", 0x91929394, 9, 0, 0, 0xA1A2A3A4),
            struct.pack(">II", 654321, 9876),
            struct.pack(">I", 3),
            bytes.fromhex("9192939495969798999a9b9c9d9e9fa0"),
        ]
    )


def _information_operations_action_dis7_body() -> bytes:
    return b"".join(
        [
            _entity_id(1, 2, 3),
            _entity_id(4, 5, 6),
            struct.pack(">IHHHHI", 0x21222324, 11, 12, 13, 14, 0x31323334),
            _entity_id(7, 8, 9),
            _entity_id(10, 11, 12),
            struct.pack(">HH", 0, 2),
            bytes.fromhex("4142434445464748494a4b4c4d4e4f50"),
        ]
    )


def _information_operations_report_dis7_body() -> bytes:
    return b"".join(
        [
            _entity_id(21, 22, 23),
            struct.pack(">HBB", 31, 32, 0),
            _entity_id(24, 25, 26),
            _entity_id(27, 28, 29),
            struct.pack(">HHH", 0, 0, 2),
            bytes.fromhex("5152535455565758595a5b5c5d5e5f60"),
        ]
    )


def _live_entity_tspi_body() -> bytes:
    return b"".join(
        [
            _entity_id(1, 2, 3),
            struct.pack(">B", 7),
            bytes.fromhex("6162636465666768696a6b6c6d6e6f70"),
        ]
    )


def _live_entity_appearance_body() -> bytes:
    return b"".join(
        [
            _entity_id(4, 5, 6),
            struct.pack(">HB", 0x3132, 9),
            bytes.fromhex("7172737475767778797a7b7c7d7e7f80"),
        ]
    )


def _live_entity_articulated_parts_body() -> bytes:
    return b"".join(
        [
            _entity_id(7, 8, 9),
            struct.pack(">B", 2),
            bytes.fromhex("8182838485868788898a8b8c8d8e8f90"),
        ]
    )


def _live_entity_fire_body() -> bytes:
    return b"".join(
        [
            _entity_id(10, 11, 12),
            struct.pack(">B", 3),
            _entity_id(13, 14, 15),
            _entity_id(16, 17, 18),
            _event_id(19, 20, 21),
            bytes.fromhex("9192939495969798999a9b9c9d9e9fa0"),
        ]
    )


def _live_entity_detonation_body() -> bytes:
    return b"".join(
        [
            _entity_id(22, 23, 24),
            struct.pack(">BB", 4, 5),
            _entity_id(25, 26, 27),
            _entity_id(28, 29, 30),
            _event_id(31, 32, 33),
            bytes.fromhex("a1a2a3a4a5a6a7a8a9aaabacadaeafb0"),
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


def _entity_damage_status_body() -> bytes:
    return b"".join(
        [
            _entity_id(1, 2, 3),
            _entity_id(4, 5, 6),
            _entity_id(7, 8, 9),
            struct.pack(">HHH", 0, 0, 2),
            bytes.fromhex("deadbeef00112233445566778899aabb"),
        ]
    )


def _attribute_dis7_body() -> bytes:
    return b"".join(
        [
            _simulation_address(301, 302),
            struct.pack(">I", 0x01020304),
            struct.pack(">H", 0x0506),
            struct.pack(">BB", 43, 7),
            struct.pack(">I", 0x11121314),
            struct.pack(">B", 9),
            struct.pack(">b", -1),
            struct.pack(">H", 2),
            bytes.fromhex("a1a2a3a4a5a6a7a8"),
        ]
    )


def _body_for_descriptor(descriptor: object) -> bytes:
    protocol_version = descriptor.protocol_version
    pdu_type = descriptor.pdu_type
    if (protocol_version, pdu_type) in {(6, 5), (7, 5)}:
        return _service_request_body()
    if (protocol_version, pdu_type) in {(6, 6), (6, 7), (7, 6), (7, 7)}:
        return _resupply_offer_or_received_body()
    if (protocol_version, pdu_type) in {(6, 8), (7, 8)}:
        return _resupply_cancel_body()
    if (protocol_version, pdu_type) in {(6, 9), (7, 9)}:
        return _repair_complete_body()
    if (protocol_version, pdu_type) in {(6, 10), (7, 10)}:
        return _repair_response_body()
    if (protocol_version, pdu_type) == (6, 43):
        return _point_object_state_dis6_body()
    if (protocol_version, pdu_type) == (7, 43):
        return _point_object_state_dis7_body()
    if (protocol_version, pdu_type) == (6, 44):
        return _linear_object_state_dis6_body()
    if (protocol_version, pdu_type) == (7, 44):
        return _linear_object_state_dis7_body()
    if (protocol_version, pdu_type) == (6, 45):
        return _areal_object_state_dis6_body()
    if (protocol_version, pdu_type) == (7, 45):
        return _areal_object_state_dis7_body()
    if (protocol_version, pdu_type) in {(6, 36), (7, 36)}:
        return _is_part_of_body()
    if (protocol_version, pdu_type) in {(6, 33), (7, 33)}:
        return _aggregate_state_dis6_body()
    if (protocol_version, pdu_type) in {(6, 35), (7, 35)}:
        return _transfer_control_body()
    if (protocol_version, pdu_type) in {(6, 34), (7, 34)}:
        return _is_group_of_dis6_body()
    if (protocol_version, pdu_type) == (6, 37):
        return _minefield_state_dis6_body()
    if (protocol_version, pdu_type) in {(6, 38), (7, 38)}:
        return _minefield_query_body()
    if (protocol_version, pdu_type) in {(6, 39), (7, 39)}:
        return _minefield_data_dis6_body()
    if (protocol_version, pdu_type) in {(6, 40), (7, 40)}:
        return _minefield_response_nack_body()
    if (protocol_version, pdu_type) in {(6, 41), (7, 41)}:
        return _environmental_process_body()
    if (protocol_version, pdu_type) in {(6, 42), (7, 42)}:
        return _gridded_data_dis6_body()
    if (protocol_version, pdu_type) == (7, 37):
        return _minefield_state_dis7_body()
    if (protocol_version, pdu_type) == (7, 72):
        return _attribute_dis7_body()
    if (protocol_version, pdu_type) == (7, 70):
        return _information_operations_action_dis7_body()
    if (protocol_version, pdu_type) == (7, 71):
        return _information_operations_report_dis7_body()
    if (protocol_version, pdu_type) in {(6, 46), (7, 46)}:
        return _live_entity_tspi_body()
    if (protocol_version, pdu_type) in {(6, 47), (7, 47)}:
        return _live_entity_appearance_body()
    if (protocol_version, pdu_type) in {(6, 48), (7, 48)}:
        return _live_entity_articulated_parts_body()
    if (protocol_version, pdu_type) in {(6, 49), (7, 49)}:
        return _live_entity_fire_body()
    if (protocol_version, pdu_type) in {(6, 50), (7, 50)}:
        return _live_entity_detonation_body()
    if (protocol_version, pdu_type) in {(6, 11), (6, 12), (7, 11), (7, 12)}:
        return _create_remove_entity_body()
    if (protocol_version, pdu_type) in {(6, 13), (7, 13)}:
        return _start_resume_body()
    if (protocol_version, pdu_type) in {(6, 14), (7, 14)}:
        return _stop_freeze_body()
    if (protocol_version, pdu_type) in {(6, 15), (7, 15)}:
        return _acknowledge_body()
    if (protocol_version, pdu_type) in {(6, 16), (7, 16)}:
        return _action_request_body()
    if (protocol_version, pdu_type) in {(6, 17), (7, 17)}:
        return _action_response_body()
    if (protocol_version, pdu_type) in {(6, 18), (7, 18)}:
        return _data_query_body()
    if (protocol_version, pdu_type) in {(6, 19), (6, 20), (7, 19), (7, 20)}:
        return _set_data_body()
    if (protocol_version, pdu_type) in {(6, 21), (7, 21)}:
        return _event_report_body()
    if (protocol_version, pdu_type) in {(6, 22), (7, 22), (6, 62), (7, 62)}:
        return _comment_body()
    if (protocol_version, pdu_type) in {(6, 24), (7, 24)}:
        return _designator_body()
    if (protocol_version, pdu_type) == (6, 25):
        return _transmitter_dis6_body()
    if (protocol_version, pdu_type) == (6, 26):
        return _signal_dis6_body()
    if (protocol_version, pdu_type) == (7, 25):
        return _transmitter_dis7_body()
    if (protocol_version, pdu_type) == (7, 26):
        return _signal_dis7_body()
    if (protocol_version, pdu_type) == (6, 27):
        return _receiver_dis6_body()
    if (protocol_version, pdu_type) == (7, 27):
        return _receiver_dis7_body()
    if (protocol_version, pdu_type) == (6, 31):
        return _intercom_signal_dis6_body()
    if (protocol_version, pdu_type) == (7, 31):
        return _intercom_signal_dis7_body()
    if (protocol_version, pdu_type) in {(6, 32), (7, 32)}:
        return _intercom_control_body()
    if (protocol_version, pdu_type) in {(6, 30), (7, 30)}:
        return _sees_body()
    if (protocol_version, pdu_type) == (6, 23):
        return _electromagnetic_emission_dis6_body()
    if (protocol_version, pdu_type) == (7, 23):
        return _electromagnetic_emission_dis7_body()
    if (protocol_version, pdu_type) == (6, 28):
        return _iff_atc_navaids_dis6_body()
    if (protocol_version, pdu_type) in {(6, 29), (7, 29)}:
        return _underwater_acoustic_body()
    if (protocol_version, pdu_type) in {(6, 51), (6, 52), (7, 51), (7, 52)}:
        return _create_remove_entity_reliable_body()
    if (protocol_version, pdu_type) in {(6, 53), (7, 53)}:
        return _start_resume_reliable_body()
    if (protocol_version, pdu_type) in {(6, 54), (7, 54)}:
        return _stop_freeze_reliable_body()
    if (protocol_version, pdu_type) in {(6, 55), (7, 55)}:
        return _acknowledge_body()
    if (protocol_version, pdu_type) in {(6, 56), (7, 56)}:
        return _action_request_reliable_body()
    if (protocol_version, pdu_type) in {(6, 57), (7, 57)}:
        return _action_response_reliable_body()
    if (protocol_version, pdu_type) in {(6, 58), (7, 58)}:
        return _data_query_reliable_body()
    if (protocol_version, pdu_type) in {(6, 59), (7, 59)}:
        return _set_data_reliable_body()
    if (protocol_version, pdu_type) in {(6, 60), (7, 60)}:
        return _data_reliable_body()
    if (protocol_version, pdu_type) in {(6, 61), (7, 61)}:
        return _event_report_reliable_body()
    if (protocol_version, pdu_type) in {(6, 63), (7, 63)}:
        return _record_reliable_body()
    if (protocol_version, pdu_type) == (6, 64):
        return _set_record_reliable_body()
    if (protocol_version, pdu_type) == (7, 64):
        return _set_record_reliable_body()
    if (protocol_version, pdu_type) in {(6, 65), (7, 65)}:
        return _record_query_reliable_body()
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
    if (protocol_version, pdu_type) == (7, 69):
        return _entity_damage_status_body()
    if (protocol_version, pdu_type) == (7, 1):
        return b"\x00" * 132
    return b"\x01\x02"


def test_semantic_parser_manifest_has_141_entry_points() -> None:
    manifest = _ensure_manifest()
    summary = manifest["summary"]
    assert summary["records"] == 141
    assert summary["semantic_parsers"] == 141
    assert summary["semantic_observation"] == 0
    assert summary["semantic_prefix"] == 0
    assert summary["semantic_decoded"] == 141
    assert summary["fully_domain_decoded"] == 141
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
    assert designator.semantic_level == "semantic_decoded"
    assert designator.descriptor.fully_domain_decoded
    assert designator.semantic_fields["standard_name"] == "Designator"
    assert designator.semantic_fields["raw_body"] == b"abc"
    assert designator.semantic_fields["semantic_decode_status"] == "decode_error"
    assert designator.semantic_fields["semantic_decode_error_type"] == "error"
    assert any("semantic decoder failed" in item for item in designator.diagnostics)


def test_other_rows_expose_opaque_payload_only() -> None:
    other = fastdis.parse_semantic_pdu(_packet(6, 0, 0, body=b"\xaa\xbb\xcc"))
    assert other is not None
    assert other.semantic_level == "semantic_decoded"
    assert other.descriptor.fully_domain_decoded
    assert other.semantic_fields["opaque_payload_bytes"] == b"\xaa\xbb\xcc"

    other_dis7 = fastdis.parse_semantic_pdu(_packet(7, 0, 0, body=b"\x11\x22"))
    assert other_dis7 is not None
    assert other_dis7.semantic_level == "semantic_decoded"
    assert other_dis7.semantic_fields["opaque_payload_bytes"] == b"\x11\x22"


def test_remaining_semantic_observation_rows_are_only_schema_gap_or_enum_only_lanes() -> None:
    manifest = _ensure_manifest()
    observation_rows = [
        record
        for record in manifest["records"]
        if record["semantic_level"] == "semantic_observation"
    ]

    assert observation_rows == []


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


def test_intercom_control_rows_expose_decoded_semantic_fields() -> None:
    intercom_control = fastdis.parse_semantic_pdu(_packet(7, 32, 4, body=_intercom_control_body()))
    assert intercom_control is not None
    assert intercom_control.semantic_level == "semantic_decoded"
    assert intercom_control.descriptor.fully_domain_decoded
    assert intercom_control.semantic_fields["semantic_decode_status"] == "decoded"
    assert intercom_control.semantic_fields["control_type"] == 5
    assert intercom_control.semantic_fields["communications_channel_type"] == 6
    assert intercom_control.semantic_fields["source_entity_id"] == {"site": 1, "application": 2, "entity": 3}
    assert intercom_control.semantic_fields["source_communications_device_id"] == 7
    assert intercom_control.semantic_fields["source_line_id"] == 8
    assert intercom_control.semantic_fields["transmit_priority"] == 9
    assert intercom_control.semantic_fields["transmit_line_state"] == 10
    assert intercom_control.semantic_fields["command"] == 11
    assert intercom_control.semantic_fields["master_entity_id"] == {"site": 4, "application": 5, "entity": 6}
    assert intercom_control.semantic_fields["master_communications_device_id"] == 12
    assert intercom_control.semantic_fields["intercom_parameters_length"] == 2
    assert intercom_control.semantic_fields["intercom_parameters_bytes"] == bytes.fromhex("4142434445464748")
    assert intercom_control.diagnostics == ("full domain decode available",)


def test_sees_rows_expose_decoded_semantic_fields() -> None:
    sees = fastdis.parse_semantic_pdu(_packet(7, 30, 6, body=_sees_body()))
    assert sees is not None
    assert sees.semantic_level == "semantic_decoded"
    assert sees.descriptor.fully_domain_decoded
    assert sees.semantic_fields["semantic_decode_status"] == "decoded"
    assert sees.semantic_fields["orginating_entity_id"] == {"site": 1, "application": 2, "entity": 3}
    assert sees.semantic_fields["infrared_signature_representation_index"] == 10
    assert sees.semantic_fields["acoustic_signature_representation_index"] == 11
    assert sees.semantic_fields["radar_cross_section_signature_representation_index"] == 12
    assert sees.semantic_fields["number_of_propulsion_systems"] == 2
    assert sees.semantic_fields["number_of_vectoring_nozzle_systems"] == 1
    assert sees.semantic_fields["propulsion_system_data"] == (
        {"power_setting": 0.25, "engine_rpm": 1100.5},
        {"power_setting": 0.5, "engine_rpm": 2200.75},
    )
    assert sees.semantic_fields["vectoring_system_data"] == (
        {"horizontal_deflection_angle": 1.25, "vertical_deflection_angle": -2.5},
    )
    assert sees.diagnostics == ("full domain decode available",)


def test_electromagnetic_emission_rows_expose_decoded_semantic_fields() -> None:
    emission = fastdis.parse_semantic_pdu(_packet(7, 23, 6, body=_electromagnetic_emission_dis7_body()))
    assert emission is not None
    assert emission.semantic_level == "semantic_decoded"
    assert emission.descriptor.fully_domain_decoded
    assert emission.semantic_fields["semantic_decode_status"] == "decoded"
    assert emission.semantic_fields["emitting_entity_id"] == {"site": 1, "application": 2, "entity": 3}
    assert emission.semantic_fields["event_id"] == {"site": 4, "application": 5, "event_number": 6}
    assert emission.semantic_fields["state_update_indicator"] == 8
    assert emission.semantic_fields["number_of_systems"] == 3
    assert emission.semantic_fields["padding_for_emissions_pdu"] == 0
    assert emission.semantic_fields["system_data_length"] == 9
    assert emission.semantic_fields["number_of_beams"] == 10
    assert emission.semantic_fields["emitter_system"] == {
        "emitter_name": 0x1112,
        "emitter_function": 13,
        "emitter_id_number": 14,
    }
    assert emission.semantic_fields["location"] == {"x": 15.5, "y": 16.5, "z": 17.5}
    assert emission.semantic_fields["systems_bytes"] == bytes.fromhex("2122232425262728")
    assert emission.diagnostics == ("full domain decode available",)


def test_iff_atc_navaids_dis6_rows_expose_decoded_semantic_fields() -> None:
    iff = fastdis.parse_semantic_pdu(_packet(6, 28, 6, body=_iff_atc_navaids_dis6_body()))
    assert iff is not None
    assert iff.semantic_level == "semantic_decoded"
    assert iff.descriptor.fully_domain_decoded
    assert iff.semantic_fields["semantic_decode_status"] == "decoded"
    assert iff.semantic_fields["emitting_entity_id"] == {"site": 1, "application": 2, "entity": 3}
    assert iff.semantic_fields["event_id"] == {"site": 4, "application": 5, "event_number": 6}
    assert iff.semantic_fields["location"] == {"x": 7.5, "y": 8.5, "z": 9.5}
    assert iff.semantic_fields["system_id"] == {
        "system_type": 10,
        "system_name": 11,
        "system_mode": 12,
        "change_options": 13,
    }
    assert iff.semantic_fields["pad2"] == 0
    assert iff.semantic_fields["fundamental_parameters"] == {
        "system_status": 14,
        "alternate_parameter4": 15,
        "information_layers": 16,
        "modifier": 17,
        "parameter1": 18,
        "parameter2": 19,
        "parameter3": 20,
        "parameter4": 21,
        "parameter5": 22,
        "parameter6": 23,
    }
    assert iff.diagnostics == ("full domain decode available",)


def test_iff_dis7_rows_expose_decoded_semantic_fields() -> None:
    iff = fastdis.parse_semantic_pdu(_packet(7, 28, 6, body=_iff_atc_navaids_dis6_body()))
    assert iff is not None
    assert iff.semantic_level == "semantic_decoded"
    assert iff.descriptor.fully_domain_decoded
    assert iff.semantic_fields["semantic_decode_status"] == "decoded"
    assert iff.semantic_fields["emitting_entity_id"] == {"site": 1, "application": 2, "entity": 3}
    assert iff.semantic_fields["event_id"] == {"site": 4, "application": 5, "event_number": 6}
    assert iff.semantic_fields["location"] == {"x": 7.5, "y": 8.5, "z": 9.5}
    assert iff.semantic_fields["system_id"] == {
        "system_type": 10,
        "system_name": 11,
        "system_mode": 12,
        "change_options": 13,
    }
    assert iff.semantic_fields["pad2"] == 0
    assert iff.semantic_fields["fundamental_parameters"] == {
        "system_status": 14,
        "data_field1": 15,
        "information_layers": 16,
        "data_field2": 17,
        "parameter1": 18,
        "parameter2": 19,
        "parameter3": 20,
        "parameter4": 21,
        "parameter5": 22,
        "parameter6": 23,
    }
    assert iff.diagnostics == ("full domain decode available",)


def test_service_request_rows_expose_decoded_logistics_fields() -> None:
    request = fastdis.parse_semantic_pdu(_packet(7, 5, 3, body=_service_request_body()))
    assert request is not None
    assert request.semantic_level == "semantic_decoded"
    assert request.descriptor.fully_domain_decoded
    assert request.semantic_fields["requesting_entity_id"] == {"site": 1, "application": 2, "entity": 3}
    assert request.semantic_fields["servicing_entity_id"] == {"site": 4, "application": 5, "entity": 6}
    assert request.semantic_fields["service_type_requested"] == 7
    assert request.semantic_fields["number_of_supply_types"] == 2
    assert request.semantic_fields["service_request_padding"] == 0
    assert request.semantic_fields["supplies"] == (
        {"supply_type": {"kind": 1, "domain": 2, "country": 225, "category": 3, "subcategory": 4, "specific": 5, "extra": 6}, "quantity": 10.5},
        {"supply_type": {"kind": 2, "domain": 3, "country": 840, "category": 7, "subcategory": 8, "specific": 9, "extra": 10}, "quantity": 20.25},
    )


def test_resupply_offer_rows_expose_decoded_logistics_fields() -> None:
    offer = fastdis.parse_semantic_pdu(_packet(6, 6, 3, body=_resupply_offer_or_received_body()))
    assert offer is not None
    assert offer.semantic_level == "semantic_decoded"
    assert offer.descriptor.fully_domain_decoded
    assert offer.semantic_fields["receiving_entity_id"] == {"site": 11, "application": 12, "entity": 13}
    assert offer.semantic_fields["supplying_entity_id"] == {"site": 14, "application": 15, "entity": 16}
    assert offer.semantic_fields["number_of_supply_types"] == 2
    assert offer.semantic_fields["padding1"] == 0
    assert offer.semantic_fields["padding2"] == 0
    assert offer.semantic_fields["supplies"] == (
        {"supply_type": {"kind": 3, "domain": 4, "country": 124, "category": 11, "subcategory": 12, "specific": 13, "extra": 14}, "quantity": 30.5},
        {"supply_type": {"kind": 4, "domain": 5, "country": 826, "category": 15, "subcategory": 16, "specific": 17, "extra": 18}, "quantity": 40.75},
    )


def test_resupply_received_rows_expose_decoded_logistics_fields() -> None:
    received = fastdis.parse_semantic_pdu(_packet(7, 7, 3, body=_resupply_offer_or_received_body()))
    assert received is not None
    assert received.semantic_level == "semantic_decoded"
    assert received.descriptor.fully_domain_decoded
    assert received.semantic_fields["receiving_entity_id"] == {"site": 11, "application": 12, "entity": 13}
    assert received.semantic_fields["supplying_entity_id"] == {"site": 14, "application": 15, "entity": 16}
    assert received.semantic_fields["number_of_supply_types"] == 2
    assert received.semantic_fields["padding1"] == 0
    assert received.semantic_fields["padding2"] == 0


def test_resupply_cancel_rows_expose_decoded_logistics_fields() -> None:
    cancel = fastdis.parse_semantic_pdu(_packet(6, 8, 3, body=_resupply_cancel_body()))
    assert cancel is not None
    assert cancel.semantic_level == "semantic_decoded"
    assert cancel.descriptor.fully_domain_decoded
    assert cancel.semantic_fields["receiving_entity_id"] == {"site": 21, "application": 22, "entity": 23}
    assert cancel.semantic_fields["supplying_entity_id"] == {"site": 24, "application": 25, "entity": 26}

    cancel_dis7 = fastdis.parse_semantic_pdu(_packet(7, 8, 3, body=_resupply_cancel_body()))
    assert cancel_dis7 is not None
    assert cancel_dis7.semantic_level == "semantic_decoded"
    assert cancel_dis7.descriptor.fully_domain_decoded
    assert cancel_dis7.semantic_fields["receiving_entity_id"] == cancel.semantic_fields["receiving_entity_id"]
    assert cancel_dis7.semantic_fields["supplying_entity_id"] == cancel.semantic_fields["supplying_entity_id"]


def test_repair_complete_rows_expose_decoded_logistics_fields() -> None:
    repair_complete = fastdis.parse_semantic_pdu(_packet(7, 9, 3, body=_repair_complete_body()))
    assert repair_complete is not None
    assert repair_complete.semantic_level == "semantic_decoded"
    assert repair_complete.descriptor.fully_domain_decoded
    assert repair_complete.semantic_fields["receiving_entity_id"] == {"site": 31, "application": 32, "entity": 33}
    assert repair_complete.semantic_fields["repairing_entity_id"] == {"site": 34, "application": 35, "entity": 36}
    assert repair_complete.semantic_fields["repair"] == 37
    assert repair_complete.semantic_fields["padding"] == 0


def test_repair_response_rows_expose_decoded_logistics_fields() -> None:
    repair_response = fastdis.parse_semantic_pdu(_packet(7, 10, 3, body=_repair_response_body()))
    assert repair_response is not None
    assert repair_response.semantic_level == "semantic_decoded"
    assert repair_response.descriptor.fully_domain_decoded
    assert repair_response.semantic_fields["receiving_entity_id"] == {"site": 41, "application": 42, "entity": 43}
    assert repair_response.semantic_fields["repairing_entity_id"] == {"site": 44, "application": 45, "entity": 46}
    assert repair_response.semantic_fields["repair_result"] == 47
    assert repair_response.semantic_fields["padding1"] == 0
    assert repair_response.semantic_fields["padding2"] == 0


def test_is_part_of_rows_expose_decoded_entity_management_fields() -> None:
    is_part_of_dis6 = fastdis.parse_semantic_pdu(_packet(6, 36, 7, body=_is_part_of_body()))
    assert is_part_of_dis6 is not None
    assert is_part_of_dis6.semantic_level == "semantic_decoded"
    assert is_part_of_dis6.descriptor.fully_domain_decoded
    assert is_part_of_dis6.semantic_fields["originating_entity_id"] == {"site": 171, "application": 172, "entity": 173}
    assert is_part_of_dis6.semantic_fields["receiving_entity_id"] == {"site": 174, "application": 175, "entity": 176}
    assert is_part_of_dis6.semantic_fields["relationship"] == {"nature": 177, "position": 178}
    assert is_part_of_dis6.semantic_fields["part_location"] == {"x": 1.25, "y": 2.5, "z": 3.75}
    assert is_part_of_dis6.semantic_fields["named_location_id"] == {"station_name": 179, "station_number": 180}
    assert is_part_of_dis6.semantic_fields["part_entity_type"] == {"kind": 5, "domain": 6, "country": 225, "category": 7, "subcategory": 8, "specific": 9, "extra": 10}

    is_part_of_dis7 = fastdis.parse_semantic_pdu(_packet(7, 36, 7, body=_is_part_of_body()))
    assert is_part_of_dis7 is not None
    assert is_part_of_dis7.semantic_level == "semantic_decoded"
    assert is_part_of_dis7.descriptor.fully_domain_decoded
    assert is_part_of_dis7.semantic_fields["originating_entity_id"] == is_part_of_dis6.semantic_fields["originating_entity_id"]
    assert is_part_of_dis7.semantic_fields["receiving_entity_id"] == is_part_of_dis6.semantic_fields["receiving_entity_id"]
    assert is_part_of_dis7.semantic_fields["relationship"] == is_part_of_dis6.semantic_fields["relationship"]
    assert is_part_of_dis7.semantic_fields["part_location"] == is_part_of_dis6.semantic_fields["part_location"]
    assert is_part_of_dis7.semantic_fields["named_location_id"] == is_part_of_dis6.semantic_fields["named_location_id"]
    assert is_part_of_dis7.semantic_fields["part_entity_type"] == is_part_of_dis6.semantic_fields["part_entity_type"]


def test_minefield_response_nack_rows_expose_decoded_minefield_fields() -> None:
    nack_dis6 = fastdis.parse_semantic_pdu(_packet(6, 40, 8, body=_minefield_response_nack_body()))
    assert nack_dis6 is not None
    assert nack_dis6.semantic_level == "semantic_decoded"
    assert nack_dis6.descriptor.fully_domain_decoded
    assert nack_dis6.semantic_fields["minefield_id"] == {"site": 181, "application": 182, "entity": 183}
    assert nack_dis6.semantic_fields["requesting_entity_id"] == {"site": 184, "application": 185, "entity": 186}
    assert nack_dis6.semantic_fields["request_id"] == 187
    assert nack_dis6.semantic_fields["number_of_missing_pdus"] == 2
    assert nack_dis6.semantic_fields["missing_pdu_sequence_numbers"] == (
        bytes.fromhex("0102030405060708"),
        bytes.fromhex("1112131415161718"),
    )

    nack_dis7 = fastdis.parse_semantic_pdu(_packet(7, 40, 8, body=_minefield_response_nack_body()))
    assert nack_dis7 is not None
    assert nack_dis7.semantic_level == "semantic_decoded"
    assert nack_dis7.descriptor.fully_domain_decoded
    assert nack_dis7.semantic_fields["minefield_id"] == nack_dis6.semantic_fields["minefield_id"]
    assert nack_dis7.semantic_fields["requesting_entity_id"] == nack_dis6.semantic_fields["requesting_entity_id"]
    assert nack_dis7.semantic_fields["request_id"] == nack_dis6.semantic_fields["request_id"]
    assert nack_dis7.semantic_fields["number_of_missing_pdus"] == nack_dis6.semantic_fields["number_of_missing_pdus"]
    assert nack_dis7.semantic_fields["missing_pdu_sequence_numbers"] == nack_dis6.semantic_fields["missing_pdu_sequence_numbers"]


def test_transfer_control_rows_expose_decoded_entity_management_fields() -> None:
    transfer = fastdis.parse_semantic_pdu(_packet(6, 35, 7, body=_transfer_control_body()))
    assert transfer is not None
    assert transfer.semantic_level == "semantic_decoded"
    assert transfer.descriptor.fully_domain_decoded
    assert transfer.semantic_fields["originating_entity_id"] == {"site": 191, "application": 192, "entity": 193}
    assert transfer.semantic_fields["receiving_entity_id"] == {"site": 194, "application": 195, "entity": 196}
    assert transfer.semantic_fields["request_id"] == 0xA1A2A3A4
    assert transfer.semantic_fields["required_reliability_service"] == 7
    assert transfer.semantic_fields["transfer_type"] == 8
    assert transfer.semantic_fields["transfer_entity_id"] == {"site": 197, "application": 198, "entity": 199}
    assert transfer.semantic_fields["number_of_record_sets"] == 2
    assert transfer.semantic_fields["record_sets_bytes"] == bytes.fromhex("0102030405060708090a0b0c")

    transfer_dis7 = fastdis.parse_semantic_pdu(_packet(7, 35, 7, body=_transfer_control_body()))
    assert transfer_dis7 is not None
    assert transfer_dis7.semantic_level == "semantic_decoded"
    assert transfer_dis7.descriptor.fully_domain_decoded
    assert transfer_dis7.semantic_fields["originating_entity_id"] == transfer.semantic_fields["originating_entity_id"]
    assert transfer_dis7.semantic_fields["receiving_entity_id"] == transfer.semantic_fields["receiving_entity_id"]
    assert transfer_dis7.semantic_fields["request_id"] == transfer.semantic_fields["request_id"]
    assert transfer_dis7.semantic_fields["required_reliability_service"] == transfer.semantic_fields["required_reliability_service"]
    assert transfer_dis7.semantic_fields["transfer_type"] == transfer.semantic_fields["transfer_type"]
    assert transfer_dis7.semantic_fields["transfer_entity_id"] == transfer.semantic_fields["transfer_entity_id"]
    assert transfer_dis7.semantic_fields["number_of_record_sets"] == transfer.semantic_fields["number_of_record_sets"]
    assert transfer_dis7.semantic_fields["record_sets_bytes"] == transfer.semantic_fields["record_sets_bytes"]


def test_aggregate_state_dis6_rows_expose_decoded_entity_management_fields() -> None:
    aggregate = fastdis.parse_semantic_pdu(_packet(6, 33, 7, body=_aggregate_state_dis6_body()))
    assert aggregate is not None
    assert aggregate.semantic_level == "semantic_decoded"
    assert aggregate.descriptor.fully_domain_decoded
    assert aggregate.semantic_fields["aggregate_id"] == {"site": 271, "application": 272, "aggregate_id": 273}
    assert aggregate.semantic_fields["force_id"] == 200
    assert aggregate.semantic_fields["aggregate_state"] == 201
    assert aggregate.semantic_fields["aggregate_type"] == {"kind": 49, "domain": 50, "country": 840, "category": 51, "subcategory": 52, "specific": 53, "extra": 54}
    assert aggregate.semantic_fields["formation"] == 0x11121314
    assert aggregate.semantic_fields["aggregate_marking"] == {"character_set": 55, "characters": bytes(range(31))}
    assert aggregate.semantic_fields["dimensions"] == {"x": 1.0, "y": 2.0, "z": 3.0}
    assert abs(aggregate.semantic_fields["orientation"]["psi"] - 0.11) < 1e-6
    assert abs(aggregate.semantic_fields["orientation"]["theta"] - 0.22) < 1e-6
    assert abs(aggregate.semantic_fields["orientation"]["phi"] - 0.33) < 1e-6
    assert aggregate.semantic_fields["center_of_mass"] == {"x": 100.25, "y": 200.5, "z": 300.75}
    assert aggregate.semantic_fields["velocity"] == {"x": 4.0, "y": 5.0, "z": 6.0}
    assert aggregate.semantic_fields["number_of_dis_aggregates"] == 1
    assert aggregate.semantic_fields["number_of_dis_entities"] == 0
    assert aggregate.semantic_fields["number_of_silent_aggregate_types"] == 1
    assert aggregate.semantic_fields["number_of_silent_entity_types"] == 1
    assert aggregate.semantic_fields["aggregate_id_list"] == ({"site": 281, "application": 282, "aggregate_id": 283},)
    assert aggregate.semantic_fields["entity_id_list"] == ()
    assert aggregate.semantic_fields["pad2_bytes"] == bytes.fromhex("aaee")
    assert aggregate.semantic_fields["silent_aggregate_system_list"] == ({"kind": 56, "domain": 57, "country": 225, "category": 58, "subcategory": 59, "specific": 60, "extra": 61},)
    assert aggregate.semantic_fields["silent_entity_system_list"] == ({"kind": 62, "domain": 63, "country": 124, "category": 64, "subcategory": 65, "specific": 66, "extra": 67},)
    assert aggregate.semantic_fields["number_of_variable_datum_records"] == 1
    assert aggregate.semantic_fields["variable_datum_bytes"] == bytes.fromhex("6162636465666768")

    aggregate_dis7 = fastdis.parse_semantic_pdu(_packet(7, 33, 7, body=_aggregate_state_dis6_body()))
    assert aggregate_dis7 is not None
    assert aggregate_dis7.semantic_level == "semantic_decoded"
    assert aggregate_dis7.descriptor.fully_domain_decoded
    assert aggregate_dis7.semantic_fields["aggregate_id"] == aggregate.semantic_fields["aggregate_id"]
    assert aggregate_dis7.semantic_fields["force_id"] == aggregate.semantic_fields["force_id"]
    assert aggregate_dis7.semantic_fields["aggregate_state"] == aggregate.semantic_fields["aggregate_state"]
    assert aggregate_dis7.semantic_fields["aggregate_type"] == aggregate.semantic_fields["aggregate_type"]
    assert aggregate_dis7.semantic_fields["formation"] == aggregate.semantic_fields["formation"]
    assert aggregate_dis7.semantic_fields["aggregate_marking"] == aggregate.semantic_fields["aggregate_marking"]
    assert aggregate_dis7.semantic_fields["dimensions"] == aggregate.semantic_fields["dimensions"]
    assert aggregate_dis7.semantic_fields["center_of_mass"] == aggregate.semantic_fields["center_of_mass"]
    assert aggregate_dis7.semantic_fields["velocity"] == aggregate.semantic_fields["velocity"]
    assert aggregate_dis7.semantic_fields["aggregate_id_list"] == aggregate.semantic_fields["aggregate_id_list"]
    assert aggregate_dis7.semantic_fields["entity_id_list"] == aggregate.semantic_fields["entity_id_list"]
    assert aggregate_dis7.semantic_fields["pad2_bytes"] == aggregate.semantic_fields["pad2_bytes"]
    assert aggregate_dis7.semantic_fields["silent_aggregate_system_list"] == aggregate.semantic_fields["silent_aggregate_system_list"]
    assert aggregate_dis7.semantic_fields["silent_entity_system_list"] == aggregate.semantic_fields["silent_entity_system_list"]
    assert aggregate_dis7.semantic_fields["number_of_variable_datum_records"] == aggregate.semantic_fields["number_of_variable_datum_records"]
    assert aggregate_dis7.semantic_fields["variable_datum_bytes"] == aggregate.semantic_fields["variable_datum_bytes"]


def test_attribute_dis7_rows_expose_decoded_entity_information_fields() -> None:
    attribute = fastdis.parse_semantic_pdu(_packet(7, 72, 1, body=_attribute_dis7_body()))
    assert attribute is not None
    assert attribute.semantic_level == "semantic_decoded"
    assert attribute.descriptor.fully_domain_decoded
    assert attribute.semantic_fields["originating_simulation_address"] == {"site": 301, "application": 302}
    assert attribute.semantic_fields["padding1"] == 0x01020304
    assert attribute.semantic_fields["padding2"] == 0x0506
    assert attribute.semantic_fields["attribute_record_pdu_type"] == 43
    assert attribute.semantic_fields["attribute_record_protocol_version"] == 7
    assert attribute.semantic_fields["master_attribute_record_type"] == 0x11121314
    assert attribute.semantic_fields["action_code"] == 9
    assert attribute.semantic_fields["padding3"] == -1
    assert attribute.semantic_fields["number_attribute_record_set"] == 2
    assert attribute.semantic_fields["attribute_record_sets_bytes"] == bytes.fromhex("a1a2a3a4a5a6a7a8")


def test_is_group_of_dis6_rows_expose_decoded_entity_management_fields() -> None:
    group = fastdis.parse_semantic_pdu(_packet(6, 34, 7, body=_is_group_of_dis6_body()))
    assert group is not None
    assert group.semantic_level == "semantic_decoded"
    assert group.descriptor.fully_domain_decoded
    assert group.semantic_fields["group_entity_id"] == {"site": 241, "application": 242, "entity": 243}
    assert group.semantic_fields["grouped_entity_category"] == 244
    assert group.semantic_fields["number_of_grouped_entities"] == 2
    assert group.semantic_fields["pad2"] == 245
    assert abs(group.semantic_fields["latitude"] - 46.125) < 1e-9
    assert abs(group.semantic_fields["longitude"] - (-93.5)) < 1e-9
    assert group.semantic_fields["grouped_entity_descriptions_bytes"] == bytes.fromhex("4142434445464748494a")

    group_dis7 = fastdis.parse_semantic_pdu(_packet(7, 34, 7, body=_is_group_of_dis6_body()))
    assert group_dis7 is not None
    assert group_dis7.semantic_level == "semantic_decoded"
    assert group_dis7.descriptor.fully_domain_decoded
    assert group_dis7.semantic_fields["group_entity_id"] == group.semantic_fields["group_entity_id"]
    assert group_dis7.semantic_fields["grouped_entity_category"] == group.semantic_fields["grouped_entity_category"]
    assert group_dis7.semantic_fields["number_of_grouped_entities"] == group.semantic_fields["number_of_grouped_entities"]
    assert group_dis7.semantic_fields["pad2"] == group.semantic_fields["pad2"]
    assert abs(group_dis7.semantic_fields["latitude"] - group.semantic_fields["latitude"]) < 1e-9
    assert abs(group_dis7.semantic_fields["longitude"] - group.semantic_fields["longitude"]) < 1e-9
    assert group_dis7.semantic_fields["grouped_entity_descriptions_bytes"] == group.semantic_fields["grouped_entity_descriptions_bytes"]


def test_minefield_state_rows_expose_decoded_minefield_fields() -> None:
    state_dis6 = fastdis.parse_semantic_pdu(_packet(6, 37, 8, body=_minefield_state_dis6_body()))
    assert state_dis6 is not None
    assert state_dis6.semantic_level == "semantic_decoded"
    assert state_dis6.descriptor.fully_domain_decoded
    assert state_dis6.semantic_fields["minefield_id"] == {"site": 221, "application": 222, "entity": 223}
    assert state_dis6.semantic_fields["minefield_sequence"] == 224
    assert state_dis6.semantic_fields["force_id"] == 225
    assert state_dis6.semantic_fields["number_of_perimeter_points"] == 2
    assert state_dis6.semantic_fields["minefield_type"] == {"kind": 1, "domain": 2, "country": 840, "category": 3, "subcategory": 4, "specific": 5, "extra": 6}
    assert state_dis6.semantic_fields["number_of_mine_types"] == 2
    assert state_dis6.semantic_fields["minefield_location"] == {"x": 10.25, "y": 20.5, "z": 30.75}
    assert abs(state_dis6.semantic_fields["minefield_orientation"]["psi"] - 0.1) < 1e-6
    assert abs(state_dis6.semantic_fields["minefield_orientation"]["theta"] - 0.2) < 1e-6
    assert abs(state_dis6.semantic_fields["minefield_orientation"]["phi"] - 0.3) < 1e-6
    assert state_dis6.semantic_fields["appearance"] == 226
    assert state_dis6.semantic_fields["protocol_mode"] == 227
    assert state_dis6.semantic_fields["perimeter_points"] == (
        {"x": 1.5, "y": 2.5},
        {"x": 3.5, "y": 4.5},
    )
    assert state_dis6.semantic_fields["mine_types"] == (
        {"kind": 7, "domain": 8, "country": 124, "category": 9, "subcategory": 10, "specific": 11, "extra": 12},
        {"kind": 13, "domain": 14, "country": 225, "category": 15, "subcategory": 16, "specific": 17, "extra": 18},
    )

    state_dis7 = fastdis.parse_semantic_pdu(_packet(7, 37, 8, body=_minefield_state_dis7_body()))
    assert state_dis7 is not None
    assert state_dis7.semantic_level == "semantic_decoded"
    assert state_dis7.descriptor.fully_domain_decoded
    assert state_dis7.semantic_fields["minefield_id"] == {"simulation_address": {"site": 231, "application": 232}, "minefield_number": 233}
    assert state_dis7.semantic_fields["minefield_sequence"] == 234
    assert state_dis7.semantic_fields["force_id"] == 235
    assert state_dis7.semantic_fields["number_of_perimeter_points"] == 2
    assert state_dis7.semantic_fields["minefield_type"] == {"kind": 19, "domain": 20, "country": 225, "category": 21, "subcategory": 22, "specific": 23, "extra": 24}
    assert state_dis7.semantic_fields["number_of_mine_types"] == 2
    assert state_dis7.semantic_fields["minefield_location"] == {"x": 40.25, "y": 50.5, "z": 60.75}
    assert abs(state_dis7.semantic_fields["minefield_orientation"]["psi"] - 0.4) < 1e-6
    assert abs(state_dis7.semantic_fields["minefield_orientation"]["theta"] - 0.5) < 1e-6
    assert abs(state_dis7.semantic_fields["minefield_orientation"]["phi"] - 0.6) < 1e-6
    assert state_dis7.semantic_fields["appearance"] == 236
    assert state_dis7.semantic_fields["protocol_mode"] == 237
    assert state_dis7.semantic_fields["perimeter_points"] == (
        {"x": 5.5, "y": 6.5},
        {"x": 7.5, "y": 8.5},
    )
    assert state_dis7.semantic_fields["mine_types"] == (
        {"kind": 25, "domain": 26, "country": 840, "category": 27, "subcategory": 28, "specific": 29, "extra": 30},
        {"kind": 31, "domain": 32, "country": 124, "category": 33, "subcategory": 34, "specific": 35, "extra": 36},
    )


def test_minefield_query_dis6_rows_expose_decoded_minefield_fields() -> None:
    query = fastdis.parse_semantic_pdu(_packet(6, 38, 8, body=_minefield_query_body()))
    assert query is not None
    assert query.semantic_level == "semantic_decoded"
    assert query.descriptor.fully_domain_decoded
    assert query.semantic_fields["minefield_id"] == {"site": 201, "application": 202, "entity": 203}
    assert query.semantic_fields["requesting_entity_id"] == {"site": 204, "application": 205, "entity": 206}
    assert query.semantic_fields["request_id"] == 207
    assert query.semantic_fields["number_of_perimeter_points"] == 2
    assert query.semantic_fields["pad2"] == 0
    assert query.semantic_fields["number_of_sensor_types"] == 2
    assert query.semantic_fields["data_filter"] == 0x01020304
    assert query.semantic_fields["requested_mine_type"] == {"kind": 3, "domain": 4, "country": 225, "category": 5, "subcategory": 6, "specific": 7, "extra": 8}
    assert query.semantic_fields["requested_perimeter_points"] == (
        {"x": 1.5, "y": 2.5},
        {"x": 3.5, "y": 4.5},
    )
    assert query.semantic_fields["sensor_types"] == (
        bytes.fromhex("1112"),
        bytes.fromhex("2122"),
    )

    query_dis7 = fastdis.parse_semantic_pdu(_packet(7, 38, 8, body=_minefield_query_body()))
    assert query_dis7 is not None
    assert query_dis7.semantic_level == "semantic_decoded"
    assert query_dis7.descriptor.fully_domain_decoded
    assert query_dis7.semantic_fields["minefield_id"] == query.semantic_fields["minefield_id"]
    assert query_dis7.semantic_fields["requesting_entity_id"] == query.semantic_fields["requesting_entity_id"]
    assert query_dis7.semantic_fields["request_id"] == query.semantic_fields["request_id"]
    assert query_dis7.semantic_fields["number_of_perimeter_points"] == query.semantic_fields["number_of_perimeter_points"]
    assert query_dis7.semantic_fields["pad2"] == query.semantic_fields["pad2"]
    assert query_dis7.semantic_fields["number_of_sensor_types"] == query.semantic_fields["number_of_sensor_types"]
    assert query_dis7.semantic_fields["data_filter"] == query.semantic_fields["data_filter"]
    assert query_dis7.semantic_fields["requested_mine_type"] == query.semantic_fields["requested_mine_type"]
    assert query_dis7.semantic_fields["requested_perimeter_points"] == query.semantic_fields["requested_perimeter_points"]
    assert query_dis7.semantic_fields["sensor_types"] == query.semantic_fields["sensor_types"]


def test_minefield_data_dis6_rows_expose_decoded_minefield_fields() -> None:
    data = fastdis.parse_semantic_pdu(_packet(6, 39, 8, body=_minefield_data_dis6_body()))
    assert data is not None
    assert data.semantic_level == "semantic_decoded"
    assert data.descriptor.fully_domain_decoded
    assert data.semantic_fields["minefield_id"] == {"site": 251, "application": 252, "entity": 253}
    assert data.semantic_fields["requesting_entity_id"] == {"site": 254, "application": 255, "entity": 256}
    assert data.semantic_fields["minefield_sequence_number"] == 257
    assert data.semantic_fields["request_id"] == 200
    assert data.semantic_fields["pdu_sequence_number"] == 3
    assert data.semantic_fields["number_of_pdus"] == 2
    assert data.semantic_fields["number_of_mines_in_this_pdu"] == 2
    assert data.semantic_fields["number_of_sensor_types"] == 2
    assert data.semantic_fields["pad2"] == 0
    assert data.semantic_fields["data_filter"] == 0x01020304
    assert data.semantic_fields["mine_type"] == {"kind": 37, "domain": 38, "country": 225, "category": 39, "subcategory": 40, "specific": 41, "extra": 42}
    assert data.semantic_fields["sensor_types"] == (
        bytes.fromhex("3132"),
        bytes.fromhex("4142"),
    )
    assert data.semantic_fields["pad3"] == 0
    assert data.semantic_fields["mine_locations"] == (
        {"x": 9.5, "y": 10.5, "z": 11.5},
        {"x": 12.5, "y": 13.5, "z": 14.5},
    )

    data_dis7 = fastdis.parse_semantic_pdu(_packet(7, 39, 8, body=_minefield_data_dis6_body()))
    assert data_dis7 is not None
    assert data_dis7.semantic_level == "semantic_decoded"
    assert data_dis7.descriptor.fully_domain_decoded
    assert data_dis7.semantic_fields["minefield_id"] == data.semantic_fields["minefield_id"]
    assert data_dis7.semantic_fields["requesting_entity_id"] == data.semantic_fields["requesting_entity_id"]
    assert data_dis7.semantic_fields["minefield_sequence_number"] == data.semantic_fields["minefield_sequence_number"]
    assert data_dis7.semantic_fields["request_id"] == data.semantic_fields["request_id"]
    assert data_dis7.semantic_fields["pdu_sequence_number"] == data.semantic_fields["pdu_sequence_number"]
    assert data_dis7.semantic_fields["number_of_pdus"] == data.semantic_fields["number_of_pdus"]
    assert data_dis7.semantic_fields["number_of_mines_in_this_pdu"] == data.semantic_fields["number_of_mines_in_this_pdu"]
    assert data_dis7.semantic_fields["number_of_sensor_types"] == data.semantic_fields["number_of_sensor_types"]
    assert data_dis7.semantic_fields["pad2"] == data.semantic_fields["pad2"]
    assert data_dis7.semantic_fields["data_filter"] == data.semantic_fields["data_filter"]
    assert data_dis7.semantic_fields["mine_type"] == data.semantic_fields["mine_type"]
    assert data_dis7.semantic_fields["sensor_types"] == data.semantic_fields["sensor_types"]
    assert data_dis7.semantic_fields["pad3"] == data.semantic_fields["pad3"]
    assert data_dis7.semantic_fields["mine_locations"] == data.semantic_fields["mine_locations"]


def test_environmental_process_dis6_rows_expose_decoded_environment_fields() -> None:
    process = fastdis.parse_semantic_pdu(_packet(6, 41, 9, body=_environmental_process_body()))
    assert process is not None
    assert process.semantic_level == "semantic_decoded"
    assert process.descriptor.fully_domain_decoded
    assert process.semantic_fields["environmental_process_id"] == {"site": 211, "application": 212, "entity": 213}
    assert process.semantic_fields["environment_type"] == {"kind": 9, "domain": 10, "country": 840, "category": 11, "subcategory": 12, "specific": 13, "extra": 14}
    assert process.semantic_fields["model_type"] == 15
    assert process.semantic_fields["environment_status"] == 16
    assert process.semantic_fields["number_of_environment_records"] == 2
    assert process.semantic_fields["sequence_number"] == 0x1718
    assert process.semantic_fields["environment_records_bytes"] == bytes.fromhex("3132333435363738393a")

    process_dis7 = fastdis.parse_semantic_pdu(_packet(7, 41, 9, body=_environmental_process_body()))
    assert process_dis7 is not None
    assert process_dis7.semantic_level == "semantic_decoded"
    assert process_dis7.descriptor.fully_domain_decoded
    assert process_dis7.semantic_fields["environmental_process_id"] == process.semantic_fields["environmental_process_id"]
    assert process_dis7.semantic_fields["environment_type"] == process.semantic_fields["environment_type"]
    assert process_dis7.semantic_fields["model_type"] == process.semantic_fields["model_type"]
    assert process_dis7.semantic_fields["environment_status"] == process.semantic_fields["environment_status"]
    assert process_dis7.semantic_fields["number_of_environment_records"] == process.semantic_fields["number_of_environment_records"]
    assert process_dis7.semantic_fields["sequence_number"] == process.semantic_fields["sequence_number"]
    assert process_dis7.semantic_fields["environment_records_bytes"] == process.semantic_fields["environment_records_bytes"]


def test_gridded_data_dis6_rows_expose_decoded_environment_fields() -> None:
    grid = fastdis.parse_semantic_pdu(_packet(6, 42, 9, body=_gridded_data_dis6_body()))
    assert grid is not None
    assert grid.semantic_level == "semantic_decoded"
    assert grid.descriptor.fully_domain_decoded
    assert grid.semantic_fields["environmental_simulation_application_id"] == {"site": 261, "application": 262, "entity": 263}
    assert grid.semantic_fields["field_number"] == 264
    assert grid.semantic_fields["pdu_number"] == 265
    assert grid.semantic_fields["pdu_total"] == 266
    assert grid.semantic_fields["coordinate_system"] == 267
    assert grid.semantic_fields["number_of_grid_axes"] == 3
    assert grid.semantic_fields["constant_grid"] == 1
    assert grid.semantic_fields["environment_type"] == {"kind": 43, "domain": 44, "country": 840, "category": 45, "subcategory": 46, "specific": 47, "extra": 48}
    assert abs(grid.semantic_fields["orientation"]["psi"] - 0.7) < 1e-6
    assert abs(grid.semantic_fields["orientation"]["theta"] - 0.8) < 1e-6
    assert abs(grid.semantic_fields["orientation"]["phi"] - 0.9) < 1e-6
    assert grid.semantic_fields["sample_time"] == 0x0102030405060708
    assert grid.semantic_fields["total_values"] == 269
    assert grid.semantic_fields["vector_dimension"] == 4
    assert grid.semantic_fields["padding1"] == 270
    assert grid.semantic_fields["padding2"] == 0
    assert grid.semantic_fields["grid_data_bytes"] == bytes.fromhex("5152535455565758595a")

    grid_dis7 = fastdis.parse_semantic_pdu(_packet(7, 42, 9, body=_gridded_data_dis6_body()))
    assert grid_dis7 is not None
    assert grid_dis7.semantic_level == "semantic_decoded"
    assert grid_dis7.descriptor.fully_domain_decoded
    assert grid_dis7.semantic_fields["environmental_simulation_application_id"] == grid.semantic_fields["environmental_simulation_application_id"]
    assert grid_dis7.semantic_fields["field_number"] == grid.semantic_fields["field_number"]
    assert grid_dis7.semantic_fields["pdu_number"] == grid.semantic_fields["pdu_number"]
    assert grid_dis7.semantic_fields["pdu_total"] == grid.semantic_fields["pdu_total"]
    assert grid_dis7.semantic_fields["coordinate_system"] == grid.semantic_fields["coordinate_system"]
    assert grid_dis7.semantic_fields["number_of_grid_axes"] == grid.semantic_fields["number_of_grid_axes"]
    assert grid_dis7.semantic_fields["constant_grid"] == grid.semantic_fields["constant_grid"]
    assert grid_dis7.semantic_fields["environment_type"] == grid.semantic_fields["environment_type"]
    assert grid_dis7.semantic_fields["orientation"] == grid.semantic_fields["orientation"]
    assert grid_dis7.semantic_fields["sample_time"] == grid.semantic_fields["sample_time"]
    assert grid_dis7.semantic_fields["total_values"] == grid.semantic_fields["total_values"]
    assert grid_dis7.semantic_fields["vector_dimension"] == grid.semantic_fields["vector_dimension"]
    assert grid_dis7.semantic_fields["padding1"] == grid.semantic_fields["padding1"]
    assert grid_dis7.semantic_fields["padding2"] == grid.semantic_fields["padding2"]
    assert grid_dis7.semantic_fields["grid_data_bytes"] == grid.semantic_fields["grid_data_bytes"]


def test_point_object_state_dis6_rows_expose_decoded_environment_fields() -> None:
    point = fastdis.parse_semantic_pdu(_packet(6, 43, 9, body=_point_object_state_dis6_body()))
    assert point is not None
    assert point.semantic_level == "semantic_decoded"
    assert point.descriptor.fully_domain_decoded
    assert point.semantic_fields["object_id"] == {"site": 51, "application": 52, "entity": 53}
    assert point.semantic_fields["referenced_object_id"] == {"site": 54, "application": 55, "entity": 56}
    assert point.semantic_fields["update_number"] == 57
    assert point.semantic_fields["force_id"] == 58
    assert point.semantic_fields["modifications"] == 59
    assert point.semantic_fields["object_type"] == {"entity_kind": 1, "domain": 2, "country": 840, "category": 3, "subcategory": 4}
    assert point.semantic_fields["object_location"] == {"x": 100.25, "y": 200.5, "z": 300.75}
    assert abs(point.semantic_fields["object_orientation"]["psi"] - 0.1) < 1e-6
    assert abs(point.semantic_fields["object_orientation"]["theta"] - 0.2) < 1e-6
    assert abs(point.semantic_fields["object_orientation"]["phi"] - 0.3) < 1e-6
    assert point.semantic_fields["object_appearance"] == 1234.5
    assert point.semantic_fields["requester_id"] == {"site": 60, "application": 61}
    assert point.semantic_fields["receiving_id"] == {"site": 62, "application": 63}
    assert point.semantic_fields["pad2"] == 64


def test_point_object_state_dis7_rows_expose_decoded_environment_fields() -> None:
    point = fastdis.parse_semantic_pdu(_packet(7, 43, 9, body=_point_object_state_dis7_body()))
    assert point is not None
    assert point.semantic_level == "semantic_decoded"
    assert point.descriptor.fully_domain_decoded
    assert point.semantic_fields["object_id"] == {"site": 71, "application": 72, "entity": 73}
    assert point.semantic_fields["referenced_object_id"] == {"site": 74, "application": 75, "entity": 76}
    assert point.semantic_fields["update_number"] == 77
    assert point.semantic_fields["force_id"] == 78
    assert point.semantic_fields["modifications"] == 79
    assert point.semantic_fields["object_type"] == {"domain": 4, "object_kind": 5, "category": 6, "subcategory": 7}
    assert point.semantic_fields["object_location"] == {"x": 400.25, "y": 500.5, "z": 600.75}
    assert abs(point.semantic_fields["object_orientation"]["psi"] - 0.4) < 1e-6
    assert abs(point.semantic_fields["object_orientation"]["theta"] - 0.5) < 1e-6
    assert abs(point.semantic_fields["object_orientation"]["phi"] - 0.6) < 1e-6
    assert point.semantic_fields["object_appearance"] == 2345.5
    assert point.semantic_fields["requester_id"] == {"site": 80, "application": 81}
    assert point.semantic_fields["receiving_id"] == {"site": 82, "application": 83}
    assert point.semantic_fields["pad2"] == 84


def test_linear_object_state_dis6_rows_expose_decoded_environment_fields() -> None:
    linear = fastdis.parse_semantic_pdu(_packet(6, 44, 9, body=_linear_object_state_dis6_body()))
    assert linear is not None
    assert linear.semantic_level == "semantic_decoded"
    assert linear.descriptor.fully_domain_decoded
    assert linear.semantic_fields["object_id"] == {"site": 131, "application": 132, "entity": 133}
    assert linear.semantic_fields["referenced_object_id"] == {"site": 134, "application": 135, "entity": 136}
    assert linear.semantic_fields["update_number"] == 137
    assert linear.semantic_fields["force_id"] == 138
    assert linear.semantic_fields["number_of_segments"] == 2
    assert linear.semantic_fields["requester_id"] == {"site": 139, "application": 140}
    assert linear.semantic_fields["receiving_id"] == {"site": 141, "application": 142}
    assert linear.semantic_fields["object_type"] == {"entity_kind": 9, "domain": 10, "country": 840, "category": 11, "subcategory": 12}
    segments = linear.semantic_fields["linear_segment_parameters"]
    assert len(segments) == 2
    assert segments[0]["segment_number"] == 1
    assert segments[0]["segment_appearance"] == bytes.fromhex("010203040506")
    assert segments[0]["location"] == {"x": 1000.25, "y": 1001.5, "z": 1002.75}
    assert abs(segments[0]["orientation"]["psi"] - 0.1) < 1e-6
    assert abs(segments[0]["orientation"]["theta"] - 0.2) < 1e-6
    assert abs(segments[0]["orientation"]["phi"] - 0.3) < 1e-6
    assert segments[0]["segment_length"] == 25
    assert segments[0]["segment_width"] == 26
    assert segments[0]["segment_height"] == 27
    assert segments[0]["segment_depth"] == 28
    assert segments[0]["pad1"] == 29
    assert segments[1]["segment_number"] == 2
    assert segments[1]["segment_appearance"] == bytes.fromhex("0a0b0c0d0e0f")
    assert segments[1]["location"] == {"x": 2000.25, "y": 2001.5, "z": 2002.75}
    assert abs(segments[1]["orientation"]["psi"] - 0.4) < 1e-6
    assert abs(segments[1]["orientation"]["theta"] - 0.5) < 1e-6
    assert abs(segments[1]["orientation"]["phi"] - 0.6) < 1e-6
    assert segments[1]["segment_length"] == 35
    assert segments[1]["segment_width"] == 36
    assert segments[1]["segment_height"] == 37
    assert segments[1]["segment_depth"] == 38
    assert segments[1]["pad1"] == 39


def test_linear_object_state_dis7_rows_expose_decoded_environment_fields() -> None:
    linear = fastdis.parse_semantic_pdu(_packet(7, 44, 9, body=_linear_object_state_dis7_body()))
    assert linear is not None
    assert linear.semantic_level == "semantic_decoded"
    assert linear.descriptor.fully_domain_decoded
    assert linear.semantic_fields["object_id"] == {"site": 151, "application": 152, "entity": 153}
    assert linear.semantic_fields["referenced_object_id"] == {"site": 154, "application": 155, "entity": 156}
    assert linear.semantic_fields["update_number"] == 157
    assert linear.semantic_fields["force_id"] == 158
    assert linear.semantic_fields["number_of_segments"] == 2
    assert linear.semantic_fields["requester_id"] == {"site": 159, "application": 160}
    assert linear.semantic_fields["receiving_id"] == {"site": 161, "application": 162}
    assert linear.semantic_fields["object_type"] == {"domain": 13, "object_kind": 14, "category": 15, "subcategory": 16}
    segments = linear.semantic_fields["linear_segment_parameters"]
    assert len(segments) == 2
    assert segments[0]["segment_number"] == 3
    assert segments[0]["segment_modification"] == 4
    assert segments[0]["general_segment_appearance"] == 0x0506
    assert segments[0]["specific_segment_appearance"] == 0x0708090A
    assert segments[0]["segment_location"] == {"x": 3000.25, "y": 3001.5, "z": 3002.75}
    assert abs(segments[0]["segment_orientation"]["psi"] - 0.7) < 1e-6
    assert abs(segments[0]["segment_orientation"]["theta"] - 0.8) < 1e-6
    assert abs(segments[0]["segment_orientation"]["phi"] - 0.9) < 1e-6
    assert abs(segments[0]["segment_length"] - 45.5) < 1e-6
    assert abs(segments[0]["segment_width"] - 46.5) < 1e-6
    assert abs(segments[0]["segment_height"] - 47.5) < 1e-6
    assert abs(segments[0]["segment_depth"] - 48.5) < 1e-6
    assert segments[0]["padding"] == 49
    assert segments[1]["segment_number"] == 5
    assert segments[1]["segment_modification"] == 6
    assert segments[1]["general_segment_appearance"] == 0x0B0C
    assert segments[1]["specific_segment_appearance"] == 0x0D0E0F10
    assert segments[1]["segment_location"] == {"x": 4000.25, "y": 4001.5, "z": 4002.75}
    assert abs(segments[1]["segment_orientation"]["psi"] - 1.0) < 1e-6
    assert abs(segments[1]["segment_orientation"]["theta"] - 1.1) < 1e-6
    assert abs(segments[1]["segment_orientation"]["phi"] - 1.2) < 1e-6
    assert abs(segments[1]["segment_length"] - 55.5) < 1e-6
    assert abs(segments[1]["segment_width"] - 56.5) < 1e-6
    assert abs(segments[1]["segment_height"] - 57.5) < 1e-6
    assert abs(segments[1]["segment_depth"] - 58.5) < 1e-6
    assert segments[1]["padding"] == 59


def test_areal_object_state_dis6_rows_expose_decoded_environment_fields() -> None:
    areal = fastdis.parse_semantic_pdu(_packet(6, 45, 9, body=_areal_object_state_dis6_body()))
    assert areal is not None
    assert areal.semantic_level == "semantic_decoded"
    assert areal.descriptor.fully_domain_decoded
    assert areal.semantic_fields["object_id"] == {"site": 91, "application": 92, "entity": 93}
    assert areal.semantic_fields["referenced_object_id"] == {"site": 94, "application": 95, "entity": 96}
    assert areal.semantic_fields["update_number"] == 97
    assert areal.semantic_fields["force_id"] == 98
    assert areal.semantic_fields["modifications"] == 99
    assert areal.semantic_fields["object_type"] == {"kind": 3, "domain": 4, "country": 225, "category": 5, "subcategory": 6, "specific": 7, "extra": 8}
    assert areal.semantic_fields["object_appearance"] == bytes.fromhex("010203040506")
    assert areal.semantic_fields["number_of_points"] == 2
    assert areal.semantic_fields["requester_id"] == {"site": 100, "application": 101}
    assert areal.semantic_fields["receiving_id"] == {"site": 102, "application": 103}
    assert areal.semantic_fields["object_locations"] == ({"x": 1.0, "y": 2.0, "z": 3.0}, {"x": 4.0, "y": 5.0, "z": 6.0})


def test_areal_object_state_dis7_rows_expose_decoded_environment_fields() -> None:
    areal = fastdis.parse_semantic_pdu(_packet(7, 45, 9, body=_areal_object_state_dis7_body()))
    assert areal is not None
    assert areal.semantic_level == "semantic_decoded"
    assert areal.descriptor.fully_domain_decoded
    assert areal.semantic_fields["object_id"] == {"site": 111, "application": 112, "entity": 113}
    assert areal.semantic_fields["referenced_object_id"] == {"site": 114, "application": 115, "entity": 116}
    assert areal.semantic_fields["update_number"] == 117
    assert areal.semantic_fields["force_id"] == 118
    assert areal.semantic_fields["modifications"] == 119
    assert areal.semantic_fields["object_type"] == {"kind": 6, "domain": 7, "country": 124, "category": 8, "subcategory": 9, "specific": 10, "extra": 11}
    assert areal.semantic_fields["specific_object_appearance"] == 120
    assert areal.semantic_fields["general_object_appearance"] == 121
    assert areal.semantic_fields["number_of_points"] == 2
    assert areal.semantic_fields["requester_id"] == {"site": 122, "application": 123}
    assert areal.semantic_fields["receiving_id"] == {"site": 124, "application": 125}
    assert areal.semantic_fields["object_locations"] == ({"x": 7.0, "y": 8.0, "z": 9.0}, {"x": 10.0, "y": 11.0, "z": 12.0})


def test_underwater_acoustic_rows_expose_decoded_semantic_fields() -> None:
    ua = fastdis.parse_semantic_pdu(_packet(7, 29, 6, body=_underwater_acoustic_body()))
    assert ua is not None
    assert ua.semantic_level == "semantic_decoded"
    assert ua.descriptor.fully_domain_decoded
    assert ua.semantic_fields["semantic_decode_status"] == "decoded"
    assert ua.semantic_fields["emitting_entity_id"] == {"site": 1, "application": 2, "entity": 3}
    assert ua.semantic_fields["event_id"] == {"site": 4, "application": 5, "event_number": 6}
    assert ua.semantic_fields["state_change_indicator"] == 7
    assert ua.semantic_fields["pad"] == 0
    assert ua.semantic_fields["passive_parameter_index"] == 8
    assert ua.semantic_fields["propulsion_plant_configuration"] == 9
    assert ua.semantic_fields["number_of_shafts"] == 1
    assert ua.semantic_fields["number_of_apas"] == 2
    assert ua.semantic_fields["number_of_ua_emitter_systems"] == 1
    assert ua.semantic_fields["shaft_rpms"] == (
        {
            "current_shaft_rpms": 100,
            "ordered_shaft_rpms": 120,
            "shaft_rpm_rate_of_change": 1.5,
        },
    )
    assert ua.semantic_fields["apa_data"] == (
        {"parameter_index": 13, "parameter_value": -14},
        {"parameter_index": 15, "parameter_value": -16},
    )
    assert ua.semantic_fields["emitter_systems_bytes"] == bytes.fromhex("3132333435363738")
    assert ua.diagnostics == ("full domain decode available",)


def test_create_entity_rows_expose_decoded_lifecycle_fields() -> None:
    create_entity = fastdis.parse_semantic_pdu(_packet(7, 11, 5, body=_create_remove_entity_body()))
    assert create_entity is not None
    assert create_entity.semantic_level == "semantic_decoded"
    assert create_entity.descriptor.fully_domain_decoded
    assert create_entity.semantic_fields["semantic_decode_status"] == "decoded"
    assert create_entity.semantic_fields["originating_entity_id"] == {"site": 1, "application": 2, "entity": 3}
    assert create_entity.semantic_fields["receiving_entity_id"] == {"site": 4, "application": 5, "entity": 6}
    assert create_entity.semantic_fields["request_id"] == 0x01020304
    assert create_entity.diagnostics == ("full domain decode available",)


def test_create_entity_reliable_rows_expose_decoded_lifecycle_fields() -> None:
    create_entity_reliable = fastdis.parse_semantic_pdu(_packet(7, 51, 10, body=_create_remove_entity_reliable_body()))
    assert create_entity_reliable is not None
    assert create_entity_reliable.semantic_level == "semantic_decoded"
    assert create_entity_reliable.descriptor.fully_domain_decoded
    assert create_entity_reliable.semantic_fields["semantic_decode_status"] == "decoded"
    assert create_entity_reliable.semantic_fields["originating_entity_id"] == {"site": 1, "application": 2, "entity": 3}
    assert create_entity_reliable.semantic_fields["receiving_entity_id"] == {"site": 4, "application": 5, "entity": 6}
    assert create_entity_reliable.semantic_fields["required_reliability_service"] == 7
    assert create_entity_reliable.semantic_fields["pad1"] == 0
    assert create_entity_reliable.semantic_fields["pad2"] == 0
    assert create_entity_reliable.semantic_fields["request_id"] == 0x0A0B0C0D
    assert create_entity_reliable.diagnostics == ("full domain decode available",)


def test_start_resume_rows_expose_decoded_control_fields() -> None:
    start_resume = fastdis.parse_semantic_pdu(_packet(7, 13, 5, body=_start_resume_body()))
    assert start_resume is not None
    assert start_resume.semantic_level == "semantic_decoded"
    assert start_resume.descriptor.fully_domain_decoded
    assert start_resume.semantic_fields["real_world_time"] == {"hour": 123456, "time_past_hour": 7890}
    assert start_resume.semantic_fields["simulation_time"] == {"hour": 222222, "time_past_hour": 3333}
    assert start_resume.semantic_fields["request_id"] == 0x01020304


def test_stop_freeze_rows_expose_decoded_control_fields() -> None:
    stop_freeze = fastdis.parse_semantic_pdu(_packet(7, 14, 5, body=_stop_freeze_body()))
    assert stop_freeze is not None
    assert stop_freeze.semantic_level == "semantic_decoded"
    assert stop_freeze.descriptor.fully_domain_decoded
    assert stop_freeze.semantic_fields["reason"] == 7
    assert stop_freeze.semantic_fields["frozen_behavior"] == 9
    assert stop_freeze.semantic_fields["padding1"] == 0
    assert stop_freeze.semantic_fields["request_id"] == 0x0A0B0C0D


def test_acknowledge_rows_expose_decoded_control_fields() -> None:
    acknowledge = fastdis.parse_semantic_pdu(_packet(7, 15, 5, body=_acknowledge_body()))
    assert acknowledge is not None
    assert acknowledge.semantic_level == "semantic_decoded"
    assert acknowledge.descriptor.fully_domain_decoded
    assert acknowledge.semantic_fields["acknowledge_flag"] == 11
    assert acknowledge.semantic_fields["response_flag"] == 12
    assert acknowledge.semantic_fields["request_id"] == 0x10203040


def test_start_resume_reliable_rows_expose_decoded_control_fields() -> None:
    start_resume = fastdis.parse_semantic_pdu(_packet(7, 53, 10, body=_start_resume_reliable_body()))
    assert start_resume is not None
    assert start_resume.semantic_level == "semantic_decoded"
    assert start_resume.descriptor.fully_domain_decoded
    assert start_resume.semantic_fields["required_reliability_service"] == 5
    assert start_resume.semantic_fields["pad1"] == 0
    assert start_resume.semantic_fields["pad2"] == 0
    assert start_resume.semantic_fields["request_id"] == 0x11121314


def test_stop_freeze_reliable_rows_expose_decoded_control_fields() -> None:
    stop_freeze = fastdis.parse_semantic_pdu(_packet(7, 54, 10, body=_stop_freeze_reliable_body()))
    assert stop_freeze is not None
    assert stop_freeze.semantic_level == "semantic_decoded"
    assert stop_freeze.descriptor.fully_domain_decoded
    assert stop_freeze.semantic_fields["reason"] == 7
    assert stop_freeze.semantic_fields["frozen_behavior"] == 9
    assert stop_freeze.semantic_fields["required_reliablity_service"] == 3
    assert stop_freeze.semantic_fields["pad1"] == 0
    assert stop_freeze.semantic_fields["request_id"] == 0x21222324


def test_action_request_rows_expose_decoded_control_fields_and_preserve_tail() -> None:
    action_request = fastdis.parse_semantic_pdu(_packet(7, 16, 5, body=_action_request_body()))
    assert action_request is not None
    assert action_request.semantic_level == "semantic_decoded"
    assert action_request.descriptor.fully_domain_decoded
    assert action_request.semantic_fields["request_id"] == 0x01020304
    assert action_request.semantic_fields["action_id"] == 0x11121314
    assert action_request.semantic_fields["number_of_fixed_datum_records"] == 1
    assert action_request.semantic_fields["number_of_variable_datum_records"] == 1
    assert action_request.semantic_fields["datum_record_bytes"] == bytes.fromhex("00112233445566778899aabbccddeeff")


def test_action_response_rows_expose_decoded_control_fields_and_preserve_tail() -> None:
    action_response = fastdis.parse_semantic_pdu(_packet(7, 17, 5, body=_action_response_body()))
    assert action_response is not None
    assert action_response.semantic_level == "semantic_decoded"
    assert action_response.descriptor.fully_domain_decoded
    assert action_response.semantic_fields["request_id"] == 0x21222324
    assert action_response.semantic_fields["request_status"] == 0x31323334
    assert action_response.semantic_fields["number_of_fixed_datum_records"] == 2
    assert action_response.semantic_fields["number_of_variable_datum_records"] == 1
    assert action_response.semantic_fields["datum_record_bytes"] == bytes.fromhex("ffeeddccbbaa99887766554433221100")


def test_action_request_reliable_rows_expose_decoded_control_fields_and_preserve_tail() -> None:
    action_request = fastdis.parse_semantic_pdu(_packet(7, 56, 10, body=_action_request_reliable_body()))
    assert action_request is not None
    assert action_request.semantic_level == "semantic_decoded"
    assert action_request.descriptor.fully_domain_decoded
    assert action_request.semantic_fields["required_reliability_service"] == 5
    assert action_request.semantic_fields["request_id"] == 0x41424344
    assert action_request.semantic_fields["action_id"] == 0x51525354
    assert action_request.semantic_fields["number_of_fixed_datum_records"] == 3
    assert action_request.semantic_fields["number_of_variable_datum_records"] == 1
    assert action_request.semantic_fields["datum_record_bytes"] == bytes.fromhex("01010101020202020303030304040404")


def test_action_response_reliable_rows_expose_decoded_control_fields_and_preserve_tail() -> None:
    action_response = fastdis.parse_semantic_pdu(_packet(7, 57, 10, body=_action_response_reliable_body()))
    assert action_response is not None
    assert action_response.semantic_level == "semantic_decoded"
    assert action_response.descriptor.fully_domain_decoded
    assert action_response.semantic_fields["request_id"] == 0x61626364
    assert action_response.semantic_fields["response_status"] == 0x71727374
    assert action_response.semantic_fields["number_of_fixed_datum_records"] == 4
    assert action_response.semantic_fields["number_of_variable_datum_records"] == 2
    assert action_response.semantic_fields["datum_record_bytes"] == bytes.fromhex("0a0b0c0d0e0f10111213141516171819")


def test_data_query_rows_expose_decoded_fields_and_preserve_tail() -> None:
    data_query = fastdis.parse_semantic_pdu(_packet(7, 18, 5, body=_data_query_body()))
    assert data_query is not None
    assert data_query.semantic_level == "semantic_decoded"
    assert data_query.descriptor.fully_domain_decoded
    assert data_query.semantic_fields["request_id"] == 0x01020304
    assert data_query.semantic_fields["time_interval"] == {"hour": 123456, "time_past_hour": 7890}
    assert data_query.semantic_fields["number_of_fixed_datum_records"] == 1
    assert data_query.semantic_fields["number_of_variable_datum_records"] == 2
    assert data_query.semantic_fields["datum_record_bytes"] == bytes.fromhex("aa00bb11cc22dd33ee44ff5566778899")


def test_set_data_rows_expose_decoded_fields_and_preserve_tail() -> None:
    set_data = fastdis.parse_semantic_pdu(_packet(7, 19, 5, body=_set_data_body()))
    assert set_data is not None
    assert set_data.semantic_level == "semantic_decoded"
    assert set_data.descriptor.fully_domain_decoded
    assert set_data.semantic_fields["request_id"] == 0x11121314
    assert set_data.semantic_fields["padding1"] == 0
    assert set_data.semantic_fields["number_of_fixed_datum_records"] == 2
    assert set_data.semantic_fields["number_of_variable_datum_records"] == 1
    assert set_data.semantic_fields["datum_record_bytes"] == bytes.fromhex("101112131415161718191a1b1c1d1e1f")


def test_data_rows_expose_decoded_fields_and_preserve_tail() -> None:
    data = fastdis.parse_semantic_pdu(_packet(7, 20, 5, body=_set_data_body()))
    assert data is not None
    assert data.semantic_level == "semantic_decoded"
    assert data.descriptor.fully_domain_decoded
    assert data.semantic_fields["request_id"] == 0x11121314
    assert data.semantic_fields["padding1"] == 0
    assert data.semantic_fields["number_of_fixed_datum_records"] == 2
    assert data.semantic_fields["number_of_variable_datum_records"] == 1
    assert data.semantic_fields["datum_record_bytes"] == bytes.fromhex("101112131415161718191a1b1c1d1e1f")


def test_data_reliable_rows_expose_decoded_fields_and_preserve_tail() -> None:
    data_reliable = fastdis.parse_semantic_pdu(_packet(7, 60, 10, body=_data_reliable_body()))
    assert data_reliable is not None
    assert data_reliable.semantic_level == "semantic_decoded"
    assert data_reliable.descriptor.fully_domain_decoded
    assert data_reliable.semantic_fields["request_id"] == 0x31323334
    assert data_reliable.semantic_fields["required_reliability_service"] == 6
    assert data_reliable.semantic_fields["pad1"] == 0
    assert data_reliable.semantic_fields["pad2"] == 0
    assert data_reliable.semantic_fields["number_of_fixed_datum_records"] == 3
    assert data_reliable.semantic_fields["number_of_variable_datum_records"] == 1
    assert data_reliable.semantic_fields["datum_record_bytes"] == bytes.fromhex("2122232425262728292a2b2c2d2e2f30")


def test_data_query_reliable_rows_expose_decoded_fields_and_preserve_tail() -> None:
    data_query = fastdis.parse_semantic_pdu(_packet(7, 58, 10, body=_data_query_reliable_body()))
    assert data_query is not None
    assert data_query.semantic_level == "semantic_decoded"
    assert data_query.descriptor.fully_domain_decoded
    assert data_query.semantic_fields["required_reliability_service"] == 5
    assert data_query.semantic_fields["request_id"] == 0x41424344
    assert data_query.semantic_fields["time_interval"] == {"hour": 222222, "time_past_hour": 3333}
    assert data_query.semantic_fields["number_of_fixed_datum_records"] == 2
    assert data_query.semantic_fields["number_of_variable_datum_records"] == 1
    assert data_query.semantic_fields["datum_record_bytes"] == bytes.fromhex("3132333435363738393a3b3c3d3e3f40")


def test_set_data_reliable_rows_expose_decoded_fields_and_preserve_tail() -> None:
    set_data = fastdis.parse_semantic_pdu(_packet(7, 59, 10, body=_set_data_reliable_body()))
    assert set_data is not None
    assert set_data.semantic_level == "semantic_decoded"
    assert set_data.descriptor.fully_domain_decoded
    assert set_data.semantic_fields["required_reliability_service"] == 7
    assert set_data.semantic_fields["request_id"] == 0x51525354
    assert set_data.semantic_fields["number_of_fixed_datum_records"] == 4
    assert set_data.semantic_fields["number_of_variable_datum_records"] == 2
    assert set_data.semantic_fields["datum_record_bytes"] == bytes.fromhex("4142434445464748494a4b4c4d4e4f50")


def test_event_report_rows_expose_decoded_fields_and_preserve_tail() -> None:
    event_report = fastdis.parse_semantic_pdu(_packet(7, 21, 5, body=_event_report_body()))
    assert event_report is not None
    assert event_report.semantic_level == "semantic_decoded"
    assert event_report.descriptor.fully_domain_decoded
    assert event_report.semantic_fields["event_type"] == 0x61626364
    assert event_report.semantic_fields["padding1"] == 0
    assert event_report.semantic_fields["number_of_fixed_datum_records"] == 1
    assert event_report.semantic_fields["number_of_variable_datum_records"] == 3
    assert event_report.semantic_fields["datum_record_bytes"] == bytes.fromhex("5152535455565758595a5b5c5d5e5f60")


def test_comment_rows_expose_decoded_fields_and_preserve_tail() -> None:
    comment = fastdis.parse_semantic_pdu(_packet(7, 22, 5, body=_comment_body()))
    assert comment is not None
    assert comment.semantic_level == "semantic_decoded"
    assert comment.descriptor.fully_domain_decoded
    assert comment.semantic_fields["number_of_fixed_datum_records"] == 2
    assert comment.semantic_fields["number_of_variable_datum_records"] == 2
    assert comment.semantic_fields["datum_record_bytes"] == bytes.fromhex("6162636465666768696a6b6c6d6e6f70")


def test_comment_reliable_rows_expose_decoded_fields_and_preserve_tail() -> None:
    comment = fastdis.parse_semantic_pdu(_packet(7, 62, 10, body=_comment_body()))
    assert comment is not None
    assert comment.semantic_level == "semantic_decoded"
    assert comment.descriptor.fully_domain_decoded
    assert comment.semantic_fields["number_of_fixed_datum_records"] == 2
    assert comment.semantic_fields["number_of_variable_datum_records"] == 2
    assert comment.semantic_fields["datum_record_bytes"] == bytes.fromhex("6162636465666768696a6b6c6d6e6f70")


def test_designator_rows_expose_decoded_fields() -> None:
    designator = fastdis.parse_semantic_pdu(_packet(7, 24, 6, body=_designator_body()))
    assert designator is not None
    assert designator.semantic_level == "semantic_decoded"
    assert designator.descriptor.fully_domain_decoded
    assert designator.semantic_fields["designating_entity_id"] == {"site": 1, "application": 2, "entity": 3}
    assert designator.semantic_fields["code_name"] == 17
    assert designator.semantic_fields["designated_entity_id"] == {"site": 4, "application": 5, "entity": 6}
    assert designator.semantic_fields["designator_code"] == 18
    assert abs(designator.semantic_fields["designator_power"] - 55.5) < 1e-6
    assert abs(designator.semantic_fields["designator_wavelength"] - 1.064) < 1e-6
    assert designator.semantic_fields["designator_spot_wrt_designated"] == {"x": 7.5, "y": 8.5, "z": 9.5}
    assert designator.semantic_fields["designator_spot_location"] == {"x": 1000.25, "y": 2000.5, "z": 3000.75}
    assert designator.semantic_fields["dead_reckoning_algorithm"] == 4
    assert designator.semantic_fields["padding1"] == 0
    assert designator.semantic_fields["padding2"] == 0
    assert designator.semantic_fields["entity_linear_acceleration"] == {"x": 0.25, "y": 0.5, "z": 0.75}


def test_transmitter_dis6_rows_expose_decoded_fields_and_preserve_tail() -> None:
    transmitter = fastdis.parse_semantic_pdu(_packet(6, 25, 4, body=_transmitter_dis6_body()))
    assert transmitter is not None
    assert transmitter.semantic_level == "semantic_decoded"
    assert transmitter.descriptor.fully_domain_decoded
    assert transmitter.semantic_fields["entity_id"] == {"site": 1, "application": 2, "entity": 3}
    assert transmitter.semantic_fields["radio_id"] == 7
    assert transmitter.semantic_fields["radio_entity_type"]["country"] == 840
    assert transmitter.semantic_fields["transmit_state"] == 6
    assert transmitter.semantic_fields["input_source"] == 8
    assert transmitter.semantic_fields["padding1"] == 0
    assert transmitter.semantic_fields["antenna_pattern_type"] == 9
    assert transmitter.semantic_fields["antenna_pattern_count"] == 2
    assert transmitter.semantic_fields["frequency"] == 123456789
    assert abs(transmitter.semantic_fields["transmit_frequency_bandwidth"] - 25.5) < 1e-6
    assert abs(transmitter.semantic_fields["power"] - 40.25) < 1e-6
    assert transmitter.semantic_fields["modulation_type"]["system"] == 0x0404
    assert transmitter.semantic_fields["crypto_system"] == 0x0505
    assert transmitter.semantic_fields["crypto_key_id"] == 0x0606
    assert transmitter.semantic_fields["modulation_parameter_count"] == 3
    assert transmitter.semantic_fields["padding2"] == 0
    assert transmitter.semantic_fields["padding3"] == 0
    assert transmitter.semantic_fields["variable_payload_bytes"] == bytes.fromhex("4142434445464748")


def test_signal_dis6_rows_expose_decoded_fields_and_preserve_payload() -> None:
    signal = fastdis.parse_semantic_pdu(_packet(6, 26, 4, body=_signal_dis6_body()))
    assert signal is not None
    assert signal.semantic_level == "semantic_decoded"
    assert signal.descriptor.fully_domain_decoded
    assert signal.semantic_fields["entity_id"] == {"site": 1, "application": 2, "entity": 3}
    assert signal.semantic_fields["radio_id"] == 7
    assert signal.semantic_fields["encoding_scheme"] == 0x0102
    assert signal.semantic_fields["tdl_type"] == 0x0304
    assert signal.semantic_fields["sample_rate"] == 44100
    assert signal.semantic_fields["data_length"] == 16
    assert signal.semantic_fields["samples"] == 2
    assert signal.semantic_fields["data_bytes"] == bytes.fromhex("0102030405060708")


def test_transmitter_dis7_rows_expose_decoded_fields_and_preserve_tail() -> None:
    transmitter = fastdis.parse_semantic_pdu(_packet(7, 25, 4, body=_transmitter_dis7_body()))
    assert transmitter is not None
    assert transmitter.semantic_level == "semantic_decoded"
    assert transmitter.descriptor.fully_domain_decoded
    assert transmitter.semantic_fields["radio_reference_id"] == {"site": 4, "application": 5, "entity": 6}
    assert transmitter.semantic_fields["radio_number"] == 11
    assert transmitter.semantic_fields["radio_entity_type"]["country"] == 840
    assert transmitter.semantic_fields["transmit_state"] == 7
    assert transmitter.semantic_fields["input_source"] == 9
    assert transmitter.semantic_fields["variable_transmitter_parameter_count"] == 2
    assert transmitter.semantic_fields["antenna_pattern_type"] == 10
    assert transmitter.semantic_fields["antenna_pattern_count"] == 3
    assert transmitter.semantic_fields["frequency"] == 987654321
    assert abs(transmitter.semantic_fields["transmit_frequency_bandwidth"] - 12.75) < 1e-6
    assert abs(transmitter.semantic_fields["power"] - 18.5) < 1e-6
    assert transmitter.semantic_fields["modulation_type"]["radio_system"] == 0x1414
    assert transmitter.semantic_fields["crypto_system"] == 0x1515
    assert transmitter.semantic_fields["crypto_key_id"] == 0x1616
    assert transmitter.semantic_fields["modulation_parameter_count"] == 4
    assert transmitter.semantic_fields["padding2"] == 0
    assert transmitter.semantic_fields["padding3"] == 0
    assert transmitter.semantic_fields["variable_payload_bytes"] == bytes.fromhex("5152535455565758")


def test_signal_dis7_rows_expose_decoded_fields_and_preserve_payload() -> None:
    signal = fastdis.parse_semantic_pdu(_packet(7, 26, 4, body=_signal_dis7_body()))
    assert signal is not None
    assert signal.semantic_level == "semantic_decoded"
    assert signal.descriptor.fully_domain_decoded
    assert signal.semantic_fields["encoding_scheme"] == 0x1112
    assert signal.semantic_fields["tdl_type"] == 0x1314
    assert signal.semantic_fields["sample_rate"] == 22050
    assert signal.semantic_fields["data_length"] == 24
    assert signal.semantic_fields["samples"] == 3
    assert signal.semantic_fields["data_bytes"] == bytes.fromhex("1112131415161718")


def test_receiver_dis6_rows_expose_decoded_fields() -> None:
    receiver = fastdis.parse_semantic_pdu(_packet(6, 27, 4, body=_receiver_dis6_body()))
    assert receiver is not None
    assert receiver.semantic_level == "semantic_decoded"
    assert receiver.descriptor.fully_domain_decoded
    assert receiver.semantic_fields["entity_id"] == {"site": 1, "application": 2, "entity": 3}
    assert receiver.semantic_fields["radio_id"] == 9
    assert receiver.semantic_fields["receiver_state"] == 5
    assert receiver.semantic_fields["padding1"] == 0
    assert abs(receiver.semantic_fields["received_power"] - 12.5) < 1e-6
    assert receiver.semantic_fields["transmitter_entity_id"] == {"site": 4, "application": 5, "entity": 6}
    assert receiver.semantic_fields["transmitter_radio_id"] == 10


def test_receiver_dis7_rows_expose_decoded_fields() -> None:
    receiver = fastdis.parse_semantic_pdu(_packet(7, 27, 4, body=_receiver_dis7_body()))
    assert receiver is not None
    assert receiver.semantic_level == "semantic_decoded"
    assert receiver.descriptor.fully_domain_decoded
    assert receiver.semantic_fields["receiver_state"] == 6
    assert receiver.semantic_fields["padding1"] == 0
    assert abs(receiver.semantic_fields["received_power"] - 7.25) < 1e-6
    assert receiver.semantic_fields["transmitter_entity_id"] == {"site": 4, "application": 5, "entity": 6}
    assert receiver.semantic_fields["transmitter_radio_id"] == 11


def test_intercom_signal_dis6_rows_expose_decoded_fields_and_preserve_payload() -> None:
    signal = fastdis.parse_semantic_pdu(_packet(6, 31, 4, body=_intercom_signal_dis6_body()))
    assert signal is not None
    assert signal.semantic_level == "semantic_decoded"
    assert signal.descriptor.fully_domain_decoded
    assert signal.semantic_fields["entity_id"] == {"site": 1, "application": 2, "entity": 3}
    assert signal.semantic_fields["communications_device_id"] == 12
    assert signal.semantic_fields["encoding_scheme"] == 0x2122
    assert signal.semantic_fields["tdl_type"] == 0x2324
    assert signal.semantic_fields["sample_rate"] == 16000
    assert signal.semantic_fields["data_length"] == 12
    assert signal.semantic_fields["samples"] == 1
    assert signal.semantic_fields["data_bytes"] == bytes.fromhex("2122232425262728")


def test_intercom_signal_dis7_rows_expose_decoded_fields_and_preserve_payload() -> None:
    signal = fastdis.parse_semantic_pdu(_packet(7, 31, 4, body=_intercom_signal_dis7_body()))
    assert signal is not None
    assert signal.semantic_level == "semantic_decoded"
    assert signal.descriptor.fully_domain_decoded
    assert signal.semantic_fields["entity_id"] == {"site": 1, "application": 2, "entity": 3}
    assert signal.semantic_fields["communications_device_id"] == 13
    assert signal.semantic_fields["encoding_scheme"] == 0x3132
    assert signal.semantic_fields["tdl_type"] == 0x3334
    assert signal.semantic_fields["sample_rate"] == 8000
    assert signal.semantic_fields["data_length"] == 8
    assert signal.semantic_fields["samples"] == 1
    assert signal.semantic_fields["data_bytes"] == bytes.fromhex("3132333435363738")


def test_event_report_reliable_rows_expose_decoded_fields_and_preserve_tail() -> None:
    event_report = fastdis.parse_semantic_pdu(_packet(7, 61, 10, body=_event_report_reliable_body()))
    assert event_report is not None
    assert event_report.semantic_level == "semantic_decoded"
    assert event_report.descriptor.fully_domain_decoded
    assert event_report.semantic_fields["event_type"] == 0x71727374
    assert event_report.semantic_fields["pad1"] == 0
    assert event_report.semantic_fields["number_of_fixed_datum_records"] == 3
    assert event_report.semantic_fields["number_of_variable_datum_records"] == 1
    assert event_report.semantic_fields["datum_record_bytes"] == bytes.fromhex("7172737475767778797a7b7c7d7e7f80")


def test_record_reliable_rows_expose_decoded_fields_and_preserve_tail() -> None:
    record = fastdis.parse_semantic_pdu(_packet(6, 63, 10, body=_record_reliable_body()))
    assert record is not None
    assert record.semantic_level == "semantic_decoded"
    assert record.descriptor.fully_domain_decoded
    assert record.semantic_fields["request_id"] == 0x71727374
    assert record.semantic_fields["required_reliability_service"] == 7
    assert record.semantic_fields["pad1"] == 0
    assert record.semantic_fields["event_type"] == 0x0102
    assert record.semantic_fields["number_of_record_sets"] == 2
    assert record.semantic_fields["record_set_bytes"] == bytes.fromhex("7172737475767778797a7b7c7d7e7f80")

    record_dis7 = fastdis.parse_semantic_pdu(_packet(7, 63, 10, body=_record_reliable_body()))
    assert record_dis7 is not None
    assert record_dis7.semantic_level == "semantic_decoded"
    assert record_dis7.descriptor.fully_domain_decoded
    assert record_dis7.semantic_fields["originating_entity_id"] == record.semantic_fields["originating_entity_id"]
    assert record_dis7.semantic_fields["receiving_entity_id"] == record.semantic_fields["receiving_entity_id"]
    assert record_dis7.semantic_fields["request_id"] == record.semantic_fields["request_id"]
    assert record_dis7.semantic_fields["required_reliability_service"] == record.semantic_fields["required_reliability_service"]
    assert record_dis7.semantic_fields["pad1"] == record.semantic_fields["pad1"]
    assert record_dis7.semantic_fields["event_type"] == record.semantic_fields["event_type"]
    assert record_dis7.semantic_fields["number_of_record_sets"] == record.semantic_fields["number_of_record_sets"]
    assert record_dis7.semantic_fields["record_set_bytes"] == record.semantic_fields["record_set_bytes"]


def test_set_record_reliable_rows_expose_decoded_fields_and_preserve_tail() -> None:
    set_record = fastdis.parse_semantic_pdu(_packet(6, 64, 10, body=_set_record_reliable_body()))
    assert set_record is not None
    assert set_record.semantic_level == "semantic_decoded"
    assert set_record.descriptor.fully_domain_decoded
    assert set_record.semantic_fields["request_id"] == 0x81828384
    assert set_record.semantic_fields["required_reliability_service"] == 8
    assert set_record.semantic_fields["pad1"] == 0
    assert set_record.semantic_fields["pad2"] == 0
    assert set_record.semantic_fields["number_of_record_sets"] == 2
    assert set_record.semantic_fields["record_set_bytes"] == bytes.fromhex("8182838485868788898a8b8c8d8e8f90")


def test_set_record_reliable_dis7_rows_expose_decoded_fields_and_preserve_tail() -> None:
    set_record = fastdis.parse_semantic_pdu(_packet(7, 64, 10, body=_set_record_reliable_body()))
    assert set_record is not None
    assert set_record.semantic_level == "semantic_decoded"
    assert set_record.descriptor.fully_domain_decoded
    assert set_record.semantic_fields["request_id"] == 0x81828384
    assert set_record.semantic_fields["required_reliability_service"] == 8
    assert set_record.semantic_fields["pad1"] == 0
    assert set_record.semantic_fields["pad2"] == 0
    assert set_record.semantic_fields["number_of_record_sets"] == 2
    assert set_record.semantic_fields["record_set_bytes"] == bytes.fromhex("8182838485868788898a8b8c8d8e8f90")


def test_record_query_reliable_rows_expose_decoded_fields_and_preserve_tail() -> None:
    record_query = fastdis.parse_semantic_pdu(_packet(7, 65, 10, body=_record_query_reliable_body()))
    assert record_query is not None
    assert record_query.semantic_level == "semantic_decoded"
    assert record_query.descriptor.fully_domain_decoded
    assert record_query.semantic_fields["request_id"] == 0x91929394
    assert record_query.semantic_fields["required_reliability_service"] == 9
    assert record_query.semantic_fields["pad1"] == 0
    assert record_query.semantic_fields["pad2"] == 0
    assert record_query.semantic_fields["event_type"] == 0xA1A2A3A4
    assert record_query.semantic_fields["time"] == {"hour": 654321, "time_past_hour": 9876}
    assert record_query.semantic_fields["number_of_records"] == 3
    assert record_query.semantic_fields["record_id_bytes"] == bytes.fromhex("9192939495969798999a9b9c9d9e9fa0")


def test_information_operations_action_dis7_rows_expose_decoded_fields_and_preserve_tail() -> None:
    action = fastdis.parse_semantic_pdu(_packet(7, 70, 13, body=_information_operations_action_dis7_body()))
    assert action is not None
    assert action.semantic_level == "semantic_decoded"
    assert action.descriptor.fully_domain_decoded
    assert action.semantic_fields["originating_sim_id"] == {"site": 1, "application": 2, "entity": 3}
    assert action.semantic_fields["receiving_sim_id"] == {"site": 4, "application": 5, "entity": 6}
    assert action.semantic_fields["request_id"] == 0x21222324
    assert action.semantic_fields["io_warfare_type"] == 11
    assert action.semantic_fields["io_simulation_source"] == 12
    assert action.semantic_fields["io_action_type"] == 13
    assert action.semantic_fields["io_action_phase"] == 14
    assert action.semantic_fields["padding1"] == 0x31323334
    assert action.semantic_fields["io_attacker_id"] == {"site": 7, "application": 8, "entity": 9}
    assert action.semantic_fields["io_primary_target_id"] == {"site": 10, "application": 11, "entity": 12}
    assert action.semantic_fields["padding2"] == 0
    assert action.semantic_fields["number_of_io_records"] == 2
    assert action.semantic_fields["io_record_bytes"] == bytes.fromhex("4142434445464748494a4b4c4d4e4f50")


def test_information_operations_report_dis7_rows_expose_decoded_fields_and_preserve_tail() -> None:
    report = fastdis.parse_semantic_pdu(_packet(7, 71, 13, body=_information_operations_report_dis7_body()))
    assert report is not None
    assert report.semantic_level == "semantic_decoded"
    assert report.descriptor.fully_domain_decoded
    assert report.semantic_fields["originating_sim_id"] == {"site": 21, "application": 22, "entity": 23}
    assert report.semantic_fields["io_sim_source"] == 31
    assert report.semantic_fields["io_report_type"] == 32
    assert report.semantic_fields["padding1"] == 0
    assert report.semantic_fields["io_attacker_id"] == {"site": 24, "application": 25, "entity": 26}
    assert report.semantic_fields["io_primary_target_id"] == {"site": 27, "application": 28, "entity": 29}
    assert report.semantic_fields["padding2"] == 0
    assert report.semantic_fields["padding3"] == 0
    assert report.semantic_fields["number_of_io_records"] == 2
    assert report.semantic_fields["io_record_bytes"] == bytes.fromhex("5152535455565758595a5b5c5d5e5f60")


def test_live_entity_tspi_rows_expose_decoded_fields_and_preserve_tail() -> None:
    tspi = fastdis.parse_semantic_pdu(_packet(6, 46, 11, body=_live_entity_tspi_body()))
    assert tspi is not None
    assert tspi.semantic_level == "semantic_decoded"
    assert tspi.descriptor.fully_domain_decoded
    assert tspi.semantic_fields["live_entity_id"] == {"site": 1, "application": 2, "entity": 3}
    assert tspi.semantic_fields["tspi_flag"] == 7
    assert tspi.semantic_fields["live_entity_state_bytes"] == bytes.fromhex("6162636465666768696a6b6c6d6e6f70")

    tspi_dis7 = fastdis.parse_semantic_pdu(_packet(7, 46, 11, body=_live_entity_tspi_body()))
    assert tspi_dis7 is not None
    assert tspi_dis7.semantic_fields["live_entity_id"] == tspi.semantic_fields["live_entity_id"]
    assert tspi_dis7.semantic_fields["tspi_flag"] == tspi.semantic_fields["tspi_flag"]
    assert tspi_dis7.semantic_fields["live_entity_state_bytes"] == tspi.semantic_fields["live_entity_state_bytes"]


def test_live_entity_appearance_rows_expose_decoded_fields_and_preserve_tail() -> None:
    appearance = fastdis.parse_semantic_pdu(_packet(6, 47, 11, body=_live_entity_appearance_body()))
    assert appearance is not None
    assert appearance.semantic_level == "semantic_decoded"
    assert appearance.descriptor.fully_domain_decoded
    assert appearance.semantic_fields["live_entity_id"] == {"site": 4, "application": 5, "entity": 6}
    assert appearance.semantic_fields["appearance_flags"] == 0x3132
    assert appearance.semantic_fields["force_id"] == 9
    assert appearance.semantic_fields["appearance_payload_bytes"] == bytes.fromhex("7172737475767778797a7b7c7d7e7f80")

    appearance_dis7 = fastdis.parse_semantic_pdu(_packet(7, 47, 11, body=_live_entity_appearance_body()))
    assert appearance_dis7 is not None
    assert appearance_dis7.semantic_fields["force_id"] == appearance.semantic_fields["force_id"]
    assert appearance_dis7.semantic_fields["appearance_payload_bytes"] == appearance.semantic_fields["appearance_payload_bytes"]


def test_live_entity_articulated_parts_rows_expose_decoded_fields_and_preserve_tail() -> None:
    articulated = fastdis.parse_semantic_pdu(_packet(6, 48, 11, body=_live_entity_articulated_parts_body()))
    assert articulated is not None
    assert articulated.semantic_level == "semantic_decoded"
    assert articulated.descriptor.fully_domain_decoded
    assert articulated.semantic_fields["live_entity_id"] == {"site": 7, "application": 8, "entity": 9}
    assert articulated.semantic_fields["number_of_parameter_records"] == 2
    assert articulated.semantic_fields["variable_parameter_bytes"] == bytes.fromhex("8182838485868788898a8b8c8d8e8f90")

    articulated_dis7 = fastdis.parse_semantic_pdu(_packet(7, 48, 11, body=_live_entity_articulated_parts_body()))
    assert articulated_dis7 is not None
    assert articulated_dis7.semantic_fields["number_of_parameter_records"] == articulated.semantic_fields["number_of_parameter_records"]
    assert articulated_dis7.semantic_fields["variable_parameter_bytes"] == articulated.semantic_fields["variable_parameter_bytes"]


def test_live_entity_fire_rows_expose_decoded_fields_and_preserve_tail() -> None:
    fire = fastdis.parse_semantic_pdu(_packet(6, 49, 11, body=_live_entity_fire_body()))
    assert fire is not None
    assert fire.semantic_level == "semantic_decoded"
    assert fire.descriptor.fully_domain_decoded
    assert fire.semantic_fields["firing_live_entity_id"] == {"site": 10, "application": 11, "entity": 12}
    assert fire.semantic_fields["flags"] == 3
    assert fire.semantic_fields["target_live_entity_id"] == {"site": 13, "application": 14, "entity": 15}
    assert fire.semantic_fields["munition_live_entity_id"] == {"site": 16, "application": 17, "entity": 18}
    assert fire.semantic_fields["event_id"] == {"site": 19, "application": 20, "event_number": 21}
    assert fire.semantic_fields["live_entity_fire_bytes"] == bytes.fromhex("9192939495969798999a9b9c9d9e9fa0")

    fire_dis7 = fastdis.parse_semantic_pdu(_packet(7, 49, 11, body=_live_entity_fire_body()))
    assert fire_dis7 is not None
    assert fire_dis7.semantic_fields["flags"] == fire.semantic_fields["flags"]
    assert fire_dis7.semantic_fields["live_entity_fire_bytes"] == fire.semantic_fields["live_entity_fire_bytes"]


def test_live_entity_detonation_rows_expose_decoded_fields_and_preserve_tail() -> None:
    detonation = fastdis.parse_semantic_pdu(_packet(6, 50, 11, body=_live_entity_detonation_body()))
    assert detonation is not None
    assert detonation.semantic_level == "semantic_decoded"
    assert detonation.descriptor.fully_domain_decoded
    assert detonation.semantic_fields["firing_live_entity_id"] == {"site": 22, "application": 23, "entity": 24}
    assert detonation.semantic_fields["detonation_flag1"] == 4
    assert detonation.semantic_fields["detonation_flag2"] == 5
    assert detonation.semantic_fields["target_live_entity_id"] == {"site": 25, "application": 26, "entity": 27}
    assert detonation.semantic_fields["munition_live_entity_id"] == {"site": 28, "application": 29, "entity": 30}
    assert detonation.semantic_fields["event_id"] == {"site": 31, "application": 32, "event_number": 33}
    assert detonation.semantic_fields["live_entity_detonation_bytes"] == bytes.fromhex("a1a2a3a4a5a6a7a8a9aaabacadaeafb0")

    detonation_dis7 = fastdis.parse_semantic_pdu(_packet(7, 50, 11, body=_live_entity_detonation_body()))
    assert detonation_dis7 is not None
    assert detonation_dis7.semantic_fields["detonation_flag1"] == detonation.semantic_fields["detonation_flag1"]
    assert detonation_dis7.semantic_fields["live_entity_detonation_bytes"] == detonation.semantic_fields["live_entity_detonation_bytes"]


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


def test_entity_damage_status_rows_expose_decoded_core_and_preserve_records() -> None:
    damage_status = fastdis.parse_semantic_pdu(_packet(7, 69, 2, body=_entity_damage_status_body()))
    assert damage_status is not None
    assert damage_status.semantic_level == "semantic_decoded"
    assert damage_status.descriptor.fully_domain_decoded
    assert damage_status.semantic_fields["semantic_decode_status"] == "decoded"
    assert damage_status.semantic_fields["firing_entity_id"] == {"site": 1, "application": 2, "entity": 3}
    assert damage_status.semantic_fields["target_entity_id"] == {"site": 4, "application": 5, "entity": 6}
    assert damage_status.semantic_fields["damaged_entity_id"] == {"site": 7, "application": 8, "entity": 9}
    assert damage_status.semantic_fields["number_of_damage_description"] == 2
    assert damage_status.semantic_fields["damage_description_record_bytes"] == bytes.fromhex("deadbeef00112233445566778899aabb")
    assert damage_status.diagnostics == ("full domain decode available",)


def test_entity_state_rows_are_fully_decoded() -> None:
    entity_state = fastdis.parse_semantic_pdu(_packet(7, 1, 1, body=b"\x00" * 132))
    assert entity_state is not None
    assert entity_state.semantic_level == "semantic_decoded"
    assert entity_state.descriptor.fully_domain_decoded
    assert entity_state.semantic_fields["semantic_decode_status"] == "decoded"


def test_generate_semantic_pdu_parsers_check_passes_for_current_tree() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "generate_semantic_pdu_parsers.py"), "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
