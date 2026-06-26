from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import run_unity_signoff
import stage_unity_host_report


def write_ready_host_manifest(host_root: Path, host_label: str, host_platform: str) -> None:
    host_dir = host_root / host_label
    host_dir.mkdir()
    (host_dir / stage_unity_host_report.HOST_MANIFEST).write_text(
        json.dumps(
            {
                "host_label": host_label,
                "host_platform": host_platform,
                "unity_workflow_status": "pass",
                "unity_runtime_status": "pass",
                "unity_orientation_status": "pass",
                "unity_startup_probe_status": "pass",
                "unity_install_status": "fail",
                "host_fingerprint": f"{host_label}-fingerprint",
                "report_digest_sha256": f"{host_label}-digest",
            }
        )
        + "\n",
        encoding="utf-8",
    )


def test_evaluate_marks_not_ready_when_install_matrix_incomplete(tmp_path: Path) -> None:
    report_dir = tmp_path / "reports"
    host_root = tmp_path / "hosts"
    report_dir.mkdir()
    host_root.mkdir()
    (report_dir / "unity_runtime_verification.json").write_text(
        json.dumps(
            {
                "phase1_exit_criteria": [
                    {"name": "Native library stages and loads in Unity", "status": "complete"},
                    {"name": "Replay demo moves GameObjects", "status": "complete"},
                    {"name": "UDP demo receives live Entity State traffic", "status": "complete"},
                ]
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (report_dir / "unity_workflow_report.json").write_text(
        json.dumps(
            {
                "unity_workflow_status": "pass",
                "unity_native_status": "pass",
                "unity_runtime_status": "pass",
                "unity_orientation_status": "pass",
                "unity_startup_probe_status": "pass",
                "unity_install_status": "fail",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (report_dir / "unity_runtime_verification.json").write_text(
        json.dumps(
            {
                "phase1_exit_criteria": [
                    {"name": "Native library stages and loads in Unity", "status": "complete"},
                    {"name": "Replay demo moves GameObjects", "status": "complete"},
                    {"name": "UDP demo receives live Entity State traffic", "status": "complete"},
                ]
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (report_dir / "unity_install_smoke.json").write_text(json.dumps({"status": "fail"}) + "\n", encoding="utf-8")
    (report_dir / "unity_runtime_verification.md").write_text("# runtime\n", encoding="utf-8")

    report = run_unity_signoff.evaluate(report_dir, host_root)

    assert report["overall_status"] == "not-fully-signed-off"


def test_evaluate_marks_ready_when_all_exit_criteria_are_complete(tmp_path: Path) -> None:
    report_dir = tmp_path / "reports"
    host_root = tmp_path / "hosts"
    report_dir.mkdir()
    host_root.mkdir()
    (report_dir / "unity_runtime_verification.json").write_text(
        json.dumps(
            {
                "phase1_exit_criteria": [
                    {"name": "Native library stages and loads in Unity", "status": "complete"},
                    {"name": "Replay demo moves GameObjects", "status": "complete"},
                    {"name": "UDP demo receives live Entity State traffic", "status": "complete"},
                ]
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (report_dir / "unity_workflow_report.json").write_text(
        json.dumps(
            {
                "unity_workflow_status": "pass",
                "unity_native_status": "pass",
                "unity_runtime_status": "pass",
                "unity_orientation_status": "pass",
                "unity_startup_probe_status": "pass",
                "unity_install_status": "pass",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (report_dir / "unity_runtime_verification.json").write_text(
        json.dumps(
            {
                "phase1_exit_criteria": [
                    {"name": "Native library stages and loads in Unity", "status": "complete"},
                    {"name": "Replay demo moves GameObjects", "status": "complete"},
                    {"name": "UDP demo receives live Entity State traffic", "status": "complete"},
                ]
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (report_dir / "unity_install_smoke.json").write_text(json.dumps({"status": "pass"}) + "\n", encoding="utf-8")
    (report_dir / "unity_runtime_verification.md").write_text("# runtime\n", encoding="utf-8")

    report = run_unity_signoff.evaluate(report_dir, host_root)

    assert report["overall_status"] == "ready"


def test_evaluate_marks_ready_when_mac_install_is_pass_even_if_host_matrix_is_not_ready(tmp_path: Path) -> None:
    report_dir = tmp_path / "reports"
    host_root = tmp_path / "hosts"
    report_dir.mkdir()
    host_root.mkdir()
    (report_dir / "unity_runtime_verification.json").write_text(
        json.dumps(
            {
                "phase1_exit_criteria": [
                    {"name": "Native library stages and loads in Unity", "status": "complete"},
                    {"name": "Replay demo moves GameObjects", "status": "complete"},
                    {"name": "UDP demo receives live Entity State traffic", "status": "complete"},
                ]
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (report_dir / "unity_workflow_report.json").write_text(
        json.dumps(
            {
                "unity_workflow_status": "pass",
                "unity_native_status": "pass",
                "unity_runtime_status": "pass",
                "unity_orientation_status": "pass",
                "unity_startup_probe_status": "pass",
                "unity_install_status": "pass",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (report_dir / "unity_runtime_verification.json").write_text(
        json.dumps(
            {
                "phase1_exit_criteria": [
                    {"name": "Native library stages and loads in Unity", "status": "complete"},
                    {"name": "Replay demo moves GameObjects", "status": "complete"},
                    {"name": "UDP demo receives live Entity State traffic", "status": "complete"},
                ]
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (report_dir / "unity_install_smoke.json").write_text(json.dumps({"status": "pass"}) + "\n", encoding="utf-8")
    (report_dir / "unity_runtime_verification.md").write_text("# runtime\n", encoding="utf-8")
    host_dir = host_root / "mac-host"
    host_dir.mkdir()
    (host_dir / stage_unity_host_report.HOST_MANIFEST).write_text(
        json.dumps(
            {
                "host_label": "mac-host",
                "host_platform": "macos",
                "unity_workflow_status": "pass",
                "unity_runtime_status": "pass",
                "unity_orientation_status": "pass",
                "unity_startup_probe_status": "pass",
                "unity_install_status": "pass",
                "host_fingerprint": "mac-host-fingerprint",
                "report_digest_sha256": "mac-host-digest",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    report = run_unity_signoff.evaluate(report_dir, host_root)
    statuses = {item["name"]: item["status"] for item in report["criteria"]}

    assert report["overall_status"] == "ready"
    assert report["host_matrix_status"] == "cross-host-incomplete"
    assert statuses["Git/UPM install works on macOS"] == "complete"


def test_main_writes_signoff_report(tmp_path: Path, monkeypatch) -> None:
    report_dir = tmp_path / "reports"
    host_root = tmp_path / "hosts"
    report_dir.mkdir()
    host_root.mkdir()
    (report_dir / "unity_runtime_verification.json").write_text(
        json.dumps(
            {
                "phase1_exit_criteria": [
                    {"name": "Native library stages and loads in Unity", "status": "complete"},
                    {"name": "Replay demo moves GameObjects", "status": "complete"},
                    {"name": "UDP demo receives live Entity State traffic", "status": "complete"},
                ]
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (report_dir / "unity_workflow_report.json").write_text(
        json.dumps(
            {
                "unity_workflow_status": "pass",
                "unity_native_status": "pass",
                "unity_runtime_status": "pass",
                "unity_orientation_status": "pass",
                "unity_startup_probe_status": "pass",
                "unity_install_status": "pass",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (report_dir / "unity_runtime_verification.json").write_text(
        json.dumps(
            {
                "phase1_exit_criteria": [
                    {"name": "Native library stages and loads in Unity", "status": "complete"},
                    {"name": "Replay demo moves GameObjects", "status": "complete"},
                    {"name": "UDP demo receives live Entity State traffic", "status": "complete"},
                ]
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (report_dir / "unity_install_smoke.json").write_text(json.dumps({"status": "pass"}) + "\n", encoding="utf-8")
    (report_dir / "unity_runtime_verification.md").write_text("# runtime\n", encoding="utf-8")
    out_dir = tmp_path / "out"
    monkeypatch.setattr(run_unity_signoff.load_local_env, "load", lambda: None)
    monkeypatch.setattr(
        run_unity_signoff,
        "parse_args",
        lambda argv=None: run_unity_signoff.argparse.Namespace(report_dir=str(report_dir), host_root=str(host_root), out_dir=str(out_dir)),
    )

    assert run_unity_signoff.main() == 0
    payload = json.loads((out_dir / "unity_signoff_report.json").read_text(encoding="utf-8"))
    assert payload["overall_status"] == "ready"


def test_evaluate_reads_host_matrix_status_from_staged_host_root(tmp_path: Path) -> None:
    report_dir = tmp_path / "reports"
    host_root = tmp_path / "hosts"
    report_dir.mkdir()
    host_root.mkdir()
    (report_dir / "unity_runtime_verification.json").write_text(
        json.dumps(
            {
                "phase1_exit_criteria": [
                    {"name": "Native library stages and loads in Unity", "status": "complete"},
                    {"name": "Replay demo moves GameObjects", "status": "complete"},
                    {"name": "UDP demo receives live Entity State traffic", "status": "complete"},
                ]
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (report_dir / "unity_workflow_report.json").write_text(
        json.dumps(
            {
                "unity_workflow_status": "pass",
                "unity_native_status": "pass",
                "unity_runtime_status": "pass",
                "unity_orientation_status": "pass",
                "unity_startup_probe_status": "pass",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (report_dir / "unity_install_smoke.json").write_text(json.dumps({"status": "pass"}) + "\n", encoding="utf-8")
    (report_dir / "unity_runtime_verification.md").write_text("# runtime\n", encoding="utf-8")
    host_dir = host_root / "mac-host"
    host_dir.mkdir()
    (host_dir / stage_unity_host_report.HOST_MANIFEST).write_text(
        json.dumps(
            {
                "host_label": "mac-host",
                "host_platform": "macos",
                "unity_workflow_status": "pass",
                "unity_runtime_status": "pass",
                "unity_orientation_status": "pass",
                "unity_startup_probe_status": "pass",
                "unity_install_status": "pass",
                "host_fingerprint": "mac-host-fingerprint",
                "report_digest_sha256": "mac-host-digest",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    report = run_unity_signoff.evaluate(report_dir, host_root)

    assert report["host_matrix_status"] == "cross-host-incomplete"


def test_evaluate_uses_runtime_phase1_criteria_for_replay_and_udp(tmp_path: Path) -> None:
    report_dir = tmp_path / "reports"
    host_root = tmp_path / "hosts"
    report_dir.mkdir()
    host_root.mkdir()
    (report_dir / "unity_runtime_verification.json").write_text(
        json.dumps(
            {
                "phase1_exit_criteria": [
                    {"name": "Native library stages and loads in Unity", "status": "complete"},
                    {"name": "Replay demo moves GameObjects", "status": "incomplete"},
                    {"name": "UDP demo receives live Entity State traffic", "status": "complete"},
                ]
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (report_dir / "unity_runtime_verification.md").write_text("# runtime\n", encoding="utf-8")
    (report_dir / "unity_workflow_report.json").write_text(
        json.dumps(
            {
                "unity_workflow_status": "pass",
                "unity_native_status": "pass",
                "unity_runtime_status": "pass",
                "unity_orientation_status": "pass",
                "unity_startup_probe_status": "pass",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (report_dir / "unity_install_matrix.json").write_text(json.dumps({"overall_status": "cross-host-ready"}) + "\n", encoding="utf-8")

    report = run_unity_signoff.evaluate(report_dir, host_root)
    statuses = {item["name"]: item["status"] for item in report["criteria"]}

    assert statuses["Replay demo moves GameObjects"] == "incomplete"
    assert statuses["UDP demo receives live Entity State traffic"] == "complete"
