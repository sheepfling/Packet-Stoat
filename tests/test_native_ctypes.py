from __future__ import annotations

import json
import os
import struct
from pathlib import Path

import pytest

import fastdis.native as native

ROOT = Path(__file__).resolve().parents[1]


def _make_pdu(version: int, pdu_type: int, *, length: int = 12, status: int = 0, padding: int = 0) -> bytes:
    header = bytearray(12)
    header[0] = version
    header[1] = 3
    header[2] = pdu_type
    header[3] = 1
    header[4:8] = (0x01020304).to_bytes(4, "big")
    header[8:10] = length.to_bytes(2, "big")
    if version >= 7:
        header[10] = status & 0xFF
        header[11] = padding & 0xFF
    else:
        header[10:12] = padding.to_bytes(2, "big")
    return bytes(header) + b"x" * max(0, length - 12)


def _make_entity_state(version: int = 7, force_id: int = 2, *, length: int = native.FASTDIS_ENTITY_STATE_FIXED_SIZE) -> bytes:
    packet = bytearray(_make_pdu(version, native.FASTDIS_ENTITY_STATE_PDU_TYPE, length=length, status=0x80))
    if len(packet) < native.FASTDIS_ENTITY_STATE_FIXED_SIZE:
        packet.extend(b"\x00" * (native.FASTDIS_ENTITY_STATE_FIXED_SIZE - len(packet)))
    b = 12
    packet[b + 0 : b + 6] = struct.pack(">HHH", 0x1111, 0x2222, 0x3333)
    packet[b + 6] = force_id
    packet[b + 7] = 0
    packet[b + 8 : b + 16] = struct.pack(">BBHBBBB", 1, 2, 840, 3, 4, 5, 6)
    packet[b + 16 : b + 24] = struct.pack(">BBHBBBB", 9, 8, 124, 7, 6, 5, 4)
    packet[b + 24 : b + 36] = struct.pack(">fff", 1.25, -2.5, 3.75)
    packet[b + 36 : b + 60] = struct.pack(">ddd", 10.0, 20.0, 30.0)
    packet[b + 60 : b + 72] = struct.pack(">fff", 0.1, 0.2, 0.3)
    packet[b + 72 : b + 76] = (0xAABBCCDD).to_bytes(4, "big")
    packet[b + 76] = 4
    packet[b + 77 : b + 92] = bytes(range(1, 16))
    packet[b + 92 : b + 104] = struct.pack(">fff", 0.5, 0.6, 0.7)
    packet[b + 104 : b + 116] = struct.pack(">fff", 1.5, 1.6, 1.7)
    packet[b + 116] = 1
    packet[b + 117 : b + 128] = b"TANK001\x00\x00\x00\x00"
    packet[b + 128 : b + 132] = (0x01020304).to_bytes(4, "big")
    return bytes(packet[:length])


def _make_create_entity(version: int = 7) -> bytes:
    packet = bytearray(_make_pdu(version, native.FASTDIS_CREATE_ENTITY_PDU_TYPE, length=native.FASTDIS_CREATE_ENTITY_FIXED_SIZE))
    packet[3] = 5
    b = 12
    packet[b + 0 : b + 6] = struct.pack(">HHH", 0x1111, 0x2222, 0x3333)
    packet[b + 6 : b + 12] = struct.pack(">HHH", 0x4444, 0x5555, 0x6666)
    packet[b + 12 : b + 16] = (0xA0B0C0D0).to_bytes(4, "big")
    return bytes(packet)


def _make_remove_entity(version: int = 7) -> bytes:
    packet = bytearray(_make_pdu(version, native.FASTDIS_REMOVE_ENTITY_PDU_TYPE, length=native.FASTDIS_REMOVE_ENTITY_FIXED_SIZE))
    packet[3] = 5
    b = 12
    packet[b + 0 : b + 6] = struct.pack(">HHH", 0x1111, 0x2222, 0x3333)
    packet[b + 6 : b + 12] = struct.pack(">HHH", 0x4444, 0x5555, 0x6666)
    packet[b + 12 : b + 16] = (0x0BADF00D).to_bytes(4, "big")
    return bytes(packet)


