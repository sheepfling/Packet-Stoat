#!/usr/bin/env python3
"""Local path defaults for external GRILL source checkouts used by FastDIS tooling."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GRILL_ROOT = ROOT / "external" / "grill"

UNREAL_PLUGIN = GRILL_ROOT / "GRILL_DISPluginForUnreal"
UNREAL_EXAMPLE = GRILL_ROOT / "GRILL_DISForUnrealExample"
UNITY_PLUGIN = GRILL_ROOT / "GRILL_DISPluginForUnity"
UNITY_EXAMPLE = GRILL_ROOT / "GRILL_DISForUnityExample"


def all_roots() -> tuple[Path, Path, Path, Path]:
    return (UNREAL_PLUGIN, UNREAL_EXAMPLE, UNITY_PLUGIN, UNITY_EXAMPLE)
