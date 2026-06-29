from __future__ import annotations

from typing import Any, Mapping

from .auth import MockLatticeAuthService
from .mock_shim import MockLatticeShim


class MockLatticeRestHarness:
    def __init__(
        self,
        *,
        auth: MockLatticeAuthService | None = None,
        shim: MockLatticeShim | None = None,
    ) -> None:
        self.auth = auth or MockLatticeAuthService()
        self.shim = shim or MockLatticeShim()

    def oauth_token(
        self,
        *,
        client_id: str,
        client_secret: str,
        grant_type: str = "client_credentials",
        scope: str | None = None,
    ) -> dict[str, object]:
        return self.auth.oauth_token_response(
            client_id=client_id,
            client_secret=client_secret,
            grant_type=grant_type,
            scope=scope,
        )

    def publish_entity(self, payload: dict[str, Any], *, headers: Mapping[str, str]) -> dict[str, Any]:
        self.auth.validate_headers(headers, required_scope="entities")
        return self.shim.publish_entity(payload)

    def publish_entities(self, payloads: list[dict[str, Any]], *, headers: Mapping[str, str]) -> dict[str, Any]:
        self.auth.validate_headers(headers, required_scope="entities")
        return self.shim.publish_batch(payloads)

    def get_entity(self, entity_id: str, *, headers: Mapping[str, str]) -> dict[str, Any] | None:
        self.auth.validate_headers(headers, required_scope="entities")
        return self.shim.get_entity(entity_id)

    def stream_entities(
        self,
        *,
        headers: Mapping[str, str],
        components_to_include: list[str] | None = None,
        heartbeat_interval_ms: int = 1000,
        pre_existing_only: bool = False,
    ) -> list[dict[str, Any]]:
        self.auth.validate_headers(headers, required_scope="streams")
        return self.shim.stream_entities(
            components_to_include=components_to_include,
            heartbeat_interval_ms=heartbeat_interval_ms,
            pre_existing_only=pre_existing_only,
        )

    def upload_object(
        self,
        path: str,
        content_type: str,
        content: bytes,
        *,
        headers: Mapping[str, str],
    ) -> dict[str, Any]:
        self.auth.validate_headers(headers, required_scope="objects")
        return self.shim.put_object(path, content_type, content)

    def get_object(self, path: str, *, headers: Mapping[str, str]) -> bytes | None:
        self.auth.validate_headers(headers, required_scope="objects")
        return self.shim.get_object(path)

    def get_object_metadata(self, path: str, *, headers: Mapping[str, str]) -> dict[str, Any] | None:
        self.auth.validate_headers(headers, required_scope="objects")
        return self.shim.get_object_metadata(path)

    def delete_object(self, path: str, *, headers: Mapping[str, str]) -> dict[str, Any]:
        self.auth.validate_headers(headers, required_scope="objects")
        return self.shim.delete_object(path)

    def list_objects(self, prefix: str = "", *, headers: Mapping[str, str]) -> list[dict[str, Any]]:
        self.auth.validate_headers(headers, required_scope="objects")
        return self.shim.list_objects(prefix)

    def link_object_to_entity_media(
        self,
        entity_id: str,
        object_path: str,
        *,
        headers: Mapping[str, str],
        label: str = "packet-stoat artifact",
    ) -> dict[str, Any]:
        self.auth.validate_headers(headers, required_scope="entities")
        return self.shim.link_object_to_entity_media(entity_id, object_path, label=label)

    def create_task(self, task: dict[str, Any], *, headers: Mapping[str, str]) -> dict[str, Any]:
        self.auth.validate_headers(headers, required_scope="tasks")
        return self.shim.create_task(task)

    def update_task_status(self, task_id: str, status: str, *, headers: Mapping[str, str]) -> dict[str, Any]:
        self.auth.validate_headers(headers, required_scope="tasks")
        return self.shim.update_task_status(task_id, status)

    def stream_tasks(self, *, headers: Mapping[str, str], agent_id: str | None = None) -> list[dict[str, Any]]:
        self.auth.validate_headers(headers, required_scope="tasks")
        return self.shim.stream_tasks(agent_id)


__all__ = ["MockLatticeRestHarness"]
