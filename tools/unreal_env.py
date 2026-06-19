#!/usr/bin/env python3
"""Resolve repo-local Unreal Engine path configuration."""

from __future__ import annotations

import os
from pathlib import Path
import platform
import shutil


DEFAULT_BINARIES = (
    "UnrealEditor-Cmd",
    "UnrealEditor",
    "UE5Editor-Cmd",
    "UE5Editor",
    "UE4Editor-Cmd",
    "UE4Editor",
)


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


def _first_existing_file(keys: list[str]) -> Path | None:
    for key in keys:
        candidate = os.environ.get(key)
        if not candidate:
            continue
        path = Path(candidate).expanduser()
        if path.is_file():
            return path
    return None


def _first_existing_dir(keys: list[str]) -> Path | None:
    for key in keys:
        candidate = os.environ.get(key)
        if not candidate:
            continue
        path = Path(candidate).expanduser()
        if path.exists():
            return path
    return None


def resolve_editor(version: str | None = None, explicit: str | None = None) -> Path | None:
    if explicit:
        path = Path(explicit).expanduser()
        if path.is_file():
            return path
        return None

    path = _first_existing_file(_versioned_keys("FASTDIS_UNREAL_EDITOR_CMD", version))
    if path is not None:
        return path

    path = _first_existing_file(_versioned_keys("FASTDIS_UNREAL_EDITOR", version))
    if path is not None:
        return path

    for candidate in DEFAULT_BINARIES:
        resolved = shutil.which(candidate)
        if resolved:
            return Path(resolved)

    engine_dir = resolve_engine_dir(version)
    if engine_dir is None:
        return None

    for name in ("UnrealEditor-Cmd", "UnrealEditor", "UE5Editor-Cmd", "UE5Editor"):
        candidate = engine_dir / "Engine" / "Binaries" / "Mac" / name
        if candidate.is_file():
            return candidate
    return None


def resolve_engine_dir(version: str | None = None) -> Path | None:
    path = _first_existing_dir(_versioned_keys("FASTDIS_UNREAL_ENGINE_DIR", version))
    if path is not None:
        return path

    if version is None:
        for fallback in ("UNREAL_ENGINE_DIR", "UE_ROOT"):
            candidate = os.environ.get(fallback)
            if not candidate:
                continue
            path = Path(candidate).expanduser()
            if path.exists():
                return path

    system = platform.system().lower()
    if system == "darwin":
        roots = [Path("/Users/Shared/Epic Games")]
        patterns = ["UE_*"]
    elif system == "windows":
        roots = [
            Path("C:/Program Files/Epic Games"),
            Path("D:/Epic Games"),
            Path("C:/Epic Games"),
        ]
        patterns = ["UE_*"]
    else:
        roots = [
            Path.home() / "UnrealEngine",
            Path("/opt/UnrealEngine"),
            Path("/opt/unreal-engine"),
        ]
        patterns = ["UE_*", "Engine"]

    candidates: list[Path] = []
    wanted_prefix = None if version is None else f"UE_{version}"
    for root in roots:
        if not root.exists():
            continue
        for pattern in patterns:
            for candidate in sorted(root.glob(pattern)):
                if wanted_prefix and not candidate.name.startswith(wanted_prefix):
                    continue
                candidates.append(candidate)

    if not candidates:
        return None
    return sorted(candidates)[-1]
