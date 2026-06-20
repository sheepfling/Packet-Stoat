from __future__ import annotations

import json
from pathlib import Path

from fastdis import parse_header
from fastdis.lattice import (
    MockLatticePublisher,
    MockPublishConfig,
    canonical_entity_to_entity_state_packet,
    canonical_entity_to_lattice_payload,
    load_canonical_entities,
)
from fastdis.tools.lattice_publish import main as lattice_publish_main


FIXTURE = Path(__file__).resolve().parent / "data" / "lattice_mock_entities.json"


def test_mock_lattice_publisher_accepts_and_records_payloads() -> None:
    entities = load_canonical_entities(FIXTURE)
    publisher = MockLatticePublisher()
    report = publisher.publish(entities)

    assert report.attempted == 2
    assert report.accepted == 2
    assert report.rejected == 0
    assert report.failed == 0
    assert report.timed_out is False
    assert len(publisher.published_payloads) == 2
    assert publisher.published_payloads[0]["entity_key"] == "100:1:42"
    assert publisher.published_payloads[1]["pose"]["orientation_dis_deg"]["phi"] == 5.0


def test_mock_lattice_publisher_rejects_configured_entities_and_stale() -> None:
    entities = load_canonical_entities(FIXTURE)
    publisher = MockLatticePublisher(
        MockPublishConfig(
            reject_entity_keys=frozenset({"100:1:42"}),
            reject_stale=True,
        )
    )
    report = publisher.publish(entities)

    assert report.accepted == 0
    assert report.rejected == 2
    assert report.failed == 0
    assert [result.status for result in report.results] == ["rejected", "rejected"]


def test_mock_lattice_publisher_timeout_is_deterministic() -> None:
    entities = load_canonical_entities(FIXTURE)
    publisher = MockLatticePublisher(MockPublishConfig(timeout_after=1))
    report = publisher.publish(entities)

    assert report.accepted == 1
    assert report.failed == 1
    assert report.timed_out is True
    assert report.results[-1].status == "timeout"


def test_canonical_entity_can_egress_to_entity_state_packet() -> None:
    entity = load_canonical_entities(FIXTURE)[0]
    packet = canonical_entity_to_entity_state_packet(entity)
    header = parse_header(packet, strict=True)

    assert header is not None
    assert header.version == 7
    assert header.pdu_type == 1
    assert header.length == len(packet)


def test_lattice_payload_shape_is_stable() -> None:
    entity = load_canonical_entities(FIXTURE)[0]
    payload = canonical_entity_to_lattice_payload(entity)

    assert payload["schema"] == "fastdis.mock-lattice.track.v1"
    assert payload["entityId"].startswith("packet-stoat:dis:v7:")
    assert payload["pose"]["location_ecef_m"] == [1000.0, 2000.0, 3000.0]
    assert payload["provenance"]["integrationName"] == "packet-stoat"
    assert payload["metadata"]["track_id"] == "trk-42"


def test_lattice_publish_cli_writes_report_and_payload_log(tmp_path: Path, monkeypatch) -> None:
    report_path = tmp_path / "report.json"
    payload_path = tmp_path / "payloads.json"
    monkeypatch.setattr(
        "sys.argv",
        [
            "lattice_publish",
            str(FIXTURE),
            "--reject-stale",
            "--report-out",
            str(report_path),
            "--payload-log-out",
            str(payload_path),
        ],
    )

    rc = lattice_publish_main()

    assert rc == 0
    report = json.loads(report_path.read_text(encoding="utf-8"))
    payloads = json.loads(payload_path.read_text(encoding="utf-8"))
    assert report["attempted"] == 2
    assert report["accepted"] == 1
    assert report["rejected"] == 1
    assert payloads[0]["entity_key"] == "100:1:42"
