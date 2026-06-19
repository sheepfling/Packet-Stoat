#!/usr/bin/env python3
"""Stage one host's Alpha 2 proof reports into a reusable cross-host bundle."""

from __future__ import annotations

import argparse
from datetime import UTC
from datetime import datetime
import json
import platform
from pathlib import Path
import re
import shutil

import load_local_env


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_DIR = ROOT / "verification_reports" / "alpha2_sample"
DEFAULT_DEST_ROOT = ROOT / "verification_reports" / "alpha2_hosts"
HOST_MANIFEST = "host_report_manifest.json"
HOST_MANIFEST_MD = "host_report_manifest.md"
REQUIRED_FILES = (
    "unreal_version_matrix.json",
    "unreal_version_matrix.md",
    "godot_workflow_report.json",
    "godot_workflow_report.md",
    "orientation_runtime_report.json",
    "orientation_runtime_report.md",
    "orientation_visual_report.json",
    "orientation_visual_report.md",
    "unreal_host_compat_report.json",
    "unreal_host_compat_report.md",
    "alpha2_release_audit_report.json",
    "alpha2_release_audit_report.md",
    "alpha2_signoff_matrix.json",
    "alpha2_signoff_matrix.md",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", default=str(DEFAULT_SOURCE_DIR), help="Directory containing the local Alpha 2 proof reports")
    parser.add_argument("--dest-root", default=str(DEFAULT_DEST_ROOT), help="Root directory that will receive the staged host bundle")
    parser.add_argument("--host-label", help="Stable label for this machine/report set; defaults to a derived host-platform slug")
    parser.add_argument("--overwrite", action="store_true", help="Replace an existing staged host bundle with the same label")
    return parser.parse_args()


def slugify(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-_.").lower()
    return slug or "host"


def detect_host_label() -> str:
    host = platform.node() or "host"
    machine = platform.machine() or "machine"
    system = platform.system() or "system"
    return slugify(f"{host}-{system}-{machine}")


def collect_manifest(source_dir: Path, host_label: str) -> dict[str, object]:
    return {
        "host_label": host_label,
        "generated_at": datetime.now(UTC).isoformat(),
        "hostname": platform.node() or host_label,
        "platform": platform.platform(),
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "python_version": platform.python_version(),
        "source_report_dir": str(source_dir),
        "required_files": list(REQUIRED_FILES),
    }


def render_manifest_markdown(manifest: dict[str, object]) -> str:
    lines = [
        "# Alpha 2 Host Report Manifest",
        "",
        f"- host_label: `{manifest['host_label']}`",
        f"- generated_at: `{manifest['generated_at']}`",
        f"- hostname: `{manifest['hostname']}`",
        f"- platform: `{manifest['platform']}`",
        f"- system: `{manifest['system']}`",
        f"- release: `{manifest['release']}`",
        f"- machine: `{manifest['machine']}`",
        f"- python_version: `{manifest['python_version']}`",
        f"- source_report_dir: `{manifest['source_report_dir']}`",
        "",
        "## Included Files",
        "",
    ]
    for name in manifest["required_files"]:
        lines.append(f"- `{name}`")
    lines.append("")
    return "\n".join(lines)


def stage_report_set(source_dir: Path, dest_dir: Path, *, overwrite: bool) -> None:
    missing = [name for name in REQUIRED_FILES if not (source_dir / name).exists()]
    if missing:
        raise FileNotFoundError(
            "Source report directory is missing required Alpha 2 proof files:\n"
            + "\n".join(f"- {name}" for name in missing)
        )
    if dest_dir.exists():
        if not overwrite:
            raise FileExistsError(f"Destination already exists: {dest_dir}")
        shutil.rmtree(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    for name in REQUIRED_FILES:
        shutil.copy2(source_dir / name, dest_dir / name)


def main() -> int:
    load_local_env.load()
    args = parse_args()
    source_dir = Path(args.source_dir).expanduser().resolve()
    dest_root = Path(args.dest_root).expanduser().resolve()
    host_label = slugify(args.host_label or detect_host_label())
    dest_dir = dest_root / host_label

    stage_report_set(source_dir, dest_dir, overwrite=args.overwrite)
    manifest = collect_manifest(source_dir, host_label)
    (dest_dir / HOST_MANIFEST).write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (dest_dir / HOST_MANIFEST_MD).write_text(render_manifest_markdown(manifest), encoding="utf-8")

    print(f"Staged host report set: {dest_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
