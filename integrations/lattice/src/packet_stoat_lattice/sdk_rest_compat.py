from __future__ import annotations

import importlib
import json
import os
from dataclasses import dataclass
from typing import Any, Mapping
from urllib.parse import parse_qs, unquote

import httpx

from .auth import AuthError
from .rest_harness import MockLatticeRestHarness


@dataclass(frozen=True)
class OfflineClientConfig:
    base_url: str
    skip_tls_verify: bool
    sandbox_token: str | None = None

    @property
    def httpx_verify(self) -> bool:
        return not self.skip_tls_verify


def build_sdk_mock_transport(harness: MockLatticeRestHarness | None = None) -> httpx.MockTransport:
    active_harness = harness or MockLatticeRestHarness()

    def handler(request: httpx.Request) -> httpx.Response:
        try:
            return _handle_request(active_harness, request)
        except AuthError as exc:
            return _json_response(exc.status_code, {"error": exc.reason})
        except KeyError as exc:
            return _json_response(404, {"error": str(exc)})
        except ValueError as exc:
            return _json_response(400, {"error": str(exc)})

    return httpx.MockTransport(handler)


def build_official_lattice_client(
    *,
    harness: MockLatticeRestHarness | None = None,
    base_url: str = "http://lattice.mock",
    token: str = "mock-environment-token",
    sandbox_token: str = "mock-sandbox-token",
    skip_tls_verify: bool | None = None,
):
    module = importlib.import_module("anduril")
    transport = build_sdk_mock_transport(harness)
    httpx_client = build_offline_httpx_client(transport=transport, skip_tls_verify=skip_tls_verify)
    return module.Lattice(
        base_url=base_url,
        token=lambda: token,
        headers={"Anduril-Sandbox-Authorization": f"Bearer {sandbox_token}"},
        httpx_client=httpx_client,
    )


def build_offline_httpx_client(
    *,
    transport: httpx.BaseTransport | None = None,
    skip_tls_verify: bool | None = None,
    timeout_seconds: float = 10.0,
) -> httpx.Client:
    if skip_tls_verify is None:
        verify = offline_client_config_from_env().httpx_verify
    else:
        verify = not skip_tls_verify
    return httpx.Client(transport=transport, verify=verify, timeout=timeout_seconds)


def offline_client_config_from_env(env: Mapping[str, str] | None = None) -> OfflineClientConfig:
    values = os.environ if env is None else env
    endpoint = values.get("LATTICE_ENDPOINT", "lattice.mock").strip() or "lattice.mock"
    base_url = endpoint if "://" in endpoint else f"https://{endpoint}"
    skip_tls_verify = values.get("SKIP_TLS_VERIFY", "").strip().lower() == "true"
    sandbox_token = values.get("SANDBOXES_TOKEN") or None
    return OfflineClientConfig(base_url=base_url, skip_tls_verify=skip_tls_verify, sandbox_token=sandbox_token)


