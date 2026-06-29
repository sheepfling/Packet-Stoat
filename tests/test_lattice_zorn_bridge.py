from __future__ import annotations

from pathlib import Path
import sys


TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import lattice_zorn_bridge


def test_load_canonical_entities_accepts_track_fixture() -> None:
    fixture = (
        Path(__file__).resolve().parents[1]
        / "packages"
        / "lattice"
        / "examples"
        / "lattice_track_fixture.json"
    )

    entities = lattice_zorn_bridge._load_canonical_entities(fixture)

    assert len(entities) == 1
    assert entities[0].entity_id.site == 100
    assert entities[0].entity_id.application == 1
    assert entities[0].entity_id.entity == 42
    assert entities[0].marking == "ALPHA4-01"


def test_evaluate_zorn_entity_events_reports_endpoint_readiness() -> None:
    ready = lattice_zorn_bridge._evaluate_zorn_entity_events(
        {
            "events": [
                {"eventType": "CREATE", "entity": {"entityId": "entity-1", "isLive": True}},
                {"eventType": "UPDATE", "entity": {"entityId": "entity-1", "isLive": True}},
                {"eventType": "DELETED", "entity": {"entityId": "entity-1", "isLive": False}},
            ]
        }
    )
    partial = lattice_zorn_bridge._evaluate_zorn_entity_events(
        {"events": [{"eventType": "CREATE", "entity": {"entityId": "entity-1", "isLive": True}}]}
    )
    failed = lattice_zorn_bridge._evaluate_zorn_entity_events({"events": []})

    assert ready["status"] == "ready"
    assert partial["status"] == "ready-with-gaps"
    assert partial["missing"] == ["entities.stream.create_update_order", "entities.stream.delete_or_non_live"]
    assert failed["status"] == "failed"


def test_canonical_to_zorn_dis_rows_emits_stream_lifecycle() -> None:
    fixture = (
        Path(__file__).resolve().parents[1]
        / "packages"
        / "lattice"
        / "examples"
        / "dis_entity_fixture.json"
    )

    entities = lattice_zorn_bridge._load_canonical_entities(fixture)
    rows = lattice_zorn_bridge._canonical_to_zorn_dis_rows(entities)

    assert len(rows) == 3
    assert rows[0]["is_live"] is True
    assert rows[1]["is_live"] is True
    assert rows[2]["is_live"] is False
    assert rows[0]["entity_id"] == rows[1]["entity_id"] == rows[2]["entity_id"]
