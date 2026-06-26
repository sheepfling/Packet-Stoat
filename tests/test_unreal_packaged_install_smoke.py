from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import run_unreal_packaged_install_smoke


def test_create_scratch_project_installs_packaged_plugin(tmp_path: Path) -> None:
    package_dir = tmp_path / "package"
    (package_dir / "FastDis.uplugin").parent.mkdir(parents=True, exist_ok=True)
    (package_dir / "FastDis.uplugin").write_text('{"FriendlyName":"FastDIS"}\n', encoding="utf-8")
    (package_dir / "Content" / "Examples").mkdir(parents=True, exist_ok=True)
    (package_dir / "Content" / "Examples" / "FastDis_Demo.umap").write_text("demo\n", encoding="utf-8")
    project_dir = tmp_path / "project"

    project_path = run_unreal_packaged_install_smoke.create_scratch_project(project_dir, package_dir, clean=True)

    assert project_path.exists()
    plugin_dir = project_dir / "Plugins" / "FastDis"
    assert plugin_dir.exists()
    descriptor = json.loads(project_path.read_text(encoding="utf-8"))
    plugin_names = {plugin["Name"] for plugin in descriptor["Plugins"]}
    assert "FastDis" in plugin_names
    assert "PythonScriptPlugin" in plugin_names


def test_missing_package_writes_report(tmp_path: Path, monkeypatch) -> None:
    json_out = tmp_path / "report.json"
    markdown_out = tmp_path / "report.md"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_unreal_packaged_install_smoke.py",
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

    assert run_unreal_packaged_install_smoke.main() == 2
    payload = json.loads(json_out.read_text(encoding="utf-8"))
    assert payload["status"] == "missing-package"
    assert "Run the Unreal packaging flow first." in payload["details"][0]


def test_dry_run_writes_command_report(tmp_path: Path, monkeypatch) -> None:
    package_dir = tmp_path / "package"
    (package_dir / "FastDis.uplugin").parent.mkdir(parents=True, exist_ok=True)
    (package_dir / "FastDis.uplugin").write_text('{"FriendlyName":"FastDIS"}\n', encoding="utf-8")
    json_out = tmp_path / "report.json"
    markdown_out = tmp_path / "report.md"

    monkeypatch.setattr(run_unreal_packaged_install_smoke, "resolve_unreal", lambda explicit, version: "/Applications/UnrealEditor")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_unreal_packaged_install_smoke.py",
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

    assert run_unreal_packaged_install_smoke.main() == 0
    payload = json.loads(json_out.read_text(encoding="utf-8"))
    assert payload["status"] == "dry-run"
    assert payload["demo_map"] == "/FastDis/Examples/FastDis_Demo"
    assert payload["command"][0] == "/Applications/UnrealEditor"


def test_run_editor_until_report_terminates_after_report(monkeypatch, tmp_path: Path) -> None:
    report_path = tmp_path / "report.json"
    state = {"now": 0.0}

    class FakeProcess:
        def __init__(self) -> None:
            self.terminated = False
            self.killed = False
            self.returncode = None

        def poll(self):
            return self.returncode

        def terminate(self) -> None:
            self.terminated = True
            self.returncode = 0

        def kill(self) -> None:
            self.killed = True
            self.returncode = -9

        def wait(self, timeout: float | None = None) -> int:
            assert timeout is None or timeout >= 0
            return int(self.returncode or 0)

    fake_process = FakeProcess()

    monkeypatch.setattr(
        run_unreal_packaged_install_smoke.subprocess,
        "Popen",
        lambda *args, **kwargs: fake_process,
    )
    monkeypatch.setattr(run_unreal_packaged_install_smoke.time, "monotonic", lambda: state["now"])

    def fake_sleep(seconds: float) -> None:
        state["now"] += seconds
        if state["now"] >= 0.25 and not report_path.exists():
            report_path.write_text("{}\n", encoding="utf-8")

    monkeypatch.setattr(run_unreal_packaged_install_smoke.time, "sleep", fake_sleep)

    returncode, elapsed, terminated_after_report, timed_out = run_unreal_packaged_install_smoke.run_editor_until_report(
        ["UnrealEditor"],
        cwd=tmp_path,
        env={},
        report_path=report_path,
        timeout_seconds=30.0,
        report_grace_seconds=1.0,
    )

    assert returncode == 0
    assert elapsed >= 1.25
    assert terminated_after_report is True
    assert timed_out is False
    assert fake_process.terminated is True


def test_main_accepts_terminated_after_report_pass(monkeypatch, tmp_path: Path) -> None:
    package_dir = tmp_path / "package"
    (package_dir / "FastDis.uplugin").parent.mkdir(parents=True, exist_ok=True)
    (package_dir / "FastDis.uplugin").write_text('{"FriendlyName":"FastDIS"}\n', encoding="utf-8")
    json_out = tmp_path / "report.json"
    markdown_out = tmp_path / "report.md"

    monkeypatch.setattr(run_unreal_packaged_install_smoke, "resolve_unreal", lambda explicit, version: "/Applications/UnrealEditor")
    monkeypatch.setattr(
        run_unreal_packaged_install_smoke,
        "run_editor_until_report",
        lambda *args, **kwargs: (0, 12.5, True, False),
    )

    original_create = run_unreal_packaged_install_smoke.create_scratch_project

    def fake_create_scratch(project_dir: Path, package_dir_arg: Path, *, clean: bool) -> Path:
        project_path = original_create(project_dir, package_dir_arg, clean=clean)
        json_out.write_text(
            json.dumps(
                {
                    "schema": "fastdis.unreal_packaged_install_smoke.v1",
                    "generated_at": "2026-06-26T00:00:00Z",
                    "status": "pass",
                    "demo_map": "/FastDis/Examples/FastDis_Demo",
                    "project_dir": str(project_dir),
                    "package_dir": str(package_dir_arg),
                    "checks": [{"name": "load_demo_map", "status": "ok", "detail": "map loaded"}],
                }
            )
            + "\n",
            encoding="utf-8",
        )
        return project_path

    monkeypatch.setattr(run_unreal_packaged_install_smoke, "create_scratch_project", fake_create_scratch)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_unreal_packaged_install_smoke.py",
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

    assert run_unreal_packaged_install_smoke.main() == 0
    payload = json.loads(json_out.read_text(encoding="utf-8"))
    assert payload["status"] == "pass"
    assert payload["terminated_after_report"] is True
    assert payload["elapsed_seconds"] == 12.5
