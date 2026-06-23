from __future__ import annotations

import hashlib
import json
from functools import lru_cache
from pathlib import Path
import sys
from typing import Any

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
    build_sdk_mock_transport,
    canonical_entity_from_fixture,
    entity_state_packet_from_track_payload,
    lattice_track_payload_from_entity,
)


def _headers() -> dict[str, str]:
    return {
        "Authorization": "Bearer mock-environment-token",
        "Anduril-Sandbox-Authorization": "Bearer mock-sandbox-token",
    }


def _rows() -> list[dict[str, object]]:
    return mapping_plan.build_plan()["records"]


def _row(version: int, pdu_type: int) -> dict[str, object]:
    return next(row for row in _rows() if row["protocol_version"] == version and row["pdu_type"] == pdu_type)


@lru_cache(maxsize=None)
def _fixture_json(path_str: str) -> dict[str, Any]:
    return json.loads((ROOT / path_str).read_text(encoding="utf-8"))


def _has_entity_fixture(path_str: str) -> bool:
    name = Path(path_str).name
    if name in {"dis_entity_fixture.json", "lattice_track_fixture.json"}:
        return True
    payload = _fixture_json(path_str)
    return "entityId" in payload


def _has_task_fixture(path_str: str) -> bool:
    payload = _fixture_json(path_str)
    return isinstance(payload.get("tasks"), list)


def _has_object_fixture(path_str: str) -> bool:
    payload = _fixture_json(path_str)
    return isinstance(payload.get("objects"), list)


def _entity_payload(path_str: str) -> dict[str, Any]:
    path = ROOT / path_str
    if path.name == "dis_entity_fixture.json":
        entity = canonical_entity_from_fixture(path)[0]
        return lattice_track_payload_from_entity(entity)
    return dict(_fixture_json(path_str))


def _select_entity_fixture(row: dict[str, object]) -> str | None:
    candidates = [path for path in row["proof_fixtures"] if _has_entity_fixture(path)]
    if not candidates:
        return None
    expected_kind = str(row["projected_public_payload_kind"])
    for path in candidates:
        payload = _entity_payload(path)
        packet_stoat = payload.get("packetStoat")
        if isinstance(packet_stoat, dict) and packet_stoat.get("projectionKind") == expected_kind:
            return path
    for preferred in ("integrations/lattice/examples/lattice_track_fixture.json", "integrations/lattice/examples/dis_entity_fixture.json"):
        if preferred in candidates:
            return preferred
    return candidates[0]


def _select_task_fixture(row: dict[str, object]) -> str | None:
    candidates = [path for path in row["proof_fixtures"] if _has_task_fixture(path)]
    if not candidates:
        return None
    expected_kind = str(row["projected_public_payload_kind"])
    for path in candidates:
        payload = _fixture_json(path)
        for task in payload["tasks"]:
            packet_stoat = task.get("packetStoat")
            if isinstance(packet_stoat, dict) and packet_stoat.get("projectionKind") == expected_kind:
                return path
    return candidates[0]


def _select_object_fixture(row: dict[str, object]) -> str | None:
    candidates = [path for path in row["proof_fixtures"] if _has_object_fixture(path)]
    if not candidates:
        return None
    expected_kind = str(row["projected_public_payload_kind"])
    for path in candidates:
        payload = _fixture_json(path)
        for obj in payload["objects"]:
            packet_stoat = obj.get("packetStoat")
            if isinstance(packet_stoat, dict) and packet_stoat.get("projectionKind") == expected_kind:
                return path
    return candidates[0]


