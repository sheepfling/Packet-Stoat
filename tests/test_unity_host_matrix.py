from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import run_unity_host_matrix
import stage_unity_host_report


def _write_host_bundle(root: Path, host_label: str, host_platform: str, *, install_status: str = "pass", startup_probe_status: str = "pass") -> None:
    host_dir = root / host_label
    host_dir.mkdir(parents=True)
    manifest = {
        "host_label": host_label,
        "host_platform": host_platform,
        "unity_workflow_status": "pass",
        "unity_runtime_status": "pass",
        "unity_orientation_status": "pass",
        "unity_startup_probe_status": startup_probe_status,
        "unity_install_status": install_status,
        "host_fingerprint": f"{host_label}-fingerprint",
        "report_digest_sha256": f"{host_label}-digest",
    }
    (host_dir / stage_unity_host_report.HOST_MANIFEST).write_text(json.dumps(manifest) + "\n", encoding="utf-8")
    (host_dir / stage_unity_host_report.HOST_MANIFEST_MD).write_text("# manifest\n", encoding="utf-8")


def test_build_report_marks_incomplete_until_all_platforms_ready(tmp_path: Path) -> None:
    _write_host_bundle(tmp_path, "mac-host", "macos")
    _write_host_bundle(tmp_path, "win-host", "windows")

    report = run_unity_host_matrix.build_report(tmp_path)

    assert report["overall_status"] == "cross-host-incomplete"
    assert report["ready_platforms"] == ["macos", "windows"]
    assert report["missing_platforms"] == ["linux"]


def test_build_report_marks_ready_when_all_platforms_ready(tmp_path: Path) -> None:
    for label, platform_name in (("mac-host", "macos"), ("win-host", "windows"), ("linux-host", "linux")):
        _write_host_bundle(tmp_path, label, platform_name)

    report = run_unity_host_matrix.build_report(tmp_path)

    assert report["overall_status"] == "cross-host-ready"
    assert report["ready_platforms"] == ["linux", "macos", "windows"] or report["ready_platforms"] == ["macos", "windows", "linux"]


def test_build_report_marks_failed_when_no_host_ready(tmp_path: Path) -> None:
    _write_host_bundle(tmp_path, "broken-win", "windows", install_status="fail")

    report = run_unity_host_matrix.build_report(tmp_path)

    assert report["overall_status"] == "cross-host-failed"


def test_build_report_requires_startup_probe_pass(tmp_path: Path) -> None:
    _write_host_bundle(tmp_path, "mac-host", "macos", startup_probe_status="fail")

    report = run_unity_host_matrix.build_report(tmp_path)

    assert report["overall_status"] == "cross-host-failed"
    assert report["hosts"][0]["startup_probe_ok"] is False


def test_main_writes_host_matrix(tmp_path: Path, monkeypatch) -> None:
    host_root = tmp_path / "hosts"
    out_dir = tmp_path / "out"
    host_root.mkdir()
    for label, platform_name in (("mac-host", "macos"), ("win-host", "windows"), ("linux-host", "linux")):
        _write_host_bundle(host_root, label, platform_name)
    monkeypatch.setattr(run_unity_host_matrix.load_local_env, "load", lambda: None)
    monkeypatch.setattr(
        run_unity_host_matrix,
        "parse_args",
        lambda argv=None: run_unity_host_matrix.argparse.Namespace(host_root=str(host_root), out_dir=str(out_dir)),
    )

    assert run_unity_host_matrix.main() == 0
    payload = json.loads((out_dir / "unity_host_matrix.json").read_text(encoding="utf-8"))
    assert payload["overall_status"] == "cross-host-ready"
