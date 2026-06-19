from __future__ import annotations

from pathlib import Path

import pytest

from fastdis.replay import ReplayFormatError, read_v1_packets, write_v1_packets
from fastdis.tools._shared import EntityStateSpec, make_entity_state_packet


def test_replay_v1_roundtrip(tmp_path: Path) -> None:
    packets = [
        make_entity_state_packet(EntityStateSpec(entity=1)),
        make_entity_state_packet(EntityStateSpec(entity=2)),
    ]
    path = tmp_path / "sample.fastdispkt"
    assert write_v1_packets(path, packets) == 2
    assert read_v1_packets(path) == packets


def test_replay_v1_rejects_truncated_file(tmp_path: Path) -> None:
    path = tmp_path / "bad.fastdispkt"
    path.write_bytes(b"\x00\x00\x00\x10short")
    with pytest.raises(ReplayFormatError):
        read_v1_packets(path)
