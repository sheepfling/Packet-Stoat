#!/usr/bin/env python3
"""Operator-facing Cesium example-project workflow wrapper."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[3]
TOOLS_DIR = ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import godot_env  # noqa: E402
import godot_vendor_workflow  # noqa: E402
import run_unity_editor_tests  # noqa: E402
import unity_env  # noqa: E402
import unity_vendor_workflow  # noqa: E402
import unreal_env  # noqa: E402
import unreal_vendor_workflow  # noqa: E402

try:  # noqa: E402
    import capture_unreal_cesium_example_views  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - optional Windows helper
    from types import SimpleNamespace

    def _capture_report_unavailable(**_kwargs: object) -> dict[str, object]:
        raise RuntimeError("capture_unreal_cesium_example_views helper is unavailable in this checkout")

    capture_unreal_cesium_example_views = SimpleNamespace(capture_report=_capture_report_unavailable)


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

UNITY_PROJECT_DEPENDENCIES: dict[str, str] = {
    "com.unity.collab-proxy": "2.7.1",
    "com.unity.feature.development": "1.0.2",
    "com.unity.ide.rider": "3.0.36",
    "com.unity.ide.visualstudio": "2.0.23",
    "com.unity.inputsystem": "1.14.2",
    "com.unity.modules.imageconversion": "1.0.0",
    "com.unity.modules.unitywebrequest": "1.0.0",
    "com.unity.modules.unitywebrequesttexture": "1.0.0",
    "com.unity.test-framework": "1.6.4",
    "com.unity.textmeshpro": "3.2.0-pre.10",
    "com.unity.timeline": "1.8.7",
    "com.unity.ugui": "2.0.0",
    "com.unity.visualscripting": "1.9.9",
}

PROOF_VIEW_CONTRACT: tuple[dict[str, object], ...] = (
    {
        "name": "orbital_nadir",
        "label": "Orbital Nadir",
        "description": "High-altitude proof image looking down toward the ellipsoid to prove globe-scale rendering.",
        "camera_mode": "nadir",
        "expected_altitude_m": 2_000_000.0,
    },
    {
        "name": "low_altitude_horizon",
        "label": "Low Altitude Horizon",
        "description": "Approximately 1000m-above-surface proof image looking near-horizontal to prove local horizon rendering.",
        "camera_mode": "horizon",
        "expected_altitude_m": 1_000.0,
    },
)


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _json_dump(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _prime_subprocess_json_artifact(path: Path, *, owner: str) -> None:
    _json_dump(
        path,
        {
            "schema": "packet_stoat.pending_subprocess_artifact.v1",
            "owner": owner,
            "generated_at": _now(),
            "status": "pending",
            "detail": "Reserved before launching subprocess so stale prior output cannot be mistaken for a fresh report.",
        },
    )


def _prime_subprocess_text_artifact(path: Path, *, owner: str) -> None:
    _write_text(
        path,
        "\n".join(
            [
                "# Pending Subprocess Artifact",
                "",
                f"- owner: `{owner}`",
                f"- generated_at: `{_now()}`",
                "- status: `pending`",
                "- detail: `Reserved before launching subprocess so stale prior output cannot be mistaken for a fresh report.`",
                "",
            ]
        ),
    )


def _prime_subprocess_report_outputs(json_path: Path, md_path: Path, *, owner: str) -> None:
    _prime_subprocess_json_artifact(json_path, owner=owner)
    _prime_subprocess_text_artifact(md_path, owner=owner)


def _load_json_if_fresh(path: Path) -> dict[str, object]:
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema") == "packet_stoat.pending_subprocess_artifact.v1":
        return {}
    return payload


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


def smoke_report_paths(engine: str) -> tuple[Path, Path]:
    prefix = ENGINE_SPECS[engine]["surface"].replace("-", "_")
    return (
        DEFAULT_REPORT_DIR / f"{prefix}_smoke.json",
        DEFAULT_REPORT_DIR / f"{prefix}_smoke.md",
    )


def proof_view_report_paths(engine: str) -> tuple[Path, Path]:
    prefix = ENGINE_SPECS[engine]["surface"].replace("-", "_")
    return (
        DEFAULT_REPORT_DIR / f"{prefix}_proof_view.json",
        DEFAULT_REPORT_DIR / f"{prefix}_proof_view.md",
    )


def versioned_smoke_report_paths(engine: str, version: str | None) -> tuple[Path, Path]:
    base_json, base_md = smoke_report_paths(engine)
    if engine != "unreal" or not version:
        return base_json, base_md
    suffix = version.replace(".", "_")
    return (
        base_json.with_name(f"{base_json.stem}_{suffix}{base_json.suffix}"),
        base_md.with_name(f"{base_md.stem}_{suffix}{base_md.suffix}"),
    )


def versioned_proof_view_report_paths(engine: str, version: str | None) -> tuple[Path, Path]:
    base_json, base_md = proof_view_report_paths(engine)
    if engine != "unreal" or not version:
        return base_json, base_md
    suffix = version.replace(".", "_")
    return (
        base_json.with_name(f"{base_json.stem}_{suffix}{base_json.suffix}"),
        base_md.with_name(f"{base_md.stem}_{suffix}{base_md.suffix}"),
    )


def workflow_commands(engine: str) -> dict[str, str]:
    return {
        "prepare_source_route": PREPARE_COMMAND,
        "vendor_doctor": str(ENGINE_SPECS[engine]["vendor_doctor_command"]),
        "vendor_full": str(ENGINE_SPECS[engine]["vendor_full_command"]),
        "discover": f"python extensions/cesium/tools/cesium_example_workflow.py discover --engine {engine}",
        "doctor": f"python extensions/cesium/tools/cesium_example_workflow.py doctor --engine {engine}",
        "report": f"python extensions/cesium/tools/cesium_example_workflow.py report --engine {engine}",
        "smoke": f"python extensions/cesium/tools/cesium_example_workflow.py smoke --engine {engine}",
        "proof_view": f"python extensions/cesium/tools/cesium_example_workflow.py proof-view --engine {engine}",
        "full": f"python extensions/cesium/tools/cesium_example_workflow.py full --engine {engine}",
    }


def proof_view_contract(engine: str) -> list[dict[str, object]]:
    return [
        {
            **view,
            "engine": engine,
            "surface": ENGINE_SPECS[engine]["surface"],
        }
        for view in PROOF_VIEW_CONTRACT
    ]


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
    smoke_json, smoke_md = smoke_report_paths(engine)
    proof_json, proof_md = proof_view_report_paths(engine)
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
        "smoke_report_json": str(smoke_json),
        "smoke_report_markdown": str(smoke_md),
        "proof_view_report_json": str(proof_json),
        "proof_view_report_markdown": str(proof_md),
        "proof_view_contract": proof_view_contract(engine),
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
    smoke_json, smoke_md = smoke_report_paths(engine)
    proof_json, proof_md = proof_view_report_paths(engine)
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
    next_steps.append(f"Run `{workflow['smoke']}` once the host prerequisites are in place.")
    next_steps.append(f"Run `{workflow['proof_view']}` to capture the two required visual proof angles.")
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
        "smoke_report_json": str(smoke_json),
        "smoke_report_markdown": str(smoke_md),
        "proof_view_report_json": str(proof_json),
        "proof_view_report_markdown": str(proof_md),
        "proof_view_contract": proof_view_contract(engine),
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
            workflow["smoke"],
            workflow["proof_view"],
            workflow["report"],
        ],
    }


def _copy_example_scaffold(engine: str, destination: Path) -> Path:
    source = resolve_example_root(engine)
    if destination.exists():
        if engine == "unreal":
            unreal_vendor_workflow.remove_tree(destination)
        else:
            unity_vendor_workflow.remove_tree(destination)
    shutil.copytree(source, destination)
    return destination


def _unity_smoke_project_dir() -> Path:
    return unity_env.work_root() / "cesium_examples" / "unity" / "CesiumVanillaExample"


def _unreal_smoke_project_dir(version: str) -> Path:
    return unreal_env.work_root() / f"ceu_{version.replace('.', '_')}" / "proj"


def _godot_smoke_project_dir() -> Path:
    return godot_env.work_root() / "cesium_examples" / "godot" / "CesiumVanillaExample"


def _update_unity_manifest(project_dir: Path, package_root: Path) -> None:
    manifest_path = project_dir / "Packages" / "manifest.json"
    payload = {"dependencies": dict(UNITY_PROJECT_DEPENDENCIES)}
    payload["dependencies"][unity_vendor_workflow.PACKAGE_NAME] = unity_vendor_workflow._package_file_reference(package_root, project_dir)
    _write_text(manifest_path, json.dumps(payload, indent=2) + "\n")


def _write_unity_smoke_runner(project_dir: Path) -> Path:
    script_path = project_dir / "Assets" / "Editor" / "CesiumVanillaExampleSmoke.cs"
    _write_text(
        script_path,
        """
