from __future__ import annotations

import importlib.util
from pathlib import Path
import types


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
    assert config["docker_user"] == "1000:1000"


def test_build_config_discovers_standard_linux_archive_for_requested_version(
    tmp_path: Path, monkeypatch
) -> None:
    module = _load_module(
        "build_unreal_linux_package_docker_discovery",
        ROOT / "tools" / "build_unreal_linux_package_docker.py",
    )
    archive = tmp_path / "Linux_Unreal_Engine_5.9.1.zip"
    archive.write_text("zip\n", encoding="utf-8")
    monkeypatch.setattr(module, "default_linux_engine_search_roots", lambda: [tmp_path])
    monkeypatch.setattr(module, "platform", types.SimpleNamespace(system=lambda: "Windows"))

    args = module.parse_args(["--engine-version", "5.9"])
    config = module.build_config(args)

    assert config["engine_archive"] == archive.resolve()
    assert config["engine_path"] is None
    assert config["engine_version"] == "5.9"
    assert config["version_label"] == "ue5.9.1-linux"
    assert str(config["engine_stage_dir"]).replace("\\", "/").endswith("/artifacts/staging/unreal/linux/ue5.9.1-linux")
    assert str(config["package_dir"]).replace("\\", "/").endswith("/artifacts/packages/unreal/linux/ue5.9.1-linux_ubuntu-24.04/package")


def test_discover_linux_engine_inputs_ignores_non_engine_versioned_archives(
    tmp_path: Path, monkeypatch
) -> None:
    module = _load_module(
        "build_unreal_linux_package_docker_discovery_filter",
        ROOT / "tools" / "build_unreal_linux_package_docker.py",
    )
    (tmp_path / "Linux_Bridge_5.8.0_2025.0.1.zip").write_text("zip\n", encoding="utf-8")
    (tmp_path / "Linux_Fab_5.8.0_0.0.13.zip").write_text("zip\n", encoding="utf-8")
    engine_archive = tmp_path / "Linux_Unreal_Engine_5.8.0.zip"
    engine_archive.write_text("zip\n", encoding="utf-8")
    monkeypatch.setattr(module, "default_linux_engine_search_roots", lambda: [tmp_path])

    rows = module.discover_linux_engine_inputs()

    assert [row["archive_path"] for row in rows] == [engine_archive.resolve()]


def test_default_linux_engine_search_roots_prefers_d_drive_on_windows(
    monkeypatch,
) -> None:
    module = _load_module(
        "build_unreal_linux_package_docker_windows_roots",
        ROOT / "tools" / "build_unreal_linux_package_docker.py",
    )
    monkeypatch.setattr(module.platform, "system", lambda: "Windows")

    roots = module.default_linux_engine_search_roots()

    assert Path(r"D:\Unreal\linux") in roots
    assert Path(r"C:\Users\Public\Unreal\engines\linux") in roots
    assert roots.index(Path(r"D:\Unreal\linux")) < roots.index(Path(r"C:\Users\Public\Unreal\engines\linux"))


def test_build_config_honors_explicit_docker_user_env(tmp_path: Path, monkeypatch) -> None:
    module = _load_module(
        "build_unreal_linux_package_docker_user",
        ROOT / "tools" / "build_unreal_linux_package_docker.py",
    )
    engine_root = tmp_path / "engine"
    for rel in module.REQUIRED_ENGINE_PATHS:
        path = engine_root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("ok\n", encoding="utf-8")

    profile = tmp_path / "profiles" / "linux.env"
    profile.parent.mkdir(parents=True, exist_ok=True)
    profile.write_text("UE_VERSION_LABEL=ue5.7.4-linux\nDOCKER_USER=4242:4242\n", encoding="utf-8")

    monkeypatch.chdir(tmp_path)

    args = module.parse_args(
        [
            "--profile",
            str(profile),
            "--engine-path",
            str(engine_root),
        ]
    )

    config = module.build_config(args)

    assert config["docker_user"] == "4242:4242"
