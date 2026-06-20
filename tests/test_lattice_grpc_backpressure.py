from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ADAPTER_SRC = ROOT / "integrations" / "lattice" / "src"
if str(ADAPTER_SRC) not in sys.path:
    sys.path.insert(0, str(ADAPTER_SRC))

from packet_stoat_lattice import canonical_entity_from_fixture, lattice_track_payload_from_entity, publish_entities, start_grpc_shim_server, stream_entity_components  # noqa: E402


DIS_FIXTURE = ROOT / "integrations" / "lattice" / "examples" / "dis_entity_fixture.json"


def test_lattice_grpc_publish_coalesces_repeated_entities() -> None:
    server, target, shim = start_grpc_shim_server()
    try:
        entity = canonical_entity_from_fixture(DIS_FIXTURE)[0]
        payloads = []
        for index in range(5):
            payload = lattice_track_payload_from_entity(entity)
            payload["timestamp"] = int(payload["timestamp"]) + index
            payloads.append(payload)

        summary = publish_entities(target, payloads)

        assert summary["received"] == 5
        assert summary["accepted"] == 5
        assert summary["coalesced"] >= 4
        assert shim.metrics()["entity_count"] == 1
    finally:
        server.stop(0)


def test_lattice_grpc_publish_soak_contract() -> None:
    server, target, shim = start_grpc_shim_server()
    try:
        entity = canonical_entity_from_fixture(DIS_FIXTURE)[0]
        payloads = []
        for entity_index in range(50):
            for update_index in range(10):
                payload = lattice_track_payload_from_entity(entity)
                payload["entity_key"] = f"100:1:{1000 + entity_index}"
                payload["entityId"] = f"packet-stoat:dis:v7:ex7:site100:app1:entity{1000 + entity_index}"
                payload["packetStoat"]["dis"]["entityId"] = 1000 + entity_index
                payload["marking"] = f"SOAK-{entity_index:02d}"
                payload["aliases"]["name"] = payload["marking"]
                payload["timestamp"] = 10_000 + update_index
                payloads.append(payload)

        summary = publish_entities(target, payloads)

        assert summary["received"] == 500
        assert summary["accepted"] == 500
        assert shim.metrics()["entity_count"] == 50
        assert summary["coalesced"] >= 450
    finally:
        server.stop(0)


def test_lattice_grpc_stream_rate_limit_suppresses_flooding() -> None:
    server, target, _shim = start_grpc_shim_server()
    try:
        entity = canonical_entity_from_fixture(DIS_FIXTURE)[0]
        payloads = []
        for index in range(5):
            payload = lattice_track_payload_from_entity(entity)
            payload["timestamp"] = 1000 + index
            payloads.append(payload)
        publish_entities(target, payloads)

        unrestricted = stream_entity_components(target, include_all_components=True, update_per_entity_limit_ms=0)
        throttled = stream_entity_components(target, include_all_components=True, update_per_entity_limit_ms=10)

        unrestricted_updates = [event for event in unrestricted if event["event_type"] == "UPDATE"]
        throttled_updates = [event for event in throttled if event["event_type"] == "UPDATE"]
        assert len(throttled_updates) < len(unrestricted_updates)
    finally:
        server.stop(0)
