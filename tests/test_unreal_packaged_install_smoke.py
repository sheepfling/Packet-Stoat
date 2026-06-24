from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import run_unreal_packaged_install_smoke


def test_create_scratch_project_installs_packaged_plugin(tmp_path: Path) -> None:
    package_dir = tmp_path / "package"
    (package_dir / "FastDis.uplugin").parent.mkdir(parents=True, exist_ok=True)
    (package_dir / "FastDis.uplugin").write_text('{"FriendlyName":"FastDIS"}\n', encoding="utf-8")
    (package_dir / "Content" / "Examples").mkdir(parents=True, exist_ok=True)
    (package_dir / "Content" / "Examples" / "FastDis_Demo.umap").write_text("demo\n", encoding="utf-8")
    project_dir = tmp_path / "project"

    project_path = run_unreal_packaged_install_smoke.create_scratch_project(project_dir, package_dir, clean=True)

    assert project_path.exists()
    plugin_dir = project_dir / "Plugins" / "FastDis"
    assert plugin_dir.exists()
    descriptor = json.loads(project_path.read_text(encoding="utf-8"))
    plugin_names = {plugin["Name"] for plugin in descriptor["Plugins"]}
    assert "FastDis" in plugin_names
    assert "PythonScriptPlugin" in plugin_names


def test_missing_package_writes_report(tmp_path: Path, monkeypatch) -> None:
    json_out = tmp_path / "report.json"
    markdown_out = tmp_path / "report.md"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_unreal_packaged_install_smoke.py",
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

    assert run_unreal_packaged_install_smoke.main() == 2
    payload = json.loads(json_out.read_text(encoding="utf-8"))
    assert payload["status"] == "missing-package"
    assert "Run the Unreal packaging flow first." in payload["details"][0]


def test_dry_run_writes_command_report(tmp_path: Path, monkeypatch) -> None:
    package_dir = tmp_path / "package"
    (package_dir / "FastDis.uplugin").parent.mkdir(parents=True, exist_ok=True)
    (package_dir / "FastDis.uplugin").write_text('{"FriendlyName":"FastDIS"}\n', encoding="utf-8")
    json_out = tmp_path / "report.json"
    markdown_out = tmp_path / "report.md"

    monkeypatch.setattr(run_unreal_packaged_install_smoke, "resolve_unreal", lambda explicit, version: "/Applications/UnrealEditor")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_unreal_packaged_install_smoke.py",
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

    assert run_unreal_packaged_install_smoke.main() == 0
    payload = json.loads(json_out.read_text(encoding="utf-8"))
    assert payload["status"] == "dry-run"
    assert payload["demo_map"] == "/FastDis/Examples/FastDis_Demo"
    assert payload["command"][0] == "/Applications/UnrealEditor"
