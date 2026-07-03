from __future__ import annotations

from types import SimpleNamespace
import sys
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import unreal_env


def test_extract_version_from_lowercase_engine_name() -> None:
    assert unreal_env._extract_version_from_name("ue5.7.4-linux") == "5.7.4"


def test_describe_install_falls_back_to_resolved_engine_dir(monkeypatch, tmp_path: Path) -> None:
    engine_root = tmp_path / "ue5.7.4-linux"
    (engine_root / "Engine" / "Build").mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(unreal_env, "discover_installs", lambda: [])
    monkeypatch.setattr(unreal_env, "resolve_engine_dir", lambda version=None: engine_root)
    monkeypatch.setattr(
        unreal_env,
        "_install_from_root",
        lambda root, source, version_hint=None: unreal_env.UnrealInstall(
            version=version_hint or "5.7.4",
            install_root=str(root),
            engine_dir=str(root / "Engine"),
            editor_path=None,
            editor_cmd_path=None,
            editor_app_path=None,
            dotnet_path="/tmp/dotnet",
            uat_path="/tmp/RunUAT.sh",
            ubt_path="/tmp/UnrealBuildTool.dll",
            source=source,
            quirks=(),
        ),
    )

    payload = unreal_env.describe_install("5.7")

    assert payload is not None
    assert payload["version"] == "5.7"
    assert payload["source"] == "resolve"


def test_resolve_engine_dotnet_prefers_linux_x64_on_x86_host(monkeypatch, tmp_path: Path) -> None:
    dotnet_root = tmp_path / "Engine" / "Binaries" / "ThirdParty" / "DotNet" / "8.0.412"
    arm = dotnet_root / "linux-arm64" / "dotnet"
    x64 = dotnet_root / "linux-x64" / "dotnet"
    arm.parent.mkdir(parents=True, exist_ok=True)
    x64.parent.mkdir(parents=True, exist_ok=True)
    arm.write_text("arm\n", encoding="utf-8")
    x64.write_text("x64\n", encoding="utf-8")

    monkeypatch.setattr(unreal_env.platform, "system", lambda: "Linux")
    monkeypatch.setattr(unreal_env.platform, "machine", lambda: "x86_64")

    assert unreal_env.resolve_engine_dotnet(tmp_path) == x64.resolve()


