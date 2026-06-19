from __future__ import annotations

import json
import sys
from pathlib import Path
import zipfile


TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import export_alpha2_host_report
import import_alpha2_host_report
import stage_alpha2_host_report


def write_host_bundle(base: Path, host_label: str) -> Path:
    host_dir = base / host_label
    host_dir.mkdir(parents=True, exist_ok=True)
    for name in stage_alpha2_host_report.REQUIRED_FILES:
        suffix = Path(name).suffix
        if suffix == ".json":
            (host_dir / name).write_text(json.dumps({"name": name}), encoding="utf-8")
        else:
            (host_dir / name).write_text(f"{name}\n", encoding="utf-8")
    manifest = {
        "host_label": host_label,
        "hostname": f"{host_label}.example",
        "platform": "macOS-15-arm64",
        "host_fingerprint": f"fingerprint-{host_label}",
        "report_digest_sha256": f"digest-{host_label}",
    }
    (host_dir / stage_alpha2_host_report.HOST_MANIFEST).write_text(json.dumps(manifest), encoding="utf-8")
    (host_dir / stage_alpha2_host_report.HOST_MANIFEST_MD).write_text("# manifest\n", encoding="utf-8")
    return host_dir


def test_export_archive_writes_host_bundle_zip(tmp_path: Path) -> None:
    host_root = tmp_path / "hosts"
    host_dir = write_host_bundle(host_root, "host-a")
    archive_path = tmp_path / "out" / "host-a.zip"

    export_alpha2_host_report.export_archive(host_dir, archive_path)

    assert archive_path.is_file()
    with zipfile.ZipFile(archive_path) as archive:
        assert "host-a/host_report_manifest.json" in archive.namelist()


def test_import_archive_round_trips_host_bundle(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    host_dir = write_host_bundle(source_root, "host-a")
    archive_path = tmp_path / "out" / "host-a.zip"
    export_alpha2_host_report.export_archive(host_dir, archive_path)

    dest = import_alpha2_host_report.import_archive(archive_path, tmp_path / "dest", overwrite=False)

    assert dest == (tmp_path / "dest" / "host-a")
    assert (dest / stage_alpha2_host_report.HOST_MANIFEST).is_file()
    assert (dest / "unreal_version_matrix.json").is_file()


def test_import_archive_rejects_label_mismatch(tmp_path: Path) -> None:
    archive_path = tmp_path / "bad.zip"
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("wrong-dir/host_report_manifest.json", json.dumps({"host_label": "host-a"}))
        archive.writestr("wrong-dir/host_report_manifest.md", "# manifest\n")
        for name in stage_alpha2_host_report.REQUIRED_FILES:
            archive.writestr(f"wrong-dir/{name}", "{}" if name.endswith(".json") else f"{name}\n")

    try:
        import_alpha2_host_report.import_archive(archive_path, tmp_path / "dest", overwrite=False)
    except ValueError as exc:
        assert "does not match manifest host_label" in str(exc)
    else:
        raise AssertionError("expected ValueError")
