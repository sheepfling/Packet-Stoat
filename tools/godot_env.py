#!/usr/bin/env python3
"""Resolve Godot and SCons tools plus host-specific artifact names."""

from __future__ import annotations

import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PRERELEASE_RANK = {
    "stable": 4,
    "rc": 3,
    "beta": 2,
    "alpha": 1,
    "dev": 0,
}


def _godot_version_kind(version_info: dict[str, Any] | None) -> str:
    if not version_info:
        return "unknown"
    channel = str(version_info.get("channel") or "")
    if channel == "stable":
        return "stable"
    if channel in {"rc", "beta", "alpha", "dev"}:
        return f"prerelease:{channel}"
    return f"unknown:{channel or 'missing'}"


def _default_work_root() -> Path:
    system = platform.system().lower()
    candidates: list[Path] = []
    if system == "windows":
        candidates.append(Path("C:/tmp/fastdis_godot"))
        candidates.append(Path("C:/fastdis_godot"))
        candidates.append(Path(tempfile.gettempdir()) / "fastdis_godot")
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            candidates.append(Path(local_app_data) / "fastdis_godot")
    else:
        candidates.append(Path("/tmp/fastdis_godot"))
        candidates.append(Path(tempfile.gettempdir()) / "fastdis_godot")

    for candidate in candidates:
        if " " not in str(candidate):
            return candidate
    return candidates[0]


