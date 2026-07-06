from __future__ import annotations

from datetime import UTC, datetime, timedelta
import os
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


def test_collect_paths_preserves_artifact_vault(monkeypatch, tmp_path: Path) -> None:
    artifacts = tmp_path / "artifacts"
    reports = artifacts / "reports"
    preserved = artifacts / "preserved"
    reports.mkdir(parents=True)
    preserved.mkdir()
    monkeypatch.setattr(clean_artifacts, "ROOT", tmp_path)
    monkeypatch.setattr(clean_artifacts, "ARTIFACTS_ROOT", artifacts)
    monkeypatch.setattr(clean_artifacts, "PRESERVED_ARTIFACTS_DIR", preserved)
    monkeypatch.setattr(clean_artifacts, "BUILD_ROOT", tmp_path / "build")
    monkeypatch.setattr(clean_artifacts, "LEGACY_ARTIFACT_DIRS", (artifacts,))

    paths = clean_artifacts.collect_paths(
        include_caches=False,
        include_legacy=True,
        include_build=False,
        include_temp=False,
        temp_max_age_days=7,
    )

    assert paths == [reports]


def test_collect_stale_temp_paths_only_returns_old_children(monkeypatch, tmp_path: Path) -> None:
    scratch = tmp_path / "artifacts" / "scratch"
    unity_tmp = tmp_path / "fastdis_unity"
    unreal_tmp = tmp_path / "fastdis_unreal"
    old_dir = scratch / "old-job"
    new_dir = scratch / "new-job"
    old_unity = unity_tmp / "old-unity"
    old_unreal = unreal_tmp / "old-unreal"
    for path in (old_dir, new_dir, old_unity, old_unreal):
        path.mkdir(parents=True, exist_ok=True)

    old_time = (datetime.now(UTC) - timedelta(days=10)).timestamp()
    new_time = (datetime.now(UTC) - timedelta(days=1)).timestamp()
    os.utime(old_dir, (old_time, old_time))
    os.utime(old_unity, (old_time, old_time))
    os.utime(old_unreal, (old_time, old_time))
    os.utime(new_dir, (new_time, new_time))

    monkeypatch.setattr(clean_artifacts, "ARTIFACTS_ROOT", tmp_path / "artifacts")
    monkeypatch.setattr(clean_artifacts.unity_env, "work_root", lambda: unity_tmp)
    monkeypatch.setattr(clean_artifacts.unreal_env, "DEFAULT_WORK_ROOT", unreal_tmp)

    paths = clean_artifacts.collect_stale_temp_paths(max_age_days=7)

    assert old_dir in paths
    assert old_unity in paths
    assert old_unreal in paths
    assert new_dir not in paths