using System;
using System.IO;
using CesiumForUnity;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

public static class CesiumVanillaExampleSmoke
{
    public static void Run()
    {
        string reportPath = GetArgument("-fastdisReportPath");
        string scenePath = "Assets/Scenes/CesiumVanillaEntry.unity";
        Directory.CreateDirectory(Path.GetDirectoryName(scenePath));

        bool packageImported = Type.GetType("CesiumForUnity.CesiumGeoreference, CesiumForUnity") != null;
        bool sceneCreated = false;
        bool componentCreated = false;

        if (packageImported)
        {
            Scene scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            GameObject root = new GameObject("Cesium Vanilla Root");
            CesiumGeoreference georeference = root.AddComponent<CesiumGeoreference>();
            componentCreated = georeference != null;
            sceneCreated = EditorSceneManager.SaveScene(scene, scenePath);
            AssetDatabase.Refresh();
        }

        string json = "{\\n"
            + "  \\"status\\": \\"" + (packageImported && componentCreated && sceneCreated ? "pass" : "fail") + "\\",\\n"
            + "  \\"package_imported\\": " + (packageImported ? "true" : "false") + ",\\n"
            + "  \\"component_created\\": " + (componentCreated ? "true" : "false") + ",\\n"
            + "  \\"scene_created\\": " + (sceneCreated ? "true" : "false") + ",\\n"
            + "  \\"scene_path\\": \\"" + scenePath + "\\"\\n"
            + "}\\n";

        if (!string.IsNullOrEmpty(reportPath))
        {
            File.WriteAllText(reportPath, json);
        }

        EditorApplication.Exit(packageImported && componentCreated && sceneCreated ? 0 : 3);
    }

