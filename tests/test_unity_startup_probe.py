from __future__ import annotations

from pathlib import Path

import sys


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import run_unity_startup_probe


def test_create_project_writes_minimal_manifest(tmp_path: Path) -> None:
    project = tmp_path / "project"

    run_unity_startup_probe.create_project(project)

    assert (project / "Packages" / "manifest.json").is_file()
    assert (project / "ProjectSettings" / "ProjectVersion.txt").is_file()


def test_startup_attempts_include_macos_fallbacks(monkeypatch, tmp_path: Path) -> None:
    install = run_unity_startup_probe.unity_env.UnityInstall(
        version="6000.5",
        install_root="/Applications/Unity/Hub/Editor/6000.5.0f1",
        editor_path="/Applications/Unity/Hub/Editor/6000.5.0f1/Unity.app/Contents/MacOS/Unity",
        editor_app_path="/Applications/Unity/Hub/Editor/6000.5.0f1/Unity.app",
        source="test",
        quirks=(),
    )
    monkeypatch.setattr(run_unity_startup_probe.host_platform, "system", lambda: "Darwin")
    monkeypatch.setattr(
        run_unity_startup_probe.run_unity_editor_tests,
        "unity_runtime_env",
        lambda report_json: {"FASTDIS_UNITY_RUNTIME_REPORT_JSON": str(report_json)},
    )
    monkeypatch.setattr(run_unity_startup_probe.run_unity_editor_tests, "unity_graphics_args", lambda: [])

    attempts = run_unity_startup_probe.startup_attempts(install, tmp_path / "project", tmp_path / "reports")

    assert [attempt["launch"] for attempt in attempts] == ["login-shell", "launch-services", "direct"]
    assert attempts[0]["cmd"][:2] == ["/bin/zsh", "-lc"]
    assert attempts[1]["cmd"][:5] == ["open", "-W", "-n", "-a", install.editor_app_path]
    assert attempts[2]["cmd"][:2] == [install.editor_path, "-batchmode"]


def test_render_markdown_surfaces_project_state_and_attempts() -> None:
    report = {
        "status": "fail",
        "host_platform": "macos",
        "unity_version": "6000.5.0f1",
        "detail": "Unity did not begin importing the scratch startup-probe project before the timeout; the project Library/ directory was never created.",
        "launch": "direct",
        "log": "/tmp/startup.log",
        "launcher_log": "/tmp/startup-launcher.log",
        "project_state": {"library_exists": False, "package_cache_exists": False, "script_assemblies_exists": False},
        "attempts": [{"launch": "direct", "status": "timeout", "returncode": -15, "timed_out": True, "elapsed_seconds": 60.0}],
    }

    markdown = run_unity_startup_probe.render_markdown(report)

    assert "Unity Startup Probe Report" in markdown
    assert "project_state.library_exists: `False`" in markdown
    assert "launch=direct status=timeout returncode=-15 timed_out=True elapsed=60.0" in markdown


def test_launcher_failure_hint_maps_known_signatures(tmp_path: Path) -> None:
    hint_log = tmp_path / "unity_startup_probe_launch_services_launcher.log"
    hint_log.write_text("kLSNoExecutableErr: The executable is missing\n", encoding="utf-8")

    hint = run_unity_startup_probe.launcher_failure_hint(hint_log)

    assert hint is not None
    assert "kLSNoExecutableErr" in hint
