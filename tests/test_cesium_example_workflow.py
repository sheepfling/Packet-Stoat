from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "extensions" / "cesium" / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import cesium_example_workflow


def test_discover_unreal_reports_preferred_lane(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("FASTDIS_CESIUM_PLUGIN_ROOT", str(tmp_path))
    monkeypatch.setattr(cesium_example_workflow.unreal_env, "discover_installs", lambda: [object()])

    payload = cesium_example_workflow.discover_payload("unreal")

    assert payload["preferred_version"] == "5.7"
    assert payload["engine_install_found"] is True
    assert payload["plugin_root"] == str(tmp_path.resolve())
    assert payload["example_project"].endswith("CesiumVanillaExample.uproject")
    assert payload["workflow_commands"]["vendor_full"] == "python tools/unreal_vendor_workflow.py full --vendor cesium"


def test_doctor_unity_reports_missing_editor(monkeypatch) -> None:
    monkeypatch.delenv("FASTDIS_CESIUM_UNITY_PLUGIN_ROOT", raising=False)
    monkeypatch.setattr(cesium_example_workflow.unity_env, "resolve_install", lambda: None)

    payload = cesium_example_workflow.doctor_payload("unity")

    assert payload["status"] == "needs-attention"
    assert any(check["name"] == "engine_install" and check["status"] == "fail" for check in payload["checks"])
    assert payload["project_marker"] is not None
    assert payload["workflow_commands"]["vendor_full"] == "python tools/unity_vendor_workflow.py full --vendor cesium-unity --unity-version 6000.5"


def test_main_doctor_json_for_godot(monkeypatch, tmp_path: Path, capsys) -> None:
    monkeypatch.setenv("FASTDIS_CESIUM_GODOT_PLUGIN_ROOT", str(tmp_path))
    monkeypatch.setattr(cesium_example_workflow.godot_env, "resolve_godot", lambda: "/opt/godot")

    rc = cesium_example_workflow.main(["doctor", "--engine", "godot", "--format", "json"])
    out = capsys.readouterr().out

    assert rc == 0
    payload = json.loads(out)
    assert payload["engine"] == "godot"
    assert payload["status"] == "ok"
    assert payload["project_marker"].endswith("project.godot")


def test_doctor_unreal_reports_missing_example_project_when_overridden(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("FASTDIS_CESIUM_PLUGIN_ROOT", str(tmp_path))
    monkeypatch.setattr(cesium_example_workflow.unreal_env, "discover_installs", lambda: [object()])
    original = cesium_example_workflow.ENGINE_SPECS["unreal"]["example_root"]
    cesium_example_workflow.ENGINE_SPECS["unreal"]["example_root"] = tmp_path / "missing"
    try:
        payload = cesium_example_workflow.doctor_payload("unreal")
    finally:
        cesium_example_workflow.ENGINE_SPECS["unreal"]["example_root"] = original

    assert payload["status"] == "needs-attention"
    assert any(check["name"] == "example_project" and check["status"] == "fail" for check in payload["checks"])


def test_report_writes_default_artifacts(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("FASTDIS_CESIUM_UNITY_PLUGIN_ROOT", str(tmp_path))
    monkeypatch.setattr(
        cesium_example_workflow.unity_env,
        "resolve_install",
        lambda: object(),
    )
    json_out = tmp_path / "report.json"
    md_out = tmp_path / "report.md"

    payload = cesium_example_workflow.report_payload("unity")
    cesium_example_workflow.write_report(payload, json_out, md_out)

    assert payload["status"] == "ok"
    assert payload["summary"]["example_lane_ready"] is True
    assert json.loads(json_out.read_text(encoding="utf-8"))["engine"] == "unity"
    assert "Cesium Unity Example" in md_out.read_text(encoding="utf-8")


def test_main_full_json_for_unreal_writes_requested_outputs(monkeypatch, tmp_path: Path, capsys) -> None:
    plugin_root = tmp_path / "plugin"
    plugin_root.mkdir()
    monkeypatch.setenv("FASTDIS_CESIUM_PLUGIN_ROOT", str(plugin_root))
    monkeypatch.setattr(cesium_example_workflow.unreal_env, "discover_installs", lambda: [object()])
    json_out = tmp_path / "full.json"
    md_out = tmp_path / "full.md"

    rc = cesium_example_workflow.main(
        [
            "full",
            "--engine",
            "unreal",
            "--format",
            "json",
            "--json-out",
            str(json_out),
            "--md-out",
            str(md_out),
        ]
    )
    out = capsys.readouterr().out

    assert rc == 0
    payload = json.loads(out)
    assert payload["mode"] == "full"
    assert payload["workflow_commands"]["vendor_full"] == "python tools/unreal_vendor_workflow.py full --vendor cesium"
    assert payload["execution_plan"][0] == "python extensions/cesium/tools/prepare_cesium_source_route.py"
    assert json_out.is_file()
    assert md_out.is_file()
