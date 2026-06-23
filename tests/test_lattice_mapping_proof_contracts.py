from __future__ import annotations

import json
from functools import lru_cache
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
)


def _headers() -> dict[str, str]:
    return {
        "Authorization": "Bearer mock-environment-token",
        "Anduril-Sandbox-Authorization": "Bearer mock-sandbox-token",
    }


def _plan_rows() -> list[dict[str, object]]:
    return mapping_plan.build_plan()["records"]


@lru_cache(maxsize=None)
def _fixture_json(path_str: str) -> dict[str, object]:
    return json.loads((ROOT / path_str).read_text(encoding="utf-8"))


def _entity_projection_matches(row: dict[str, object], fixture_path: str) -> bool:
    fixture = _fixture_json(fixture_path)
    packet_stoat = fixture.get("packetStoat")
    if not isinstance(packet_stoat, dict):
        return False
    projection_kind = packet_stoat.get("projectionKind")
    if projection_kind == row["projected_public_payload_kind"]:
        return True
    return row["projected_public_payload_kind"] in {"track_entity", "entity_lifecycle_update"} and "entityId" in fixture


def _task_projection_matches(row: dict[str, object], fixture_path: str) -> bool:
    fixture = _fixture_json(fixture_path)
    tasks = fixture.get("tasks")
    if not isinstance(tasks, list):
        return False
    for task in tasks:
        packet_stoat = task.get("packetStoat")
        if isinstance(packet_stoat, dict) and packet_stoat.get("projectionKind") == row["projected_public_payload_kind"]:
            return True
    return False


def _object_projection_matches(row: dict[str, object], fixture_path: str) -> bool:
    fixture = _fixture_json(fixture_path)
    objects = fixture.get("objects")
    if not isinstance(objects, list):
        return False
    for obj in objects:
        packet_stoat = obj.get("packetStoat")
        if isinstance(packet_stoat, dict) and packet_stoat.get("projectionKind") == row["projected_public_payload_kind"]:
            return True
    return False


@lru_cache(maxsize=None)
def _validate_fixture_runtime(path_str: str) -> str:
    path = ROOT / path_str
    name = path.name

    if name == "dis_entity_fixture.json":
        entities = canonical_entity_from_fixture(path)
        assert entities
        return "dis_entity"

    if name == "lattice_track_fixture.json":
        packet = entity_state_packet_from_fixture(path)
        header = parse_header(packet, strict=True)
        assert header is not None
        assert header[2] == 1
        return "track_packet"

    payload = _fixture_json(path_str)
    if "entityId" in payload:
        harness = MockLatticeRestHarness()
        transport = build_sdk_mock_transport(harness)
        with httpx.Client(transport=transport, base_url="http://lattice.mock", headers=_headers()) as client:
            published = client.put("/api/v1/entities", json=payload)
            fetched = client.get(f"/api/v1/entities/{payload['entityId']}")
        assert published.status_code == 200
        assert fetched.status_code == 200
        return "entity"

    if isinstance(payload.get("tasks"), list):
        shim = MockLatticeShim()
        for task in payload["tasks"]:
            shim.create_task(task)
        streamed = shim.stream_tasks()
        assert len(streamed) == len(payload["tasks"])
        return "task"

    if isinstance(payload.get("objects"), list):
        harness = MockLatticeRestHarness()
        transport = build_sdk_mock_transport(harness)
        with httpx.Client(transport=transport, base_url="http://lattice.mock", headers=_headers()) as client:
            for obj in payload["objects"]:
                uploaded = client.post(
                    f"/api/v1/objects/{obj['path']}",
                    content=str(obj["content"]).encode("utf-8"),
                    headers={"content-type": str(obj["content_type"]), **_headers()},
                )
                downloaded = client.get(f"/api/v1/objects/{obj['path']}")
                assert uploaded.status_code == 200
                assert downloaded.status_code == 200
                assert downloaded.content == str(obj["content"]).encode("utf-8")
        return "object"

    raise AssertionError(f"unsupported fixture shape: {path_str}")


def test_every_row_declares_satisfiable_proof_contracts() -> None:
    rows = _plan_rows()

    for row in rows:
        fixture_paths = list(row["proof_fixtures"])
        assert fixture_paths

        if "entity_roundtrip" in row["proof_modes"]:
            names = {Path(path).name for path in fixture_paths}
            assert {"dis_entity_fixture.json", "lattice_track_fixture.json"} <= names

        if "entity_projection_contract" in row["proof_modes"]:
            assert any(_entity_projection_matches(row, path) for path in fixture_paths), row

        if "task_fixture_contract" in row["proof_modes"]:
            assert any(_task_projection_matches(row, path) for path in fixture_paths), row

        if "object_fixture_contract" in row["proof_modes"]:
            assert any(Path(path).name.endswith("object_fixture.json") or _object_projection_matches(row, path) for path in fixture_paths), row

        if "raw_sidecar_preservation" in row["proof_modes"]:
            assert any(_validate_fixture_runtime(path) == "object" for path in fixture_paths if "object" in Path(path).name or "attribute" in Path(path).name), row


def test_unique_mapping_fixtures_are_runtime_valid() -> None:
    rows = _plan_rows()
    fixture_paths = sorted({path for row in rows for path in row["proof_fixtures"]})
    results = {_validate_fixture_runtime(path) for path in fixture_paths}

    assert {"dis_entity", "track_packet", "entity", "task", "object"} <= results
