from __future__ import annotations

import json
import os
from pathlib import Path

from fastdis.replay import read_v1_packets
from fastdis.replay import write_v1_packets
from fastdis.tools.lattice_shim import main as lattice_shim_main
from fastdis.tools._shared import EntityStateSpec, make_entity_state_packet


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = ROOT / "integrations" / "lattice" / "examples"
DIS_FIXTURE = FIXTURE_DIR / "dis_entity_fixture.json"
TRACK_FIXTURE = FIXTURE_DIR / "lattice_track_fixture.json"
OBJECT_FIXTURE = FIXTURE_DIR / "object_fixture.json"
TASK_FIXTURE = FIXTURE_DIR / "task_fixture.json"


def test_dis_to_shim_writes_reports(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        "sys.argv",
        [
            "lattice_shim",
            "dis-to-shim",
            str(DIS_FIXTURE),
            "--out-dir",
            str(tmp_path),
        ],
    )

    rc = lattice_shim_main()

    assert rc == 0
    report = json.loads((tmp_path / "dis_to_shim_report.json").read_text(encoding="utf-8"))
    entities = json.loads((tmp_path / "shim_entities.json").read_text(encoding="utf-8"))
    assert report["accepted"] == 1
    assert report["entity_count"] == 1
    assert entities[0]["entityId"].startswith("packet-stoat:dis:v7:")
    assert (tmp_path / "shim_event_log.jsonl").is_file()


def test_shim_to_dis_writes_replay_and_report(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        "sys.argv",
        [
            "lattice_shim",
            "shim-to-dis",
            str(TRACK_FIXTURE),
            "--out-dir",
            str(tmp_path),
        ],
    )

    rc = lattice_shim_main()

    assert rc == 0
    report = json.loads((tmp_path / "shim_to_dis_report.json").read_text(encoding="utf-8"))
    replay_path = tmp_path / "shim_to_dis.fastdispkt"
    packets = read_v1_packets(replay_path)
    assert report["packet_count"] == 1
    assert report["exportable_entity_count"] == 1
    assert report["suppressed_entity_count"] == 0
    assert report["stream_event_count"] == 2
    assert report["entity_ids"][0].startswith("packet-stoat:dis:v7:")
    assert len(packets) == 1
    assert report["packet_lengths"] == [len(packets[0])]
    assert (tmp_path / "canonical_entities.json").is_file()
    assert (tmp_path / "stream_events.json").is_file()


def test_dis_to_shim_accepts_replay_fixture_when_native_library_is_available(monkeypatch, tmp_path: Path) -> None:
    if not os.environ.get("FASTDIS_LIBRARY"):
        try:
            from fastdis.native import find_native_library
        except Exception:
            def find_native_library() -> None:
                return None
        if not find_native_library():
            import pytest

            pytest.skip("native fastdis library not available")

    replay_path = tmp_path / "sample.fastdispkt"
    packets = [
        make_entity_state_packet(EntityStateSpec(site=200, application=3, entity=9, force_id=2)),
        make_entity_state_packet(EntityStateSpec(site=200, application=3, entity=10, force_id=1)),
    ]
    write_v1_packets(replay_path, packets)

    monkeypatch.setattr(
        "sys.argv",
        [
            "lattice_shim",
            "dis-to-shim",
            str(replay_path),
            "--out-dir",
            str(tmp_path / "replay_out"),
        ],
    )

    rc = lattice_shim_main()

    assert rc == 0
    report = json.loads((tmp_path / "replay_out" / "dis_to_shim_report.json").read_text(encoding="utf-8"))
    entities = json.loads((tmp_path / "replay_out" / "shim_entities.json").read_text(encoding="utf-8"))
    assert report["accepted"] == 2
    assert report["entity_count"] == 2
    assert entities[0]["packetStoat"]["source"] == "dis-ingress"


def test_shim_to_dis_suppresses_dis_ingress_loop_payloads(monkeypatch, tmp_path: Path) -> None:
    replay_path = tmp_path / "loop.fastdispkt"
    packets = [make_entity_state_packet(EntityStateSpec(site=300, application=4, entity=11, force_id=1))]
    write_v1_packets(replay_path, packets)

    monkeypatch.setattr(
        "sys.argv",
        [
            "lattice_shim",
            "shim-to-dis",
            str(replay_path),
            "--out-dir",
            str(tmp_path / "loop_out"),
        ],
    )

    rc = lattice_shim_main()

    assert rc == 0
    report = json.loads((tmp_path / "loop_out" / "shim_to_dis_report.json").read_text(encoding="utf-8"))
    assert report["packet_count"] == 0
    assert report["exportable_entity_count"] == 0
    assert report["suppressed_entity_count"] == 1
    assert report["suppressed"][0]["reason"] == "packet-stoat.dis_ingress"


def test_lab_state_writes_object_and_task_reports(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        "sys.argv",
        [
            "lattice_shim",
            "lab-state",
            "--object-fixture",
            str(OBJECT_FIXTURE),
            "--task-fixture",
            str(TASK_FIXTURE),
            "--out-dir",
            str(tmp_path),
        ],
    )

    rc = lattice_shim_main()

    assert rc == 0
    report = json.loads((tmp_path / "lab_state_report.json").read_text(encoding="utf-8"))
    tasks = json.loads((tmp_path / "tasks.json").read_text(encoding="utf-8"))
    objects = json.loads((tmp_path / "objects.json").read_text(encoding="utf-8"))
    task_events = json.loads((tmp_path / "task_events.json").read_text(encoding="utf-8"))
    assert report["object_count"] == 2
    assert report["task_count"] == 2
    assert report["task_event_count"] == 2
    assert objects[0]["path"].startswith("reports/alpha4/")
    assert tasks[0]["task_id"].startswith("task-alpha4-")
    assert task_events[0]["kind"] == "TaskExecute"
