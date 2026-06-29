"""FastDIS-local adapter scaffold checks.

These tests validate deterministic shim state and helper behavior. They do not
stand in for external Zorn or real Lattice backend proof.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from fastdis import parse_header


ROOT = Path(__file__).resolve().parents[1]
ADAPTER_SRC = ROOT / "packages" / "lattice" / "src"
if str(ADAPTER_SRC) not in sys.path:
    sys.path.insert(0, str(ADAPTER_SRC))

from packet_stoat_lattice import (  # noqa: E402
    HttpMockPublisher,
    JsonlPublisher,
    MockLatticeShim,
    build_publish_report,
    canonical_entity_from_fixture,
    entity_is_exportable_to_dis,
    entity_state_packet_from_fixture,
    entity_state_packet_from_track_payload,
    lattice_track_payload_from_entity,
    loop_suppression_reason,
    map_force_disposition,
    map_platform_kind,
    publish_fixture,
)


FIXTURE = ROOT / "packages" / "lattice" / "examples" / "dis_entity_fixture.json"


FIXTURE_DIR = ROOT / "packages" / "lattice" / "examples"
DIS_FIXTURE = FIXTURE_DIR / "dis_entity_fixture.json"
TRACK_FIXTURE = FIXTURE_DIR / "lattice_track_fixture.json"


def test_adapter_fixture_can_publish_through_http_mock() -> None:
    publisher = HttpMockPublisher()
    report = publish_fixture(DIS_FIXTURE, publisher)

    assert report["attempted"] == 1
    assert report["accepted"] == 1
    assert publisher.payloads[0]["track"]["platform_kind"] == "aircraft"
    assert publisher.payloads[0]["track"]["disposition"] == "friendly"


def test_adapter_jsonl_publisher_writes_payloads(tmp_path: Path) -> None:
    entities = canonical_entity_from_fixture(DIS_FIXTURE)
    publisher = JsonlPublisher(tmp_path / "publish.jsonl")

    report = build_publish_report(entities, publisher)

    assert report["accepted"] == 1
    lines = (tmp_path / "publish.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    payload = json.loads(lines[0])
    assert payload["entity_key"] == "100:1:42"


def test_adapter_track_payload_can_egress_back_to_dis() -> None:
    payload = json.loads(TRACK_FIXTURE.read_text(encoding="utf-8"))

    packet = entity_state_packet_from_track_payload(payload)
    header = parse_header(packet, strict=True)

    assert header is not None
    assert header.pdu_type == 1
    assert header.length == len(packet)


def test_adapter_dis_fixture_can_egress_to_dis_packet() -> None:
    packet = entity_state_packet_from_fixture(DIS_FIXTURE)
    header = parse_header(packet, strict=True)

    assert header is not None
    assert header.version == 7
    assert header.pdu_type == 1


def test_adapter_mapping_helpers_are_stable() -> None:
    entity = canonical_entity_from_fixture(DIS_FIXTURE)[0]
    payload = lattice_track_payload_from_entity(entity)

    assert map_force_disposition(1) == "friendly"
    assert map_platform_kind(entity) == "aircraft"
    assert payload["track"]["platform_kind"] == "aircraft"
    assert payload["packetStoat"]["deadReckoning"]["algorithm"] == 4
    assert payload["packetStoat"]["deadReckoning"]["algorithm_name"] == "DRM_RVW"


def test_mock_shim_keeps_latest_state_and_emits_stream_events() -> None:
    shim = MockLatticeShim()
    payload = lattice_track_payload_from_entity(canonical_entity_from_fixture(DIS_FIXTURE)[0])

    result = shim.publish_entity(payload)

    assert result["status"] == "accepted"
    assert shim.metrics()["entity_count"] == 1
    events = shim.stream_entities(components_to_include=["location", "provenance"], heartbeat_interval_ms=500)
    assert events[0]["kind"] == "EntityEvent"
    assert "pose" in events[0]["payload"]
    assert "provenance" in events[0]["payload"]
    assert events[-1]["kind"] == "Heartbeat"
    assert events[-1]["heartbeat_interval_ms"] == 500


def test_mock_shim_can_filter_preexisting_entities() -> None:
    shim = MockLatticeShim()
    payload = lattice_track_payload_from_entity(canonical_entity_from_fixture(DIS_FIXTURE)[0])
    shim.publish_entity(payload)

    events = shim.stream_entities(pre_existing_only=True, include_heartbeat=False)

    assert len(events) == 1
    assert events[0]["entityId"] == payload["entityId"]


def test_mock_shim_object_store_and_task_mailbox_work(tmp_path: Path) -> None:
    shim = MockLatticeShim()

    object_result = shim.put_object("reports/track.json", "application/json", b'{"ok":true}')
    task_result = shim.create_task({"task_id": "task-1", "agent_id": "packet-stoat", "task_type": "GenerateTrackReport"})
    status_result = shim.update_task_status("task-1", "completed")
    log_path = tmp_path / "events.jsonl"
    shim.write_event_log_jsonl(log_path)

    assert object_result["status"] == "accepted"
    assert shim.get_object("reports/track.json") == b'{"ok":true}'
    assert shim.list_objects("reports/")[0]["path"] == "reports/track.json"
    assert task_result["status"] == "accepted"
    assert shim.stream_tasks("packet-stoat")[0]["task_type"] == "GenerateTrackReport"
    assert status_result["task_status"] == "completed"
    assert log_path.is_file()
    assert "ObjectPut" in log_path.read_text(encoding="utf-8")


def test_mock_shim_suppresses_dis_originated_entities_on_export() -> None:
    shim = MockLatticeShim()
    entity = canonical_entity_from_fixture(DIS_FIXTURE)[0]
    dis_payload = lattice_track_payload_from_entity(entity)
    dis_payload["source"] = "dis-ingress"
    dis_payload["packetStoat"]["source"] = "dis-ingress"
    mock_payload = json.loads(TRACK_FIXTURE.read_text(encoding="utf-8"))
    shim.publish_entity(dis_payload)
    shim.publish_entity(mock_payload)

    exportable = shim.exportable_entities_for_dis()

    assert entity_is_exportable_to_dis(dis_payload) is False
    assert entity_is_exportable_to_dis(mock_payload) is True
    assert len(exportable) == 1
    assert exportable[0]["entity_key"] == "100:1:42"
def test_mock_shim_objects_tasks_and_loop_report() -> None:
    entity = canonical_entity_from_fixture(FIXTURE)[0]
    shim = MockLatticeShim()
    payload = lattice_track_payload_from_entity(entity)

    accepted = shim.publish_entity(payload)
    shim.put_object("reports/track.json", "application/json", b"{}")
    shim.create_task({"task_id": "task-1", "agent_id": "packet-stoat", "task_type": "emit"})
    shim.update_task_status("task-1", "running")

    assert accepted["status"] == "accepted"
    assert shim.metrics()["object_count"] == 1
    assert shim.metrics()["task_count"] == 1
    assert shim.list_tasks()[0]["status"] == "running"
    export_report = shim.export_report_for_dis()
    assert export_report["exportable_count"] == 1
    assert export_report["suppressed_count"] == 0


def test_loop_suppression_reason_marks_dis_ingress_payloads() -> None:
    entity = canonical_entity_from_fixture(FIXTURE)[0]
    shim_payload = lattice_track_payload_from_entity(entity)
    shim_payload["packetStoat"] = {"source": "dis-ingress"}

    assert entity_is_exportable_to_dis(shim_payload) is False
    assert loop_suppression_reason(shim_payload) == "packet-stoat.dis_ingress"
