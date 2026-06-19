from __future__ import annotations

import json
import sys
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import run_godot_orientation_verification as godot_runner
import run_unreal_orientation_verification as unreal_runner
import sync_orientation_fixtures as sync_fixtures


def test_orientation_fixture_sync_roundtrip(tmp_path: Path) -> None:
    destination = tmp_path / "orientation_engine_cases.json"
    result = sync_fixtures.write_fixture_copy(destination)
    payload = json.loads(destination.read_text(encoding="utf-8"))
    checksum_path = destination.with_suffix(".json.sha256")

    assert payload["schema"] == "fastdis.orientation_engine_cases.v1"
    assert result["cases"] == len(payload["cases"])
    assert checksum_path.is_file()
    assert result["sha256"] in checksum_path.read_text(encoding="utf-8")


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
