from __future__ import annotations

from pathlib import Path
import json
import socket
import threading
import time

import pytest

from fastdis import parse_header
from fastdis.native import find_native_library
from fastdis.replay import read_v1_packets, write_v1_packets
from fastdis.tools._shared import (
    EntityStateSpec,
    load_session_truth,
    make_entity_state_packet,
    receive_udp_packets,
    send_udp_packets,
)
from fastdis.tools.net_smoke import main as net_smoke_main
from fastdis.tools.recv import main as recv_main
from fastdis.tools.send_entity import build_packets


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


def test_send_entity_can_emit_truth_file(tmp_path: Path) -> None:
    class Args:
        count = 4
        entity_count = 2
        site = 100
        application = 1
        entity = 0
        force_id = 1
        exercise_id = 3
        marking = "FASTDIS"
        lat = 29.5597
        lon = -95.0831
        alt = 100.0
        heading = 90.0
        pitch = 0.0
        roll = 0.0

    packets, _orientation, truth = build_packets(Args())
    assert len(packets) == 4
    truth_path = tmp_path / "expected_session.json"
    truth_path.write_text(json.dumps(truth, indent=2), encoding="utf-8")
    payload = load_session_truth(truth_path)
    assert payload["packet_count"] == 4
    assert payload["unique_entities"] == 2
    assert [entity["entity"] for entity in payload["latest_entities"]] == [0, 1]


def test_recv_verifies_truth_when_native_library_is_available(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    if not find_native_library():
        pytest.skip("native fastdis library not available")
    port = _ephemeral_port()
    truth_path = tmp_path / "expected_session.json"

    class Args:
        count = 4
        entity_count = 2
        site = 100
        application = 1
        entity = 0
        force_id = 1
        exercise_id = 3
        marking = "FASTDIS"
        lat = 29.5597
        lon = -95.0831
        alt = 100.0
        heading = 90.0
        pitch = 0.0
        roll = 0.0

    packets, _orientation, truth = build_packets(Args())
    truth_path.write_text(json.dumps(truth, indent=2), encoding="utf-8")

    def _sender() -> None:
        time.sleep(0.1)
        send_udp_packets(packets=packets, host="127.0.0.1", port=port)

    thread = threading.Thread(target=_sender, daemon=True)
    thread.start()
    monkeypatch.setattr(
        "sys.argv",
        [
            "recv",
            "--bind",
            "127.0.0.1",
            "--port",
            str(port),
            "--max-packets",
            "4",
            "--timeout",
            "1.0",
            "--surface",
            "python",
            "--verify",
            str(truth_path),
        ],
    )
    rc = recv_main()
    thread.join(timeout=2.0)
    assert rc == 0
    report = json.loads(capsys.readouterr().out)
    assert report["surface"] == "python"
    assert report["packets_received"] == 4
    assert report["unique_entities"] == 2
    assert report["errors"] == []
