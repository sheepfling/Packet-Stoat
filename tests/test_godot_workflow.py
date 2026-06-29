from __future__ import annotations

import argparse
import sys
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import build_godot_extension
import godot_env
import godot_workflow


def test_windows_wrapper_names() -> None:
    assert godot_env.wrapper_names("windows", "x86_64") == [
        "fastdis_gdextension.windows.template_debug.x86_64.dll",
        "fastdis_gdextension.windows.template_release.x86_64.dll",
    ]


def test_linux_arm64_wrapper_names() -> None:
    assert godot_env.wrapper_names("linux", "arm64") == [
        "libfastdis_gdextension.linux.template_debug.arm64.so",
        "libfastdis_gdextension.linux.template_release.arm64.so",
    ]


def test_windows_shared_library_names() -> None:
    assert godot_env.shared_library_names("windows") == ["fastdis.dll"]


def test_build_command_defaults() -> None:
    args = argparse.Namespace(skip_native_build=False)
    recorded: list[list[str]] = []

    def fake_run_step(cmd: list[str]) -> int:
        recorded.append(cmd)
        return 0

    original = godot_workflow.run_step
    godot_workflow.run_step = fake_run_step
    try:
        assert godot_workflow.command_build(args) == 0
    finally:
        godot_workflow.run_step = original

    assert recorded == [[sys.executable, "tools/build_godot_extension.py"]]


def test_bootstrap_command_runs_report() -> None:
    args = argparse.Namespace()
    recorded: list[list[str]] = []

    def fake_run_step(cmd: list[str]) -> int:
        recorded.append(cmd)
        return 0

    original = godot_workflow.run_step
    godot_workflow.run_step = fake_run_step
    try:
        assert godot_workflow.command_bootstrap(args) == 0
    finally:
        godot_workflow.run_step = original

    assert recorded == [[sys.executable, "tools/run_godot_report.py"]]


def test_full_command_delegates_to_bootstrap(monkeypatch) -> None:
    called: list[str] = []

    monkeypatch.setattr(godot_workflow, "command_bootstrap", lambda _args: called.append("bootstrap") or 0)

    assert godot_workflow.command_full() == 0
    assert called == ["bootstrap"]


def test_report_command_forwards_skip_flags() -> None:
    args = argparse.Namespace(skip_build=True, skip_verify=True, skip_demo=False, skip_missing_lib=True)
    recorded: list[list[str]] = []

    def fake_run_step(cmd: list[str]) -> int:
        recorded.append(cmd)
        return 0

    original = godot_workflow.run_step
    godot_workflow.run_step = fake_run_step
    try:
        assert godot_workflow.command_report(args) == 0
    finally:
        godot_workflow.run_step = original

    assert recorded == [[
        sys.executable,
        "tools/run_godot_report.py",
        "--skip-build",
        "--skip-verify",
        "--skip-missing-lib",
    ]]


def test_staged_state_tracks_manifest_freshness(monkeypatch, tmp_path: Path) -> None:
    demo_dir = tmp_path / "demo"
    verify_dir = tmp_path / "verify"
    demo_dir.mkdir()
    verify_dir.mkdir()
    monkeypatch.setattr(godot_workflow, "DEMO_BIN_DIR", demo_dir)
    monkeypatch.setattr(godot_workflow, "VERIFY_BIN_DIR", verify_dir)
    monkeypatch.setattr(
        godot_workflow.godot_env,
        "wrapper_names",
        lambda host_platform=None: ["libfastdis_gdextension.macos.template_debug.dylib"],
    )
    monkeypatch.setattr(
        godot_workflow.godot_env,
        "shared_library_names",
        lambda host_platform=None: ["libfastdis.dylib"],
    )
    monkeypatch.setattr(build_godot_extension, "manifest_is_current", lambda directory: directory == demo_dir)
    for directory in (demo_dir, verify_dir):
        (directory / "libfastdis_gdextension.macos.template_debug.dylib").write_text("x", encoding="utf-8")
        (directory / "libfastdis.dylib").write_text("x", encoding="utf-8")

    state = godot_workflow.staged_state()

    assert state["demo_wrapper_present"] is True
    assert state["verify_wrapper_present"] is True
    assert state["demo_manifest_current"] is True
    assert state["verify_manifest_current"] is False


