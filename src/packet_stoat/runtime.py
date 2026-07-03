"""Shared CLI process helpers for repo-local command wrappers."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
from typing import Sequence


ROOT = Path(__file__).resolve().parents[2]


def env() -> dict[str, str]:
    payload = os.environ.copy()
    src = str(ROOT / "src")
    lattice_src = str(ROOT / "packages" / "lattice" / "src")
    pythonpath = payload.get("PYTHONPATH")
    payload["PYTHONPATH"] = os.pathsep.join([src, lattice_src] if not pythonpath else [src, lattice_src, pythonpath])
    return payload


def run(cmd: Sequence[str]) -> int:
    print("+", " ".join(cmd))
    completed = subprocess.run(list(cmd), cwd=ROOT, env=env())
    return completed.returncode


def run_module(module: str, args: Sequence[str]) -> int:
    return run([sys.executable, "-m", module, *args])


def run_tool(tool: str, args: Sequence[str]) -> int:
    return run([sys.executable, str(ROOT / "tools" / tool), *args])
