#!/usr/bin/env python3
"""Generate the FastDIS DIS 6/7 <-> Lattice/Zorn mapping plan."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SEMANTIC_MANIFEST = ROOT / "generated" / "semantic_pdu_parser_manifest.json"
JSON_OUT = ROOT / "generated" / "lattice_dis_mapping_plan.json"
MD_OUT = ROOT / "docs" / "LATTICE_DIS_MAPPING_PLAN.md"

ENTITY_TYPES = {1, 11, 12, 67}
WARFARE_EVENT_TYPES = {2, 3, 4, 49, 50, 66, 68, 69}
COMMUNICATION_TYPES = {23, 24, 25, 26, 27, 28, 29, 30, 31, 32}
SIM_CONTROL_TYPES = set(range(13, 23)) | set(range(51, 66))
LOGISTICS_TYPES = {5, 6, 7, 8, 9, 10}
AGGREGATE_TYPES = {33, 34, 35, 36}
MINEFIELD_TYPES = {37, 38, 39, 40}
ENVIRONMENT_TYPES = {41, 42, 43, 44, 45}
INFO_OPS_TYPES = {70, 71, 72}
STRICT_BUCKETS = ("Entity", "Task", "Object")

def _surface_for(row: dict[str, Any]) -> dict[str, str]:
    pdu_type = int(row["pdu_type"])
    if pdu_type == 0:
        return {
            "primary_lattice_object": "ObjectArtifact",
            "ingress_mapping": "DIS Other PDU -> versioned raw packet artifact with header metadata and provenance",
            "egress_mapping": "Object artifact with preserved raw payload -> original PDU bytes",
            "rest_route": "POST /api/v1/objects for raw packet artifact and metadata record",
            "grpc_route": "artifact-correlated generic notification only; payload remains REST object backed",
            "egress_policy": "emit_original_if_raw_artifact_present_else_drop_with_diagnostic",
            "loss_policy": "preserve_raw_required_for_lossless_egress",
        }
    if pdu_type == 1:
        return {
            "primary_lattice_object": "Entity",
            "ingress_mapping": "DIS Entity State -> canonical entity -> Lattice Entity location/aliases/milView/ontology/provenance/taskCatalog",
            "egress_mapping": "Lattice Entity location/aliases/milView/ontology -> DIS Entity State",
            "rest_route": "PUT /api/v1/entities, GET /api/v1/entities/{id}, POST /api/v1/entities/events",
            "grpc_route": "EntityManagerAPI.PublishEntity/GetEntity/StreamEntityComponents",
            "egress_policy": "emit_dis_entity_state",
            "loss_policy": "structured",
        }
    if pdu_type in {11, 12, 67}:
        return {
            "primary_lattice_object": "EntityLifecycle",
            "ingress_mapping": "DIS lifecycle/update PDU -> canonical lifecycle event -> Lattice entity create/update/non-live",
            "egress_mapping": "Lattice entity create/update/delete/non-live -> DIS lifecycle/update PDU when target version supports it",
            "rest_route": "PUT /api/v1/entities, POST /api/v1/entities/events",
            "grpc_route": "EntityManagerAPI.PublishEntity/StreamEntityComponents",
            "egress_policy": "emit_lifecycle_pdu_or_entity_state_fallback",
            "loss_policy": "diagnostic_defaulted_fields",
        }
    if pdu_type in WARFARE_EVENT_TYPES:
        return {
            "primary_lattice_object": "SimulationEvent",
            "ingress_mapping": "DIS event PDU -> Lattice-shaped SimulationEvent with raw DIS sidecar",
            "egress_mapping": "SimulationEvent with DIS sidecar -> original or target-version event PDU",
            "rest_route": "POST /api/v1/objects for sidecar artifact plus Entity media/result link when needed",
            "grpc_route": "generic observation/event stream until official event surface is available",
            "egress_policy": "emit_original_if_raw_sidecar_else_generic_observation",
            "loss_policy": "preserve_raw_required_for_lossless_egress",
        }
    if pdu_type in COMMUNICATION_TYPES:
        return {
            "primary_lattice_object": "CommunicationObservation",
            "ingress_mapping": "DIS radio/sensor/comms PDU -> communication/sensor observation with raw sidecar",
            "egress_mapping": "CommunicationObservation with raw sidecar -> original PDU; otherwise no lossless DIS emission",
            "rest_route": "POST /api/v1/objects for payload sidecars; entity media/provenance links optional",
            "grpc_route": "generic observation stream until official communication surface is available",
            "egress_policy": "emit_original_if_raw_sidecar_else_drop_with_diagnostic",
            "loss_policy": "preserve_raw_required_for_lossless_egress",
        }
    if pdu_type in SIM_CONTROL_TYPES:
        return {
            "primary_lattice_object": "TaskOrControlEvent",
            "ingress_mapping": "DIS simulation management PDU -> Task/control event depending action semantics",
            "egress_mapping": "Task lifecycle/control event -> DIS simulation management PDU when explicit mapping exists",
            "rest_route": "POST /api/v1/tasks, PUT /api/v1/tasks/{id}/status, PUT /api/v1/tasks/{id}/cancel",
            "grpc_route": "TaskManagerAPI.CreateTask/UpdateStatus/CancelTask/StreamTasks/ListenAsAgent",
            "egress_policy": "emit_task_control_pdu_when_semantic_fields_available",
            "loss_policy": "diagnostic_required_for_task_semantics",
        }
    if pdu_type in LOGISTICS_TYPES:
        return {
            "primary_lattice_object": "LogisticsObservation",
            "ingress_mapping": "DIS logistics PDU -> logistics observation/task hint with raw sidecar",
            "egress_mapping": "LogisticsObservation with raw sidecar -> original PDU",
            "rest_route": "Entity provenance/media plus object sidecar; task route if operator action is required",
            "grpc_route": "generic observation stream",
            "egress_policy": "emit_original_if_raw_sidecar_else_generic_observation",
            "loss_policy": "preserve_raw_required_for_lossless_egress",
        }
    if pdu_type in AGGREGATE_TYPES:
        return {
            "primary_lattice_object": "EntityRelationship",
            "ingress_mapping": "DIS aggregate/relationship PDU -> entity relationship observation",
            "egress_mapping": "Entity relationship with raw sidecar -> original PDU",
            "rest_route": "PUT /api/v1/entities with aliases/provenance plus object sidecar",
            "grpc_route": "EntityManagerAPI publish/stream for relationship-bearing entities",
            "egress_policy": "emit_original_if_raw_sidecar_else_relationship_observation_only",
            "loss_policy": "partial_without_relationship_schema",
        }
    if pdu_type in MINEFIELD_TYPES:
        return {
            "primary_lattice_object": "HazardObservation",
            "ingress_mapping": "DIS minefield PDU -> hazard/area observation with raw sidecar",
            "egress_mapping": "HazardObservation with raw sidecar -> original PDU",
            "rest_route": "Object sidecar plus optional entity/media link",
            "grpc_route": "generic observation stream",
            "egress_policy": "emit_original_if_raw_sidecar_else_drop_with_diagnostic",
            "loss_policy": "preserve_raw_required_for_lossless_egress",
        }
    if pdu_type in ENVIRONMENT_TYPES:
        return {
            "primary_lattice_object": "EnvironmentObservation",
            "ingress_mapping": "DIS environment/object-state PDU -> environment observation or object metadata sidecar",
            "egress_mapping": "EnvironmentObservation with raw sidecar -> original PDU",
            "rest_route": "Objects REST sidecar; entity media when attached to an entity",
            "grpc_route": "generic observation stream",
            "egress_policy": "emit_original_if_raw_sidecar_else_drop_with_diagnostic",
            "loss_policy": "preserve_raw_required_for_lossless_egress",
        }
    if pdu_type in INFO_OPS_TYPES:
        return {
            "primary_lattice_object": "InformationOperationsObservation",
            "ingress_mapping": "DIS 7 information/attribute PDU -> information operations observation with raw sidecar",
            "egress_mapping": "Observation with raw sidecar -> DIS 7 PDU only; DIS 6 target drops with diagnostic",
            "rest_route": "Objects REST sidecar plus entity/task link when applicable",
            "grpc_route": "generic observation stream",
            "egress_policy": "emit_dis7_only_or_drop_with_diagnostic",
            "loss_policy": "dis7_only",
        }
    return {
        "primary_lattice_object": "SimulationPduObservation",
        "ingress_mapping": "DIS PDU -> generic simulation PDU observation with header, typed envelope, diagnostics, and raw sidecar",
        "egress_mapping": "Observation with raw sidecar -> original PDU; typed envelope can emit target-version header when allowed",
        "rest_route": "Objects REST sidecar; optional entity/task/media link if correlated",
        "grpc_route": "generic observation stream",
        "egress_policy": "emit_original_if_raw_sidecar_else_generic_observation_only",
        "loss_policy": "preserve_raw_required_for_lossless_egress",
    }


def _record(row: dict[str, Any]) -> dict[str, Any]:
    surface = _surface_for(row)
    lattice_object = str(surface["primary_lattice_object"])
    strict_bucket = _strict_bucket_for(row, lattice_object)
    return {
        "protocol_version": int(row["protocol_version"]),
        "pdu_type": int(row["pdu_type"]),
        "standard_name": str(row["standard_name"]),
        "standard_class_name": str(row["standard_class_name"]),
        "family_name": str(row["family_name"]),
        "semantic_level": str(row["semantic_level"]),
        "fully_domain_decoded": bool(row["fully_domain_decoded"]),
        "strict_lattice_bucket": strict_bucket,
        "lattice_subtype": lattice_object,
        "rest_surface_kinds": _rest_surface_kinds(str(surface["rest_route"])),
        "grpc_surface_kind": _grpc_surface_kind(str(surface["grpc_route"])),
        "egress_conformance": _egress_conformance(str(surface["loss_policy"]), str(surface["egress_policy"])),
        **surface,
    }


def _strict_bucket_for(row: dict[str, Any], lattice_object: str) -> str:
    pdu_type = int(row["pdu_type"])
    if lattice_object in {"Entity", "EntityLifecycle", "EntityRelationship"}:
        return "Entity"
    if lattice_object == "TaskOrControlEvent":
        return "Task"
    if lattice_object == "SimulationEvent":
        return "Task"
    if lattice_object == "LogisticsObservation":
        return "Task"
    if lattice_object == "CommunicationObservation":
        return "Entity"
    if lattice_object == "EnvironmentObservation":
        return "Object"
    if lattice_object == "HazardObservation":
        return "Object"
    if lattice_object == "InformationOperationsObservation":
        return "Object" if pdu_type == 72 else "Task"
    if lattice_object == "SimulationPduObservation":
        return "Entity"
    if lattice_object == "ObjectArtifact":
        return "Object"
    if lattice_object.endswith("Observation"):
        return "Object"
    raise ValueError(f"Unclassified lattice object: {lattice_object}")


def _rest_surface_kinds(rest_route: str) -> list[str]:
    kinds: list[str] = []
    lowered = rest_route.lower()
    if "/api/v1/entities" in rest_route or " entity " in lowered or "entity " in lowered or "entity/" in lowered:
        kinds.append("entities")
    if "/api/v1/tasks" in rest_route or "task route" in lowered or "tasks/" in lowered:
        kinds.append("tasks")
    if "/api/v1/objects" in rest_route or "object sidecar" in lowered or "objects rest" in lowered or "raw packet artifact" in lowered:
        kinds.append("objects")
    return sorted(set(kinds))


def _grpc_surface_kind(grpc_route: str) -> str:
    if "EntityManagerAPI" in grpc_route:
        return "entities"
    if "TaskManagerAPI" in grpc_route:
        return "tasks"
    return "generic"


def _egress_conformance(loss_policy: str, egress_policy: str) -> str:
    if loss_policy == "structured":
        return "structured"
    if "raw" in loss_policy or "raw" in egress_policy:
        return "raw_required"
    if loss_policy in {"diagnostic_defaulted_fields", "diagnostic_required_for_task_semantics", "partial_without_relationship_schema", "dis7_only"}:
        return "diagnostic"
    return "best_effort"


def _observation_reduction_targets(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return []


def validate_plan(plan: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    records = plan["records"]
    expected_bucket_counts = Counter(str(row["strict_lattice_bucket"]) for row in records)
    if dict(sorted(expected_bucket_counts.items())) != plan["summary"]["strict_lattice_buckets"]:
        issues.append("strict_lattice_buckets summary does not match record rows")
    for row in records:
        key = f"DIS{row['protocol_version']}:{row['pdu_type']}:{row['standard_name']}"
        bucket = row["strict_lattice_bucket"]
        if bucket not in STRICT_BUCKETS:
            issues.append(f"{key} has invalid strict bucket {bucket}")
            continue
        if not row["rest_surface_kinds"]:
            issues.append(f"{key} has no derived REST surface kinds")
        grpc_kind = row["grpc_surface_kind"]
        if bucket == "Entity":
            if not ({"entities", "objects"} & set(row["rest_surface_kinds"])):
                issues.append(f"{key} entity bucket missing entity/object REST surface")
            if grpc_kind not in {"entities", "generic"}:
                issues.append(f"{key} entity bucket has invalid gRPC kind {grpc_kind}")
        elif bucket == "Task":
            if not ({"tasks", "objects"} & set(row["rest_surface_kinds"])):
                issues.append(f"{key} task bucket missing task/object REST surface")
            if grpc_kind not in {"tasks", "generic"}:
                issues.append(f"{key} task bucket has invalid gRPC kind {grpc_kind}")
        elif bucket == "Object":
            if "objects" not in row["rest_surface_kinds"]:
                issues.append(f"{key} object bucket missing object REST surface")
            if grpc_kind != "generic":
                issues.append(f"{key} object bucket has invalid gRPC kind {grpc_kind}")
    return issues


def build_plan() -> dict[str, Any]:
    payload = json.loads(SEMANTIC_MANIFEST.read_text(encoding="utf-8"))
    records = [_record(row) for row in payload["records"]]
    strict_buckets = Counter(str(row["strict_lattice_bucket"]) for row in records)
    subtypes = Counter(str(row["lattice_subtype"]) for row in records)
    loss = Counter(str(row["loss_policy"]) for row in records)
    return {
        "schema": "fastdis.lattice_dis_mapping_plan.v1",
        "generated_at": "deterministic",
        "source": str(SEMANTIC_MANIFEST.relative_to(ROOT)),
        "policy": {
            "coverage_rule": "Every standard DIS 6/7 PDU row has an explicit Lattice/Zorn ingress and egress policy.",
            "loss_rule": "No row may silently disappear; lossy mappings require diagnostics and raw sidecar preservation where needed.",
            "objects_rule": "Objects are REST-only; gRPC mappings use entity/task/generic observation streams.",
            "bucket_rule": "Every row must classify into exactly one strict bucket: Entity, Task, Object, or Observation.",
        },
        "summary": {
            "records": len(records),
            "strict_lattice_buckets": dict(sorted(strict_buckets.items())),
            "lattice_subtypes": dict(sorted(subtypes.items())),
            "observation_reduction_targets": _observation_reduction_targets(records),
            "loss_policies": dict(sorted(loss.items())),
            "bucket_conformance": _bucket_conformance_summary(records),
        },
        "records": records,
    }


def _bucket_conformance_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for bucket in STRICT_BUCKETS:
        rows = [row for row in records if row["strict_lattice_bucket"] == bucket]
        summary[bucket] = {
            "rows": len(rows),
            "rest_surface_kind_counts": dict(sorted(Counter(kind for row in rows for kind in row["rest_surface_kinds"]).items())),
            "grpc_surface_kind_counts": dict(sorted(Counter(str(row["grpc_surface_kind"]) for row in rows).items())),
            "egress_conformance_counts": dict(sorted(Counter(str(row["egress_conformance"]) for row in rows).items())),
        }
    return summary


def render_markdown(plan: dict[str, Any]) -> str:
    lines = [
        "# Lattice DIS Mapping Plan",
        "",
        "Generated from the 141-row semantic DIS 6/7 manifest.",
        "",
        f"- records: `{plan['summary']['records']}`",
        "",
        "## Policy",
        "",
    ]
    for value in plan["policy"].values():
        lines.append(f"- {value}")
        lines.extend(
        [
            "",
            "## Strict Bucket Summary",
            "",
            "| Bucket | Rows |",
            "|---|---:|",
        ]
    )
    for bucket, count in plan["summary"]["strict_lattice_buckets"].items():
        lines.append(f"| {bucket} | {count} |")
    lines.extend(
        [
            "",
            "## Bucket Conformance",
            "",
            "| Bucket | Rows | REST surfaces | gRPC surfaces | Egress modes |",
            "|---|---:|---|---|---|",
        ]
    )
    for bucket, info in plan["summary"]["bucket_conformance"].items():
        lines.append(
            f"| {bucket} | {info['rows']} | {json.dumps(info['rest_surface_kind_counts'], sort_keys=True)} | "
            f"{json.dumps(info['grpc_surface_kind_counts'], sort_keys=True)} | "
            f"{json.dumps(info['egress_conformance_counts'], sort_keys=True)} |"
        )
    lines.extend(
        [
            "",
            "## Lattice Subtype Summary",
            "",
            "| Subtype | Strict bucket | Rows |",
            "|---|---|---:|",
        ]
    )
    for subtype, count in plan["summary"]["lattice_subtypes"].items():
        sample = next(row for row in plan["records"] if row["lattice_subtype"] == subtype)
        bucket = sample["strict_lattice_bucket"]
        lines.append(f"| {subtype} | {bucket} | {count} |")
    lines.extend(
        [
            "",
            "## Observation Reduction Targets",
            "",
            "| Current subtype | Rows | Target bucket | Why reduce it |",
            "|---|---:|---|---|",
        ]
    )
    for target in plan["summary"]["observation_reduction_targets"]:
        lines.append(
            f"| {target['subtype']} | {target['rows']} | {target['target_bucket']} | {target['rationale']} |"
        )
    lines.extend(
        [
            "",
            "## Row Mapping",
            "",
            "| DIS | PDU | Name | Strict bucket | Lattice subtype | REST route | gRPC route | Egress | Loss policy |",
            "|---:|---:|---|---|---|---|---|---|---|",
        ]
    )
    for row in plan["records"]:
        lines.append(
            f"| {row['protocol_version']} | {row['pdu_type']} | {row['standard_name']} | "
            f"{row['strict_lattice_bucket']} | {row['lattice_subtype']} | {row['rest_route']} | {row['grpc_route']} | "
            f"{row['egress_policy']} | {row['loss_policy']} |"
        )
    return "\n".join(lines) + "\n"


def write_outputs(plan: dict[str, Any]) -> None:
    JSON_OUT.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    MD_OUT.write_text(render_markdown(plan), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail if checked-in outputs are stale.")
    args = parser.parse_args()
    plan = build_plan()
    issues = validate_plan(plan)
    if args.check:
        stale = []
        expected_json = json.dumps(plan, indent=2, sort_keys=True) + "\n"
        expected_md = render_markdown(plan)
        if not JSON_OUT.is_file() or JSON_OUT.read_text(encoding="utf-8") != expected_json:
            stale.append(str(JSON_OUT.relative_to(ROOT)))
        if not MD_OUT.is_file() or MD_OUT.read_text(encoding="utf-8") != expected_md:
            stale.append(str(MD_OUT.relative_to(ROOT)))
        if issues:
            print("invalid lattice DIS mapping plan: " + "; ".join(issues))
            return 1
        if stale:
            print("stale lattice DIS mapping outputs: " + ", ".join(stale))
            return 1
        print("lattice DIS mapping outputs are up to date")
        return 0
    if issues:
        print("invalid lattice DIS mapping plan: " + "; ".join(issues))
        return 1
    write_outputs(plan)
    print(json.dumps({"records": plan["summary"]["records"], "json": str(JSON_OUT), "markdown": str(MD_OUT)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
