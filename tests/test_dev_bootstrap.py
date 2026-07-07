from __future__ import annotations

import argparse
from pathlib import Path
import sys

TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import bootstrap_local_dev


def test_load_dev_requirements_includes_core_bootstrap_dependencies() -> None:
    requirements = bootstrap_local_dev.load_dev_requirements()

    assert "pytest>=8" in requirements
    assert "Pillow>=10" in requirements
    assert "scipy>=1.11" in requirements


def test_build_dev_check_command_defaults_to_quick() -> None:
    command = bootstrap_local_dev.build_dev_check_command([])

    assert Path(command[1]).name == "dev_check.py"
    assert command[-1] == "--quick"


def test_build_dev_check_command_forwards_explicit_args() -> None:
    command = bootstrap_local_dev.build_dev_check_command(["--all"])

    assert Path(command[1]).name == "dev_check.py"
    assert command[-1] == "--all"


def test_build_env_prepares_paths(monkeypatch, tmp_path: Path) -> None:
    prefix = tmp_path / "deps"
    work_root = tmp_path / "work"
    prefix_site = bootstrap_local_dev.prefix_site_packages(prefix)
    prefix_site.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("PYTHONPATH", "existing-path")
    monkeypatch.delenv("TEMP", raising=False)
    monkeypatch.delenv("TMP", raising=False)

    env = bootstrap_local_dev.build_env(prefix, work_root)

    parts = env["PYTHONPATH"].split(";")
    assert parts[0] == str(prefix_site)
    assert parts[1] == str(bootstrap_local_dev.ROOT / "src")
    assert parts[2] == str(bootstrap_local_dev.ROOT / "packages" / "lattice" / "src")
    assert parts[3] == "existing-path"
    assert env["FASTDIS_UNREAL_WORK_ROOT"] == str(work_root / "unreal")
    assert env["FASTDIS_GODOT_WORK_ROOT"] == str(work_root / "godot")
    assert env["FASTDIS_UNITY_WORK_ROOT"] == str(work_root / "unity")
    assert env["FASTDIS_DEV_TMP_ROOT"] == str(work_root / "tmp")
    assert env["TEMP"] == str(work_root / "tmp")
    assert env["TMP"] == str(work_root / "tmp")


def test_build_env_prepends_scoop_shims_on_windows(monkeypatch, tmp_path: Path) -> None:
    scoop_shims = tmp_path / "scoop" / "shims"
    scoop_shims.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(bootstrap_local_dev.platform, "system", lambda: "Windows")
    monkeypatch.setattr(bootstrap_local_dev.Path, "home", lambda: tmp_path)

    env = bootstrap_local_dev.build_env(tmp_path / "deps", tmp_path / "work")

    assert env["PATH"].split(";")[0] == str(scoop_shims)


def test_default_work_root_prefers_short_windows_tmp_root(monkeypatch) -> None:
    monkeypatch.setattr(bootstrap_local_dev.platform, "system", lambda: "Windows")

    assert bootstrap_local_dev._default_work_root() == Path("C:/tmp/fastdis_dev")


def test_classify_bootstrap_state_covers_host_variants() -> None:
    assert bootstrap_local_dev.classify_bootstrap_state(deps_ready=False, work_roots_ready=False, state_present=False) == "fresh-host"
    assert bootstrap_local_dev.classify_bootstrap_state(deps_ready=True, work_roots_ready=False, state_present=True) == "semi-configured"
    assert bootstrap_local_dev.classify_bootstrap_state(deps_ready=True, work_roots_ready=True, state_present=True) == "fully-configured"


def test_detect_bootstrap_readiness_reports_existing_work_roots(monkeypatch, tmp_path: Path) -> None:
    prefix = tmp_path / "deps"
    work_root = tmp_path / "work"
    for child in ("unreal", "godot", "unity", "tmp"):
        (work_root / child).mkdir(parents=True, exist_ok=True)

    state = bootstrap_local_dev.BootstrapState(
        python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        requirements=("pytest>=8",),
    )

    monkeypatch.setattr(bootstrap_local_dev, "load_state", lambda: state)
    monkeypatch.setattr(bootstrap_local_dev, "prefix_site_packages", lambda value: value / "Lib" / "site-packages")
    (prefix / "Lib" / "site-packages").mkdir(parents=True, exist_ok=True)

    readiness = bootstrap_local_dev.detect_bootstrap_readiness(prefix, work_root, state.requirements)

    assert readiness.host_state == "fully-configured"
    assert readiness.deps_ready is True
    assert readiness.work_roots_ready is True


def test_main_blocks_windows_without_scoop_tools(monkeypatch, capsys) -> None:
    args = argparse.Namespace(deps_prefix=Path("deps"), work_root=Path("work"), skip_install=True, prepare_only=True, dev_check_args=[])
    readiness = bootstrap_local_dev.BootstrapReadiness(
        host_state="fresh-host",
        deps_ready=False,
        work_roots_ready=False,
        state_present=False,
    )

    monkeypatch.setattr(bootstrap_local_dev.platform, "system", lambda: "Windows")
    monkeypatch.setattr(bootstrap_local_dev, "parse_args", lambda: args)
    monkeypatch.setattr(bootstrap_local_dev, "load_dev_requirements", lambda: ("pytest>=8",))
    monkeypatch.setattr(bootstrap_local_dev, "detect_bootstrap_readiness", lambda *_args: readiness)
    monkeypatch.setattr(bootstrap_local_dev, "missing_windows_tool_packages", lambda: ("git", "cmake"))

    assert bootstrap_local_dev.main() == 1

    out = capsys.readouterr().out
    assert "windows tools: missing git, cmake" in out
    assert "blocked until Scoop-managed tools are available" in out


def test_main_reports_bootstrap_state(monkeypatch, capsys) -> None:
    args = argparse.Namespace(deps_prefix=Path("deps"), work_root=Path("work"), skip_install=True, prepare_only=True, dev_check_args=[])
    readiness = bootstrap_local_dev.BootstrapReadiness(
        host_state="semi-configured",
        deps_ready=True,
        work_roots_ready=False,
        state_present=True,
    )

    monkeypatch.setattr(bootstrap_local_dev.platform, "system", lambda: "Linux")
    monkeypatch.setattr(bootstrap_local_dev, "parse_args", lambda: args)
    monkeypatch.setattr(bootstrap_local_dev, "load_dev_requirements", lambda: ("pytest>=8",))
    monkeypatch.setattr(bootstrap_local_dev, "detect_bootstrap_readiness", lambda *_args: readiness)
    monkeypatch.setattr(bootstrap_local_dev, "build_env", lambda *_args: {})

    assert bootstrap_local_dev.main() == 0

    out = capsys.readouterr().out
    assert "bootstrap state: semi-configured" in out
    assert "bootstrap plan: repair any missing dev deps or work roots" in out
