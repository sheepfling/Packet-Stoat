from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import run_unreal_vendor_install_smoke


def test_create_scratch_project_installs_packaged_plugin(tmp_path: Path) -> None:
    package_dir = tmp_path / "package"
    package_dir.mkdir()
    (package_dir / "CesiumForUnreal.uplugin").write_text("{}\n", encoding="utf-8")
    project_dir = tmp_path / "project"

    project_path = run_unreal_vendor_install_smoke.create_scratch_project(
        project_dir,
        package_dir,
        "CesiumForUnreal",
        clean=True,
    )

    assert project_path.exists()
    plugin_dir = project_dir / "Plugins" / "CesiumForUnreal"
    assert plugin_dir.exists()
    descriptor = json.loads(project_path.read_text(encoding="utf-8"))
    plugin_names = {plugin["Name"] for plugin in descriptor["Plugins"]}
    assert "CesiumForUnreal" in plugin_names
    assert "PythonScriptPlugin" in plugin_names


def test_missing_package_writes_report(tmp_path: Path, monkeypatch) -> None:
    json_out = tmp_path / "report.json"
    markdown_out = tmp_path / "report.md"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_unreal_vendor_install_smoke.py",
            "--vendor",
            "cesium",
            "--package-dir",
            str(tmp_path / "missing-package"),
            "--project-dir",
            str(tmp_path / "project"),
            "--json-out",
            str(json_out),
            "--markdown-out",
            str(markdown_out),
        ],
    )

    assert run_unreal_vendor_install_smoke.main() == 2
    payload = json.loads(json_out.read_text(encoding="utf-8"))
    assert payload["status"] == "missing-package"


def test_dry_run_writes_command_report(tmp_path: Path, monkeypatch) -> None:
    package_dir = tmp_path / "package"
    package_dir.mkdir()
    (package_dir / "CesiumForUnreal.uplugin").write_text("{}\n", encoding="utf-8")
    json_out = tmp_path / "report.json"
    markdown_out = tmp_path / "report.md"

    monkeypatch.setattr(run_unreal_vendor_install_smoke, "resolve_unreal", lambda explicit, version: "/Applications/UnrealEditor")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_unreal_vendor_install_smoke.py",
            "--vendor",
            "cesium",
            "--package-dir",
            str(package_dir),
            "--project-dir",
            str(tmp_path / "project"),
            "--json-out",
            str(json_out),
            "--markdown-out",
            str(markdown_out),
            "--dry-run",
        ],
    )

    assert run_unreal_vendor_install_smoke.main() == 0
    payload = json.loads(json_out.read_text(encoding="utf-8"))
    assert payload["status"] == "dry-run"
    assert payload["plugin_name"] == "CesiumForUnreal"
    assert payload["command"][0] == "/Applications/UnrealEditor"


def test_main_classifies_missing_report_from_editor_log(monkeypatch, tmp_path: Path) -> None:
    package_dir = tmp_path / "package"
    package_dir.mkdir()
    (package_dir / "CesiumForUnreal.uplugin").write_text("{}\n", encoding="utf-8")
    json_out = tmp_path / "report.json"
    markdown_out = tmp_path / "report.md"

    monkeypatch.setattr(run_unreal_vendor_install_smoke, "resolve_unreal", lambda explicit, version: "/Applications/UnrealEditor")
    monkeypatch.setattr(
        run_unreal_vendor_install_smoke,
        "run_editor_until_report",
        lambda *args, **kwargs: (1, 3.0, False, False),
    )
    monkeypatch.setattr(
        run_unreal_vendor_install_smoke.unreal_editor_log,
        "summarize_editor_failure",
        lambda path: {"failure_kind": "plugin-version-incompatible", "detail": "version mismatch", "log_excerpt": []},
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_unreal_vendor_install_smoke.py",
            "--vendor",
            "cesium",
            "--package-dir",
            str(package_dir),
            "--project-dir",
            str(tmp_path / "project"),
            "--json-out",
            str(json_out),
            "--markdown-out",
            str(markdown_out),
        ],
    )

    assert run_unreal_vendor_install_smoke.main() == 1
    payload = json.loads(json_out.read_text(encoding="utf-8"))
    assert payload["status"] == "plugin-version-incompatible"
