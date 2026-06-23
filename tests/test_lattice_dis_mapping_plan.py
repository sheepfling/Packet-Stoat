from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = ROOT / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import generate_lattice_dis_mapping_plan as mapping_plan


def test_lattice_dis_mapping_plan_covers_all_141_rows() -> None:
    plan = mapping_plan.build_plan()

    assert plan["summary"]["records"] == 141
    assert len(plan["records"]) == 141
    assert all(row["strict_lattice_bucket"] in {"Entity", "Task", "Object"} for row in plan["records"])
    assert all(row["lattice_subtype"] for row in plan["records"])
    assert all(row["ingress_mapping"] for row in plan["records"])
    assert all(row["egress_mapping"] for row in plan["records"])
    assert all(row["loss_policy"] for row in plan["records"])
    assert all(row["rest_surface_kinds"] for row in plan["records"])
    assert all(row["grpc_surface_kind"] for row in plan["records"])
    assert all(row["egress_conformance"] for row in plan["records"])
    assert all(isinstance(row["lossy_ingress_supported"], bool) for row in plan["records"])
    assert all(isinstance(row["lossy_egress_supported"], bool) for row in plan["records"])
    assert all(row["lossy_ingress_policy"] for row in plan["records"])
    assert all(row["lossy_egress_policy"] for row in plan["records"])
    assert all(row["lossy_mode_class"] in {"strict_only", "ingress_only", "bidirectional"} for row in plan["records"])
    assert all(row["closest_public_surface"] in {"entity", "task", "object", "none"} for row in plan["records"])
    assert all(row["surface_confidence"] in {"direct", "projected", "archive_only"} for row in plan["records"])
    assert all(row["protocol_availability"] in {"rest_only", "rest_and_grpc", "none"} for row in plan["records"])
    assert all(row["fallback_mode"] in {"lossless", "projected", "observe_only", "archive_only", "drop_with_receipt"} for row in plan["records"])
    assert all(isinstance(row["research_basis"], list) and row["research_basis"] for row in plan["records"])
    assert all(isinstance(row["candidate_public_components"], list) and row["candidate_public_components"] for row in plan["records"])
    assert all(row["payload_projection"] for row in plan["records"])
    assert all(isinstance(row["transport_constraints"], list) and row["transport_constraints"] for row in plan["records"])
    assert all(isinstance(row["proof_modes"], list) and row["proof_modes"] for row in plan["records"])
    assert all(isinstance(row["proof_fixtures"], list) and row["proof_fixtures"] for row in plan["records"])
    assert all(
        row["proof_depth"] in {
            "lossless_roundtrip_runtime",
            "archive_preservation_runtime",
            "semantic_egress_runtime",
            "transport_egress_runtime",
        }
        for row in plan["records"]
    )
    assert all(row["projected_public_payload_kind"] for row in plan["records"])
    assert all(row["why_not_lossless"] for row in plan["records"])
    assert all(row["why_not_lossless_code"] in {"none", "component_subset_only", "dis7_only_target_gap", "event_model_gap", "no_public_relationship_schema", "raw_artifact_source_of_truth", "task_schema_gap"} for row in plan["records"])


