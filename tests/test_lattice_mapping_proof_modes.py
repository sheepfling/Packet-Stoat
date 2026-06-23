from __future__ import annotations

import json
from pathlib import Path
import sys

import httpx


ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = ROOT / "tools"
ADAPTER_SRC = ROOT / "integrations" / "lattice" / "src"
sys.path.insert(0, str(TOOLS_DIR))
sys.path.insert(0, str(ADAPTER_SRC))

import generate_lattice_dis_mapping_plan as mapping_plan  # noqa: E402
from fastdis import parse_header  # noqa: E402
from packet_stoat_lattice import (  # noqa: E402
    MockLatticeRestHarness,
    MockLatticeShim,
    build_sdk_mock_transport,
    canonical_entity_from_fixture,
    entity_state_packet_from_fixture,
    lattice_track_payload_from_entity,
)


FIXTURE_DIR = ROOT / "integrations" / "lattice" / "examples"
DIS_FIXTURE = FIXTURE_DIR / "dis_entity_fixture.json"
TRACK_FIXTURE = FIXTURE_DIR / "lattice_track_fixture.json"
OBJECT_FIXTURE = FIXTURE_DIR / "object_fixture.json"
TASK_FIXTURE = FIXTURE_DIR / "task_fixture.json"
TASK_CONTROL_FIXTURE = FIXTURE_DIR / "lattice_task_control_fixture.json"
TASK_START_FIXTURE = FIXTURE_DIR / "lattice_task_start_fixture.json"
TASK_FREEZE_FIXTURE = FIXTURE_DIR / "lattice_task_freeze_fixture.json"
TASK_ACK_FIXTURE = FIXTURE_DIR / "lattice_task_ack_fixture.json"
TASK_ACTION_REQUEST_FIXTURE = FIXTURE_DIR / "lattice_task_action_request_fixture.json"
TASK_ACTION_RESPONSE_FIXTURE = FIXTURE_DIR / "lattice_task_action_response_fixture.json"
TASK_SET_DATA_FIXTURE = FIXTURE_DIR / "lattice_task_set_data_fixture.json"
TASK_DATA_PAYLOAD_FIXTURE = FIXTURE_DIR / "lattice_task_data_payload_fixture.json"
TASK_DATA_QUERY_FIXTURE = FIXTURE_DIR / "lattice_task_data_query_fixture.json"
TASK_COMMENT_FIXTURE = FIXTURE_DIR / "lattice_task_comment_fixture.json"
TASK_RECORD_R_FIXTURE = FIXTURE_DIR / "lattice_task_record_r_fixture.json"
TASK_SET_RECORD_FIXTURE = FIXTURE_DIR / "lattice_task_set_record_fixture.json"
TASK_RECORD_QUERY_FIXTURE = FIXTURE_DIR / "lattice_task_record_query_fixture.json"
TASK_LOGISTICS_FIXTURE = FIXTURE_DIR / "lattice_task_logistics_fixture.json"
TASK_SERVICE_FIXTURE = FIXTURE_DIR / "lattice_task_service_fixture.json"
TASK_RESUPPLY_OFFER_FIXTURE = FIXTURE_DIR / "lattice_task_resupply_offer_fixture.json"
TASK_RESUPPLY_RECEIVED_FIXTURE = FIXTURE_DIR / "lattice_task_resupply_received_fixture.json"
TASK_RESUPPLY_CANCEL_FIXTURE = FIXTURE_DIR / "lattice_task_resupply_cancel_fixture.json"
TASK_REPAIR_COMPLETE_FIXTURE = FIXTURE_DIR / "lattice_task_repair_complete_fixture.json"
TASK_REPAIR_RESPONSE_FIXTURE = FIXTURE_DIR / "lattice_task_repair_response_fixture.json"
SIGNAL_FIXTURE = FIXTURE_DIR / "lattice_signal_fixture.json"
SENSOR_FIXTURE = FIXTURE_DIR / "lattice_sensor_fixture.json"
EM_OBSERVATION_FIXTURE = FIXTURE_DIR / "lattice_em_observation_fixture.json"
DESIGNATOR_FIXTURE = FIXTURE_DIR / "lattice_designator_fixture.json"
TRANSMITTER_FIXTURE = FIXTURE_DIR / "lattice_transmitter_fixture.json"
RECEIVER_FIXTURE = FIXTURE_DIR / "lattice_receiver_fixture.json"
ANNOTATION_FIXTURE = FIXTURE_DIR / "lattice_annotation_fixture.json"
INTERCOM_SIGNAL_FIXTURE = FIXTURE_DIR / "lattice_intercom_signal_fixture.json"
INTERCOM_CONTROL_FIXTURE = FIXTURE_DIR / "lattice_intercom_control_fixture.json"
UNDERWATER_SIGNAL_FIXTURE = FIXTURE_DIR / "lattice_underwater_signal_fixture.json"
EMISSION_FIXTURE = FIXTURE_DIR / "lattice_emission_fixture.json"
GEO_FIXTURE = FIXTURE_DIR / "lattice_geo_fixture.json"
GEO_GRID_FIXTURE = FIXTURE_DIR / "lattice_geo_grid_fixture.json"
GEO_POINT_FIXTURE = FIXTURE_DIR / "lattice_geo_point_fixture.json"
GEO_LINE_FIXTURE = FIXTURE_DIR / "lattice_geo_line_fixture.json"
GEO_AREAL_FIXTURE = FIXTURE_DIR / "lattice_geo_areal_fixture.json"
GEO_MINEFIELD_QUERY_FIXTURE = FIXTURE_DIR / "lattice_geo_minefield_query_fixture.json"
GEO_MINEFIELD_DATA_FIXTURE = FIXTURE_DIR / "lattice_geo_minefield_data_fixture.json"
GEO_MINEFIELD_NACK_FIXTURE = FIXTURE_DIR / "lattice_geo_minefield_nack_fixture.json"
GEO_ENV_PROCESS_FIXTURE = FIXTURE_DIR / "lattice_geo_environment_process_fixture.json"
TSPI_FIXTURE = FIXTURE_DIR / "lattice_tspi_fixture.json"
APPEARANCE_FIXTURE = FIXTURE_DIR / "lattice_appearance_fixture.json"
ARTICULATED_FIXTURE = FIXTURE_DIR / "lattice_articulated_parts_fixture.json"
CREATE_ENTITY_FIXTURE = FIXTURE_DIR / "lattice_create_entity_fixture.json"
REMOVE_ENTITY_FIXTURE = FIXTURE_DIR / "lattice_remove_entity_fixture.json"
ENTITY_STATE_UPDATE_FIXTURE = FIXTURE_DIR / "lattice_entity_state_update_fixture.json"
RELATIONSHIP_FIXTURE = FIXTURE_DIR / "lattice_relationship_fixture.json"
AGGREGATE_STATE_FIXTURE = FIXTURE_DIR / "lattice_aggregate_state_fixture.json"
IS_GROUP_OF_FIXTURE = FIXTURE_DIR / "lattice_is_group_of_fixture.json"
IS_PART_OF_FIXTURE = FIXTURE_DIR / "lattice_is_part_of_fixture.json"
RELATIONSHIP_OWNERSHIP_FIXTURE = FIXTURE_DIR / "lattice_relationship_ownership_fixture.json"
EVENT_TASK_FIXTURE = FIXTURE_DIR / "lattice_event_task_fixture.json"
EVENT_FIRE_FIXTURE = FIXTURE_DIR / "lattice_event_fire_fixture.json"
EVENT_LE_FIRE_FIXTURE = FIXTURE_DIR / "lattice_event_le_fire_fixture.json"
EVENT_DIRECTED_ENERGY_FIRE_FIXTURE = FIXTURE_DIR / "lattice_event_directed_energy_fire_fixture.json"
EVENT_DETONATION_FIXTURE = FIXTURE_DIR / "lattice_event_detonation_fixture.json"
EVENT_LE_DETONATION_FIXTURE = FIXTURE_DIR / "lattice_event_le_detonation_fixture.json"
EVENT_COLLISION_FIXTURE = FIXTURE_DIR / "lattice_event_collision_fixture.json"
EVENT_COLLISION_ELASTIC_FIXTURE = FIXTURE_DIR / "lattice_event_collision_elastic_fixture.json"
ENTITY_DAMAGE_FIXTURE = FIXTURE_DIR / "lattice_entity_damage_fixture.json"
INFO_OPS_ACTION_FIXTURE = FIXTURE_DIR / "lattice_info_ops_action_fixture.json"
INFO_OPS_REPORT_FIXTURE = FIXTURE_DIR / "lattice_info_ops_report_fixture.json"
ATTRIBUTE_FIXTURE = FIXTURE_DIR / "lattice_attribute_fixture.json"
TASK_EVENT_REPORT_FIXTURE = FIXTURE_DIR / "lattice_task_event_report_fixture.json"
TASK_ENTITY_RELIABLE_FIXTURE = FIXTURE_DIR / "lattice_task_entity_reliable_fixture.json"


