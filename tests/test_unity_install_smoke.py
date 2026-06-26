from __future__ import annotations

from pathlib import Path

import sys


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import run_unity_install_smoke


def test_clear_previous_artifacts_removes_only_existing_files(tmp_path: Path) -> None:
    stale_json = tmp_path / "unity_install_smoke.json"
    stale_log = tmp_path / "unity_install_smoke.log"
    stale_json.write_text("old", encoding="utf-8")
    stale_log.write_text("old", encoding="utf-8")

    run_unity_install_smoke.clear_previous_artifacts(stale_json, stale_log, tmp_path / "missing.json")

    assert not stale_json.exists()
    assert not stale_log.exists()


def test_install_criteria_reads_check_statuses_and_cache_evidence() -> None:
    report = {
        "checks": [
            {"name": "native_abi_loads", "status": "pass"},
            {"name": "world_processes_entity_state_packet", "status": "pass"},
            {"name": "world_auto_spawns_and_positions_actor", "status": "pass"},
            {"name": "replay_player_steps_world_state", "status": "fail"},
            {"name": "receiver_socket_loopback_feeds_world", "status": "pass"},
        ],
        "package_cache_locations": ["Library/PackageCache/com.sheepfling.fastdis@demo"],
    }

    criteria = run_unity_install_smoke.install_criteria(report)

    assert criteria == {
        "native_abi_loads": True,
        "world_processes_entity_state_packet": True,
        "world_auto_spawns_and_positions_actor": True,
        "replay_player_steps_world_state": False,
        "receiver_socket_loopback_feeds_world": True,
        "git_package_cache_detected": True,
    }


def test_project_state_reports_import_markers(tmp_path: Path) -> None:
    project = tmp_path / "project"
    (project / "Library" / "PackageCache").mkdir(parents=True)
    (project / "Library" / "ScriptAssemblies").mkdir(parents=True)

    state = run_unity_install_smoke.project_state(project)

    assert state == {
        "library_exists": True,
        "package_cache_exists": True,
        "script_assemblies_exists": True,
    }


