#!/usr/bin/env python3
"""Classify Unreal editor log failures for benchmark/reporting lanes."""

from __future__ import annotations

from pathlib import Path


def read_log(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def classify_editor_failure(output: str) -> str | None:
    if "designed for build" in output and "The following modules are missing or built with a different engine version" in output:
        return "plugin-version-incompatible"
    if "could not be found. Please ensure that this module exists and that it is compiled." in output:
        return "missing-game-module"
    if "Invalid value for PACKAGE_FILE_TAG at start of file." in output:
        return "invalid-package-file-tag"
    if "Python script executed with errors" in output or "Traceback (most recent call last)" in output:
        return "python-script-error"
    if "Failed to load plugin" in output:
        return "plugin-load-failed"
    if "Unable to read module manifest" in output:
        return "module-manifest-unreadable"
    return None


def failure_note(failure_kind: str | None) -> str | None:
    if failure_kind == "plugin-version-incompatible":
        return (
            "public GRILL Unreal plugins were skipped by this Unreal editor because their declared engine versions "
            "do not match the current host/editor lane"
        )
    if failure_kind == "missing-game-module":
        return (
            "the GRILL example project could not load its game module on this host/editor lane, so runtime asset export "
            "or FastDIS swap materialization could not proceed"
        )
    if failure_kind == "invalid-package-file-tag":
        return (
            "Unreal reported unloadable package files in the GRILL example content on this host/editor lane, which is "
            "consistent with a source/assets version mismatch"
        )
    if failure_kind == "python-script-error":
        return "the Unreal Python automation script itself failed inside the editor"
    if failure_kind == "plugin-load-failed":
        return "an Unreal plugin required by the lane failed to load before the benchmark helper could run"
    if failure_kind == "module-manifest-unreadable":
        return "Unreal could not read a required module manifest before the lane could execute"
    return None


def summarize_editor_failure(log_path: Path) -> dict[str, object]:
    output = read_log(log_path)
    failure_kind = classify_editor_failure(output)
    return {
        "failure_kind": failure_kind,
        "detail": failure_note(failure_kind),
        "log_excerpt": build_excerpt(output),
    }


def build_excerpt(output: str, *, limit: int = 12) -> list[str]:
    if not output:
        return []
    interesting: list[str] = []
    needles = (
        "designed for build",
        "missing or built with a different engine version",
        "could not be found. Please ensure that this module exists and that it is compiled.",
        "Invalid value for PACKAGE_FILE_TAG at start of file.",
        "Python script executed with errors",
        "Traceback (most recent call last)",
        "Failed to load plugin",
        "Unable to read module manifest",
    )
    for line in output.splitlines():
        if any(needle in line for needle in needles):
            interesting.append(line.strip())
            if len(interesting) >= limit:
                break
    return interesting
