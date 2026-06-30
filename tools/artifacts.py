"""Shared local artifact paths for FastDIS developer scripts.

`build/` is reserved for transient compiler/build-system state such as CMake
worktrees and intermediates. Human-inspectable local outputs like reports,
benchmark receipts, staged release bundles, and verification artifacts live
under `artifacts/`.
"""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILD_ROOT = ROOT / "build"
ARTIFACTS_ROOT = ROOT / "artifacts"

CMAKE_ROOT = BUILD_ROOT / "cmake"
CMAKE_HOST = CMAKE_ROOT / "host"
CMAKE_MINGW_WIN64 = CMAKE_ROOT / "mingw-win64"
CMAKE_LINUX_X86_64 = CMAKE_ROOT / "linux-x86_64"

DIST_DIR = ARTIFACTS_ROOT / "dist"
REPORTS_DIR = ARTIFACTS_ROOT / "reports"
TOOL_VENVS_DIR = BUILD_ROOT / "tool_venvs"
BENCHMARK_RESULTS_DIR = ARTIFACTS_ROOT / "benchmark_results"
RELEASE_ARTIFACTS_DIR = ARTIFACTS_ROOT / "release_artifacts"
VERIFICATION_REPORTS_DIR = ARTIFACTS_ROOT / "verification_reports"


LEGACY_ARTIFACT_DIRS = (
    ROOT / "dist",
    ROOT / "release_artifacts",
    ROOT / "benchmark_results",
    ROOT / "benchmark_reports",
    ROOT / "verification_reports",
    ROOT / "artifacts",
    ROOT / "build-mingw-win64",
    ROOT / "build-linux-x86_64",
    ROOT / "build-alpha3-sanitizers",
    ROOT / "build-sanitizers",
    ROOT / "build-tsan",
)


def rel(path: Path) -> str:
    """Return a stable path relative to the repo root when possible."""
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()
