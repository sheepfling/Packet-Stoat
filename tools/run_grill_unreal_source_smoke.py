#!/usr/bin/env python3
"""Inspect the GRILL Unreal source route and record whether this host can build it."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path
import platform as host_platform
import subprocess
from typing import Any

import grill_paths
import load_local_env
import prepare_grill_source_route
import unreal_env


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PLUGIN_ROOT = grill_paths.UNREAL_PLUGIN
DEFAULT_EXAMPLE_ROOT = grill_paths.UNREAL_EXAMPLE
DEFAULT_OUT_DIR = ROOT / "verification_reports" / "unreal_grill_baseline"


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def host_unreal_platform() -> str:
    system = host_platform.system().lower()
    if system == "darwin":
        return "Mac"
    if system == "windows":
        return "Win64"
    return "Linux"


def git_commit(path: Path) -> str | None:
    try:
        completed = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "HEAD"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return completed.stdout.strip() or None


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def plugin_descriptor_path(plugin_root: Path) -> Path:
    matches = sorted(plugin_root.glob("*.uplugin"))
    if not matches:
        raise FileNotFoundError(f"no .uplugin found under {plugin_root}")
    return matches[0]


def project_descriptor_path(example_root: Path) -> Path:
    matches = sorted(example_root.glob("*.uproject"))
    if not matches:
        raise FileNotFoundError(f"no .uproject found under {example_root}")
    return matches[0]


def plugin_whitelist_platforms(descriptor: dict[str, Any]) -> list[str]:
    platforms: list[str] = []
    for module in descriptor.get("Modules", []):
        if not isinstance(module, dict):
            continue
        for field in ("WhitelistPlatforms", "PlatformAllowList"):
            values = module.get(field)
            if isinstance(values, list):
                for value in values:
                    if isinstance(value, str) and value not in platforms:
                        platforms.append(value)
    return platforms


def third_party_binary_platforms(plugin_root: Path) -> list[str]:
    base = plugin_root / "Source" / "ThirdParty" / "Binaries"
    if not base.is_dir():
        return []
    return sorted(child.name for child in base.iterdir() if child.is_dir())


def build_cs_has_win64_only_linkage(plugin_root: Path) -> bool:
    build_cs = plugin_root / "Source" / "DISRuntime" / "DISRuntime.Build.cs"
    if not build_cs.is_file():
        return False
    text = build_cs.read_text(encoding="utf-8")
    return "Win64" in text and ("OpenDIS6.lib" in text or "OpenDIS7.lib" in text)


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# GRILL Unreal Source Smoke",
        "",
        f"- status: `{report['status']}`",
        f"- host_platform: `{report['host_platform']}`",
        f"- requested_engine_version: `{report.get('requested_engine_version')}`",
        f"- resolved_engine_version: `{report.get('resolved_engine_version')}`",
        f"- plugin_root: `{report.get('plugin_root')}`",
        f"- example_root: `{report.get('example_root')}`",
        f"- detail: `{report.get('detail')}`",
        "",
        "## Source Pins",
        "",
        f"- plugin_commit: `{report.get('plugin_commit')}`",
        f"- example_commit: `{report.get('example_commit')}`",
        f"- example_plugin_commit: `{report.get('example_plugin_commit')}`",
        "",
        "## Platform Evidence",
        "",
        f"- plugin_whitelist_platforms: `{', '.join(report.get('plugin_whitelist_platforms', []))}`",
        f"- third_party_binary_platforms: `{', '.join(report.get('third_party_binary_platforms', []))}`",
        f"- win64_only_build_cs_linkage: `{report.get('win64_only_build_cs_linkage')}`",
        "",
    ]
    install = report.get("install")
    if isinstance(install, dict):
        lines.extend(
            [
                "## Install",
                "",
                f"- install_root: `{install.get('install_root')}`",
                f"- editor: `{install.get('editor_path')}`",
                "",
            ]
        )
    probe = report.get("platform_probe")
    if isinstance(probe, dict):
        lines.extend(
            [
                "## Platform Probe",
                "",
                f"- status: `{probe.get('status')}`",
                f"- failure_kind: `{probe.get('failure_kind')}`",
                f"- detail: `{probe.get('detail')}`",
                "",
            ]
        )
    blockers = report.get("blockers") or []
    lines.extend(["## Blockers", ""])
    if blockers:
        for blocker in blockers:
            lines.append(f"- {blocker}")
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plugin-root", type=Path, default=DEFAULT_PLUGIN_ROOT)
    parser.add_argument("--example-root", type=Path, default=DEFAULT_EXAMPLE_ROOT)
    parser.add_argument("--engine-version", default="4.27")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--prepare-checkout", dest="prepare_checkout", action="store_true", help="Fetch and switch the local GRILL public-route Unreal repos onto their expected benchmark branches before probing.")
    parser.add_argument("--no-prepare-checkout", dest="prepare_checkout", action="store_false", help="Skip automatic GRILL checkout preparation.")
    parser.set_defaults(prepare_checkout=None)
    return parser.parse_args(argv)


def should_prepare_checkout(args: argparse.Namespace) -> bool:
    if args.prepare_checkout is not None:
        return bool(args.prepare_checkout)
    return (
        args.plugin_root.expanduser().resolve() == DEFAULT_PLUGIN_ROOT.resolve()
        and args.example_root.expanduser().resolve() == DEFAULT_EXAMPLE_ROOT.resolve()
    )


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    plugin_root = args.plugin_root.expanduser().resolve()
    example_root = args.example_root.expanduser().resolve()
    report: dict[str, Any] = {
        "schema": "fastdis.grill_unreal_source_smoke.v1",
        "generated_at": utc_now(),
        "status": "fail",
        "host_platform": host_unreal_platform(),
        "requested_engine_version": args.engine_version,
        "resolved_engine_version": None,
        "plugin_root": str(plugin_root),
        "example_root": str(example_root),
        "plugin_commit": git_commit(plugin_root),
        "example_commit": git_commit(example_root),
        "example_plugin_commit": git_commit(example_root / "Plugins" / "DISPluginForUnreal"),
        "blockers": [],
    }

    if should_prepare_checkout(args):
        prep_report = prepare_grill_source_route.build_report(
            [
                prepare_grill_source_route.RepoSpec(
                    key="unreal_plugin",
                    label="GRILL Unreal plugin",
                    path=plugin_root,
                    target_branch="ue5",
                ),
                prepare_grill_source_route.RepoSpec(
                    key="unreal_example",
                    label="GRILL Unreal example",
                    path=example_root,
                    target_branch="ue5",
                    update_submodules=True,
                ),
            ],
            fetch=True,
            allow_dirty=False,
            update_submodules=True,
        )
        report["checkout_prepare"] = prep_report
        for row in prep_report.get("repos", []):
            if isinstance(row, dict) and row.get("status") != "prepared":
                report["status"] = "checkout-prepare-failed"
                report["detail"] = "GRILL Unreal source-route checkout preparation failed before the host probe."
                report["blockers"].append(f"{row.get('key')}: {row.get('status')}")
        report["plugin_commit"] = git_commit(plugin_root)
        report["example_commit"] = git_commit(example_root)
        report["example_plugin_commit"] = git_commit(example_root / "Plugins" / "DISPluginForUnreal")
        if report["blockers"]:
            return report

    if not plugin_root.is_dir():
        report["status"] = "missing-source"
        report["detail"] = "GRILL Unreal plugin source checkout not found."
        report["blockers"].append("plugin source checkout missing")
        return report
    if not example_root.is_dir():
        report["status"] = "missing-source"
        report["detail"] = "GRILL Unreal example source checkout not found."
        report["blockers"].append("example source checkout missing")
        return report

    plugin_descriptor = load_json(plugin_descriptor_path(plugin_root))
    project_descriptor = load_json(project_descriptor_path(example_root))
    whitelist_platforms = plugin_whitelist_platforms(plugin_descriptor)
    binary_platforms = third_party_binary_platforms(plugin_root)
    win64_only_build = build_cs_has_win64_only_linkage(plugin_root)
    report["plugin_descriptor"] = {
        "friendly_name": plugin_descriptor.get("FriendlyName"),
        "engine_version": plugin_descriptor.get("EngineVersion"),
    }
    report["project_descriptor"] = {
        "engine_association": project_descriptor.get("EngineAssociation"),
    }
    report["plugin_whitelist_platforms"] = whitelist_platforms
    report["third_party_binary_platforms"] = binary_platforms
    report["win64_only_build_cs_linkage"] = win64_only_build

    install = next((row for row in unreal_env.discover_installs() if row.version == args.engine_version), None)
    if install is not None:
        report["resolved_engine_version"] = install.version
        report["install"] = install.to_dict()
    else:
        report["status"] = "missing-install"
        report["detail"] = f"Unreal {args.engine_version} install not found on this host."
        report["blockers"].append(f"Unreal {args.engine_version} install missing")
        return report

    host_platform_name = report["host_platform"]
    if whitelist_platforms and host_platform_name not in whitelist_platforms:
        report["status"] = "blocked-host-platform"
        report["detail"] = (
            f"GRILL Unreal source route is not buildable on this host: plugin manifest allows "
            f"{', '.join(whitelist_platforms)} but current host platform is {host_platform_name}."
        )
        report["blockers"].append(
            f"plugin manifest does not allow host platform {host_platform_name}"
        )
        if win64_only_build:
            report["blockers"].append("DISRuntime.Build.cs links Win64-only OpenDIS import libraries")
        if binary_platforms and host_platform_name not in binary_platforms:
            report["blockers"].append(
                f"third-party binary payload is present only for {', '.join(binary_platforms)}"
            )
        return report

    if win64_only_build and host_platform_name != "Win64":
        report["status"] = "blocked-host-platform"
        report["detail"] = "GRILL Unreal build rules link Win64-only third-party binaries on this host."
        report["blockers"].append("DISRuntime.Build.cs links Win64-only OpenDIS import libraries")
        return report

    project_path = project_descriptor_path(example_root)
    probe = unreal_env.probe_host_platform_support(install, project_path)
    report["platform_probe"] = probe
    if probe.get("status") == "ok":
        report["status"] = "pass"
        report["detail"] = "GRILL Unreal source route passed the host platform build probe."
    else:
        report["status"] = "probe-fail"
        report["detail"] = str(probe.get("detail") or "GRILL Unreal source route failed the host platform build probe.")
        if probe.get("failure_kind"):
            report["blockers"].append(str(probe["failure_kind"]))
    return report


def main(argv: list[str] | None = None) -> int:
    load_local_env.load()
    args = parse_args(argv)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    report = build_report(args)
    json_path = args.out_dir / "grill_unreal_source_smoke.json"
    md_path = args.out_dir / "grill_unreal_source_smoke.md"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report) + "\n", encoding="utf-8")
    print(f"JSON: {json_path}")
    print(f"Markdown: {md_path}")
    return 0 if report["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
