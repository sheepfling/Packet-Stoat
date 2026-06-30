#!/usr/bin/env python3
"""Run a manifest-declared workspace hook for a surface."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import shlex
import subprocess
import sys

import godot_env
import host_capability_matrix
import load_local_env
import windows_wheel_workflow
import workspace_manifest
import workspace_requirement_eval


ROOT = Path(__file__).resolve().parents[1]


def _split_command(command: str) -> list[str]:
    return shlex.split(command, posix=False)


def _env() -> dict[str, str]:
    env = os.environ.copy()
    src = str(ROOT / "src")
    pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = src if not pythonpath else f"{src}{os.pathsep}{pythonpath}"
    return env


def _normalize_command(argv: list[str]) -> list[str]:
    if not argv:
        return argv
    head = argv[0].lower()
    if head == "fastdis":
        return [sys.executable, "-m", "fastdis", *argv[1:]]
    if head == "python":
        return [sys.executable, *argv[1:]]
    return argv


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("surface", help="Surface id from the workspace manifest")
    parser.add_argument("hook", help="Canonical hook name to run")
    return parser.parse_args(argv)


def resolve_hook(surface_id: str, hook_name: str) -> dict[str, str]:
    manifest = workspace_manifest.load_manifest()
    surface = workspace_manifest.surface_spec(surface_id, manifest)
    hooks = workspace_manifest.surface_hooks(surface, manifest)
    if hook_name not in hooks:
        raise KeyError(f"hook '{hook_name}' is not declared for surface '{surface_id}'")
    return hooks[hook_name]


def _requirement_context() -> dict[str, object]:
    docker = host_capability_matrix._docker_probe()
    linux_direct = host_capability_matrix._linux_direct_probe()
    wsl = host_capability_matrix._wsl_probe()
    godot = godot_env.describe_host()
    unity_versions, _unity_default = host_capability_matrix._unity_versions_payload()
    unreal_versions = host_capability_matrix._unreal_versions_payload()
    linux_profile_versions = host_capability_matrix._unreal_linux_profile_versions()
    wheel = windows_wheel_workflow.doctor_payload(windows_wheel_workflow.DEFAULT_MINGW_PREFIX)
    return host_capability_matrix._requirement_context(
        docker=docker,
        linux_direct=linux_direct,
        wsl=wsl,
        godot=godot,
        unity_versions=unity_versions,
        unreal_versions=unreal_versions,
        linux_profile_versions=linux_profile_versions,
        wheel=wheel,
    )


def main(argv: list[str] | None = None) -> int:
    load_local_env.load()
    args = parse_args(argv)
    hook = resolve_hook(args.surface, args.hook)
    status = hook.get("status") or "unsupported"
    command = hook.get("command") or ""

    print(f"surface: {args.surface}")
    print(f"hook: {args.hook}")
    print(f"category: {hook.get('category') or 'unknown'}")
    print(f"status: {status}")
    if hook.get("notes"):
        print(f"notes: {hook['notes']}")
    requirements = hook.get("requirements") or []
    requirement_state = workspace_requirement_eval.evaluate_requirements(
        requirements,
        context=_requirement_context(),
    )
    print(f"requirement_status: {requirement_state['status']}")
    if requirement_state["failures"]:
        for failure in requirement_state["failures"]:
            print(
                "requirement_failure: "
                + f"{failure['diagnostic_code']} "
                + f"(expected={','.join(failure.get('expected') or []) or 'none'}; "
                + f"discovered={failure.get('discovered') or 'unknown'})"
            )
    if requirement_state["remediation"]:
        print(f"remediation: {', '.join(requirement_state['remediation'])}")

    if status == "unsupported":
        print("command: none")
        return 2
    if not command:
        print("command: none")
        return 2
    if requirement_state["blocking"]:
        print("command: blocked-by-requirements")
        return 2

    argv = _normalize_command(_split_command(command))
    print("+", " ".join(argv))
    completed = subprocess.run(argv, cwd=ROOT, env=_env())
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
