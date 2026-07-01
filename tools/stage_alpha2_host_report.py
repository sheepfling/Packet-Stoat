#!/usr/bin/env python3
"""Stage one host's Alpha 2 proof reports into a reusable cross-host bundle."""

from __future__ import annotations

import argparse
from datetime import UTC
from datetime import datetime
import hashlib
import json
from pathlib import Path
import shutil

import evidence_layout
import host_profile
import load_local_env


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_DIR = evidence_layout.ALPHA2_SAMPLE_DIR
DEFAULT_DEST_ROOT = evidence_layout.ALPHA2_HOSTS_DIR
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
    parser.add_argument("--hostname", help="Override the recorded hostname for host-identity quirks or remote-capture workflows")
    parser.add_argument("--host-system", help="Override the recorded platform.system() value for host-identity quirks")
    parser.add_argument("--host-release", help="Override the recorded platform.release() value for host-identity quirks")
    parser.add_argument("--host-machine", help="Override the recorded platform.machine() value for host-identity quirks")
    parser.add_argument("--host-python-version", help="Override the recorded platform.python_version() value")
    parser.add_argument("--host-fingerprint-seed", help="Additional stable fingerprint seed for hosts that need explicit identity disambiguation")
    parser.add_argument("--overwrite", action="store_true", help="Replace an existing staged host bundle with the same label")
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def compute_report_digest(source_dir: Path) -> str:
    digest = hashlib.sha256()
    for name in REQUIRED_FILES:
        digest.update(name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(sha256_file(source_dir / name).encode("ascii"))
        digest.update(b"\0")
    return digest.hexdigest()


def detect_host_label() -> str:
    return host_profile.resolve_host_profile().host_label


def collect_manifest(source_dir: Path, profile: host_profile.HostProfile) -> dict[str, object]:
    return {
        "host_label": profile.host_label,
        "generated_at": datetime.now(UTC).isoformat(),
        "hostname": profile.hostname,
        "host_platform": profile.host_platform,
        "platform": profile.platform_string,
        "system": profile.system,
        "release": profile.release,
        "machine": profile.machine,
        "python_version": profile.python_version,
        "host_identity_source": profile.identity_source,
        "host_fingerprint": profile.host_fingerprint,
        "report_digest_sha256": compute_report_digest(source_dir),
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
        f"- host_identity_source: `{manifest['host_identity_source']}`",
        f"- host_fingerprint: `{manifest['host_fingerprint']}`",
        f"- report_digest_sha256: `{manifest['report_digest_sha256']}`",
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
    profile = host_profile.resolve_host_profile(
        host_label_override=args.host_label,
        hostname_override=args.hostname,
        system_override=args.host_system,
        release_override=args.host_release,
        machine_override=args.host_machine,
        python_version_override=args.host_python_version,
        fingerprint_seed_override=args.host_fingerprint_seed,
    )
    host_label = profile.host_label
    dest_dir = dest_root / host_label

    stage_report_set(source_dir, dest_dir, overwrite=args.overwrite)
    manifest = collect_manifest(source_dir, profile)
    (dest_dir / HOST_MANIFEST).write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (dest_dir / HOST_MANIFEST_MD).write_text(render_manifest_markdown(manifest), encoding="utf-8")

    print(f"Staged host report set: {dest_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
