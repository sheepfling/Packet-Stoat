from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import godot_vendor_workflow


def test_vendor_slug_normalizes_input() -> None:
    assert godot_vendor_workflow.vendor_slug("Cesium Godot") == "cesium-godot"


def test_resolve_addon_root_prefers_known_layout(tmp_path: Path) -> None:
    addon = tmp_path / "godot3dtiles" / "addons" / "cesium_godot"
    addon.mkdir(parents=True)

    resolved = godot_vendor_workflow.resolve_addon_root(tmp_path, None)

    assert resolved == addon.resolve()


def test_doctor_payload_reports_missing_plugin_root(monkeypatch) -> None:
    monkeypatch.delenv("FASTDIS_CESIUM_GODOT_PLUGIN_ROOT", raising=False)
    monkeypatch.setattr(godot_vendor_workflow.godot_env, "resolve_godot", lambda explicit=None: None)
    monkeypatch.setattr(godot_vendor_workflow, "detected_godot_version", lambda: None)

    payload = godot_vendor_workflow.doctor_payload("cesium-godot", None, None, "4.1")

    assert payload["status"] == "needs-attention"
    assert any(check["name"] == "plugin_root" and check["status"] == "fail" for check in payload["checks"])


def test_doctor_payload_accepts_supported_layout_and_version(monkeypatch, tmp_path: Path) -> None:
    addon = tmp_path / "godot3dtiles" / "addons" / "cesium_godot"
    addon.mkdir(parents=True)
    (addon / "plugin.cfg").write_text("[plugin]\n", encoding="utf-8")
    (addon / "Godot3DTiles.gdextension").write_text("[configuration]\n", encoding="utf-8")
    monkeypatch.setattr(godot_vendor_workflow.godot_env, "resolve_godot", lambda explicit=None: "/opt/godot")
    monkeypatch.setattr(godot_vendor_workflow, "detected_godot_version", lambda: "4.3")
    monkeypatch.setattr(
        godot_vendor_workflow.godot_env,
        "describe_host",
        lambda: {"platform": "windows", "arch": "x86_64", "godot": "/opt/godot", "scons": "scons"},
    )

    payload = godot_vendor_workflow.doctor_payload("cesium-godot", str(tmp_path), None, "4.1")

    assert payload["status"] == "ok"
    assert any(check["name"] == "godot_version" and check["status"] == "ok" for check in payload["checks"])


def test_discover_includes_godot_version(monkeypatch, capsys) -> None:
    monkeypatch.setattr(godot_vendor_workflow.godot_env, "describe_host", lambda: {"godot": "/opt/godot"})
    monkeypatch.setattr(godot_vendor_workflow, "detected_godot_version", lambda: "4.2")

    rc = godot_vendor_workflow.main(["discover", "--format", "json"])
    out = capsys.readouterr().out

    assert rc == 0
    payload = json.loads(out)
    assert payload["godot_version"] == "4.2"


def test_report_payload_includes_fix_report(monkeypatch, tmp_path: Path) -> None:
    addon = tmp_path / "godot3dtiles" / "addons" / "cesium_godot"
    addon.mkdir(parents=True)
    (addon / "plugin.cfg").write_text("[plugin]\n", encoding="utf-8")
    (addon / "Godot3DTiles.gdextension").write_text("[configuration]\n", encoding="utf-8")
    monkeypatch.setattr(godot_vendor_workflow.godot_env, "resolve_godot", lambda explicit=None: "/opt/godot")
    monkeypatch.setattr(godot_vendor_workflow, "detected_godot_version", lambda: "4.3")
    monkeypatch.setattr(
        godot_vendor_workflow.godot_env,
        "describe_host",
        lambda: {"platform": "windows", "arch": "x86_64", "godot": "/opt/godot", "scons": "scons"},
    )

    payload = godot_vendor_workflow.report_payload("cesium-godot", str(tmp_path), None, "4.1")

    assert payload["schema"] == "packet_stoat.godot_vendor_plugin_report.v1"
    assert payload["mode"] == "report"
    assert payload["status"] == "ok"
    assert payload["fix_report"]["upstream_project"] == "cesium-godot"


