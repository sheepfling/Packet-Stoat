#!/usr/bin/env python3
"""Export the GRILL Unreal mapping asset to normalized JSON via Unreal Python."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path
import shutil
import subprocess
import time
from typing import Any

import grill_paths
import load_local_env
import run_unreal_orientation_verification as unreal_harness
import unreal_editor_log
import unreal_env


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "tools" / "unreal" / "export_grill_mapping_manifest.py"
ALIAS_ROOT = unreal_harness.ALIAS_ROOT
ALIAS_SCRIPT_PATH = unreal_env.alias_repo_path(SCRIPT_PATH)
DEFAULT_EXAMPLE_ROOT = grill_paths.UNREAL_EXAMPLE
DEFAULT_PLUGIN_ROOT = grill_paths.UNREAL_PLUGIN
DEFAULT_WORK_ROOT = unreal_env.DEFAULT_WORK_ROOT / "grill_unreal_mapping_export"
DEFAULT_TEMP_PROJECT_DIR = DEFAULT_WORK_ROOT / "project"
DEFAULT_LOG_DIR = unreal_env.DEFAULT_WORK_ROOT / "logs" / "grill_mapping_export"
DEFAULT_LOG_PATH = DEFAULT_LOG_DIR / "GRILLMappingExport.log"
DEFAULT_EXPORT_JSON = ROOT / "verification_reports" / "unreal_grill_baseline" / "grill_mapping_export.json"
DEFAULT_REPORT_JSON = ROOT / "verification_reports" / "unreal_grill_baseline" / "grill_mapping_export_report.json"
DEFAULT_REPORT_MD = ROOT / "verification_reports" / "unreal_grill_baseline" / "grill_mapping_export_report.md"
DEFAULT_ASSET_PATH = "/Game/DISEnumerationMappings"
DEFAULT_EDITOR_MAP = "/Engine/Maps/Entry"
SUCCESS_MARKER = "FASTDIS_GRILL_MAPPING_EXPORT complete"
IGNORED_EXAMPLE_TREE_NAMES = {".git", ".vs", "Binaries", "Intermediate", "Saved", "__pycache__"}
IGNORED_PLUGIN_TREE_NAMES = {".git", ".vs", "Intermediate", "Saved", "__pycache__"}
OPTIONAL_SAMPLE_PLUGINS: tuple[str, ...] = ("CesiumForUnreal", "LowEntryExtStdLib")
MINIMAL_CUSTOM_BPFL_HEADER = """// Compatibility-staged for the FastDIS GRILL export lane.

#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "Custom_BPFL.generated.h"

UCLASS()
class GRILLDISEXAMPLE_API UCustom_BPFL : public UBlueprintFunctionLibrary
{
\tGENERATED_BODY()

public:
\tUFUNCTION(BlueprintPure)
\tstatic FString GetCustomConfigVar_String(FString SectionName, FString VariableName, bool& IsValid);
};
"""
MINIMAL_CUSTOM_BPFL_CPP = """// Compatibility-staged for the FastDIS GRILL export lane.

#include "Custom_BPFL.h"

