#!/usr/bin/env python3
"""Materialize a FastDIS Unreal enumeration mapping asset from imported GRILL JSON."""

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
SCRIPT_PATH = ROOT / "tools" / "unreal" / "materialize_fastdis_mapping_asset.py"
ALIAS_ROOT = unreal_harness.ALIAS_ROOT
ALIAS_SCRIPT_PATH = unreal_env.alias_repo_path(SCRIPT_PATH)
DEFAULT_EXAMPLE_ROOT = grill_paths.UNREAL_EXAMPLE
DEFAULT_INPUT_MANIFEST = ROOT / "artifacts" / "reports" / "unreal_grill_swap" / "fastdis_mapping_manifest.json"
DEFAULT_WORK_ROOT = unreal_env.DEFAULT_WORK_ROOT / "grill_unreal_mapping_materialize"
DEFAULT_TEMP_PROJECT_DIR = DEFAULT_WORK_ROOT / "project"
DEFAULT_LOG_DIR = unreal_env.DEFAULT_WORK_ROOT / "logs" / "grill_mapping_materialize"
DEFAULT_LOG_PATH = DEFAULT_LOG_DIR / "GRILLMappingMaterialize.log"
DEFAULT_RESULT_JSON = ROOT / "verification_reports" / "unreal_grill_baseline" / "grill_mapping_materialize.json"
DEFAULT_REPORT_JSON = ROOT / "verification_reports" / "unreal_grill_baseline" / "grill_mapping_materialize_report.json"
DEFAULT_REPORT_MD = ROOT / "verification_reports" / "unreal_grill_baseline" / "grill_mapping_materialize_report.md"
DEFAULT_ASSET_PATH = "/Game/FastDis/DA_ImportedGRILLMappings"
FASTDIS_PLUGIN_ROOT = ROOT / "packages" / "unreal" / "FastDis"
SUCCESS_MARKER = "FASTDIS_GRILL_MAPPING_MATERIALIZE complete"


def _now() -> str:
    return datetime.now(UTC).isoformat()


def resolve_unreal(explicit: str | None, engine_version: str | None) -> str | None:
    path = unreal_env.resolve_editor(engine_version, explicit)
    return str(path) if path else None


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _mount_path(destination: Path, source: Path) -> None:
    try:
        destination.symlink_to(source, target_is_directory=source.is_dir())
    except OSError:
        if source.is_dir():
            shutil.copytree(source, destination)
        else:
            shutil.copy2(source, destination)


def build_temp_project(example_root: Path, temp_project_dir: Path, *, fastdis_plugin_root: Path) -> Path:
    if temp_project_dir.exists():
        shutil.rmtree(temp_project_dir)
    temp_project_dir.mkdir(parents=True, exist_ok=True)

    for name in ("Config", "Content", "Source"):
        source = example_root / name
        if source.exists():
            _mount_path(temp_project_dir / name, source)

    plugins_dir = temp_project_dir / "Plugins"
    plugins_dir.mkdir(parents=True, exist_ok=True)
    example_plugins_dir = example_root / "Plugins"
    if example_plugins_dir.exists():
        for child in sorted(example_plugins_dir.iterdir()):
            _mount_path(plugins_dir / child.name, child)
    _mount_path(plugins_dir / "FastDis", fastdis_plugin_root)

    source_project = sorted(example_root.glob("*.uproject"))
    if not source_project:
        raise FileNotFoundError(f"Could not find .uproject under {example_root}")
    descriptor = _read_json(source_project[0])
    plugins = descriptor.setdefault("Plugins", [])
    plugin_names = {plugin.get("Name") for plugin in plugins if isinstance(plugin, dict)}
    if "PythonScriptPlugin" not in plugin_names:
        plugins.append({"Name": "PythonScriptPlugin", "Enabled": True})
    if "FastDis" not in plugin_names:
        plugins.append({"Name": "FastDis", "Enabled": True})
    project_path = temp_project_dir / "GRILLDISExampleFastDisImport.uproject"
    project_path.write_text(json.dumps(descriptor, indent=2) + "\n", encoding="utf-8")
    return project_path


