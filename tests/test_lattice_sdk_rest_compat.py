from __future__ import annotations

import importlib
import sys
from pathlib import Path

import httpx
import pytest


ROOT = Path(__file__).resolve().parents[1]
ADAPTER_SRC = ROOT / "integrations" / "lattice" / "src"
if str(ADAPTER_SRC) not in sys.path:
    sys.path.insert(0, str(ADAPTER_SRC))

from packet_stoat_lattice import MockLatticeRestHarness, build_official_lattice_client, build_sdk_mock_transport  # noqa: E402


def test_sdk_mock_transport_handles_official_entity_routes() -> None:
    harness = MockLatticeRestHarness()
    transport = build_sdk_mock_transport(harness)
    headers = {
        "Authorization": "Bearer mock-environment-token",
        "Anduril-Sandbox-Authorization": "Bearer mock-sandbox-token",
    }
    with httpx.Client(transport=transport, base_url="http://lattice.mock", headers=headers) as client:
        published = client.put(
            "/api/v1/entities",
            json={
                "entityId": "sdk-entity-1",
                "isLive": True,
                "aliases": {"name": "SDK Entity"},
                "provenance": {
                    "integrationName": "packet-stoat",
                    "dataType": "mock.track",
                    "sourceUpdateTime": 1,
                },
            },
        )
        fetched = client.get("/api/v1/entities/sdk-entity-1")

    assert published.status_code == 200
    assert published.json()["entityId"] == "sdk-entity-1"
    assert fetched.status_code == 200
    assert fetched.json()["aliases"]["name"] == "SDK Entity"


def test_sdk_mock_transport_rejects_missing_sandbox_header() -> None:
    transport = build_sdk_mock_transport()
    with httpx.Client(transport=transport, base_url="http://lattice.mock") as client:
        response = client.put(
            "/api/v1/entities",
            headers={"Authorization": "Bearer mock-environment-token"},
            json={"entityId": "sdk-entity-2"},
        )

    assert response.status_code == 403


def test_sdk_mock_transport_handles_surrogate_object_lifecycle() -> None:
    harness = MockLatticeRestHarness()
    transport = build_sdk_mock_transport(harness)
    headers = {
        "Authorization": "Bearer mock-environment-token",
        "Anduril-Sandbox-Authorization": "Bearer mock-sandbox-token",
    }
    content = b'{"entityId":"sdk-object-entity","kind":"surrogate"}'

    with httpx.Client(transport=transport, base_url="http://lattice.mock", headers=headers) as client:
        uploaded = client.post(
            "/api/v1/objects/reports/sdk-object-entity.json",
            content=content,
            headers={"content-type": "application/json", **headers},
        )
        metadata = client.head("/api/v1/objects/reports/sdk-object-entity.json")
        downloaded = client.get("/api/v1/objects/reports/sdk-object-entity.json")
        listed = client.get("/api/v1/objects", params={"prefix": "reports/"})
        deleted = client.delete("/api/v1/objects/reports/sdk-object-entity.json")
        missing = client.get("/api/v1/objects/reports/sdk-object-entity.json")

    assert uploaded.status_code == 200
    assert uploaded.json()["contentIdentifier"]["relativePath"] == "reports/sdk-object-entity.json"
    assert metadata.status_code == 200
    assert metadata.headers["content-length"] == str(len(content))
    assert metadata.headers["content-type"] == "application/json"
    assert downloaded.status_code == 200
    assert downloaded.content == content
    assert listed.status_code == 200
    assert [row["contentIdentifier"]["relativePath"] for row in listed.json()["pathMetadatas"]] == [
        "reports/sdk-object-entity.json"
    ]
    assert deleted.status_code == 204
    assert missing.status_code == 404


def test_sdk_mock_transport_rejects_invalid_surrogate_object_paths() -> None:
    transport = build_sdk_mock_transport()
    headers = {
        "Authorization": "Bearer mock-environment-token",
        "Anduril-Sandbox-Authorization": "Bearer mock-sandbox-token",
    }
    with httpx.Client(transport=transport, base_url="http://lattice.mock", headers=headers) as client:
        response = client.post("/api/v1/objects/reports/bad path.json", content=b"bad")

    assert response.status_code == 400
    assert "object path" in response.json()["error"]


def test_sdk_mock_transport_handles_task_surrogate_lifecycle() -> None:
    transport = build_sdk_mock_transport()
    headers = {
        "Authorization": "Bearer mock-environment-token",
        "Anduril-Sandbox-Authorization": "Bearer mock-sandbox-token",
    }
    task_payload = {
        "taskId": "sdk-task-1",
        "description": "Inspect surrogate object route",
        "displayName": "Visual Inspection",
        "relations": {"assignee": {"entityId": "agent-7"}},
        "specification": {"target": "sdk-object-entity"},
    }

    with httpx.Client(transport=transport, base_url="http://lattice.mock", headers=headers) as client:
        created = client.post("/api/v1/tasks", json=task_payload)
        fetched = client.get("/api/v1/tasks/sdk-task-1")
        running = client.put("/api/v1/tasks/sdk-task-1/status", json={"newStatus": "STATUS_IN_PROGRESS"})
        cancel = client.put("/api/v1/tasks/sdk-task-1/cancel", json={"reason": "operator-requested"})

    assert created.status_code == 200
    assert created.json()["taskId"] == "sdk-task-1"
    assert created.json()["packetStoat"]["agentId"] == "agent-7"
    assert fetched.status_code == 200
    assert fetched.json()["displayName"] == "Visual Inspection"
    assert running.status_code == 200
    assert running.json()["status"]["status"] == "in_progress"
    assert cancel.status_code == 200
    assert cancel.json()["status"]["status"] == "cancel_requested"


def test_sdk_mock_transport_entity_stream_is_sse_and_filters_components() -> None:
    harness = MockLatticeRestHarness()
    transport = build_sdk_mock_transport(harness)
    headers = {
        "Authorization": "Bearer mock-environment-token",
        "Anduril-Sandbox-Authorization": "Bearer mock-sandbox-token",
    }

    with httpx.Client(transport=transport, base_url="http://lattice.mock", headers=headers) as client:
        client.put(
            "/api/v1/entities",
            json={
                "entityId": "sdk-stream-1",
                "aliases": {"name": "Streamed Entity"},
                "location": {"position": {"latitudeDegrees": 1.0, "longitudeDegrees": 2.0}},
                "milView": {"disposition": "FRIENDLY"},
            },
        )
        response = client.post(
            "/api/v1/entities/stream",
            json={"componentsToInclude": ["aliases"], "preExistingOnly": True, "heartbeatIntervalMS": 25},
        )

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream"
    assert "Streamed Entity" in response.text
    assert "Heartbeat" in response.text
    assert "milView" not in response.text


def test_official_lattice_sdk_can_use_mock_transport_when_installed() -> None:
    try:
        importlib.import_module("anduril")
    except ModuleNotFoundError:
        pytest.skip("anduril-lattice-sdk is not installed")

    client = build_official_lattice_client()
    raw_response = client.entities.with_raw_response.publish_entity(
        entity_id="sdk-entity-3",
        is_live=True,
        aliases={"name": "SDK Entity 3"},
        provenance={
            "integrationName": "packet-stoat",
            "dataType": "mock.track",
            "sourceUpdateTime": 1,
        },
    )

    assert raw_response.status_code == 200