def _make_start_resume(version: int = 7) -> bytes:
    packet = bytearray(_make_pdu(version, native.FASTDIS_START_RESUME_PDU_TYPE, length=native.FASTDIS_START_RESUME_FIXED_SIZE))
    packet[3] = 5
    b = 12
    packet[b + 0 : b + 6] = struct.pack(">HHH", 0x1111, 0x2222, 0x3333)
    packet[b + 6 : b + 12] = struct.pack(">HHH", 0x4444, 0x5555, 0x6666)
    packet[b + 12 : b + 20] = struct.pack(">II", 7, 123456)
    packet[b + 20 : b + 28] = struct.pack(">II", 9, 654321)
    packet[b + 28 : b + 32] = (0x01020304).to_bytes(4, "big")
    return bytes(packet)


def _make_stop_freeze(version: int = 7) -> bytes:
    packet = bytearray(_make_pdu(version, native.FASTDIS_STOP_FREEZE_PDU_TYPE, length=native.FASTDIS_STOP_FREEZE_FIXED_SIZE))
    packet[3] = 5
    b = 12
    packet[b + 0 : b + 6] = struct.pack(">HHH", 0x1111, 0x2222, 0x3333)
    packet[b + 6 : b + 12] = struct.pack(">HHH", 0x4444, 0x5555, 0x6666)
    packet[b + 12 : b + 20] = struct.pack(">II", 5, 7654321)
    packet[b + 20] = 3
    packet[b + 21] = 4
    packet[b + 22 : b + 24] = (0xABCD).to_bytes(2, "big")
    packet[b + 24 : b + 28] = (0x0F1E2D3C).to_bytes(4, "big")
    return bytes(packet)


def _has_native_library() -> bool:
    return bool(os.environ.get("FASTDIS_LIBRARY") or native.find_native_library())


@pytest.mark.skipif(not _has_native_library(), reason="fastdis shared library is not built")
def test_ctypes_parse_header_tuple() -> None:
    lib = native.load_native()
    assert lib.abi_version() == native.FASTDIS_ABI_VERSION
    assert lib.abi_epoch() == native.FASTDIS_ABI_EPOCH == 0
    assert lib.abi_revision() == native.FASTDIS_ABI_REVISION == 10
    assert lib.parse_header_tuple(_make_pdu(7, 1, status=0x80)) == (7, 3, 1, 1, 0x01020304, 12, 0x80, 0)
    assert lib.parse_header_tuple(_make_pdu(6, 1, padding=0x1234)) == (6, 3, 1, 1, 0x01020304, 12, -1, 0x1234)


@pytest.mark.skipif(not _has_native_library(), reason="fastdis shared library is not built")
def test_ctypes_header_status_padding_properties() -> None:
    dis7 = native.FastDisHeader(
        native.FASTDIS_PROTOCOL_VERSION_DIS7,
        3,
        1,
        1,
        0x01020304,
        12,
        0x80,
        0x44,
        0,
    )
    assert dis7.has_pdu_status
    assert dis7.pdu_status == 0x80
    assert dis7.padding_octet == 0x44
    assert dis7.legacy_padding is None

    dis6 = native.FastDisHeader(
        native.FASTDIS_PROTOCOL_VERSION_DIS6,
        3,
        1,
        1,
        0x01020304,
        12,
        native.FASTDIS_HEADER_STATUS_UNAVAILABLE,
        0x1234,
        0,
    )
    assert not dis6.has_pdu_status
    assert dis6.pdu_status is None
    assert dis6.padding_octet is None
    assert dis6.legacy_padding == 0x1234


@pytest.mark.skipif(not _has_native_library(), reason="fastdis shared library is not built")
def test_ctypes_allow_truncated_flag() -> None:
    lib = native.load_native()
    packet = _make_pdu(7, 1, length=16)[:12]
    with pytest.raises(native.FastDisError):
        lib.parse_header_tuple(packet)
    assert lib.parse_header_tuple(packet, flags=native.FASTDIS_FLAG_ALLOW_TRUNCATED)[5] == 16


@pytest.mark.skipif(not _has_native_library(), reason="fastdis shared library is not built")
def test_ctypes_scan_packets_filters_and_downsamples() -> None:
    lib = native.load_native()
    packets = [
        _make_pdu(7, 1),
        _make_pdu(7, 2),
        b"bad",
        _make_pdu(7, 1),
        _make_pdu(7, 1),
    ]
    called: list[tuple[tuple[int, int, int, int, int, int, int, int], object]] = []

    stats = lib.scan_many(
        packets,
        lambda version, exercise_id, pdu_type, protocol_family, timestamp, length, status, packet: called.append(
            ((version, exercise_id, pdu_type, protocol_family, timestamp, length, status), packet)
        ),
        versions=7,
        pdu_types=1,
        sample_every=2,
        return_stats=True,
    )

    assert stats == {"seen": 5, "malformed": 1, "accepted": 3, "emitted": 2}
    assert len(called) == 2
    assert called[0][0][0:3] == (7, 3, 1)
    assert called[0][1] is packets[0]
    assert called[1][1] is packets[4]