def build_command(unreal_binary: str, project_path: Path) -> list[str]:
    DEFAULT_LOG_DIR.mkdir(parents=True, exist_ok=True)
    if DEFAULT_LOG_PATH.exists():
        DEFAULT_LOG_PATH.unlink()
    return [
        unreal_binary,
        str(project_path),
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


def unreal_python_log_failed(log_path: Path) -> bool:
    if not log_path.exists():
        return False
    text = log_path.read_text(encoding="utf-8", errors="replace")
    return "Traceback (most recent call last)" in text or "Python script executed with errors" in text


def unreal_python_log_succeeded(log_path: Path) -> bool:
    if not log_path.exists():
        return False
    return SUCCESS_MARKER in log_path.read_text(encoding="utf-8", errors="replace")


def run_editor_until_result(command: list[str], *, cwd: Path, env: dict[str, str], result_json: Path, timeout_seconds: float) -> tuple[int, float]:
    started = time.monotonic()
    completed = subprocess.Popen(command, cwd=cwd, env=env)
    while True:
        rc = completed.poll()
        if rc is not None:
            return rc, round(time.monotonic() - started, 3)
        if result_json.exists():
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
        "# GRILL Unreal Mapping Materialize",
        "",
        f"- generated_at: `{report['generated_at']}`",
        f"- status: `{report['status']}`",
        f"- example_root: `{report.get('example_root')}`",
        f"- project_file: `{report.get('project_file')}`",
        f"- input_manifest: `{report.get('input_manifest')}`",
        f"- asset_path: `{report.get('asset_path')}`",
        f"- result_json: `{report.get('result_json')}`",
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
    parser.add_argument("--input-manifest", type=Path, default=DEFAULT_INPUT_MANIFEST)
    parser.add_argument("--asset-path", default=DEFAULT_ASSET_PATH)
    parser.add_argument("--temp-project-dir", type=Path, default=DEFAULT_TEMP_PROJECT_DIR)
    parser.add_argument("--result-json", type=Path, default=DEFAULT_RESULT_JSON)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_REPORT_JSON)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_REPORT_MD)
    parser.add_argument("--timeout-seconds", type=float, default=300.0)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    load_local_env.load()
    args = parse_args()
    example_root = args.example_root.expanduser().resolve()
    input_manifest = args.input_manifest.expanduser().resolve()
    result_json = args.result_json.expanduser().resolve()
    json_out = args.json_out.expanduser().resolve()
    markdown_out = args.markdown_out.expanduser().resolve()
    report = {
        "schema": "fastdis.grill_unreal_mapping_materialize.v1",
        "generated_at": _now(),
        "status": "dry-run" if args.dry_run else "running",
        "engine_version": args.engine_version,
        "example_root": str(example_root),
        "input_manifest": str(input_manifest),
        "asset_path": args.asset_path,
        "result_json": str(result_json),
        "log_path": str(DEFAULT_LOG_PATH),
        "details": [],
    }

    if not example_root.is_dir():
        report["status"] = "missing-example"
        report["details"].append("GRILL Unreal example checkout not found.")
        write_report(report, json_out, markdown_out)
        return 2

    if not input_manifest.is_file():
        report["status"] = "missing-input"
        report["details"].append("Imported FastDIS mapping manifest not found.")
        write_report(report, json_out, markdown_out)
        return 2

    if not FASTDIS_PLUGIN_ROOT.is_dir():
        report["status"] = "missing-fastdis-plugin"
        report["details"].append("FastDIS Unreal plugin root not found.")
        write_report(report, json_out, markdown_out)
        return 2

    project_path = build_temp_project(example_root, args.temp_project_dir.expanduser().resolve(), fastdis_plugin_root=FASTDIS_PLUGIN_ROOT)
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

    result_json.parent.mkdir(parents=True, exist_ok=True)
    if result_json.exists():
        result_json.unlink()
    env = dict(unreal_env.build_env())
    env["FASTDIS_FASTDIS_MAPPING_JSON"] = str(input_manifest)
    env["FASTDIS_FASTDIS_MAPPING_ASSET_PATH"] = args.asset_path
    env["FASTDIS_FASTDIS_MAPPING_RESULT_JSON"] = str(result_json)
    returncode, elapsed = run_editor_until_result(command, cwd=ALIAS_ROOT, env=env, result_json=result_json, timeout_seconds=args.timeout_seconds)
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
        report["details"].append("Unreal Python materialize route reported errors.")
    elif result_json.exists() and unreal_python_log_succeeded(DEFAULT_LOG_PATH):
        report["status"] = "ok"
        result_payload = _read_json(result_json)
        report["row_count"] = result_payload.get("row_count")
        report["materialized_asset"] = result_payload.get("asset_path")
    elif returncode != 0:
        report["status"] = str(report.get("failure_kind") or "editor-failed")
        if report.get("failure_detail"):
            report["details"].append(str(report["failure_detail"]))
        report["details"].append(f"Unreal exited with code {returncode}.")
    else:
        report["status"] = "missing-result"
        report["details"].append("Unreal completed without writing the expected materialize result JSON.")
    write_report(report, json_out, markdown_out)
    print(f"JSON: {json_out}")
    print(f"Markdown: {markdown_out}")
    print(f"status: {report['status']}")
    return 0 if report["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
