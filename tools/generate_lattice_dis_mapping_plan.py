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
RESEARCH_SOURCE_CATALOG = {
    "auth_guide": {
        "title": "Authenticate",
        "url": "https://developer.anduril.com/guides/getting-started/authenticate",
        "note": "REST handles OAuth token lifecycle automatically; gRPC requires explicit token refresh and metadata injection.",
    },
    "entities_overview": {
        "title": "Entities overview",
        "url": "https://developer.anduril.com/guides/entities/overview",
        "note": "Documents track, asset, signal-of-interest, sensor point-of-interest, geo-entity, and entity lifecycle patterns.",
    },
    "objects_overview": {
        "title": "Objects overview",
        "url": "https://developer.anduril.com/guides/objects/overview",
        "note": "Documents REST-only object storage, CDN distribution, TTL expiry, checksums, and entity media linkage.",
    },
    "offline_guide": {
        "title": "Connect to offline environments",
        "url": "https://developer.anduril.com/guides/best-practices/connect-offline",
        "note": "Documents self-signed TLS handling and keeps offline transport concerns separate from mapping semantics.",
    },
    "protocol_guide": {
        "title": "Choose a protocol",
        "url": "https://developer.anduril.com/guides/best-practices/choose-a-protocol",
        "note": "Documents REST vs gRPC availability, retries, streaming shape, and the fact that Objects are REST-only.",
    },
    "tasks_overview": {
        "title": "Tasks overview",
        "url": "https://developer.anduril.com/guides/tasks/overview",
        "note": "Documents task lifecycle, task catalog, status updates, and deliberate action semantics.",
    },
}
PUBLIC_FAMILY_RATIONALES = {
    "CommunicationObservation": {
        "closest_public_surface": "entity",
        "rationale": "The public entity model explicitly covers sensor points of interest and signals of interest, so communication and sensor PDUs fit better as projected entities than as opaque files, even though there is no DIS-native communications API.",
        "research_basis": ["entities_overview", "protocol_guide"],
    },
    "Entity": {
        "closest_public_surface": "entity",
        "rationale": "Entity State maps directly to the public entity model because Lattice entities are composable COP state containers with lifecycle and partial-state handling.",
        "research_basis": ["entities_overview", "protocol_guide"],
    },
    "EntityLifecycle": {
        "closest_public_surface": "entity",
        "rationale": "Create, update, and remove semantics align with the public entity lifecycle model, but some DIS lifecycle details must be defaulted or projected.",
        "research_basis": ["entities_overview", "protocol_guide"],
    },
    "EntityRelationship": {
        "closest_public_surface": "entity",
        "rationale": "Aggregate and relationship PDUs are closest to entity-linked relationship state because the public entity model supports composable components and aliases, but not a DIS-native relationship schema.",
        "research_basis": ["entities_overview", "protocol_guide"],
    },
    "EnvironmentObservation": {
        "closest_public_surface": "entity",
        "rationale": "The public entity model includes geo-entities for shapes, regions, and points of interest, which is a closer public analogue for environment and object-state PDUs than REST objects alone; objects remain the raw sidecar path.",
        "research_basis": ["entities_overview", "objects_overview", "protocol_guide"],
    },
    "HazardObservation": {
        "closest_public_surface": "entity",
        "rationale": "Minefield and hazard rows align more closely with geo-entity regions and map overlays than with raw object storage alone, while objects remain the preservation surface for exact DIS fidelity.",
        "research_basis": ["entities_overview", "objects_overview", "protocol_guide"],
    },
    "InformationOperationsObservation": {
        "closest_public_surface": "task",
        "rationale": "Information-operations PDUs are modeled as projected tasks when they describe deliberate effects or operations, with object-backed preservation for raw DIS fidelity.",
        "research_basis": ["tasks_overview", "objects_overview", "protocol_guide"],
    },
    "LogisticsObservation": {
        "closest_public_surface": "task",
        "rationale": "Logistics PDUs are closest to tasks because they often describe operator- or agent-executed servicing actions, but the public task model does not directly encode DIS logistics semantics.",
        "research_basis": ["tasks_overview", "protocol_guide"],
    },
    "ObjectArtifact": {
        "closest_public_surface": "object",
        "rationale": "Raw artifacts map directly to the public Objects model because objects are the documented file/data storage and retrieval surface.",
        "research_basis": ["objects_overview", "protocol_guide"],
    },
    "SimulationEvent": {
        "closest_public_surface": "task",
        "rationale": "Warfare and simulation-event PDUs are closest to tasks as projected operational events because Tasks is the documented public action/lifecycle surface, even though it is not a native DIS event schema.",
        "research_basis": ["tasks_overview", "protocol_guide"],
    },
    "SimulationPduObservation": {
        "closest_public_surface": "entity",
        "rationale": "Unclassified live/simulation PDUs are currently projected toward entities when they can contribute COP state, otherwise preserved as linked observations and sidecars.",
        "research_basis": ["entities_overview", "objects_overview", "protocol_guide"],
    },
    "TaskOrControlEvent": {
        "closest_public_surface": "task",
        "rationale": "Simulation-management PDUs are the closest public match to tasks because the Tasks API is explicitly for deliberate, sequential actions with lifecycle and routing.",
        "research_basis": ["tasks_overview", "protocol_guide"],
    },
}
FAMILY_PROJECTION_CATALOG = {
    "CommunicationObservation": {
        "candidate_public_components": ["aliases", "location", "milView", "ontology", "provenance", "signal", "sensors"],
        "payload_projection": "Project comms/sensor rows into signal-of-interest or sensor point-of-interest entities, with object sidecars when raw payload detail exceeds documented entity components.",
        "transport_constraints": [
            "entity projection can use REST or gRPC",
            "raw payload sidecars require REST Objects",
            "advanced filtering is strongest on gRPC entity streams",
        ],
        "proof_modes": ["entity_projection_contract", "raw_sidecar_preservation"],
        "proof_fixtures": ["integrations/lattice/examples/lattice_signal_fixture.json", "integrations/lattice/examples/object_fixture.json"],
    },
    "Entity": {
        "candidate_public_components": ["aliases", "location", "milView", "ontology", "provenance", "health", "taskCatalog"],
        "payload_projection": "Map canonical Entity State directly into public entity components and emit back through the existing canonical entity round-trip.",
        "transport_constraints": [
            "REST and gRPC both support entity publish/get/stream",
            "REST handles OAuth token lifecycle automatically",
            "gRPC requires manual token refresh and metadata injection",
        ],
        "proof_modes": ["entity_roundtrip", "entity_publish_get_stream"],
        "proof_fixtures": ["integrations/lattice/examples/dis_entity_fixture.json", "integrations/lattice/examples/lattice_track_fixture.json"],
    },
    "EntityLifecycle": {
        "candidate_public_components": ["aliases", "location", "milView", "ontology", "provenance", "isLive", "expiryTime"],
        "payload_projection": "Project create/update/remove rows into entity lifecycle updates, using isLive and expiry-driven delete semantics when there is no exact DIS lifecycle surface on egress.",
        "transport_constraints": [
            "REST and gRPC both support entity lifecycle flows",
            "delete semantics rely on isLive false or expiry time in public docs",
        ],
        "proof_modes": ["entity_projection_contract", "entity_publish_get_stream"],
        "proof_fixtures": ["integrations/lattice/examples/dis_entity_fixture.json", "integrations/lattice/examples/lattice_track_fixture.json"],
    },
    "EntityRelationship": {
        "candidate_public_components": ["aliases", "ontology", "provenance", "location", "media"],
        "payload_projection": "Project aggregate and relationship rows into entity-linked relationship state plus object sidecars for DIS-specific relationship detail not modeled by public entity components.",
        "transport_constraints": [
            "entity projection can use REST or gRPC",
            "relationship detail sidecars require REST Objects",
        ],
        "proof_modes": ["entity_projection_contract", "raw_sidecar_preservation"],
        "proof_fixtures": ["integrations/lattice/examples/lattice_relationship_fixture.json", "integrations/lattice/examples/object_fixture.json"],
    },
    "EnvironmentObservation": {
        "candidate_public_components": ["aliases", "ontology", "geoDetails", "geoShape", "location", "provenance", "media"],
        "payload_projection": "Project environment/object-state rows into geo-entity shapes, regions, or points of interest, keeping raw DIS sidecars for exact object-state fidelity.",
        "transport_constraints": [
            "geo-entity projection can use REST or gRPC entity surfaces",
            "raw payload and media linkage require REST Objects",
            "object-sidecar expiry/delete requires resetting entity media references",
        ],
        "proof_modes": ["entity_projection_contract", "raw_sidecar_preservation", "object_fixture_contract"],
        "proof_fixtures": ["integrations/lattice/examples/lattice_geo_fixture.json", "integrations/lattice/examples/object_fixture.json"],
    },
    "HazardObservation": {
        "candidate_public_components": ["aliases", "ontology", "geoDetails", "geoShape", "location", "provenance", "media"],
        "payload_projection": "Project hazard and minefield rows into geo-entity overlays or hazard regions, with object sidecars preserving exact DIS hazard records for egress.",
        "transport_constraints": [
            "geo-style entity projection can use REST or gRPC entity surfaces",
            "hazard raw detail sidecars require REST Objects",
        ],
        "proof_modes": ["entity_projection_contract", "raw_sidecar_preservation", "object_fixture_contract"],
        "proof_fixtures": ["integrations/lattice/examples/lattice_geo_fixture.json", "integrations/lattice/examples/object_fixture.json"],
    },
    "InformationOperationsObservation": {
        "candidate_public_components": ["description", "specification", "status", "result", "provenance", "media"],
        "payload_projection": "Project DIS 7 information-operations rows into task-like operational records, but preserve raw payloads because the public task surface is not a native DIS info-ops schema.",
        "transport_constraints": [
            "task projection can use REST or gRPC",
            "raw fidelity sidecars require REST Objects",
            "DIS 7-only rows cannot emit DIS 6 without diagnostics",
        ],
        "proof_modes": ["task_fixture_contract", "raw_sidecar_preservation"],
        "proof_fixtures": ["integrations/lattice/examples/lattice_event_task_fixture.json", "integrations/lattice/examples/object_fixture.json"],
    },
    "LogisticsObservation": {
        "candidate_public_components": ["description", "specification", "status", "allocation", "result", "provenance"],
        "payload_projection": "Project logistics rows into task-like servicing or operator workflow payloads, keeping raw DIS sidecars when exact logistics semantics do not fit the public task schema.",
        "transport_constraints": [
            "task projection can use REST or gRPC",
            "lossless egress still depends on raw sidecars",
        ],
        "proof_modes": ["task_fixture_contract", "raw_sidecar_preservation"],
        "proof_fixtures": ["integrations/lattice/examples/task_fixture.json", "integrations/lattice/examples/object_fixture.json"],
    },
    "ObjectArtifact": {
        "candidate_public_components": ["contentIdentifier", "sizeBytes", "lastUpdatedAt", "expiryTime", "checksum"],
        "payload_projection": "Preserve raw DIS bytes as REST object artifacts with metadata, checksums, and optional entity/media references.",
        "transport_constraints": [
            "Objects are REST-only",
            "checksum and TTL semantics come from the Objects API",
        ],
        "proof_modes": ["object_fixture_contract", "raw_sidecar_preservation"],
        "proof_fixtures": ["integrations/lattice/examples/object_fixture.json", "integrations/lattice/examples/dis_entity_fixture.json"],
    },
    "SimulationEvent": {
        "candidate_public_components": ["description", "specification", "status", "result", "allocation", "provenance", "media"],
        "payload_projection": "Project warfare and simulation-event rows into task-like operational events with attached object sidecars when a richer event body must be preserved.",
        "transport_constraints": [
            "task projection can use REST or gRPC",
            "raw event fidelity sidecars require REST Objects",
        ],
        "proof_modes": ["task_fixture_contract", "raw_sidecar_preservation"],
        "proof_fixtures": ["integrations/lattice/examples/lattice_event_task_fixture.json", "integrations/lattice/examples/object_fixture.json"],
    },
    "SimulationPduObservation": {
        "candidate_public_components": ["aliases", "location", "ontology", "provenance", "media"],
        "payload_projection": "Project generic live/simulation rows into minimal entity-linked observations and preserve the original DIS payload as an object sidecar when semantics are underspecified.",
        "transport_constraints": [
            "minimal entity projection can use REST or gRPC",
            "raw payload preservation requires REST Objects",
        ],
        "proof_modes": ["entity_projection_contract", "raw_sidecar_preservation"],
        "proof_fixtures": ["integrations/lattice/examples/dis_entity_fixture.json", "integrations/lattice/examples/object_fixture.json"],
    },
    "TaskOrControlEvent": {
        "candidate_public_components": ["description", "specification", "version", "createdBy", "lastUpdatedBy", "status", "progress", "result", "allocation"],
        "payload_projection": "Project simulation-management rows into public task lifecycle records, using status/result/progress/allocation fields and task catalog links where appropriate.",
        "transport_constraints": [
            "task projection can use REST or gRPC",
            "REST has built-in retries while gRPC has stronger streaming/filtering but manual auth/retry work",
        ],
        "proof_modes": ["task_fixture_contract", "task_stream_contract"],
        "proof_fixtures": ["integrations/lattice/examples/task_fixture.json"],
    },
}

