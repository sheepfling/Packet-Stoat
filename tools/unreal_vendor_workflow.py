#!/usr/bin/env python3
"""Operator-facing Unreal vendor-plugin workflow wrapper."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import time

import build_unreal_plugin
import load_local_env
import unreal_env
import workspace_manifest


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT_DIR = ROOT / "artifacts" / "reports" / "unreal_vendor_plugin"
MANIFEST = workspace_manifest.load_manifest()
UNREAL_SURFACE = workspace_manifest.surface_spec("unreal", MANIFEST)
DEFAULT_SUPPORTED_VERSIONS = [
    version["version"] for version in workspace_manifest.surface_versions(UNREAL_SURFACE, MANIFEST)
]


def preferred_unreal_version() -> str:
    return workspace_manifest.surface_preferred_version(UNREAL_SURFACE, MANIFEST)


def supported_unreal_versions_label() -> str:
    return " or ".join(DEFAULT_SUPPORTED_VERSIONS)


def process_provenance(version: str | None) -> dict[str, object]:
    return {
        "leading_edge_reporting": True,
        "process_matters_as_evidence": True,
        "operator_interventions": [
            {
                "kind": "source-prep",
                "value": "cmake -B extern/build-fastdis -S extern -DCMAKE_BUILD_TYPE=Release && cmake --build extern/build-fastdis --target install --config Release",
                "reason": "hydrate cesium-native dependencies and install ThirdParty headers/libs into the plugin checkout",
            },
            {
                "kind": "toolchain-alignment",
                "value": "On Windows, pin CMake/vcpkg to Unreal's preferred MSVC family from Engine/Config/Windows/Windows_SDK.json.",
                "reason": "avoid cesium-native static libraries being built with a newer STL/toolchain than UnrealBuildTool will use for plugin linking",
            },
            {
                "kind": "cache-normalization",
                "value": "If ezvcpkg emits tinyxml2Config.cmake with backslashes, normalize them to forward slashes and rerun CMake configure.",
                "reason": "work around Windows path escaping that can break source prep before compilation starts",
            },
        ],
        "engine_lane": version or preferred_unreal_version(),
        "reporting_expectation": "Report any cache-file normalization, path-escaping workaround, or toolchain override used during source prep together with the resulting package proof.",
    }


def run_step(cmd: list[str]) -> int:
    print("+", " ".join(str(part) for part in cmd))
    completed = subprocess.run(cmd, cwd=ROOT, env=unreal_env.build_env())
    return completed.returncode


def run_step_in_dir(cmd: list[str], cwd: Path) -> int:
    print("+", " ".join(str(part) for part in cmd))
    completed = subprocess.run(cmd, cwd=cwd, env=unreal_env.build_env())
    return completed.returncode


def vendor_slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    if not slug:
        raise SystemExit("Vendor id must not be empty.")
    return slug


def vendor_env_token(value: str) -> str:
    return vendor_slug(value).replace("-", "_").upper()


def _resolve_env_path(keys: list[str]) -> Path | None:
    for key in keys:
        raw = os.environ.get(key)
        if raw:
            return Path(raw).expanduser()
    return None


def resolve_plugin_root(vendor: str, explicit: str | None) -> Path | None:
    if explicit:
        return Path(explicit).expanduser().resolve()
    env_token = vendor_env_token(vendor)
    candidate = _resolve_env_path(
        [
            f"FASTDIS_{env_token}_PLUGIN_ROOT",
            f"FASTDIS_{env_token}_UNREAL_PLUGIN_ROOT",
            "FASTDIS_UNREAL_VENDOR_PLUGIN_ROOT",
        ]
    )
    return None if candidate is None else candidate.resolve()


def resolve_uplugin_path(vendor: str, plugin_root: Path | None, explicit: str | None) -> Path | None:
    if explicit:
        candidate = Path(explicit).expanduser()
        if not candidate.is_absolute() and plugin_root is not None:
            candidate = plugin_root / candidate
        return candidate.resolve()

    env_token = vendor_env_token(vendor)
    env_candidate = _resolve_env_path(
        [
            f"FASTDIS_{env_token}_UPLUGIN",
            "FASTDIS_UNREAL_VENDOR_UPLUGIN",
        ]
    )
    if env_candidate is not None:
        if not env_candidate.is_absolute() and plugin_root is not None:
            env_candidate = plugin_root / env_candidate
        return env_candidate.resolve()

    if plugin_root is None or not plugin_root.is_dir():
        return None
    matches = sorted(plugin_root.glob("*.uplugin"))
    if not matches:
        return None
    if len(matches) > 1:
        names = ", ".join(path.name for path in matches)
        raise SystemExit(
            f"Multiple .uplugin files found under {plugin_root}: {names}. "
            "Pass --uplugin to select one explicitly."
        )
    return matches[0].resolve()


def install_for_version(version: str | None) -> unreal_env.UnrealInstall | None:
    installs = unreal_env.discover_installs()
    if version is not None:
        for install in installs:
            if unreal_env.version_matches(version, install.version):
                return install
        return None
    if installs:
        return installs[0]
    return None


def _version_label(version: str | None) -> str:
    return version or "default"


def _unreal_root_hint() -> str:
    system = unreal_env.platform.system().lower()
    if system == "windows":
        return r'FASTDIS_UNREAL_ROOTS="C:\Program Files\Epic Games;D:\Epic Games;C:\Users\Public\Unreal\engines"'
    if system == "darwin":
        return 'FASTDIS_UNREAL_ROOTS="/Users/Shared/Epic Games:/Applications"'
    return 'FASTDIS_UNREAL_ROOTS="$HOME/UnrealEngine:/opt/UnrealEngine"'


def _selected_stable_over_newer_prerelease(selected: unreal_env.UnrealInstall | None, installs: list[unreal_env.UnrealInstall]) -> str | None:
    if selected is None or unreal_env.version_kind(selected.version) != "stable":
        return None
    selected_parsed = unreal_env._parse_unreal_version(selected.version)
    if selected_parsed is None:
        return None
    selected_base = tuple(selected_parsed["parts"])
    newer_prereleases: list[str] = []
    for install in installs:
        if install.install_root == selected.install_root:
            continue
        kind = unreal_env.version_kind(install.version)
        parsed = unreal_env._parse_unreal_version(install.version)
        if parsed is None or not kind.startswith("prerelease:"):
            continue
        if tuple(parsed["parts"]) > selected_base:
            newer_prereleases.append(str(install.version or "unknown"))
    if not newer_prereleases:
        return None
    return ",".join(newer_prereleases)


def plugin_uses_source_checkout(plugin_root: Path | None) -> bool:
    if plugin_root is None:
        return False
    return (plugin_root / "extern" / "CMakeLists.txt").is_file()


def source_third_party_include_dir(plugin_root: Path) -> Path:
    return plugin_root / "Source" / "ThirdParty" / "include"


def source_third_party_lib_dir(plugin_root: Path) -> Path:
    return plugin_root / "Source" / "ThirdParty" / "lib"


def source_checkout_prepared(plugin_root: Path | None) -> bool:
    if plugin_root is None:
        return False
    include_dir = source_third_party_include_dir(plugin_root)
    lib_dir = source_third_party_lib_dir(plugin_root)
    return include_dir.is_dir() and any(lib_dir.glob("*"))


def _parse_windows_sdk_json(install: unreal_env.UnrealInstall | None) -> dict[str, object] | None:
    if install is None:
        return None
    path = Path(install.install_root) / "Engine" / "Config" / "Windows" / "Windows_SDK.json"
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def preferred_msvc_toolchain(install: unreal_env.UnrealInstall | None) -> dict[str, str] | None:
    if unreal_env.platform.system().lower() != "windows":
        return None
    payload = _parse_windows_sdk_json(install)
    if not isinstance(payload, dict):
        return None
    preferred = payload.get("PreferredVisualCppVersions")
    if not isinstance(preferred, list) or not preferred:
        return None
    first = str(preferred[0])
    minimum = first.split("-")[0]
    family = ".".join(minimum.split(".")[:2]) if minimum else ""
    if not family:
        return None
    return {"family": family, "minimum": minimum}


def _parse_version_tuple(value: str) -> tuple[int, ...]:
    return tuple(int(part) for part in value.split(".") if part)


def _version_in_range(version: str, bounds: str) -> bool:
    lower, _, upper = bounds.partition("-")
    parsed = _parse_version_tuple(version)
    if lower and parsed < _parse_version_tuple(lower):
        return False
    if upper and parsed > _parse_version_tuple(upper):
        return False
    return True


def installed_msvc_toolchains() -> list[str]:
    if unreal_env.platform.system().lower() != "windows":
        return []
    root = Path(r"C:\Program Files\Microsoft Visual Studio\18\Community\VC\Tools\MSVC")
    if not root.is_dir():
        return []
    versions = [entry.name for entry in root.iterdir() if entry.is_dir() and re.fullmatch(r"\d+\.\d+\.\d+", entry.name)]
    return sorted(versions, key=_parse_version_tuple)


def installed_msvc_toolchain_details() -> list[dict[str, str]]:
    versions = installed_msvc_toolchains()
    details: list[dict[str, str]] = []
    for folder_version in versions:
        cl_path = (
            Path(r"C:\Program Files\Microsoft Visual Studio\18\Community\VC\Tools\MSVC")
            / folder_version
            / "bin"
            / "Hostx64"
            / "x64"
            / "cl.exe"
        )
        compiler_version = folder_version
        if cl_path.is_file():
            try:
                powershell = [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    f"(Get-Item '{cl_path}').VersionInfo.ProductVersion",
                ]
                completed = subprocess.run(
                    powershell,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if completed.returncode == 0:
                    raw_version = completed.stdout.strip()
                    normalized = ".".join(raw_version.split(".")[:3])
                    if re.fullmatch(r"\d+\.\d+\.\d+", normalized):
                        compiler_version = normalized
            except OSError:
                pass
        details.append(
            {
                "folder_version": folder_version,
                "compiler_version": compiler_version,
                "family": ".".join(compiler_version.split(".")[:2]),
            }
        )
    return details


def resolve_msvc_toolchain(install: unreal_env.UnrealInstall | None) -> dict[str, object] | None:
    if unreal_env.platform.system().lower() != "windows":
        return None
    payload = _parse_windows_sdk_json(install)
    if not isinstance(payload, dict):
        return None
    installed = installed_msvc_toolchain_details()
    preferred_ranges = [str(value) for value in payload.get("PreferredVisualCppVersions", []) if str(value).strip()]
    banned_ranges = [str(value) for value in payload.get("BannedVisualCppVersions", []) if str(value).strip()]
    minimum_version = str(payload.get("MinimumVisualCppVersion", "")).strip()

    def is_banned(version: str) -> bool:
        return any(_version_in_range(version, bounds) for bounds in banned_ranges)

    chosen_folder = ""
    chosen_compiler = ""
    selection_reason = ""
    for bounds in preferred_ranges:
        for toolchain in installed:
            compiler_version = str(toolchain["compiler_version"])
            if is_banned(compiler_version):
                continue
            if _version_in_range(compiler_version, bounds):
                chosen_folder = str(toolchain["folder_version"])
                chosen_compiler = compiler_version
                selection_reason = "preferred"
                break
        if chosen_folder:
            break
    if not chosen_folder:
        eligible = [
            toolchain
            for toolchain in installed
            if not is_banned(str(toolchain["compiler_version"]))
            and (
                not minimum_version
                or _parse_version_tuple(str(toolchain["compiler_version"])) >= _parse_version_tuple(minimum_version)
            )
        ]
        if eligible:
            chosen_folder = str(eligible[-1]["folder_version"])
            chosen_compiler = str(eligible[-1]["compiler_version"])
            selection_reason = "fallback"

    preferred = preferred_msvc_toolchain(install)
    family = ".".join(chosen_compiler.split(".")[:2]) if chosen_compiler else ""
    return {
        "preferred": preferred,
        "preferred_ranges": preferred_ranges,
        "banned_ranges": banned_ranges,
        "minimum_version": minimum_version,
        "installed_versions": [str(toolchain["compiler_version"]) for toolchain in installed],
        "installed_toolchains": installed,
        "selected_version": chosen_compiler,
        "selected_folder_version": chosen_folder,
        "selected_family": family,
        "selection_reason": selection_reason,
    }


def _extract_msvc_version(text: str | None) -> str | None:
    if not text:
        return None
    match = re.search(r"MSVC[\\/](?P<version>\d+\.\d+\.\d+)", text.replace("\\", "/"))
    if match:
        return match.group("version")
    return None


def source_prep_toolchain(plugin_root: Path | None) -> dict[str, str] | None:
    if plugin_root is None:
        return None
    cache_path = plugin_root / "extern" / "build-fastdis" / "CMakeCache.txt"
    if not cache_path.is_file():
        return None
    try:
        text = cache_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    generator_match = re.search(r"^CMAKE_GENERATOR:INTERNAL=(?P<value>.+)$", text, re.MULTILINE)
    toolset_match = re.search(r"^CMAKE_GENERATOR_TOOLSET:INTERNAL=(?P<value>.*)$", text, re.MULTILINE)
    linker_match = re.search(r"^CMAKE_LINKER:FILEPATH=(?P<value>.+)$", text, re.MULTILINE)
    ar_match = re.search(r"^CMAKE_AR:FILEPATH=(?P<value>.+)$", text, re.MULTILINE)
    version = _extract_msvc_version(linker_match.group("value") if linker_match else None) or _extract_msvc_version(ar_match.group("value") if ar_match else None)
    family = ".".join(version.split(".")[:2]) if version else None
    return {
        "cache": str(cache_path),
        "generator": generator_match.group("value").strip() if generator_match else "",
        "generator_toolset": toolset_match.group("value").strip() if toolset_match else "",
        "msvc_version": version or "",
        "msvc_family": family or "",
    }


def normalize_tinyxml2_config(work_root: Path | None = None) -> list[str]:
    root = work_root or unreal_env.work_root()
    search_root = root / "home" / ".ezvcpkg"
    if not search_root.is_dir():
        return []
    normalized: list[str] = []
    for path in search_root.glob("**/share/tinyxml2/tinyxml2Config.cmake"):
        try:
            original = path.read_text(encoding="utf-8")
        except OSError:
            continue
        updated = original.replace("\\", "/")
        if updated == original:
            continue
        path.write_text(updated, encoding="utf-8")
        normalized.append(str(path))
    return normalized


def remove_tree(path: Path) -> None:
    if not path.exists():
        return

    def _onexc(func, entry_path, exc) -> None:
        if isinstance(exc, PermissionError):
            try:
                os.chmod(entry_path, stat.S_IWRITE)
            except OSError:
                pass
            try:
                func(entry_path)
            except OSError:
                pass
            return
        raise exc

    shutil.rmtree(path, onexc=_onexc)


def doctor_payload(
    vendor: str,
    version: str | None,
    plugin_root_arg: str | None,
    uplugin_arg: str | None,
) -> dict[str, object]:
    install = install_for_version(version)
    resolved_plugin_root = resolve_plugin_root(vendor, plugin_root_arg)
    resolved_uplugin = resolve_uplugin_path(vendor, resolved_plugin_root, uplugin_arg)

    payload: dict[str, object] = {
        "vendor": vendor_slug(vendor),
        "requested_version": version,
        "resolved_version": install.version if install is not None else None,
        "status": "ok",
        "plugin_root": str(resolved_plugin_root) if resolved_plugin_root is not None else None,
        "uplugin": str(resolved_uplugin) if resolved_uplugin is not None else None,
        "install": install.to_dict() if install is not None else None,
        "checks": [],
        "next_steps": [],
        "source_checkout": False,
        "source_checkout_prepared": None,
    }

    checks: list[dict[str, str]] = []

    def add_check(name: str, status: str, detail: str) -> None:
        checks.append({"name": name, "status": status, "detail": detail})

    if resolved_plugin_root is None:
        add_check("plugin_root", "fail", f"no plugin root configured for vendor {vendor_slug(vendor)}")
    elif not resolved_plugin_root.exists():
        add_check("plugin_root", "fail", f"plugin root does not exist: {resolved_plugin_root}")
    elif not resolved_plugin_root.is_dir():
        add_check("plugin_root", "fail", f"plugin root is not a directory: {resolved_plugin_root}")
    else:
        add_check("plugin_root", "ok", str(resolved_plugin_root))

    if resolved_uplugin is None:
        add_check("plugin_descriptor", "fail", f"no .uplugin resolved for vendor {vendor_slug(vendor)}")
    elif not resolved_uplugin.exists():
        add_check("plugin_descriptor", "fail", f"plugin descriptor does not exist: {resolved_uplugin}")
    else:
        add_check("plugin_descriptor", "ok", str(resolved_uplugin))

    uses_source_checkout = plugin_uses_source_checkout(resolved_plugin_root)
    payload["source_checkout"] = uses_source_checkout
    if uses_source_checkout and resolved_plugin_root is not None:
        prepared = source_checkout_prepared(resolved_plugin_root)
        payload["source_checkout_prepared"] = prepared
        include_dir = source_third_party_include_dir(resolved_plugin_root)
        lib_dir = source_third_party_lib_dir(resolved_plugin_root)
        resolved_toolchain = resolve_msvc_toolchain(install)
        preferred_toolchain = resolved_toolchain["preferred"] if resolved_toolchain is not None else None
        cached_toolchain = source_prep_toolchain(resolved_plugin_root)
        add_check("source_checkout", "ok", "extern/CMakeLists.txt present")
        add_check(
            "third_party_include",
            "ok" if include_dir.is_dir() else "fail",
            str(include_dir),
        )
        add_check(
            "third_party_lib",
            "ok" if lib_dir.is_dir() and any(lib_dir.glob("*")) else "fail",
            str(lib_dir),
        )
        if preferred_toolchain is not None:
            add_check(
                "preferred_msvc_toolchain",
                "ok",
                f"{preferred_toolchain['family']} (minimum installed version hint {preferred_toolchain['minimum']})",
            )
        if resolved_toolchain is not None:
            selected_version = str(resolved_toolchain.get("selected_version") or "")
            selected_folder_version = str(resolved_toolchain.get("selected_folder_version") or "")
            selection_reason = str(resolved_toolchain.get("selection_reason") or "")
            installed_versions = ", ".join(
                f"{toolchain['compiler_version']} via {toolchain['folder_version']}"
                for toolchain in resolved_toolchain.get("installed_toolchains", [])
            ) or "none detected"
            preferred_ranges = ", ".join(str(value) for value in resolved_toolchain.get("preferred_ranges", [])) or "none declared"
            if selected_version:
                status = "ok" if selection_reason == "preferred" else "warn"
                detail = (
                    f"{selected_version} via {selected_folder_version or 'unknown folder'} ({selection_reason}); "
                    f"installed: {installed_versions}; preferred ranges: {preferred_ranges}"
                )
            else:
                status = "fail"
                detail = f"no usable installed MSVC toolchain found; installed: {installed_versions}; preferred ranges: {preferred_ranges}"
            add_check("installed_msvc_toolchain", status, detail)
        if cached_toolchain is not None and cached_toolchain.get("msvc_family"):
            status = "ok"
            detail = (
                f"{cached_toolchain['msvc_version']} via {cached_toolchain['generator'] or 'unknown generator'}"
            )
            selected_family = str(resolved_toolchain.get("selected_family") or "") if resolved_toolchain is not None else ""
            if selected_family and cached_toolchain["msvc_family"] != selected_family:
                status = "fail"
                detail = (
                    f"{cached_toolchain['msvc_version']} via {cached_toolchain['generator'] or 'unknown generator'} "
                    f"does not match selected source-prep family {selected_family}"
                )
            add_check("source_prep_toolchain", status, detail)
    elif resolved_plugin_root is not None:
        payload["source_checkout_prepared"] = None
        add_check("source_checkout", "ok", "plugin root does not expose the cesium-unreal extern source layout")

    if install is None:
        add_check("engine install", "fail", f"no Unreal install discovered for {_version_label(version)}")
        add_check("discovery roots", "warn", f"no install discovered; try {_unreal_root_hint()}")
    else:
        add_check("engine root", "ok", install.install_root)
        add_check("version kind", "ok", unreal_env.version_kind(install.version))
        add_check("editor", "ok" if install.editor_path is not None else "fail", install.editor_path or "missing editor executable")
        add_check("automation tool", "ok" if install.uat_path is not None else "fail", install.uat_path or "missing RunUAT")
        add_check("build tool", "ok" if install.ubt_path is not None else "fail", install.ubt_path or "missing UnrealBuildTool.dll")
        add_check("bundled dotnet", "ok" if install.dotnet_path is not None else "fail", install.dotnet_path or "missing bundled dotnet")
        prerelease_note = _selected_stable_over_newer_prerelease(install, unreal_env.discover_installs())
        if prerelease_note:
            add_check("version selection", "ok", f"selected stable {install.version}; newer prerelease installs also exist: {prerelease_note}")
        permissions = unreal_env.permission_probe(install)
        payload["permissions"] = permissions
        for check in permissions["checks"]:
            add_check(f"permission:{check['name']}", str(check["status"]), str(check["detail"]))

    payload["checks"] = checks
    failures = [check for check in checks if check["status"] == "fail"]
    payload["status"] = "ok" if not failures else "needs-attention"

    if failures:
        payload["next_steps"] = [
            f"Set FASTDIS_{vendor_env_token(vendor)}_PLUGIN_ROOT to the local plugin checkout root, or pass --plugin-root.",
            "If the plugin descriptor is not at the plugin root, pass --uplugin with the .uplugin filename or path.",
            "Set FASTDIS_UNREAL_ENGINE_DIR or FASTDIS_UNREAL_ENGINE_DIR_5_8 style variables so Unreal discovery can find a supported install.",
            f"If Unreal is installed outside the standard launcher roots, try {_unreal_root_hint()}.",
            "If this is a raw cesium-unreal source checkout, run python tools/unreal_vendor_workflow.py prepare-source --vendor cesium --engine-version <version> before BuildPlugin.",
            "If source prep already ran on Windows, verify its CMake/vcpkg toolchain matches Unreal's preferred MSVC family before trusting linker failures.",
            "Run `python tools/list_unreal_installs.py` to inspect available Unreal versions on this machine.",
        ]
    else:
        suggested_version = install.version or preferred_unreal_version()
        payload["next_steps"] = [
            f"Package the preferred lane: python tools/unreal_vendor_workflow.py build --vendor {vendor_slug(vendor)} --engine-version {suggested_version}",
            f"Run the cross-version matrix: python tools/unreal_vendor_workflow.py matrix --vendor {vendor_slug(vendor)} --versions {' '.join(DEFAULT_SUPPORTED_VERSIONS)}",
        ]
    return payload


def print_doctor(payload: dict[str, object]) -> None:
    requested = payload["requested_version"] or "default"
    resolved = payload["resolved_version"] or "none"
    print(f"Unreal vendor doctor for {payload['vendor']}")
    print(f"status: {payload['status']}")
    print(f"requested_version: {requested}")
    print(f"resolved_version: {resolved}")
    print(f"plugin_root: {payload['plugin_root'] or 'missing'}")
    print(f"uplugin: {payload['uplugin'] or 'missing'}")
    print(f"source_checkout: {payload['source_checkout']}")
    print(f"source_checkout_prepared: {payload['source_checkout_prepared']}")
    print("checks:")
    for check in payload["checks"]:
        print(f"  - {check['name']}: {check['status']} ({check['detail']})")
    print("next:")
    for step in payload["next_steps"]:
        print(f"  - {step}")


def _default_build_report_paths(vendor: str, version: str | None) -> tuple[Path, Path]:
    version_slug = (version or preferred_unreal_version()).replace(".", "_")
    base = DEFAULT_REPORT_DIR / f"{vendor_slug(vendor)}_{version_slug}_build"
    return base.with_suffix(".json"), base.with_suffix(".md")


def _default_progress_report_paths(vendor: str, version: str | None) -> tuple[Path, Path]:
    version_slug = (version or preferred_unreal_version()).replace(".", "_")
    base = DEFAULT_REPORT_DIR / f"{vendor_slug(vendor)}_{version_slug}_progress"
    return base.with_suffix(".json"), base.with_suffix(".md")


def _default_progress_events_path(vendor: str, version: str | None) -> Path:
    version_slug = (version or preferred_unreal_version()).replace(".", "_")
    base = DEFAULT_REPORT_DIR / f"{vendor_slug(vendor)}_{version_slug}_progress"
    return base.with_suffix(".jsonl")


def _default_install_smoke_report_paths(vendor: str, version: str | None) -> tuple[Path, Path]:
    version_slug = (version or preferred_unreal_version()).replace(".", "_")
    base = DEFAULT_REPORT_DIR / f"{vendor_slug(vendor)}_{version_slug}_install_smoke"
    return base.with_suffix(".json"), base.with_suffix(".md")


def _default_handoff_paths(vendor: str, version: str | None) -> tuple[Path, Path]:
    version_slug = (version or preferred_unreal_version()).replace(".", "_")
    base = DEFAULT_REPORT_DIR / f"{vendor_slug(vendor)}_{version_slug}_upstream_handoff"
    return base.with_suffix(".json"), base.with_suffix(".md")


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _truncate_line(value: str | None, limit: int = 300) -> str:
    text = str(value or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def render_progress_markdown(report: dict[str, object]) -> str:
    lines = [
        "# Unreal Vendor Lane Progress",
        "",
        f"- status: `{report.get('status')}`",
        f"- phase: `{report.get('phase')}`",
        f"- vendor: `{report.get('vendor')}`",
        f"- engine_version: `{report.get('engine_version') or 'unknown'}`",
        f"- started_at: `{report.get('started_at')}`",
        f"- updated_at: `{report.get('updated_at')}`",
        f"- elapsed_seconds: `{report.get('elapsed_seconds')}`",
        f"- selected_compiler_version: `{report.get('selected_compiler_version') or ''}`",
        f"- selected_folder_version: `{report.get('selected_folder_version') or ''}`",
        f"- selection_reason: `{report.get('selection_reason') or ''}`",
        f"- last_completed_step: `{report.get('last_completed_step') or ''}`",
        f"- current_log: `{report.get('current_log') or ''}`",
        "",
    ]
    last_log_line = str(report.get("last_log_line") or "").strip()
    if last_log_line:
        lines.extend(["## Last Log Line", "", "```text", last_log_line, "```", ""])
    return "\n".join(lines)


def write_progress_report(payload: dict[str, object], json_out: Path, md_out: Path) -> None:
    json_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    md_out.write_text(render_progress_markdown(payload), encoding="utf-8")


def append_progress_event(
    event_path: Path,
    *,
    vendor: str,
    version: str | None,
    event: str,
    phase: str,
    detail: str | None = None,
) -> None:
    event_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "timestamp": _utc_now(),
        "vendor": vendor_slug(vendor),
        "engine_version": version,
        "event": event,
        "phase": phase,
    }
    if detail:
        payload["detail"] = detail
    with event_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload) + "\n")


def progress_payload(
    *,
    vendor: str,
    version: str | None,
    resolved_toolchain: dict[str, object] | None,
    json_out: Path,
    md_out: Path,
) -> dict[str, object]:
    started_at = _utc_now()
    return {
        "schema": "packet_stoat.unreal_vendor_progress.v1",
        "vendor": vendor_slug(vendor),
        "engine_version": version,
        "status": "running",
        "phase": "starting",
        "started_at": started_at,
        "updated_at": started_at,
        "elapsed_seconds": 0.0,
        "selected_compiler_version": str(resolved_toolchain.get("selected_version") or "") if resolved_toolchain else "",
        "selected_folder_version": str(resolved_toolchain.get("selected_folder_version") or "") if resolved_toolchain else "",
        "selection_reason": str(resolved_toolchain.get("selection_reason") or "") if resolved_toolchain else "",
        "last_completed_step": "",
        "current_log": "",
        "last_log_line": "",
        "pid": None,
        "report_json": str(json_out),
        "report_markdown": str(md_out),
        "events_jsonl": str(_default_progress_events_path(vendor, version)),
    }


def update_progress_report(
    payload: dict[str, object],
    *,
    json_out: Path | None = None,
    md_out: Path | None = None,
    status: str | None = None,
    phase: str | None = None,
    current_log: str | None = None,
    last_log_line: str | None = None,
    last_completed_step: str | None = None,
    pid: int | None = None,
) -> None:
    if status is not None:
        payload["status"] = status
    if phase is not None:
        payload["phase"] = phase
    if current_log is not None:
        payload["current_log"] = current_log
    if last_log_line is not None:
        payload["last_log_line"] = _truncate_line(last_log_line)
    if last_completed_step is not None:
        payload["last_completed_step"] = last_completed_step
    if pid is not None:
        payload["pid"] = pid
    started_raw = str(payload.get("started_at") or "")
    try:
        started = datetime.fromisoformat(started_raw)
    except ValueError:
        started = datetime.now(UTC)
    now = datetime.now(UTC)
    payload["updated_at"] = now.isoformat()
    payload["elapsed_seconds"] = round((now - started).total_seconds(), 3)
    write_progress_report(
        payload,
        json_out or Path(str(payload["report_json"])).resolve(),
        md_out or Path(str(payload["report_markdown"])).resolve(),
    )


def _phase_from_build_output(line: str, current_phase: str) -> tuple[str, str | None]:
    text = line.strip()
    if not text:
        return current_phase, None
    if text.startswith("Running AutomationTool"):
        return "automationtool", None
    if text.startswith("Building plugin for host platforms"):
        return "buildplugin_host", None
    if text.startswith("Building UnrealEditor"):
        return "buildplugin_editor", None
    if "Building UnrealGame - UnrealGame - Win64 Development" in text:
        return "buildplugin_game_development", None
    if "Building UnrealGame - UnrealGame - Win64 Shipping" in text:
        return "buildplugin_game_shipping", None
    if text.startswith("Result: Succeeded"):
        return current_phase, current_phase
    return current_phase, None


def render_build_markdown(report: dict[str, object]) -> str:
    lines = [
        "# Unreal Vendor Plugin Build",
        "",
        f"- vendor: `{report['vendor']}`",
        f"- engine_version: `{report.get('engine_version', 'unknown')}`",
        f"- status: `{report['status']}`",
        f"- plugin_root: `{report.get('plugin_root', '')}`",
        f"- uplugin: `{report.get('uplugin', '')}`",
        f"- package_dir: `{report.get('package_dir', '')}`",
        "",
    ]
    resolved_toolchain = report.get("resolved_msvc_toolchain")
    if isinstance(resolved_toolchain, dict):
        selected_version = str(resolved_toolchain.get("selected_version") or "")
        selected_folder_version = str(resolved_toolchain.get("selected_folder_version") or "")
        selection_reason = str(resolved_toolchain.get("selection_reason") or "")
        if selected_version:
            lines.extend(
                [
                    "## Toolchain",
                    "",
                    f"- selected_compiler_version: `{selected_version}`",
                    f"- selected_folder_version: `{selected_folder_version or 'unknown'}`",
                    f"- selection_reason: `{selection_reason or 'unknown'}`",
                    "",
                ]
            )
    command = report.get("build_command") or []
    if command:
        lines.extend(["## Repro", "", "```bash", " ".join(str(part) for part in command), "```", ""])
    detail = str(report.get("detail") or "").strip()
    if detail:
        lines.extend(["## Detail", "", "```text", detail, "```", ""])
    return "\n".join(lines)


def write_build_report(payload: dict[str, object], json_out: Path, md_out: Path) -> None:
    json_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    md_out.write_text(render_build_markdown(payload), encoding="utf-8")


def render_handoff_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Cesium Unreal Upstream Handoff",
        "",
        f"- vendor: `{payload['vendor']}`",
        f"- engine_version: `{payload['engine_version']}`",
        f"- baseline_version: `{payload['baseline_version']}`",
        f"- status: `{payload['status']}`",
        f"- failure_class: `{payload['failure_class']}`",
        f"- source_repo: `{payload['source_repo']}`",
        f"- build_report_json: `{payload['build_report_json']}`",
        f"- install_smoke_json: `{payload.get('install_smoke_json') or ''}`",
        "",
        "## Suggested Title",
        "",
        payload["title"],
        "",
        "## Suggested Issue Body",
        "",
        payload["issue_body_markdown"].rstrip(),
        "",
    ]
    return "\n".join(lines)


def write_handoff(payload: dict[str, object], json_out: Path, md_out: Path) -> None:
    json_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    md_out.write_text(render_handoff_markdown(payload), encoding="utf-8")


def default_package_dir(vendor: str, descriptor: Path, version: str | None) -> Path:
    version_slug = (version or preferred_unreal_version()).replace(".", "_")
    return ROOT / "build" / "unreal_vendor_plugins" / vendor_slug(vendor) / version_slug / descriptor.stem


def _target_platforms(raw: str | None) -> list[str]:
    return build_unreal_plugin.parse_target_platforms(raw, build_unreal_plugin.host_platform_name())


def classify_build_failure(build_report: dict[str, object], install_report: dict[str, object] | None) -> str:
    if build_report.get("status") == "dry-run":
        return "dry-run"
    if build_report.get("status") != "ok":
        failure_text = "\n".join(
            str(value)
            for value in [
                build_report.get("detail"),
                build_report.get("raw_output"),
            ]
            if value
        ).lower()
        if any(token in failure_text for token in ("error c", "error lnk", ": error:", "fatal error", "undefined symbol", "undefined reference")):
            return "compile-or-link"
        if "platform " in failure_text and "not a valid platform to build" in failure_text:
            return "host-platform-unavailable"
        if any(token in failure_text for token in ("access is denied", "unauthorizedaccessexception", "permission")):
            return "engine-permission"
    return "build-failed"


def _run_buildplugin_with_progress(
    cmd: list[str],
    *,
    progress: dict[str, object] | None,
    vendor: str,
    version: str | None,
) -> None:
    print("+", " ".join(str(part) for part in cmd))
    captured: list[str] = []
    progress_json = Path(str(progress["report_json"])).resolve() if progress is not None else None
    progress_md = Path(str(progress["report_markdown"])).resolve() if progress is not None else None
    event_path = Path(str(progress["events_jsonl"])).resolve() if progress is not None else None
    current_phase = str(progress.get("phase") or "buildplugin") if progress is not None else "buildplugin"

    for attempt in range(3):
        completed_output: list[str] = []
        process = subprocess.Popen(
            cmd,
            cwd=ROOT,
            env=unreal_env.build_env(),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        if progress is not None:
            update_progress_report(
                progress,
                json_out=progress_json,
                md_out=progress_md,
                phase=current_phase,
                current_log="running BuildPlugin",
                pid=process.pid,
            )
            if event_path is not None and attempt == 0:
                append_progress_event(
                    event_path,
                    vendor=vendor,
                    version=version,
                    event="buildplugin_started",
                    phase=current_phase,
                    detail="BuildPlugin subprocess launched",
                )
        assert process.stdout is not None
        for raw_line in process.stdout:
            print(raw_line, end="")
            completed_output.append(raw_line)
            next_phase, completed_phase = _phase_from_build_output(raw_line, current_phase)
            if progress is not None:
                if next_phase != current_phase:
                    current_phase = next_phase
                    update_progress_report(
                        progress,
                        json_out=progress_json,
                        md_out=progress_md,
                        phase=current_phase,
                        current_log=f"phase {current_phase}",
                        last_log_line=raw_line,
                    )
                    if event_path is not None:
                        append_progress_event(
                            event_path,
                            vendor=vendor,
                            version=version,
                            event="phase_changed",
                            phase=current_phase,
                            detail=_truncate_line(raw_line),
                        )
                else:
                    update_progress_report(
                        progress,
                        json_out=progress_json,
                        md_out=progress_md,
                        current_log=f"phase {current_phase}",
                        last_log_line=raw_line,
                    )
                if completed_phase and event_path is not None:
                    append_progress_event(
                        event_path,
                        vendor=vendor,
                        version=version,
                        event="phase_succeeded",
                        phase=completed_phase,
                        detail="Result: Succeeded",
                    )
                    update_progress_report(
                        progress,
                        json_out=progress_json,
                        md_out=progress_md,
                        last_completed_step=completed_phase,
                    )
        process.wait()
        output = "".join(completed_output)
        if process.returncode == 0:
            return

        if "A conflicting instance of AutomationTool is already running" in output:
            if progress is not None:
                update_progress_report(
                    progress,
                    json_out=progress_json,
                    md_out=progress_md,
                    status="fail",
                    current_log="AutomationTool conflict",
                    last_log_line=output,
                )
            raise SystemExit(
                "Unreal AutomationTool is already running for another build on this machine. "
                "Wait for the other Unreal build to finish, or terminate the stale AutomationTool process, then rerun "
                "`python tools/unreal_workflow.py build --engine-version ...`."
            )
        if "A conflicting instance of Global\\UnrealBuildTool_Mutex_" in output and attempt < 2:
            print("warning: UnrealBuildTool mutex was busy; retrying packaging step after a short backoff")
            if progress is not None:
                update_progress_report(
                    progress,
                    json_out=progress_json,
                    md_out=progress_md,
                    current_log="retrying after UnrealBuildTool mutex conflict",
                    last_log_line=output,
                )
            time.sleep(5)
            captured.extend(completed_output)
            continue
        captured.extend(completed_output)
        if progress is not None:
            update_progress_report(
                progress,
                json_out=progress_json,
                md_out=progress_md,
                status="fail",
                current_log="BuildPlugin failed",
                last_log_line=output,
            )
        raise subprocess.CalledProcessError(process.returncode or 1, cmd, output="".join(captured))

    if install_report is None:
        return "packaged-only"
    status = str(install_report.get("status") or "")
    if status == "pass":
        return "verified-build"
    log_summary = install_report.get("log_summary")
    if isinstance(log_summary, dict) and log_summary.get("failure_kind"):
        return str(log_summary["failure_kind"])
    if status in {"missing-report", "missing-install", "missing-package", "missing-plugin-descriptor"}:
        return status
    return "install-smoke-failed"


def package_plugin(
    *,
    vendor: str,
    version: str | None,
    plugin_root_arg: str | None,
    uplugin_arg: str | None,
    package_dir_arg: str | None,
    target_platforms_arg: str | None,
    clean_package: bool,
    skip_platform_probe: bool,
    dry_run: bool,
    progress: dict[str, object] | None = None,
) -> dict[str, object]:
    install = install_for_version(version)
    if install is None:
        raise SystemExit(
            "Could not locate an Unreal Engine install. Set --engine-version or a FASTDIS_UNREAL_ENGINE_DIR style variable."
        )

    plugin_root = resolve_plugin_root(vendor, plugin_root_arg)
    if plugin_root is None:
        raise SystemExit(
            f"Could not resolve plugin root for vendor {vendor_slug(vendor)}. "
            f"Set FASTDIS_{vendor_env_token(vendor)}_PLUGIN_ROOT or pass --plugin-root."
        )
    if not plugin_root.is_dir():
        raise SystemExit(f"Plugin root is not a directory: {plugin_root}")
    if plugin_uses_source_checkout(plugin_root) and not source_checkout_prepared(plugin_root):
        raise SystemExit(
            f"Plugin root {plugin_root} is a raw cesium-unreal source checkout without Source/ThirdParty output. "
            "Run `python tools/unreal_vendor_workflow.py prepare-source --vendor cesium --engine-version <version>` first."
        )

    descriptor = resolve_uplugin_path(vendor, plugin_root, uplugin_arg)
    if descriptor is None or not descriptor.is_file():
        raise SystemExit(
            f"Could not resolve a .uplugin descriptor under {plugin_root}. Pass --uplugin if needed."
        )

    target_platforms = _target_platforms(target_platforms_arg)
    host_platform = build_unreal_plugin.host_platform_name()
    if any(target != host_platform for target in target_platforms):
        raise SystemExit(
            "This workflow is host-oriented. Run it on the target OS or request only the host target platform. "
            f"Host platform is {host_platform}; requested targets were {target_platforms}."
        )

    engine_root = Path(install.install_root)
    package_dir = (
        Path(package_dir_arg).expanduser().resolve()
        if package_dir_arg
        else default_package_dir(vendor, descriptor, install.version or version)
    )
    package_dir_for_uat = build_unreal_plugin.unreal_safe_dir(
        package_dir,
        f"{vendor_slug(vendor)}_{descriptor.stem}_{(install.version or version or preferred_unreal_version()).replace('.', '_')}",
    )

    if not skip_platform_probe:
        build_unreal_plugin.validate_host_platform_or_warn(engine_root, install.version or version)
    if progress is not None:
        update_progress_report(
            progress,
            phase="preparing",
            current_log="validated host platform and build rules",
        )

    build_unreal_plugin.ensure_build_rules_compatibility(engine_root)
    if clean_package and package_dir.exists():
        remove_tree(package_dir)
    if package_dir_for_uat != package_dir and package_dir_for_uat.exists():
        remove_tree(package_dir_for_uat)

    command = [
        str(build_unreal_plugin.uat_path(engine_root)),
        "BuildPlugin",
        f"-Plugin={descriptor}",
        f"-Package={package_dir_for_uat}",
        f"-TargetPlatforms={'+'.join(target_platforms)}",
    ]
    if dry_run:
        print("+", " ".join(command))
    else:
        if progress is not None:
            update_progress_report(
                progress,
                phase="buildplugin",
                current_log="launching BuildPlugin",
                last_log_line="BuildPlugin",
            )
        _run_buildplugin_with_progress(
            command,
            progress=progress,
            vendor=vendor,
            version=install.version or version,
        )

    packaged_descriptor = package_dir / descriptor.name
    if not dry_run and not packaged_descriptor.is_file():
        raise SystemExit(f"BuildPlugin completed without producing {packaged_descriptor}")
    if progress is not None:
        update_progress_report(
            progress,
            phase="build_complete",
            current_log="BuildPlugin completed and package verified",
            last_completed_step="build_complete",
        )
        append_progress_event(
            Path(str(progress["events_jsonl"])).resolve(),
            vendor=vendor,
            version=install.version or version,
            event="build_completed",
            phase="build_complete",
            detail=str(packaged_descriptor),
        )

    return {
        "vendor": vendor_slug(vendor),
        "engine_version": install.version or version,
        "plugin_root": str(plugin_root),
        "uplugin": str(descriptor),
        "package_dir": str(package_dir),
        "target_platforms": target_platforms,
        "build_command": [str(part) for part in command],
        "status": "dry-run" if dry_run else "ok",
        "process_provenance": process_provenance(install.version or version),
    }


def prepare_source_checkout(
    *,
    vendor: str,
    version: str | None,
    plugin_root_arg: str | None,
    clean_build: bool,
    build_type: str,
    dry_run: bool,
) -> dict[str, object]:
    install = install_for_version(version)
    if install is None:
        raise SystemExit(
            "Could not locate an Unreal Engine install. Set --engine-version or a FASTDIS_UNREAL_ENGINE_DIR style variable."
        )
    plugin_root = resolve_plugin_root(vendor, plugin_root_arg)
    if plugin_root is None or not plugin_root.is_dir():
        raise SystemExit(f"Could not resolve plugin root for vendor {vendor_slug(vendor)}.")
    extern_root = plugin_root / "extern"
    if not extern_root.is_dir() or not (extern_root / "CMakeLists.txt").is_file():
        raise SystemExit(f"Plugin root {plugin_root} does not look like a cesium-unreal source checkout.")

    build_dir = extern_root / "build-fastdis"
    if clean_build and build_dir.exists():
        shutil.rmtree(build_dir)

    env = unreal_env.build_env()
    env["UNREAL_ENGINE_ROOT"] = install.install_root
    configure_cmd = ["cmake", "-B", str(build_dir), "-S", str(extern_root), f"-DCMAKE_BUILD_TYPE={build_type}"]
    resolved_toolchain = resolve_msvc_toolchain(install)
    preferred_toolchain = resolved_toolchain["preferred"] if resolved_toolchain is not None else None
    selected_version = str(resolved_toolchain.get("selected_version") or "") if resolved_toolchain is not None else ""
    selected_folder_version = str(resolved_toolchain.get("selected_folder_version") or "") if resolved_toolchain is not None else ""
    selected_family = str(resolved_toolchain.get("selected_family") or "") if resolved_toolchain is not None else ""
    if unreal_env.platform.system().lower() == "windows" and selected_folder_version and selected_family:
        env["VCPKG_PLATFORM_TOOLSET_VERSION"] = selected_family
        env["VCToolsVersion"] = selected_folder_version
        configure_cmd.extend(["-G", "Visual Studio 18 2026", "-A", "x64"])
    build_cmd = ["cmake", "--build", str(build_dir), "--target", "install", "--config", build_type]

    if dry_run:
        print("+", " ".join(configure_cmd))
        print("+", " ".join(build_cmd))
    else:
        print("+", " ".join(configure_cmd))
        configured = subprocess.run(configure_cmd, cwd=extern_root, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if configured.stdout:
            print(configured.stdout, end="")
        if configured.returncode != 0:
            normalized = normalize_tinyxml2_config()
            if normalized:
                print("warning: normalized tinyxml2 CMake config paths after configure failure")
                print("+", " ".join(configure_cmd))
                configured = subprocess.run(configure_cmd, cwd=extern_root, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                if configured.stdout:
                    print(configured.stdout, end="")
            if configured.returncode != 0:
                raise SystemExit("Cesium Unreal source prep configure failed.")
        print("+", " ".join(build_cmd))
        built = subprocess.run(build_cmd, cwd=extern_root, env=env)
        if built.returncode != 0:
            raise SystemExit("Cesium Unreal source prep build/install failed.")

    return {
        "vendor": vendor_slug(vendor),
        "engine_version": install.version or version,
        "plugin_root": str(plugin_root),
        "extern_root": str(extern_root),
        "build_dir": str(build_dir),
        "build_type": build_type,
        "status": "dry-run" if dry_run else ("ok" if source_checkout_prepared(plugin_root) else "needs-attention"),
        "third_party_include": str(source_third_party_include_dir(plugin_root)),
        "third_party_lib": str(source_third_party_lib_dir(plugin_root)),
        "preferred_msvc_toolchain": preferred_toolchain,
        "resolved_msvc_toolchain": resolved_toolchain,
        "process_provenance": process_provenance(install.version or version),
    }


def _add_common_vendor_args(parser: argparse.ArgumentParser, *, include_engine: bool) -> None:
    parser.add_argument("--vendor", required=True, help="Vendor id, for example cesium")
    if include_engine:
        parser.add_argument("--engine-version", default=preferred_unreal_version())
    parser.add_argument("--plugin-root", help="Vendor plugin root containing the .uplugin")
    parser.add_argument("--uplugin", help="Explicit .uplugin path or filename")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    discover = subparsers.add_parser("discover", help="List detected Unreal installs")
    discover.add_argument("--format", choices=("table", "json"), default="table")

    doctor = subparsers.add_parser("doctor", help="Validate a vendor plugin root against a selected Unreal lane")
    _add_common_vendor_args(doctor, include_engine=False)
    doctor.add_argument("--engine-version", help=f"Versioned Unreal env selector, for example {supported_unreal_versions_label()}")
    doctor.add_argument("--format", choices=("text", "json"), default="text")

    build = subparsers.add_parser("build", help="Package a vendor Unreal plugin with BuildPlugin")
    _add_common_vendor_args(build, include_engine=True)
    build.add_argument("--package-dir", help="Override the BuildPlugin package directory")
    build.add_argument("--target-platforms", help="Unreal BuildPlugin target platforms, for example Mac or Win64")
    build.add_argument("--clean-package", action="store_true", help="Delete the package directory before BuildPlugin")
    build.add_argument("--skip-platform-probe", action="store_true", help="Skip the host compatibility preflight")
    build.add_argument("--dry-run", action="store_true")

    prepare = subparsers.add_parser("prepare-source", help="Prepare a cesium-unreal source checkout by installing ThirdParty dependencies")
    _add_common_vendor_args(prepare, include_engine=True)
    prepare.add_argument("--clean-build", action="store_true", help="Delete the source-prep build directory before configuring CMake")
    prepare.add_argument("--build-type", default="Release", choices=("Debug", "Release", "RelWithDebInfo"))
    prepare.add_argument("--dry-run", action="store_true")

    package = subparsers.add_parser("package", help="Alias for build")
    _add_common_vendor_args(package, include_engine=True)
    package.add_argument("--package-dir", help="Override the BuildPlugin package directory")
    package.add_argument("--target-platforms", help="Unreal BuildPlugin target platforms, for example Mac or Win64")
    package.add_argument("--clean-package", action="store_true", help="Delete the package directory before BuildPlugin")
    package.add_argument("--skip-platform-probe", action="store_true", help="Skip the host compatibility preflight")
    package.add_argument("--dry-run", action="store_true")

    install_smoke = subparsers.add_parser("install-smoke", help="Install the packaged vendor plugin into a clean scratch project and verify the editor can open it")
    _add_common_vendor_args(install_smoke, include_engine=True)
    install_smoke.add_argument("--package-dir", help="Packaged plugin directory produced by BuildPlugin")
    install_smoke.add_argument("--project-dir", help="Scratch project directory for this install smoke")
    install_smoke.add_argument("--json-out", help="JSON report output path")
    install_smoke.add_argument("--md-out", help="Markdown report output path")
    install_smoke.add_argument("--clean-project", action="store_true")
    install_smoke.add_argument("--dry-run", action="store_true")

    handoff = subparsers.add_parser("handoff", help="Package a vendor Unreal plugin and emit an upstream-facing handoff packet")
    _add_common_vendor_args(handoff, include_engine=True)
    handoff.add_argument("--baseline-version", default="5.7", help="Known-good comparison lane used in the issue framing")
    handoff.add_argument("--package-dir", help="Override the BuildPlugin package directory")
    handoff.add_argument("--project-dir", help="Scratch project directory for install smoke")
    handoff.add_argument("--target-platforms", help="Unreal BuildPlugin target platforms, for example Mac or Win64")
    handoff.add_argument("--clean-package", action="store_true", help="Delete the package directory before BuildPlugin")
    handoff.add_argument("--skip-platform-probe", action="store_true", help="Skip the host compatibility preflight")
    handoff.add_argument("--clean-project", action="store_true")
    handoff.add_argument("--build-json-out", help="Build JSON report output path")
    handoff.add_argument("--build-md-out", help="Build Markdown report output path")
    handoff.add_argument("--install-json-out", help="Install smoke JSON report output path")
    handoff.add_argument("--install-md-out", help="Install smoke Markdown report output path")
    handoff.add_argument("--json-out", help="Handoff JSON output path")
    handoff.add_argument("--md-out", help="Handoff Markdown output path")
    handoff.add_argument("--dry-run", action="store_true")

    matrix = subparsers.add_parser("matrix", help="Package one vendor plugin across multiple Unreal versions")
    _add_common_vendor_args(matrix, include_engine=False)
    matrix.add_argument("--versions", nargs="+", default=DEFAULT_SUPPORTED_VERSIONS)
    matrix.add_argument("--package-root", help="Override the base output directory for versioned packages")
    matrix.add_argument("--target-platforms", help="Unreal BuildPlugin target platforms, for example Mac or Win64")
    matrix.add_argument("--clean-package", action="store_true", help="Delete each versioned package directory before BuildPlugin")
    matrix.add_argument("--skip-platform-probe", action="store_true", help="Skip the host compatibility preflight")
    matrix.add_argument("--dry-run", action="store_true")
    matrix.add_argument("--json-out")
    matrix.add_argument("--md-out")

    full = subparsers.add_parser("full", help="Doctor the vendor plugin, then run the supported-version packaging matrix")
    _add_common_vendor_args(full, include_engine=False)
    full.add_argument("--versions", nargs="+", default=DEFAULT_SUPPORTED_VERSIONS)
    full.add_argument("--package-root", help="Override the base output directory for versioned packages")
    full.add_argument("--target-platforms", help="Unreal BuildPlugin target platforms, for example Mac or Win64")
    full.add_argument("--clean-package", action="store_true", help="Delete each versioned package directory before BuildPlugin")
    full.add_argument("--skip-platform-probe", action="store_true", help="Skip the host compatibility preflight")
    full.add_argument("--dry-run", action="store_true")
    full.add_argument("--json-out")
    full.add_argument("--md-out")

    return parser.parse_args(argv)


def command_discover(args: argparse.Namespace) -> int:
    installs = [install.to_dict() for install in unreal_env.discover_installs()]
    if args.format == "json":
        print(json.dumps(installs, indent=2))
        return 0 if installs else 1
    if not installs:
        print("No Unreal installs discovered.")
        print(f"Hint: try {_unreal_root_hint()}")
        return 1
    for install in installs:
        version = install["version"] or "unknown"
        quirks = ", ".join(install["quirks"]) if install["quirks"] else "none"
        print(f"{version}: {install['install_root']}")
        print(f"  editor: {install['editor_path'] or 'missing'}")
        print(f"  uat:    {install['uat_path'] or 'missing'}")
        print(f"  ubt:    {install['ubt_path'] or 'missing'}")
        print(f"  dotnet: {install['dotnet_path'] or 'missing'}")
        print(f"  source: {install['source']}")
        print(f"  version_kind: {unreal_env.version_kind(install['version'])}")
        print(f"  quirks: {quirks}")
    return 0


def command_doctor(args: argparse.Namespace) -> int:
    payload = doctor_payload(args.vendor, args.engine_version, args.plugin_root, args.uplugin)
    if args.format == "json":
        print(json.dumps(payload, indent=2))
    else:
        print_doctor(payload)
    return 0 if payload["status"] == "ok" else 2


def command_build(args: argparse.Namespace) -> int:
    package_plugin(
        vendor=args.vendor,
        version=args.engine_version,
        plugin_root_arg=args.plugin_root,
        uplugin_arg=args.uplugin,
        package_dir_arg=args.package_dir,
        target_platforms_arg=args.target_platforms,
        clean_package=args.clean_package,
        skip_platform_probe=args.skip_platform_probe,
        dry_run=args.dry_run,
    )
    return 0


def command_prepare_source(args: argparse.Namespace) -> int:
    payload = prepare_source_checkout(
        vendor=args.vendor,
        version=args.engine_version,
        plugin_root_arg=args.plugin_root,
        clean_build=args.clean_build,
        build_type=args.build_type,
        dry_run=args.dry_run,
    )
    print(json.dumps(payload, indent=2))
    return 0 if payload["status"] in {"ok", "dry-run"} else 2


def build_report_payload(
    *,
    vendor: str,
    version: str | None,
    plugin_root_arg: str | None,
    uplugin_arg: str | None,
    package_dir_arg: str | None,
    target_platforms_arg: str | None,
    clean_package: bool,
    skip_platform_probe: bool,
    dry_run: bool,
) -> dict[str, object]:
    json_out, md_out = _default_build_report_paths(vendor, version)
    progress_json, progress_md = _default_progress_report_paths(vendor, version)
    install = install_for_version(version)
    resolved_toolchain = resolve_msvc_toolchain(install)
    progress = progress_payload(
        vendor=vendor,
        version=install.version if install is not None else version,
        resolved_toolchain=resolved_toolchain,
        json_out=progress_json,
        md_out=progress_md,
    )
    update_progress_report(progress, json_out=progress_json, md_out=progress_md, current_log="starting build report flow")
    append_progress_event(
        Path(str(progress["events_jsonl"])).resolve(),
        vendor=vendor,
        version=install.version if install is not None else version,
        event="lane_started",
        phase="starting",
        detail="unreal vendor build report flow started",
    )
    try:
        row = package_plugin(
            vendor=vendor,
            version=version,
            plugin_root_arg=plugin_root_arg,
            uplugin_arg=uplugin_arg,
            package_dir_arg=package_dir_arg,
            target_platforms_arg=target_platforms_arg,
            clean_package=clean_package,
            skip_platform_probe=skip_platform_probe,
            dry_run=dry_run,
            progress=progress,
        )
        update_progress_report(
            progress,
            json_out=progress_json,
            md_out=progress_md,
            status="pass",
            phase="build_complete",
            current_log="build phase completed successfully",
            last_completed_step="build_complete",
        )
        append_progress_event(
            Path(str(progress["events_jsonl"])).resolve(),
            vendor=vendor,
            version=install.version if install is not None else version,
            event="lane_phase_completed",
            phase="build_complete",
            detail="build report payload completed",
        )
        return {
            "schema": "packet_stoat.unreal_vendor_plugin_build.v1",
            "mode": "build",
            **row,
            "resolved_msvc_toolchain": resolved_toolchain,
            "report_json": str(json_out),
            "report_markdown": str(md_out),
            "progress_json": str(progress_json),
            "progress_markdown": str(progress_md),
            "progress_events_jsonl": str(progress["events_jsonl"]),
            "detail": "",
            "raw_output": "",
        }
    except subprocess.CalledProcessError as exc:
        update_progress_report(
            progress,
            json_out=progress_json,
            md_out=progress_md,
            status="fail",
            current_log="build phase failed",
            last_log_line=str(getattr(exc, "output", "") or str(exc)),
        )
        append_progress_event(
            Path(str(progress["events_jsonl"])).resolve(),
            vendor=vendor,
            version=install.version if install is not None else version,
            event="lane_failed",
            phase=str(progress.get("phase") or "buildplugin"),
            detail=str(exc),
        )
        plugin_root = resolve_plugin_root(vendor, plugin_root_arg)
        descriptor = resolve_uplugin_path(vendor, plugin_root, uplugin_arg)
        package_dir = (
            Path(package_dir_arg).expanduser().resolve()
            if package_dir_arg
            else (default_package_dir(vendor, descriptor, install.version or version) if install is not None and descriptor is not None else None)
        )
        return {
            "schema": "packet_stoat.unreal_vendor_plugin_build.v1",
            "mode": "build",
            "vendor": vendor_slug(vendor),
            "engine_version": install.version if install is not None else version,
            "plugin_root": str(plugin_root) if plugin_root is not None else None,
            "uplugin": str(descriptor) if descriptor is not None else None,
            "package_dir": str(package_dir) if package_dir is not None else None,
            "target_platforms": _target_platforms(target_platforms_arg),
            "build_command": [str(part) for part in exc.cmd],
            "status": "fail",
            "report_json": str(json_out),
            "report_markdown": str(md_out),
            "progress_json": str(progress_json),
            "progress_markdown": str(progress_md),
            "progress_events_jsonl": str(progress["events_jsonl"]),
            "detail": str(exc),
            "raw_output": str(getattr(exc, "output", "") or ""),
            "resolved_msvc_toolchain": resolved_toolchain,
            "process_provenance": process_provenance(version),
        }
    except SystemExit as exc:
        update_progress_report(
            progress,
            json_out=progress_json,
            md_out=progress_md,
            status="fail",
            current_log="build phase aborted",
            last_log_line=str(exc),
        )
        append_progress_event(
            Path(str(progress["events_jsonl"])).resolve(),
            vendor=vendor,
            version=install.version if install is not None else version,
            event="lane_aborted",
            phase=str(progress.get("phase") or "starting"),
            detail=str(exc),
        )
        plugin_root = resolve_plugin_root(vendor, plugin_root_arg)
        descriptor = resolve_uplugin_path(vendor, plugin_root, uplugin_arg) if plugin_root is not None else None
        package_dir = (
            Path(package_dir_arg).expanduser().resolve()
            if package_dir_arg
            else (default_package_dir(vendor, descriptor, install.version or version) if install is not None and descriptor is not None else None)
        )
        return {
            "schema": "packet_stoat.unreal_vendor_plugin_build.v1",
            "mode": "build",
            "vendor": vendor_slug(vendor),
            "engine_version": install.version if install is not None else version,
            "plugin_root": str(plugin_root) if plugin_root is not None else None,
            "uplugin": str(descriptor) if descriptor is not None else None,
            "package_dir": str(package_dir) if package_dir is not None else None,
            "target_platforms": _target_platforms(target_platforms_arg),
            "build_command": [],
            "status": "fail",
            "report_json": str(json_out),
            "report_markdown": str(md_out),
            "progress_json": str(progress_json),
            "progress_markdown": str(progress_md),
            "progress_events_jsonl": str(progress["events_jsonl"]),
            "detail": str(exc),
            "raw_output": "",
            "resolved_msvc_toolchain": resolved_toolchain,
            "process_provenance": process_provenance(version),
        }


def _default_install_project_dir(vendor: str, version: str | None, plugin_name: str) -> Path:
    version_slug = (version or preferred_unreal_version()).replace(".", "_")
    return unreal_env.work_root() / "vendor_install_smoke" / vendor_slug(vendor) / version_slug / plugin_name


def _install_smoke_paths(
    vendor: str,
    version: str | None,
    plugin_root_arg: str | None,
    uplugin_arg: str | None,
    package_dir_arg: str | None,
    project_dir_arg: str | None,
    json_out_arg: str | None,
    md_out_arg: str | None,
) -> tuple[Path, Path, Path, Path]:
    plugin_root = resolve_plugin_root(vendor, plugin_root_arg)
    descriptor = resolve_uplugin_path(vendor, plugin_root, uplugin_arg)
    if descriptor is None:
        raise SystemExit("Could not resolve a .uplugin for install smoke.")
    package_dir = (
        Path(package_dir_arg).expanduser().resolve()
        if package_dir_arg
        else default_package_dir(vendor, descriptor, version)
    )
    project_dir = (
        Path(project_dir_arg).expanduser().resolve()
        if project_dir_arg
        else _default_install_project_dir(vendor, version, descriptor.stem)
    )
    json_out = (
        Path(json_out_arg).expanduser().resolve()
        if json_out_arg
        else _default_install_smoke_report_paths(vendor, version)[0]
    )
    md_out = (
        Path(md_out_arg).expanduser().resolve()
        if md_out_arg
        else _default_install_smoke_report_paths(vendor, version)[1]
    )
    return descriptor, package_dir, project_dir, json_out, md_out


def install_smoke_report_payload(
    *,
    vendor: str,
    version: str | None,
    plugin_root_arg: str | None,
    uplugin_arg: str | None,
    package_dir_arg: str | None,
    project_dir_arg: str | None,
    json_out_arg: str | None,
    md_out_arg: str | None,
    clean_project: bool,
    dry_run: bool,
) -> dict[str, object]:
    descriptor, package_dir, project_dir, json_out, md_out = _install_smoke_paths(
        vendor,
        version,
        plugin_root_arg,
        uplugin_arg,
        package_dir_arg,
        project_dir_arg,
        json_out_arg,
        md_out_arg,
    )
    cmd = unreal_env.python_command() + [
        "tools/run_unreal_vendor_install_smoke.py",
        "--vendor",
        vendor_slug(vendor),
        "--engine-version",
        version or preferred_unreal_version(),
        "--package-dir",
        str(package_dir),
        "--project-dir",
        str(project_dir),
        "--json-out",
        str(json_out),
        "--markdown-out",
        str(md_out),
    ]
    if clean_project:
        cmd.append("--clean-project")
    if dry_run:
        cmd.append("--dry-run")
    if dry_run:
        return {
            "schema": "packet_stoat.unreal_vendor_install_smoke.v1",
            "vendor": vendor_slug(vendor),
            "engine_version": version,
            "plugin_name": descriptor.stem,
            "package_dir": str(package_dir),
            "project_dir": str(project_dir),
            "json_out": str(json_out),
            "md_out": str(md_out),
            "command": cmd,
            "status": "dry-run",
        }
    rc = run_step(cmd)
    if json_out.is_file():
        payload = json.loads(json_out.read_text(encoding="utf-8"))
        payload["json_out"] = str(json_out)
        payload["md_out"] = str(md_out)
        payload["command"] = cmd
        payload["returncode"] = rc
        return payload
    return {
        "schema": "packet_stoat.unreal_vendor_install_smoke.v1",
        "vendor": vendor_slug(vendor),
        "engine_version": version,
        "plugin_name": descriptor.stem,
        "package_dir": str(package_dir),
        "project_dir": str(project_dir),
        "json_out": str(json_out),
        "md_out": str(md_out),
        "command": cmd,
        "returncode": rc,
        "status": "missing-report",
    }


def command_install_smoke(args: argparse.Namespace) -> int:
    payload = install_smoke_report_payload(
        vendor=args.vendor,
        version=args.engine_version,
        plugin_root_arg=args.plugin_root,
        uplugin_arg=args.uplugin,
        package_dir_arg=args.package_dir,
        project_dir_arg=args.project_dir,
        json_out_arg=args.json_out,
        md_out_arg=args.md_out,
        clean_project=args.clean_project,
        dry_run=args.dry_run,
    )
    return 0 if payload["status"] in {"pass", "dry-run"} else int(payload.get("returncode") or 1)


def _matrix_package_dir(package_root: Path | None, vendor: str, version: str, descriptor_name: str) -> Path:
    base = package_root if package_root is not None else (ROOT / "build" / "unreal_vendor_plugins" / vendor_slug(vendor))
    return base / version.replace(".", "_") / descriptor_name


def _report_paths(vendor: str, json_out: str | None, md_out: str | None) -> tuple[Path, Path]:
    base = DEFAULT_REPORT_DIR / vendor_slug(vendor)
    return (
        Path(json_out).expanduser().resolve() if json_out else base.with_name(f"{vendor_slug(vendor)}_matrix.json"),
        Path(md_out).expanduser().resolve() if md_out else base.with_name(f"{vendor_slug(vendor)}_matrix.md"),
    )


def _write_matrix_report(report: dict[str, object], json_out: Path, md_out: Path) -> None:
    json_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Unreal Vendor Plugin Matrix",
        "",
        f"- vendor: `{report['vendor']}`",
        f"- overall_status: `{report['overall_status']}`",
        "",
        "| version | status | prepare | compiler | folder | install | package_dir | detail |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in report["results"]:
        lines.append(
            f"| {row['version']} | {row['status']} | {row.get('prepare_source_status') or ''} | {row.get('selected_compiler_version') or ''} | {row.get('selected_folder_version') or ''} | {row.get('install_smoke_status') or ''} | {row.get('package_dir') or ''} | {row.get('detail') or ''} |"
        )
    md_out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def command_matrix(args: argparse.Namespace) -> int:
    resolved_plugin_root = resolve_plugin_root(args.vendor, args.plugin_root)
    resolved_uplugin = resolve_uplugin_path(args.vendor, resolved_plugin_root, args.uplugin)
    descriptor_name = resolved_uplugin.stem if resolved_uplugin is not None else vendor_slug(args.vendor)
    package_root = Path(args.package_root).expanduser().resolve() if args.package_root else None
    json_out, md_out = _report_paths(args.vendor, args.json_out, args.md_out)
    results: list[dict[str, object]] = []
    source_checkout = plugin_uses_source_checkout(resolved_plugin_root)

    for version in args.versions:
        package_dir = _matrix_package_dir(package_root, args.vendor, version, descriptor_name)
        try:
            prepare_report: dict[str, object] | None = None
            if source_checkout:
                prepare_report = prepare_source_checkout(
                    vendor=args.vendor,
                    version=version,
                    plugin_root_arg=args.plugin_root,
                    clean_build=True,
                    build_type="Release",
                    dry_run=args.dry_run,
                )
            row = build_report_payload(
                vendor=args.vendor,
                version=version,
                plugin_root_arg=args.plugin_root,
                uplugin_arg=args.uplugin,
                package_dir_arg=str(package_dir),
                target_platforms_arg=args.target_platforms,
                clean_package=args.clean_package,
                skip_platform_probe=args.skip_platform_probe,
                dry_run=args.dry_run,
            )
            build_json, build_md = _default_build_report_paths(args.vendor, version)
            row["report_json"] = str(build_json)
            row["report_markdown"] = str(build_md)
            write_build_report(row, build_json, build_md)
            results.append(
                {
                    "version": version,
                    "status": row["status"],
                    "package_dir": row["package_dir"],
                    "detail": "",
                    "build_report_json": str(build_json),
                    "build_report_markdown": str(build_md),
                }
            )
            if prepare_report is not None:
                resolved_toolchain = prepare_report.get("resolved_msvc_toolchain")
                if isinstance(resolved_toolchain, dict):
                    results[-1]["selected_compiler_version"] = str(resolved_toolchain.get("selected_version") or "")
                    results[-1]["selected_folder_version"] = str(resolved_toolchain.get("selected_folder_version") or "")
                    results[-1]["selection_reason"] = str(resolved_toolchain.get("selection_reason") or "")
                results[-1]["prepare_source_status"] = str(prepare_report.get("status") or "")
            install_cmd = argparse.Namespace(
                vendor=args.vendor,
                engine_version=version,
                plugin_root=args.plugin_root,
                uplugin=args.uplugin,
                package_dir=str(package_dir),
                project_dir=None,
                json_out=None,
                md_out=None,
                clean_project=True,
                dry_run=args.dry_run,
            )
            install_code = command_install_smoke(install_cmd)
            results[-1]["install_smoke_status"] = "ok" if install_code == 0 else "fail"
            if install_code != 0:
                results[-1]["status"] = "fail"
                results[-1]["detail"] = "install smoke failed"
        except (SystemExit, subprocess.CalledProcessError) as exc:
            results.append(
                {
                    "version": version,
                    "status": "fail",
                    "package_dir": str(package_dir),
                    "detail": str(exc),
                }
            )

    overall_status = "ok" if all(row["status"] in {"ok", "dry-run"} for row in results) else "fail"
    report = {
        "schema": "packet_stoat.unreal_vendor_plugin_matrix.v1",
        "vendor": vendor_slug(args.vendor),
        "overall_status": overall_status,
        "results": results,
    }
    _write_matrix_report(report, json_out, md_out)
    return 0 if overall_status == "ok" else 2


def handoff_payload(args: argparse.Namespace) -> dict[str, object]:
    build_report = build_report_payload(
        vendor=args.vendor,
        version=args.engine_version,
        plugin_root_arg=args.plugin_root,
        uplugin_arg=args.uplugin,
        package_dir_arg=args.package_dir,
        target_platforms_arg=args.target_platforms,
        clean_package=args.clean_package,
        skip_platform_probe=args.skip_platform_probe,
        dry_run=args.dry_run,
    )
    build_json, build_md = _default_build_report_paths(args.vendor, args.engine_version)
    if args.build_json_out:
        build_json = Path(args.build_json_out).expanduser().resolve()
    if args.build_md_out:
        build_md = Path(args.build_md_out).expanduser().resolve()
    build_report["report_json"] = str(build_json)
    build_report["report_markdown"] = str(build_md)
    write_build_report(build_report, build_json, build_md)
    progress_json = Path(str(build_report.get("progress_json") or _default_progress_report_paths(args.vendor, args.engine_version)[0])).resolve()
    progress_md = Path(str(build_report.get("progress_markdown") or _default_progress_report_paths(args.vendor, args.engine_version)[1])).resolve()
    progress_events = Path(str(build_report.get("progress_events_jsonl") or _default_progress_events_path(args.vendor, args.engine_version))).resolve()
    progress = progress_payload(
        vendor=args.vendor,
        version=str(build_report.get("engine_version") or args.engine_version or ""),
        resolved_toolchain=build_report.get("resolved_msvc_toolchain") if isinstance(build_report.get("resolved_msvc_toolchain"), dict) else None,
        json_out=progress_json,
        md_out=progress_md,
    )
    if progress_json.is_file():
        progress = json.loads(progress_json.read_text(encoding="utf-8"))
    progress["report_json"] = str(progress_json)
    progress["report_markdown"] = str(progress_md)
    progress["events_jsonl"] = str(progress_events)

    install_report: dict[str, object] | None = None
    if build_report["status"] in {"ok", "dry-run"}:
        update_progress_report(
            progress,
            json_out=progress_json,
            md_out=progress_md,
            phase="install_smoke",
            current_log="starting install smoke",
            last_completed_step=str(progress.get("last_completed_step") or "build_complete"),
        )
        append_progress_event(
            progress_events,
            vendor=args.vendor,
            version=str(build_report.get("engine_version") or args.engine_version or ""),
            event="install_smoke_started",
            phase="install_smoke",
            detail="launching install smoke verification",
        )
        install_report = install_smoke_report_payload(
            vendor=args.vendor,
            version=args.engine_version,
            plugin_root_arg=args.plugin_root,
            uplugin_arg=args.uplugin,
            package_dir_arg=build_report.get("package_dir"),
            project_dir_arg=args.project_dir,
            json_out_arg=args.install_json_out,
            md_out_arg=args.install_md_out,
            clean_project=args.clean_project,
            dry_run=args.dry_run,
        )
        install_status = str(install_report.get("status") or "")
        if install_status in {"pass", "dry-run"}:
            update_progress_report(
                progress,
                json_out=progress_json,
                md_out=progress_md,
                phase="complete",
                status="pass",
                current_log="install smoke completed successfully",
                last_completed_step="install_smoke",
            )
            append_progress_event(
                progress_events,
                vendor=args.vendor,
                version=str(build_report.get("engine_version") or args.engine_version or ""),
                event="install_smoke_completed",
                phase="complete",
                detail=install_status,
            )
        else:
            update_progress_report(
                progress,
                json_out=progress_json,
                md_out=progress_md,
                phase="install_smoke",
                status="fail",
                current_log="install smoke failed",
                last_completed_step=str(progress.get("last_completed_step") or "build_complete"),
            )
            append_progress_event(
                progress_events,
                vendor=args.vendor,
                version=str(build_report.get("engine_version") or args.engine_version or ""),
                event="install_smoke_failed",
                phase="install_smoke",
                detail=install_status,
            )

    failure_class = classify_build_failure(build_report, install_report)
    handoff_json, handoff_md = _default_handoff_paths(args.vendor, args.engine_version)
    if args.json_out:
        handoff_json = Path(args.json_out).expanduser().resolve()
    if args.md_out:
        handoff_md = Path(args.md_out).expanduser().resolve()
    if failure_class == "verified-build":
        title = f"{vendor_slug(args.vendor)} Unreal {args.engine_version} verification"
    elif str(args.engine_version) == str(args.baseline_version):
        title = f"{vendor_slug(args.vendor)} Unreal {args.engine_version} build failure"
    else:
        title = f"{vendor_slug(args.vendor)} Unreal {args.engine_version} regression against {args.baseline_version}"
    repro_command = " ".join(str(part) for part in build_report.get("build_command", [])) or "unavailable"
    body_lines = [
        "## Summary",
        f"- classification: `{failure_class}`",
        f"- vendor: `{build_report['vendor']}`",
        f"- engine_version: `{build_report.get('engine_version') or 'unknown'}`",
        f"- baseline_version: `{args.baseline_version}`",
        f"- status: `{build_report.get('status')}`",
        "",
        "## Repro",
        f"```bash\n{repro_command}\n```",
        "",
        "## Evidence",
        f"- build_report_json: `{build_report['report_json']}`",
        f"- build_report_markdown: `{build_report['report_markdown']}`",
    ]
    if install_report is not None:
        body_lines.append(f"- install_smoke_json: `{install_report.get('json_out')}`")
        body_lines.append(f"- install_smoke_markdown: `{install_report.get('md_out')}`")
    detail = str(build_report.get("raw_output") or build_report.get("detail") or "").strip()
    if detail:
        body_lines.extend(["", "## Failure Detail", "```text", detail, "```"])
    if install_report is not None and install_report.get("status") not in {"pass", "dry-run"}:
        install_detail = json.dumps(install_report.get("log_summary") or install_report.get("details") or install_report, indent=2)
        body_lines.extend(["", "## Install Smoke Detail", "```json", install_detail, "```"])
    body_lines.extend(
        [
            "",
            "## Notes",
            "- This packet was generated from the Packet Stoat Cesium Unreal vendor lane.",
            "- Unreal 5.7 is treated as the expected comparison lane; Unreal 5.8 is the bleeding-edge compatibility target that may legitimately fail while upstream catches up.",
            "- Report any cache normalization, path escaping workaround, or toolchain override alongside the final result.",
        ]
    )
    return {
        "schema": "packet_stoat.cesium_unreal_upstream_handoff.v1",
        "mode": "handoff",
        "vendor": build_report["vendor"],
        "engine_version": build_report.get("engine_version"),
        "baseline_version": args.baseline_version,
        "status": "ready" if failure_class in {"verified-build", "compile-or-link", "build-failed", "engine-permission", "host-platform-unavailable", "install-smoke-failed"} else "needs-attention",
        "failure_class": failure_class,
        "source_repo": "https://github.com/CesiumGS/cesium-unreal",
        "title": title,
        "repro_command": repro_command,
        "build_report_json": build_report["report_json"],
        "build_report_markdown": build_report["report_markdown"],
        "progress_json": str(progress_json),
        "progress_markdown": str(progress_md),
        "progress_events_jsonl": str(progress_events),
        "install_smoke_json": install_report.get("json_out") if install_report is not None else None,
        "install_smoke_markdown": install_report.get("md_out") if install_report is not None else None,
        "handoff_json": str(handoff_json),
        "handoff_markdown": str(handoff_md),
        "issue_body_markdown": "\n".join(body_lines) + "\n",
        "build_report": build_report,
        "install_smoke_report": install_report,
    }


def command_handoff(args: argparse.Namespace) -> int:
    payload = handoff_payload(args)
    build_report = payload.get("build_report")
    if isinstance(build_report, dict):
        write_build_report(
            build_report,
            Path(str(build_report["report_json"])).resolve(),
            Path(str(build_report["report_markdown"])).resolve(),
        )
    json_out = Path(payload["handoff_json"]).resolve()
    md_out = Path(payload["handoff_markdown"]).resolve()
    write_handoff(payload, json_out, md_out)
    print(json.dumps(payload, indent=2))
    return 0 if payload["status"] == "ready" else 2


def command_full(args: argparse.Namespace) -> int:
    doctor_code = command_doctor(
        argparse.Namespace(
            vendor=args.vendor,
            engine_version=None,
            plugin_root=args.plugin_root,
            uplugin=args.uplugin,
            format="text",
        )
    )
    if doctor_code != 0:
        return doctor_code
    return command_matrix(args)


def main(argv: list[str] | None = None) -> int:
    load_local_env.load()
    args = parse_args(argv)
    if args.command == "discover":
        return command_discover(args)
    if args.command == "doctor":
        return command_doctor(args)
    if args.command in {"build", "package"}:
        return command_build(args)
    if args.command == "prepare-source":
        return command_prepare_source(args)
    if args.command == "install-smoke":
        return command_install_smoke(args)
    if args.command == "handoff":
        return command_handoff(args)
    if args.command == "matrix":
        return command_matrix(args)
    if args.command == "full":
        return command_full(args)
    raise SystemExit(f"Unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