def test_report_command_writes_json_and_markdown(monkeypatch, tmp_path: Path, capsys) -> None:
    addon = tmp_path / "godot3dtiles" / "addons" / "cesium_godot"
    addon.mkdir(parents=True)
    (addon / "plugin.cfg").write_text("[plugin]\n", encoding="utf-8")
    (addon / "Godot3DTiles.gdextension").write_text("[configuration]\n", encoding="utf-8")
    monkeypatch.setattr(godot_vendor_workflow.godot_env, "resolve_godot", lambda explicit=None: "/opt/godot")
    monkeypatch.setattr(godot_vendor_workflow, "detected_godot_version", lambda: "4.3")
    monkeypatch.setattr(
        godot_vendor_workflow.godot_env,
        "describe_host",
        lambda: {"platform": "windows", "arch": "x86_64", "godot": "/opt/godot", "scons": "scons"},
    )
    json_out = tmp_path / "report.json"
    md_out = tmp_path / "report.md"

    rc = godot_vendor_workflow.main(
        [
            "report",
            "--vendor",
            "cesium-godot",
            "--plugin-root",
            str(tmp_path),
            "--json-out",
            str(json_out),
            "--md-out",
            str(md_out),
        ]
    )
    out = capsys.readouterr().out

    assert rc == 0
    payload = json.loads(out)
    assert payload["report_json"] == str(json_out.resolve())
    assert json_out.is_file()
    assert md_out.is_file()


def test_build_payload_dry_run_uses_upstream_scons_route(monkeypatch, tmp_path: Path) -> None:
    addon = tmp_path / "godot3dtiles" / "addons" / "cesium_godot"
    addon.mkdir(parents=True)
    (addon / "plugin.cfg").write_text("[plugin]\n", encoding="utf-8")
    (addon / "Godot3DTiles.gdextension").write_text("[configuration]\n", encoding="utf-8")
    (tmp_path / "SConstruct.py").write_text("# stub\n", encoding="utf-8")
    monkeypatch.setattr(godot_vendor_workflow.godot_env, "resolve_godot", lambda explicit=None: "/opt/godot")
    monkeypatch.setattr(godot_vendor_workflow, "detected_godot_version", lambda: "4.3")
    monkeypatch.setattr(
        godot_vendor_workflow.godot_env,
        "describe_host",
        lambda: {"platform": "windows", "arch": "x86_64", "godot": "/opt/godot", "scons": "scons"},
    )

    payload = godot_vendor_workflow.build_payload(
        "cesium-godot",
        str(tmp_path),
        None,
        "4.1",
        None,
        None,
        None,
        "template_release",
        "extension",
        2,
        True,
    )

    assert payload["status"] == "dry-run"
    assert payload["build_status"] == "dry-run"
    assert payload["build_command"][:3] == ["scons", "-f", "SConstruct.py"]
    assert "compileTarget=extension" in payload["build_command"]
    assert "target=template_release" in payload["build_command"]


def test_build_payload_captures_compile_failure(monkeypatch, tmp_path: Path) -> None:
    addon = tmp_path / "godot3dtiles" / "addons" / "cesium_godot"
    addon.mkdir(parents=True)
    (addon / "plugin.cfg").write_text("[plugin]\n", encoding="utf-8")
    (addon / "Godot3DTiles.gdextension").write_text("[configuration]\n", encoding="utf-8")
    (tmp_path / "SConstruct.py").write_text("# stub\n", encoding="utf-8")
    monkeypatch.setattr(godot_vendor_workflow.godot_env, "resolve_godot", lambda explicit=None: "/opt/godot")
    monkeypatch.setattr(godot_vendor_workflow, "detected_godot_version", lambda: "4.3")
    monkeypatch.setattr(
        godot_vendor_workflow.godot_env,
        "describe_host",
        lambda: {"platform": "windows", "arch": "x86_64", "godot": "/opt/godot", "scons": "scons"},
    )

    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(args[0], 1, stdout="", stderr="error C2664: compile failed\n")

    monkeypatch.setattr(godot_vendor_workflow.subprocess, "run", fake_run)

    payload = godot_vendor_workflow.build_payload(
        "cesium-godot",
        str(tmp_path),
        None,
        "4.1",
        str(tmp_path / "build.json"),
        str(tmp_path / "build.md"),
        str(tmp_path / "build.log"),
        "template_release",
        "extension",
        1,
        False,
    )

    assert payload["status"] == "fail"
    assert payload["build_status"] == "fail"
    assert "compile failed" in "\n".join(payload["failure_tail"])
    assert Path(payload["log"]).is_file()


