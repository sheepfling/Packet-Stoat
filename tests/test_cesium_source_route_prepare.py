from __future__ import annotations

from pathlib import Path
import sys


TOOLS_DIR = Path(__file__).resolve().parents[1] / "extensions" / "cesium" / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import prepare_cesium_source_route as prep


def test_default_repo_specs_use_fork_remotes() -> None:
    specs = {spec.key: spec for spec in prep.default_repo_specs()}

    assert specs["unreal_plugin"].remote_url == "https://github.com/sheepfling/cesium-unreal.git"
    assert specs["unity_plugin"].remote_url == "https://github.com/sheepfling/cesium-unity.git"
    assert specs["godot_plugin"].remote_url == "https://github.com/sheepfling/3D-Tiles-For-Godot.git"
    assert specs["godot_plugin"].target_branch == "master"


def test_default_repo_specs_honor_branch_overrides(monkeypatch) -> None:
    monkeypatch.setenv("FASTDIS_CESIUM_UNREAL_BRANCH", "fork/unreal-58-macos-silicon-fixes")
    monkeypatch.setenv("FASTDIS_CESIUM_UNREAL_REMOTE", "https://github.com/sheepfling/cesium-unreal.git")

    specs = {spec.key: spec for spec in prep.default_repo_specs()}

    assert specs["unreal_plugin"].target_branch == "fork/unreal-58-macos-silicon-fixes"
    assert specs["unreal_plugin"].remote_url == "https://github.com/sheepfling/cesium-unreal.git"


def test_prepare_repo_clones_missing_checkout_from_fork_remote(monkeypatch, tmp_path: Path) -> None:
    spec = prep.RepoSpec(
        key="unreal_plugin",
        label="Cesium Unreal plugin",
        path=tmp_path / "cesium-unreal",
        remote_url="https://github.com/sheepfling/cesium-unreal.git",
        target_branch="main",
        submodule_url_overrides=(("extern/cesium-native", "https://github.com/CesiumGS/cesium-native.git"),),
        update_submodules=True,
        official=True,
    )

    inspect_calls: list[dict[str, object]] = [
        {
            "exists": False,
            "is_git_checkout": False,
            "resolved_target_branch": None,
            "target_commit": None,
            "current_branch": None,
            "head_commit": None,
            "dirty": None,
            "has_gitmodules": False,
            "remote_url": None,
        },
        {
            "exists": True,
            "is_git_checkout": True,
            "resolved_target_branch": "main",
            "target_commit": "abc123",
            "current_branch": "main",
            "head_commit": "abc123",
            "dirty": False,
            "has_gitmodules": True,
            "remote_url": spec.remote_url,
        },
        {
            "exists": True,
            "is_git_checkout": True,
            "resolved_target_branch": "main",
            "target_commit": "abc123",
            "current_branch": "main",
            "head_commit": "abc123",
            "dirty": False,
            "has_gitmodules": True,
            "remote_url": spec.remote_url,
        },
        {
            "exists": True,
            "is_git_checkout": True,
            "resolved_target_branch": "main",
            "target_commit": "abc123",
            "current_branch": "main",
            "head_commit": "abc123",
            "dirty": False,
            "has_gitmodules": True,
            "remote_url": spec.remote_url,
        },
    ]
    commands: list[list[str]] = []

    def fake_inspect_repo(_spec: prep.RepoSpec) -> dict[str, object]:
        return inspect_calls.pop(0)

    class Completed:
        def __init__(self, returncode: int = 0, stdout: str = "") -> None:
            self.returncode = returncode
            self.stdout = stdout

    def fake_run(cmd, cwd=None, stdout=None, stderr=None, text=None, check=False):
        commands.append([str(part) for part in cmd])
        return Completed(0, "")

    monkeypatch.setattr(prep, "inspect_repo", fake_inspect_repo)
    monkeypatch.setattr(prep.subprocess, "run", fake_run)

    report = prep.prepare_repo(spec, fetch=True, allow_dirty=False, update_submodules=True)

    assert report["status"] == "prepared"
    assert commands[0][:4] == ["git", "-c", "http.sslVerify=false", "clone"]
    assert commands[0][4:8] == ["--branch", "main", "--single-branch", spec.remote_url]
    assert commands[1][5:8] == ["fetch", "--all", "--prune"]
    assert commands[2][5:10] == [
        "config",
        "--local",
        "submodule.extern/cesium-native.url",
        "https://github.com/CesiumGS/cesium-native.git",
    ]
    assert commands[3][5:8] == ["submodule", "update", "--init"]
