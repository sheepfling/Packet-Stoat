"""Pure-Python fallback implementation for fastdis.

The public API intentionally mirrors the optional C accelerator. Keep this file
simple and allocation-light so it is also useful as reference code.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Callable

HeaderTuple = tuple[int, int, int, int, int, int, int, int]
PacketCallback = Callable[[int, int, int, int, int, int, int, object], object]


def _mask(values: None | int | Iterable[int], name: str) -> set[int] | None:
    if values is None:
        return None
    if isinstance(values, int):
        vals = [values]
    else:
        vals = list(values)
    out: set[int] = set()
    for value in vals:
        if not isinstance(value, int):
            raise TypeError(f"{name} values must be integers")
        if not 0 <= value <= 255:
            raise ValueError(f"{name} values must be in the range 0..255")
        out.add(value)
    return out


def _be16(buf: memoryview, offset: int) -> int:
    return (buf[offset] << 8) | buf[offset + 1]


def _be32(buf: memoryview, offset: int) -> int:
    return (
        (buf[offset] << 24)
        | (buf[offset + 1] << 16)
        | (buf[offset + 2] << 8)
        | buf[offset + 3]
    )


def parse_header(data: bytes | bytearray | memoryview, strict: bool = True) -> HeaderTuple | None:
    """Parse a DIS PDU header and return an 8-int tuple.

    Tuple layout:
        (version, exercise_id, pdu_type, protocol_family,
         timestamp, length, status, padding)

    For DIS 6 / pre-DIS7 packets, status is -1 and padding is the 16-bit
    padding field. For DIS 7+, status is byte 10 and padding is byte 11.
    """

    try:
        buf = memoryview(data).cast("B")
    except TypeError:
        if strict:
            raise
        return None

    if len(buf) < 12:
        if strict:
            raise ValueError("DIS PDU is shorter than the 12-byte header")
        return None

    version = buf[0]
    exercise_id = buf[1]
    pdu_type = buf[2]
    protocol_family = buf[3]
    timestamp = _be32(buf, 4)
    length = _be16(buf, 8)

    if length < 12:
        if strict:
            raise ValueError("DIS PDU length field is smaller than the header")
        return None
    if length > len(buf):
        if strict:
            raise ValueError("DIS PDU length field exceeds supplied buffer length")
        return None

    if version >= 7:
        status = buf[10]
        padding = buf[11]
    else:
        status = -1
        padding = _be16(buf, 10)

    return (version, exercise_id, pdu_type, protocol_family, timestamp, length, status, padding)


def _matches(
    header: HeaderTuple,
    pdu_types: set[int] | None,
    versions: set[int] | None,
    families: set[int] | None,
    exercise_ids: set[int] | None,
) -> bool:
    return (
        (pdu_types is None or header[2] in pdu_types)
        and (versions is None or header[0] in versions)
        and (families is None or header[3] in families)
        and (exercise_ids is None or header[1] in exercise_ids)
    )


def scan_many(
    packets: Iterable[bytes | bytearray | memoryview],
    callback: PacketCallback | None,
    *,
    pdu_types: None | int | Iterable[int] = None,
    versions: None | int | Iterable[int] = None,
    families: None | int | Iterable[int] = None,
    exercise_ids: None | int | Iterable[int] = None,
    sample_every: int = 1,
    sample_offset: int = 0,
    strict: bool = False,
) -> tuple[int, int, int]:
    """Scan datagrams, filter early, and invoke a callback only for retained PDUs.

    The callback signature is:
        callback(version, exercise_id, pdu_type, protocol_family,
                 timestamp, length, status, packet)

    The packet object is passed through without copying.
    """

    if callback is not None and not callable(callback):
        raise TypeError("callback must be callable or None")
    if sample_every < 1:
        raise ValueError("sample_every must be >= 1")

    pdu_type_set = _mask(pdu_types, "pdu_types")
    version_set = _mask(versions, "versions")
    family_set = _mask(families, "families")
    exercise_set = _mask(exercise_ids, "exercise_ids")
    normalized_offset = sample_offset % sample_every

    seen = accepted = emitted = 0
    for packet in packets:
        seen += 1
        header = parse_header(packet, strict=strict)
        if header is None:
            continue
        if not _matches(header, pdu_type_set, version_set, family_set, exercise_set):
            continue
        accepted_index = accepted
        accepted += 1
        if accepted_index % sample_every != normalized_offset:
            continue
        emitted += 1
        if callback is not None:
            callback(*header[:7], packet)

    return seen, accepted, emitted


def count_by_type(
    packets: Iterable[bytes | bytearray | memoryview],
    *,
    versions: None | int | Iterable[int] = None,
    families: None | int | Iterable[int] = None,
    exercise_ids: None | int | Iterable[int] = None,
    strict: bool = False,
) -> list[int]:
    """Return a 256-entry count table indexed by PDU type."""

    version_set = _mask(versions, "versions")
    family_set = _mask(families, "families")
    exercise_set = _mask(exercise_ids, "exercise_ids")
    counts = [0] * 256

    for packet in packets:
        header = parse_header(packet, strict=strict)
        if header is None:
            continue
        if _matches(header, None, version_set, family_set, exercise_set):
            counts[header[2]] += 1
    return counts
