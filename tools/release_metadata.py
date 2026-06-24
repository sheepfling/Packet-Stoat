"""Release metadata helpers derived from the current project version."""

from __future__ import annotations

from pathlib import Path
import re
import tomllib

from artifacts import BENCHMARK_RESULTS_DIR, RELEASE_ARTIFACTS_DIR, ROOT


def project_version(root: Path = ROOT) -> str:
    pyproject = root / "pyproject.toml"
    payload = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    return str(payload["project"]["version"])


def release_tag_from_python_version(version: str) -> str:
    match = re.fullmatch(r"(?P<base>\d+\.\d+\.\d+)a(?P<alpha>\d+)", version)
    if not match:
        return f"v{version}"
    return f"v{match.group('base')}-alpha{match.group('alpha')}"


def plugin_version_name_from_python_version(version: str) -> str:
    return release_tag_from_python_version(version).removeprefix("v")


def plugin_version_number_from_python_version(version: str) -> int:
    match = re.fullmatch(r"(?P<base>\d+\.\d+\.\d+)a(?P<alpha>\d+)", version)
    if not match:
        raise ValueError(f"Unsupported alpha version format: {version}")
    return int(match.group("alpha"))


def release_tag(root: Path = ROOT) -> str:
    return release_tag_from_python_version(project_version(root))


def artifact_dir(root: Path = ROOT) -> Path:
    _ = root
    return RELEASE_ARTIFACTS_DIR / "current"


def benchmark_dir(root: Path = ROOT) -> Path:
    _ = root
    return BENCHMARK_RESULTS_DIR / "current"
