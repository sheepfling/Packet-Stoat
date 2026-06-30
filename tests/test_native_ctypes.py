from __future__ import annotations

import json
import os
import struct
from pathlib import Path

import pytest

import fastdis.native as native

ROOT = Path(__file__).resolve().parents[1]


def test_find_native_library_prefers_windows_dll_over_linux_so(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    build_root = tmp_path / "build" / "cmake"
    linux_dir = build_root / "linux-x86_64"
    windows_dir = build_root / "host" / "Release"
    linux_dir.mkdir(parents=True)
    windows_dir.mkdir(parents=True)
    (linux_dir / "libfastdis.so").write_bytes(b"linux")
    (windows_dir / "fastdis.dll").write_bytes(b"windows")

    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("FASTDIS_LIBRARY", raising=False)
    monkeypatch.setattr(native.platform, "system", lambda: "Windows")
    monkeypatch.setattr(native.ctypes.util, "find_library", lambda _name: None)

    resolved = native.find_native_library()

    assert resolved == str(windows_dir / "fastdis.dll")


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


def _make_fire(version: int = 7) -> bytes:
    packet = bytearray(_make_pdu(version, native.FASTDIS_FIRE_PDU_TYPE, length=native.FASTDIS_FIRE_FIXED_SIZE, status=0x80))
    packet[3] = 2
    b = 12
    packet[b + 0 : b + 6] = struct.pack(">HHH", 0x0001, 0x0002, 0x0003)
    packet[b + 6 : b + 12] = struct.pack(">HHH", 0x0004, 0x0005, 0x0006)
    packet[b + 12 : b + 18] = struct.pack(">HHH", 0x0007, 0x0008, 0x0009)
    packet[b + 18 : b + 24] = struct.pack(">HHH", 0x000A, 0x000B, 0x000C)
    packet[b + 24 : b + 28] = struct.pack(">I", 99)
    packet[b + 28 : b + 52] = struct.pack(">ddd", 1000.5, 2000.25, 3000.75)
    packet[b + 52 : b + 60] = struct.pack(">BBHBBBB", 2, 1, 225, 4, 5, 6, 7)
    packet[b + 60 : b + 68] = struct.pack(">HHHH", 101, 202, 3, 600)
    packet[b + 68 : b + 80] = struct.pack(">fff", 1.5, 2.5, 3.5)
    packet[b + 80 : b + 84] = struct.pack(">f", 4444.5)
    return bytes(packet)


def _make_detonation(version: int = 7) -> bytes:
    packet = bytearray(_make_pdu(version, native.FASTDIS_DETONATION_PDU_TYPE, length=native.FASTDIS_DETONATION_FIXED_SIZE + 16, status=0x80))
    packet[3] = 2
    b = 12
    packet[b + 0 : b + 6] = struct.pack(">HHH", 0x0001, 0x0002, 0x0003)
    packet[b + 6 : b + 12] = struct.pack(">HHH", 0x0004, 0x0005, 0x0006)
    packet[b + 12 : b + 18] = struct.pack(">HHH", 0x0007, 0x0008, 0x0009)
    packet[b + 18 : b + 24] = struct.pack(">HHH", 0x000A, 0x000B, 0x000C)
    packet[b + 24 : b + 36] = struct.pack(">fff", 11.0, 22.0, 33.0)
    packet[b + 36 : b + 60] = struct.pack(">ddd", 111.5, 222.25, 333.75)
    packet[b + 60 : b + 68] = struct.pack(">BBHBBBB", 2, 1, 225, 4, 5, 6, 7)
    packet[b + 68 : b + 76] = struct.pack(">HHHH", 101, 202, 3, 600)
    packet[b + 76 : b + 88] = struct.pack(">fff", -4.0, -5.0, -6.0)
    packet[b + 88 : b + 92] = struct.pack(">BBH", 17, 1, 0)
    packet[b + 92 : b + 108] = bytes.fromhex("0102030405060708090a0b0c0d0e0f10")
    return bytes(packet)


def _make_remove_entity(version: int = 7) -> bytes:
    packet = bytearray(_make_pdu(version, native.FASTDIS_REMOVE_ENTITY_PDU_TYPE, length=native.FASTDIS_REMOVE_ENTITY_FIXED_SIZE))
    packet[3] = 5
    b = 12
    packet[b + 0 : b + 6] = struct.pack(">HHH", 0x1111, 0x2222, 0x3333)
    packet[b + 6 : b + 12] = struct.pack(">HHH", 0x4444, 0x5555, 0x6666)
    packet[b + 12 : b + 16] = (0x0BADF00D).to_bytes(4, "big")
    return bytes(packet)


def _make_designator(version: int = 7) -> bytes:
    packet = bytearray(_make_pdu(version, native.FASTDIS_DESIGNATOR_PDU_TYPE, length=native.FASTDIS_DESIGNATOR_FIXED_SIZE))
    packet[3] = 6
    b = 12
    packet[b + 0 : b + 6] = struct.pack(">HHH", 0x0001, 0x0002, 0x0003)
    packet[b + 6 : b + 8] = struct.pack(">H", 0x1234)
    packet[b + 8 : b + 14] = struct.pack(">HHH", 0x0004, 0x0005, 0x0006)
    packet[b + 14 : b + 16] = struct.pack(">H", 0x2345)
    packet[b + 16 : b + 24] = struct.pack(">ff", 12.5, 1.25)
    packet[b + 24 : b + 36] = struct.pack(">fff", 2.5, 3.5, 4.5)
    packet[b + 36 : b + 60] = struct.pack(">ddd", 100.0, 200.0, 300.0)
    packet[b + 60] = 4
    packet[b + 61 : b + 63] = struct.pack(">H", 0x3456)
    packet[b + 63] = 0x78
    packet[b + 64 : b + 76] = struct.pack(">fff", 5.5, 6.5, 7.5)
    return bytes(packet)


def _make_transmitter(version: int = 7) -> bytes:
    if version >= 7:
        tail = struct.pack(">fff", 9.0, 10.0, 11.0) + struct.pack(">fff", 12.0, 13.0, 14.0)
        length = native.FASTDIS_TRANSMITTER_FIXED_SIZE + len(tail)
    else:
        tail = bytes.fromhex("010203")
        length = native.FASTDIS_TRANSMITTER_FIXED_SIZE + len(tail)
    packet = bytearray(_make_pdu(version, native.FASTDIS_TRANSMITTER_PDU_TYPE, length=length))
    packet[3] = 4
    b = 12
    packet[b + 0 : b + 6] = struct.pack(">HHH", 0x0001, 0x0002, 0x0003)
    packet[b + 6 : b + 8] = struct.pack(">H", 0x1212)
    if version >= 7:
        packet[b + 8 : b + 16] = struct.pack(">BBHBBBB", 1, 2, 840, 5, 6, 7, 8)
        packet[b + 18 : b + 20] = struct.pack(">H", 2)
    else:
        packet[b + 8 : b + 16] = struct.pack(">BBHBBH", 1, 2, 840, 5, 6, 0x0708)
        packet[b + 18 : b + 20] = struct.pack(">H", 0)
    packet[b + 16] = 9
    packet[b + 17] = 10
    packet[b + 20 : b + 44] = struct.pack(">ddd", 10.0, 20.0, 30.0)
    packet[b + 44 : b + 56] = struct.pack(">fff", 1.0, 2.0, 3.0)
    packet[b + 56 : b + 60] = struct.pack(">HH", 0x4444, 1 if version >= 7 else 0)
    packet[b + 60 : b + 64] = struct.pack(">I", 225000)
    packet[b + 64 : b + 72] = struct.pack(">ff", 50.5, 60.5)
    packet[b + 72 : b + 80] = struct.pack(">HHHH", 1, 2, 3, 4)
    packet[b + 80 : b + 84] = struct.pack(">HH", 0x5555, 0x6666)
    packet[b + 84] = 1 if version >= 7 else 3
    packet[b + 85 : b + 87] = struct.pack(">H", 0x7777)
    packet[b + 87] = 0x88
    packet[native.FASTDIS_TRANSMITTER_FIXED_SIZE : length] = tail
    return bytes(packet)


def _make_signal(version: int = 7) -> bytes:
    if version >= 7:
        length = native.FASTDIS_SIGNAL_DIS7_FIXED_SIZE + 4
    else:
        length = native.FASTDIS_SIGNAL_DIS6_FIXED_SIZE + 4
    packet = bytearray(_make_pdu(version, native.FASTDIS_SIGNAL_PDU_TYPE, length=length))
    packet[3] = 4
    b = 12
    offset = 0
    if version < 7:
        packet[b + 0 : b + 6] = struct.pack(">HHH", 0x0001, 0x0002, 0x0003)
        packet[b + 6 : b + 8] = struct.pack(">H", 0x1111)
        offset = 8
    packet[b + offset + 0 : b + offset + 12] = struct.pack(">HHIHH", 0x2222, 0x3333, 48000, 4, 2)
    packet[b + offset + 12 : b + offset + 16] = bytes.fromhex("41424344")
    return bytes(packet)


def _make_receiver(version: int = 7) -> bytes:
    length = native.FASTDIS_RECEIVER_DIS7_FIXED_SIZE if version >= 7 else native.FASTDIS_RECEIVER_DIS6_FIXED_SIZE
    packet = bytearray(_make_pdu(version, native.FASTDIS_RECEIVER_PDU_TYPE, length=length))
    packet[3] = 4
    b = 12
    offset = 0
    if version < 7:
        packet[b + 0 : b + 6] = struct.pack(">HHH", 0x0001, 0x0002, 0x0003)
        packet[b + 6 : b + 8] = struct.pack(">H", 0x1111)
        offset = 8
    packet[b + offset + 0 : b + offset + 4] = struct.pack(">HH", 0x2222, 0x3333)
    packet[b + offset + 4 : b + offset + 8] = struct.pack(">f", 12.5)
    packet[b + offset + 8 : b + offset + 14] = struct.pack(">HHH", 0x0004, 0x0005, 0x0006)
    packet[b + offset + 14 : b + offset + 16] = struct.pack(">H", 0x4444)
    return bytes(packet)


def _make_iff_atc_navaids_layer1(version: int = 7) -> bytes:
    packet = bytearray(_make_pdu(version, native.FASTDIS_IFF_ATC_NAVAIDS_LAYER1_PDU_TYPE, length=native.FASTDIS_IFF_ATC_NAVAIDS_LAYER1_FIXED_SIZE))
    packet[3] = 6
    b = 12
    packet[b + 0 : b + 6] = struct.pack(">HHH", 0x0001, 0x0002, 0x0003)
    packet[b + 6 : b + 12] = struct.pack(">HHH", 0x0004, 0x0005, 0x0006)
    packet[b + 12 : b + 24] = struct.pack(">fff", 1.0, 2.0, 3.0)
    packet[b + 24 : b + 30] = struct.pack(">HHBB", 0x1111, 0x2222, 0x33, 0x44)
    packet[b + 30 : b + 32] = struct.pack(">H", 0x5555)
    packet[b + 32 : b + 48] = struct.pack(">BBBBHHHHHH", 1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
    return bytes(packet)


def _make_intercom_signal(version: int = 7) -> bytes:
    packet = bytearray(_make_pdu(version, native.FASTDIS_INTERCOM_SIGNAL_PDU_TYPE, length=native.FASTDIS_INTERCOM_SIGNAL_FIXED_SIZE + 4))
    packet[3] = 4
    b = 12
    packet[b + 0 : b + 6] = struct.pack(">HHH", 0x0001, 0x0002, 0x0003)
    packet[b + 6 : b + 8] = struct.pack(">H", 0x1212)
    packet[b + 8 : b + 20] = struct.pack(">HHIHH", 0x2222, 0x3333, 32000, 4, 2)
    packet[b + 20 : b + 24] = bytes.fromhex("51525354")
    return bytes(packet)


def _make_intercom_control(version: int = 7) -> bytes:
    packet = bytearray(_make_pdu(version, native.FASTDIS_INTERCOM_CONTROL_PDU_TYPE, length=native.FASTDIS_INTERCOM_CONTROL_FIXED_SIZE + 4))
    packet[3] = 4
    b = 12
    packet[b + 0 : b + 2] = bytes([0x11, 0x22])
    packet[b + 2 : b + 8] = struct.pack(">HHH", 0x0001, 0x0002, 0x0003)
    packet[b + 8 : b + 13] = bytes([0x33, 0x44, 0x55, 0x66, 0x77])
    packet[b + 13 : b + 19] = struct.pack(">HHH", 0x0004, 0x0005, 0x0006)
    packet[b + 19 : b + 21] = struct.pack(">H", 0x8888)
    packet[b + 21 : b + 25] = struct.pack(">I", 4)
    packet[b + 25 : b + 29] = bytes.fromhex("61626364")
    return bytes(packet)


def _make_attribute(version: int = 7) -> bytes:
    packet = bytearray(_make_pdu(version, native.FASTDIS_ATTRIBUTE_PDU_TYPE, length=native.FASTDIS_ATTRIBUTE_FIXED_SIZE + 4))
    packet[3] = native.FASTDIS_ENTITY_INFORMATION_FAMILY
    b = 12
    packet[b + 0 : b + 4] = struct.pack(">HH", 0x0101, 0x0202)
    packet[b + 4 : b + 8] = struct.pack(">i", 0x11223344)
    packet[b + 8 : b + 10] = struct.pack(">h", 0x5566)
    packet[b + 10] = 67
    packet[b + 11] = 7
    packet[b + 12 : b + 16] = struct.pack(">I", 0x778899AA)
    packet[b + 16] = 0x12
    packet[b + 17] = 0x34
    packet[b + 18 : b + 20] = struct.pack(">H", 1)
    packet[b + 20 : b + 24] = bytes.fromhex("61626364")
    return bytes(packet)


def _make_directed_energy_fire(version: int = 7) -> bytes:
    packet = bytearray(_make_pdu(version, native.FASTDIS_DIRECTED_ENERGY_FIRE_PDU_TYPE, length=native.FASTDIS_DIRECTED_ENERGY_FIRE_FIXED_SIZE + 4))
    packet[3] = 2
    b = 12
    packet[b + 0 : b + 6] = struct.pack(">HHH", 0x0001, 0x0002, 0x0003)
    packet[b + 6 : b + 12] = struct.pack(">HHH", 0x0004, 0x0005, 0x0006)
    packet[b + 12 : b + 20] = struct.pack(">BBHBBBB", 2, 1, 225, 4, 5, 6, 7)
    packet[b + 20 : b + 28] = struct.pack(">II", 7, 123456)
    packet[b + 28 : b + 32] = struct.pack(">f", 1.25)
    packet[b + 32 : b + 44] = struct.pack(">fff", 2.5, 3.5, 4.5)
    packet[b + 44 : b + 48] = struct.pack(">f", 5.5)
    packet[b + 48 : b + 52] = struct.pack(">f", 6.5)
    packet[b + 52 : b + 56] = struct.pack(">f", 7.5)
    packet[b + 56 : b + 60] = struct.pack(">f", 8.5)
    packet[b + 60 : b + 64] = struct.pack(">i", 9012)
    packet[b + 64 : b + 68] = struct.pack(">i", 0x10203040)
    packet[b + 68] = 0x11
    packet[b + 69] = 0x22
    packet[b + 70 : b + 74] = struct.pack(">I", 0x33445566)
    packet[b + 74 : b + 76] = struct.pack(">H", 0x7788)
    packet[b + 76 : b + 78] = struct.pack(">H", 1)
    packet[b + 78 : b + 82] = bytes.fromhex("90919293")
    return bytes(packet)


def _make_entity_damage_status(version: int = 7) -> bytes:
    packet = bytearray(_make_pdu(version, native.FASTDIS_ENTITY_DAMAGE_STATUS_PDU_TYPE, length=native.FASTDIS_ENTITY_DAMAGE_STATUS_FIXED_SIZE + 4))
    packet[3] = 2
    b = 12
    packet[b + 0 : b + 6] = struct.pack(">HHH", 0x0001, 0x0002, 0x0003)
    packet[b + 6 : b + 12] = struct.pack(">HHH", 0x0004, 0x0005, 0x0006)
    packet[b + 12 : b + 18] = struct.pack(">HHH", 0x0007, 0x0008, 0x0009)
    packet[b + 18 : b + 20] = struct.pack(">H", 0x1112)
    packet[b + 20 : b + 22] = struct.pack(">H", 0x1314)
    packet[b + 22 : b + 24] = struct.pack(">H", 1)
    packet[b + 24 : b + 28] = bytes.fromhex("a1a2a3a4")
    return bytes(packet)


def _make_iff(version: int = 7) -> bytes:
    packet = bytearray(_make_pdu(version, native.FASTDIS_IFF_PDU_TYPE, length=native.FASTDIS_IFF_FIXED_SIZE))
    packet[3] = 6
    b = 12
    packet[b + 0 : b + 6] = struct.pack(">HHH", 0x0001, 0x0002, 0x0003)
    packet[b + 6 : b + 12] = struct.pack(">HHH", 0x0004, 0x0005, 0x0006)
    packet[b + 12 : b + 24] = struct.pack(">fff", 1.0, 2.0, 3.0)
    packet[b + 24 : b + 30] = struct.pack(">HHBB", 0x1111, 0x2222, 0x33, 0x44)
    packet[b + 30 : b + 32] = struct.pack(">H", 0x5555)
    packet[b + 32 : b + 48] = struct.pack(">BBBBHHHHHH", 1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
    return bytes(packet)


def _make_electronic_emissions(version: int = 7) -> bytes:
    tail = bytes.fromhex("e1e2e3e4e5e6")
    length = native.FASTDIS_ELECTRONIC_EMISSIONS_FIXED_SIZE + len(tail)
    packet = bytearray(_make_pdu(version, native.FASTDIS_ELECTRONIC_EMISSIONS_PDU_TYPE, length=length))
    packet[3] = 6
    b = 12
    packet[b + 0 : b + 6] = struct.pack(">HHH", 0x0001, 0x0002, 0x0003)
    packet[b + 6 : b + 12] = struct.pack(">HHH", 0x0004, 0x0005, 0x0006)
    packet[b + 12] = 0x07
    packet[b + 13] = 0x02
    packet[b + 14 : b + 16] = struct.pack(">H", 0x0809)
    packet[b + 16 : b + 22] = tail
    return bytes(packet)


def _make_information_operations_action(version: int = 7) -> bytes:
    packet = bytearray(_make_pdu(version, native.FASTDIS_INFORMATION_OPERATIONS_ACTION_PDU_TYPE, length=native.FASTDIS_INFORMATION_OPERATIONS_ACTION_FIXED_SIZE + 4))
    packet[3] = 13
    b = 12
    packet[b + 0 : b + 6] = struct.pack(">HHH", 0x0001, 0x0002, 0x0003)
    packet[b + 6 : b + 12] = struct.pack(">HHH", 0x0004, 0x0005, 0x0006)
    packet[b + 12 : b + 16] = struct.pack(">I", 0x11223344)
    packet[b + 16 : b + 24] = struct.pack(">HHHH", 0x0102, 0x0304, 0x0506, 0x0708)
    packet[b + 24 : b + 28] = struct.pack(">I", 0x55667788)
    packet[b + 28 : b + 34] = struct.pack(">HHH", 0x0007, 0x0008, 0x0009)
    packet[b + 34 : b + 40] = struct.pack(">HHH", 0x000A, 0x000B, 0x000C)
    packet[b + 40 : b + 44] = struct.pack(">HH", 0x090A, 1)
    packet[b + 44 : b + 48] = bytes.fromhex("c1c2c3c4")
    return bytes(packet)


def _make_ua(version: int = 7) -> bytes:
    tail = bytes.fromhex("f1f2f3f4f5f6f7f8")
    length = native.FASTDIS_UA_FIXED_SIZE + len(tail)
    packet = bytearray(_make_pdu(version, native.FASTDIS_UA_PDU_TYPE, length=length))
    packet[3] = 6
    b = 12
    packet[b + 0 : b + 6] = struct.pack(">HHH", 0x0001, 0x0002, 0x0003)
    packet[b + 6 : b + 12] = struct.pack(">HHH", 0x0004, 0x0005, 0x0006)
    packet[b + 12] = 0x0A
    packet[b + 13] = 0x0B
    packet[b + 14 : b + 16] = struct.pack(">H", 0x0C0D)
    packet[b + 16] = 0x0E
    packet[b + 17] = 0x01
    packet[b + 18] = 0x02
    packet[b + 19] = 0x03
    packet[b + 20 : b + 28] = tail
    return bytes(packet)


def _make_information_operations_report(version: int = 7) -> bytes:
    packet = bytearray(_make_pdu(version, native.FASTDIS_INFORMATION_OPERATIONS_REPORT_PDU_TYPE, length=native.FASTDIS_INFORMATION_OPERATIONS_REPORT_FIXED_SIZE + 4))
    packet[3] = 13
    b = 12
    packet[b + 0 : b + 6] = struct.pack(">HHH", 0x0001, 0x0002, 0x0003)
    packet[b + 6 : b + 10] = struct.pack(">HBB", 0x0102, 0x03, 0x04)
    packet[b + 10 : b + 16] = struct.pack(">HHH", 0x0004, 0x0005, 0x0006)
    packet[b + 16 : b + 22] = struct.pack(">HHH", 0x0007, 0x0008, 0x0009)
    packet[b + 22 : b + 28] = struct.pack(">HHH", 0x1112, 0x1314, 1)
    packet[b + 28 : b + 32] = bytes.fromhex("d1d2d3d4")
    return bytes(packet)


def _make_sees(version: int = 7) -> bytes:
    tail = bytes.fromhex("aabbccddeeff0011")
    length = native.FASTDIS_SEES_FIXED_SIZE + len(tail)
    packet = bytearray(_make_pdu(version, native.FASTDIS_SEES_PDU_TYPE, length=length))
    packet[3] = 6
    b = 12
    packet[b + 0 : b + 6] = struct.pack(">HHH", 0x0011, 0x0022, 0x0033)
    packet[b + 6 : b + 8] = struct.pack(">H", 0x1112)
    packet[b + 8 : b + 10] = struct.pack(">H", 0x1314)
    packet[b + 10 : b + 12] = struct.pack(">H", 0x1516)
    packet[b + 12 : b + 14] = struct.pack(">H", 0x0002)
    packet[b + 14 : b + 16] = struct.pack(">H", 0x0003)
    packet[b + 16 : b + 24] = tail
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


def _make_acknowledge(version: int = 7) -> bytes:
    packet = bytearray(_make_pdu(version, native.FASTDIS_ACKNOWLEDGE_PDU_TYPE, length=native.FASTDIS_ACKNOWLEDGE_FIXED_SIZE))
    packet[3] = 5
    b = 12
    packet[b + 0 : b + 6] = struct.pack(">HHH", 0x1111, 0x2222, 0x3333)
    packet[b + 6 : b + 12] = struct.pack(">HHH", 0x4444, 0x5555, 0x6666)
    packet[b + 12 : b + 16] = struct.pack(">HH", 0x1234, 0x5678)
    packet[b + 16 : b + 20] = (0xCAFEBABE).to_bytes(4, "big")
    return bytes(packet)


def _make_create_entity_reliable(version: int = 7) -> bytes:
    packet = bytearray(_make_pdu(version, native.FASTDIS_CREATE_ENTITY_RELIABLE_PDU_TYPE, length=native.FASTDIS_CREATE_ENTITY_RELIABLE_FIXED_SIZE))
    packet[3] = 10
    b = 12
    packet[b + 0 : b + 6] = struct.pack(">HHH", 0x1111, 0x2222, 0x3333)
    packet[b + 6 : b + 12] = struct.pack(">HHH", 0x4444, 0x5555, 0x6666)
    packet[b + 12] = 7
    packet[b + 13 : b + 15] = (0x1357).to_bytes(2, "big")
    packet[b + 15] = 9
    packet[b + 16 : b + 20] = (0xA0B0C0D0).to_bytes(4, "big")
    return bytes(packet)


def _make_remove_entity_reliable(version: int = 7) -> bytes:
    packet = bytearray(_make_pdu(version, native.FASTDIS_REMOVE_ENTITY_RELIABLE_PDU_TYPE, length=native.FASTDIS_REMOVE_ENTITY_RELIABLE_FIXED_SIZE))
    packet[3] = 10
    b = 12
    packet[b + 0 : b + 6] = struct.pack(">HHH", 0x1111, 0x2222, 0x3333)
    packet[b + 6 : b + 12] = struct.pack(">HHH", 0x4444, 0x5555, 0x6666)
    packet[b + 12] = 8
    packet[b + 13 : b + 15] = (0x2468).to_bytes(2, "big")
    packet[b + 15] = 10
    packet[b + 16 : b + 20] = (0x0BADF00D).to_bytes(4, "big")
    return bytes(packet)


def _make_start_resume_reliable(version: int = 7) -> bytes:
    packet = bytearray(_make_pdu(version, native.FASTDIS_START_RESUME_RELIABLE_PDU_TYPE, length=native.FASTDIS_START_RESUME_RELIABLE_FIXED_SIZE))
    packet[3] = 10
    b = 12
    packet[b + 0 : b + 6] = struct.pack(">HHH", 0x1111, 0x2222, 0x3333)
    packet[b + 6 : b + 12] = struct.pack(">HHH", 0x4444, 0x5555, 0x6666)
    packet[b + 12 : b + 20] = struct.pack(">II", 7, 123456)
    packet[b + 20 : b + 28] = struct.pack(">II", 9, 654321)
    packet[b + 28] = 11
    packet[b + 29 : b + 31] = (0xAAAA).to_bytes(2, "big")
    packet[b + 31] = 12
    packet[b + 32 : b + 36] = (0x01020304).to_bytes(4, "big")
    return bytes(packet)


def _make_stop_freeze_reliable(version: int = 7) -> bytes:
    packet = bytearray(_make_pdu(version, native.FASTDIS_STOP_FREEZE_RELIABLE_PDU_TYPE, length=native.FASTDIS_STOP_FREEZE_RELIABLE_FIXED_SIZE))
    packet[3] = 10
    b = 12
    packet[b + 0 : b + 6] = struct.pack(">HHH", 0x1111, 0x2222, 0x3333)
    packet[b + 6 : b + 12] = struct.pack(">HHH", 0x4444, 0x5555, 0x6666)
    packet[b + 12 : b + 20] = struct.pack(">II", 5, 7654321)
    packet[b + 20] = 3
    packet[b + 21] = 4
    packet[b + 22] = 13
    packet[b + 23] = 14
    packet[b + 24 : b + 28] = (0x0F1E2D3C).to_bytes(4, "big")
    return bytes(packet)


def _make_acknowledge_reliable(version: int = 7) -> bytes:
    packet = bytearray(_make_pdu(version, native.FASTDIS_ACKNOWLEDGE_RELIABLE_PDU_TYPE, length=native.FASTDIS_ACKNOWLEDGE_RELIABLE_FIXED_SIZE))
    packet[3] = 10
    b = 12
    packet[b + 0 : b + 6] = struct.pack(">HHH", 0x1111, 0x2222, 0x3333)
    packet[b + 6 : b + 12] = struct.pack(">HHH", 0x4444, 0x5555, 0x6666)
    packet[b + 12 : b + 16] = struct.pack(">HH", 0x9ABC, 0xDEF0)
    packet[b + 16 : b + 20] = (0xFACECAFE).to_bytes(4, "big")
    return bytes(packet)


def _make_action_request(version: int = 7) -> bytes:
    tail = bytes.fromhex("00112233445566778899aabbccddeeff")
    length = native.FASTDIS_ACTION_REQUEST_FIXED_SIZE + len(tail)
    packet = bytearray(_make_pdu(version, native.FASTDIS_ACTION_REQUEST_PDU_TYPE, length=length))
    packet[3] = 5
    b = 12
    packet[b + 0 : b + 6] = struct.pack(">HHH", 1, 2, 3)
    packet[b + 6 : b + 12] = struct.pack(">HHH", 4, 5, 6)
    packet[b + 12 : b + 28] = struct.pack(">IIII", 0x01020304, 0x11121314, 1, 1)
    packet[b + 28 : b + 44] = tail
    return bytes(packet)


def _make_data_query_reliable(version: int = 7) -> bytes:
    tail = bytes.fromhex("3132333435363738393a3b3c3d3e3f40")
    length = native.FASTDIS_DATA_QUERY_RELIABLE_FIXED_SIZE + len(tail)
    packet = bytearray(_make_pdu(version, native.FASTDIS_DATA_QUERY_RELIABLE_PDU_TYPE, length=length))
    packet[3] = 10
    b = 12
    packet[b + 0 : b + 6] = struct.pack(">HHH", 1, 2, 3)
    packet[b + 6 : b + 12] = struct.pack(">HHH", 4, 5, 6)
    packet[b + 12 : b + 36] = b"".join(
        [
            struct.pack(">BHBI", 5, 0, 0, 0x41424344),
            struct.pack(">II", 222222, 3333),
            struct.pack(">II", 2, 1),
        ]
    )
    packet[b + 36 : b + 52] = tail
    return bytes(packet)


def _make_record_reliable(version: int = 7) -> bytes:
    tail = bytes.fromhex("1011121314151617")
    length = native.FASTDIS_RECORD_RELIABLE_FIXED_SIZE + len(tail)
    packet = bytearray(_make_pdu(version, native.FASTDIS_RECORD_RELIABLE_PDU_TYPE, length=length))
    packet[3] = 10
    b = 12
    packet[b + 0 : b + 6] = struct.pack(">HHH", 1, 2, 3)
    packet[b + 6 : b + 12] = struct.pack(">HHH", 4, 5, 6)
    packet[b + 12 : b + 24] = b"".join(
        [
            struct.pack(">I", 0x51525354),
            struct.pack(">BBH", 7, 8, 0x090A),
            struct.pack(">I", 2),
        ]
    )
    packet[b + 24 : b + 32] = tail
    return bytes(packet)


def _make_set_record_reliable(version: int = 7) -> bytes:
    tail = bytes.fromhex("2122232425262728")
    length = native.FASTDIS_SET_RECORD_RELIABLE_FIXED_SIZE + len(tail)
    packet = bytearray(_make_pdu(version, native.FASTDIS_SET_RECORD_RELIABLE_PDU_TYPE, length=length))
    packet[3] = 10
    b = 12
    packet[b + 0 : b + 6] = struct.pack(">HHH", 1, 2, 3)
    packet[b + 6 : b + 12] = struct.pack(">HHH", 4, 5, 6)
    packet[b + 12 : b + 24] = b"".join(
        [
            struct.pack(">I", 0x61626364),
            struct.pack(">BHBI", 9, 0x0B0C, 13, 3),
        ]
    )
    packet[b + 28 : b + 36] = tail
    return bytes(packet)


def _make_record_query_reliable(version: int = 7) -> bytes:
    tail = bytes.fromhex("3132333435363738")
    length = native.FASTDIS_RECORD_QUERY_RELIABLE_FIXED_SIZE + len(tail)
    packet = bytearray(_make_pdu(version, native.FASTDIS_RECORD_QUERY_RELIABLE_PDU_TYPE, length=length))
    packet[3] = 10
    b = 12
    packet[b + 0 : b + 6] = struct.pack(">HHH", 1, 2, 3)
    packet[b + 6 : b + 12] = struct.pack(">HHH", 4, 5, 6)
    packet[b + 12 : b + 30] = b"".join(
        [
            struct.pack(">I", 0x71727374),
            struct.pack(">BHBHI", 14, 0x1516, 17, 0x1819, 0x1A1B1C1D),
            struct.pack(">I", 2),
        ]
    )
    packet[b + 30 : b + 38] = tail
    return bytes(packet)


def _make_service_request(version: int = 7) -> bytes:
    tail = bytes.fromhex("4142434445464748")
    length = native.FASTDIS_SERVICE_REQUEST_FIXED_SIZE + len(tail)
    packet = bytearray(_make_pdu(version, native.FASTDIS_SERVICE_REQUEST_PDU_TYPE, length=length))
    packet[3] = 3
    b = 12
    packet[b + 0 : b + 6] = struct.pack(">HHH", 1, 2, 3)
    packet[b + 6 : b + 12] = struct.pack(">HHH", 4, 5, 6)
    packet[b + 12] = 7
    packet[b + 13] = 2
    packet[b + 14 : b + 16] = (0x4041).to_bytes(2, "big")
    packet[b + 16 : b + 24] = tail
    return bytes(packet)


def _make_resupply_offer(version: int = 7) -> bytes:
    tail = bytes.fromhex("5152535455565758")
    length = native.FASTDIS_RESUPPLY_OFFER_FIXED_SIZE + len(tail)
    packet = bytearray(_make_pdu(version, native.FASTDIS_RESUPPLY_OFFER_PDU_TYPE, length=length))
    packet[3] = 3
    b = 12
    packet[b + 0 : b + 6] = struct.pack(">HHH", 1, 2, 3)
    packet[b + 6 : b + 12] = struct.pack(">HHH", 4, 5, 6)
    packet[b + 12] = 2
    packet[b + 13 : b + 16] = bytes([0x11, 0x12, 0x13])
    packet[b + 16 : b + 24] = tail
    return bytes(packet)


def _make_resupply_received(version: int = 7) -> bytes:
    tail = bytes.fromhex("6162636465666768")
    length = native.FASTDIS_RESUPPLY_RECEIVED_FIXED_SIZE + len(tail)
    packet = bytearray(_make_pdu(version, native.FASTDIS_RESUPPLY_RECEIVED_PDU_TYPE, length=length))
    packet[3] = 3
    b = 12
    packet[b + 0 : b + 6] = struct.pack(">HHH", 1, 2, 3)
    packet[b + 6 : b + 12] = struct.pack(">HHH", 4, 5, 6)
    packet[b + 12] = 2
    packet[b + 13 : b + 15] = (0x6162).to_bytes(2, "big")
    packet[b + 15] = 0x63
    packet[b + 16 : b + 24] = tail
    return bytes(packet)


def _make_resupply_cancel(version: int = 7) -> bytes:
    packet = bytearray(_make_pdu(version, native.FASTDIS_RESUPPLY_CANCEL_PDU_TYPE, length=native.FASTDIS_RESUPPLY_CANCEL_FIXED_SIZE))
    packet[3] = 3
    b = 12
    packet[b + 0 : b + 6] = struct.pack(">HHH", 1, 2, 3)
    packet[b + 6 : b + 12] = struct.pack(">HHH", 4, 5, 6)
    return bytes(packet)


def _make_repair_complete(version: int = 7) -> bytes:
    packet = bytearray(_make_pdu(version, native.FASTDIS_REPAIR_COMPLETE_PDU_TYPE, length=native.FASTDIS_REPAIR_COMPLETE_FIXED_SIZE))
    packet[3] = 3
    b = 12
    packet[b + 0 : b + 6] = struct.pack(">HHH", 1, 2, 3)
    packet[b + 6 : b + 12] = struct.pack(">HHH", 4, 5, 6)
    packet[b + 12 : b + 14] = (0x7172).to_bytes(2, "big")
    packet[b + 14 : b + 16] = (0x7374).to_bytes(2, "big")
    return bytes(packet)


def _make_repair_response(version: int = 7) -> bytes:
    packet = bytearray(_make_pdu(version, native.FASTDIS_REPAIR_RESPONSE_PDU_TYPE, length=native.FASTDIS_REPAIR_RESPONSE_FIXED_SIZE))
    packet[3] = 3
    b = 12
    packet[b + 0 : b + 6] = struct.pack(">HHH", 1, 2, 3)
    packet[b + 6 : b + 12] = struct.pack(">HHH", 4, 5, 6)
    packet[b + 12] = 0x75
    packet[b + 13 : b + 15] = (0x7677).to_bytes(2, "big")
    packet[b + 15] = 0x78
    return bytes(packet)


def _make_other(version: int = 7) -> bytes:
    tail = b"OTHR"
    packet = bytearray(_make_pdu(version, native.FASTDIS_OTHER_PDU_TYPE, length=native.FASTDIS_OTHER_FIXED_SIZE + len(tail)))
    packet[3] = 0
    packet[native.FASTDIS_OTHER_FIXED_SIZE : native.FASTDIS_OTHER_FIXED_SIZE + len(tail)] = tail
    return bytes(packet)


def _make_aggregate_state(version: int = 7) -> bytes:
    tail = bytes.fromhex("a1a2a3a4a5a6")
    packet = bytearray(_make_pdu(version, native.FASTDIS_AGGREGATE_STATE_PDU_TYPE, length=native.FASTDIS_AGGREGATE_STATE_FIXED_SIZE + len(tail)))
    packet[3] = 7
    b = 12
    packet[b + 0 : b + 6] = struct.pack(">HHH", 1, 2, 3)
    packet[b + 6] = 4
    packet[b + 7] = 5
    packet[b + 8 : b + 16] = struct.pack(">BBHBBBB", 1, 2, 840, 3, 4, 5, 6)
    packet[b + 16 : b + 20] = struct.pack(">I", 0x11223344)
    packet[b + 20] = 1
    packet[b + 21 : b + 52] = b"AGGREGATE-ALPHA".ljust(31, b"\x00")
    packet[b + 52 : b + 64] = struct.pack(">fff", 1.0, 2.0, 3.0)
    packet[b + 64 : b + 76] = struct.pack(">fff", 0.1, 0.2, 0.3)
    packet[b + 76 : b + 100] = struct.pack(">ddd", 10.0, 20.0, 30.0)
    packet[b + 100 : b + 112] = struct.pack(">fff", 4.0, 5.0, 6.0)
    packet[b + 112 : b + 120] = struct.pack(">HHHH", 7, 8, 9, 10)
    packet[native.FASTDIS_AGGREGATE_STATE_FIXED_SIZE : native.FASTDIS_AGGREGATE_STATE_FIXED_SIZE + len(tail)] = tail
    return bytes(packet)


def _make_is_group_of(version: int = 7) -> bytes:
    tail = bytes.fromhex("b1b2b3b4")
    packet = bytearray(_make_pdu(version, native.FASTDIS_IS_GROUP_OF_PDU_TYPE, length=native.FASTDIS_IS_GROUP_OF_FIXED_SIZE + len(tail)))
    packet[3] = 7
    b = 12
    packet[b + 0 : b + 6] = struct.pack(">HHH", 1, 2, 3)
    packet[b + 6] = 0x21
    packet[b + 7] = 0x02
    packet[b + 8 : b + 12] = struct.pack(">I", 0x10203040)
    packet[b + 12 : b + 28] = struct.pack(">dd", 41.25, -93.5)
    packet[native.FASTDIS_IS_GROUP_OF_FIXED_SIZE : native.FASTDIS_IS_GROUP_OF_FIXED_SIZE + len(tail)] = tail
    return bytes(packet)


def _make_transfer_control_request(version: int = 6) -> bytes:
    tail = bytes.fromhex("c1c2c3c4")
    packet = bytearray(_make_pdu(version, native.FASTDIS_TRANSFER_CONTROL_REQUEST_PDU_TYPE, length=native.FASTDIS_TRANSFER_CONTROL_REQUEST_FIXED_SIZE + len(tail)))
    packet[3] = 7
    b = 12
    packet[b + 0 : b + 6] = struct.pack(">HHH", 1, 2, 3)
    packet[b + 6 : b + 12] = struct.pack(">HHH", 4, 5, 6)
    packet[b + 12 : b + 16] = struct.pack(">I", 0x11223344)
    packet[b + 16] = 0x07
    packet[b + 17] = 0x08
    packet[b + 18 : b + 24] = struct.pack(">HHH", 7, 8, 9)
    packet[b + 24] = 0x02
    packet[native.FASTDIS_TRANSFER_CONTROL_REQUEST_FIXED_SIZE : native.FASTDIS_TRANSFER_CONTROL_REQUEST_FIXED_SIZE + len(tail)] = tail
    return bytes(packet)


def _make_transfer_ownership(version: int = 7) -> bytes:
    tail = bytes.fromhex("d1d2d3d4")
    packet = bytearray(_make_pdu(version, native.FASTDIS_TRANSFER_OWNERSHIP_PDU_TYPE, length=native.FASTDIS_TRANSFER_OWNERSHIP_FIXED_SIZE + len(tail)))
    packet[3] = 7
    b = 12
    packet[b + 0 : b + 6] = struct.pack(">HHH", 10, 11, 12)
    packet[b + 6 : b + 12] = struct.pack(">HHH", 13, 14, 15)
    packet[b + 12 : b + 16] = struct.pack(">I", 0x55667788)
    packet[b + 16] = 0x09
    packet[b + 17] = 0x0A
    packet[b + 18 : b + 24] = struct.pack(">HHH", 16, 17, 18)
    packet[b + 24] = 0x03
    packet[native.FASTDIS_TRANSFER_OWNERSHIP_FIXED_SIZE : native.FASTDIS_TRANSFER_OWNERSHIP_FIXED_SIZE + len(tail)] = tail
    return bytes(packet)


def _make_is_part_of(version: int = 7) -> bytes:
    packet = bytearray(_make_pdu(version, native.FASTDIS_IS_PART_OF_PDU_TYPE, length=native.FASTDIS_IS_PART_OF_FIXED_SIZE))
    packet[3] = 7
    b = 12
    packet[b + 0 : b + 6] = struct.pack(">HHH", 1, 2, 3)
    packet[b + 6 : b + 12] = struct.pack(">HHH", 4, 5, 6)
    packet[b + 12 : b + 16] = struct.pack(">HH", 0x1112, 0x1314)
    packet[b + 16 : b + 28] = struct.pack(">fff", 7.0, 8.0, 9.0)
    packet[b + 28 : b + 32] = struct.pack(">HH", 0x2122, 0x2324)
    packet[b + 32 : b + 40] = struct.pack(">BBHBBBB", 2, 3, 225, 4, 5, 6, 7)
    return bytes(packet)


def _make_minefield_state(version: int = 6) -> bytes:
    if version >= 7:
        body = b"".join(
            [
                struct.pack(">HH", 231, 232),
                struct.pack(">H", 233),
                struct.pack(">HBB", 234, 235, 2),
                struct.pack(">BBHBBBB", 19, 20, 225, 21, 22, 23, 24),
                struct.pack(">H", 2),
                struct.pack(">ddd", 40.25, 50.5, 60.75),
                struct.pack(">fff", 0.4, 0.5, 0.6),
                struct.pack(">HH", 236, 237),
                struct.pack(">ff", 5.5, 6.5),
                struct.pack(">ff", 7.5, 8.5),
                struct.pack(">BBHBBBB", 25, 26, 840, 27, 28, 29, 30),
                struct.pack(">BBHBBBB", 31, 32, 124, 33, 34, 35, 36),
            ]
        )
    else:
        body = b"".join(
            [
                struct.pack(">HHH", 221, 222, 223),
                struct.pack(">HBB", 224, 225, 2),
                struct.pack(">BBHBBBB", 1, 2, 840, 3, 4, 5, 6),
                struct.pack(">H", 2),
                struct.pack(">ddd", 10.25, 20.5, 30.75),
                struct.pack(">fff", 0.1, 0.2, 0.3),
                struct.pack(">HH", 226, 227),
                struct.pack(">ff", 1.5, 2.5),
                struct.pack(">ff", 3.5, 4.5),
                struct.pack(">BBHBBBB", 7, 8, 124, 9, 10, 11, 12),
                struct.pack(">BBHBBBB", 13, 14, 225, 15, 16, 17, 18),
            ]
        )
    packet = bytearray(_make_pdu(version, native.FASTDIS_MINEFIELD_STATE_PDU_TYPE, length=12 + len(body)))
    packet[3] = 8
    packet[12:] = body
    return bytes(packet)


def _make_minefield_query(version: int = 6) -> bytes:
    body = b"".join(
        [
            struct.pack(">HHH", 201, 202, 203),
            struct.pack(">HHH", 204, 205, 206),
            struct.pack(">BBBBI", 207, 2, 0, 2, 0x01020304),
            struct.pack(">BBHBBBB", 3, 4, 225, 5, 6, 7, 8),
            struct.pack(">ff", 1.5, 2.5),
            struct.pack(">ff", 3.5, 4.5),
            bytes.fromhex("1112"),
            bytes.fromhex("2122"),
        ]
    )
    packet = bytearray(_make_pdu(version, native.FASTDIS_MINEFIELD_QUERY_PDU_TYPE, length=12 + len(body)))
    packet[3] = 8
    packet[12:] = body
    return bytes(packet)


def _make_minefield_data(version: int = 6) -> bytes:
    body = b"".join(
        [
            struct.pack(">HHH", 251, 252, 253),
            struct.pack(">HHH", 254, 255, 256),
            struct.pack(">HBBBBBBI", 257, 200, 3, 2, 2, 2, 0, 0x01020304),
            struct.pack(">BBHBBBB", 37, 38, 225, 39, 40, 41, 42),
            bytes.fromhex("3132"),
            bytes.fromhex("4142"),
            struct.pack(">B", 0),
            struct.pack(">fff", 9.5, 10.5, 11.5),
            struct.pack(">fff", 12.5, 13.5, 14.5),
        ]
    )
    packet = bytearray(_make_pdu(version, native.FASTDIS_MINEFIELD_DATA_PDU_TYPE, length=73))
    packet[3] = 8
    packet[12:] = body
    return bytes(packet)


def _make_environmental_process(version: int = 6) -> bytes:
    body = b"".join(
        [
            struct.pack(">HHH", 211, 212, 213),
            struct.pack(">BBHBBBB", 9, 10, 840, 11, 12, 13, 14),
            struct.pack(">BBBH", 15, 16, 2, 0x1718),
            bytes.fromhex("3132333435363738393a"),
        ]
    )
    packet = bytearray(_make_pdu(version, native.FASTDIS_ENVIRONMENTAL_PROCESS_PDU_TYPE, length=12 + len(body)))
    packet[3] = 9
    packet[12:] = body
    return bytes(packet)


def _make_gridded_data(version: int = 6) -> bytes:
    body = b"".join(
        [
            struct.pack(">HHH", 261, 262, 263),
            struct.pack(">HHHHBB", 264, 265, 266, 267, 3, 1),
            struct.pack(">BBHBBBB", 43, 44, 840, 45, 46, 47, 48),
            struct.pack(">fff", 0.7, 0.8, 0.9),
            struct.pack(">q", 0x0102030405060708),
            struct.pack(">IBHB", 269, 4, 270, 0),
            bytes.fromhex("5152535455565758595a"),
        ]
    )
    packet = bytearray(_make_pdu(version, native.FASTDIS_GRIDDED_DATA_PDU_TYPE, length=12 + len(body)))
    packet[3] = 9
    packet[12:] = body
    return bytes(packet)


def _make_point_object_state(version: int = 6) -> bytes:
    if version >= 7:
        body = b"".join(
            [
                struct.pack(">HHH", 71, 72, 73),
                struct.pack(">HHH", 74, 75, 76),
                struct.pack(">HBB", 77, 78, 79),
                struct.pack(">BBBB", 4, 5, 6, 7),
                struct.pack(">ddd", 400.25, 500.5, 600.75),
                struct.pack(">fff", 0.4, 0.5, 0.6),
                struct.pack(">d", 2345.5),
                struct.pack(">HH", 80, 81),
                struct.pack(">HH", 82, 83),
                struct.pack(">I", 84),
            ]
        )
    else:
        body = b"".join(
            [
                struct.pack(">HHH", 51, 52, 53),
                struct.pack(">HHH", 54, 55, 56),
                struct.pack(">HBB", 57, 58, 59),
                struct.pack(">BBHBB", 1, 2, 840, 3, 4),
                struct.pack(">ddd", 100.25, 200.5, 300.75),
                struct.pack(">fff", 0.1, 0.2, 0.3),
                struct.pack(">d", 1234.5),
                struct.pack(">HH", 60, 61),
                struct.pack(">HH", 62, 63),
                struct.pack(">I", 64),
            ]
        )
    packet = bytearray(_make_pdu(version, native.FASTDIS_POINT_OBJECT_STATE_PDU_TYPE, length=12 + len(body)))
    packet[3] = 9
    packet[12:] = body
    return bytes(packet)


def _make_linear_object_state(version: int = 6) -> bytes:
    if version >= 7:
        body = b"".join(
            [
                struct.pack(">HHH", 151, 152, 153),
                struct.pack(">HHH", 154, 155, 156),
                struct.pack(">HBB", 157, 158, 2),
                struct.pack(">HH", 159, 160),
                struct.pack(">HH", 161, 162),
                struct.pack(">BBBB", 13, 14, 15, 16),
                struct.pack(">BBHI", 3, 4, 0x0506, 0x0708090A),
                struct.pack(">ddd", 3000.25, 3001.5, 3002.75),
                struct.pack(">fff", 0.7, 0.8, 0.9),
                struct.pack(">ffffI", 45.5, 46.5, 47.5, 48.5, 49),
                struct.pack(">BBHI", 5, 6, 0x0B0C, 0x0D0E0F10),
                struct.pack(">ddd", 4000.25, 4001.5, 4002.75),
                struct.pack(">fff", 1.0, 1.1, 1.2),
                struct.pack(">ffffI", 55.5, 56.5, 57.5, 58.5, 59),
            ]
        )
    else:
        body = b"".join(
            [
                struct.pack(">HHH", 131, 132, 133),
                struct.pack(">HHH", 134, 135, 136),
                struct.pack(">HBB", 137, 138, 2),
                struct.pack(">HH", 139, 140),
                struct.pack(">HH", 141, 142),
                struct.pack(">BBHBB", 9, 10, 840, 11, 12),
                struct.pack(">B", 1),
                bytes.fromhex("010203040506"),
                struct.pack(">ddd", 1000.25, 1001.5, 1002.75),
                struct.pack(">fff", 0.1, 0.2, 0.3),
                struct.pack(">HHHHI", 25, 26, 27, 28, 29),
                struct.pack(">B", 2),
                bytes.fromhex("0a0b0c0d0e0f"),
                struct.pack(">ddd", 2000.25, 2001.5, 2002.75),
                struct.pack(">fff", 0.4, 0.5, 0.6),
                struct.pack(">HHHHI", 35, 36, 37, 38, 39),
            ]
        )
    packet = bytearray(_make_pdu(version, native.FASTDIS_LINEAR_OBJECT_STATE_PDU_TYPE, length=12 + len(body)))
    packet[3] = 9
    packet[12:] = body
    return bytes(packet)


def _make_areal_object_state(version: int = 6) -> bytes:
    if version >= 7:
        body = b"".join(
            [
                struct.pack(">HHH", 111, 112, 113),
                struct.pack(">HHH", 114, 115, 116),
                struct.pack(">HBB", 117, 118, 119),
                struct.pack(">BBHBBBB", 6, 7, 124, 8, 9, 10, 11),
                struct.pack(">IH", 120, 121),
                struct.pack(">H", 2),
                struct.pack(">HH", 122, 123),
                struct.pack(">HH", 124, 125),
                struct.pack(">ddd", 7.0, 8.0, 9.0),
                struct.pack(">ddd", 10.0, 11.0, 12.0),
            ]
        )
    else:
        body = b"".join(
            [
                struct.pack(">HHH", 91, 92, 93),
                struct.pack(">HHH", 94, 95, 96),
                struct.pack(">HBB", 97, 98, 99),
                struct.pack(">BBHBBBB", 3, 4, 225, 5, 6, 7, 8),
                bytes.fromhex("010203040506"),
                struct.pack(">H", 2),
                struct.pack(">HH", 100, 101),
                struct.pack(">HH", 102, 103),
                struct.pack(">ddd", 1.0, 2.0, 3.0),
                struct.pack(">ddd", 4.0, 5.0, 6.0),
            ]
        )
    packet = bytearray(_make_pdu(version, native.FASTDIS_AREAL_OBJECT_STATE_PDU_TYPE, length=12 + len(body)))
    packet[3] = 9
    packet[12:] = body
    return bytes(packet)


def _make_minefield_response_nack(version: int = 6) -> bytes:
    body = b"".join(
        [
            struct.pack(">HHH", 181, 182, 183),
            struct.pack(">HHH", 184, 185, 186),
            struct.pack(">BB", 187, 2),
            bytes.fromhex("0102030405060708"),
            bytes.fromhex("1112131415161718"),
        ]
    )
    packet = bytearray(_make_pdu(version, native.FASTDIS_MINEFIELD_RESPONSE_NACK_PDU_TYPE, length=42))
    packet[3] = 8
    packet[12:] = body
    return bytes(packet)


def _has_native_library() -> bool:
    return bool(os.environ.get("FASTDIS_LIBRARY") or native.find_native_library())


@pytest.mark.skipif(not _has_native_library(), reason="fastdis shared library is not built")
def test_ctypes_parse_header_tuple() -> None:
    lib = native.load_native()
    assert lib.abi_version() == native.FASTDIS_ABI_VERSION
    assert lib.abi_epoch() == native.FASTDIS_ABI_EPOCH == 0
    assert lib.abi_revision() == native.FASTDIS_ABI_REVISION == 16
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

    acknowledge = lib.parse_acknowledge(_make_acknowledge(7))
    assert acknowledge.header[0:4] == (7, 3, 15, 5)
    assert acknowledge.acknowledge_flag == 0x1234
    assert acknowledge.response_flag == 0x5678
    assert acknowledge.request_id == 0xCAFEBABE

    create_reliable = lib.parse_create_entity_reliable(_make_create_entity_reliable(7))
    assert create_reliable.header[0:4] == (7, 3, 51, 10)
    assert create_reliable.required_reliability_service == 7
    assert create_reliable.pad1 == 0x1357
    assert create_reliable.pad2 == 9
    assert create_reliable.request_id == 0xA0B0C0D0

    remove_reliable = lib.parse_remove_entity_reliable(_make_remove_entity_reliable(6))
    assert remove_reliable.header[0:4] == (6, 3, 52, 10)
    assert remove_reliable.required_reliability_service == 8
    assert remove_reliable.pad1 == 0x2468
    assert remove_reliable.pad2 == 10
    assert remove_reliable.request_id == 0x0BADF00D

    start_reliable = lib.parse_start_resume_reliable(_make_start_resume_reliable(7))
    assert start_reliable.header[0:4] == (7, 3, 53, 10)
    assert start_reliable.real_world_time == (7, 123456)
    assert start_reliable.simulation_time == (9, 654321)
    assert start_reliable.required_reliability_service == 11
    assert start_reliable.pad1 == 0xAAAA
    assert start_reliable.pad2 == 12
    assert start_reliable.request_id == 0x01020304

    stop_reliable = lib.parse_stop_freeze_reliable(_make_stop_freeze_reliable(6))
    assert stop_reliable.header[0:4] == (6, 3, 54, 10)
    assert stop_reliable.real_world_time == (5, 7654321)
    assert stop_reliable.reason == 3
    assert stop_reliable.frozen_behavior == 4
    assert stop_reliable.required_reliablity_service == 13
    assert stop_reliable.pad1 == 14
    assert stop_reliable.request_id == 0x0F1E2D3C

    acknowledge_reliable = lib.parse_acknowledge_reliable(_make_acknowledge_reliable(7))
    assert acknowledge_reliable.header[0:4] == (7, 3, 55, 10)
    assert acknowledge_reliable.acknowledge_flag == 0x9ABC
    assert acknowledge_reliable.response_flag == 0xDEF0
    assert acknowledge_reliable.request_id == 0xFACECAFE


@pytest.mark.skipif(not _has_native_library(), reason="fastdis shared library is not built")
def test_ctypes_parse_datum_bearing_simulation_management_pdus() -> None:
    lib = native.load_native()

    action_request = lib.parse_action_request(_make_action_request(7))
    assert action_request.header[0:4] == (7, 3, 16, 5)
    assert action_request.request_id == 0x01020304
    assert action_request.action_id == 0x11121314
    assert action_request.number_of_fixed_datum_records == 1
    assert action_request.number_of_variable_datum_records == 1
    assert action_request.datum_record_bytes == bytes.fromhex("00112233445566778899aabbccddeeff")

    data_query_reliable = lib.parse_data_query_reliable(_make_data_query_reliable(7))
    assert data_query_reliable.header[0:4] == (7, 3, 58, 10)
    assert data_query_reliable.required_reliability_service == 5
    assert data_query_reliable.request_id == 0x41424344
    assert data_query_reliable.time_interval == (222222, 3333)
    assert data_query_reliable.number_of_fixed_datum_records == 2
    assert data_query_reliable.number_of_variable_datum_records == 1
    assert data_query_reliable.datum_record_bytes == bytes.fromhex("3132333435363738393a3b3c3d3e3f40")


@pytest.mark.skipif(not _has_native_library(), reason="fastdis shared library is not built")
def test_ctypes_parse_record_reliable_pdus() -> None:
    lib = native.load_native()

    record_reliable = lib.parse_record_reliable(_make_record_reliable(7))
    assert record_reliable.header[0:4] == (7, 3, 63, 10)
    assert record_reliable.request_id == 0x51525354
    assert record_reliable.required_reliability_service == 7
    assert record_reliable.pad1 == 8
    assert record_reliable.event_type == 0x090A
    assert record_reliable.record_set_count == 2
    assert record_reliable.record_set_bytes == bytes.fromhex("1011121314151617")

    set_record_reliable = lib.parse_set_record_reliable(_make_set_record_reliable(6))
    assert set_record_reliable.header[0:4] == (6, 3, 64, 10)
    assert set_record_reliable.request_id == 0x61626364
    assert set_record_reliable.required_reliability_service == 9
    assert set_record_reliable.pad1 == 0x0B0C
    assert set_record_reliable.pad2 == 13
    assert set_record_reliable.record_set_count == 3
    assert set_record_reliable.record_set_bytes == bytes.fromhex("2122232425262728")

    record_query_reliable = lib.parse_record_query_reliable(_make_record_query_reliable(7))
    assert record_query_reliable.header[0:4] == (7, 3, 65, 10)
    assert record_query_reliable.request_id == 0x71727374
    assert record_query_reliable.required_reliability_service == 14
    assert record_query_reliable.pad1 == 0x1516
    assert record_query_reliable.pad2 == 17
    assert record_query_reliable.event_type == 0x1819
    assert record_query_reliable.time == 0x1A1B1C1D
    assert record_query_reliable.record_id_count == 2
    assert record_query_reliable.record_id_bytes == bytes.fromhex("3132333435363738")


@pytest.mark.skipif(not _has_native_library(), reason="fastdis shared library is not built")
def test_ctypes_parse_dis7_late_fixed_prefix_pdus() -> None:
    lib = native.load_native()

    attribute = lib.parse_attribute(_make_attribute(7))
    assert attribute.header[0:4] == (7, 3, 72, 1)
    assert attribute.originating_simulation_address == (0x0101, 0x0202)
    assert attribute.padding1 == 0x11223344
    assert attribute.padding2 == 0x5566
    assert attribute.attribute_record_pdu_type == 67
    assert attribute.attribute_record_protocol_version == 7
    assert attribute.master_attribute_record_type == 0x778899AA
    assert attribute.action_code == 0x12
    assert attribute.padding3 == 0x34
    assert attribute.number_attribute_record_set == 1
    assert attribute.attribute_record_set_bytes == bytes.fromhex("61626364")

    directed_energy_fire = lib.parse_directed_energy_fire(_make_directed_energy_fire(7))
    assert directed_energy_fire.header[0:4] == (7, 3, 68, 2)
    assert directed_energy_fire.firing_entity_id == (1, 2, 3)
    assert directed_energy_fire.target_entity_id == (4, 5, 6)
    assert directed_energy_fire.munition_type == (2, 1, 225, 4, 5, 6, 7)
    assert directed_energy_fire.shot_start_time == (7, 123456)
    assert directed_energy_fire.commulative_shot_time == pytest.approx(1.25)
    assert directed_energy_fire.aperture_emitter_location == pytest.approx((2.5, 3.5, 4.5))
    assert directed_energy_fire.aperture_diameter == pytest.approx(5.5)
    assert directed_energy_fire.wavelength == pytest.approx(6.5)
    assert directed_energy_fire.peak_irradiance == pytest.approx(7.5)
    assert directed_energy_fire.pulse_repetition_frequency == pytest.approx(8.5)
    assert directed_energy_fire.pulse_width == 9012
    assert directed_energy_fire.flags == 0x10203040
    assert directed_energy_fire.pulse_shape == 0x11
    assert directed_energy_fire.padding1 == 0x22
    assert directed_energy_fire.padding2 == 0x33445566
    assert directed_energy_fire.padding3 == 0x7788
    assert directed_energy_fire.number_of_de_records == 1
    assert directed_energy_fire.de_record_bytes == bytes.fromhex("90919293")

    entity_damage_status = lib.parse_entity_damage_status(_make_entity_damage_status(7))
    assert entity_damage_status.header[0:4] == (7, 3, 69, 2)
    assert entity_damage_status.firing_entity_id == (1, 2, 3)
    assert entity_damage_status.target_entity_id == (4, 5, 6)
    assert entity_damage_status.damaged_entity_id == (7, 8, 9)
    assert entity_damage_status.padding1 == 0x1112
    assert entity_damage_status.padding2 == 0x1314
    assert entity_damage_status.number_of_damage_description == 1
    assert entity_damage_status.damage_description_bytes == bytes.fromhex("a1a2a3a4")

    iff = lib.parse_iff(_make_iff(7))
    assert iff.header[0:4] == (7, 3, 28, 6)
    assert iff.emitting_entity_id == (1, 2, 3)
    assert iff.event_id == (4, 5, 6)
    assert iff.location == pytest.approx((1.0, 2.0, 3.0))
    assert iff.system_id == (0x1111, 0x2222, 0x33, 0x44)
    assert iff.padding2 == 0x5555
    assert iff.fundamental_parameters == (1, 2, 3, 4, 5, 6, 7, 8, 9, 10)

    io_action = lib.parse_information_operations_action(_make_information_operations_action(7))
    assert io_action.header[0:4] == (7, 3, 70, 13)
    assert io_action.originating_sim_id == (1, 2, 3)
    assert io_action.receiving_sim_id == (4, 5, 6)
    assert io_action.request_id == 0x11223344
    assert io_action.io_warfare_type == 0x0102
    assert io_action.io_simulation_source == 0x0304
    assert io_action.io_action_type == 0x0506
    assert io_action.io_action_phase == 0x0708
    assert io_action.padding1 == 0x55667788
    assert io_action.io_attacker_id == (7, 8, 9)
    assert io_action.io_primary_target_id == (10, 11, 12)
    assert io_action.padding2 == 0x090A
    assert io_action.number_of_io_records == 1
    assert io_action.io_record_bytes == bytes.fromhex("c1c2c3c4")

    io_report = lib.parse_information_operations_report(_make_information_operations_report(7))
    assert io_report.header[0:4] == (7, 3, 71, 13)
    assert io_report.originating_sim_id == (1, 2, 3)
    assert io_report.io_sim_source == 0x0102
    assert io_report.io_report_type == 0x03
    assert io_report.padding1 == 0x04
    assert io_report.io_attacker_id == (4, 5, 6)
    assert io_report.io_primary_target_id == (7, 8, 9)
    assert io_report.padding2 == 0x1112
    assert io_report.padding3 == 0x1314
    assert io_report.number_of_io_records == 1
    assert io_report.io_record_bytes == bytes.fromhex("d1d2d3d4")


@pytest.mark.skipif(not _has_native_library(), reason="fastdis shared library is not built")
def test_ctypes_parse_logistics_pdus() -> None:
    lib = native.load_native()

    service_request = lib.parse_service_request(_make_service_request(7))
    assert service_request.header[0:4] == (7, 3, 5, 3)
    assert service_request.service_type_requested == 7
    assert service_request.number_of_supply_types == 2
    assert service_request.service_request_padding == 0x4041
    assert service_request.supply_bytes == bytes.fromhex("4142434445464748")

    resupply_offer = lib.parse_resupply_offer(_make_resupply_offer(6))
    assert resupply_offer.header[0:4] == (6, 3, 6, 3)
    assert resupply_offer.number_of_supply_types == 2
    assert resupply_offer.padding_bytes == bytes([0x11, 0x12, 0x13])
    assert resupply_offer.supply_bytes == bytes.fromhex("5152535455565758")

    resupply_received = lib.parse_resupply_received(_make_resupply_received(7))
    assert resupply_received.header[0:4] == (7, 3, 7, 3)
    assert resupply_received.number_of_supply_types == 2
    assert resupply_received.padding1 == 0x6162
    assert resupply_received.padding2 == 0x63
    assert resupply_received.supply_bytes == bytes.fromhex("6162636465666768")

    resupply_cancel = lib.parse_resupply_cancel(_make_resupply_cancel(7))
    assert resupply_cancel.header[0:4] == (7, 3, 8, 3)
    assert resupply_cancel.receiving_entity_id == (1, 2, 3)
    assert resupply_cancel.supplying_entity_id == (4, 5, 6)

    repair_complete = lib.parse_repair_complete(_make_repair_complete(6))
    assert repair_complete.header[0:4] == (6, 3, 9, 3)
    assert repair_complete.repair == 0x7172
    assert repair_complete.padding2 == 0x7374

    repair_response = lib.parse_repair_response(_make_repair_response(7))
    assert repair_response.header[0:4] == (7, 3, 10, 3)
    assert repair_response.repair_result == 0x75
    assert repair_response.padding1 == 0x7677
    assert repair_response.padding2 == 0x78


@pytest.mark.skipif(not _has_native_library(), reason="fastdis shared library is not built")
def test_ctypes_parse_minefield_pdus() -> None:
    lib = native.load_native()

    state6 = lib.parse_minefield_state(_make_minefield_state(6))
    assert state6.header[0:4] == (6, 3, 37, 8)
    assert state6.minefield_id == (221, 222, 223)
    assert state6.minefield_sequence == 224
    assert state6.force_id == 225
    assert state6.number_of_perimeter_points == 2
    assert state6.minefield_type == (1, 2, 840, 3, 4, 5, 6)
    assert state6.number_of_mine_types == 2
    assert state6.minefield_location == pytest.approx((10.25, 20.5, 30.75))
    assert state6.minefield_orientation == pytest.approx((0.1, 0.2, 0.3))
    assert state6.appearance == 226
    assert state6.protocol_mode == 227
    assert state6.perimeter_point_bytes == struct.pack(">ffff", 1.5, 2.5, 3.5, 4.5)
    assert state6.mine_type_bytes == struct.pack(">BBHBBBBBBHBBBB", 7, 8, 124, 9, 10, 11, 12, 13, 14, 225, 15, 16, 17, 18)

    state7 = lib.parse_minefield_state(_make_minefield_state(7))
    assert state7.header[0:4] == (7, 3, 37, 8)
    assert state7.minefield_id == (231, 232, 233)
    assert state7.minefield_sequence == 234
    assert state7.force_id == 235
    assert state7.number_of_perimeter_points == 2
    assert state7.minefield_type == (19, 20, 225, 21, 22, 23, 24)
    assert state7.number_of_mine_types == 2
    assert state7.minefield_location == pytest.approx((40.25, 50.5, 60.75))
    assert state7.minefield_orientation == pytest.approx((0.4, 0.5, 0.6))
    assert state7.appearance == 236
    assert state7.protocol_mode == 237

    query = lib.parse_minefield_query(_make_minefield_query(6))
    assert query.header[0:4] == (6, 3, 38, 8)
    assert query.minefield_id == (201, 202, 203)
    assert query.requesting_entity_id == (204, 205, 206)
    assert query.request_id == 207
    assert query.number_of_perimeter_points == 2
    assert query.pad2 == 0
    assert query.number_of_sensor_types == 2
    assert query.data_filter == 0x01020304
    assert query.requested_mine_type == (3, 4, 225, 5, 6, 7, 8)
    assert query.requested_perimeter_point_bytes == struct.pack(">ffff", 1.5, 2.5, 3.5, 4.5)
    assert query.sensor_type_bytes == bytes.fromhex("11122122")

    data = lib.parse_minefield_data(_make_minefield_data(7))
    assert data.header[0:4] == (7, 3, 39, 8)
    assert data.minefield_id == (251, 252, 253)
    assert data.requesting_entity_id == (254, 255, 256)
    assert data.minefield_sequence_number == 257
    assert data.request_id == 200
    assert data.pdu_sequence_number == 3
    assert data.number_of_pdus == 2
    assert data.number_of_mines_in_this_pdu == 2
    assert data.number_of_sensor_types == 2
    assert data.pad2 == 0
    assert data.data_filter == 0x01020304
    assert data.mine_type == (37, 38, 225, 39, 40, 41, 42)
    assert data.pad3 == 0
    assert data.sensor_type_bytes == bytes.fromhex("31324142")
    assert data.mine_location_bytes == struct.pack(">ffffff", 9.5, 10.5, 11.5, 12.5, 13.5, 14.5)

    nack = lib.parse_minefield_response_nack(_make_minefield_response_nack(6))
    assert nack.header[0:4] == (6, 3, 40, 8)
    assert nack.minefield_id == (181, 182, 183)
    assert nack.requesting_entity_id == (184, 185, 186)
    assert nack.request_id == 187
    assert nack.number_of_missing_pdus == 2
    assert nack.missing_pdu_sequence_number_bytes == bytes.fromhex("01020304050607081112131415161718")


@pytest.mark.skipif(not _has_native_library(), reason="fastdis shared library is not built")
def test_ctypes_parse_synthetic_environment_pdus() -> None:
    lib = native.load_native()

    process = lib.parse_environmental_process(_make_environmental_process(6))
    assert process.header[0:4] == (6, 3, 41, 9)
    assert process.environmental_process_id == (211, 212, 213)
    assert process.environment_type == (9, 10, 840, 11, 12, 13, 14)
    assert process.model_type == 15
    assert process.environment_status == 16
    assert process.number_of_environment_records == 2
    assert process.sequence_number == 0x1718
    assert process.environment_record_bytes == bytes.fromhex("3132333435363738393a")

    grid = lib.parse_gridded_data(_make_gridded_data(7))
    assert grid.header[0:4] == (7, 3, 42, 9)
    assert grid.environmental_simulation_application_id == (261, 262, 263)
    assert grid.field_number == 264
    assert grid.pdu_number == 265
    assert grid.pdu_total == 266
    assert grid.coordinate_system == 267
    assert grid.number_of_grid_axes == 3
    assert grid.constant_grid == 1
    assert grid.environment_type == (43, 44, 840, 45, 46, 47, 48)
    assert grid.orientation == pytest.approx((0.7, 0.8, 0.9))
    assert grid.sample_time == 0x0102030405060708
    assert grid.total_values == 269
    assert grid.vector_dimension == 4
    assert grid.padding1 == 270
    assert grid.padding2 == 0
    assert grid.grid_data_bytes == bytes.fromhex("5152535455565758595a")

    point6 = lib.parse_point_object_state(_make_point_object_state(6))
    assert point6.header[0:4] == (6, 3, 43, 9)
    assert point6.object_id == (51, 52, 53)
    assert point6.referenced_object_id == (54, 55, 56)
    assert point6.update_number == 57
    assert point6.force_id == 58
    assert point6.modifications == 59
    assert point6.object_type == (2, 1, 840, 3, 4)
    assert point6.object_location == pytest.approx((100.25, 200.5, 300.75))
    assert point6.object_orientation == pytest.approx((0.1, 0.2, 0.3))
    assert point6.object_appearance == pytest.approx(1234.5)
    assert point6.requester_id == (60, 61)
    assert point6.receiving_id == (62, 63)
    assert point6.pad2 == 64

    point7 = lib.parse_point_object_state(_make_point_object_state(7))
    assert point7.object_id == (71, 72, 73)
    assert point7.referenced_object_id == (74, 75, 76)
    assert point7.object_type == (4, 5, 0, 6, 7)
    assert point7.object_location == pytest.approx((400.25, 500.5, 600.75))
    assert point7.object_orientation == pytest.approx((0.4, 0.5, 0.6))
    assert point7.object_appearance == pytest.approx(2345.5)

    linear6 = lib.parse_linear_object_state(_make_linear_object_state(6))
    assert linear6.header[0:4] == (6, 3, 44, 9)
    assert linear6.object_id == (131, 132, 133)
    assert linear6.referenced_object_id == (134, 135, 136)
    assert linear6.update_number == 137
    assert linear6.force_id == 138
    assert linear6.number_of_segments == 2
    assert linear6.requester_id == (139, 140)
    assert linear6.receiving_id == (141, 142)
    assert linear6.object_type == (10, 9, 840, 11, 12)
    assert len(linear6.linear_segment_parameter_bytes) == 2 * native.FASTDIS_LINEAR_SEGMENT_PARAMETER_DIS6_SIZE

    linear7 = lib.parse_linear_object_state(_make_linear_object_state(7))
    assert linear7.object_id == (151, 152, 153)
    assert linear7.referenced_object_id == (154, 155, 156)
    assert linear7.object_type == (13, 14, 0, 15, 16)
    assert len(linear7.linear_segment_parameter_bytes) == 2 * native.FASTDIS_LINEAR_SEGMENT_PARAMETER_DIS7_SIZE

    areal6 = lib.parse_areal_object_state(_make_areal_object_state(6))
    assert areal6.header[0:4] == (6, 3, 45, 9)
    assert areal6.object_id == (91, 92, 93)
    assert areal6.referenced_object_id == (94, 95, 96)
    assert areal6.update_number == 97
    assert areal6.force_id == 98
    assert areal6.modifications == 99
    assert areal6.object_type == (3, 4, 225, 5, 6, 7, 8)
    assert areal6.object_appearance_bytes == bytes.fromhex("010203040506")
    assert areal6.number_of_points == 2
    assert areal6.requester_id == (100, 101)
    assert areal6.receiving_id == (102, 103)
    assert len(areal6.object_location_bytes) == 48

    areal7 = lib.parse_areal_object_state(_make_areal_object_state(7))
    assert areal7.object_id == (111, 112, 113)
    assert areal7.referenced_object_id == (114, 115, 116)
    assert areal7.object_type == (6, 7, 124, 8, 9, 10, 11)
    assert areal7.object_appearance_bytes == struct.pack(">IH", 120, 121)
    assert areal7.number_of_points == 2
    assert areal7.requester_id == (122, 123)
    assert areal7.receiving_id == (124, 125)
    assert len(areal7.object_location_bytes) == 48


@pytest.mark.skipif(not _has_native_library(), reason="fastdis shared library is not built")
def test_ctypes_parse_radio_designator_pdus() -> None:
    lib = native.load_native()

    designator = lib.parse_designator(_make_designator(7))
    assert designator.header[0:4] == (7, 3, 24, 6)
    assert designator.designating_entity_id == (1, 2, 3)
    assert designator.code_name == 0x1234
    assert designator.designated_entity_id == (4, 5, 6)
    assert designator.designator_code == 0x2345
    assert designator.designator_power == pytest.approx(12.5)
    assert designator.designator_wavelength == pytest.approx(1.25)
    assert designator.designator_spot_wrt_designated == pytest.approx((2.5, 3.5, 4.5))
    assert designator.designator_spot_location == pytest.approx((100.0, 200.0, 300.0))
    assert designator.dead_reckoning_algorithm == 4
    assert designator.padding1 == 0x3456
    assert designator.padding2 == 0x78
    assert designator.entity_linear_acceleration == pytest.approx((5.5, 6.5, 7.5))

    signal6 = lib.parse_signal(_make_signal(6))
    assert signal6.header[0:4] == (6, 3, 26, 4)
    assert signal6.entity_id == (1, 2, 3)
    assert signal6.radio_id == 0x1111
    assert signal6.encoding_scheme == 0x2222
    assert signal6.tdl_type == 0x3333
    assert signal6.sample_rate == 48000
    assert signal6.data_length == 4
    assert signal6.samples == 2
    assert signal6.data_bytes == bytes.fromhex("41424344")

    signal7 = lib.parse_signal(_make_signal(7))
    assert signal7.header[0:4] == (7, 3, 26, 4)
    assert signal7.entity_id == (0, 0, 0)
    assert signal7.radio_id == 0
    assert signal7.data_bytes == bytes.fromhex("41424344")

    receiver6 = lib.parse_receiver(_make_receiver(6))
    assert receiver6.header[0:4] == (6, 3, 27, 4)
    assert receiver6.entity_id == (1, 2, 3)
    assert receiver6.radio_id == 0x1111
    assert receiver6.receiver_state == 0x2222
    assert receiver6.padding1 == 0x3333
    assert receiver6.received_power == pytest.approx(12.5)
    assert receiver6.transmitter_entity_id == (4, 5, 6)
    assert receiver6.transmitter_radio_id == 0x4444

    receiver7 = lib.parse_receiver(_make_receiver(7))
    assert receiver7.header[0:4] == (7, 3, 27, 4)
    assert receiver7.entity_id == (0, 0, 0)
    assert receiver7.radio_id == 0
    assert receiver7.transmitter_entity_id == (4, 5, 6)

    intercom = lib.parse_intercom_signal(_make_intercom_signal(7))
    assert intercom.header[0:4] == (7, 3, 31, 4)
    assert intercom.entity_id == (1, 2, 3)
    assert intercom.communications_device_id == 0x1212
    assert intercom.encoding_scheme == 0x2222
    assert intercom.tdl_type == 0x3333
    assert intercom.sample_rate == 32000
    assert intercom.data_length == 4
    assert intercom.samples == 2
    assert intercom.data_bytes == bytes.fromhex("51525354")

    transmitter6 = lib.parse_transmitter(_make_transmitter(6))
    assert transmitter6.header[0:4] == (6, 3, 25, 4)
    assert transmitter6.entity_id == (1, 2, 3)
    assert transmitter6.radio_id == 0x1212
    assert transmitter6.radio_entity_type == (1, 2, 840, 5, 6, 0x0708)
    assert transmitter6.entity_type == (0, 0, 0, 0, 0, 0, 0)
    assert transmitter6.transmit_state == 9
    assert transmitter6.input_source == 10
    assert transmitter6.modulation_parameter_count == 3
    assert transmitter6.modulation_parameter_bytes == bytes.fromhex("010203")
    assert transmitter6.antenna_pattern_bytes == b""

    transmitter7 = lib.parse_transmitter(_make_transmitter(7))
    assert transmitter7.header[0:4] == (7, 3, 25, 4)
    assert transmitter7.entity_type == (1, 2, 840, 5, 6, 7, 8)
    assert transmitter7.variable_transmitter_parameter_count == 2
    assert transmitter7.frequency == 225000
    assert transmitter7.transmit_frequency_bandwidth == pytest.approx(50.5)
    assert transmitter7.power == pytest.approx(60.5)
    assert transmitter7.modulation_type == (1, 2, 3, 4)
    assert transmitter7.modulation_parameter_bytes == struct.pack(">fff", 9.0, 10.0, 11.0)
    assert transmitter7.antenna_pattern_bytes == struct.pack(">fff", 12.0, 13.0, 14.0)

    iff = lib.parse_iff_atc_navaids_layer1(_make_iff_atc_navaids_layer1(7))
    assert iff.header[0:4] == (7, 3, 28, 6)
    assert iff.emitting_entity_id == (1, 2, 3)
    assert iff.event_id == (4, 5, 6)
    assert iff.location == pytest.approx((1.0, 2.0, 3.0))
    assert iff.system_id == (0x1111, 0x2222, 0x33, 0x44)
    assert iff.padding2 == 0x5555
    assert iff.fundamental_parameters == (1, 2, 3, 4, 5, 6, 7, 8, 9, 10)

    intercom_control = lib.parse_intercom_control(_make_intercom_control(7))
    assert intercom_control.header[0:4] == (7, 3, 32, 4)
    assert intercom_control.control_type == 0x11
    assert intercom_control.communications_channel_type == 0x22
    assert intercom_control.source_entity_id == (1, 2, 3)
    assert intercom_control.source_communications_device_id == 0x33
    assert intercom_control.source_line_id == 0x44
    assert intercom_control.transmit_priority == 0x55
    assert intercom_control.transmit_line_state == 0x66
    assert intercom_control.command == 0x77
    assert intercom_control.master_entity_id == (4, 5, 6)
    assert intercom_control.master_communications_device_id == 0x8888
    assert intercom_control.intercom_parameters_length == 4
    assert intercom_control.intercom_parameters_bytes == b"abcd"


@pytest.mark.skipif(not _has_native_library(), reason="fastdis shared library is not built")
def test_ctypes_parse_distributed_emissions_pdus() -> None:
    lib = native.load_native()

    electronic6 = lib.parse_electronic_emissions(_make_electronic_emissions(6))
    assert electronic6.header[0:4] == (6, 3, 23, 6)
    assert electronic6.emitting_entity_id == (1, 2, 3)
    assert electronic6.event_id == (4, 5, 6)
    assert electronic6.state_update_indicator == 0x07
    assert electronic6.number_of_systems == 0x02
    assert electronic6.padding1 == 0x0809
    assert electronic6.system_record_bytes == bytes.fromhex("e1e2e3e4e5e6")

    electronic7 = lib.parse_electronic_emissions(_make_electronic_emissions(7))
    assert electronic7.header[0:4] == (7, 3, 23, 6)
    assert electronic7.system_record_bytes == bytes.fromhex("e1e2e3e4e5e6")

    ua = lib.parse_ua(_make_ua(6))
    assert ua.header[0:4] == (6, 3, 29, 6)
    assert ua.emitting_entity_id == (1, 2, 3)
    assert ua.event_id == (4, 5, 6)
    assert ua.state_change_indicator == 0x0A
    assert ua.padding1 == 0x0B
    assert ua.passive_parameter_index == 0x0C0D
    assert ua.propulsion_plant_configuration == 0x0E
    assert ua.number_of_shafts == 1
    assert ua.number_of_apas == 2
    assert ua.number_of_ua_emitter_systems == 3
    assert ua.ua_record_bytes == bytes.fromhex("f1f2f3f4f5f6f7f8")

    sees = lib.parse_sees(_make_sees(7))
    assert sees.header[0:4] == (7, 3, 30, 6)
    assert sees.originating_entity_id == (0x0011, 0x0022, 0x0033)
    assert sees.infrared_signature_representation_index == 0x1112
    assert sees.acoustic_signature_representation_index == 0x1314
    assert sees.radar_cross_section_signature_representation_index == 0x1516
    assert sees.number_of_propulsion_systems == 2
    assert sees.number_of_vectoring_nozzle_systems == 3
    assert sees.supplemental_emission_record_bytes == bytes.fromhex("aabbccddeeff0011")


@pytest.mark.skipif(not _has_native_library(), reason="fastdis shared library is not built")
def test_ctypes_parse_protocol_family_zero_and_entity_management_pdus() -> None:
    lib = native.load_native()

    other6 = lib.parse_other_pdu(_make_other(6))
    assert other6.header[0:4] == (6, 3, 0, 0)
    assert other6.opaque_payload_bytes == b"OTHR"

    other7 = lib.parse_other_pdu(_make_other(7))
    assert other7.header[0:4] == (7, 3, 0, 0)
    assert other7.opaque_payload_bytes == b"OTHR"

    aggregate = lib.parse_aggregate_state(_make_aggregate_state(7))
    assert aggregate.header[0:4] == (7, 3, 33, 7)
    assert aggregate.aggregate_id == (1, 2, 3)
    assert aggregate.force_id == 4
    assert aggregate.aggregate_state == 5
    assert aggregate.aggregate_type == (1, 2, 840, 3, 4, 5, 6)
    assert aggregate.formation == 0x11223344
    assert aggregate.aggregate_marking_character_set == 1
    assert aggregate.aggregate_marking.startswith(b"AGGREGATE-ALPHA")
    assert aggregate.dimensions == pytest.approx((1.0, 2.0, 3.0))
    assert aggregate.orientation == pytest.approx((0.1, 0.2, 0.3))
    assert aggregate.center_of_mass == pytest.approx((10.0, 20.0, 30.0))
    assert aggregate.velocity == pytest.approx((4.0, 5.0, 6.0))
    assert aggregate.number_of_dis_aggregates == 7
    assert aggregate.number_of_dis_entities == 8
    assert aggregate.number_of_silent_aggregate_types == 9
    assert aggregate.number_of_silent_entity_types == 10
    assert aggregate.aggregate_record_bytes == bytes.fromhex("a1a2a3a4a5a6")

    group = lib.parse_is_group_of(_make_is_group_of(6))
    assert group.header[0:4] == (6, 3, 34, 7)
    assert group.group_entity_id == (1, 2, 3)
    assert group.grouped_entity_category == 0x21
    assert group.number_of_grouped_entities == 2
    assert group.pad2 == 0x10203040
    assert group.latitude == pytest.approx(41.25)
    assert group.longitude == pytest.approx(-93.5)
    assert group.grouped_entity_description_bytes == bytes.fromhex("b1b2b3b4")

    control = lib.parse_transfer_control_request(_make_transfer_control_request(6))
    assert control.header[0:4] == (6, 3, 35, 7)
    assert control.originating_entity_id == (1, 2, 3)
    assert control.receiving_entity_id == (4, 5, 6)
    assert control.request_id == 0x11223344
    assert control.required_reliability_service == 0x07
    assert control.transfer_type == 0x08
    assert control.transfer_entity_id == (7, 8, 9)
    assert control.number_of_record_sets == 0x02
    assert control.record_set_bytes == bytes.fromhex("c1c2c3c4")

    ownership = lib.parse_transfer_ownership(_make_transfer_ownership(7))
    assert ownership.header[0:4] == (7, 3, 35, 7)
    assert ownership.originating_entity_id == (10, 11, 12)
    assert ownership.receiving_entity_id == (13, 14, 15)
    assert ownership.request_id == 0x55667788
    assert ownership.required_reliability_service == 0x09
    assert ownership.transfer_type == 0x0A
    assert ownership.transfer_entity_id == (16, 17, 18)
    assert ownership.number_of_record_sets == 0x03
    assert ownership.record_set_bytes == bytes.fromhex("d1d2d3d4")

    part = lib.parse_is_part_of(_make_is_part_of(7))
    assert part.header[0:4] == (7, 3, 36, 7)
    assert part.originating_entity_id == (1, 2, 3)
    assert part.receiving_entity_id == (4, 5, 6)
    assert part.relationship == (0x1112, 0x1314)
    assert part.part_location == pytest.approx((7.0, 8.0, 9.0))
    assert part.named_location == (0x2122, 0x2324)
    assert part.part_entity_type == (2, 3, 225, 4, 5, 6, 7)


@pytest.mark.skipif(not _has_native_library(), reason="fastdis shared library is not built")
def test_ctypes_parse_warfare_pdus() -> None:
    lib = native.load_native()

    fire = lib.parse_fire(_make_fire(7))
    assert fire.header[0:4] == (7, 3, 2, 2)
    assert fire.firing_entity_id == (1, 2, 3)
    assert fire.target_entity_id == (4, 5, 6)
    assert fire.munition_entity_id == (7, 8, 9)
    assert fire.event_id == (10, 11, 12)
    assert fire.fire_mission_index == 99
    assert fire.world_location == pytest.approx((1000.5, 2000.25, 3000.75))
    assert fire.munition_type == (2, 1, 225, 4, 5, 6, 7)
    assert (fire.warhead, fire.fuse, fire.quantity, fire.rate) == (101, 202, 3, 600)
    assert fire.velocity == pytest.approx((1.5, 2.5, 3.5))
    assert fire.range_to_target == pytest.approx(4444.5)

    detonation = lib.parse_detonation(_make_detonation(6))
    assert detonation.header[0:4] == (6, 3, 3, 2)
    assert detonation.firing_entity_id == (1, 2, 3)
    assert detonation.target_entity_id == (4, 5, 6)
    assert detonation.exploding_entity_id == (7, 8, 9)
    assert detonation.event_id == (10, 11, 12)
    assert detonation.velocity == pytest.approx((11.0, 22.0, 33.0))
    assert detonation.world_location == pytest.approx((111.5, 222.25, 333.75))
    assert detonation.munition_type == (2, 1, 225, 4, 5, 6, 7)
    assert detonation.location_in_entity_coordinates == pytest.approx((-4.0, -5.0, -6.0))
    assert detonation.detonation_result == 17
    assert detonation.variable_parameter_count == 1
    assert detonation.padding1 == 0


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
