from __future__ import annotations

import json
from pathlib import Path
import sys
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import unreal_vendor_workflow


def test_vendor_slug_normalizes_input() -> None:
    assert unreal_vendor_workflow.vendor_slug("Cesium For Unreal") == "cesium-for-unreal"


def test_resolve_plugin_root_prefers_vendor_env(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("FASTDIS_CESIUM_PLUGIN_ROOT", str(tmp_path))

    resolved = unreal_vendor_workflow.resolve_plugin_root("cesium", None)

    assert resolved == tmp_path.resolve()


def test_resolve_uplugin_path_autodiscovers_single_descriptor(tmp_path: Path) -> None:
    (tmp_path / "CesiumForUnreal.uplugin").write_text("{}\n", encoding="utf-8")

    resolved = unreal_vendor_workflow.resolve_uplugin_path("cesium", tmp_path, None)

    assert resolved == (tmp_path / "CesiumForUnreal.uplugin").resolve()


def test_doctor_payload_reports_missing_plugin_root(monkeypatch) -> None:
    monkeypatch.delenv("FASTDIS_CESIUM_PLUGIN_ROOT", raising=False)
    monkeypatch.setattr(unreal_vendor_workflow, "install_for_version", lambda version: None)

    payload = unreal_vendor_workflow.doctor_payload("cesium", "5.8", None, None)

    assert payload["status"] == "needs-attention"
    assert any(check["name"] == "plugin_root" and check["status"] == "fail" for check in payload["checks"])


def test_build_command_invokes_buildplugin(monkeypatch, tmp_path: Path) -> None:
    plugin_root = tmp_path / "cesium"
    plugin_root.mkdir()
    descriptor = plugin_root / "CesiumForUnreal.uplugin"
    descriptor.write_text("{}\n", encoding="utf-8")
    (plugin_root / "Source" / "ThirdParty" / "include").mkdir(parents=True)
    (plugin_root / "Source" / "ThirdParty" / "lib" / "Windows-AMD64-Release").mkdir(parents=True)
    package_dir = tmp_path / "package"

    install = SimpleNamespace(version="5.8", install_root=str(tmp_path / "UE_5.8"))
    monkeypatch.setattr(unreal_vendor_workflow, "install_for_version", lambda version: install)
    monkeypatch.setattr(unreal_vendor_workflow.build_unreal_plugin, "host_platform_name", lambda: "Win64")
    monkeypatch.setattr(unreal_vendor_workflow.build_unreal_plugin, "parse_target_platforms", lambda raw, host: [host])
    monkeypatch.setattr(unreal_vendor_workflow.build_unreal_plugin, "validate_host_platform_or_warn", lambda engine_root, version: None)
    monkeypatch.setattr(unreal_vendor_workflow.build_unreal_plugin, "ensure_build_rules_compatibility", lambda engine_root: None)
    monkeypatch.setattr(unreal_vendor_workflow.build_unreal_plugin, "unreal_safe_dir", lambda path, label: path)
    monkeypatch.setattr(unreal_vendor_workflow.build_unreal_plugin, "uat_path", lambda engine_root: engine_root / "Engine" / "Build" / "BatchFiles" / "RunUAT.bat")

    recorded: list[list[str]] = []

    def fake_run(cmd: list[str]) -> None:
        recorded.append([str(part) for part in cmd])
        package_dir.mkdir(parents=True, exist_ok=True)
        (package_dir / "CesiumForUnreal.uplugin").write_text("{}\n", encoding="utf-8")

    monkeypatch.setattr(unreal_vendor_workflow.build_unreal_plugin, "run", fake_run)

    args = unreal_vendor_workflow.parse_args(
        [
            "build",
            "--vendor",
            "cesium",
            "--engine-version",
            "5.8",
            "--plugin-root",
            str(plugin_root),
            "--package-dir",
            str(package_dir),
            "--clean-package",
        ]
    )

    assert unreal_vendor_workflow.command_build(args) == 0
    assert recorded == [[
        str(Path(install.install_root) / "Engine" / "Build" / "BatchFiles" / "RunUAT.bat"),
        "BuildPlugin",
        f"-Plugin={descriptor.resolve()}",
        f"-Package={package_dir.resolve()}",
        "-TargetPlatforms=Win64",
    ]]


def test_matrix_writes_report(monkeypatch, tmp_path: Path) -> None:
    rows = []

    def fake_package_plugin(**kwargs: object) -> dict[str, object]:
        rows.append(str(kwargs["version"]))
        return {
            "status": "ok",
            "package_dir": str(tmp_path / str(kwargs["version"])),
        }

    monkeypatch.setattr(unreal_vendor_workflow, "package_plugin", fake_package_plugin)
    monkeypatch.setattr(unreal_vendor_workflow, "command_install_smoke", lambda args: 0)
    json_out = tmp_path / "matrix.json"
    md_out = tmp_path / "matrix.md"
    args = unreal_vendor_workflow.parse_args(
        [
            "matrix",
            "--vendor",
            "cesium",
            "--versions",
            "5.7",
            "5.8",
            "--json-out",
            str(json_out),
            "--md-out",
            str(md_out),
        ]
    )

    assert unreal_vendor_workflow.command_matrix(args) == 0
    assert rows == ["5.7", "5.8"]
    payload = json.loads(json_out.read_text(encoding="utf-8"))
    assert payload["overall_status"] == "ok"
    assert [row["version"] for row in payload["results"]] == ["5.7", "5.8"]
    assert all(row["install_smoke_status"] == "ok" for row in payload["results"])
    assert md_out.is_file()


def test_doctor_payload_reports_unprepared_source_checkout(monkeypatch, tmp_path: Path) -> None:
    plugin_root = tmp_path / "cesium-unreal"
    plugin_root.mkdir()
    (plugin_root / "CesiumForUnreal.uplugin").write_text("{}\n", encoding="utf-8")
    (plugin_root / "extern").mkdir()
    (plugin_root / "extern" / "CMakeLists.txt").write_text("cmake_minimum_required(VERSION 3.15)\n", encoding="utf-8")
    monkeypatch.setattr(
        unreal_vendor_workflow,
        "install_for_version",
        lambda version: SimpleNamespace(
            version="5.7",
            install_root=str(tmp_path / "UE_5.7"),
            editor_path=str(tmp_path / "UE_5.7" / "Editor.exe"),
            uat_path=str(tmp_path / "UE_5.7" / "RunUAT.bat"),
            ubt_path=str(tmp_path / "UE_5.7" / "UnrealBuildTool.dll"),
            dotnet_path=str(tmp_path / "UE_5.7" / "dotnet.exe"),
            to_dict=lambda: {"version": "5.7"},
        ),
    )
    monkeypatch.setattr(unreal_vendor_workflow.unreal_env, "permission_probe", lambda install: {"checks": []})

    payload = unreal_vendor_workflow.doctor_payload("cesium", "5.7", str(plugin_root), None)

    assert payload["status"] == "needs-attention"
    assert payload["source_checkout"] is True
    assert payload["source_checkout_prepared"] is False
    assert any(check["name"] == "third_party_include" and check["status"] == "fail" for check in payload["checks"])


def test_prepare_source_runs_cmake(monkeypatch, tmp_path: Path) -> None:
    plugin_root = tmp_path / "cesium-unreal"
    plugin_root.mkdir()
    (plugin_root / "extern").mkdir()
    (plugin_root / "extern" / "CMakeLists.txt").write_text("cmake_minimum_required(VERSION 3.15)\n", encoding="utf-8")
    install = SimpleNamespace(version="5.7", install_root=str(tmp_path / "UE_5.7"))
    monkeypatch.setattr(unreal_vendor_workflow, "install_for_version", lambda version: install)
    recorded: list[tuple[list[str], Path]] = []

    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    def fake_subprocess_run(cmd: list[str], cwd: Path, env: dict[str, str]) -> Completed:
        recorded.append((cmd, cwd))
        (plugin_root / "Source" / "ThirdParty" / "include").mkdir(parents=True, exist_ok=True)
        (plugin_root / "Source" / "ThirdParty" / "lib" / "Windows-AMD64-Release").mkdir(parents=True, exist_ok=True)
        return Completed(0)

    monkeypatch.setattr(unreal_vendor_workflow.subprocess, "run", fake_subprocess_run)

    payload = unreal_vendor_workflow.prepare_source_checkout(
        vendor="cesium",
        version="5.7",
        plugin_root_arg=str(plugin_root),
        clean_build=False,
        build_type="Release",
        dry_run=False,
    )

    assert payload["status"] == "ok"
    assert len(recorded) == 2
    assert recorded[0][0][:3] == ["cmake", "-B", str(plugin_root / "extern" / "build-fastdis")]
    assert recorded[1][0][:4] == ["cmake", "--build", str(plugin_root / "extern" / "build-fastdis"), "--target"]


def test_install_smoke_command_builds_expected_runner(monkeypatch, tmp_path: Path) -> None:
    plugin_root = tmp_path / "cesium"
    plugin_root.mkdir()
    (plugin_root / "CesiumForUnreal.uplugin").write_text("{}\n", encoding="utf-8")

    recorded: list[list[str]] = []
    monkeypatch.setattr(unreal_vendor_workflow, "run_step", lambda cmd: recorded.append(cmd) or 0)

    args = unreal_vendor_workflow.parse_args(
        [
            "install-smoke",
            "--vendor",
            "cesium",
            "--engine-version",
            "5.7",
            "--plugin-root",
            str(plugin_root),
            "--package-dir",
            str(tmp_path / "package"),
            "--project-dir",
            str(tmp_path / "project"),
            "--clean-project",
            "--dry-run",
        ]
    )

    assert unreal_vendor_workflow.command_install_smoke(args) == 0
    assert recorded == [[
        sys.executable,
        "tools/run_unreal_vendor_install_smoke.py",
        "--vendor",
        "cesium",
        "--engine-version",
        "5.7",
        "--package-dir",
        str((tmp_path / "package").resolve()),
        "--project-dir",
        str((tmp_path / "project").resolve()),
        "--json-out",
        str((unreal_vendor_workflow.DEFAULT_REPORT_DIR / "cesium_5_7_install_smoke.json").resolve()),
        "--markdown-out",
        str((unreal_vendor_workflow.DEFAULT_REPORT_DIR / "cesium_5_7_install_smoke.md").resolve()),
        "--clean-project",
        "--dry-run",
    ]]