def _headers() -> dict[str, str]:
    return {
        "Authorization": "Bearer mock-environment-token",
        "Anduril-Sandbox-Authorization": "Bearer mock-sandbox-token",
    }


def _row(version: int, pdu_type: int) -> dict[str, object]:
    plan = mapping_plan.build_plan()
    return next(row for row in plan["records"] if row["protocol_version"] == version and row["pdu_type"] == pdu_type)


def test_entity_roundtrip_proof_mode_is_runnable() -> None:
    row = _row(7, 1)

    assert "entity_roundtrip" in row["proof_modes"]
    packet = entity_state_packet_from_fixture(TRACK_FIXTURE)
    header = parse_header(packet, strict=True)
    assert header is not None
    assert header[0] == 7
    assert header[2] == 1


def test_entity_publish_get_stream_proof_mode_is_runnable() -> None:
    row = _row(7, 67)

    assert "entity_publish_get_stream" in row["proof_modes"]
    harness = MockLatticeRestHarness()
    transport = build_sdk_mock_transport(harness)
    entity = canonical_entity_from_fixture(DIS_FIXTURE)[0]
    payload = lattice_track_payload_from_entity(entity)

    with httpx.Client(transport=transport, base_url="http://lattice.mock", headers=_headers()) as client:
        published = client.put("/api/v1/entities", json=payload)
        fetched = client.get(f"/api/v1/entities/{payload['entityId']}")
        streamed = client.post("/api/v1/entities/events", json={"afterSequence": 0, "limit": 10})

    assert published.status_code == 200
    assert fetched.status_code == 200
    assert fetched.json()["entityId"] == payload["entityId"]
    assert any(event.get("entityId") == payload["entityId"] for event in streamed.json()["events"])


