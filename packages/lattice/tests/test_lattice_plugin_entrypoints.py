from __future__ import annotations

from packet_stoat_lattice.plugins import jsonl_publisher, mock_publisher, real_publisher, shim_stream


def test_lattice_plugin_factories_construct_without_credentials(tmp_path) -> None:
    assert jsonl_publisher(tmp_path / "payloads.jsonl").publish_entity({"entity_key": "1:2:3"})["status"] == "accepted"
    assert mock_publisher().publish_entity({"entity_key": "1:2:3"})["status"] == "accepted"
    assert real_publisher().publish_entity({"entity_key": "1:2:3"})["status"] == "dry-run"
    assert shim_stream().metrics()["entity_count"] == 0
