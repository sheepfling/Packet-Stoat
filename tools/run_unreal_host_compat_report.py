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
DEFAULT_PROBE_PROJECT = ROOT / "examples" / "unreal" / "FastDisOrientationVerification" / "FastDisOrientationVerification.uproject"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--versions", nargs="+", default=["5.6", "5.7", "5.8"], help="Unreal versions to probe")
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

    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "host": detect_host_facts(),
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