def test_entity_lifecycle_projection_fixtures_are_runnable() -> None:
    create_row = _row(7, 11)
    remove_row = _row(7, 12)
    update_row = _row(7, 67)
    harness = MockLatticeRestHarness()
    transport = build_sdk_mock_transport(harness)
    create_payload = json.loads(CREATE_ENTITY_FIXTURE.read_text(encoding="utf-8"))
    remove_payload = json.loads(REMOVE_ENTITY_FIXTURE.read_text(encoding="utf-8"))
    update_payload = json.loads(ENTITY_STATE_UPDATE_FIXTURE.read_text(encoding="utf-8"))

    assert "entity_projection_contract" in create_row["proof_modes"]
    assert "entity_projection_contract" in remove_row["proof_modes"]
    assert "entity_projection_contract" in update_row["proof_modes"]

    with httpx.Client(transport=transport, base_url="http://lattice.mock", headers=_headers()) as client:
        client.put("/api/v1/entities", json=create_payload)
        client.put("/api/v1/entities", json=remove_payload)
        client.put("/api/v1/entities", json=update_payload)
        create_fetched = client.get(f"/api/v1/entities/{create_payload['entityId']}")
        remove_fetched = client.get(f"/api/v1/entities/{remove_payload['entityId']}")
        update_fetched = client.get(f"/api/v1/entities/{update_payload['entityId']}")

    assert create_fetched.json()["packetStoat"]["projectionKind"] == "entity_create_projection"
    assert remove_fetched.json()["packetStoat"]["projectionKind"] == "entity_remove_projection"
    assert update_fetched.json()["packetStoat"]["projectionKind"] == "entity_state_update_projection"


def test_task_fixture_and_stream_proof_modes_are_runnable() -> None:
    row = _row(6, 13)
    shim = MockLatticeShim()
    task_rows = json.loads(TASK_FIXTURE.read_text(encoding="utf-8"))["tasks"]

    assert "task_fixture_contract" in row["proof_modes"]
    assert "task_stream_contract" in row["proof_modes"]
    created = [shim.create_task(task) for task in task_rows]
    streamed = shim.stream_tasks()

    assert len(created) == len(task_rows)
    assert len(streamed) == len(task_rows)
    assert streamed[0]["kind"] == "TaskExecute"


def test_raw_sidecar_and_object_fixture_proof_modes_are_runnable() -> None:
    row = _row(6, 0)
    harness = MockLatticeRestHarness()
    transport = build_sdk_mock_transport(harness)
    raw_packet = entity_state_packet_from_fixture(DIS_FIXTURE)
    object_rows = json.loads(OBJECT_FIXTURE.read_text(encoding="utf-8"))["objects"]
    object_path = object_rows[0]["path"]

    assert "object_fixture_contract" in row["proof_modes"]
    assert "raw_sidecar_preservation" in row["proof_modes"]

    with httpx.Client(transport=transport, base_url="http://lattice.mock", headers=_headers()) as client:
        uploaded = client.post(
            f"/api/v1/objects/{object_path}",
            content=raw_packet,
            headers={"content-type": "application/octet-stream", **_headers()},
        )
        downloaded = client.get(f"/api/v1/objects/{object_path}")

    assert uploaded.status_code == 200
    assert downloaded.status_code == 200
    assert downloaded.content == raw_packet


def test_signal_projection_fixture_is_runnable() -> None:
    row = _row(7, 26)
    harness = MockLatticeRestHarness()
    transport = build_sdk_mock_transport(harness)
    payload = json.loads(SIGNAL_FIXTURE.read_text(encoding="utf-8"))

    assert "entity_projection_contract" in row["proof_modes"]
    assert "raw_sidecar_preservation" in row["proof_modes"]

    with httpx.Client(transport=transport, base_url="http://lattice.mock", headers=_headers()) as client:
        published = client.put("/api/v1/entities", json=payload)
        fetched = client.get(f"/api/v1/entities/{payload['entityId']}")

    assert published.status_code == 200
    assert fetched.status_code == 200
    assert fetched.json()["signal"]["emitterNotation"] == "RADAR-X"
    assert fetched.json()["packetStoat"]["projectionKind"] == "signal_of_interest_entity"


def test_sensor_and_annotation_projection_fixtures_are_runnable() -> None:
    sensor_row = _row(7, 24)
    annotation_row = _row(7, 28)
    harness = MockLatticeRestHarness()
    transport = build_sdk_mock_transport(harness)
    sensor_payload = json.loads(SENSOR_FIXTURE.read_text(encoding="utf-8"))
    annotation_payload = json.loads(ANNOTATION_FIXTURE.read_text(encoding="utf-8"))

    assert "entity_projection_contract" in sensor_row["proof_modes"]
    assert "entity_projection_contract" in annotation_row["proof_modes"]

    with httpx.Client(transport=transport, base_url="http://lattice.mock", headers=_headers()) as client:
        sensor_published = client.put("/api/v1/entities", json=sensor_payload)
        annotation_published = client.put("/api/v1/entities", json=annotation_payload)
        sensor_fetched = client.get(f"/api/v1/entities/{sensor_payload['entityId']}")
        annotation_fetched = client.get(f"/api/v1/entities/{annotation_payload['entityId']}")

    assert sensor_published.status_code == 200
    assert annotation_published.status_code == 200
    assert sensor_fetched.json()["packetStoat"]["projectionKind"] == "sensor_point_of_interest_entity"
    assert annotation_fetched.json()["packetStoat"]["projectionKind"] == "entity_signal_annotation"


def test_emission_and_designator_projection_fixtures_are_runnable() -> None:
    emission_row = _row(7, 23)
    designator_row = _row(7, 24)
    harness = MockLatticeRestHarness()
    transport = build_sdk_mock_transport(harness)
    emission_payload = json.loads(EM_OBSERVATION_FIXTURE.read_text(encoding="utf-8"))
    designator_payload = json.loads(DESIGNATOR_FIXTURE.read_text(encoding="utf-8"))

    assert "entity_projection_contract" in emission_row["proof_modes"]
    assert "entity_projection_contract" in designator_row["proof_modes"]

    with httpx.Client(transport=transport, base_url="http://lattice.mock", headers=_headers()) as client:
        em_published = client.put("/api/v1/entities", json=emission_payload)
        des_published = client.put("/api/v1/entities", json=designator_payload)
        em_fetched = client.get(f"/api/v1/entities/{emission_payload['entityId']}")
        des_fetched = client.get(f"/api/v1/entities/{designator_payload['entityId']}")

    assert em_published.status_code == 200
    assert des_published.status_code == 200
    assert em_fetched.json()["packetStoat"]["projectionKind"] == "emission_sensor_entity"
    assert des_fetched.json()["packetStoat"]["projectionKind"] == "designator_entity"


