from __future__ import annotations

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
