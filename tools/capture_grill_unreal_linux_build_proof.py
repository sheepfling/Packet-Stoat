#!/usr/bin/env python3
"""Capture pinned evidence for a GRILL Unreal Linux BuildPlugin proof run."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
import os
from pathlib import Path
import platform
import subprocess
from typing import Any

import grill_paths

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PLUGIN_ROOT = grill_paths.UNREAL_PLUGIN
DEFAULT_PROFILE = DEFAULT_PLUGIN_ROOT / "Scripts" / "linux_proof_profiles" / "ubuntu_24_04_ue57.env"
DEFAULT_PACKAGE_DIR = (
    DEFAULT_PLUGIN_ROOT
    / ".build"
    / "grill_buildplugin_linux"
    / "ue5.7.4-linux_ubuntu-24.04"
    / "package"
)
DEFAULT_OUT_DIR = ROOT / "verification_reports" / "unreal_grill_baseline"


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def git_output(path: Path, *args: str) -> str | None:
    try:
        completed = subprocess.run(
            ["git", "-C", str(path), *args],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    value = completed.stdout.strip()
    return value or None


def parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("'").strip('"')
    return values


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def safe_file_size(path: Path) -> int | None:
    try:
        return path.stat().st_size
    except OSError:
        return None


def inventory(paths: list[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        rows.append(
            {
                "path": path.as_posix(),
                "exists": path.is_file(),
                "size_bytes": safe_file_size(path) if path.is_file() else None,
            }
        )
    return rows


def package_file_count(package_dir: Path) -> int:
    if not package_dir.is_dir():
        return 0
    return sum(1 for path in package_dir.rglob("*") if path.is_file())


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    plugin_root = args.plugin_root.expanduser().resolve()
    profile_path = args.profile.expanduser().resolve()
    package_dir = args.package_dir.expanduser().resolve()
    env_values = parse_env_file(profile_path)
    descriptor_path = package_dir / "GRILLDISForUnreal.uplugin"
    descriptor = load_json(descriptor_path) if descriptor_path.is_file() else {}
    binaries = inventory(
        [
            package_dir / "Binaries" / "Linux" / "libUnrealEditor-DISRuntime.so",
            package_dir / "Binaries" / "Linux" / "libUnrealEditor-DISEditor.so",
            package_dir / "Source" / "ThirdParty" / "Binaries" / "Linux" / "libOpenDIS6.a",
        ]
    )
    module_allow_lists: list[str] = []
    for module in descriptor.get("Modules", []):
        if not isinstance(module, dict):
            continue
        for field in ("PlatformAllowList", "WhitelistPlatforms"):
            values = module.get(field)
            if isinstance(values, list):
                for value in values:
                    if isinstance(value, str) and value not in module_allow_lists:
                        module_allow_lists.append(value)

    status = "pass"
    blockers: list[str] = []
    if not package_dir.is_dir():
        status = "fail"
        blockers.append("packaged Linux plugin directory is missing")
    for row in binaries:
        if not row["exists"]:
            status = "fail"
            blockers.append(f"missing required packaged artifact: {row['path']}")

    return {
        "schema": "fastdis.grill_unreal_linux_build_proof.v1",
        "generated_at_utc": utc_now(),
        "status": status,
        "product": "GRILL DIS for Unreal",
        "claim_boundary": "Build-proof only. This artifact proves Linux plugin packaging from the pinned GRILL source route on a Mac host via Docker. It does not claim Linux runtime gameplay, benchmark throughput, or same-host FastDIS-vs-GRILL performance parity.",
        "host": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
        },
        "repository": {
            "plugin_root": display_path(plugin_root),
            "plugin_commit": git_output(plugin_root, "rev-parse", "HEAD"),
            "plugin_branch": git_output(plugin_root, "rev-parse", "--abbrev-ref", "HEAD"),
            "plugin_remote": git_output(plugin_root, "remote", "get-url", "origin"),
        },
        "proof_profile": {
            "path": display_path(profile_path),
            "exists": profile_path.is_file(),
            "ue_version_label": env_values.get("UE_VERSION_LABEL"),
            "ue_proof_profile": env_values.get("UE_PROOF_PROFILE"),
            "ue_linux_image": env_values.get("UE_LINUX_IMAGE"),
            "docker_platform": env_values.get("DOCKER_PLATFORM"),
            "ue_host_path": env_values.get("UE_HOST_PATH") or None,
            "ue_host_archive": env_values.get("UE_HOST_ARCHIVE") or None,
            "host_engine_stage_dir": env_values.get("HOST_ENGINE_STAGE_DIR") or None,
        },
        "package": {
            "path": display_path(package_dir),
            "exists": package_dir.is_dir(),
            "file_count": package_file_count(package_dir),
            "descriptor_path": display_path(descriptor_path),
            "engine_version": descriptor.get("EngineVersion"),
            "friendly_name": descriptor.get("FriendlyName"),
            "installed": descriptor.get("Installed"),
            "platform_allow_list": module_allow_lists,
            "required_artifacts": binaries,
        },
        "blockers": blockers,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# GRILL Unreal Linux Build Proof",
        "",
        f"- status: `{report['status']}`",
        f"- product: `{report['product']}`",
        f"- package: `{report['package']['path']}`",
        f"- engine_version: `{report['package']['engine_version']}`",
        "",
        report["claim_boundary"],
        "",
        "## Source Route",
        "",
        f"- plugin_root: `{report['repository']['plugin_root']}`",
        f"- plugin_commit: `{report['repository']['plugin_commit']}`",
        f"- plugin_branch: `{report['repository']['plugin_branch']}`",
        f"- plugin_remote: `{report['repository']['plugin_remote']}`",
        "",
        "## Docker Proof Profile",
        "",
        f"- profile: `{report['proof_profile']['path']}`",
        f"- ue_version_label: `{report['proof_profile']['ue_version_label']}`",
        f"- ue_proof_profile: `{report['proof_profile']['ue_proof_profile']}`",
        f"- ue_linux_image: `{report['proof_profile']['ue_linux_image']}`",
        f"- docker_platform: `{report['proof_profile']['docker_platform']}`",
        f"- ue_host_archive: `{report['proof_profile']['ue_host_archive']}`",
        "",
        "## Package Evidence",
        "",
        f"- exists: `{report['package']['exists']}`",
        f"- file_count: `{report['package']['file_count']}`",
        f"- platform_allow_list: `{', '.join(report['package']['platform_allow_list'])}`",
        "",
        "## Required Artifacts",
        "",
    ]
    for row in report["package"]["required_artifacts"]:
        lines.append(
            f"- `{row['path']}` exists=`{row['exists']}` size_bytes=`{row['size_bytes']}`"
        )
    lines.extend(["", "## Blockers", ""])
    if report["blockers"]:
        for blocker in report["blockers"]:
            lines.append(f"- {blocker}")
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plugin-root", type=Path, default=DEFAULT_PLUGIN_ROOT)
    parser.add_argument("--profile", type=Path, default=DEFAULT_PROFILE)
    parser.add_argument("--package-dir", type=Path, default=DEFAULT_PACKAGE_DIR)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_OUT_DIR / "grill_unreal_linux_build_proof.json")
    parser.add_argument("--md-out", type=Path, default=DEFAULT_OUT_DIR / "grill_unreal_linux_build_proof.md")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report = build_report(args)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.md_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    args.md_out.write_text(render_markdown(report) + "\n", encoding="utf-8")
    print(f"json: {display_path(args.json_out)}")
    print(f"md: {display_path(args.md_out)}")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
