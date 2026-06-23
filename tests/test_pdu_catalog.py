from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import fastdis
from fastdis import catalog

ROOT = Path(__file__).resolve().parents[1]


def _ensure_message_coverage_manifest() -> Path:
    path = ROOT / "generated" / "message_coverage_manifest.json"
    if path.exists():
        return path
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "generate_pdu_catalog.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return path


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
        "EntityStateUpdatePdu",
        "EntityStatePdu",
        "EntityStateUpdatePdu",
    ]


def test_cross_language_coverage_is_complete_and_honest() -> None:
    for entry in fastdis.MESSAGE_COVERAGE:
        assert entry.c_catalog
        assert entry.cpp_catalog
        assert entry.python_catalog
        assert entry.unreal_catalog
        assert entry.godot_catalog
        assert not entry.unity_catalog

        if entry.class_name in {"EntityStatePdu", "EntityStateUpdatePdu"}:
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
        assert entry.cataloged
        assert entry.header_validated

        if entry.class_name in {"EntityStatePdu", "EntityStateUpdatePdu"}:
            assert entry.min_length_known
            assert entry.typed_prefix_parser
            assert entry.fuzzed_deep
        else:
            assert not entry.min_length_known
            assert not entry.typed_prefix_parser
            assert not entry.fuzzed_deep
        assert entry.full_parser
        assert entry.serializer
        assert entry.roundtrip_tested
        assert entry.fuzzed_shallow
        if entry.class_name == "EntityStatePdu":
            assert entry.differential_oracle == "open-dis-python fixture report"
        else:
            assert entry.differential_oracle is None


def test_message_coverage_helpers() -> None:
    entity_state = fastdis.find_message_coverage(7, 1)
    assert entity_state is not None
    assert entity_state.class_name == "EntityStatePdu"
    assert entity_state.c_body_decoder
    entity_state_update = fastdis.find_message_coverage(7, 67)
    assert entity_state_update is not None
    assert entity_state_update.class_name == "EntityStateUpdatePdu"
    assert entity_state_update.c_body_decoder

    fire = fastdis.find_message_coverage(7, 2)
    assert fire is not None
    assert fire.class_name == "FirePdu"
    assert not fire.c_body_decoder

    unsupported = fastdis.unsupported_body_decoders(7)
    assert fire in unsupported
    assert entity_state not in unsupported
    assert entity_state_update not in unsupported


def test_generated_message_coverage_manifest_is_consistent() -> None:
    payload = json.loads(_ensure_message_coverage_manifest().read_text(encoding="utf-8"))
    assert payload["summary"]["records"] == len(fastdis.MESSAGE_COVERAGE)
    assert payload["summary"]["cataloged"] == len(fastdis.MESSAGE_COVERAGE)
    assert payload["summary"]["header_validated"] == len(fastdis.MESSAGE_COVERAGE)
    assert payload["summary"]["min_length_known"] == 4
    assert payload["summary"]["typed_prefix_parser"] == 4
    assert payload["summary"]["full_parser"] == len(fastdis.MESSAGE_COVERAGE)
    assert payload["summary"]["serializer"] == len(fastdis.MESSAGE_COVERAGE)
    assert payload["summary"]["roundtrip_tested"] == len(fastdis.MESSAGE_COVERAGE)
    assert payload["summary"]["fuzzed_deep"] == 4
    assert payload["summary"]["fuzzed_shallow"] == len(fastdis.MESSAGE_COVERAGE)


def test_generate_pdu_catalog_check_passes_for_current_tree() -> None:
    _ensure_message_coverage_manifest()
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "generate_pdu_catalog.py"), "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
