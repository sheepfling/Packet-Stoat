#!/usr/bin/env python3
"""Import a portable Alpha 2 host bundle archive into the repo host-report root."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import zipfile

import evidence_layout
import load_local_env
import stage_alpha2_host_report


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_HOST_ROOT = evidence_layout.ALPHA2_HOSTS_DIR


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", help="Zip archive produced by export_alpha2_host_report.py")
    parser.add_argument("--host-root", default=str(DEFAULT_HOST_ROOT), help="Root directory that will receive the imported host bundle")
    parser.add_argument("--overwrite", action="store_true", help="Replace an existing host bundle with the same label")
    parser.add_argument("--checksum", help="Optional .sha256 sidecar to verify before import")
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_archive_checksum(archive_path: Path, checksum_path: Path) -> None:
    line = checksum_path.read_text(encoding="utf-8").strip()
    if not line:
        raise ValueError(f"Checksum file is empty: {checksum_path}")
    expected, _, recorded_name = line.partition("  ")
    if not expected or not recorded_name:
        raise ValueError(f"Checksum file has unexpected format: {checksum_path}")
    if recorded_name != archive_path.name:
        raise ValueError(
            f"Checksum sidecar references {recorded_name!r}, expected {archive_path.name!r}"
        )
    actual = sha256_file(archive_path)
    if actual != expected:
        raise ValueError(
            f"Archive checksum mismatch for {archive_path.name}: expected {expected}, got {actual}"
        )


def validate_extracted_host_dir(host_dir: Path) -> str:
    manifest_path = host_dir / stage_alpha2_host_report.HOST_MANIFEST
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Imported bundle is missing {stage_alpha2_host_report.HOST_MANIFEST}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    host_label = str(manifest.get("host_label") or "").strip()
    if not host_label:
        raise ValueError("Imported host manifest is missing host_label")
    expected = set(stage_alpha2_host_report.REQUIRED_FILES + (stage_alpha2_host_report.HOST_MANIFEST, stage_alpha2_host_report.HOST_MANIFEST_MD))
    missing = [name for name in expected if not (host_dir / name).exists()]
    if missing:
        raise FileNotFoundError("Imported host bundle is incomplete:\n" + "\n".join(f"- {name}" for name in missing))
    if host_dir.name != host_label:
        raise ValueError(f"Archive top-level directory {host_dir.name!r} does not match manifest host_label {host_label!r}")
    return host_label


def import_archive(archive_path: Path, host_root: Path, *, overwrite: bool) -> Path:
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_root = Path(tmp_dir)
        with zipfile.ZipFile(archive_path) as archive:
            archive.extractall(tmp_root)
        children = [child for child in tmp_root.iterdir() if child.is_dir()]
        if len(children) != 1:
            raise ValueError("Imported archive must contain exactly one top-level host directory")
        extracted = children[0]
        host_label = validate_extracted_host_dir(extracted)
        dest_dir = host_root / host_label
        if dest_dir.exists():
            if not overwrite:
                raise FileExistsError(f"Destination already exists: {dest_dir}")
            shutil.rmtree(dest_dir)
        host_root.mkdir(parents=True, exist_ok=True)
        shutil.copytree(extracted, dest_dir)
        return dest_dir


def main() -> int:
    load_local_env.load()
    args = parse_args()
    archive_path = Path(args.archive).expanduser().resolve()
    checksum_path = Path(args.checksum).expanduser().resolve() if args.checksum else archive_path.with_suffix(archive_path.suffix + ".sha256")
    if checksum_path.exists():
        verify_archive_checksum(archive_path, checksum_path)
    host_root = Path(args.host_root).expanduser().resolve()
    dest_dir = import_archive(archive_path, host_root, overwrite=args.overwrite)
    print(f"Imported host report bundle: {dest_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
