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


def test_resolve_cmake_executable_prefers_scoop_install(monkeypatch, tmp_path: Path) -> None:
    scoop_cmake = tmp_path / "scoop" / "apps" / "cmake" / "current" / "bin" / "cmake.exe"
    scoop_cmake.parent.mkdir(parents=True, exist_ok=True)
    scoop_cmake.write_text("", encoding="utf-8")
    monkeypatch.setattr(unreal_vendor_workflow.shutil, "which", lambda name: None)
    monkeypatch.setattr(unreal_vendor_workflow.Path, "home", lambda: tmp_path)

    assert unreal_vendor_workflow.resolve_cmake_executable() == str(scoop_cmake)


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

    monkeypatch.setattr(unreal_vendor_workflow, "_run_buildplugin_with_progress", lambda cmd, progress, vendor, version: fake_run(cmd))

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


def test_progress_report_writes_snapshot_and_event_log(tmp_path: Path) -> None:
    progress_json = tmp_path / "progress.json"
    progress_md = tmp_path / "progress.md"
    events_jsonl = tmp_path / "progress.jsonl"
    payload = unreal_vendor_workflow.progress_payload(
        vendor="cesium",
        version="5.8",
        resolved_toolchain={
            "selected_version": "14.50.35735",
            "selected_folder_version": "14.50.35717",
            "selection_reason": "preferred",
        },
        json_out=progress_json,
        md_out=progress_md,
    )
    payload["events_jsonl"] = str(events_jsonl)

    unreal_vendor_workflow.update_progress_report(
        payload,
        json_out=progress_json,
        md_out=progress_md,
        phase="buildplugin_editor",
        current_log="phase buildplugin_editor",
        last_log_line="Building UnrealEditor...",
        last_completed_step="automationtool",
        pid=1234,
    )
    unreal_vendor_workflow.append_progress_event(
        events_jsonl,
        vendor="cesium",
        version="5.8",
        event="phase_changed",
        phase="buildplugin_editor",
        detail="Building UnrealEditor...",
    )

    snapshot = json.loads(progress_json.read_text(encoding="utf-8"))
    assert snapshot["phase"] == "buildplugin_editor"
    assert snapshot["selected_compiler_version"] == "14.50.35735"
    assert snapshot["pid"] == 1234
    assert "Building UnrealEditor..." in progress_md.read_text(encoding="utf-8")
    events = [json.loads(line) for line in events_jsonl.read_text(encoding="utf-8").splitlines()]
    assert events[0]["event"] == "phase_changed"
    assert events[0]["phase"] == "buildplugin_editor"


def test_phase_from_build_output_detects_linux_game_phases() -> None:
    phase, completed = unreal_vendor_workflow._phase_from_build_output(
        'Running: dotnet UnrealBuildTool.dll UnrealGame Linux Development -Project="/tmp/HostProject.uproject"',
        "buildplugin_editor",
    )
    assert phase == "buildplugin_game_development"
    assert completed is None

    phase, completed = unreal_vendor_workflow._phase_from_build_output(
        'Running: dotnet UnrealBuildTool.dll UnrealGame Linux Shipping -Project="/tmp/HostProject.uproject"',
        phase,
    )
    assert phase == "buildplugin_game_shipping"
    assert completed is None