def _assert_entity_egress_runtime(row: dict[str, object]) -> None:
    fixture_path = _select_entity_fixture(row)
    assert fixture_path is not None, row
    payload = _entity_payload(fixture_path)
    harness = MockLatticeRestHarness()
    transport = build_sdk_mock_transport(harness)

    with httpx.Client(transport=transport, base_url="http://lattice.mock", headers=_headers()) as client:
        published = client.put("/api/v1/entities", json=payload)
        fetched = client.get(f"/api/v1/entities/{payload['entityId']}")
        streamed = client.post("/api/v1/entities/events", json={"afterSequence": 0, "limit": 10})

    assert published.status_code == 200
    assert fetched.status_code == 200
    assert streamed.status_code == 200
    fetched_payload = fetched.json()
    assert fetched_payload["entityId"] == payload["entityId"]
    assert any(event.get("entityId") == payload["entityId"] for event in streamed.json()["events"])

    packet_stoat = fetched_payload.get("packetStoat")
    if isinstance(packet_stoat, dict) and row["projected_public_payload_kind"] != "track_entity":
        assert packet_stoat.get("projectionKind") == row["projected_public_payload_kind"]

    if row["egress_conformance"] == "structured":
        packet = entity_state_packet_from_track_payload(fetched_payload)
        header = parse_header(packet, strict=True)
        assert header is not None
        assert header[2] == 1

    if "raw_sidecar_preservation" in row["proof_modes"]:
        object_fixture = _select_object_fixture(row)
        if object_fixture is not None:
            object_row = _fixture_json(object_fixture)["objects"][0]
            content = str(object_row["content"]).encode("utf-8")
            result = harness.upload_object(
                str(object_row["path"]),
                str(object_row["content_type"]),
                content,
                headers=_headers(),
            )
            link = harness.link_object_to_entity_media(
                str(payload["entityId"]),
                str(object_row["path"]),
                headers=_headers(),
                label="packet-stoat sidecar",
            )
            linked = harness.get_entity(str(payload["entityId"]), headers=_headers())

            assert result["path"] == object_row["path"]
            assert link["object_path"] == object_row["path"]
            assert linked is not None
            media = linked.get("media", {})
            items = media.get("items", [])
            assert any(item.get("relativePath") == object_row["path"] for item in items)


def _assert_task_egress_runtime(row: dict[str, object]) -> None:
    fixture_path = _select_task_fixture(row)
    assert fixture_path is not None, row
    payload = _fixture_json(fixture_path)
    harness = MockLatticeRestHarness()

    created_ids: list[str] = []
    for task in payload["tasks"]:
        result = harness.create_task(dict(task), headers=_headers())
        created_ids.append(str(result["task_id"]))

    streamed = harness.stream_tasks(headers=_headers())
    assert len(streamed) == len(payload["tasks"])
    assert {event["task_id"] for event in streamed} == set(created_ids)
    assert all(event["kind"] == "TaskExecute" for event in streamed)

    expected_kind = str(row["projected_public_payload_kind"])
    assert any(
        isinstance(event.get("payload", {}).get("packetStoat"), dict)
        and event["payload"]["packetStoat"].get("projectionKind") == expected_kind
        for event in streamed
    )

    updated = harness.update_task_status(created_ids[0], "running", headers=_headers())
    assert updated["task_status"] == "running"


def _assert_object_egress_runtime(row: dict[str, object]) -> None:
    fixture_path = _select_object_fixture(row)
    assert fixture_path is not None, row
    payload = _fixture_json(fixture_path)
    harness = MockLatticeRestHarness()
    transport = build_sdk_mock_transport(harness)
    object_row = payload["objects"][0]
    content = str(object_row["content"]).encode("utf-8")
    expected_sha = hashlib.sha256(content).hexdigest()

    with httpx.Client(transport=transport, base_url="http://lattice.mock", headers=_headers()) as client:
        uploaded = client.post(
            f"/api/v1/objects/{object_row['path']}",
            content=content,
            headers={"content-type": str(object_row["content_type"]), **_headers()},
        )
        metadata = client.head(f"/api/v1/objects/{object_row['path']}")
        downloaded = client.get(f"/api/v1/objects/{object_row['path']}")
        listed = client.get("/api/v1/objects", params={"prefix": str(object_row["path"]).split("/")[0]})

    assert uploaded.status_code == 200
    assert metadata.status_code == 200
    assert downloaded.status_code == 200
    assert listed.status_code == 200
    assert downloaded.content == content
    assert metadata.headers["x-packet-stoat-sha256"] == expected_sha
    assert any(
        item["contentIdentifier"]["relativePath"] == object_row["path"]
        for item in listed.json()["pathMetadatas"]
    )


def _upload_first_sidecar(harness: MockLatticeRestHarness, row: dict[str, object]) -> tuple[str, bytes] | None:
    object_fixture = _select_object_fixture(row)
    if object_fixture is None:
        return None
    object_row = _fixture_json(object_fixture)["objects"][0]
    content = str(object_row["content"]).encode("utf-8")
    harness.upload_object(
        str(object_row["path"]),
        str(object_row["content_type"]),
        content,
        headers=_headers(),
    )
    return str(object_row["path"]), content


def test_each_row_has_runtime_egress_surface_for_its_declared_bucket() -> None:
    for row in _rows():
        bucket = str(row["strict_lattice_bucket"])
        if bucket == "Entity":
            _assert_entity_egress_runtime(row)
        elif bucket == "Task":
            _assert_task_egress_runtime(row)
        elif bucket == "Object":
            _assert_object_egress_runtime(row)
        else:
            raise AssertionError(f"unexpected strict bucket: {bucket}")


