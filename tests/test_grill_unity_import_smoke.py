from __future__ import annotations

import json
from pathlib import Path
import sys
import tarfile


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import run_grill_unity_import_smoke


def test_grill_import_smoke_create_project_copies_plugin(tmp_path: Path) -> None:
    project = tmp_path / "project"
    plugin = tmp_path / "plugin"
    plugin.mkdir()
    (plugin / "README.md").write_text("grill\n", encoding="utf-8")
    (plugin / "DISPluginContent").mkdir(parents=True)

    run_grill_unity_import_smoke.create_project(project, plugin, "6000.5.0f1")

    manifest = json.loads((project / "Packages" / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["dependencies"] == {}
    assert (project / "Assets" / "GRILL_DIS" / "README.md").read_text(encoding="utf-8") == "grill\n"
    assert "6000.5.0f1" in (project / "ProjectSettings" / "ProjectVersion.txt").read_text(encoding="utf-8")


def test_grill_import_smoke_create_project_extracts_unitypackage(tmp_path: Path) -> None:
    project = tmp_path / "project"
    package = tmp_path / "grill_dis_for_unity.unitypackage"
    staging = tmp_path / "staging"
    entry = staging / "abcd1234"
    entry.mkdir(parents=True)
    (entry / "pathname").write_text("GRILL_DIS/README.md\n", encoding="utf-8")
    (entry / "asset").write_text("grill package\n", encoding="utf-8")
    (entry / "asset.meta").write_text("fileFormatVersion: 2\n", encoding="utf-8")
    with tarfile.open(package, "w:gz") as archive:
        archive.add(entry / "pathname", arcname="abcd1234/pathname")
        archive.add(entry / "asset", arcname="abcd1234/asset")
        archive.add(entry / "asset.meta", arcname="abcd1234/asset.meta")

    run_grill_unity_import_smoke.create_project(project, package, "6000.5.0f1")

    assert (project / "Assets" / "GRILL_DIS" / "README.md").read_text(encoding="utf-8") == "grill package\n"
    assert (project / "Assets" / "GRILL_DIS" / "README.md.meta").is_file()


def test_grill_import_smoke_enable_required_builtin_modules_updates_manifest(tmp_path: Path) -> None:
    manifest_path = tmp_path / "Packages" / "manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text('{"dependencies":{"com.unity.test-framework":"1.0.0"}}\n', encoding="utf-8")

    run_grill_unity_import_smoke.enable_required_builtin_modules(tmp_path)

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["dependencies"]["com.unity.modules.imgui"] == "1.0.0"
    assert manifest["dependencies"]["com.unity.modules.physics"] == "1.0.0"


def test_grill_import_smoke_render_markdown_mentions_status() -> None:
    report = {
        "status": "fail",
        "host_platform": "macos",
        "unity_version": "6000.5.0f1",
        "plugin_root": "/tmp/GRILL",
        "detail": "import failed",
        "launch": "login-shell",
        "log": "/tmp/grill.log",
        "launcher_log": "/tmp/grill_launcher.log",
        "failure_stage": "plugin-import",
        "failure_reason": "grill-project-import-never-started",
        "startup_probe": {"status": "pass", "detail": "blank project startup passed"},
        "project_state": {"library_exists": False, "package_cache_exists": False, "script_assemblies_exists": False},
        "attempts": [{"launch": "login-shell", "status": "fail", "returncode": 1, "timed_out": False, "elapsed_seconds": 1.2}],
    }

    markdown = run_grill_unity_import_smoke.render_markdown(report)

    assert "GRILL Unity Import Smoke" in markdown
    assert "status: `fail`" in markdown
    assert "failure_stage: `plugin-import`" in markdown
    assert "startup_probe.status: `pass`" in markdown
    assert "launch=login-shell status=fail" in markdown


def test_grill_import_smoke_classify_report_distinguishes_host_startup_block() -> None:
    classification = run_grill_unity_import_smoke.classify_report(
        startup_probe_report={"status": "fail", "detail": "blank startup failed"},
        state={"library_exists": False, "script_assemblies_exists": False},
        log_analysis={},
        hint="kLSNoExecutableErr",
    )

    assert classification["status"] == "blocked-host-startup"
    assert classification["failure_stage"] == "host-startup"