def test_verify_command_forwards_flags() -> None:
    args = argparse.Namespace(dry_run=True, skip_build=True)
    recorded: list[list[str]] = []

    def fake_run_step(cmd: list[str]) -> int:
        recorded.append(cmd)
        return 0

    original = godot_workflow.run_step
    godot_workflow.run_step = fake_run_step
    try:
        assert godot_workflow.command_verify(args) == 0
    finally:
        godot_workflow.run_step = original

    assert recorded == [[sys.executable, "tools/run_godot_orientation_verification.py", "--dry-run", "--skip-build"]]


def test_demo_command_forwards_flags() -> None:
    args = argparse.Namespace(dry_run=True, skip_build=True)
    recorded: list[list[str]] = []

    def fake_run_step(cmd: list[str]) -> int:
        recorded.append(cmd)
        return 0

    original = godot_workflow.run_step
    godot_workflow.run_step = fake_run_step
    try:
        assert godot_workflow.command_demo(args) == 0
    finally:
        godot_workflow.run_step = original

    assert recorded == [[sys.executable, "tools/run_godot_demo_smoke.py", "--dry-run", "--skip-build"]]


def test_replay_matrix_command_forwards_flags() -> None:
    args = argparse.Namespace(skip_build=True, if_available=True)
    recorded: list[list[str]] = []

    def fake_run_step(cmd: list[str]) -> int:
        recorded.append(cmd)
        return 0

    original = godot_workflow.run_step
    godot_workflow.run_step = fake_run_step
    try:
        assert godot_workflow.command_replay_matrix(args) == 0
    finally:
        godot_workflow.run_step = original

    assert recorded == [[sys.executable, "tools/run_godot_replay_matrix.py", "--skip-build", "--if-available"]]


def test_missing_lib_command_forwards_flags() -> None:
    args = argparse.Namespace(dry_run=True, skip_build=True)
    recorded: list[list[str]] = []

    def fake_run_step(cmd: list[str]) -> int:
        recorded.append(cmd)
        return 0

    original = godot_workflow.run_step
    godot_workflow.run_step = fake_run_step
    try:
        assert godot_workflow.command_missing_lib(args) == 0
    finally:
        godot_workflow.run_step = original

    assert recorded == [[sys.executable, "tools/run_godot_missing_library_check.py", "--dry-run", "--skip-build"]]


def test_python_command_prefers_current_interpreter() -> None:
    assert godot_env.python_command() == [sys.executable]


def test_build_env_redirects_home_cache_and_tmp_into_godot_work_root() -> None:
    env = godot_env.build_env()
    work_root = godot_env.work_root()

    assert env["HOME"].startswith(str(work_root))
    assert env["XDG_CONFIG_HOME"].startswith(env["HOME"])
    assert env["XDG_DATA_HOME"].startswith(env["HOME"])
    assert env["XDG_CACHE_HOME"].startswith(env["HOME"])
    assert env["TMPDIR"].startswith(str(work_root))
    assert " " not in str(work_root)
    if sys.platform == "darwin":
        assert env["CFFIXED_USER_HOME"] == env["HOME"]


def test_godot_doctor_reports_permission_checks() -> None:
    payload = godot_workflow.doctor_payload()
    check_names = {check["name"] for check in payload["checks"]}

    assert "permission:work_root" in check_names
    assert "permission:demo_bin" in check_names
    assert "permission:verify_bin" in check_names
    assert any("replay matrix" in step for step in payload["next_steps"])


def test_windows_build_env_redirects_temp_and_appdata(monkeypatch) -> None:
    monkeypatch.setattr(godot_env.platform, "system", lambda: "Windows")
    monkeypatch.setenv("FASTDIS_GODOT_WORK_ROOT", r"C:\fastdis_godot")
    env = godot_env.build_env()

    assert env["HOME"].startswith(r"C:\fastdis_godot")
    assert env["USERPROFILE"].startswith(r"C:\fastdis_godot")
    assert env["APPDATA"].startswith(r"C:\fastdis_godot")
    assert env["LOCALAPPDATA"].startswith(r"C:\fastdis_godot")
    assert env["TEMP"].startswith(r"C:\fastdis_godot")
    assert env["TMP"].startswith(r"C:\fastdis_godot")