def test_enrich_failure_detail_marks_pre_import_timeout(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    launcher_log = tmp_path / "launcher.log"
    launcher_log.write_text("attempt to write a readonly database\n", encoding="utf-8")
    report = {"status": "fail", "detail": "timeout", "launcher_log": str(launcher_log)}

    run_unity_install_smoke.enrich_failure_detail(report, project)

    assert "did not begin importing the scratch project" in report["detail"]
    assert report["project_state"]["library_exists"] is False
    assert "readonly database" in report["detail"]


def test_failure_classification_marks_pre_import_start_failure() -> None:
    report = {
        "status": "fail",
        "launch": "direct",
        "package_cache_locations": [],
        "project_state": {"library_exists": False, "package_cache_exists": False, "script_assemblies_exists": False},
        "attempts": [{"launch": "launch-services", "status": "fail"}],
    }

    assert run_unity_install_smoke.failure_classification(report) == {
        "failure_stage": "host-startup",
        "failure_reason": "project-import-never-started",
    }


def test_render_markdown_surfaces_checks_and_install_criteria() -> None:
    report = {
        "status": "pass",
        "host_platform": "macos",
        "unity_version": "6000.5.0f1",
        "abi_version": 7,
        "detail": "install smoke checks passed",
        "manifest_git_url": "file:///tmp/repo.git?path=integrations/unity/com.sheepfling.fastdis",
        "repo_root": "/tmp/repo",
        "project_dir": "/tmp/project",
        "log": "/tmp/install.log",
        "launch": "direct",
        "launcher_log": "/tmp/launcher.log",
        "total": 5,
        "passed": 5,
        "failed": 0,
        "checks": [
            {"name": "native_abi_loads", "status": "pass"},
            {"name": "receiver_socket_loopback_feeds_world", "status": "pass"},
        ],
        "attempts": [{"launch": "direct", "status": "pass", "returncode": 0, "timed_out": False, "elapsed_seconds": 1.23}],
        "package_cache_locations": ["Library/PackageCache/com.sheepfling.fastdis@demo"],
        "plugin_inventory": {"macos": True, "windows": True, "linux": True},
        "project_state": {"library_exists": True, "package_cache_exists": True, "script_assemblies_exists": True},
        "failure_stage": "none",
        "failure_reason": "none",
    }

    markdown = run_unity_install_smoke.render_markdown(report)

    assert "## Checks" in markdown
    assert "- check `native_abi_loads`: `pass`" in markdown
    assert "## Install Criteria" in markdown
    assert "- receiver_socket_loopback_feeds_world: `True`" in markdown
    assert "- git_package_cache_detected: `True`" in markdown
    assert "- project_state.library_exists: `True`" in markdown
    assert "- failure_stage: `none`" in markdown
    assert "## Attempts" in markdown
    assert "- launch=direct status=pass returncode=0 timed_out=False elapsed=1.23" in markdown


def test_install_smoke_attempts_include_macos_fallbacks(monkeypatch, tmp_path: Path) -> None:
    install = run_unity_install_smoke.unity_env.UnityInstall(
        version="6000.5",
        install_root="/Applications/Unity/Hub/Editor/6000.5.0f1",
        editor_path="/Applications/Unity/Hub/Editor/6000.5.0f1/Unity.app/Contents/MacOS/Unity",
        editor_app_path="/Applications/Unity/Hub/Editor/6000.5.0f1/Unity.app",
        source="test",
        quirks=(),
    )
    monkeypatch.setattr(run_unity_install_smoke.host_platform, "system", lambda: "Darwin")
    monkeypatch.setattr(
        run_unity_install_smoke.run_unity_editor_tests,
        "unity_runtime_env",
        lambda report_json: {"FASTDIS_UNITY_RUNTIME_REPORT_JSON": str(report_json)},
    )
    monkeypatch.setattr(run_unity_install_smoke.run_unity_editor_tests, "unity_graphics_args", lambda: [])

    attempts = run_unity_install_smoke.install_smoke_attempts(install, tmp_path / "project", tmp_path / "reports")

    assert [attempt["launch"] for attempt in attempts] == ["login-shell", "launch-services", "direct"]
    assert attempts[0]["cmd"][0:2] == ["/bin/zsh", "-lc"]
    assert attempts[1]["cmd"][0:5] == ["open", "-W", "-n", "-a", install.editor_app_path]
    assert attempts[2]["cmd"][0:2] == [install.editor_path, "-batchmode"]
    assert attempts[2]["env"]["FASTDIS_UNITY_RUNTIME_REPORT_JSON"].endswith("unity_install_smoke.json")


def test_attempt_timeout_budget_reserves_time_for_direct_fallback() -> None:
    attempts = [
        {"launch": "login-shell"},
        {"launch": "launch-services"},
        {"launch": "direct"},
    ]

    first = run_unity_install_smoke.attempt_timeout_budget(240, attempts, 0)
    second = run_unity_install_smoke.attempt_timeout_budget(195, attempts, 1)
    third = run_unity_install_smoke.attempt_timeout_budget(150, attempts, 2)

    assert first == 45
    assert second == 45
    assert third == 150


def test_create_project_runner_includes_replay_and_loopback(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    repo_root = tmp_path / "repo"
    (repo_root / "integrations" / "unity" / "com.sheepfling.fastdis").mkdir(parents=True)

    run_unity_install_smoke.create_project(project_dir, repo_root)

    runner = (project_dir / "Assets" / "Editor" / "FastDisInstallSmokeRunner.cs").read_text(encoding="utf-8")
    assert "FastDisReplayPlayer replayPlayer = root.AddComponent<FastDisReplayPlayer>();" in runner
    assert '"receiver_socket_loopback_feeds_world"' in runner
    assert "SendLoopbackPacket(receiver, CreateEntityStatePdu(6, 1))" in runner
    assert "replayPlayer.LoadReplay(BuildReplay(CreateEntityStatePdu(7, 2), CreateEntityStateUpdatePdu(7)));" in runner
