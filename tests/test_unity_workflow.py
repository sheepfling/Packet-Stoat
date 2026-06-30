from __future__ import annotations

import json
from pathlib import Path

import sys


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import build_unity_native_matrix
import run_unity_editor_tests
import unity_env
import stage_unity_native
import unity_workflow


def test_unity_env_discovers_editor_from_versioned_env(monkeypatch, tmp_path: Path) -> None:
    root = tmp_path / "6000.5.0f1"
    app = root / "Unity.app"
    executable = app / "Contents" / "MacOS" / "Unity"
    executable.parent.mkdir(parents=True)
    executable.write_text("", encoding="utf-8")
    monkeypatch.setenv("FASTDIS_UNITY_EDITOR_6000_5", str(app))

    install = unity_env.resolve_install("6000.5")

    assert install is not None
    assert install.version == "6000.5"
    assert install.editor_path == str(executable.resolve())


def test_unity_env_prefers_an_install_with_an_editor_over_hub(monkeypatch) -> None:
    hub = unity_env.UnityInstall(
        version="Hub",
        install_root="C:/Program Files/Unity/Hub",
        editor_path=None,
        editor_app_path=None,
        source="scan:C:/Program Files/Unity",
        quirks=("missing-editor-executable",),
    )
    editor = unity_env.UnityInstall(
        version="6000.5.1f1",
        install_root="C:/Program Files/Unity/Hub/Editor/6000.5.1f1",
        editor_path="C:/Program Files/Unity/Hub/Editor/6000.5.1f1/Editor/Unity.exe",
        editor_app_path=None,
        source="scan:C:/Program Files/Unity/Hub/Editor",
        quirks=(),
    )
    monkeypatch.setattr(unity_env, "discover_installs", lambda: [hub, editor])

    install = unity_env.resolve_install()
    host = unity_env.describe_host()

    assert install is not None
    assert install.editor_path == editor.editor_path
    assert host["default_install"]["editor_path"] == editor.editor_path
    assert host["recommended_editor_overrides"]["FASTDIS_UNITY_EDITOR"] == editor.editor_path
    assert host["recommended_editor_overrides"]["FASTDIS_UNITY_EDITOR_DIR"] == editor.install_root


def test_unity_package_state_has_required_surface() -> None:
    state = unity_workflow.package_state()

    assert state
    assert all(state.values())


def test_stage_unity_native_copies_host_library(tmp_path: Path) -> None:
    package = tmp_path / "package"
    build = tmp_path / "build"
    out = tmp_path / "reports"
    build.mkdir()
    (build / "libfastdis.dylib").write_bytes(b"native")

    report = stage_unity_native.stage("macos", package, build, out)

    staged = package / "Runtime" / "Plugins" / "macOS" / "libfastdis.dylib"
    assert report["status"] == "pass"
    assert staged.read_bytes() == b"native"
    assert staged.with_name("libfastdis.dylib.meta").is_file()
    assert (out / "unity_native_stage_macos.json").is_file()


def test_unity_native_matrix_doctor_has_three_targets() -> None:
    payload = build_unity_native_matrix.doctor_payload()

    assert {"macos", "windows", "linux"} <= set(payload["targets"])
    assert payload["targets"]["macos"]["method"] == "host CMake"
    assert payload["targets"]["windows"]["method"] == "MinGW-w64 cross compile"
    assert payload["targets"]["linux"]["method"] == "direct CMake toolchain or Docker linux/amd64 CMake build"
    assert {"direct", "docker"} <= set(payload["targets"]["linux"]["backends"])


def test_unity_native_matrix_doctor_accepts_plain_windres(monkeypatch) -> None:
    def fake_tool_status(name: str) -> dict[str, object]:
        return {"tool": name, "path": f"C:/Tools/{name}.exe", "available": True}

    monkeypatch.setattr(build_unity_native_matrix, "tool_status", fake_tool_status)
    monkeypatch.setattr(build_unity_native_matrix, "resolve_rc_tool", lambda prefix: r"C:\gcc\bin\windres.exe")
    monkeypatch.setattr(
        build_unity_native_matrix,
        "linux_direct_backend_probe",
        lambda _path: {"available": False, "detail": "missing", "status": "partial", "toolchain_file": "toolchain", "cmake": "", "zig": ""},
    )

    payload = build_unity_native_matrix.doctor_payload()

    assert payload["tools"]["mingw_windres"]["available"] is True
    assert payload["tools"]["mingw_windres"]["path"] == r"C:\gcc\bin\windres.exe"
    assert payload["targets"]["windows"]["available"] is True


def test_unity_native_matrix_write_report(tmp_path: Path) -> None:
    results = {
        "status": "pass",
        "targets": {
            "macos": {"status": "pass", "artifact": "/tmp/macos.dylib"},
            "windows": {"status": "pass", "artifact": "/tmp/windows.dll"},
            "linux": {"status": "pass", "artifact": "/tmp/linux.so"},
        },
        "staged": [{"platform": "macos", "native_library": "Runtime/Plugins/macOS/libfastdis.dylib"}],
    }

    json_path, md_path = build_unity_native_matrix.write_report(results, tmp_path)

    assert json_path.is_file()
    assert md_path.is_file()
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["status"] == "pass"
    assert "unity native matrix" in md_path.read_text(encoding="utf-8").lower()


def test_unity_native_matrix_prefers_real_linux_shared_library(tmp_path: Path, monkeypatch) -> None:
    build_dir = tmp_path / "linux-build"
    build_dir.mkdir()
    versioned = build_dir / "libfastdis.so.0.13.0"
    alias = build_dir / "libfastdis.so"
    versioned.write_bytes(b"linux-real")
    alias.write_bytes(b"linux-alias")

    original = build_unity_native_matrix._path_is_file

    def fake_path_is_file(path: Path) -> bool:
        if path == alias:
            return False
        return original(path)

    monkeypatch.setattr(build_unity_native_matrix, "_path_is_file", fake_path_is_file)

    resolved = build_unity_native_matrix._latest_linux_shared_library(build_dir)

    assert resolved == versioned


def test_unity_native_matrix_build_linux_docker_materializes_windows_readable_alias(tmp_path: Path, monkeypatch) -> None:
    build_dir = tmp_path / "linux-build"
    build_dir.mkdir()
    versioned = build_dir / "libfastdis.so.0.13.0"
    alias_path = build_dir / "libfastdis.so"
    versioned.write_bytes(b"linux-real")
    alias_path.write_bytes(b"linux-alias")

    commands: list[list[str]] = []
    removed: list[Path] = []

    monkeypatch.setattr(build_unity_native_matrix, "ROOT", tmp_path)
    monkeypatch.setattr(build_unity_native_matrix, "CMAKE_LINUX_X86_64", build_dir)
    monkeypatch.setattr(build_unity_native_matrix, "run", lambda cmd, required=True: commands.append(cmd) or 0)
    monkeypatch.setattr(build_unity_native_matrix, "_latest_linux_shared_library", lambda path: versioned if path == build_dir else None)
    monkeypatch.setattr(build_unity_native_matrix, "_path_is_file", lambda path: path == versioned)
    monkeypatch.setattr(build_unity_native_matrix, "_remove_if_present", lambda path: removed.append(path) or path.unlink())

    alias = build_unity_native_matrix.build_linux_docker("Release", "ubuntu:24.04")

    assert commands
    assert alias == build_dir / "libfastdis.so"
    assert removed == [alias_path]
    assert alias.read_bytes() == b"linux-real"


def test_unity_native_matrix_build_linux_direct_uses_toolchain(tmp_path: Path, monkeypatch) -> None:
    build_dir = tmp_path / "linux-build"
    build_dir.mkdir()
    toolchain = tmp_path / "linux-zig.cmake"
    toolchain.write_text("set(CMAKE_SYSTEM_NAME Linux)\n", encoding="utf-8")
    versioned = build_dir / "libfastdis.so.0.13.0"
    versioned.write_bytes(b"linux-real")

    commands: list[list[str]] = []

    monkeypatch.setattr(build_unity_native_matrix, "ROOT", tmp_path)
    monkeypatch.setattr(build_unity_native_matrix, "CMAKE_LINUX_X86_64", build_dir)
    monkeypatch.setattr(build_unity_native_matrix, "run", lambda cmd, required=True: commands.append(cmd) or 0)
    monkeypatch.setattr(
        build_unity_native_matrix,
        "linux_direct_backend_probe",
        lambda path: {"available": True, "detail": "cmake=ok; zig=ok; toolchain=ok"} if path == toolchain else {"available": False, "detail": "bad"},
    )

    alias = build_unity_native_matrix.build_linux_direct("Release", toolchain, "Ninja")

    assert alias == build_dir / "libfastdis.so"
    assert alias.read_bytes() == b"linux-real"
    assert commands[0][:3] == ["cmake", "-G", "Ninja"]
    assert any(str(toolchain.resolve()) in part for part in commands[0])
    assert commands[1][-2:] == ["--target", "fastdis_shared"]


def test_unity_native_matrix_auto_prefers_direct_linux_backend(monkeypatch, tmp_path: Path) -> None:
    toolchain = tmp_path / "linux-zig.cmake"
    toolchain.write_text("set(CMAKE_SYSTEM_NAME Linux)\n", encoding="utf-8")
    monkeypatch.setattr(
        build_unity_native_matrix,
        "linux_direct_backend_probe",
        lambda path: {"available": True, "detail": "ready"} if path == toolchain else {"available": False, "detail": "missing"},
    )

    assert build_unity_native_matrix.resolve_linux_backend("auto", toolchain) == "direct"