def test_transmitter_and_receiver_projection_fixtures_are_runnable() -> None:
    transmitter_row = _row(7, 25)
    receiver_row = _row(7, 27)
    harness = MockLatticeRestHarness()
    transport = build_sdk_mock_transport(harness)
    transmitter_payload = json.loads(TRANSMITTER_FIXTURE.read_text(encoding="utf-8"))
    receiver_payload = json.loads(RECEIVER_FIXTURE.read_text(encoding="utf-8"))

    assert "entity_projection_contract" in transmitter_row["proof_modes"]
    assert "entity_projection_contract" in receiver_row["proof_modes"]

    with httpx.Client(transport=transport, base_url="http://lattice.mock", headers=_headers()) as client:
        tx_published = client.put("/api/v1/entities", json=transmitter_payload)
        rx_published = client.put("/api/v1/entities", json=receiver_payload)
        tx_fetched = client.get(f"/api/v1/entities/{transmitter_payload['entityId']}")
        rx_fetched = client.get(f"/api/v1/entities/{receiver_payload['entityId']}")

    assert tx_published.status_code == 200
    assert rx_published.status_code == 200
    assert tx_fetched.json()["packetStoat"]["projectionKind"] == "transmitter_entity"
    assert rx_fetched.json()["packetStoat"]["projectionKind"] == "receiver_entity"


def test_intercom_signal_and_control_projection_fixtures_are_runnable() -> None:
    signal_row = _row(7, 31)
    control_row = _row(7, 32)
    harness = MockLatticeRestHarness()
    transport = build_sdk_mock_transport(harness)
    signal_payload = json.loads(INTERCOM_SIGNAL_FIXTURE.read_text(encoding="utf-8"))
    control_payload = json.loads(INTERCOM_CONTROL_FIXTURE.read_text(encoding="utf-8"))

    assert "entity_projection_contract" in signal_row["proof_modes"]
    assert "entity_projection_contract" in control_row["proof_modes"]

    with httpx.Client(transport=transport, base_url="http://lattice.mock", headers=_headers()) as client:
        sig_published = client.put("/api/v1/entities", json=signal_payload)
        ctl_published = client.put("/api/v1/entities", json=control_payload)
        sig_fetched = client.get(f"/api/v1/entities/{signal_payload['entityId']}")
        ctl_fetched = client.get(f"/api/v1/entities/{control_payload['entityId']}")

    assert sig_published.status_code == 200
    assert ctl_published.status_code == 200
    assert sig_fetched.json()["packetStoat"]["projectionKind"] == "intercom_signal_annotation"
    assert ctl_fetched.json()["packetStoat"]["projectionKind"] == "intercom_control_annotation"


def test_underwater_and_emission_projection_fixtures_are_runnable() -> None:
    underwater_row = _row(7, 29)
    emission_row = _row(7, 30)
    harness = MockLatticeRestHarness()
    transport = build_sdk_mock_transport(harness)
    underwater_payload = json.loads(UNDERWATER_SIGNAL_FIXTURE.read_text(encoding="utf-8"))
    emission_payload = json.loads(EMISSION_FIXTURE.read_text(encoding="utf-8"))

    assert "entity_projection_contract" in underwater_row["proof_modes"]
    assert "entity_projection_contract" in emission_row["proof_modes"]

    with httpx.Client(transport=transport, base_url="http://lattice.mock", headers=_headers()) as client:
        underwater_published = client.put("/api/v1/entities", json=underwater_payload)
        emission_published = client.put("/api/v1/entities", json=emission_payload)
        underwater_fetched = client.get(f"/api/v1/entities/{underwater_payload['entityId']}")
        emission_fetched = client.get(f"/api/v1/entities/{emission_payload['entityId']}")

    assert underwater_published.status_code == 200
    assert emission_published.status_code == 200
    assert underwater_fetched.json()["packetStoat"]["projectionKind"] == "signal_of_interest_entity"
    assert emission_fetched.json()["packetStoat"]["projectionKind"] == "sensor_point_of_interest_entity"


def test_geo_and_hazard_projection_fixtures_are_runnable() -> None:
    row = _row(7, 37)
    harness = MockLatticeRestHarness()
    transport = build_sdk_mock_transport(harness)
    payload = json.loads(GEO_FIXTURE.read_text(encoding="utf-8"))
    object_rows = json.loads(OBJECT_FIXTURE.read_text(encoding="utf-8"))["objects"]
    object_path = object_rows[0]["path"]

    assert "entity_projection_contract" in row["proof_modes"]
    assert "object_fixture_contract" in row["proof_modes"]

    with httpx.Client(transport=transport, base_url="http://lattice.mock", headers=_headers()) as client:
        uploaded = client.put("/api/v1/entities", json=payload)
        sidecar = client.post(
            f"/api/v1/objects/{object_path}",
            content=b'{\"hazard\":\"minefield\"}',
            headers={"content-type": "application/json", **_headers()},
        )
        linked = harness.link_object_to_entity_media(
            payload["entityId"],
            object_path,
            headers=_headers(),
            label="hazard-sidecar",
        )
        fetched = client.get(f"/api/v1/entities/{payload['entityId']}")

    assert uploaded.status_code == 200
    assert sidecar.status_code == 200
    assert linked["status"] == "accepted"
    assert fetched.status_code == 200
    assert fetched.json()["geoDetails"]["type"] == "GEO_TYPE_CONTROL_AREA"
    assert fetched.json()["media"]["items"][0]["relativePath"] == object_path


