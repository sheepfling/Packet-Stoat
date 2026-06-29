"""Local shim-only bucket conformance checks.

These tests prove FastDIS-local route behavior and fixture expectations.
They do not prove Zorn compatibility or real Lattice compatibility.
"""

from __future__ import annotations

import sys
from pathlib import Path

import httpx


ROOT = Path(__file__).resolve().parents[1]
ADAPTER_SRC = ROOT / "packages" / "lattice" / "src"
if str(ADAPTER_SRC) not in sys.path:
    sys.path.insert(0, str(ADAPTER_SRC))

from fastdis import parse_header  # noqa: E402
from packet_stoat_lattice import (  # noqa: E402
    MockLatticeRestHarness,
    MockLatticeShim,
    build_sdk_mock_transport,
    canonical_entity_from_fixture,
    entity_state_packet_from_fixture,
    lattice_track_payload_from_entity,
    publish_entities,
    start_grpc_shim_server,
    stream_entity_components,
)


DIS_FIXTURE = ROOT / "packages" / "lattice" / "examples" / "dis_entity_fixture.json"


def _headers() -> dict[str, str]:
    return {
        "Authorization": "Bearer mock-environment-token",
        "Anduril-Sandbox-Authorization": "Bearer mock-sandbox-token",
    }


def test_entity_bucket_rest_grpc_publish_get_stream_parity() -> None:
    shim = MockLatticeShim()
    harness = MockLatticeRestHarness(shim=shim)
    transport = build_sdk_mock_transport(harness)
    entity = canonical_entity_from_fixture(DIS_FIXTURE)[0]
    rest_payload = lattice_track_payload_from_entity(entity)
    grpc_payload = dict(rest_payload)
    grpc_payload["entityId"] = f"{rest_payload['entityId']}-grpc"

    server, target, _active_shim = start_grpc_shim_server(shim=shim)
    try:
        with httpx.Client(transport=transport, base_url="http://lattice.mock", headers=_headers()) as client:
            published = client.put("/api/v1/entities", json=rest_payload)
            fetched_rest = client.get(f"/api/v1/entities/{rest_payload['entityId']}")

            preexisting = stream_entity_components(target, preexisting_only=True, include_all_components=True)

            grpc_summary = publish_entities(target, [grpc_payload])
            fetched_grpc = client.get(f"/api/v1/entities/{grpc_payload['entityId']}")
            polled = client.post("/api/v1/entities/events", json={"afterSequence": 0, "limit": 20})

        assert published.status_code == 200
        assert fetched_rest.status_code == 200
        assert fetched_rest.json()["entityId"] == rest_payload["entityId"]
        assert any(event["entity_id"] == rest_payload["entityId"] for event in preexisting if event["entity_id"])
        assert grpc_summary["accepted"] == 1
        assert fetched_grpc.status_code == 200
        assert fetched_grpc.json()["entityId"] == grpc_payload["entityId"]
        event_ids = {
            event.get("entityId")
            for event in polled.json().get("events", [])
            if isinstance(event, dict)
        }
        assert rest_payload["entityId"] in event_ids
        assert grpc_payload["entityId"] in event_ids
    finally:
        server.stop(0)


def test_task_bucket_rest_create_status_cancel_stream_conformance() -> None:
    harness = MockLatticeRestHarness()
    transport = build_sdk_mock_transport(harness)
    headers = _headers()
    task_payload = {
        "taskId": "bucket-task-1",
        "description": "Inspect entity bucket parity",
        "displayName": "Entity Inspect",
        "relations": {"assignee": {"entityId": "agent-42"}},
        "specification": {"target": "entity-42"},
    }

    with httpx.Client(transport=transport, base_url="http://lattice.mock", headers=headers) as client:
        created = client.post("/api/v1/tasks", json=task_payload)
        fetched = client.get("/api/v1/tasks/bucket-task-1")
        running = client.put("/api/v1/tasks/bucket-task-1/status", json={"newStatus": "STATUS_IN_PROGRESS"})
        cancel = client.put("/api/v1/tasks/bucket-task-1/cancel", json={"reason": "operator-requested"})
        stream = client.post("/api/v1/tasks/stream", json={"agentId": "agent-42"})

    assert created.status_code == 200
    assert fetched.status_code == 200
    assert running.status_code == 200
    assert cancel.status_code == 200
    assert stream.status_code == 200
    assert created.json()["taskId"] == "bucket-task-1"
    assert fetched.json()["displayName"] == "Entity Inspect"
    assert running.json()["status"]["status"] == "in_progress"
    assert cancel.json()["status"]["status"] == "cancel_requested"
    task_rows = stream.json()["tasks"]
    assert len(task_rows) == 1
    assert task_rows[0]["task_id"] == "bucket-task-1"
    assert task_rows[0]["status"] == "cancel_requested"


def test_object_bucket_upload_metadata_download_delete_and_raw_sidecar_egress() -> None:
    harness = MockLatticeRestHarness()
    transport = build_sdk_mock_transport(harness)
    headers = _headers()
    raw_packet = entity_state_packet_from_fixture(DIS_FIXTURE)
    object_path = "raw/dis/entity_state_packet.pdu"

    with httpx.Client(transport=transport, base_url="http://lattice.mock", headers=headers) as client:
        uploaded = client.post(
            f"/api/v1/objects/{object_path}",
            content=raw_packet,
            headers={"content-type": "application/octet-stream", **headers},
        )
        metadata = client.head(f"/api/v1/objects/{object_path}")
        downloaded = client.get(f"/api/v1/objects/{object_path}")
        listed = client.get("/api/v1/objects", params={"prefix": "raw/dis/"})
        deleted = client.delete(f"/api/v1/objects/{object_path}")
        missing = client.get(f"/api/v1/objects/{object_path}")

    assert uploaded.status_code == 200
    assert metadata.status_code == 200
    assert downloaded.status_code == 200
    assert listed.status_code == 200
    assert deleted.status_code == 204
    assert missing.status_code == 404
    assert metadata.headers["content-length"] == str(len(raw_packet))
    assert downloaded.content == raw_packet
    assert listed.json()["pathMetadatas"][0]["contentIdentifier"]["relativePath"] == object_path

    header = parse_header(downloaded.content, strict=True)
    assert header is not None
    assert header[2] == 1