def test_windows_scons_candidates_include_current_python_scripts() -> None:
    original = godot_env.platform.system
    try:
        godot_env.platform.system = lambda: "Windows"
        candidates = godot_env.default_scons_candidates()
    finally:
        godot_env.platform.system = original

    executable_dir = Path(sys.executable).resolve().parent
    assert str(executable_dir / "scons.exe") in candidates
    assert str(executable_dir / "Scripts" / "scons.exe") in candidates


def test_windows_godot_candidates_include_public_engine_installs(monkeypatch, tmp_path: Path) -> None:
    public_root = tmp_path / "Public"
    install_dir = public_root / "Godot" / "engines" / "Godot_v4.7-stable_win64"
    install_dir.mkdir(parents=True)
    console = install_dir / "Godot_v4.7-stable_win64_console.exe"
    gui = install_dir / "Godot_v4.7-stable_win64.exe"
    console.write_text("console", encoding="utf-8")
    gui.write_text("gui", encoding="utf-8")
    monkeypatch.setattr(godot_env.platform, "system", lambda: "Windows")
    monkeypatch.setenv("PUBLIC", str(public_root))

    candidates = godot_env.default_godot_candidates()

    assert str(console) in candidates
    assert str(gui) in candidates
    assert candidates.index(str(console)) < candidates.index(str(gui))
    assert candidates.index(str(console)) < candidates.index("godot.exe")