def test_egress_conformance_classes_have_matching_runtime_behavior() -> None:
    for row in _rows():
        conformance = str(row["egress_conformance"])
        proof_modes = set(row["proof_modes"])

        if conformance == "structured":
            assert str(row["strict_lattice_bucket"]) == "Entity", row
            assert "entity_roundtrip" in proof_modes or "entity_publish_get_stream" in proof_modes, row
            continue

        if conformance == "diagnostic":
            assert proof_modes & {"entity_projection_contract", "task_fixture_contract", "object_fixture_contract"}, row
            if str(row["strict_lattice_bucket"]) == "Task":
                assert bool(row["lossy_egress_supported"]), row
            continue

        if conformance == "raw_required":
            assert "raw_sidecar_preservation" in proof_modes, row
            assert _select_object_fixture(row) is not None, row
            continue

        raise AssertionError(f"unexpected egress conformance: {conformance}")


def test_relationship_entity_egress_preserves_semantics_and_sidecar_linkage() -> None:
    aggregate_row = _row(7, 33)
    ownership_row = _row(7, 35)
    harness = MockLatticeRestHarness()

    aggregate_payload = _entity_payload(_select_entity_fixture(aggregate_row))
    ownership_payload = _entity_payload(_select_entity_fixture(ownership_row))

    harness.publish_entity(aggregate_payload, headers=_headers())
    harness.publish_entity(ownership_payload, headers=_headers())

    aggregate_sidecar = _upload_first_sidecar(harness, aggregate_row)
    ownership_sidecar = _upload_first_sidecar(harness, ownership_row)
    assert aggregate_sidecar is not None
    assert ownership_sidecar is not None

    harness.link_object_to_entity_media(aggregate_payload["entityId"], aggregate_sidecar[0], headers=_headers(), label="aggregate-sidecar")
    harness.link_object_to_entity_media(ownership_payload["entityId"], ownership_sidecar[0], headers=_headers(), label="ownership-sidecar")

    aggregate_entity = harness.get_entity(str(aggregate_payload["entityId"]), headers=_headers())
    ownership_entity = harness.get_entity(str(ownership_payload["entityId"]), headers=_headers())

    assert aggregate_entity is not None
    assert ownership_entity is not None
    aggregate_relationships = aggregate_entity["packetStoat"]["relationships"]
    ownership_relationships = ownership_entity["packetStoat"]["relationships"]

    assert aggregate_relationships[0]["relationshipType"] == "AggregateState"
    assert ownership_relationships[0]["relationshipType"] == "TransferOwnership"
    assert any(item["relativePath"] == aggregate_sidecar[0] for item in aggregate_entity["media"]["items"])
    assert any(item["relativePath"] == ownership_sidecar[0] for item in ownership_entity["media"]["items"])


def test_logistics_task_egress_preserves_projection_specification_and_sidecar() -> None:
    rows = [_row(7, 5), _row(7, 7), _row(7, 10)]
    harness = MockLatticeRestHarness()

    for row, expected_spec in zip(
        rows,
        ["ServiceRequest", "ResupplyReceived", "RepairResponse"],
        strict=True,
    ):
        fixture_path = _select_task_fixture(row)
        assert fixture_path is not None
        task = dict(_fixture_json(fixture_path)["tasks"][0])

        created = harness.create_task(task, headers=_headers())
        streamed = harness.stream_tasks(headers=_headers())
        stored = next(event for event in streamed if event["task_id"] == created["task_id"])

        assert stored["payload"]["packetStoat"]["projectionKind"] == row["projected_public_payload_kind"]
        assert stored["payload"]["specification"]
        assert expected_spec in json.dumps(stored["payload"]["specification"], sort_keys=True)

        sidecar = _upload_first_sidecar(harness, row)
        assert sidecar is not None
        stored_object = harness.get_object(sidecar[0], headers=_headers())
        assert stored_object == sidecar[1]

        updated = harness.update_task_status(created["task_id"], "completed", headers=_headers())
        assert updated["task_status"] == "completed"


def test_event_task_egress_preserves_event_semantics_and_raw_sidecar() -> None:
    rows = [_row(7, 68), _row(7, 50), _row(7, 66)]
    expected_types = {
        68: "DirectedEnergyFire",
        50: "LEDetonation",
        66: "CollisionElastic",
    }
    harness = MockLatticeRestHarness()

    for row in rows:
        fixture_path = _select_task_fixture(row)
        assert fixture_path is not None
        task = dict(_fixture_json(fixture_path)["tasks"][0])

        created = harness.create_task(task, headers=_headers())
        stored = next(event for event in harness.stream_tasks(headers=_headers()) if event["task_id"] == created["task_id"])
        spec_json = json.dumps(stored["payload"]["specification"], sort_keys=True)

        assert stored["payload"]["packetStoat"]["projectionKind"] == row["projected_public_payload_kind"]
        assert expected_types[int(row["pdu_type"])] in spec_json

        sidecar = _upload_first_sidecar(harness, row)
        assert sidecar is not None
        metadata = harness.get_object_metadata(sidecar[0], headers=_headers())
        assert metadata is not None
        assert metadata["sha256"] == hashlib.sha256(sidecar[1]).hexdigest()