def test_lattice_dis_mapping_plan_has_core_strict_buckets_and_targets() -> None:
    plan = mapping_plan.build_plan()
    buckets = plan["summary"]["strict_lattice_buckets"]
    subtypes = plan["summary"]["lattice_subtypes"]
    targets = plan["summary"]["observation_reduction_targets"]
    loss_policies = plan["summary"]["loss_policies"]
    lossy_classes = plan["summary"]["lossy_mode_classes"]
    lossy_ingress = plan["summary"]["lossy_ingress_support"]
    lossy_egress = plan["summary"]["lossy_egress_support"]
    public_surfaces = plan["summary"]["closest_public_surfaces"]
    confidence = plan["summary"]["surface_confidence"]
    fallbacks = plan["summary"]["fallback_modes"]
    proof_depth = plan["summary"]["proof_depth"]

    assert buckets == {"Entity": 42, "Object": 21, "Task": 78}
    assert subtypes["Entity"] == 2
    assert subtypes["ObjectArtifact"] == 2
    assert subtypes["TaskOrControlEvent"] >= 20
    assert subtypes["SimulationEvent"] >= 10
    assert targets == []
    assert loss_policies["preserve_raw_required_for_lossless_egress"] == 72
    assert "lossy_without_raw" not in loss_policies
    assert lossy_classes == {"bidirectional": 59, "ingress_only": 78, "strict_only": 4}
    assert lossy_ingress == {"strict_only": 4, "supported": 137}
    assert lossy_egress == {"strict_only": 82, "supported": 59}
    assert public_surfaces == {"entity": 60, "object": 3, "task": 78}
    assert confidence == {"direct": 4, "projected": 137}
    assert fallbacks == {"archive_only": 2, "lossless": 2, "observe_only": 35, "projected": 102}
    assert proof_depth == {
        "lossless_roundtrip_runtime": 2,
        "archive_preservation_runtime": 3,
        "semantic_egress_runtime": 136,
        "transport_egress_runtime": 0,
    }
    projection_kinds = plan["summary"]["projection_kinds"]
    non_lossless = plan["summary"]["non_lossless_reasons"]
    assert projection_kinds["track_entity"] == 2
    assert projection_kinds["entity_create_projection"] == 2
    assert projection_kinds["entity_remove_projection"] == 2
    assert projection_kinds["entity_state_update_projection"] == 2
    assert projection_kinds["task_lifecycle_control"] == 8
    assert projection_kinds["geo_entity_hazard_region"] == 2
    assert projection_kinds["signal_of_interest_entity"] >= 4
    assert projection_kinds["task_ack_projection"] == 2
    assert projection_kinds["task_ack_reliable_projection"] == 2
    assert projection_kinds["task_action_request_projection"] == 4
    assert projection_kinds["task_action_response_projection"] == 4
    assert projection_kinds["task_set_data_projection"] == 4
    assert projection_kinds["task_data_payload_projection"] == 4
    assert projection_kinds["task_data_query_projection"] == 4
    assert projection_kinds["task_comment_projection"] == 4
    assert projection_kinds["task_entity_damage_event"] == 1
    assert projection_kinds["task_information_operation_action"] == 1
    assert projection_kinds["task_information_operation_report"] == 1
    assert projection_kinds["task_record_reliable_projection"] == 2
    assert projection_kinds["task_set_record_projection"] == 2
    assert projection_kinds["task_record_query_projection"] == 2
    assert projection_kinds["task_resupply_offer_action"] == 2
    assert projection_kinds["task_resupply_received_action"] == 2
    assert projection_kinds["task_resupply_cancel_action"] == 2
    assert projection_kinds["task_repair_complete_action"] == 2
    assert projection_kinds["task_repair_response_action"] == 2
    assert projection_kinds["task_start_projection"] == 4
    assert projection_kinds["task_freeze_projection"] == 4
    assert projection_kinds["emission_sensor_entity"] == 2
    assert projection_kinds["designator_entity"] == 2
    assert projection_kinds["transmitter_entity"] == 2
    assert projection_kinds["receiver_entity"] == 2
    assert projection_kinds["entity_signal_annotation"] == 2
    assert projection_kinds["intercom_signal_annotation"] == 2
    assert projection_kinds["intercom_control_annotation"] == 2
    assert projection_kinds["entity_visual_state_annotation"] == 2
    assert projection_kinds["entity_articulation_annotation"] == 2
    assert projection_kinds["entity_aggregate_projection"] == 2
    assert projection_kinds["entity_group_membership_projection"] == 2
    assert projection_kinds["entity_part_relationship_projection"] == 2
    assert projection_kinds["task_le_fire_event"] == 2
    assert projection_kinds["task_directed_energy_fire_event"] == 1
    assert projection_kinds["task_le_detonation_event"] == 2
    assert projection_kinds["task_collision_elastic_event"] == 2
    assert projection_kinds["geo_grid_overlay"] == 2
    assert projection_kinds["geo_entity_polygon"] == 2
    assert projection_kinds["geo_minefield_query_overlay"] == 2
    assert projection_kinds["geo_minefield_data_overlay"] == 2
    assert projection_kinds["geo_minefield_response_nack"] == 2
    assert non_lossless["none"] == 2
    assert non_lossless["component_subset_only"] >= 40
    component_summary = {row["lattice_subtype"]: row for row in plan["summary"]["component_mapping_summary"]}
    assert component_summary["Entity"]["proof_modes"] == ["entity_roundtrip", "entity_publish_get_stream"]
    assert "geoShape" in component_summary["EnvironmentObservation"]["candidate_public_components"]
    assert "signal" in component_summary["CommunicationObservation"]["candidate_public_components"]
    assert component_summary["TaskOrControlEvent"]["proof_fixtures"] == ["integrations/lattice/examples/task_fixture.json"]
    assert component_summary["LogisticsObservation"]["proof_fixtures"] == [
        "integrations/lattice/examples/task_fixture.json",
        "integrations/lattice/examples/object_fixture.json",
    ]
    assert component_summary["CommunicationObservation"]["proof_fixtures"] == [
        "integrations/lattice/examples/lattice_signal_fixture.json",
        "integrations/lattice/examples/object_fixture.json",
    ]
    assert component_summary["EnvironmentObservation"]["proof_fixtures"] == [
        "integrations/lattice/examples/lattice_geo_fixture.json",
        "integrations/lattice/examples/object_fixture.json",
    ]


