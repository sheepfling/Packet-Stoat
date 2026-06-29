from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
import sys

import httpx


ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = ROOT / "tools"
ADAPTER_SRC = ROOT / "packages" / "lattice" / "src"
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
)


def _headers() -> dict[str, str]:
    return {
        "Authorization": "Bearer mock-environment-token",
        "Anduril-Sandbox-Authorization": "Bearer mock-sandbox-token",
    }


def _rows() -> list[dict[str, object]]:
    return mapping_plan.build_plan()["records"]


@lru_cache(maxsize=None)
def _fixture_json(path_str: str) -> dict[str, object]:
    return json.loads((ROOT / path_str).read_text(encoding="utf-8"))


def _has_entity_fixture(path_str: str) -> bool:
    payload = _fixture_json(path_str)
    return "entityId" in payload


def _has_task_fixture(path_str: str) -> bool:
    payload = _fixture_json(path_str)
    return isinstance(payload.get("tasks"), list)


def _has_object_fixture(path_str: str) -> bool:
    payload = _fixture_json(path_str)
    return isinstance(payload.get("objects"), list)


def _exercise_entity_fixture(path_str: str) -> None:
    path = ROOT / path_str
    if path.name == "lattice_track_fixture.json":
        packet = entity_state_packet_from_fixture(path)
        header = parse_header(packet, strict=True)
        assert header is not None
        return
    if path.name == "dis_entity_fixture.json":
        assert canonical_entity_from_fixture(path)
        return
    payload = _fixture_json(path_str)
    harness = MockLatticeRestHarness()
    transport = build_sdk_mock_transport(harness)
    with httpx.Client(transport=transport, base_url="http://lattice.mock", headers=_headers()) as client:
        published = client.put("/api/v1/entities", json=payload)
        fetched = client.get(f"/api/v1/entities/{payload['entityId']}")
    assert published.status_code == 200
    assert fetched.status_code == 200


def _exercise_task_fixture(path_str: str) -> None:
    payload = _fixture_json(path_str)
    shim = MockLatticeShim()
    for task in payload["tasks"]:
        shim.create_task(task)
    assert len(shim.stream_tasks()) == len(payload["tasks"])


def _exercise_object_fixture(path_str: str) -> None:
    payload = _fixture_json(path_str)
    harness = MockLatticeRestHarness()
    transport = build_sdk_mock_transport(harness)
    with httpx.Client(transport=transport, base_url="http://lattice.mock", headers=_headers()) as client:
        for obj in payload["objects"]:
            content = str(obj["content"]).encode("utf-8")
            uploaded = client.post(
                f"/api/v1/objects/{obj['path']}",
                content=content,
                headers={"content-type": str(obj["content_type"]), **_headers()},
            )
            downloaded = client.get(f"/api/v1/objects/{obj['path']}")
            assert uploaded.status_code == 200
            assert downloaded.status_code == 200
            assert downloaded.content == content


def test_every_row_has_transport_contract_consistent_with_its_fixtures() -> None:
    for row in _rows():
        fixture_paths = list(row["proof_fixtures"])
        has_entity = any(_has_entity_fixture(path) for path in fixture_paths)
        has_task = any(_has_task_fixture(path) for path in fixture_paths)
        has_object = any(_has_object_fixture(path) for path in fixture_paths)

        rest_surface_kinds = set(row["rest_surface_kinds"])
        grpc_surface_kind = str(row["grpc_surface_kind"])
        protocol_availability = str(row["protocol_availability"])
        egress_conformance = str(row["egress_conformance"])
        proof_modes = set(row["proof_modes"])

        if "entities" in rest_surface_kinds and str(row["strict_lattice_bucket"]) == "Entity":
            assert has_entity, row
        if "tasks" in rest_surface_kinds and str(row["strict_lattice_bucket"]) == "Task":
            assert has_task, row
        if "objects" in rest_surface_kinds and (
            str(row["strict_lattice_bucket"]) == "Object" or "raw_sidecar_preservation" in proof_modes
        ):
            assert has_object, row

        if grpc_surface_kind == "entities":
            assert protocol_availability == "rest_and_grpc", row
            assert has_entity, row
        elif grpc_surface_kind == "tasks":
            assert protocol_availability == "rest_and_grpc", row
            assert has_task, row
        elif grpc_surface_kind == "generic":
            assert protocol_availability in {"rest_only", "rest_and_grpc"}, row

        if egress_conformance == "structured":
            assert "entity_roundtrip" in proof_modes or "entity_publish_get_stream" in proof_modes, row
        elif egress_conformance == "raw_required":
            assert "raw_sidecar_preservation" in proof_modes, row
            assert has_object, row
        elif egress_conformance == "diagnostic":
            assert proof_modes & {"entity_projection_contract", "task_fixture_contract", "object_fixture_contract"}, row


def test_unique_fixture_surfaces_are_transport_executable() -> None:
    rows = _rows()
    entity_paths = sorted({path for row in rows for path in row["proof_fixtures"] if _has_entity_fixture(path)})
    task_paths = sorted({path for row in rows for path in row["proof_fixtures"] if _has_task_fixture(path)})
    object_paths = sorted({path for row in rows for path in row["proof_fixtures"] if _has_object_fixture(path)})

    assert entity_paths and task_paths and object_paths

    for path in entity_paths:
        _exercise_entity_fixture(path)
    for path in task_paths:
        _exercise_task_fixture(path)
    for path in object_paths:
        _exercise_object_fixture(path)
