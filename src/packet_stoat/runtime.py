"""Shared CLI process helpers for repo-local command wrappers."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
from typing import Sequence


ROOT = Path(__file__).resolve().parents[2]
LOCAL_BOOTSTRAP_PREFIX = ROOT / "build" / "tool_bootstrap" / "dev" / "python"
LOCAL_BOOTSTRAP_SITE_PACKAGES = LOCAL_BOOTSTRAP_PREFIX / "Lib" / "site-packages"
LOCAL_BOOTSTRAP_WORK_ROOT = ROOT / "build" / "work" / "dev"


def env() -> dict[str, str]:
    payload = os.environ.copy()
    path_entries = [str(ROOT / "src"), str(ROOT / "packages" / "lattice" / "src")]
    if LOCAL_BOOTSTRAP_SITE_PACKAGES.is_dir():
        path_entries.insert(0, str(LOCAL_BOOTSTRAP_SITE_PACKAGES))
    pythonpath = payload.get("PYTHONPATH")
    payload["PYTHONPATH"] = os.pathsep.join(path_entries if not pythonpath else [*path_entries, pythonpath])
    if LOCAL_BOOTSTRAP_WORK_ROOT.is_dir():
        payload.setdefault("FASTDIS_UNREAL_WORK_ROOT", str(LOCAL_BOOTSTRAP_WORK_ROOT / "unreal"))
        payload.setdefault("FASTDIS_GODOT_WORK_ROOT", str(LOCAL_BOOTSTRAP_WORK_ROOT / "godot"))
        payload.setdefault("FASTDIS_UNITY_WORK_ROOT", str(LOCAL_BOOTSTRAP_WORK_ROOT / "unity"))
        payload.setdefault("FASTDIS_DEV_TMP_ROOT", str(LOCAL_BOOTSTRAP_WORK_ROOT / "tmp"))
        payload.setdefault("TEMP", str(LOCAL_BOOTSTRAP_WORK_ROOT / "tmp"))
        payload.setdefault("TMP", str(LOCAL_BOOTSTRAP_WORK_ROOT / "tmp"))
    return payload


def run(cmd: Sequence[str]) -> int:
    print("+", " ".join(cmd))
    completed = subprocess.run(list(cmd), cwd=ROOT, env=env())
    return completed.returncode


def run_module(module: str, args: Sequence[str]) -> int:
    return run([sys.executable, "-m", module, *args])


def run_tool(tool: str, args: Sequence[str]) -> int:
    return run([sys.executable, str(ROOT / "tools" / tool), *args])
