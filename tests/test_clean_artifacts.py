from __future__ import annotations

from pathlib import Path
import sys

import pytest


TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import clean_artifacts


def test_collect_windows_mangled_dirs(tmp_path: Path) -> None:
    if sys.platform.startswith("win"):
        pytest.skip("Windows-style mangled directory names are only created on non-Windows hosts")
    mangled = tmp_path / "C:\\fastdis_godot"
    normal = tmp_path / "src"
    mangled.mkdir()
    normal.mkdir()

    assert clean_artifacts.collect_windows_mangled_dirs(tmp_path) == [mangled]


def test_remove_path_deletes_directory(tmp_path: Path) -> None:
    artifact = tmp_path / "build"
    artifact.mkdir()
    (artifact / "report.json").write_text("{}", encoding="utf-8")

    row = clean_artifacts.remove_path(artifact)

    assert row["removed"] is True
    assert not artifact.exists()
