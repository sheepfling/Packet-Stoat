"""Shared local artifact paths for FastDIS developer scripts.

All disposable build products should live under ``build/`` by default. Source
generators may still maintain checked source-adjacent files such as
``docs/MESSAGE_COVERAGE.md``; this module is for local/operator outputs.
"""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILD_ROOT = ROOT / "build"

CMAKE_ROOT = BUILD_ROOT / "cmake"
CMAKE_HOST = CMAKE_ROOT / "host"
CMAKE_MINGW_WIN64 = CMAKE_ROOT / "mingw-win64"
CMAKE_LINUX_X86_64 = CMAKE_ROOT / "linux-x86_64"

DIST_DIR = BUILD_ROOT / "dist"
REPORTS_DIR = BUILD_ROOT / "reports"
TOOL_VENVS_DIR = BUILD_ROOT / "tool_venvs"
BENCHMARK_RESULTS_DIR = BUILD_ROOT / "benchmark_results"
RELEASE_ARTIFACTS_DIR = BUILD_ROOT / "release_artifacts"
VERIFICATION_REPORTS_DIR = BUILD_ROOT / "verification_reports"


LEGACY_ARTIFACT_DIRS = (
    ROOT / "dist",
    ROOT / "release_artifacts",
    ROOT / "benchmark_results",
    ROOT / "benchmark_reports",
    ROOT / "verification_reports",
    ROOT / "build-mingw-win64",
    ROOT / "build-linux-x86_64",
    ROOT / "build-alpha3-sanitizers",
    ROOT / "build-sanitizers",
    ROOT / "build-tsan",
)


def rel(path: Path) -> str:
    """Return a stable path relative to the repo root when possible."""
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)
