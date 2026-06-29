from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ADAPTER_SRC = ROOT / "packages" / "lattice" / "src"
if str(ADAPTER_SRC) not in sys.path:
    sys.path.insert(0, str(ADAPTER_SRC))

from packet_stoat_lattice import canonical_entity_from_fixture, lattice_track_payload_from_entity, publish_entities, start_grpc_shim_server, stream_entity_components  # noqa: E402


DIS_FIXTURE = ROOT / "packages" / "lattice" / "examples" / "dis_entity_fixture.json"


def test_lattice_grpc_stream_preexisting_and_deleted_events() -> None:
    server, target, _shim = start_grpc_shim_server()
    try:
        entity = canonical_entity_from_fixture(DIS_FIXTURE)[0]
        live_payload = lattice_track_payload_from_entity(entity)
        stale_payload = lattice_track_payload_from_entity(entity)
        stale_payload["stale"] = True
        stale_payload["isLive"] = False

        publish_entities(target, [live_payload, stale_payload])
        preexisting = stream_entity_components(target, preexisting_only=True, include_all_components=True)
        updates = stream_entity_components(target, include_all_components=True)

        assert preexisting[0]["event_type"] == "PREEXISTING"
        assert preexisting[-1]["event_type"] == "HEARTBEAT"
        assert any(event["event_type"] == "DELETED" for event in updates if event["entity_id"])
    finally:
        server.stop(0)