def test_communication_entity_egress_preserves_signal_and_designator_semantics() -> None:
    signal_row = _row(7, 26)
    designator_row = _row(7, 24)
    harness = MockLatticeRestHarness()

    signal_payload = _entity_payload(_select_entity_fixture(signal_row))
    designator_payload = _entity_payload(_select_entity_fixture(designator_row))

    harness.publish_entity(signal_payload, headers=_headers())
    harness.publish_entity(designator_payload, headers=_headers())

    signal_entity = harness.get_entity(str(signal_payload["entityId"]), headers=_headers())
    designator_entity = harness.get_entity(str(designator_payload["entityId"]), headers=_headers())
    assert signal_entity is not None
    assert designator_entity is not None

    assert signal_entity["packetStoat"]["projectionKind"] == "signal_of_interest_entity"
    assert signal_entity["signal"]["emitterNotation"] == "RADAR-X"
    assert signal_entity["signal"]["fixed"] is True
    sensors = signal_entity["sensors"]["sensors"]
    assert sensors[0]["sensorType"] == "SENSOR_TYPE_RADAR"

    assert designator_entity["packetStoat"]["projectionKind"] == "designator_entity"
    designator_sensors = designator_entity["sensors"]["sensors"]
    assert designator_sensors[0]["sensorType"] == "SENSOR_TYPE_LASER"
    assert designator_entity["ontology"]["platformType"] == "Designator"

    signal_sidecar = _upload_first_sidecar(harness, signal_row)
    designator_sidecar = _upload_first_sidecar(harness, designator_row)
    assert signal_sidecar is not None
    assert designator_sidecar is not None
    harness.link_object_to_entity_media(signal_payload["entityId"], signal_sidecar[0], headers=_headers(), label="signal-sidecar")
    harness.link_object_to_entity_media(designator_payload["entityId"], designator_sidecar[0], headers=_headers(), label="designator-sidecar")

    signal_linked = harness.get_entity(str(signal_payload["entityId"]), headers=_headers())
    designator_linked = harness.get_entity(str(designator_payload["entityId"]), headers=_headers())
    assert any(item["relativePath"] == signal_sidecar[0] for item in signal_linked["media"]["items"])
    assert any(item["relativePath"] == designator_sidecar[0] for item in designator_linked["media"]["items"])


def test_geo_and_hazard_entity_egress_preserves_shape_semantics_and_sidecars() -> None:
    environment_row = _row(7, 41)
    minefield_data_row = _row(7, 39)
    harness = MockLatticeRestHarness()

    environment_payload = _entity_payload(_select_entity_fixture(environment_row))
    minefield_payload = _entity_payload(_select_entity_fixture(minefield_data_row))

    harness.publish_entity(environment_payload, headers=_headers())
    harness.publish_entity(minefield_payload, headers=_headers())

    environment_entity = harness.get_entity(str(environment_payload["entityId"]), headers=_headers())
    minefield_entity = harness.get_entity(str(minefield_payload["entityId"]), headers=_headers())
    assert environment_entity is not None
    assert minefield_entity is not None

    assert environment_entity["packetStoat"]["projectionKind"] == "geo_entity_region"
    assert environment_entity["geoDetails"]["type"] == "GEO_TYPE_CONTROL_AREA"
    assert "ellipse" in environment_entity["geoShape"]

    assert minefield_entity["packetStoat"]["projectionKind"] == "geo_minefield_data_overlay"
    polygon = minefield_entity["geoShape"]["polygon"]
    assert len(polygon["rings"][0]["positions"]) >= 4
    assert minefield_entity["provenance"]["dataType"] == "dis.minefield_data"

    environment_sidecar = _upload_first_sidecar(harness, environment_row)
    minefield_sidecar = _upload_first_sidecar(harness, minefield_data_row)
    assert environment_sidecar is not None
    assert minefield_sidecar is not None
    harness.link_object_to_entity_media(environment_payload["entityId"], environment_sidecar[0], headers=_headers(), label="environment-sidecar")
    harness.link_object_to_entity_media(minefield_payload["entityId"], minefield_sidecar[0], headers=_headers(), label="minefield-sidecar")

    environment_linked = harness.get_entity(str(environment_payload["entityId"]), headers=_headers())
    minefield_linked = harness.get_entity(str(minefield_payload["entityId"]), headers=_headers())
    assert any(item["relativePath"] == environment_sidecar[0] for item in environment_linked["media"]["items"])
    assert any(item["relativePath"] == minefield_sidecar[0] for item in minefield_linked["media"]["items"])


