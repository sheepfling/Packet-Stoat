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
    assert "unreal:" in out
    assert "godot:" in out
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


def test_cli_routes_engine_workflows(monkeypatch) -> None:
    calls: list[list[str]] = []

    def fake_run(cmd: Sequence[str]) -> int:
        calls.append(list(cmd))
        return 0

    monkeypatch.setattr(cli, "_run", fake_run)

    assert cli.main(["engine", "unreal", "doctor", "--engine-version", "5.8"]) == 0
    assert cli.main(["engine", "godot", "verify", "--dry-run"]) == 0
    assert cli.main(["engine", "unity", "doctor", "--unity-version", "6000.5"]) == 0

    assert calls[0][-3:] == ["doctor", "--engine-version", "5.8"]
    assert calls[0][-4].endswith("tools/unreal_workflow.py")
    assert calls[1][-2:] == ["verify", "--dry-run"]
    assert calls[1][-3].endswith("tools/godot_workflow.py")
    assert calls[2][-3:] == ["doctor", "--unity-version", "6000.5"]
    assert calls[2][-4].endswith("tools/unity_workflow.py")


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

    assert calls[0][-1].endswith("tools/run_alpha4_1_sdk_gap_report.py")
    assert calls[1][-4].endswith("tools/lattice_workflow.py")
    assert calls[1][-3:] == ["doctor", "--format", "json"]
    assert calls[2][-1].endswith("tools/run_alpha4_1_sdk_gap_report.py")
    assert calls[3][-2].endswith("tools/dev_check.py")
    assert calls[3][-1] == "--quick"
    assert calls[4][1].endswith("tools/list_deliverables.py")
    assert calls[4][-2:] == ["--format", "json"]


def test_cli_routes_orientation_summary(monkeypatch) -> None:
    calls: list[list[str]] = []

    def fake_run(cmd: Sequence[str]) -> int:
        calls.append(list(cmd))
        return 0

    monkeypatch.setattr(cli, "_run", fake_run)

    assert cli.main(["orient", "summary", "--refresh"]) == 0

    assert calls[0][1].endswith("tools/run_engine_orientation_summary.py")
    assert calls[0][-1] == "--refresh"