@pytest.mark.skipif(not _has_native_library(), reason="fastdis shared library is not built")
def test_ctypes_parse_entity_state_prefix() -> None:
    lib = native.load_native()
    entity = lib.parse_entity_state_prefix(_make_entity_state())
    assert entity.header[0:4] == (7, 3, 1, 1)
    assert entity.entity_id == (0x1111, 0x2222, 0x3333)
    assert entity.force_id == 2
    assert entity.variable_parameter_count == 0
    assert entity.entity_type == (1, 2, 840, 3, 4, 5, 6)
    assert entity.alternate_entity_type == (9, 8, 124, 7, 6, 5, 4)
    assert entity.linear_velocity == pytest.approx((1.25, -2.5, 3.75))
    assert entity.location == pytest.approx((10.0, 20.0, 30.0))
    assert entity.orientation == pytest.approx((0.1, 0.2, 0.3))
    assert entity.appearance == 0xAABBCCDD
    assert entity.dead_reckoning_algorithm == 4
    assert entity.dead_reckoning_parameters == bytes(range(1, 16))
    assert entity.dead_reckoning_linear_acceleration == pytest.approx((0.5, 0.6, 0.7))
    assert entity.dead_reckoning_angular_velocity == pytest.approx((1.5, 1.6, 1.7))
    assert entity.marking_character_set == 1
    assert entity.marking_text == "TANK001"
    assert entity.capabilities == 0x01020304
    assert entity.has_field(native.FASTDIS_ES_FIELD_ALL)


@pytest.mark.skipif(not _has_native_library(), reason="fastdis shared library is not built")
def test_ctypes_scan_entity_state_filters_force_id() -> None:
    lib = native.load_native()
    packets = [
        _make_entity_state(force_id=2),
        _make_entity_state(force_id=3),
        _make_pdu(7, 2, length=native.FASTDIS_ENTITY_STATE_FIXED_SIZE),
        _make_entity_state(force_id=2)[:64],
    ]
    called: list[tuple[native.EntityStatePrefix, object]] = []

    stats = lib.scan_entity_state_many(
        packets,
        lambda entity, packet: called.append((entity, packet)),
        versions=7,
        entity_force_ids=2,
        return_stats=True,
    )

    assert stats == {"seen": 4, "malformed": 1, "accepted": 1, "emitted": 1}
    assert len(called) == 1
    assert called[0][0].force_id == 2
    assert called[0][0].entity_id == (0x1111, 0x2222, 0x3333)
    assert called[0][1] is packets[0]



@pytest.mark.skipif(not _has_native_library(), reason="fastdis shared library is not built")
def test_ctypes_entity_state_field_subscription() -> None:
    lib = native.load_native()
    entity = lib.parse_entity_state_fields(
        _make_entity_state(),
        fields=native.FASTDIS_ES_FIELD_LOCATION | native.FASTDIS_ES_FIELD_ORIENTATION,
    )
    assert entity.has_field(native.FASTDIS_ES_FIELD_HEADER)
    assert entity.has_field(native.FASTDIS_ES_FIELD_FORCE_ID)
    assert entity.has_field(native.FASTDIS_ES_FIELD_LOCATION | native.FASTDIS_ES_FIELD_ORIENTATION)
    assert not entity.has_field(native.FASTDIS_ES_FIELD_ENTITY_TYPE)
    assert entity.force_id == 2
    assert entity.entity_id == (0, 0, 0)
    assert entity.location == pytest.approx((10.0, 20.0, 30.0))
    assert entity.orientation == pytest.approx((0.1, 0.2, 0.3))
    assert entity.appearance == 0

    packets = [_make_entity_state(force_id=2), _make_entity_state(force_id=2)]
    called: list[native.EntityStatePrefix] = []
    stats = lib.scan_entity_state_many(
        packets,
        lambda entity, packet: called.append(entity),
        entity_state_fields=native.FASTDIS_ES_FIELD_LOCATION,
        return_stats=True,
    )
    assert stats == {"seen": 2, "malformed": 0, "accepted": 2, "emitted": 2}
    assert len(called) == 2
    assert called[0].has_field(native.FASTDIS_ES_FIELD_LOCATION)
    assert not called[0].has_field(native.FASTDIS_ES_FIELD_ORIENTATION)
    assert called[0].orientation == pytest.approx((0.0, 0.0, 0.0))


