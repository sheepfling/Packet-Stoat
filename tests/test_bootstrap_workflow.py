from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import bootstrap_workflow


def test_doctor_mode_prints_found_and_skipped_summary(monkeypatch, tmp_path: Path, capsys) -> None:
    out_dir = tmp_path / "reports"
    monkeypatch.setattr(
        bootstrap_workflow,
        "parse_args",
        lambda: bootstrap_workflow.argparse.Namespace(
            out_dir=str(out_dir),
            doctor=True,
            skip_godot=False,
            skip_unreal=True,
            unreal_version=None,
        ),
    )
    monkeypatch.setattr(bootstrap_workflow.load_local_env, "load", lambda: None)
    monkeypatch.setattr(
        bootstrap_workflow.unreal_env,
        "discover_installs",
        lambda: [SimpleNamespace(version="5.8", editor_path=r"C:\Epic\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe")],
    )
    monkeypatch.setattr(
        bootstrap_workflow,
        "host_payload",
        lambda: {
            "platform": "Windows",
            "arch": "AMD64",
            "godot": r"C:\Users\Public\Godot\engines\Godot_v4.7-stable_win64\Godot_v4.7-stable_win64_console.exe",
            "scons": r"C:\Users\peanu\GIT\sheepfling\Packet-Stoat\.venv\Scripts\scons.exe",
            "unity_editor": r"C:\Program Files\Unity\Hub\Editor\6000.5.1f1\Editor\Unity.exe",
            "unity_install_root": r"C:\Program Files\Unity\Hub\Editor\6000.5.1f1",
            "unity_override_editor": r"C:\Program Files\Unity\Hub\Editor\6000.5.1f1\Editor\Unity.exe",
            "unity_override_editor_dir": r"C:\Program Files\Unity\Hub\Editor\6000.5.1f1",
            "unreal_host": "Win64",
        },
    )
    monkeypatch.setattr(
        bootstrap_workflow.host_capability_matrix,
        "build_payload",
        lambda: {
            "routes": [
                {
                    "name": "godot-native",
                    "surface": "godot",
                    "activation": "ready-now",
                    "light_up_command": "fastdis engine godot full",
                    "evidence_commands": ["fastdis engine godot doctor"],
                    "missing_installs": [],
                    "install_commands": [],
                    "missing_setup_steps": [],
                },
                {
                    "name": "windows-cross-mingw",
                    "surface": "python",
                    "activation": "ready-after-setup",
                    "light_up_command": "python tools/windows_wheel_workflow.py full --no-isolation",
                    "evidence_commands": ["python tools/windows_wheel_workflow.py doctor"],
                    "missing_installs": [],
                    "install_commands": [],
                    "missing_setup_steps": ["Run the wheel workflow"],
                },
            ]
        },
    )
    monkeypatch.setattr(
        bootstrap_workflow,
        "collect_legacy_output_dirs",
        lambda: [{"source": "build/reports", "destination": "artifacts/reports"}],
    )
    monkeypatch.setattr(bootstrap_workflow, "run_lane", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("doctor mode should not run lanes")))

    exit_code = bootstrap_workflow.main()
    out = capsys.readouterr().out

    assert exit_code == 0
    assert "FastDIS bootstrap doctor" in out
    assert "C:\\Users\\Public\\Godot\\engines\\Godot_v4.7-stable_win64\\Godot_v4.7-stable_win64_console.exe" in out
    assert "C:\\Users\\peanu\\GIT\\sheepfling\\Packet-Stoat\\.venv\\Scripts\\scons.exe" in out
    assert "C:\\Program Files\\Unity\\Hub\\Editor\\6000.5.1f1\\Editor\\Unity.exe" in out
    assert "recommended_FASTDIS_UNITY_EDITOR" in out
    assert "$env:FASTDIS_UNITY_EDITOR = 'C:\\Program Files\\Unity\\Hub\\Editor\\6000.5.1f1\\Editor\\Unity.exe'" in out
    assert "$env:FASTDIS_UNITY_EDITOR_DIR = 'C:\\Program Files\\Unity\\Hub\\Editor\\6000.5.1f1'" in out
    assert "- unreal_version: `5.8`" in out
    assert "- next_command: `fastdis bootstrap --skip-unreal --unreal-version 5.8`" in out
    assert "- legacy_output_dirs: `1`" in out
    assert "warning: legacy local outputs were found under old build/ or repo-root locations" in out
    assert "remediation: remove or relocate these directories before trusting the local output tree" in out
    assert "build/reports -> artifacts/reports" in out
    assert "- cross_platform_policy:" in out
    assert "Linux target from Windows: canonical backends are direct CMake cross-compile or Docker fallback" in out
    assert "- route_activation:" in out
    assert "godot-native: ready-now" in out
    assert "windows-cross-mingw" not in out
    assert "action: `run`" in out
    assert "action: `skipped`" in out
    assert not (out_dir / "bootstrap_report.json").exists()
    assert not (out_dir / "bootstrap_report.md").exists()


