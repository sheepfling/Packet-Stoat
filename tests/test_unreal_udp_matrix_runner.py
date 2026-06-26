from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = ROOT / "tools"
sys.path.insert(0, str(TOOLS_DIR))


def _fake_install(module):
    return module.unreal_env.UnrealInstall(
        version="5.8",
        install_root="/Users/Shared/Epic Games/UE_5.8",
        engine_dir="/Users/Shared/Epic Games/UE_5.8/Engine",
        editor_path="/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor",
        editor_cmd_path="/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor-Cmd",
        editor_app_path=None,
        dotnet_path="/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/ThirdParty/DotNet/dotnet",
        uat_path="/Users/Shared/Epic Games/UE_5.8/Engine/Build/BatchFiles/RunUAT.sh",
        ubt_path="/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/DotNET/UnrealBuildTool/UnrealBuildTool.dll",
        source="test",
        quirks=(),
    )


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_failure_payload_marks_engine_intermediate_write_denied_as_pending() -> None:
    module = _load_module("run_unreal_udp_smoke", ROOT / "tools" / "run_unreal_udp_smoke.py")
    args = module.argparse.Namespace(scenario="entity_state_1x10hz")

    payload = module._failure_payload(
        args=args,
        recv_command=["UnrealEditor-Cmd"],
        recv_output="UnauthorizedAccessException: Access to the path '/Users/Shared/Epic Games/UE_5.8/Engine/Intermediate/Build/Mac/x64/UnrealEditor' is denied.",
        recv_returncode=6,
        failure_kind="engine-intermediate-write-denied",
        errors=["Unreal harness setup failed with exit status 6"],
    )

    assert payload["status"] == "pending"
    assert payload["failure_kind"] == "engine-intermediate-write-denied"
    assert any("managed run denied Unreal writes" in error for error in payload["errors"])
    assert payload["scenario"] == "entity_state_1x10hz"
    assert payload["scenario_suite"] == module.CORE_SCENARIO_SUITE


def test_setup_failure_is_emitted_as_json(monkeypatch, capsys) -> None:
    module = _load_module("run_unreal_udp_smoke", ROOT / "tools" / "run_unreal_udp_smoke.py")
    monkeypatch.setattr(module.load_local_env, "load", lambda: None)
    monkeypatch.setattr(
        module,
        "parse_args",
        lambda: module.argparse.Namespace(
            unreal=None,
            engine_version="5.8",
            count=24,
            entity_count=1,
            rate_hz=10.0,
            scenario="entity_state_1x10hz",
            timeout=30.0,
            dry_run=False,
        ),
    )
    monkeypatch.setattr(module, "clear_harness_log", lambda: None)
    monkeypatch.setattr(module, "resolve_unreal", lambda explicit, engine_version: "/Engines/UE_5.8/UnrealEditor-Cmd")
    monkeypatch.setattr(module, "build_command", lambda unreal_binary: [unreal_binary, "Project.uproject"])
    monkeypatch.setattr(module, "_discover_install", lambda engine_version: _fake_install(module))
    monkeypatch.setattr(
        module.unreal_env,
        "probe_host_platform_support",
        lambda install, project_path: {"failure_kind": None},
    )
    monkeypatch.setattr(module.unreal_env, "path_writable", lambda path: (True, str(path)))

    def fail_setup(engine_version):
        raise subprocess.CalledProcessError(
            6,
            ["dotnet", "UnrealBuildTool.dll"],
            output=(
                "UnauthorizedAccessException: Access to the path "
                "'/Users/Shared/Epic Games/UE_5.8/Engine/Intermediate/Build/Mac/x64/UnrealEditor' is denied."
            ),
        )

    monkeypatch.setattr(module, "ensure_runtime_plugin", fail_setup)
    monkeypatch.setattr(module, "ensure_harness_built", lambda engine_version: None)

    rc = module.main()

    assert rc == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "pending"
    assert payload["failure_kind"] == "engine-intermediate-write-denied"
    assert payload["recv_returncode"] == 6


def test_host_probe_short_circuits_as_pending(monkeypatch, capsys) -> None:
    module = _load_module("run_unreal_udp_smoke", ROOT / "tools" / "run_unreal_udp_smoke.py")
    monkeypatch.setattr(module.load_local_env, "load", lambda: None)
    monkeypatch.setattr(
        module,
        "parse_args",
        lambda: module.argparse.Namespace(
            unreal=None,
            engine_version="5.8",
            count=24,
            entity_count=1,
            rate_hz=10.0,
            scenario="entity_state_1x10hz",
            timeout=30.0,
            dry_run=False,
        ),
    )
    monkeypatch.setattr(module, "clear_harness_log", lambda: None)
    monkeypatch.setattr(module, "resolve_unreal", lambda explicit, engine_version: "/Engines/UE_5.8/UnrealEditor-Cmd")
    monkeypatch.setattr(module, "build_command", lambda unreal_binary: [unreal_binary, "Project.uproject"])
    monkeypatch.setattr(module, "_discover_install", lambda engine_version: _fake_install(module))
    monkeypatch.setattr(module.unreal_env, "path_writable", lambda path: (True, str(path)))
    monkeypatch.setattr(
        module.unreal_env,
        "probe_host_platform_support",
        lambda install, project_path: {
            "failure_kind": "engine-intermediate-write-denied",
            "detail": "managed run denied Unreal writes under /Users/Shared/Epic Games/.../Engine/Intermediate/...",
            "output": "UnauthorizedAccessException: Access to the path '/Users/Shared/Epic Games/UE_5.8/Engine/Intermediate/Build/Mac/x64/UnrealEditor' is denied.",
        },
    )

    rc = module.main()

    assert rc == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "pending"
    assert payload["failure_kind"] == "engine-intermediate-write-denied"
    assert any("managed run denied Unreal writes" in error for error in payload["errors"])


def test_engine_target_intermediate_probe_short_circuits_as_pending(monkeypatch, capsys) -> None:
    module = _load_module("run_unreal_udp_smoke", ROOT / "tools" / "run_unreal_udp_smoke.py")
    monkeypatch.setattr(module.load_local_env, "load", lambda: None)
    monkeypatch.setattr(
        module,
        "parse_args",
        lambda: module.argparse.Namespace(
            unreal=None,
            engine_version="5.8",
            count=24,
            entity_count=1,
            rate_hz=10.0,
            scenario="entity_state_1x10hz",
            timeout=30.0,
            dry_run=False,
        ),
    )
    monkeypatch.setattr(module, "clear_harness_log", lambda: None)
    monkeypatch.setattr(module, "resolve_unreal", lambda explicit, engine_version: "/Engines/UE_5.8/UnrealEditor-Cmd")
    monkeypatch.setattr(module, "build_command", lambda unreal_binary: [unreal_binary, "Project.uproject"])
    install = _fake_install(module)
    monkeypatch.setattr(module, "_discover_install", lambda engine_version: install)
    monkeypatch.setattr(
        module.unreal_env,
        "path_writable",
        lambda path: (False, f"{path}: [Errno 1] Operation not permitted"),
    )

    rc = module.main()

    assert rc == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "pending"
    assert payload["failure_kind"] == "engine-intermediate-write-denied"
    assert "Operation not permitted" in payload["errors"][0]