def _handle_request(harness: MockLatticeRestHarness, request: httpx.Request) -> httpx.Response:
    path = request.url.path
    headers = {key: value for key, value in request.headers.items()}

    if request.method == "POST" and path == "/api/v1/oauth/token":
        harness.auth.validate_sandbox_headers(headers)
        payload = _token_body(request)
        return _json_response(
            200,
            dict(
                harness.oauth_token(
                    client_id=str(payload.get("client_id", "")),
                    client_secret=str(payload.get("client_secret", "")),
                    grant_type=str(payload.get("grant_type", "client_credentials")),
                    scope=str(payload["scope"]) if "scope" in payload else None,
                )
            ),
        )

    if request.method == "PUT" and path == "/api/v1/entities":
        payload = _json_body(request)
        harness.publish_entity(payload, headers=headers)
        return _json_response(200, payload)

    if request.method == "GET" and path.startswith("/api/v1/entities/"):
        entity_id = unquote(path.removeprefix("/api/v1/entities/"))
        payload = harness.get_entity(entity_id, headers=headers)
        if payload is None:
            return _json_response(404, {"error": "entity not found"})
        return _json_response(200, payload)

    if request.method == "POST" and path == "/api/v1/entities/events":
        harness.auth.validate_headers(headers, required_scope="streams")
        events = harness.shim.stream_entities(pre_existing_only=True, include_heartbeat=False)
        return _json_response(200, {"sessionToken": "mock-session", "events": events})

    if request.method == "POST" and path == "/api/v1/entities/stream":
        request_payload = _json_body(request)
        events = harness.stream_entities(
            headers=headers,
            components_to_include=request_payload.get("componentsToInclude"),
            heartbeat_interval_ms=int(request_payload.get("heartbeatIntervalMS") or 1000),
            pre_existing_only=bool(request_payload.get("preExistingOnly")),
        )
        return _sse_response(events)

    if request.method == "GET" and path == "/api/v1/objects":
        prefix = request.url.params.get("prefix", "")
        objects = [_path_metadata(row) for row in harness.list_objects(prefix, headers=headers)]
        return _json_response(200, {"pathMetadatas": objects, "nextPageToken": None})

    if path.startswith("/api/v1/objects/"):
        object_path = _decode_object_path(path.removeprefix("/api/v1/objects/"))
        if request.method == "POST":
            result = harness.upload_object(
                object_path,
                request.headers.get("content-type", "application/octet-stream"),
                request.content,
                headers=headers,
            )
            return _json_response(200, _path_metadata(result))
        if request.method == "GET":
            content = harness.get_object(object_path, headers=headers)
            if content is None:
                return _json_response(404, {"error": "object not found"})
            metadata = harness.get_object_metadata(object_path, headers=headers) or {}
            return httpx.Response(
                200,
                content=content,
                headers={
                    "content-type": str(metadata.get("content_type", "application/octet-stream")),
                    "x-packet-stoat-sha256": str(metadata.get("sha256", "")),
                },
            )
        if request.method == "HEAD":
            metadata = harness.get_object_metadata(object_path, headers=headers)
            if metadata is None:
                return _json_response(404, {"error": "object not found"})
            return httpx.Response(
                200,
                headers={
                    "content-length": str(metadata["size_bytes"]),
                    "content-type": str(metadata["content_type"]),
                    "x-packet-stoat-sha256": str(metadata["sha256"]),
                },
            )
        if request.method == "DELETE":
            harness.delete_object(object_path, headers=headers)
            return httpx.Response(204)

    if request.method == "POST" and path == "/api/v1/tasks":
        payload = _json_body(request)
        task_id = str(payload.get("taskId") or payload.get("task_id") or "task-sdk-1")
        result = harness.create_task(
            {
                "task_id": task_id,
                "agent_id": _agent_id_from_task_payload(payload),
                "task_type": str(payload.get("displayName") or payload.get("taskType") or "Task"),
                "payload": payload,
            },
            headers=headers,
        )
        return _json_response(200, _task_payload(harness, task_id, result))

    if path.startswith("/api/v1/tasks/"):
        task_tail = path.removeprefix("/api/v1/tasks/")
        if task_tail.endswith("/status") and request.method == "PUT":
            task_id = unquote(task_tail.removesuffix("/status"))
            payload = _json_body(request)
            status = _status_from_task_status_payload(payload.get("newStatus"))
            harness.update_task_status(task_id, status, headers=headers)
            return _json_response(200, _task_payload(harness, task_id))
        if task_tail.endswith("/cancel") and request.method == "PUT":
            task_id = unquote(task_tail.removesuffix("/cancel"))
            harness.update_task_status(task_id, "cancel_requested", headers=headers)
            return _json_response(200, _task_payload(harness, task_id))
        if request.method == "GET":
            task_id = unquote(task_tail)
            return _json_response(200, _task_payload(harness, task_id))

    if request.method == "POST" and path == "/api/v1/tasks/stream":
        payload = _json_body(request)
        agent_id = payload.get("agentId")
        events = harness.stream_tasks(headers=headers, agent_id=None if agent_id is None else str(agent_id))
        return _json_response(200, {"tasks": events})

    return _json_response(404, {"error": f"unhandled SDK mock route: {request.method} {path}"})