    private static string GetArgument(string name)
    {
        string[] args = Environment.GetCommandLineArgs();
        for (int i = 0; i < args.Length - 1; i++)
        {
            if (args[i] == name)
            {
                return args[i + 1];
            }
        }
        return string.Empty;
    }
}
""".strip()
        + "\n",
    )
    return script_path


def _unity_smoke_command(editor: str, project_dir: Path, log_path: Path, report_path: Path) -> list[str]:
    command = [editor]
    command.extend(["-batchmode", *run_unity_editor_tests.unity_graphics_args()])
    command.extend(
        [
            "-accept-apiupdate",
            "-quit",
            "-projectPath",
            str(project_dir),
            "-executeMethod",
            "CesiumVanillaExampleSmoke.Run",
            "-fastdisReportPath",
            str(report_path),
            "-logFile",
            str(log_path),
        ]
    )
    return command


def _run_unity_smoke(*, json_out: Path, md_out: Path, dry_run: bool) -> dict[str, object]:
    doctor = doctor_payload("unity")
    plugin_root = resolve_plugin_root("unity")
    install = unity_env.resolve_install(ENGINE_SPECS["unity"]["preferred_version"])
    project_dir = _unity_smoke_project_dir()
    log_path = unity_env.work_root() / "logs" / "cesium_examples" / "unity_smoke.log"
    live_report = unity_env.work_root() / "reports" / "cesium_examples" / "unity_smoke_live.json"

    if plugin_root is None or install is None:
        payload = {
            "schema": "packet_stoat.cesium_example_smoke.v1",
            "engine": "unity",
            "surface": ENGINE_SPECS["unity"]["surface"],
            "label": ENGINE_SPECS["unity"]["label"],
            "status": "needs-attention",
            "generated_at": _now(),
            "detail": "Unity example smoke requires both a Cesium Unity plugin root and a discovered Unity 6000.5 editor.",
            "checks": doctor["checks"],
            "workflow_commands": workflow_commands("unity"),
            "report_json": str(json_out),
            "report_markdown": str(md_out),
        }
        write_report(payload, json_out, md_out)
        return payload

    _copy_example_scaffold("unity", project_dir)
    package_root, touched = unity_vendor_workflow.stage_plugin_root(project_dir, plugin_root)
    _update_unity_manifest(project_dir, package_root)
    _write_unity_smoke_runner(project_dir)
    command = _unity_smoke_command(str(install.editor_path), project_dir, log_path, live_report)

    if dry_run:
        payload = {
            "schema": "packet_stoat.cesium_example_smoke.v1",
            "engine": "unity",
            "surface": ENGINE_SPECS["unity"]["surface"],
            "label": ENGINE_SPECS["unity"]["label"],
            "status": "dry-run",
            "generated_at": _now(),
            "unity_version": install.version,
            "plugin_root": str(plugin_root),
            "project_dir": str(project_dir),
            "staged_package_root": str(package_root),
            "touched_reinterop_sources": touched,
            "command": command,
            "log": str(log_path),
            "live_report": str(live_report),
            "report_json": str(json_out),
            "report_markdown": str(md_out),
        }
        write_report(payload, json_out, md_out)
        return payload

    log_path.parent.mkdir(parents=True, exist_ok=True)
    live_report.parent.mkdir(parents=True, exist_ok=True)
    if log_path.exists():
        log_path.unlink()
    _prime_subprocess_json_artifact(live_report, owner="cesium_example_workflow:unity")

    completed = subprocess.run(command, cwd=ROOT, env=unity_env.build_env(), capture_output=False, check=False)
    raw = _load_json_if_fresh(live_report)
    payload = {
        "schema": "packet_stoat.cesium_example_smoke.v1",
        "engine": "unity",
        "surface": ENGINE_SPECS["unity"]["surface"],
        "label": ENGINE_SPECS["unity"]["label"],
        "status": raw.get("status", "pass" if completed.returncode == 0 else "fail"),
        "generated_at": _now(),
        "unity_version": install.version,
        "plugin_root": str(plugin_root),
        "project_dir": str(project_dir),
        "staged_package_root": str(package_root),
        "touched_reinterop_sources": touched,
        "command": command,
        "returncode": completed.returncode,
        "log": str(log_path),
        "live_report": str(live_report),
        "checks": [
            {"name": "package_imported", "status": "ok" if raw.get("package_imported") else "fail", "detail": str(raw.get("package_imported"))},
            {"name": "component_created", "status": "ok" if raw.get("component_created") else "fail", "detail": str(raw.get("component_created"))},
            {"name": "scene_created", "status": "ok" if raw.get("scene_created") else "fail", "detail": str(raw.get("scene_path") or "Assets/Scenes/CesiumVanillaEntry.unity")},
        ],
        "detail": "Unity example smoke completed." if completed.returncode == 0 else "Unity example smoke failed; inspect the Unity log and live report.",
        "report_json": str(json_out),
        "report_markdown": str(md_out),
    }
    write_report(payload, json_out, md_out)
    return payload


def _unreal_smoke_report_from_install(report: dict[str, object], json_out: Path, md_out: Path) -> dict[str, object]:
    payload = {
        "schema": "packet_stoat.cesium_example_smoke.v1",
        "engine": "unreal",
        "surface": ENGINE_SPECS["unreal"]["surface"],
        "label": ENGINE_SPECS["unreal"]["label"],
        "status": report.get("status", "fail"),
        "generated_at": _now(),
        "detail": report.get("details", ["Unreal example smoke completed."])[0] if report.get("details") else "Unreal example smoke completed.",
        "checks": report.get("checks", []),
        "command": report.get("command"),
        "project_dir": report.get("project_dir"),
        "package_dir": report.get("package_dir"),
        "engine_version": report.get("engine_version"),
        "json_out": str(json_out),
        "md_out": str(md_out),
        "vendor_report_json": report.get("json_out"),
        "vendor_report_markdown": report.get("md_out"),
    }
    write_report(payload, json_out, md_out)
    return payload


def _resolve_unreal_packaged_plugin_dir(package_root: Path, descriptor_stem: str) -> Path:
    direct = package_root / f"{descriptor_stem}.uplugin"
    if direct.is_file():
        return package_root
    host_project_plugin = package_root / "HostProject" / "Plugins" / descriptor_stem
    if (host_project_plugin / f"{descriptor_stem}.uplugin").is_file():
        return host_project_plugin
    return package_root


def _stage_unreal_packaged_plugin(package_dir: Path, version: str, descriptor_stem: str) -> Path:
    staged_dir = unreal_env.work_root() / f"ceu_{version.replace('.', '_')}" / "pkg" / descriptor_stem
    if staged_dir.exists():
        shutil.rmtree(staged_dir)
    ignore = shutil.ignore_patterns(".git", "Intermediate", "Saved", "build-fastdis", "extern")
    shutil.copytree(package_dir, staged_dir, ignore=ignore)
    return staged_dir


def _run_unreal_smoke(*, json_out: Path, md_out: Path, dry_run: bool, engine_version: str | None) -> dict[str, object]:
    version = engine_version or ENGINE_SPECS["unreal"]["preferred_version"]
    doctor = doctor_payload("unreal")
    plugin_root = resolve_plugin_root("unreal")
    example_project_dir = _unreal_smoke_project_dir(version)
    packaged_root: Path | None = None
    descriptor = unreal_vendor_workflow.resolve_uplugin_path("cesium", plugin_root, None) if plugin_root is not None else None
    if descriptor is not None:
        packaged_root = unreal_vendor_workflow.default_package_dir("cesium", descriptor, version)
    if plugin_root is None or descriptor is None or packaged_root is None:
        payload = {
            "schema": "packet_stoat.cesium_example_smoke.v1",
            "engine": "unreal",
            "surface": ENGINE_SPECS["unreal"]["surface"],
            "label": ENGINE_SPECS["unreal"]["label"],
            "status": "needs-attention",
            "generated_at": _now(),
            "detail": "Unreal example smoke requires a Cesium plugin root and resolvable .uplugin descriptor.",
            "checks": doctor["checks"],
            "workflow_commands": workflow_commands("unreal"),
            "report_json": str(json_out),
            "report_markdown": str(md_out),
        }
        write_report(payload, json_out, md_out)
        return payload

    _copy_example_scaffold("unreal", example_project_dir)
    packaged_plugin_dir = _resolve_unreal_packaged_plugin_dir(packaged_root, descriptor.stem)
    staged_package_dir = _stage_unreal_packaged_plugin(packaged_plugin_dir, version, descriptor.stem)
    json_vendor = json_out.parent / f"{json_out.stem}_vendor.json"
    md_vendor = md_out.parent / f"{md_out.stem}_vendor.md"
    _prime_subprocess_report_outputs(
        json_vendor,
        md_vendor,
        owner=f"cesium_example_workflow:unreal:{version}",
    )
    command = unreal_vendor_workflow.install_smoke_report_payload(
        vendor="cesium",
        version=version,
        plugin_root_arg=str(plugin_root),
        uplugin_arg=str(descriptor),
        package_dir_arg=str(staged_package_dir),
        project_dir_arg=str(example_project_dir),
        json_out_arg=str(json_vendor),
        md_out_arg=str(md_vendor),
        clean_project=False,
        dry_run=dry_run,
    )
    if dry_run:
        payload = {
            "schema": "packet_stoat.cesium_example_smoke.v1",
            "engine": "unreal",
            "surface": ENGINE_SPECS["unreal"]["surface"],
            "label": ENGINE_SPECS["unreal"]["label"],
            "status": "dry-run",
            "generated_at": _now(),
            "engine_version": version,
            "plugin_root": str(plugin_root),
            "project_dir": str(example_project_dir),
            "package_dir": str(staged_package_dir),
            "command": command.get("command"),
            "vendor_report_json": str(json_vendor),
            "vendor_report_markdown": str(md_vendor),
            "report_json": str(json_out),
            "report_markdown": str(md_out),
        }
        write_report(payload, json_out, md_out)
        return payload
    return _unreal_smoke_report_from_install(command, json_out, md_out)


def _write_godot_smoke_script(project_dir: Path) -> Path:
    script_path = project_dir / "run_cesium_example_smoke.gd"
    _write_text(
        script_path,
        """
