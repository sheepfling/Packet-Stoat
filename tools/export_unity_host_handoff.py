#!/usr/bin/env python3
"""Export a self-contained Unity cross-host proof handoff kit."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import zipfile

import load_local_env


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = ROOT / "packages" / "unity" / "com.sheepfling.fastdis"
DEFAULT_OUT_DIR = ROOT / "dist" / "unity_host_handoff"
TOOL_FILES = (
    "tools/load_local_env.py",
    "tools/unity_env.py",
    "tools/unity_workflow.py",
    "tools/run_unity_editor_tests.py",
    "tools/run_unity_startup_probe.py",
    "tools/run_unity_install_smoke.py",
    "tools/run_unity_install_matrix.py",
    "tools/run_unity_host_matrix.py",
    "tools/run_unity_orientation_verification.py",
    "tools/run_unity_signoff.py",
    "tools/import_unity_host_report.py",
    "tools/sync_unity_host_reports.py",
    "tools/capture_unity_host_report.py",
    "tools/stage_unity_host_report.py",
    "tools/export_unity_host_report.py",
)
DOC_FILES = (
    "docs/UNITY_CROSS_HOST_SIGNOFF.md",
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR), help="Directory that will receive the archive")
    return parser.parse_args(argv)


def package_version() -> str:
    payload = json.loads((PACKAGE_ROOT / "package.json").read_text(encoding="utf-8"))
    return str(payload.get("version") or "unknown")


def handoff_paths() -> list[Path]:
    paths = [ROOT / relative for relative in TOOL_FILES + DOC_FILES]
    for path in sorted(PACKAGE_ROOT.rglob("*")):
        if path.is_file():
            paths.append(path)
    return paths


def validate_handoff_paths(paths: list[Path]) -> None:
    missing = [path for path in paths if not path.is_file()]
    if missing:
        raise FileNotFoundError("Unity host handoff kit is missing required files:\n" + "\n".join(f"- {path}" for path in missing))


def relative_archive_paths(paths: list[Path]) -> list[tuple[Path, Path]]:
    bundle_root = Path(f"fastdis-unity-host-handoff-{package_version()}")
    archive_paths: list[tuple[Path, Path]] = []
    for path in paths:
        archive_paths.append((path, bundle_root / path.relative_to(ROOT)))
    return archive_paths


def render_readme() -> str:
    return "\n".join(
        [
            "# Unity Host Handoff Kit",
            "",
            "This archive is intended for a Windows/Linux/macOS host that needs to",
            "collect Unity Phase 1 proof artifacts and export a portable host bundle.",
            "",
            "## Expected Workflow",
            "",
            "1. Unzip this archive on the proof host.",
            "2. From the archive root, run one of:",
            "",
            "```bash",
            "python tools/run_unity_startup_probe.py --unity-version 6000.5",
            "python tools/capture_unity_host_report.py --unity-version 6000.5",
            "python tools/capture_unity_host_report.py --unity-version 6000.5 --skip-native-build",
            "```",
            "",
            "Run the startup probe first when qualifying a new proof host. If it",
            "cannot create the scratch Unity project Library/ directory, stop and",
            "fix the Unity/OS host before spending time on install smoke.",
            "",
            "Use `--skip-native-build` on hosts that are only validating the already-",
            "staged Unity plug-ins and do not have a local FastDIS native build",
            "toolchain available.",
            "",
            "3. Bring the resulting `dist/unity_host_reports/<host-label>.zip` archive",
            "   and its `.sha256` sidecar back to the aggregation checkout.",
            "4. On the aggregation checkout, import it with:",
            "",
            "```bash",
            "python tools/import_unity_host_report.py dist/unity_host_reports/<host-label>.zip",
            "python tools/sync_unity_host_reports.py",
            "python tools/run_unity_host_matrix.py",
            "python tools/run_unity_signoff.py",
            "```",
            "",
            "Those steps refresh the adopted install matrix, staged host matrix,",
            "workflow report, and final signoff summary.",
            "",
            "See `docs/UNITY_CROSS_HOST_SIGNOFF.md` in this archive for the full flow.",
            "",
        ]
    )


def export_archive(archive_path: Path) -> Path:
    paths = handoff_paths()
    validate_handoff_paths(paths)
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    readme_payload = render_readme()
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for source, arcname in relative_archive_paths(paths):
            archive.write(source, arcname=str(arcname))
        bundle_root = Path(f"fastdis-unity-host-handoff-{package_version()}")
        archive.writestr(str(bundle_root / "README.md"), readme_payload)
    return archive_path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_archive_checksum(archive_path: Path) -> Path:
    checksum_path = archive_path.with_suffix(archive_path.suffix + ".sha256")
    checksum_path.write_text(f"{sha256_file(archive_path)}  {archive_path.name}\n", encoding="utf-8")
    return checksum_path


def main(argv: list[str] | None = None) -> int:
    load_local_env.load()
    args = parse_args(argv)
    out_dir = Path(args.out_dir).expanduser().resolve()
    archive_path = out_dir / f"fastdis-unity-host-handoff-{package_version()}.zip"
    export_archive(archive_path)
    checksum_path = write_archive_checksum(archive_path)
    print(f"Exported Unity host handoff archive: {archive_path}")
    print(f"Archive checksum: {checksum_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
