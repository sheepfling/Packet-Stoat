#!/usr/bin/env python3
"""Resolve Unreal Engine installs and editor launch paths."""

from __future__ import annotations

from dataclasses import asdict
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys


DEFAULT_BINARIES = (
    "UnrealEditor-Cmd",
    "UnrealEditor",
    "UE5Editor-Cmd",
    "UE5Editor",
    "UE4Editor-Cmd",
    "UE4Editor",
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WORK_ROOT = Path("/tmp/fastdis_unreal")

MAC_EDITOR_NAMES = (
    "UnrealEditor-Cmd",
    "UnrealEditor",
    "UE5Editor-Cmd",
    "UE5Editor",
)


@dataclass(frozen=True)
class UnrealInstall:
    version: str | None
    install_root: str
    engine_dir: str
    editor_path: str | None
    editor_cmd_path: str | None
    editor_app_path: str | None
    dotnet_path: str | None
    uat_path: str | None
    ubt_path: str | None
    source: str
    quirks: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


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


def _normalize_engine_root(candidate: str | Path | None) -> Path | None:
    if candidate is None:
        return None
    path = Path(candidate).expanduser()
    if not path.exists():
        return None
    if (path / "Engine").is_dir():
        return path.resolve()
    if path.name == "Engine" and (path / "Build").is_dir():
        return path.parent.resolve()
    return None


def _normalize_editor_candidate(candidate: str | Path | None) -> Path | None:
    if candidate is None:
        return None
    path = Path(candidate).expanduser()
    if not path.exists():
        return None
    if path.is_file():
        return path.resolve()
    if path.suffix == ".app":
        macos_dir = path / "Contents" / "MacOS"
        if macos_dir.is_dir():
            for child in macos_dir.iterdir():
                if child.is_file() and os.access(child, os.X_OK):
                    return child.resolve()
    return None


def _install_root_from_editor_path(editor_path: Path) -> Path | None:
    for parent in editor_path.parents:
        if parent.name == "Engine" and (parent / "Build").is_dir():
            return parent.parent.resolve()
    return None


def _extract_version_from_name(name: str) -> str | None:
    match = re.search(r"UE[_-](\d+(?:\.\d+)*)", name)
    if match:
        return match.group(1)
    return None


def _platform_roots() -> tuple[list[Path], list[str]]:
    system = platform.system().lower()
    if system == "darwin":
        return [Path("/Users/Shared/Epic Games"), Path("/Applications")], ["UE_*", "Unreal Engine*", "UE*"]
    if system == "windows":
        return [
            Path("C:/Program Files/Epic Games"),
            Path("D:/Epic Games"),
            Path("C:/Epic Games"),
        ], ["UE_*", "Unreal Engine*"]
    return [
        Path.home() / "UnrealEngine",
        Path("/opt/UnrealEngine"),
        Path("/opt/unreal-engine"),
    ], ["UE_*", "Engine"]


def _editor_paths_for_root(install_root: Path) -> tuple[Path | None, Path | None, Path | None]:
    engine_bin = install_root / "Engine" / "Binaries" / platform_dir_name()
    if not engine_bin.is_dir():
        return None, None, None

    editor_cmd: Path | None = None
    editor: Path | None = None
    editor_app: Path | None = None

    for name in MAC_EDITOR_NAMES if platform.system().lower() == "darwin" else DEFAULT_BINARIES:
        candidate = engine_bin / name
        if candidate.is_file():
            if name.endswith("-Cmd") and editor_cmd is None:
                editor_cmd = candidate.resolve()
            elif editor is None:
                editor = candidate.resolve()

    if platform.system().lower() == "darwin":
        app = engine_bin / "UnrealEditor.app"
        if app.is_dir():
            editor_app = app.resolve()
            if editor is None:
                normalized = _normalize_editor_candidate(app)
                if normalized is not None:
                    editor = normalized

    return editor, editor_cmd, editor_app


def platform_dir_name() -> str:
    system = platform.system().lower()
    if system == "darwin":
        return "Mac"
    if system == "windows":
        return "Win64"
    return "Linux"


def python_command() -> list[str]:
    if sys.executable:
        return [sys.executable]
    if platform.system().lower() == "windows":
        return ["python"]
    return ["python3"]


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
    if platform.system().lower() == "darwin":
        env["CFFIXED_USER_HOME"] = str(sandbox_home)
    if platform.system().lower() == "windows":
        env["USERPROFILE"] = str(sandbox_home)
        env["APPDATA"] = str(sandbox_home / "AppData" / "Roaming")
        env["LOCALAPPDATA"] = str(sandbox_home / "AppData" / "Local")
    return env


def clear_generated_state(project_path: Path) -> None:
    project_root = project_path.resolve().parent
    for generated_dir in (project_root / "Binaries", project_root / "Intermediate"):
        if generated_dir.exists():
            shutil.rmtree(generated_dir)

    plugins_dir = project_root / "Plugins"
    if not plugins_dir.is_dir():
        return
    for plugin_dir in plugins_dir.iterdir():
        if not plugin_dir.is_dir():
            continue
        for generated_dir in (plugin_dir / "Binaries", plugin_dir / "Intermediate"):
            if generated_dir.exists():
                shutil.rmtree(generated_dir)


def repo_alias_root(root: Path = ROOT) -> Path:
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


def alias_repo_path(path: Path, root: Path = ROOT) -> Path:
    resolved_root = root.resolve()
    resolved_path = path.resolve()
    alias_root = repo_alias_root(root)
    if alias_root == resolved_root:
        return resolved_path
    return alias_root / resolved_path.relative_to(resolved_root)


def classify_probe_failure(output: str) -> str | None:
    if (
        "Access to the path '/Users/" in output
        and "Library/Logs/Unreal Engine/LocalBuildLogs" in output
    ) or (
        "Access to the path '/Users/" in output
        and "Library/Application Support/Epic/UnrealBuildTool" in output
    ):
        return "sandbox-home-write-denied"
    if "Platform Mac is not a valid platform to build" in output:
        return "host-mac-platform-unavailable"
    if "Platform Win64 is not a valid platform to build" in output:
        return "host-win64-platform-unavailable"
    if "Platform Linux is not a valid platform to build" in output:
        return "host-linux-platform-unavailable"
    return None


def probe_failure_note(failure_kind: str | None) -> str | None:
    if failure_kind == "sandbox-home-write-denied":
        return (
            "managed/sandboxed run denied Unreal writes under ~/Library; "
            "rerun outside the sandbox or provide writable Unreal log/cache paths"
        )
    if failure_kind == "host-mac-platform-unavailable":
        return (
            "host Mac SDK/platform rejected by this engine install before plugin code compiled; "
            "verify the engine/Xcode/macOS compatibility for this Unreal minor"
        )
    if failure_kind == "host-win64-platform-unavailable":
        return (
            "host Win64 platform rejected by this engine install before plugin code compiled; "
            "verify the engine/Visual Studio/Windows SDK compatibility for this Unreal minor"
        )
    if failure_kind == "host-linux-platform-unavailable":
        return (
            "host Linux platform rejected by this engine install before plugin code compiled; "
            "verify the engine/clang/Linux SDK compatibility for this Unreal minor"
        )
    return None


def probe_host_platform_support(install: UnrealInstall, project_path: Path | None = None) -> dict[str, object]:
    if not install.dotnet_path or not install.ubt_path:
        return {
            "status": "unavailable",
            "failure_kind": "missing-build-tool",
            "detail": "bundled dotnet or UnrealBuildTool.dll is missing",
            "command": None,
        }
    if project_path is None:
        return {
            "status": "unavailable",
            "failure_kind": "missing-project",
            "detail": "probe requires a concrete Unreal project path",
            "command": None,
        }

    # Unreal generated code is not portable across engine minors. If a 5.8 run
    # has already touched this project, scrub generated state before probing a
    # 5.7 or 5.6 lane so UHT/UBT do not reuse incompatible output.
    clear_generated_state(project_path)

    command = [
        install.dotnet_path,
        install.ubt_path,
        project_path.stem + "Editor",
        platform_dir_name(),
        "Development",
        f"-project={project_path}",
        "-NoAction",
        "-NoHotReloadFromIDE",
        "-WaitMutex",
    ]

    cache_dir = DEFAULT_WORK_ROOT / "probe_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_key = hashlib.sha256("\0".join(command).encode("utf-8")).hexdigest()
    cache_path = cache_dir / f"{cache_key}.json"
    if cache_path.is_file():
        try:
            cached = json.loads(cache_path.read_text(encoding="utf-8"))
            if isinstance(cached, dict) and cached.get("command") == command:
                return cached
        except json.JSONDecodeError:
            pass

    completed = subprocess.run(
        command,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=build_env(),
    )
    output = completed.stdout
    if completed.returncode == 0:
        result = {
            "status": "ok",
            "failure_kind": None,
            "detail": f"{platform_dir_name()} target-generation probe succeeded",
            "command": command,
            "output": output,
        }
        cache_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        return result

    failure_kind = classify_probe_failure(output)
    detail = probe_failure_note(failure_kind) or f"{platform_dir_name()} platform validation failed"
    if failure_kind == "sandbox-home-write-denied":
        status = "warn"
    elif failure_kind is not None:
        status = "fail"
    else:
        status = "warn"
    result = {
        "status": status,
        "failure_kind": failure_kind,
        "detail": detail,
        "command": command,
        "output": output,
    }
    if failure_kind is not None and failure_kind != "sandbox-home-write-denied":
        cache_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def _install_from_root(install_root: Path, *, source: str, version_hint: str | None = None) -> UnrealInstall | None:
    normalized_root = _normalize_engine_root(install_root)
    if normalized_root is None:
        return None

    version = version_hint or _extract_version_from_name(normalized_root.name)
    editor, editor_cmd, editor_app = _editor_paths_for_root(normalized_root)
    engine_dir = normalized_root / "Engine"
    dotnet = next(
        (
            candidate.resolve()
            for candidate in sorted((normalized_root / "Engine" / "Binaries" / "ThirdParty" / "DotNet").rglob("dotnet"))
            if candidate.is_file()
        ),
        None,
    )
    uat = normalized_root / "Engine" / "Build" / "BatchFiles" / ("RunUAT.bat" if platform.system().lower() == "windows" else "RunUAT.sh")
    ubt = normalized_root / "Engine" / "Binaries" / "DotNET" / "UnrealBuildTool" / "UnrealBuildTool.dll"

    quirks: list[str] = []
    if platform.system().lower() == "darwin" and editor_cmd is None and editor is not None:
        quirks.append("missing UnrealEditor-Cmd; use UnrealEditor")
    if editor_app is not None:
        quirks.append("editor app bundle present")
    if editor is None:
        quirks.append("no direct editor executable discovered")
    if not uat.exists():
        quirks.append("RunUAT missing")
    if not ubt.exists():
        quirks.append("UnrealBuildTool.dll missing")
    if dotnet is None:
        quirks.append("bundled dotnet missing")

    return UnrealInstall(
        version=version,
        install_root=str(normalized_root),
        engine_dir=str(engine_dir),
        editor_path=str(editor) if editor is not None else None,
        editor_cmd_path=str(editor_cmd) if editor_cmd is not None else None,
        editor_app_path=str(editor_app) if editor_app is not None else None,
        dotnet_path=str(dotnet) if dotnet is not None else None,
        uat_path=str(uat) if uat.exists() else None,
        ubt_path=str(ubt) if ubt.exists() else None,
        source=source,
        quirks=tuple(quirks),
    )


def discover_installs() -> list[UnrealInstall]:
    installs: dict[tuple[str | None, str], UnrealInstall] = {}

    for env_base in ("FASTDIS_UNREAL_ENGINE_DIR", "FASTDIS_UNREAL_EDITOR", "FASTDIS_UNREAL_EDITOR_CMD"):
        for key, value in sorted(os.environ.items()):
            if not key.startswith(env_base):
                continue
            if env_base.endswith("ENGINE_DIR"):
                normalized_root = _normalize_engine_root(value)
            else:
                editor = _normalize_editor_candidate(value)
                normalized_root = None if editor is None else _install_root_from_editor_path(editor)
            if normalized_root is None:
                continue
            version_hint = None
            suffix = key.removeprefix(env_base).lstrip("_")
            if suffix:
                version_hint = suffix.replace("_", ".")
            install = _install_from_root(normalized_root, source=f"env:{key}", version_hint=version_hint)
            if install is not None:
                installs[(install.version, install.install_root)] = install

    roots, patterns = _platform_roots()
    for root in roots:
        if not root.exists():
            continue
        for pattern in patterns:
            for candidate in sorted(root.glob(pattern)):
                install = _install_from_root(candidate, source=f"scan:{root}")
                if install is not None:
                    installs[(install.version, install.install_root)] = install

    return sorted(installs.values(), key=lambda item: ((item.version or ""), item.install_root))


def resolve_engine_dir(version: str | None = None) -> Path | None:
    for key in _versioned_keys("FASTDIS_UNREAL_ENGINE_DIR", version):
        path = _normalize_engine_root(os.environ.get(key))
        if path is not None:
            return path

    if version is None:
        for fallback in ("UNREAL_ENGINE_DIR", "UE_ROOT"):
            path = _normalize_engine_root(os.environ.get(fallback))
            if path is not None:
                return path

    installs = discover_installs()
    if version is not None:
        for install in installs:
            if install.version == version:
                return Path(install.install_root)
        return None
    if installs:
        return Path(installs[-1].install_root)
    return None


def resolve_editor(version: str | None = None, explicit: str | None = None) -> Path | None:
    explicit_path = _normalize_editor_candidate(explicit)
    if explicit_path is not None:
        return explicit_path

    for key in _versioned_keys("FASTDIS_UNREAL_EDITOR_CMD", version):
        path = _normalize_editor_candidate(os.environ.get(key))
        if path is not None:
            return path

    engine_dir = resolve_engine_dir(version)
    if engine_dir is not None:
        install = _install_from_root(engine_dir, source="resolve", version_hint=version)
        if install is not None:
            if install.editor_cmd_path:
                return Path(install.editor_cmd_path)
            if install.editor_path:
                return Path(install.editor_path)

    for key in _versioned_keys("FASTDIS_UNREAL_EDITOR", version):
        path = _normalize_editor_candidate(os.environ.get(key))
        if path is not None:
            return path

    for candidate in DEFAULT_BINARIES:
        resolved = shutil.which(candidate)
        if resolved:
            return Path(resolved)
    return None


def describe_install(version: str | None = None) -> dict[str, object] | None:
    install: UnrealInstall | None = None
    if version is not None:
        for candidate in discover_installs():
            if candidate.version == version:
                install = candidate
                break
    else:
        root = resolve_engine_dir()
        if root is not None:
            install = _install_from_root(root, source="resolve")
    if install is None:
        return None
    return install.to_dict()
