#!/usr/bin/env python3
"""Capture current FastDIS Unreal Linux portability proof without overstating runtime claims."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path
import platform
import subprocess
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PLUGIN_DIR = ROOT / "examples" / "unreal" / "FastDis"
DEFAULT_LINUX_BUILD_DIR = ROOT / "build" / "cmake" / "linux-x86_64"
DEFAULT_BUILD_CS = DEFAULT_PLUGIN_DIR / "Source" / "FastDisUnreal" / "FastDisUnreal.Build.cs"
DEFAULT_MAC_INSTALL_SMOKE = ROOT / "build" / "reports" / "unreal_packaged_install_smoke.json"
DEFAULT_OUT_DIR = ROOT / "verification_reports" / "unreal_fastdis_baseline"
DEFAULT_LINUX_PACKAGE_DIR = Path("/private/tmp/fastdis_unreal/FastDisPackage")


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


def load_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def safe_file_size(path: Path) -> int | None:
    try:
        return path.stat().st_size
    except OSError:
        return None


def file_row(path: Path) -> dict[str, Any]:
    return {
        "path": display_path(path),
        "exists": path.is_file(),
        "size_bytes": safe_file_size(path) if path.is_file() else None,
    }


def package_file_count(path: Path) -> int:
    if not path.is_dir():
        return 0
    return sum(1 for item in path.rglob("*") if item.is_file())


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    plugin_dir = args.plugin_dir.expanduser().resolve()
    linux_build_dir = args.linux_build_dir.expanduser().resolve()
    build_cs = args.build_cs.expanduser().resolve()
    mac_install_smoke_path = args.mac_install_smoke.expanduser().resolve()
    linux_package_dir = args.linux_package_dir.expanduser().resolve()
    descriptor_path = plugin_dir / "FastDis.uplugin"
    descriptor = load_json(descriptor_path) or {}
    mac_install_smoke = load_json(mac_install_smoke_path) or {}
    build_cs_text = build_cs.read_text(encoding="utf-8") if build_cs.is_file() else ""

    linux_lib = file_row(linux_build_dir / "libfastdis.so.0.13.0")
    linux_package_lib = file_row(linux_package_dir / "ThirdParty" / "fastdis" / "lib" / "Linux" / "libfastdis.so")
    linux_package_descriptor = file_row(linux_package_dir / "FastDis.uplugin")

    has_linux_linkage = "libfastdis.so" in build_cs_text and 'if (Target.Platform == UnrealTargetPlatform.Linux)' in build_cs_text
    has_linux_runtime_dep = 'RuntimeDependencies.Add' in build_cs_text and "libfastdis.so" in build_cs_text
    has_linux_readme_doc = (plugin_dir / "README.md").is_file() and "Plugins/FastDis/ThirdParty/fastdis/lib/Linux/libfastdis.so" in (
        (plugin_dir / "README.md").read_text(encoding="utf-8") if (plugin_dir / "README.md").is_file() else ""
    )

    status = "payload-ready"
    blockers: list[str] = []
    if not linux_lib["exists"]:
        status = "blocked"
        blockers.append("Linux native libfastdis build artifact is missing")
    if not has_linux_linkage:
        status = "blocked"
        blockers.append("FastDis Unreal Build.cs does not currently express Linux linkage")
    if not has_linux_runtime_dep:
        status = "blocked"
        blockers.append("FastDis Unreal Build.cs does not currently stage Linux runtime dependencies")
    if mac_install_smoke.get("status") != "pass":
        blockers.append("Current packaged-install smoke is not green on the local host")

    if linux_package_descriptor["exists"] and linux_package_lib["exists"]:
        status = "package-proof"

    claim_boundary = (
        "This artifact proves FastDIS currently has a built Linux native lib, explicit Unreal Linux linkage/staging rules, "
        "and a green packaged-install smoke on the current host. "
        "It only proves a packaged Unreal Linux plugin payload when a real Linux package directory is present."
    )

    return {
        "schema": "fastdis.fastdis_unreal_linux_proof.v1",
        "generated_at_utc": utc_now(),
        "status": status,
        "product": "FastDIS Unreal",
        "claim_boundary": claim_boundary,
        "host": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
        },
        "repository": {
            "repo_root": display_path(ROOT),
            "commit": git_output(ROOT, "rev-parse", "HEAD"),
            "branch": git_output(ROOT, "rev-parse", "--abbrev-ref", "HEAD"),
        },
        "plugin": {
            "path": display_path(plugin_dir),
            "descriptor_path": display_path(descriptor_path),
            "version_name": descriptor.get("VersionName"),
            "version": descriptor.get("Version"),
        },
        "linux_native": {
            "build_dir": display_path(linux_build_dir),
            "library": linux_lib,
            "build_cs_path": display_path(build_cs),
            "has_linux_linkage": has_linux_linkage,
            "has_linux_runtime_dependency": has_linux_runtime_dep,
            "readme_mentions_linux_payload": has_linux_readme_doc,
        },
        "current_host_package_smoke": {
            "path": display_path(mac_install_smoke_path),
            "status": mac_install_smoke.get("status"),
            "engine_version": mac_install_smoke.get("engine_version"),
            "package_dir": mac_install_smoke.get("package_dir"),
        },
        "linux_package": {
            "path": display_path(linux_package_dir),
            "exists": linux_package_dir.is_dir(),
            "file_count": package_file_count(linux_package_dir),
            "descriptor": linux_package_descriptor,
            "library": linux_package_lib,
        },
        "blockers": blockers,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# FastDIS Unreal Linux Proof",
        "",
        f"- status: `{report['status']}`",
        f"- product: `{report['product']}`",
        f"- plugin_version: `{report['plugin']['version_name']}`",
        "",
        report["claim_boundary"],
        "",
        "## Native Linux Payload",
        "",
        f"- build_dir: `{report['linux_native']['build_dir']}`",
        f"- library: `{report['linux_native']['library']['path']}` exists=`{report['linux_native']['library']['exists']}` size_bytes=`{report['linux_native']['library']['size_bytes']}`",
        f"- has_linux_linkage: `{report['linux_native']['has_linux_linkage']}`",
        f"- has_linux_runtime_dependency: `{report['linux_native']['has_linux_runtime_dependency']}`",
        f"- readme_mentions_linux_payload: `{report['linux_native']['readme_mentions_linux_payload']}`",
        "",
        "## Current Host Packaged Smoke",
        "",
        f"- report: `{report['current_host_package_smoke']['path']}`",
        f"- status: `{report['current_host_package_smoke']['status']}`",
        f"- engine_version: `{report['current_host_package_smoke']['engine_version']}`",
        f"- package_dir: `{report['current_host_package_smoke']['package_dir']}`",
        "",
        "## Linux Package",
        "",
        f"- path: `{report['linux_package']['path']}`",
        f"- exists: `{report['linux_package']['exists']}`",
        f"- file_count: `{report['linux_package']['file_count']}`",
        f"- descriptor_exists: `{report['linux_package']['descriptor']['exists']}`",
        f"- linux_lib_exists: `{report['linux_package']['library']['exists']}`",
        "",
        "## Blockers",
        "",
    ]
    if report["blockers"]:
        for blocker in report["blockers"]:
            lines.append(f"- {blocker}")
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plugin-dir", type=Path, default=DEFAULT_PLUGIN_DIR)
    parser.add_argument("--linux-build-dir", type=Path, default=DEFAULT_LINUX_BUILD_DIR)
    parser.add_argument("--build-cs", type=Path, default=DEFAULT_BUILD_CS)
    parser.add_argument("--mac-install-smoke", type=Path, default=DEFAULT_MAC_INSTALL_SMOKE)
    parser.add_argument("--linux-package-dir", type=Path, default=DEFAULT_LINUX_PACKAGE_DIR)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_OUT_DIR / "fastdis_unreal_linux_proof.json")
    parser.add_argument("--md-out", type=Path, default=DEFAULT_OUT_DIR / "fastdis_unreal_linux_proof.md")
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
    return 0 if report["status"] in {"payload-ready", "package-proof"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