def test_task_message_egress_preserves_query_and_comment_semantics() -> None:
    data_query_row = _row(7, 18)
    comment_row = _row(7, 22)
    harness = MockLatticeRestHarness()

    for row, expected_type, expected_key, expected_value in (
        (data_query_row, "task_data_query_projection", "messageType", "DataQuery"),
        (comment_row, "task_comment_projection", "messageType", "Comment"),
    ):
        fixture_path = _select_task_fixture(row)
        assert fixture_path is not None
        task = dict(_fixture_json(fixture_path)["tasks"][0])
        created = harness.create_task(task, headers=_headers())
        stored = next(event for event in harness.stream_tasks(headers=_headers()) if event["task_id"] == created["task_id"])

        assert stored["payload"]["packetStoat"]["projectionKind"] == expected_type
        assert stored["payload"]["specification"][expected_key] == expected_value
        assert stored["payload"]["displayName"]


def test_control_task_egress_preserves_start_freeze_and_reliable_semantics() -> None:
    harness = MockLatticeRestHarness()
    fixture_expectations = [
        (_row(7, 13), "StartResume", "StartResumeReliable"),
        (_row(7, 14), "StopFreeze", "StopFreezeReliable"),
    ]

    for row, expected_primary, expected_reliable in fixture_expectations:
        fixture_path = _select_task_fixture(row)
        assert fixture_path is not None
        tasks = list(_fixture_json(fixture_path)["tasks"])
        created_ids = [harness.create_task(dict(task), headers=_headers())["task_id"] for task in tasks]
        streamed = [event for event in harness.stream_tasks(headers=_headers()) if event["task_id"] in set(created_ids)]

        control_types = {event["payload"]["specification"]["controlType"] for event in streamed}
        projection_kinds = {event["payload"]["packetStoat"]["projectionKind"] for event in streamed}

        assert control_types == {expected_primary, expected_reliable}
        assert projection_kinds == {row["projected_public_payload_kind"]}
        assert all(event["payload"]["displayName"] for event in streamed)


def test_action_and_data_task_egress_preserves_semantics_and_reliable_pairs() -> None:
    harness = MockLatticeRestHarness()
    checks = [
        (_row(7, 16), "controlType", {"ActionRequest", "ActionRequestReliable"}),
        (_row(7, 17), "controlType", {"ActionResponse", "ActionResponseReliable"}),
        (_row(7, 19), "messageType", {"SetData", "SetDataReliable"}),
        (_row(7, 20), "messageType", {"Data", "DataReliable"}),
    ]

    for row, spec_key, expected_values in checks:
        fixture_path = _select_task_fixture(row)
        assert fixture_path is not None
        tasks = list(_fixture_json(fixture_path)["tasks"])
        created_ids = [harness.create_task(dict(task), headers=_headers())["task_id"] for task in tasks]
        streamed = [event for event in harness.stream_tasks(headers=_headers()) if event["task_id"] in set(created_ids)]

        observed_values = {event["payload"]["specification"][spec_key] for event in streamed}
        projection_kinds = {event["payload"]["packetStoat"]["projectionKind"] for event in streamed}

        assert observed_values == expected_values
        assert projection_kinds == {row["projected_public_payload_kind"]}


def test_transmitter_and_receiver_egress_preserves_comms_semantics() -> None:
    transmitter_row = _row(7, 25)
    receiver_row = _row(7, 27)
    harness = MockLatticeRestHarness()

    transmitter_payload = _entity_payload(_select_entity_fixture(transmitter_row))
    receiver_payload = _entity_payload(_select_entity_fixture(receiver_row))

    harness.publish_entity(transmitter_payload, headers=_headers())
    harness.publish_entity(receiver_payload, headers=_headers())

    transmitter = harness.get_entity(str(transmitter_payload["entityId"]), headers=_headers())
    receiver = harness.get_entity(str(receiver_payload["entityId"]), headers=_headers())
    assert transmitter is not None
    assert receiver is not None

    assert transmitter["packetStoat"]["projectionKind"] == "transmitter_entity"
    assert transmitter["signal"]["modality"] == "MODALITY_RF"
    assert transmitter["ontology"]["platformType"] == "Transmitter"

    assert receiver["packetStoat"]["projectionKind"] == "receiver_entity"
    assert receiver["signal"]["modality"] == "MODALITY_RF"
    assert receiver["ontology"]["platformType"] == "Receiver"