def _json_body(request: httpx.Request) -> dict[str, Any]:
    if not request.content:
        return {}
    return dict(json.loads(request.content.decode("utf-8")))


def _token_body(request: httpx.Request) -> dict[str, Any]:
    if not request.content:
        return {}
    content_type = request.headers.get("content-type", "").lower()
    body = request.content.decode("utf-8")
    if "application/x-www-form-urlencoded" in content_type:
        return {key: values[-1] for key, values in parse_qs(body, keep_blank_values=True).items()}
    return dict(json.loads(body))


def _json_response(status_code: int, payload: dict[str, Any]) -> httpx.Response:
    return httpx.Response(status_code, json=payload, headers={"content-type": "application/json"})


def _sse_response(events: list[dict[str, Any]]) -> httpx.Response:
    lines: list[str] = []
    for event in events:
        lines.append(f"event: {event.get('kind', 'message')}")
        lines.append(f"data: {json.dumps(event, sort_keys=True)}")
        lines.append("")
    return httpx.Response(200, content="\n".join(lines).encode("utf-8"), headers={"content-type": "text/event-stream"})


def _decode_object_path(value: str) -> str:
    return unquote(value)


def _path_metadata(payload: dict[str, Any]) -> dict[str, Any]:
    path = str(payload["path"])
    size = int(payload.get("size_bytes", 0))
    updated = payload.get("updated_at_unix_s") or payload.get("created_at_unix_s") or 0
    return {
        "contentIdentifier": {
            "relativePath": path,
        },
        "sizeBytes": size,
        "lastUpdatedAt": _unix_to_iso(float(updated)),
        "packetStoat": {
            "sha256": payload.get("sha256", ""),
            "contentType": payload.get("content_type", "application/octet-stream"),
        },
    }


def _unix_to_iso(value: float) -> str:
    from datetime import datetime, timezone

    return datetime.fromtimestamp(value, timezone.utc).isoformat().replace("+00:00", "Z")


def _agent_id_from_task_payload(payload: dict[str, Any]) -> str:
    relations = payload.get("relations")
    if isinstance(relations, dict):
        assignee = relations.get("assignee") or relations.get("assignedTo")
        if isinstance(assignee, dict):
            return str(assignee.get("entityId") or assignee.get("id") or "packet-stoat")
    return "packet-stoat"


def _status_from_task_status_payload(payload: Any) -> str:
    if isinstance(payload, str):
        return payload.lower().removeprefix("status_")
    if isinstance(payload, dict):
        value = payload.get("status") or payload.get("state") or payload.get("name")
        if value is not None:
            return str(value).lower().removeprefix("status_")
    return "in_progress"


def _task_payload(harness: MockLatticeRestHarness, task_id: str, result: dict[str, Any] | None = None) -> dict[str, Any]:
    rows = [row for row in harness.shim.list_tasks() if row["task_id"] == task_id]
    if not rows:
        raise KeyError(f"task not found: {task_id}")
    row = rows[0]
    return {
        "taskId": row["task_id"],
        "description": row["payload"].get("description"),
        "displayName": row["payload"].get("displayName") or row["task_type"],
        "status": {
            "status": row["status"],
        },
        "packetStoat": {
            "agentId": row["agent_id"],
            "result": result or {},
        },
    }


__all__ = [
    "OfflineClientConfig",
    "build_official_lattice_client",
    "build_offline_httpx_client",
    "build_sdk_mock_transport",
    "offline_client_config_from_env",
]
