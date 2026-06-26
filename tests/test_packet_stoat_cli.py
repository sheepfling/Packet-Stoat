from __future__ import annotations

from collections.abc import Sequence

import fastdis.cli as cli


def test_cli_doctor_prints_three_lanes(capsys) -> None:
    rc = cli.main(["doctor"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "FastDIS doctor" in out
    assert "python:" in out
    assert "pdu-json:" in out
    assert "replay-json:" in out
    assert "simtest:" in out
    assert "enums:" in out
    assert "unreal:" in out
    assert "godot:" in out
    assert "install-smoke" in out
    assert "grill-baseline-init" in out
    assert "grill-benchmark" in out
    assert "adopt-install-smoke" in out
    assert "stage-host-report" in out
    assert "export-host-report" in out
    assert "export-host-handoff" in out
    assert "import-host-report" in out
    assert "sync-host-reports" in out
    assert "host-matrix" in out
    assert "capture-host-report" in out
    assert "demo" in out
    assert "startup-probe" in out
    assert "parity-check" in out
    assert "signoff" in out
    assert "cross-engine-equivalence" in out
    assert "head-to-head-benchmark" in out
    assert "grill-baseline-init" in out
    assert "grill-import-smoke" in out
    assert "benchmark-refresh" in out
    assert "benchmark-matrix" in out
    assert "benchmark-coverage" in out
    assert "benchmark-scenario-contract" in out
    assert "benchmark-surface-claims" in out
    assert "benchmark-audit" in out
    assert "benchmark-claim-summary" in out
    assert "benchmark-competitor-summary" in out
    assert "benchmark-contract-check" in out
    assert "competitor-handoff" in out
    assert "competitor-handoff-check" in out
    assert "import-competitor-handoff" in out
    assert "orient:" in out
    assert "lattice:" in out


def test_cli_support_keeps_fastdis_surface(capsys) -> None:
    rc = cli.main(["support"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "FASTDIS support surface" in out
    assert "Protocol versions:" in out
    assert "PDU families:" in out


def test_cli_routes_python_tools(monkeypatch) -> None:
    calls: list[list[str]] = []

    def fake_run(cmd: Sequence[str]) -> int:
        calls.append(list(cmd))
        return 0

    monkeypatch.setattr(cli, "_run", fake_run)

    assert cli.main(["send-entity", "--count", "3"]) == 0
    assert cli.main(["recv", "--max-packets", "3"]) == 0
    assert cli.main(["replay-send", "capture.fastdispkt"]) == 0

    assert calls[0][1:3] == ["-m", "fastdis.tools.send_entity"]
    assert calls[0][-2:] == ["--count", "3"]
    assert calls[1][1:3] == ["-m", "fastdis.tools.recv"]
    assert calls[2][1:3] == ["-m", "fastdis.tools.replay_send"]


def test_cli_routes_json_tools(monkeypatch) -> None:
    calls: list[list[str]] = []

    def fake_run(cmd: Sequence[str]) -> int:
        calls.append(list(cmd))
        return 0

    monkeypatch.setattr(cli, "_run", fake_run)

    assert cli.main(["pdu", "to-json", "packet.bin", "--out", "packet.json"]) == 0
    assert cli.main(["replay", "roundtrip", "capture.fastdispkt", "--out", "roundtrip.fastdispkt"]) == 0

    assert calls[0][1:3] == ["-m", "fastdis.tools.pdu_json"]
    assert calls[0][-4:] == ["to-json", "packet.bin", "--out", "packet.json"]
    assert calls[1][1:3] == ["-m", "fastdis.tools.replay_json"]
    assert calls[1][-4:] == ["roundtrip", "capture.fastdispkt", "--out", "roundtrip.fastdispkt"]


def test_cli_routes_simtest_tools(monkeypatch) -> None:
    calls: list[list[str]] = []

    def fake_run(cmd: Sequence[str]) -> int:
        calls.append(list(cmd))
        return 0

    monkeypatch.setattr(cli, "_run", fake_run)

    assert cli.main(["simtest", "compare", "run", "baseline", "--report", "report"]) == 0

    assert calls[0][1:3] == ["-m", "fastdis.tools.simtest"]
    assert calls[0][-5:] == ["compare", "run", "baseline", "--report", "report"]


def test_cli_routes_enum_tools(capsys) -> None:
    assert cli.main(["enums", "lookup", "force_id", "1"]) == 0

    out = capsys.readouterr().out
    assert '"family": "force_id"' in out
    assert '"label": "Friendly"' in out


def test_cli_routes_engine_workflows(monkeypatch) -> None:
    calls: list[list[str]] = []

    def fake_run(cmd: Sequence[str]) -> int:
        calls.append(list(cmd))
        return 0

    monkeypatch.setattr(cli, "_run", fake_run)

    assert cli.main(["engine", "unreal", "doctor", "--engine-version", "5.8"]) == 0
    assert cli.main(["engine", "unreal", "grill-baseline-init", "--engine-version", "5.8"]) == 0
    assert cli.main(["engine", "unreal", "grill-benchmark", "--allow-sample-grill"]) == 0
    assert cli.main(["engine", "godot", "verify", "--dry-run"]) == 0
    assert cli.main(["engine", "unity", "doctor", "--unity-version", "6000.5"]) == 0

    assert calls[0][-3:] == ["doctor", "--engine-version", "5.8"]
    assert calls[0][-4].endswith("tools/unreal_workflow.py")
    assert calls[1][-3:] == ["grill-baseline-init", "--engine-version", "5.8"]
    assert calls[1][-4].endswith("tools/unreal_workflow.py")
    assert calls[2][-2:] == ["grill-benchmark", "--allow-sample-grill"]
    assert calls[2][-3].endswith("tools/unreal_workflow.py")
    assert calls[3][-2:] == ["verify", "--dry-run"]
    assert calls[3][-3].endswith("tools/godot_workflow.py")
    assert calls[4][-3:] == ["doctor", "--unity-version", "6000.5"]
    assert calls[4][-4].endswith("tools/unity_workflow.py")


def test_cli_routes_unity_install_matrix_workflows(monkeypatch) -> None:
    calls: list[list[str]] = []

    def fake_run(cmd: Sequence[str]) -> int:
        calls.append(list(cmd))
        return 0

    monkeypatch.setattr(cli, "_run", fake_run)

    assert cli.main(["engine", "unity", "install-smoke", "--unity-version", "6000.5"]) == 0
    assert cli.main(["engine", "unity", "adopt-install-smoke", "--host", "windows", "--report", "windows_report.json"]) == 0

    assert calls[0][-3:] == ["install-smoke", "--unity-version", "6000.5"]
    assert calls[0][-4].endswith("tools/unity_workflow.py")
    assert calls[1][-5:] == ["adopt-install-smoke", "--host", "windows", "--report", "windows_report.json"]
    assert calls[1][-6].endswith("tools/unity_workflow.py")


def test_cli_routes_unity_demo_workflow(monkeypatch) -> None:
    calls: list[list[str]] = []

    def fake_run(cmd: Sequence[str]) -> int:
        calls.append(list(cmd))
        return 0

    monkeypatch.setattr(cli, "_run", fake_run)

    assert cli.main(["engine", "unity", "demo", "--unity-version", "6000.5", "--dry-run"]) == 0

    assert calls[0][-4:] == ["demo", "--unity-version", "6000.5", "--dry-run"]
    assert calls[0][-5].endswith("tools/unity_workflow.py")


def test_cli_routes_unity_host_bundle_workflows(monkeypatch) -> None:
    calls: list[list[str]] = []

    def fake_run(cmd: Sequence[str]) -> int:
        calls.append(list(cmd))
        return 0

    monkeypatch.setattr(cli, "_run", fake_run)

    assert cli.main(["engine", "unity", "stage-host-report", "--overwrite"]) == 0
    assert cli.main(["engine", "unity", "export-host-report", "windows-demo"]) == 0
    assert cli.main(["engine", "unity", "export-host-handoff", "--out-dir", "handoff"]) == 0
    assert cli.main(["engine", "unity", "import-host-report", "windows-demo.zip"]) == 0
    assert cli.main(["engine", "unity", "sync-host-reports", "--host-root", "unity_hosts"]) == 0
    assert cli.main(["engine", "unity", "host-matrix", "--host-root", "unity_hosts"]) == 0
    assert cli.main(["engine", "unity", "signoff", "--report-dir", "reports"]) == 0
    assert cli.main(["engine", "unity", "capture-host-report", "--skip-full", "--skip-export"]) == 0

    assert calls[0][-2:] == ["stage-host-report", "--overwrite"]
    assert calls[0][-3].endswith("tools/unity_workflow.py")
    assert calls[1][-2:] == ["export-host-report", "windows-demo"]
    assert calls[1][-3].endswith("tools/unity_workflow.py")
    assert calls[2][-3:] == ["export-host-handoff", "--out-dir", "handoff"]
    assert calls[2][-4].endswith("tools/unity_workflow.py")
    assert calls[3][-2:] == ["import-host-report", "windows-demo.zip"]
    assert calls[3][-3].endswith("tools/unity_workflow.py")
    assert calls[4][-3:] == ["sync-host-reports", "--host-root", "unity_hosts"]
    assert calls[4][-4].endswith("tools/unity_workflow.py")
    assert calls[5][-3:] == ["host-matrix", "--host-root", "unity_hosts"]
    assert calls[5][-4].endswith("tools/unity_workflow.py")
    assert calls[6][-3:] == ["signoff", "--report-dir", "reports"]
    assert calls[6][-4].endswith("tools/unity_workflow.py")
    assert calls[7][-3:] == ["capture-host-report", "--skip-full", "--skip-export"]
    assert calls[7][-4].endswith("tools/unity_workflow.py")


def test_cli_routes_unity_proof_report_workflows(monkeypatch) -> None:
    calls: list[list[str]] = []

    def fake_run(cmd: Sequence[str]) -> int:
        calls.append(list(cmd))
        return 0

    monkeypatch.setattr(cli, "_run", fake_run)

    assert cli.main(["engine", "unity", "cross-engine-equivalence", "--out-dir", "reports"]) == 0
    assert cli.main(["engine", "unity", "head-to-head-benchmark", "--grill", "baseline.json"]) == 0

    assert calls[0][-3:] == ["cross-engine-equivalence", "--out-dir", "reports"]
    assert calls[0][-4].endswith("tools/unity_workflow.py")
    assert calls[1][-3:] == ["head-to-head-benchmark", "--grill", "baseline.json"]
    assert calls[1][-4].endswith("tools/unity_workflow.py")


def test_cli_routes_unity_grill_baseline_init(monkeypatch) -> None:
    calls: list[list[str]] = []

    def fake_run(cmd: Sequence[str]) -> int:
        calls.append(list(cmd))
        return 0

    monkeypatch.setattr(cli, "_run", fake_run)

    assert cli.main(["engine", "unity", "grill-baseline-init", "--unity-version", "6000.5.0f1"]) == 0

    assert calls[0][-3:] == ["grill-baseline-init", "--unity-version", "6000.5.0f1"]
    assert calls[0][-4].endswith("tools/unity_workflow.py")


def test_cli_routes_unity_grill_import_smoke(monkeypatch) -> None:
    calls: list[list[str]] = []

    def fake_run(cmd: Sequence[str]) -> int:
        calls.append(list(cmd))
        return 0

    monkeypatch.setattr(cli, "_run", fake_run)

    assert cli.main(["engine", "unity", "grill-import-smoke", "--unity-version", "6000.5"]) == 0

    assert calls[0][-3:] == ["grill-import-smoke", "--unity-version", "6000.5"]
    assert calls[0][-4].endswith("tools/unity_workflow.py")


def test_cli_routes_lattice_and_release_workflows(monkeypatch) -> None:
    calls: list[list[str]] = []

    def fake_run(cmd: Sequence[str]) -> int:
        calls.append(list(cmd))
        return 0

    monkeypatch.setattr(cli, "_run", fake_run)

    assert cli.main(["lattice", "sdk-check"]) == 0
    assert cli.main(["lattice", "doctor", "--format", "json"]) == 0
    assert cli.main(["release", "alpha4-1-gap"]) == 0
    assert cli.main(["release", "check", "--quick"]) == 0
    assert cli.main(["release", "deliverables", "--format", "json"]) == 0
    assert cli.main(["release", "benchmark-refresh", "--skip-unity-compare"]) == 0
    assert cli.main(["release", "benchmark-matrix"]) == 0
    assert cli.main(["release", "benchmark-coverage"]) == 0
    assert cli.main(["release", "benchmark-scenario-contract"]) == 0
    assert cli.main(["release", "benchmark-surface-claims"]) == 0
    assert cli.main(["release", "benchmark-audit", "--fail-incomplete"]) == 0
    assert cli.main(["release", "benchmark-claim-summary"]) == 0
    assert cli.main(["release", "benchmark-competitor-summary"]) == 0
    assert cli.main(["release", "benchmark-contract-check", "--fail-missing"]) == 0
    assert cli.main(["release", "competitor-handoff", "--out-dir", "handoff"]) == 0
    assert cli.main(["release", "competitor-handoff-check", "handoff.zip", "--fail-missing"]) == 0
    assert cli.main(["release", "import-competitor-handoff", "returned.zip", "--skip-refresh"]) == 0

    assert calls[0][-1].endswith("tools/run_alpha4_1_sdk_gap_report.py")
    assert calls[1][-4].endswith("tools/lattice_workflow.py")
    assert calls[1][-3:] == ["doctor", "--format", "json"]
    assert calls[2][-1].endswith("tools/run_alpha4_1_sdk_gap_report.py")
    assert calls[3][-2].endswith("tools/dev_check.py")
    assert calls[3][-1] == "--quick"
    assert calls[4][1].endswith("tools/list_deliverables.py")
    assert calls[4][-2:] == ["--format", "json"]
    assert calls[5][1].endswith("tools/refresh_engine_benchmark_artifacts.py")
    assert calls[5][-1] == "--skip-unity-compare"
    assert calls[6][1].endswith("tools/build_benchmark_matrix_report.py")
    assert calls[7][1].endswith("tools/build_benchmark_coverage_report.py")
    assert calls[8][1].endswith("tools/build_scenario_contract_report.py")
    assert calls[9][1].endswith("tools/build_surface_claim_report.py")
    assert calls[10][1].endswith("tools/audit_engine_benchmark_completion.py")
    assert calls[10][-1] == "--fail-incomplete"
    assert calls[11][1].endswith("tools/build_benchmark_claim_summary.py")
    assert calls[12][1].endswith("tools/build_competitor_lane_summary.py")
    assert calls[13][1].endswith("tools/check_benchmark_contract_stack.py")
    assert calls[13][-1] == "--fail-missing"
    assert calls[14][1].endswith("tools/export_competitor_benchmark_handoff.py")
    assert calls[14][-2:] == ["--out-dir", "handoff"]
    assert calls[15][1].endswith("tools/check_competitor_handoff_workbench.py")
    assert calls[15][-2:] == ["handoff.zip", "--fail-missing"]
    assert calls[16][1].endswith("tools/import_competitor_benchmark_handoff.py")
    assert calls[16][-2:] == ["returned.zip", "--skip-refresh"]


def test_cli_routes_orientation_summary(monkeypatch) -> None:
    calls: list[list[str]] = []

    def fake_run(cmd: Sequence[str]) -> int:
        calls.append(list(cmd))
        return 0

    monkeypatch.setattr(cli, "_run", fake_run)

    assert cli.main(["orient", "summary", "--refresh"]) == 0

    assert calls[0][1].endswith("tools/run_engine_orientation_summary.py")
    assert calls[0][-1] == "--refresh"
