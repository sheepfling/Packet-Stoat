#!/usr/bin/env python3
"""Shared Unity launcher-attempt builders for host-specific editor routing."""

from __future__ import annotations

from pathlib import Path
import platform as host_platform
import shlex
from typing import Any


def is_macos() -> bool:
    return host_platform.system().lower() == "darwin"


def build_login_shell_attempt(
    unity_command: list[str],
    *,
    log_path: Path,
    launcher_log_path: Path,
    results_json: Path | None = None,
) -> dict[str, object]:
    return {
        "mode": "interactive",
        "launch": "login-shell",
        "cmd": ["/bin/zsh", "-lc", " ".join(shlex.quote(part) for part in unity_command)],
        "unity_command": unity_command,
        "env": None,
        "results_json": results_json,
        "log": log_path,
        "launcher_log": launcher_log_path,
    }


def build_launch_services_attempt(
    editor_app_path: str,
    unity_command: list[str],
    *,
    log_path: Path,
    launcher_log_path: Path,
    results_json: Path | None = None,
) -> dict[str, object]:
    return {
        "mode": "interactive",
        "launch": "launch-services",
        "cmd": ["open", "-W", "-n", "-a", editor_app_path, "--args", *unity_command[1:]],
        "unity_command": [editor_app_path, *unity_command[1:]],
        "env": None,
        "results_json": results_json,
        "log": log_path,
        "launcher_log": launcher_log_path,
    }


def build_direct_attempt(
    cmd: list[str],
    *,
    unity_command: list[str],
    mode: str,
    env: dict[str, str] | None,
    log_path: Path,
    launcher_log_path: Path,
    results_json: Path | None = None,
) -> dict[str, object]:
    return {
        "mode": mode,
        "launch": "direct",
        "cmd": cmd,
        "unity_command": unity_command,
        "env": env,
        "results_json": results_json,
        "log": log_path,
        "launcher_log": launcher_log_path,
    }


def macos_interactive_attempts(
    unity_command: list[str],
    *,
    editor_app_path: str | None,
    log_path: Path,
    report_dir: Path,
    launcher_prefix: str,
    results_json: Path | None = None,
) -> list[dict[str, Any]]:
    if not is_macos():
        return []
    attempts: list[dict[str, Any]] = [
        build_login_shell_attempt(
            unity_command,
            log_path=log_path,
            launcher_log_path=report_dir / f"{launcher_prefix}_login_shell_launcher.log",
            results_json=results_json,
        )
    ]
    if editor_app_path:
        attempts.append(
            build_launch_services_attempt(
                editor_app_path,
                unity_command,
                log_path=log_path,
                launcher_log_path=report_dir / f"{launcher_prefix}_launch_services_launcher.log",
                results_json=results_json,
            )
        )
    return attempts
