from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import host_capability_matrix


def test_build_payload_tempered_by_detected_routes(monkeypatch) -> None:
    monkeypatch.setattr(
        host_capability_matrix,
        "host_facts",
        lambda: type(
            "Facts",
            (),
            {
                "host_class": "windows",
                "preferred_runtime_hosts": ("windows", "linux-docker"),
                "cross_build_targets": ("windows", "linux", "macos"),
            },
        )(),
    )
    monkeypatch.setattr(
        host_capability_matrix,
        "_docker_probe",
        lambda: {"status": "ready", "executable": "docker", "detail": "docker daemon reachable"},
    )
    monkeypatch.setattr(
        host_capability_matrix,
        "_linux_direct_probe",
        lambda: {"status": "partial", "executable": "", "detail": "cmake=ok; zig=missing; toolchain=ok"},
    )
    monkeypatch.setattr(
        host_capability_matrix,
        "_wsl_probe",
        lambda: {"status": "ready", "executable": "wsl", "detail": "Default Distribution: Ubuntu"},
    )
    monkeypatch.setattr(
        host_capability_matrix.godot_env,
        "describe_host",
        lambda: {
            "platform": "windows",
            "arch": "x86_64",
            "godot": r"C:\Godot\Godot.exe",
            "scons": r"C:\venv\Scripts\scons.exe",
            "repo_root": str(ROOT),
            "repo_alias_root": str(ROOT),
            "uses_repo_alias": False,
            "work_root": r"C:\tmp\godot",
            "work_root_has_spaces": False,
            "wrapper_names": [],
            "shared_library_names": [],
        },
    )
    monkeypatch.setattr(
        host_capability_matrix.unity_env,
        "describe_host",
        lambda: {
            "platform": "Windows",
            "arch": "AMD64",
            "repo_root": str(ROOT),
            "work_root": r"C:\tmp\unity",
            "work_root_has_spaces": False,
            "installs": [
                {
                    "version": "6000.5.1f1",
                    "install_root": r"C:\Program Files\Unity\Hub\Editor\6000.5.1f1",
                    "editor_path": r"C:\Program Files\Unity\Hub\Editor\6000.5.1f1\Editor\Unity.exe",
                    "source": "scan",
                    "quirks": [],
                }
            ],
            "default_install": {
                "version": "6000.5.1f1",
                "install_root": r"C:\Program Files\Unity\Hub\Editor\6000.5.1f1",
                "editor_path": r"C:\Program Files\Unity\Hub\Editor\6000.5.1f1\Editor\Unity.exe",
                "source": "scan",
                "quirks": [],
            },
            "recommended_editor_overrides": {
                "FASTDIS_UNITY_EDITOR": r"C:\Program Files\Unity\Hub\Editor\6000.5.1f1\Editor\Unity.exe",
                "FASTDIS_UNITY_EDITOR_DIR": r"C:\Program Files\Unity\Hub\Editor\6000.5.1f1",
            },
        },
    )
    monkeypatch.setattr(
        host_capability_matrix.unreal_env,
        "discover_installs",
        lambda: [
            host_capability_matrix.unreal_env.UnrealInstall(
                version="5.8",
                install_root=r"C:\Epic\UE_5.8",
                engine_dir=r"C:\Epic\UE_5.8\Engine",
                editor_path=r"C:\Epic\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe",
                editor_cmd_path=r"C:\Epic\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe",
                editor_app_path=None,
                dotnet_path=r"C:\Epic\UE_5.8\Engine\Binaries\ThirdParty\DotNet\dotnet.exe",
                uat_path=r"C:\Epic\UE_5.8\Engine\Build\BatchFiles\RunUAT.bat",
                ubt_path=r"C:\Epic\UE_5.8\Engine\Binaries\DotNET\UnrealBuildTool\UnrealBuildTool.dll",
                source="scan",
                quirks=(),
            )
        ],
    )
    monkeypatch.setattr(host_capability_matrix, "_unreal_linux_profile_versions", lambda: ["5.7", "5.8"])
    monkeypatch.setattr(
        host_capability_matrix.windows_wheel_workflow,
        "doctor_payload",
        lambda _prefix: {"status": "ready-with-gaps", "checks": [{"name": "cmake", "status": "ok", "detail": "cmake"}]},
    )
    monkeypatch.setattr(host_capability_matrix.shutil, "which", lambda name: "C:/Tools/cmake.exe" if name == "cmake" else None)

    payload = host_capability_matrix.build_payload()

    routes = {row["name"]: row for row in payload["routes"]}
    surfaces = {row["id"]: row for row in payload["surfaces"]}
    assert payload["host"]["host_class"] == "windows"
    assert "install-smoke" in payload["canonical_surface_hooks"]
    assert payload["canonical_hook_categories"]["package"] == "packaging"
    assert surfaces["unity"]["hooks"]["doctor"]["command"] == "fastdis engine unity doctor --unity-version 6000.5"
    assert surfaces["unity"]["hooks"]["doctor"]["category"] == "lifecycle"
    assert surfaces["unity"]["preferred_version"] == "6000.5"
    assert [row["version"] for row in surfaces["unreal"]["supported_versions"]] == ["5.7", "5.8"]
    assert any(row["preferred"] for row in surfaces["unreal"]["supported_versions"])
    assert surfaces["unreal"]["hooks"]["full"]["command"] == "fastdis engine unreal full --engine-version 5.8"
    assert surfaces["python"]["hooks"]["discover"]["status"] == "unsupported"
    assert surfaces["godot"]["hooks"]["install-smoke"]["status"] == "unsupported"
    assert routes["godot-native"]["status"] == "ready"
    assert routes["godot-native"]["activation"] == "ready-now"
    assert routes["godot-native"]["version_status"] == "undiscovered"
    assert routes["unity-native"]["status"] == "ready"
    assert routes["unity-native"]["activation"] == "ready-now"
    assert routes["unity-native"]["version_status"] == "preferred-match"
    assert routes["unity-linux-cross-direct"]["status"] == "partial"
    assert routes["unity-linux-cross-direct"]["activation"] == "ready-after-install"
    assert routes["unity-linux-cross-direct"]["missing_installs"] == ["zig", "cmake"]
    assert routes["unity-linux-cross-direct"]["install_commands"] == ["scoop install zig cmake"]
    assert routes["unity-linux-cross-direct"]["version_status"] == "preferred-match"
    assert routes["unity-linux-cross-direct"]["requirement_status"] == "warn"
    assert routes["unity-linux-docker"]["status"] == "ready"
    assert routes["unity-linux-docker"]["activation"] == "ready-now"
    assert routes["unreal-native"]["status"] == "ready"
    assert routes["unreal-native"]["version_status"] == "preferred-match"
    assert routes["unreal-linux-docker"]["status"] == "ready"
    assert routes["windows-cross-mingw"]["status"] == "partial"
    assert routes["windows-cross-mingw"]["activation"] == "ready-after-setup"
    assert routes["windows-cross-mingw"]["missing_installs"] == []
    assert routes["windows-cross-mingw"]["missing_setup_steps"]
    assert routes["windows-cross-mingw"]["light_up_command"] == "python tools/windows_wheel_workflow.py full --no-isolation"
    assert routes["windows-cross-mingw"]["requirement_status"] == "warn"
    assert routes["windows-cross-mingw"]["remediation_steps"]
    assert payload["engines"]["unity"]["recommended_overrides"]["FASTDIS_UNITY_EDITOR"].endswith("Unity.exe")
    assert payload["toolchains"]["linux_shared"]["status"] == "partial"
    assert payload["toolchains"]["windows_cross_mingw"]["status"] == "ready-with-gaps"
    assert payload["cross_platform_policy"]
    assert any("Linux direct and Linux Docker separately" in item for item in payload["cross_platform_policy"])
    assert "godot-native" in payload["route_summary"]["ready_now"]
    assert "unity-linux-cross-direct" in payload["route_summary"]["ready_after_install"]
    assert "windows-cross-mingw" in payload["route_summary"]["ready_after_setup"]
    assert "unity-native" in payload["route_summary"]["preferred_version_match"]
    assert payload["next_steps"]
    assert "fastdis bootstrap doctor" in payload["next_steps"]


