"""FastDIS tactical symbol descriptor helpers.

This package intentionally stays separate from ``fastdis`` core. It can depend
on FastDIS protocol identity records, but FastDIS core must never depend on this
package or any renderer/baker dependency.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping


ENTITY_TYPE_KEYS = ("kind", "domain", "country", "category", "subcategory", "specific", "extra")


@dataclass(frozen=True, slots=True)
class SymbolDescriptor:
    """Renderer-neutral tactical symbol selection result."""

    standard: str
    affiliation: str
    symbol_set: str
    sidc: str | None
    entity_type: str
    label: str
    confidence: str
    rule_id: str


@dataclass(frozen=True, slots=True)
class SymbolModifiers:
    """Renderer-facing tactical symbol modifiers."""

    unique_designation: str | None = None
    direction_degrees: float | None = None
    quantity: int | None = None
    staff_comments: str | None = None
    status: str = "present"


@dataclass(frozen=True, slots=True)
class PositionEcef:
    """Optional symbol placement in DIS ECEF meters."""

    x_m: float
    y_m: float
    z_m: float


@dataclass(frozen=True, slots=True)
class SymbolHandoff:
    """Small renderer handoff object for maps, engines, and atlas lookup."""

    descriptor: SymbolDescriptor
    modifiers: SymbolModifiers
    position_ecef_m: PositionEcef | None = None
    atlas_key: str | None = None


def descriptor_from_mapping(payload: Mapping[str, object]) -> SymbolDescriptor:
    """Build a descriptor from a validated mapping payload."""

    return SymbolDescriptor(
        standard=str(payload.get("standard", "MIL-STD-2525")),
        affiliation=str(payload.get("affiliation", "unknown")),
        symbol_set=str(payload.get("symbol_set", "unknown")),
        sidc=str(payload["sidc"]) if payload.get("sidc") is not None else None,
        entity_type=str(payload.get("entity_type", "unknown")),
        label=str(payload.get("label", "Unknown")),
        confidence=str(payload.get("confidence", "policy")),
        rule_id=str(payload.get("rule_id", "unknown")),
    )


def _int_from_mapping(mapping: Mapping[str, object], key: str) -> int:
    return _coerce_int(mapping.get(key, 0))


def _coerce_int(value: object) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str):
        return int(value, 10)
    return 0


def normalize_entity_type(value: object) -> tuple[int, int, int, int, int, int, int]:
    """Normalize a DIS entity type tuple from string, mapping, or sequence input."""

    if isinstance(value, str):
        parts = value.split(".")
        if len(parts) != 7:
            raise ValueError("entity_type string must contain seven DIS fields")
        return tuple(int(part, 10) for part in parts)  # type: ignore[return-value]
    if isinstance(value, Mapping):
        return tuple(_int_from_mapping(value, key) for key in ENTITY_TYPE_KEYS)  # type: ignore[return-value]
    if isinstance(value, (tuple, list)) and len(value) == 7:
        return tuple(int(part) for part in value)  # type: ignore[return-value]
    raise ValueError("entity_type must be a seven-field string, mapping, or sequence")


def entity_type_to_string(entity_type: tuple[int, int, int, int, int, int, int]) -> str:
    """Render a normalized entity type tuple as DIS dotted notation."""

    return ".".join(str(part) for part in entity_type)


def affiliation_from_force_id(force_id: object) -> str:
    """Map DIS Force ID to a tactical affiliation policy label."""

    try:
        numeric = _coerce_int(force_id)
    except (TypeError, ValueError):
        numeric = 0
    return {
        1: "friendly",
        2: "hostile",
        3: "neutral",
    }.get(numeric, "unknown")


def symbol_set_from_entity_type(entity_type: tuple[int, int, int, int, int, int, int]) -> tuple[str, str, str]:
    """Return symbol set, human label, and rule id for a DIS entity type."""

    kind, domain, *_rest = entity_type
    if kind == 1 and domain == 1:
        return "land", "Land platform", "dis-platform-land-generic"
    if kind == 1 and domain == 2:
        return "air", "Air platform", "dis-platform-air-generic"
    if kind == 1 and domain == 3:
        return "surface", "Surface platform", "dis-platform-surface-generic"
    if kind == 1 and domain == 4:
        return "subsurface", "Subsurface platform", "dis-platform-subsurface-generic"
    if kind == 1 and domain == 5:
        return "space", "Space platform", "dis-platform-space-generic"
    return "unknown", "Unknown entity", "dis-entity-generic"


def _marking_text(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, bytes):
        text = value.decode("ascii", errors="ignore")
    elif isinstance(value, (list, tuple)):
        text = bytes(int(part) for part in value).decode("ascii", errors="ignore")
    else:
        text = str(value)
    text = text.replace("\x00", "").strip()
    return text or None


def _heading_from_orientation(value: object) -> float | None:
    if not isinstance(value, Mapping):
        return None
    psi = value.get("psi")
    if psi is None:
        return None
    try:
        return math.degrees(float(psi)) % 360.0
    except (TypeError, ValueError):
        return None


def _position_from_location(value: object) -> PositionEcef | None:
    if not isinstance(value, Mapping):
        return None
    try:
        return PositionEcef(
            x_m=float(value["x"]),
            y_m=float(value["y"]),
            z_m=float(value["z"]),
        )
    except (KeyError, TypeError, ValueError):
        return None


def resolve_from_entity_state(entity_state: Mapping[str, object]) -> SymbolHandoff:
    """Resolve a renderer handoff from DIS Entity State identity metadata.

    The compact FastDIS transform shape is intentionally not enough here: the
    input must include the seven-field ``entity_type`` identity tuple.
    """

    if "entity_type" not in entity_state:
        raise ValueError("entity_type is required; compact transform output is insufficient for symbology")
    entity_type = normalize_entity_type(entity_state["entity_type"])
    entity_type_text = entity_type_to_string(entity_type)
    symbol_set, label, rule_id = symbol_set_from_entity_type(entity_type)
    marking = _marking_text(entity_state.get("marking"))
    descriptor = SymbolDescriptor(
        standard="generic",
        affiliation=affiliation_from_force_id(entity_state.get("force_id", 0)),
        symbol_set=symbol_set,
        sidc=None,
        entity_type=entity_type_text,
        label=label,
        confidence="fallback" if symbol_set != "unknown" else "unknown",
        rule_id=rule_id,
    )
    modifiers = SymbolModifiers(
        unique_designation=marking,
        direction_degrees=_heading_from_orientation(entity_state.get("orientation_rad")),
        status="present",
    )
    atlas_key = f"{descriptor.standard}:{descriptor.affiliation}:{descriptor.symbol_set}:{descriptor.sidc or 'none'}"
    return SymbolHandoff(
        descriptor=descriptor,
        modifiers=modifiers,
        position_ecef_m=_position_from_location(entity_state.get("location_ecef_m")),
        atlas_key=atlas_key,
    )


__all__ = [
    "PositionEcef",
    "SymbolDescriptor",
    "SymbolHandoff",
    "SymbolModifiers",
    "affiliation_from_force_id",
    "descriptor_from_mapping",
    "entity_type_to_string",
    "normalize_entity_type",
    "resolve_from_entity_state",
    "symbol_set_from_entity_type",
]
