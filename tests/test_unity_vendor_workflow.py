from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import unity_vendor_workflow


def test_doctor_payload_accepts_valid_layout(monkeypatch, tmp_path: Path) -> None:
    plugin_root = tmp_path / "cesium-unity"
    plugin_root.mkdir()
    (plugin_root / "package.json").write_text(json.dumps({"name": "com.cesium.unity", "unity": "2022.3"}) + "\n", encoding="utf-8")
    (plugin_root / "Source").mkdir()
    (plugin_root / "native~").mkdir()
    (plugin_root / "Reinterop~").mkdir()
    (plugin_root / "Build~").mkdir()
    (plugin_root / "Reinterop.dll").write_text("stub\n", encoding="utf-8")
    monkeypatch.setenv("FASTDIS_CESIUM_UNITY_PLUGIN_ROOT", str(plugin_root))
    monkeypatch.setattr(
        unity_vendor_workflow.unity_env,
        "resolve_install",
        lambda version=None: unity_vendor_workflow.unity_env.UnityInstall(
            version="6000.5.0f1",
            install_root=str(tmp_path / "Unity"),
            editor_path=str(tmp_path / "Unity" / "Editor" / "Unity.exe"),
            editor_app_path=None,
            source="env:FASTDIS_UNITY_EDITOR",
            quirks=(),
        ),
    )

    payload = unity_vendor_workflow.doctor_payload("cesium-unity", "6000.5", None)

    assert payload["status"] == "ok"
    assert payload["package_name"] == "com.cesium.unity"
    assert payload["source_checkout"] is True
    assert payload["source_checkout_prepared"] is True
    assert any(check["name"] == "package_manifest" and check["status"] == "ok" for check in payload["checks"])


def test_build_payload_dry_run_materializes_project(monkeypatch, tmp_path: Path) -> None:
    plugin_root = tmp_path / "cesium-unity"
    plugin_root.mkdir()
    (plugin_root / "package.json").write_text(json.dumps({"name": "com.cesium.unity", "unity": "2022.3"}) + "\n", encoding="utf-8")
    (plugin_root / "Reinterop~").mkdir()
    (plugin_root / "Build~").mkdir()
    (plugin_root / "Reinterop.dll").write_text("stub\n", encoding="utf-8")
    monkeypatch.setattr(
        unity_vendor_workflow.unity_env,
        "resolve_install",
        lambda version=None: unity_vendor_workflow.unity_env.UnityInstall(
            version="6000.5.0f1",
            install_root=str(tmp_path / "Unity"),
            editor_path=str(tmp_path / "Unity" / "Editor" / "Unity.exe"),
            editor_app_path=None,
            source="env:FASTDIS_UNITY_EDITOR",
            quirks=(),
        ),
    )
    project_dir = tmp_path / "project"

    payload = unity_vendor_workflow.build_payload(
        vendor="cesium-unity",
        version="6000.5",
        plugin_root_arg=str(plugin_root),
        project_dir_arg=str(project_dir),
        json_out_arg=str(tmp_path / "report.json"),
        md_out_arg=str(tmp_path / "report.md"),
        clean_project=False,
        dry_run=True,
    )

    manifest = json.loads((project_dir / "Packages" / "manifest.json").read_text(encoding="utf-8"))
    assert payload["status"] == "dry-run"
    assert "com.cesium.unity" in manifest["dependencies"]
    assert (project_dir / "Assets" / "Editor" / "CesiumUnityVendorSmoke.cs").is_file()


def test_prepare_source_runs_reinterop_publish(monkeypatch, tmp_path: Path) -> None:
    plugin_root = tmp_path / "cesium-unity"
    plugin_root.mkdir()
    (plugin_root / "Reinterop~").mkdir()
    (plugin_root / "Build~").mkdir()
    recorded: list[tuple[list[str], Path]] = []

    def fake_run(cmd: list[str], cwd: Path) -> int:
        recorded.append((cmd, cwd))
        (plugin_root / "Reinterop.dll").write_text("stub\n", encoding="utf-8")
        return 0

    monkeypatch.setattr(unity_vendor_workflow, "run_step_in_dir", fake_run)

    payload = unity_vendor_workflow.prepare_source_checkout("cesium-unity", str(plugin_root), dry_run=False)

    assert payload["status"] == "ok"
    assert recorded == [(["dotnet", "publish", "Reinterop~", "-o", "."], plugin_root)]