def _dedupe_candidates(candidates: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for candidate in candidates:
        if candidate and candidate not in seen:
            seen.add(candidate)
            ordered.append(candidate)
    return ordered


def _split_configured_paths(value: str | None) -> list[Path]:
    if not value:
        return []
    paths: list[Path] = []
    for raw_part in value.split(os.pathsep):
        part = raw_part.strip().strip('"')
        if not part:
            continue
        paths.append(Path(os.path.expandvars(part)).expanduser())
    return paths


def _parse_godot_version_label(value: str | None) -> dict[str, Any] | None:
    if not value:
        return None
    normalized = value.replace(".exe", "")
    match = re.search(
        r"Godot_v(?P<base>\d+\.\d+(?:\.\d+)?)(?:[-._]?(?P<tag>stable|rc|beta|alpha|dev)(?P<num>\d+)?)?",
        normalized,
        re.IGNORECASE,
    )
    if not match:
        return None
    base = match.group("base")
    tag = (match.group("tag") or "stable").lower()
    number = match.group("num") or ""
    suffix = "" if tag == "stable" else f"-{tag}{number}"
    return {
        "version": f"{base}{suffix}",
        "version_family": ".".join(base.split(".")[:2]),
        "base_version": base,
        "channel": tag,
        "channel_number": int(number) if number else 0,
    }


def _godot_sort_key(version_info: dict[str, Any]) -> tuple[int, int, int, int, int]:
    parts = [int(part) for part in str(version_info["base_version"]).split(".")]
    while len(parts) < 3:
        parts.append(0)
    return (
        parts[0],
        parts[1],
        parts[2],
        PRERELEASE_RANK.get(str(version_info["channel"]), -1),
        int(version_info["channel_number"]),
    )


def _godot_resolution_key(version_info: dict[str, Any]) -> tuple[int, int, int, int, int]:
    parts = [int(part) for part in str(version_info["base_version"]).split(".")]
    while len(parts) < 3:
        parts.append(0)
    stable_bias = 1 if str(version_info["channel"]) == "stable" else 0
    return (
        parts[0],
        parts[1],
        stable_bias,
        parts[2],
        int(version_info["channel_number"]),
    )


def _append_godot_candidate(
    installs: list[dict[str, Any]],
    seen_paths: set[str],
    candidate: str,
    *,
    source: str,
) -> None:
    resolved = _resolve_candidate(candidate)
    if not resolved or resolved in seen_paths:
        return
    path = Path(resolved)
    version_info = _parse_godot_version_label(str(path))
    entry: dict[str, Any] = {
        "path": resolved,
        "source": source,
        "binary_kind": "console" if "_console" in path.name.lower() else "gui",
        "version": None,
        "version_family": None,
        "base_version": None,
        "channel": None,
        "channel_number": None,
    }
    if version_info:
        entry.update(version_info)
        entry["version_kind"] = _godot_version_kind(version_info)
    else:
        entry["version_kind"] = "unknown"
    seen_paths.add(resolved)
    installs.append(entry)


def discover_godot_installs(explicit: str | None = None) -> list[dict[str, Any]]:
    installs: list[dict[str, Any]] = []
    seen_paths: set[str] = set()
    if explicit:
        _append_godot_candidate(installs, seen_paths, explicit, source="explicit")
    env_candidate = os.environ.get("FASTDIS_GODOT")
    if env_candidate:
        _append_godot_candidate(installs, seen_paths, env_candidate, source="env")
    for candidate in configured_godot_candidates():
        _append_godot_candidate(installs, seen_paths, candidate, source="config")
    for candidate in default_godot_candidates():
        _append_godot_candidate(installs, seen_paths, candidate, source="scan")
    for candidate in path_godot_candidates():
        _append_godot_candidate(installs, seen_paths, candidate, source="path")
    installs.sort(
        key=lambda entry: (
            _godot_resolution_key(entry) if entry.get("base_version") else (-1, -1, -1, -1, -1),
            1 if entry.get("binary_kind") == "console" else 0,
        ),
        reverse=True,
    )
    return installs


DEFAULT_WORK_ROOT = _default_work_root()


def work_root() -> Path:
    override = os.environ.get("FASTDIS_GODOT_WORK_ROOT")
    if override:
        return Path(override).expanduser()
    return DEFAULT_WORK_ROOT


def path_writable(path: Path) -> tuple[bool, str]:
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ".fastdis_write_probe"
        probe.write_text("ok\n", encoding="utf-8")
        probe.unlink()
        return True, str(path)
    except OSError as exc:
        return False, f"{path}: {exc}"


def host_platform_name() -> str:
    system = platform.system().lower()
    if system == "darwin":
        return "macos"
    if system == "windows":
        return "windows"
    return "linux"


def host_arch_name() -> str:
    machine = platform.machine().lower()
    if machine in {"arm64", "aarch64"}:
        return "arm64"
    return "x86_64"


def default_godot_candidates() -> list[str]:
    return _scan_godot_roots(default_godot_scan_roots()) + platform_godot_direct_candidates()


def configured_godot_roots() -> list[Path]:
    return _split_configured_paths(os.environ.get("FASTDIS_GODOT_ROOTS"))


def configured_godot_candidates() -> list[str]:
    return _scan_godot_roots(configured_godot_roots())


def default_godot_scan_roots() -> list[Path]:
    system = platform.system().lower()
    if system == "darwin":
        return [
            Path("/Applications"),
            Path.home() / "Applications",
            Path.home() / "Dev" / "Godot",
            Path.home() / "bin",
            Path("/usr/local/bin"),
            Path("/opt/homebrew/bin"),
        ]
    if system == "windows":
        program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
        program_files_x86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
        local_app_data = os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))
        user_profile = Path(os.environ.get("USERPROFILE", str(Path.home())))
        return [
            Path(os.environ.get("PUBLIC", r"C:\Users\Public")) / "Godot" / "engines",
            Path(r"C:\Godot"),
            Path(program_files),
            Path(program_files) / "Godot",
            Path(program_files_x86) / "Godot",
            Path(local_app_data) / "Programs" / "Godot",
            user_profile / "Godot",
            user_profile / "Dev" / "Godot",
            user_profile / "scoop" / "apps" / "godot" / "current",
        ]
    return [
        Path.home() / "bin",
        Path.home() / ".local" / "bin",
        Path.home() / "Dev" / "Godot",
        Path("/usr/local/bin"),
        Path("/usr/bin"),
        Path("/opt/godot"),
        Path("/snap/bin"),
    ]


def platform_godot_direct_candidates() -> list[str]:
    system = platform.system().lower()
    if system == "darwin":
        return _dedupe_candidates(
            [
                "/Applications/Godot.app/Contents/MacOS/Godot",
                str(Path.home() / "Applications" / "Godot.app" / "Contents" / "MacOS" / "Godot"),
                "/Applications/Godot 4.app/Contents/MacOS/Godot",
                str(Path.home() / "Applications" / "Godot 4.app" / "Contents" / "MacOS" / "Godot"),
            ]
        )
    if system == "windows":
        return []
    return []


