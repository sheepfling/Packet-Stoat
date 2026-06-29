#!/usr/bin/env python3
"""Discover Unity Editor installs for FastDIS Unity package workflows."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import os
from pathlib import Path
import platform
import re
import shutil
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]


def _default_work_root() -> Path:
    system = platform.system().lower()
    if system == "windows":
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            return Path(local_app_data) / "fastdis_unity"
        return Path(tempfile.gettempdir()) / "fastdis_unity"
    return Path(tempfile.gettempdir()) / "fastdis_unity"


DEFAULT_WORK_ROOT = _default_work_root()


@dataclass(frozen=True)
class UnityInstall:
    version: str
    install_root: str
    editor_path: str | None
    editor_app_path: str | None
    source: str
    quirks: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def python_command() -> list[str]:
    if sys.executable:
        return [sys.executable]
    if platform.system().lower() == "windows":
        return ["python"]
    return ["python3"]


def work_root() -> Path:
    override = os.environ.get("FASTDIS_UNITY_WORK_ROOT")
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


def build_env() -> dict[str, str]:
    env = dict(os.environ)
    root = work_root()
    if env.get("FASTDIS_UNITY_PRESERVE_HOME") in {"1", "true", "TRUE", "yes", "YES"}:
        sandbox_cache = root / "cache"
        sandbox_cache.mkdir(parents=True, exist_ok=True)
        # Preserve HOME and temp locations together. Unity Hub/licensing uses per-user
        # IPC/cache state under the normal login environment; redirecting TMPDIR can
        # make batchmode miss the signed-in license even when Hub is active.
        return env
    sandbox_home = root / "home"
    sandbox_tmp = root / "tmp"
    sandbox_cache = root / "cache"
    unity_cache = sandbox_home / "Library" / "Caches" / "com.unity3d.UnityEditor"
    for directory in (sandbox_home, sandbox_tmp, sandbox_cache, unity_cache):
        directory.mkdir(parents=True, exist_ok=True)
    env["HOME"] = str(sandbox_home)
    env["XDG_CONFIG_HOME"] = str(sandbox_home / ".config")
    env["XDG_DATA_HOME"] = str(sandbox_home / ".local" / "share")
    env["XDG_CACHE_HOME"] = str(sandbox_cache)
    env["TMPDIR"] = str(sandbox_tmp)
    if platform.system().lower() == "darwin":
        env["CFFIXED_USER_HOME"] = str(sandbox_home)
    if platform.system().lower() == "windows":
        env["USERPROFILE"] = str(sandbox_home)
        env["APPDATA"] = str(sandbox_home / "AppData" / "Roaming")
        env["LOCALAPPDATA"] = str(sandbox_home / "AppData" / "Local")
        env["TEMP"] = str(sandbox_tmp)
        env["TMP"] = str(sandbox_tmp)
    return env


def _version_suffix(version: str | None) -> str | None:
    if version is None:
        return None
    normalized = version.strip()
    if not normalized:
        return None
    return normalized.replace(".", "_").replace("-", "_")


def _versioned_keys(base: str, version: str | None) -> list[str]:
    suffix = _version_suffix(version)
    keys: list[str] = []
    if suffix:
        keys.append(f"{base}_{suffix}")
    keys.append(base)
    return keys


def _normalize_editor_path(candidate: str | Path | None) -> Path | None:
    if candidate is None:
        return None
    path = Path(candidate).expanduser()
    if not path.exists():
        return None
    if path.is_file():
        return path.resolve()
    if path.suffix == ".app":
        executable = path / "Contents" / "MacOS" / "Unity"
        if executable.is_file():
            return executable.resolve()
    executable = path / "Editor" / ("Unity.exe" if platform.system().lower() == "windows" else "Unity")
    if executable.is_file():
        return executable.resolve()
    executable = path / "Unity.app" / "Contents" / "MacOS" / "Unity"
    if executable.is_file():
        return executable.resolve()
    return None


def _install_root_from_editor(editor_path: Path) -> Path | None:
    for parent in editor_path.parents:
        if parent.name == "Unity.app":
            return parent.parent.resolve()
        if parent.name == "Editor" and re.match(r"\d", parent.parent.name):
            return parent.parent.resolve()
        if re.match(r"\d{4}\.\d+\.", parent.name):
            return parent.resolve()
    return None


def _editor_paths_for_root(root: Path) -> tuple[Path | None, Path | None]:
    if platform.system().lower() == "darwin":
        app = root / "Unity.app"
        editor = _normalize_editor_path(app)
        return editor, app.resolve() if app.is_dir() else None
    editor = root / "Editor" / ("Unity.exe" if platform.system().lower() == "windows" else "Unity")
    return editor.resolve() if editor.is_file() else None, None


def _platform_roots() -> list[Path]:
    system = platform.system().lower()
    if system == "darwin":
        return [Path("/Applications/Unity/Hub/Editor"), Path.home() / "Applications" / "Unity" / "Hub" / "Editor"]
    if system == "windows":
        return [
            Path("C:/Program Files/Unity/Hub/Editor"),
            Path("C:/Program Files/Unity"),
            Path("D:/Unity/Hub/Editor"),
        ]
    return [
        Path.home() / "Unity" / "Hub" / "Editor",
        Path("/opt/Unity/Hub/Editor"),
        Path("/opt/unity/Hub/Editor"),
    ]


def _version_from_root(root: Path) -> str:
    return root.name


def _install_from_root(root: Path, source: str) -> UnityInstall | None:
    if not root.exists():
        return None
    editor, app = _editor_paths_for_root(root)
    quirks: list[str] = []
    if editor is None:
        quirks.append("missing-editor-executable")
    return UnityInstall(
        version=_version_from_root(root),
        install_root=str(root.resolve()),
        editor_path=str(editor) if editor else None,
        editor_app_path=str(app) if app else None,
        source=source,
        quirks=tuple(quirks),
    )


def env_install(version: str | None = None) -> UnityInstall | None:
    for key in _versioned_keys("FASTDIS_UNITY_EDITOR", version):
        editor = _normalize_editor_path(os.environ.get(key))
        if editor is None:
            continue
        root = _install_root_from_editor(editor) or editor.parent
        return UnityInstall(
            version=version or _version_from_root(root),
            install_root=str(root),
            editor_path=str(editor),
            editor_app_path=str(root / "Unity.app") if (root / "Unity.app").is_dir() else None,
            source=f"env:{key}",
            quirks=(),
        )
    for key in _versioned_keys("FASTDIS_UNITY_EDITOR_DIR", version):
        candidate = os.environ.get(key)
        if not candidate:
            continue
        install = _install_from_root(Path(candidate).expanduser(), f"env:{key}")
        if install is not None:
            return install
    return None


def discover_installs() -> list[UnityInstall]:
    installs: dict[str, UnityInstall] = {}
    env = env_install(None)
    if env is not None:
        installs[env.install_root] = env
    path_editor = shutil.which("unity") or shutil.which("Unity") or shutil.which("Unity.exe")
    if path_editor:
        editor = Path(path_editor).resolve()
        root = _install_root_from_editor(editor) or editor.parent
        installs[str(root)] = UnityInstall(
            version=_version_from_root(root),
            install_root=str(root),
            editor_path=str(editor),
            editor_app_path=str(root / "Unity.app") if (root / "Unity.app").is_dir() else None,
            source="PATH",
            quirks=(),
        )
    for base in _platform_roots():
        if not base.is_dir():
            continue
        for root in sorted(path for path in base.iterdir() if path.is_dir()):
            install = _install_from_root(root, f"scan:{base}")
            if install is not None:
                installs.setdefault(install.install_root, install)
    return sorted(installs.values(), key=lambda install: install.version)


def _preferred_install(installs: list[UnityInstall]) -> UnityInstall | None:
    for install in reversed(installs):
        if install.editor_path is not None:
            return install
    return installs[-1] if installs else None


def recommended_editor_overrides(install: UnityInstall | None) -> dict[str, str]:
    if install is None or install.editor_path is None:
        return {}
    overrides = {"FASTDIS_UNITY_EDITOR": install.editor_path}
    if install.install_root:
        overrides["FASTDIS_UNITY_EDITOR_DIR"] = install.install_root
    return overrides


def resolve_install(version: str | None = None) -> UnityInstall | None:
    env = env_install(version)
    if env is not None:
        return env
    installs = discover_installs()
    if version:
        for install in installs:
            if install.version == version or install.version.startswith(version):
                return install
        return None
    return _preferred_install(installs)


def describe_host() -> dict[str, object]:
    current_work_root = work_root()
    discovered = discover_installs()
    preferred = _preferred_install(discovered)
    installs = [install.to_dict() for install in discovered]
    return {
        "platform": platform.system(),
        "arch": platform.machine(),
        "repo_root": str(ROOT),
        "work_root": str(current_work_root),
        "work_root_has_spaces": " " in str(current_work_root),
        "installs": installs,
        "default_install": preferred.to_dict() if preferred else None,
        "recommended_editor_overrides": recommended_editor_overrides(preferred),
    }
