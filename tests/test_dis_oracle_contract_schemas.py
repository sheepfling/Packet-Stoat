from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _schema(name: str) -> dict:
    return json.loads((ROOT / "schemas" / "json" / name).read_text(encoding="utf-8"))


def test_dis_oracle_contract_schema_consts_are_registered() -> None:
    expected = {
        "fastdis.dis_oracle_vector.v1.schema.json": "fastdis.dis_oracle_vector.v1",
        "fastdis.dis_oracle_normalized_pdu.v1.schema.json": "fastdis.dis_oracle_normalized_pdu.v1",
        "fastdis.dis_oracle_wrapper_result.v1.schema.json": "fastdis.dis_oracle_wrapper_result.v1",
        "fastdis.dis_oracle_external_status.v1.schema.json": "fastdis.dis_oracle_external_status.v1",
        "fastdis.dis_oracle_wrapper_contract.v1.schema.json": "fastdis.dis_oracle_wrapper_contract.v1",
        "fastdis.dis_oracle_wrapper_worklist.v1.schema.json": "fastdis.dis_oracle_wrapper_worklist.v1",
        "fastdis.dis_oracle_divergence_audit.v1.schema.json": "fastdis.dis_oracle_divergence_audit.v1",
        "fastdis.dis_oracle_workbench_plan.v1.schema.json": "fastdis.dis_oracle_workbench_plan.v1",
        "fastdis.dis_oracle_source_pins_report.v1.schema.json": "fastdis.dis_oracle_source_pins_report.v1",
        "fastdis.dis_oracle_source_candidates_report.v1.schema.json": "fastdis.dis_oracle_source_candidates_report.v1",
        "fastdis.dis_oracle_source_candidate_resolution.v1.schema.json": "fastdis.dis_oracle_source_candidate_resolution.v1",
        "fastdis.dis_oracle_source_candidate_promotion.v1.schema.json": "fastdis.dis_oracle_source_candidate_promotion.v1",
        "fastdis.dis_oracle_source_pin_worklist.v1.schema.json": "fastdis.dis_oracle_source_pin_worklist.v1",
        "fastdis.dis_oracle_source_sync.v1.schema.json": "fastdis.dis_oracle_source_sync.v1",
        "fastdis.dis_oracle_source_pin_checkouts.v1.schema.json": "fastdis.dis_oracle_source_pin_checkouts.v1",
        "fastdis.dis_oracle_source_readiness.v1.schema.json": "fastdis.dis_oracle_source_readiness.v1",
        "fastdis.dis_oracle_proof_bundle.v1.schema.json": "fastdis.dis_oracle_proof_bundle.v1",
        "fastdis.dis_oracle_layout_candidates.v1.schema.json": "fastdis.dis_oracle_layout_candidates.v1",
        "fastdis.dis_oracle_reference_pins_report.v1.schema.json": "fastdis.dis_oracle_reference_pins_report.v1",
        "fastdis.dis_oracle_reference_pin_audit.v1.schema.json": "fastdis.dis_oracle_reference_pin_audit.v1",
        "fastdis.dis_oracle_reference_pin_worklist.v1.schema.json": "fastdis.dis_oracle_reference_pin_worklist.v1",
        "fastdis.dis_oracle_proof_line.v1.schema.json": "fastdis.dis_oracle_proof_line.v1",
        "fastdis.dis_oracle_layout_pin_review_packet.v1.schema.json": "fastdis.dis_oracle_layout_pin_review_packet.v1",
        "fastdis.dis_oracle_layout_pin_review_batch.v1.schema.json": "fastdis.dis_oracle_layout_pin_review_batch.v1",
        "fastdis.dis_oracle_layout_pin_review_batch_audit.v1.schema.json": "fastdis.dis_oracle_layout_pin_review_batch_audit.v1",
        "fastdis.dis_oracle_layout_pin_review_outcome.v1.schema.json": "fastdis.dis_oracle_layout_pin_review_outcome.v1",
        "fastdis.dis_oracle_layout_pin_review_outcome_audit.v1.schema.json": "fastdis.dis_oracle_layout_pin_review_outcome_audit.v1",
        "fastdis.dis_oracle_layout_pin_review_outcome_apply.v1.schema.json": "fastdis.dis_oracle_layout_pin_review_outcome_apply.v1",
        "fastdis.dis_oracle_layout_pin_review_sheet.v1.schema.json": "fastdis.dis_oracle_layout_pin_review_sheet.v1",
        "fastdis.dis_oracle_layout_pin_review_sheet_audit.v1.schema.json": "fastdis.dis_oracle_layout_pin_review_sheet_audit.v1",
        "fastdis.dis_oracle_layout_pin_review_todo.v1.schema.json": "fastdis.dis_oracle_layout_pin_review_todo.v1",
        "fastdis.dis_oracle_layout_pin_review_workflow.v1.schema.json": "fastdis.dis_oracle_layout_pin_review_workflow.v1",
        "fastdis.dis_oracle_layout_pin_batch_iteration.v1.schema.json": "fastdis.dis_oracle_layout_pin_batch_iteration.v1",
        "fastdis.dis_oracle_layout_pin_active_review_packet.v1.schema.json": "fastdis.dis_oracle_layout_pin_active_review_packet.v1",
        "fastdis.dis_oracle_layout_pin_active_review_preflight.v1.schema.json": "fastdis.dis_oracle_layout_pin_active_review_preflight.v1",
        "fastdis.dis_oracle_candidate_layout_repair_worklist.v1.schema.json": "fastdis.dis_oracle_candidate_layout_repair_worklist.v1",
        "fastdis.dis_oracle_candidate_layout_repair_patch_skeletons.v1.schema.json": "fastdis.dis_oracle_candidate_layout_repair_patch_skeletons.v1",
        "fastdis.dis_oracle_candidate_layout_repair_patch_fill.v1.schema.json": "fastdis.dis_oracle_candidate_layout_repair_patch_fill.v1",
        "fastdis.dis_oracle_candidate_layout_repair_patch_audit.v1.schema.json": "fastdis.dis_oracle_candidate_layout_repair_patch_audit.v1",
        "fastdis.dis_oracle_candidate_layout_repair_apply.v1.schema.json": "fastdis.dis_oracle_candidate_layout_repair_apply.v1",
        "fastdis.dis_oracle_layout_pin_pipeline.v1.schema.json": "fastdis.dis_oracle_layout_pin_pipeline.v1",
        "fastdis.dis_oracle_layout_pin_campaign.v1.schema.json": "fastdis.dis_oracle_layout_pin_campaign.v1",
        "fastdis.dis_oracle_layout_pin_first_tranche.v1.schema.json": "fastdis.dis_oracle_layout_pin_first_tranche.v1",
        "fastdis.dis_oracle_layout_pin_tranche.v1.schema.json": "fastdis.dis_oracle_layout_pin_tranche.v1",
        "fastdis.dis_oracle_layout_pin_tranche_plan.v1.schema.json": "fastdis.dis_oracle_layout_pin_tranche_plan.v1",
        "fastdis.dis_oracle_parallel_work_plan.v1.schema.json": "fastdis.dis_oracle_parallel_work_plan.v1",
        "fastdis.dis_oracle_vector_authoring_packet.v1.schema.json": "fastdis.dis_oracle_vector_authoring_packet.v1",
        "fastdis.dis_oracle_vector_authoring_sheet.v1.schema.json": "fastdis.dis_oracle_vector_authoring_sheet.v1",
        "fastdis.dis_oracle_vector_spec_basis_packet.v1.schema.json": "fastdis.dis_oracle_vector_spec_basis_packet.v1",
        "fastdis.dis_oracle_reference_pin_apply.v1.schema.json": "fastdis.dis_oracle_reference_pin_apply.v1",
        "fastdis.dis_oracle_layout_promotion.v1.schema.json": "fastdis.dis_oracle_layout_promotion.v1",
        "fastdis.dis_oracle_layout_readiness.v1.schema.json": "fastdis.dis_oracle_layout_readiness.v1",
        "fastdis.dis_oracle_core6_tranche.v1.schema.json": "fastdis.dis_oracle_core6_tranche.v1",
        "fastdis.dis_oracle_vector_readiness.v1.schema.json": "fastdis.dis_oracle_vector_readiness.v1",
        "fastdis.dis_oracle_vector_fixture_workbench.v1.schema.json": "fastdis.dis_oracle_vector_fixture_workbench.v1",
        "fastdis.dis_oracle_vector_worklist.v1.schema.json": "fastdis.dis_oracle_vector_worklist.v1",
        "fastdis.dis_oracle_promotion_queue.v1.schema.json": "fastdis.dis_oracle_promotion_queue.v1",
        "fastdis.dis_oracle_answerability.v1.schema.json": "fastdis.dis_oracle_answerability.v1",
        "fastdis.benchmark_claim_overreach.v1.schema.json": "fastdis.benchmark_claim_overreach.v1",
    }

    for filename, schema_name in expected.items():
        payload = _schema(filename)
        assert payload["properties"]["schema"]["const"] == schema_name
        assert schema_name in payload["$id"]


