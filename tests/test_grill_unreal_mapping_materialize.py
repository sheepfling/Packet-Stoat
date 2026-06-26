from __future__ import annotations

import json
import sys
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import run_unreal_grill_mapping_materialize as materialize_runner


def test_build_temp_project_mounts_fastdis_plugin(tmp_path: Path) -> None:
    example_root = tmp_path / "GRILL_DISForUnrealExample"
    (example_root / "Content").mkdir(parents=True)
    (example_root / "Plugins" / "GRILLDISForUnreal").mkdir(parents=True)
    (example_root / "Source").mkdir(parents=True)
    (example_root / "Config").mkdir(parents=True)
    (example_root / "GRILLDISExample.uproject").write_text(
        json.dumps(
            {
                "FileVersion": 3,
                "Plugins": [
                    {"Name": "GRILLDISForUnreal", "Enabled": True},
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    fastdis_plugin_root = tmp_path / "FastDis"
    fastdis_plugin_root.mkdir()

    project_path = materialize_runner.build_temp_project(example_root, tmp_path / "temp_project", fastdis_plugin_root=fastdis_plugin_root)
    descriptor = json.loads(project_path.read_text(encoding="utf-8"))
    plugin_names = {plugin["Name"] for plugin in descriptor["Plugins"]}
    assert "PythonScriptPlugin" in plugin_names
    assert "FastDis" in plugin_names
    assert (project_path.parent / "Plugins" / "GRILLDISForUnreal").is_symlink()
    assert (project_path.parent / "Plugins" / "FastDis").is_symlink()


def test_build_command_includes_execute_python_script(tmp_path: Path) -> None:
    project_path = tmp_path / "Example.uproject"
    project_path.write_text("{}\n", encoding="utf-8")
    command = materialize_runner.build_command("UnrealEditor-Cmd", project_path)
    assert command[0] == "UnrealEditor-Cmd"
    assert any(part.startswith("-ExecutePythonScript=") for part in command)
    assert str(project_path) in command


def test_main_dry_run_writes_report(monkeypatch, tmp_path: Path) -> None:
    example_root = tmp_path / "GRILL_DISForUnrealExample"
    (example_root / "Content").mkdir(parents=True)
    (example_root / "Plugins").mkdir(parents=True)
    (example_root / "Source").mkdir(parents=True)
    (example_root / "Config").mkdir(parents=True)
    (example_root / "GRILLDISExample.uproject").write_text('{"FileVersion":3,"Plugins":[]}\n', encoding="utf-8")

    input_manifest = tmp_path / "fastdis_mapping_manifest.json"
    input_manifest.write_text('{"rows":[]}\n', encoding="utf-8")
    result_json = tmp_path / "grill_mapping_materialize.json"
    report_json = tmp_path / "grill_mapping_materialize_report.json"
    report_md = tmp_path / "grill_mapping_materialize_report.md"

    args = materialize_runner.argparse.Namespace(
        unreal=None,
        engine_version="5.8",
        example_root=example_root,
        input_manifest=input_manifest,
        asset_path="/Game/FastDis/DA_ImportedGRILLMappings",
        temp_project_dir=tmp_path / "temp_project",
        result_json=result_json,
        json_out=report_json,
        markdown_out=report_md,
        timeout_seconds=30.0,
        dry_run=True,
    )
    monkeypatch.setattr(materialize_runner, "parse_args", lambda: args)
    monkeypatch.setattr(materialize_runner.load_local_env, "load", lambda: None)
    monkeypatch.setattr(materialize_runner, "resolve_unreal", lambda explicit, version: "UnrealEditor-Cmd")
    monkeypatch.setattr(materialize_runner, "FASTDIS_PLUGIN_ROOT", tmp_path / "FastDis")
    materialize_runner.FASTDIS_PLUGIN_ROOT.mkdir()

    assert materialize_runner.main() == 0
    report = json.loads(report_json.read_text(encoding="utf-8"))
    assert report["status"] == "dry-run"
    assert report["asset_path"] == "/Game/FastDis/DA_ImportedGRILLMappings"
    assert "ExecutePythonScript" in " ".join(report["command"])


def test_write_report_renders_failure_kind(tmp_path: Path) -> None:
    json_path = tmp_path / "report.json"
    markdown_path = tmp_path / "report.md"
    report = {
        "generated_at": "2026-06-26T00:00:00+00:00",
        "status": "plugin-version-incompatible",
        "example_root": "/tmp/example",
        "project_file": "/tmp/example.uproject",
        "input_manifest": "/tmp/manifest.json",
        "asset_path": "/Game/FastDis/DA_ImportedGRILLMappings",
        "result_json": "/tmp/result.json",
        "log_path": "/tmp/editor.log",
        "details": ["detail"],
        "failure_kind": "plugin-version-incompatible",
        "failure_detail": "plugin mismatch",
        "log_excerpt": ["plugin line"],
    }

    materialize_runner.write_report(report, json_path, markdown_path)

    markdown = markdown_path.read_text(encoding="utf-8")
    assert "failure_kind: `plugin-version-incompatible`" in markdown
    assert "plugin mismatch" in markdown
    assert "plugin line" in markdown
