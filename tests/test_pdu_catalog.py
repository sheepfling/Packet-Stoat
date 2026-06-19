from __future__ import annotations

import fastdis
from fastdis import catalog


def test_generated_pdu_catalog_is_exposed() -> None:
    assert len(fastdis.PDU_CATALOG) == 114
    assert fastdis.known_pdu_types(6)
    assert fastdis.known_pdu_types(7)


def test_entity_state_is_known_and_implemented() -> None:
    entry = fastdis.find_pdu(7, 1)
    assert entry is not None
    assert entry.class_name == "EntityStatePdu"
    assert entry.protocol_family == 1
    assert entry.has_body_decoder
    assert fastdis.body_decoder_available(7, 1)


def test_fire_is_known_but_body_decoder_is_not_claimed() -> None:
    entry = fastdis.find_pdu(7, 2)
    assert entry is not None
    assert entry.class_name == "FirePdu"
    assert entry.family_name == "Warfare"
    assert not entry.has_body_decoder
    assert not fastdis.body_decoder_available(7, 2)


def test_catalog_module_reports_families_and_decoders() -> None:
    families = catalog.supported_pdu_families()
    assert "Entity Information" in families
    assert "Warfare" in families
    assert [entry.class_name for entry in catalog.implemented_body_decoders()] == [
        "EntityStatePdu",
        "EntityStatePdu",
    ]