def test_geo_point_line_polygon_egress_preserves_shape_semantics() -> None:
    point_row = _row(7, 43)
    line_row = _row(7, 44)
    polygon_row = _row(7, 45)
    harness = MockLatticeRestHarness()

    point_payload = _entity_payload(_select_entity_fixture(point_row))
    line_payload = _entity_payload(_select_entity_fixture(line_row))
    polygon_payload = _entity_payload(_select_entity_fixture(polygon_row))

    for payload in (point_payload, line_payload, polygon_payload):
        harness.publish_entity(payload, headers=_headers())

    point = harness.get_entity(str(point_payload["entityId"]), headers=_headers())
    line = harness.get_entity(str(line_payload["entityId"]), headers=_headers())
    polygon = harness.get_entity(str(polygon_payload["entityId"]), headers=_headers())
    assert point is not None
    assert line is not None
    assert polygon is not None

    assert point["packetStoat"]["projectionKind"] == "geo_entity_point"
    assert "point" in point["geoShape"]
    assert point["geoShape"]["point"]["position"]["latitudeDegrees"] > 0

    assert line["packetStoat"]["projectionKind"] == "geo_entity_line"
    assert len(line["geoShape"]["line"]["positions"]) == 2

    assert polygon["packetStoat"]["projectionKind"] == "geo_entity_polygon"
    assert len(polygon["geoShape"]["polygon"]["rings"][0]["positions"]) >= 4


def test_additional_communication_entity_egress_preserves_semantics() -> None:
    harness = MockLatticeRestHarness()
    checks = [
        (_row(7, 23), "emission_sensor_entity", ("sensors", "sensors", 0, "sensorType"), "SENSOR_TYPE_ELECTRONIC_SUPPORT"),
        (_row(7, 28), "entity_signal_annotation", ("packetStoat", "annotations", 0, "kind"), "IFF"),
        (_row(7, 29), "signal_of_interest_entity", ("signal", "emitterNotation"), "SONAR-PING"),
        (_row(7, 30), "sensor_point_of_interest_entity", ("sensors", "sensors", 0, "sensorType"), "SENSOR_TYPE_RADAR"),
        (_row(7, 31), "intercom_signal_annotation", ("packetStoat", "annotations", 0, "kind"), "INTERCOM_SIGNAL"),
        (_row(7, 32), "intercom_control_annotation", ("packetStoat", "annotations", 0, "kind"), "INTERCOM_CONTROL"),
    ]

    def dig(payload: dict[str, object], path: tuple[object, ...]) -> object:
        cur: object = payload
        for part in path:
            if isinstance(part, int):
                cur = cur[part]  # type: ignore[index]
            else:
                cur = cur[part]  # type: ignore[index]
        return cur

    for row, expected_kind, field_path, expected_value in checks:
        payload = _entity_payload(_select_entity_fixture(row))
        harness.publish_entity(payload, headers=_headers())
        entity = harness.get_entity(str(payload["entityId"]), headers=_headers())
        assert entity is not None
        assert entity["packetStoat"]["projectionKind"] == expected_kind
        assert dig(entity, field_path) == expected_value


def test_relationship_group_and_part_egress_preserves_semantics() -> None:
    harness = MockLatticeRestHarness()
    checks = [
        (_row(7, 34), "entity_group_membership_projection", "IsGroupOf", "memberEntityId"),
        (_row(7, 36), "entity_part_relationship_projection", "IsPartOf", "parentEntityId"),
    ]

    for row, expected_kind, expected_relationship, id_key in checks:
        payload = _entity_payload(_select_entity_fixture(row))
        harness.publish_entity(payload, headers=_headers())
        entity = harness.get_entity(str(payload["entityId"]), headers=_headers())
        assert entity is not None
        assert entity["packetStoat"]["projectionKind"] == expected_kind
        relationship = entity["packetStoat"]["relationships"][0]
        assert relationship["relationshipType"] == expected_relationship
        assert relationship[id_key]