def test_lattice_dis_mapping_plan_validates_bucket_conformance() -> None:
    plan = mapping_plan.build_plan()
    issues = mapping_plan.validate_plan(plan)
    conformance = plan["summary"]["bucket_conformance"]

    assert issues == []
    assert conformance["Entity"]["rows"] == 42
    assert conformance["Task"]["rows"] == 78
    assert conformance["Object"]["rows"] == 21
    assert conformance["Entity"]["grpc_surface_kind_counts"] == {"entities": 16, "generic": 26}
    assert conformance["Task"]["grpc_surface_kind_counts"] == {"generic": 28, "tasks": 50}
    assert conformance["Object"]["grpc_surface_kind_counts"] == {"generic": 21}
    assert conformance["Entity"]["lossy_mode_class_counts"] == {"bidirectional": 6, "ingress_only": 34, "strict_only": 2}
    assert conformance["Task"]["lossy_mode_class_counts"] == {"bidirectional": 52, "ingress_only": 26}
    assert conformance["Object"]["lossy_mode_class_counts"] == {"bidirectional": 1, "ingress_only": 18, "strict_only": 2}
    assert conformance["Entity"]["closest_public_surface_counts"] == {"entity": 42}
    assert conformance["Task"]["closest_public_surface_counts"] == {"task": 78}
    assert conformance["Object"]["closest_public_surface_counts"] == {"entity": 18, "object": 3}
    assert conformance["Entity"]["fallback_mode_counts"] == {"lossless": 2, "observe_only": 6, "projected": 34}
    assert conformance["Task"]["fallback_mode_counts"] == {"observe_only": 28, "projected": 50}
    assert conformance["Object"]["fallback_mode_counts"] == {"archive_only": 2, "observe_only": 1, "projected": 18}


def test_lattice_dis_mapping_outputs_are_current() -> None:
    plan = mapping_plan.build_plan()
    expected_json = json.dumps(plan, indent=2, sort_keys=True) + "\n"
    expected_md = mapping_plan.render_markdown(plan)

    assert mapping_plan.JSON_OUT.read_text(encoding="utf-8") == expected_json
    assert mapping_plan.MD_OUT.read_text(encoding="utf-8") == expected_md


def test_dis6_version_twins_inherit_semantic_proof_when_projection_and_fixture_match() -> None:
    plan = mapping_plan.build_plan()

    by_key = {(row["protocol_version"], row["pdu_type"]): row for row in plan["records"]}
    for pdu_type in range(2, 68):
        dis6 = by_key[(6, pdu_type)]
        dis7 = by_key[(7, pdu_type)]
        assert dis6["projected_public_payload_kind"] == dis7["projected_public_payload_kind"]
        assert dis6["proof_fixtures"] == dis7["proof_fixtures"]
        assert dis6["proof_modes"] == dis7["proof_modes"]
        assert dis6["proof_depth"] == "semantic_egress_runtime"
        assert dis7["proof_depth"] == "semantic_egress_runtime"


def test_lattice_dis_mapping_proof_fixtures_exist() -> None:
    plan = mapping_plan.build_plan()

    fixture_paths = {
        ROOT / fixture
        for row in plan["records"]
        for fixture in row["proof_fixtures"]
    }

    assert fixture_paths
    for fixture in fixture_paths:
        assert fixture.is_file(), fixture


