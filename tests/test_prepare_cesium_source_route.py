from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run(cmd: list[str], cwd: Path) -> None:
    subprocess.run(cmd, cwd=cwd, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)


def _make_remote_and_clone(tmp_path: Path, *, target_branch: str) -> Path:
    source = tmp_path / "source"
    remote = tmp_path / "remote.git"
    checkout = tmp_path / "checkout"
    source.mkdir()
    _run(["git", "init", "-b", "main"], source)
    _run(["git", "config", "user.email", "test@example.com"], source)
    _run(["git", "config", "user.name", "Test User"], source)
    (source / "README.md").write_text("main\n", encoding="utf-8")
    _run(["git", "add", "README.md"], source)
    _run(["git", "commit", "-m", "main"], source)
    _run(["git", "branch", target_branch], source)
    _run(["git", "checkout", target_branch], source)
    (source / "README.md").write_text(f"{target_branch}\n", encoding="utf-8")
    _run(["git", "commit", "-am", target_branch], source)
    _run(["git", "init", "--bare", str(remote)], tmp_path)
    _run(["git", "remote", "add", "origin", str(remote)], source)
    _run(["git", "push", "--all", "origin"], source)
    _run(["git", "clone", str(remote), str(checkout)], tmp_path)
    return checkout


def test_default_repo_specs_encode_public_branch_policy() -> None:
    module = _load_module("prepare_cesium_source_route", ROOT / "extensions" / "cesium" / "tools" / "prepare_cesium_source_route.py")

    specs = {spec.key: spec for spec in module.default_repo_specs()}

    assert specs["unreal_plugin"].target_branch == "main"
    assert specs["unity_plugin"].target_branch == "main"
    assert specs["unreal_samples"].target_branch == "main"
    assert specs["godot_plugin"].target_branch == "main"
    assert specs["godot_plugin"].fallback_branches == ("master",)
    assert specs["godot_plugin"].official is False


def test_prepare_repo_switches_checkout_to_target_branch(tmp_path: Path) -> None:
    module = _load_module("prepare_cesium_source_route", ROOT / "extensions" / "cesium" / "tools" / "prepare_cesium_source_route.py")
    checkout = _make_remote_and_clone(tmp_path, target_branch="ue5")
    spec = module.RepoSpec(
        key="unreal_plugin",
        label="Cesium Unreal plugin",
        path=checkout,
        target_branch="ue5",
    )

    result = module.prepare_repo(spec, fetch=False, allow_dirty=False, update_submodules=False)

    assert result["status"] == "prepared"
    assert result["after"]["current_branch"] == "ue5"
    assert result["after"]["head_commit"] == result["after"]["target_commit"]


def test_prepare_repo_blocks_dirty_checkout_when_not_allowed(tmp_path: Path) -> None:
    module = _load_module("prepare_cesium_source_route", ROOT / "extensions" / "cesium" / "tools" / "prepare_cesium_source_route.py")
    checkout = _make_remote_and_clone(tmp_path, target_branch="ue5")
    spec = module.RepoSpec(
        key="unreal_plugin",
        label="Cesium Unreal plugin",
        path=checkout,
        target_branch="ue5",
    )
    (checkout / "README.md").write_text("dirty\n", encoding="utf-8")

    result = module.prepare_repo(spec, fetch=False, allow_dirty=False, update_submodules=False)

    assert result["status"] == "blocked-dirty"
    assert "checkout has local modifications" in result["blockers"]


def test_prepare_repo_uses_fallback_branch_when_primary_missing(tmp_path: Path) -> None:
    module = _load_module("prepare_cesium_source_route", ROOT / "extensions" / "cesium" / "tools" / "prepare_cesium_source_route.py")
    checkout = _make_remote_and_clone(tmp_path, target_branch="master")
    spec = module.RepoSpec(
        key="godot_plugin",
        label="3D Tiles for Godot",
        path=checkout,
        target_branch="release-main",
        fallback_branches=("master",),
    )

    result = module.prepare_repo(spec, fetch=False, allow_dirty=False, update_submodules=False)

    assert result["status"] == "prepared"
    assert result["after"]["resolved_target_branch"] == "master"
    assert result["after"]["current_branch"] == "master"
