from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import stage_unity_host_report
import sync_unity_host_reports


def _write_host_bundle(root: Path, host_label: str, host_platform: str) -> None:
    host_dir = root / host_label
    host_dir.mkdir(parents=True)
    (host_dir / f"unity_install_smoke_{host_platform}.json").write_text(
        json.dumps({"schema": "fastdis.unity_install_smoke.v1", "status": "pass", "host_platform": host_platform}) + "\n",
        encoding="utf-8",
    )
    (host_dir / f"unity_install_smoke_{host_platform}.md").write_text("# install\n", encoding="utf-8")
    manifest = {"host_label": host_label, "host_platform": host_platform}
    (host_dir / stage_unity_host_report.HOST_MANIFEST).write_text(json.dumps(manifest) + "\n", encoding="utf-8")
    (host_dir / stage_unity_host_report.HOST_MANIFEST_MD).write_text("# manifest\n", encoding="utf-8")


def test_sync_host_reports_refreshes_aggregate_artifacts(tmp_path: Path, monkeypatch) -> None:
    host_root = tmp_path / "hosts"
    report_dir = tmp_path / "reports"
    host_root.mkdir()
    report_dir.mkdir()
    _write_host_bundle(host_root, "mac-host", "macos")
    _write_host_bundle(host_root, "win-host", "windows")
    refreshed = (
        report_dir / "unity_install_matrix.json",
        report_dir / "unity_install_matrix.md",
        report_dir / "unity_host_matrix.json",
        report_dir / "unity_host_matrix.md",
        report_dir / "unity_workflow_report.json",
        report_dir / "unity_workflow_report.md",
        report_dir / "unity_signoff_report.json",
        report_dir / "unity_signoff_report.md",
    )
    monkeypatch.setattr(sync_unity_host_reports.load_local_env, "load", lambda: None)
    monkeypatch.setattr(
        sync_unity_host_reports.import_unity_host_report,
        "refresh_aggregate_reports",
        lambda _report_dir, _host_root: refreshed,
    )
    monkeypatch.setattr(
        sync_unity_host_reports,
        "parse_args",
        lambda argv=None: sync_unity_host_reports.argparse.Namespace(host_root=str(host_root), report_dir=str(report_dir)),
    )

    assert sync_unity_host_reports.main() == 0
    assert (report_dir / "unity_install_smoke_macos.json").is_file()
    assert (report_dir / "unity_install_smoke_windows.json").is_file()


def test_sync_host_reports_rejects_duplicate_platforms(tmp_path: Path, monkeypatch) -> None:
    host_root = tmp_path / "hosts"
    report_dir = tmp_path / "reports"
    host_root.mkdir()
    report_dir.mkdir()
    _write_host_bundle(host_root, "win-a", "windows")
    _write_host_bundle(host_root, "win-b", "windows")
    monkeypatch.setattr(sync_unity_host_reports.load_local_env, "load", lambda: None)
    monkeypatch.setattr(
        sync_unity_host_reports,
        "parse_args",
        lambda argv=None: sync_unity_host_reports.argparse.Namespace(host_root=str(host_root), report_dir=str(report_dir)),
    )

    try:
        sync_unity_host_reports.main()
    except FileNotFoundError:
        raise
    except ValueError as exc:
        assert "Duplicate Unity host bundle for platform windows" in str(exc)
    else:
        raise AssertionError("expected duplicate platform validation to fail")
