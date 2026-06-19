from __future__ import annotations

from pathlib import Path
import socket
import threading

import pytest

from fastdis import parse_header
from fastdis.native import find_native_library
from fastdis.replay import read_v1_packets, write_v1_packets
from fastdis.tools._shared import EntityStateSpec, make_entity_state_packet, receive_udp_packets, send_udp_packets
from fastdis.tools.net_smoke import main as net_smoke_main


def _ephemeral_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def test_send_udp_packets_roundtrip() -> None:
    port = _ephemeral_port()
    captured: list[bytes] = []
    packets = [make_entity_state_packet(EntityStateSpec(entity=7))]

    def _receiver() -> None:
        captured.extend(receive_udp_packets(bind_host="127.0.0.1", port=port, max_packets=1, timeout_s=1.0))

    thread = threading.Thread(target=_receiver, daemon=True)
    thread.start()
    send_udp_packets(packets=packets, host="127.0.0.1", port=port)
    thread.join(timeout=2.0)

    assert len(captured) == 1
    header = parse_header(captured[0], strict=True)
    assert header is not None
    assert header.pdu_type == 1


def test_replay_send_source_is_compatible_with_replay_reader(tmp_path: Path) -> None:
    packets = [
        make_entity_state_packet(EntityStateSpec(entity=1)),
        make_entity_state_packet(EntityStateSpec(entity=2)),
    ]
    path = tmp_path / "capture.fastdispkt"
    write_v1_packets(path, packets)
    assert read_v1_packets(path) == packets


def test_net_smoke_passes_when_native_library_is_available(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    if not find_native_library():
        pytest.skip("native fastdis library not available")
    replay_path = tmp_path / "smoke.fastdispkt"
    monkeypatch.setattr(
        "sys.argv",
        [
            "net_smoke",
            "--count",
            "4",
            "--entity-count",
            "2",
            "--entity",
            "0",
            "--write-replay",
            str(replay_path),
        ],
    )
    rc = net_smoke_main()
    assert rc == 0
    packets = read_v1_packets(replay_path)
    assert len(packets) == 4
    headers = [parse_header(packet, strict=True) for packet in packets]
    assert all(header is not None for header in headers)