def test_build_payload_reports_supported_not_preferred_versions(monkeypatch) -> None:
    monkeypatch.setattr(
        host_capability_matrix,
        "host_facts",
        lambda: type(
            "Facts",
            (),
            {
                "host_class": "windows",
                "preferred_runtime_hosts": ("windows",),
                "cross_build_targets": ("windows",),
            },
        )(),
    )
    monkeypatch.setattr(
        host_capability_matrix,
        "_docker_probe",
        lambda: {"status": "partial", "executable": "docker", "detail": "docker daemon not reachable"},
    )
    monkeypatch.setattr(
        host_capability_matrix,
        "_linux_direct_probe",
        lambda: {"status": "partial", "executable": "", "detail": "cmake=ok; zig=missing; toolchain=ok"},
    )
    monkeypatch.setattr(
        host_capability_matrix,
        "_wsl_probe",
        lambda: {"status": "ready", "executable": "wsl", "detail": "Default Distribution: Ubuntu"},
    )
    monkeypatch.setattr(
        host_capability_matrix.godot_env,
        "describe_host",
        lambda: {
            "platform": "windows",
            "arch": "x86_64",
            "godot": r"C:\Users\Public\Godot\engines\Godot_v4.7-stable_win64\Godot_v4.7-stable_win64_console.exe",
            "scons": r"C:\venv\Scripts\scons.exe",
            "repo_root": str(ROOT),
            "repo_alias_root": str(ROOT),
            "uses_repo_alias": False,
            "work_root": r"C:\tmp\godot",
            "work_root_has_spaces": False,
            "wrapper_names": [],
            "shared_library_names": [],
        },
    )
    monkeypatch.setattr(
        host_capability_matrix.unity_env,
        "describe_host",
        lambda: {
            "platform": "Windows",
            "arch": "AMD64",
            "repo_root": str(ROOT),
            "work_root": r"C:\tmp\unity",
            "work_root_has_spaces": False,
            "installs": [
                {
                    "version": "6000.5.1f1",
                    "install_root": r"C:\Program Files\Unity\Hub\Editor\6000.5.1f1",
                    "editor_path": r"C:\Program Files\Unity\Hub\Editor\6000.5.1f1\Editor\Unity.exe",
                    "source": "scan",
                    "quirks": [],
                }
            ],
            "default_install": {
                "version": "6000.5.1f1",
                "install_root": r"C:\Program Files\Unity\Hub\Editor\6000.5.1f1",
                "editor_path": r"C:\Program Files\Unity\Hub\Editor\6000.5.1f1\Editor\Unity.exe",
                "source": "scan",
                "quirks": [],
            },
            "recommended_editor_overrides": {},
        },
    )
    monkeypatch.setattr(
        host_capability_matrix.unreal_env,
        "discover_installs",
        lambda: [
            host_capability_matrix.unreal_env.UnrealInstall(
                version="5.7",
                install_root=r"C:\Epic\UE_5.7",
                engine_dir=r"C:\Epic\UE_5.7\Engine",
                editor_path=r"C:\Epic\UE_5.7\Engine\Binaries\Win64\UnrealEditor.exe",
                editor_cmd_path=r"C:\Epic\UE_5.7\Engine\Binaries\Win64\UnrealEditor-Cmd.exe",
                editor_app_path=None,
                dotnet_path=r"C:\Epic\UE_5.7\Engine\Binaries\ThirdParty\DotNet\dotnet.exe",
                uat_path=r"C:\Epic\UE_5.7\Engine\Build\BatchFiles\RunUAT.bat",
                ubt_path=r"C:\Epic\UE_5.7\Engine\Binaries\DotNET\UnrealBuildTool\UnrealBuildTool.dll",
                source="scan",
                quirks=(),
            )
        ],
    )
    monkeypatch.setattr(host_capability_matrix, "_unreal_linux_profile_versions", lambda: ["5.7"])
    monkeypatch.setattr(
        host_capability_matrix.windows_wheel_workflow,
        "doctor_payload",
        lambda _prefix: {"status": "ready", "checks": []},
    )
    monkeypatch.setattr(host_capability_matrix.shutil, "which", lambda name: "C:/Tools/cmake.exe" if name == "cmake" else None)

    payload = host_capability_matrix.build_payload()
    routes = {row["name"]: row for row in payload["routes"]}

    assert routes["unreal-native"]["status"] == "ready"
    assert routes["unreal-native"]["version_status"] == "supported-not-preferred"
    assert routes["unreal-native"]["preferred_surface_version"] == "5.8"
    assert routes["unreal-native"]["matched_surface_versions"] == ["5.7"]
    assert "unreal-native" in payload["route_summary"]["supported_not_preferred"]


