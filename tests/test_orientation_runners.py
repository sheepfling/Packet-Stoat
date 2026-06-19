from __future__ import annotations

import json
import sys
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import run_godot_demo_smoke as godot_demo_runner
import run_godot_orientation_verification as godot_runner
import run_unreal_demo_smoke as unreal_demo_runner
import run_unreal_orientation_verification as unreal_runner
import sync_orientation_fixtures as sync_fixtures


def test_orientation_fixture_sync_roundtrip(tmp_path: Path) -> None:
    destination = tmp_path / "orientation_engine_cases.json"
    result = sync_fixtures.write_fixture_copy(destination)
    payload = json.loads(destination.read_text(encoding="utf-8"))
    checksum_path = sync_fixtures.checksum_path_for(destination)

    assert payload["schema"] == "fastdis.orientation_engine_cases.v1"
    assert result["cases"] == len(payload["cases"])
    assert checksum_path.is_file()
    assert result["sha256"] in checksum_path.read_text(encoding="utf-8")
    assert sync_fixtures.verify_fixture_copy(destination)["sha256"] == result["sha256"]


def test_orientation_fixture_verify_rejects_payload_drift(tmp_path: Path) -> None:
    destination = tmp_path / "orientation_engine_cases.json"
    sync_fixtures.write_fixture_copy(destination)
    payload = json.loads(destination.read_text(encoding="utf-8"))
    payload["cases"][0]["name"] = "tampered_case"
    destination.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    try:
        sync_fixtures.verify_fixture_copy(destination)
    except ValueError as exc:
        assert "drifted from canonical source" in str(exc)
    else:
        raise AssertionError("expected verify_fixture_copy to reject payload drift")


def test_orientation_fixture_verify_rejects_checksum_drift(tmp_path: Path) -> None:
    destination = tmp_path / "orientation_engine_cases.json"
    sync_fixtures.write_fixture_copy(destination)
    checksum_path = sync_fixtures.checksum_path_for(destination)
    checksum_path.write_text("deadbeef  orientation_engine_cases.json\n", encoding="utf-8")

    try:
        sync_fixtures.verify_fixture_copy(destination)
    except ValueError as exc:
        assert "checksum mismatch" in str(exc)
    else:
        raise AssertionError("expected verify_fixture_copy to reject checksum drift")


def test_orientation_fixture_sync_declares_engine_destinations() -> None:
    assert set(sync_fixtures.DESTINATIONS) == {"godot", "unreal", "unity"}
    assert "Assets/StreamingAssets/orientation_engine_cases.json" in str(sync_fixtures.DESTINATIONS["unity"])


def test_unity_orientation_scaffold_files_exist() -> None:
    unity_root = sync_fixtures.ROOT / "examples" / "unity" / "FastDisOrientationVerification"
    assert (unity_root / "README.md").is_file()
    assert (unity_root / "Assets" / "Scenes" / "OrientationVerification.unity").is_file()
    assert (unity_root / "Assets" / "Scripts" / "FastDisOrientationVerifier.cs").is_file()
    assert sync_fixtures.DESTINATIONS["unity"].is_file()
    assert sync_fixtures.DESTINATIONS["unity"].with_suffix(".json.sha256").is_file()


def test_godot_orientation_runner_builds_headless_command() -> None:
    command = godot_runner.build_command("godot")
    assert command[0] == "godot"
    assert "--headless" in command
    assert "--path" in command
    assert "--script" in command
    assert command[-1].endswith("run_orientation_tests.gd")
    assert "fastdis_orientation_verification" in command[command.index("--path") + 1]


def test_unreal_orientation_runner_builds_automation_command() -> None:
    command = unreal_runner.build_command("UnrealEditor-Cmd")
    assert command[0] == "UnrealEditor-Cmd"
    assert command[1].endswith("FastDisOrientationVerification.uproject")
    assert any("Automation RunTests FastDis.Orientation; Quit" in item for item in command)
    assert "-unattended" in command


def test_unreal_demo_runner_builds_automation_command() -> None:
    command = unreal_demo_runner.build_command("UnrealEditor-Cmd")
    assert command[0] == "UnrealEditor-Cmd"
    assert command[1].endswith("FastDisOrientationVerification.uproject")
    assert any("Automation RunTests FastDis.Demo; Quit" in item for item in command)
    assert "-unattended" in command


def test_godot_demo_runner_builds_headless_command() -> None:
    command = godot_demo_runner.build_command("godot")
    assert command[0] == "godot"
    assert "--headless" in command
    assert "--path" in command
    assert "--script" in command
    assert command[-1].endswith("run_demo_smoke.gd")
    assert "fastdis_demo" in command[command.index("--path") + 1]


