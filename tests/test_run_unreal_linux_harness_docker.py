from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = ROOT / "tools"
sys.path.insert(0, str(TOOLS_DIR))


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_build_config_resolves_relative_cli_engine_path_from_repo_root(tmp_path: Path, monkeypatch) -> None:
    module = _load_module(
        "run_unreal_linux_harness_docker",
        ROOT / "tools" / "run_unreal_linux_harness_docker.py",
    )
    helper = _load_module(
        "build_unreal_linux_package_docker_for_harness",
        ROOT / "tools" / "build_unreal_linux_package_docker.py",
    )
    engine_root = tmp_path / "repo" / ".build" / "linux_unreal_engine" / "ue5.7.4-linux"
    for rel in helper.REQUIRED_ENGINE_PATHS:
        path = engine_root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("ok\n", encoding="utf-8")

    profile = tmp_path / "profiles" / "linux.env"
    profile.parent.mkdir(parents=True, exist_ok=True)
    profile.write_text("UE_VERSION_LABEL=ue5.7.4-linux\n", encoding="utf-8")

    monkeypatch.chdir(tmp_path / "repo")

    args = module.parse_args(
        [
            "--mode",
            "verify",
            "--profile",
            str(profile),
            "--engine-path",
            ".build/linux_unreal_engine/ue5.7.4-linux",
        ]
    )

    config = module.build_config(args)

    assert config["engine_path"] == engine_root.resolve()
    assert config["json_out"].name == "fastdis_unreal_linux_verify.json"


def test_run_capture_writes_fallback_report_when_inner_harness_does_not_emit_one(
    tmp_path: Path, monkeypatch
) -> None:
    module = _load_module(
        "run_unreal_linux_harness_docker_fallback",
        ROOT / "tools" / "run_unreal_linux_harness_docker.py",
    )
    helper = _load_module(
        "build_unreal_linux_package_docker_for_harness_fallback",
        ROOT / "tools" / "build_unreal_linux_package_docker.py",
    )
    engine_root = tmp_path / "engine"
    for rel in helper.REQUIRED_ENGINE_PATHS:
        path = engine_root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("ok\n", encoding="utf-8")

    monkeypatch.setattr(module.docker_build, "docker_preflight", lambda image, platform_name: None)

    class Completed:
        returncode = 124

    monkeypatch.setattr(module.subprocess, "run", lambda command, cwd=None: Completed())

    config = {
        "image": "fastdis-linux-proof:ubuntu24.04",
        "platform": "linux/amd64",
        "ue_root_in_container": "/opt/unreal-engine",
        "safe_label": "ue5.7.4-linux_ubuntu-24.04",
        "engine_path": engine_root,
        "engine_archive": None,
        "engine_stage_dir": tmp_path / "stage",
        "force_reextract": False,
        "json_out": tmp_path / "out" / "verify.json",
        "md_out": tmp_path / "out" / "verify.md",
        "mode": "verify",
        "engine_version": "5.7",
        "dry_run": False,
        "timeout_seconds": 30,
    }

    rc = module.run_capture(config)

    assert rc == 124
    payload = json.loads(config["json_out"].read_text(encoding="utf-8"))
    assert payload["status"] == "timeout"
    assert "work_dir" in payload