@pytest.mark.skipif(not _has_native_library(), reason="fastdis shared library is not built")
def test_ctypes_scanner_entity_id_allow_and_block() -> None:
    lib = native.load_native()
    p1 = bytearray(_make_entity_state(force_id=2))
    p2 = bytearray(_make_entity_state(force_id=2))
    p2[12:18] = struct.pack(">HHH", 0x9999, 0x2222, 0x3333)
    packets = [bytes(p1), bytes(p2)]

    scanner = lib.create_scanner(
        versions=7,
        entity_state_fields=native.FASTDIS_ES_FIELD_LOCATION | native.FASTDIS_ES_FIELD_ORIENTATION,
    )
    try:
        assert scanner.entity_id_count() == 0
        scanner.allow_entity_ids((0x1111, 0x2222, 0x3333))
        assert scanner.get_entity_id_filter_mode() == native.FASTDIS_ENTITY_ID_FILTER_ALLOW
        assert scanner.contains_entity_id(0x1111, 0x2222, 0x3333)
        assert scanner.entity_id_count() == 1

        called: list[native.EntityStatePrefix] = []
        stats = scanner.scan_entity_state_many(packets, lambda entity, packet: called.append(entity), return_stats=True)
        assert stats == {"seen": 2, "malformed": 0, "accepted": 1, "emitted": 1}
        assert len(called) == 1
        assert called[0].entity_id == (0x1111, 0x2222, 0x3333)
        assert called[0].has_field(native.FASTDIS_ES_FIELD_ENTITY_ID)
        assert called[0].has_field(native.FASTDIS_ES_FIELD_LOCATION)
        assert not called[0].has_field(native.FASTDIS_ES_FIELD_MARKING)

        scanner.block_entity_ids((0x1111, 0x2222, 0x3333))
        called.clear()
        stats = scanner.scan_entity_state_many(packets, lambda entity, packet: called.append(entity), return_stats=True)
        assert stats == {"seen": 2, "malformed": 0, "accepted": 1, "emitted": 1}
        assert len(called) == 1
        assert called[0].entity_id == (0x9999, 0x2222, 0x3333)
    finally:
        scanner.close()


@pytest.mark.skipif(not _has_native_library(), reason="fastdis shared library is not built")
def test_ctypes_generic_config_and_scanner_filter_helpers() -> None:
    lib = native.load_native()
    config = lib.new_config()
    lib.set_config_filter(config, "versions", [6, 7])
    lib.set_config_filter(config, "pdu_types", 1)
    assert lib.config_filter_contains(config, "versions", 6)
    assert lib.config_filter_contains(config, "versions", 7)
    assert not lib.config_filter_contains(config, "versions", 5)
    assert lib.config_filter_contains(config, native.FASTDIS_FILTER_PDU_TYPE, 1)
    assert not lib.config_filter_contains(config, native.FASTDIS_FILTER_PDU_TYPE, 2)

    scanner = lib.create_scanner(config)
    try:
        assert scanner.filter_contains("versions", 7)
        assert not scanner.filter_contains("pdu_types", 2)
        returned = scanner.only_pdu_types([1, 2]).only_protocol_families(1).only_exercise_ids([3]).only_entity_force_ids([1, 2])
        assert returned is scanner
        assert scanner.filter_contains("pdu_types", 2)
        assert scanner.filter_contains("families", 1)
        assert scanner.filter_contains("exercise_ids", 3)
        assert scanner.filter_contains("force_ids", 2)
        assert not scanner.filter_contains("force_ids", 3)
        scanner.only_entity_force_ids(None)
        assert scanner.filter_contains("force_ids", 3)
        scanner.only_entity_force_ids([1, 2])
        scanner.set_sample(5, 1).set_entity_state_fields("pose")
        updated = scanner.get_config()
        assert updated.sample_every == 5
        assert updated.sample_offset == 1
        assert updated.entity_state_fields & native.FASTDIS_ES_FIELD_POSE

        assert native.entity_state_field_mask("location", "orientation") == (
            native.FASTDIS_ES_FIELD_LOCATION | native.FASTDIS_ES_FIELD_ORIENTATION
        )
        assert scanner.set_entity_ids(native.FASTDIS_ENTITY_ID_FILTER_ALLOW, [(100, 1, 42), (100, 1, 43)]) is scanner
        assert scanner.entity_id_count() == 2
        assert scanner.contains_entity_id(100, 1, 42)
        assert scanner.add_entity_ids((100, 1, 44)) is scanner
        assert scanner.entity_id_count() == 3
        assert scanner.disable_entity_id_filter() is scanner
        assert scanner.get_entity_id_filter_mode() == native.FASTDIS_ENTITY_ID_FILTER_DISABLED
    finally:
        scanner.close()


