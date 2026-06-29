#!/usr/bin/env python3
"""Stage credential-free Alpha5 release artifacts locally."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

from artifacts import BENCHMARK_RESULTS_DIR, DIST_DIR, VERIFICATION_REPORTS_DIR
from release_metadata import artifact_dir as current_artifact_dir
from release_metadata import benchmark_dir as current_benchmark_dir
from release_metadata import release_tag


ROOT = Path(__file__).resolve().parents[1]
VERSION = release_tag(ROOT)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def should_skip(path: Path) -> bool:
    parts = set(path.parts)
    if parts & {
        ".git",
        "__pycache__",
        ".pytest_cache",
        "build",
        "dist",
        "release_artifacts",
        "benchmark_results",
        "benchmark_reports",
        "verification_reports",
        "Library",
        "Temp",
        "Obj",
        "Logs",
        "UserSettings",
        ".godot",
        "Intermediate",
        "Saved",
        "Binaries",
        ".venv",
        ".mypy_cache",
        ".ruff_cache",
        ".pyright",
        ".agent",
        ".agents",
    }:
        return True
    if path.name in {".DS_Store", ".env", ".env.local", ".envrc"}:
        return True
    return path.suffix in {".pyc", ".pyo", ".pem", ".key", ".p12", ".pfx"}


def zip_tree(source: Path, archive_path: Path, *, prefix: str) -> None:
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(source.rglob("*")):
            if path.is_dir() or should_skip(path):
                continue
            archive.write(path, Path(prefix) / path.relative_to(source))
        bad = archive.testzip()
        if bad:
            raise RuntimeError(f"zip integrity failure at {bad}")


def zip_paths(paths: list[Path], archive_path: Path, *, prefix: str) -> None:
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for source in paths:
            if not source.exists():
                continue
            if source.is_file():
                archive.write(source, Path(prefix) / source.name)
                continue
            for path in sorted(source.rglob("*")):
                if path.is_dir() or should_skip(path):
                    continue
                archive.write(path, Path(prefix) / source.name / path.relative_to(source))
        bad = archive.testzip()
        if bad:
            raise RuntimeError(f"zip integrity failure at {bad}")


def copy_dist(out_dir: Path) -> list[Path]:
    copied: list[Path] = []
    dist = DIST_DIR
    if not dist.is_dir():
        return copied
    for path in sorted(dist.iterdir()):
        if path.is_file():
            dest = out_dir / path.name
            shutil.copy2(path, dest)
            copied.append(dest)
    return copied


def stage(args: argparse.Namespace) -> dict[str, object]:
    out_dir = args.out_dir.resolve()
    if args.clean and out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    artifacts: list[Path] = []
    artifacts.extend(copy_dist(out_dir))

    benchmark_candidates = [current_benchmark_dir(ROOT), BENCHMARK_RESULTS_DIR / "alpha5"]
    benchmark_path = next((path for path in benchmark_candidates if path.exists()), benchmark_candidates[0])

    artifact_specs = [
        ("fastdis-docs", [ROOT / "docs"]),
        ("fastdis-verification", [ROOT / "build" / "reports", VERIFICATION_REPORTS_DIR]),
        ("fastdis-benchmarks", [benchmark_path]),
        ("fastdis-lattice-lab", [ROOT / "packages" / "lattice"]),
        ("fastdis-unity-upm", [ROOT / "packages" / "unity" / "com.sheepfling.fastdis"]),
        ("fastdis-unreal-plugin", [ROOT / "packages" / "unreal" / "FastDis"]),
        ("fastdis-godot-addon", [ROOT / "packages" / "godot" / "fastdis_demo" / "addons" / "fastdis"]),
    ]
    for name, paths in artifact_specs:
        if not any(path.exists() for path in paths):
            continue
        archive = out_dir / f"{name}-{VERSION}.zip"
        zip_paths(paths, archive, prefix=f"{name}-{VERSION}")
        artifacts.append(archive)

    source_archive = out_dir / f"fastdis-{VERSION}-source.zip"
    zip_tree(ROOT, source_archive, prefix=f"fastdis-{VERSION}-source")
    artifacts.append(source_archive)

    checksums = out_dir / "SHA256SUMS"
    checksums.write_text("".join(f"{sha256_file(path)}  {path.name}\n" for path in sorted(artifacts)), encoding="utf-8")
    artifacts.append(checksums)

    manifest = {
        "schema": "fastdis.release_manifest.v1",
        "version": VERSION,
        "credential_gated": ["PyPI/TestPyPI publish", "Fab publish", "Godot marketplace publish", "Unity Asset Store publish", "live Lattice endpoint checks"],
        "artifacts": [
            {
                "name": path.name,
                "path": str(path),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
            for path in sorted(artifacts)
        ],
    }
    manifest_path = out_dir / "RELEASE_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"release artifacts: {out_dir}")
    print(f"manifest: {manifest_path}")
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=current_artifact_dir(ROOT))
    parser.add_argument("--clean", action="store_true")
    return parser.parse_args()


def main() -> int:
    stage(parse_args())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
