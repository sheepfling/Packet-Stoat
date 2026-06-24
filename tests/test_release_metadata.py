from __future__ import annotations

from pathlib import Path

import sys


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import release_metadata


def test_release_tag_from_python_version_handles_alpha_versions() -> None:
    assert release_metadata.release_tag_from_python_version("0.17.0a10") == "v0.17.0-alpha10"


def test_release_metadata_reads_current_project_version() -> None:
    assert release_metadata.project_version(ROOT) == "0.17.0a10"
    assert release_metadata.release_tag(ROOT) == "v0.17.0-alpha10"
    assert release_metadata.artifact_dir(ROOT).name == "current"
    assert release_metadata.benchmark_dir(ROOT).name == "current"