@pytest.mark.skipif(not _has_native_library(), reason="fastdis shared library is not built")
def test_ctypes_transform_and_batch_outputs() -> None:
    lib = native.load_native()
    p1 = bytearray(_make_entity_state(force_id=2))
    p2 = bytearray(_make_entity_state(force_id=2))
    p2[12:18] = struct.pack(">HHH", 0x9999, 0x2222, 0x3333)
    packets = [bytes(p1), bytes(p2)]

    transform = lib.parse_entity_transform(packets[0])
    assert transform.entity_id == (0x1111, 0x2222, 0x3333)
    assert transform.force_id == 2
    assert transform.exercise_id == 3
    assert transform.version == 7
    assert transform.timestamp == 0x01020304
    assert transform.appearance == 0xAABBCCDD
    assert transform.location == pytest.approx((10.0, 20.0, 30.0))
    assert transform.orientation == pytest.approx((0.1, 0.2, 0.3))
    assert transform.linear_velocity == pytest.approx((1.25, -2.5, 3.75))
    assert transform.dead_reckoning_algorithm == native.FASTDIS_DR_RVW
    assert transform.dead_reckoning_parameters == bytes(range(1, 16))
    assert transform.dead_reckoning_linear_acceleration == pytest.approx((0.5, 0.6, 0.7))
    assert transform.dead_reckoning_angular_velocity == pytest.approx((1.5, 1.6, 1.7))
    assert lib.dead_reckoning_algorithm_name(native.FASTDIS_DR_RVW) == "DRM_RVW"
    assert lib.dead_reckoning_algorithm_known(native.FASTDIS_DR_FVB) is True
    assert lib.dead_reckoning_algorithm_known(10) is False
    for algorithm in range(native.FASTDIS_DR_OTHER, native.FASTDIS_DR_FVB + 1):
        variant = transform._replace(dead_reckoning_algorithm=algorithm)
        assert lib.extrapolate_transform_dead_reckoning(variant, 1.0).entity_id == transform.entity_id
    dead_reckoned_transform = lib.extrapolate_transform_dead_reckoning(transform, 2.0)
    assert dead_reckoned_transform.location == pytest.approx((13.5, 16.2, 38.9))
    assert dead_reckoned_transform.orientation == pytest.approx((3.1, 3.4, 3.7))

    config = lib.new_config()
    lib.use_config_profile(config, "pose")
    records, meta = lib.scan_entity_state_to_batch(packets, config=config, capacity=1, return_stats=True)
    assert meta == {"seen": 2, "malformed": 0, "accepted": 2, "emitted": 2, "stored": 1, "dropped": 1, "capacity": 1}
    assert len(records) == 1
    assert records[0].entity_id == (0x1111, 0x2222, 0x3333)
    assert records[0].location == pytest.approx((10.0, 20.0, 30.0))

    transform_config = lib.new_config()
    lib.use_config_profile(transform_config, native.FASTDIS_PROFILE_ENTITY_TRANSFORM)
    transforms, meta = lib.scan_entity_transforms_to_batch(packets, config=transform_config, return_stats=True)
    assert meta["stored"] == 2
    assert meta["dropped"] == 0
    assert [x.entity_id for x in transforms] == [(0x1111, 0x2222, 0x3333), (0x9999, 0x2222, 0x3333)]


