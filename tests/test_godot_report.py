from __future__ import annotations

import json
import sys
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import run_godot_report


def test_critical_doctor_failures_only_considers_host_tooling_checks() -> None:
    payload = {
        "checks": [
            {"name": "godot", "status": "ok", "detail": "ok"},
            {"name": "scons", "status": "fail", "detail": "missing"},
            {"name": "cmake", "status": "ok", "detail": "ok"},
            {"name": "godot-cpp", "status": "ok", "detail": "ok"},
            {"name": "demo wrapper", "status": "fail", "detail": "stale"},
        ]
    }
    failures = run_godot_report.critical_doctor_failures(payload)
    assert failures == [{"name": "scons", "status": "fail", "detail": "missing"}]


def test_summarize_markdown_includes_all_lanes() -> None:
    report = {
        "generated_at": "2026-06-19T12:00:00Z",
        "doctor": {
            "status": "passed",
            "notes": [],
            "checks": [{"name": "godot", "status": "ok", "detail": "/Applications/Godot.app"}],
            "host": {
                "platform": "macos",
                "arch": "arm64",
                "godot": "/Applications/Godot.app/Contents/MacOS/Godot",
                "scons": "/opt/homebrew/bin/scons",
                "repo_alias_root": "/tmp/fastdis_godot/repo",
                "work_root": "/tmp/fastdis_godot",
            },
        },
        "lanes": {
            "build": {"status": "passed", "notes": []},
            "verify": {"status": "passed", "notes": []},
            "demo": {"status": "passed", "notes": []},
            "missing_lib": {"status": "passed", "notes": []},
        },
    }
    markdown = run_godot_report.summarize_markdown(report)
    assert "| Lane | Status | Notes |" in markdown
    assert "| missing-lib | passed | none |" in markdown
    assert "- work_root: `/tmp/fastdis_godot`" in markdown


def test_main_blocks_runnable_lanes_when_doctor_proves_host_tooling_gap(monkeypatch, tmp_path: Path) -> None:
    out_dir = tmp_path / "reports"
    monkeypatch.setattr(
        run_godot_report,
        "parse_args",
        lambda: run_godot_report.argparse.Namespace(
            out_dir=str(out_dir),
            skip_build=False,
            skip_verify=False,
            skip_demo=False,
            skip_missing_lib=False,
        ),
    )
    monkeypatch.setattr(run_godot_report.load_local_env, "load", lambda: None)
    monkeypatch.setattr(
        run_godot_report.godot_workflow,
        "doctor_payload",
        lambda: {
            "host": {
                "platform": "macos",
                "arch": "arm64",
                "godot": None,
                "scons": None,
                "repo_alias_root": "/tmp/fastdis_godot/repo",
                "work_root": "/tmp/fastdis_godot",
            },
            "checks": [
                {"name": "godot", "status": "fail", "detail": "missing godot executable"},
                {"name": "scons", "status": "ok", "detail": "ok"},
                {"name": "cmake", "status": "ok", "detail": "ok"},
                {"name": "godot-cpp", "status": "ok", "detail": "ok"},
            ],
        },
    )

    exit_code = run_godot_report.main()

    assert exit_code == 2
    payload = json.loads((out_dir / "godot_workflow_report.json").read_text(encoding="utf-8"))
    assert payload["doctor"]["status"] == "needs-attention"
    assert payload["lanes"]["build"]["status"] == "blocked"
    assert payload["lanes"]["verify"]["status"] == "blocked"
    assert payload["lanes"]["demo"]["status"] == "blocked"
    assert payload["lanes"]["missing_lib"]["status"] == "blocked"


def test_main_runs_all_positive_lanes_and_writes_report(monkeypatch, tmp_path: Path) -> None:
    out_dir = tmp_path / "reports"
    monkeypatch.setattr(
        run_godot_report,
        "parse_args",
        lambda: run_godot_report.argparse.Namespace(
            out_dir=str(out_dir),
            skip_build=False,
            skip_verify=False,
            skip_demo=False,
            skip_missing_lib=False,
        ),
    )
    monkeypatch.setattr(run_godot_report.load_local_env, "load", lambda: None)
    monkeypatch.setattr(
        run_godot_report.godot_workflow,
        "doctor_payload",
        lambda: {
            "host": {
                "platform": "macos",
                "arch": "arm64",
                "godot": "/Applications/Godot.app/Contents/MacOS/Godot",
                "scons": "/opt/homebrew/bin/scons",
                "repo_alias_root": "/tmp/fastdis_godot/repo",
                "work_root": "/tmp/fastdis_godot",
            },
            "checks": [
                {"name": "godot", "status": "ok", "detail": "ok"},
                {"name": "scons", "status": "ok", "detail": "ok"},
                {"name": "cmake", "status": "ok", "detail": "ok"},
                {"name": "godot-cpp", "status": "ok", "detail": "ok"},
            ],
        },
    )
    recorded: list[list[str]] = []

    def fake_run_step(cmd: list[str]) -> tuple[int, str]:
        recorded.append(cmd)
        return 0, "ok"

    monkeypatch.setattr(run_godot_report, "run_step", fake_run_step)

    exit_code = run_godot_report.main()

    assert exit_code == 0
    assert recorded == [
        [sys.executable, "tools/build_godot_extension.py"],
        [sys.executable, "tools/run_godot_orientation_verification.py", "--skip-build"],
        [sys.executable, "tools/run_godot_demo_smoke.py", "--skip-build"],
        [sys.executable, "tools/run_godot_missing_library_check.py", "--skip-build"],
    ]
    payload = json.loads((out_dir / "godot_workflow_report.json").read_text(encoding="utf-8"))
    assert payload["lanes"]["build"]["status"] == "passed"
    assert payload["lanes"]["missing_lib"]["status"] == "passed"
