from __future__ import annotations

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import create_unreal_fab_demo_assets


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_unreal_fab_asset_generator_scripts_exist_and_target_plugin_content() -> None:
    runner = read(ROOT / "tools" / "create_unreal_fab_demo_assets.py")
    script = read(ROOT / "tools" / "unreal" / "create_fab_demo_assets.py")

    assert "ExecutePythonScript" in runner
    assert "ensure_runtime_plugin" in runner
    assert "ensure_harness_built" in runner
    assert "CreateFastDisFabDemoAssets.log" in runner
    assert "GENERATED_DEMO_MAP" in runner
    assert "GENERATED_MAPPING_ASSET" in runner
    assert "GENERATED_DEMO_CONTROLLER_BP" in runner
    assert "GENERATED_STATUS_WIDGET_BP" in runner
    assert "unreal_python_log_succeeded" in runner
    assert "/FastDis/Examples/FastDis_Demo" in script
    assert "/FastDis/Examples/DA_FastDisEntityMappings" in script
    assert "BP_FastDisDemoController" in script
    assert "WBP_FastDisRuntimeStatus" in script
    assert "/Script/FastDisUnreal.FastDisDemoController" in script
    assert "/Script/FastDisUnreal.FastDisRuntimeStatusWidget" in script
    assert "create_example_entity_mapping_asset" in script
    assert "BlueprintFactory" in script
    assert "WidgetBlueprintFactory" in script
    assert "spawn_actor_from_class" in script
    assert "save_current_level" in script
    assert "FASTDIS_FAB_ASSET_GEN" in script


def test_unreal_fab_asset_generator_dry_run_command_shape() -> None:
    completed = subprocess.run(
        [
            "python3",
            "tools/create_unreal_fab_demo_assets.py",
            "--dry-run",
            "--engine-version",
            "5.8",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=True,
    )

    output = completed.stdout
    assert "FastDisOrientationVerification.uproject" in output
    assert "-ExecutePythonScript=" in output
    assert "tools/unreal/create_fab_demo_assets.py" in output
    assert "-NullRHI" in output
    assert "CreateFastDisFabDemoAssets.log" in output


def test_unreal_fab_asset_generator_detects_python_errors(tmp_path: Path) -> None:
    log_path = tmp_path / "unreal.log"
    log_path.write_text(
        "LogPython: Error: Traceback\nLogEditorPythonExecuter: Error: Python script executed with errors\n",
        encoding="utf-8",
    )

    assert create_unreal_fab_demo_assets.unreal_python_log_failed(log_path) is True


def test_unreal_fab_asset_generator_detects_success_marker(tmp_path: Path) -> None:
    log_path = tmp_path / "unreal.log"
    log_path.write_text("LogPython: FASTDIS_FAB_ASSET_GEN complete\n", encoding="utf-8")

    assert create_unreal_fab_demo_assets.unreal_python_log_succeeded(log_path) is True