@pytest.mark.skipif(not _has_native_library(), reason="fastdis shared library is not built")
def test_ctypes_parse_simulation_management_pdus() -> None:
    lib = native.load_native()

    create = lib.parse_create_entity(_make_create_entity(7))
    assert create.header[0:4] == (7, 3, 11, 5)
    assert create.originating_entity_id == (0x1111, 0x2222, 0x3333)
    assert create.receiving_entity_id == (0x4444, 0x5555, 0x6666)
    assert create.request_id == 0xA0B0C0D0

    remove = lib.parse_remove_entity(_make_remove_entity(6))
    assert remove.header[0:4] == (6, 3, 12, 5)
    assert remove.request_id == 0x0BADF00D

    start = lib.parse_start_resume(_make_start_resume(7))
    assert start.header[0:4] == (7, 3, 13, 5)
    assert start.real_world_time == (7, 123456)
    assert start.simulation_time == (9, 654321)
    assert start.request_id == 0x01020304

    stop = lib.parse_stop_freeze(_make_stop_freeze(6))
    assert stop.header[0:4] == (6, 3, 14, 5)
    assert stop.real_world_time == (5, 7654321)
    assert stop.reason == 3
    assert stop.frozen_behavior == 4
    assert stop.padding1 == 0xABCD
    assert stop.request_id == 0x0F1E2D3C


@pytest.mark.skipif(not _has_native_library(), reason="fastdis shared library is not built")
def test_ctypes_dead_reckoning_engine_fixture_parity() -> None:
    lib = native.load_native()
    fixture = json.loads((ROOT / "tests" / "data" / "dead_reckoning_engine_cases.json").read_text(encoding="utf-8"))
    base = fixture["initial_transform"]
    template = lib.parse_entity_transform(_make_entity_state())
    template = template._replace(
        location=tuple(base["location_ecef_m"]),
        orientation=tuple(base["orientation_rad"]),
        linear_velocity=tuple(base["linear_velocity"]),
        dead_reckoning_linear_acceleration=tuple(base["linear_acceleration"]),
        dead_reckoning_angular_velocity=tuple(base["angular_velocity"]),
    )
    seconds = float(fixture["seconds"])
    for case in fixture["cases"]:
        transform = template._replace(dead_reckoning_algorithm=int(case["algorithm"]))
        actual = lib.extrapolate_transform_dead_reckoning(transform, seconds)
        assert actual.location == pytest.approx(tuple(case["expected_location_ecef_m"]), abs=1e-5)
        assert actual.orientation == pytest.approx(tuple(case["expected_orientation_rad"]), abs=1e-5)


@pytest.mark.skipif(not _has_native_library(), reason="fastdis shared library is not built")
def test_ctypes_scanner_profiles_and_transform_batch() -> None:
    lib = native.load_native()
    p1 = bytearray(_make_entity_state(force_id=2))
    p2 = bytearray(_make_entity_state(force_id=2))
    p2[12:18] = struct.pack(">HHH", 0x9999, 0x2222, 0x3333)
    packets = [bytes(p1), bytes(p2)]

    with lib.create_scanner() as scanner:
        scanner.use_entity_transform_profile().allow_entity_ids((0x1111, 0x2222, 0x3333))
        records, meta = scanner.scan_entity_transforms_to_batch(packets, return_stats=True)
        assert meta == {"seen": 2, "malformed": 0, "accepted": 1, "emitted": 1, "stored": 1, "dropped": 0, "capacity": 2}
        assert len(records) == 1
        assert records[0].entity_id == (0x1111, 0x2222, 0x3333)

        scanner.disable_entity_id_filter().use_entity_state_pose_profile()
        entities, meta = scanner.scan_entity_state_to_batch(packets, capacity=4, return_stats=True)
        assert meta["stored"] == 2
        assert meta["dropped"] == 0
        assert all(entity.has_field(native.FASTDIS_ES_FIELD_LOCATION | native.FASTDIS_ES_FIELD_ORIENTATION) for entity in entities)


