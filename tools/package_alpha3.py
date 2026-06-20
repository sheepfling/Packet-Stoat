#!/usr/bin/env python3
"""Create the fastdis v0.13.0-alpha3 source bundle."""

from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUNDLE_NAME = "fastdis_alpha_v0_13_0"
ARCHIVE_NAME = f"{BUNDLE_NAME}.zip"
CHECKSUM_FILE = "CHECKSUMS.sha256"
EXCLUDED_PREFIXES = (
    ".git/",
    ".pytest_cache/",
    ".venv/",
    "benchmark_results/",
    "build/",
    "build-",
    "dist/",
    "release_artifacts/",
)
EXCLUDED_PARTS = {"__pycache__"}
TOP_LEVEL_EXCLUDES = {".gitignore"}
ALPHA3_HOST_REQUIRED_FILES = {
    "orientation_verification_report.json",
    "orientation_verification_report.md",
    "orientation_visual_report.json",
    "orientation_visual_report.md",
    "orientation_pipeline_report.json",
    "orientation_pipeline_report.md",
    "godot_workflow_report.json",
    "godot_workflow_report.md",
    "unreal_version_matrix.json",
    "unreal_version_matrix.md",
    "sanitizer_smoke_report.json",
    "sanitizer_smoke_report.md",
    "io_routes_report.json",
    "io_routes_report.md",
    "network_ingest_matrix.json",
    "network_ingest_matrix.md",
    "host_report_manifest.json",
    "host_report_manifest.md",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def should_include(path: str) -> bool:
    if path in TOP_LEVEL_EXCLUDES:
        return False
    if any(path.startswith(prefix) for prefix in EXCLUDED_PREFIXES):
        return False
    parts = Path(path).parts
    if any(part in EXCLUDED_PARTS for part in parts):
        return False
    if parts and parts[0].startswith(".") and parts[0] != ".github":
        return False
    if len(parts) >= 4 and parts[0] == "verification_reports" and parts[1] == "alpha3_hosts":
        return parts[3] in ALPHA3_HOST_REQUIRED_FILES
    return True


def _git_paths(*args: str) -> list[str]:
    result = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", *args, "-z"],
        check=True,
        stdout=subprocess.PIPE,
    )
    return [item for item in result.stdout.decode("utf-8").split("\0") if item]


def repo_files() -> list[str]:
    tracked = _git_paths()
    others = _git_paths("--others", "--exclude-standard")
    combined = sorted(set(tracked + others))
    return [path for path in combined if should_include(path) and (ROOT / path).exists()]


def write_checksums(base_dir: Path, relative_paths: list[str], checksum_path: Path) -> None:
    lines = []
    for relative_path in relative_paths:
        if relative_path == CHECKSUM_FILE:
            continue
        digest = sha256_file(base_dir / relative_path)
        lines.append(f"{digest}  {relative_path}")
    checksum_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def copy_bundle_files(destination: Path, relative_paths: list[str]) -> None:
    for relative_path in relative_paths:
        source = ROOT / relative_path
        target = destination / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def create_archive(bundle_dir: Path, archive_path: Path) -> None:
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(bundle_dir.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(bundle_dir.parent))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "dist" / "alpha3",
        help="Directory that will receive the staging tree and zip archive.",
    )
    parser.add_argument(
        "--write-root-checksums",
        action="store_true",
        help="Refresh the repository CHECKSUMS.sha256 file before packaging.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    relative_paths = repo_files()
    if CHECKSUM_FILE not in relative_paths:
        relative_paths.append(CHECKSUM_FILE)
        relative_paths.sort()

    if args.write_root_checksums:
        write_checksums(ROOT, relative_paths, ROOT / CHECKSUM_FILE)

    output_dir = args.output_dir.resolve()
    bundle_dir = output_dir / BUNDLE_NAME
    archive_path = output_dir / ARCHIVE_NAME
    archive_checksum_path = output_dir / f"{ARCHIVE_NAME}.sha256"

    if bundle_dir.exists():
        shutil.rmtree(bundle_dir)
    if archive_path.exists():
        archive_path.unlink()
    if archive_checksum_path.exists():
        archive_checksum_path.unlink()

    output_dir.mkdir(parents=True, exist_ok=True)
    copy_bundle_files(bundle_dir, relative_paths)
    write_checksums(bundle_dir, relative_paths, bundle_dir / CHECKSUM_FILE)
    create_archive(bundle_dir, archive_path)
    archive_checksum_path.write_text(
        f"{sha256_file(archive_path)}  {archive_path.name}\n",
        encoding="utf-8",
    )

    with zipfile.ZipFile(archive_path) as archive:
        bad_entry = archive.testzip()
    if bad_entry is not None:
        raise RuntimeError(f"zip integrity failure at {bad_entry}")

    print(f"bundle: {bundle_dir}")
    print(f"archive: {archive_path}")
    print(f"archive checksum: {archive_checksum_path}")
    print(f"files: {len(relative_paths)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
