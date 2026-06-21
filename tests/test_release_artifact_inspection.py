from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import zipfile


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import inspect_alpha5_release_artifacts


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def _write_manifest(artifact_dir: Path, paths: list[Path]) -> None:
    manifest = {
        "schema": "fastdis.alpha5_release_manifest.v1",
        "version": "v0.15.0-alpha5",
        "artifacts": [{"name": path.name, "sha256": _sha256(path), "bytes": path.stat().st_size} for path in paths],
    }
    (artifact_dir / "RELEASE_MANIFEST.json").write_text(json.dumps(manifest), encoding="utf-8")


def _zip(path: Path, entries: dict[str, bytes]) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, payload in entries.items():
            archive.writestr(name, payload)


def test_release_artifact_inspection_accepts_clean_bundle(tmp_path: Path) -> None:
    archive = tmp_path / "fastdis-docs-v0.15.0-alpha5.zip"
    _zip(archive, {"fastdis-docs-v0.15.0-alpha5/README.md": b"# docs\n"})
    wheel = tmp_path / "fastdis-0.15.0a5-py3-none-any.whl"
    wheel.write_bytes(b"wheel")
    _write_manifest(tmp_path, [archive, wheel])

    report = inspect_alpha5_release_artifacts.inspect_artifact_dir(tmp_path)

    assert report["overall_status"] == "pass"
    assert report["issues"] == []


def test_release_artifact_inspection_rejects_forbidden_archive_paths(tmp_path: Path) -> None:
    archive = tmp_path / "fastdis-source-v0.15.0-alpha5.zip"
    _zip(archive, {"fastdis-source-v0.15.0-alpha5/.venv/bin/python": b"local venv"})
    _write_manifest(tmp_path, [archive])

    report = inspect_alpha5_release_artifacts.inspect_artifact_dir(tmp_path)

    assert report["overall_status"] == "fail"
    assert any(issue["kind"] == "forbidden_path_part" for issue in report["issues"])


def test_release_artifact_inspection_rejects_secret_patterns(tmp_path: Path) -> None:
    archive = tmp_path / "fastdis-docs-v0.15.0-alpha5.zip"
    _zip(archive, {"fastdis-docs-v0.15.0-alpha5/token.txt": b"token=ghp_123456789012345678901234567890123456"})
    _write_manifest(tmp_path, [archive])

    report = inspect_alpha5_release_artifacts.inspect_artifact_dir(tmp_path)

    assert report["overall_status"] == "fail"
    assert any(issue["kind"] == "secret_pattern" for issue in report["issues"])


def test_release_artifact_inspection_rejects_bad_artifact_versions(tmp_path: Path) -> None:
    archive = tmp_path / "fastdis-docs-v0.14.0-alpha4.zip"
    _zip(archive, {"fastdis-docs-v0.14.0-alpha4/README.md": b"# stale\n"})
    _write_manifest(tmp_path, [archive])

    report = inspect_alpha5_release_artifacts.inspect_artifact_dir(tmp_path)

    assert report["overall_status"] == "fail"
    assert any(issue["kind"] == "unexpected_artifact_version" for issue in report["issues"])
