from __future__ import annotations

import fastdis


def pdu(version: int, pdu_type: int, *, exercise: int = 1, family: int = 1) -> bytes:
    header = bytearray(12)
    header[0] = version
    header[1] = exercise
    header[2] = pdu_type
    header[3] = family
    header[8:10] = (12).to_bytes(2, "big")
    if version >= 7:
        header[10] = 0
        header[11] = 0
    return bytes(header)


def test_scan_filters_and_downsamples_without_copying() -> None:
    packets = [
        pdu(7, 1),
        pdu(7, 2),
        pdu(6, 1),
        pdu(7, 1),
        b"bad",
        pdu(7, 1),
    ]
    called = []

    def cb(version, exercise_id, pdu_type, protocol_family, timestamp, length, status, packet):
        called.append((version, exercise_id, pdu_type, protocol_family, timestamp, length, status, packet))

    stats = fastdis.scan_many(
        packets,
        cb,
        versions={7},
        pdu_types={1},
        sample_every=2,
        strict=False,
    )

    assert stats == (6, 3, 2)
    assert len(called) == 2
    assert called[0][0:7] == (7, 1, 1, 1, 0, 12, 0)
    assert called[0][7] is packets[0]
    assert called[1][7] is packets[5]


def test_scan_can_count_without_callback() -> None:
    packets = [pdu(7, 1), pdu(7, 1), pdu(7, 2), pdu(6, 1)]
    assert fastdis.scan_many(packets, None, versions=7, pdu_types=1) == (4, 2, 2)


def test_count_by_type() -> None:
    counts = fastdis.count_by_type([pdu(7, 1), pdu(7, 2), pdu(7, 1), pdu(6, 1)], versions=7)
    assert counts[1] == 2
    assert counts[2] == 1
    assert counts[3] == 0
