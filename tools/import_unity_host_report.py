#!/usr/bin/env python3
"""Import a portable Unity host bundle archive and adopt its install evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import zipfile

import load_local_env
import run_unity_install_matrix
import run_unity_host_matrix
import run_unity_signoff
import stage_unity_host_report
import unity_workflow


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_HOST_ROOT = ROOT / "verification_reports" / "unity_hosts"
DEFAULT_REPORT_DIR = ROOT / "artifacts" / "reports"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", help="Zip archive produced by export_unity_host_report.py")
    parser.add_argument("--host-root", default=str(DEFAULT_HOST_ROOT), help="Root directory that will receive the imported host bundle")
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR), help="Directory that will receive adopted unity_install_smoke_<host>.json evidence")
    parser.add_argument("--overwrite", action="store_true", help="Replace an existing host bundle with the same label")
    parser.add_argument("--checksum", help="Optional .sha256 sidecar to verify before import")
    return parser.parse_args(argv)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_archive_checksum(archive_path: Path, checksum_path: Path) -> None:
    line = checksum_path.read_text(encoding="utf-8").strip()
    expected, _, recorded_name = line.partition("  ")
    if not expected or recorded_name != archive_path.name:
        raise ValueError(f"Checksum file has unexpected format: {checksum_path}")
    actual = sha256_file(archive_path)
    if actual != expected:
        raise ValueError(f"Archive checksum mismatch for {archive_path.name}: expected {expected}, got {actual}")


def validate_extracted_host_dir(host_dir: Path) -> tuple[str, dict[str, object]]:
    manifest_path = host_dir / stage_unity_host_report.HOST_MANIFEST
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Imported bundle is missing {stage_unity_host_report.HOST_MANIFEST}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    host_label = str(manifest.get("host_label") or "").strip()
    if not host_label:
        raise ValueError("Imported host manifest is missing host_label")
    required_files = tuple(str(name) for name in manifest.get("required_files") or ())
    expected = set(required_files + (stage_unity_host_report.HOST_MANIFEST, stage_unity_host_report.HOST_MANIFEST_MD))
    missing = [name for name in expected if not (host_dir / name).exists()]
    if missing:
        raise FileNotFoundError("Imported Unity host bundle is incomplete:\n" + "\n".join(f"- {name}" for name in missing))
    if host_dir.name != host_label:
        raise ValueError(f"Archive top-level directory {host_dir.name!r} does not match manifest host_label {host_label!r}")
    return host_label, manifest


def import_archive(archive_path: Path, host_root: Path, *, overwrite: bool) -> tuple[Path, dict[str, object]]:
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_root = Path(tmp_dir)
        with zipfile.ZipFile(archive_path) as archive:
            archive.extractall(tmp_root)
        children = [child for child in tmp_root.iterdir() if child.is_dir()]
        if len(children) != 1:
            raise ValueError("Imported archive must contain exactly one top-level host directory")
        extracted = children[0]
        host_label, manifest = validate_extracted_host_dir(extracted)
        dest_dir = host_root / host_label
        if dest_dir.exists():
            if not overwrite:
                raise FileExistsError(f"Destination already exists: {dest_dir}")
            shutil.rmtree(dest_dir)
        host_root.mkdir(parents=True, exist_ok=True)
        shutil.copytree(extracted, dest_dir)
        return dest_dir, manifest


def adopt_install_smoke_from_bundle(host_dir: Path, manifest: dict[str, object], report_dir: Path) -> tuple[Path, Path]:
    host_platform = str(manifest.get("host_platform") or "").strip()
    if host_platform not in {"macos", "windows", "linux"}:
        raise ValueError(f"Unity host bundle manifest has unexpected host_platform: {host_platform!r}")
    report_dir.mkdir(parents=True, exist_ok=True)
    source_json = host_dir / f"unity_install_smoke_{host_platform}.json"
    source_md = host_dir / f"unity_install_smoke_{host_platform}.md"
    dest_json = report_dir / source_json.name
    dest_md = report_dir / source_md.name
    shutil.copy2(source_json, dest_json)
    shutil.copy2(source_md, dest_md)
    return dest_json, dest_md


def refresh_aggregate_reports(report_dir: Path, host_root: Path) -> tuple[Path, Path, Path, Path, Path, Path, Path, Path]:
    matrix = run_unity_install_matrix.build_report(report_dir)
    matrix_json = report_dir / "unity_install_matrix.json"
    matrix_md = report_dir / "unity_install_matrix.md"
    matrix_json.write_text(json.dumps(matrix, indent=2) + "\n", encoding="utf-8")
    matrix_md.write_text(run_unity_install_matrix.render_markdown(matrix), encoding="utf-8")

    host_matrix = run_unity_host_matrix.build_report(host_root)
    host_matrix_json = report_dir / "unity_host_matrix.json"
    host_matrix_md = report_dir / "unity_host_matrix.md"
    host_matrix_json.write_text(json.dumps(host_matrix, indent=2) + "\n", encoding="utf-8")
    host_matrix_md.write_text(run_unity_host_matrix.render_markdown(host_matrix), encoding="utf-8")

    existing_workflow = unity_workflow._read_json_report(report_dir / "unity_workflow_report.json") or {}
    requested_version = existing_workflow.get("requested_version")
    workflow = unity_workflow.doctor_payload(str(requested_version) if requested_version else None, report_dir)
    unity_workflow.write_report(workflow, report_dir)

    signoff = run_unity_signoff.evaluate(report_dir, host_root)
    signoff_json = report_dir / "unity_signoff_report.json"
    signoff_md = report_dir / "unity_signoff_report.md"
    signoff_json.write_text(json.dumps(signoff, indent=2) + "\n", encoding="utf-8")
    signoff_md.write_text(run_unity_signoff.render_markdown(signoff), encoding="utf-8")
    return (
        matrix_json,
        matrix_md,
        host_matrix_json,
        host_matrix_md,
        report_dir / "unity_workflow_report.json",
        report_dir / "unity_workflow_report.md",
        signoff_json,
        signoff_md,
    )


def main(argv: list[str] | None = None) -> int:
    load_local_env.load()
    args = parse_args(argv)
    archive_path = Path(args.archive).expanduser().resolve()
    checksum_path = Path(args.checksum).expanduser().resolve() if args.checksum else archive_path.with_suffix(archive_path.suffix + ".sha256")
    if checksum_path.exists():
        verify_archive_checksum(archive_path, checksum_path)
    host_root = Path(args.host_root).expanduser().resolve()
    report_dir = Path(args.report_dir).expanduser().resolve()
    dest_dir, manifest = import_archive(archive_path, host_root, overwrite=args.overwrite)
    adopted_json, adopted_md = adopt_install_smoke_from_bundle(dest_dir, manifest, report_dir)
    matrix_json, matrix_md, host_matrix_json, host_matrix_md, workflow_json, workflow_md, signoff_json, signoff_md = refresh_aggregate_reports(report_dir, host_root)
    print(f"Imported Unity host report bundle: {dest_dir}")
    print(f"Adopted install evidence: {adopted_json}")
    print(f"Adopted install summary: {adopted_md}")
    print(f"Refreshed install matrix: {matrix_json}")
    print(f"Refreshed install matrix summary: {matrix_md}")
    print(f"Refreshed host matrix: {host_matrix_json}")
    print(f"Refreshed host matrix summary: {host_matrix_md}")
    print(f"Refreshed workflow report: {workflow_json}")
    print(f"Refreshed workflow summary: {workflow_md}")
    print(f"Refreshed signoff report: {signoff_json}")
    print(f"Refreshed signoff summary: {signoff_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