def test_dis_oracle_contract_examples_satisfy_required_keys() -> None:
    normalized = {
        "schema": "fastdis.dis_oracle_normalized_pdu.v1",
        "version": "dis6",
        "pdu_type": 1,
        "pdu_name": "Entity State",
        "protocol_family": 1,
        "wire": {
            "total_length": 144,
            "endianness": "big",
            "sha256": "0" * 64,
            "field_offsets": {"header.protocolVersion": 0},
        },
        "fields": {"header": {}, "body": {}},
        "counts": {},
        "variable_records": [],
        "padding": [],
    }
    vector = {
        "schema": "fastdis.dis_oracle_vector.v1",
        "id": "dis6-entity-state-minimal",
        "version": "dis6",
        "pdu_type": 1,
        "pdu_name": "Entity State",
        "vector_type": "minimal",
        "spec_basis": [{"standard": "ieee-1278.1a-1998", "reference": "table TBD", "claim": "Entity State field layout"}],
        "semantic_message": {},
        "expected_wire": {"status": "layout_only", "endianness": "big"},
    }
    wrapper = {
        "schema": "fastdis.dis_oracle_wrapper_result.v1",
        "command": "decode",
        "version": "dis6",
        "oracle": {"id": "kdis6", "oracle_class": "implementation_oracle"},
        "status": "pass",
        "decoded_json": normalized,
        "warnings": [],
        "implementation": {"name": "KDIS", "implementation_version": None, "source_commit": None},
    }

    examples = [
        ("fastdis.dis_oracle_normalized_pdu.v1.schema.json", normalized),
        ("fastdis.dis_oracle_vector.v1.schema.json", vector),
        ("fastdis.dis_oracle_wrapper_result.v1.schema.json", wrapper),
    ]
    for filename, example in examples:
        schema = _schema(filename)
        assert set(schema["required"]).issubset(example)