def test_geo_point_and_line_projection_fixtures_are_runnable() -> None:
    point_row = _row(7, 43)
    line_row = _row(7, 44)
    harness = MockLatticeRestHarness()
    transport = build_sdk_mock_transport(harness)
    point_payload = json.loads(GEO_POINT_FIXTURE.read_text(encoding="utf-8"))
    line_payload = json.loads(GEO_LINE_FIXTURE.read_text(encoding="utf-8"))

    assert "entity_projection_contract" in point_row["proof_modes"]
    assert "entity_projection_contract" in line_row["proof_modes"]

    with httpx.Client(transport=transport, base_url="http://lattice.mock", headers=_headers()) as client:
        point_published = client.put("/api/v1/entities", json=point_payload)
        line_published = client.put("/api/v1/entities", json=line_payload)
        point_fetched = client.get(f"/api/v1/entities/{point_payload['entityId']}")
        line_fetched = client.get(f"/api/v1/entities/{line_payload['entityId']}")

    assert point_published.status_code == 200
    assert line_published.status_code == 200
    assert point_fetched.json()["packetStoat"]["projectionKind"] == "geo_entity_point"
    assert line_fetched.json()["packetStoat"]["projectionKind"] == "geo_entity_line"


def test_geo_grid_and_areal_projection_fixtures_are_runnable() -> None:
    grid_row = _row(7, 42)
    areal_row = _row(7, 45)
    harness = MockLatticeRestHarness()
    transport = build_sdk_mock_transport(harness)
    grid_payload = json.loads(GEO_GRID_FIXTURE.read_text(encoding="utf-8"))
    areal_payload = json.loads(GEO_AREAL_FIXTURE.read_text(encoding="utf-8"))

    assert "entity_projection_contract" in grid_row["proof_modes"]
    assert "entity_projection_contract" in areal_row["proof_modes"]

    with httpx.Client(transport=transport, base_url="http://lattice.mock", headers=_headers()) as client:
        grid_published = client.put("/api/v1/entities", json=grid_payload)
        areal_published = client.put("/api/v1/entities", json=areal_payload)
        grid_fetched = client.get(f"/api/v1/entities/{grid_payload['entityId']}")
        areal_fetched = client.get(f"/api/v1/entities/{areal_payload['entityId']}")

    assert grid_published.status_code == 200
    assert areal_published.status_code == 200
    assert grid_fetched.json()["packetStoat"]["projectionKind"] == "geo_grid_overlay"
    assert areal_fetched.json()["packetStoat"]["projectionKind"] == "geo_entity_polygon"


def test_environment_process_and_minefield_query_projection_fixtures_are_runnable() -> None:
    env_row = _row(7, 41)
    minefield_row = _row(7, 38)
    harness = MockLatticeRestHarness()
    transport = build_sdk_mock_transport(harness)
    env_payload = json.loads(GEO_ENV_PROCESS_FIXTURE.read_text(encoding="utf-8"))
    minefield_payload = json.loads(GEO_MINEFIELD_QUERY_FIXTURE.read_text(encoding="utf-8"))

    assert "entity_projection_contract" in env_row["proof_modes"]
    assert "entity_projection_contract" in minefield_row["proof_modes"]

    with httpx.Client(transport=transport, base_url="http://lattice.mock", headers=_headers()) as client:
        env_published = client.put("/api/v1/entities", json=env_payload)
        minefield_published = client.put("/api/v1/entities", json=minefield_payload)
        env_fetched = client.get(f"/api/v1/entities/{env_payload['entityId']}")
        minefield_fetched = client.get(f"/api/v1/entities/{minefield_payload['entityId']}")

    assert env_published.status_code == 200
    assert minefield_published.status_code == 200
    assert env_fetched.json()["packetStoat"]["projectionKind"] == "geo_entity_region"
    assert minefield_fetched.json()["packetStoat"]["projectionKind"] == "geo_minefield_query_overlay"


def test_minefield_data_and_nack_projection_fixtures_are_runnable() -> None:
    data_row = _row(7, 39)
    nack_row = _row(7, 40)
    harness = MockLatticeRestHarness()
    transport = build_sdk_mock_transport(harness)
    data_payload = json.loads(GEO_MINEFIELD_DATA_FIXTURE.read_text(encoding="utf-8"))
    nack_payload = json.loads(GEO_MINEFIELD_NACK_FIXTURE.read_text(encoding="utf-8"))

    assert "entity_projection_contract" in data_row["proof_modes"]
    assert "entity_projection_contract" in nack_row["proof_modes"]

    with httpx.Client(transport=transport, base_url="http://lattice.mock", headers=_headers()) as client:
        data_published = client.put("/api/v1/entities", json=data_payload)
        nack_published = client.put("/api/v1/entities", json=nack_payload)
        data_fetched = client.get(f"/api/v1/entities/{data_payload['entityId']}")
        nack_fetched = client.get(f"/api/v1/entities/{nack_payload['entityId']}")

    assert data_published.status_code == 200
    assert nack_published.status_code == 200
    assert data_fetched.json()["packetStoat"]["projectionKind"] == "geo_minefield_data_overlay"
    assert nack_fetched.json()["packetStoat"]["projectionKind"] == "geo_minefield_response_nack"


def test_relationship_projection_fixture_is_runnable() -> None:
    row = _row(7, 33)
    harness = MockLatticeRestHarness()
    transport = build_sdk_mock_transport(harness)
    payload = json.loads(RELATIONSHIP_FIXTURE.read_text(encoding="utf-8"))

    assert "entity_projection_contract" in row["proof_modes"]

    with httpx.Client(transport=transport, base_url="http://lattice.mock", headers=_headers()) as client:
        published = client.put("/api/v1/entities", json=payload)
        fetched = client.get(f"/api/v1/entities/{payload['entityId']}")

    assert published.status_code == 200
    assert fetched.status_code == 200
    assert fetched.json()["packetStoat"]["relationships"][0]["relationshipType"] == "IsGroupOf"


