#!/usr/bin/env python3
"""Resolve Godot and SCons tools plus host-specific artifact names."""

from __future__ import annotations

import os
from pathlib import Path
import platform
import shutil
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WORK_ROOT = Path(tempfile.gettempdir()).resolve() / "fastdis_godot"


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
    system = platform.system().lower()
    if system == "darwin":
        return [
            "godot",
            "godot4",
            "godot4.3",
            "godot4.2",
            "/Applications/Godot.app/Contents/MacOS/Godot",
            str(Path.home() / "Applications" / "Godot.app" / "Contents" / "MacOS" / "Godot"),
        ]
    if system == "windows":
        program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
        program_files_x86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
        local_app_data = os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))
        user_profile = Path(os.environ.get("USERPROFILE", str(Path.home())))
        return [
            "godot.exe",
            "godot4.exe",
            "godot4.3.exe",
            "godot4.2.exe",
            str(Path(program_files) / "Godot_v4.3-stable_win64.exe"),
            str(Path(program_files) / "Godot_v4.2-stable_win64.exe"),
            str(Path(program_files) / "Godot" / "Godot_v4.3-stable_win64.exe"),
            str(Path(program_files) / "Godot" / "Godot_v4.2-stable_win64.exe"),
            str(Path(program_files) / "Godot" / "Godot.exe"),
            str(Path(program_files_x86) / "Godot" / "Godot.exe"),
            str(Path(local_app_data) / "Programs" / "Godot" / "Godot.exe"),
            str(user_profile / "scoop" / "apps" / "godot" / "current" / "godot.exe"),
            str(user_profile / "scoop" / "shims" / "godot.exe"),
        ]
    return [
        "godot",
        "godot4",
        "godot4.3",
        "godot4.2",
        "/usr/bin/godot",
        "/usr/local/bin/godot",
        "/snap/bin/godot",
    ]


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
    if explicit:
        return _resolve_candidate(explicit)
    env_candidate = os.environ.get("FASTDIS_GODOT")
    if env_candidate:
        resolved = _resolve_candidate(env_candidate)
        if resolved:
            return resolved
    for candidate in default_godot_candidates():
        resolved = _resolve_candidate(candidate)
        if resolved:
            return resolved
    return None


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


def wrapper_names(host_platform: str | None = None) -> list[str]:
    platform_name = host_platform or host_platform_name()
    if platform_name == "windows":
        return [
            "fastdis_gdextension.windows.template_debug.x86_64.dll",
            "fastdis_gdextension.windows.template_release.x86_64.dll",
        ]
    if platform_name == "macos":
        return [
            "libfastdis_gdextension.macos.template_debug.dylib",
            "libfastdis_gdextension.macos.template_release.dylib",
        ]
    return [
        "libfastdis_gdextension.linux.template_debug.x86_64.so",
        "libfastdis_gdextension.linux.template_release.x86_64.so",
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
    sandbox_home = DEFAULT_WORK_ROOT / "home"
    sandbox_home.mkdir(parents=True, exist_ok=True)
    sandbox_tmp = DEFAULT_WORK_ROOT / "tmp"
    sandbox_tmp.mkdir(parents=True, exist_ok=True)
    env["HOME"] = str(sandbox_home)
    env["XDG_CONFIG_HOME"] = str(sandbox_home / ".config")
    env["XDG_DATA_HOME"] = str(sandbox_home / ".local" / "share")
    env["XDG_CACHE_HOME"] = str(sandbox_home / ".cache")
    env["TMPDIR"] = str(sandbox_tmp)
    system = platform.system().lower()
    if system == "darwin":
        env["CFFIXED_USER_HOME"] = str(sandbox_home)
    if system == "windows":
        env["USERPROFILE"] = str(sandbox_home)
        env["APPDATA"] = str(sandbox_home / "AppData" / "Roaming")
        env["LOCALAPPDATA"] = str(sandbox_home / "AppData" / "Local")
    return env


def repo_alias_root(root: Path) -> Path:
    resolved = root.resolve()
    if " " not in str(resolved):
        return resolved

    alias_root = DEFAULT_WORK_ROOT / "repo"
    alias_root.parent.mkdir(parents=True, exist_ok=True)
    if alias_root.exists() or alias_root.is_symlink():
        return alias_root
    try:
        alias_root.symlink_to(resolved, target_is_directory=True)
        return alias_root
    except OSError:
        return resolved


def describe_host() -> dict[str, object]:
    alias_root = repo_alias_root(ROOT)
    return {
        "platform": host_platform_name(),
        "arch": host_arch_name(),
        "godot": resolve_godot(),
        "scons": resolve_scons(),
        "repo_root": str(ROOT),
        "repo_alias_root": str(alias_root),
        "uses_repo_alias": alias_root != ROOT.resolve(),
        "work_root": str(DEFAULT_WORK_ROOT),
        "wrapper_names": wrapper_names(),
        "shared_library_names": shared_library_names(),
    }
