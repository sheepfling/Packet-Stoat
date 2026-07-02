#!/usr/bin/env python3
"""Operator-facing Cesium example-project workflow wrapper."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[3]
TOOLS_DIR = ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import godot_env
import unity_env
import unreal_env


CESIUM_ROOT = ROOT / "external" / "cesium"
PREPARE_COMMAND = "python extensions/cesium/tools/prepare_cesium_source_route.py"
DEFAULT_REPORT_DIR = ROOT / "artifacts" / "reports" / "cesium_examples"

ENGINE_SPECS = {
    "unreal": {
        "surface": "cesium-unreal-example",
        "label": "Cesium Unreal Example",
        "preferred_version": "5.7",
        "supported_versions": ["5.7", "5.8"],
        "plugin_root_env": "FASTDIS_CESIUM_PLUGIN_ROOT",
        "default_plugin_root": CESIUM_ROOT / "cesium-unreal",
        "sample_root": CESIUM_ROOT / "cesium-unreal-samples",
        "example_root": ROOT / "extensions" / "cesium" / "examples" / "unreal" / "CesiumVanillaExample",
        "uproject_name": "CesiumVanillaExample.uproject",
        "vendor_doctor_command": "python tools/unreal_vendor_workflow.py doctor --vendor cesium",
        "vendor_full_command": "python tools/unreal_vendor_workflow.py full --vendor cesium",
        "example_bar": [
            "open a clean Unreal project on the supported lane",
            "enable the Cesium plugin and prove editor open/load",
            "load one geospatial scene with known camera start",
            "keep the project pure Cesium with no FastDIS dependency",
            "capture a report and rerunnable setup note",
        ],
    },
    "unity": {
        "surface": "cesium-unity-example",
        "label": "Cesium Unity Example",
        "preferred_version": "6000.5",
        "supported_versions": ["6000.5"],
        "plugin_root_env": "FASTDIS_CESIUM_UNITY_PLUGIN_ROOT",
        "default_plugin_root": CESIUM_ROOT / "cesium-unity",
        "sample_root": None,
        "example_root": ROOT / "extensions" / "cesium" / "examples" / "unity" / "CesiumVanillaExample",
        "uproject_name": None,
        "project_marker": ROOT / "extensions" / "cesium" / "examples" / "unity" / "CesiumVanillaExample" / "ProjectSettings" / "ProjectVersion.txt",
        "vendor_doctor_command": "python tools/unity_vendor_workflow.py doctor --vendor cesium-unity --unity-version 6000.5",
        "vendor_full_command": "python tools/unity_vendor_workflow.py full --vendor cesium-unity --unity-version 6000.5",
        "example_bar": [
            "open a clean Unity project on the supported lane",
            "install the Cesium Unity package with a documented path",
            "load one geospatial scene with known camera start",
            "keep the project pure Cesium with no FastDIS dependency",
            "capture a report and rerunnable setup note",
        ],
    },
    "godot": {
        "surface": "cesium-godot-example",
        "label": "Cesium Godot Example",
        "preferred_version": "4.7",
        "supported_versions": ["4.7"],
        "plugin_root_env": "FASTDIS_CESIUM_GODOT_PLUGIN_ROOT",
        "default_plugin_root": CESIUM_ROOT / "3D-Tiles-For-Godot",
        "sample_root": None,
        "example_root": ROOT / "extensions" / "cesium" / "examples" / "godot" / "CesiumVanillaExample",
        "uproject_name": None,
        "project_marker": ROOT / "extensions" / "cesium" / "examples" / "godot" / "CesiumVanillaExample" / "project.godot",
        "vendor_doctor_command": "python tools/godot_vendor_workflow.py doctor --vendor cesium-godot",
        "vendor_full_command": "python tools/godot_vendor_workflow.py full --vendor cesium-godot",
        "example_bar": [
            "open a clean Godot project on the supported lane",
            "install the 3D Tiles plugin with a documented path",
            "load one geospatial scene with known camera start",
            "keep the project pure Cesium with no FastDIS dependency",
            "capture a build proof or compile-failure packet from the upstream SCons route",
        ],
    },
}


def resolve_plugin_root(engine: str) -> Path | None:
    spec = ENGINE_SPECS[engine]
    env_value = os.environ.get(spec["plugin_root_env"])
    if env_value:
        return Path(env_value).expanduser().resolve()
    default_root = spec["default_plugin_root"]
    if default_root.is_dir():
        return default_root.resolve()
    return None


def resolve_sample_root(engine: str) -> Path | None:
    sample_root = ENGINE_SPECS[engine]["sample_root"]
    if isinstance(sample_root, Path) and sample_root.is_dir():
        return sample_root.resolve()
    return None


def resolve_example_root(engine: str) -> Path:
    return Path(ENGINE_SPECS[engine]["example_root"]).resolve()


def resolve_example_project_file(engine: str) -> Path | None:
    project_name = ENGINE_SPECS[engine]["uproject_name"]
    if not project_name:
        return None
    return resolve_example_root(engine) / project_name


def resolve_project_marker(engine: str) -> Path | None:
    marker = ENGINE_SPECS[engine].get("project_marker")
    if isinstance(marker, Path):
        return marker.resolve()
    return None


def report_paths(engine: str) -> tuple[Path, Path]:
    prefix = ENGINE_SPECS[engine]["surface"].replace("-", "_")
    return (
        DEFAULT_REPORT_DIR / f"{prefix}.json",
        DEFAULT_REPORT_DIR / f"{prefix}.md",
    )


def workflow_commands(engine: str) -> dict[str, str]:
    return {
        "prepare_source_route": PREPARE_COMMAND,
        "vendor_doctor": str(ENGINE_SPECS[engine]["vendor_doctor_command"]),
        "vendor_full": str(ENGINE_SPECS[engine]["vendor_full_command"]),
        "discover": f"python extensions/cesium/tools/cesium_example_workflow.py discover --engine {engine}",
        "doctor": f"python extensions/cesium/tools/cesium_example_workflow.py doctor --engine {engine}",
        "report": f"python extensions/cesium/tools/cesium_example_workflow.py report --engine {engine}",
        "full": f"python extensions/cesium/tools/cesium_example_workflow.py full --engine {engine}",
    }


def engine_install_found(engine: str) -> bool:
    if engine == "unreal":
        return bool(unreal_env.discover_installs())
    if engine == "unity":
        return unity_env.resolve_install() is not None
    if engine == "godot":
        return bool(godot_env.resolve_godot())
    raise KeyError(engine)


def discover_payload(engine: str) -> dict[str, object]:
    spec = ENGINE_SPECS[engine]
    plugin_root = resolve_plugin_root(engine)
    sample_root = resolve_sample_root(engine)
    json_out, md_out = report_paths(engine)
    return {
        "engine": engine,
        "surface": spec["surface"],
        "preferred_version": spec["preferred_version"],
        "supported_versions": spec["supported_versions"],
        "plugin_root": str(plugin_root) if plugin_root else None,
        "sample_root": str(sample_root) if sample_root else None,
        "example_root": str(resolve_example_root(engine)),
        "example_project": str(resolve_example_project_file(engine)) if resolve_example_project_file(engine) else None,
        "project_marker": str(resolve_project_marker(engine)) if resolve_project_marker(engine) else None,
        "engine_install_found": engine_install_found(engine),
        "workflow_commands": workflow_commands(engine),
        "report_json": str(json_out),
        "report_markdown": str(md_out),
    }


def doctor_payload(engine: str) -> dict[str, object]:
    spec = ENGINE_SPECS[engine]
    plugin_root = resolve_plugin_root(engine)
    sample_root = resolve_sample_root(engine)
    example_root = resolve_example_root(engine)
    example_project = resolve_example_project_file(engine)
    project_marker = resolve_project_marker(engine)
    workflow = workflow_commands(engine)
    json_out, md_out = report_paths(engine)
    checks: list[dict[str, str]] = []
    next_steps: list[str] = []

    def add_check(name: str, ok: bool, detail: str) -> None:
        checks.append({"name": name, "status": "ok" if ok else "fail", "detail": detail})

    add_check(
        "plugin_root",
        plugin_root is not None,
        f"plugin root: {plugin_root}" if plugin_root else f"set {spec['plugin_root_env']} or prepare external/cesium source route",
    )
    if engine == "unreal":
        add_check(
            "sample_root",
            sample_root is not None,
            f"sample root: {sample_root}" if sample_root else "Cesium Unreal samples checkout is optional but recommended for richer example parity work",
        )
        add_check(
            "example_project",
            example_project is not None and example_project.is_file(),
            f"example project: {example_project}" if example_project is not None and example_project.is_file() else f"missing Unreal example project scaffold under {example_root}",
        )
    else:
        add_check(
            "example_root",
            example_root.is_dir(),
            f"example root: {example_root}" if example_root.is_dir() else f"missing example root: {example_root}",
        )
        add_check(
            "project_marker",
            project_marker is not None and project_marker.is_file(),
            f"project marker: {project_marker}" if project_marker is not None and project_marker.is_file() else f"missing project marker under {example_root}",
        )
    has_engine = engine_install_found(engine)
    add_check(
        "engine_install",
        has_engine,
        f"{engine} install discovered" if has_engine else f"no supported {engine} install discovered on this host",
    )

    status = "ok" if all(check["status"] == "ok" for check in checks if check["name"] != "sample_root") else "needs-attention"
    if plugin_root is None:
        next_steps.append(f"Run `{PREPARE_COMMAND}` or set the plugin-root environment variable.")
    if not has_engine:
        next_steps.append(f"Install a supported {engine} engine version for this example lane.")
    next_steps.append(f"Keep the vendor prerequisite green: `{workflow['vendor_full']}`.")
    next_steps.extend(f"Meet example-project bar: {item}." for item in spec["example_bar"])

    return {
        "schema": "packet_stoat.cesium_example_lane.v1",
        "engine": engine,
        "surface": spec["surface"],
        "label": spec["label"],
        "status": status,
        "preferred_version": spec["preferred_version"],
        "supported_versions": spec["supported_versions"],
        "plugin_root": str(plugin_root) if plugin_root else None,
        "sample_root": str(sample_root) if sample_root else None,
        "example_root": str(example_root),
        "example_project": str(example_project) if example_project else None,
        "project_marker": str(project_marker) if project_marker else None,
        "checks": checks,
        "workflow_commands": workflow,
        "example_bar": spec["example_bar"],
        "next_steps": next_steps,
        "report_json": str(json_out),
        "report_markdown": str(md_out),
    }


def report_payload(engine: str) -> dict[str, object]:
    doctor = doctor_payload(engine)
    workflow = dict(doctor["workflow_commands"])
    readiness = {
        "plugin_root_ready": doctor["plugin_root"] is not None,
        "engine_install_ready": any(check["name"] == "engine_install" and check["status"] == "ok" for check in doctor["checks"]),
        "example_scaffold_ready": all(
            check["status"] == "ok"
            for check in doctor["checks"]
            if check["name"] in {"example_project", "example_root", "project_marker"}
        ),
        "sample_root_ready": any(check["name"] == "sample_root" and check["status"] == "ok" for check in doctor["checks"]),
    }
    return {
        "schema": "packet_stoat.cesium_example_report.v1",
        "mode": "report",
        **doctor,
        "status": doctor["status"],
        "workflow_commands": workflow,
        "readiness": readiness,
        "summary": {
            "overall_status": doctor["status"],
            "vendor_prerequisite": workflow["vendor_full"],
            "prepare_source_route": workflow["prepare_source_route"],
            "example_lane_ready": doctor["status"] == "ok",
        },
    }


def full_payload(engine: str) -> dict[str, object]:
    report = report_payload(engine)
    workflow = dict(report["workflow_commands"])
    return {
        **report,
        "schema": "packet_stoat.cesium_example_full.v1",
        "mode": "full",
        "execution_plan": [
            workflow["prepare_source_route"],
            workflow["vendor_full"],
            workflow["doctor"],
            workflow["report"],
        ],
    }


def render_markdown(payload: dict[str, object]) -> str:
    lines = [
        f"# {payload['label']}",
        "",
        f"- engine: `{payload['engine']}`",
        f"- surface: `{payload['surface']}`",
        f"- status: `{payload['status']}`",
        f"- preferred_version: `{payload['preferred_version']}`",
        f"- plugin_root: `{payload.get('plugin_root') or 'missing'}`",
        f"- sample_root: `{payload.get('sample_root') or 'n/a'}`",
        "",
        "## Checks",
        "",
    ]
    for check in payload.get("checks", []):
        lines.append(f"- `{check['name']}`: `{check['status']}`")
        lines.append(f"  detail: `{check['detail']}`")
    lines.extend(["", "## Workflow Commands", ""])
    for key, value in payload.get("workflow_commands", {}).items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Example Bar", ""])
    for item in payload.get("example_bar", []):
        lines.append(f"- {item}")
    lines.extend(["", "## Next Steps", ""])
    for item in payload.get("next_steps", []):
        lines.append(f"- {item}")
    if payload.get("execution_plan"):
        lines.extend(["", "## Full Plan", ""])
        for command in payload["execution_plan"]:
            lines.append(f"- `{command}`")
    return "\n".join(lines) + "\n"


def write_report(payload: dict[str, object], json_out: Path, md_out: Path) -> None:
    json_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    md_out.write_text(render_markdown(payload), encoding="utf-8")


def print_text(payload: dict[str, object]) -> None:
    print(payload["label"])
    print(f"status: {payload['status']}")
    print(f"preferred_version: {payload['preferred_version']}")
    print(f"supported_versions: {', '.join(payload['supported_versions'])}")
    print(f"plugin_root: {payload.get('plugin_root') or 'missing'}")
    print(f"sample_root: {payload.get('sample_root') or 'n/a'}")
    print("checks:")
    for check in payload.get("checks", []):
        print(f"  - {check['name']}: {check['status']} ({check['detail']})")
    print("workflow_commands:")
    for key, value in payload.get("workflow_commands", {}).items():
        print(f"  - {key}: {value}")
    if payload.get("report_json"):
        print(f"report_json: {payload['report_json']}")
    if payload.get("report_markdown"):
        print(f"report_markdown: {payload['report_markdown']}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    for name in ("discover", "doctor", "report", "full"):
        sub = subparsers.add_parser(name)
        sub.add_argument("--engine", choices=sorted(ENGINE_SPECS), required=True)
        sub.add_argument("--format", choices=("text", "json"), default="text")
        if name in {"report", "full"}:
            sub.add_argument("--json-out", type=Path)
            sub.add_argument("--md-out", type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.command == "discover":
        payload = discover_payload(args.engine)
    elif args.command == "doctor":
        payload = doctor_payload(args.engine)
    elif args.command == "report":
        payload = report_payload(args.engine)
        json_out = args.json_out or report_paths(args.engine)[0]
        md_out = args.md_out or report_paths(args.engine)[1]
        write_report(payload, json_out, md_out)
    else:
        payload = full_payload(args.engine)
        json_out = args.json_out or report_paths(args.engine)[0]
        md_out = args.md_out or report_paths(args.engine)[1]
        write_report(payload, json_out, md_out)

    if args.format == "json":
        print(json.dumps(payload, indent=2))
    else:
        print_text(payload)
    return 0 if payload.get("status", "ok") == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