def test_aggregate_group_and_part_relationship_projection_fixtures_are_runnable() -> None:
    aggregate_row = _row(7, 33)
    group_row = _row(7, 34)
    part_row = _row(7, 36)
    harness = MockLatticeRestHarness()
    transport = build_sdk_mock_transport(harness)
    aggregate_payload = json.loads(AGGREGATE_STATE_FIXTURE.read_text(encoding="utf-8"))
    group_payload = json.loads(IS_GROUP_OF_FIXTURE.read_text(encoding="utf-8"))
    part_payload = json.loads(IS_PART_OF_FIXTURE.read_text(encoding="utf-8"))

    assert "entity_projection_contract" in aggregate_row["proof_modes"]
    assert "entity_projection_contract" in group_row["proof_modes"]
    assert "entity_projection_contract" in part_row["proof_modes"]

    with httpx.Client(transport=transport, base_url="http://lattice.mock", headers=_headers()) as client:
        client.put("/api/v1/entities", json=aggregate_payload)
        client.put("/api/v1/entities", json=group_payload)
        client.put("/api/v1/entities", json=part_payload)
        aggregate_fetched = client.get(f"/api/v1/entities/{aggregate_payload['entityId']}")
        group_fetched = client.get(f"/api/v1/entities/{group_payload['entityId']}")
        part_fetched = client.get(f"/api/v1/entities/{part_payload['entityId']}")

    assert aggregate_fetched.json()["packetStoat"]["projectionKind"] == "entity_aggregate_projection"
    assert group_fetched.json()["packetStoat"]["projectionKind"] == "entity_group_membership_projection"
    assert part_fetched.json()["packetStoat"]["projectionKind"] == "entity_part_relationship_projection"


def test_relationship_ownership_projection_fixture_is_runnable() -> None:
    row = _row(7, 35)
    harness = MockLatticeRestHarness()
    transport = build_sdk_mock_transport(harness)
    payload = json.loads(RELATIONSHIP_OWNERSHIP_FIXTURE.read_text(encoding="utf-8"))

    assert "entity_projection_contract" in row["proof_modes"]

    with httpx.Client(transport=transport, base_url="http://lattice.mock", headers=_headers()) as client:
        published = client.put("/api/v1/entities", json=payload)
        fetched = client.get(f"/api/v1/entities/{payload['entityId']}")

    assert published.status_code == 200
    assert fetched.status_code == 200
    assert fetched.json()["packetStoat"]["relationships"][0]["relationshipType"] == "TransferOwnership"


def test_tspi_appearance_and_articulated_projection_fixtures_are_runnable() -> None:
    tspi_row = _row(7, 46)
    appearance_row = _row(7, 47)
    articulated_row = _row(7, 48)
    harness = MockLatticeRestHarness()
    transport = build_sdk_mock_transport(harness)
    tspi_payload = json.loads(TSPI_FIXTURE.read_text(encoding="utf-8"))
    appearance_payload = json.loads(APPEARANCE_FIXTURE.read_text(encoding="utf-8"))
    articulated_payload = json.loads(ARTICULATED_FIXTURE.read_text(encoding="utf-8"))

    assert "entity_projection_contract" in tspi_row["proof_modes"]
    assert "entity_projection_contract" in appearance_row["proof_modes"]
    assert "entity_projection_contract" in articulated_row["proof_modes"]

    with httpx.Client(transport=transport, base_url="http://lattice.mock", headers=_headers()) as client:
        client.put("/api/v1/entities", json=tspi_payload)
        client.put("/api/v1/entities", json=appearance_payload)
        client.put("/api/v1/entities", json=articulated_payload)
        tspi_fetched = client.get(f"/api/v1/entities/{tspi_payload['entityId']}")
        appearance_fetched = client.get(f"/api/v1/entities/{appearance_payload['entityId']}")
        articulated_fetched = client.get(f"/api/v1/entities/{articulated_payload['entityId']}")

    assert tspi_fetched.json()["packetStoat"]["projectionKind"] == "entity_pose_annotation"
    assert appearance_fetched.json()["packetStoat"]["projectionKind"] == "entity_visual_state_annotation"
    assert articulated_fetched.json()["packetStoat"]["projectionKind"] == "entity_articulation_annotation"


def test_event_task_projection_fixture_is_runnable() -> None:
    row = _row(7, 2)
    shim = MockLatticeShim()
    task_rows = json.loads(EVENT_TASK_FIXTURE.read_text(encoding="utf-8"))["tasks"]

    assert "task_fixture_contract" in row["proof_modes"]
    created = [shim.create_task(task) for task in task_rows]
    streamed = shim.stream_tasks()

    assert len(created) == len(task_rows)
    assert streamed[0]["payload"]["packetStoat"]["projectionKind"] == "task_event_projection"


def test_event_row_specific_task_projection_fixtures_are_runnable() -> None:
    fire_row = _row(7, 2)
    detonation_row = _row(7, 3)
    collision_row = _row(7, 4)
    shim = MockLatticeShim()
    fire_rows = json.loads(EVENT_FIRE_FIXTURE.read_text(encoding="utf-8"))["tasks"]
    detonation_rows = json.loads(EVENT_DETONATION_FIXTURE.read_text(encoding="utf-8"))["tasks"]
    collision_rows = json.loads(EVENT_COLLISION_FIXTURE.read_text(encoding="utf-8"))["tasks"]

    assert "task_fixture_contract" in fire_row["proof_modes"]
    assert "task_fixture_contract" in detonation_row["proof_modes"]
    assert "task_fixture_contract" in collision_row["proof_modes"]

    for task in fire_rows + detonation_rows + collision_rows:
        shim.create_task(task)
    streamed = shim.stream_tasks()
    projection_kinds = {event["payload"]["packetStoat"]["projectionKind"] for event in streamed}
    task_types = {event["task_type"] for event in streamed}

    assert projection_kinds == {"task_event_projection"}
    assert {"simulation-event-fire", "simulation-event-detonation", "simulation-event-collision"} <= task_types