def test_markdown_report_includes_unity_session_snippet() -> None:
    report = {
        "generated_at": "2026-06-29T00:00:00+00:00",
        "host": {
            "platform": "Windows",
            "arch": "AMD64",
            "unreal_host": "Win64",
            "godot": r"C:\Godot\Godot.exe",
            "scons": r"C:\venv\Scripts\scons.exe",
            "unity_editor": r"C:\Program Files\Unity\Hub\Editor\6000.5.1f1\Editor\Unity.exe",
            "unity_install_root": r"C:\Program Files\Unity\Hub\Editor\6000.5.1f1",
            "unity_override_editor": r"C:\Program Files\Unity\Hub\Editor\6000.5.1f1\Editor\Unity.exe",
            "unity_override_editor_dir": r"C:\Program Files\Unity\Hub\Editor\6000.5.1f1",
            "unity_override_snippet": [
                "$env:FASTDIS_UNITY_EDITOR = 'C:\\Program Files\\Unity\\Hub\\Editor\\6000.5.1f1\\Editor\\Unity.exe'",
                "$env:FASTDIS_UNITY_EDITOR_DIR = 'C:\\Program Files\\Unity\\Hub\\Editor\\6000.5.1f1'",
            ],
        },
        "lanes": {
            "godot": {"status": "passed", "notes": [], "command": ["python", "tools/run_godot_report.py"]},
            "unreal": {"status": "skipped", "notes": ["user requested skip"], "command": None},
        },
    }

    markdown = bootstrap_workflow.summarize_markdown(report)

    assert "## Unity Session" in markdown
    assert "recommended_FASTDIS_UNITY_EDITOR" in markdown
    assert "$env:FASTDIS_UNITY_EDITOR = 'C:\\Program Files\\Unity\\Hub\\Editor\\6000.5.1f1\\Editor\\Unity.exe'" in markdown
    assert "$env:FASTDIS_UNITY_EDITOR_DIR = 'C:\\Program Files\\Unity\\Hub\\Editor\\6000.5.1f1'" in markdown
    assert "## Cross-Platform Policy" in markdown
    assert "Linux target from Windows: canonical backends are direct CMake cross-compile or Docker fallback" in markdown


def test_doctor_mode_reports_clean_artifact_layout(monkeypatch, tmp_path: Path, capsys) -> None:
    out_dir = tmp_path / "reports"
    monkeypatch.setattr(
        bootstrap_workflow,
        "parse_args",
        lambda: bootstrap_workflow.argparse.Namespace(
            out_dir=str(out_dir),
            doctor=True,
            skip_godot=True,
            skip_unreal=True,
            unreal_version=None,
        ),
    )
    monkeypatch.setattr(bootstrap_workflow.load_local_env, "load", lambda: None)
    monkeypatch.setattr(bootstrap_workflow.unreal_env, "discover_installs", lambda: [])
    monkeypatch.setattr(
        bootstrap_workflow,
        "host_payload",
        lambda: {
            "platform": "Windows",
            "arch": "AMD64",
            "godot": "",
            "scons": "",
            "unity_editor": "",
            "unity_install_root": "",
            "unity_override_editor": "",
            "unity_override_editor_dir": "",
            "unreal_host": "Win64",
        },
    )
    monkeypatch.setattr(bootstrap_workflow.host_capability_matrix, "build_payload", lambda: {"routes": []})
    monkeypatch.setattr(bootstrap_workflow, "collect_legacy_output_dirs", lambda: [])

    exit_code = bootstrap_workflow.main()
    out = capsys.readouterr().out

    assert exit_code == 0
    assert "- legacy_output_dirs: `0`" in out
    assert "status: using current artifacts/ layout only" in out