def test_ack_and_reliable_record_task_egress_preserves_semantics() -> None:
    harness = MockLatticeRestHarness()
    checks = [
        (_row(7, 15), "task_ack_projection", "controlType", "Acknowledge"),
        (_row(7, 55), "task_ack_reliable_projection", "controlType", "AcknowledgeReliable"),
        (_row(7, 58), "task_data_query_projection", "messageType", "DataQueryReliable"),
        (_row(7, 62), "task_comment_projection", "messageType", "CommentReliable"),
        (_row(7, 63), "task_record_reliable_projection", "messageType", "RecordReliable"),
        (_row(7, 64), "task_set_record_projection", "messageType", "SetRecordReliable"),
        (_row(7, 65), "task_record_query_projection", "messageType", "RecordQueryReliable"),
    ]

    for row, expected_kind, spec_key, expected_value in checks:
        fixture_path = _select_task_fixture(row)
        assert fixture_path is not None
        tasks = [dict(task) for task in _fixture_json(fixture_path)["tasks"]]
        created_ids = [harness.create_task(task, headers=_headers())["task_id"] for task in tasks]
        streamed = [event for event in harness.stream_tasks(headers=_headers()) if event["task_id"] in set(created_ids)]

        assert any(
            event["payload"]["packetStoat"]["projectionKind"] == expected_kind
            and event["payload"]["specification"][spec_key] == expected_value
            for event in streamed
        )


def test_lifecycle_entity_egress_preserves_create_remove_update_semantics() -> None:
    harness = MockLatticeRestHarness()
    checks = [
        (_row(7, 11), "entity_create_projection", True, "dis.create_entity"),
        (_row(7, 12), "entity_remove_projection", False, "dis.remove_entity"),
        (_row(7, 67), "entity_state_update_projection", True, "dis.entity_state_update"),
    ]

    for row, expected_kind, expected_live, expected_type in checks:
        payload = _entity_payload(_select_entity_fixture(row))
        harness.publish_entity(payload, headers=_headers())
        entity = harness.get_entity(str(payload["entityId"]), headers=_headers())
        assert entity is not None
        assert entity["packetStoat"]["projectionKind"] == expected_kind
        assert entity["isLive"] is expected_live
        assert entity["provenance"]["dataType"] == expected_type


def test_minefield_and_hazard_egress_preserves_overlay_semantics() -> None:
    harness = MockLatticeRestHarness()
    checks = [
        (_row(7, 37), "geo_entity_hazard_region", "dis.environment"),
        (_row(7, 38), "geo_minefield_query_overlay", "dis.minefield_query"),
        (_row(7, 40), "geo_minefield_response_nack", "dis.minefield_response_nack"),
    ]

    for row, expected_kind, expected_type in checks:
        payload = _entity_payload(_select_entity_fixture(row))
        harness.publish_entity(payload, headers=_headers())
        entity = harness.get_entity(str(payload["entityId"]), headers=_headers())
        assert entity is not None
        assert entity["packetStoat"]["projectionKind"] == expected_kind
        assert entity["provenance"]["dataType"] == expected_type
        polygon = entity["geoShape"]["polygon"]
        assert len(polygon["rings"][0]["positions"]) >= 4


def test_annotation_style_entity_egress_preserves_pose_appearance_and_articulation() -> None:
    harness = MockLatticeRestHarness()
    checks = [
        (_row(7, 46), "entity_pose_annotation", ("pose", "headingDegrees"), 87.0),
        (_row(7, 47), "entity_visual_state_annotation", ("packetStoat", "appearance", "damageState"), "slight_damage"),
        (_row(7, 48), "entity_articulation_annotation", ("packetStoat", "articulation", "part"), "turret"),
    ]

    def dig(payload: dict[str, object], path: tuple[object, ...]) -> object:
        cur: object = payload
        for part in path:
            cur = cur[part]  # type: ignore[index]
        return cur

    for row, expected_kind, field_path, expected_value in checks:
        payload = _entity_payload(_select_entity_fixture(row))
        harness.publish_entity(payload, headers=_headers())
        entity = harness.get_entity(str(payload["entityId"]), headers=_headers())
        assert entity is not None
        assert entity["packetStoat"]["projectionKind"] == expected_kind
        assert dig(entity, field_path) == expected_value


def test_generic_event_task_egress_preserves_event_semantics() -> None:
    harness = MockLatticeRestHarness()
    checks = [
        (_row(7, 2), "task_event_projection", "eventType", "Fire"),
        (_row(7, 3), "task_event_projection", "eventType", "Detonation"),
        (_row(7, 4), "task_event_projection", "eventType", "Collision"),
        (_row(7, 49), "task_le_fire_event", "eventType", "LEFire"),
    ]

    for row, expected_kind, spec_key, expected_value in checks:
        fixture_path = _select_task_fixture(row)
        assert fixture_path is not None
        task = dict(_fixture_json(fixture_path)["tasks"][0])
        task_id = harness.create_task(task, headers=_headers())["task_id"]
        stored = next(event for event in harness.stream_tasks(headers=_headers()) if event["task_id"] == task_id)

        assert stored["payload"]["packetStoat"]["projectionKind"] == expected_kind
        assert stored["payload"]["specification"][spec_key] == expected_value


