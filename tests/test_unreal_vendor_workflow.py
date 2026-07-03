from __future__ import annotations

import json
from pathlib import Path
import stat
import subprocess
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
    assert any(check["name"] == "discovery roots" and "FASTDIS_UNREAL_ROOTS" in check["detail"] for check in payload["checks"])


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
    assert any(check["name"] == "version kind" and check["detail"] == "stable" for check in payload["checks"])


def test_doctor_payload_flags_windows_toolchain_mismatch(monkeypatch, tmp_path: Path) -> None:
    plugin_root = tmp_path / "cesium-unreal"
    plugin_root.mkdir()
    (plugin_root / "CesiumForUnreal.uplugin").write_text("{}\n", encoding="utf-8")
    (plugin_root / "extern" / "build-fastdis").mkdir(parents=True)
    (plugin_root / "extern" / "CMakeLists.txt").write_text("cmake_minimum_required(VERSION 3.15)\n", encoding="utf-8")
    (plugin_root / "Source" / "ThirdParty" / "include").mkdir(parents=True)
    (plugin_root / "Source" / "ThirdParty" / "lib" / "Windows-AMD64-Release").mkdir(parents=True)
    (plugin_root / "extern" / "build-fastdis" / "CMakeCache.txt").write_text(
        "CMAKE_GENERATOR:INTERNAL=Visual Studio 18 2026\n"
        "CMAKE_LINKER:FILEPATH=C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231/bin/Hostx64/x64/link.exe\n",
        encoding="utf-8",
    )
    engine_root = tmp_path / "UE_5.7"
    (engine_root / "Engine" / "Config" / "Windows").mkdir(parents=True)
    (engine_root / "Engine" / "Config" / "Windows" / "Windows_SDK.json").write_text(
        json.dumps({"PreferredVisualCppVersions": ["14.44.35207-14.44.99999"]}) + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        unreal_vendor_workflow,
        "install_for_version",
        lambda version: SimpleNamespace(
            version="5.7",
            install_root=str(engine_root),
            editor_path=str(engine_root / "Editor.exe"),
            uat_path=str(engine_root / "RunUAT.bat"),
            ubt_path=str(engine_root / "UnrealBuildTool.dll"),
            dotnet_path=str(engine_root / "dotnet.exe"),
            to_dict=lambda: {"version": "5.7"},
        ),
    )
    monkeypatch.setattr(unreal_vendor_workflow.unreal_env, "permission_probe", lambda install: {"checks": []})

    payload = unreal_vendor_workflow.doctor_payload("cesium", "5.7", str(plugin_root), None)

    assert any(check["name"] == "preferred_msvc_toolchain" and "14.44" in check["detail"] for check in payload["checks"])
    assert any(check["name"] == "source_prep_toolchain" and check["status"] == "fail" for check in payload["checks"])


