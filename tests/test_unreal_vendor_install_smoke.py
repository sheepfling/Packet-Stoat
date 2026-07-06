from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import run_unreal_vendor_install_smoke


def test_create_scratch_project_installs_packaged_plugin(tmp_path: Path) -> None:
    package_dir = tmp_path / "package"
    package_dir.mkdir()
    (package_dir / "CesiumForUnreal.uplugin").write_text("{}\n", encoding="utf-8")
    project_dir = tmp_path / "project"

    project_path = run_unreal_vendor_install_smoke.create_scratch_project(
        project_dir,
        package_dir,
        "CesiumForUnreal",
        clean=True,
    )

    assert project_path.exists()
    assert (project_dir / "Binaries" / "Linux").is_dir()
    plugin_dir = project_dir / "Plugins" / "CesiumForUnreal"
    assert plugin_dir.exists()
    source_root = project_dir / "Source" / "CesiumForUnrealInstallSmoke"
    assert (source_root / "CesiumForUnrealInstallSmoke.Build.cs").is_file()
    assert (source_root / "CesiumForUnrealInstallSmoke.cpp").is_file()
    assert (project_dir / "Source" / "CesiumForUnrealInstallSmoke.Target.cs").is_file()
    assert (project_dir / "Source" / "CesiumForUnrealInstallSmokeEditor.Target.cs").is_file()
    descriptor = json.loads(project_path.read_text(encoding="utf-8"))
    plugin_names = {plugin["Name"] for plugin in descriptor["Plugins"]}
    assert "CesiumForUnreal" in plugin_names
    assert "PythonScriptPlugin" in plugin_names
    assert descriptor["Modules"][0]["Name"] == "CesiumForUnrealInstallSmoke"


def test_missing_package_writes_report(tmp_path: Path, monkeypatch) -> None:
    json_out = tmp_path / "report.json"
    markdown_out = tmp_path / "report.md"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_unreal_vendor_install_smoke.py",
            "--vendor",
            "cesium",
            "--package-dir",
            str(tmp_path / "missing-package"),
            "--project-dir",
            str(tmp_path / "project"),
            "--json-out",
            str(json_out),
            "--markdown-out",
            str(markdown_out),
        ],
    )

    assert run_unreal_vendor_install_smoke.main() == 2
    payload = json.loads(json_out.read_text(encoding="utf-8"))
    assert payload["status"] == "missing-package"


def test_dry_run_writes_command_report(tmp_path: Path, monkeypatch) -> None:
    package_dir = tmp_path / "package"
    package_dir.mkdir()
    (package_dir / "CesiumForUnreal.uplugin").write_text("{}\n", encoding="utf-8")
    json_out = tmp_path / "report.json"
    markdown_out = tmp_path / "report.md"

    monkeypatch.setattr(run_unreal_vendor_install_smoke, "resolve_unreal", lambda explicit, version: "/Applications/UnrealEditor")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_unreal_vendor_install_smoke.py",
            "--vendor",
            "cesium",
            "--package-dir",
            str(package_dir),
            "--project-dir",
            str(tmp_path / "project"),
            "--json-out",
            str(json_out),
            "--markdown-out",
            str(markdown_out),
            "--dry-run",
        ],
    )

    assert run_unreal_vendor_install_smoke.main() == 0
    payload = json.loads(json_out.read_text(encoding="utf-8"))
    assert payload["status"] == "dry-run"
    assert payload["plugin_name"] == "CesiumForUnreal"
    assert payload["command"][0] == "/Applications/UnrealEditor"
    assert "-NullRHI" in payload["command"]


def test_main_classifies_missing_report_from_editor_log(monkeypatch, tmp_path: Path) -> None:
    package_dir = tmp_path / "package"
    package_dir.mkdir()
    (package_dir / "CesiumForUnreal.uplugin").write_text("{}\n", encoding="utf-8")
    json_out = tmp_path / "report.json"
    markdown_out = tmp_path / "report.md"

    monkeypatch.setattr(run_unreal_vendor_install_smoke, "resolve_unreal", lambda explicit, version: "/Applications/UnrealEditor")
    monkeypatch.setattr(
        run_unreal_vendor_install_smoke,
        "run_editor_until_report",
        lambda *args, **kwargs: (1, 3.0, False, False),
    )
    monkeypatch.setattr(
        run_unreal_vendor_install_smoke.unreal_editor_log,
        "summarize_editor_failure",
        lambda path: {"failure_kind": "plugin-version-incompatible", "detail": "version mismatch", "log_excerpt": []},
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_unreal_vendor_install_smoke.py",
            "--vendor",
            "cesium",
            "--package-dir",
            str(package_dir),
            "--project-dir",
            str(tmp_path / "project"),
            "--json-out",
            str(json_out),
            "--markdown-out",
            str(markdown_out),
        ],
    )

    assert run_unreal_vendor_install_smoke.main() == 1
    payload = json.loads(json_out.read_text(encoding="utf-8"))
    assert payload["status"] == "plugin-version-incompatible"