def test_probe_work_root_isolated_by_project_and_version(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("FASTDIS_UNREAL_WORK_ROOT", str(tmp_path / "ue_work"))

    install_57 = unreal_env.UnrealInstall(
        version="5.7",
        install_root=str(tmp_path / "UE_5.7"),
        engine_dir=str(tmp_path / "UE_5.7" / "Engine"),
        editor_path=None,
        editor_cmd_path=None,
        editor_app_path=None,
        dotnet_path=None,
        uat_path=None,
        ubt_path=None,
        source="test",
        quirks=(),
    )
    install_58 = unreal_env.UnrealInstall(
        version="5.8",
        install_root=str(tmp_path / "UE_5.8"),
        engine_dir=str(tmp_path / "UE_5.8" / "Engine"),
        editor_path=None,
        editor_cmd_path=None,
        editor_app_path=None,
        dotnet_path=None,
        uat_path=None,
        ubt_path=None,
        source="test",
        quirks=(),
    )
    project_a = tmp_path / "A" / "RouteA.uproject"
    project_b = tmp_path / "B" / "RouteB.uproject"
    project_a.parent.mkdir(parents=True, exist_ok=True)
    project_b.parent.mkdir(parents=True, exist_ok=True)
    project_a.write_text("{}", encoding="utf-8")
    project_b.write_text("{}", encoding="utf-8")

    root_57 = unreal_env.probe_work_root(install_57, project_a)
    root_58 = unreal_env.probe_work_root(install_58, project_a)
    root_b = unreal_env.probe_work_root(install_58, project_b)

    assert root_57 != root_58
    assert root_58 != root_b
    assert "5_7" in str(root_57)
    assert "5_8" in str(root_58)


def test_probe_host_platform_support_uses_aliased_project_path(monkeypatch, tmp_path: Path) -> None:
    project = tmp_path / "projects" / "LongProject" / "Demo.uproject"
    project.parent.mkdir(parents=True, exist_ok=True)
    project.write_text("{}", encoding="utf-8")
    aliased = tmp_path / "alias" / "Demo.uproject"
    aliased.parent.mkdir(parents=True, exist_ok=True)
    aliased.write_text("{}", encoding="utf-8")

    install = unreal_env.UnrealInstall(
        version="5.8",
        install_root=str(tmp_path / "UE_5.8"),
        engine_dir=str(tmp_path / "UE_5.8" / "Engine"),
        editor_path=None,
        editor_cmd_path=None,
        editor_app_path=None,
        dotnet_path="/tmp/dotnet",
        uat_path="/tmp/RunUAT.sh",
        ubt_path="/tmp/UnrealBuildTool.dll",
        source="test",
        quirks=(),
    )

    recorded: dict[str, object] = {}

    monkeypatch.setattr(unreal_env, "alias_repo_path", lambda path, root=unreal_env.ROOT: aliased)
    monkeypatch.setattr(unreal_env, "clear_generated_state", lambda path: None)
    monkeypatch.setattr(unreal_env, "build_env_for_root", lambda root: {"FAKE": str(root)})

    def fake_run(command, **kwargs):
        recorded["command"] = command
        recorded["env"] = kwargs.get("env")
        return SimpleNamespace(returncode=0, stdout="ok")

    monkeypatch.setattr(unreal_env.subprocess, "run", fake_run)

    result = unreal_env.probe_host_platform_support(install, project, timeout_seconds=5.0)

    assert result["status"] == "ok"
    assert any(str(aliased) in part for part in recorded["command"])


def test_unreal_configured_roots_expand_path_list(monkeypatch, tmp_path: Path) -> None:
    first = tmp_path / "one"
    second = tmp_path / "two"
    monkeypatch.setenv("FASTDIS_UNREAL_ROOTS", f"{first}{unreal_env.os.pathsep}{second}")

    roots = unreal_env.configured_roots()

    assert roots == [first, second]


def test_unreal_discover_installs_honors_configured_roots(monkeypatch, tmp_path: Path) -> None:
    custom_root = tmp_path / "custom-unreal-root"
    install_root = custom_root / "UE_5.8"
    editor = install_root / "Engine" / "Binaries" / "Win64" / "UnrealEditor.exe"
    build = install_root / "Engine" / "Build"
    dotnet = install_root / "Engine" / "Binaries" / "ThirdParty" / "DotNet" / "8.0.0" / "win-x64" / "dotnet.exe"
    uat = install_root / "Engine" / "Build" / "BatchFiles" / "RunUAT.bat"
    ubt = install_root / "Engine" / "Binaries" / "DotNET" / "UnrealBuildTool" / "UnrealBuildTool.dll"
    editor.parent.mkdir(parents=True)
    build.mkdir(parents=True)
    dotnet.parent.mkdir(parents=True)
    uat.parent.mkdir(parents=True)
    ubt.parent.mkdir(parents=True)
    editor.write_text("", encoding="utf-8")
    dotnet.write_text("", encoding="utf-8")
    uat.write_text("", encoding="utf-8")
    ubt.write_text("", encoding="utf-8")
    monkeypatch.setattr(unreal_env.platform, "system", lambda: "Windows")
    monkeypatch.setenv("FASTDIS_UNREAL_ROOTS", str(custom_root))
    monkeypatch.delenv("FASTDIS_UNREAL_ENGINE_DIR", raising=False)
    monkeypatch.delenv("FASTDIS_UNREAL_EDITOR", raising=False)
    monkeypatch.delenv("FASTDIS_UNREAL_EDITOR_CMD", raising=False)
    monkeypatch.setattr(unreal_env, "_platform_roots", lambda: ([], ["UE_*"]))

    installs = unreal_env.discover_installs()

    assert installs
    assert installs[0].install_root == str(install_root.resolve())
    assert installs[0].source == f"scan:{custom_root}"


def test_unreal_version_sort_prefers_stable_over_preview(monkeypatch, tmp_path: Path) -> None:
    stable_root = tmp_path / "UE_5.8"
    preview_root = tmp_path / "UE_5.9-preview1"
    for root in (stable_root, preview_root):
        (root / "Engine" / "Build").mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(unreal_env.platform, "system", lambda: "Windows")
    monkeypatch.setattr(unreal_env, "_platform_roots", lambda: ([tmp_path], ["UE_*"]))

    installs = unreal_env.discover_installs()

    assert installs
    assert installs[0].install_root == str(stable_root.resolve())


def test_unreal_version_sort_handles_double_digit_minors(monkeypatch, tmp_path: Path) -> None:
    older_root = tmp_path / "UE_5.8"
    newer_root = tmp_path / "UE_5.10"
    for root in (older_root, newer_root):
        (root / "Engine" / "Build").mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(unreal_env.platform, "system", lambda: "Windows")
    monkeypatch.setattr(unreal_env, "_platform_roots", lambda: ([tmp_path], ["UE_*"]))

    installs = unreal_env.discover_installs()

    assert installs
    assert installs[0].install_root == str(newer_root.resolve())
