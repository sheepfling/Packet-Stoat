from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import generate_endpoint_mapping_manifest as endpoint_manifest
from generate_pdu_catalog import PduRecord


def _record(pdu_type: int, class_name: str) -> PduRecord:
    return PduRecord(
        protocol_version=7,
        pdu_type=pdu_type,
        protocol_family=1,
        class_name=class_name,
        name=class_name.removesuffix("Pdu"),
        family_name="Test",
        body_decoder=False,
    )


def test_known_pdu_endpoint_behaviors_are_never_invisible() -> None:
    payload = endpoint_manifest.build_payload(
        [
            _record(1, "EntityStatePdu"),
            _record(23, "ElectronicEmissionsPdu"),
            _record(51, "CreateEntityReliablePdu"),
            _record(68, "DirectedEnergyFirePdu"),
            _record(255, "ExperimentalPdu"),
        ]
    )

    assert payload["summary"]["missing_endpoint_behavior"] == 0
    for row in payload["records"]:
        for endpoint in ("python", "unreal", "godot", "lattice_lab"):
            assert row[endpoint]["behavior"] != "none"


def test_endpoint_manifest_promotes_generic_endpoint_categories() -> None:
    communication = endpoint_manifest.record_mapping(_record(23, "ElectronicEmissionsPdu"))
    sim_control = endpoint_manifest.record_mapping(_record(51, "CreateEntityReliablePdu"))
    event = endpoint_manifest.record_mapping(_record(68, "DirectedEnergyFirePdu"))

    assert communication["support_level"] == "cataloged_generic_endpoint"
    assert communication["lattice_lab"]["behavior"] == "communication_event"
    assert sim_control["support_level"] == "cataloged_generic_endpoint"
    assert sim_control["lattice_lab"]["behavior"] == "simulation_control_event"
    assert event["support_level"] == "cataloged_generic_endpoint"
    assert event["lattice_lab"]["behavior"] == "simulation_event"
