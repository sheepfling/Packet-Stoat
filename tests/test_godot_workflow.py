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
    assert godot_env.wrapper_names("windows") == [
        "fastdis_gdextension.windows.template_debug.x86_64.dll",
        "fastdis_gdextension.windows.template_release.x86_64.dll",
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

    assert env["HOME"].startswith(str(godot_env.DEFAULT_WORK_ROOT))
    assert env["XDG_CONFIG_HOME"].startswith(env["HOME"])
    assert env["XDG_DATA_HOME"].startswith(env["HOME"])
    assert env["XDG_CACHE_HOME"].startswith(env["HOME"])
    assert env["TMPDIR"].startswith(str(godot_env.DEFAULT_WORK_ROOT))
    assert str(godot_env.DEFAULT_WORK_ROOT) == "/tmp/fastdis_godot"
    assert " " not in str(godot_env.DEFAULT_WORK_ROOT)
    if sys.platform == "darwin":
        assert env["CFFIXED_USER_HOME"] == env["HOME"]


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


def test_build_wrapper_requests_both_wrapper_variants(monkeypatch, tmp_path: Path) -> None:
    recorded: list[list[str]] = []

    monkeypatch.setattr(build_godot_extension.godot_env, "resolve_scons", lambda: "scons")
    monkeypatch.setattr(build_godot_extension.godot_env, "build_env", lambda: {})
    monkeypatch.setattr(build_godot_extension.godot_env, "host_platform_name", lambda: "macos")
    monkeypatch.setattr(build_godot_extension.godot_env, "host_arch_name", lambda: "arm64")
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
            str(build_godot_extension.ALIAS_GDEXTENSION_DIR),
        ],
        [
            "scons",
            "platform=macos",
            "target=template_release",
            "arch=arm64",
            "-j1",
            "-C",
            str(build_godot_extension.ALIAS_GDEXTENSION_DIR),
        ],
    ]


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
