from __future__ import annotations

import sys
from pathlib import Path
from typing import cast

import grpc
import pytest


ROOT = Path(__file__).resolve().parents[1]
ADAPTER_SRC = ROOT / "packages" / "lattice" / "src"
if str(ADAPTER_SRC) not in sys.path:
    sys.path.insert(0, str(ADAPTER_SRC))

from packet_stoat_lattice import (  # noqa: E402
    MockLatticeAuthService,
    canonical_entity_from_fixture,
    inspect_official_grpc_surface,
    lattice_track_payload_from_entity,
    publish_entities,
    start_grpc_shim_server,
    stream_entity_components,
)


DIS_FIXTURE = ROOT / "packages" / "lattice" / "examples" / "dis_entity_fixture.json"


def _metadata(auth_service: MockLatticeAuthService) -> list[tuple[str, str]]:
    token = auth_service.issue_client_credentials_token("packet-stoat-client", "packet-stoat-secret")
    return [
        ("authorization", f"Bearer {token.access_token}"),
        ("anduril-sandbox-authorization", f"Bearer {auth_service.config.sandbox_token}"),
    ]


def test_lattice_grpc_mock_accepts_auth_metadata_handshake() -> None:
    auth_service = MockLatticeAuthService()
    server, target, shim = start_grpc_shim_server(auth_service=auth_service, require_auth=True)
    try:
        entity = canonical_entity_from_fixture(DIS_FIXTURE)[0]
        payload = lattice_track_payload_from_entity(entity)
        summary = publish_entities(target, [payload], metadata=_metadata(auth_service))
        events = stream_entity_components(target, components_to_include=["aliases"], metadata=_metadata(auth_service))

        assert summary["accepted"] == 1
        assert shim.metrics()["entity_count"] == 1
        assert events[0]["event_type"] == "UPDATE"
        assert "aliases" in cast(dict[str, object], events[0]["payload"])
    finally:
        server.stop(0)


def test_lattice_grpc_mock_rejects_missing_auth_metadata_when_required() -> None:
    auth_service = MockLatticeAuthService()
    server, target, _shim = start_grpc_shim_server(auth_service=auth_service, require_auth=True)
    try:
        entity = canonical_entity_from_fixture(DIS_FIXTURE)[0]
        payload = lattice_track_payload_from_entity(entity)

        with pytest.raises(grpc.RpcError) as exc_info:
            publish_entities(target, [payload])

        assert exc_info.value.code() == grpc.StatusCode.PERMISSION_DENIED

        with pytest.raises(grpc.RpcError) as missing_bearer:
            publish_entities(
                target,
                [payload],
                metadata=[("anduril-sandbox-authorization", f"Bearer {auth_service.config.sandbox_token}")],
            )

        assert missing_bearer.value.code() == grpc.StatusCode.UNAUTHENTICATED
    finally:
        server.stop(0)


def test_lattice_official_buf_surface_probe_is_safe_without_stubs() -> None:
    report = inspect_official_grpc_surface()

    assert report["status"] in {"passed", "skipped"}
    assert report["source"] == "buf.build/anduril/lattice-sdk/sdks/main:grpc/python"
    assert "EntityManagerAPIStub" in report["required_service_symbols"]
    assert "PublishEntitiesRequest" in report["required_message_symbols"]
