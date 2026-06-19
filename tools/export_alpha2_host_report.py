#!/usr/bin/env python3
"""Export one staged Alpha 2 host bundle as a portable archive."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import zipfile

import load_local_env
import stage_alpha2_host_report


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_HOST_ROOT = ROOT / "verification_reports" / "alpha2_hosts"
DEFAULT_OUT_DIR = ROOT / "dist" / "alpha2_host_reports"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("host_label", help="Host bundle label under verification_reports/alpha2_hosts/")
    parser.add_argument("--host-root", default=str(DEFAULT_HOST_ROOT), help="Root directory containing staged host bundles")
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR), help="Directory that will receive the archive")
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def export_archive(host_dir: Path, archive_path: Path) -> None:
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(stage_alpha2_host_report.REQUIRED_FILES + (stage_alpha2_host_report.HOST_MANIFEST, stage_alpha2_host_report.HOST_MANIFEST_MD)):
            path = host_dir / name
            archive.write(path, arcname=f"{host_dir.name}/{name}")


def write_archive_checksum(archive_path: Path) -> Path:
    checksum_path = archive_path.with_suffix(archive_path.suffix + ".sha256")
    checksum_path.write_text(f"{sha256_file(archive_path)}  {archive_path.name}\n", encoding="utf-8")
    return checksum_path


def main() -> int:
    load_local_env.load()
    args = parse_args()
    host_root = Path(args.host_root).expanduser().resolve()
    host_dir = host_root / args.host_label
    if not host_dir.is_dir():
        raise FileNotFoundError(f"Host bundle not found: {host_dir}")
    missing = [
        name
        for name in stage_alpha2_host_report.REQUIRED_FILES + (stage_alpha2_host_report.HOST_MANIFEST, stage_alpha2_host_report.HOST_MANIFEST_MD)
        if not (host_dir / name).exists()
    ]
    if missing:
        raise FileNotFoundError("Host bundle is incomplete:\n" + "\n".join(f"- {name}" for name in missing))
    out_dir = Path(args.out_dir).expanduser().resolve()
    archive_path = out_dir / f"{args.host_label}.zip"
    export_archive(host_dir, archive_path)
    checksum_path = write_archive_checksum(archive_path)
    print(f"Exported host report archive: {archive_path}")
    print(f"Archive checksum: {checksum_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