def test_handoff_payload_formats_upstream_issue_for_compile_failure(monkeypatch, tmp_path: Path) -> None:
    addon = tmp_path / "godot3dtiles" / "addons" / "cesium_godot"
    addon.mkdir(parents=True)
    (addon / "plugin.cfg").write_text("[plugin]\n", encoding="utf-8")
    (addon / "Godot3DTiles.gdextension").write_text("[configuration]\n", encoding="utf-8")
    (tmp_path / "SConstruct.py").write_text("# stub\n", encoding="utf-8")
    monkeypatch.setattr(godot_vendor_workflow.godot_env, "resolve_godot", lambda explicit=None: "/opt/godot")
    monkeypatch.setattr(godot_vendor_workflow, "detected_godot_version", lambda: "4.3")
    monkeypatch.setattr(
        godot_vendor_workflow.godot_env,
        "describe_host",
        lambda: {"platform": "windows", "arch": "x86_64", "godot": "/opt/godot", "scons": "scons"},
    )

    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(args[0], 1, stdout="", stderr="error C2664: compile failed\n")

    monkeypatch.setattr(godot_vendor_workflow.subprocess, "run", fake_run)

    payload = godot_vendor_workflow.handoff_payload(
        "cesium-godot",
        str(tmp_path),
        None,
        "4.1",
        str(tmp_path / "build.json"),
        str(tmp_path / "build.md"),
        str(tmp_path / "build.log"),
        "template_release",
        "extension",
        1,
        False,
    )

    assert payload["schema"] == "packet_stoat.cesium_godot_upstream_handoff.v1"
    assert payload["status"] == "ready"
    assert payload["failure_class"] == "compile-or-link"
    assert "## Repro" in payload["issue_body_markdown"]
    assert "compile failed" in payload["issue_body_markdown"]


def test_handoff_command_writes_outputs(monkeypatch, tmp_path: Path, capsys) -> None:
    addon = tmp_path / "godot3dtiles" / "addons" / "cesium_godot"
    addon.mkdir(parents=True)
    (addon / "plugin.cfg").write_text("[plugin]\n", encoding="utf-8")
    (addon / "Godot3DTiles.gdextension").write_text("[configuration]\n", encoding="utf-8")
    (tmp_path / "SConstruct.py").write_text("# stub\n", encoding="utf-8")
    monkeypatch.setattr(godot_vendor_workflow.godot_env, "resolve_godot", lambda explicit=None: "/opt/godot")
    monkeypatch.setattr(godot_vendor_workflow, "detected_godot_version", lambda: "4.3")
    monkeypatch.setattr(
        godot_vendor_workflow.godot_env,
        "describe_host",
        lambda: {"platform": "windows", "arch": "x86_64", "godot": "/opt/godot", "scons": "scons"},
    )

    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(args[0], 1, stdout="", stderr="error C2664: compile failed\n")

    monkeypatch.setattr(godot_vendor_workflow.subprocess, "run", fake_run)
    json_out = tmp_path / "handoff.json"
    md_out = tmp_path / "handoff.md"

    rc = godot_vendor_workflow.main(
        [
            "handoff",
            "--vendor",
            "cesium-godot",
            "--plugin-root",
            str(tmp_path),
            "--json-out",
            str(json_out),
            "--md-out",
            str(md_out),
        ]
    )
    out = capsys.readouterr().out

    assert rc == 0
    payload = json.loads(out)
    assert payload["handoff_json"] == str(json_out.resolve())
    assert json_out.is_file()
    assert md_out.is_file()
