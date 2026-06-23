"""SISO-style enum lookup helpers.

FastDIS treats enumeration labels as advisory metadata. Unknown or locally
extended values are preserved numerically and displayed as ``Unknown(value)``.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .pdu_logging import PDU_LOG_DESCRIPTORS, find_pdu_log_descriptor


UNKNOWN_POLICY = "preserve_numeric_and_label_unknown"
PINNED_REFERENCE = "siso-ref-010-v32"


@dataclass(frozen=True, slots=True)
class EnumValue:
    family: str
    value: int
    label: str
    known: bool
    source: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


PROTOCOL_FAMILY: dict[int, str] = {
    0: "Other",
    1: "Entity Information",
    2: "Warfare",
    3: "Logistics",
    4: "Radio Communications",
    5: "Simulation Management",
    6: "Distributed Emission Regeneration",
    7: "Entity Management",
    8: "Minefield",
    9: "Synthetic Environment",
    10: "Simulation Management with Reliability",
    11: "Live Entity",
    12: "Non-Real-Time",
    13: "Information Operations",
}

FORCE_ID: dict[int, str] = {
    0: "Other",
    1: "Friendly",
    2: "Opposing",
    3: "Neutral",
}

DEAD_RECKONING_ALGORITHM: dict[int, str] = {
    0: "OTHER",
    1: "STATIC",
    2: "DRM_FPW",
    3: "DRM_RPW",
    4: "DRM_RVW",
    5: "DRM_FVW",
    6: "DRM_FPB",
    7: "DRM_RPB",
    8: "DRM_RVB",
    9: "DRM_FVB",
}

ENTITY_KIND: dict[int, str] = {
    0: "Other",
    1: "Platform",
    2: "Munition",
    3: "Life Form",
    4: "Environmental",
    5: "Cultural Feature",
    6: "Supply",
    7: "Radio",
    8: "Expendable",
    9: "Sensor/Emitter",
}

ENTITY_DOMAIN: dict[int, str] = {
    0: "Other",
    1: "Land",
    2: "Air",
    3: "Surface",
    4: "Subsurface",
    5: "Space",
}

COUNTRY: dict[int, str] = {
    0: "Other",
    225: "United States",
}

ENTITY_CATEGORY_HINTS: dict[tuple[int, int, int], str] = {
    (1, 1, 1): "Tank",
    (1, 2, 1): "Fighter/Air Defense",
    (1, 2, 2): "Attack/Strike",
    (1, 2, 3): "Bomber",
    (1, 2, 4): "Cargo/Tanker",
    (1, 2, 5): "ASW/Patrol/Observation",
    (1, 2, 6): "Electronic Warfare",
    (1, 3, 1): "Aircraft Carrier",
    (2, 0, 0): "Munition",
}

TABLES: dict[str, dict[int, str]] = {
    "protocol_family": PROTOCOL_FAMILY,
    "force_id": FORCE_ID,
    "dead_reckoning_algorithm": DEAD_RECKONING_ALGORITHM,
    "entity_kind": ENTITY_KIND,
    "entity_domain": ENTITY_DOMAIN,
    "country": COUNTRY,
}


def unknown_label(value: int) -> str:
    return f"Unknown({value})"


def lookup(family: str, value: int, *, version: int | None = None) -> EnumValue:
    normalized = family.lower().replace("-", "_")
    if normalized in {"pdu", "pdu_type", "pdutype"}:
        if version is None:
            raise ValueError("pdu_type lookup requires version=")
        descriptor = find_pdu_log_descriptor(version, value)
        if descriptor is None:
            return EnumValue("pdu_type", value, unknown_label(value), False, PINNED_REFERENCE)
        return EnumValue("pdu_type", value, descriptor.canonical_name, True, "fastdis_pdu_standard_backbone")
    table = TABLES.get(normalized)
    if table is None:
        raise KeyError(f"Unknown enum family: {family}")
    label = table.get(value)
    return EnumValue(normalized, value, label if label is not None else unknown_label(value), label is not None, PINNED_REFERENCE)


def lookup_entity_type(
    kind: int,
    domain: int,
    country: int,
    category: int,
    subcategory: int,
    specific: int,
    extra: int,
) -> dict[str, Any]:
    category_hint = ENTITY_CATEGORY_HINTS.get((kind, domain, category))
    progressive_keys = [
        f"{kind}.{domain}.{country}.{category}.{subcategory}.{specific}.{extra}",
        f"{kind}.{domain}.{country}.{category}.{subcategory}.{specific}.*",
        f"{kind}.{domain}.{country}.{category}.{subcategory}.*",
        f"{kind}.{domain}.{country}.{category}.*",
        f"{kind}.{domain}.{country}.*",
        f"{kind}.{domain}.*",
    ]
    return {
        "schema": "fastdis.enum.entity_type.v1",
        "source": PINNED_REFERENCE,
        "unknown_policy": UNKNOWN_POLICY,
        "numeric": {
            "kind": kind,
            "domain": domain,
            "country": country,
            "category": category,
            "subcategory": subcategory,
            "specific": specific,
            "extra": extra,
        },
        "components": {
            "kind": lookup("entity_kind", kind).to_dict(),
            "domain": lookup("entity_domain", domain).to_dict(),
            "country": lookup("country", country).to_dict(),
            "category": {
                "family": "entity_category",
                "value": category,
                "label": category_hint if category_hint else unknown_label(category),
                "known": category_hint is not None,
                "source": PINNED_REFERENCE,
            },
            "subcategory": {
                "family": "entity_subcategory",
                "value": subcategory,
                "label": unknown_label(subcategory),
                "known": False,
                "source": PINNED_REFERENCE,
            },
            "specific": {
                "family": "entity_specific",
                "value": specific,
                "label": unknown_label(specific),
                "known": False,
                "source": PINNED_REFERENCE,
            },
            "extra": {
                "family": "entity_extra",
                "value": extra,
                "label": unknown_label(extra),
                "known": False,
                "source": PINNED_REFERENCE,
            },
        },
        "progressive_fallback_keys": progressive_keys,
        "summary": " / ".join(
            [
                lookup("entity_kind", kind).label,
                lookup("entity_domain", domain).label,
                lookup("country", country).label,
                category_hint or f"Category {category}",
            ]
        ),
    }


def pdu_type_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": item.version,
            "value": item.pdu_type,
            "label": item.canonical_name,
            "protocol_family": item.protocol_family,
            "protocol_family_label": item.family_name,
            "source": "fastdis_pdu_standard_backbone",
        }
        for item in PDU_LOG_DESCRIPTORS
    ]


def coverage_manifest() -> dict[str, Any]:
    families = [
        {
            "enum_name": "PduType",
            "values_total": len(PDU_LOG_DESCRIPTORS),
            "values_imported": len(PDU_LOG_DESCRIPTORS),
            "coverage_status": "generated_backbone_complete",
            "source": "fastdis_pdu_standard_backbone",
        },
        *[
            {
                "enum_name": name,
                "values_total": len(table),
                "values_imported": len(table),
                "coverage_status": "tracked_core_values",
                "source": PINNED_REFERENCE,
            }
            for name, table in TABLES.items()
        ],
        {
            "enum_name": "EntityType",
            "values_total": len(ENTITY_CATEGORY_HINTS),
            "values_imported": len(ENTITY_CATEGORY_HINTS),
            "coverage_status": "progressive_fallback_numeric_preserve",
            "source": PINNED_REFERENCE,
        },
    ]
    return {
        "schema": "fastdis.enum_coverage.v1",
        "pinned_reference": PINNED_REFERENCE,
        "unknown_value_policy": UNKNOWN_POLICY,
        "full_siso_ref_010_imported": False,
        "families": families,
    }


def describe_packet_header(version: int, pdu_type: int, protocol_family: int, force_id: int | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema": "fastdis.enum.packet_header_description.v1",
        "version": version,
        "pdu_type": lookup("pdu_type", pdu_type, version=version).to_dict(),
        "protocol_family": lookup("protocol_family", protocol_family).to_dict(),
        "unknown_policy": UNKNOWN_POLICY,
    }
    if force_id is not None:
        payload["force_id"] = lookup("force_id", force_id).to_dict()
    return payload
