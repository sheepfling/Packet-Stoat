from __future__ import annotations

import json
import math

import pytest

import fastdis
from fastdis.packet_json import (
    entity_state_packet_from_json,
    entity_state_packet_to_json,
    packet_from_json_record,
    packet_to_json_record,
)
from fastdis.tools._shared import EntityStateSpec, make_entity_state_packet


def test_packet_json_lossless_roundtrip_preserves_bytes() -> None:
    packet = make_entity_state_packet(EntityStateSpec(site=10, application=20, entity=30, marking="JSONTEST"))

    record = packet_to_json_record(packet, decode_level="semantic", raw_policy="include")
    rebuilt = packet_from_json_record(record)

    assert rebuilt == packet
    assert record["fastdis_schema"] == "fastdis.packet.v1"
    assert record["header"]["pdu_name"] == "Entity State"  # pyright: ignore[reportIndexIssue]
    assert record["support"]["typed_parser"] is True  # pyright: ignore[reportIndexIssue]


def test_packet_json_raw_validation_rejects_mismatched_sha() -> None:
    packet = make_entity_state_packet(EntityStateSpec())
    record = packet_to_json_record(packet, raw_policy="include")
    record["packet"]["sha256"] = "0" * 64  # pyright: ignore[reportIndexIssue]

    with pytest.raises(ValueError, match="sha256"):
        packet_from_json_record(record)


def test_entity_state_editable_json_rebuilds_packet() -> None:
    payload = {
        "fastdis_schema": "fastdis.pdu.entity_state.v1",
        "target_dis_version": 7,
        "header": {
            "protocol_version": 7,
            "exercise_id": 4,
            "pdu_type": 1,
            "protocol_family": 1,
            "timestamp": 123456,
        },
        "entity_state": {
            "entity_id": {"site": 100, "application": 2, "entity": 42},
            "force_id": 1,
            "entity_type": [1, 2, 840, 3, 4, 5, 6],
            "location_ecef_m": {"x": -123.0, "y": 456.0, "z": 789.0},
            "orientation_rad": {"psi": 0.1, "theta": 0.2, "phi": 0.3},
            "linear_velocity_mps": {"x": 10.0, "y": 0.0, "z": 0.0},
            "marking": "EDITJSON",
        },
    }

    packet = entity_state_packet_from_json(payload)
    entity = fastdis.canonical_entity_from_entity_state_packet(packet)

    assert entity.entity_id.site == 100
    assert entity.entity_id.application == 2
    assert entity.entity_id.entity == 42
    assert entity.marking == "EDITJSON"
    assert entity.location_ecef_m == (-123.0, 456.0, 789.0)
    assert entity.velocity_mps == (10.0, 0.0, 0.0)
    assert math.isclose(entity.orientation_dis_deg[0], math.degrees(0.1), rel_tol=1e-6)


def test_entity_state_to_editable_json_can_be_rebuilt_without_raw() -> None:
    packet = make_entity_state_packet(EntityStateSpec(site=3, application=4, entity=5, marking="EDITABLE"))
    payload = entity_state_packet_to_json(packet)

    rebuilt = packet_from_json_record(payload, prefer_raw=False)
    entity = fastdis.canonical_entity_from_entity_state_packet(rebuilt)

    assert entity.entity_id.site == 3
    assert entity.entity_id.application == 4
    assert entity.entity_id.entity == 5
    assert entity.marking == "EDITABLE"


def test_pdu_json_cli_roundtrip(tmp_path) -> None:
    from fastdis.tools import pdu_json

    packet_path = tmp_path / "packet.bin"
    json_path = tmp_path / "packet.json"
    rebuilt_path = tmp_path / "rebuilt.bin"
    packet = make_entity_state_packet(EntityStateSpec(entity=77))
    packet_path.write_bytes(packet)

    assert pdu_json.main(["to-json", str(packet_path), "--out", str(json_path)]) == 0
    assert json.loads(json_path.read_text(encoding="utf-8"))["fastdis_schema"] == "fastdis.packet.v1"
    assert pdu_json.main(["from-json", str(json_path), "--out", str(rebuilt_path)]) == 0

    assert rebuilt_path.read_bytes() == packet
