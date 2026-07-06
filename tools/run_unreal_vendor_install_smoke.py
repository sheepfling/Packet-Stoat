#!/usr/bin/env python3
"""Install a packaged vendor Unreal plugin into a clean scratch project and smoke it."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from json import JSONDecodeError
from pathlib import Path
import shutil
import subprocess
import time
from typing import Any

from artifacts import REPORTS_DIR, rel
import load_local_env
import run_unreal_orientation_verification as unreal_harness
import unreal_editor_log
import unreal_env


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "tools" / "unreal" / "verify_vendor_plugin_install.py"
ALIAS_ROOT = unreal_harness.ALIAS_ROOT
ALIAS_SCRIPT_PATH = unreal_env.alias_repo_path(SCRIPT_PATH)
DEFAULT_TIMEOUT_SECONDS = 300.0
DEFAULT_REPORT_GRACE_SECONDS = 5.0
DEFAULT_POLL_INTERVAL_SECONDS = 0.25


def _now() -> str:
    return datetime.now(UTC).isoformat()


def resolve_unreal(explicit: str | None, engine_version: str | None) -> str | None:
    path = unreal_env.resolve_editor(engine_version, explicit)
    return str(path) if path else None


def resolve_package_descriptor(package_dir: Path) -> Path | None:
    matches = sorted(package_dir.glob("*.uplugin"))
    if not matches:
        return None
    if len(matches) > 1:
        raise SystemExit(
            f"Multiple .uplugin files found under {package_dir}: {', '.join(path.name for path in matches)}"
        )
    return matches[0]


def make_project_descriptor(plugin_name: str, project_name: str) -> dict[str, Any]:
    return {
        "FileVersion": 3,
        "EngineAssociation": "",
        "Category": "",
        "Description": f"Scratch project for packaged Unreal plugin install smoke: {plugin_name}.",
        "Modules": [
            {
                "Name": project_name,
                "Type": "Runtime",
                "LoadingPhase": "Default",
            }
        ],
        "Plugins": [
            {"Name": plugin_name, "Enabled": True},
            {"Name": "PythonScriptPlugin", "Enabled": True},
        ],
    }


def create_scratch_project(project_dir: Path, package_dir: Path, plugin_name: str, *, clean: bool) -> Path:
    if clean and project_dir.exists():
        shutil.rmtree(project_dir)
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "Binaries" / "Linux").mkdir(parents=True, exist_ok=True)
    plugins_dir = project_dir / "Plugins"
    plugins_dir.mkdir(parents=True, exist_ok=True)
    project_name = f"{plugin_name}InstallSmoke"
    installed_plugin_dir = plugins_dir / plugin_name
    if installed_plugin_dir.exists():
        shutil.rmtree(installed_plugin_dir)
    shutil.copytree(package_dir, installed_plugin_dir)
    source_dir = project_dir / "Source" / project_name
    source_dir.mkdir(parents=True, exist_ok=True)
    (source_dir / f"{project_name}.Build.cs").write_text(
        "\n".join(
            [
                "using UnrealBuildTool;",
                "",
                f"public class {project_name} : ModuleRules",
                "{",
                f"    public {project_name}(ReadOnlyTargetRules Target) : base(Target)",
                "    {",
                "        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;",
                "        PublicDependencyModuleNames.AddRange(new string[]",
                "        {",
                '            "Core",',
                '            "CoreUObject",',
                '            "Engine",',
                '            "InputCore",',
                "        });",
                "    }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (source_dir / f"{project_name}.cpp").write_text(
        "\n".join(
            [
                '#include "Modules/ModuleManager.h"',
                "",
                f'IMPLEMENT_PRIMARY_GAME_MODULE(FDefaultGameModuleImpl, {project_name}, "{project_name}");',
                "",
            ]
        ),
        encoding="utf-8",
    )
    source_root = project_dir / "Source"
    (source_root / f"{project_name}.Target.cs").write_text(
        "\n".join(
            [
                "using UnrealBuildTool;",
                "using System.Collections.Generic;",
                "",
                f"public class {project_name}Target : TargetRules",
                "{",
                f"    public {project_name}Target(TargetInfo Target) : base(Target)",
                "    {",
                "        Type = TargetType.Game;",
                "        BuildEnvironment = TargetBuildEnvironment.Unique;",
                "        DefaultBuildSettings = BuildSettingsVersion.V5;",
                "        IncludeOrderVersion = EngineIncludeOrderVersion.Unreal5_8;",
                f'        ExtraModuleNames.Add("{project_name}");',
                "    }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (source_root / f"{project_name}Editor.Target.cs").write_text(
        "\n".join(
            [
                "using UnrealBuildTool;",
                "using System.Collections.Generic;",
                "",
                f"public class {project_name}EditorTarget : TargetRules",
                "{",
                f"    public {project_name}EditorTarget(TargetInfo Target) : base(Target)",
                "    {",
                "        Type = TargetType.Editor;",
                "        BuildEnvironment = TargetBuildEnvironment.Unique;",
                "        DefaultBuildSettings = BuildSettingsVersion.V5;",
                "        IncludeOrderVersion = EngineIncludeOrderVersion.Unreal5_8;",
                f'        ExtraModuleNames.Add("{project_name}");',
                "    }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    project_path = project_dir / f"{project_name}.uproject"
    project_path.write_text(
        json.dumps(make_project_descriptor(plugin_name, project_name), indent=2) + "\n",
        encoding="utf-8",
    )
    return project_path


def build_command(unreal_binary: str, project_path: Path, log_path: Path) -> list[str]:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    if log_path.exists():
        log_path.unlink()
    return [
        unreal_binary,
        str(project_path),
        f"-ExecutePythonScript={ALIAS_SCRIPT_PATH}",
        "-unattended",
        "-nop4",
        "-nosplash",
        "-NullRHI",
        "-RenderOffscreen",
        "-NoSound",
        "-stdout",
        "-FullStdOutLogOutput",
        f"-abslog={log_path}",
    ]


def _is_pending_subprocess_artifact(report_path: Path) -> bool:
    if not report_path.exists():
        return False
    try:
        payload = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, JSONDecodeError):
        return False
    return payload.get("schema") == "packet_stoat.pending_subprocess_artifact.v1"


def run_editor_until_report(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
    report_path: Path,
    timeout_seconds: float,
    report_grace_seconds: float,
    baseline_report_mtime: float | None = None,
    poll_interval_seconds: float = DEFAULT_POLL_INTERVAL_SECONDS,
) -> tuple[int, float, bool, bool]:
    started = time.monotonic()
    process = subprocess.Popen(command, cwd=cwd, env=env)
    terminated_after_report = False
    timed_out = False
    returncode: int | None = None
    report_seen_at: float | None = None

    while True:
        returncode = process.poll()
        now = time.monotonic()
        elapsed = round(now - started, 3)
        if returncode is not None:
            return returncode, elapsed, terminated_after_report, timed_out
        report_ready = report_path.exists()
        if report_ready and baseline_report_mtime is not None:
            report_ready = report_path.stat().st_mtime > baseline_report_mtime
        if report_ready and _is_pending_subprocess_artifact(report_path):
            report_ready = False
        if report_ready:
            if report_seen_at is None:
                report_seen_at = now
            elif now - report_seen_at >= report_grace_seconds:
                process.terminate()
                terminated_after_report = True
                try:
                    returncode = process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    returncode = process.wait(timeout=10)
                elapsed = round(time.monotonic() - started, 3)
                return returncode, elapsed, terminated_after_report, timed_out
        if now - started >= timeout_seconds:
            timed_out = True
            process.terminate()
            try:
                returncode = process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                returncode = process.wait(timeout=10)
            elapsed = round(time.monotonic() - started, 3)
            return returncode, elapsed, terminated_after_report, timed_out
        time.sleep(poll_interval_seconds)


def write_report(report: dict[str, Any], json_path: Path, markdown_path: Path) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Unreal Vendor Install Smoke",
        "",
        f"- vendor: `{report['vendor']}`",
        f"- plugin_name: `{report['plugin_name']}`",
        f"- status: `{report['status']}`",
        f"- engine_version: `{report.get('engine_version')}`",
        f"- package_dir: `{report.get('package_dir')}`",
        f"- project_dir: `{report.get('project_dir')}`",
        "",
    ]
    details = report.get("details") or []
    if details:
        lines.extend(["## Details", ""])
        for detail in details:
            lines.append(f"- {detail}")
        lines.append("")
    log_summary = report.get("log_summary")
    if isinstance(log_summary, dict):
        lines.extend(["## Log Summary", "", "```json", json.dumps(log_summary, indent=2), "```", ""])
    markdown_path.write_text("\n".join(lines), encoding="utf-8")


def base_report(
    *,
    vendor: str,
    plugin_name: str,
    engine_version: str | None,
    package_dir: Path,
    project_dir: Path,
    status: str,
    details: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "schema": "packet_stoat.unreal_vendor_install_smoke.v1",
        "generated_at": _now(),
        "vendor": vendor,
        "plugin_name": plugin_name,
        "status": status,
        "engine_version": engine_version,
        "package_dir": rel(package_dir),
        "project_dir": rel(project_dir),
        "details": details or [],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vendor", required=True)
    parser.add_argument("--plugin-name", help="Override plugin name used in the scratch project; defaults to the packaged .uplugin stem")
    parser.add_argument("--unreal", help="Explicit UnrealEditor executable path")
    parser.add_argument("--engine-version", help="Versioned Unreal env selector, for example 5.7 or 5.8")
    parser.add_argument("--package-dir", required=True, help="Packaged plugin directory produced by BuildPlugin")
    parser.add_argument("--project-dir", required=True, help="Scratch clean project directory for install smoke")
    parser.add_argument("--json-out", default=str(REPORTS_DIR / "unreal_vendor_install_smoke.json"))
    parser.add_argument("--markdown-out", default=str(REPORTS_DIR / "unreal_vendor_install_smoke.md"))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--clean-project", action="store_true")
    parser.add_argument("--timeout-seconds", type=float, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("--report-grace-seconds", type=float, default=DEFAULT_REPORT_GRACE_SECONDS)
    parser.add_argument(
        "--editor-project-path",
        help="Optional alternate path passed to Unreal instead of the scratch project_dir; useful when the editor needs the project mounted at a specific container location.",
    )
    return parser.parse_args()


def main() -> int:
    load_local_env.load()
    args = parse_args()
    package_dir = Path(args.package_dir).expanduser().resolve()
    project_dir = Path(args.project_dir).expanduser().resolve()
    editor_project_dir = Path(args.editor_project_path).expanduser().resolve() if args.editor_project_path else project_dir
    json_out = Path(args.json_out).expanduser().resolve()
    markdown_out = Path(args.markdown_out).expanduser().resolve()
    # Keep editor logs next to the persisted reports so container crashes still leave evidence.
    log_dir = json_out.parent / "logs" / "vendor_install_smoke"
    log_path = log_dir / f"{args.vendor}_{args.engine_version or 'default'}.log"

    descriptor = resolve_package_descriptor(package_dir)
    plugin_name = args.plugin_name or (descriptor.stem if descriptor is not None else "UnknownPlugin")

    if not package_dir.exists():
        report = base_report(
            vendor=args.vendor,
            plugin_name=plugin_name,
            engine_version=args.engine_version,
            package_dir=package_dir,
            project_dir=project_dir,
            status="missing-package",
            details=["Packaged plugin directory does not exist. Run the vendor packaging flow first."],
        )
        write_report(report, json_out, markdown_out)
        return 2

    if descriptor is None:
        report = base_report(
            vendor=args.vendor,
            plugin_name=plugin_name,
            engine_version=args.engine_version,
            package_dir=package_dir,
            project_dir=project_dir,
            status="missing-plugin-descriptor",
            details=["No .uplugin descriptor was found in the packaged plugin directory."],
        )
        write_report(report, json_out, markdown_out)
        return 2

    project_path = create_scratch_project(project_dir, package_dir, plugin_name, clean=args.clean_project)
    unreal_binary = resolve_unreal(args.unreal, args.engine_version)
    if unreal_binary is None:
        report = base_report(
            vendor=args.vendor,
            plugin_name=plugin_name,
            engine_version=args.engine_version,
            package_dir=package_dir,
            project_dir=project_dir,
            status="missing-install",
            details=["Could not resolve an Unreal editor executable for this lane."],
        )
        write_report(report, json_out, markdown_out)
        return 3

    editor_project_path = editor_project_dir / project_path.name
    command = build_command(unreal_binary, editor_project_path, log_path)
    report = base_report(
        vendor=args.vendor,
        plugin_name=plugin_name,
        engine_version=args.engine_version,
        package_dir=package_dir,
        project_dir=project_dir,
        status="dry-run" if args.dry_run else "running",
    )
    report["command"] = command
    report["project_file"] = rel(project_path)
    report["installed_plugin_dir"] = rel(project_dir / "Plugins" / plugin_name)
    report["log_path"] = rel(log_path)
    if args.dry_run:
        write_report(report, json_out, markdown_out)
        print(" ".join(command))
        return 0

    env = unreal_env.build_env()
    env["FASTDIS_VENDOR_INSTALL_REPORT"] = str(json_out)
    env["FASTDIS_VENDOR_INSTALL_MARKDOWN"] = str(markdown_out)
    env["FASTDIS_VENDOR_INSTALL_PROJECT_DIR"] = str(project_dir)
    env["FASTDIS_VENDOR_INSTALL_PACKAGE_DIR"] = str(package_dir)
    env["FASTDIS_VENDOR_INSTALL_PLUGIN_NAME"] = plugin_name
    env["FASTDIS_VENDOR_INSTALL_UPLUGIN"] = str(descriptor)
    env["FASTDIS_VENDOR_INSTALL_VENDOR"] = args.vendor
    baseline_report_mtime = json_out.stat().st_mtime if json_out.exists() else None

    returncode, elapsed, terminated_after_report, timed_out = run_editor_until_report(
        command,
        cwd=ALIAS_ROOT,
        env=env,
        report_path=json_out,
        timeout_seconds=args.timeout_seconds,
        report_grace_seconds=args.report_grace_seconds,
        baseline_report_mtime=baseline_report_mtime,
    )
    if not json_out.exists() or _is_pending_subprocess_artifact(json_out):
        log_summary = unreal_editor_log.summarize_editor_failure(log_path)
        report = base_report(
            vendor=args.vendor,
            plugin_name=plugin_name,
            engine_version=args.engine_version,
            package_dir=package_dir,
            project_dir=project_dir,
            status="missing-report",
            details=["Unreal exited without replacing the pending vendor install smoke report."],
        )
        report["command"] = command
        report["returncode"] = returncode
        report["elapsed_seconds"] = elapsed
        report["terminated_after_report"] = terminated_after_report
        report["timed_out"] = timed_out
        report["log_summary"] = log_summary
        if log_summary.get("failure_kind"):
            report["status"] = str(log_summary["failure_kind"])
        write_report(report, json_out, markdown_out)
    else:
        report = json.loads(json_out.read_text(encoding="utf-8"))
        report["command"] = command
        report["returncode"] = returncode
        report["elapsed_seconds"] = elapsed
        report["terminated_after_report"] = terminated_after_report
        report["timed_out"] = timed_out
        log_summary = unreal_editor_log.summarize_editor_failure(log_path)
        report["log_summary"] = log_summary
        if report.get("status") == "pass" and log_summary.get("failure_kind"):
            report["status"] = str(log_summary["failure_kind"])
            details = list(report.get("details") or [])
            note = log_summary.get("detail")
            if note and note not in details:
                details.append(str(note))
            excerpt = log_summary.get("log_excerpt") or []
            if excerpt:
                details.append(str(excerpt[0]))
            report["details"] = details
        write_report(report, json_out, markdown_out)

    successful_statuses = {"pass"}
    final_status = str(report.get("status") or "")
    return 0 if final_status in successful_statuses and (returncode == 0 or terminated_after_report or timed_out) else returncode or 1


if __name__ == "__main__":
    raise SystemExit(main())