WHY_NOT_LOSSLESS_NOTES = {
    "component_subset_only": "The closest public surface exposes only a subset of the DIS fields, so FastDIS must project or sidecar the remaining semantics.",
    "dis7_only_target_gap": "The source row is DIS 7-only or version-sensitive, so cross-version egress cannot be lossless for every target.",
    "event_model_gap": "The public Lattice surface has no DIS-native warfare/event schema, so event rows remain projected or raw-backed.",
    "no_public_relationship_schema": "The public entity model lacks a DIS-native aggregate/relationship schema, so relationship rows remain projected with sidecars.",
    "raw_artifact_source_of_truth": "The raw DIS bytes are the source of truth and the public object surface is used for archival/preservation rather than semantic reconstruction.",
    "task_schema_gap": "The public Tasks API is action-oriented but does not directly encode the full DIS control/logistics semantics.",
}

LOSSLESS_ROUNDTRIP_ROWS = {
    (6, 1),
    (7, 1),
}

ARCHIVE_PRESERVATION_ROWS = {
    (6, 0),
    (7, 0),
    (7, 72),
}

SEMANTIC_EGRESS_PDU_TYPES_BOTH_VERSIONS = set(range(2, 68))

SEMANTIC_EGRESS_ROWS = {
    (7, 68),
    (7, 69),
    (7, 70),
    (7, 71),
}


