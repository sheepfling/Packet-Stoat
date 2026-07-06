from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import run_unreal_vendor_linux_docker


def test_dry_run_payload_records_handoff_lane(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(run_unreal_vendor_linux_docker, "docker_available", lambda: (True, "ok"))
    monkeypatch.setattr(run_unreal_vendor_linux_docker, "image_available", lambda image: True)
    monkeypatch.setattr(
        run_unreal_vendor_linux_docker,
        "build_config",
        lambda args: {
            "profile_path": ROOT / "tools" / "unreal_linux_profiles" / "ubuntu_24_04_ue58.env",
            "image": "fastdis-linux-proof:ubuntu24.04",
            "platform": "linux/amd64",
            "docker_user": "1000:1000",
            "ue_root_in_container": "/opt/unreal-engine",
            "version_label": "ue5.8-linux",
            "proof_profile": "ubuntu-24.04",
            "engine_path": ROOT,
            "engine_archive": None,
            "engine_stage_dir": tmp_path / "stage",
            "force_reextract": False,
            "selected_input": {"version": "5.8"},
            "discovered_inputs": [],
            "search_roots": [tmp_path],
        },
    )
    args = run_unreal_vendor_linux_docker.parse_args(
        [
            "--dry-run",
            "--json-out",
            str(tmp_path / "linux.json"),
            "--md-out",
            str(tmp_path / "linux.md"),
            "--docker-log-mode",
            "tee",
            "--log-tail-lines",
            "120",
        ]
    )

    payload = run_unreal_vendor_linux_docker.build_payload(args)

    assert payload["schema"] == "packet_stoat.unreal_vendor_linux_docker.v1"
    assert payload["status"] == "dry-run"
    assert "tools/unreal_vendor_workflow.py prepare-source" in payload["command_text"]
    assert "tools/unreal_vendor_workflow.py handoff" in payload["command_text"]
    assert "--target-platforms Linux" in payload["command_text"]
    assert "--baseline-version 5.7" in payload["command_text"]
    assert payload["observability"]["docker_log_mode"] == "tee"
    assert payload["observability"]["log_tail_lines"] == 120
    assert "--user 1000:1000" in payload["command_text"]
    assert payload["lane_manifest"]["schema"] == "packet_stoat.unreal_vendor_linux_lane_manifest.v1"
    assert payload["lane_manifest_json"].endswith("lane_manifest.json")
    assert payload["lane_manifest"]["image"]["tag"] == "fastdis-linux-proof:ubuntu24.04"


def test_failed_docker_run_classifies_inner_compile_failure(monkeypatch, tmp_path: Path) -> None:
    handoff = tmp_path / "handoff.json"
    handoff.write_text(
        json.dumps(
            {
                "failure_class": "compile-or-link",
                "status": "ready",
                "build_report": {
                    "status": "fail",
                    "detail": "fatal error: CesiumRuntime.h: No such file or directory",
                },
                "install_smoke_report": {"status": "missing-package"},
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(run_unreal_vendor_linux_docker, "docker_available", lambda: (True, "ok"))
    monkeypatch.setattr(run_unreal_vendor_linux_docker, "image_available", lambda image: True)
    monkeypatch.setattr(
        run_unreal_vendor_linux_docker,
        "build_config",
        lambda args: {
            "profile_path": ROOT / "tools" / "unreal_linux_profiles" / "ubuntu_24_04_ue58.env",
            "image": "fastdis-linux-proof:ubuntu24.04",
            "platform": "linux/amd64",
            "docker_user": "1000:1000",
            "ue_root_in_container": "/opt/unreal-engine",
            "version_label": "ue5.8-linux",
            "proof_profile": "ubuntu-24.04",
            "engine_path": ROOT,
            "engine_archive": None,
            "engine_stage_dir": tmp_path / "stage",
            "force_reextract": False,
            "selected_input": {"version": "5.8"},
            "discovered_inputs": [],
            "search_roots": [tmp_path],
        },
    )
    monkeypatch.setattr(
        run_unreal_vendor_linux_docker,
        "output_paths",
        lambda args: {
            "json_out": tmp_path / "outer.json",
            "md_out": tmp_path / "outer.md",
            "handoff_json": handoff,
            "handoff_md": tmp_path / "handoff.md",
            "build_json": tmp_path / "build.json",
            "build_md": tmp_path / "build.md",
            "install_json": tmp_path / "install.json",
            "install_md": tmp_path / "install.md",
            "progress_json": tmp_path / "progress.json",
            "progress_md": tmp_path / "progress.md",
            "progress_events": tmp_path / "progress.jsonl",
            "inner_log": tmp_path / "inner.log",
            "docker_log": tmp_path / "docker.log",
            "package_dir": tmp_path / "package",
            "project_dir": tmp_path / "project",
            "lane_manifest_json": tmp_path / "lane_manifest.json",
            "lane_manifest_md": tmp_path / "lane_manifest.md",
        },
    )
    monkeypatch.setattr(
        run_unreal_vendor_linux_docker,
        "run_docker_command",
        lambda *args, **kwargs: (2, ["fatal error"], [], "fatal error"),
    )
    monkeypatch.setattr(run_unreal_vendor_linux_docker, "clear_reused_report_paths", lambda paths: [])
    monkeypatch.setattr(
        run_unreal_vendor_linux_docker,
        "load_json",
        lambda path, min_mtime=None: {
            "failure_class": "compile-or-link",
            "status": "ready",
            "build_report": {
                "status": "fail",
                "detail": "fatal error: CesiumRuntime.h: No such file or directory",
            },
            "install_smoke_report": {"status": "missing-package"},
        },
    )
    monkeypatch.setattr(
        run_unreal_vendor_linux_docker,
        "build_docker_command",
        lambda args, config, paths: ["docker", "run"],
    )

    args = run_unreal_vendor_linux_docker.parse_args([])
    payload = run_unreal_vendor_linux_docker.build_payload(args)

    assert payload["status"] == "fail"
    assert payload["failure_class"] == "compile-or-link"
    assert any("CesiumRuntime.h" in edge for edge in payload["rough_edges"])


def test_timeout_ignores_stale_handoff(monkeypatch, tmp_path: Path) -> None:
    stale_handoff = tmp_path / "stale-handoff.json"
    stale_handoff.write_text('{"failure_class": "verified-build", "status": "ready"}', encoding="utf-8")
    old_time = time.time() - 3600
    os.utime(stale_handoff, (old_time, old_time))
    monkeypatch.setattr(run_unreal_vendor_linux_docker, "docker_available", lambda: (True, "ok"))
    monkeypatch.setattr(run_unreal_vendor_linux_docker, "image_available", lambda image: True)
    monkeypatch.setattr(
        run_unreal_vendor_linux_docker,
        "build_config",
        lambda args: {
            "profile_path": ROOT / "tools" / "unreal_linux_profiles" / "ubuntu_24_04_ue58.env",
            "image": "fastdis-linux-proof:ubuntu24.04",
            "platform": "linux/amd64",
            "docker_user": "1000:1000",
            "ue_root_in_container": "/opt/unreal-engine",
            "version_label": "ue5.8-linux",
            "proof_profile": "ubuntu-24.04",
            "engine_path": ROOT,
            "engine_archive": None,
            "engine_stage_dir": tmp_path / "stage",
            "force_reextract": False,
            "selected_input": {"version": "5.8"},
            "discovered_inputs": [],
            "search_roots": [tmp_path],
        },
    )
    monkeypatch.setattr(
        run_unreal_vendor_linux_docker,
        "output_paths",
        lambda args: {
            "json_out": tmp_path / "outer.json",
            "md_out": tmp_path / "outer.md",
            "handoff_json": stale_handoff,
            "handoff_md": tmp_path / "handoff.md",
            "build_json": tmp_path / "build.json",
            "build_md": tmp_path / "build.md",
            "install_json": tmp_path / "install.json",
            "install_md": tmp_path / "install.md",
            "progress_json": tmp_path / "progress.json",
            "progress_md": tmp_path / "progress.md",
            "progress_events": tmp_path / "progress.jsonl",
            "inner_log": tmp_path / "inner.log",
            "docker_log": tmp_path / "docker.log",
            "package_dir": tmp_path / "package",
            "project_dir": tmp_path / "project",
            "lane_manifest_json": tmp_path / "lane_manifest.json",
            "lane_manifest_md": tmp_path / "lane_manifest.md",
        },
    )

    def fake_run_docker_command(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd=["docker", "run"], timeout=5)

    monkeypatch.setattr(run_unreal_vendor_linux_docker, "run_docker_command", fake_run_docker_command)
    monkeypatch.setattr(
        run_unreal_vendor_linux_docker,
        "build_docker_command",
        lambda args, config, paths: ["docker", "run"],
    )

    args = run_unreal_vendor_linux_docker.parse_args(["--timeout-seconds", "5"])
    payload = run_unreal_vendor_linux_docker.build_payload(args)

    assert payload["status"] == "fail"
    assert payload["failure_class"] == "timeout"
    assert str(stale_handoff) in payload["cleared_artifacts"]
    assert payload["handoff_json"] == str(stale_handoff)
    assert any("attempted cleanup" in edge for edge in payload["rough_edges"])


def test_normalization_script_is_targeted_and_verbose() -> None:
    lines = run_unreal_vendor_linux_docker._mark_executables_script("/opt/unreal-engine")
    script = "\n".join(lines)

    assert "Engine/Source/ThirdParty" not in script
    assert "Engine/Extras/ThirdPartyNotUE/SDKs/HostLinux" in script
    assert "('linux-binaries', root / 'Engine/Binaries/Linux', 'linux-binaries')" in script
    assert "phase_count % 250 == 0" in script


def test_build_inner_command_creates_report_parent_dirs(tmp_path: Path) -> None:
    args = run_unreal_vendor_linux_docker.parse_args([])
    repo_tmp = ROOT / "artifacts" / "test-temp" / "unreal_vendor_linux_docker"
    config = {
        "ue_root_in_container": "/opt/unreal-engine",
        "engine_compiler_dir": ROOT / "artifacts" / "staging" / "unreal" / "linux" / "ue5.8.0-linux" / "Engine" / "Extras" / "ThirdPartyNotUE" / "SDKs" / "HostLinux" / "Linux_x64" / "v26_clang-20.1.8-rockylinux8" / "x86_64-unknown-linux-gnu",
        "engine_path": ROOT / "artifacts" / "staging" / "unreal" / "linux" / "ue5.8.0-linux",
    }
    paths = {
        "inner_log": repo_tmp / "reports" / "inner.log",
        "docker_log": repo_tmp / "reports" / "stdout.log",
        "handoff_json": repo_tmp / "reports" / "handoff.json",
        "handoff_md": repo_tmp / "reports" / "handoff.md",
        "build_json": repo_tmp / "reports" / "build.json",
        "build_md": repo_tmp / "reports" / "build.md",
        "install_json": repo_tmp / "reports" / "install.json",
        "install_md": repo_tmp / "reports" / "install.md",
        "progress_json": repo_tmp / "reports" / "progress.json",
        "progress_md": repo_tmp / "reports" / "progress.md",
        "progress_events": repo_tmp / "reports" / "progress.jsonl",
        "package_dir": repo_tmp / "pkg" / "CesiumForUnreal",
        "project_dir": repo_tmp / "scratch" / "project",
        "lane_manifest_json": repo_tmp / "reports" / "lane_manifest.json",
        "lane_manifest_md": repo_tmp / "reports" / "lane_manifest.md",
    }

    command = run_unreal_vendor_linux_docker.build_inner_command(
        args,
        config,
        paths,
        archive_present=False,
        extract_archive=False,
    )

    assert 'mkdir -p "/src/' in command
    assert "/src/" in command