def test_resolve_msvc_toolchain_falls_forward_when_installed_preferred_is_banned(monkeypatch, tmp_path: Path) -> None:
    engine_root = tmp_path / "UE_5.8"
    (engine_root / "Engine" / "Config" / "Windows").mkdir(parents=True)
    (engine_root / "Engine" / "Config" / "Windows" / "Windows_SDK.json").write_text(
        json.dumps(
                {
                    "PreferredVisualCppVersions": ["14.50.35717-14.50.99999", "14.44.35207-14.44.99999"],
                    "BannedVisualCppVersions": ["14.50.0-14.50.35722", "14.44.0-14.44.35210"],
                    "MinimumVisualCppVersion": "14.38.33130",
                }
            )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(unreal_vendor_workflow, "installed_msvc_toolchains", lambda: ["14.44.35207", "14.51.36231"])

    resolved = unreal_vendor_workflow.resolve_msvc_toolchain(SimpleNamespace(install_root=str(engine_root)))

    assert resolved is not None
    assert resolved["selected_version"] == "14.51.36231"
    assert resolved["selected_family"] == "14.51"
    assert resolved["selection_reason"] == "fallback"


def test_install_for_version_prefers_sorted_default(monkeypatch) -> None:
    stable = SimpleNamespace(version="5.8", install_root="C:/Epic/UE_5.8")
    preview = SimpleNamespace(version="5.9-preview1", install_root="C:/Epic/UE_5.9-preview1")
    monkeypatch.setattr(unreal_vendor_workflow.unreal_env, "discover_installs", lambda: [stable, preview])

    install = unreal_vendor_workflow.install_for_version(None)

    assert install is stable


def test_discover_prints_root_hint_when_missing(monkeypatch, capsys) -> None:
    monkeypatch.setattr(unreal_vendor_workflow.unreal_env, "discover_installs", lambda: [])

    rc = unreal_vendor_workflow.command_discover(type("Args", (), {"format": "table"})())
    out = capsys.readouterr().out

    assert rc == 1
    assert "No Unreal installs discovered." in out
    assert "FASTDIS_UNREAL_ROOTS" in out


def test_prepare_source_runs_cmake(monkeypatch, tmp_path: Path) -> None:
    plugin_root = tmp_path / "cesium-unreal"
    plugin_root.mkdir()
    (plugin_root / "extern").mkdir()
    (plugin_root / "extern" / "CMakeLists.txt").write_text("cmake_minimum_required(VERSION 3.15)\n", encoding="utf-8")
    install_root = tmp_path / "UE_5.7"
    (install_root / "Engine" / "Config" / "Windows").mkdir(parents=True)
    (install_root / "Engine" / "Config" / "Windows" / "Windows_SDK.json").write_text(
        json.dumps({"PreferredVisualCppVersions": ["14.44.35207-14.44.99999"]}) + "\n",
        encoding="utf-8",
    )
    install = SimpleNamespace(version="5.7", install_root=str(install_root))
    monkeypatch.setattr(unreal_vendor_workflow, "install_for_version", lambda version: install)
    monkeypatch.setattr(
        unreal_vendor_workflow,
        "installed_msvc_toolchains",
        lambda: ["14.44.35207", "14.51.36231"],
    )
    recorded: list[tuple[list[str], Path]] = []

    class Completed:
        def __init__(self, returncode: int, stdout: str = "") -> None:
            self.returncode = returncode
            self.stdout = stdout

    def fake_subprocess_run(cmd: list[str], cwd: Path, env: dict[str, str], **kwargs: object) -> Completed:
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
    assert "Visual Studio 18 2026" in recorded[0][0]
    assert "-T" not in recorded[0][0]
    assert recorded[1][0][:4] == ["cmake", "--build", str(plugin_root / "extern" / "build-fastdis"), "--target"]
    assert payload["preferred_msvc_toolchain"]["family"] == "14.44"
    assert payload["resolved_msvc_toolchain"]["selected_version"] == "14.44.35207"
    assert payload["process_provenance"]["process_matters_as_evidence"] is True


def test_normalize_tinyxml2_config_rewrites_backslashes(tmp_path: Path) -> None:
    config = tmp_path / "home" / ".ezvcpkg" / "abc" / "installed" / "x64-windows-unreal" / "share" / "tinyxml2" / "tinyxml2Config.cmake"
    config.parent.mkdir(parents=True)
    config.write_text('set(tinyxml2_LIBRARIES "C:\\\\Program Files\\\\Epic Games\\\\UE_5.7\\\\tinyxml2.lib")\n', encoding="utf-8")

    normalized = unreal_vendor_workflow.normalize_tinyxml2_config(tmp_path)

    assert normalized == [str(config)]
    assert "\\Program Files\\" not in config.read_text(encoding="utf-8")


def test_remove_tree_clears_read_only_file(tmp_path: Path) -> None:
    root = tmp_path / "tree"
    root.mkdir()
    child = root / "file.txt"
    child.write_text("x\n", encoding="utf-8")
    child.chmod(stat.S_IREAD)

    unreal_vendor_workflow.remove_tree(root)

    assert not root.exists()


def test_install_smoke_command_builds_expected_runner(monkeypatch, tmp_path: Path) -> None:
    plugin_root = tmp_path / "cesium"
    plugin_root.mkdir()
    (plugin_root / "CesiumForUnreal.uplugin").write_text("{}\n", encoding="utf-8")

    payload = unreal_vendor_workflow.install_smoke_report_payload(
        vendor="cesium",
        version="5.7",
        plugin_root_arg=str(plugin_root),
        uplugin_arg=None,
        package_dir_arg=str(tmp_path / "package"),
        project_dir_arg=str(tmp_path / "project"),
        json_out_arg=None,
        md_out_arg=None,
        clean_project=True,
        dry_run=True,
    )

    assert payload["status"] == "dry-run"
    assert payload["command"] == [
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
    ]


def test_build_report_payload_captures_buildplugin_failure(monkeypatch, tmp_path: Path) -> None:
    plugin_root = tmp_path / "cesium"
    plugin_root.mkdir()
    descriptor = plugin_root / "CesiumForUnreal.uplugin"
    descriptor.write_text("{}\n", encoding="utf-8")
    (plugin_root / "Source" / "ThirdParty" / "include").mkdir(parents=True)
    (plugin_root / "Source" / "ThirdParty" / "lib" / "Windows-AMD64-Release").mkdir(parents=True)
    install = SimpleNamespace(version="5.8", install_root=str(tmp_path / "UE_5.8"))
    monkeypatch.setattr(unreal_vendor_workflow, "install_for_version", lambda version: install)
    monkeypatch.setattr(unreal_vendor_workflow.build_unreal_plugin, "host_platform_name", lambda: "Win64")
    monkeypatch.setattr(unreal_vendor_workflow.build_unreal_plugin, "parse_target_platforms", lambda raw, host: [host])
    monkeypatch.setattr(unreal_vendor_workflow.build_unreal_plugin, "validate_host_platform_or_warn", lambda engine_root, version: None)
    monkeypatch.setattr(unreal_vendor_workflow.build_unreal_plugin, "ensure_build_rules_compatibility", lambda engine_root: None)
    monkeypatch.setattr(unreal_vendor_workflow.build_unreal_plugin, "unreal_safe_dir", lambda path, label: path)
    monkeypatch.setattr(unreal_vendor_workflow.build_unreal_plugin, "uat_path", lambda engine_root: engine_root / "Engine" / "Build" / "BatchFiles" / "RunUAT.bat")

    def fake_run(cmd: list[str]) -> None:
        raise subprocess.CalledProcessError(6, cmd, output="error C2664: compile failed\n")

    monkeypatch.setattr(unreal_vendor_workflow.build_unreal_plugin, "run", fake_run)

    payload = unreal_vendor_workflow.build_report_payload(
        vendor="cesium",
        version="5.8",
        plugin_root_arg=str(plugin_root),
        uplugin_arg=None,
        package_dir_arg=str(tmp_path / "package"),
        target_platforms_arg=None,
        clean_package=False,
        skip_platform_probe=False,
        dry_run=False,
    )

    assert payload["status"] == "fail"
    assert "error C2664" in payload["raw_output"]
    assert payload["build_command"][1] == "BuildPlugin"


def test_handoff_payload_formats_upstream_issue_for_58_failure(monkeypatch, tmp_path: Path) -> None:
    plugin_root = tmp_path / "cesium"
    plugin_root.mkdir()
    descriptor = plugin_root / "CesiumForUnreal.uplugin"
    descriptor.write_text("{}\n", encoding="utf-8")
    (plugin_root / "Source" / "ThirdParty" / "include").mkdir(parents=True)
    (plugin_root / "Source" / "ThirdParty" / "lib" / "Windows-AMD64-Release").mkdir(parents=True)
    install = SimpleNamespace(version="5.8", install_root=str(tmp_path / "UE_5.8"))
    monkeypatch.setattr(unreal_vendor_workflow, "install_for_version", lambda version: install)
    monkeypatch.setattr(unreal_vendor_workflow.build_unreal_plugin, "host_platform_name", lambda: "Win64")
    monkeypatch.setattr(unreal_vendor_workflow.build_unreal_plugin, "parse_target_platforms", lambda raw, host: [host])
    monkeypatch.setattr(unreal_vendor_workflow.build_unreal_plugin, "validate_host_platform_or_warn", lambda engine_root, version: None)
    monkeypatch.setattr(unreal_vendor_workflow.build_unreal_plugin, "ensure_build_rules_compatibility", lambda engine_root: None)
    monkeypatch.setattr(unreal_vendor_workflow.build_unreal_plugin, "unreal_safe_dir", lambda path, label: path)
    monkeypatch.setattr(unreal_vendor_workflow.build_unreal_plugin, "uat_path", lambda engine_root: engine_root / "Engine" / "Build" / "BatchFiles" / "RunUAT.bat")

    def fake_run(cmd: list[str]) -> None:
        raise subprocess.CalledProcessError(6, cmd, output="error C2664: compile failed\n")

    monkeypatch.setattr(unreal_vendor_workflow.build_unreal_plugin, "run", fake_run)

    args = unreal_vendor_workflow.parse_args(
        [
            "handoff",
            "--vendor",
            "cesium",
            "--engine-version",
            "5.8",
            "--plugin-root",
            str(plugin_root),
            "--package-dir",
            str(tmp_path / "package"),
            "--json-out",
            str(tmp_path / "handoff.json"),
            "--md-out",
            str(tmp_path / "handoff.md"),
        ]
    )

    payload = unreal_vendor_workflow.handoff_payload(args)

    assert payload["schema"] == "packet_stoat.cesium_unreal_upstream_handoff.v1"
    assert payload["status"] == "ready"
    assert payload["failure_class"] == "compile-or-link"
    assert "baseline_version: `5.7`" in payload["issue_body_markdown"]
    assert "error C2664" in payload["issue_body_markdown"]


def test_handoff_command_writes_outputs(monkeypatch, tmp_path: Path, capsys) -> None:
    plugin_root = tmp_path / "cesium"
    plugin_root.mkdir()
    descriptor = plugin_root / "CesiumForUnreal.uplugin"
    descriptor.write_text("{}\n", encoding="utf-8")
    (plugin_root / "Source" / "ThirdParty" / "include").mkdir(parents=True)
    (plugin_root / "Source" / "ThirdParty" / "lib" / "Windows-AMD64-Release").mkdir(parents=True)
    install = SimpleNamespace(version="5.8", install_root=str(tmp_path / "UE_5.8"))
    monkeypatch.setattr(unreal_vendor_workflow, "install_for_version", lambda version: install)
    monkeypatch.setattr(unreal_vendor_workflow.build_unreal_plugin, "host_platform_name", lambda: "Win64")
    monkeypatch.setattr(unreal_vendor_workflow.build_unreal_plugin, "parse_target_platforms", lambda raw, host: [host])
    monkeypatch.setattr(unreal_vendor_workflow.build_unreal_plugin, "validate_host_platform_or_warn", lambda engine_root, version: None)
    monkeypatch.setattr(unreal_vendor_workflow.build_unreal_plugin, "ensure_build_rules_compatibility", lambda engine_root: None)
    monkeypatch.setattr(unreal_vendor_workflow.build_unreal_plugin, "unreal_safe_dir", lambda path, label: path)
    monkeypatch.setattr(unreal_vendor_workflow.build_unreal_plugin, "uat_path", lambda engine_root: engine_root / "Engine" / "Build" / "BatchFiles" / "RunUAT.bat")

    def fake_run(cmd: list[str]) -> None:
        raise subprocess.CalledProcessError(6, cmd, output="error C2664: compile failed\n")

    monkeypatch.setattr(unreal_vendor_workflow.build_unreal_plugin, "run", fake_run)

    rc = unreal_vendor_workflow.main(
        [
            "handoff",
            "--vendor",
            "cesium",
            "--engine-version",
            "5.8",
            "--plugin-root",
            str(plugin_root),
            "--package-dir",
            str(tmp_path / "package"),
            "--json-out",
            str(tmp_path / "handoff.json"),
            "--md-out",
            str(tmp_path / "handoff.md"),
        ]
    )
    out = capsys.readouterr().out

    assert rc == 0
    payload = json.loads(out)
    assert payload["handoff_json"] == str((tmp_path / "handoff.json").resolve())
    assert (tmp_path / "handoff.json").is_file()
    assert (tmp_path / "handoff.md").is_file()