def test_main_json_prints_matrix(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        host_capability_matrix,
        "build_payload",
        lambda: {
            "schema": "fastdis.host_capability_matrix.v1",
            "canonical_surface_hooks": ["doctor"],
            "canonical_hook_categories": {"doctor": "lifecycle"},
            "surfaces": [{"id": "unity", "hooks": {"doctor": {"status": "supported", "command": "fastdis engine unity doctor --unity-version 6000.5", "notes": ""}}}],
            "host": {"platform": "Windows", "arch": "AMD64", "host_class": "windows", "preferred_runtime_hosts": ["windows"], "cross_build_targets": ["windows"]},
            "software": {"docker": {"status": "ready", "detail": "ok"}, "zig": {"status": "partial", "detail": "zig missing"}, "wsl": {"status": "ready", "detail": "ok"}, "cmake": "cmake", "godot": "", "scons": ""},
            "engines": {"godot": {"status": "unavailable", "host": {}}, "unity": {"status": "ready", "default_install": None, "installs": [], "recommended_overrides": {}}, "unreal": {"status": "partial", "installs": [], "linux_docker_profiles": []}},
            "toolchains": {"linux_shared": {"status": "partial", "toolchain_file": "cmake/toolchains/linux-x86_64-zig.cmake", "detail": "zig missing"}, "windows_cross_mingw": {"status": "ready", "toolchain_file": "cmake/toolchains/mingw-w64-x86_64.cmake", "detail": "canonical"}, "windows_wheel": {"status": "ready", "checks": []}},
            "cross_platform_policy": ["policy"],
            "route_summary": {"ready_now": ["python-core"], "ready_after_install": ["unity-linux-cross-direct"], "ready_after_setup": ["windows-cross-mingw"], "supported_on_host": [], "unsupported_on_host": []},
            "routes": [{"name": "windows-cross-mingw", "activation": "ready-after-setup", "detail": "backend=mingw-direct", "installs": ["mingw-w64"], "light_up_command": "python tools/windows_wheel_workflow.py full --no-isolation", "evidence_commands": ["python tools/windows_wheel_workflow.py doctor"], "missing_installs": [], "install_commands": [], "missing_setup_steps": ["Run the wheel workflow"], "version_status": "supported-not-preferred", "version_detail": "installed=3.13; matched=3.13; preferred=3.14", "requirement_status": "pass", "remediation_steps": []}],
            "next_steps": [],
        },
    )

    rc = host_capability_matrix.main(["--format", "json"])
    out = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert out["schema"] == "fastdis.host_capability_matrix.v1"
    assert out["host"]["platform"] == "Windows"


