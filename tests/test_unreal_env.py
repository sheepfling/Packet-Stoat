from __future__ import annotations

import json
import sys
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import unreal_env


def test_classify_probe_failure_detects_sandbox_write_denied() -> None:
    output = (
        "Access to the path '/Users/rick/Library/Logs/Unreal Engine/LocalBuildLogs/Log.txt' is denied.\n"
    )
    assert unreal_env.classify_probe_failure(output) == "sandbox-home-write-denied"


def test_classify_probe_failure_detects_mac_platform_unavailable() -> None:
    output = "Platform Mac is not a valid platform to build."
    assert unreal_env.classify_probe_failure(output) == "host-mac-platform-unavailable"


def test_probe_failure_note_describes_sandbox_case() -> None:
    note = unreal_env.probe_failure_note("sandbox-home-write-denied")
    assert note is not None
    assert "sandbox" in note
    assert "~/Library" in note


def test_build_env_redirects_home_into_unreal_work_root() -> None:
    env = unreal_env.build_env()

    assert env["HOME"].startswith(str(unreal_env.DEFAULT_WORK_ROOT))
    assert env["XDG_CONFIG_HOME"].startswith(env["HOME"])
    assert env["XDG_DATA_HOME"].startswith(env["HOME"])
    assert env["XDG_CACHE_HOME"].startswith(env["HOME"])
    assert env["TMPDIR"].startswith(str(unreal_env.DEFAULT_WORK_ROOT))
    assert env["UE-LocalDataCachePath"] == str(unreal_env.DEFAULT_WORK_ROOT / "ddc")
    assert env["UE-SharedDataCachePath"] == str(unreal_env.DEFAULT_WORK_ROOT / "sddc")
    assert " " not in env["UE-LocalDataCachePath"]
    assert " " not in env["UE-SharedDataCachePath"]
    if sys.platform == "darwin":
        assert env["CFFIXED_USER_HOME"] == env["HOME"]


def test_clear_generated_state_removes_project_and_plugin_outputs(tmp_path: Path) -> None:
    project_dir = tmp_path / "Project"
    project_dir.mkdir()
    project_path = project_dir / "Project.uproject"
    project_path.write_text("{}\n", encoding="utf-8")
    project_binaries = project_dir / "Binaries"
    project_intermediate = project_dir / "Intermediate"
    plugin_binaries = project_dir / "Plugins" / "FastDis" / "Binaries"
    plugin_intermediate = project_dir / "Plugins" / "FastDis" / "Intermediate"
    for directory in (project_binaries, project_intermediate, plugin_binaries, plugin_intermediate):
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "marker.txt").write_text("x", encoding="utf-8")

    unreal_env.clear_generated_state(project_path)

    for directory in (project_binaries, project_intermediate, plugin_binaries, plugin_intermediate):
        assert not directory.exists()


def test_probe_clears_generated_state_before_returning_cached_result(monkeypatch, tmp_path: Path) -> None:
    project_dir = tmp_path / "Project"
    project_dir.mkdir()
    project_path = project_dir / "Project.uproject"
    project_path.write_text("{}\n", encoding="utf-8")

    install = unreal_env.UnrealInstall(
        version="5.7",
        install_root="/EngineRoot",
        engine_dir="/EngineRoot/Engine",
        editor_path="/EngineRoot/Engine/Binaries/Mac/UnrealEditor",
        editor_cmd_path="/EngineRoot/Engine/Binaries/Mac/UnrealEditor-Cmd",
        editor_app_path=None,
        dotnet_path="/EngineRoot/dotnet",
        uat_path="/EngineRoot/RunUAT.sh",
        ubt_path="/EngineRoot/UnrealBuildTool.dll",
        source="test",
        quirks=(),
    )

    command = [
        install.dotnet_path,
        install.ubt_path,
        project_path.stem + "Editor",
        unreal_env.platform_dir_name(),
        "Development",
        f"-project={project_path}",
        "-NoAction",
        "-NoHotReloadFromIDE",
        "-WaitMutex",
    ]
    cache_key = unreal_env.hashlib.sha256("\0".join(command).encode("utf-8")).hexdigest()
    cache_dir = tmp_path / "probe_cache"
    cache_dir.mkdir()
    cache_path = cache_dir / f"{cache_key}.json"
    cached_result = {
        "status": "ok",
        "failure_kind": None,
        "detail": "cached",
        "command": command,
        "output": "",
    }
    cache_path.write_text(json.dumps(cached_result), encoding="utf-8")

    generated_dir = project_dir / "Intermediate"
    generated_dir.mkdir()
    (generated_dir / "marker.txt").write_text("x", encoding="utf-8")

    monkeypatch.setattr(unreal_env, "DEFAULT_WORK_ROOT", tmp_path)
    result = unreal_env.probe_host_platform_support(install, project_path)

    assert result["detail"] == "cached"
    assert not generated_dir.exists()


def test_alias_repo_path_uses_no_space_root_when_workspace_has_spaces(monkeypatch, tmp_path: Path) -> None:
    root = tmp_path / "repo with spaces"
    root.mkdir()
    project_path = root / "examples" / "unreal" / "FastDisOrientationVerification" / "Project.uproject"
    project_path.parent.mkdir(parents=True)
    project_path.write_text("{}\n", encoding="utf-8")

    work_root = tmp_path / "scratch"
    monkeypatch.setattr(unreal_env, "DEFAULT_WORK_ROOT", work_root)

    alias = unreal_env.alias_repo_path(project_path, root)

    assert " " not in str(alias)
    assert alias.name == "Project.uproject"
