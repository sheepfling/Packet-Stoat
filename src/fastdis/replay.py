"""Replay helpers for the dependency-free `.fastdispkt` v1 format."""

from __future__ import annotations

from pathlib import Path
from typing import BinaryIO, Iterable, Iterator


MAX_PACKET_LENGTH = 16 * 1024 * 1024


class ReplayFormatError(ValueError):
    """Raised when a replay file is malformed."""


def _read_exact(handle: BinaryIO, size: int) -> bytes:
    data = handle.read(size)
    if len(data) != size:
        raise ReplayFormatError("truncated replay file")
    return data


def iter_v1_packets(path: str | Path) -> Iterator[bytes]:
    """Yield packets from a simple length-prefixed `.fastdispkt` v1 replay."""

    replay_path = Path(path)
    with replay_path.open("rb") as handle:
        while True:
            length_bytes = handle.read(4)
            if not length_bytes:
                return
            if len(length_bytes) != 4:
                raise ReplayFormatError("truncated replay file before packet length")
            length = int.from_bytes(length_bytes, "big")
            if length <= 0 or length > MAX_PACKET_LENGTH:
                raise ReplayFormatError(f"invalid replay packet length: {length}")
            yield _read_exact(handle, length)


def read_v1_packets(path: str | Path, *, limit: int | None = None) -> list[bytes]:
    """Read packets from a `.fastdispkt` v1 replay into memory."""

    packets: list[bytes] = []
    for packet in iter_v1_packets(path):
        packets.append(packet)
        if limit is not None and len(packets) >= limit:
            break
    return packets


def write_v1_packets(path: str | Path, packets: Iterable[bytes | bytearray | memoryview]) -> int:
    """Write packets to a `.fastdispkt` v1 replay file."""

    replay_path = Path(path)
    replay_path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with replay_path.open("wb") as handle:
        for packet in packets:
            blob = bytes(packet)
            length = len(blob)
            if length <= 0 or length > MAX_PACKET_LENGTH:
                raise ReplayFormatError(f"invalid replay packet length: {length}")
            handle.write(length.to_bytes(4, "big"))
            handle.write(blob)
            count += 1
    return count