def test_unity_native_matrix_clears_incompatible_cache(tmp_path: Path) -> None:
    build_dir = tmp_path / "linux-build"
    build_dir.mkdir()
    cache = build_dir / "CMakeCache.txt"
    cache.write_text("CMAKE_HOME_DIRECTORY:INTERNAL=/src\nCMAKE_CACHEFILE_DIR:INTERNAL=/src/build/cmake/linux-x86_64\n", encoding="utf-8")

    build_unity_native_matrix._clear_if_incompatible_cmake_cache(
        build_dir,
        str(tmp_path / "repo"),
        str(build_dir),
    )

    assert not build_dir.exists()


def test_unity_build_env_redirects_home_cache_and_tmp(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("FASTDIS_UNITY_WORK_ROOT", str(tmp_path / "unity_work"))

    env = unity_env.build_env()

    assert env["HOME"].startswith(str(tmp_path / "unity_work"))
    assert env["TMPDIR"].startswith(str(tmp_path / "unity_work"))
    assert env["XDG_CACHE_HOME"].startswith(str(tmp_path / "unity_work"))


def test_unity_doctor_reports_permission_checks() -> None:
    payload = unity_workflow.doctor_payload(None)
    check_names = {check["name"] for check in payload["checks"]}

    assert "permission:work_root" in check_names
    assert "permission:package_plugins" in check_names


def test_unity_doctor_payload_reports_package_and_warns_for_unstaged_native() -> None:
    payload = unity_workflow.doctor_payload(None)
    check_names = {check["name"] for check in payload["checks"]}

    assert payload["unity_alpha5_result"] in {"pass", "fail"}
    assert payload["passed_scope"] in {
        "workflow/package/native-staging parity",
        "workflow/package/native-staging/runtime parity",
        "workflow/package/native-staging/runtime/orientation parity",
        "workflow/package/native-staging/runtime/orientation/install parity",
        "workflow/package/native-staging/runtime/orientation/install matrix parity",
    }
    assert payload["next_scope"] in {
        "Unity Editor runtime verification",
        "Unity orientation verification scene",
        "Unity Git/UPM install smoke",
        "Release polish",
        "Broaden Unity install-surface evidence and release polish",
    }
    assert payload["unity_workflow_status"] in {"pass", "fail"}
    assert payload["unity_native_status"] in {"pass", "not_verified"}
    assert payload["unity_native_matrix_status"] in {"pass", "fail", "not_run"}
    assert isinstance(payload["unity_native_matrix_targets"], list)
    assert payload["unity_runtime_status"] in {"pass", "fail", "blocked_license", "not_run"}
    assert payload["unity_orientation_status"] in {"pass", "fail", "blocked_license", "not_run"}
    assert payload["unity_install_status"] in {"pass", "fail", "blocked_license", "not_run"}
    assert payload["unity_install_host"] in {"macos", "windows", "linux"}
    assert payload["unity_install_matrix_status"] in {"pass", "incomplete", "fail", "not_run"}
    assert isinstance(payload["unity_install_matrix_hosts"], list)
    assert payload["unity_host_matrix_status"] in {"pass", "incomplete", "fail", "not_run"}
    assert payload["unity_signoff_status"] in {"pass", "incomplete", "fail", "not_run"}
    assert payload["unity_csharp_bridge_status"] in {"pass", "fail", "not_run"}
    assert payload["unity_cross_engine_equivalence_status"] in {"pass", "incomplete", "fail", "not_run"}
    assert payload["unity_head_to_head_benchmark_status"] in {"pass", "incomplete", "fail", "not_run"}
    assert {"alpha6", "alpha7", "alpha8", "beta1"} <= set(payload["unity_parity"])
    assert payload["unity_runtime_launcher"] in {
        "macos-login-shell-interactive",
        "batchmode",
        "batchmode-nographics",
    }
    assert payload["unity_demo_status"] in {"pass", "fail", "blocked_license", "not_run"}
    assert payload["runtime_notes"]
    assert "package:package_json" in check_names
    assert "native:current-platform" in check_names
    assert "native:macos" in check_names
    assert "runtime:launcher" in check_names
    assert "runtime:bridge-probe" in check_names
    assert "runtime:orientation-scene" in check_names
    assert "runtime:startup-probe" in check_names
    assert "runtime:install-smoke" in check_names
    assert "runtime:install-smoke-matrix" in check_names
    assert "runtime:host-bundle-matrix" in check_names
    assert "runtime:signoff" in check_names
    assert "runtime:cross-engine-equivalence" in check_names
    assert "runtime:head-to-head-benchmark" in check_names
    assert "parity:beta1" in check_names
    assert payload["package_root"].replace("\\", "/").endswith("packages/unity/com.sheepfling.fastdis")
    assert any("swap-baseline-init" in step for step in payload["next_steps"])
    assert any("swap-import-smoke" in step for step in payload["next_steps"])
    assert any("swap-benchmark" in step for step in payload["next_steps"])
    assert any("replay-matrix" in step for step in payload["next_steps"])
    assert any("parity-check --milestone beta1" in step for step in payload["next_steps"])
    assert payload["recommended_editor_overrides"]


def test_swap_baseline_init_alias_is_supported(monkeypatch) -> None:
    monkeypatch.setattr(sys, "argv", ["unity_workflow.py", "swap-baseline-init", "--unity-version", "6000.5.0f1"])
    args = unity_workflow.parse_args()

    assert args.command == "swap-baseline-init"


def test_swap_import_smoke_alias_is_supported(monkeypatch) -> None:
    monkeypatch.setattr(sys, "argv", ["unity_workflow.py", "swap-import-smoke", "--unity-version", "6000.5"])
    args = unity_workflow.parse_args()

    assert args.command == "swap-import-smoke"


def test_swap_benchmark_alias_is_supported(monkeypatch) -> None:
    monkeypatch.setattr(sys, "argv", ["unity_workflow.py", "swap-benchmark"])
    args = unity_workflow.parse_args()

    assert args.command == "swap-benchmark"


def test_unity_doctor_reports_native_matrix_when_present(monkeypatch) -> None:
    monkeypatch.setattr(
        unity_workflow,
        "latest_runtime_report",
        lambda out_dir=unity_workflow.DEFAULT_REPORT_DIR: {"overall_status": "pass", "lanes": [{"platform": "EditorMethod", "launch": "login-shell"}]},
    )
    monkeypatch.setattr(
        unity_workflow,
        "latest_orientation_report",
        lambda out_dir=unity_workflow.DEFAULT_REPORT_DIR: {"status": "pass", "scene": "Assets/Scenes/OrientationVerification.unity"},
    )
    monkeypatch.setattr(
        unity_workflow,
        "latest_bridge_probe_report",
        lambda out_dir=unity_workflow.DEFAULT_REPORT_DIR: {"overall_status": "pass", "native_library": "/tmp/libfastdis.dylib"},
    )
    monkeypatch.setattr(
        unity_workflow,
        "latest_install_smoke_report",
        lambda out_dir=unity_workflow.DEFAULT_REPORT_DIR: {"status": "pass", "host_platform": "macos", "repo_root": "/tmp/repo", "failure_stage": "none", "failure_reason": "none"},
    )
    monkeypatch.setattr(
        unity_workflow,
        "latest_native_matrix_report",
        lambda out_dir=unity_workflow.DEFAULT_REPORT_DIR: {"status": "pass", "targets": {"macos": {"status": "pass"}, "windows": {"status": "pass"}, "linux": {"status": "pass"}}},
    )
    monkeypatch.setattr(unity_workflow, "latest_install_matrix_report", lambda out_dir=unity_workflow.DEFAULT_REPORT_DIR: None)
    monkeypatch.setattr(unity_workflow, "latest_host_matrix_report", lambda out_dir=unity_workflow.DEFAULT_REPORT_DIR: None)
    monkeypatch.setattr(unity_workflow, "latest_signoff_report", lambda out_dir=unity_workflow.DEFAULT_REPORT_DIR: None)
    monkeypatch.setattr(
        unity_workflow,
        "latest_cross_engine_equivalence_report",
        lambda out_dir=unity_workflow.DEFAULT_REPORT_DIR: {"status": "complete"},
    )
    monkeypatch.setattr(
        unity_workflow,
        "latest_head_to_head_benchmark_report",
        lambda out_dir=unity_workflow.DEFAULT_REPORT_DIR: {"status": "complete"},
    )
    monkeypatch.setattr(
        unity_workflow,
        "install_smoke_matrix_reports",
        lambda out_dir=unity_workflow.DEFAULT_REPORT_DIR: {"macos": {"status": "pass", "host_platform": "macos"}},
    )

    payload = unity_workflow.doctor_payload(None)

    assert payload["unity_native_matrix_status"] == "pass"
    assert payload["unity_native_matrix_targets"] == ["macos", "windows", "linux"]
    assert payload["unity_cross_engine_equivalence_status"] == "pass"
    assert payload["unity_head_to_head_benchmark_status"] == "pass"
    assert payload["unity_parity"]["alpha6"]["status"] == "FAIL"
    check = next(item for item in payload["checks"] if item["name"] == "runtime:native-matrix")
    assert check["status"] == "ok"


def test_install_smoke_matrix_reports_incomplete_until_all_hosts_present(monkeypatch) -> None:
    monkeypatch.setattr(
        unity_workflow,
        "latest_runtime_report",
        lambda out_dir=unity_workflow.DEFAULT_REPORT_DIR: {"overall_status": "pass", "lanes": [{"platform": "EditorMethod", "launch": "login-shell"}]},
    )
    monkeypatch.setattr(
        unity_workflow,
        "latest_orientation_report",
        lambda out_dir=unity_workflow.DEFAULT_REPORT_DIR: {"status": "pass", "scene": "Assets/Scenes/OrientationVerification.unity"},
    )
    monkeypatch.setattr(
        unity_workflow,
        "latest_bridge_probe_report",
        lambda out_dir=unity_workflow.DEFAULT_REPORT_DIR: {"overall_status": "pass", "native_library": "/tmp/libfastdis.dylib"},
    )
    monkeypatch.setattr(unity_workflow, "latest_install_matrix_report", lambda out_dir=unity_workflow.DEFAULT_REPORT_DIR: None)
    monkeypatch.setattr(
        unity_workflow,
        "latest_install_smoke_report",
        lambda out_dir=unity_workflow.DEFAULT_REPORT_DIR: {"status": "pass", "host_platform": "macos", "repo_root": "/tmp/repo", "failure_stage": "none", "failure_reason": "none"},
    )
    monkeypatch.setattr(unity_workflow, "latest_host_matrix_report", lambda out_dir=unity_workflow.DEFAULT_REPORT_DIR: None)
    monkeypatch.setattr(unity_workflow, "latest_signoff_report", lambda out_dir=unity_workflow.DEFAULT_REPORT_DIR: None)
    monkeypatch.setattr(unity_workflow, "latest_cross_engine_equivalence_report", lambda out_dir=unity_workflow.DEFAULT_REPORT_DIR: None)
    monkeypatch.setattr(unity_workflow, "latest_head_to_head_benchmark_report", lambda out_dir=unity_workflow.DEFAULT_REPORT_DIR: None)
    monkeypatch.setattr(
        unity_workflow,
        "install_smoke_matrix_reports",
        lambda out_dir=unity_workflow.DEFAULT_REPORT_DIR: {"macos": {"status": "pass", "host_platform": "macos"}},
    )

    payload = unity_workflow.doctor_payload(None)

    assert payload["unity_install_status"] == "pass"
    assert payload["unity_install_host"] == "macos"
    assert payload["unity_install_matrix_status"] == "incomplete"
    assert payload["unity_install_matrix_hosts"] == ["macos"]
    assert payload["unity_host_matrix_status"] == "not_run"
    assert payload["unity_signoff_status"] == "not_run"
    assert payload["unity_cross_engine_equivalence_status"] == "not_run"
    assert payload["unity_head_to_head_benchmark_status"] == "not_run"
    assert payload["next_scope"] == "Release polish"


def test_unity_report_command_reads_requested_out_dir(tmp_path: Path) -> None:
    report_dir = tmp_path / "reports"
    report_dir.mkdir()
    (report_dir / "unity_runtime_verification.json").write_text(
        '{"overall_status":"pass","lanes":[{"platform":"EditorMethod","launch":"login-shell"}]}\n',
        encoding="utf-8",
    )
    (report_dir / "unity_orientation_verification.json").write_text(
        '{"status":"pass","scene":"Assets/Scenes/OrientationVerification.unity"}\n',
        encoding="utf-8",
    )
    (report_dir / "unity_csharp_bridge_probe.json").write_text(
        '{"overall_status":"pass","native_library":"/tmp/libfastdis.dylib"}\n',
        encoding="utf-8",
    )
    (report_dir / "unity_install_smoke_macos.json").write_text(
        '{"schema":"fastdis.unity_install_smoke.v1","status":"pass","host_platform":"macos","repo_root":"/tmp/repo","failure_stage":"none","failure_reason":"none"}\n',
        encoding="utf-8",
    )
    (report_dir / "unity_install_smoke_windows.json").write_text(
        '{"schema":"fastdis.unity_install_smoke.v1","status":"pass","host_platform":"windows","repo_root":"/tmp/repo","failure_stage":"none","failure_reason":"none"}\n',
        encoding="utf-8",
    )
    (report_dir / "unity_install_smoke_linux.json").write_text(
        '{"schema":"fastdis.unity_install_smoke.v1","status":"pass","host_platform":"linux","repo_root":"/tmp/repo","failure_stage":"none","failure_reason":"none"}\n',
        encoding="utf-8",
    )
    args = type("Args", (), {"unity_version": None, "out_dir": str(report_dir)})()

    assert unity_workflow.command_report(args) == 0
    payload = json.loads((report_dir / "unity_workflow_report.json").read_text(encoding="utf-8"))
    assert payload["unity_runtime_status"] == "pass"
    assert payload["unity_install_matrix_status"] == "pass"
    assert payload["unity_install_matrix_hosts"] == ["macos", "windows", "linux"]
    assert payload["unity_host_matrix_status"] == "not_run"
    assert payload["unity_signoff_status"] == "not_run"
    assert payload["unity_cross_engine_equivalence_status"] == "not_run"
    assert payload["unity_head_to_head_benchmark_status"] == "not_run"


def test_unity_doctor_uses_install_matrix_report_when_present(monkeypatch) -> None:
    monkeypatch.setattr(
        unity_workflow,
        "latest_runtime_report",
        lambda out_dir=unity_workflow.DEFAULT_REPORT_DIR: {"overall_status": "pass", "lanes": [{"platform": "EditorMethod", "launch": "login-shell"}]},
    )
    monkeypatch.setattr(
        unity_workflow,
        "latest_orientation_report",
        lambda out_dir=unity_workflow.DEFAULT_REPORT_DIR: {"status": "pass", "scene": "Assets/Scenes/OrientationVerification.unity"},
    )
    monkeypatch.setattr(
        unity_workflow,
        "latest_bridge_probe_report",
        lambda out_dir=unity_workflow.DEFAULT_REPORT_DIR: {"overall_status": "pass", "native_library": "/tmp/libfastdis.dylib"},
    )
    monkeypatch.setattr(
        unity_workflow,
        "latest_install_smoke_report",
        lambda out_dir=unity_workflow.DEFAULT_REPORT_DIR: {"status": "pass", "host_platform": "macos", "repo_root": "/tmp/repo", "failure_stage": "none", "failure_reason": "none"},
    )
    monkeypatch.setattr(
        unity_workflow,
        "latest_install_matrix_report",
        lambda out_dir=unity_workflow.DEFAULT_REPORT_DIR: {"overall_status": "cross-host-failed"},
    )
    monkeypatch.setattr(
        unity_workflow,
        "install_smoke_matrix_reports",
        lambda out_dir=unity_workflow.DEFAULT_REPORT_DIR: {"macos": {"status": "pass", "host_platform": "macos"}},
    )

    payload = unity_workflow.doctor_payload(None)

    assert payload["unity_install_matrix_status"] == "fail"
    check_names = {check["name"] for check in payload["checks"]}
    assert "runtime:install-signoff" in check_names


def test_unity_doctor_reads_host_matrix_and_signoff_reports(monkeypatch) -> None:
    monkeypatch.setattr(
        unity_workflow,
        "latest_runtime_report",
        lambda out_dir=unity_workflow.DEFAULT_REPORT_DIR: {"overall_status": "pass", "lanes": [{"platform": "EditorMethod", "launch": "login-shell"}]},
    )
    monkeypatch.setattr(
        unity_workflow,
        "latest_orientation_report",
        lambda out_dir=unity_workflow.DEFAULT_REPORT_DIR: {"status": "pass", "scene": "Assets/Scenes/OrientationVerification.unity"},
    )
    monkeypatch.setattr(
        unity_workflow,
        "latest_bridge_probe_report",
        lambda out_dir=unity_workflow.DEFAULT_REPORT_DIR: {"overall_status": "pass", "native_library": "/tmp/libfastdis.dylib"},
    )
    monkeypatch.setattr(
        unity_workflow,
        "latest_install_smoke_report",
        lambda out_dir=unity_workflow.DEFAULT_REPORT_DIR: {"status": "pass", "host_platform": "macos", "repo_root": "/tmp/repo", "failure_stage": "none", "failure_reason": "none"},
    )
    monkeypatch.setattr(
        unity_workflow,
        "latest_install_matrix_report",
        lambda out_dir=unity_workflow.DEFAULT_REPORT_DIR: {"overall_status": "cross-host-incomplete"},
    )
    monkeypatch.setattr(
        unity_workflow,
        "latest_host_matrix_report",
        lambda out_dir=unity_workflow.DEFAULT_REPORT_DIR: {"overall_status": "cross-host-ready", "ready_platforms": ["linux", "macos", "windows"]},
    )
    monkeypatch.setattr(
        unity_workflow,
        "latest_signoff_report",
        lambda out_dir=unity_workflow.DEFAULT_REPORT_DIR: {"overall_status": "not-fully-signed-off"},
    )
    monkeypatch.setattr(
        unity_workflow,
        "latest_cross_engine_equivalence_report",
        lambda out_dir=unity_workflow.DEFAULT_REPORT_DIR: {"status": "complete"},
    )
    monkeypatch.setattr(
        unity_workflow,
        "latest_head_to_head_benchmark_report",
        lambda out_dir=unity_workflow.DEFAULT_REPORT_DIR: {
            "status": "incomplete",
            "validation": {"grill_errors": ["missing payload"], "fastdis_errors": []},
        },
    )
    monkeypatch.setattr(
        unity_workflow,
        "install_smoke_matrix_reports",
        lambda out_dir=unity_workflow.DEFAULT_REPORT_DIR: {"macos": {"status": "pass", "host_platform": "macos"}},
    )

    payload = unity_workflow.doctor_payload(None)

    assert payload["unity_host_matrix_status"] == "pass"
    assert payload["unity_signoff_status"] == "incomplete"
    assert payload["unity_cross_engine_equivalence_status"] == "pass"
    assert payload["unity_head_to_head_benchmark_status"] == "incomplete"
    host_matrix_check = next(check for check in payload["checks"] if check["name"] == "runtime:host-bundle-matrix")
    signoff_check = next(check for check in payload["checks"] if check["name"] == "runtime:signoff")
    cross_engine_check = next(check for check in payload["checks"] if check["name"] == "runtime:cross-engine-equivalence")
    head_to_head_check = next(check for check in payload["checks"] if check["name"] == "runtime:head-to-head-benchmark")
    assert host_matrix_check["status"] == "ok"
    assert "cross-host-ready" in host_matrix_check["detail"]
    assert signoff_check["status"] == "warn"
    assert "not-fully-signed-off" in signoff_check["detail"]
    assert cross_engine_check["status"] == "ok"
    assert "complete" in cross_engine_check["detail"]
    assert head_to_head_check["status"] == "warn"
    assert "incomplete" in head_to_head_check["detail"]
    assert "grill_errors=missing payload" in head_to_head_check["detail"]
    parity_check = next(check for check in payload["checks"] if check["name"] == "parity:beta1")
    assert parity_check["status"] == "warn"
    assert "FAIL" in parity_check["detail"]
    assert "head_to_head_benchmark" in parity_check["detail"]


def test_unity_doctor_derives_install_failure_stage_from_project_state(monkeypatch) -> None:
    monkeypatch.setattr(
        unity_workflow,
        "latest_runtime_report",
        lambda out_dir=unity_workflow.DEFAULT_REPORT_DIR: {"overall_status": "pass", "lanes": [{"platform": "EditorMethod", "launch": "login-shell"}]},
    )
    monkeypatch.setattr(
        unity_workflow,
        "latest_orientation_report",
        lambda out_dir=unity_workflow.DEFAULT_REPORT_DIR: {"status": "pass", "scene": "Assets/Scenes/OrientationVerification.unity"},
    )
    monkeypatch.setattr(
        unity_workflow,
        "latest_bridge_probe_report",
        lambda out_dir=unity_workflow.DEFAULT_REPORT_DIR: {"overall_status": "pass", "native_library": "/tmp/libfastdis.dylib"},
    )
    monkeypatch.setattr(unity_workflow, "latest_install_matrix_report", lambda out_dir=unity_workflow.DEFAULT_REPORT_DIR: None)
    monkeypatch.setattr(
        unity_workflow,
        "latest_install_smoke_report",
        lambda out_dir=unity_workflow.DEFAULT_REPORT_DIR: {
            "status": "fail",
            "host_platform": "macos",
            "repo_root": "/tmp/repo",
            "project_state": {"library_exists": False, "package_cache_exists": False, "script_assemblies_exists": False},
            "package_cache_locations": [],
        },
    )
    monkeypatch.setattr(unity_workflow, "install_smoke_matrix_reports", lambda out_dir=unity_workflow.DEFAULT_REPORT_DIR: {})

    payload = unity_workflow.doctor_payload(None)

    install_check = next(check for check in payload["checks"] if check["name"] == "runtime:install-smoke")
    host_health = next(check for check in payload["checks"] if check["name"] == "runtime:install-host-health")
    assert "stage=host-startup" in install_check["detail"]
    assert "reason=project-import-never-started" in install_check["detail"]
    assert host_health["status"] == "warn"


def test_unity_runtime_verify_command_builds_expected_runner(monkeypatch) -> None:
    recorded: list[list[str]] = []

    def fake_run_step(cmd: list[str], **_kwargs: object) -> int:
        recorded.append(cmd)
        return 0

    monkeypatch.setattr(unity_workflow, "run_step", fake_run_step)
    args = type(
        "Args",
        (),
        {
            "unity_version": "6000.5",
            "platform": ["EditMode"],
            "project_dir": "/tmp/fastdis_unity_test_project",
            "out_dir": "/tmp/fastdis_unity_reports",
            "timeout": 123,
            "dry_run": True,
        },
    )()

    assert unity_workflow.command_runtime_verify(args) == 0
    assert recorded
    assert recorded[0][:2] == unity_env.python_command() + ["tools/run_unity_editor_tests.py"][-1:]
    assert "--unity-version" in recorded[0]
    assert "--platform" in recorded[0]
    assert "--dry-run" in recorded[0]


def test_unity_demo_command_reuses_runtime_verifier(monkeypatch) -> None:
    recorded: list[object] = []

    def fake_runtime_verify(args: object) -> int:
        recorded.append(args)
        return 0

    monkeypatch.setattr(unity_workflow, "command_runtime_verify", fake_runtime_verify)
    args = type("Args", (), {"unity_version": "6000.5", "out_dir": "/tmp/fastdis_unity_reports", "timeout": 456, "dry_run": True})()

    assert unity_workflow.command_demo(args) == 0
    assert recorded
    forwarded = recorded[0]
    assert forwarded.unity_version == "6000.5"
    assert forwarded.out_dir == "/tmp/fastdis_unity_reports"
    assert forwarded.timeout == 456
    assert forwarded.dry_run is True


def test_unity_bridge_probe_command_builds_expected_runner(monkeypatch) -> None:
    recorded: list[list[str]] = []

    def fake_run_step(cmd: list[str], **_kwargs: object) -> int:
        recorded.append(cmd)
        return 0

    monkeypatch.setattr(unity_workflow, "run_step", fake_run_step)
    args = type("Args", (), {"out_dir": "/tmp/fastdis_unity_reports"})()

    assert unity_workflow.command_bridge_probe(args) == 0
    assert recorded == [unity_env.python_command() + ["tools/probe_unity_csharp_bridge.py", "--out-dir", "/tmp/fastdis_unity_reports"]]


def test_unity_parity_check_command_delegates_to_gate(monkeypatch) -> None:
    recorded: list[list[str]] = []

    def fake_main(argv: list[str]) -> int:
        recorded.append(argv)
        return 0

    monkeypatch.setattr(unity_workflow.check_unity_parity, "main", fake_main)
    args = type("Args", (), {"matrix": "/tmp/unity_grill_parity.yaml", "milestone": "alpha6", "format": "json"})()

    assert unity_workflow.command_parity_check(args) == 0
    assert recorded == [[
        "--matrix",
        "/tmp/unity_grill_parity.yaml",
        "--milestone",
        "alpha6",
        "--format",
        "json",
    ]]


def test_unity_orientation_verify_command_builds_expected_runner(monkeypatch) -> None:
    recorded: list[list[str]] = []

    def fake_run_step(cmd: list[str], **_kwargs: object) -> int:
        recorded.append(cmd)
        return 0

    monkeypatch.setattr(unity_workflow, "run_step", fake_run_step)
    args = type("Args", (), {"unity_version": "6000.5", "out_dir": "/tmp/fastdis_unity_reports", "timeout": 321})()

    assert unity_workflow.command_orientation_verify(args) == 0
    assert recorded == [
        unity_env.python_command()
        + ["tools/run_unity_orientation_verification.py", "--unity-version", "6000.5", "--out-dir", "/tmp/fastdis_unity_reports", "--timeout", "321"]
    ]


def test_unity_install_smoke_command_builds_expected_runner(monkeypatch) -> None:
    recorded: list[list[str]] = []

    def fake_run_step(cmd: list[str], **_kwargs: object) -> int:
        recorded.append(cmd)
        return 0

    monkeypatch.setattr(unity_workflow, "run_step", fake_run_step)
    args = type("Args", (), {"unity_version": "6000.5", "out_dir": "/tmp/fastdis_unity_reports", "timeout": 654})()

    assert unity_workflow.command_install_smoke(args) == 0
    assert recorded == [
        unity_env.python_command()
        + ["tools/run_unity_install_smoke.py", "--unity-version", "6000.5", "--out-dir", "/tmp/fastdis_unity_reports", "--timeout", "654"]
    ]


def test_unity_startup_probe_command_builds_expected_runner(monkeypatch) -> None:
    recorded: list[list[str]] = []

    def fake_run_step(cmd: list[str], **_kwargs: object) -> int:
        recorded.append(cmd)
        return 0

    monkeypatch.setattr(unity_workflow, "run_step", fake_run_step)
    args = type("Args", (), {"unity_version": "6000.5", "project_dir": "/tmp/startup_project", "out_dir": "/tmp/fastdis_unity_reports", "timeout": 77})()

    assert unity_workflow.command_startup_probe(args) == 0
    assert recorded == [
        unity_env.python_command()
        + [
            "tools/run_unity_startup_probe.py",
            "--unity-version",
            "6000.5",
            "--project-dir",
            "/tmp/startup_project",
            "--out-dir",
            "/tmp/fastdis_unity_reports",
            "--timeout",
            "77",
        ]
    ]


def test_unity_install_matrix_command_builds_expected_runner(monkeypatch) -> None:
    recorded: list[list[str]] = []

    def fake_run_step(cmd: list[str], **_kwargs: object) -> int:
        recorded.append(cmd)
        return 0

    monkeypatch.setattr(unity_workflow, "run_step", fake_run_step)
    args = type("Args", (), {"report_dir": "/tmp/fastdis_unity_reports", "out_dir": "/tmp/fastdis_unity_reports"})()

    assert unity_workflow.command_install_matrix(args) == 0
    assert recorded == [
        unity_env.python_command()
        + ["tools/run_unity_install_matrix.py", "--report-dir", "/tmp/fastdis_unity_reports", "--out-dir", "/tmp/fastdis_unity_reports"]
    ]


def test_unity_adopt_install_smoke_command_builds_expected_runner(monkeypatch) -> None:
    recorded: list[list[str]] = []

    def fake_run_step(cmd: list[str], **_kwargs: object) -> int:
        recorded.append(cmd)
        return 0

    monkeypatch.setattr(unity_workflow, "run_step", fake_run_step)
    args = type(
        "Args",
        (),
        {"host": "windows", "report": "/tmp/windows_unity_install_smoke.json", "log": "/tmp/windows_unity_install_smoke.log", "out_dir": "/tmp/fastdis_unity_reports"},
    )()

    assert unity_workflow.command_adopt_install_smoke(args) == 0
    assert recorded == [
        unity_env.python_command()
        + [
            "tools/adopt_unity_install_smoke.py",
            "--host",
            "windows",
            "--report",
            "/tmp/windows_unity_install_smoke.json",
            "--log",
            "/tmp/windows_unity_install_smoke.log",
            "--out-dir",
            "/tmp/fastdis_unity_reports",
        ]
    ]


def test_unity_stage_host_report_command_builds_expected_runner(monkeypatch) -> None:
    recorded: list[list[str]] = []

    def fake_run_step(cmd: list[str], **_kwargs: object) -> int:
        recorded.append(cmd)
        return 0

    monkeypatch.setattr(unity_workflow, "run_step", fake_run_step)
    args = type(
        "Args",
        (),
        {
            "source_dir": "/tmp/fastdis_unity_reports",
            "dest_root": "/tmp/unity_hosts",
            "host_label": "windows-demo",
            "host_platform": "windows",
            "overwrite": True,
        },
    )()

    assert unity_workflow.command_stage_host_report(args) == 0
    assert recorded == [
        unity_env.python_command()
        + [
            "tools/stage_unity_host_report.py",
            "--source-dir",
            "/tmp/fastdis_unity_reports",
            "--dest-root",
            "/tmp/unity_hosts",
            "--host-label",
            "windows-demo",
            "--host-platform",
            "windows",
            "--overwrite",
        ]
    ]


def test_unity_export_host_report_command_builds_expected_runner(monkeypatch) -> None:
    recorded: list[list[str]] = []

    def fake_run_step(cmd: list[str], **_kwargs: object) -> int:
        recorded.append(cmd)
        return 0

    monkeypatch.setattr(unity_workflow, "run_step", fake_run_step)
    args = type("Args", (), {"host_label": "windows-demo", "host_root": "/tmp/unity_hosts", "out_dir": "/tmp/unity_archives"})()

    assert unity_workflow.command_export_host_report(args) == 0
    assert recorded == [
        unity_env.python_command()
        + ["tools/export_unity_host_report.py", "windows-demo", "--host-root", "/tmp/unity_hosts", "--out-dir", "/tmp/unity_archives"]
    ]


def test_unity_export_host_handoff_command_builds_expected_runner(monkeypatch) -> None:
    recorded: list[list[str]] = []

    def fake_run_step(cmd: list[str], **_kwargs: object) -> int:
        recorded.append(cmd)
        return 0

    monkeypatch.setattr(unity_workflow, "run_step", fake_run_step)
    args = type("Args", (), {"out_dir": "/tmp/unity_handoff"})()

    assert unity_workflow.command_export_host_handoff(args) == 0
    assert recorded == [
        unity_env.python_command() + ["tools/export_unity_host_handoff.py", "--out-dir", "/tmp/unity_handoff"]
    ]


def test_unity_import_host_report_command_builds_expected_runner(monkeypatch) -> None:
    recorded: list[list[str]] = []

    def fake_run_step(cmd: list[str], **_kwargs: object) -> int:
        recorded.append(cmd)
        return 0

    monkeypatch.setattr(unity_workflow, "run_step", fake_run_step)
    args = type(
        "Args",
        (),
        {"archive": "/tmp/windows-demo.zip", "host_root": "/tmp/unity_hosts", "report_dir": "/tmp/fastdis_unity_reports", "overwrite": True, "checksum": "/tmp/windows-demo.zip.sha256"},
    )()

    assert unity_workflow.command_import_host_report(args) == 0
    assert recorded == [
        unity_env.python_command()
        + [
            "tools/import_unity_host_report.py",
            "/tmp/windows-demo.zip",
            "--host-root",
            "/tmp/unity_hosts",
            "--report-dir",
            "/tmp/fastdis_unity_reports",
            "--overwrite",
            "--checksum",
            "/tmp/windows-demo.zip.sha256",
        ]
    ]


def test_unity_sync_host_reports_command_builds_expected_runner(monkeypatch) -> None:
    recorded: list[list[str]] = []

    def fake_run_step(cmd: list[str], **_kwargs: object) -> int:
        recorded.append(cmd)
        return 0

    monkeypatch.setattr(unity_workflow, "run_step", fake_run_step)
    args = type("Args", (), {"host_root": "/tmp/unity_hosts", "report_dir": "/tmp/fastdis_unity_reports"})()

    assert unity_workflow.command_sync_host_reports(args) == 0
    assert recorded == [
        unity_env.python_command()
        + ["tools/sync_unity_host_reports.py", "--host-root", "/tmp/unity_hosts", "--report-dir", "/tmp/fastdis_unity_reports"]
    ]


def test_unity_host_matrix_command_builds_expected_runner(monkeypatch) -> None:
    recorded: list[list[str]] = []

    def fake_run_step(cmd: list[str], **_kwargs: object) -> int:
        recorded.append(cmd)
        return 0

    monkeypatch.setattr(unity_workflow, "run_step", fake_run_step)
    args = type("Args", (), {"host_root": "/tmp/unity_hosts", "out_dir": "/tmp/fastdis_unity_reports"})()

    assert unity_workflow.command_host_matrix(args) == 0
    assert recorded == [
        unity_env.python_command()
        + ["tools/run_unity_host_matrix.py", "--host-root", "/tmp/unity_hosts", "--out-dir", "/tmp/fastdis_unity_reports"]
    ]


def test_unity_signoff_command_builds_expected_runner(monkeypatch) -> None:
    recorded: list[list[str]] = []

    def fake_run_step(cmd: list[str], **_kwargs: object) -> int:
        recorded.append(cmd)
        return 0

    monkeypatch.setattr(unity_workflow, "run_step", fake_run_step)
    args = type("Args", (), {"report_dir": "/tmp/fastdis_unity_reports", "host_root": "/tmp/unity_hosts", "out_dir": "/tmp/fastdis_unity_reports"})()

    assert unity_workflow.command_signoff(args) == 0
    assert recorded == [
        unity_env.python_command()
        + ["tools/run_unity_signoff.py", "--report-dir", "/tmp/fastdis_unity_reports", "--host-root", "/tmp/unity_hosts", "--out-dir", "/tmp/fastdis_unity_reports"]
    ]


def test_unity_cross_engine_equivalence_command_builds_expected_runner(monkeypatch) -> None:
    recorded: list[list[str]] = []

    def fake_run_step(cmd: list[str], **_kwargs: object) -> int:
        recorded.append(cmd)
        return 0

    monkeypatch.setattr(unity_workflow, "run_step", fake_run_step)
    args = type("Args", (), {"out_dir": "/tmp/fastdis_unity_reports"})()

    assert unity_workflow.command_cross_engine_equivalence(args) == 0
    assert recorded == [
        unity_env.python_command()
        + [
            "tools/build_unity_cross_engine_equivalence_report.py",
            "--json-out",
            "/tmp/fastdis_unity_reports/unity_cross_engine_equivalence.json",
            "--md-out",
            "/tmp/fastdis_unity_reports/unity_cross_engine_equivalence.md",
        ]
    ]


def test_unity_head_to_head_benchmark_command_builds_expected_runner(monkeypatch) -> None:
    recorded: list[list[str]] = []

    def fake_run_step(cmd: list[str], **_kwargs: object) -> int:
        recorded.append(cmd)
        return 0

    monkeypatch.setattr(unity_workflow, "run_step", fake_run_step)
    args = type(
        "Args",
        (),
        {
            "out_dir": "/tmp/fastdis_unity_reports",
            "fastdis": "/tmp/bench/current.json",
            "grill": "/tmp/grill/baseline.json",
        },
    )()

    assert unity_workflow.command_head_to_head_benchmark(args) == 0
    assert recorded == [
        unity_env.python_command()
        + [
            "tools/build_unity_head_to_head_benchmark_report.py",
            "--fastdis",
            "/tmp/bench/current.json",
            "--grill",
            "/tmp/grill/baseline.json",
            "--json-out",
            "/tmp/fastdis_unity_reports/unity_head_to_head_benchmark.json",
            "--md-out",
            "/tmp/fastdis_unity_reports/unity_head_to_head_benchmark.md",
        ]
    ]


def test_unity_grill_baseline_init_command_builds_expected_runner(monkeypatch) -> None:
    recorded: list[list[str]] = []

    def fake_run_step(cmd: list[str], **_kwargs: object) -> int:
        recorded.append(cmd)
        return 0

    monkeypatch.setattr(unity_workflow, "run_step", fake_run_step)
    args = type(
        "Args",
        (),
        {
            "out": "/tmp/grill.json",
            "fastdis": "/tmp/current.json",
            "unity_version": "6000.5.0f1",
            "scene": "LoopbackBench",
            "traffic_mix": "100% Entity State",
            "scripting_backend": "Mono",
            "commit": "abc123",
            "limit_cases": 5,
            "overwrite": True,
        },
    )()

    assert unity_workflow.command_grill_baseline_init(args) == 0
    assert recorded == [
        unity_env.python_command()
        + [
            "tools/init_unity_grill_benchmark_baseline.py",
            "--out",
            "/tmp/grill.json",
            "--fastdis",
            "/tmp/current.json",
            "--unity-version",
            "6000.5.0f1",
            "--scene",
            "LoopbackBench",
            "--traffic-mix",
            "100% Entity State",
            "--scripting-backend",
            "Mono",
            "--commit",
            "abc123",
            "--limit-cases",
            "5",
            "--overwrite",
        ]
    ]


def test_unity_grill_import_smoke_command_builds_expected_runner(monkeypatch) -> None:
    recorded: list[list[str]] = []

    def fake_run_step(cmd: list[str], **_kwargs: object) -> int:
        recorded.append(cmd)
        return 0

    monkeypatch.setattr(unity_workflow, "run_step", fake_run_step)
    args = type(
        "Args",
        (),
        {
            "plugin_root": "/tmp/GRILL_DISPluginForUnity",
            "unity_version": "6000.5",
            "project_dir": "/tmp/grill_project",
            "out_dir": "/tmp/reports",
            "timeout": 90,
        },
    )()

    assert unity_workflow.command_grill_import_smoke(args) == 0
    assert recorded == [
        unity_env.python_command()
        + [
            "tools/run_grill_unity_import_smoke.py",
            "--plugin-root",
            "/tmp/GRILL_DISPluginForUnity",
            "--unity-version",
            "6000.5",
            "--out-dir",
            "/tmp/reports",
            "--timeout",
            "90",
            "--project-dir",
            "/tmp/grill_project",
        ]
    ]


def test_unity_replay_matrix_command_builds_expected_runner(monkeypatch) -> None:
    recorded: list[list[str]] = []

    def fake_run_step(cmd: list[str], **_kwargs: object) -> int:
        recorded.append(cmd)
        return 0

    monkeypatch.setattr(unity_workflow, "run_step", fake_run_step)
    args = type(
        "Args",
        (),
        {
            "unity_version": "6000.5",
            "project_dir": "/tmp/unity_replay_project",
            "out_dir": "/tmp/unity_replay_reports",
            "packet_budget": 64,
            "timeout": 180,
            "if_available": True,
        },
    )()

    assert unity_workflow.command_replay_matrix(args) == 0
    assert recorded == [
        unity_env.python_command()
        + [
            "tools/run_unity_replay_matrix.py",
            "--unity-version",
            "6000.5",
            "--project-dir",
            "/tmp/unity_replay_project",
            "--out-dir",
            "/tmp/unity_replay_reports",
            "--packet-budget",
            "64",
            "--timeout",
            "180",
            "--if-available",
        ]
    ]


def test_unity_capture_host_report_command_builds_expected_runner(monkeypatch) -> None:
    recorded: list[list[str]] = []

    def fake_run_step(cmd: list[str], **_kwargs: object) -> int:
        recorded.append(cmd)
        return 0

    monkeypatch.setattr(unity_workflow, "run_step", fake_run_step)
    args = type(
        "Args",
        (),
        {
            "source_dir": "/tmp/fastdis_unity_reports",
            "host_label": "windows-demo",
            "host_platform": "windows",
            "dest_root": "/tmp/unity_hosts",
            "archive_out_dir": "/tmp/unity_archives",
            "unity_version": "6000.5",
            "skip_full": False,
            "skip_stage": False,
            "skip_export": True,
            "skip_install_matrix": False,
        },
    )()

    assert unity_workflow.command_capture_host_report(args) == 0
    assert recorded == [
        unity_env.python_command()
        + [
            "tools/capture_unity_host_report.py",
            "--source-dir",
            "/tmp/fastdis_unity_reports",
            "--host-label",
            "windows-demo",
            "--host-platform",
            "windows",
            "--dest-root",
            "/tmp/unity_hosts",
            "--archive-out-dir",
            "/tmp/unity_archives",
            "--unity-version",
            "6000.5",
            "--skip-export",
        ]
    ]


def test_unity_build_all_native_runs_matrix_verify_and_report(monkeypatch) -> None:
    calls: list[object] = []

    def fake_run_step(cmd: list[str], **_kwargs: object) -> int:
        calls.append(cmd)
        return 0

    monkeypatch.setattr(unity_workflow, "run_step", fake_run_step)
    monkeypatch.setattr(unity_workflow, "command_verify", lambda _args: calls.append("verify") or 0)
    monkeypatch.setattr(unity_workflow, "command_report", lambda args: calls.append(("report", args.out_dir)) or 0)
    args = type("Args", (), {"unity_version": "6000.5", "skip_native_build": False, "all_native": True})()

    assert unity_workflow.command_build(args) == 0
    assert calls[0] == unity_env.python_command() + ["tools/build_unity_native_matrix.py", "build", "--keep-going", "--out-dir", str(unity_workflow.DEFAULT_REPORT_DIR)]
    assert calls[1] == "verify"
    assert calls[2] == ("report", str(unity_workflow.DEFAULT_REPORT_DIR))


def test_unity_full_reuses_build_verify_and_does_not_run_verify_twice(monkeypatch) -> None:
    calls: list[object] = []

    monkeypatch.setattr(
        unity_workflow,
        "command_doctor",
        lambda _args: calls.append("doctor") or 0,
    )
    monkeypatch.setattr(
        unity_workflow,
        "command_build",
        lambda args: calls.append(("build", args.skip_native_build)) or 0,
    )
    monkeypatch.setattr(
        unity_workflow,
        "command_verify",
        lambda _args: calls.append("verify") or 0,
    )
    monkeypatch.setattr(
        unity_workflow,
        "command_bridge_probe",
        lambda _args: calls.append("bridge") or 0,
    )
    monkeypatch.setattr(
        unity_workflow,
        "command_demo",
        lambda _args: calls.append("demo") or 0,
    )
    monkeypatch.setattr(
        unity_workflow,
        "command_report",
        lambda _args: calls.append("report") or 0,
    )
    monkeypatch.setattr(
        unity_workflow,
        "command_orientation_verify",
        lambda _args: calls.append("orientation") or 0,
    )
    monkeypatch.setattr(
        unity_workflow,
        "command_startup_probe",
        lambda _args: calls.append("startup-probe") or 0,
    )
    monkeypatch.setattr(
        unity_workflow,
        "command_install_smoke",
        lambda _args: calls.append("install") or 0,
    )
    monkeypatch.setattr(
        unity_workflow,
        "command_install_matrix",
        lambda _args: calls.append("install-matrix") or 0,
    )
    monkeypatch.setattr(
        unity_workflow,
        "command_host_matrix",
        lambda _args: calls.append("host-matrix") or 0,
    )
    monkeypatch.setattr(
        unity_workflow,
        "command_signoff",
        lambda _args: calls.append("signoff") or 2,
    )
    monkeypatch.setattr(
        unity_workflow,
        "command_cross_engine_equivalence",
        lambda _args: calls.append("cross-engine-equivalence") or 0,
    )
    monkeypatch.setattr(
        unity_workflow,
        "command_head_to_head_benchmark",
        lambda _args: calls.append("head-to-head-benchmark") or 1,
    )
    args = type("Args", (), {"unity_version": "6000.5", "skip_native_build": True, "skip_runtime": False, "skip_orientation": False, "skip_startup_probe": False, "skip_install_smoke": False})()

    assert unity_workflow.command_full(args) == 0
    assert calls == ["doctor", ("build", True), "bridge", "demo", "orientation", "startup-probe", "install", "install-matrix", "host-matrix", "report", "signoff", "cross-engine-equivalence", "head-to-head-benchmark", "report"]


def test_unity_full_treats_install_matrix_incomplete_as_nonfatal(monkeypatch) -> None:
    monkeypatch.setattr(unity_workflow, "command_doctor", lambda _args: 0)
    monkeypatch.setattr(unity_workflow, "command_build", lambda _args: 0)
    monkeypatch.setattr(unity_workflow, "command_bridge_probe", lambda _args: 0)
    monkeypatch.setattr(unity_workflow, "command_demo", lambda _args: 0)
    monkeypatch.setattr(unity_workflow, "command_orientation_verify", lambda _args: 0)
    monkeypatch.setattr(unity_workflow, "command_startup_probe", lambda _args: 0)
    monkeypatch.setattr(unity_workflow, "command_install_smoke", lambda _args: 0)
    monkeypatch.setattr(unity_workflow, "command_install_matrix", lambda _args: 1)
    monkeypatch.setattr(unity_workflow, "command_host_matrix", lambda _args: 1)
    monkeypatch.setattr(unity_workflow, "command_signoff", lambda _args: 2)
    monkeypatch.setattr(unity_workflow, "command_cross_engine_equivalence", lambda _args: 0)
    monkeypatch.setattr(unity_workflow, "command_head_to_head_benchmark", lambda _args: 1)
    monkeypatch.setattr(unity_workflow, "command_report", lambda _args: 0)
    args = type("Args", (), {"unity_version": "6000.5", "skip_native_build": True, "skip_runtime": False, "skip_orientation": False, "skip_startup_probe": False, "skip_install_smoke": False})()

    assert unity_workflow.command_full(args) == 0


def test_unity_full_forwards_skip_native_build_flag(monkeypatch) -> None:
    captured: list[bool] = []

    monkeypatch.setattr(unity_workflow, "command_doctor", lambda _args: 0)
    monkeypatch.setattr(unity_workflow, "command_build", lambda args: captured.append(bool(args.skip_native_build)) or 0)
    monkeypatch.setattr(unity_workflow, "command_bridge_probe", lambda _args: 0)
    monkeypatch.setattr(unity_workflow, "command_demo", lambda _args: 0)
    monkeypatch.setattr(unity_workflow, "command_orientation_verify", lambda _args: 0)
    monkeypatch.setattr(unity_workflow, "command_startup_probe", lambda _args: 0)
    monkeypatch.setattr(unity_workflow, "command_install_smoke", lambda _args: 0)
    monkeypatch.setattr(unity_workflow, "command_install_matrix", lambda _args: 0)
    monkeypatch.setattr(unity_workflow, "command_host_matrix", lambda _args: 0)
    monkeypatch.setattr(unity_workflow, "command_signoff", lambda _args: 2)
    monkeypatch.setattr(unity_workflow, "command_cross_engine_equivalence", lambda _args: 0)
    monkeypatch.setattr(unity_workflow, "command_head_to_head_benchmark", lambda _args: 1)
    monkeypatch.setattr(unity_workflow, "command_report", lambda _args: 0)
    args = type("Args", (), {"unity_version": "6000.5", "skip_native_build": False, "skip_runtime": False, "skip_orientation": False, "skip_startup_probe": False, "skip_install_smoke": False})()

    assert unity_workflow.command_full(args) == 0
    assert captured == [False]


def test_unity_full_skips_install_smoke_when_startup_probe_fails(monkeypatch, tmp_path: Path) -> None:
    calls: list[str] = []

    monkeypatch.setattr(unity_workflow, "command_doctor", lambda _args: 0)
    monkeypatch.setattr(unity_workflow, "command_build", lambda _args: 0)
    monkeypatch.setattr(unity_workflow, "command_bridge_probe", lambda _args: 0)
    monkeypatch.setattr(unity_workflow, "command_demo", lambda _args: 0)
    monkeypatch.setattr(unity_workflow, "command_orientation_verify", lambda _args: 0)
    monkeypatch.setattr(unity_workflow, "command_startup_probe", lambda _args: calls.append("startup-probe") or 1)
    monkeypatch.setattr(unity_workflow, "latest_startup_probe_report", lambda _out_dir=unity_workflow.DEFAULT_REPORT_DIR: {"host_platform": "macos", "project_dir": "/tmp/probe", "project_state": {"library_exists": False}, "attempts": []})
    monkeypatch.setattr(unity_workflow.run_unity_install_smoke, "build_startup_blocked_report", lambda report, out_dir: {"schema": "fastdis.unity_install_smoke.v1", "status": "fail", "host_platform": "macos", "project_state": report["project_state"]})
    monkeypatch.setattr(unity_workflow, "command_install_smoke", lambda _args: calls.append("install") or 0)
    monkeypatch.setattr(unity_workflow, "command_install_matrix", lambda _args: 0)
    monkeypatch.setattr(unity_workflow, "command_host_matrix", lambda _args: 1)
    monkeypatch.setattr(unity_workflow, "command_signoff", lambda _args: 2)
    monkeypatch.setattr(unity_workflow, "command_cross_engine_equivalence", lambda _args: 0)
    monkeypatch.setattr(unity_workflow, "command_head_to_head_benchmark", lambda _args: 1)
    monkeypatch.setattr(unity_workflow, "command_report", lambda _args: 0)
    monkeypatch.setattr(unity_workflow, "ROOT", tmp_path)
    report_dir = tmp_path / "artifacts" / "reports"
    monkeypatch.setattr(unity_workflow, "DEFAULT_REPORT_DIR", report_dir)
    report_dir.mkdir(parents=True)
    args = type("Args", (), {"unity_version": "6000.5", "skip_native_build": False, "skip_runtime": False, "skip_orientation": False, "skip_startup_probe": False, "skip_install_smoke": False})()

    assert unity_workflow.command_full(args) == 1
    assert calls == ["startup-probe"]
    assert (report_dir / "unity_install_smoke.json").is_file()


def test_unity_editor_test_project_manifest_references_local_package(tmp_path: Path) -> None:
    project = tmp_path / "unity_project"

    run_unity_editor_tests.create_project(project)

    manifest = (project / "Packages" / "manifest.json").read_text(encoding="utf-8")
    local_package = project / "LocalPackages" / "com.sheepfling.fastdis"
    assert "com.sheepfling.fastdis" in manifest
    assert "file:../LocalPackages/com.sheepfling.fastdis" in manifest
    assert local_package.exists()
    assert "testables" in manifest


def test_unity_editor_method_attempts_include_launch_services_fallback_on_macos(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(run_unity_editor_tests, "use_interactive_editor_method", lambda: True)
    monkeypatch.setattr(run_unity_editor_tests.host_platform, "system", lambda: "Darwin")
    install = unity_env.UnityInstall(
        version="6000.5.0f1",
        install_root="/Applications/Unity/Hub/Editor/6000.5.0f1",
        editor_path="/Applications/Unity/Hub/Editor/6000.5.0f1/Unity.app/Contents/MacOS/Unity",
        editor_app_path="/Applications/Unity/Hub/Editor/6000.5.0f1/Unity.app",
        source="test",
        quirks=(),
    )

    attempts = run_unity_editor_tests.editor_method_attempts(install, tmp_path / "project", tmp_path / "reports")

    assert [attempt["launch"] for attempt in attempts] == ["login-shell", "launch-services"]
    assert attempts[0]["cmd"][:2] == ["/bin/zsh", "-lc"]
    assert attempts[1]["cmd"][:5] == ["open", "-W", "-n", "-a", install.editor_app_path]


def test_unity_editor_method_retries_launch_services_after_ui_entitlement(monkeypatch, tmp_path: Path) -> None:
    first_result = tmp_path / "first.json"
    second_result = tmp_path / "second.json"
    first_log = tmp_path / "first.log"
    second_log = tmp_path / "second.log"
    first_log.write_text("first attempt\n", encoding="utf-8")
    second_log.write_text("second attempt\n", encoding="utf-8")
    attempts = [
        {
            "mode": "interactive",
            "launch": "login-shell",
            "cmd": ["first"],
            "unity_command": ["first"],
            "env": None,
            "results_json": first_result,
            "log": first_log,
        },
        {
            "mode": "interactive",
            "launch": "launch-services",
            "cmd": ["second"],
            "unity_command": ["second"],
            "env": None,
            "results_json": second_result,
            "log": second_log,
        },
    ]
    diagnostics = {
        first_log: {
            "status": "blocked_license",
            "code": "unity_ui_entitlement_missing",
            "needle": "'com.unity.editor.ui' was not found",
            "detail": "missing ui entitlement",
            "remediation": ["retry differently"],
        },
        second_log: {
            "status": "pass",
            "code": None,
            "needle": None,
            "detail": None,
            "remediation": [],
        },
    }
    payloads = {
        first_result: {},
        second_result: {"status": "pass", "total": 1, "passed": 1, "failed": 0},
    }
    responses = iter(
        [
            (0, False, False, diagnostics[first_log]),
            (0, False, False, diagnostics[second_log]),
        ]
    )

    monkeypatch.setattr(run_unity_editor_tests, "editor_method_attempts", lambda *_args, **_kwargs: attempts)
    monkeypatch.setattr(run_unity_editor_tests, "run_editor_method_process", lambda *_args, **_kwargs: next(responses))
    monkeypatch.setattr(run_unity_editor_tests, "read_editor_method_payload", lambda path: payloads[path])
    monkeypatch.setattr(run_unity_editor_tests, "analyze_log", lambda path: diagnostics[path])

    lane = run_unity_editor_tests.run_unity_editor_method("/tmp/Unity.app/Contents/MacOS/Unity", tmp_path / "project", tmp_path / "reports", timeout=5)

    assert lane["status"] == "pass"
    assert lane["launch"] == "launch-services"
    assert lane["tests"]["passed"] == 1
    assert [attempt["launch"] for attempt in lane["attempts"]] == ["login-shell", "launch-services"]


def test_unity_editor_method_preserves_blocked_license_when_fallback_launcher_fails(monkeypatch, tmp_path: Path) -> None:
    first_result = tmp_path / "first.json"
    second_result = tmp_path / "second.json"
    first_log = tmp_path / "first.log"
    second_log = tmp_path / "second.log"
    second_launcher_log = tmp_path / "launch_services.log"
    attempts = [
        {
            "mode": "interactive",
            "launch": "login-shell",
            "cmd": ["first"],
            "unity_command": ["first"],
            "env": None,
            "results_json": first_result,
            "log": first_log,
        },
        {
            "mode": "interactive",
            "launch": "launch-services",
            "cmd": ["second"],
            "unity_command": ["second"],
            "env": None,
            "results_json": second_result,
            "log": second_log,
            "launcher_log": second_launcher_log,
        },
    ]
    diagnostics = {
        first_log: {
            "status": "blocked_license",
            "code": "unity_ui_entitlement_missing",
            "needle": "'com.unity.editor.ui' was not found",
            "detail": "missing ui entitlement",
            "remediation": ["retry differently"],
        },
        second_log: {
            "status": None,
            "code": None,
            "needle": None,
            "detail": None,
            "remediation": [],
        },
    }
    payloads = {
        first_result: {},
        second_result: {},
    }
    monkeypatch.setattr(run_unity_editor_tests, "editor_method_attempts", lambda *_args, **_kwargs: attempts)
    calls = {"count": 0}

    def fake_run_editor_method_process(*_args, **kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            return (0, False, False, diagnostics[first_log])
        launcher_log_path = kwargs["launcher_log_path"]
        launcher_log_path.write_text("kLSNoExecutableErr\n", encoding="utf-8")
        return (1, False, False, diagnostics[second_log])

    monkeypatch.setattr(run_unity_editor_tests, "run_editor_method_process", fake_run_editor_method_process)
    monkeypatch.setattr(run_unity_editor_tests, "read_editor_method_payload", lambda path: payloads[path])
    monkeypatch.setattr(run_unity_editor_tests, "analyze_log", lambda path: diagnostics[path])

    lane = run_unity_editor_tests.run_unity_editor_method("/tmp/Unity.app/Contents/MacOS/Unity", tmp_path / "project", tmp_path / "reports", timeout=5)

    assert lane["status"] == "blocked_license"
    assert lane["diagnostic_code"] == "unity_ui_entitlement_missing"
    assert "Launch Services fallback also failed" in lane["diagnostic_detail"]


def test_unity_log_analysis_identifies_headless_entitlement(tmp_path: Path) -> None:
    log = tmp_path / "unity.log"
    log.write_text(
        "[Licensing::Module] Error: 'com.unity.editor.headless' was not found.\n"
        "No valid Unity Editor license found. Please activate your license.\n",
        encoding="utf-8",
    )

    analysis = run_unity_editor_tests.analyze_log(log)

    assert analysis["status"] == "blocked_license"
    assert analysis["code"] == "unity_headless_entitlement_missing"
    assert "FASTDIS_UNITY_BATCHMODE" in " ".join(analysis["remediation"])


def test_unity_log_analysis_identifies_ui_entitlement_environment_issue(tmp_path: Path) -> None:
    log = tmp_path / "unity.log"
    log.write_text(
        "[Licensing::Module] Error: 'com.unity.editor.ui' was not found.\n"
        "No valid Unity Editor license found. Please activate your license.\n",
        encoding="utf-8",
    )

    analysis = run_unity_editor_tests.analyze_log(log)

    assert analysis["status"] == "blocked_license"
    assert analysis["code"] == "unity_ui_entitlement_missing"
    assert "login-shell" in " ".join(analysis["remediation"])


def test_unity_log_analysis_identifies_invalid_meta_yaml(tmp_path: Path) -> None:
    log = tmp_path / "unity.log"
    log.write_text(
        "YAML Parsing error 'Parser Failure at line 18: Expect ':' between key and value within mapping'\n",
        encoding="utf-8",
    )

    analysis = run_unity_editor_tests.analyze_log(log)

    assert analysis["status"] == "unity_asset_meta_invalid"
    assert analysis["code"] == "unity_yaml_meta_invalid"


def test_unity_log_analysis_identifies_readonly_database_host_startup_block(tmp_path: Path) -> None:
    log = tmp_path / "unity.log"
    log.write_text(
        "attempt to write a readonly database\n",
        encoding="utf-8",
    )

    analysis = run_unity_editor_tests.analyze_log(log)

    assert analysis["status"] == "host_startup_blocked"
    assert analysis["code"] == "unity_host_startup_readonly_database"
    assert "licensing cache is writable" in " ".join(analysis["remediation"])


def test_runtime_report_derives_phase1_exit_criteria_from_editor_method_checks() -> None:
    report = {
        "lanes": [
            {
                "platform": "EditorMethod",
                "details": {
                    "schema": "fastdis.unity_editor_method_verification.v1",
                    "checks": [
                        {"name": "native_abi_loads", "status": "pass"},
                        {"name": "replay_player_parses_fastdispkt_stream", "status": "pass"},
                        {"name": "replay_player_steps_world_state", "status": "pass"},
                        {"name": "receiver_socket_loopback_feeds_world", "status": "pass"},
                        {"name": "world_processes_entity_state_packet", "status": "pass"},
                        {"name": "world_exposes_last_entity_transform", "status": "pass"},
                        {"name": "world_auto_spawns_and_positions_actor", "status": "pass"},
                        {"name": "remove_entity_request_clears_known_entity", "status": "pass"},
                    ],
                },
            }
        ]
    }

    criteria = run_unity_editor_tests.derive_phase1_exit_criteria(report)
    status_by_name = {item["name"]: item["status"] for item in criteria}

    assert status_by_name["Native library stages and loads in Unity"] == "complete"
    assert status_by_name["Replay demo moves GameObjects"] == "complete"
    assert status_by_name["UDP demo receives live Entity State traffic"] == "complete"
    assert status_by_name["Entity mapper applies transforms to spawned GameObjects"] == "complete"
    assert status_by_name["Diagnostics window exposes runtime counters"] == "complete"


def test_runtime_report_udp_criterion_accepts_legacy_inject_check() -> None:
    report = {
        "lanes": [
            {
                "platform": "EditorMethod",
                "details": {
                    "schema": "fastdis.unity_editor_method_verification.v1",
                    "checks": [
                        {"name": "receiver_inject_packet_feeds_world", "status": "pass"},
                    ],
                },
            }
        ]
    }

    criteria = run_unity_editor_tests.derive_phase1_exit_criteria(report)
    status_by_name = {item["name"]: item["status"] for item in criteria}

    assert status_by_name["UDP demo receives live Entity State traffic"] == "complete"


def test_runtime_report_markdown_lists_phase1_exit_criteria() -> None:
    report = {
        "overall_status": "pass",
        "unity_version": "6000.5.0f1",
        "editor": "/Applications/Unity/Unity.app/Contents/MacOS/Unity",
        "project_dir": "/tmp/runtime_project",
        "phase1_exit_criteria": [
            {
                "name": "Replay demo moves GameObjects",
                "status": "complete",
                "note": "Replay playback advanced world state.",
                "required_checks": [
                    {"name": "replay_player_parses_fastdispkt_stream", "status": "pass"},
                    {"name": "replay_player_steps_world_state", "status": "pass"},
                ],
            }
        ],
        "lanes": [
            {
                "platform": "EditorMethod",
                "status": "pass",
                "diagnostic": None,
                "diagnostic_code": None,
                "tests": {"total": 1, "passed": 1, "failed": 0, "skipped": 0},
                "details": {"schema": "fastdis.unity_editor_method_verification.v1", "total": 1, "passed": 1, "failed": 0, "checks": []},
            }
        ],
    }

    markdown = run_unity_editor_tests.render_markdown(report)

    assert "## Phase 1 Exit Criteria" in markdown
    assert "`complete` Replay demo moves GameObjects" in markdown
    assert "check: pass replay_player_steps_world_state" in markdown


def test_runtime_verifier_preserves_previous_pass_report_on_transient_failed_retry(tmp_path: Path, monkeypatch) -> None:
    out_dir = tmp_path / "reports"
    out_dir.mkdir()
    previous = {
        "schema": "fastdis.unity_runtime_verification.v1",
        "overall_status": "pass",
        "unity_version": "6000.5.0f1",
        "editor": "/tmp/Unity",
        "project_dir": "/tmp/project",
        "lanes": [
            {
                "platform": "EditorMethod",
                "status": "pass",
                "tests": {"status": "pass", "total": 2, "passed": 2, "failed": 0, "skipped": 0},
                "details": {
                    "schema": "fastdis.unity_editor_method_verification.v1",
                    "checks": [
                        {"name": "native_abi_loads", "status": "pass"},
                        {"name": "replay_player_parses_fastdispkt_stream", "status": "pass"},
                        {"name": "replay_player_steps_world_state", "status": "pass"},
                        {"name": "receiver_inject_packet_feeds_world", "status": "pass"},
                        {"name": "world_processes_entity_state_packet", "status": "pass"},
                        {"name": "world_exposes_last_entity_transform", "status": "pass"},
                        {"name": "world_auto_spawns_and_positions_actor", "status": "pass"},
                        {"name": "remove_entity_request_clears_known_entity", "status": "pass"},
                    ],
                },
            }
        ],
    }
    (out_dir / "unity_runtime_verification.json").write_text(json.dumps(previous) + "\n", encoding="utf-8")
    monkeypatch.setattr(run_unity_editor_tests.load_local_env, "load", lambda: None)
    monkeypatch.setattr(
        run_unity_editor_tests,
        "parse_args",
        lambda argv=None: run_unity_editor_tests.argparse.Namespace(
            unity_version="6000.5",
            platform=None,
            project_dir=None,
            out_dir=out_dir,
            timeout=600,
            runner="editor-method",
            dry_run=False,
        ),
    )
    monkeypatch.setattr(
        run_unity_editor_tests.unity_env,
        "resolve_install",
        lambda version: unity_env.UnityInstall(
            version="6000.5.0f1",
            install_root="/tmp",
            editor_path="/tmp/Unity",
            editor_app_path=None,
            source="test",
            quirks=(),
        ),
    )
    monkeypatch.setattr(run_unity_editor_tests, "create_project", lambda _project_dir: None)
    monkeypatch.setattr(
        run_unity_editor_tests,
        "run_unity_editor_method",
        lambda *_args, **_kwargs: {
            "platform": "EditorMethod",
            "status": "fail",
            "diagnostic": None,
            "diagnostic_code": None,
            "diagnostic_detail": None,
            "remediation": [],
            "returncode": -15,
            "elapsed_seconds": 12.0,
            "tests": {"status": "missing", "total": 0, "passed": 0, "failed": 0, "skipped": 0},
            "details": {},
        },
    )

    assert run_unity_editor_tests.main() == 1
    preserved = json.loads((out_dir / "unity_runtime_verification.json").read_text(encoding="utf-8"))
    attempt = json.loads((out_dir / "unity_runtime_verification_attempt.json").read_text(encoding="utf-8"))

    assert preserved["overall_status"] == "pass"
    assert preserved["phase1_exit_criteria"][0]["status"] == "complete"
    assert attempt["overall_status"] == "fail"
