from __future__ import annotations

import fastdis
from fastdis import catalog


def test_generated_pdu_catalog_is_exposed() -> None:
    assert len(fastdis.PDU_CATALOG) == 114
    assert len(fastdis.MESSAGE_COVERAGE) == len(fastdis.PDU_CATALOG)
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


def test_cross_language_coverage_is_complete_and_honest() -> None:
    for entry in fastdis.MESSAGE_COVERAGE:
        assert entry.c_catalog
        assert entry.cpp_catalog
        assert entry.python_catalog
        assert entry.unreal_catalog
        assert entry.godot_catalog
        assert not entry.unity_catalog

        if entry.class_name == "EntityStatePdu":
            assert entry.c_body_decoder
            assert entry.cpp_body_decoder
            assert entry.python_body_decoder
            assert entry.unreal_adapter
            assert entry.godot_adapter
        else:
            assert not entry.c_body_decoder
            assert not entry.cpp_body_decoder
            assert not entry.python_body_decoder
            assert not entry.unreal_adapter
            assert not entry.godot_adapter
        assert not entry.unity_adapter


def test_message_coverage_helpers() -> None:
    entity_state = fastdis.find_message_coverage(7, 1)
    assert entity_state is not None
    assert entity_state.class_name == "EntityStatePdu"
    assert entity_state.c_body_decoder

    fire = fastdis.find_message_coverage(7, 2)
    assert fire is not None
    assert fire.class_name == "FirePdu"
    assert not fire.c_body_decoder

    unsupported = fastdis.unsupported_body_decoders(7)
    assert fire in unsupported
    assert entity_state not in unsupported