def test_fire_detonation_and_collision_variant_projection_fixtures_are_runnable() -> None:
    le_fire_row = _row(7, 49)
    directed_row = _row(7, 68)
    le_detonation_row = _row(7, 50)
    elastic_row = _row(7, 66)
    shim = MockLatticeShim()
    tasks = (
        json.loads(EVENT_LE_FIRE_FIXTURE.read_text(encoding="utf-8"))["tasks"]
        + json.loads(EVENT_DIRECTED_ENERGY_FIRE_FIXTURE.read_text(encoding="utf-8"))["tasks"]
        + json.loads(EVENT_LE_DETONATION_FIXTURE.read_text(encoding="utf-8"))["tasks"]
        + json.loads(EVENT_COLLISION_ELASTIC_FIXTURE.read_text(encoding="utf-8"))["tasks"]
    )

    assert "task_fixture_contract" in le_fire_row["proof_modes"]
    assert "task_fixture_contract" in directed_row["proof_modes"]
    assert "task_fixture_contract" in le_detonation_row["proof_modes"]
    assert "task_fixture_contract" in elastic_row["proof_modes"]

    for task in tasks:
        shim.create_task(task)
    streamed = shim.stream_tasks()
    by_type = {event["task_type"]: event["payload"]["packetStoat"]["projectionKind"] for event in streamed}

    assert by_type["simulation-event-le-fire"] == "task_le_fire_event"
    assert by_type["simulation-event-directed-energy-fire"] == "task_directed_energy_fire_event"
    assert by_type["simulation-event-le-detonation"] == "task_le_detonation_event"
    assert by_type["simulation-event-collision-elastic"] == "task_collision_elastic_event"


def test_entity_damage_and_info_ops_projection_fixtures_are_runnable() -> None:
    damage_row = _row(7, 69)
    action_row = _row(7, 70)
    report_row = _row(7, 71)
    shim = MockLatticeShim()
    damage_rows = json.loads(ENTITY_DAMAGE_FIXTURE.read_text(encoding="utf-8"))["tasks"]
    action_rows = json.loads(INFO_OPS_ACTION_FIXTURE.read_text(encoding="utf-8"))["tasks"]
    report_rows = json.loads(INFO_OPS_REPORT_FIXTURE.read_text(encoding="utf-8"))["tasks"]

    assert "task_fixture_contract" in damage_row["proof_modes"]
    assert "task_fixture_contract" in action_row["proof_modes"]
    assert "task_fixture_contract" in report_row["proof_modes"]

    for task in damage_rows + action_rows + report_rows:
        shim.create_task(task)
    streamed = shim.stream_tasks()
    by_type = {event["task_type"]: event["payload"]["packetStoat"]["projectionKind"] for event in streamed}

    assert by_type["simulation-event-entity-damage"] == "task_entity_damage_event"
    assert by_type["information-operations-action"] == "task_information_operation_action"
    assert by_type["information-operations-report"] == "task_information_operation_report"


def test_attribute_archive_fixture_is_runnable() -> None:
    row = _row(7, 72)
    harness = MockLatticeRestHarness()
    transport = build_sdk_mock_transport(harness)
    object_rows = json.loads(ATTRIBUTE_FIXTURE.read_text(encoding="utf-8"))["objects"]
    object_path = object_rows[0]["path"]
    object_content = object_rows[0]["content"].encode("utf-8")

    assert "raw_sidecar_preservation" in row["proof_modes"]

    with httpx.Client(transport=transport, base_url="http://lattice.mock", headers=_headers()) as client:
        uploaded = client.post(
            f"/api/v1/objects/{object_path}",
            content=object_content,
            headers={"content-type": object_rows[0]["content_type"], **_headers()},
        )
        downloaded = client.get(f"/api/v1/objects/{object_path}")

    assert uploaded.status_code == 200
    assert downloaded.status_code == 200
    assert downloaded.content == object_content


def test_control_message_and_logistics_task_projection_fixtures_are_runnable() -> None:
    control_row = _row(7, 13)
    message_row = _row(7, 18)
    logistics_row = _row(7, 5)
    shim = MockLatticeShim()
    control_rows = json.loads(TASK_CONTROL_FIXTURE.read_text(encoding="utf-8"))["tasks"]
    message_rows = json.loads(TASK_DATA_QUERY_FIXTURE.read_text(encoding="utf-8"))["tasks"] + json.loads(TASK_COMMENT_FIXTURE.read_text(encoding="utf-8"))["tasks"]
    logistics_rows = json.loads(TASK_SERVICE_FIXTURE.read_text(encoding="utf-8"))["tasks"]

    assert "task_fixture_contract" in control_row["proof_modes"]
    assert "task_fixture_contract" in message_row["proof_modes"]
    assert "task_fixture_contract" in logistics_row["proof_modes"]

    for task in control_rows + message_rows + logistics_rows:
        shim.create_task(task)
    streamed = shim.stream_tasks()
    by_type = {event["task_type"]: event["payload"]["packetStoat"]["projectionKind"] for event in streamed}

    assert by_type["simulation-control-start"] == "task_lifecycle_control"
    assert by_type["simulation-data-query"] == "task_data_query_projection"
    assert by_type["simulation-comment"] == "task_comment_projection"
    assert by_type["logistics-service-request"] == "task_service_action"


