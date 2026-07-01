from __future__ import annotations

import json
from pathlib import Path
import sys
import zipfile


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import export_unity_host_report
import import_unity_host_report
import stage_unity_host_report


def _write_source_reports(root: Path, host_platform: str = "windows") -> None:
    common = {
        "unity_workflow_report.json": {"unity_workflow_status": "pass", "unity_runtime_status": "pass", "unity_orientation_status": "pass"},
        "unity_runtime_verification.json": {"overall_status": "pass"},
        "unity_orientation_verification.json": {"status": "pass"},
        "unity_startup_probe.json": {"status": "pass"},
        "unity_csharp_bridge_probe.json": {"overall_status": "pass"},
    }
    for name, payload in common.items():
        (root / name).write_text(json.dumps(payload) + "\n", encoding="utf-8")
        (root / name.replace(".json", ".md")).write_text(f"# {name}\n", encoding="utf-8")
    install = {
        "schema": "fastdis.unity_install_smoke.v1",
        "status": "pass",
        "host_platform": host_platform,
        "detail": "pass",
        "unity_version": "6000.5.0f1",
    }
    (root / f"unity_install_smoke_{host_platform}.json").write_text(json.dumps(install) + "\n", encoding="utf-8")
    (root / f"unity_install_smoke_{host_platform}.md").write_text("# install smoke\n", encoding="utf-8")


