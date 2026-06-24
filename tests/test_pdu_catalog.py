from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import fastdis
from fastdis import catalog

ROOT = Path(__file__).resolve().parents[1]

EXPECTED_IMPLEMENTED_DECODERS = {
    "AcknowledgePdu",
    "AcknowledgeReliablePdu",
    "ActionRequestPdu",
    "ActionRequestReliablePdu",
    "ActionResponsePdu",
    "ActionResponseReliablePdu",
    "CollisionElasticPdu",
    "CollisionPdu",
    "CommentPdu",
    "CommentReliablePdu",
    "CreateEntityPdu",
    "CreateEntityReliablePdu",
    "DataPdu",
    "DataQueryPdu",
    "DataQueryReliablePdu",
    "DataReliablePdu",
    "DetonationPdu",
    "DesignatorPdu",
    "DirectedEnergyFirePdu",
    "ElectronicEmissionsPdu",
    "EntityStatePdu",
    "EntityDamageStatusPdu",
    "EntityStateUpdatePdu",
    "EventReportPdu",
    "EventReportReliablePdu",
    "FirePdu",
    "IffAtcNavAidsLayer1Pdu",
    "IffPdu",
    "AttributePdu",
    "InformationOperationsActionPdu",
    "InformationOperationsReportPdu",
    "IntercomSignalPdu",
    "IntercomControlPdu",
    "OtherPdu",
    "AggregateStatePdu",
    "IsGroupOfPdu",
    "TransferControlRequestPdu",
    "TransferOwnershipPdu",
    "IsPartOfPdu",
    "MinefieldStatePdu",
    "MinefieldQueryPdu",
    "MinefieldDataPdu",
    "MinefieldResponseNackPdu",
    "EnvironmentalProcessPdu",
    "GriddedDataPdu",
    "PointObjectStatePdu",
    "LinearObjectStatePdu",
    "ArealObjectStatePdu",
    "TSPIPdu",
    "AppearancePdu",
    "ArticulatedPartsPdu",
    "LEFirePdu",
    "LEDetonationPdu",
    "RecordQueryReliablePdu",
    "RecordReliablePdu",
    "RepairCompletePdu",
    "RepairResponsePdu",
    "ReceiverPdu",
    "RemoveEntityPdu",
    "RemoveEntityReliablePdu",
    "ResupplyCancelPdu",
    "ResupplyOfferPdu",
    "ResupplyReceivedPdu",
    "SeesPdu",
    "ServiceRequestPdu",
    "SetRecordReliablePdu",
    "SetDataPdu",
    "SetDataReliablePdu",
    "SignalPdu",
    "StartResumePdu",
    "StartResumeReliablePdu",
    "StopFreezePdu",
    "StopFreezeReliablePdu",
    "TransmitterPdu",
    "UaPdu",
}


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
    assert len(fastdis.PDU_CATALOG) == 141
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


def test_fire_is_known_and_implemented() -> None:
    entry = fastdis.find_pdu(7, 2)
    assert entry is not None
    assert entry.class_name == "FirePdu"
    assert entry.family_name == "Warfare"
    assert entry.has_body_decoder
    assert fastdis.body_decoder_available(7, 2)


def test_catalog_module_reports_families_and_decoders() -> None:
    families = catalog.supported_pdu_families()
    assert "Entity Information" in families
    assert "Warfare" in families
    implemented = [entry.class_name for entry in catalog.implemented_body_decoders()]
    assert len(implemented) == 141
    assert set(implemented) == EXPECTED_IMPLEMENTED_DECODERS