def test_lattice_dis_mapping_row_level_justification_examples() -> None:
    plan = mapping_plan.build_plan()

    def row(version: int, pdu_type: int) -> dict[str, object]:
        return next(item for item in plan["records"] if item["protocol_version"] == version and item["pdu_type"] == pdu_type)

    entity_state = row(7, 1)
    assert entity_state["projected_public_payload_kind"] == "track_entity"
    assert entity_state["why_not_lossless_code"] == "none"
    assert entity_state["proof_depth"] == "lossless_roundtrip_runtime"

    other6 = row(6, 0)
    assert other6["projected_public_payload_kind"] == "raw_object_artifact"
    assert other6["proof_depth"] == "archive_preservation_runtime"

    other7 = row(7, 0)
    assert other7["projected_public_payload_kind"] == "raw_object_artifact"
    assert other7["proof_depth"] == "archive_preservation_runtime"

    signal = row(7, 26)
    assert signal["projected_public_payload_kind"] == "signal_of_interest_entity"
    assert signal["why_not_lossless_code"] == "component_subset_only"

    designator = row(7, 24)
    assert designator["projected_public_payload_kind"] == "designator_entity"
    assert designator["proof_depth"] == "semantic_egress_runtime"
    assert designator["proof_fixtures"] == [
        "integrations/lattice/examples/lattice_designator_fixture.json",
        "integrations/lattice/examples/object_fixture.json",
    ]

    em_observation = row(7, 23)
    assert em_observation["projected_public_payload_kind"] == "emission_sensor_entity"
    assert em_observation["proof_fixtures"] == [
        "integrations/lattice/examples/lattice_em_observation_fixture.json",
        "integrations/lattice/examples/object_fixture.json",
    ]

    iff = row(7, 28)
    assert iff["projected_public_payload_kind"] == "entity_signal_annotation"
    assert iff["proof_fixtures"] == [
        "integrations/lattice/examples/lattice_annotation_fixture.json",
        "integrations/lattice/examples/object_fixture.json",
    ]

    transmitter = row(7, 25)
    assert transmitter["projected_public_payload_kind"] == "transmitter_entity"
    assert transmitter["proof_depth"] == "semantic_egress_runtime"
    assert transmitter["proof_fixtures"] == [
        "integrations/lattice/examples/lattice_transmitter_fixture.json",
        "integrations/lattice/examples/object_fixture.json",
    ]

    receiver = row(7, 27)
    assert receiver["projected_public_payload_kind"] == "receiver_entity"
    assert receiver["proof_depth"] == "semantic_egress_runtime"
    assert receiver["proof_fixtures"] == [
        "integrations/lattice/examples/lattice_receiver_fixture.json",
        "integrations/lattice/examples/object_fixture.json",
    ]

    intercom = row(7, 31)
    assert intercom["projected_public_payload_kind"] == "intercom_signal_annotation"
    assert intercom["proof_depth"] == "semantic_egress_runtime"
    assert intercom["proof_fixtures"] == [
        "integrations/lattice/examples/lattice_intercom_signal_fixture.json",
        "integrations/lattice/examples/object_fixture.json",
    ]

    intercom_control = row(7, 32)
    assert intercom_control["projected_public_payload_kind"] == "intercom_control_annotation"
    assert intercom_control["proof_depth"] == "semantic_egress_runtime"
    assert intercom_control["proof_fixtures"] == [
        "integrations/lattice/examples/lattice_intercom_control_fixture.json",
        "integrations/lattice/examples/object_fixture.json",
    ]

    underwater = row(7, 29)
    assert underwater["proof_depth"] == "semantic_egress_runtime"
    assert underwater["proof_fixtures"] == [
        "integrations/lattice/examples/lattice_underwater_signal_fixture.json",
        "integrations/lattice/examples/object_fixture.json",
    ]

    supplemental = row(7, 30)
    assert supplemental["proof_depth"] == "semantic_egress_runtime"
    assert supplemental["proof_fixtures"] == [
        "integrations/lattice/examples/lattice_emission_fixture.json",
        "integrations/lattice/examples/object_fixture.json",
    ]

    fire = row(7, 2)
    assert fire["projected_public_payload_kind"] == "task_event_projection"
    assert fire["why_not_lossless_code"] == "event_model_gap"
    assert fire["proof_depth"] == "semantic_egress_runtime"
    assert fire["proof_fixtures"] == [
        "integrations/lattice/examples/lattice_event_fire_fixture.json",
        "integrations/lattice/examples/object_fixture.json",
    ]

    collision = row(7, 4)
    assert collision["proof_depth"] == "semantic_egress_runtime"
    assert collision["proof_fixtures"] == [
        "integrations/lattice/examples/lattice_event_collision_fixture.json",
        "integrations/lattice/examples/object_fixture.json",
    ]

    le_fire = row(7, 49)
    assert le_fire["projected_public_payload_kind"] == "task_le_fire_event"
    assert le_fire["proof_depth"] == "semantic_egress_runtime"
    assert le_fire["proof_fixtures"] == [
        "integrations/lattice/examples/lattice_event_le_fire_fixture.json",
        "integrations/lattice/examples/object_fixture.json",
    ]

    directed_energy = row(7, 68)
    assert directed_energy["projected_public_payload_kind"] == "task_directed_energy_fire_event"
    assert directed_energy["proof_depth"] == "semantic_egress_runtime"
    assert directed_energy["proof_fixtures"] == [
        "integrations/lattice/examples/lattice_event_directed_energy_fire_fixture.json",
        "integrations/lattice/examples/object_fixture.json",
    ]

    le_detonation = row(7, 50)
    assert le_detonation["projected_public_payload_kind"] == "task_le_detonation_event"
    assert le_detonation["proof_fixtures"] == [
        "integrations/lattice/examples/lattice_event_le_detonation_fixture.json",
        "integrations/lattice/examples/object_fixture.json",
    ]

    collision_elastic = row(7, 66)
    assert collision_elastic["projected_public_payload_kind"] == "task_collision_elastic_event"
    assert collision_elastic["proof_fixtures"] == [
        "integrations/lattice/examples/lattice_event_collision_elastic_fixture.json",
        "integrations/lattice/examples/object_fixture.json",
    ]

    aggregate = row(7, 33)
    assert aggregate["projected_public_payload_kind"] == "entity_aggregate_projection"
    assert aggregate["why_not_lossless_code"] == "no_public_relationship_schema"
    assert aggregate["proof_depth"] == "semantic_egress_runtime"
    assert aggregate["proof_fixtures"] == [
        "integrations/lattice/examples/lattice_aggregate_state_fixture.json",
        "integrations/lattice/examples/object_fixture.json",
    ]

    is_group_of = row(7, 34)
    assert is_group_of["projected_public_payload_kind"] == "entity_group_membership_projection"
    assert is_group_of["proof_depth"] == "semantic_egress_runtime"
    assert is_group_of["proof_fixtures"] == [
        "integrations/lattice/examples/lattice_is_group_of_fixture.json",
        "integrations/lattice/examples/object_fixture.json",
    ]

    is_part_of = row(7, 36)
    assert is_part_of["projected_public_payload_kind"] == "entity_part_relationship_projection"
    assert is_part_of["proof_depth"] == "semantic_egress_runtime"
    assert is_part_of["proof_fixtures"] == [
        "integrations/lattice/examples/lattice_is_part_of_fixture.json",
        "integrations/lattice/examples/object_fixture.json",
    ]

    env_point = row(7, 43)
    assert env_point["projected_public_payload_kind"] == "geo_entity_point"
    assert env_point["proof_depth"] == "semantic_egress_runtime"
    assert env_point["proof_fixtures"] == [
        "integrations/lattice/examples/lattice_geo_point_fixture.json",
        "integrations/lattice/examples/object_fixture.json",
    ]

    env_line = row(7, 44)
    assert env_line["projected_public_payload_kind"] == "geo_entity_line"
    assert env_line["proof_depth"] == "semantic_egress_runtime"
    assert env_line["proof_fixtures"] == [
        "integrations/lattice/examples/lattice_geo_line_fixture.json",
        "integrations/lattice/examples/object_fixture.json",
    ]

    grid = row(7, 42)
    assert grid["projected_public_payload_kind"] == "geo_grid_overlay"
    assert grid["proof_depth"] == "semantic_egress_runtime"
    assert grid["proof_fixtures"] == [
        "integrations/lattice/examples/lattice_geo_grid_fixture.json",
        "integrations/lattice/examples/object_fixture.json",
    ]

    areal = row(7, 45)
    assert areal["projected_public_payload_kind"] == "geo_entity_polygon"
    assert areal["proof_depth"] == "semantic_egress_runtime"
    assert areal["proof_fixtures"] == [
        "integrations/lattice/examples/lattice_geo_areal_fixture.json",
        "integrations/lattice/examples/object_fixture.json",
    ]

    hazard = row(7, 37)
    assert hazard["projected_public_payload_kind"] == "geo_entity_hazard_region"

    minefield_query = row(7, 38)
    assert minefield_query["projected_public_payload_kind"] == "geo_minefield_query_overlay"
    assert minefield_query["proof_depth"] == "semantic_egress_runtime"
    assert minefield_query["proof_fixtures"] == [
        "integrations/lattice/examples/lattice_geo_minefield_query_fixture.json",
        "integrations/lattice/examples/object_fixture.json",
    ]

    minefield_data = row(7, 39)
    assert minefield_data["projected_public_payload_kind"] == "geo_minefield_data_overlay"
    assert minefield_data["proof_fixtures"] == [
        "integrations/lattice/examples/lattice_geo_minefield_data_fixture.json",
        "integrations/lattice/examples/object_fixture.json",
    ]

    minefield_nack = row(7, 40)
    assert minefield_nack["projected_public_payload_kind"] == "geo_minefield_response_nack"
    assert minefield_nack["proof_depth"] == "semantic_egress_runtime"
    assert minefield_nack["proof_fixtures"] == [
        "integrations/lattice/examples/lattice_geo_minefield_nack_fixture.json",
        "integrations/lattice/examples/object_fixture.json",
    ]

    env_process = row(7, 41)
    assert env_process["proof_fixtures"] == [
        "integrations/lattice/examples/lattice_geo_environment_process_fixture.json",
        "integrations/lattice/examples/object_fixture.json",
    ]

    ownership = row(7, 35)
    assert ownership["proof_fixtures"] == [
        "integrations/lattice/examples/lattice_relationship_ownership_fixture.json",
        "integrations/lattice/examples/object_fixture.json",
    ]

    service_request = row(7, 5)
    assert service_request["projected_public_payload_kind"] == "task_service_action"
    assert service_request["proof_fixtures"] == [
        "integrations/lattice/examples/lattice_task_service_fixture.json",
        "integrations/lattice/examples/object_fixture.json",
    ]

    resupply_offer = row(7, 6)
    assert resupply_offer["projected_public_payload_kind"] == "task_resupply_offer_action"
    assert resupply_offer["proof_depth"] == "semantic_egress_runtime"
    assert resupply_offer["proof_fixtures"] == [
        "integrations/lattice/examples/lattice_task_resupply_offer_fixture.json",
        "integrations/lattice/examples/object_fixture.json",
    ]

    resupply_received = row(7, 7)
    assert resupply_received["projected_public_payload_kind"] == "task_resupply_received_action"
    assert resupply_received["proof_fixtures"] == [
        "integrations/lattice/examples/lattice_task_resupply_received_fixture.json",
        "integrations/lattice/examples/object_fixture.json",
    ]

    resupply_cancel = row(7, 8)
    assert resupply_cancel["projected_public_payload_kind"] == "task_resupply_cancel_action"
    assert resupply_cancel["proof_depth"] == "semantic_egress_runtime"
    assert resupply_cancel["proof_fixtures"] == [
        "integrations/lattice/examples/lattice_task_resupply_cancel_fixture.json",
        "integrations/lattice/examples/object_fixture.json",
    ]

    repair_complete = row(7, 9)
    assert repair_complete["projected_public_payload_kind"] == "task_repair_complete_action"
    assert repair_complete["proof_depth"] == "semantic_egress_runtime"
    assert repair_complete["proof_fixtures"] == [
        "integrations/lattice/examples/lattice_task_repair_complete_fixture.json",
        "integrations/lattice/examples/object_fixture.json",
    ]

    repair_response = row(7, 10)
    assert repair_response["projected_public_payload_kind"] == "task_repair_response_action"
    assert repair_response["proof_fixtures"] == [
        "integrations/lattice/examples/lattice_task_repair_response_fixture.json",
        "integrations/lattice/examples/object_fixture.json",
    ]

    start_resume = row(7, 13)
    assert start_resume["projected_public_payload_kind"] == "task_start_projection"
    assert start_resume["proof_depth"] == "semantic_egress_runtime"
    assert start_resume["proof_fixtures"] == [
        "integrations/lattice/examples/lattice_task_start_fixture.json",
    ]

    stop_freeze = row(7, 14)
    assert stop_freeze["projected_public_payload_kind"] == "task_freeze_projection"
    assert stop_freeze["proof_depth"] == "semantic_egress_runtime"
    assert stop_freeze["proof_fixtures"] == [
        "integrations/lattice/examples/lattice_task_freeze_fixture.json",
    ]

    acknowledge = row(7, 15)
    assert acknowledge["projected_public_payload_kind"] == "task_ack_projection"
    assert acknowledge["proof_depth"] == "semantic_egress_runtime"
    assert acknowledge["proof_fixtures"] == [
        "integrations/lattice/examples/lattice_task_ack_only_fixture.json",
    ]

    acknowledge_r = row(7, 55)
    assert acknowledge_r["projected_public_payload_kind"] == "task_ack_reliable_projection"
    assert acknowledge_r["proof_depth"] == "semantic_egress_runtime"
    assert acknowledge_r["proof_fixtures"] == [
        "integrations/lattice/examples/lattice_task_ack_reliable_fixture.json",
    ]

    action_request = row(7, 16)
    assert action_request["projected_public_payload_kind"] == "task_action_request_projection"
    assert action_request["proof_fixtures"] == [
        "integrations/lattice/examples/lattice_task_action_request_fixture.json",
    ]

    action_response = row(7, 17)
    assert action_response["projected_public_payload_kind"] == "task_action_response_projection"
    assert action_response["proof_fixtures"] == [
        "integrations/lattice/examples/lattice_task_action_response_fixture.json",
    ]

    event_report = row(7, 21)
    assert event_report["proof_depth"] == "semantic_egress_runtime"
    assert event_report["proof_fixtures"] == [
        "integrations/lattice/examples/lattice_task_event_report_fixture.json",
    ]

    create_entity_r = row(7, 51)
    assert create_entity_r["proof_depth"] == "semantic_egress_runtime"
    assert create_entity_r["proof_fixtures"] == [
        "integrations/lattice/examples/lattice_task_entity_reliable_fixture.json",
    ]

    remove_entity_r = row(7, 52)
    assert remove_entity_r["proof_depth"] == "semantic_egress_runtime"
    assert remove_entity_r["proof_fixtures"] == [
        "integrations/lattice/examples/lattice_task_entity_reliable_fixture.json",
    ]

    data_query = row(7, 18)
    assert data_query["proof_depth"] == "semantic_egress_runtime"
    assert data_query["proof_fixtures"] == [
        "integrations/lattice/examples/lattice_task_data_query_fixture.json",
    ]
    assert data_query["projected_public_payload_kind"] == "task_data_query_projection"

    comment = row(7, 22)
    assert comment["projected_public_payload_kind"] == "task_comment_projection"
    assert comment["proof_depth"] == "semantic_egress_runtime"
    assert comment["proof_fixtures"] == [
        "integrations/lattice/examples/lattice_task_comment_fixture.json",
    ]

    set_data = row(7, 19)
    assert set_data["projected_public_payload_kind"] == "task_set_data_projection"
    assert set_data["proof_fixtures"] == [
        "integrations/lattice/examples/lattice_task_set_data_fixture.json",
    ]

    data_payload = row(7, 20)
    assert data_payload["projected_public_payload_kind"] == "task_data_payload_projection"
    assert data_payload["proof_fixtures"] == [
        "integrations/lattice/examples/lattice_task_data_payload_fixture.json",
    ]

    record_r = row(7, 63)
    assert record_r["projected_public_payload_kind"] == "task_record_reliable_projection"
    assert record_r["proof_depth"] == "semantic_egress_runtime"
    assert record_r["proof_fixtures"] == [
        "integrations/lattice/examples/lattice_task_record_r_fixture.json",
    ]

    set_record_r = row(7, 64)
    assert set_record_r["projected_public_payload_kind"] == "task_set_record_projection"
    assert set_record_r["proof_depth"] == "semantic_egress_runtime"
    assert set_record_r["proof_fixtures"] == [
        "integrations/lattice/examples/lattice_task_set_record_fixture.json",
    ]

    record_query_r = row(7, 65)
    assert record_query_r["projected_public_payload_kind"] == "task_record_query_projection"
    assert record_query_r["proof_depth"] == "semantic_egress_runtime"
    assert record_query_r["proof_fixtures"] == [
        "integrations/lattice/examples/lattice_task_record_query_fixture.json",
    ]

    attr = row(7, 72)
    assert attr["projected_public_payload_kind"] == "object_archive_projection"
    assert attr["why_not_lossless_code"] == "dis7_only_target_gap"
    assert attr["proof_depth"] == "archive_preservation_runtime"
    assert attr["proof_fixtures"] == [
        "integrations/lattice/examples/lattice_attribute_fixture.json",
        "integrations/lattice/examples/object_fixture.json",
    ]

    tspi = row(7, 46)
    assert tspi["projected_public_payload_kind"] == "entity_pose_annotation"
    assert tspi["proof_depth"] == "semantic_egress_runtime"
    assert tspi["proof_fixtures"] == [
        "integrations/lattice/examples/lattice_tspi_fixture.json",
        "integrations/lattice/examples/object_fixture.json",
    ]

    appearance = row(7, 47)
    assert appearance["projected_public_payload_kind"] == "entity_visual_state_annotation"
    assert appearance["proof_depth"] == "semantic_egress_runtime"
    assert appearance["proof_fixtures"] == [
        "integrations/lattice/examples/lattice_appearance_fixture.json",
        "integrations/lattice/examples/object_fixture.json",
    ]

    articulated = row(7, 48)
    assert articulated["projected_public_payload_kind"] == "entity_articulation_annotation"
    assert articulated["proof_depth"] == "semantic_egress_runtime"
    assert articulated["proof_fixtures"] == [
        "integrations/lattice/examples/lattice_articulated_parts_fixture.json",
        "integrations/lattice/examples/object_fixture.json",
    ]

    entity_damage = row(7, 69)
    assert entity_damage["projected_public_payload_kind"] == "task_entity_damage_event"
    assert entity_damage["proof_depth"] == "semantic_egress_runtime"
    assert entity_damage["proof_fixtures"] == [
        "integrations/lattice/examples/lattice_entity_damage_fixture.json",
        "integrations/lattice/examples/object_fixture.json",
    ]

    info_ops_action = row(7, 70)
    assert info_ops_action["projected_public_payload_kind"] == "task_information_operation_action"
    assert info_ops_action["proof_depth"] == "semantic_egress_runtime"
    assert info_ops_action["proof_fixtures"] == [
        "integrations/lattice/examples/lattice_info_ops_action_fixture.json",
        "integrations/lattice/examples/object_fixture.json",
    ]

    info_ops_report = row(7, 71)
    assert info_ops_report["projected_public_payload_kind"] == "task_information_operation_report"
    assert info_ops_report["proof_depth"] == "semantic_egress_runtime"
    assert info_ops_report["proof_fixtures"] == [
        "integrations/lattice/examples/lattice_info_ops_report_fixture.json",
        "integrations/lattice/examples/object_fixture.json",
    ]

    create_entity = row(7, 11)
    assert create_entity["projected_public_payload_kind"] == "entity_create_projection"
    assert create_entity["proof_depth"] == "semantic_egress_runtime"
    assert create_entity["proof_fixtures"] == [
        "integrations/lattice/examples/lattice_create_entity_fixture.json",
        "integrations/lattice/examples/object_fixture.json",
    ]

    remove_entity = row(7, 12)
    assert remove_entity["projected_public_payload_kind"] == "entity_remove_projection"
    assert remove_entity["proof_depth"] == "semantic_egress_runtime"
    assert remove_entity["proof_fixtures"] == [
        "integrations/lattice/examples/lattice_remove_entity_fixture.json",
        "integrations/lattice/examples/object_fixture.json",
    ]

    state_update = row(7, 67)
    assert state_update["projected_public_payload_kind"] == "entity_state_update_projection"
    assert state_update["proof_depth"] == "semantic_egress_runtime"
    assert state_update["proof_fixtures"] == [
        "integrations/lattice/examples/lattice_entity_state_update_fixture.json",
        "integrations/lattice/examples/object_fixture.json",
    ]