def test_stage_unity_host_report_writes_manifest(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "source"
    dest_root = tmp_path / "hosts"
    source.mkdir()
    _write_source_reports(source, "linux")
    monkeypatch.setattr(stage_unity_host_report.load_local_env, "load", lambda: None)
    monkeypatch.setattr(
        stage_unity_host_report,
        "parse_args",
        lambda argv=None: stage_unity_host_report.argparse.Namespace(
            source_dir=str(source),
            dest_root=str(dest_root),
            host_label="linux-box",
            host_platform="linux",
            hostname=None,
            host_system=None,
            host_release=None,
            host_machine=None,
            host_python_version=None,
            host_fingerprint_seed=None,
            overwrite=False,
        ),
    )

    rc = stage_unity_host_report.main()

    assert rc == 0
    manifest = json.loads((dest_root / "linux-box" / stage_unity_host_report.HOST_MANIFEST).read_text(encoding="utf-8"))
    assert manifest["host_platform"] == "linux"
    assert manifest["unity_install_status"] == "pass"
    assert manifest["unity_install_host"] == "linux"
    assert manifest["unity_startup_probe_status"] == "pass"


def test_stage_unity_host_report_supports_host_identity_overrides(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "source"
    dest_root = tmp_path / "hosts"
    source.mkdir()
    _write_source_reports(source, "windows")
    monkeypatch.setattr(stage_unity_host_report.load_local_env, "load", lambda: None)
    monkeypatch.setattr(
        stage_unity_host_report,
        "parse_args",
        lambda argv=None: stage_unity_host_report.argparse.Namespace(
            source_dir=str(source),
            dest_root=str(dest_root),
            host_label="windows-lab-a",
            host_platform="windows",
            hostname="win-lab-a",
            host_system="Windows",
            host_release="11",
            host_machine="x86_64",
            host_python_version="3.12.9",
            host_fingerprint_seed="seed-a",
            overwrite=False,
        ),
    )

    rc = stage_unity_host_report.main()

    assert rc == 0
    manifest = json.loads((dest_root / "windows-lab-a" / stage_unity_host_report.HOST_MANIFEST).read_text(encoding="utf-8"))
    assert manifest["hostname"] == "win-lab-a"
    assert manifest["system"] == "Windows"
    assert manifest["machine"] == "x86_64"
    assert manifest["host_identity_source"] == "overridden"
    assert len(manifest["host_fingerprint"]) == 64


def test_export_and_import_unity_host_report_archive(tmp_path: Path, monkeypatch) -> None:
    host_root = tmp_path / "hosts"
    host_dir = host_root / "windows-box"
    host_dir.mkdir(parents=True)
    _write_source_reports(host_dir, "windows")
    manifest = {
        "host_label": "windows-box",
        "host_platform": "windows",
        "required_files": list(stage_unity_host_report.required_files_for("windows")),
        "unity_workflow_status": "pass",
        "unity_runtime_status": "pass",
        "unity_orientation_status": "pass",
        "unity_startup_probe_status": "pass",
        "unity_install_status": "pass",
        "host_fingerprint": "windows-box-fingerprint",
        "report_digest_sha256": "windows-box-digest",
    }
    (host_dir / stage_unity_host_report.HOST_MANIFEST).write_text(json.dumps(manifest) + "\n", encoding="utf-8")
    (host_dir / stage_unity_host_report.HOST_MANIFEST_MD).write_text("# manifest\n", encoding="utf-8")

    archive_dir = tmp_path / "dist"
    export_args = export_unity_host_report.argparse.Namespace(host_label="windows-box", host_root=str(host_root), out_dir=str(archive_dir))
    monkeypatch.setattr(export_unity_host_report.load_local_env, "load", lambda: None)
    monkeypatch.setattr(export_unity_host_report, "parse_args", lambda argv=None: export_args)

    assert export_unity_host_report.main() == 0
    archive = archive_dir / "windows-box.zip"
    assert archive.is_file()
    with zipfile.ZipFile(archive) as zf:
        assert "windows-box/unity_install_smoke_windows.json" in zf.namelist()

    import_host_root = tmp_path / "imported_hosts"
    report_dir = tmp_path / "reports"
    report_dir.mkdir()
    (report_dir / "unity_runtime_verification.json").write_text('{"overall_status":"pass","lanes":[{"platform":"EditorMethod","launch":"login-shell"}]}\n', encoding="utf-8")
    (report_dir / "unity_orientation_verification.json").write_text('{"status":"pass","scene":"Assets/Scenes/OrientationVerification.unity"}\n', encoding="utf-8")
    (report_dir / "unity_startup_probe.json").write_text('{"status":"pass"}\n', encoding="utf-8")
    (report_dir / "unity_csharp_bridge_probe.json").write_text('{"overall_status":"pass","native_library":"/tmp/libfastdis.dylib"}\n', encoding="utf-8")
    (report_dir / "unity_install_smoke_macos.json").write_text('{"schema":"fastdis.unity_install_smoke.v1","status":"pass","host_platform":"macos","repo_root":"/tmp/repo"}\n', encoding="utf-8")
    (report_dir / "unity_workflow_report.json").write_text('{"requested_version":"6000.5"}\n', encoding="utf-8")
    import_args = import_unity_host_report.argparse.Namespace(
        archive=str(archive),
        host_root=str(import_host_root),
        report_dir=str(report_dir),
        overwrite=False,
        checksum=None,
    )
    monkeypatch.setattr(import_unity_host_report.load_local_env, "load", lambda: None)
    monkeypatch.setattr(import_unity_host_report, "parse_args", lambda argv=None: import_args)

    assert import_unity_host_report.main() == 0
    assert (import_host_root / "windows-box" / "unity_install_smoke_windows.json").is_file()
    assert (report_dir / "unity_install_smoke_windows.json").is_file()
    assert (report_dir / "unity_install_matrix.json").is_file()
    assert (report_dir / "unity_host_matrix.json").is_file()
    assert (report_dir / "unity_signoff_report.json").is_file()
    workflow = json.loads((report_dir / "unity_workflow_report.json").read_text(encoding="utf-8"))
    assert workflow["unity_install_matrix_status"] == "incomplete"
    assert workflow["unity_host_matrix_status"] == "incomplete"
    signoff = json.loads((report_dir / "unity_signoff_report.json").read_text(encoding="utf-8"))
    assert signoff["install_matrix_status"] == "cross-host-incomplete"
    assert signoff["host_matrix_status"] == "cross-host-incomplete"
