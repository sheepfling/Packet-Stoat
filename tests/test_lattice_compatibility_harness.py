"""Local harness proof only.

This module keeps deterministic FastDIS shim behavior honest. It is not an
external-backend compatibility proof.
"""

from __future__ import annotations

import sys
from pathlib import Path
import time

import pytest


ROOT = Path(__file__).resolve().parents[1]
ADAPTER_SRC = ROOT / "packages" / "lattice" / "src"
if str(ADAPTER_SRC) not in sys.path:
    sys.path.insert(0, str(ADAPTER_SRC))

from packet_stoat_lattice import (  # noqa: E402
    AuthError,
    MockLatticeAuthConfig,
    MockLatticeAuthService,
    MockLatticeRestHarness,
    canonical_entity_from_fixture,
    lattice_track_payload_from_entity,
)


DIS_FIXTURE = ROOT / "packages" / "lattice" / "examples" / "dis_entity_fixture.json"


def _payload() -> dict[str, object]:
    return lattice_track_payload_from_entity(canonical_entity_from_fixture(DIS_FIXTURE)[0])


def _headers(access_token: str, sandbox_token: str = "mock-sandbox-token") -> dict[str, str]:
    return {
        "Authorization": f"Bearer {access_token}",
        "Anduril-Sandbox-Authorization": f"Bearer {sandbox_token}",
    }


def test_auth_client_credentials_environment_token_and_sandbox_header() -> None:
    auth = MockLatticeAuthService(MockLatticeAuthConfig(token_ttl_seconds=5))
    response = auth.oauth_token_response(
        client_id="packet-stoat-client",
        client_secret="packet-stoat-secret",
        scope="entities streams",
    )

    record = auth.validate_headers(_headers(str(response["access_token"])), required_scope="entities")
    env_record = auth.validate_headers(_headers("mock-environment-token"), required_scope="tasks")

    assert record.subject == "packet-stoat-client"
    assert env_record.subject == "environment-token"
    assert auth.refresh_recommended(str(response["access_token"]), margin_seconds=10)


def test_auth_rejects_missing_expired_and_under_scoped_tokens() -> None:
    auth = MockLatticeAuthService(MockLatticeAuthConfig(token_ttl_seconds=1))
    response = auth.oauth_token_response(
        client_id="packet-stoat-client",
        client_secret="packet-stoat-secret",
        scope="entities",
    )

    with pytest.raises(AuthError, match="missing or invalid sandbox authorization") as sandbox_error:
        auth.validate_headers({"Authorization": f"Bearer {response['access_token']}"}, required_scope="entities")
    with pytest.raises(AuthError, match="missing required scope") as scope_error:
        auth.validate_headers(_headers(str(response["access_token"])), required_scope="objects")
    with pytest.raises(AuthError, match="expired bearer token") as expired_error:
        auth.validate_headers(_headers(str(response["access_token"])), required_scope="entities", now=9999999999.0)

    assert sandbox_error.value.status_code == 403
    assert scope_error.value.status_code == 403
    assert expired_error.value.status_code == 401


def test_rest_harness_authenticates_publish_get_stream_object_and_task_flow() -> None:
    harness = MockLatticeRestHarness()
    token = harness.oauth_token(client_id="packet-stoat-client", client_secret="packet-stoat-secret")
    headers = _headers(str(token["access_token"]))
    payload = _payload()

    published = harness.publish_entity(payload, headers=headers)
    fetched = harness.get_entity(str(payload["entityId"]), headers=headers)
    uploaded = harness.upload_object("reports/track.json", "application/json", b'{"ok":true}', headers=headers)
    linked = harness.link_object_to_entity_media(str(payload["entityId"]), "reports/track.json", headers=headers)
    task = harness.create_task(
        {
            "task_id": "task-compat-1",
            "agent_id": str(payload["entityId"]),
            "task_type": "VisualId",
            "description": "classify track",
            "specification": "{}",
            "version": "v1",
            "created_by": "operator",
            "last_updated_by": "operator",
        },
        headers=headers,
    )
    status = harness.update_task_status("task-compat-1", "in_progress", headers=headers)
    entity_events = harness.stream_entities(headers=headers, components_to_include=["media", "location"])
    task_events = harness.stream_tasks(headers=headers, agent_id=str(payload["entityId"]))

    assert published["status"] == "accepted"
    assert fetched is not None
    assert uploaded["sha256"]
    assert linked["status"] == "accepted"
    assert task["status"] == "accepted"
    assert status["task_status"] == "in_progress"
    assert entity_events[-1]["kind"] == "Heartbeat"
    assert task_events[0]["task_type"] == "VisualId"


def test_object_paths_media_links_expiry_and_restart_semantics() -> None:
    harness = MockLatticeRestHarness()
    token = harness.oauth_token(client_id="packet-stoat-client", client_secret="packet-stoat-secret")
    headers = _headers(str(token["access_token"]))
    payload = _payload()

    with pytest.raises(ValueError, match="object path"):
        harness.upload_object("../bad path.png", "image/png", b"x", headers=headers)

    payload["expiryTime"] = 1
    harness.publish_entity(payload, headers=headers)
    expired = harness.shim.expire_entities(now_ms=2)
    assert expired["expired_entity_ids"] == [payload["entityId"]]
    assert harness.get_entity(str(payload["entityId"]), headers=headers)["isLive"] is False

    no_expiry_payload = _payload()
    no_expiry_payload["entityId"] = "packet-stoat:no-expiry"
    no_expiry_payload["noExpiry"] = True
    harness.publish_entity(no_expiry_payload, headers=headers)
    dropped = harness.shim.simulate_restart(now_unix_s=time.time() + 999.0, no_expiry_republish_window_s=300)
    assert dropped["dropped_entity_ids"] == ["packet-stoat:no-expiry"]


def test_task_lifecycle_rejects_invalid_and_terminal_transitions() -> None:
    harness = MockLatticeRestHarness()
    token = harness.oauth_token(client_id="packet-stoat-client", client_secret="packet-stoat-secret")
    headers = _headers(str(token["access_token"]))
    harness.create_task({"task_id": "task-terminal", "agent_id": "agent-1", "task_type": "VisualId"}, headers=headers)

    with pytest.raises(ValueError, match="unsupported task status"):
        harness.update_task_status("task-terminal", "teleported", headers=headers)

    harness.update_task_status("task-terminal", "completed", headers=headers)
    with pytest.raises(ValueError, match="terminal task"):
        harness.update_task_status("task-terminal", "in_progress", headers=headers)
