#!/usr/bin/env python3
"""Shared workflow/editor version defaults used by tools and tests."""

from __future__ import annotations


DEFAULT_UNREAL_SUPPORTED_VERSIONS: tuple[str, ...] = ("5.7", "5.8")
DEFAULT_UNREAL_ENGINE_VERSION = DEFAULT_UNREAL_SUPPORTED_VERSIONS[0]

DEFAULT_UNITY_VERSION_PREFIX = "6000.5"
DEFAULT_UNITY_EDITOR_VERSION = "6000.5.0f1"
