from __future__ import annotations

import subprocess
import sys
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import build_unreal_plugin


def test_ensure_build_rules_compatibility_builds_marketplace_rules_when_missing(monkeypatch, tmp_path: Path) -> None:
    engine_root = tmp_path / "UE_5.7"
    actual_rules_dir = engine_root / "Engine" / "Intermediate" / "Build" / "BuildRules"
    rules_project = engine_root / "Engine" / "Intermediate" / "Build" / "BuildRulesProjects" / "MarketplaceRules" / "MarketplaceRules.csproj"
    actual_rules_dir.mkdir(parents=True)
    rules_project.parent.mkdir(parents=True, exist_ok=True)
    rules_project.write_text("<Project />\n", encoding="utf-8")
    dotnet = engine_root / "Engine" / "Binaries" / "ThirdParty" / "DotNet" / "8.0" / "dotnet"
    dotnet.parent.mkdir(parents=True, exist_ok=True)
    dotnet.write_text("", encoding="utf-8")

    recorded: list[list[str]] = []

    def fake_run(cmd: list[str], *, cwd: Path | None = None) -> None:
        recorded.append(cmd)
        (actual_rules_dir / "MarketplaceRules.dll").write_text("dll", encoding="utf-8")

    monkeypatch.setattr(build_unreal_plugin, "run", fake_run)
    monkeypatch.setattr(build_unreal_plugin, "resolve_engine_dotnet", lambda engine_dir: dotnet)

    build_unreal_plugin.ensure_build_rules_compatibility(engine_root)

    assert recorded == [[
        str(dotnet),
        "build",
        str(rules_project),
        "-c",
        "Development",
        "-o",
        str(actual_rules_dir),
    ]]
    expected_rules_dir = engine_root / "Engine" / "Source" / "Epic" / "UnrealEngine" / "Intermediate" / "Build" / "BuildRules"
    assert expected_rules_dir.exists()


def test_ensure_build_rules_compatibility_skips_build_when_marketplace_rules_present(monkeypatch, tmp_path: Path) -> None:
    engine_root = tmp_path / "UE_5.7"
    actual_rules_dir = engine_root / "Engine" / "Intermediate" / "Build" / "BuildRules"
    actual_rules_dir.mkdir(parents=True)
    (actual_rules_dir / "MarketplaceRules.dll").write_text("dll", encoding="utf-8")

    called = False

    def fake_run(cmd: list[str], *, cwd: Path | None = None) -> None:
        nonlocal called
        called = True

    monkeypatch.setattr(build_unreal_plugin, "run", fake_run)

    build_unreal_plugin.ensure_build_rules_compatibility(engine_root)

    assert called is False
    expected_rules_dir = engine_root / "Engine" / "Source" / "Epic" / "UnrealEngine" / "Intermediate" / "Build" / "BuildRules"
    assert expected_rules_dir.exists()


def test_run_retries_once_on_unrealbuildtool_mutex_conflict(monkeypatch) -> None:
    outputs = [
        subprocess.CompletedProcess(
            args=["uat"],
            returncode=10,
            stdout="A conflicting instance of Global\\UnrealBuildTool_Mutex_deadbeef is already running.\n",
        ),
        subprocess.CompletedProcess(args=["uat"], returncode=0, stdout="ok\n"),
    ]
    recorded_sleeps: list[int] = []

    monkeypatch.setattr(build_unreal_plugin.subprocess, "run", lambda *args, **kwargs: outputs.pop(0))
    monkeypatch.setattr(build_unreal_plugin.time, "sleep", lambda seconds: recorded_sleeps.append(seconds))

    build_unreal_plugin.run(["uat"])

    assert recorded_sleeps == [5]
