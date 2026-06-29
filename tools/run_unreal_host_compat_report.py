#!/usr/bin/env python3
"""Write a host/toolchain compatibility report for Unreal engine lanes."""

from __future__ import annotations

import argparse
from datetime import UTC
from datetime import datetime
import json
import platform
from pathlib import Path
import subprocess

import load_local_env
import unreal_env


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = ROOT / "build" / "reports"
DEFAULT_PROBE_PROJECT = ROOT / "packages" / "unreal" / "FastDisOrientationVerification" / "FastDisOrientationVerification.uproject"
DEFAULT_SUPPORTED_VERSIONS = ["5.7", "5.8"]
EPIC_MACOS_REQUIREMENTS_URL = "https://dev.epicgames.com/documentation/en-us/unreal-engine/macos-development-requirements-for-unreal-engine"
EPIC_UE56_MACOS_BASELINE = {
    "minimum_macos": "Sonoma 14.0",
    "recommended_macos": "Latest macOS 14 Sonoma",
    "minimum_xcode": "Xcode 15.2",
    "recommended_xcode": "Xcode 15.4 or newer",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--versions", nargs="+", default=DEFAULT_SUPPORTED_VERSIONS, help="Unreal versions to probe")
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR), help="Directory for JSON/Markdown reports")
    parser.add_argument("--probe-project", default=str(DEFAULT_PROBE_PROJECT), help="Project used for the UBT host probe")
    return parser.parse_args()


