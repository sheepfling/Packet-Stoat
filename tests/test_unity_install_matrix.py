from __future__ import annotations

import json
from pathlib import Path

import sys


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import run_unity_install_matrix


def _write_report(root: Path, host: str, *, status: str = "pass") -> None:
    payload = {
        "schema": "fastdis.unity_install_smoke.v1",
        "status": status,
        "host_platform": host,
        "detail": status,
        "unity_version": "6000.5.0f1",
        "manifest_git_url": "file:///tmp/fake.git?path=packages/unity/com.sheepfling.fastdis",
        "package_cache_locations": ["Library/PackageCache/com.sheepfling.fastdis@demo"],
        "plugin_inventory": {"macos": True, "windows": True, "linux": True},
        "failure_stage": "none" if status == "pass" else "host-startup",
        "failure_reason": "none" if status == "pass" else "project-import-never-started",
    }
    (root / f"unity_install_smoke_{host}.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def test_build_report_marks_incomplete_when_hosts_missing(tmp_path: Path) -> None:
    _write_report(tmp_path, "macos")

    report = run_unity_install_matrix.build_report(tmp_path)

    assert report["overall_status"] == "cross-host-incomplete"
    assert report["ready_hosts"] == ["macos"]
    assert report["missing_hosts"] == ["windows", "linux"]


def test_build_report_marks_ready_when_all_hosts_pass(tmp_path: Path) -> None:
    for host in run_unity_install_matrix.REQUIRED_HOSTS:
        _write_report(tmp_path, host)

    report = run_unity_install_matrix.build_report(tmp_path)

    assert report["overall_status"] == "cross-host-ready"
    assert report["ready_hosts"] == ["macos", "windows", "linux"]
    assert report["missing_hosts"] == []


def test_build_report_marks_failed_when_present_host_fails(tmp_path: Path) -> None:
    _write_report(tmp_path, "macos")
    _write_report(tmp_path, "windows", status="fail")

    report = run_unity_install_matrix.build_report(tmp_path)

    assert report["overall_status"] == "cross-host-failed"
    statuses = {row["host"]: row["status"] for row in report["rows"]}
    assert statuses["windows"] == "fail"
    failed_row = next(row for row in report["rows"] if row["host"] == "windows")
    assert failed_row["failure_stage"] == "host-startup"


def test_render_markdown_includes_failure_stage_and_reason(tmp_path: Path) -> None:
    _write_report(tmp_path, "macos")
    _write_report(tmp_path, "windows", status="fail")

    markdown = run_unity_install_matrix.render_markdown(run_unity_install_matrix.build_report(tmp_path))

    assert "stage=host-startup reason=project-import-never-started" in markdown


def test_host_row_derives_failure_stage_from_project_state_when_missing(tmp_path: Path) -> None:
    payload = {
        "schema": "fastdis.unity_install_smoke.v1",
        "status": "fail",
        "host_platform": "macos",
        "detail": "timed out",
        "project_state": {"library_exists": False, "package_cache_exists": False, "script_assemblies_exists": False},
        "package_cache_locations": [],
    }
    (tmp_path / "unity_install_smoke_macos.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    row = run_unity_install_matrix.host_row(tmp_path, "macos")

    assert row["failure_stage"] == "host-startup"
    assert row["failure_reason"] == "project-import-never-started"


def test_main_writes_matrix_artifacts(tmp_path: Path, monkeypatch) -> None:
    reports = tmp_path / "reports"
    out = tmp_path / "out"
    reports.mkdir()
    for host in run_unity_install_matrix.REQUIRED_HOSTS:
        _write_report(reports, host)

    monkeypatch.setattr(
        run_unity_install_matrix,
        "parse_args",
        lambda argv=None: run_unity_install_matrix.argparse.Namespace(report_dir=reports, out_dir=out),
    )
    monkeypatch.setattr(run_unity_install_matrix.load_local_env, "load", lambda: None)

    rc = run_unity_install_matrix.main()

    assert rc == 0
    payload = json.loads((out / "unity_install_matrix.json").read_text(encoding="utf-8"))
    assert payload["overall_status"] == "cross-host-ready"
    markdown = (out / "unity_install_matrix.md").read_text(encoding="utf-8")
    assert "Unity Install Signoff Matrix" in markdown
