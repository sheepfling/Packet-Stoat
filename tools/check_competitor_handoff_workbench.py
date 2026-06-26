#!/usr/bin/env python3
"""Validate that a competitor handoff archive contains the expected workbench payload."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from typing import Any
import zipfile

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import export_competitor_benchmark_handoff

DEFAULT_OUT_DIR = ROOT / "build" / "reports" / "competitor_handoff_workbench_check"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", help="Path to a competitor handoff .zip archive or extracted bundle directory")
    parser.add_argument("--json-out", type=Path, default=DEFAULT_OUT_DIR / "competitor_handoff_workbench_check.json")
    parser.add_argument("--md-out", type=Path, default=DEFAULT_OUT_DIR / "competitor_handoff_workbench_check.md")
    parser.add_argument("--fail-missing", action="store_true", help="Return nonzero when required files are missing")
    return parser.parse_args(argv)


def display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def load_bundle_root(bundle_path: Path) -> tuple[Path, tempfile.TemporaryDirectory[str] | None]:
    if bundle_path.is_dir():
        return bundle_path, None
    if bundle_path.is_file() and bundle_path.suffix == ".zip":
        tmp_dir = tempfile.TemporaryDirectory()
        tmp_root = Path(tmp_dir.name)
        with zipfile.ZipFile(bundle_path) as archive:
            archive.extractall(tmp_root)
        dirs = [child for child in tmp_root.iterdir() if child.is_dir()]
        if len(dirs) != 1:
            raise ValueError("Expected exactly one top-level bundle directory in archive")
        return dirs[0], tmp_dir
    raise FileNotFoundError(f"Bundle path is neither a directory nor a .zip archive: {bundle_path}")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_manifest(bundle_root: Path) -> dict[str, Any] | None:
    manifest_path = bundle_root / export_competitor_benchmark_handoff.MANIFEST_NAME
    if not manifest_path.is_file():
        return None
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def manifest_required_rows(bundle_root: Path, manifest: dict[str, Any]) -> tuple[list[dict[str, Any]], int]:
    rows: list[dict[str, Any]] = []
    missing_count = 0
    for entry in manifest.get("files", []):
        relative = Path(str(entry["path"]))
        target = bundle_root / relative
        exists = target.is_file()
        row: dict[str, Any] = {
            "path": relative.as_posix(),
            "exists": exists,
            "size_bytes": entry.get("size_bytes"),
            "sha256": entry.get("sha256"),
        }
        if not exists:
            missing_count += 1
            row["checksum_match"] = False
        else:
            row["checksum_match"] = sha256_file(target) == entry.get("sha256")
        rows.append(row)
    return rows, missing_count


def build_report(bundle_root: Path) -> dict[str, Any]:
    manifest = load_manifest(bundle_root)
    manifest_present = manifest is not None
    manifest_valid = False
    rows: list[dict[str, Any]] = []
    missing_count = 0
    checksum_mismatch_count = 0
    readme_exists = (bundle_root / "README.md").is_file()
    bundle_kind = "archive_bundle" if manifest_present else "local_checkout"
    self_describing_bundle = False

    if manifest is not None:
        rows, missing_count = manifest_required_rows(bundle_root, manifest)
        checksum_mismatch_count = sum(1 for row in rows if not row["checksum_match"])
        manifest_valid = (
            manifest.get("schema") == "fastdis.competitor_benchmark_handoff_manifest.v1"
            and isinstance(manifest.get("files"), list)
            and any(row["path"] == "README.md" for row in rows)
        )
        self_describing_bundle = manifest_valid
    else:
        required = [Path(relative) for relative in export_competitor_benchmark_handoff.HANDOFF_FILES]
        for relative in required:
            exists = (bundle_root / relative).is_file()
            if not exists:
                missing_count += 1
            rows.append(
                {
                    "path": relative.as_posix(),
                    "exists": exists,
                    "checksum_match": None,
                }
            )
        if not readme_exists:
            missing_count += 1

    if manifest_present and not manifest_valid:
        missing_count += 1

    status = "pass" if missing_count == 0 and checksum_mismatch_count == 0 else "fail"
    return {
        "schema": "fastdis.competitor_handoff_workbench_check.v1",
        "bundle_root": display_path(bundle_root),
        "status": status,
        "summary": {
            "required_file_count": len(rows),
            "present_file_count": sum(1 for row in rows if row["exists"]),
            "missing_file_count": missing_count,
            "checksum_mismatch_count": checksum_mismatch_count,
            "readme_present": readme_exists,
            "bundle_kind": bundle_kind,
            "self_describing_bundle": self_describing_bundle,
            "manifest_present": manifest_present,
            "manifest_valid": manifest_valid,
        },
        "rows": rows,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Competitor Handoff Workbench Check",
        "",
        f"- schema: `{report['schema']}`",
        f"- bundle_root: `{report['bundle_root']}`",
        f"- status: `{report['status']}`",
        f"- required_file_count: `{report['summary']['required_file_count']}`",
        f"- present_file_count: `{report['summary']['present_file_count']}`",
        f"- missing_file_count: `{report['summary']['missing_file_count']}`",
        f"- checksum_mismatch_count: `{report['summary']['checksum_mismatch_count']}`",
        f"- readme_present: `{report['summary']['readme_present']}`",
        f"- bundle_kind: `{report['summary']['bundle_kind']}`",
        f"- self_describing_bundle: `{report['summary']['self_describing_bundle']}`",
        f"- manifest_present: `{report['summary']['manifest_present']}`",
        f"- manifest_valid: `{report['summary']['manifest_valid']}`",
        "",
        "| path | exists | checksum_match |",
        "| --- | --- | --- |",
    ]
    for row in report["rows"]:
        lines.append(f"| {row['path']} | {row['exists']} | {row['checksum_match']} |")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    bundle_path = Path(args.bundle).expanduser().resolve()
    bundle_root, tmp_dir = load_bundle_root(bundle_path)
    try:
        report = build_report(bundle_root)
    finally:
        if tmp_dir is not None:
            tmp_dir.cleanup()
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.md_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    args.md_out.write_text(render_markdown(report) + "\n", encoding="utf-8")
    print(f"json: {display_path(args.json_out)}")
    print(f"md: {display_path(args.md_out)}")
    return 1 if args.fail_missing and report["status"] != "pass" else 0


if __name__ == "__main__":
    raise SystemExit(main())
