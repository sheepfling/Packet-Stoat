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


def _sandbox_report_dir(monkeypatch, tmp_path: Path) -> Path:
    report_dir = tmp_path / "reports"
    monkeypatch.setattr(godot_vendor_workflow, "DEFAULT_REPORT_DIR", report_dir)
    return report_dir


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
    assert any(check["name"] == "godot discovery roots" and "FASTDIS_GODOT_ROOTS" in check["detail"] for check in payload["checks"])


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
        lambda: {
            "platform": "windows",
            "arch": "x86_64",
            "godot": "/opt/godot",
            "scons": "scons",
            "installs": [
                {"version": "4.3", "version_kind": "stable", "path": "/opt/godot"},
                {"version": "4.4-rc1", "version_kind": "prerelease:rc", "path": "/opt/godot-rc"},
            ],
        },
    )

    payload = godot_vendor_workflow.doctor_payload("cesium-godot", str(tmp_path), None, "4.1")

    assert payload["status"] == "ok"
    assert any(check["name"] == "godot_version" and check["status"] == "ok" for check in payload["checks"])
    assert any(check["name"] == "godot_version_kind" and check["detail"] == "stable" for check in payload["checks"])
    assert any(check["name"] == "version selection" and "4.4-rc1" in check["detail"] for check in payload["checks"])


def test_discover_includes_godot_version(monkeypatch, capsys) -> None:
    monkeypatch.setattr(godot_vendor_workflow.godot_env, "describe_host", lambda: {"godot": "/opt/godot", "installs": []})
    monkeypatch.setattr(godot_vendor_workflow, "detected_godot_version", lambda: "4.2")

    rc = godot_vendor_workflow.main(["discover", "--format", "json"])
    out = capsys.readouterr().out

    assert rc == 0
    payload = json.loads(out)
    assert payload["godot_version"] == "4.2"


def test_discover_prints_root_hint_when_missing(monkeypatch, capsys) -> None:
    monkeypatch.setattr(godot_vendor_workflow.godot_env, "describe_host", lambda: {"godot": None, "installs": []})
    monkeypatch.setattr(godot_vendor_workflow, "detected_godot_version", lambda: None)

    rc = godot_vendor_workflow.main(["discover"])
    out = capsys.readouterr().out

    assert rc == 1
    assert "No Godot installs discovered." in out
    assert "FASTDIS_GODOT_ROOTS" in out


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
    _sandbox_report_dir(monkeypatch, tmp_path)
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
    _sandbox_report_dir(monkeypatch, tmp_path)
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
        "tee",
        80,
        True,
    )

    assert payload["status"] == "dry-run"
    assert payload["build_status"] == "dry-run"
    assert payload["build_command"][:3] == ["scons", "-f", "SConstruct.py"]
    assert "compileTarget=extension" in payload["build_command"]
    assert "target=template_release" in payload["build_command"]
    assert "buildCesium=YES" in payload["build_command"]
    assert payload["process_provenance"]["process_matters_as_evidence"] is True
    assert payload["process_provenance"]["build_characteristics"]["heavy_native_build"] is True
    assert payload["build_environment"]["work_root"]
    assert "HOME" in payload["build_environment"]["overrides"]
    assert "EZVCPKG_BASEDIR" in payload["build_environment"]["overrides"]
    assert payload["observability"]["log_mode"] == "tee"
    assert payload["observability"]["log_tail_lines"] == 80
    assert "streamed" in payload["observability"]["log_capture"]


def test_clean_native_cache_removes_stale_cmake_outputs(tmp_path: Path) -> None:
    native_dir = tmp_path / "cesium_godot" / "native"
    native_dir.mkdir(parents=True)
    cache_file = native_dir / "CMakeCache.txt"
    cache_dir = native_dir / "CMakeFiles"
    cache_file.write_text("stale\n", encoding="utf-8")
    cache_dir.mkdir()
    (cache_dir / "marker.txt").write_text("stale\n", encoding="utf-8")

    cleaned = godot_vendor_workflow.clean_native_cache(tmp_path)

    assert str(cache_file) in cleaned
    assert str(cache_dir) in cleaned
    assert not cache_file.exists()
    assert not cache_dir.exists()


def test_built_artifact_candidates_finds_addon_lib_output(monkeypatch, tmp_path: Path) -> None:
    lib_dir = tmp_path / "godot3dtiles" / "addons" / "cesium_godot" / "lib"
    lib_dir.mkdir(parents=True)
    artifact = lib_dir / "libGodot3DTiles.linux.template_release.x86_64.so"
    artifact.write_text("stub", encoding="utf-8")
    monkeypatch.setattr(godot_vendor_workflow.godot_env, "host_platform_name", lambda: "linux")
    monkeypatch.setattr(godot_vendor_workflow.godot_env, "host_arch_name", lambda: "x86_64")

    matches = godot_vendor_workflow.built_artifact_candidates(tmp_path, "template_release")

    assert matches == [artifact.resolve()]


def test_build_payload_captures_compile_failure(monkeypatch, tmp_path: Path) -> None:
    _sandbox_report_dir(monkeypatch, tmp_path)
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
        "capture",
        20,
        False,
    )

    assert payload["status"] == "fail"
    assert payload["build_status"] == "fail"
    assert "compile failed" in "\n".join(payload["failure_tail"])
    assert Path(payload["log"]).is_file()
    assert payload["cleaned_native_cache"] == []


def test_handoff_payload_formats_upstream_issue_for_compile_failure(monkeypatch, tmp_path: Path) -> None:
    _sandbox_report_dir(monkeypatch, tmp_path)
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
        "capture",
        20,
        False,
    )

    assert payload["schema"] == "packet_stoat.cesium_godot_upstream_handoff.v1"
    assert payload["status"] == "ready"
    assert payload["failure_class"] == "compile-or-link"
    assert "## Repro" in payload["issue_body_markdown"]
    assert "compile failed" in payload["issue_body_markdown"]


def test_handoff_command_writes_outputs(monkeypatch, tmp_path: Path, capsys) -> None:
    report_dir = _sandbox_report_dir(monkeypatch, tmp_path)
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
    assert (report_dir / "cesium-godot_build.json").is_file()
