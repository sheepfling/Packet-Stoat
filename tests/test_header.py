from __future__ import annotations

import pytest

import fastdis


def pdu(version: int, pdu_type: int, *, length: int = 12, status: int = 0, padding: int = 0) -> bytes:
    header = bytearray(12)
    header[0] = version
    header[1] = 3  # exercise ID
    header[2] = pdu_type
    header[3] = 1  # protocol family
    header[4:8] = (0x01020304).to_bytes(4, "big")
    header[8:10] = length.to_bytes(2, "big")
    if version >= 7:
        header[10] = status
        header[11] = padding & 0xFF
    else:
        header[10:12] = padding.to_bytes(2, "big")
    return bytes(header) + b"x" * max(0, length - 12)


def test_parse_dis7_header_tuple() -> None:
    got = fastdis.parse_header_tuple(pdu(7, 1, status=0x80, padding=0x00))
    assert got == (7, 3, 1, 1, 0x01020304, 12, 0x80, 0)


def test_parse_dis6_header_tuple() -> None:
    got = fastdis.parse_header_tuple(pdu(6, 1, padding=0x1234))
    assert got == (6, 3, 1, 1, 0x01020304, 12, -1, 0x1234)


def test_parse_header_named_object() -> None:
    got = fastdis.parse_header(pdu(7, 2, status=7))
    assert got is not None
    assert got.version == 7
    assert got.pdu_type == 2
    assert got.status == 7


def test_invalid_short_packet_strict_false() -> None:
    assert fastdis.parse_header_tuple(b"abc", strict=False) is None


def test_invalid_short_packet_strict_true() -> None:
    with pytest.raises(ValueError):
        fastdis.parse_header_tuple(b"abc", strict=True)


def test_invalid_length_too_large() -> None:
    packet = bytearray(pdu(7, 1, length=12))
    packet[8:10] = (13).to_bytes(2, "big")
    with pytest.raises(ValueError):
        fastdis.parse_header_tuple(bytes(packet), strict=True)
