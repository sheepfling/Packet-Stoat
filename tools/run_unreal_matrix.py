#!/usr/bin/env python3
"""Run Unreal plugin/orientation verification across multiple engine versions."""

from __future__ import annotations

import argparse
from datetime import datetime, UTC
import json
from pathlib import Path
import subprocess
import sys

import load_local_env
import unreal_env


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = ROOT / "build" / "reports"


def classify_failure(output: str) -> str | None:
    if (
        "Access to the path '/Users/" in output
        and "Library/Logs/Unreal Engine/LocalBuildLogs" in output
    ) or (
        "Access to the path '/Users/" in output
        and "Library/Application Support/Epic/UnrealBuildTool" in output
    ):
        return "sandbox-home-write-denied"
    if "Platform Mac is not a valid platform to build" in output:
        return "host-mac-platform-unavailable"
    if "A conflicting instance of AutomationTool is already running" in output:
        return "automationtool-conflict"
    if "Could not find an Unreal editor executable" in output:
        return "missing-editor"
    if "Could not locate an Unreal Engine install" in output or "install not discovered" in output:
        return "missing-install"
    return None


def failure_note(failure_kind: str | None) -> str | None:
    if failure_kind == "sandbox-home-write-denied":
        return (
            "managed/sandboxed run denied Unreal writes under ~/Library; "
            "rerun outside the sandbox or provide writable Unreal log/cache paths"
        )
    if failure_kind == "host-mac-platform-unavailable":
        return (
            "host Mac SDK/platform rejected by this engine install before plugin code compiled; "
            "verify the engine/Xcode/macOS compatibility for this Unreal minor"
        )
    if failure_kind == "automationtool-conflict":
        return "another AutomationTool instance was already running on this machine"
    if failure_kind == "missing-editor":
        return "editor executable could not be resolved for this engine lane"
    if failure_kind == "missing-install":
        return "engine install was not discovered for this matrix lane"
    return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--versions", nargs="+", default=["5.6", "5.7", "5.8"], help="Unreal versions to test")
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR), help="Directory for JSON/Markdown reports")
    parser.add_argument("--skip-orientation", action="store_true", help="Only build/package the plugin lane")
    parser.add_argument("--skip-plugin-build", action="store_true", help="Only run the orientation harness")
    parser.add_argument("--skip-demo", action="store_true", help="Skip the replay/demo smoke harness lane")
    return parser.parse_args()


def run_step(cmd: list[str]) -> tuple[int, str]:
    completed = subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    return completed.returncode, completed.stdout


def summarize_markdown(report: dict[str, object]) -> str:
    lines = [
        "# Unreal Version Matrix",
        "",
        f"- generated_at: `{report['generated_at']}`",
        f"- host_platform: `{report['host_platform']}`",
        "",
        "| Version | Discovered | Plugin Build | Orientation | Demo | Notes |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for result in report["results"]:
        discovered = "yes" if result["discovered"] else "no"
        plugin = result["plugin_build"]["status"]
        orientation = result["orientation"]["status"]
        demo = result["demo"]["status"]
        notes = "; ".join(result["notes"]) if result["notes"] else "none"
        lines.append(f"| {result['version']} | {discovered} | {plugin} | {orientation} | {demo} | {notes} |")
    lines.extend([
        "",
        "## Install Quirks",
        "",
    ])
    for result in report["results"]:
        lines.append(f"### {result['version']}")
        install = result.get("install")
        if not install:
            lines.append("- install not discovered")
            continue
        lines.append(f"- install_root: `{install['install_root']}`")
        lines.append(f"- editor_path: `{install['editor_path'] or 'missing'}`")
        lines.append(f"- uat_path: `{install['uat_path'] or 'missing'}`")
        quirks = install.get("quirks") or []
        if quirks:
            for quirk in quirks:
                lines.append(f"- quirk: {quirk}")
        else:
            lines.append("- quirk: none")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    load_local_env.load()
    args = parse_args()
    out_dir = Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    report: dict[str, object] = {
        "generated_at": datetime.now(UTC).isoformat(),
        "host_platform": sys.platform,
        "results": [],
    }

    discovered_by_version = {install.version: install.to_dict() for install in unreal_env.discover_installs()}
    overall_ok = True

    for version in args.versions:
        install = discovered_by_version.get(version)
        result: dict[str, object] = {
            "version": version,
            "discovered": install is not None,
            "install": install,
            "notes": [],
            "plugin_build": {"status": "skipped", "returncode": None, "command": None},
            "orientation": {"status": "skipped", "returncode": None, "command": None},
            "demo": {"status": "skipped", "returncode": None, "command": None},
        }

        if install is None:
            result["notes"].append("install not discovered")
            result["plugin_build"]["status"] = "missing-install"
            result["orientation"]["status"] = "missing-install"
            result["demo"]["status"] = "missing-install"
            report["results"].append(result)
            overall_ok = False
            continue

        if not args.skip_plugin_build:
            cmd = unreal_env.python_command() + [
                "tools/build_unreal_plugin.py",
                "--engine-version",
                version,
                "--clean-package",
            ]
            result["plugin_build"]["command"] = cmd
            code, output = run_step(cmd)
            result["plugin_build"]["returncode"] = code
            result["plugin_build"]["status"] = "passed" if code == 0 else "failed"
            result["plugin_build"]["output"] = output
            if code != 0:
                result["notes"].append("plugin build failed")
                failure_kind = classify_failure(output)
                result["plugin_build"]["failure_kind"] = failure_kind
                note = failure_note(failure_kind)
                if note and note not in result["notes"]:
                    result["notes"].append(note)
                overall_ok = False

        if not args.skip_orientation:
            cmd = unreal_env.python_command() + [
                "tools/run_unreal_orientation_verification.py",
                "--engine-version",
                version,
            ]
            result["orientation"]["command"] = cmd
            code, output = run_step(cmd)
            result["orientation"]["returncode"] = code
            result["orientation"]["status"] = "passed" if code == 0 else "failed"
            result["orientation"]["output"] = output
            if code != 0:
                result["notes"].append("orientation harness failed")
                failure_kind = classify_failure(output)
                result["orientation"]["failure_kind"] = failure_kind
                note = failure_note(failure_kind)
                if note and note not in result["notes"]:
                    result["notes"].append(note)
                overall_ok = False

        if not args.skip_demo:
            cmd = unreal_env.python_command() + [
                "tools/run_unreal_demo_smoke.py",
                "--engine-version",
                version,
            ]
            result["demo"]["command"] = cmd
            code, output = run_step(cmd)
            result["demo"]["returncode"] = code
            result["demo"]["status"] = "passed" if code == 0 else "failed"
            result["demo"]["output"] = output
            if code != 0:
                result["notes"].append("demo smoke failed")
                failure_kind = classify_failure(output)
                result["demo"]["failure_kind"] = failure_kind
                note = failure_note(failure_kind)
                if note and note not in result["notes"]:
                    result["notes"].append(note)
                overall_ok = False

        report["results"].append(result)

    json_path = out_dir / "unreal_version_matrix.json"
    md_path = out_dir / "unreal_version_matrix.md"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(summarize_markdown(report), encoding="utf-8")

    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    return 0 if overall_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