def test_main_downgrades_pass_when_log_shows_plugin_load_failure(monkeypatch, tmp_path: Path) -> None:
    package_dir = tmp_path / "package"
    package_dir.mkdir()
    descriptor = package_dir / "CesiumForUnreal.uplugin"
    descriptor.write_text("{}\n", encoding="utf-8")
    json_out = tmp_path / "report.json"
    markdown_out = tmp_path / "report.md"

    monkeypatch.setattr(run_unreal_vendor_install_smoke, "resolve_unreal", lambda explicit, version: "/Applications/UnrealEditor")
    monkeypatch.setattr(
        run_unreal_vendor_install_smoke,
        "run_editor_until_report",
        lambda *args, **kwargs: (1, 3.0, True, False),
    )
    monkeypatch.setattr(
        run_unreal_vendor_install_smoke.unreal_editor_log,
        "summarize_editor_failure",
        lambda path: {
            "failure_kind": "plugin-load-failed",
            "detail": "an Unreal plugin required by the lane failed to load before the helper could run, usually because a required runtime module was missing",
            "log_excerpt": ["Plugin 'CesiumForUnreal' failed to load because module 'CesiumRuntime' could not be found."],
        },
    )

    def fake_write_report(report: dict[str, object], json_path: Path, markdown_path: Path) -> None:
        json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        markdown_path.write_text("report\n", encoding="utf-8")

    monkeypatch.setattr(run_unreal_vendor_install_smoke, "write_report", fake_write_report)
    json_out.write_text(
        json.dumps(
            {
                "schema": "packet_stoat.unreal_vendor_install_smoke.v1",
                "vendor": "cesium",
                "plugin_name": "CesiumForUnreal",
                "status": "pass",
                "project_dir": str(tmp_path / "project"),
                "package_dir": str(package_dir),
                "checks": [],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_unreal_vendor_install_smoke.py",
            "--vendor",
            "cesium",
            "--package-dir",
            str(package_dir),
            "--project-dir",
            str(tmp_path / "project"),
            "--json-out",
            str(json_out),
            "--markdown-out",
            str(markdown_out),
        ],
    )

    assert run_unreal_vendor_install_smoke.main() == 1
    payload = json.loads(json_out.read_text(encoding="utf-8"))
    assert payload["status"] == "plugin-load-failed"
    assert payload["log_summary"]["failure_kind"] == "plugin-load-failed"


def test_run_editor_until_report_ignores_pending_placeholder(monkeypatch, tmp_path: Path) -> None:
    report_path = tmp_path / "report.json"
    report_path.write_text(
        json.dumps(
            {
                "schema": "packet_stoat.pending_subprocess_artifact.v1",
                "status": "pending",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    baseline = report_path.stat().st_mtime

    class FakeProcess:
        def __init__(self) -> None:
            self.returncode = None

        def poll(self):
            return self.returncode

        def terminate(self):
            self.returncode = 0

        def wait(self, timeout=None):
            return int(self.returncode or 0)

        def kill(self):
            self.returncode = -9

    monkeypatch.setattr(run_unreal_vendor_install_smoke.subprocess, "Popen", lambda *args, **kwargs: FakeProcess())

    times = iter([0.0, 0.1, 0.2, 0.31, 0.32])
    monkeypatch.setattr(run_unreal_vendor_install_smoke.time, "monotonic", lambda: next(times))
    monkeypatch.setattr(run_unreal_vendor_install_smoke.time, "sleep", lambda seconds: None)

    returncode, elapsed, terminated_after_report, timed_out = run_unreal_vendor_install_smoke.run_editor_until_report(
        ["UnrealEditor-Cmd.exe"],
        cwd=tmp_path,
        env={},
        report_path=report_path,
        timeout_seconds=0.3,
        report_grace_seconds=0.05,
        baseline_report_mtime=baseline,
        poll_interval_seconds=0.0,
    )

    assert timed_out is True
    assert terminated_after_report is False
    assert returncode == 0