def test_cross_language_coverage_is_complete_and_honest() -> None:
    for entry in fastdis.MESSAGE_COVERAGE:
        assert entry.c_catalog
        assert entry.cpp_catalog
        assert entry.python_catalog
        assert entry.unreal_catalog
        assert entry.godot_catalog
        assert entry.unity_catalog

        if entry.class_name in EXPECTED_IMPLEMENTED_DECODERS:
            assert entry.c_body_decoder
            assert entry.cpp_body_decoder
            assert entry.python_body_decoder
            assert entry.unreal_adapter
            assert entry.godot_adapter
            assert entry.unity_adapter
        else:
            assert not entry.c_body_decoder
            assert not entry.cpp_body_decoder
            assert not entry.python_body_decoder
            assert not entry.unreal_adapter
            assert not entry.godot_adapter
            assert not entry.unity_adapter
        assert entry.cataloged
        assert entry.header_validated

        if entry.class_name in EXPECTED_IMPLEMENTED_DECODERS:
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

    create_entity = fastdis.find_message_coverage(7, 11)
    assert create_entity is not None
    assert create_entity.class_name == "CreateEntityPdu"
    assert create_entity.c_body_decoder

    start_resume = fastdis.find_message_coverage(7, 13)
    assert start_resume is not None
    assert start_resume.class_name == "StartResumePdu"
    assert start_resume.c_body_decoder

    acknowledge = fastdis.find_message_coverage(7, 15)
    assert acknowledge is not None
    assert acknowledge.class_name == "AcknowledgePdu"
    assert acknowledge.c_body_decoder

    create_entity_reliable = fastdis.find_message_coverage(7, 51)
    assert create_entity_reliable is not None
    assert create_entity_reliable.class_name == "CreateEntityReliablePdu"
    assert create_entity_reliable.c_body_decoder

    remove_entity_reliable = fastdis.find_message_coverage(7, 52)
    assert remove_entity_reliable is not None
    assert remove_entity_reliable.class_name == "RemoveEntityReliablePdu"
    assert remove_entity_reliable.c_body_decoder

    start_resume_reliable = fastdis.find_message_coverage(7, 53)
    assert start_resume_reliable is not None
    assert start_resume_reliable.class_name == "StartResumeReliablePdu"
    assert start_resume_reliable.c_body_decoder

    stop_freeze_reliable = fastdis.find_message_coverage(7, 54)
    assert stop_freeze_reliable is not None
    assert stop_freeze_reliable.class_name == "StopFreezeReliablePdu"
    assert stop_freeze_reliable.c_body_decoder

    acknowledge_reliable = fastdis.find_message_coverage(7, 55)
    assert acknowledge_reliable is not None
    assert acknowledge_reliable.class_name == "AcknowledgeReliablePdu"
    assert acknowledge_reliable.c_body_decoder

    fire = fastdis.find_message_coverage(7, 2)
    assert fire is not None
    assert fire.class_name == "FirePdu"
    assert fire.c_body_decoder

    detonation = fastdis.find_message_coverage(7, 3)
    assert detonation is not None
    assert detonation.class_name == "DetonationPdu"
    assert detonation.c_body_decoder

    collision = fastdis.find_message_coverage(7, 4)
    assert collision is not None
    assert collision.class_name == "CollisionPdu"
    assert collision.c_body_decoder

    collision_elastic = fastdis.find_message_coverage(7, 66)
    assert collision_elastic is not None
    assert collision_elastic.class_name == "CollisionElasticPdu"
    assert collision_elastic.c_body_decoder

    unsupported = fastdis.unsupported_body_decoders(7)
    assert fire not in unsupported
    assert detonation not in unsupported
    assert collision not in unsupported
    assert collision_elastic not in unsupported
    assert entity_state not in unsupported
    assert entity_state_update not in unsupported
    assert create_entity not in unsupported
    assert start_resume not in unsupported
    assert acknowledge not in unsupported
    assert create_entity_reliable not in unsupported
    assert remove_entity_reliable not in unsupported
    assert start_resume_reliable not in unsupported
    assert stop_freeze_reliable not in unsupported
    assert acknowledge_reliable not in unsupported


def test_generated_message_coverage_manifest_is_consistent() -> None:
    payload = json.loads(_ensure_message_coverage_manifest().read_text(encoding="utf-8"))
    assert payload["summary"]["records"] == len(fastdis.MESSAGE_COVERAGE)
    assert payload["summary"]["cataloged"] == len(fastdis.MESSAGE_COVERAGE)
    assert payload["summary"]["header_validated"] == len(fastdis.MESSAGE_COVERAGE)
    assert payload["summary"]["min_length_known"] == 141
    assert payload["summary"]["typed_prefix_parser"] == 141
    assert payload["summary"]["full_parser"] == len(fastdis.MESSAGE_COVERAGE)
    assert payload["summary"]["serializer"] == len(fastdis.MESSAGE_COVERAGE)
    assert payload["summary"]["roundtrip_tested"] == len(fastdis.MESSAGE_COVERAGE)
    assert payload["summary"]["fuzzed_deep"] == 141
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