def _lossy_modes(
    pdu_type: int,
    lattice_object: str,
    loss_policy: str,
) -> dict[str, Any]:
    if lattice_object == "ObjectArtifact":
        return {
            "lossy_ingress_supported": False,
            "lossy_ingress_policy": "strict_raw_artifact_only",
            "lossy_egress_supported": False,
            "lossy_egress_policy": "strict_raw_artifact_only",
            "lossy_mode_class": "strict_only",
        }
    if loss_policy == "structured":
        return {
            "lossy_ingress_supported": False,
            "lossy_ingress_policy": "structured_lossless_entity_projection",
            "lossy_egress_supported": False,
            "lossy_egress_policy": "structured_lossless_entity_emit",
            "lossy_mode_class": "strict_only",
        }
    if lattice_object == "EntityLifecycle":
        return {
            "lossy_ingress_supported": True,
            "lossy_ingress_policy": "normalize_entity_lifecycle_with_defaulted_fields",
            "lossy_egress_supported": True,
            "lossy_egress_policy": "emit_lifecycle_or_entity_state_fallback_with_defaults",
            "lossy_mode_class": "bidirectional",
        }
    if lattice_object == "TaskOrControlEvent":
        return {
            "lossy_ingress_supported": True,
            "lossy_ingress_policy": "normalize_task_or_control_event_with_diagnostics",
            "lossy_egress_supported": True,
            "lossy_egress_policy": "emit_task_control_projection_when_semantics_are_present",
            "lossy_mode_class": "bidirectional",
        }
    if lattice_object == "InformationOperationsObservation":
        return {
            "lossy_ingress_supported": True,
            "lossy_ingress_policy": "normalize_info_ops_observation_with_version_diagnostics",
            "lossy_egress_supported": True,
            "lossy_egress_policy": "emit_dis7_projection_only",
            "lossy_mode_class": "bidirectional",
        }
    return {
        "lossy_ingress_supported": True,
        "lossy_ingress_policy": "normalize_to_observation_or_sidecar_with_diagnostics",
        "lossy_egress_supported": False,
        "lossy_egress_policy": "lossless_raw_sidecar_required_for_dis_emit",
        "lossy_mode_class": "ingress_only",
    }


def _public_analogue(
    pdu_type: int,
    lattice_object: str,
    strict_bucket: str,
    loss_policy: str,
) -> dict[str, Any]:
    if lattice_object == "ObjectArtifact":
        return {
            "closest_public_surface": "object",
            "surface_confidence": "direct",
            "protocol_availability": "rest_only",
            "fallback_mode": "archive_only",
            "research_basis": ["objects_overview", "protocol_guide"],
        }
    if loss_policy == "structured":
        return {
            "closest_public_surface": "entity",
            "surface_confidence": "direct",
            "protocol_availability": "rest_and_grpc",
            "fallback_mode": "lossless",
            "research_basis": ["entities_overview", "protocol_guide"],
        }
    if lattice_object == "EntityLifecycle":
        return {
            "closest_public_surface": "entity",
            "surface_confidence": "projected",
            "protocol_availability": "rest_and_grpc",
            "fallback_mode": "projected",
            "research_basis": ["entities_overview", "protocol_guide"],
        }
    if lattice_object in {"TaskOrControlEvent", "SimulationEvent", "LogisticsObservation"}:
        return {
            "closest_public_surface": "task",
            "surface_confidence": "projected",
            "protocol_availability": "rest_and_grpc",
            "fallback_mode": "projected" if lattice_object == "TaskOrControlEvent" else "observe_only",
            "research_basis": ["tasks_overview", "protocol_guide"],
        }
    if lattice_object in {"CommunicationObservation", "EntityRelationship"}:
        return {
            "closest_public_surface": "entity",
            "surface_confidence": "projected",
            "protocol_availability": "rest_and_grpc",
            "fallback_mode": "projected",
            "research_basis": ["entities_overview", "protocol_guide"],
        }
    if lattice_object in {"EnvironmentObservation", "HazardObservation"}:
        return {
            "closest_public_surface": "entity",
            "surface_confidence": "projected",
            "protocol_availability": "rest_and_grpc",
            "fallback_mode": "projected",
            "research_basis": ["entities_overview", "objects_overview", "protocol_guide"],
        }
    if lattice_object == "InformationOperationsObservation" and strict_bucket == "Object":
        return {
            "closest_public_surface": "object",
            "surface_confidence": "projected",
            "protocol_availability": "rest_only",
            "fallback_mode": "observe_only",
            "research_basis": ["objects_overview", "protocol_guide"],
        }
    if strict_bucket == "Entity":
        return {
            "closest_public_surface": "entity",
            "surface_confidence": "projected",
            "protocol_availability": "rest_and_grpc",
            "fallback_mode": "observe_only",
            "research_basis": ["entities_overview", "protocol_guide"],
        }
    if strict_bucket == "Task":
        return {
            "closest_public_surface": "task",
            "surface_confidence": "projected",
            "protocol_availability": "rest_and_grpc",
            "fallback_mode": "observe_only",
            "research_basis": ["tasks_overview", "protocol_guide"],
        }
    return {
        "closest_public_surface": "object",
        "surface_confidence": "projected",
        "protocol_availability": "rest_only",
        "fallback_mode": "observe_only",
        "research_basis": ["objects_overview", "protocol_guide"],
    }