def path_godot_candidates() -> list[str]:
    system = platform.system().lower()
    if system == "windows":
        return [
            "godot.exe",
            "godot4.exe",
            "godot4.7.exe",
            "godot4.6.exe",
            "godot4.5.exe",
            "godot4.4.exe",
            "godot4.3.exe",
            "godot4.2.exe",
        ]
    return [
        "godot",
        "godot4",
        "godot4.7",
        "godot4.6",
        "godot4.5",
        "godot4.4",
        "godot4.3",
        "godot4.2",
    ]


def _scan_godot_roots(roots: list[Path]) -> list[str]:
    candidates: list[str] = []
    for root in roots:
        candidates.extend(_godot_candidates_from_root(root))
    return _dedupe_candidates(candidates)


def _godot_candidates_from_root(root: Path) -> list[str]:
    system = platform.system().lower()
    expanded = root.expanduser()
    if expanded.is_file():
        return [str(expanded)]
    if not expanded.exists() or not expanded.is_dir():
        return []
    if system == "windows":
        patterns = [
            "Godot.exe",
            "godot.exe",
            "Godot_v*.exe",
            "Godot_v*/Godot_v*_console.exe",
            "Godot_v*/Godot_v*.exe",
            "*/Godot.exe",
            "*/godot.exe",
        ]
    elif system == "darwin":
        patterns = [
            "Godot.app/Contents/MacOS/Godot",
            "Godot 4.app/Contents/MacOS/Godot",
            "*Godot*.app/Contents/MacOS/Godot",
            "godot",
            "godot4",
            "Godot_v*",
        ]
    else:
        patterns = [
            "godot",
            "godot4",
            "Godot_v*",
            "Godot_v*/Godot_v*",
        ]

    console: list[str] = []
    gui: list[str] = []
    for pattern in patterns:
        for candidate in sorted(expanded.glob(pattern), reverse=True):
            if not candidate.is_file():
                continue
            normalized = str(candidate)
            if "_console" in candidate.name.lower():
                console.append(normalized)
            else:
                gui.append(normalized)
    return _dedupe_candidates(console + gui)


def default_scons_candidates() -> list[str]:
    system = platform.system().lower()
    if system == "windows":
        executable_dir = Path(sys.executable).resolve().parent
        local_app_data = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local")))
        return [
            str(ROOT / ".venv" / "Scripts" / "scons.exe"),
            str(ROOT / ".venv" / "Scripts" / "scons.bat"),
            str(executable_dir / "scons.exe"),
            str(executable_dir / "scons.bat"),
            str(executable_dir / "Scripts" / "scons.exe"),
            str(executable_dir / "Scripts" / "scons.bat"),
            str(local_app_data / "Programs" / "Python" / "Python312" / "Scripts" / "scons.exe"),
            str(local_app_data / "Programs" / "Python" / "Python311" / "Scripts" / "scons.exe"),
            str(local_app_data / "Programs" / "Python" / "Python310" / "Scripts" / "scons.exe"),
            "scons.exe",
            "scons.bat",
            "scons",
        ]
    return [
        str(ROOT / ".venv" / "bin" / "scons"),
        "scons",
    ]


def _resolve_candidate(candidate: str) -> str | None:
    if not candidate:
        return None
    path = Path(candidate).expanduser()
    if path.is_file():
        return str(path.resolve())
    resolved = shutil.which(candidate)
    if resolved:
        return resolved
    return None


def resolve_godot(explicit: str | None = None) -> str | None:
    installs = discover_godot_installs(explicit)
    if not installs:
        return None
    return str(installs[0]["path"])


def resolve_scons() -> str | None:
    env_candidate = os.environ.get("FASTDIS_SCONS")
    if env_candidate:
        resolved = _resolve_candidate(env_candidate)
        if resolved:
            return resolved
    for candidate in default_scons_candidates():
        resolved = _resolve_candidate(candidate)
        if resolved:
            return resolved
    return None


def python_command() -> list[str]:
    if sys.executable:
        return [sys.executable]
    if platform.system().lower() == "windows":
        return ["python"]
    return ["python3"]


