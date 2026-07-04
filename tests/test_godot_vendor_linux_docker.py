from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import run_godot_vendor_linux_docker


def test_dry_run_payload_records_docker_command(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(run_godot_vendor_linux_docker, "docker_available", lambda: (True, "ok"))
    monkeypatch.setattr(run_godot_vendor_linux_docker, "image_available", lambda image: True)
    args = run_godot_vendor_linux_docker.parse_args(
        [
            "--dry-run",
            "--plugin-root",
            "external/cesium/3D-Tiles-For-Godot",
            "--json-out",
            str(tmp_path / "linux.json"),
            "--md-out",
            str(tmp_path / "linux.md"),
            "--scons-jobs",
            "6",
            "--docker-log-mode",
            "tee",
            "--inner-log-mode",
            "tee",
            "--log-tail-lines",
            "120",
        ]
    )

    payload = run_godot_vendor_linux_docker.build_payload(args)

    assert payload["schema"] == "packet_stoat.godot_vendor_linux_docker.v1"
    assert payload["status"] == "dry-run"
    assert payload["image"] == "fastdis-godot-linux-proof:godot4.7-ubuntu24.04"
    assert payload["cache_volume"] == "fastdis-godot-linux-proof-cache"
    assert "--scons-jobs 6" in payload["command_text"]
    assert "--log-mode tee" in payload["command_text"]
    assert "--log-tail-lines 120" in payload["command_text"]
    assert "--name" in payload["command"]
    assert "fastdis-godot-linux-proof-cache:/tmp/fastdis_godot" in payload["command_text"]
    assert "tools/godot_vendor_workflow.py handoff" in payload["command_text"]
    assert payload["inner_environment"]["FASTDIS_GODOT_WORK_ROOT"] == "/tmp/fastdis_godot"
    assert payload["inner_environment"]["curl_http_version"] == "1.1"
    assert payload["observability"]["docker_log_mode"] == "tee"
    assert payload["observability"]["inner_log_mode"] == "tee"
    assert payload["observability"]["log_tail_lines"] == 120
    assert payload["docker_log"].endswith("cesium-godot_linux_docker_stdout.log")


def test_failed_docker_run_classifies_missing_godot_toolchain(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(run_godot_vendor_linux_docker, "docker_available", lambda: (True, "ok"))
    monkeypatch.setattr(run_godot_vendor_linux_docker, "image_available", lambda image: True)
    monkeypatch.setattr(
        run_godot_vendor_linux_docker,
        "DEFAULT_INNER_JSON",
        run_godot_vendor_linux_docker.ROOT / "artifacts" / "reports" / "godot_vendor_plugin" / "missing-inner.json",
    )

    def fake_run(command, **kwargs):
        if command == ["docker", "info"]:
            return subprocess.CompletedProcess(command, 0, stdout="ok", stderr="")
        if command[:3] == ["docker", "image", "inspect"]:
            return subprocess.CompletedProcess(command, 0, stdout="[]", stderr="")
        return subprocess.CompletedProcess(command, 2, stdout="godot executable missing\n", stderr="")

    monkeypatch.setattr(run_godot_vendor_linux_docker.subprocess, "run", fake_run)
    args = run_godot_vendor_linux_docker.parse_args(
        [
            "--json-out",
            str(tmp_path / "linux.json"),
            "--md-out",
            str(tmp_path / "linux.md"),
        ]
    )

    payload = run_godot_vendor_linux_docker.build_payload(args)

    assert payload["status"] == "fail"
    assert payload["failure_class"] == "engine-missing"
    assert payload["stdout_tail"] == ["godot executable missing"]


def test_inner_handoff_failed_checks_become_rough_edges(monkeypatch, tmp_path: Path) -> None:
    inner = tmp_path / "inner.json"
    inner.write_text(
        """
{
  "failure_class": "toolchain-missing",
  "build_report": {
    "doctor_checks": [
      {"name": "godot", "status": "fail", "detail": "missing godot executable"},
      {"name": "scons", "status": "fail", "detail": "missing scons executable"}
    ],
    "next_steps": ["Install SCons or set FASTDIS_SCONS."]
  }
}
""".strip(),
        encoding="utf-8",
    )
    monkeypatch.setattr(run_godot_vendor_linux_docker, "DEFAULT_INNER_JSON", inner)

    loaded = run_godot_vendor_linux_docker.load_inner_handoff()
    edges = run_godot_vendor_linux_docker.inner_rough_edges(loaded)

    assert edges == [
        "godot: missing godot executable",
        "scons: missing scons executable",
        "next: Install SCons or set FASTDIS_SCONS.",
    ]


def test_timeout_ignores_stale_inner_handoff(monkeypatch, tmp_path: Path) -> None:
    stale_inner = tmp_path / "stale-inner.json"
    stale_inner.write_text('{"failure_class": "verified-build", "build_report": {"status": "pass"}}', encoding="utf-8")
    old_time = time.time() - 3600
    os.utime(stale_inner, (old_time, old_time))
    monkeypatch.setattr(run_godot_vendor_linux_docker, "DEFAULT_INNER_JSON", stale_inner)
    monkeypatch.setattr(run_godot_vendor_linux_docker, "docker_available", lambda: (True, "ok"))
    monkeypatch.setattr(run_godot_vendor_linux_docker, "image_available", lambda image: True)
    monkeypatch.setattr(run_godot_vendor_linux_docker, "build_docker_command", lambda args: ["docker", "run"])

    def fake_run_docker_command(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd=["docker", "run"], timeout=5)

    monkeypatch.setattr(run_godot_vendor_linux_docker, "run_docker_command", fake_run_docker_command)
    args = run_godot_vendor_linux_docker.parse_args(
        [
            "--json-out",
            str(tmp_path / "linux.json"),
            "--md-out",
            str(tmp_path / "linux.md"),
            "--timeout-seconds",
            "5",
        ]
    )

    payload = run_godot_vendor_linux_docker.build_payload(args)

    assert payload["status"] == "fail"
    assert payload["failure_class"] == "timeout"
    assert payload["inner_handoff_json"] is None
    assert any("predated this run" in edge for edge in payload["rough_edges"])