@pytest.mark.skipif(not _has_native_library(), reason="fastdis shared library is not built")
def test_ctypes_entity_table_latest_state_changed_and_stale() -> None:
    lib = native.load_native()
    p1 = bytearray(_make_entity_state(force_id=2))
    p2 = bytearray(_make_entity_state(force_id=2))
    p2[12:18] = struct.pack(">HHH", 0x9999, 0x2222, 0x3333)

    scanner = lib.create_scanner().use_entity_transform_profile()
    table = lib.create_entity_table(reserve=8)
    try:
        stats = table.ingest(scanner, [bytes(p1), bytes(p2)], advance_tick=True)
        assert stats["scan"] == {"seen": 2, "malformed": 0, "accepted": 2, "emitted": 2}
        assert stats["table_updates"] == 2
        assert stats["new_entities"] == 2
        assert stats["changed_entities"] == 2
        assert stats["entity_count"] == 2
        assert table.size() == 2
        assert table.tick() == 1

        first = table.get((0x1111, 0x2222, 0x3333))
        assert first is not None
        assert first.transform.location == pytest.approx((10.0, 20.0, 30.0))
        assert first.first_seen_tick == 1
        assert first.last_seen_tick == 1
        assert first.has_change(native.FASTDIS_ENTITY_CHANGE_NEW)

        changed, meta = table.snapshot_changed(return_meta=True, clear=True)
        assert len(changed) == 2
        assert meta["stored"] == 2
        assert table.snapshot_changed() == []

        p1_changed = bytearray(_make_entity_state(force_id=2))
        p1_changed[12 + 36 : 12 + 60] = struct.pack(">ddd", 100.0, 20.0, 30.0)
        stats = table.ingest(scanner, [bytes(p1_changed)], advance_tick=True)
        assert stats["new_entities"] == 0
        assert stats["changed_entities"] == 1
        assert stats["unchanged_entities"] == 0
        assert table.tick() == 2

        first = table.get((0x1111, 0x2222, 0x3333))
        assert first is not None
        assert first.transform.location == pytest.approx((100.0, 20.0, 30.0))
        assert first.update_count == 2
        assert first.has_change(native.FASTDIS_ENTITY_CHANGE_UPDATED)

        table.advance_tick(3)
        stale = table.snapshot_stale(2)
        assert len(stale) == 2
        assert all(item.has_change(native.FASTDIS_ENTITY_CHANGE_STALE) for item in stale)

        removed, meta = table.evict_stale(2, capacity=1, return_meta=True)
        assert len(removed) == 1
        assert meta["dropped"] == 1
        assert table.size() == 0
        assert table.get((0x1111, 0x2222, 0x3333)) is None
    finally:
        table.close()
        scanner.close()