def test_logistics_task_egress_preserves_offer_cancel_complete_semantics() -> None:
    harness = MockLatticeRestHarness()
    checks = [
        (_row(7, 6), "task_resupply_offer_action", "logisticsType", "ResupplyOffer"),
        (_row(7, 8), "task_resupply_cancel_action", "logisticsType", "ResupplyCancel"),
        (_row(7, 9), "task_repair_complete_action", "logisticsType", "RepairComplete"),
    ]

    for row, expected_kind, spec_key, expected_value in checks:
        fixture_path = _select_task_fixture(row)
        assert fixture_path is not None
        task = dict(_fixture_json(fixture_path)["tasks"][0])
        task_id = harness.create_task(task, headers=_headers())["task_id"]
        stored = next(event for event in harness.stream_tasks(headers=_headers()) if event["task_id"] == task_id)

        assert stored["payload"]["packetStoat"]["projectionKind"] == expected_kind
        assert stored["payload"]["specification"][spec_key] == expected_value


def test_task_lifecycle_control_variants_preserve_semantics() -> None:
    harness = MockLatticeRestHarness()
    checks = [
        (_row(7, 21), "task_lifecycle_control", "messageType", "EventReport"),
        (_row(7, 51), "task_lifecycle_control", "messageType", "CreateEntityReliable"),
        (_row(7, 52), "task_lifecycle_control", "messageType", "RemoveEntityReliable"),
        (_row(7, 61), "task_lifecycle_control", "messageType", "EventReport"),
    ]

    for row, expected_kind, spec_key, expected_value in checks:
        fixture_path = _select_task_fixture(row)
        assert fixture_path is not None
        tasks = [dict(task) for task in _fixture_json(fixture_path)["tasks"]]
        created_ids = [harness.create_task(task, headers=_headers())["task_id"] for task in tasks]
        streamed = [event for event in harness.stream_tasks(headers=_headers()) if event["task_id"] in set(created_ids)]

        assert any(
            event["payload"]["packetStoat"]["projectionKind"] == expected_kind
            and event["payload"]["specification"][spec_key] == expected_value
            for event in streamed
        )


def test_geo_grid_and_info_ops_style_rows_preserve_semantics() -> None:
    harness = MockLatticeRestHarness()

    grid_payload = _entity_payload(_select_entity_fixture(_row(7, 42)))
    harness.publish_entity(grid_payload, headers=_headers())
    grid = harness.get_entity(str(grid_payload["entityId"]), headers=_headers())
    assert grid is not None
    assert grid["packetStoat"]["projectionKind"] == "geo_grid_overlay"
    assert grid["geoDetails"]["type"] == "GEO_TYPE_GRIDDED_DATA"
    assert len(grid["geoShape"]["polygon"]["rings"][0]["positions"]) >= 5

    task_checks = [
        (_row(7, 69), "task_entity_damage_event", "eventType", "EntityDamageStatus"),
        (_row(7, 70), "task_information_operation_action", "infoOpsType", "Action"),
        (_row(7, 71), "task_information_operation_report", "infoOpsType", "Report"),
    ]
    for row, expected_kind, spec_key, expected_value in task_checks:
        fixture_path = _select_task_fixture(row)
        assert fixture_path is not None
        task = dict(_fixture_json(fixture_path)["tasks"][0])
        task_id = harness.create_task(task, headers=_headers())["task_id"]
        stored = next(event for event in harness.stream_tasks(headers=_headers()) if event["task_id"] == task_id)
        assert stored["payload"]["packetStoat"]["projectionKind"] == expected_kind
        assert stored["payload"]["specification"][spec_key] == expected_value


def test_archive_rows_preserve_object_projection_and_bytes() -> None:
    harness = MockLatticeRestHarness()
    rows = [_row(6, 0), _row(7, 0), _row(7, 72)]

    for row in rows:
        fixture_path = _select_object_fixture(row)
        assert fixture_path is not None
        payload = _fixture_json(fixture_path)
        obj = payload["objects"][0]
        content = str(obj["content"]).encode("utf-8")

        uploaded = harness.upload_object(
            str(obj["path"]),
            str(obj["content_type"]),
            content,
            headers=_headers(),
        )
        downloaded = harness.get_object(str(obj["path"]), headers=_headers())
        metadata = harness.get_object_metadata(str(obj["path"]), headers=_headers())

        assert uploaded["path"] == obj["path"]
        assert downloaded == content
        assert metadata is not None
        assert metadata["content_type"] == obj["content_type"]
        if isinstance(obj.get("packetStoat"), dict):
            assert obj["packetStoat"]["projectionKind"] == row["projected_public_payload_kind"]
