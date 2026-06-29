from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_build_config_resolves_relative_cli_engine_path_from_repo_root(
    tmp_path: Path, monkeypatch
) -> None:
    module = _load_module(
        "build_unreal_linux_package_docker",
        ROOT / "tools" / "build_unreal_linux_package_docker.py",
    )
    engine_root = tmp_path / "repo" / ".build" / "linux_unreal_engine" / "ue5.7.4-linux"
    for rel in module.REQUIRED_ENGINE_PATHS:
        path = engine_root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("ok\n", encoding="utf-8")

    profile = tmp_path / "profiles" / "linux.env"
    profile.parent.mkdir(parents=True, exist_ok=True)
    profile.write_text("UE_VERSION_LABEL=ue5.7.4-linux\n", encoding="utf-8")

    monkeypatch.chdir(tmp_path / "repo")

    args = module.parse_args(
        [
            "--profile",
            str(profile),
            "--engine-path",
            ".build/linux_unreal_engine/ue5.7.4-linux",
        ]
    )

    config = module.build_config(args)

    assert config["engine_path"] == engine_root.resolve()
