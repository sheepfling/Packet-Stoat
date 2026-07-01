#!/usr/bin/env python3
"""Summarize which FastDIS routes are workable on the current host."""

from __future__ import annotations

import argparse
import build_unity_grill_baseline_status
import build_unreal_grill_baseline_status
import grill_paths
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
from typing import Any

import path_compat
import godot_env
import load_local_env
import unity_env
import unreal_env
import unreal_workflow
import windows_wheel_workflow
from test_shards import host_facts
import workspace_manifest
import workspace_requirement_eval
import host_profile


ROOT = Path(__file__).resolve().parents[1]
UNREAL_LINUX_PROFILES = ROOT / "tools" / "unreal_linux_profiles"
LINUX_ZIG_TOOLCHAIN = ROOT / "cmake" / "toolchains" / "linux-x86_64-zig.cmake"


def _status(ok: bool, partial: bool = False) -> str:
    if ok:
        return "ready"
    if partial:
        return "partial"
    return "unavailable"


def _clean_probe_text(text: str) -> str:
    return text.replace("\x00", "").strip()


def _resolve_existing_or_default(path: Path) -> Path:
    return path_compat.resolve_existing(path) or path


def _docker_probe() -> dict[str, str]:
    docker = shutil.which("docker")
    if not docker:
        return {
            "status": "unavailable",
            "executable": "",
            "detail": "docker executable not found on PATH",
        }
    try:
        completed = subprocess.run(
            ["docker", "info", "--format", "{{.ServerVersion}}"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return {
            "status": "partial",
            "executable": docker,
            "detail": f"docker executable exists but probe failed: {exc}",
        }
    output = _clean_probe_text(completed.stdout or completed.stderr or "")
    if completed.returncode == 0:
        version = output or "reachable"
        return {
            "status": "ready",
            "executable": docker,
            "detail": f"docker daemon reachable ({version})",
        }
    detail = output.splitlines()[0] if output else "docker daemon not reachable"
    return {
        "status": "partial",
        "executable": docker,
        "detail": detail,
    }


def _wsl_probe() -> dict[str, str]:
    if platform.system().lower() != "windows":
        return {
            "status": "unavailable",
            "executable": "",
            "detail": "WSL is only relevant on Windows hosts",
        }
    wsl = shutil.which("wsl")
    if not wsl:
        return {
            "status": "unavailable",
            "executable": "",
            "detail": "wsl executable not found on PATH",
        }
    try:
        completed = subprocess.run(
            ["wsl", "--status"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return {
            "status": "partial",
            "executable": wsl,
            "detail": f"wsl executable exists but probe failed: {exc}",
        }
    output = _clean_probe_text(completed.stdout or completed.stderr or "")
    if completed.returncode == 0:
        detail = output.splitlines()[0] if output else "wsl available"
        return {
            "status": "ready",
            "executable": wsl,
            "detail": detail,
        }
    detail = output.splitlines()[0] if output else "wsl reported an error"
    return {
        "status": "partial",
        "executable": wsl,
        "detail": detail,
    }


def _linux_direct_probe() -> dict[str, str]:
    cmake = shutil.which("cmake")
    zig = shutil.which("zig")
    toolchain_exists = LINUX_ZIG_TOOLCHAIN.is_file()
    ready = bool(cmake and zig and toolchain_exists)
    return {
        "status": "ready" if ready else "partial",
        "executable": zig or "",
        "detail": (
            f"cmake={'ok' if cmake else 'missing'}; "
            f"zig={'ok' if zig else 'missing'}; "
            f"toolchain={'ok' if toolchain_exists else 'missing'}"
        ),
    }


def _classify_route(*, supported: bool, ready: bool, installable: bool) -> str:
    if ready:
        return "ready-now"
    if installable:
        return "ready-after-install"
    if supported:
        return "supported-on-host"
    return "unsupported-on-host"


def _route_row(
    *,
    route: dict[str, Any],
    name: str,
    host_scope: list[str],
    supported: bool,
    ready: bool,
    installable: bool,
    detail: str,
    commands: list[str],
    installs: list[str] | None = None,
    install_commands: list[str] | None = None,
    setup_steps: list[str] | None = None,
    evidence_commands: list[str] | None = None,
    activation: str | None = None,
    preferred_surface_version: str = "",
    supported_surface_versions: list[str] | None = None,
    discovered_surface_versions: list[str] | None = None,
    matched_surface_versions: list[str] | None = None,
    version_status: str = "not-applicable",
    version_detail: str = "",
    requirement_status: str = "pass",
    requirement_failures: list[dict[str, Any]] | None = None,
    remediation_steps: list[str] | None = None,
) -> dict[str, Any]:
    resolved_activation = activation or _classify_route(supported=supported, ready=ready, installable=installable)
    required_installs = installs or []
    missing_installs = required_installs if resolved_activation == "ready-after-install" else []
    resolved_install_commands = (install_commands or []) if resolved_activation == "ready-after-install" else []
    missing_setup_steps = setup_steps or []
    if resolved_activation != "ready-after-setup":
        missing_setup_steps = []
    return {
        "name": name,
        "label": str(route.get("label") or name),
        "surface": str(route.get("surface") or ""),
        "engine": str(route.get("engine") or ""),
        "target": str(route.get("target") or ""),
        "backend": str(route.get("backend") or ""),
        "proof_kind": str(route.get("proof_kind") or ""),
        "status": _status(ready, partial=supported and not ready),
        "activation": resolved_activation,
        "supported": supported,
        "ready": ready,
        "installable": installable,
        "host_scope": host_scope,
        "detail": detail,
        "commands": commands,
        "installs": required_installs,
        "missing_installs": missing_installs,
        "install_commands": resolved_install_commands,
        "missing_setup_steps": missing_setup_steps,
        "light_up_command": commands[-1] if commands else "",
        "evidence_commands": evidence_commands or commands[:1],
        "preferred_surface_version": preferred_surface_version,
        "supported_surface_versions": supported_surface_versions or [],
        "discovered_surface_versions": discovered_surface_versions or [],
        "matched_surface_versions": matched_surface_versions or [],
        "version_status": version_status,
        "version_detail": version_detail,
        "requirement_status": requirement_status,
        "requirement_failures": requirement_failures or [],
        "remediation_steps": remediation_steps or [],
    }


def _version_matches(requested: str, discovered: str) -> bool:
    return discovered == requested or discovered.startswith(f"{requested}.")


def _godot_discovered_versions(godot: dict[str, Any]) -> list[str]:
    executable = str(godot.get("godot") or "")
    if not executable:
        return []
    match = re.search(r"Godot_v(\d+\.\d+)-stable", executable, re.IGNORECASE)
    if match:
        return [match.group(1)]
    match = re.search(r"godot(?:_|-)?(\d+\.\d+)", Path(executable).name, re.IGNORECASE)
    if match:
        return [match.group(1)]
    return []


def _python_discovered_versions() -> list[str]:
    return [f"{sys.version_info.major}.{sys.version_info.minor}"]


def _route_version_state(
    route: dict[str, Any],
    *,
    manifest: dict[str, Any],
    godot: dict[str, Any],
    unity_versions: list[dict[str, Any]],
    unreal_versions: list[dict[str, Any]],
) -> dict[str, Any]:
    preferred = workspace_manifest.route_preferred_surface_version(route, manifest)
    supported = workspace_manifest.route_supported_surface_versions(route, manifest)
    surface = str(route.get("surface") or "")
    if not supported and not preferred:
        return {
            "preferred_surface_version": "",
            "supported_surface_versions": [],
            "discovered_surface_versions": [],
            "matched_surface_versions": [],
            "version_status": "not-applicable",
            "version_detail": "route does not declare surface version requirements",
        }
    if surface == "python":
        discovered = _python_discovered_versions()
    elif surface == "godot":
        discovered = _godot_discovered_versions(godot)
    elif surface == "unity":
        discovered = [str(row.get("version") or "") for row in unity_versions if row.get("version")]
    elif surface == "unreal":
        discovered = [str(row.get("version") or "") for row in unreal_versions if row.get("version")]
    else:
        discovered = []
    matched = [
        discovered_version
        for discovered_version in discovered
        if any(_version_matches(requested, discovered_version) for requested in supported)
    ]
    if not discovered:
        return {
            "preferred_surface_version": preferred,
            "supported_surface_versions": supported,
            "discovered_surface_versions": [],
            "matched_surface_versions": [],
            "version_status": "undiscovered",
            "version_detail": f"declared={','.join(supported) or 'none'}; host version not discovered",
        }
    if preferred and any(_version_matches(preferred, discovered_version) for discovered_version in discovered):
        return {
            "preferred_surface_version": preferred,
            "supported_surface_versions": supported,
            "discovered_surface_versions": discovered,
            "matched_surface_versions": matched,
            "version_status": "preferred-match",
            "version_detail": f"installed={','.join(discovered)}; preferred={preferred}",
        }
    if matched:
        return {
            "preferred_surface_version": preferred,
            "supported_surface_versions": supported,
            "discovered_surface_versions": discovered,
            "matched_surface_versions": matched,
            "version_status": "supported-not-preferred",
            "version_detail": (
                f"installed={','.join(discovered)}; matched={','.join(matched)}; preferred={preferred or 'none'}"
            ),
        }
    return {
        "preferred_surface_version": preferred,
        "supported_surface_versions": supported,
        "discovered_surface_versions": discovered,
        "matched_surface_versions": [],
        "version_status": "unsupported-version",
        "version_detail": (
            f"installed={','.join(discovered)}; supported={','.join(supported) or 'none'}; preferred={preferred or 'none'}"
        ),
    }


def _unreal_linux_profile_versions() -> list[str]:
    versions: list[str] = []
    if not UNREAL_LINUX_PROFILES.is_dir():
        return versions
    for path in sorted(UNREAL_LINUX_PROFILES.glob("ubuntu_24_04_ue*.env")):
        suffix = path.stem.removeprefix("ubuntu_24_04_ue")
        if len(suffix) >= 2:
            versions.append(f"{suffix[0]}.{suffix[1:]}")
    return versions


def _grill_source_present(path: Path) -> bool:
    return path.expanduser().resolve().is_dir()


def _build_competitor_routes() -> list[dict[str, Any]]:
    unity_plugin = grill_paths.UNITY_PLUGIN
    unity_example = grill_paths.UNITY_EXAMPLE
    unreal_plugin = grill_paths.UNREAL_PLUGIN
    unreal_example = grill_paths.UNREAL_EXAMPLE

    unity_status = build_unity_grill_baseline_status.build_report(
        _resolve_existing_or_default(build_unity_grill_baseline_status.DEFAULT_FASTDIS),
        head_to_head_path=_resolve_existing_or_default(build_unity_grill_baseline_status.DEFAULT_HEAD_TO_HEAD),
        import_smoke_path=_resolve_existing_or_default(build_unity_grill_baseline_status.DEFAULT_IMPORT_SMOKE),
        grill_candidates=[_resolve_existing_or_default(path) for path in build_unity_grill_baseline_status.DEFAULT_GRILL_CANDIDATES],
    )
    unreal_status = build_unreal_grill_baseline_status.build_report(
        _resolve_existing_or_default(build_unreal_grill_baseline_status.DEFAULT_FASTDIS),
        source_smoke_path=_resolve_existing_or_default(build_unreal_grill_baseline_status.DEFAULT_SOURCE_SMOKE),
        mapping_export_path=_resolve_existing_or_default(build_unreal_grill_baseline_status.DEFAULT_MAPPING_EXPORT),
        mapping_materialize_path=_resolve_existing_or_default(build_unreal_grill_baseline_status.DEFAULT_MAPPING_MATERIALIZE),
        linux_build_proof_path=_resolve_existing_or_default(build_unreal_grill_baseline_status.DEFAULT_LINUX_BUILD_PROOF),
        grill_candidates=[_resolve_existing_or_default(path) for path in build_unreal_grill_baseline_status.DEFAULT_GRILL_CANDIDATES],
    )

    unity_source_present = _grill_source_present(unity_plugin) or _grill_source_present(unity_example)
    unreal_source_present = _grill_source_present(unreal_plugin) or _grill_source_present(unreal_example)

    unity_import_status = str(((unity_status.get("import_smoke") or {}) if isinstance(unity_status.get("import_smoke"), dict) else {}).get("status") or "")
    unreal_source_status = str(((unreal_status.get("source_smoke") or {}) if isinstance(unreal_status.get("source_smoke"), dict) else {}).get("status") or "")
    unreal_mapping_export_status = str(((unreal_status.get("mapping_export") or {}) if isinstance(unreal_status.get("mapping_export"), dict) else {}).get("status") or "")
    unreal_mapping_materialize_status = str(((unreal_status.get("mapping_materialize") or {}) if isinstance(unreal_status.get("mapping_materialize"), dict) else {}).get("status") or "")
    unreal_linux_status = str(((unreal_status.get("linux_build_proof") or {}) if isinstance(unreal_status.get("linux_build_proof"), dict) else {}).get("status") or "")

    def competitor_route(
        *,
        name: str,
        label: str,
        surface: str,
        endpoint: str,
        source_present: bool,
        ready: bool,
        detail: str,
        light_up_command: str,
        evidence_commands: list[str],
        blockers: list[str],
        notes: str = "",
    ) -> dict[str, Any]:
        if ready:
            activation = "ready-now"
            status = "ready"
        elif source_present:
            activation = "blocked-on-competitor"
            status = "blocked"
        else:
            activation = "missing-source"
            status = "unavailable"
        return {
            "name": name,
            "label": label,
            "surface": surface,
            "endpoint": endpoint,
            "status": status,
            "activation": activation,
            "source_present": source_present,
            "ready": ready,
            "detail": detail,
            "light_up_command": light_up_command,
            "evidence_commands": evidence_commands,
            "blockers": blockers,
            "notes": notes,
        }

    routes = [
        competitor_route(
            name="grill-unity-import-smoke",
            label="GRILL Unity Import Smoke",
            surface="grill_unity",
            endpoint="import-smoke",
            source_present=unity_source_present,
            ready=unity_import_status == "pass",
            detail=f"import_smoke={unity_import_status or 'missing'}; source={'present' if unity_source_present else 'missing'}",
            light_up_command="python tools/run_grill_unity_import_smoke.py --unity-version 6000.5.0f1",
            evidence_commands=["python tools/run_grill_unity_import_smoke.py --unity-version 6000.5.0f1"],
            blockers=list(unity_status.get("blockers") or []),
            notes="Public GRILL Unity source/package route on the current host/editor combination.",
        ),
        competitor_route(
            name="grill-unity-benchmark",
            label="GRILL Unity Benchmark Readiness",
            surface="grill_unity",
            endpoint="benchmark",
            source_present=unity_source_present,
            ready=str(unity_status.get("status") or "") == "ready",
            detail=f"baseline_status={unity_status.get('status') or 'missing'}",
            light_up_command="python tools/run_unity_grill_benchmark.py",
            evidence_commands=[
                "python tools/build_unity_grill_baseline_status.py",
                "python tools/run_unity_grill_benchmark.py",
            ],
            blockers=list(unity_status.get("blockers") or []),
            notes="Same-host FastDIS-vs-GRILL Unity benchmark/comparison readiness.",
        ),
        competitor_route(
            name="grill-unreal-source-smoke",
            label="GRILL Unreal Source Smoke",
            surface="grill_unreal",
            endpoint="source-smoke",
            source_present=unreal_source_present,
            ready=unreal_source_status == "pass",
            detail=f"source_smoke={unreal_source_status or 'missing'}; source={'present' if unreal_source_present else 'missing'}",
            light_up_command="python tools/run_grill_unreal_source_smoke.py --engine-version 5.8",
            evidence_commands=["python tools/run_grill_unreal_source_smoke.py --engine-version 5.8"],
            blockers=list(unreal_status.get("blockers") or []),
            notes="Public GRILL Unreal source route on the current host/editor combination.",
        ),
        competitor_route(
            name="grill-unreal-swap-smoke",
            label="GRILL Unreal Swap/Mapping Smoke",
            surface="grill_unreal",
            endpoint="mapping-swap",
            source_present=unreal_source_present,
            ready=unreal_mapping_export_status in {"ok", "dry-run"} and unreal_mapping_materialize_status in {"ok", "dry-run"},
            detail=(
                f"mapping_export={unreal_mapping_export_status or 'missing'}; "
                f"mapping_materialize={unreal_mapping_materialize_status or 'missing'}"
            ),
            light_up_command="python tools/unreal_workflow.py grill-swap-smoke --engine-version 5.8",
            evidence_commands=[
                "python tools/run_grill_unreal_mapping_export.py --engine-version 5.8",
                "python tools/run_unreal_grill_mapping_materialize.py --engine-version 5.8",
            ],
            blockers=list(unreal_status.get("blockers") or []),
            notes="GRILL-shaped Unreal object/id mapping and FastDIS swap-materialize lane.",
        ),
        competitor_route(
            name="grill-unreal-linux-proof",
            label="GRILL Unreal Linux Proof",
            surface="grill_unreal",
            endpoint="linux-build-proof",
            source_present=unreal_source_present,
            ready=unreal_linux_status == "pass",
            detail=f"linux_build_proof={unreal_linux_status or 'missing'}",
            light_up_command="python tools/unreal_workflow.py grill-linux-proof --engine-version 5.8",
            evidence_commands=["python tools/unreal_workflow.py grill-linux-proof --engine-version 5.8"],
            blockers=list(unreal_status.get("blockers") or []),
            notes="Docker/Linux portability proof for the GRILL Unreal public route.",
        ),
        competitor_route(
            name="grill-unreal-benchmark",
            label="GRILL Unreal Benchmark Readiness",
            surface="grill_unreal",
            endpoint="benchmark",
            source_present=unreal_source_present,
            ready=str(unreal_status.get("status") or "") == "ready",
            detail=f"baseline_status={unreal_status.get('status') or 'missing'}",
            light_up_command="python tools/run_unreal_grill_benchmark.py",
            evidence_commands=[
                "python tools/build_unreal_grill_baseline_status.py",
                "python tools/run_unreal_grill_benchmark.py",
            ],
            blockers=list(unreal_status.get("blockers") or []),
            notes="Same-host FastDIS-vs-GRILL Unreal benchmark/comparison readiness.",
        ),
    ]
    return routes


def _unreal_versions_payload() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for install in unreal_env.discover_installs():
        ready = all(
            [
                bool(install.editor_path),
                bool(install.uat_path),
                bool(install.ubt_path),
                bool(install.dotnet_path),
            ]
        )
        rows.append(
            {
                "version": install.version or "unknown",
                "status": _status(ready, partial=not ready),
                "install_root": install.install_root,
                "editor": install.editor_path or "",
                "source": install.source,
                "quirks": list(install.quirks),
            }
        )
    return rows


def _unity_versions_payload() -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    host = unity_env.describe_host()
    installs = host["installs"]
    default_install = host["default_install"]
    rows: list[dict[str, Any]] = []
    for install in installs:
        ready = bool(install.get("editor_path"))
        rows.append(
            {
                "version": str(install.get("version") or "unknown"),
                "status": _status(ready, partial=not ready),
                "install_root": str(install.get("install_root") or ""),
                "editor": str(install.get("editor_path") or ""),
                "source": str(install.get("source") or ""),
                "quirks": list(install.get("quirks") or []),
            }
        )
    return rows, default_install


def _requirement_context(
    *,
    docker: dict[str, str],
    linux_direct: dict[str, str],
    wsl: dict[str, str],
    godot: dict[str, Any],
    unity_versions: list[dict[str, Any]],
    unreal_versions: list[dict[str, Any]],
    linux_profile_versions: list[str],
    wheel: dict[str, Any],
) -> dict[str, Any]:
    wheel_checks = {
        str(check.get("name") or ""): str(check.get("status") or "")
        for check in wheel.get("checks") or []
        if isinstance(check, dict) and check.get("name")
    }
    executables = {
        "cmake": shutil.which("cmake") or "",
        "zig": shutil.which("zig") or "",
        "docker": docker.get("executable") or "",
        "wsl": wsl.get("executable") or "",
        "scons": str(godot.get("scons") or ""),
        "godot": str(godot.get("godot") or ""),
        "x86_64-w64-mingw32-gcc": wheel_checks.get("x86_64-w64-mingw32-gcc", "") in {"ok", "present"},
        "x86_64-w64-mingw32-g++": wheel_checks.get("x86_64-w64-mingw32-g++", "") in {"ok", "present"},
    }
    normalized_executables = {
        name: value if isinstance(value, str) else ("present" if value else "")
        for name, value in executables.items()
    }
    backends = {
        "docker": str(docker.get("status") or "unavailable"),
        "direct": str(linux_direct.get("status") or "unavailable"),
        "wsl": str(wsl.get("status") or "unavailable"),
        "mingw-direct": "ready" if wheel.get("status") in {"ready", "ready-with-gaps"} else "partial",
    }
    godot_versions = _godot_discovered_versions(godot)
    godot_status = "ready" if godot_versions else ("partial" if godot.get("godot") else "unavailable")
    unity_detected_versions = [str(row.get("version") or "") for row in unity_versions if row.get("version")]
    unity_status = "ready" if any(row.get("status") == "ready" for row in unity_versions) else ("partial" if unity_versions else "unavailable")
    unreal_detected_versions = [str(row.get("version") or "") for row in unreal_versions if row.get("version")]
    unreal_status = "ready" if any(row.get("status") == "ready" for row in unreal_versions) else ("partial" if unreal_versions else "unavailable")
    engines = {
        "godot": {"status": godot_status, "versions": godot_versions},
        "unity": {"status": unity_status, "versions": unity_detected_versions},
        "unreal": {"status": unreal_status, "versions": unreal_detected_versions},
        "unreal-linux-docker": {"status": "ready" if linux_profile_versions else "partial", "versions": list(linux_profile_versions)},
    }
    return {
        "interpreter": workspace_requirement_eval.interpreter_payload(),
        "executables": normalized_executables,
        "backends": backends,
        "engines": engines,
        "env": os.environ,
    }


def _route_runtime_state(
    route: dict[str, Any],
    *,
    manifest: dict[str, Any],
    host_class: str,
    docker: dict[str, str],
    linux_direct: dict[str, str],
    godot: dict[str, Any],
    unity_default: dict[str, Any] | None,
    unity_versions: list[dict[str, Any]],
    unreal_versions: list[dict[str, Any]],
    linux_profile_versions: list[str],
    wheel: dict[str, Any],
    requirement_context: dict[str, Any],
) -> dict[str, Any]:
    route_id = str(route.get("id") or "")
    supported = workspace_manifest.route_supported_on_host(route, host_class)
    requirement_state = workspace_requirement_eval.evaluate_requirements(
        workspace_manifest.route_requirements(route, manifest),
        context=requirement_context,
    )
    version_state = _route_version_state(
        route,
        manifest=manifest,
        godot=godot,
        unity_versions=unity_versions,
        unreal_versions=unreal_versions,
    )
    version_ready = version_state["version_status"] in {
        "preferred-match",
        "supported-not-preferred",
        "undiscovered",
        "not-applicable",
    }
    requirement_ready = not requirement_state["blocking"]
    activation_override = None
    if requirement_state["blocking"]:
        activation_override = "blocked-by-version-policy"
    if route_id == "python-core":
        return {
            "supported": supported,
            "ready": version_ready and requirement_ready,
            "installable": False,
            "detail": "core Python/CLI routes are available on this host",
            "version_state": version_state,
            "requirement_state": requirement_state,
            "activation": activation_override,
        }
    if route_id == "godot-native":
        ready = bool(godot.get("godot")) and bool(godot.get("scons")) and version_ready and requirement_ready
        return {
            "supported": supported,
            "ready": ready,
            "installable": supported and not ready,
            "detail": f"godot={godot.get('godot') or 'missing'}; scons={godot.get('scons') or 'missing'}",
            "version_state": version_state,
            "requirement_state": requirement_state,
            "activation": activation_override,
        }
    if route_id == "unity-native":
        ready = bool(unity_default and unity_default.get("editor_path")) and version_ready and requirement_ready
        detail = (
            f"default={unity_default.get('version')} editor={unity_default.get('editor_path')}"
            if unity_default
            else "no Unity install discovered"
        )
        return {
            "supported": supported,
            "ready": ready,
            "installable": supported and not ready,
            "detail": detail,
            "version_state": version_state,
            "requirement_state": requirement_state,
            "activation": activation_override,
        }
    if route_id == "unity-linux-cross-direct":
        ready = linux_direct["status"] == "ready" and version_ready and requirement_ready
        return {
            "supported": supported,
            "ready": ready,
            "installable": supported and not ready,
            "detail": f"backend=direct; {linux_direct['detail']}",
            "version_state": version_state,
            "requirement_state": requirement_state,
            "activation": activation_override,
        }
    if route_id == "unity-linux-docker":
        ready = docker["status"] == "ready" and version_ready and requirement_ready
        return {
            "supported": supported,
            "ready": ready,
            "installable": supported and not ready,
            "detail": f"backend=docker; {docker['detail']}",
            "version_state": version_state,
            "requirement_state": requirement_state,
            "activation": activation_override,
        }
    if route_id == "unreal-native":
        ready = any(row["status"] == "ready" for row in unreal_versions) and version_ready and requirement_ready
        detail = (
            ", ".join(f"{row['version']}={row['status']}" for row in unreal_versions)
            if unreal_versions
            else "no Unreal installs discovered"
        )
        return {
            "supported": supported,
            "ready": ready,
            "installable": supported and not ready,
            "detail": detail,
            "version_state": version_state,
            "requirement_state": requirement_state,
            "activation": activation_override,
        }
    if route_id == "unreal-linux-docker":
        ready = docker["status"] == "ready" and bool(linux_profile_versions) and version_ready and requirement_ready
        installable = supported and ((docker["status"] != "unavailable") or bool(linux_profile_versions))
        return {
            "supported": supported,
            "ready": ready,
            "installable": installable,
            "detail": f"docker={docker['status']}; profiles={','.join(linux_profile_versions) or 'none'}",
            "version_state": version_state,
            "requirement_state": requirement_state,
            "activation": activation_override,
        }
    if route_id == "windows-cross-mingw":
        ready = wheel["status"] == "ready" and version_ready and requirement_ready
        partial = wheel["status"] == "ready-with-gaps"
        return {
            "supported": supported,
            "ready": ready,
            "installable": supported and not ready,
            "detail": f"backend=mingw-direct; wheel doctor={wheel['status']}",
            "activation": activation_override or ("ready-after-setup" if supported and partial and not ready else None),
            "version_state": version_state,
            "requirement_state": requirement_state,
        }
    return {
        "supported": supported,
        "ready": False,
        "installable": supported,
        "detail": "route is declared in the workspace manifest but does not yet have a host evaluator",
        "version_state": version_state,
        "requirement_state": requirement_state,
        "activation": activation_override,
    }


def build_payload(*, host_system_override: str | None = None, host_machine_override: str | None = None, host_platform_override: str | None = None) -> dict[str, Any]:
    manifest = workspace_manifest.load_manifest()
    if host_system_override is None and host_machine_override is None and host_platform_override is None:
        shard_host = host_facts()
    else:
        shard_host = host_facts(system_override=host_system_override or host_platform_override, machine_override=host_machine_override)
    detected_host = host_profile.resolve_host_profile(
        system_override=host_system_override or host_platform_override,
        machine_override=host_machine_override,
    )
    docker = _docker_probe()
    linux_direct = _linux_direct_probe()
    wsl = _wsl_probe()
    godot = godot_env.describe_host()
    unity_versions, unity_default = _unity_versions_payload()
    unreal_versions = _unreal_versions_payload()
    wheel = windows_wheel_workflow.doctor_payload(windows_wheel_workflow.DEFAULT_MINGW_PREFIX)
    linux_profile_versions = _unreal_linux_profile_versions()
    requirement_context = _requirement_context(
        docker=docker,
        linux_direct=linux_direct,
        wsl=wsl,
        godot=godot,
        unity_versions=unity_versions,
        unreal_versions=unreal_versions,
        linux_profile_versions=linux_profile_versions,
        wheel=wheel,
    )

    host_class = shard_host.host_class
    godot_ready = bool(godot.get("godot")) and bool(godot.get("scons"))
    routes: list[dict[str, Any]] = []
    for route in workspace_manifest.route_specs(manifest):
        runtime = _route_runtime_state(
            route,
            manifest=manifest,
            host_class=host_class,
            docker=docker,
            linux_direct=linux_direct,
            godot=godot,
            unity_default=unity_default,
            unity_versions=unity_versions,
            unreal_versions=unreal_versions,
            linux_profile_versions=linux_profile_versions,
            wheel=wheel,
            requirement_context=requirement_context,
        )
        routes.append(
            _route_row(
                route=route,
                name=str(route.get("id") or ""),
                ready=bool(runtime["ready"]),
                supported=bool(runtime["supported"]),
                installable=bool(runtime["installable"]),
                host_scope=[str(value) for value in route.get("supported_host_classes") or []],
                detail=str(runtime["detail"]),
                commands=[str(value) for value in route.get("commands") or []],
                installs=workspace_manifest.route_installs(route, host_class),
                install_commands=workspace_manifest.route_install_commands(route, host_class),
                setup_steps=workspace_manifest.route_setup_steps(route, host_class),
                evidence_commands=[str(value) for value in route.get("evidence_commands") or []],
                activation=runtime.get("activation"),
                preferred_surface_version=str(runtime["version_state"]["preferred_surface_version"]),
                supported_surface_versions=list(runtime["version_state"]["supported_surface_versions"]),
                discovered_surface_versions=list(runtime["version_state"]["discovered_surface_versions"]),
                matched_surface_versions=list(runtime["version_state"]["matched_surface_versions"]),
                version_status=str(runtime["version_state"]["version_status"]),
                version_detail=str(runtime["version_state"]["version_detail"]),
                requirement_status=str(runtime["requirement_state"]["status"]),
                requirement_failures=list(runtime["requirement_state"]["failures"]),
                remediation_steps=list(runtime["requirement_state"]["remediation"]),
            )
        )
    competitor_routes = _build_competitor_routes()

    return {
        "schema": "fastdis.host_capability_matrix.v1",
        "workspace": workspace_manifest.workspace_metadata(manifest),
        "canonical_surface_hooks": workspace_manifest.canonical_surface_hooks(manifest),
        "canonical_hook_categories": workspace_manifest.canonical_hook_categories(manifest),
        "surfaces": [
            {
                **surface,
                "preferred_version": workspace_manifest.surface_preferred_version(surface, manifest),
                "supported_versions": workspace_manifest.surface_versions(surface, manifest),
                "hooks": workspace_manifest.surface_hooks(surface, manifest),
            }
            for surface in workspace_manifest.surface_specs(manifest)
        ],
        "host": {
            "platform": detected_host.system,
            "arch": detected_host.machine,
            "host_platform": detected_host.host_platform,
            "hostname": detected_host.hostname,
            "host_identity_source": detected_host.identity_source,
            "python": sys.executable,
            "host_class": shard_host.host_class,
            "preferred_runtime_hosts": list(shard_host.preferred_runtime_hosts),
            "cross_build_targets": list(shard_host.cross_build_targets),
        },
        "software": {
            "docker": docker,
            "zig": {
                "status": linux_direct["status"],
                "executable": linux_direct["executable"],
                "detail": linux_direct["detail"],
            },
            "wsl": wsl,
            "cmake": shutil.which("cmake") or "",
            "scons": str(godot.get("scons") or ""),
            "godot": str(godot.get("godot") or ""),
        },
        "engines": {
            "godot": {
                "status": _status(godot_ready, partial=bool(godot.get("godot")) or bool(godot.get("scons"))),
                "host": godot,
            },
            "unity": {
                "status": _status(bool(unity_default and unity_default.get("editor_path")), partial=bool(unity_versions)),
                "default_install": unity_default,
                "installs": unity_versions,
                "recommended_overrides": unity_env.describe_host().get("recommended_editor_overrides", {}),
            },
            "unreal": {
                "status": _status(any(row["status"] == "ready" for row in unreal_versions), partial=bool(unreal_versions)),
                "installs": unreal_versions,
                "linux_docker_profiles": linux_profile_versions,
            },
        },
        "toolchains": {
            "linux_shared": {
                "status": linux_direct["status"],
                "toolchain_file": str(LINUX_ZIG_TOOLCHAIN),
                "detail": linux_direct["detail"],
            },
            "windows_cross_mingw": {
                "status": wheel["status"],
                "toolchain_file": str(ROOT / "cmake" / "toolchains" / "mingw-w64-x86_64.cmake"),
                "detail": "canonical Windows cross-target backend on macOS/Linux hosts",
            },
            "windows_wheel": {
                "status": wheel["status"],
                "checks": wheel["checks"],
            }
        },
        "cross_platform_policy": workspace_manifest.cross_platform_policy(shard_host.host_class, manifest),
        "routes": routes,
        "competitor_routes": competitor_routes,
        "route_summary": {
            "ready_now": [route["name"] for route in routes if route["activation"] == "ready-now"],
            "ready_after_install": [route["name"] for route in routes if route["activation"] == "ready-after-install"],
            "ready_after_setup": [route["name"] for route in routes if route["activation"] == "ready-after-setup"],
            "supported_on_host": [route["name"] for route in routes if route["activation"] == "supported-on-host"],
            "unsupported_on_host": [route["name"] for route in routes if route["activation"] == "unsupported-on-host"],
            "blocked_by_version_policy": [route["name"] for route in routes if route["activation"] == "blocked-by-version-policy"],
            "preferred_version_match": [route["name"] for route in routes if route["version_status"] == "preferred-match"],
            "supported_not_preferred": [route["name"] for route in routes if route["version_status"] == "supported-not-preferred"],
            "unsupported_version": [route["name"] for route in routes if route["version_status"] == "unsupported-version"],
            "undiscovered_version": [route["name"] for route in routes if route["version_status"] == "undiscovered"],
        },
        "competitor_summary": {
            "ready_now": [route["name"] for route in competitor_routes if route["activation"] == "ready-now"],
            "blocked_on_competitor": [route["name"] for route in competitor_routes if route["activation"] == "blocked-on-competitor"],
            "missing_source": [route["name"] for route in competitor_routes if route["activation"] == "missing-source"],
        },
        "next_steps": workspace_manifest.next_steps(manifest),
    }


def render_text(payload: dict[str, Any]) -> str:
    host = payload["host"]
    lines = [
        "FastDIS host capability matrix",
        "",
        f"- platform: `{host['platform']}`",
        f"- arch: `{host['arch']}`",
        f"- host_class: `{host['host_class']}`",
        f"- preferred_runtime_hosts: `{','.join(host['preferred_runtime_hosts']) or 'none'}`",
        f"- cross_build_targets: `{','.join(host['cross_build_targets']) or 'none'}`",
        "",
        "Surfaces:",
    ]
    for surface in payload.get("surfaces", []):
        hooks = surface.get("hooks") or {}
        hook_labels = ",".join(sorted(f"{name}={spec.get('status', 'unknown')}" for name, spec in hooks.items())) or "none"
        preferred_version = surface.get("preferred_version") or "none"
        supported_versions = ",".join(version["version"] for version in surface.get("supported_versions", [])) or "none"
        lines.append(
            f"- {surface['id']}: preferred_version={preferred_version}; supported_versions={supported_versions}; hooks={hook_labels}"
        )
    lines.extend([
        "",
        "Routes:",
    ])
    for route in payload["routes"]:
        installs = f"; installs={','.join(route['installs'])}" if route.get("installs") else ""
        version_clause = f"; versions={route['version_status']} [{route['version_detail']}]" if route.get("version_status") else ""
        requirement_clause = ""
        if route.get("requirement_status") not in {"", "pass"}:
            requirement_clause = f"; requirements={route['requirement_status']}"
        lines.append(f"- {route['name']}: {route['activation']} ({route['detail']}{version_clause}{requirement_clause}{installs})")
    competitor_summary = payload.get("competitor_summary", {})
    competitor_routes = payload.get("competitor_routes", [])
    if competitor_routes:
        lines.extend([
            "",
            "Competitor routes:",
        ])
        for route in competitor_routes:
            blockers = f"; blockers={','.join(route.get('blockers') or [])}" if route.get("blockers") else ""
            lines.append(f"- {route['name']}: {route['activation']} ({route['detail']}{blockers})")
    route_summary = payload.get("route_summary", {})
    lines.extend(["", "Activation buckets:"])
    for key in (
        "ready_now",
        "ready_after_install",
        "ready_after_setup",
        "supported_on_host",
        "unsupported_on_host",
        "blocked_by_version_policy",
        "preferred_version_match",
        "supported_not_preferred",
        "unsupported_version",
        "undiscovered_version",
    ):
        values = route_summary.get(key, [])
        lines.append(f"- {key}: `{','.join(values) or 'none'}`")
    if competitor_routes:
        lines.extend(["", "Competitor buckets:"])
        for key in ("ready_now", "blocked_on_competitor", "missing_source"):
            values = competitor_summary.get(key, [])
            lines.append(f"- {key}: `{','.join(values) or 'none'}`")
    lines.extend(
        [
            "",
            "Software:",
            f"- docker: {payload['software']['docker']['status']} ({payload['software']['docker']['detail']})",
            f"- zig: {payload['software']['zig']['status']} ({payload['software']['zig']['detail']})",
            f"- wsl: {payload['software']['wsl']['status']} ({payload['software']['wsl']['detail']})",
            f"- cmake: `{payload['software']['cmake'] or 'missing'}`",
            f"- godot: `{payload['software']['godot'] or 'missing'}`",
            f"- scons: `{payload['software']['scons'] or 'missing'}`",
            "",
            "Installed versions:",
        ]
    )
    unity = payload["engines"]["unity"]
    unreal = payload["engines"]["unreal"]
    lines.append(
        "- unity: "
        + (", ".join(f"{row['version']}={row['status']}" for row in unity["installs"]) or "none")
    )
    lines.append(
        "- unreal: "
        + (", ".join(f"{row['version']}={row['status']}" for row in unreal["installs"]) or "none")
    )
    lines.append(
        "- unreal linux docker profiles: "
        + (",".join(unreal["linux_docker_profiles"]) or "none")
    )
    lines.extend(["", "Cross-platform policy:"])
    for item in payload.get("cross_platform_policy", []):
        lines.append(f"- {item}")
    lines.extend(["", "Remediation:"])
    for route in payload["routes"]:
        if route["activation"] == "ready-now":
            continue
        lines.append(f"- {route['name']}:")
        lines.append(f"  status: {route['activation']}")
        lines.append(f"  light_up: {route['light_up_command'] or 'none'}")
        lines.append(f"  evidence: {', '.join(route['evidence_commands']) or 'none'}")
        lines.append(f"  missing_installs: {', '.join(route['missing_installs']) or 'none'}")
        lines.append(f"  install_commands: {', '.join(route['install_commands']) or 'none'}")
        lines.append(f"  missing_setup_steps: {', '.join(route['missing_setup_steps']) or 'none'}")
    lines.extend(["", "Next:"])
    for step in payload["next_steps"]:
        lines.append(f"- {step}")
    return "\n".join(lines)


def render_summary(payload: dict[str, Any]) -> str:
    host = payload["host"]
    route_summary = payload.get("route_summary", {})
    competitor_summary = payload.get("competitor_summary", {})
    lines = [
        "FastDIS workspace summary",
        f"host={host['platform']}/{host['arch']} class={host['host_class']}",
        f"ready_now={','.join(route_summary.get('ready_now', [])) or 'none'}",
        f"ready_after_install={','.join(route_summary.get('ready_after_install', [])) or 'none'}",
        f"ready_after_setup={','.join(route_summary.get('ready_after_setup', [])) or 'none'}",
        f"supported_on_host={','.join(route_summary.get('supported_on_host', [])) or 'none'}",
        f"unsupported_on_host={','.join(route_summary.get('unsupported_on_host', [])) or 'none'}",
        f"blocked_by_version_policy={','.join(route_summary.get('blocked_by_version_policy', [])) or 'none'}",
        f"preferred_version_match={','.join(route_summary.get('preferred_version_match', [])) or 'none'}",
        f"supported_not_preferred={','.join(route_summary.get('supported_not_preferred', [])) or 'none'}",
        f"unsupported_version={','.join(route_summary.get('unsupported_version', [])) or 'none'}",
        f"competitor_ready_now={','.join(competitor_summary.get('ready_now', [])) or 'none'}",
        f"competitor_blocked={','.join(competitor_summary.get('blocked_on_competitor', [])) or 'none'}",
        f"competitor_missing_source={','.join(competitor_summary.get('missing_source', [])) or 'none'}",
    ]
    for route in payload["routes"]:
        if route["activation"] == "ready-after-install":
            lines.append(
                "install "
                + f"{route['name']}: "
                + (", ".join(route.get("install_commands") or []) or ", ".join(route.get("missing_installs") or []) or "see doctor")
            )
        if route["activation"] == "ready-after-setup":
            lines.append(
                "setup "
                + f"{route['name']}: "
                + (route.get("light_up_command") or ", ".join(route.get("missing_setup_steps") or []) or "see doctor")
            )
        if route.get("version_status") == "supported-not-preferred":
            lines.append(f"version {route['name']}: {route.get('version_detail') or 'supported but not preferred'}")
        if route.get("version_status") == "unsupported-version":
            lines.append(f"version {route['name']}: {route.get('version_detail') or 'installed version not supported'}")
        if route.get("requirement_status") == "fail":
            lines.append(f"requirement {route['name']}: {', '.join(route.get('remediation_steps') or []) or 'see doctor'}")
    return "\n".join(lines)


def render_routes_text(payload: dict[str, Any]) -> str:
    lines = ["FastDIS workspace routes", ""]
    for route in payload.get("routes", []):
        lines.append(f"- {route['name']}: {route.get('label', route['name'])}")
        lines.append(
            "  "
            + f"surface={route.get('surface') or 'none'}; engine={route.get('engine') or 'none'}; "
            + f"target={route.get('target') or 'none'}; backend={route.get('backend') or 'none'}; "
            + f"proof_kind={route.get('proof_kind') or 'none'}"
        )
        lines.append(
            "  "
            + f"activation={route.get('activation') or 'none'}; status={route.get('status') or 'unknown'}; "
            + f"supported={route.get('supported')}; ready={route.get('ready')}; installable={route.get('installable')}"
        )
        lines.append(
            "  "
            + f"preferred_surface_version={route.get('preferred_surface_version') or 'none'}; "
            + f"supported_surface_versions={','.join(route.get('supported_surface_versions') or []) or 'none'}; "
            + f"discovered_surface_versions={','.join(route.get('discovered_surface_versions') or []) or 'none'}; "
            + f"matched_surface_versions={','.join(route.get('matched_surface_versions') or []) or 'none'}"
        )
        lines.append(
            "  "
            + f"version_status={route.get('version_status') or 'none'}; "
            + f"version_detail={route.get('version_detail') or 'none'}"
        )
        lines.append(
            "  "
            + f"requirement_status={route.get('requirement_status') or 'none'}; "
            + f"remediation_steps={', '.join(route.get('remediation_steps') or []) or 'none'}"
        )
        lines.append(f"  detail: {route.get('detail') or 'none'}")
        lines.append(f"  commands: {', '.join(route.get('commands') or []) or 'none'}")
        lines.append(f"  evidence_commands: {', '.join(route.get('evidence_commands') or []) or 'none'}")
        lines.append(f"  install_commands: {', '.join(route.get('install_commands') or []) or 'none'}")
        lines.append(f"  missing_setup_steps: {', '.join(route.get('missing_setup_steps') or []) or 'none'}")
    competitor_routes = payload.get("competitor_routes", [])
    if competitor_routes:
        lines.extend(["", "Competitor routes", ""])
        for route in competitor_routes:
            lines.append(f"- {route['name']}: {route.get('label', route['name'])}")
            lines.append(
                "  "
                + f"surface={route.get('surface') or 'none'}; endpoint={route.get('endpoint') or 'none'}; "
                + f"activation={route.get('activation') or 'none'}; status={route.get('status') or 'unknown'}; "
                + f"source_present={route.get('source_present')}; ready={route.get('ready')}"
            )
            lines.append(f"  detail: {route.get('detail') or 'none'}")
            lines.append(f"  light_up: {route.get('light_up_command') or 'none'}")
            lines.append(f"  evidence_commands: {', '.join(route.get('evidence_commands') or []) or 'none'}")
            lines.append(f"  blockers: {', '.join(route.get('blockers') or []) or 'none'}")
    return "\n".join(lines)


def render_routes_summary(payload: dict[str, Any]) -> str:
    lines = ["FastDIS workspace routes summary"]
    for route in payload.get("routes", []):
        lines.append(
            f"{route['name']}="
            + f"{route.get('activation') or 'none'}"
            + f";version_status={route.get('version_status') or 'none'}"
            + f";requirements={route.get('requirement_status') or 'none'}"
            + f";preferred={route.get('preferred_surface_version') or 'none'}"
            + f";matched={','.join(route.get('matched_surface_versions') or []) or 'none'}"
        )
    for route in payload.get("competitor_routes", []):
        lines.append(
            f"{route['name']}="
            + f"{route.get('activation') or 'none'}"
            + f";status={route.get('status') or 'none'}"
            + f";endpoint={route.get('endpoint') or 'none'}"
            + f";source_present={route.get('source_present')}"
        )
    return "\n".join(lines)


def _ci_rows(
    payload: dict[str, Any],
    *,
    host_class: str | None = None,
    surface: str | None = None,
    proof_kind: str | None = None,
    bootstrap_only: bool = False,
    include_compat: bool = False,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for route in payload.get("routes", []):
        if host_class and host_class not in (route.get("host_scope") or []):
            continue
        if surface and route.get("surface") != surface:
            continue
        if proof_kind and route.get("proof_kind") != proof_kind:
            continue
        manifest_route = workspace_manifest.route_spec(str(route.get("name") or ""))
        if bootstrap_only and not workspace_manifest.route_bootstrap_capable(manifest_route):
            continue
        supported_versions = list(route.get("supported_surface_versions") or [])
        preferred_version = str(route.get("preferred_surface_version") or "")
        selected_versions = supported_versions if include_compat and supported_versions else ([preferred_version] if preferred_version else [""])
        for selected_version in selected_versions:
            version_kind = "preferred" if selected_version == preferred_version else "compat"
            rows.append(
                {
                    "route": route.get("name"),
                    "surface": route.get("surface"),
                    "host_class": host_class or ",".join(route.get("host_scope") or []),
                    "target": route.get("target"),
                    "backend": route.get("backend"),
                    "proof_kind": route.get("proof_kind"),
                    "surface_version": selected_version,
                    "version_kind": version_kind,
                    "bootstrap_capable": workspace_manifest.route_bootstrap_capable(manifest_route),
                    "job_name": f"{route.get('name')}-{(host_class or 'any')}-{selected_version or 'default'}",
                }
            )
    return rows


def render_ci_summary(payload: dict[str, Any], *, host_class: str | None, surface: str | None, proof_kind: str | None, bootstrap_only: bool, include_compat: bool) -> str:
    rows = _ci_rows(payload, host_class=host_class, surface=surface, proof_kind=proof_kind, bootstrap_only=bootstrap_only, include_compat=include_compat)
    lines = ["FastDIS workspace CI summary"]
    for row in rows:
        lines.append(
            f"{row['job_name']}="
            + f"{row['route']};surface={row['surface']};host={row['host_class']};version={row['surface_version'] or 'default'};kind={row['version_kind']}"
        )
    if len(lines) == 1:
        lines.append("none")
    return "\n".join(lines)


def _surface_summary(hooks: dict[str, dict[str, str]]) -> str:
    labels = [f"{name}={spec.get('status', 'unknown')}" for name, spec in hooks.items()]
    return ",".join(sorted(labels)) or "none"


def render_surfaces_text(payload: dict[str, Any]) -> str:
    lines = ["FastDIS workspace surfaces", ""]
    for surface in payload.get("surfaces", []):
        hooks = surface.get("hooks") or {}
        lines.append(f"- {surface['id']}: {surface.get('label', surface['id'])}")
        lines.append(f"  preferred_version: {surface.get('preferred_version') or 'none'}")
        supported_versions = surface.get("supported_versions") or []
        if supported_versions:
            lines.append(
                "  supported_versions: "
                + ", ".join(
                    f"{version['version']}[{version.get('status') or 'supported'}{' preferred' if version.get('preferred') else ''}]"
                    for version in supported_versions
                )
            )
        else:
            lines.append("  supported_versions: none")
        lines.append(f"  hooks: {_surface_summary(hooks)}")
        for hook_name, hook_spec in sorted(hooks.items()):
            lines.append(
                "  "
                + f"{hook_name}: category={hook_spec.get('category', 'unknown')}; "
                + f"status={hook_spec.get('status', 'unknown')}; "
                + f"command={hook_spec.get('command') or 'none'}; "
                + f"notes={hook_spec.get('notes') or 'none'}"
            )
        lines.append(f"  package_paths: {', '.join(surface.get('package_paths') or []) or 'none'}")
        lines.append(f"  example_paths: {', '.join(surface.get('example_paths') or []) or 'none'}")
        lines.append(f"  proof_kinds: {', '.join(surface.get('proof_kinds') or []) or 'none'}")
    return "\n".join(lines)


def render_surfaces_summary(payload: dict[str, Any]) -> str:
    lines = ["FastDIS workspace surfaces summary"]
    for surface in payload.get("surfaces", []):
        hooks = surface.get("hooks") or {}
        preferred_version = surface.get("preferred_version") or "none"
        supported_versions = ",".join(version["version"] for version in surface.get("supported_versions", [])) or "none"
        lines.append(
            f"{surface['id']}[preferred={preferred_version};versions={supported_versions}]={_surface_summary(hooks)}"
        )
    lines.append(
        "categories="
        + ",".join(
            f"{name}:{category}"
            for name, category in sorted((payload.get("canonical_hook_categories") or {}).items())
        )
    )
    return "\n".join(lines)


def _hook_rows(payload: dict[str, Any], *, category: str | None = None) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for surface in payload.get("surfaces", []):
        surface_id = str(surface.get("id") or "")
        for hook_name, hook_spec in (surface.get("hooks") or {}).items():
            hook_category = str(hook_spec.get("category") or "")
            if category and hook_category != category:
                continue
            rows.append(
                {
                    "surface": surface_id,
                    "hook": str(hook_name),
                    "category": hook_category,
                    "status": str(hook_spec.get("status") or ""),
                    "command": str(hook_spec.get("command") or ""),
                    "notes": str(hook_spec.get("notes") or ""),
                    "requirements": json.dumps(hook_spec.get("requirements") or []),
                }
            )
    return rows


def render_hooks_text(payload: dict[str, Any], *, category: str | None = None) -> str:
    title = "FastDIS workspace hooks"
    if category:
        title += f" ({category})"
    lines = [title, ""]
    for row in _hook_rows(payload, category=category):
        lines.append(
            f"- {row['surface']}.{row['hook']}: "
            f"category={row['category']}; status={row['status']}; "
            f"command={row['command'] or 'none'}; notes={row['notes'] or 'none'}; requirements={row['requirements'] or '[]'}"
        )
    if len(lines) == 2:
        lines.append("- none")
    return "\n".join(lines)


def render_hooks_summary(payload: dict[str, Any], *, category: str | None = None) -> str:
    title = "FastDIS workspace hooks summary"
    if category:
        title += f" ({category})"
    lines = [title]
    for row in _hook_rows(payload, category=category):
        lines.append(f"{row['surface']}.{row['hook']}={row['status']}")
    if len(lines) == 1:
        lines.append("none")
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--view", choices=("matrix", "routes", "surfaces", "hooks", "ci"), default="matrix")
    parser.add_argument("--category", choices=("lifecycle", "proof", "demo", "packaging", "install"))
    parser.add_argument("--format", choices=("text", "json", "summary"), default="text")
    parser.add_argument("--host-class", choices=("windows", "macos", "linux"))
    parser.add_argument("--host-platform-override", choices=("windows", "macos", "linux"), help="Override the detected host platform for route-discovery what-if checks")
    parser.add_argument("--host-system-override", help="Override the detected platform.system() value for route-discovery what-if checks")
    parser.add_argument("--host-machine-override", help="Override the detected platform.machine() value for route-discovery what-if checks")
    parser.add_argument("--surface")
    parser.add_argument("--proof-kind")
    parser.add_argument("--bootstrap-only", action="store_true")
    parser.add_argument("--include-compat", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    load_local_env.load()
    args = parse_args(argv)
    payload_kwargs = {
        "host_system_override": args.host_system_override,
        "host_machine_override": args.host_machine_override,
        "host_platform_override": args.host_platform_override,
    }
    if any(value is not None for value in payload_kwargs.values()):
        payload = build_payload(**payload_kwargs)
    else:
        payload = build_payload()
    if args.view == "hooks" and args.format == "json":
        print(
            json.dumps(
                {
                    "schema": payload["schema"],
                    "workspace": payload["workspace"],
                    "canonical_hook_categories": payload.get("canonical_hook_categories", {}),
                    "hooks": _hook_rows(payload, category=args.category),
                },
                indent=2,
            )
        )
    elif args.view == "hooks" and args.format == "summary":
        print(render_hooks_summary(payload, category=args.category))
    elif args.view == "hooks":
        print(render_hooks_text(payload, category=args.category))
    elif args.view == "ci" and args.format == "json":
        print(
            json.dumps(
                {
                    "schema": payload["schema"],
                    "workspace": payload["workspace"],
                    "ci_rows": _ci_rows(
                        payload,
                        host_class=args.host_class,
                        surface=args.surface,
                        proof_kind=args.proof_kind,
                        bootstrap_only=args.bootstrap_only,
                        include_compat=args.include_compat,
                    ),
                },
                indent=2,
            )
        )
    elif args.view == "ci" and args.format == "summary":
        print(
            render_ci_summary(
                payload,
                host_class=args.host_class,
                surface=args.surface,
                proof_kind=args.proof_kind,
                bootstrap_only=args.bootstrap_only,
                include_compat=args.include_compat,
            )
        )
    elif args.view == "ci":
        print(
            json.dumps(
                _ci_rows(
                    payload,
                    host_class=args.host_class,
                    surface=args.surface,
                    proof_kind=args.proof_kind,
                    bootstrap_only=args.bootstrap_only,
                    include_compat=args.include_compat,
                ),
                indent=2,
            )
        )
    elif args.view == "routes" and args.format == "json":
        print(
            json.dumps(
                {
                    "schema": payload["schema"],
                    "workspace": payload["workspace"],
                    "route_summary": payload.get("route_summary", {}),
                    "routes": payload["routes"],
                },
                indent=2,
            )
        )
    elif args.view == "routes" and args.format == "summary":
        print(render_routes_summary(payload))
    elif args.view == "routes":
        print(render_routes_text(payload))
    elif args.view == "surfaces" and args.format == "json":
        print(json.dumps({"schema": payload["schema"], "workspace": payload["workspace"], "surfaces": payload["surfaces"]}, indent=2))
    elif args.view == "surfaces" and args.format == "summary":
        print(render_surfaces_summary(payload))
    elif args.view == "surfaces":
        print(render_surfaces_text(payload))
    elif args.format == "json":
        print(json.dumps(payload, indent=2))
    elif args.format == "summary":
        print(render_summary(payload))
    else:
        print(render_text(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