def capture_command(cmd: list[str]) -> dict[str, object]:
    completed = subprocess.run(
        cmd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    return {
        "command": cmd,
        "returncode": completed.returncode,
        "output": completed.stdout,
    }


def detect_host_facts() -> dict[str, object]:
    facts: dict[str, object] = {
        "platform_system": platform.system(),
        "platform_release": platform.release(),
        "platform_version": platform.version(),
        "machine": platform.machine(),
    }
    if platform.system().lower() == "darwin":
        facts["xcode_select"] = capture_command(["xcode-select", "-p"])
        facts["sw_vers"] = capture_command(["sw_vers"])
        facts["clang_version"] = capture_command(["xcrun", "clang", "--version"])
        facts["sdk_path"] = capture_command(["xcrun", "--show-sdk-path"])
    else:
        facts["clang_version"] = capture_command(["clang", "--version"])
    return facts


def summarize_markdown(report: dict[str, object]) -> str:
    lines = [
        "# Unreal Host Compatibility Report",
        "",
        f"- generated_at: `{report['generated_at']}`",
        f"- host_platform: `{report['host']['platform_system']}`",
        f"- host_machine: `{report['host']['machine']}`",
        "",
        "| Version | Discovered | Probe Status | Failure Kind | Summary |",
        "| --- | --- | --- | --- | --- |",
    ]
    for lane in report["lanes"]:
        probe = lane["probe"]
        lines.append(
            f"| {lane['version']} | {'yes' if lane['discovered'] else 'no'} | {probe['status']} | {probe.get('failure_kind') or 'none'} | {probe['detail']} |"
        )
    lines.extend(["", "## Host Facts", ""])
    for key in ("xcode_select", "sw_vers", "clang_version", "sdk_path"):
        value = report["host"].get(key)
        if not value:
            continue
        lines.append(f"### {key}")
        lines.append("")
        lines.append(f"- returncode: `{value['returncode']}`")
        lines.append("```text")
        lines.append(str(value["output"]).rstrip())
        lines.append("```")
        lines.append("")
    lines.append("## Compatibility Interpretation")
    lines.append("")
    lines.append(f"- Official Epic reference: `{report['official_reference']['macos_requirements_url']}`")
    ue56 = report["official_reference"]["ue56_macos_baseline"]
    lines.append(
        "- UE 5.6 macOS baseline from Epic (kept as optional compatibility reference, not a required Alpha 2 signoff lane): "
        f"minimum macOS `{ue56['minimum_macos']}`, recommended macOS `{ue56['recommended_macos']}`, "
        f"minimum Xcode `{ue56['minimum_xcode']}`, recommended Xcode `{ue56['recommended_xcode']}`."
    )
    host_summary = report["host"].get("sw_vers_summary")
    if host_summary:
        lines.append(f"- This host reported macOS `{host_summary}`.")
    clang_summary = report["host"].get("clang_summary")
    if clang_summary:
        lines.append(f"- This host reported toolchain `{clang_summary}`.")
    lines.append(
        "- Alpha 2 signoff uses Unreal 5.7 and 5.8 as the supported engine lanes. Use an explicit `--versions 5.6 5.7 5.8` run only when you want optional 5.6 compatibility evidence."
    )
    lines.append("")
    lines.append("## Lane Details")
    lines.append("")
    for lane in report["lanes"]:
        lines.append(f"### {lane['version']}")
        lines.append("")
        if lane["install"] is None:
            lines.append("- install not discovered")
            lines.append("")
            continue
        lines.append(f"- install_root: `{lane['install']['install_root']}`")
        lines.append(f"- editor_path: `{lane['install']['editor_path'] or 'missing'}`")
        lines.append(f"- dotnet_path: `{lane['install']['dotnet_path'] or 'missing'}`")
        lines.append(f"- ubt_path: `{lane['install']['ubt_path'] or 'missing'}`")
        quirks = lane["install"].get("quirks") or []
        if quirks:
            for quirk in quirks:
                lines.append(f"- quirk: {quirk}")
        else:
            lines.append("- quirk: none")
        lines.append(f"- probe status: `{lane['probe']['status']}`")
        lines.append(f"- probe detail: {lane['probe']['detail']}")
        if lane["probe"].get("failure_kind"):
            lines.append(f"- probe failure kind: `{lane['probe']['failure_kind']}`")
        command = lane["probe"].get("command")
        if command:
            lines.append("- probe command:")
            lines.append("```text")
            lines.append(" ".join(command))
            lines.append("```")
        output = lane["probe"].get("output")
        if output:
            lines.append("- probe output excerpt:")
            lines.append("```text")
            lines.append(str(output).rstrip()[:4000])
            lines.append("```")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    load_local_env.load()
    args = parse_args()
    out_dir = Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    probe_project = Path(args.probe_project).expanduser().resolve()

    installs = {install.version: install for install in unreal_env.discover_installs()}
    lanes: list[dict[str, object]] = []
    overall_ok = True
    for version in args.versions:
        install = installs.get(version)
        if install is None:
            lanes.append(
                {
                    "version": version,
                    "discovered": False,
                    "install": None,
                    "probe": {
                        "status": "missing-install",
                        "failure_kind": "missing-install",
                        "detail": "engine install not discovered",
                        "command": None,
                        "output": "",
                    },
                }
            )
            overall_ok = False
            continue
        probe = unreal_env.probe_host_platform_support(install, probe_project)
        lanes.append(
            {
                "version": version,
                "discovered": True,
                "install": install.to_dict(),
                "probe": probe,
            }
        )
        overall_ok = overall_ok and probe["status"] == "ok"

    host = detect_host_facts()
    sw_vers_output = str(host.get("sw_vers", {}).get("output", ""))
    clang_output = str(host.get("clang_version", {}).get("output", ""))
    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "host": {
            **host,
            "sw_vers_summary": next(
                (
                    line.split(":", 1)[1].strip()
                    for line in sw_vers_output.splitlines()
                    if line.startswith("ProductVersion:")
                ),
                None,
            ),
            "clang_summary": clang_output.splitlines()[0] if clang_output else None,
        },
        "official_reference": {
            "macos_requirements_url": EPIC_MACOS_REQUIREMENTS_URL,
            "ue56_macos_baseline": EPIC_UE56_MACOS_BASELINE,
        },
        "probe_project": str(probe_project),
        "lanes": lanes,
    }
    json_path = out_dir / "unreal_host_compat_report.json"
    md_path = out_dir / "unreal_host_compat_report.md"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(summarize_markdown(report), encoding="utf-8")
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    return 0 if overall_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