def test_main_summary_prints_compact_actions(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        host_capability_matrix,
        "build_payload",
        lambda: {
            "schema": "fastdis.host_capability_matrix.v1",
            "host": {"platform": "Windows", "arch": "AMD64", "host_class": "windows", "preferred_runtime_hosts": ["windows"], "cross_build_targets": ["windows"]},
            "routes": [
                {
                    "name": "godot-native",
                    "activation": "ready-now",
                    "install_commands": [],
                    "missing_installs": [],
                    "missing_setup_steps": [],
                    "light_up_command": "fastdis engine godot full",
                    "version_status": "preferred-match",
                    "version_detail": "installed=4.7; preferred=4.7",
                },
                {
                    "name": "unity-linux-cross-direct",
                    "activation": "ready-after-install",
                    "install_commands": ["scoop install zig cmake"],
                    "missing_installs": ["zig", "cmake"],
                    "missing_setup_steps": [],
                    "light_up_command": "python tools/build_unity_native_matrix.py build --targets linux --linux-backend direct",
                    "version_status": "preferred-match",
                    "version_detail": "installed=6000.5.1f1; preferred=6000.5",
                    "requirement_status": "pass",
                    "remediation_steps": [],
                },
                {
                    "name": "windows-cross-mingw",
                    "activation": "ready-after-setup",
                    "install_commands": [],
                    "missing_installs": [],
                    "missing_setup_steps": ["Run the wheel workflow"],
                    "light_up_command": "python tools/windows_wheel_workflow.py full --no-isolation",
                    "version_status": "supported-not-preferred",
                    "version_detail": "installed=3.13; matched=3.13; preferred=3.14",
                    "requirement_status": "pass",
                    "remediation_steps": [],
                },
                {
                    "name": "unreal-native",
                    "activation": "ready-now",
                    "install_commands": [],
                    "missing_installs": [],
                    "missing_setup_steps": [],
                    "light_up_command": "fastdis engine unreal doctor --engine-version 5.8",
                    "version_status": "supported-not-preferred",
                    "version_detail": "installed=5.7; matched=5.7; preferred=5.8",
                    "requirement_status": "pass",
                    "remediation_steps": [],
                },
            ],
            "route_summary": {
                "ready_now": ["godot-native", "unreal-native"],
                "ready_after_install": ["unity-linux-cross-direct"],
                "ready_after_setup": ["windows-cross-mingw"],
                "supported_on_host": [],
                "unsupported_on_host": [],
                "preferred_version_match": ["godot-native", "unity-linux-cross-direct"],
                "supported_not_preferred": ["windows-cross-mingw", "unreal-native"],
                "unsupported_version": [],
            },
        },
    )

    rc = host_capability_matrix.main(["--format", "summary"])
    out = capsys.readouterr().out

    assert rc == 0
    assert "FastDIS workspace summary" in out
    assert "host=Windows/AMD64 class=windows" in out
    assert "ready_now=godot-native" in out
    assert "ready_after_install=unity-linux-cross-direct" in out
    assert "install unity-linux-cross-direct: scoop install zig cmake" in out
    assert "setup windows-cross-mingw: python tools/windows_wheel_workflow.py full --no-isolation" in out
    assert "supported_not_preferred=windows-cross-mingw,unreal-native" in out
    assert "version windows-cross-mingw: installed=3.13; matched=3.13; preferred=3.14" in out
    assert "version unreal-native: installed=5.7; matched=5.7; preferred=5.8" in out


