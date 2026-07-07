#!/usr/bin/env python3
"""Prepare a local dev environment and run the default FastDIS check.

This wrapper exists so a fresh host can bootstrap the required Python wheels
and scratch paths in one step instead of hand-exporting temp variables and
remembering the dev dependency list.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import os
from pathlib import Path
import subprocess
import sys
import sysconfig
import shutil
import platform
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP_ROOT = ROOT / "build" / "tool_bootstrap" / "dev"
DEFAULT_DEPS_PREFIX = BOOTSTRAP_ROOT / "python"
STATE_PATH = BOOTSTRAP_ROOT / "bootstrap_state.json"
WINDOWS_SCOOP_PACKAGES = ("git", "cmake", "pwsh")
NODE_BIN = Path.home() / ".cache" / "codex-runtimes" / "codex-primary-runtime" / "dependencies" / "node" / "bin"


@dataclass(frozen=True)
class BootstrapState:
    python_version: str
    requirements: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "python_version": self.python_version,
            "requirements": list(self.requirements),
        }


@dataclass(frozen=True)
class BootstrapReadiness:
    host_state: str
    deps_ready: bool
    work_roots_ready: bool
    state_present: bool


def _default_work_root() -> Path:
    if platform.system().lower() == "windows":
        return Path("C:/tmp/fastdis_dev")
    return ROOT / "build" / "work" / "dev"


DEFAULT_WORK_ROOT = _default_work_root()


def load_dev_requirements() -> tuple[str, ...]:
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    try:
        import tomllib
    except ModuleNotFoundError as exc:  # pragma: no cover - Python 3.11 fallback
        raise RuntimeError("tomllib is required to read pyproject.toml") from exc

    payload = tomllib.loads(pyproject)
    project = payload.get("project", {})
    optional = project.get("optional-dependencies", {})
    requirements = optional.get("dev", [])
    if not isinstance(requirements, list) or not requirements:
        raise RuntimeError("pyproject.toml does not define a non-empty dev extra")
    return tuple(str(item) for item in requirements)


def _prefix_paths(prefix: Path) -> dict[str, Path]:
    paths = sysconfig.get_paths(vars={"base": str(prefix), "platbase": str(prefix)})
    return {name: Path(value) for name, value in paths.items()}


def prefix_site_packages(prefix: Path) -> Path:
    return _prefix_paths(prefix)["purelib"]


def prefix_scripts_dir(prefix: Path) -> Path:
    return _prefix_paths(prefix)["scripts"]


def load_state() -> BootstrapState | None:
    if not STATE_PATH.is_file():
        return None
    payload = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return None
    python_version = str(payload.get("python_version", ""))
    requirements = payload.get("requirements", [])
    if not python_version or not isinstance(requirements, list):
        return None
    return BootstrapState(python_version=python_version, requirements=tuple(str(item) for item in requirements))


def classify_bootstrap_state(*, deps_ready: bool, work_roots_ready: bool, state_present: bool) -> str:
    if deps_ready and work_roots_ready:
        return "fully-configured"
    if deps_ready or work_roots_ready or state_present:
        return "semi-configured"
    return "fresh-host"


def detect_bootstrap_readiness(prefix: Path, work_root: Path, requirements: tuple[str, ...]) -> BootstrapReadiness:
    expected = BootstrapState(
        python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        requirements=requirements,
    )
    current = load_state()
    deps_ready = current == expected and prefix_site_packages(prefix).is_dir()
    work_roots_ready = all(
        (work_root / name).is_dir()
        for name in ("unreal", "godot", "unity", "tmp")
    )
    state_present = current is not None
    return BootstrapReadiness(
        host_state=classify_bootstrap_state(
            deps_ready=deps_ready,
            work_roots_ready=work_roots_ready,
            state_present=state_present,
        ),
        deps_ready=deps_ready,
        work_roots_ready=work_roots_ready,
        state_present=state_present,
    )


def write_state(state: BootstrapState) -> None:
    BOOTSTRAP_ROOT.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state.to_dict(), indent=2) + "\n", encoding="utf-8")


def ensure_dev_dependencies(prefix: Path, requirements: tuple[str, ...]) -> bool:
    current = load_state()
    expected = BootstrapState(python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}", requirements=requirements)
    site_packages = prefix_site_packages(prefix)
    if current == expected and site_packages.is_dir():
        return False

    prefix.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--upgrade",
        "--disable-pip-version-check",
        "--prefix",
        str(prefix),
        *requirements,
    ]
    completed = subprocess.run(cmd, cwd=ROOT, text=True)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)
    write_state(expected)
    return True


def ensure_work_roots(work_root: Path) -> dict[str, Path]:
    roots = {
        "FASTDIS_UNREAL_WORK_ROOT": work_root / "unreal",
        "FASTDIS_GODOT_WORK_ROOT": work_root / "godot",
        "FASTDIS_UNITY_WORK_ROOT": work_root / "unity",
        "FASTDIS_DEV_TMP_ROOT": work_root / "tmp",
    }
    for path in roots.values():
        path.mkdir(parents=True, exist_ok=True)
    return roots


def scoop_executable() -> str | None:
    candidate = shutil.which("scoop")
    if candidate:
        return candidate
    if platform.system().lower() == "windows":
        shim = Path.home() / "scoop" / "shims" / "scoop.cmd"
        if shim.is_file():
            return str(shim)
    return None


def missing_windows_tool_packages() -> tuple[str, ...]:
    if platform.system().lower() != "windows":
        return ()
    missing = []
    for package in WINDOWS_SCOOP_PACKAGES:
        if shutil.which(package) is None:
            missing.append(package)
    return tuple(missing)


def build_env(prefix: Path, work_root: Path) -> dict[str, str]:
    env = os.environ.copy()
    site_packages = prefix_site_packages(prefix)
    lattice_src = ROOT / "packages" / "lattice" / "src"
    extra_paths = [str(site_packages), str(ROOT / "src"), str(lattice_src)]
    existing = env.get("PYTHONPATH")
    if existing:
        extra_paths.append(existing)
    env["PYTHONPATH"] = os.pathsep.join(extra_paths)
    if platform.system().lower() == "windows":
        scoop_shims = Path.home() / "scoop" / "shims"
        if scoop_shims.is_dir():
            env["PATH"] = str(scoop_shims) + os.pathsep + env.get("PATH", "")
        if NODE_BIN.is_dir():
            env["PATH"] = env.get("PATH", "") + os.pathsep + str(NODE_BIN)
    elif NODE_BIN.is_dir():
        env["PATH"] = str(NODE_BIN) + os.pathsep + env.get("PATH", "")
    for key, path in ensure_work_roots(work_root).items():
        env.setdefault(key, str(path))
    env.setdefault("TEMP", str(work_root / "tmp"))
    env.setdefault("TMP", str(work_root / "tmp"))
    return env


def build_dev_check_command(dev_check_args: list[str]) -> list[str]:
    args = list(dev_check_args)
    if not args:
        args = ["--quick"]
    return [sys.executable, "tools/dev_check.py", *args]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--deps-prefix", type=Path, default=DEFAULT_DEPS_PREFIX, help="Prefix directory for local Python dev dependencies")
    parser.add_argument("--work-root", type=Path, default=DEFAULT_WORK_ROOT, help="Scratch root for Unreal, Godot, Unity, and temp state")
    parser.add_argument("--skip-install", action="store_true", help="Skip installing dev dependencies and only prepare the runtime environment")
    parser.add_argument("--prepare-only", action="store_true", help="Install dev dependencies and scratch roots without running dev_check.py")
    parser.add_argument("dev_check_args", nargs=argparse.REMAINDER, default=[], help="Arguments forwarded to tools/dev_check.py")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    requirements = load_dev_requirements()
    readiness = detect_bootstrap_readiness(args.deps_prefix, args.work_root, requirements)
    print(f"bootstrap state: {readiness.host_state}")
    if readiness.host_state == "fresh-host":
        print("bootstrap plan: install dev deps, create work roots, then run the quick check")
    elif readiness.host_state == "semi-configured":
        print("bootstrap plan: repair any missing dev deps or work roots, then run the quick check")
    else:
        print("bootstrap plan: reuse the existing dev deps and work roots, then run the quick check")
    if platform.system().lower() == "windows":
        missing_tools = missing_windows_tool_packages()
        if missing_tools:
            print("windows tools: missing", ", ".join(missing_tools))
            print("windows tools: blocked until Scoop-managed tools are available")
            return 1
        else:
            print("windows tools: scoop-managed host tools already available")
    if not args.skip_install:
        installed = ensure_dev_dependencies(args.deps_prefix, requirements)
        print(f"dev dependencies: {'installed' if installed else 'already present'}")
    else:
        print("dev dependencies: skipped")

    env = build_env(args.deps_prefix, args.work_root)
    if args.prepare_only:
        print("bootstrap work root:", args.work_root)
        print("bootstrap deps prefix:", args.deps_prefix)
        return 0
    dev_check_args = args.dev_check_args
    if dev_check_args and dev_check_args[0] == "--":
        dev_check_args = dev_check_args[1:]
    command = build_dev_check_command(dev_check_args)
    print("bootstrap work root:", args.work_root)
    print("bootstrap deps prefix:", args.deps_prefix)
    print("+", " ".join(command))
    completed = subprocess.run(command, cwd=ROOT, env=env, text=True)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