FString UCustom_BPFL::GetCustomConfigVar_String(FString SectionName, FString VariableName, bool& IsValid)
{
\tif (!GConfig)
\t{
\t\tIsValid = false;
\t\treturn TEXT("");
\t}

\tFString Value;
\tIsValid = GConfig->GetString(*SectionName, *VariableName, Value, GGameIni);
\treturn Value;
}
"""


def _now() -> str:
    return datetime.now(UTC).isoformat()


def resolve_unreal(explicit: str | None, engine_version: str | None) -> str | None:
    path = unreal_env.resolve_editor(engine_version, explicit)
    return str(path) if path else None


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def detect_editor_target(project_root: Path, project_path: Path) -> str:
    source_dir = project_root / "Source"
    matches = sorted(source_dir.glob("*Editor.Target.cs"))
    if matches:
        return matches[0].name[: -len(".Target.cs")]
    return f"{project_path.stem}Editor"


def _ignore_example_tree_entries(_: str, names: list[str]) -> set[str]:
    return {name for name in names if name in IGNORED_EXAMPLE_TREE_NAMES}


def _ignore_plugin_tree_entries(_: str, names: list[str]) -> set[str]:
    return {name for name in names if name in IGNORED_PLUGIN_TREE_NAMES}


def _mount_path(destination: Path, source: Path, *, ignore=None) -> None:
    try:
        destination.symlink_to(source, target_is_directory=source.is_dir())
    except OSError:
        if source.is_dir():
            shutil.copytree(source, destination, ignore=ignore)
        else:
            shutil.copy2(source, destination)


def _disable_optional_sample_plugins(project_path: Path, plugin_names: tuple[str, ...]) -> list[str]:
    payload = _read_json(project_path)
    plugins = payload.get("Plugins")
    if not isinstance(plugins, list):
        return []
    disabled: list[str] = []
    optional_names = set(plugin_names)
    changed = False
    for entry in plugins:
        if not isinstance(entry, dict):
            continue
        name = entry.get("Name")
        if not isinstance(name, str) or name not in optional_names:
            continue
        if entry.get("Enabled") is not False:
            entry["Enabled"] = False
            changed = True
        disabled.append(name)
    if changed:
        project_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return disabled


def _remove_optional_plugin_dirs(plugins_dir: Path, plugin_names: tuple[str, ...]) -> list[str]:
    removed: list[str] = []
    for name in plugin_names:
        candidate = plugins_dir / name
        if not candidate.exists():
            continue
        if candidate.is_symlink() or candidate.is_file():
            candidate.unlink()
        else:
            shutil.rmtree(candidate)
        removed.append(name)
    return removed


def _patch_staged_example_for_minimal_route(staged_example_root: Path) -> list[str]:
    modified: list[str] = []
    build_cs = staged_example_root / "Source" / "GRILLDISExample" / "GRILLDISExample.Build.cs"
    if build_cs.is_file():
        text = build_cs.read_text(encoding="utf-8")
        updated_lines = [line for line in text.splitlines() if "CesiumRuntime" not in line]
        updated = "\n".join(updated_lines)
        if text.endswith("\n"):
            updated += "\n"
        if updated != text:
            build_cs.write_text(updated, encoding="utf-8")
            modified.append(str(build_cs))
    custom_header = staged_example_root / "Source" / "GRILLDISExample" / "Custom_BPFL.h"
    if custom_header.is_file():
        custom_header.write_text(MINIMAL_CUSTOM_BPFL_HEADER, encoding="utf-8")
        modified.append(str(custom_header))
    custom_cpp = staged_example_root / "Source" / "GRILLDISExample" / "Custom_BPFL.cpp"
    if custom_cpp.is_file():
        custom_cpp.write_text(MINIMAL_CUSTOM_BPFL_CPP, encoding="utf-8")
        modified.append(str(custom_cpp))
    return modified


def build_temp_project(example_root: Path, temp_project_dir: Path, *, grill_plugin_root: Path = DEFAULT_PLUGIN_ROOT) -> Path:
    if temp_project_dir.exists():
        shutil.rmtree(temp_project_dir)
    temp_project_dir.mkdir(parents=True, exist_ok=True)

    for name in ("Config", "Content", "Source"):
        source = example_root / name
        if source.exists():
            _mount_path(temp_project_dir / name, source, ignore=_ignore_example_tree_entries)

    plugins_dir = temp_project_dir / "Plugins"
    plugins_dir.mkdir(parents=True, exist_ok=True)
    example_plugins_dir = example_root / "Plugins"
    embedded_plugin_name = "DISPluginForUnreal" if (example_plugins_dir / "DISPluginForUnreal").exists() else grill_plugin_root.name
    if example_plugins_dir.exists():
        for child in sorted(example_plugins_dir.iterdir()):
            if child.name == embedded_plugin_name:
                continue
            _mount_path(plugins_dir / child.name, child, ignore=_ignore_plugin_tree_entries)
    if grill_plugin_root.exists():
        _mount_path(plugins_dir / embedded_plugin_name, grill_plugin_root, ignore=_ignore_plugin_tree_entries)

    source_project = sorted(example_root.glob("*.uproject"))
    if not source_project:
        raise FileNotFoundError(f"Could not find .uproject under {example_root}")
    descriptor = _read_json(source_project[0])
    plugins = descriptor.setdefault("Plugins", [])
    plugin_names = {plugin.get("Name") for plugin in plugins if isinstance(plugin, dict)}
    if "PythonScriptPlugin" not in plugin_names:
        plugins.append({"Name": "PythonScriptPlugin", "Enabled": True})
    project_path = temp_project_dir / "GRILLDISExampleExport.uproject"
    project_path.write_text(json.dumps(descriptor, indent=2) + "\n", encoding="utf-8")
    _disable_optional_sample_plugins(project_path, OPTIONAL_SAMPLE_PLUGINS)
    _remove_optional_plugin_dirs(plugins_dir, OPTIONAL_SAMPLE_PLUGINS)
    _patch_staged_example_for_minimal_route(temp_project_dir)
    return project_path


def build_command(unreal_binary: str, project_path: Path) -> list[str]:
    DEFAULT_LOG_DIR.mkdir(parents=True, exist_ok=True)
    if DEFAULT_LOG_PATH.exists():
        DEFAULT_LOG_PATH.unlink()
    return [
        unreal_binary,
        str(project_path),
        DEFAULT_EDITOR_MAP,
        f"-ExecutePythonScript={ALIAS_SCRIPT_PATH}",
        "-unattended",
        "-nop4",
        "-nosplash",
        "-NullRHI",
        "-NoSound",
        "-stdout",
        "-FullStdOutLogOutput",
        f"-abslog={DEFAULT_LOG_PATH}",
    ]


def ensure_project_built(project_root: Path, project_path: Path, engine_version: str | None) -> tuple[list[str], str]:
    install = unreal_env.describe_install(engine_version)
    if install is None or not install.get("ubt_path") or not install.get("dotnet_path"):
        version_label = engine_version or "default"
        raise RuntimeError(f"Could not find UnrealBuildTool or bundled dotnet for engine version {version_label}")

    unreal_env.clear_generated_state(project_path)
    target_name = detect_editor_target(project_root, project_path)
    command = [
        str(install["dotnet_path"]),
        str(install["ubt_path"]),
        target_name,
        unreal_env.platform_dir_name(),
        "Development",
        f"-project={project_path}",
        "-waitmutex",
        "-NoHotReloadFromIDE",
    ]
    completed = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=unreal_env.build_env(),
    )
    output = completed.stdout or ""
    if completed.returncode != 0:
        raise RuntimeError(output.strip() or f"UnrealBuildTool failed with exit code {completed.returncode}")
    return command, output


def unreal_python_log_failed(log_path: Path) -> bool:
    if not log_path.exists():
        return False
    text = log_path.read_text(encoding="utf-8", errors="replace")
    return "Traceback (most recent call last)" in text or "Python script executed with errors" in text


def unreal_python_log_succeeded(log_path: Path) -> bool:
    if not log_path.exists():
        return False
    return SUCCESS_MARKER in log_path.read_text(encoding="utf-8", errors="replace")


def run_editor_until_export(command: list[str], *, cwd: Path, env: dict[str, str], export_json: Path, timeout_seconds: float) -> tuple[int, float]:
    started = time.monotonic()
    completed = subprocess.Popen(command, cwd=cwd, env=env)
    while True:
        rc = completed.poll()
        if rc is not None:
            return rc, round(time.monotonic() - started, 3)
        if export_json.exists():
            completed.terminate()
            try:
                rc = completed.wait(timeout=10)
            except subprocess.TimeoutExpired:
                completed.kill()
                rc = completed.wait(timeout=10)
            return rc, round(time.monotonic() - started, 3)
        if time.monotonic() - started >= timeout_seconds:
            completed.terminate()
            try:
                rc = completed.wait(timeout=10)
            except subprocess.TimeoutExpired:
                completed.kill()
                rc = completed.wait(timeout=10)
            return rc, round(time.monotonic() - started, 3)
        time.sleep(0.25)


def write_report(report: dict[str, Any], json_path: Path, markdown_path: Path) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# GRILL Unreal Mapping Export",
        "",
        f"- generated_at: `{report['generated_at']}`",
        f"- status: `{report['status']}`",
        f"- example_root: `{report.get('example_root')}`",
        f"- project_file: `{report.get('project_file')}`",
        f"- asset_path: `{report.get('asset_path')}`",
        f"- export_json: `{report.get('export_json')}`",
        f"- log_path: `{report.get('log_path')}`",
        "",
    ]
    details = report.get("details") or []
    if details:
        lines.extend(["## Details", ""])
        for detail in details:
            lines.append(f"- {detail}")
        lines.append("")
    if report.get("failure_kind"):
        lines.extend(["## Failure Kind", "", f"- failure_kind: `{report['failure_kind']}`"])
        if report.get("failure_detail"):
            lines.append(f"- failure_detail: `{report['failure_detail']}`")
        lines.append("")
    excerpts = report.get("log_excerpt") or []
    if excerpts:
        lines.extend(["## Log Excerpt", ""])
        for excerpt in excerpts:
            lines.append(f"- `{excerpt}`")
        lines.append("")
    if report.get("command"):
        lines.extend(["## Command", "", "```text", " ".join(report["command"]), "```", ""])
    markdown_path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--unreal", help="Explicit UnrealEditor executable path")
    parser.add_argument("--engine-version", help="Versioned Unreal env selector, for example 5.7 or 5.8")
    parser.add_argument("--example-root", type=Path, default=DEFAULT_EXAMPLE_ROOT)
    parser.add_argument("--asset-path", default=DEFAULT_ASSET_PATH)
    parser.add_argument("--temp-project-dir", type=Path, default=DEFAULT_TEMP_PROJECT_DIR)
    parser.add_argument("--export-json", type=Path, default=DEFAULT_EXPORT_JSON)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_REPORT_JSON)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_REPORT_MD)
    parser.add_argument("--timeout-seconds", type=float, default=300.0)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    load_local_env.load()
    args = parse_args()
    example_root = args.example_root.expanduser().resolve()
    export_json = args.export_json.expanduser().resolve()
    json_out = args.json_out.expanduser().resolve()
    markdown_out = args.markdown_out.expanduser().resolve()
    report = {
        "schema": "fastdis.grill_unreal_mapping_export.v1",
        "generated_at": _now(),
        "status": "dry-run" if args.dry_run else "running",
        "engine_version": args.engine_version,
        "example_root": str(example_root),
        "asset_path": args.asset_path,
        "export_json": str(export_json),
        "log_path": str(DEFAULT_LOG_PATH),
        "details": [],
    }

    if not example_root.is_dir():
        report["status"] = "missing-example"
        report["details"].append("GRILL Unreal example checkout not found.")
        write_report(report, json_out, markdown_out)
        return 2

    project_path = build_temp_project(
        example_root,
        args.temp_project_dir.expanduser().resolve(),
        grill_plugin_root=DEFAULT_PLUGIN_ROOT,
    )
    report["project_file"] = str(project_path)
    unreal_binary = resolve_unreal(args.unreal, args.engine_version)
    if unreal_binary is None:
        report["status"] = "missing-install"
        report["details"].append("Could not resolve an Unreal editor executable for this lane.")
        write_report(report, json_out, markdown_out)
        return 3

    command = build_command(unreal_binary, project_path)
    report["command"] = command
    write_report(report, json_out, markdown_out)
    print(" ".join(command))
    if args.dry_run:
        return 0

    try:
        prebuild_command, prebuild_output = ensure_project_built(project_path.parent, project_path, args.engine_version)
    except RuntimeError as exc:
        report["status"] = "build-failed"
        report["failure_kind"] = "build-failed"
        report["failure_detail"] = str(exc)
        report["details"].append("UnrealBuildTool could not compile the staged GRILL example editor target.")
        write_report(report, json_out, markdown_out)
        return 1
    report["prebuild_command"] = prebuild_command
    if prebuild_output.strip():
        report["prebuild_output_excerpt"] = prebuild_output.strip().splitlines()[-20:]

    export_json.parent.mkdir(parents=True, exist_ok=True)
    if export_json.exists():
        export_json.unlink()
    env = dict(unreal_env.build_env())
    env["FASTDIS_GRILL_MAPPING_ASSET"] = args.asset_path
    env["FASTDIS_GRILL_EXPORT_JSON"] = str(export_json)
    returncode, elapsed = run_editor_until_export(command, cwd=ALIAS_ROOT, env=env, export_json=export_json, timeout_seconds=args.timeout_seconds)
    report["elapsed_seconds"] = elapsed
    failure_summary = unreal_editor_log.summarize_editor_failure(DEFAULT_LOG_PATH)
    if failure_summary["failure_kind"]:
        report["failure_kind"] = failure_summary["failure_kind"]
    if failure_summary["detail"]:
        report["failure_detail"] = failure_summary["detail"]
    if failure_summary["log_excerpt"]:
        report["log_excerpt"] = failure_summary["log_excerpt"]
    if unreal_python_log_failed(DEFAULT_LOG_PATH):
        report["status"] = "python-failed"
        report["details"].append("Unreal Python export reported errors.")
    elif export_json.exists() and unreal_python_log_succeeded(DEFAULT_LOG_PATH):
        report["status"] = "ok"
        exported = _read_json(export_json)
        report["row_count"] = len(exported.get("rows", []))
    elif returncode != 0:
        report["status"] = str(report.get("failure_kind") or "editor-failed")
        if report.get("failure_detail"):
            report["details"].append(str(report["failure_detail"]))
        report["details"].append(f"Unreal exited with code {returncode}.")
    else:
        report["status"] = "missing-export"
        report["details"].append("Unreal completed without writing the expected export JSON.")
    write_report(report, json_out, markdown_out)
    print(f"JSON: {json_out}")
    print(f"Markdown: {markdown_out}")
    print(f"status: {report['status']}")
    return 0 if report["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
