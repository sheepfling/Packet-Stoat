from __future__ import annotations

import json

from fastdis.replay import read_v1_packets, write_v1_packets
from fastdis.tools._shared import EntityStateSpec, make_entity_state_packet


def test_replay_json_cli_roundtrip_and_diff(tmp_path) -> None:
    from fastdis.tools import replay_json

    packets = [
        make_entity_state_packet(EntityStateSpec(entity=1, marking="ONE")),
        make_entity_state_packet(EntityStateSpec(entity=2, marking="TWO")),
    ]
    replay_path = tmp_path / "capture.fastdispkt"
    jsonl_path = tmp_path / "capture.jsonl"
    rebuilt_path = tmp_path / "rebuilt.fastdispkt"
    roundtrip_path = tmp_path / "roundtrip.fastdispkt"
    write_v1_packets(replay_path, packets)

    assert replay_json.main(["to-json", str(replay_path), "--out", str(jsonl_path)]) == 0
    records = [json.loads(line) for line in jsonl_path.read_text(encoding="utf-8").splitlines()]
    assert [record["record_index"] for record in records] == [0, 1]
    assert all(record["packet"]["raw_base64"] for record in records)

    assert replay_json.main(["from-json", str(jsonl_path), "--out", str(rebuilt_path)]) == 0
    assert read_v1_packets(rebuilt_path) == packets

    assert replay_json.main(["roundtrip", str(replay_path), "--out", str(roundtrip_path)]) == 0
    assert read_v1_packets(roundtrip_path) == packets
    assert replay_json.main(["diff", str(replay_path), str(roundtrip_path)]) == 0


def test_replay_json_diff_detects_mismatch(tmp_path) -> None:
    from fastdis.tools import replay_json

    left = tmp_path / "left.fastdispkt"
    right = tmp_path / "right.fastdispkt"
    write_v1_packets(left, [make_entity_state_packet(EntityStateSpec(entity=1))])
    write_v1_packets(right, [make_entity_state_packet(EntityStateSpec(entity=2))])

    assert replay_json.main(["diff", str(left), str(right)]) == 1