@pytest.mark.skipif(not _has_native_library(), reason="fastdis shared library is not built")
def test_ctypes_snapshot_buffer_double_buffer_handoff() -> None:
    lib = native.load_native()
    p1 = bytearray(_make_entity_state(force_id=2))
    p2 = bytearray(_make_entity_state(force_id=2))
    p2[12:18] = struct.pack(">HHH", 0x9999, 0x2222, 0x3333)

    with lib.create_scanner().use_entity_transform_profile() as scanner, lib.create_entity_table(reserve=8) as table:
        table.ingest(scanner, [bytes(p1), bytes(p2)], advance_tick=True)
        with lib.create_snapshot_buffer(4) as snapshots:
            assert snapshots.capacity() == 4
            assert snapshots.slot_count() == 2
            assert snapshots.generation() == 0
            assert snapshots.stats() == {
                "publish_attempts": 0,
                "publish_successes": 0,
                "publish_busy": 0,
                "acquire_count": 0,
                "release_count": 0,
                "max_snapshot_count": 0,
                "dropped_snapshots": 0,
            }

            view = snapshots.publish_changed(table, clear=False)
            assert view.count == 2
            assert view.dropped == 0
            assert view.generation == 1
            assert len(view.snapshots) == 2
            assert view.snapshots[0].has_change(native.FASTDIS_ENTITY_CHANGE_NEW)
            extrapolated_transform = lib.extrapolate_transform_linear(view.snapshots[0].transform, 2.0)
            assert extrapolated_transform.location == pytest.approx((12.5, 15.0, 37.5))
            extrapolated_snapshot = lib.extrapolate_snapshot_linear(
                view.snapshots[0],
                target_tick=view.snapshots[0].last_seen_tick + 2,
                seconds_per_tick=0.5,
            )
            assert extrapolated_snapshot.transform.location == pytest.approx((11.25, 17.5, 33.75))
            assert extrapolated_snapshot.has_change(native.FASTDIS_ENTITY_CHANGE_EXTRAPOLATED)
            dead_reckoned_snapshot = lib.extrapolate_snapshot_dead_reckoning(
                view.snapshots[0],
                target_tick=view.snapshots[0].last_seen_tick + 2,
                seconds_per_tick=0.5,
            )
            assert dead_reckoned_snapshot.transform.location == pytest.approx((11.5, 17.8, 34.1))
            assert dead_reckoned_snapshot.has_change(native.FASTDIS_ENTITY_CHANGE_EXTRAPOLATED)
            assert snapshots.stats()["publish_successes"] == 1
            assert snapshots.stats()["max_snapshot_count"] == 2

            held = snapshots.acquire_latest()
            try:
                assert held.count == 2
                assert held.generation == 1
                second = snapshots.publish_all(table)
                assert second.count == 2
                assert second.generation == 2
                with pytest.raises(native.FastDisError, match="busy"):
                    snapshots.publish_all(table)
                stats = snapshots.stats()
                assert stats["publish_attempts"] == 3
                assert stats["publish_successes"] == 2
                assert stats["publish_busy"] == 1
                assert stats["acquire_count"] == 1
                assert stats["release_count"] == 0

                copied, meta = snapshots.copy_latest(return_meta=True)
                assert len(copied) == 2
                assert meta["dropped"] == 0
                assert meta["generation"] == 2
                extrapolated, extrapolated_meta = snapshots.copy_latest_extrapolated(
                    target_tick=copied[0].last_seen_tick + 2,
                    seconds_per_tick=0.5,
                    return_meta=True,
                )
                assert len(extrapolated) == 2
                assert extrapolated_meta["dropped"] == 0
                assert extrapolated_meta["generation"] == 2
                assert extrapolated_meta["seconds_per_tick"] == 0.5
                assert extrapolated[0].transform.location == pytest.approx((11.25, 17.5, 33.75))
                assert extrapolated[0].has_change(native.FASTDIS_ENTITY_CHANGE_EXTRAPOLATED)
                dead_reckoned, dead_reckoned_meta = snapshots.copy_latest_dead_reckoned(
                    target_tick=copied[0].last_seen_tick + 2,
                    seconds_per_tick=0.5,
                    return_meta=True,
                )
                assert len(dead_reckoned) == 2
                assert dead_reckoned_meta["dropped"] == 0
                assert dead_reckoned[0].transform.location == pytest.approx((11.5, 17.8, 34.1))
                assert dead_reckoned[0].has_change(native.FASTDIS_ENTITY_CHANGE_EXTRAPOLATED)
            finally:
                held.close()
            assert snapshots.stats()["release_count"] == 1

            third = snapshots.publish_all(table)
            assert third.generation == 3
            with snapshots.acquire_latest() as acquired:
                assert acquired.count == 2
                with pytest.raises(native.FastDisError, match="busy"):
                    snapshots.resize(2)
            snapshots.reset_stats()
            assert snapshots.stats()["publish_attempts"] == 0
            assert snapshots.stats()["acquire_count"] == 0
            assert snapshots.stats()["release_count"] == 0
            snapshots.resize(2)
            assert snapshots.capacity() == 2

            table.mark_all_clean()
            p1_changed = bytearray(_make_entity_state(force_id=2))
            p1_changed[12 + 36 : 12 + 60] = struct.pack(">ddd", 250.0, 20.0, 30.0)
            combined_view, combined_stats = snapshots.ingest_and_publish_changed(
                table,
                scanner,
                [bytes(p1_changed)],
                return_stats=True,
            )
            assert combined_stats["scan"] == {"seen": 1, "malformed": 0, "accepted": 1, "emitted": 1}
            assert combined_stats["changed_entities"] == 1
            assert combined_view.count == 1
            assert combined_view.snapshots[0].transform.location == pytest.approx((250.0, 20.0, 30.0))

            table.advance_tick(3)
            evicted = snapshots.publish_evict_stale(table, 2)
            assert evicted.count == 2
            assert table.size() == 0

        table.ingest(scanner, [bytes(p1), bytes(p2)], advance_tick=True)
        with lib.create_snapshot_buffer(4, slots=3) as snapshots:
            assert snapshots.slot_count() == 3
            first = snapshots.publish_all(table)
            assert first.generation == 1
            held_a = snapshots.acquire_latest()
            held_b = None
            try:
                second = snapshots.publish_all(table)
                assert second.generation == 2
                held_b = snapshots.acquire_latest()
                third = snapshots.publish_all(table)
                assert third.generation == 3
                with pytest.raises(native.FastDisError, match="busy"):
                    snapshots.publish_all(table)
            finally:
                held_a.close()
                if held_b is not None:
                    held_b.close()