def test_main_surfaces_summary_prints_hook_inventory(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        host_capability_matrix,
        "build_payload",
        lambda: {
            "schema": "fastdis.host_capability_matrix.v1",
            "workspace": {"id": "packet-stoat"},
            "canonical_surface_hooks": ["doctor", "full"],
            "canonical_hook_categories": {"doctor": "lifecycle", "full": "proof"},
            "surfaces": [
                {"id": "python", "label": "Python", "preferred_version": "3.14", "supported_versions": [{"version": "3.12", "status": "supported", "preferred": False, "notes": "", "aliases": []}, {"version": "3.13", "status": "supported", "preferred": False, "notes": "", "aliases": []}, {"version": "3.14", "status": "preferred", "preferred": True, "notes": "", "aliases": []}], "package_paths": ["src/fastdis"], "example_paths": ["examples"], "proof_kinds": ["integration-proof"], "hooks": {"doctor": {"category": "lifecycle", "status": "supported", "command": "fastdis doctor", "notes": ""}, "full": {"category": "proof", "status": "supported", "command": "python -m pytest", "notes": ""}}},
                {"id": "godot", "label": "Godot", "preferred_version": "4.7", "supported_versions": [{"version": "4.7", "status": "preferred", "preferred": True, "notes": "", "aliases": []}], "package_paths": ["packages/godot/fastdis_gdextension"], "example_paths": ["packages/godot/fastdis_demo"], "proof_kinds": ["runtime-proof"], "hooks": {"doctor": {"category": "lifecycle", "status": "supported", "command": "fastdis engine godot doctor", "notes": ""}, "full": {"category": "proof", "status": "supported", "command": "fastdis engine godot full", "notes": ""}}},
            ],
        },
    )

    rc = host_capability_matrix.main(["--view", "surfaces", "--format", "summary"])
    out = capsys.readouterr().out

    assert rc == 0
    assert "FastDIS workspace surfaces summary" in out
    assert "python[preferred=3.14;versions=3.12,3.13,3.14]=doctor=supported,full=supported" in out
    assert "godot[preferred=4.7;versions=4.7]=doctor=supported,full=supported" in out
    assert "categories=doctor:lifecycle,full:proof" in out


