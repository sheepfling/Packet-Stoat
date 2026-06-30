#!/usr/bin/env python3
"""Load the manifest that describes Packet Stoat's reusable workspace routes."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "workspace_manifest.yaml"


def _as_list(value: Any, *, field: str) -> list[Any]:
    if isinstance(value, list):
        return value
    raise ValueError(f"workspace manifest field '{field}' must be a list")


def _as_dict(value: Any, *, field: str) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    raise ValueError(f"workspace manifest field '{field}' must be a mapping")


@lru_cache(maxsize=1)
def load_manifest(path: Path = DEFAULT_MANIFEST) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("workspace manifest must be a top-level mapping")
    if payload.get("schema") != "packet_stoat.workspace_manifest.v1":
        raise ValueError("workspace manifest schema is missing or unsupported")
    _as_dict(payload.get("workspace"), field="workspace")
    _as_dict(payload.get("cross_platform_policy") or {}, field="cross_platform_policy")
    _as_list(payload.get("next_steps") or [], field="next_steps")
    _as_list(payload.get("canonical_surface_hooks") or [], field="canonical_surface_hooks")
    _as_dict(payload.get("canonical_hook_categories") or {}, field="canonical_hook_categories")
    _as_list(payload.get("surfaces"), field="surfaces")
    _as_list(payload.get("routes"), field="routes")
    return payload


def workspace_metadata(manifest: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = manifest or load_manifest()
    return _as_dict(payload["workspace"], field="workspace")


def surface_specs(manifest: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    payload = manifest or load_manifest()
    surfaces = _as_list(payload["surfaces"], field="surfaces")
    return [_as_dict(surface, field="surfaces[]") for surface in surfaces]


def surface_spec(surface_id: str, manifest: dict[str, Any] | None = None) -> dict[str, Any]:
    for surface in surface_specs(manifest):
        if surface.get("id") == surface_id:
            return surface
    raise KeyError(f"surface '{surface_id}' not found in workspace manifest")


def canonical_surface_hooks(manifest: dict[str, Any] | None = None) -> list[str]:
    payload = manifest or load_manifest()
    hooks = _as_list(payload.get("canonical_surface_hooks") or [], field="canonical_surface_hooks")
    return [str(value) for value in hooks]


def canonical_hook_categories(manifest: dict[str, Any] | None = None) -> dict[str, str]:
    payload = manifest or load_manifest()
    categories = _as_dict(payload.get("canonical_hook_categories") or {}, field="canonical_hook_categories")
    normalized = {str(name): str(category) for name, category in categories.items()}
    for hook_name in canonical_surface_hooks(payload):
        if hook_name not in normalized:
            raise ValueError(f"canonical hook '{hook_name}' is missing a category")
    return normalized


def surface_hooks(surface: dict[str, Any], manifest: dict[str, Any] | None = None) -> dict[str, dict[str, str]]:
    hooks = _as_dict(surface.get("hooks") or {}, field=f"surfaces[{surface.get('id')}].hooks")
    categories = canonical_hook_categories(manifest)
    normalized: dict[str, dict[str, str]] = {}
    for hook_name in canonical_surface_hooks(manifest):
        entry = hooks.get(hook_name)
        if entry is None:
            normalized[hook_name] = {
                "category": categories[hook_name],
                "status": "unsupported",
                "command": "",
                "notes": "This surface does not currently declare this canonical hook.",
                "requirements": [],
                "remediation": [],
            }
            continue
        if isinstance(entry, str):
            normalized[hook_name] = {
                "category": categories[hook_name],
                "status": "supported",
                "command": str(entry),
                "notes": "",
                "requirements": [],
                "remediation": [],
            }
            continue
        entry_dict = _as_dict(entry, field=f"surfaces[{surface.get('id')}].hooks.{hook_name}")
        normalized[hook_name] = {
            "category": str(entry_dict.get("category") or categories[hook_name]),
            "status": str(entry_dict.get("status") or "supported"),
            "command": str(entry_dict.get("command") or ""),
            "notes": str(entry_dict.get("notes") or ""),
            "requirements": hook_requirements(surface, hook_name, manifest),
            "remediation": [str(value) for value in _as_list(entry_dict.get("remediation") or [], field=f"surfaces[{surface.get('id')}].hooks.{hook_name}.remediation")],
        }
    return normalized


def surface_preferred_version(surface: dict[str, Any], manifest: dict[str, Any] | None = None) -> str:
    del manifest  # surface-local metadata; kept for API symmetry
    preferred = surface.get("preferred_version")
    if preferred is not None:
        return str(preferred)
    raw_versions = _as_list(surface.get("supported_versions") or [], field=f"surfaces[{surface.get('id')}].supported_versions")
    for index, value in enumerate(raw_versions):
        if isinstance(value, str):
            if index == 0:
                return value
            continue
        entry = _as_dict(value, field=f"surfaces[{surface.get('id')}].supported_versions[{index}]")
        if str(entry.get("status") or "") == "preferred":
            return str(entry.get("version") or "")
        if index == 0 and entry.get("version") is not None:
            preferred = str(entry["version"])
    if preferred is not None:
        return preferred
    return ""


def surface_versions(surface: dict[str, Any], manifest: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    del manifest  # surface-local metadata; kept for API symmetry
    preferred = surface_preferred_version(surface)
    raw_versions = surface.get("supported_versions") or []
    values = _as_list(raw_versions, field=f"surfaces[{surface.get('id')}].supported_versions")
    normalized: list[dict[str, Any]] = []
    for index, value in enumerate(values):
        if isinstance(value, str):
            version = value
            status = "preferred" if value == preferred else "supported"
            notes = ""
            aliases: list[str] = []
        else:
            entry = _as_dict(value, field=f"surfaces[{surface.get('id')}].supported_versions[{index}]")
            if "version" not in entry:
                raise ValueError(f"surface '{surface.get('id')}' version entry at index {index} is missing 'version'")
            version = str(entry["version"])
            status = str(entry.get("status") or ("preferred" if version == preferred else "supported"))
            notes = str(entry.get("notes") or "")
            aliases = [str(alias) for alias in _as_list(entry.get("aliases") or [], field=f"surfaces[{surface.get('id')}].supported_versions[{index}].aliases")]
        normalized.append(
            {
                "version": str(version),
                "status": status,
                "notes": notes,
                "aliases": aliases,
                "preferred": str(version) == preferred or status == "preferred",
            }
        )
    return normalized


def cross_platform_policy(host_class: str, manifest: dict[str, Any] | None = None) -> list[str]:
    payload = manifest or load_manifest()
    policies = _as_dict(payload.get("cross_platform_policy") or {}, field="cross_platform_policy")
    default_values = _as_list(policies.get("default") or [], field="cross_platform_policy.default")
    host_values = _as_list(policies.get(host_class) or [], field=f"cross_platform_policy.{host_class}")
    return [str(value) for value in [*default_values, *host_values]]


def next_steps(manifest: dict[str, Any] | None = None) -> list[str]:
    payload = manifest or load_manifest()
    steps = _as_list(payload.get("next_steps") or [], field="next_steps")
    return [str(step) for step in steps]


def route_specs(manifest: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    payload = manifest or load_manifest()
    routes = _as_list(payload["routes"], field="routes")
    return [_as_dict(route, field="routes[]") for route in routes]


def route_spec(route_id: str, manifest: dict[str, Any] | None = None) -> dict[str, Any]:
    for route in route_specs(manifest):
        if route.get("id") == route_id:
            return route
    raise KeyError(f"route '{route_id}' not found in workspace manifest")


def route_supported_on_host(route: dict[str, Any], host_class: str) -> bool:
    supported = route.get("supported_host_classes") or []
    return host_class in supported


def route_preferred_surface_version(route: dict[str, Any], manifest: dict[str, Any] | None = None) -> str:
    preferred = route.get("preferred_surface_version")
    if preferred is not None:
        return str(preferred)
    surface_id = str(route.get("surface") or "")
    if not surface_id:
        return ""
    return surface_preferred_version(surface_spec(surface_id, manifest), manifest)


def route_supported_surface_versions(route: dict[str, Any], manifest: dict[str, Any] | None = None) -> list[str]:
    raw_versions = route.get("supported_surface_versions")
    if raw_versions is not None:
        return [
            str(value)
            for value in _as_list(raw_versions, field=f"routes[{route.get('id')}].supported_surface_versions")
        ]
    surface_id = str(route.get("surface") or "")
    if not surface_id:
        return []
    return [version["version"] for version in surface_versions(surface_spec(surface_id, manifest), manifest)]


def route_installs(route: dict[str, Any], host_class: str) -> list[str]:
    installs = _as_dict(route.get("required_installs") or {}, field=f"routes[{route.get('id')}].required_installs")
    values = installs.get(host_class) or []
    return [str(value) for value in _as_list(values, field=f"routes[{route.get('id')}].required_installs.{host_class}")]


def route_install_commands(route: dict[str, Any], host_class: str) -> list[str]:
    commands = _as_dict(route.get("install_commands") or {}, field=f"routes[{route.get('id')}].install_commands")
    values = commands.get(host_class) or []
    return [str(value) for value in _as_list(values, field=f"routes[{route.get('id')}].install_commands.{host_class}")]


def route_setup_steps(route: dict[str, Any], host_class: str) -> list[str]:
    steps = _as_dict(route.get("setup_steps") or {}, field=f"routes[{route.get('id')}].setup_steps")
    values = steps.get(host_class) or []
    return [str(value) for value in _as_list(values, field=f"routes[{route.get('id')}].setup_steps.{host_class}")]


def hook_requirements(surface: dict[str, Any], hook_name: str, manifest: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    del manifest  # surface-local metadata; kept for API symmetry
    hooks = _as_dict(surface.get("hooks") or {}, field=f"surfaces[{surface.get('id')}].hooks")
    entry = hooks.get(hook_name)
    if not isinstance(entry, dict):
        return []
    values = _as_list(entry.get("requirements") or [], field=f"surfaces[{surface.get('id')}].hooks.{hook_name}.requirements")
    return [_as_dict(value, field=f"surfaces[{surface.get('id')}].hooks.{hook_name}.requirements[]") for value in values]


def route_requirements(route: dict[str, Any], manifest: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    del manifest
    values = _as_list(route.get("requirements") or [], field=f"routes[{route.get('id')}].requirements")
    return [_as_dict(value, field=f"routes[{route.get('id')}].requirements[]") for value in values]


def route_bootstrap_capable(route: dict[str, Any]) -> bool:
    return bool(route.get("bootstrap_capable", False))