def _public_family_summary(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    subtype_counts = Counter(str(row["lattice_subtype"]) for row in records)
    out: list[dict[str, Any]] = []
    for subtype, info in sorted(PUBLIC_FAMILY_RATIONALES.items()):
        out.append(
            {
                "lattice_subtype": subtype,
                "rows": subtype_counts.get(subtype, 0),
                "closest_public_surface": info["closest_public_surface"],
                "rationale": info["rationale"],
                "research_basis": info["research_basis"],
            }
        )
    return out


def _projected_family_backlog(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    subtype_counts = Counter(str(row["lattice_subtype"]) for row in records if row["surface_confidence"] == "projected")
    backlog: list[dict[str, Any]] = []
    for subtype, rows in sorted(subtype_counts.items(), key=lambda item: (-item[1], item[0])):
        info = PUBLIC_FAMILY_RATIONALES.get(subtype)
        if info is None:
            continue
        closest_surface = str(info["closest_public_surface"])
        if closest_surface == "entity":
            next_research = "Inspect publish/watch entity guides and component reference coverage for explicit component-level projections."
        elif closest_surface == "task":
            next_research = "Inspect operate/listen/update task guides and task specification examples for stronger semantic action mappings."
        else:
            next_research = "Inspect object upload/list/delete reference and media-link patterns for sidecar and archive workflows."
        backlog.append(
            {
                "lattice_subtype": subtype,
                "rows": rows,
                "closest_public_surface": closest_surface,
                "next_research": next_research,
            }
        )
    return backlog


def _component_projection(
    pdu_type: int,
    standard_name: str,
    lattice_object: str,
    public_surface: str,
) -> dict[str, Any]:
    info = FAMILY_PROJECTION_CATALOG[lattice_object]
    proof_modes = _row_specific_proof_modes(
        pdu_type,
        standard_name,
        lattice_object,
        list(info["proof_modes"]),
    )
    proof_fixtures = _row_specific_proof_fixtures(
        pdu_type,
        standard_name,
        lattice_object,
        list(info["proof_fixtures"]),
    )
    return {
        "candidate_public_components": list(info["candidate_public_components"]),
        "payload_projection": str(info["payload_projection"]),
        "transport_constraints": list(info["transport_constraints"]),
        "proof_modes": proof_modes,
        "proof_fixtures": proof_fixtures,
        "closest_public_surface": public_surface,
    }


def _component_mapping_summary(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    subtype_counts = Counter(str(row["lattice_subtype"]) for row in records)
    out: list[dict[str, Any]] = []
    for subtype, info in sorted(FAMILY_PROJECTION_CATALOG.items()):
        out.append(
            {
                "lattice_subtype": subtype,
                "rows": subtype_counts.get(subtype, 0),
                "candidate_public_components": list(info["candidate_public_components"]),
                "proof_modes": list(info["proof_modes"]),
                "proof_fixtures": list(info["proof_fixtures"]),
            }
        )
    return out


def _row_justification(
    pdu_type: int,
    standard_name: str,
    lattice_object: str,
    fallback_mode: str,
    loss_policy: str,
    protocol_version: int,
) -> dict[str, Any]:
    if lattice_object == "Entity":
        return {
            "projected_public_payload_kind": "track_entity",
            "why_not_lossless_code": "none",
            "why_not_lossless": "Entity State is the current lossless semantic path.",
        }
    if lattice_object == "EntityLifecycle":
        lowered = standard_name.lower()
        payload_kind = "entity_lifecycle_update"
        if "create entity" in lowered:
            payload_kind = "entity_create_projection"
        elif "remove entity" in lowered:
            payload_kind = "entity_remove_projection"
        elif "entity state update" in lowered:
            payload_kind = "entity_state_update_projection"
        return {
            "projected_public_payload_kind": payload_kind,
            "why_not_lossless_code": "component_subset_only",
            "why_not_lossless": WHY_NOT_LOSSLESS_NOTES["component_subset_only"],
        }
    if lattice_object == "CommunicationObservation":
        name = standard_name.lower()
        payload_kind = "signal_of_interest_entity"
        if "electromagnetic emission" in name:
            payload_kind = "emission_sensor_entity"
        elif "designator" in name:
            payload_kind = "designator_entity"
        elif "transmitter" in name:
            payload_kind = "transmitter_entity"
        elif "receiver" in name:
            payload_kind = "receiver_entity"
        elif "emission" in name:
            payload_kind = "sensor_point_of_interest_entity"
        elif "intercom signal" in name:
            payload_kind = "intercom_signal_annotation"
        elif "intercom control" in name:
            payload_kind = "intercom_control_annotation"
        elif "iff" in name or "intercom" in name:
            payload_kind = "entity_signal_annotation"
        return {
            "projected_public_payload_kind": payload_kind,
            "why_not_lossless_code": "component_subset_only",
            "why_not_lossless": WHY_NOT_LOSSLESS_NOTES["component_subset_only"],
        }
    if lattice_object == "SimulationEvent":
        lowered = standard_name.lower()
        payload_kind = "task_event_projection"
        if "entity damage status" in lowered:
            payload_kind = "task_entity_damage_event"
        elif "directed energy fire" in lowered:
            payload_kind = "task_directed_energy_fire_event"
        elif "le fire" in lowered:
            payload_kind = "task_le_fire_event"
        elif "le detonation" in lowered:
            payload_kind = "task_le_detonation_event"
        elif "collision-elastic" in lowered:
            payload_kind = "task_collision_elastic_event"
        return {
            "projected_public_payload_kind": payload_kind,
            "why_not_lossless_code": "event_model_gap",
            "why_not_lossless": WHY_NOT_LOSSLESS_NOTES["event_model_gap"],
        }
    if lattice_object == "EntityRelationship":
        lowered = standard_name.lower()
        payload_kind = "entity_relationship_projection"
        if "aggregate state" in lowered:
            payload_kind = "entity_aggregate_projection"
        elif "isgroupof" in lowered:
            payload_kind = "entity_group_membership_projection"
        elif "ispartof" in lowered:
            payload_kind = "entity_part_relationship_projection"
        return {
            "projected_public_payload_kind": payload_kind,
            "why_not_lossless_code": "no_public_relationship_schema",
            "why_not_lossless": WHY_NOT_LOSSLESS_NOTES["no_public_relationship_schema"],
        }
    if lattice_object == "EnvironmentObservation":
        payload_kind = "geo_entity_region"
        lowered = standard_name.lower()
        if "point" in lowered:
            payload_kind = "geo_entity_point"
        elif "linear" in lowered:
            payload_kind = "geo_entity_line"
        elif "gridded" in lowered:
            payload_kind = "geo_grid_overlay"
        elif "areal" in lowered:
            payload_kind = "geo_entity_polygon"
        return {
            "projected_public_payload_kind": payload_kind,
            "why_not_lossless_code": "component_subset_only",
            "why_not_lossless": WHY_NOT_LOSSLESS_NOTES["component_subset_only"],
        }
    if lattice_object == "HazardObservation":
        lowered = standard_name.lower()
        payload_kind = "geo_entity_hazard_region"
        if "query" in lowered:
            payload_kind = "geo_minefield_query_overlay"
        elif "data" in lowered:
            payload_kind = "geo_minefield_data_overlay"
        elif "nack" in lowered:
            payload_kind = "geo_minefield_response_nack"
        return {
            "projected_public_payload_kind": payload_kind,
            "why_not_lossless_code": "component_subset_only",
            "why_not_lossless": WHY_NOT_LOSSLESS_NOTES["component_subset_only"],
        }
    if lattice_object == "InformationOperationsObservation":
        if pdu_type == 72:
            payload_kind = "object_archive_projection"
        elif "report" in standard_name.lower():
            payload_kind = "task_information_operation_report"
        else:
            payload_kind = "task_information_operation_action"
        return {
            "projected_public_payload_kind": payload_kind,
            "why_not_lossless_code": "dis7_only_target_gap" if protocol_version == 7 else "task_schema_gap",
            "why_not_lossless": WHY_NOT_LOSSLESS_NOTES["dis7_only_target_gap"] if protocol_version == 7 else WHY_NOT_LOSSLESS_NOTES["task_schema_gap"],
        }
    if lattice_object == "LogisticsObservation":
        lowered = standard_name.lower()
        payload_kind = "task_logistics_action"
        if "service" in lowered:
            payload_kind = "task_service_action"
        elif "resupply offer" in lowered:
            payload_kind = "task_resupply_offer_action"
        elif "resupply received" in lowered:
            payload_kind = "task_resupply_received_action"
        elif "resupply cancel" in lowered:
            payload_kind = "task_resupply_cancel_action"
        elif "resupply" in lowered:
            payload_kind = "task_resupply_action"
        elif "repair complete" in lowered:
            payload_kind = "task_repair_complete_action"
        elif "repair response" in lowered:
            payload_kind = "task_repair_response_action"
        elif "repair" in lowered:
            payload_kind = "task_repair_action"
        return {
            "projected_public_payload_kind": payload_kind,
            "why_not_lossless_code": "task_schema_gap",
            "why_not_lossless": WHY_NOT_LOSSLESS_NOTES["task_schema_gap"],
        }
    if lattice_object == "ObjectArtifact":
        return {
            "projected_public_payload_kind": "raw_object_artifact",
            "why_not_lossless_code": "raw_artifact_source_of_truth",
            "why_not_lossless": WHY_NOT_LOSSLESS_NOTES["raw_artifact_source_of_truth"],
        }
    if lattice_object == "SimulationPduObservation":
        lowered = standard_name.lower()
        payload_kind = "entity_pose_annotation"
        if "appearance" in lowered:
            payload_kind = "entity_visual_state_annotation"
        elif "articulated" in lowered:
            payload_kind = "entity_articulation_annotation"
        return {
            "projected_public_payload_kind": payload_kind,
            "why_not_lossless_code": "component_subset_only",
            "why_not_lossless": WHY_NOT_LOSSLESS_NOTES["component_subset_only"],
        }
    if lattice_object == "TaskOrControlEvent":
        lowered = standard_name.lower()
        payload_kind = "task_lifecycle_control"
        if "start/resume" in lowered:
            payload_kind = "task_start_projection"
        elif "stop/freeze" in lowered:
            payload_kind = "task_freeze_projection"
        elif "action request" in lowered:
            payload_kind = "task_action_request_projection"
        elif "action response" in lowered:
            payload_kind = "task_action_response_projection"
        elif "set data" in lowered:
            payload_kind = "task_set_data_projection"
        elif standard_name in {"Data", "Data-R"}:
            payload_kind = "task_data_payload_projection"
        elif standard_name in {"Record-R"}:
            payload_kind = "task_record_reliable_projection"
        elif standard_name in {"Set Record-R"}:
            payload_kind = "task_set_record_projection"
        elif standard_name in {"Record Query-R"}:
            payload_kind = "task_record_query_projection"
        elif "data query" in lowered:
            payload_kind = "task_data_query_projection"
        elif "comment" in lowered:
            payload_kind = "task_comment_projection"
        elif standard_name == "Acknowledge":
            payload_kind = "task_ack_projection"
        elif standard_name == "Acknowledge-R":
            payload_kind = "task_ack_reliable_projection"
        elif "record" in lowered:
            payload_kind = "task_record_projection"
        elif "data" in lowered or "comment" in lowered:
            payload_kind = "task_message_projection"
        elif "acknowledge" in lowered:
            payload_kind = "task_acknowledgement_projection"
        return {
            "projected_public_payload_kind": payload_kind,
            "why_not_lossless_code": "task_schema_gap",
            "why_not_lossless": WHY_NOT_LOSSLESS_NOTES["task_schema_gap"],
        }
    return {
        "projected_public_payload_kind": fallback_mode,
        "why_not_lossless_code": "component_subset_only" if loss_policy != "structured" else "none",
        "why_not_lossless": WHY_NOT_LOSSLESS_NOTES["component_subset_only"] if loss_policy != "structured" else "Entity State is the current lossless semantic path.",
    }


def _row_specific_proof_fixtures(
    pdu_type: int,
    standard_name: str,
    lattice_object: str,
    family_proof_fixtures: list[str],
) -> list[str]:
    if lattice_object == "CommunicationObservation":
        if pdu_type == 23:
            return [
                "integrations/lattice/examples/lattice_em_observation_fixture.json",
                "integrations/lattice/examples/object_fixture.json",
            ]
        if pdu_type == 24:
            return [
                "integrations/lattice/examples/lattice_designator_fixture.json",
                "integrations/lattice/examples/object_fixture.json",
            ]
        if pdu_type == 25:
            return [
                "integrations/lattice/examples/lattice_transmitter_fixture.json",
                "integrations/lattice/examples/object_fixture.json",
            ]
        if pdu_type == 27:
            return [
                "integrations/lattice/examples/lattice_receiver_fixture.json",
                "integrations/lattice/examples/object_fixture.json",
            ]
        if pdu_type == 30:
            return [
                "integrations/lattice/examples/lattice_emission_fixture.json",
                "integrations/lattice/examples/object_fixture.json",
            ]
        if pdu_type == 28:
            return [
                "integrations/lattice/examples/lattice_annotation_fixture.json",
                "integrations/lattice/examples/object_fixture.json",
            ]
        if pdu_type == 31:
            return [
                "integrations/lattice/examples/lattice_intercom_signal_fixture.json",
                "integrations/lattice/examples/object_fixture.json",
            ]
        if pdu_type == 32:
            return [
                "integrations/lattice/examples/lattice_intercom_control_fixture.json",
                "integrations/lattice/examples/object_fixture.json",
            ]
        if pdu_type == 29:
            return [
                "integrations/lattice/examples/lattice_underwater_signal_fixture.json",
                "integrations/lattice/examples/object_fixture.json",
            ]
        return family_proof_fixtures
    if lattice_object == "EnvironmentObservation":
        lowered = standard_name.lower()
        if "environmental process" in lowered:
            return [
                "integrations/lattice/examples/lattice_geo_environment_process_fixture.json",
                "integrations/lattice/examples/object_fixture.json",
            ]
        if "gridded" in lowered:
            return [
                "integrations/lattice/examples/lattice_geo_grid_fixture.json",
                "integrations/lattice/examples/object_fixture.json",
            ]
        if "point" in lowered:
            return [
                "integrations/lattice/examples/lattice_geo_point_fixture.json",
                "integrations/lattice/examples/object_fixture.json",
            ]
        if "linear" in lowered:
            return [
                "integrations/lattice/examples/lattice_geo_line_fixture.json",
                "integrations/lattice/examples/object_fixture.json",
            ]
        if "areal" in lowered:
            return [
                "integrations/lattice/examples/lattice_geo_areal_fixture.json",
                "integrations/lattice/examples/object_fixture.json",
            ]
        return family_proof_fixtures
    if lattice_object == "HazardObservation":
        if pdu_type == 38:
            return [
                "integrations/lattice/examples/lattice_geo_minefield_query_fixture.json",
                "integrations/lattice/examples/object_fixture.json",
            ]
        if pdu_type == 39:
            return [
                "integrations/lattice/examples/lattice_geo_minefield_data_fixture.json",
                "integrations/lattice/examples/object_fixture.json",
            ]
        if pdu_type == 40:
            return [
                "integrations/lattice/examples/lattice_geo_minefield_nack_fixture.json",
                "integrations/lattice/examples/object_fixture.json",
            ]
        return family_proof_fixtures
    if lattice_object == "EntityRelationship":
        lowered = standard_name.lower()
        if pdu_type == 35:
            return [
                "integrations/lattice/examples/lattice_relationship_ownership_fixture.json",
                "integrations/lattice/examples/object_fixture.json",
            ]
        if "aggregate state" in lowered:
            return [
                "integrations/lattice/examples/lattice_aggregate_state_fixture.json",
                "integrations/lattice/examples/object_fixture.json",
            ]
        if "isgroupof" in lowered:
            return [
                "integrations/lattice/examples/lattice_is_group_of_fixture.json",
                "integrations/lattice/examples/object_fixture.json",
            ]
        if "ispartof" in lowered:
            return [
                "integrations/lattice/examples/lattice_is_part_of_fixture.json",
                "integrations/lattice/examples/object_fixture.json",
            ]
        return family_proof_fixtures
    if lattice_object == "SimulationEvent":
        lowered = standard_name.lower()
        if "entity damage status" in lowered:
            return [
                "integrations/lattice/examples/lattice_entity_damage_fixture.json",
                "integrations/lattice/examples/object_fixture.json",
            ]
        if "directed energy fire" in lowered:
            return [
                "integrations/lattice/examples/lattice_event_directed_energy_fire_fixture.json",
                "integrations/lattice/examples/object_fixture.json",
            ]
        if "le fire" in lowered:
            return [
                "integrations/lattice/examples/lattice_event_le_fire_fixture.json",
                "integrations/lattice/examples/object_fixture.json",
            ]
        if "fire" in lowered:
            return [
                "integrations/lattice/examples/lattice_event_fire_fixture.json",
                "integrations/lattice/examples/object_fixture.json",
            ]
        if "le detonation" in lowered:
            return [
                "integrations/lattice/examples/lattice_event_le_detonation_fixture.json",
                "integrations/lattice/examples/object_fixture.json",
            ]
        if "detonation" in lowered:
            return [
                "integrations/lattice/examples/lattice_event_detonation_fixture.json",
                "integrations/lattice/examples/object_fixture.json",
            ]
        if "collision-elastic" in lowered:
            return [
                "integrations/lattice/examples/lattice_event_collision_elastic_fixture.json",
                "integrations/lattice/examples/object_fixture.json",
            ]
        if "collision" in lowered:
            return [
                "integrations/lattice/examples/lattice_event_collision_fixture.json",
                "integrations/lattice/examples/object_fixture.json",
            ]
    if lattice_object == "TaskOrControlEvent":
        lowered = standard_name.lower()
        if "event report" in lowered:
            return ["integrations/lattice/examples/lattice_task_event_report_fixture.json"]
        if pdu_type in {51, 52}:
            return ["integrations/lattice/examples/lattice_task_entity_reliable_fixture.json"]
        if standard_name == "Acknowledge":
            return ["integrations/lattice/examples/lattice_task_ack_only_fixture.json"]
        if standard_name == "Acknowledge-R":
            return ["integrations/lattice/examples/lattice_task_ack_reliable_fixture.json"]
        if "start/resume" in lowered:
            return ["integrations/lattice/examples/lattice_task_start_fixture.json"]
        if "stop/freeze" in lowered:
            return ["integrations/lattice/examples/lattice_task_freeze_fixture.json"]
        if "action request" in lowered:
            return ["integrations/lattice/examples/lattice_task_action_request_fixture.json"]
        if "action response" in lowered:
            return ["integrations/lattice/examples/lattice_task_action_response_fixture.json"]
        if "set data" in lowered:
            return ["integrations/lattice/examples/lattice_task_set_data_fixture.json"]
        if standard_name in {"Data", "Data-R"}:
            return ["integrations/lattice/examples/lattice_task_data_payload_fixture.json"]
        if "data query" in lowered:
            return ["integrations/lattice/examples/lattice_task_data_query_fixture.json"]
        if "comment" in lowered:
            return ["integrations/lattice/examples/lattice_task_comment_fixture.json"]
        if standard_name == "Record-R":
            return ["integrations/lattice/examples/lattice_task_record_r_fixture.json"]
        if standard_name == "Set Record-R":
            return ["integrations/lattice/examples/lattice_task_set_record_fixture.json"]
        if standard_name == "Record Query-R":
            return ["integrations/lattice/examples/lattice_task_record_query_fixture.json"]
        if "record" in lowered:
            return ["integrations/lattice/examples/lattice_task_record_fixture.json"]
        if any(token in lowered for token in ("start/resume", "stop/freeze", "action request", "action response", "acknowledge")):
            return ["integrations/lattice/examples/lattice_task_control_fixture.json"]
        if any(token in lowered for token in ("data", "record", "comment", "query")):
            return ["integrations/lattice/examples/lattice_task_message_fixture.json"]
        return family_proof_fixtures
    if lattice_object == "LogisticsObservation":
        lowered = standard_name.lower()
        if "service request" in lowered:
            return [
                "integrations/lattice/examples/lattice_task_service_fixture.json",
                "integrations/lattice/examples/object_fixture.json",
            ]
        if "resupply offer" in lowered:
            return [
                "integrations/lattice/examples/lattice_task_resupply_offer_fixture.json",
                "integrations/lattice/examples/object_fixture.json",
            ]
        if "resupply received" in lowered:
            return [
                "integrations/lattice/examples/lattice_task_resupply_received_fixture.json",
                "integrations/lattice/examples/object_fixture.json",
            ]
        if "resupply cancel" in lowered:
            return [
                "integrations/lattice/examples/lattice_task_resupply_cancel_fixture.json",
                "integrations/lattice/examples/object_fixture.json",
            ]
        if "resupply" in lowered:
            return [
                "integrations/lattice/examples/lattice_task_resupply_fixture.json",
                "integrations/lattice/examples/object_fixture.json",
            ]
        if "repair complete" in lowered:
            return [
                "integrations/lattice/examples/lattice_task_repair_complete_fixture.json",
                "integrations/lattice/examples/object_fixture.json",
            ]
        if "repair response" in lowered:
            return [
                "integrations/lattice/examples/lattice_task_repair_response_fixture.json",
                "integrations/lattice/examples/object_fixture.json",
            ]
        if "repair" in lowered:
            return [
                "integrations/lattice/examples/lattice_task_repair_fixture.json",
                "integrations/lattice/examples/object_fixture.json",
            ]
        return [
            "integrations/lattice/examples/lattice_task_logistics_fixture.json",
            "integrations/lattice/examples/object_fixture.json",
        ]
    if lattice_object == "InformationOperationsObservation":
        lowered = standard_name.lower()
        if pdu_type == 72:
            return [
                "integrations/lattice/examples/lattice_attribute_fixture.json",
                "integrations/lattice/examples/object_fixture.json",
            ]
        if "report" in lowered:
            return [
                "integrations/lattice/examples/lattice_info_ops_report_fixture.json",
                "integrations/lattice/examples/object_fixture.json",
            ]
        return [
            "integrations/lattice/examples/lattice_info_ops_action_fixture.json",
            "integrations/lattice/examples/object_fixture.json",
        ]
    if lattice_object == "SimulationPduObservation":
        lowered = standard_name.lower()
        if "tspi" in lowered:
            return [
                "integrations/lattice/examples/lattice_tspi_fixture.json",
                "integrations/lattice/examples/object_fixture.json",
            ]
        if "appearance" in lowered:
            return [
                "integrations/lattice/examples/lattice_appearance_fixture.json",
                "integrations/lattice/examples/object_fixture.json",
            ]
        if "articulated" in lowered:
            return [
                "integrations/lattice/examples/lattice_articulated_parts_fixture.json",
                "integrations/lattice/examples/object_fixture.json",
            ]
    if lattice_object == "EntityLifecycle":
        lowered = standard_name.lower()
        if "create entity" in lowered:
            return [
                "integrations/lattice/examples/lattice_create_entity_fixture.json",
                "integrations/lattice/examples/object_fixture.json",
            ]
        if "remove entity" in lowered:
            return [
                "integrations/lattice/examples/lattice_remove_entity_fixture.json",
                "integrations/lattice/examples/object_fixture.json",
            ]
        if "entity state update" in lowered:
            return [
                "integrations/lattice/examples/lattice_entity_state_update_fixture.json",
                "integrations/lattice/examples/object_fixture.json",
            ]
    return family_proof_fixtures


def _row_specific_proof_modes(
    pdu_type: int,
    standard_name: str,
    lattice_object: str,
    family_proof_modes: list[str],
) -> list[str]:
    if lattice_object == "InformationOperationsObservation" and pdu_type == 72:
        return ["object_fixture_contract", "raw_sidecar_preservation"]
    return family_proof_modes


def _projection_kind_summary(records: list[dict[str, Any]]) -> dict[str, int]:
    return dict(sorted(Counter(str(row["projected_public_payload_kind"]) for row in records).items()))


def _non_lossless_reason_summary(records: list[dict[str, Any]]) -> dict[str, int]:
    return dict(sorted(Counter(str(row["why_not_lossless_code"]) for row in records).items()))


def _proof_depth(version: int, pdu_type: int) -> str:
    key = (version, pdu_type)
    if key in LOSSLESS_ROUNDTRIP_ROWS:
        return "lossless_roundtrip_runtime"
    if key in ARCHIVE_PRESERVATION_ROWS:
        return "archive_preservation_runtime"
    if version in {6, 7} and pdu_type in SEMANTIC_EGRESS_PDU_TYPES_BOTH_VERSIONS:
        return "semantic_egress_runtime"
    if key in SEMANTIC_EGRESS_ROWS:
        return "semantic_egress_runtime"
    return "transport_egress_runtime"


def _proof_depth_summary(records: list[dict[str, Any]]) -> dict[str, int]:
    counts = Counter(str(row["proof_depth"]) for row in records)
    for key in (
        "lossless_roundtrip_runtime",
        "archive_preservation_runtime",
        "semantic_egress_runtime",
        "transport_egress_runtime",
    ):
        counts.setdefault(key, 0)
    return dict(sorted(counts.items()))


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
    lossy_modes = _lossy_modes(int(row["pdu_type"]), lattice_object, str(surface["loss_policy"]))
    public_analogue = _public_analogue(int(row["pdu_type"]), lattice_object, strict_bucket, str(surface["loss_policy"]))
    component_projection = _component_projection(
        int(row["pdu_type"]),
        str(row["standard_name"]),
        lattice_object,
        str(public_analogue["closest_public_surface"]),
    )
    row_justification = _row_justification(
        int(row["pdu_type"]),
        str(row["standard_name"]),
        lattice_object,
        str(public_analogue["fallback_mode"]),
        str(surface["loss_policy"]),
        int(row["protocol_version"]),
    )
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
        **lossy_modes,
        **public_analogue,
        **component_projection,
        "proof_depth": _proof_depth(int(row["protocol_version"]), int(row["pdu_type"])),
        **row_justification,
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
        if not isinstance(row.get("lossy_ingress_supported"), bool):
            issues.append(f"{key} missing lossy_ingress_supported boolean")
        if not isinstance(row.get("lossy_egress_supported"), bool):
            issues.append(f"{key} missing lossy_egress_supported boolean")
        if not str(row.get("lossy_ingress_policy") or "").strip():
            issues.append(f"{key} missing lossy_ingress_policy")
        if not str(row.get("lossy_egress_policy") or "").strip():
            issues.append(f"{key} missing lossy_egress_policy")
        if str(row.get("lossy_mode_class") or "") not in {"strict_only", "ingress_only", "bidirectional"}:
            issues.append(f"{key} has invalid lossy_mode_class {row.get('lossy_mode_class')}")
        if str(row.get("closest_public_surface") or "") not in {"entity", "task", "object", "none"}:
            issues.append(f"{key} has invalid closest_public_surface {row.get('closest_public_surface')}")
        if str(row.get("surface_confidence") or "") not in {"direct", "projected", "archive_only"}:
            issues.append(f"{key} has invalid surface_confidence {row.get('surface_confidence')}")
        if str(row.get("protocol_availability") or "") not in {"rest_only", "rest_and_grpc", "none"}:
            issues.append(f"{key} has invalid protocol_availability {row.get('protocol_availability')}")
        if str(row.get("fallback_mode") or "") not in {"lossless", "projected", "observe_only", "archive_only", "drop_with_receipt"}:
            issues.append(f"{key} has invalid fallback_mode {row.get('fallback_mode')}")
        basis = row.get("research_basis")
        if not isinstance(basis, list) or not basis:
            issues.append(f"{key} missing research_basis")
        components = row.get("candidate_public_components")
        if not isinstance(components, list) or not components:
            issues.append(f"{key} missing candidate_public_components")
        payload_projection = str(row.get("payload_projection") or "").strip()
        if not payload_projection:
            issues.append(f"{key} missing payload_projection")
        constraints = row.get("transport_constraints")
        if not isinstance(constraints, list) or not constraints:
            issues.append(f"{key} missing transport_constraints")
        proof_modes = row.get("proof_modes")
        if not isinstance(proof_modes, list) or not proof_modes:
            issues.append(f"{key} missing proof_modes")
        proof_depth = str(row.get("proof_depth") or "")
        if proof_depth not in {
            "lossless_roundtrip_runtime",
            "archive_preservation_runtime",
            "semantic_egress_runtime",
            "transport_egress_runtime",
        }:
            issues.append(f"{key} invalid proof_depth {proof_depth}")
        proof_fixtures = row.get("proof_fixtures")
        if not isinstance(proof_fixtures, list) or not proof_fixtures:
            issues.append(f"{key} missing proof_fixtures")
        if not str(row.get("projected_public_payload_kind") or "").strip():
            issues.append(f"{key} missing projected_public_payload_kind")
        reason_code = str(row.get("why_not_lossless_code") or "")
        if reason_code not in {"none", *WHY_NOT_LOSSLESS_NOTES.keys()}:
            issues.append(f"{key} has invalid why_not_lossless_code {reason_code}")
        if not str(row.get("why_not_lossless") or "").strip():
            issues.append(f"{key} missing why_not_lossless")
    return issues


def build_plan() -> dict[str, Any]:
    payload = json.loads(SEMANTIC_MANIFEST.read_text(encoding="utf-8"))
    records = [_record(row) for row in payload["records"]]
    strict_buckets = Counter(str(row["strict_lattice_bucket"]) for row in records)
    subtypes = Counter(str(row["lattice_subtype"]) for row in records)
    loss = Counter(str(row["loss_policy"]) for row in records)
    lossy_classes = Counter(str(row["lossy_mode_class"]) for row in records)
    lossy_ingress = Counter("supported" if bool(row["lossy_ingress_supported"]) else "strict_only" for row in records)
    lossy_egress = Counter("supported" if bool(row["lossy_egress_supported"]) else "strict_only" for row in records)
    public_surfaces = Counter(str(row["closest_public_surface"]) for row in records)
    surface_confidence = Counter(str(row["surface_confidence"]) for row in records)
    fallback_modes = Counter(str(row["fallback_mode"]) for row in records)
    return {
        "schema": "fastdis.lattice_dis_mapping_plan.v1",
        "generated_at": "deterministic",
        "source": str(SEMANTIC_MANIFEST.relative_to(ROOT)),
        "policy": {
            "coverage_rule": "Every standard DIS 6/7 PDU row has an explicit Lattice/Zorn ingress and egress policy.",
            "loss_rule": "No row may silently disappear; lossy mappings require diagnostics and raw sidecar preservation where needed.",
            "lossy_mode_rule": "Lossy ingress and lossy egress are tracked separately for every row; lossy egress never implies silent data invention.",
            "public_surface_rule": "Closest-public-surface mappings are grounded in the published Entities, Tasks, Objects, and protocol guides; they describe the nearest public Lattice analogue, not a promise of perfect semantic parity.",
            "objects_rule": "Objects are REST-only; gRPC mappings use entity/task/generic observation streams.",
            "bucket_rule": "Every row must classify into exactly one strict bucket: Entity, Task, Object, or Observation.",
        },
        "summary": {
            "records": len(records),
            "strict_lattice_buckets": dict(sorted(strict_buckets.items())),
            "lattice_subtypes": dict(sorted(subtypes.items())),
            "observation_reduction_targets": _observation_reduction_targets(records),
            "loss_policies": dict(sorted(loss.items())),
            "lossy_mode_classes": dict(sorted(lossy_classes.items())),
            "lossy_ingress_support": dict(sorted(lossy_ingress.items())),
            "lossy_egress_support": dict(sorted(lossy_egress.items())),
            "closest_public_surfaces": dict(sorted(public_surfaces.items())),
            "surface_confidence": dict(sorted(surface_confidence.items())),
            "fallback_modes": dict(sorted(fallback_modes.items())),
            "projection_kinds": _projection_kind_summary(records),
            "non_lossless_reasons": _non_lossless_reason_summary(records),
            "proof_depth": _proof_depth_summary(records),
            "research_source_catalog": RESEARCH_SOURCE_CATALOG,
            "public_family_summary": _public_family_summary(records),
            "projected_family_backlog": _projected_family_backlog(records),
            "component_mapping_summary": _component_mapping_summary(records),
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
            "lossy_mode_class_counts": dict(sorted(Counter(str(row["lossy_mode_class"]) for row in rows).items())),
            "closest_public_surface_counts": dict(sorted(Counter(str(row["closest_public_surface"]) for row in rows).items())),
            "fallback_mode_counts": dict(sorted(Counter(str(row["fallback_mode"]) for row in rows).items())),
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
            "| Bucket | Rows | REST surfaces | gRPC surfaces | Egress modes | Lossy classes | Public surfaces | Fallback modes |",
            "|---|---:|---|---|---|---|---|---|",
        ]
    )
    for bucket, info in plan["summary"]["bucket_conformance"].items():
        lines.append(
            f"| {bucket} | {info['rows']} | {json.dumps(info['rest_surface_kind_counts'], sort_keys=True)} | "
            f"{json.dumps(info['grpc_surface_kind_counts'], sort_keys=True)} | "
            f"{json.dumps(info['egress_conformance_counts'], sort_keys=True)} | "
            f"{json.dumps(info['lossy_mode_class_counts'], sort_keys=True)} | "
            f"{json.dumps(info['closest_public_surface_counts'], sort_keys=True)} | "
            f"{json.dumps(info['fallback_mode_counts'], sort_keys=True)} |"
        )
    lines.extend(
        [
            "",
            "## Lossy Mode Summary",
            "",
            f"- lossy mode classes: `{json.dumps(plan['summary']['lossy_mode_classes'], sort_keys=True)}`",
            f"- lossy ingress support: `{json.dumps(plan['summary']['lossy_ingress_support'], sort_keys=True)}`",
            f"- lossy egress support: `{json.dumps(plan['summary']['lossy_egress_support'], sort_keys=True)}`",
            "",
            "## Public Surface Summary",
            "",
            f"- closest public surfaces: `{json.dumps(plan['summary']['closest_public_surfaces'], sort_keys=True)}`",
            f"- surface confidence: `{json.dumps(plan['summary']['surface_confidence'], sort_keys=True)}`",
            f"- fallback modes: `{json.dumps(plan['summary']['fallback_modes'], sort_keys=True)}`",
            f"- projection kinds: `{json.dumps(plan['summary']['projection_kinds'], sort_keys=True)}`",
            f"- non-lossless reasons: `{json.dumps(plan['summary']['non_lossless_reasons'], sort_keys=True)}`",
            f"- proof depth: `{json.dumps(plan['summary']['proof_depth'], sort_keys=True)}`",
            "",
            "## Public Family Rationale",
            "",
            "| Lattice subtype | Rows | Closest public surface | Research basis | Rationale |",
            "|---|---:|---|---|---|",
        ]
    )
    for item in plan["summary"]["public_family_summary"]:
        lines.append(
            f"| {item['lattice_subtype']} | {item['rows']} | {item['closest_public_surface']} | "
            f"{', '.join(item['research_basis'])} | {item['rationale']} |"
        )
    lines.extend(
        [
            "",
            "## Research Source Catalog",
            "",
            "| Key | Title | URL | Note |",
            "|---|---|---|---|",
        ]
    )
    for key, info in sorted(plan["summary"]["research_source_catalog"].items()):
        lines.append(f"| {key} | {info['title']} | {info['url']} | {info['note']} |")
    lines.extend(
        [
            "",
            "## Projected Family Backlog",
            "",
            "| Lattice subtype | Projected rows | Closest public surface | Next research |",
            "|---|---:|---|---|",
        ]
    )
    for item in plan["summary"]["projected_family_backlog"]:
        lines.append(
            f"| {item['lattice_subtype']} | {item['rows']} | {item['closest_public_surface']} | {item['next_research']} |"
        )
    lines.extend(
        [
            "",
            "## Component Mapping Summary",
            "",
            "| Lattice subtype | Rows | Candidate public components | Proof modes | Proof fixtures |",
            "|---|---:|---|---|---|",
        ]
    )
    for item in plan["summary"]["component_mapping_summary"]:
        lines.append(
            f"| {item['lattice_subtype']} | {item['rows']} | "
            f"{', '.join(item['candidate_public_components'])} | "
            f"{', '.join(item['proof_modes'])} | "
            f"{', '.join(item['proof_fixtures'])} |"
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
            "| DIS | PDU | Name | Strict bucket | Closest public surface | Confidence | Protocols | Fallback | Projection kind | Why not lossless | Proof depth | Lattice subtype | Public components | Proof modes | Lossy class | Lossy ingress | Lossy egress | REST route | gRPC route | Egress | Loss policy |",
            "|---:|---:|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
        ]
    )
    for row in plan["records"]:
        lines.append(
            f"| {row['protocol_version']} | {row['pdu_type']} | {row['standard_name']} | "
            f"{row['strict_lattice_bucket']} | {row['closest_public_surface']} | {row['surface_confidence']} | "
            f"{row['protocol_availability']} | {row['fallback_mode']} | {row['projected_public_payload_kind']} | "
            f"{row['why_not_lossless_code']} | {row['proof_depth']} | {row['lattice_subtype']} | "
            f"{', '.join(row['candidate_public_components'])} | {', '.join(row['proof_modes'])} | {row['lossy_mode_class']} | "
            f"{row['lossy_ingress_policy']} | {row['lossy_egress_policy']} | {row['rest_route']} | {row['grpc_route']} | "
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
