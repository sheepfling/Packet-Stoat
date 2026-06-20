from __future__ import annotations

from importlib.metadata import EntryPoint, entry_points
from typing import Any


ENTRY_POINT_GROUPS = {
    "packet_sources": "fastdis.packet_sources",
    "entity_publishers": "fastdis.entity_publishers",
    "entity_streams": "fastdis.entity_streams",
    "consumers": "fastdis.consumers",
    "workflows": "fastdis.workflows",
    "reporters": "fastdis.reporters",
}


def entry_point_group(kind: str) -> str:
    try:
        return ENTRY_POINT_GROUPS[kind]
    except KeyError as exc:
        known = ", ".join(sorted(ENTRY_POINT_GROUPS))
        raise ValueError(f"unknown fastdis plugin kind {kind!r}; expected one of: {known}") from exc


def list_entry_points(kind: str) -> dict[str, EntryPoint]:
    group = entry_point_group(kind)
    return {entry_point.name: entry_point for entry_point in entry_points(group=group)}


def load_entry_points(kind: str) -> dict[str, Any]:
    return {name: entry_point.load() for name, entry_point in list_entry_points(kind).items()}


__all__ = [
    "ENTRY_POINT_GROUPS",
    "entry_point_group",
    "list_entry_points",
    "load_entry_points",
]