def test_godot_orientation_runner_detects_complete_staged_build(tmp_path: Path) -> None:
    addon_dir = tmp_path / "addons"
    addon_dir.mkdir()
    for name in ("libfastdis_gdextension.macos.template_debug.dylib", "libfastdis_gdextension.macos.template_release.dylib"):
        (addon_dir / name).write_text("x", encoding="utf-8")
    (addon_dir / "libfastdis.dylib").write_text("x", encoding="utf-8")

    original_bin_dir = godot_runner.ADDON_BIN_DIR
    original_manifest_current = godot_runner.build_godot_extension.manifest_is_current
    original_wrapper_names = godot_runner.godot_env.wrapper_names
    original_shared_names = godot_runner.godot_env.shared_library_names
    godot_runner.ADDON_BIN_DIR = addon_dir
    godot_runner.build_godot_extension.manifest_is_current = lambda directory: True
    godot_runner.godot_env.wrapper_names = lambda host_platform=None: [
        "libfastdis_gdextension.macos.template_debug.dylib",
        "libfastdis_gdextension.macos.template_release.dylib",
    ]
    godot_runner.godot_env.shared_library_names = lambda host_platform=None: ["libfastdis.dylib"]
    try:
        assert godot_runner.staged_build_complete() is True
    finally:
        godot_runner.ADDON_BIN_DIR = original_bin_dir
        godot_runner.build_godot_extension.manifest_is_current = original_manifest_current
        godot_runner.godot_env.wrapper_names = original_wrapper_names
        godot_runner.godot_env.shared_library_names = original_shared_names


def test_godot_demo_runner_detects_incomplete_staged_build(tmp_path: Path) -> None:
    addon_dir = tmp_path / "addons"
    addon_dir.mkdir()
    (addon_dir / "libfastdis_gdextension.macos.template_debug.dylib").write_text("x", encoding="utf-8")
    (addon_dir / "libfastdis.dylib").write_text("x", encoding="utf-8")

    original_bin_dir = godot_demo_runner.ADDON_BIN_DIR
    original_manifest_current = godot_demo_runner.build_godot_extension.manifest_is_current
    original_wrapper_names = godot_demo_runner.godot_env.wrapper_names
    original_shared_names = godot_demo_runner.godot_env.shared_library_names
    godot_demo_runner.ADDON_BIN_DIR = addon_dir
    godot_demo_runner.build_godot_extension.manifest_is_current = lambda directory: True
    godot_demo_runner.godot_env.wrapper_names = lambda host_platform=None: [
        "libfastdis_gdextension.macos.template_debug.dylib",
        "libfastdis_gdextension.macos.template_release.dylib",
    ]
    godot_demo_runner.godot_env.shared_library_names = lambda host_platform=None: ["libfastdis.dylib"]
    try:
        assert godot_demo_runner.staged_build_complete() is False
    finally:
        godot_demo_runner.ADDON_BIN_DIR = original_bin_dir
        godot_demo_runner.build_godot_extension.manifest_is_current = original_manifest_current
        godot_demo_runner.godot_env.wrapper_names = original_wrapper_names
        godot_demo_runner.godot_env.shared_library_names = original_shared_names


def test_godot_orientation_runner_detects_stale_manifest(tmp_path: Path) -> None:
    addon_dir = tmp_path / "addons"
    addon_dir.mkdir()
    for name in ("libfastdis_gdextension.macos.template_debug.dylib", "libfastdis_gdextension.macos.template_release.dylib"):
        (addon_dir / name).write_text("x", encoding="utf-8")
    (addon_dir / "libfastdis.dylib").write_text("x", encoding="utf-8")

    original_bin_dir = godot_runner.ADDON_BIN_DIR
    original_manifest_current = godot_runner.build_godot_extension.manifest_is_current
    original_wrapper_names = godot_runner.godot_env.wrapper_names
    original_shared_names = godot_runner.godot_env.shared_library_names
    godot_runner.ADDON_BIN_DIR = addon_dir
    godot_runner.build_godot_extension.manifest_is_current = lambda directory: False
    godot_runner.godot_env.wrapper_names = lambda host_platform=None: [
        "libfastdis_gdextension.macos.template_debug.dylib",
        "libfastdis_gdextension.macos.template_release.dylib",
    ]
    godot_runner.godot_env.shared_library_names = lambda host_platform=None: ["libfastdis.dylib"]
    try:
        assert godot_runner.staged_build_complete() is False
    finally:
        godot_runner.ADDON_BIN_DIR = original_bin_dir
        godot_runner.build_godot_extension.manifest_is_current = original_manifest_current
        godot_runner.godot_env.wrapper_names = original_wrapper_names
        godot_runner.godot_env.shared_library_names = original_shared_names