def test_ack_action_data_record_and_specialized_logistics_task_projection_fixtures_are_runnable() -> None:
    ack_row = _row(7, 15)
    action_row = _row(7, 16)
    data_row = _row(7, 19)
    record_row = _row(7, 63)
    resupply_row = _row(7, 6)
    repair_row = _row(7, 9)
    shim = MockLatticeShim()
    ack_rows = json.loads((FIXTURE_DIR / "lattice_task_ack_only_fixture.json").read_text(encoding="utf-8"))["tasks"] + json.loads((FIXTURE_DIR / "lattice_task_ack_reliable_fixture.json").read_text(encoding="utf-8"))["tasks"]
    action_rows = json.loads(TASK_ACTION_REQUEST_FIXTURE.read_text(encoding="utf-8"))["tasks"] + json.loads(TASK_ACTION_RESPONSE_FIXTURE.read_text(encoding="utf-8"))["tasks"]
    data_rows = json.loads(TASK_SET_DATA_FIXTURE.read_text(encoding="utf-8"))["tasks"] + json.loads(TASK_DATA_PAYLOAD_FIXTURE.read_text(encoding="utf-8"))["tasks"]
    record_rows = (
        json.loads(TASK_RECORD_R_FIXTURE.read_text(encoding="utf-8"))["tasks"]
        + json.loads(TASK_SET_RECORD_FIXTURE.read_text(encoding="utf-8"))["tasks"]
        + json.loads(TASK_RECORD_QUERY_FIXTURE.read_text(encoding="utf-8"))["tasks"]
    )
    resupply_rows = (
        json.loads(TASK_RESUPPLY_OFFER_FIXTURE.read_text(encoding="utf-8"))["tasks"]
        + json.loads(TASK_RESUPPLY_RECEIVED_FIXTURE.read_text(encoding="utf-8"))["tasks"]
        + json.loads(TASK_RESUPPLY_CANCEL_FIXTURE.read_text(encoding="utf-8"))["tasks"]
    )
    repair_rows = (
        json.loads(TASK_REPAIR_COMPLETE_FIXTURE.read_text(encoding="utf-8"))["tasks"]
        + json.loads(TASK_REPAIR_RESPONSE_FIXTURE.read_text(encoding="utf-8"))["tasks"]
    )

    assert "task_fixture_contract" in ack_row["proof_modes"]
    assert "task_fixture_contract" in action_row["proof_modes"]
    assert "task_fixture_contract" in data_row["proof_modes"]
    assert "task_fixture_contract" in record_row["proof_modes"]
    assert "task_fixture_contract" in resupply_row["proof_modes"]
    assert "task_fixture_contract" in repair_row["proof_modes"]

    for task in ack_rows + action_rows + data_rows + record_rows + resupply_rows + repair_rows:
        shim.create_task(task)
    streamed = shim.stream_tasks()
    by_type = {event["task_type"]: event["payload"]["packetStoat"]["projectionKind"] for event in streamed}

    assert by_type["simulation-acknowledge"] == "task_ack_projection"
    assert by_type["simulation-acknowledge-r"] == "task_ack_reliable_projection"
    assert by_type["simulation-action-request"] == "task_action_request_projection"
    assert by_type["simulation-action-response"] == "task_action_response_projection"
    assert by_type["simulation-set-data"] == "task_set_data_projection"
    assert by_type["simulation-data"] == "task_data_payload_projection"
    assert by_type["simulation-record-r"] == "task_record_reliable_projection"
    assert by_type["simulation-set-record-r"] == "task_set_record_projection"
    assert by_type["simulation-record-query-r"] == "task_record_query_projection"
    assert by_type["logistics-resupply-offer"] == "task_resupply_offer_action"
    assert by_type["logistics-resupply-received"] == "task_resupply_received_action"
    assert by_type["logistics-resupply-cancel"] == "task_resupply_cancel_action"
    assert by_type["logistics-repair-complete"] == "task_repair_complete_action"
    assert by_type["logistics-repair-response"] == "task_repair_response_action"


def test_start_and_freeze_task_projection_fixtures_are_runnable() -> None:
    start_row = _row(7, 13)
    freeze_row = _row(7, 14)
    shim = MockLatticeShim()
    start_rows = json.loads(TASK_START_FIXTURE.read_text(encoding="utf-8"))["tasks"]
    freeze_rows = json.loads(TASK_FREEZE_FIXTURE.read_text(encoding="utf-8"))["tasks"]

    assert "task_fixture_contract" in start_row["proof_modes"]
    assert "task_fixture_contract" in freeze_row["proof_modes"]

    for task in start_rows + freeze_rows:
        shim.create_task(task)
    streamed = shim.stream_tasks()
    by_type = {event["task_type"]: event["payload"]["packetStoat"]["projectionKind"] for event in streamed}

    assert by_type["simulation-control-start"] == "task_start_projection"
    assert by_type["simulation-control-start-r"] == "task_start_projection"
    assert by_type["simulation-control-freeze"] == "task_freeze_projection"
    assert by_type["simulation-control-freeze-r"] == "task_freeze_projection"


def test_event_report_and_entity_reliable_task_projection_fixtures_are_runnable() -> None:
    report_row = _row(7, 21)
    create_row = _row(7, 51)
    shim = MockLatticeShim()
    report_rows = json.loads(TASK_EVENT_REPORT_FIXTURE.read_text(encoding="utf-8"))["tasks"]
    reliable_rows = json.loads(TASK_ENTITY_RELIABLE_FIXTURE.read_text(encoding="utf-8"))["tasks"]

    assert "task_fixture_contract" in report_row["proof_modes"]
    assert "task_fixture_contract" in create_row["proof_modes"]

    for task in report_rows + reliable_rows:
        shim.create_task(task)
    streamed = shim.stream_tasks()
    task_types = {event["task_type"] for event in streamed}
    projection_kinds = {event["payload"]["packetStoat"]["projectionKind"] for event in streamed}

    assert "simulation-event-report" in task_types
    assert "simulation-create-entity-r" in task_types
    assert "simulation-remove-entity-r" in task_types
    assert projection_kinds == {"task_lifecycle_control"}