def test_main_routes_summary_prints_route_versions(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        host_capability_matrix,
        "build_payload",
        lambda: {
            "schema": "fastdis.host_capability_matrix.v1",
            "workspace": {"id": "packet-stoat"},
            "routes": [
                {
                    "name": "unreal-native",
                    "activation": "ready-now",
                    "version_status": "supported-not-preferred",
                    "requirement_status": "pass",
                    "preferred_surface_version": "5.8",
                    "matched_surface_versions": ["5.7"],
                },
                {
                    "name": "unity-native",
                    "activation": "ready-now",
                    "version_status": "preferred-match",
                    "requirement_status": "pass",
                    "preferred_surface_version": "6000.5",
                    "matched_surface_versions": ["6000.5.1f1"],
                },
            ],
        },
    )

    rc = host_capability_matrix.main(["--view", "routes", "--format", "summary"])
    out = capsys.readouterr().out

    assert rc == 0
    assert "FastDIS workspace routes summary" in out
    assert "unreal-native=ready-now;version_status=supported-not-preferred;requirements=pass;preferred=5.8;matched=5.7" in out
    assert "unity-native=ready-now;version_status=preferred-match;requirements=pass;preferred=6000.5;matched=6000.5.1f1" in out


def test_main_ci_summary_prints_manifest_driven_rows(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        host_capability_matrix,
        "build_payload",
        lambda: {
            "schema": "fastdis.host_capability_matrix.v1",
            "workspace": {"id": "packet-stoat"},
            "routes": [
                {
                    "name": "godot-native",
                    "surface": "godot",
                    "host_scope": ["windows", "macos"],
                    "target": "host",
                    "backend": "native",
                    "proof_kind": "runtime-proof",
                    "preferred_surface_version": "4.7",
                    "supported_surface_versions": ["4.7"],
                },
                {
                    "name": "windows-cross-mingw",
                    "surface": "python",
                    "host_scope": ["windows", "linux"],
                    "target": "windows",
                    "backend": "mingw-direct",
                    "proof_kind": "build-proof",
                    "preferred_surface_version": "3.14",
                    "supported_surface_versions": ["3.12", "3.13", "3.14"],
                },
            ],
        },
    )

    rc = host_capability_matrix.main(["--view", "ci", "--host-class", "windows", "--include-compat", "--format", "summary"])
    out = capsys.readouterr().out

    assert rc == 0
    assert "FastDIS workspace CI summary" in out
    assert "godot-native-windows-4.7=godot-native;surface=godot;host=windows;version=4.7;kind=preferred" in out
    assert "windows-cross-mingw-windows-3.12=windows-cross-mingw;surface=python;host=windows;version=3.12;kind=compat" in out


def test_main_hooks_summary_filters_by_category(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        host_capability_matrix,
        "build_payload",
        lambda: {
            "schema": "fastdis.host_capability_matrix.v1",
            "workspace": {"id": "packet-stoat"},
            "canonical_hook_categories": {"doctor": "lifecycle", "full": "proof", "demo": "demo"},
            "surfaces": [
                {
                    "id": "python",
                    "hooks": {
                        "doctor": {"category": "lifecycle", "status": "supported", "command": "fastdis doctor", "notes": ""},
                        "full": {"category": "proof", "status": "supported", "command": "python -m pytest", "notes": ""},
                    },
                },
                {
                    "id": "godot",
                    "hooks": {
                        "doctor": {"category": "lifecycle", "status": "supported", "command": "fastdis engine godot doctor", "notes": ""},
                        "demo": {"category": "demo", "status": "supported", "command": "fastdis engine godot demo", "notes": ""},
                    },
                },
            ],
        },
    )

    rc = host_capability_matrix.main(["--view", "hooks", "--category", "proof", "--format", "summary"])
    out = capsys.readouterr().out

    assert rc == 0
    assert "FastDIS workspace hooks summary (proof)" in out
    assert "python.full=supported" in out
    assert "godot.demo" not in out
