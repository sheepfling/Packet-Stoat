from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = ROOT / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import run_orientation_runtime_report


def test_parse_events_extracts_numeric_orientation_lines() -> None:
    text = """
FASTDIS_ORIENTATION_PASS case=level_north axis=forward angle_deg=0.00000000 dot=1.00000000 threshold_deg=0.01000000
FASTDIS_ORIENTATION_PASS case=level_north axis=right angle_deg=0.00000001 dot=0.99999999 threshold_deg=0.01000000
"""
    events = run_orientation_runtime_report.parse_events(text)
    assert len(events) == 2
    assert events[0]["case"] == "level_north"
    assert events[0]["axis"] == "forward"
    assert events[1]["angle_deg"] == 1e-8


def test_summarize_events_reports_counts_and_extrema() -> None:
    summary = run_orientation_runtime_report.summarize_events(
        [
            {"status": "pass", "case": "a", "axis": "forward", "angle_deg": 0.1, "dot": 0.99, "threshold_deg": 0.5},
            {"status": "fail", "case": "b", "axis": "up", "angle_deg": 0.2, "dot": 0.98, "threshold_deg": 0.5},
        ]
    )
    assert summary["event_count"] == 2
    assert summary["case_count"] == 2
    assert summary["failure_count"] == 1
    assert summary["max_angle_deg"] == 0.2
    assert summary["min_dot"] == 0.98


def test_main_writes_reports_from_stubbed_lanes(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        run_orientation_runtime_report,
        "run_unreal_lane",
        lambda engine_version, out_dir: {
            "status": "passed",
            "returncode": 0,
            "command": ["unreal"],
            "notes": [],
            "events": [{"status": "pass", "case": "u", "axis": "forward", "angle_deg": 0.0, "dot": 1.0, "threshold_deg": 0.01}],
            "summary": run_orientation_runtime_report.summarize_events(
                [{"status": "pass", "case": "u", "axis": "forward", "angle_deg": 0.0, "dot": 1.0, "threshold_deg": 0.01}]
            ),
            "raw_output_path": "verification_reports/alpha2_sample/unreal.log",
        },
    )
    monkeypatch.setattr(
        run_orientation_runtime_report,
        "run_godot_lane",
        lambda out_dir: {
            "status": "passed",
            "returncode": 0,
            "command": ["godot"],
            "notes": [],
            "events": [{"status": "pass", "case": "g", "axis": "forward", "angle_deg": 0.0, "dot": 1.0, "threshold_deg": 0.01}],
            "summary": run_orientation_runtime_report.summarize_events(
                [{"status": "pass", "case": "g", "axis": "forward", "angle_deg": 0.0, "dot": 1.0, "threshold_deg": 0.01}]
            ),
            "raw_output_path": "verification_reports/alpha2_sample/godot.log",
        },
    )
    monkeypatch.setattr(sys, "argv", ["run_orientation_runtime_report.py", "--out-dir", str(tmp_path)])

    rc = run_orientation_runtime_report.main()
    assert rc == 0
    payload = json.loads((tmp_path / "orientation_runtime_report.json").read_text(encoding="utf-8"))
    assert payload["lanes"]["unreal"]["5.8"]["status"] == "passed"
    assert payload["unreal_engine_versions"] == ["5.8"]
    assert payload["lanes"]["godot"]["summary"]["event_count"] == 1
    assert "Orientation Runtime Report" in (tmp_path / "orientation_runtime_report.md").read_text(encoding="utf-8")


def test_main_supports_multiple_unreal_versions(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        run_orientation_runtime_report,
        "run_unreal_lane",
        lambda engine_version, out_dir: {
            "status": "passed",
            "returncode": 0,
            "command": ["unreal", engine_version],
            "notes": [],
            "events": [{"status": "pass", "case": engine_version, "axis": "forward", "angle_deg": 0.0, "dot": 1.0, "threshold_deg": 0.01}],
            "summary": run_orientation_runtime_report.summarize_events(
                [{"status": "pass", "case": engine_version, "axis": "forward", "angle_deg": 0.0, "dot": 1.0, "threshold_deg": 0.01}]
            ),
            "raw_output_path": f"verification_reports/alpha2_sample/unreal_{engine_version}.log",
        },
    )
    monkeypatch.setattr(
        run_orientation_runtime_report,
        "run_godot_lane",
        lambda out_dir: {
            "status": "passed",
            "returncode": 0,
            "command": ["godot"],
            "notes": [],
            "events": [],
            "summary": run_orientation_runtime_report.summarize_events([]),
            "raw_output_path": "verification_reports/alpha2_sample/godot.log",
        },
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_orientation_runtime_report.py",
            "--out-dir",
            str(tmp_path),
            "--engine-version",
            "5.7",
            "--engine-version",
            "5.8",
        ],
    )

    rc = run_orientation_runtime_report.main()
    assert rc == 0
    payload = json.loads((tmp_path / "orientation_runtime_report.json").read_text(encoding="utf-8"))
    assert payload["unreal_engine_versions"] == ["5.7", "5.8"]
    assert payload["lanes"]["unreal"]["5.7"]["status"] == "passed"
    assert payload["lanes"]["unreal"]["5.8"]["status"] == "passed"
    markdown = (tmp_path / "orientation_runtime_report.md").read_text(encoding="utf-8")
    assert "| unreal-5.7 | passed | 1 | 1 | 0.00000000 | 1.00000000 | none |" in markdown
    assert "| unreal-5.8 | passed | 1 | 1 | 0.00000000 | 1.00000000 | none |" in markdown