def test_build_report_payload_includes_progress_paths(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(unreal_vendor_workflow, "DEFAULT_REPORT_DIR", tmp_path / "reports")
    monkeypatch.setattr(
        unreal_vendor_workflow,
        "install_for_version",
        lambda version: SimpleNamespace(version="5.8", install_root=str(tmp_path / "UE_5.8")),
    )
    monkeypatch.setattr(
        unreal_vendor_workflow,
        "resolve_msvc_toolchain",
        lambda install: {
            "selected_version": "14.50.35735",
            "selected_folder_version": "14.50.35717",
            "selection_reason": "preferred",
        },
    )
    monkeypatch.setattr(
        unreal_vendor_workflow,
        "package_plugin",
        lambda **kwargs: {
            "vendor": "cesium",
            "engine_version": "5.8",
            "plugin_root": str(tmp_path / "plugin"),
            "uplugin": str(tmp_path / "plugin" / "CesiumForUnreal.uplugin"),
            "package_dir": str(tmp_path / "package"),
            "target_platforms": ["Win64"],
            "build_command": ["RunUAT.bat", "BuildPlugin"],
            "status": "ok",
            "process_provenance": {},
        },
    )

    payload = unreal_vendor_workflow.build_report_payload(
        vendor="cesium",
        version="5.8",
        plugin_root_arg=None,
        uplugin_arg=None,
        package_dir_arg=None,
        target_platforms_arg=None,
        clean_package=False,
        skip_platform_probe=False,
        dry_run=False,
    )

    assert payload["status"] == "ok"
    assert str(payload["progress_json"]).endswith("cesium_5_8_progress.json")
    assert str(payload["progress_markdown"]).endswith("cesium_5_8_progress.md")
    assert str(payload["progress_events_jsonl"]).endswith("cesium_5_8_progress.jsonl")


def test_matrix_writes_report(monkeypatch, tmp_path: Path) -> None:
    rows = []
    prepares = []

    def fake_prepare_source_checkout(**kwargs: object) -> dict[str, object]:
        prepares.append(str(kwargs["version"]))
        return {
            "status": "ok",
            "resolved_msvc_toolchain": {
                "selected_version": f"{kwargs['version']}.compiler",
                "selected_folder_version": f"{kwargs['version']}.folder",
                "selection_reason": "preferred",
            },
        }

    def fake_build_report_payload(**kwargs: object) -> dict[str, object]:
        rows.append(str(kwargs["version"]))
        return {
            "vendor": "cesium",
            "engine_version": str(kwargs["version"]),
            "plugin_root": str(tmp_path / "plugin"),
            "uplugin": str(tmp_path / "plugin" / "CesiumForUnreal.uplugin"),
            "package_dir": str(tmp_path / str(kwargs["version"])),
            "target_platforms": ["Win64"],
            "build_command": ["RunUAT.bat", "BuildPlugin"],
            "status": "ok",
            "process_provenance": {},
        }

    monkeypatch.setattr(unreal_vendor_workflow, "prepare_source_checkout", fake_prepare_source_checkout)
    monkeypatch.setattr(unreal_vendor_workflow, "build_report_payload", fake_build_report_payload)
    monkeypatch.setattr(unreal_vendor_workflow, "command_install_smoke", lambda args: 0)
    monkeypatch.setattr(unreal_vendor_workflow, "plugin_uses_source_checkout", lambda plugin_root: True)
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
    assert prepares == ["5.7", "5.8"]
    assert rows == ["5.7", "5.8"]
    payload = json.loads(json_out.read_text(encoding="utf-8"))
    assert payload["overall_status"] == "ok"
    assert [row["version"] for row in payload["results"]] == ["5.7", "5.8"]
    assert all(row["install_smoke_status"] == "ok" for row in payload["results"])
    assert payload["results"][0]["prepare_source_status"] == "ok"
    assert payload["results"][0]["selected_compiler_version"] == "5.7.compiler"
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
    monkeypatch.setattr(
        unreal_vendor_workflow,
        "installed_msvc_toolchain_details",
        lambda: [
            {"folder_version": "14.44.35207", "compiler_version": "14.44.35207", "family": "14.44"},
            {"folder_version": "14.51.36231", "compiler_version": "14.51.36231", "family": "14.51"},
        ],
    )

    resolved = unreal_vendor_workflow.resolve_msvc_toolchain(SimpleNamespace(install_root=str(engine_root)))

    assert resolved is not None
    assert resolved["selected_version"] == "14.51.36231"
    assert resolved["selected_folder_version"] == "14.51.36231"
    assert resolved["selected_family"] == "14.51"
    assert resolved["selection_reason"] == "fallback"


def test_resolve_msvc_toolchain_uses_actual_compiler_version_from_folder(monkeypatch, tmp_path: Path) -> None:
    engine_root = tmp_path / "UE_5.8"
    (engine_root / "Engine" / "Config" / "Windows").mkdir(parents=True)
    (engine_root / "Engine" / "Config" / "Windows" / "Windows_SDK.json").write_text(
        json.dumps(
            {
                "PreferredVisualCppVersions": ["14.50.35717-14.50.99999"],
                "BannedVisualCppVersions": ["14.50.0-14.50.35722"],
                "MinimumVisualCppVersion": "14.38.33130",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        unreal_vendor_workflow,
        "installed_msvc_toolchain_details",
        lambda: [
            {"folder_version": "14.50.35717", "compiler_version": "14.50.35735", "family": "14.50"},
            {"folder_version": "14.51.36231", "compiler_version": "14.51.36231", "family": "14.51"},
        ],
    )

    resolved = unreal_vendor_workflow.resolve_msvc_toolchain(SimpleNamespace(install_root=str(engine_root)))

    assert resolved is not None
    assert resolved["selected_version"] == "14.50.35735"
    assert resolved["selected_folder_version"] == "14.50.35717"
    assert resolved["selected_family"] == "14.50"
    assert resolved["selection_reason"] == "preferred"


def test_resolve_msvc_toolchain_honors_unreal_preference_order(monkeypatch, tmp_path: Path) -> None:
    engine_root = tmp_path / "UE_5.8"
    (engine_root / "Engine" / "Config" / "Windows").mkdir(parents=True)
    (engine_root / "Engine" / "Config" / "Windows" / "Windows_SDK.json").write_text(
        json.dumps(
            {
                "PreferredVisualCppVersions": ["14.50.35717-14.50.99999", "14.44.35207-14.44.99999"],
                "BannedVisualCppVersions": ["14.50.0-14.50.35722", "14.44.0-14.44.35210"],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        unreal_vendor_workflow,
        "installed_msvc_toolchain_details",
        lambda: [
            {"folder_version": "14.44.35207", "compiler_version": "14.44.35228", "family": "14.44"},
            {"folder_version": "14.50.35717", "compiler_version": "14.50.35735", "family": "14.50"},
        ],
    )

    resolved = unreal_vendor_workflow.resolve_msvc_toolchain(SimpleNamespace(install_root=str(engine_root)))

    assert resolved is not None
    assert resolved["selected_version"] == "14.50.35735"
    assert resolved["selected_folder_version"] == "14.50.35717"


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
        "installed_msvc_toolchain_details",
        lambda: [
            {"folder_version": "14.44.35207", "compiler_version": "14.44.35207", "family": "14.44"},
            {"folder_version": "14.51.36231", "compiler_version": "14.51.36231", "family": "14.51"},
        ],
    )
    monkeypatch.setattr(unreal_vendor_workflow, "resolve_cmake_executable", lambda: r"C:\Tools\cmake.exe")
    monkeypatch.setattr(
        unreal_vendor_workflow.unreal_env,
        "build_env",
        lambda: {"UNREAL_ENGINE_ROOT": str(install_root), "FASTDIS_UNREAL_WORK_ROOT": str(tmp_path / "work")},
    )
    recorded: list[tuple[list[str], Path, dict[str, str]]] = []

    class Completed:
        def __init__(self, returncode: int, stdout: str = "") -> None:
            self.returncode = returncode
            self.stdout = stdout

    def fake_subprocess_run(cmd: list[str], cwd: Path, env: dict[str, str], **kwargs: object) -> Completed:
        recorded.append((cmd, cwd, dict(env)))
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
    assert recorded[0][0][:3] == [r"C:\Tools\cmake.exe", "-B", str(plugin_root / "extern" / "build-fastdis")]
    assert unreal_vendor_workflow.WINDOWS_CMAKE_GENERATOR in recorded[0][0]
    assert "-T" not in recorded[0][0]
    assert recorded[1][0][:4] == [r"C:\Tools\cmake.exe", "--build", str(plugin_root / "extern" / "build-fastdis"), "--target"]
    assert recorded[0][2]["GIT_SSL_NO_VERIFY"] == "true"
    assert recorded[0][2]["VCPKG_FORCE_SYSTEM_BINARIES"] == "1"
    assert recorded[0][2]["PATH"].split(";")[0] == str(tmp_path / "work" / "bin")
    assert recorded[0][2]["PATH"].split(";")[1] == r"C:\Tools"
    assert (tmp_path / "work" / "bin" / "pwsh.cmd").is_file()
    assert payload["preferred_msvc_toolchain"]["family"] == "14.44"
    assert payload["resolved_msvc_toolchain"]["selected_version"] == "14.44.35207"
    assert payload["resolved_msvc_toolchain"]["selected_folder_version"] == "14.44.35207"
    assert payload["process_provenance"]["process_matters_as_evidence"] is True


def test_prepare_source_uses_unreal_linux_toolchain_when_compiler_dir_present(monkeypatch, tmp_path: Path) -> None:
    plugin_root = tmp_path / "cesium-unreal"
    extern_root = plugin_root / "extern"
    plugin_root.mkdir()
    extern_root.mkdir()
    (extern_root / "CMakeLists.txt").write_text("cmake_minimum_required(VERSION 3.15)\n", encoding="utf-8")
    (extern_root / "unreal-linux-toolchain.cmake").write_text("set(CMAKE_SYSTEM_NAME Linux)\n", encoding="utf-8")
    install_root = tmp_path / "UE_5.8"
    install = SimpleNamespace(version="5.8", install_root=str(install_root))
    monkeypatch.setattr(unreal_vendor_workflow, "install_for_version", lambda version: install)
    monkeypatch.setattr(unreal_vendor_workflow.unreal_env.platform, "system", lambda: "Linux")
    monkeypatch.setenv("UNREAL_ENGINE_COMPILER_DIR", "/opt/unreal-toolchain/x86_64-unknown-linux-gnu")
    monkeypatch.setattr(unreal_vendor_workflow, "resolve_cmake_executable", lambda: "cmake")
    recorded: list[tuple[list[str], Path, dict[str, str]]] = []

    class Completed:
        def __init__(self, returncode: int, stdout: str = "") -> None:
            self.returncode = returncode
            self.stdout = stdout

    def fake_build_env() -> dict[str, str]:
        return {
            "UNREAL_ENGINE_COMPILER_DIR": "/opt/unreal-toolchain/x86_64-unknown-linux-gnu",
            "FASTDIS_UNREAL_WORK_ROOT": str(tmp_path / "work"),
        }

    def fake_subprocess_run(cmd: list[str], cwd: Path, env: dict[str, str], **kwargs: object) -> Completed:
        recorded.append((cmd, cwd, dict(env)))
        (plugin_root / "Source" / "ThirdParty" / "include").mkdir(parents=True, exist_ok=True)
        (plugin_root / "Source" / "ThirdParty" / "lib" / "Linux-x86_64-Release").mkdir(parents=True, exist_ok=True)
        return Completed(0)

    monkeypatch.setattr(unreal_vendor_workflow.unreal_env, "build_env", fake_build_env)
    monkeypatch.setattr(unreal_vendor_workflow.subprocess, "run", fake_subprocess_run)

    payload = unreal_vendor_workflow.prepare_source_checkout(
        vendor="cesium",
        version="5.8",
        plugin_root_arg=str(plugin_root),
        clean_build=False,
        build_type="Release",
        dry_run=False,
    )

    assert payload["status"] == "ok"
    assert len(recorded) == 2
    assert f"-DCMAKE_TOOLCHAIN_FILE={extern_root / 'unreal-linux-toolchain.cmake'}" in recorded[0][0]
    assert "-DCMAKE_POSITION_INDEPENDENT_CODE=ON" in recorded[0][0]
    assert recorded[0][2]["VCPKG_TRIPLET"] == "x64-linux-unreal"
    assert recorded[0][2]["UNREAL_ENGINE_ROOT"] == str(install_root)


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


def test_install_smoke_command_treats_unwritten_placeholder_as_missing_report(monkeypatch, tmp_path: Path) -> None:
    plugin_root = tmp_path / "cesium"
    plugin_root.mkdir()
    (plugin_root / "CesiumForUnreal.uplugin").write_text("{}\n", encoding="utf-8")
    json_out = tmp_path / "install.json"
    md_out = tmp_path / "install.md"

    monkeypatch.setattr(unreal_vendor_workflow, "run_step", lambda cmd: 7)

    payload = unreal_vendor_workflow.install_smoke_report_payload(
        vendor="cesium",
        version="5.7",
        plugin_root_arg=str(plugin_root),
        uplugin_arg=None,
        package_dir_arg=str(tmp_path / "package"),
        project_dir_arg=str(tmp_path / "project"),
        json_out_arg=str(json_out),
        md_out_arg=str(md_out),
        clean_project=True,
        dry_run=False,
    )

    assert payload["status"] == "missing-report"
    assert payload["returncode"] == 7
    reserved = json.loads(json_out.read_text(encoding="utf-8"))
    assert reserved["schema"] == "packet_stoat.pending_subprocess_artifact.v1"


def test_build_report_payload_captures_buildplugin_failure(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(unreal_vendor_workflow, "DEFAULT_REPORT_DIR", tmp_path / "reports")
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

    monkeypatch.setattr(
        unreal_vendor_workflow,
        "_run_buildplugin_with_progress",
        lambda cmd, progress, vendor, version: fake_run(cmd),
    )

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
    monkeypatch.setattr(unreal_vendor_workflow, "DEFAULT_REPORT_DIR", tmp_path / "reports")
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

    monkeypatch.setattr(
        unreal_vendor_workflow,
        "_run_buildplugin_with_progress",
        lambda cmd, progress, vendor, version: fake_run(cmd),
    )

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
    monkeypatch.setattr(unreal_vendor_workflow, "DEFAULT_REPORT_DIR", tmp_path / "reports")
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

    monkeypatch.setattr(
        unreal_vendor_workflow,
        "_run_buildplugin_with_progress",
        lambda cmd, progress, vendor, version: fake_run(cmd),
    )

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
    assert (unreal_vendor_workflow.DEFAULT_REPORT_DIR / "cesium_5_8_build.json").is_file()