def wrapper_names(host_platform: str | None = None, host_arch: str | None = None) -> list[str]:
    platform_name = host_platform or host_platform_name()
    arch_name = host_arch or host_arch_name()
    if platform_name == "windows":
        return [
            f"fastdis_gdextension.windows.template_debug.{arch_name}.dll",
            f"fastdis_gdextension.windows.template_release.{arch_name}.dll",
        ]
    if platform_name == "macos":
        return [
            "libfastdis_gdextension.macos.template_debug.dylib",
            "libfastdis_gdextension.macos.template_release.dylib",
        ]
    return [
        f"libfastdis_gdextension.linux.template_debug.{arch_name}.so",
        f"libfastdis_gdextension.linux.template_release.{arch_name}.so",
    ]


def shared_library_names(host_platform: str | None = None) -> list[str]:
    platform_name = host_platform or host_platform_name()
    if platform_name == "windows":
        return ["fastdis.dll"]
    if platform_name == "macos":
        return ["libfastdis.dylib", "libfastdis.0.dylib", "libfastdis.0.12.0.dylib"]
    return ["libfastdis.so"]


def build_env() -> dict[str, str]:
    env = dict(os.environ)
    root = work_root()
    sandbox_home = root / "home"
    sandbox_home.mkdir(parents=True, exist_ok=True)
    sandbox_tmp = root / "tmp"
    sandbox_tmp.mkdir(parents=True, exist_ok=True)
    ezvcpkg_base = sandbox_home / ".ezvcpkg"
    ezvcpkg_base.mkdir(parents=True, exist_ok=True)
    env["HOME"] = str(sandbox_home)
    env["XDG_CONFIG_HOME"] = str(sandbox_home / ".config")
    env["XDG_DATA_HOME"] = str(sandbox_home / ".local" / "share")
    env["XDG_CACHE_HOME"] = str(sandbox_home / ".cache")
    env["TMPDIR"] = str(sandbox_tmp)
    env["EZVCPKG_BASEDIR"] = str(ezvcpkg_base)
    system = platform.system().lower()
    if system == "darwin":
        env["CFFIXED_USER_HOME"] = str(sandbox_home)
    if system == "windows":
        env["USERPROFILE"] = str(sandbox_home)
        env["APPDATA"] = str(sandbox_home / "AppData" / "Roaming")
        env["LOCALAPPDATA"] = str(sandbox_home / "AppData" / "Local")
        env["TEMP"] = str(sandbox_tmp)
        env["TMP"] = str(sandbox_tmp)
    return env


def repo_alias_root(root: Path) -> Path:
    resolved = root.resolve()
    if " " not in str(resolved):
        return resolved

    alias_root = work_root() / "repo"
    alias_root.parent.mkdir(parents=True, exist_ok=True)
    if alias_root.exists() or alias_root.is_symlink():
        return alias_root
    try:
        alias_root.symlink_to(resolved, target_is_directory=True)
        return alias_root
    except OSError:
        if platform.system().lower() == "windows":
            try:
                subprocess.run(
                    ["cmd", "/c", "mklink", "/J", str(alias_root), str(resolved)],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                if alias_root.exists():
                    return alias_root
            except (OSError, subprocess.SubprocessError):
                pass
        return resolved


def describe_host() -> dict[str, object]:
    alias_root = repo_alias_root(ROOT)
    current_work_root = work_root()
    godot_installs = discover_godot_installs()
    return {
        "platform": host_platform_name(),
        "arch": host_arch_name(),
        "godot": str(godot_installs[0]["path"]) if godot_installs else None,
        "godot_versions": list(dict.fromkeys(str(entry["version"]) for entry in godot_installs if entry.get("version"))),
        "godot_installs": godot_installs,
        "scons": resolve_scons(),
        "repo_root": str(ROOT),
        "repo_alias_root": str(alias_root),
        "uses_repo_alias": alias_root != ROOT.resolve(),
        "work_root": str(current_work_root),
        "work_root_has_spaces": " " in str(current_work_root),
        "work_root_reason": (
            "FASTDIS_GODOT_WORK_ROOT override"
            if os.environ.get("FASTDIS_GODOT_WORK_ROOT")
            else "default short native-build root"
        ),
        "wrapper_names": wrapper_names(),
        "shared_library_names": shared_library_names(),
    }
