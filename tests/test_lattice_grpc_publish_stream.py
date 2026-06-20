from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ADAPTER_SRC = ROOT / "integrations" / "lattice" / "src"
if str(ADAPTER_SRC) not in sys.path:
    sys.path.insert(0, str(ADAPTER_SRC))

from packet_stoat_lattice import (  # noqa: E402
    canonical_entity_from_fixture,
    lattice_track_payload_from_entity,
    publish_entities,
    start_grpc_shim_server,
    stream_entity_components,
)


DIS_FIXTURE = ROOT / "integrations" / "lattice" / "examples" / "dis_entity_fixture.json"


def test_lattice_grpc_publish_and_stream_roundtrip_contract() -> None:
    server, target, shim = start_grpc_shim_server()
    try:
        entity = canonical_entity_from_fixture(DIS_FIXTURE)[0]
        payloads = [lattice_track_payload_from_entity(entity)]

        summary = publish_entities(target, payloads)
        events = stream_entity_components(
            target,
            components_to_include=["location", "provenance", "aliases", "ontology", "milView"],
            heartbeat_period_millis=250,
        )

        assert summary["received"] == 1
        assert summary["accepted"] == 1
        assert shim.metrics()["entity_count"] == 1
        assert events[0]["event_type"] == "UPDATE"
        assert "location" in events[0]["payload"]
        assert "pose" not in events[0]["payload"]
        assert events[-1]["event_type"] == "HEARTBEAT"
    finally:
        server.stop(0)