extends SceneTree

func _init() -> void:
    var report_path := OS.get_environment("FASTDIS_CESIUM_EXAMPLE_REPORT")
    var addon_root := "res://addons/cesium_godot"
    var descriptor_path := addon_root + "/Godot3DTiles.gdextension"
    var plugin_cfg_path := addon_root + "/plugin.cfg"
    var descriptor_present := FileAccess.file_exists(descriptor_path)
    var plugin_cfg_present := FileAccess.file_exists(plugin_cfg_path)
    if descriptor_present:
        load(descriptor_path)
    var georeference_class_present := ClassDB.class_exists("CesiumGeoreference")
    var status := "pass" if descriptor_present and plugin_cfg_present and georeference_class_present else "fail"
    var payload := {
        "status": status,
        "descriptor_present": descriptor_present,
        "plugin_cfg_present": plugin_cfg_present,
        "georeference_class_present": georeference_class_present,
        "descriptor_path": descriptor_path,
        "plugin_cfg_path": plugin_cfg_path
    }
    if report_path != "":
        var file := FileAccess.open(report_path, FileAccess.WRITE)
        if file != null:
            file.store_string(JSON.stringify(payload, "  "))
            file.store_string("\\n")
    quit(0 if status == "pass" else 3)
""".strip()
        + "\n",
    )
    return script_path


def _run_godot_smoke(*, json_out: Path, md_out: Path, dry_run: bool) -> dict[str, object]:
    doctor = doctor_payload("godot")
    plugin_root = resolve_plugin_root("godot")
    addon_root = godot_vendor_workflow.resolve_addon_root(plugin_root, None) if plugin_root is not None else None
    godot_binary = godot_env.resolve_godot()
    project_dir = _godot_smoke_project_dir()
    log_path = godot_env.work_root() / "logs" / "cesium_examples" / "godot_smoke.log"
    live_report = godot_env.work_root() / "reports" / "cesium_examples" / "godot_smoke_live.json"

    if plugin_root is None or addon_root is None or godot_binary is None:
        payload = {
            "schema": "packet_stoat.cesium_example_smoke.v1",
            "engine": "godot",
            "surface": ENGINE_SPECS["godot"]["surface"],
            "label": ENGINE_SPECS["godot"]["label"],
            "status": "needs-attention",
            "generated_at": _now(),
            "detail": "Godot example smoke requires a vendor addon root and a discovered Godot editor.",
            "checks": doctor["checks"],
            "workflow_commands": workflow_commands("godot"),
            "report_json": str(json_out),
            "report_markdown": str(md_out),
        }
        write_report(payload, json_out, md_out)
        return payload

    _copy_example_scaffold("godot", project_dir)
    destination_addon_root = project_dir / "addons" / "cesium_godot"
    destination_addon_root.parent.mkdir(parents=True, exist_ok=True)
    if destination_addon_root.exists():
        shutil.rmtree(destination_addon_root)
    shutil.copytree(addon_root, destination_addon_root)
    script_path = _write_godot_smoke_script(project_dir)
    command = [
        godot_binary,
        "--headless",
        "--path",
        str(project_dir),
        "--script",
        str(script_path),
    ]

    if dry_run:
        payload = {
            "schema": "packet_stoat.cesium_example_smoke.v1",
            "engine": "godot",
            "surface": ENGINE_SPECS["godot"]["surface"],
            "label": ENGINE_SPECS["godot"]["label"],
            "status": "dry-run",
            "generated_at": _now(),
            "plugin_root": str(plugin_root),
            "addon_root": str(addon_root),
            "project_dir": str(project_dir),
            "command": command,
            "log": str(log_path),
            "live_report": str(live_report),
            "report_json": str(json_out),
            "report_markdown": str(md_out),
        }
        write_report(payload, json_out, md_out)
        return payload

    log_path.parent.mkdir(parents=True, exist_ok=True)
    live_report.parent.mkdir(parents=True, exist_ok=True)
    _prime_subprocess_json_artifact(live_report, owner="cesium_example_workflow:godot")
    env = godot_env.build_env()
    env["FASTDIS_CESIUM_EXAMPLE_REPORT"] = str(live_report)
    with log_path.open("w", encoding="utf-8") as handle:
        completed = subprocess.run(command, cwd=ROOT, env=env, stdout=handle, stderr=subprocess.STDOUT, check=False)

    raw = _load_json_if_fresh(live_report)
    payload = {
        "schema": "packet_stoat.cesium_example_smoke.v1",
        "engine": "godot",
        "surface": ENGINE_SPECS["godot"]["surface"],
        "label": ENGINE_SPECS["godot"]["label"],
        "status": raw.get("status", "pass" if completed.returncode == 0 else "fail"),
        "generated_at": _now(),
        "plugin_root": str(plugin_root),
        "addon_root": str(addon_root),
        "project_dir": str(project_dir),
        "command": command,
        "returncode": completed.returncode,
        "log": str(log_path),
        "live_report": str(live_report),
        "checks": [
            {"name": "descriptor_present", "status": "ok" if raw.get("descriptor_present") else "fail", "detail": str(raw.get("descriptor_path") or "")},
            {"name": "plugin_cfg_present", "status": "ok" if raw.get("plugin_cfg_present") else "fail", "detail": str(raw.get("plugin_cfg_path") or "")},
            {"name": "georeference_class_present", "status": "ok" if raw.get("georeference_class_present") else "fail", "detail": "ClassDB.class_exists(CesiumGeoreference)"},
        ],
        "detail": "Godot example smoke completed." if completed.returncode == 0 else "Godot example smoke failed; inspect the Godot log and live report.",
        "report_json": str(json_out),
        "report_markdown": str(md_out),
    }
    write_report(payload, json_out, md_out)
    return payload


def smoke_payload(engine: str, *, dry_run: bool, engine_version: str | None = None, json_out: Path | None = None, md_out: Path | None = None) -> dict[str, object]:
    report_json, report_md = versioned_smoke_report_paths(engine, engine_version)
    json_out = json_out or report_json
    md_out = md_out or report_md
    if engine == "unity":
        return _run_unity_smoke(json_out=json_out, md_out=md_out, dry_run=dry_run)
    if engine == "unreal":
        return _run_unreal_smoke(json_out=json_out, md_out=md_out, dry_run=dry_run, engine_version=engine_version)
    if engine == "godot":
        return _run_godot_smoke(json_out=json_out, md_out=md_out, dry_run=dry_run)
    raise KeyError(engine)


def _proof_view_status(engine: str, *, dry_run: bool, ready: bool) -> str:
    if dry_run:
        return "dry-run"
    if ready:
        return "pass"
    return "needs-attention"


def _proof_view_stub_views(engine: str, *, status: str, detail: str, image_root: Path | None = None) -> list[dict[str, object]]:
    views: list[dict[str, object]] = []
    for view in proof_view_contract(engine):
        name = str(view["name"])
        image_path = image_root / f"{name}.png" if image_root is not None else None
        metadata_path = image_root / f"{name}.json" if image_root is not None else None
        views.append(
            {
                **view,
                "status": status,
                "detail": detail,
                "image_path": str(image_path) if image_path is not None else None,
                "metadata_path": str(metadata_path) if metadata_path is not None else None,
            }
        )
    return views


def _run_unreal_proof_view(*, json_out: Path, md_out: Path, dry_run: bool, engine_version: str | None) -> dict[str, object]:
    version = engine_version or ENGINE_SPECS["unreal"]["preferred_version"]
    doctor = doctor_payload("unreal")
    plugin_root = resolve_plugin_root("unreal")
    example_project = _unreal_smoke_project_dir(version)
    packaged_root: Path | None = None
    descriptor = unreal_vendor_workflow.resolve_uplugin_path("cesium", plugin_root, None) if plugin_root is not None else None
    if descriptor is not None:
        packaged_root = unreal_vendor_workflow.default_package_dir("cesium", descriptor, version)
    if plugin_root is None or descriptor is None or packaged_root is None:
        payload = {
            "schema": "packet_stoat.cesium_example_proof_view.v1",
            "engine": "unreal",
            "surface": ENGINE_SPECS["unreal"]["surface"],
            "label": ENGINE_SPECS["unreal"]["label"],
            "status": "needs-attention",
            "generated_at": _now(),
            "engine_version": version,
            "detail": "Unreal proof-view requires a prepared Cesium plugin root and staged example project.",
            "checks": doctor["checks"],
            "workflow_commands": workflow_commands("unreal"),
            "proof_view_contract": proof_view_contract("unreal"),
            "views": _proof_view_stub_views("unreal", status="needs-attention", detail="Cesium Unreal plugin root is missing."),
            "report_json": str(json_out),
            "report_markdown": str(md_out),
        }
        write_report(payload, json_out, md_out)
        return payload
    packaged_plugin_dir = _resolve_unreal_packaged_plugin_dir(packaged_root, descriptor.stem)
    staged_package_dir = _stage_unreal_packaged_plugin(packaged_plugin_dir, version, descriptor.stem)
    return capture_unreal_cesium_example_views.capture_report(
        project_dir=example_project,
        engine_version=version,
        json_out=json_out,
        md_out=md_out,
        dry_run=dry_run,
        package_dir=staged_package_dir,
        clean_project=True,
    )


def _run_unity_proof_view(*, json_out: Path, md_out: Path, dry_run: bool) -> dict[str, object]:
    doctor = doctor_payload("unity")
    plugin_root = resolve_plugin_root("unity")
    install = unity_env.resolve_install(ENGINE_SPECS["unity"]["preferred_version"])
    project_dir = _unity_smoke_project_dir()
    detail = (
        "Unity proof-view contract is defined, but this lane still needs a rendered editor capture route that does not rely on the smoke-only batchmode report."
    )
    payload = {
        "schema": "packet_stoat.cesium_example_proof_view.v1",
        "engine": "unity",
        "surface": ENGINE_SPECS["unity"]["surface"],
        "label": ENGINE_SPECS["unity"]["label"],
        "status": _proof_view_status("unity", dry_run=dry_run, ready=False),
        "generated_at": _now(),
        "unity_version": getattr(install, "version", ENGINE_SPECS["unity"]["preferred_version"]),
        "plugin_root": str(plugin_root) if plugin_root is not None else None,
        "project_dir": str(project_dir),
        "detail": detail,
        "checks": doctor["checks"],
        "workflow_commands": workflow_commands("unity"),
        "proof_view_contract": proof_view_contract("unity"),
        "views": _proof_view_stub_views("unity", status="pending", detail=detail, image_root=project_dir / "ProofViews"),
        "report_json": str(json_out),
        "report_markdown": str(md_out),
    }
    write_report(payload, json_out, md_out)
    return payload


def _run_godot_proof_view(*, json_out: Path, md_out: Path, dry_run: bool) -> dict[str, object]:
    doctor = doctor_payload("godot")
    plugin_root = resolve_plugin_root("godot")
    addon_root = godot_vendor_workflow.resolve_addon_root(plugin_root, None) if plugin_root is not None else None
    project_dir = _godot_smoke_project_dir()
    detail = (
        "Godot proof-view contract is defined, but the current 3D-Tiles-For-Godot route does not expose the same no-network ellipsoid tileset path and its editor-level recreate_tileset route is marked pending upstream."
    )
    payload = {
        "schema": "packet_stoat.cesium_example_proof_view.v1",
        "engine": "godot",
        "surface": ENGINE_SPECS["godot"]["surface"],
        "label": ENGINE_SPECS["godot"]["label"],
        "status": _proof_view_status("godot", dry_run=dry_run, ready=False),
        "generated_at": _now(),
        "plugin_root": str(plugin_root) if plugin_root is not None else None,
        "addon_root": str(addon_root) if addon_root is not None else None,
        "project_dir": str(project_dir),
        "detail": detail,
        "checks": doctor["checks"],
        "workflow_commands": workflow_commands("godot"),
        "proof_view_contract": proof_view_contract("godot"),
        "views": _proof_view_stub_views("godot", status="pending", detail=detail, image_root=project_dir / "ProofViews"),
        "report_json": str(json_out),
        "report_markdown": str(md_out),
    }
    write_report(payload, json_out, md_out)
    return payload


def proof_view_payload(engine: str, *, dry_run: bool, engine_version: str | None = None, json_out: Path | None = None, md_out: Path | None = None) -> dict[str, object]:
    report_json, report_md = versioned_proof_view_report_paths(engine, engine_version)
    json_out = json_out or report_json
    md_out = md_out or report_md
    if engine == "unity":
        return _run_unity_proof_view(json_out=json_out, md_out=md_out, dry_run=dry_run)
    if engine == "unreal":
        return _run_unreal_proof_view(json_out=json_out, md_out=md_out, dry_run=dry_run, engine_version=engine_version)
    if engine == "godot":
        return _run_godot_proof_view(json_out=json_out, md_out=md_out, dry_run=dry_run)
    raise KeyError(engine)


def render_markdown(payload: dict[str, object]) -> str:
    lines = [
        f"# {payload['label']}",
        "",
        f"- engine: `{payload['engine']}`",
        f"- surface: `{payload['surface']}`",
        f"- status: `{payload['status']}`",
    ]
    if payload.get("preferred_version") is not None:
        lines.append(f"- preferred_version: `{payload['preferred_version']}`")
    if payload.get("plugin_root") is not None:
        lines.append(f"- plugin_root: `{payload.get('plugin_root') or 'missing'}`")
    if payload.get("sample_root") is not None:
        lines.append(f"- sample_root: `{payload.get('sample_root') or 'n/a'}`")
    if payload.get("detail"):
        lines.append(f"- detail: `{payload['detail']}`")
    if payload.get("proof_view_contract"):
        lines.extend(["", "## Proof View Contract", ""])
        for view in payload["proof_view_contract"]:
            lines.append(f"- `{view['name']}`: `{view['description']}`")
    lines.extend(["", "## Checks", ""])
    for check in payload.get("checks", []):
        lines.append(f"- `{check['name']}`: `{check['status']}`")
        lines.append(f"  detail: `{check['detail']}`")
    if payload.get("views"):
        lines.extend(["", "## Views", ""])
        for view in payload["views"]:
            lines.append(f"- `{view['name']}`: `{view['status']}`")
            if view.get("image_path"):
                lines.append(f"  image: `{view['image_path']}`")
            if view.get("detail"):
                lines.append(f"  detail: `{view['detail']}`")
    if payload.get("workflow_commands"):
        lines.extend(["", "## Workflow Commands", ""])
        for key, value in payload.get("workflow_commands", {}).items():
            lines.append(f"- `{key}`: `{value}`")
    if payload.get("example_bar"):
        lines.extend(["", "## Example Bar", ""])
        for item in payload.get("example_bar", []):
            lines.append(f"- {item}")
    if payload.get("next_steps"):
        lines.extend(["", "## Next Steps", ""])
        for item in payload.get("next_steps", []):
            lines.append(f"- {item}")
    if payload.get("execution_plan"):
        lines.extend(["", "## Full Plan", ""])
        for command in payload["execution_plan"]:
            lines.append(f"- `{command}`")
    if payload.get("command"):
        lines.extend(["", "## Command", "", f"`{' '.join(str(part) for part in payload['command'])}`"])
    return "\n".join(lines) + "\n"


def write_report(payload: dict[str, object], json_out: Path, md_out: Path) -> None:
    json_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    md_out.write_text(render_markdown(payload), encoding="utf-8")


def print_text(payload: dict[str, object]) -> None:
    print(payload["label"])
    print(f"status: {payload['status']}")
    if payload.get("preferred_version") is not None:
        print(f"preferred_version: {payload['preferred_version']}")
    if payload.get("supported_versions"):
        print(f"supported_versions: {', '.join(payload['supported_versions'])}")
    if payload.get("plugin_root") is not None:
        print(f"plugin_root: {payload.get('plugin_root') or 'missing'}")
    if payload.get("sample_root") is not None:
        print(f"sample_root: {payload.get('sample_root') or 'n/a'}")
    if payload.get("detail"):
        print(f"detail: {payload['detail']}")
    if payload.get("proof_view_contract"):
        print("proof_view_contract:")
        for view in payload["proof_view_contract"]:
            print(f"  - {view['name']}: {view['description']}")
    print("checks:")
    for check in payload.get("checks", []):
        print(f"  - {check['name']}: {check['status']} ({check['detail']})")
    if payload.get("views"):
        print("views:")
        for view in payload["views"]:
            print(f"  - {view['name']}: {view['status']} ({view.get('detail')})")
    if payload.get("workflow_commands"):
        print("workflow_commands:")
        for key, value in payload.get("workflow_commands", {}).items():
            print(f"  - {key}: {value}")
    if payload.get("command"):
        print("command:")
        print(f"  {' '.join(str(part) for part in payload['command'])}")
    if payload.get("report_json"):
        print(f"report_json: {payload['report_json']}")
    if payload.get("report_markdown"):
        print(f"report_markdown: {payload['report_markdown']}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    for name in ("discover", "doctor", "report", "full", "smoke", "proof-view"):
        sub = subparsers.add_parser(name)
        sub.add_argument("--engine", choices=sorted(ENGINE_SPECS), required=True)
        sub.add_argument("--format", choices=("text", "json"), default="text")
        if name in {"report", "full", "smoke", "proof-view"}:
            sub.add_argument("--json-out", type=Path)
            sub.add_argument("--md-out", type=Path)
        if name in {"smoke", "proof-view"}:
            sub.add_argument("--dry-run", action="store_true")
            sub.add_argument("--engine-version", help="Override Unreal engine version for the smoke lane")
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
    elif args.command == "smoke":
        payload = smoke_payload(
            args.engine,
            dry_run=args.dry_run,
            engine_version=getattr(args, "engine_version", None),
            json_out=args.json_out,
            md_out=args.md_out,
        )
    elif args.command == "proof-view":
        payload = proof_view_payload(
            args.engine,
            dry_run=args.dry_run,
            engine_version=getattr(args, "engine_version", None),
            json_out=args.json_out,
            md_out=args.md_out,
        )
    else:
        payload = full_payload(args.engine)
        json_out = args.json_out or report_paths(args.engine)[0]
        md_out = args.md_out or report_paths(args.engine)[1]
        write_report(payload, json_out, md_out)

    if args.format == "json":
        print(json.dumps(payload, indent=2))
    else:
        print_text(payload)
    return 0 if payload.get("status", "ok") in {"ok", "pass", "dry-run"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
