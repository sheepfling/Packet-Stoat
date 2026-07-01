#!/usr/bin/env python3
"""Stage one host's Unity proof reports into a reusable cross-host bundle."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import shutil

import evidence_layout
import host_profile
import load_local_env
import unity_workflow


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_DIR = ROOT / "artifacts" / "reports"
DEFAULT_DEST_ROOT = evidence_layout.UNITY_HOSTS_DIR
HOST_MANIFEST = "unity_host_report_manifest.json"
HOST_MANIFEST_MD = "unity_host_report_manifest.md"
REQUIRED_COMMON_FILES = (
    "unity_workflow_report.json",
    "unity_workflow_report.md",
    "unity_runtime_verification.json",
    "unity_runtime_verification.md",
    "unity_orientation_verification.json",
    "unity_orientation_verification.md",
    "unity_startup_probe.json",
    "unity_startup_probe.md",
    "unity_csharp_bridge_probe.json",
    "unity_csharp_bridge_probe.md",
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", default=str(DEFAULT_SOURCE_DIR), help="Directory containing the local Unity proof reports")
    parser.add_argument("--dest-root", default=str(DEFAULT_DEST_ROOT), help="Root directory that will receive the staged host bundle")
    parser.add_argument("--host-label", help="Stable label for this machine/report set; defaults to a derived host-platform slug")
    parser.add_argument("--host-platform", choices=("macos", "windows", "linux"), help="Override the host platform label")
    parser.add_argument("--hostname", help="Override the recorded hostname for host-identity quirks or remote-capture workflows")
    parser.add_argument("--host-system", help="Override the recorded platform.system() value for host-identity quirks")
    parser.add_argument("--host-release", help="Override the recorded platform.release() value for host-identity quirks")
    parser.add_argument("--host-machine", help="Override the recorded platform.machine() value for host-identity quirks")
    parser.add_argument("--host-python-version", help="Override the recorded platform.python_version() value")
    parser.add_argument("--host-fingerprint-seed", help="Additional stable fingerprint seed for hosts that need explicit identity disambiguation")
    parser.add_argument("--overwrite", action="store_true", help="Replace an existing staged host bundle with the same label")
    return parser.parse_args(argv)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def host_platform_label(source_dir: Path, override: str | None) -> str:
    if override:
        return override
    report = unity_workflow.latest_install_smoke_report(source_dir)
    if report and report.get("host_platform"):
        return str(report["host_platform"])
    return unity_workflow.host_install_label()


def required_files_for(host_platform: str) -> tuple[str, ...]:
    return REQUIRED_COMMON_FILES + (
        f"unity_install_smoke_{host_platform}.json",
        f"unity_install_smoke_{host_platform}.md",
    )


def compute_report_digest(source_dir: Path, required_files: tuple[str, ...]) -> str:
    digest = hashlib.sha256()
    for name in required_files:
        digest.update(name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(sha256_file(source_dir / name).encode("ascii"))
        digest.update(b"\0")
    return digest.hexdigest()


def detect_host_label() -> str:
    return host_profile.resolve_host_profile().host_label


def collect_manifest(
    source_dir: Path,
    profile: host_profile.HostProfile,
    required_files: tuple[str, ...],
) -> dict[str, object]:
    install_smoke = unity_workflow._read_json_report(source_dir / f"unity_install_smoke_{profile.host_platform}.json") or {}
    workflow_report = unity_workflow._read_json_report(source_dir / "unity_workflow_report.json") or {}
    startup_probe = unity_workflow._read_json_report(source_dir / "unity_startup_probe.json") or {}
    return {
        "host_label": profile.host_label,
        "host_platform": profile.host_platform,
        "generated_at": datetime.now(UTC).isoformat(),
        "hostname": profile.hostname,
        "platform": profile.platform_string,
        "system": profile.system,
        "release": profile.release,
        "machine": profile.machine,
        "python_version": profile.python_version,
        "host_identity_source": profile.identity_source,
        "host_fingerprint": profile.host_fingerprint,
        "report_digest_sha256": compute_report_digest(source_dir, required_files),
        "source_report_dir": str(source_dir),
        "required_files": list(required_files),
        "unity_install_status": install_smoke.get("status"),
        "unity_install_host": install_smoke.get("host_platform") or profile.host_platform,
        "unity_workflow_status": workflow_report.get("unity_workflow_status"),
        "unity_runtime_status": workflow_report.get("unity_runtime_status"),
        "unity_orientation_status": workflow_report.get("unity_orientation_status"),
        "unity_startup_probe_status": startup_probe.get("status"),
    }


def render_manifest_markdown(manifest: dict[str, object]) -> str:
    lines = [
        "# Unity Host Report Manifest",
        "",
        f"- host_label: `{manifest['host_label']}`",
        f"- host_platform: `{manifest['host_platform']}`",
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
        f"- unity_workflow_status: `{manifest.get('unity_workflow_status', 'unknown')}`",
        f"- unity_runtime_status: `{manifest.get('unity_runtime_status', 'unknown')}`",
        f"- unity_orientation_status: `{manifest.get('unity_orientation_status', 'unknown')}`",
        f"- unity_startup_probe_status: `{manifest.get('unity_startup_probe_status', 'unknown')}`",
        f"- unity_install_status: `{manifest.get('unity_install_status', 'unknown')}`",
        "",
        "## Included Files",
        "",
    ]
    for name in manifest["required_files"]:
        lines.append(f"- `{name}`")
    lines.append("")
    return "\n".join(lines)


def stage_report_set(source_dir: Path, dest_dir: Path, required_files: tuple[str, ...], *, overwrite: bool) -> None:
    missing = [name for name in required_files if not (source_dir / name).exists()]
    if missing:
        raise FileNotFoundError(
            "Source report directory is missing required Unity proof files:\n" + "\n".join(f"- {name}" for name in missing)
        )
    if dest_dir.exists():
        if not overwrite:
            raise FileExistsError(f"Destination already exists: {dest_dir}")
        shutil.rmtree(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    for name in required_files:
        shutil.copy2(source_dir / name, dest_dir / name)


def main(argv: list[str] | None = None) -> int:
    load_local_env.load()
    args = parse_args(argv)
    source_dir = Path(args.source_dir).expanduser().resolve()
    dest_root = Path(args.dest_root).expanduser().resolve()
    profile = host_profile.resolve_host_profile(
        host_label_override=args.host_label,
        host_platform_override=args.host_platform or host_platform_label(source_dir, None),
        hostname_override=args.hostname,
        system_override=args.host_system,
        release_override=args.host_release,
        machine_override=args.host_machine,
        python_version_override=args.host_python_version,
        fingerprint_seed_override=args.host_fingerprint_seed,
    )
    host_label = profile.host_label
    host_platform = profile.host_platform
    required_files = required_files_for(host_platform)
    dest_dir = dest_root / host_label

    stage_report_set(source_dir, dest_dir, required_files, overwrite=args.overwrite)
    manifest = collect_manifest(source_dir, profile, required_files)
    (dest_dir / HOST_MANIFEST).write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (dest_dir / HOST_MANIFEST_MD).write_text(render_manifest_markdown(manifest), encoding="utf-8")
    print(f"Staged Unity host report set: {dest_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