def test_macos_godot_candidates_prefer_app_bundle_before_path(monkeypatch) -> None:
    monkeypatch.setattr(godot_env.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(godot_env.Path, "home", classmethod(lambda cls: Path("/Users/tester")))

    candidates = godot_env.default_godot_candidates()

    assert candidates.index("/Applications/Godot.app/Contents/MacOS/Godot") < candidates.index("godot")
    assert candidates.index("/Applications/Godot.app/Contents/MacOS/Godot") < candidates.index("godot4")
    assert candidates.index("/Applications/Godot.app/Contents/MacOS/Godot") < candidates.index("/usr/local/bin/godot")


def test_default_work_root_prefers_no_space_windows_localappdata(monkeypatch) -> None:
    monkeypatch.setattr(godot_env.platform, "system", lambda: "Windows")
    monkeypatch.setenv("LOCALAPPDATA", r"C:\Users\rick\AppData\Local")
    monkeypatch.delenv("FASTDIS_GODOT_WORK_ROOT", raising=False)

    work_root = godot_env._default_work_root()

    assert str(work_root).replace("\\", "/").endswith("/Local/fastdis_godot")
    assert " " not in str(work_root)


def test_prune_host_artifacts_removes_stale_fastdis_binaries(tmp_path: Path) -> None:
    good = tmp_path / "libfastdis.dylib"
    stale_shared = tmp_path / "libfastdis 2.dylib"
    stale_wrapper = tmp_path / "libfastdis_gdextension.macos.template_debug 2.dylib"
    unrelated = tmp_path / "README.txt"
    for path in (good, stale_shared, stale_wrapper, unrelated):
        path.write_text("x", encoding="utf-8")

    build_godot_extension.prune_host_artifacts(tmp_path, {"libfastdis.dylib"})

    assert good.exists()
    assert unrelated.exists()
    assert not stale_shared.exists()
    assert not stale_wrapper.exists()


def test_parse_wrapper_targets_normalizes_debug_and_release() -> None:
    assert build_godot_extension.parse_wrapper_targets("debug,release") == (
        "template_debug",
        "template_release",
    )


def test_parse_wrapper_targets_rejects_unknown_values() -> None:
    try:
        build_godot_extension.parse_wrapper_targets("editor")
    except SystemExit as exc:
        assert "Unsupported Godot wrapper target" in str(exc)
    else:
        raise AssertionError("expected SystemExit for unsupported wrapper target")


def test_native_link_dir_prefers_windows_import_library(monkeypatch, tmp_path: Path) -> None:
    release_dir = tmp_path / "Release"
    release_dir.mkdir()
    (release_dir / "fastdis.lib").write_text("x", encoding="utf-8")
    monkeypatch.setattr(build_godot_extension.godot_env, "host_platform_name", lambda: "windows")

    assert build_godot_extension.native_link_dir(tmp_path) == release_dir


def test_build_wrapper_requests_both_wrapper_variants(monkeypatch, tmp_path: Path) -> None:
    recorded: list[list[str]] = []
    gdextension_dir = tmp_path / "fastdis_gdextension"
    (gdextension_dir / "godot-cpp").mkdir(parents=True)
    (gdextension_dir / "godot-cpp" / "SConstruct").write_text("# stub\n", encoding="utf-8")
    (tmp_path / "libfastdis.dylib").write_text("x", encoding="utf-8")

    monkeypatch.setattr(build_godot_extension.godot_env, "resolve_scons", lambda: "scons")
    monkeypatch.setattr(build_godot_extension.godot_env, "build_env", lambda: {})
    monkeypatch.setattr(build_godot_extension.godot_env, "host_platform_name", lambda: "macos")
    monkeypatch.setattr(build_godot_extension.godot_env, "host_arch_name", lambda: "arm64")
    monkeypatch.setattr(build_godot_extension, "REAL_GDEXTENSION_DIR", gdextension_dir)
    monkeypatch.setattr(build_godot_extension, "bootstrap_godot_cpp", lambda: gdextension_dir / "godot-cpp")
    monkeypatch.setattr(build_godot_extension, "run", lambda cmd, cwd=None, env=None: recorded.append(cmd))
    monkeypatch.setattr(build_godot_extension, "prune_host_artifacts", lambda directory, allowed_names: None)

    build_godot_extension.build_wrapper(tmp_path, ("template_debug", "template_release"), 1)

    assert recorded == [
        [
            "scons",
            "platform=macos",
            "target=template_debug",
            "arch=arm64",
            "-j1",
            "-C",
            str(build_godot_extension.alias_gdextension_dir()),
        ],
        [
            "scons",
            "platform=macos",
            "target=template_release",
            "arch=arm64",
            "-j1",
            "-C",
            str(build_godot_extension.alias_gdextension_dir()),
        ],
    ]


def test_bootstrap_godot_cpp_uses_ref_candidates(monkeypatch, tmp_path: Path) -> None:
    gdextension_dir = tmp_path / "fastdis_gdextension"
    monkeypatch.setattr(build_godot_extension, "REAL_GDEXTENSION_DIR", gdextension_dir)
    monkeypatch.setattr(build_godot_extension.shutil, "which", lambda name: "git" if name == "git" else None)
    monkeypatch.setattr(build_godot_extension, "godot_cpp_ref_candidates", lambda: ["4.7", "master"])
    recorded: list[list[str]] = []
    ready_state = {"value": False}

    def fake_ready() -> bool:
        return ready_state["value"]

    def fake_run(cmd: list[str], cwd=None, env=None) -> None:
        recorded.append(cmd)
        checkout = gdextension_dir / "godot-cpp"
        checkout.mkdir(parents=True, exist_ok=True)
        (checkout / "SConstruct").write_text("# stub\n", encoding="utf-8")
        ready_state["value"] = True

    monkeypatch.setattr(build_godot_extension, "godot_cpp_is_ready", fake_ready)
    monkeypatch.setattr(build_godot_extension, "run", fake_run)

    assert build_godot_extension.bootstrap_godot_cpp() == gdextension_dir / "godot-cpp"
    assert recorded[0][1:4] == ["clone", "--depth", "1"]
    assert recorded[0][4] == "--branch"
    assert recorded[0][5] == "4.7"


def test_verify_staged_outputs_requires_full_wrapper_set(monkeypatch, tmp_path: Path) -> None:
    demo_dir = tmp_path / "demo"
    verify_dir = tmp_path / "verify"
    demo_dir.mkdir()
    verify_dir.mkdir()
    (demo_dir / "libfastdis_gdextension.macos.template_debug.dylib").write_text("x", encoding="utf-8")
    (verify_dir / "libfastdis_gdextension.macos.template_debug.dylib").write_text("x", encoding="utf-8")
    (demo_dir / "libfastdis.dylib").write_text("x", encoding="utf-8")
    (verify_dir / "libfastdis.dylib").write_text("x", encoding="utf-8")

    monkeypatch.setattr(build_godot_extension, "REAL_DEMO_BIN_DIR", demo_dir)
    monkeypatch.setattr(build_godot_extension, "REAL_VERIFY_BIN_DIR", verify_dir)
    monkeypatch.setattr(
        build_godot_extension.godot_env,
        "wrapper_names",
        lambda host_platform=None: [
            "libfastdis_gdextension.macos.template_debug.dylib",
            "libfastdis_gdextension.macos.template_release.dylib",
        ],
    )
    monkeypatch.setattr(
        build_godot_extension.godot_env,
        "shared_library_names",
        lambda host_platform=None: ["libfastdis.dylib"],
    )
    monkeypatch.setattr(build_godot_extension, "manifest_is_current", lambda directory: True)

    try:
        build_godot_extension.verify_staged_outputs()
    except SystemExit as exc:
        assert "template_release" in str(exc)
    else:
        raise AssertionError("expected SystemExit when a wrapper variant is missing")


def test_manifest_current_roundtrip(monkeypatch, tmp_path: Path) -> None:
    demo_dir = tmp_path / "demo"
    verify_dir = tmp_path / "verify"
    monkeypatch.setattr(build_godot_extension, "REAL_DEMO_BIN_DIR", demo_dir)
    monkeypatch.setattr(build_godot_extension, "REAL_VERIFY_BIN_DIR", verify_dir)

    written = build_godot_extension.write_build_manifest()

    assert len(written) == 2
    assert build_godot_extension.manifest_is_current(demo_dir) is True
    assert build_godot_extension.manifest_is_current(verify_dir) is True


def test_manifest_current_rejects_drift(monkeypatch, tmp_path: Path) -> None:
    demo_dir = tmp_path / "demo"
    verify_dir = tmp_path / "verify"
    monkeypatch.setattr(build_godot_extension, "REAL_DEMO_BIN_DIR", demo_dir)
    monkeypatch.setattr(build_godot_extension, "REAL_VERIFY_BIN_DIR", verify_dir)
    build_godot_extension.write_build_manifest()

    manifest = build_godot_extension.manifest_path(demo_dir)
    manifest.write_text('{"schema":"wrong"}\n', encoding="utf-8")

    assert build_godot_extension.manifest_is_current(demo_dir) is False


def test_verify_staged_outputs_requires_current_manifest(monkeypatch, tmp_path: Path) -> None:
    demo_dir = tmp_path / "demo"
    verify_dir = tmp_path / "verify"
    demo_dir.mkdir()
    verify_dir.mkdir()
    for directory in (demo_dir, verify_dir):
        (directory / "libfastdis_gdextension.macos.template_debug.dylib").write_text("x", encoding="utf-8")
        (directory / "libfastdis_gdextension.macos.template_release.dylib").write_text("x", encoding="utf-8")
        (directory / "libfastdis.dylib").write_text("x", encoding="utf-8")

    monkeypatch.setattr(build_godot_extension, "REAL_DEMO_BIN_DIR", demo_dir)
    monkeypatch.setattr(build_godot_extension, "REAL_VERIFY_BIN_DIR", verify_dir)
    monkeypatch.setattr(
        build_godot_extension.godot_env,
        "wrapper_names",
        lambda host_platform=None: [
            "libfastdis_gdextension.macos.template_debug.dylib",
            "libfastdis_gdextension.macos.template_release.dylib",
        ],
    )
    monkeypatch.setattr(
        build_godot_extension.godot_env,
        "shared_library_names",
        lambda host_platform=None: ["libfastdis.dylib"],
    )
    monkeypatch.setattr(build_godot_extension, "manifest_is_current", lambda directory: False)

    try:
        build_godot_extension.verify_staged_outputs()
    except SystemExit as exc:
        assert "stale or missing build manifest" in str(exc)
    else:
        raise AssertionError("expected SystemExit when the build manifest is stale")
