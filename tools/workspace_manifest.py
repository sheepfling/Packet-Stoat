#!/usr/bin/env python3
"""Load the manifest that describes Packet Stoat's reusable workspace routes."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any
from string import Formatter

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
    _as_dict(payload.get("route_task_templates") or {}, field="route_task_templates")
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


def route_task_templates(manifest: dict[str, Any] | None = None) -> dict[str, dict[str, Any]]:
    payload = manifest or load_manifest()
    templates = _as_dict(payload.get("route_task_templates") or {}, field="route_task_templates")
    return {str(name): _as_dict(value, field=f"route_task_templates.{name}") for name, value in templates.items()}


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


def _format_string(value: str, parameters: dict[str, str]) -> str:
    formatter = Formatter()
    field_names = [field_name for _, field_name, _, _ in formatter.parse(value) if field_name]
    if not field_names:
        return value
    missing = [field_name for field_name in field_names if field_name not in parameters]
    if missing:
        missing_list = ", ".join(sorted(set(missing)))
        raise ValueError(f"workspace manifest string template is missing parameters: {missing_list}")
    return value.format(**parameters)


def _format_string_list(values: list[Any], parameters: dict[str, str], *, field: str) -> list[str]:
    normalized = _as_list(values, field=field)
    return [_format_string(str(value), parameters) for value in normalized]


def _merge_parameters(base: dict[str, str], override: dict[str, Any], *, field: str) -> dict[str, str]:
    merged = dict(base)
    override_dict = _as_dict(override, field=field)
    for key, value in override_dict.items():
        merged[str(key)] = _format_string(str(value), merged)
    return merged


def route_parameters(route: dict[str, Any], manifest: dict[str, Any] | None = None) -> dict[str, str]:
    surface_id = str(route.get("surface") or "")
    engine = str(route.get("engine") or surface_id)
    target = str(route.get("target") or "")
    backend = str(route.get("backend") or "")
    preferred_surface_version = route_preferred_surface_version(route, manifest)
    parameters = {
        "route_id": str(route.get("id") or ""),
        "route_label": str(route.get("label") or route.get("id") or ""),
        "surface": surface_id,
        "engine": engine,
        "target": target,
        "backend": backend,
        "proof_kind": str(route.get("proof_kind") or ""),
        "preferred_surface_version": preferred_surface_version,
        "surface_version": preferred_surface_version,
        "fastdis_artifact_dir": "",
        "grill_artifact_dir": "",
    }
    if engine:
        parameters["fastdis_artifact_dir"] = f"artifacts/verification_reports/{engine}_fastdis_baseline"
        parameters["grill_artifact_dir"] = f"artifacts/verification_reports/{engine}_grill_baseline"
    raw_parameters = _as_dict(route.get("parameters") or {}, field=f"routes[{route.get('id')}].parameters")
    for key, value in raw_parameters.items():
        parameters[str(key)] = _format_string(str(value), parameters)
    return parameters


def route_commands(route: dict[str, Any], manifest: dict[str, Any] | None = None) -> list[str]:
    parameters = route_parameters(route, manifest)
    return _format_string_list(route.get("commands") or [], parameters, field=f"routes[{route.get('id')}].commands")


def route_evidence_commands(route: dict[str, Any], manifest: dict[str, Any] | None = None) -> list[str]:
    parameters = route_parameters(route, manifest)
    return _format_string_list(
        route.get("evidence_commands") or [],
        parameters,
        field=f"routes[{route.get('id')}].evidence_commands",
    )


def route_tasks(route: dict[str, Any], manifest: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    parameters = route_parameters(route, manifest)
    raw_tasks = route.get("tasks")
    raw_task_template_ids = route.get("task_templates")
    normalized: list[dict[str, Any]] = []
    if raw_tasks is None and raw_task_template_ids is None:
        evidence_commands = route_evidence_commands(route, manifest)
        commands = route_commands(route, manifest)
        if evidence_commands:
            normalized.append(
                {
                    "id": "evidence",
                    "label": "Evidence",
                    "stage": "evidence",
                    "route_family": "default",
                    "parallel_safe": False,
                    "commands": evidence_commands,
                    "artifacts": [],
                    "notes": "",
                }
            )
        if commands:
            normalized.append(
                {
                    "id": "light-up",
                    "label": "Light Up",
                    "stage": "light-up",
                    "route_family": "default",
                    "parallel_safe": False,
                    "commands": commands,
                    "artifacts": [],
                    "notes": "",
                }
            )
        return normalized

    entries: list[tuple[str, dict[str, Any]]] = []
    if raw_task_template_ids is not None:
        template_ids = _as_list(raw_task_template_ids, field=f"routes[{route.get('id')}].task_templates")
        templates = route_task_templates(manifest)
        for index, template_id_value in enumerate(template_ids):
            template_id = str(template_id_value)
            if template_id not in templates:
                raise KeyError(f"route task template '{template_id}' not found for route '{route.get('id')}'")
            entries.append((f"template:{template_id}:{index}", templates[template_id]))
    if raw_tasks is not None:
        values = _as_list(raw_tasks, field=f"routes[{route.get('id')}].tasks")
        for index, value in enumerate(values):
            entry = _as_dict(value, field=f"routes[{route.get('id')}].tasks[{index}]")
            template_id = entry.get("template")
            if template_id is not None:
                templates = route_task_templates(manifest)
                template_name = str(template_id)
                if template_name not in templates:
                    raise KeyError(f"route task template '{template_name}' not found for route '{route.get('id')}'")
                template_parameters = _merge_parameters(
                    parameters,
                    entry.get("parameters") or {},
                    field=f"routes[{route.get('id')}].tasks[{index}].parameters",
                )
                template_entry = dict(templates[template_name])
                template_entry["_parameters"] = template_parameters
                entries.append((f"task-template:{template_name}:{index}", template_entry))
                continue
            entries.append((f"task:{index}", entry))

    for index, (field_key, entry) in enumerate(entries):
        entry_parameters = entry.pop("_parameters", None)
        task_parameters = parameters if not isinstance(entry_parameters, dict) else entry_parameters
        commands = _format_string_list(
            entry.get("commands") or [],
            task_parameters,
            field=f"routes[{route.get('id')}].{field_key}.commands",
        )
        artifacts = _format_string_list(
            entry.get("artifacts") or [],
            task_parameters,
            field=f"routes[{route.get('id')}].{field_key}.artifacts",
        )
        normalized.append(
            {
                "id": _format_string(str(entry.get("id") or f"task-{index + 1}"), task_parameters),
                "label": _format_string(str(entry.get("label") or entry.get("id") or f"Task {index + 1}"), task_parameters),
                "stage": _format_string(str(entry.get("stage") or "custom"), task_parameters),
                "route_family": _format_string(str(entry.get("route_family") or "default"), task_parameters),
                "parallel_safe": bool(entry.get("parallel_safe", False)),
                "commands": commands,
                "artifacts": artifacts,
                "notes": _format_string(str(entry.get("notes") or ""), task_parameters),
            }
        )
    return normalized
